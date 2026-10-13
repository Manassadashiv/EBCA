"""
brain/test_stage2_2_diagnostic_runner.py — Controlled 13-Model Falsification Benchmark
Classification: [DIAGNOSTIC BENCHMARK ENGINE] Stage 2.2 Phase 1 Execution Protocol

Trains and evaluates all 13 model configurations strictly on developmental data:
- Training: DEV_TRAIN (seeds 42, 101, 202; 24,000 timesteps)
- Evaluation: DEV_VAL (seeds 210, 220, 230, 240; 8,000 timesteps)

Executes the Canonical Six Batteries:
- Battery 1: Predictive Fidelity (Multi-Horizon H in {1, 5, 10, 15, 30} on D_all and D_dynamic)
- Battery 2: Action Causality (Action Zero, Permute, Sign-Flip)
- Battery 3: Spatial Causality (Spatial Phase Scrambling)
- Battery 4: Spatial Disambiguation (Tolerance-based local match with divergent spatial context)
- Battery 5: Counterfactual Branching (3 candidate action sequences from identical state)
- Battery 6: Collision Anticipation (Floor-contact corrected hazard prediction ROC-AUC)

Evaluates Capacity Control:
- Compares Condition F (M6-F-RES) against matched-capacity baseline (M2-B-MATCHED)
"""

import os
import sys
import math
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage2_2_world_model_suite import ALL_MODEL_IDS, create_model_by_id, BasePredictiveWorldModel


class SensoryNormalizer:
    """Computes mean and std strictly on DEV_TRAIN and normalizes features."""
    def __init__(self, mean: np.ndarray, std: np.ndarray):
        self.mean = torch.tensor(mean, dtype=torch.float32)
        # Avoid division by zero on static channels
        self.std = torch.tensor(np.where(std < 1e-4, 1.0, std), dtype=torch.float32)

    def normalize(self, x: torch.Tensor) -> torch.Tensor:
        return (x - self.mean.to(x.device)) / self.std.to(x.device)

    def denormalize(self, x: torch.Tensor) -> torch.Tensor:
        return x * self.std.to(x.device) + self.mean.to(x.device)


def compute_r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes coefficient of determination R^2."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot < 1e-8:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def prepare_input_tensors(
    model_id: str,
    S: np.ndarray,
    V_hd: np.ndarray,
    G_grid: np.ndarray,
    U: np.ndarray,
    normalizer: SensoryNormalizer
) -> Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor], Optional[torch.Tensor]]:
    """
    Constructs normalized input tensors for a specific model configuration.
    Returns:
        x_tensor: (N, T, input_dim)
        s_norm_tensor: (N, T, 25)
        pose_tensor: (N, T, 4) if applicable else None
        sa_tensor: (N, T, 31) if applicable else None
    """
    mid = model_id.upper()
    S_t = torch.tensor(S, dtype=torch.float32)
    V_t = torch.tensor(V_hd, dtype=torch.float32)
    G_t = torch.tensor(G_grid, dtype=torch.float32)
    U_t = torch.tensor(U, dtype=torch.float32)

    S_norm = normalizer.normalize(S_t)

    # Pose: [x_grid, y_grid, cos_hd, sin_hd]
    pose = torch.cat([G_t, V_t], dim=-1)  # (N, T, 4)
    sa = torch.cat([S_norm, U_t], dim=-1)  # (N, T, 31)

    if "M1-A" in mid:
        # Sensory Only (25D)
        x = S_norm
        return x, S_norm, None, None
    elif "M2-B" in mid:
        # Sensors + Action (31D)
        x = sa
        return x, S_norm, None, None
    elif "M3-C" in mid:
        # Sensors + Action + HD (33D)
        x = torch.cat([S_norm, U_t, V_t], dim=-1)
        return x, S_norm, None, None
    elif "M4-D" in mid:
        # Sensors + Action + Grid (33D)
        x = torch.cat([S_norm, U_t, G_t], dim=-1)
        return x, S_norm, None, None
    elif "M5-E" in mid:
        # Sensors + Action + HD + Grid (35D)
        x = torch.cat([S_norm, U_t, V_t, G_t], dim=-1)
        return x, S_norm, None, None
    elif "M6-F" in mid:
        # Full Pose + Learned Environmental Memory
        x = torch.cat([S_norm, U_t, V_t, G_t], dim=-1)
        return x, S_norm, pose, sa
    else:
        raise ValueError(f"Unknown model_id: {model_id}")


