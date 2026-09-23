"""
brain/test_stage2_spatial_grounding_benchmark.py — Forensic Spatial Grounding Architecture Benchmark
Classification: [SCIENTIFIC BENCHMARK] 4-Condition Information Gain & Grounding Comparison

Empirically answers:
"How much predictive information is already present in CARL's Stage 2.1 spatial state?"

Evaluates 4 distinct representations under identical recurrent capacity (GRU-128 + MLP decoder):
- Condition A: Sensors only (31 dims)
- Condition B: Sensors + HD ring (33 dims) [Stage 2.2 Baseline]
- Condition C: Sensors + Spatial Grid state (33 dims)
- Condition D: Sensors + HD + Spatial Grid state (35 dims) [Full Spatial Grounding]

Metrics on PRIMARY_UNSEEN_TEST (N=25 episodes, seeds 303, 404, 505, 606, 707):
- Dynamic Sonar R2 (s < 4.5m)
- Gyro Yaw Rate R2
- Proprioception R2
- Composite RMSE across H=1, 5, 10, 15, 30
- Causal Action Sensitivity (Action-Zero Degradation)
- Paired Wilcoxon signed-rank tests (D vs A, D vs B, D vs C)
"""

import os
import sys
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from scipy import stats

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot < 1e-8:
        return 1.0 if ss_res < 1e-8 else 0.0
    return float(1.0 - (ss_res / ss_tot))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


class SpatialTrajectoryDataset(Dataset):
    def __init__(self, npz_path: Path, seq_len: int = 11):
        data = np.load(npz_path)
        self.S = data["S"]            # (N, T, 25)
        self.V_hd = data["V_hd"]      # (N, T, 2)
        self.G_grid = data["G_grid"]  # (N, T, 2)
        self.U = data["U"]            # (N, T, 6)
        self.seq_len = seq_len

        self.samples = []
        n_ep, T, _ = self.S.shape
        for ep in range(n_ep):
            for t in range(0, T - seq_len, 5):
                self.samples.append((ep, t))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        ep, t = self.samples[idx]
        return (
            torch.from_numpy(self.S[ep, t: t + self.seq_len]),
            torch.from_numpy(self.V_hd[ep, t: t + self.seq_len]),
            torch.from_numpy(self.G_grid[ep, t: t + self.seq_len]),
            torch.from_numpy(self.U[ep, t: t + self.seq_len])
        )


class BenchmarkWorldModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, batch_first=True)
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, 25)
        )

        bounds_min = np.array([0.0]*15 + [-50.0]*3 + [-20.0]*3 + [-math.pi]*3 + [0.0], dtype=np.float32)
        bounds_max = np.array([5.0]*15 + [50.0]*3 + [20.0]*3 + [math.pi]*3 + [1.0], dtype=np.float32)
        self.register_buffer("bounds_min", torch.from_numpy(bounds_min))
        self.register_buffer("bounds_max", torch.from_numpy(bounds_max))

    def forward_step(self, h_t: torch.Tensor, x_t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # x_t: (B, input_dim)
        out, h_next = self.gru(x_t.unsqueeze(1), h_t)
        s_norm_hat = self.decoder(out.squeeze(1))
        return h_next, s_norm_hat

    def clamp_physical_bounds(self, s: torch.Tensor) -> torch.Tensor:
        return torch.max(torch.min(s, self.bounds_max), self.bounds_min)


def train_single_condition(
    condition_name: str,
    input_dim: int,
    build_x_fn,
    train_loader: DataLoader,
    mu: np.ndarray,
    sigma: np.ndarray,
    epochs: int = 25,
    device: str = "cpu"
) -> BenchmarkWorldModel:
    print(f"\n--- Training {condition_name} (Input Dim: {input_dim}) ---")
    model = BenchmarkWorldModel(input_dim=input_dim).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    mu_t = torch.from_numpy(mu).to(device)
    sig_t = torch.from_numpy(sigma).to(device)

    weights = np.array([1.0]*15 + [1.0]*3 + [2.0]*3 + [1.0]*3 + [0.1], dtype=np.float32)
    w_loss = torch.from_numpy(weights).to(device)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        n_batches = 0
        tf_ratio = max(0.2, 0.8 - (epoch / epochs) * 0.6)

        for s_seq, v_seq, g_seq, u_seq in train_loader:
            s_seq = s_seq.to(device)
            v_seq = v_seq.to(device)
            g_seq = g_seq.to(device)
            u_seq = u_seq.to(device)

            B = s_seq.size(0)
            H = s_seq.size(1) - 1
            h = torch.zeros(1, B, model.hidden_dim, device=device)

            curr_s = s_seq[:, 0, :]
            curr_v = v_seq[:, 0, :]
            curr_g = g_seq[:, 0, :]

            batch_loss = 0.0
            for k in range(H):
                s_norm = (curr_s - mu_t) / sig_t
                u_k = u_seq[:, k, :]
                x_k = build_x_fn(s_norm, curr_v, curr_g, u_k)

                h, s_norm_hat = model.forward_step(h, x_k)

                target_s = s_seq[:, k + 1, :]
                target_norm = (target_s - mu_t) / sig_t
                loss_step = torch.mean(w_loss * (s_norm_hat - target_norm)**2)
                batch_loss += loss_step

                if np.random.rand() < tf_ratio:
                    curr_s = target_s
                    curr_v = v_seq[:, k + 1, :]
                    curr_g = g_seq[:, k + 1, :]
                else:
                    s_hat_raw = (s_norm_hat * sig_t) + mu_t
                    curr_s = model.clamp_physical_bounds(s_hat_raw)
                    curr_v = v_seq[:, k + 1, :]
                    curr_g = g_seq[:, k + 1, :]

            optimizer.zero_grad()
            batch_loss = batch_loss / H
            batch_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += batch_loss.item()
            n_batches += 1

        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:2d}/{epochs} | Loss: {total_loss / n_batches:.5f}")

    return model


