"""
brain/train_stage2_2_world_model.py — Self-Supervised Training Pipeline (Stage 2.2)
Classification: [TRAINING PIPELINE] Multi-Horizon Autoregressive Optimization

Trains the Action-Conditioned Recurrent World Model on DEV_TRAIN and validates on DEV_VAL.
Implements:
- Multi-horizon autoregressive loss (H=10) with scheduled sampling
- Modality-weighted normalized MSE loss
- Early stopping on DEV_VAL autoregressive loss
- Checkpoint selection & permanent hard freeze to checkpoints/carl_stage2_2_world_model_frozen.pt
- SHA-256 cryptographic provenance logging
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage2_2_world_model import (
    CarlStage2WorldModel,
    SensoryNormalizer,
    LinearActionPredictor
)


class TrajectoryDataset(Dataset):
    """PyTorch Dataset for multi-step sensorimotor trajectories."""
    def __init__(self, npz_path: Path, seq_len: int = 15):
        data = np.load(npz_path)
        self.S = data["S"]        # (N_episodes, T, 25)
        self.V_hd = data["V_hd"]  # (N_episodes, T, 2)
        self.U = data["U"]        # (N_episodes, T, 6)
        self.seq_len = seq_len

        self.samples = []
        n_ep, T, _ = self.S.shape
        for ep in range(n_ep):
            for t in range(0, T - seq_len, 5):  # stride 5 for diverse starting states
                self.samples.append((ep, t))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        ep, t = self.samples[idx]
        s_seq = self.S[ep, t: t + self.seq_len]         # (seq_len, 25)
        v_hd_seq = self.V_hd[ep, t: t + self.seq_len]   # (seq_len, 2)
        u_seq = self.U[ep, t: t + self.seq_len]         # (seq_len, 6)
        return (
            torch.from_numpy(s_seq),
            torch.from_numpy(v_hd_seq),
            torch.from_numpy(u_seq)
        )


def compute_sha256(file_path: Path) -> str:
    """Computes cryptographic SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def train_world_model(
    epochs: int = 40,
    batch_size: int = 64,
    lr: float = 1e-3,
    hidden_dim: int = 128,
    horizon: int = 10,
    device: str = "cpu"
):
    print("\n" + "=" * 70)
    print("STARTING STAGE 2.2 SELF-SUPERVISED TRAINING PIPELINE")
    print("=" * 70)

    dataset_dir = Path("evidence/stage2_2/datasets")
    checkpoints_dir = Path("checkpoints")
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    train_path = dataset_dir / "dev_train.npz"
    val_path = dataset_dir / "dev_val.npz"
    norm_path = checkpoints_dir / "stage2_2_norm_stats.npz"

    assert train_path.exists(), f"Missing {train_path}"
    assert val_path.exists(), f"Missing {val_path}"
    assert norm_path.exists(), f"Missing {norm_path}"

    # 1. Load Normalization Statistics
    norm_data = np.load(norm_path)
    mu = norm_data["mu"]
    sigma = norm_data["sigma"]
    normalizer = SensoryNormalizer(mu, sigma)

    # 2. Fit and Save Linear Baseline Model
    print("\nFitting Baseline B (Linear Action Predictor) on DEV_TRAIN...")
    train_npz = np.load(train_path)
    S_tr = train_npz["S"]
    V_tr = train_npz["V_hd"]
    U_tr = train_npz["U"]

    S_curr_all = S_tr[:, :-1, :].reshape(-1, 25)
    V_curr_all = V_tr[:, :-1, :].reshape(-1, 2)
    U_curr_all = U_tr[:, :-1, :].reshape(-1, 6)
    S_next_all = S_tr[:, 1:, :].reshape(-1, 25)

    linear_baseline = LinearActionPredictor(alpha=10.0)
    linear_baseline.fit(S_curr_all, V_curr_all, U_curr_all, S_next_all)
    np.save(checkpoints_dir / "stage2_2_linear_weights.npy", linear_baseline.W)
    print(f"Baseline B weights saved to {checkpoints_dir / 'stage2_2_linear_weights.npy'}")

    # 3. Create Datasets and DataLoaders
    train_ds = TrajectoryDataset(train_path, seq_len=horizon + 1)
    val_ds = TrajectoryDataset(val_path, seq_len=horizon + 1)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    print(f"Dataset Loaded: {len(train_ds)} train sequences, {len(val_ds)} val sequences (Horizon H={horizon})")

    # 4. Initialize World Model
    model = CarlStage2WorldModel(hidden_dim=hidden_dim, dt=0.030).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    # Channel loss weighting: sonar=1.0, accel=1.0, gyro=2.0, proprio=1.0, batt=0.1
    weights = np.array([1.0]*15 + [1.0]*3 + [2.0]*3 + [1.0]*3 + [0.1], dtype=np.float32)
    w_loss = torch.from_numpy(weights).to(device)

    best_val_loss = float("inf")
    best_epoch = 0
    patience = 15
    patience_counter = 0

    train_loss_history = []
    val_loss_history = []

    frozen_model_path = checkpoints_dir / "carl_stage2_2_world_model_frozen.pt"

    for epoch in range(1, epochs + 1):
        # Training Phase with Scheduled Sampling
        model.train()
        total_train_loss = 0.0
        n_train_batches = 0

        # Teacher forcing ratio decays from 0.8 to 0.2 over epochs
        tf_ratio = max(0.2, 0.8 - (epoch / epochs) * 0.6)

        for s_seq, v_hd_seq, u_seq in train_loader:
            s_seq = s_seq.to(device)        # (B, H+1, 25)
            v_hd_seq = v_hd_seq.to(device)  # (B, H+1, 2)
            u_seq = u_seq.to(device)        # (B, H+1, 6)

            B = s_seq.size(0)
            h = torch.zeros(1, B, hidden_dim, device=device)

            curr_s = s_seq[:, 0, :]
            curr_v_hd = v_hd_seq[:, 0, :]

            batch_loss = 0.0

            for k in range(horizon):
                u_k = u_seq[:, k, :]
                target_s = s_seq[:, k + 1, :]

                s_norm_k = normalizer.normalize(curr_s)
                h, s_norm_hat_next = model.forward_step(h, s_norm_k, curr_v_hd, u_k)

                target_norm_next = normalizer.normalize(target_s)
                step_loss = torch.mean(w_loss * (s_norm_hat_next - target_norm_next)**2)
                batch_loss += step_loss

                # Next step input selection: teacher forcing vs autoregressive prediction
                if np.random.rand() < tf_ratio:
                    curr_s = target_s
                    curr_v_hd = v_hd_seq[:, k + 1, :]
                else:
                    s_hat_raw = normalizer.denormalize(s_norm_hat_next)
                    curr_s = model.clamp_physical_bounds(s_hat_raw)
                    # Update heading from predicted gyro z
                    omega_z = curr_s[:, 20]
                    dtheta = omega_z * 0.030
                    cos_dt, sin_dt = torch.cos(dtheta), torch.sin(dtheta)
                    vx = curr_v_hd[:, 0] * cos_dt - curr_v_hd[:, 1] * sin_dt
                    vy = curr_v_hd[:, 0] * sin_dt + curr_v_hd[:, 1] * cos_dt
                    norm_v = torch.sqrt(vx**2 + vy**2 + 1e-9)
                    curr_v_hd = torch.stack([vx / norm_v, vy / norm_v], dim=-1)

            optimizer.zero_grad()
            batch_loss = batch_loss / horizon
            batch_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_train_loss += batch_loss.item()
            n_train_batches += 1

        avg_train_loss = total_train_loss / n_train_batches
        train_loss_history.append(avg_train_loss)

        # Validation Phase: PURE AUTOREGRESSIVE ROLLOUT (tf_ratio = 0.0)
        model.eval()
        total_val_loss = 0.0
        n_val_batches = 0

        with torch.no_grad():
            for s_seq, v_hd_seq, u_seq in val_loader:
                s_seq = s_seq.to(device)
                v_hd_seq = v_hd_seq.to(device)
                u_seq = u_seq.to(device)

                B = s_seq.size(0)
                h0 = torch.zeros(1, B, hidden_dim, device=device)
                s0 = s_seq[:, 0, :]
                v_hd0 = v_hd_seq[:, 0, :]
                u_rollout = u_seq[:, :horizon, :]

                s_pred_seq, _, _ = model.rollout_mental_trajectory(
                    h_0=h0,
                    s_0=s0,
                    v_hd_0=v_hd0,
                    u_seq=u_rollout,
                    normalizer=normalizer
                )

                target_seq = s_seq[:, 1: horizon + 1, :]
                # Compute normalized loss
                target_norm_seq = normalizer.normalize(target_seq)
                pred_norm_seq = normalizer.normalize(s_pred_seq)
                val_loss = torch.mean(w_loss.unsqueeze(0).unsqueeze(0) * (pred_norm_seq - target_norm_seq)**2)

                total_val_loss += val_loss.item()
                n_val_batches += 1

        avg_val_loss = total_val_loss / n_val_batches
        val_loss_history.append(avg_val_loss)

        # Checkpoint Tracking & Early Stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_epoch = epoch
            patience_counter = 0
            # Save current best model checkpoint
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "hidden_dim": hidden_dim,
                "val_loss": avg_val_loss,
                "dt": 0.030
            }, frozen_model_path)
            status_flag = "[BEST SAVED]"
        else:
            patience_counter += 1
            status_flag = f"[patience {patience_counter}/{patience}]"

        if epoch % 5 == 0 or epoch == 1 or "BEST" in status_flag:
            print(f"Epoch {epoch:2d}/{epochs:2d} | Train Loss: {avg_train_loss:.5f} | Val Loss (Auto-H10): {avg_val_loss:.5f} {status_flag}")

        if patience_counter >= patience:
            print(f"\nEarly stopping triggered at epoch {epoch}. Best epoch: {best_epoch} with val loss {best_val_loss:.5f}")
            break

    # 5. Lock and Hard Freeze the Selected Checkpoint
    print("\n" + "=" * 70)
    print(f"HARD FREEZING SELECTED CHECKPOINT: {frozen_model_path}")
    checkpoint_hash = compute_sha256(frozen_model_path)
    train_hash = compute_sha256(train_path)
    val_hash = compute_sha256(val_path)
    norm_hash = compute_sha256(norm_path)

    receipt = {
        "milestone": "Stage 2.2 World Model Training Receipt",
        "best_epoch": best_epoch,
        "best_val_loss_h10": best_val_loss,
        "final_train_loss": train_loss_history[-1],
        "hidden_dim": hidden_dim,
        "horizon": horizon,
        "frozen_checkpoint_file": str(frozen_model_path),
        "frozen_checkpoint_sha256": checkpoint_hash,
        "dev_train_sha256": train_hash,
        "dev_val_sha256": val_hash,
        "norm_stats_sha256": norm_hash,
        "train_loss_history": train_loss_history,
        "val_loss_history": val_loss_history
    }

    receipt_path = checkpoints_dir / "stage2_2_training_receipt.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    print(f"Training Receipt Saved to {receipt_path}")
    print(f"Checkpoint SHA-256: {checkpoint_hash}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    train_world_model(epochs=35, batch_size=64, lr=1e-3, horizon=10)