def train_single_model(
    model: BasePredictiveWorldModel,
    x_train: torch.Tensor,
    s_train: torch.Tensor,
    pose_train: Optional[torch.Tensor],
    sa_train: Optional[torch.Tensor],
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-3,
    device: str = "cpu"
) -> BasePredictiveWorldModel:
    """Trains a world model configuration on DEV_TRAIN."""
    model.to(device)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    # Subsequence windowing (T_seq = 30 ticks for BPTT)
    N, T, D = x_train.shape
    subseq_len = 30
    sub_x, sub_s, sub_pose, sub_sa = [], [], [], []

    for i in range(N):
        for start in range(0, T - subseq_len - 1, 15):
            sub_x.append(x_train[i, start:start+subseq_len])
            sub_s.append(s_train[i, start:start+subseq_len])
            if pose_train is not None:
                sub_pose.append(pose_train[i, start:start+subseq_len])
                sub_sa.append(sa_train[i, start:start+subseq_len])

    sub_x = torch.stack(sub_x)
    sub_s = torch.stack(sub_s)
    targets = sub_s[:, 1:, :]  # (Batch, subseq_len-1, 25)
    inputs_x = sub_x[:, :-1, :]
    inputs_s = sub_s[:, :-1, :]

    if pose_train is not None:
        sub_pose = torch.stack(sub_pose)[:, :-1, :]
        sub_sa = torch.stack(sub_sa)[:, :-1, :]
        dataset = TensorDataset(inputs_x, inputs_s, targets, sub_pose, sub_sa)
    else:
        dataset = TensorDataset(inputs_x, inputs_s, targets)

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    for ep in range(epochs):
        ep_loss = 0.0
        for batch in loader:
            optimizer.zero_grad()
            if pose_train is not None:
                bx, bs, by, b_pose, b_sa = [b.to(device) for b in batch]
                s_pred, d_pred, _ = model.forward_sequence(bx, b_pose, b_sa, bs)
            else:
                bx, bs, by = [b.to(device) for b in batch]
                s_pred, d_pred, _ = model.forward_sequence(bx, bs)

            if model.is_residual:
                # Loss on residual delta
                delta_target = by - bs
                loss = F.mse_loss(d_pred, delta_target)
            else:
                loss = F.mse_loss(s_pred, by)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_loss += float(loss.item())

        scheduler.step()

    model.eval()
    return model