def evaluate_condition_rollouts(
    model: BenchmarkWorldModel,
    build_x_fn,
    S_test: np.ndarray,
    V_test: np.ndarray,
    G_test: np.ndarray,
    U_test: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    zero_action: bool = False
) -> Dict[str, Any]:
    model.eval()
    mu_t = torch.from_numpy(mu)
    sig_t = torch.from_numpy(sigma)

    N_ep, T, _ = S_test.shape
    horizons = [1, 5, 10, 15, 30]
    h_metrics = {}
    ep_rmses = []

    for H in horizons:
        all_true = []
        all_pred = []

        for ep in range(N_ep):
            s_ep = S_test[ep]
            v_ep = V_test[ep]
            g_ep = G_test[ep]
            u_ep = U_test[ep]

            ep_step_errs = []
            for t in range(0, T - H - 1, H):
                h0 = torch.zeros(1, 1, model.hidden_dim)
                curr_s = torch.from_numpy(s_ep[t:t+1]).float()
                curr_v = torch.from_numpy(v_ep[t:t+1]).float()
                curr_g = torch.from_numpy(g_ep[t:t+1]).float()

                preds = []
                for step_k in range(H):
                    s_norm = (curr_s - mu_t) / sig_t
                    u_k = torch.zeros(1, 6) if zero_action else torch.from_numpy(u_ep[t + step_k: t + step_k + 1]).float()
                    x_k = build_x_fn(s_norm, curr_v, curr_g, u_k)

                    with torch.no_grad():
                        h0, s_norm_hat = model.forward_step(h0, x_k)

                    s_hat_raw = (s_norm_hat * sig_t) + mu_t
                    curr_s = model.clamp_physical_bounds(s_hat_raw)
                    curr_v = torch.from_numpy(v_ep[t + step_k + 1: t + step_k + 2]).float()
                    curr_g = torch.from_numpy(g_ep[t + step_k + 1: t + step_k + 2]).float()

                    preds.append(curr_s.numpy())

                p_roll = np.concatenate(preds, axis=0)
                y_roll = s_ep[t + 1: t + 1 + H]

                all_true.append(y_roll)
                all_pred.append(p_roll)
                if H == 10:
                    ep_step_errs.append(np.mean((p_roll[:, :24] - y_roll[:, :24])**2))

            if H == 10 and len(ep_step_errs) > 0:
                ep_rmses.append(float(np.sqrt(np.mean(ep_step_errs))))

        y_true = np.concatenate(all_true, axis=0)
        y_pred = np.concatenate(all_pred, axis=0)

        # Metrics
        # Gyro (18..20)
        r2_gyro = compute_r2(y_true[:, 18:21], y_pred[:, 18:21])
        # Dynamic Sonar (< 4.5m)
        dyn_mask = (y_true[:, :15] < 4.5)
        if np.sum(dyn_mask) > 100:
            r2_sonar_dyn = compute_r2(y_true[:, :15][dyn_mask], y_pred[:, :15][dyn_mask])
        else:
            r2_sonar_dyn = 0.0
        # All Sonars
        r2_sonar_all = compute_r2(y_true[:, :15], y_pred[:, :15])
        # Proprioception (15..17)
        r2_prop = compute_r2(y_true[:, 21:24], y_pred[:, 21:24])
        # Composite 24-D
        r2_comp = compute_r2(y_true[:, :24], y_pred[:, :24])
        rmse_comp = compute_rmse(y_true[:, :24], y_pred[:, :24])

        h_metrics[f"H_{H}"] = {
            "r2_gyro": r2_gyro,
            "r2_sonar_dynamic": r2_sonar_dyn,
            "r2_sonar_all": r2_sonar_all,
            "r2_proprio": r2_prop,
            "r2_composite": r2_comp,
            "rmse_composite": rmse_comp
        }

    return {
        "horizon_metrics": h_metrics,
        "ep_rmses_h10": ep_rmses,
        "mean_rmse_h10": float(np.mean(ep_rmses)) if len(ep_rmses) > 0 else 0.0
    }