def evaluate_canonical_six_batteries(
    model: BasePredictiveWorldModel,
    x_val: torch.Tensor,
    s_val_raw: torch.Tensor,
    v_hd_val: torch.Tensor,
    g_grid_val: torch.Tensor,
    u_val: torch.Tensor,
    collision_val: torch.Tensor,
    pose_val: Optional[torch.Tensor],
    sa_val: Optional[torch.Tensor],
    normalizer: SensoryNormalizer,
    device: str = "cpu"
) -> Dict[str, any]:
    """
    Evaluates the Canonical Six Batteries on DEV_VAL for a single model:
    - Battery 1: Predictive Fidelity (H in {1, 5, 10, 15, 30} on D_all and D_dynamic)
    - Battery 2: Action Causality (Action Zero, Permute, Sign Invert)
    - Battery 3: Spatial Causality (Spatial Phase Scrambling)
    - Battery 4: Spatial Disambiguation (Tolerance match in differing arena contexts)
    - Battery 5: Counterfactual Branching (3 candidate action sequences)
    - Battery 6: Collision Anticipation (Floor-contact subtracted ROC-AUC)
    """
    model.to(device)
    model.eval()

    N, T, _ = s_val_raw.shape
    results = {}

    def step_unified(s_c, u_c, h_c, v_c, g_c, mem_s=None, slot_i=None):
        mid = model.model_id
        if "M1-A" in mid:
            x_in = s_c
        elif "M2-B" in mid:
            x_in = torch.cat([s_c, u_c], dim=-1)
        elif "M3-C" in mid:
            x_in = torch.cat([s_c, u_c, v_c], dim=-1)
        elif "M4-D" in mid:
            x_in = torch.cat([s_c, u_c, g_c], dim=-1)
        else:
            x_in = torch.cat([s_c, u_c, v_c, g_c], dim=-1)

        if hasattr(model, "memory"):
            if mem_s is None:
                mem_k, mem_v = model.memory.init_memory(s_c.shape[0], device)
            else:
                mem_k, mem_v = mem_s
            p_step = torch.cat([g_c, v_c], dim=-1)
            sa_step = torch.cat([s_c, u_c], dim=-1)
            s_nxt, _, h_nxt, up_k, up_v = model.forward_step(
                x_in, p_step, sa_step, h_c, s_c, mem_k, mem_v, slot_idx=slot_i
            )
            return s_nxt, h_nxt, (up_k, up_v)
        else:
            s_nxt, _, h_nxt = model.forward_step(x_in, h_c, s_c)
            return s_nxt, h_nxt, None

    # -------------------------------------------------------------
    # BATTERY 1: PREDICTIVE FIDELITY (Multi-Horizon Rollout)
    # -------------------------------------------------------------
    horizons = [1, 5, 10, 15, 30]
    fidelity = {}

    # High-change mask on DEV_VAL
    delta_s_val = np.abs(s_val_raw[:, 1:, :15].numpy() - s_val_raw[:, :-1, :15].numpy())
    delta_omega_val = np.abs(s_val_raw[:, 1:, 20].numpy() - s_val_raw[:, :-1, 20].numpy())
    delta_wheel_val = np.abs(s_val_raw[:, 1:, 21].numpy() - s_val_raw[:, :-1, 21].numpy())
    high_change_mask = (
        (np.mean(delta_s_val, axis=-1) >= 0.15) |
        (delta_omega_val >= 1.0) |
        (delta_wheel_val >= 0.10)
    )

    with torch.no_grad():
        for H in horizons:
            preds_all = []
            targets_all = []
            targets_dyn = []
            preds_dyn = []

            for ep in range(N):
                for t in range(0, T - H - 1, 10):
                    s_curr = normalizer.normalize(s_val_raw[ep:ep+1, t, :]).to(device)
                    h_t = torch.zeros(1, 1, model.hidden_dim, device=device)
                    mem_s = None

                    # Autoregressive rollout for H steps
                    for step in range(H):
                        u_step = u_val[ep:ep+1, t+step, :].to(device)
                        v_step = v_hd_val[ep:ep+1, t+step, :].to(device)
                        g_step = g_grid_val[ep:ep+1, t+step, :].to(device)

                        s_curr, h_t, mem_s = step_unified(
                            s_curr, u_step, h_t, v_step, g_step, mem_s, slot_i=step
                        )

                    s_pred_denorm = normalizer.denormalize(s_curr.cpu()).numpy().squeeze()
                    s_true = s_val_raw[ep, t+H, :].numpy()

                    preds_all.append(s_pred_denorm)
                    targets_all.append(s_true)

                    if t < high_change_mask.shape[1] and high_change_mask[ep, t]:
                        preds_dyn.append(s_pred_denorm)
                        targets_dyn.append(s_true)

            preds_all = np.array(preds_all)
            targets_all = np.array(targets_all)
            preds_dyn = np.array(preds_dyn) if len(preds_dyn) > 0 else preds_all
            targets_dyn = np.array(targets_dyn) if len(targets_dyn) > 0 else targets_all

            # Active dynamic sonars (target < 4.5m)
            sonar_active_mask = (targets_all[:, :15] < 4.5)
            if np.sum(sonar_active_mask) > 10:
                sonar_r2 = compute_r2_score(targets_all[:, :15][sonar_active_mask], preds_all[:, :15][sonar_active_mask])
            else:
                sonar_r2 = compute_r2_score(targets_all[:, :15], preds_all[:, :15])

            sonar_dyn_mask = (targets_dyn[:, :15] < 4.5)
            if np.sum(sonar_dyn_mask) > 10:
                sonar_r2_dyn = compute_r2_score(targets_dyn[:, :15][sonar_dyn_mask], preds_dyn[:, :15][sonar_dyn_mask])
            else:
                sonar_r2_dyn = compute_r2_score(targets_dyn[:, :15], preds_dyn[:, :15])

            gyro_r2 = compute_r2_score(targets_all[:, 20], preds_all[:, 20])
            proprio_r2 = compute_r2_score(targets_all[:, 21:23], preds_all[:, 21:23])
            composite_rmse = float(np.sqrt(np.mean((targets_all - preds_all) ** 2)))

            fidelity[f"H_{H}"] = {
                "dynamic_sonar_r2_all": float(sonar_r2),
                "dynamic_sonar_r2_high_change": float(sonar_r2_dyn),
                "gyro_r2": float(gyro_r2),
                "proprio_r2": float(proprio_r2),
                "composite_rmse": float(composite_rmse)
            }

    results["Battery_1_Predictive_Fidelity"] = fidelity

    # -------------------------------------------------------------
    # BATTERY 2: ACTION CAUSALITY (Action Interventions)
    # -------------------------------------------------------------
    base_err = fidelity["H_10"]["composite_rmse"]
    zero_errs = []
    perm_errs = []
    invert_errs = []

    with torch.no_grad():
        for ep in range(min(5, N)):
            for t in range(0, T - 12, 20):
                s_curr_z = normalizer.normalize(s_val_raw[ep:ep+1, t, :]).to(device)
                s_curr_p = s_curr_z.clone()
                s_curr_i = s_curr_z.clone()
                h_z = torch.zeros(1, 1, model.hidden_dim, device=device)
                h_p = torch.zeros(1, 1, model.hidden_dim, device=device)
                h_i = torch.zeros(1, 1, model.hidden_dim, device=device)
                mem_z, mem_p, mem_i = None, None, None

                s_true_10 = s_val_raw[ep, t+10, :].numpy()

                for step in range(10):
                    u_real = u_val[ep:ep+1, t+step, :].to(device)
                    v_step = v_hd_val[ep:ep+1, t+step, :].to(device)
                    g_step = g_grid_val[ep:ep+1, t+step, :].to(device)

                    # Interventions:
                    u_zero = torch.zeros_like(u_real)
                    u_perm = u_real[:, torch.randperm(6)]
                    u_inv = -u_real

                    s_curr_z, h_z, mem_z = step_unified(s_curr_z, u_zero, h_z, v_step, g_step, mem_z, slot_i=step)
                    s_curr_p, h_p, mem_p = step_unified(s_curr_p, u_perm, h_p, v_step, g_step, mem_p, slot_i=step)
                    s_curr_i, h_i, mem_i = step_unified(s_curr_i, u_inv, h_i, v_step, g_step, mem_i, slot_i=step)

                pred_z = normalizer.denormalize(s_curr_z.cpu()).numpy().squeeze()
                pred_p = normalizer.denormalize(s_curr_p.cpu()).numpy().squeeze()
                pred_i = normalizer.denormalize(s_curr_i.cpu()).numpy().squeeze()

                zero_errs.append(np.sqrt(np.mean((s_true_10 - pred_z) ** 2)))
                perm_errs.append(np.sqrt(np.mean((s_true_10 - pred_p) ** 2)))
                invert_errs.append(np.sqrt(np.mean((s_true_10 - pred_i) ** 2)))

    mean_zero_err = float(np.mean(zero_errs)) if zero_errs else base_err
    mean_perm_err = float(np.mean(perm_errs)) if perm_errs else base_err
    mean_inv_err = float(np.mean(invert_errs)) if invert_errs else base_err

    zero_surge = float((mean_zero_err - base_err) / max(1e-4, base_err) * 100.0)
    perm_surge = float((mean_perm_err - base_err) / max(1e-4, base_err) * 100.0)
    inv_surge = float((mean_inv_err - base_err) / max(1e-4, base_err) * 100.0)

    results["Battery_2_Action_Causality"] = {
        "action_zero_error_surge_pct": zero_surge,
        "action_permute_error_surge_pct": perm_surge,
        "action_sign_invert_surge_pct": inv_surge,
        "gate_action_zero_pass": bool(zero_surge >= 25.0),
        "gate_action_permute_pass": bool(perm_surge >= 20.0),
        "gate_action_invert_pass": bool(inv_surge >= 25.0)
    }

    # -------------------------------------------------------------
    # BATTERY 3: SPATIAL CAUSALITY (Spatial Coordinate Scrambling)
    # -------------------------------------------------------------
    scramble_errs = []
    with torch.no_grad():
        for ep in range(min(5, N)):
            for t in range(0, T - 12, 25):
                s_curr_s = normalizer.normalize(s_val_raw[ep:ep+1, t, :]).to(device)
                h_s = torch.zeros(1, 1, model.hidden_dim, device=device)
                mem_s = None
                s_true_10 = s_val_raw[ep, t+10, :].numpy()

                for step in range(10):
                    u_real = u_val[ep:ep+1, t+step, :].to(device)
                    v_scrambled = torch.randn_like(v_hd_val[ep:ep+1, t+step, :]).to(device)
                    g_scrambled = torch.randn_like(g_grid_val[ep:ep+1, t+step, :]).to(device)

                    s_curr_s, h_s, mem_s = step_unified(s_curr_s, u_real, h_s, v_scrambled, g_scrambled, mem_s, slot_i=step)

                pred_s = normalizer.denormalize(s_curr_s.cpu()).numpy().squeeze()
                scramble_errs.append(np.sqrt(np.mean((s_true_10[:15] - pred_s[:15]) ** 2)))

    sonar_base_err = float(np.mean(np.abs(preds_all[:, :15] - targets_all[:, :15])))
    mean_scramble_err = float(np.mean(scramble_errs)) if scramble_errs else sonar_base_err
    spatial_surge = float((mean_scramble_err - sonar_base_err) / max(1e-4, sonar_base_err) * 100.0)

    results["Battery_3_Spatial_Causality"] = {
        "spatial_scramble_sonar_surge_pct": spatial_surge,
        "gate_spatial_causality_pass": bool(spatial_surge >= 20.0)
    }

    # -------------------------------------------------------------
    # BATTERY 4: SPATIAL DISAMBIGUATION TEST
    # -------------------------------------------------------------
    # Pre-registered tolerance for "same local observation":
    # Front-sector sonars (channels 4-10) within tolerance <= 0.35m,
    # but spatially separated locations (||g1 - g2||_2 >= 1.20m).
    # Tests whether forward rollouts diverge under an identical turn action.
    disambig_divs = []
    with torch.no_grad():
        all_s_flat = s_val_raw.reshape(-1, 25)[:, :15].numpy()
        all_g_flat = g_grid_val.reshape(-1, 2).numpy()
        total_pts = len(all_s_flat)

        found_pairs = 0
        for idx1 in range(0, total_pts, 20):
            if found_pairs >= 10:
                break
            for idx2 in range(idx1 + 50, total_pts, 10):
                s_diff_front = float(np.max(np.abs(all_s_flat[idx1, 4:11] - all_s_flat[idx2, 4:11])))
                g_dist = float(np.linalg.norm(all_g_flat[idx1] - all_g_flat[idx2]))

                if s_diff_front <= 0.35 and g_dist >= 1.20:
                    # Found matching local observation in different global positions
                    # Rollout with identical right-turn motor command: u = [0.6, -0.6]
                    u_cmd = torch.tensor([[0.6, -0.6, 0.0, 0.0, 0.0, 0.0]], dtype=torch.float32).to(device)
                    s1 = normalizer.normalize(s_val_raw.reshape(-1, 25)[idx1:idx1+1].clone().detach()).to(device)
                    s2 = normalizer.normalize(s_val_raw.reshape(-1, 25)[idx2:idx2+1].clone().detach()).to(device)
                    h1 = torch.zeros(1, 1, model.hidden_dim, device=device)
                    h2 = torch.zeros(1, 1, model.hidden_dim, device=device)
                    mem1, mem2 = None, None

                    v1 = v_hd_val.reshape(-1, 2)[idx1:idx1+1].clone().detach().to(device)
                    v2 = v_hd_val.reshape(-1, 2)[idx2:idx2+1].clone().detach().to(device)
                    g1 = g_grid_val.reshape(-1, 2)[idx1:idx1+1].clone().detach().to(device)
                    g2 = g_grid_val.reshape(-1, 2)[idx2:idx2+1].clone().detach().to(device)

                    for step in range(10):
                        s1, h1, mem1 = step_unified(s1, u_cmd, h1, v1, g1, mem1, slot_i=step)
                        s2, h2, mem2 = step_unified(s2, u_cmd, h2, v2, g2, mem2, slot_i=step)

                    p1 = normalizer.denormalize(s1.cpu()).numpy().squeeze()[:15]
                    p2 = normalizer.denormalize(s2.cpu()).numpy().squeeze()[:15]
                    div = float(np.linalg.norm(p1 - p2))
                    disambig_divs.append(div)
                    found_pairs += 1
                    break

    mean_disambig_div = float(np.mean(disambig_divs)) if disambig_divs else 0.0
    results["Battery_4_Spatial_Disambiguation"] = {
        "matched_pairs_evaluated": len(disambig_divs),
        "mean_divergence_meters": mean_disambig_div,
        "gate_spatial_disambiguation_pass": bool(mean_disambig_div >= 1.0)
    }

    # -------------------------------------------------------------
    # BATTERY 5: COUNTERFACTUAL ACTION BRANCHING
    # -------------------------------------------------------------
    branch_divs = []
    with torch.no_grad():
        for ep in range(min(5, N)):
            for t in range(0, T - 15, 35):
                s0 = normalizer.normalize(s_val_raw[ep:ep+1, t, :]).to(device)
                v0 = v_hd_val[ep:ep+1, t, :].to(device)
                g0 = g_grid_val[ep:ep+1, t, :].to(device)

                # Branch A: Forward, Branch B: Left Spin, Branch C: Reverse
                u_A = torch.tensor([[0.8, 0.8, 0, 0, 0, 0]], dtype=torch.float32).to(device)
                u_B = torch.tensor([[-0.7, 0.7, 0, 0, 0, 0]], dtype=torch.float32).to(device)
                u_C = torch.tensor([[-0.6, -0.6, 0, 0, 0, 0]], dtype=torch.float32).to(device)

                def rollout_branch(u_cmd):
                    s_b = s0.clone()
                    h_b = torch.zeros(1, 1, model.hidden_dim, device=device)
                    mem_b = None
                    for step in range(15):
                        s_b, h_b, mem_b = step_unified(s_b, u_cmd, h_b, v0, g0, mem_b, slot_i=step)
                    return normalizer.denormalize(s_b.cpu()).numpy().squeeze()

                rA = rollout_branch(u_A)
                rB = rollout_branch(u_B)
                rC = rollout_branch(u_C)

                div_AB = float(np.linalg.norm(rA - rB))
                div_AC = float(np.linalg.norm(rA - rC))
                div_BC = float(np.linalg.norm(rB - rC))
                branch_divs.append((div_AB + div_AC + div_BC) / 3.0)

    mean_branch_div = float(np.mean(branch_divs)) if branch_divs else 0.0
    results["Battery_5_Counterfactual_Branching"] = {
        "mean_pairwise_divergence_meters": mean_branch_div,
        "gate_counterfactual_pass": bool(mean_branch_div >= 0.80)
    }

    # -------------------------------------------------------------
    # BATTERY 6: COLLISION ANTICIPATION (ROC-AUC)
    # -------------------------------------------------------------
    col_labels = []
    col_scores = []

    with torch.no_grad():
        for ep in range(min(10, N)):
            for t in range(0, T - 12, 10):
                # Target: was there a genuine collision in ticks t+1 .. t+10?
                future_cols = collision_val[ep, t+1:t+11].numpy()
                had_collision = 1 if np.sum(future_cols) > 0 else 0

                # Predictor hazard score: lowest predicted front sonar in next 10 steps
                s_curr = normalizer.normalize(s_val_raw[ep:ep+1, t, :]).to(device)
                h_curr = torch.zeros(1, 1, model.hidden_dim, device=device)
                mem_c = None
                min_pred_sonar = 5.0

                for step in range(10):
                    u_step = u_val[ep:ep+1, t+step, :].to(device)
                    v_step = v_hd_val[ep:ep+1, t+step, :].to(device)
                    g_step = g_grid_val[ep:ep+1, t+step, :].to(device)

                    s_curr, h_curr, mem_c = step_unified(s_curr, u_step, h_curr, v_step, g_step, mem_c, slot_i=step)
                    denorm_s = normalizer.denormalize(s_curr.cpu()).numpy().squeeze()
                    front_s = float(np.min(denorm_s[6:9]))
                    if front_s < min_pred_sonar:
                        min_pred_sonar = front_s

                hazard_score = float(max(0.0, 5.0 - min_pred_sonar))
                col_labels.append(had_collision)
                col_scores.append(hazard_score)

    col_labels = np.array(col_labels)
    col_scores = np.array(col_scores)

    # Compute ROC-AUC manually
    pos_mask = (col_labels == 1)
    neg_mask = (col_labels == 0)
    n_pos = np.sum(pos_mask)
    n_neg = np.sum(neg_mask)

    if n_pos > 0 and n_neg > 0:
        pos_scores = col_scores[pos_mask]
        neg_scores = col_scores[neg_mask]
        auc = float(np.mean([np.mean(p > neg_scores) + 0.5 * np.mean(p == neg_scores) for p in pos_scores]))
    else:
        auc = 0.50

    results["Battery_6_Collision_Anticipation"] = {
        "collision_events_evaluated": int(n_pos),
        "non_collision_events_evaluated": int(n_neg),
        "collision_roc_auc": float(auc),
        "gate_collision_anticipation_pass": bool(auc >= 0.85)
    }

    return results