def run_spatial_grounding_benchmark():
    print("=" * 80)
    print("FORENSIC SPATIAL GROUNDING ARCHITECTURE BENCHMARK")
    print("=" * 80)

    datasets_dir = Path("evidence/stage2_2/datasets")
    train_path = datasets_dir / "spatial_dev_train.npz"
    test_path = datasets_dir / "spatial_unseen_test.npz"

    assert train_path.exists() and test_path.exists(), "Missing spatial datasets. Run collector first!"

    train_ds = SpatialTrajectoryDataset(train_path, seq_len=11)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, drop_last=True)

    # Compute normalization statistics
    tr_npz = np.load(train_path)
    S_tr = tr_npz["S"].reshape(-1, 25)
    mu = np.mean(S_tr, axis=0).astype(np.float32)
    sigma = np.maximum(np.std(S_tr, axis=0), 1e-4).astype(np.float32)

    # Load unseen test set
    test_npz = np.load(test_path)
    S_test = test_npz["S"]
    V_test = test_npz["V_hd"]
    G_test = test_npz["G_grid"]
    U_test = test_npz["U"]

    # Define the 4 Condition Input Builders
    # Condition A: Sensors only (25 + 6 = 31)
    build_a = lambda s, v, g, u: torch.cat([s, u], dim=-1)
    # Condition B: Sensors + HD Ring (25 + 2 + 6 = 33)
    build_b = lambda s, v, g, u: torch.cat([s, v, u], dim=-1)
    # Condition C: Sensors + Spatial Grid (25 + 2 + 6 = 33)
    build_c = lambda s, v, g, u: torch.cat([s, g, u], dim=-1)
    # Condition D: Sensors + HD + Spatial Grid (25 + 2 + 2 + 6 = 35)
    build_d = lambda s, v, g, u: torch.cat([s, v, g, u], dim=-1)

    conditions = [
        ("Condition A (Sensors Only)", 31, build_a),
        ("Condition B (Sensors + HD Ring)", 33, build_b),
        ("Condition C (Sensors + Spatial Grid)", 33, build_c),
        ("Condition D (Sensors + HD + Spatial Grid)", 35, build_d),
    ]

    trained_models = {}
    results = {}

    for name, inp_dim, b_fn in conditions:
        model = train_single_condition(
            condition_name=name,
            input_dim=inp_dim,
            build_x_fn=b_fn,
            train_loader=train_loader,
            mu=mu,
            sigma=sigma,
            epochs=25
        )
        trained_models[name] = (model, b_fn)

        # Standard Evaluation
        eval_res = evaluate_condition_rollouts(
            model=model,
            build_x_fn=b_fn,
            S_test=S_test,
            V_test=V_test,
            G_test=G_test,
            U_test=U_test,
            mu=mu,
            sigma=sigma,
            zero_action=False
        )

        # Action-Zero Ablation Evaluation
        abl_res = evaluate_condition_rollouts(
            model=model,
            build_x_fn=b_fn,
            S_test=S_test,
            V_test=V_test,
            G_test=G_test,
            U_test=U_test,
            mu=mu,
            sigma=sigma,
            zero_action=True
        )

        intact_rmse = eval_res["mean_rmse_h10"]
        zero_rmse = abl_res["mean_rmse_h10"]
        deg_pct = ((zero_rmse - intact_rmse) / intact_rmse) * 100.0

        eval_res["action_zero_rmse_h10"] = zero_rmse
        eval_res["action_sensitivity_degradation_pct"] = deg_pct

        results[name] = eval_res
        print(f"\n[{name}] H=10 Summary:")
        h10 = eval_res["horizon_metrics"]["H_10"]
        print(f"  Dynamic Sonar R2: {h10['r2_sonar_dynamic']:.4f} | Gyro R2: {h10['r2_gyro']:.4f} | Proprio R2: {h10['r2_proprio']:.4f}")
        print(f"  Composite RMSE:   {intact_rmse:.4f} | Action-Zero Deg: +{deg_pct:.1f}%")

    # Statistical Significance Comparisons: Condition D vs A, B, C
    ep_d = results["Condition D (Sensors + HD + Spatial Grid)"]["ep_rmses_h10"]
    comparisons = {}

    for name, _, _ in conditions[:3]:
        ep_other = results[name]["ep_rmses_h10"]
        stat, p_val = stats.wilcoxon(ep_other, ep_d, alternative="greater")
        diff = np.array(ep_other) - np.array(ep_d)
        d_eff = float(np.mean(diff) / (np.std(diff) + 1e-9))
        pct_imp = float((np.mean(ep_other) - np.mean(ep_d)) / np.mean(ep_other) * 100.0)

        comparisons[f"D_vs_{name[:11]}"] = {
            "wilcoxon_stat": float(stat),
            "p_value": float(p_val),
            "cohens_d": d_eff,
            "pct_improvement": pct_imp
        }

    scorecard = {
        "milestone": "Forensic Spatial Grounding Architecture Benchmark",
        "conditions": results,
        "statistical_comparisons": comparisons,
        "norm_mu": mu.tolist(),
        "norm_sigma": sigma.tolist()
    }

    out_json = Path("evidence/stage2_2/spatial_grounding_scorecard.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETE! Scorecard saved to: {out_json}")
    print("=" * 80)
    return scorecard


if __name__ == "__main__":
    run_spatial_grounding_benchmark()