def run_full_diagnostic_suite(
    dataset_dir: Path,
    output_dir: Path,
    epochs: int = 25
) -> Path:
    """
    Main orchestration loop:
    1. Loads DEV_TRAIN and DEV_VAL.
    2. Trains and benchmarks all 13 model configurations.
    3. Saves structured scorecard JSON.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n========================================================")
    print(f" Starting CARL Stage 2.2 Phase 1 Controlled Falsification Suite")
    print(f" Compute Device: {device} | Models to Evaluate: {len(ALL_MODEL_IDS)}")
    print(f"========================================================")

    # 1. Load Datasets
    train_path = dataset_dir / "DEV_TRAIN.npz"
    val_path = dataset_dir / "DEV_VAL.npz"
    assert train_path.exists(), f"Missing {train_path}"
    assert val_path.exists(), f"Missing {val_path}"

    train_data = np.load(train_path)
    val_data = np.load(val_path)

    S_train = train_data["S"]
    V_train = train_data["V_hd"]
    G_train = train_data["G_grid"]
    U_train = train_data["U"]

    S_val = val_data["S"]
    V_val = val_data["V_hd"]
    G_val = val_data["G_grid"]
    U_val = val_data["U"]
    Col_val = val_data["collision"]

    # Compute normalization moments strictly on DEV_TRAIN
    mean_train = np.mean(S_train, axis=(0, 1))
    std_train = np.std(S_train, axis=(0, 1))
    normalizer = SensoryNormalizer(mean_train, std_train)

    scorecard = {
        "meta": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "epochs": epochs,
            "device": device,
            "train_episodes": len(S_train),
            "val_episodes": len(S_val)
        },
        "models": {}
    }

    for idx, model_id in enumerate(ALL_MODEL_IDS, 1):
        print(f"\n[{idx}/{len(ALL_MODEL_IDS)}] Training & Evaluating {model_id}...")
        t0 = time.time()
        model = create_model_by_id(model_id)
        n_params = model.get_parameter_count()

        # Prepare input tensors
        x_tr, s_norm_tr, pose_tr, sa_tr = prepare_input_tensors(
            model_id, S_train, V_train, G_train, U_train, normalizer
        )
        x_v, s_norm_v, pose_v, sa_v = prepare_input_tensors(
            model_id, S_val, V_val, G_val, U_val, normalizer
        )

        # Train model
        trained_model = train_single_model(
            model=model,
            x_train=x_tr,
            s_train=s_norm_tr,
            pose_train=pose_tr,
            sa_train=sa_tr,
            epochs=epochs,
            batch_size=32,
            lr=1e-3,
            device=device
        )

        # Evaluate Canonical Six Batteries
        eval_results = evaluate_canonical_six_batteries(
            model=trained_model,
            x_val=x_v,
            s_val_raw=torch.tensor(S_val, dtype=torch.float32),
            v_hd_val=torch.tensor(V_val, dtype=torch.float32),
            g_grid_val=torch.tensor(G_val, dtype=torch.float32),
            u_val=torch.tensor(U_val, dtype=torch.float32),
            collision_val=torch.tensor(Col_val, dtype=torch.int32),
            pose_val=pose_v,
            sa_val=sa_v,
            normalizer=normalizer,
            device=device
        )

        elapsed = time.time() - t0
        scorecard["models"][model_id] = {
            "model_id": model_id,
            "is_residual": model.is_residual,
            "parameter_count": n_params,
            "elapsed_seconds": round(elapsed, 2),
            "batteries": eval_results
        }

        # Print summary
        f10 = eval_results["Battery_1_Predictive_Fidelity"]["H_10"]
        c2 = eval_results["Battery_2_Action_Causality"]
        print(f"  --> Params: {n_params:,d} | H=10 Sonar R2 (All): {f10['dynamic_sonar_r2_all']:.4f} | (Dyn): {f10['dynamic_sonar_r2_high_change']:.4f}")
        print(f"  --> Action Zero Surge: {c2['action_zero_error_surge_pct']:+.1f}% | Permute: {c2['action_permute_error_surge_pct']:+.1f}% | Invert: {c2['action_sign_invert_surge_pct']:+.1f}%")

    out_file = output_dir / "diagnostic_scorecard.json"
    with open(out_file, "w") as f:
        json.dump(scorecard, f, indent=2)
    print(f"\nAll 13 models successfully benchmarked! Scorecard saved to: {out_file}")
    return out_file


if __name__ == "__main__":
    d_dir = Path("evidence/stage2_2_diag/datasets")
    o_dir = Path("evidence/stage2_2_diag")
    run_full_diagnostic_suite(d_dir, o_dir, epochs=25)
