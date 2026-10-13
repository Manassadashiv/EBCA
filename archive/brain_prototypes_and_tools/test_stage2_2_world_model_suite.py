"""
brain/test_stage2_2_world_model_suite.py — Master Adversarial Verification Suite (Stage 2.2)
Classification: [ADVERSARIAL VERIFICATION] Strict Post-Freeze Falsification Battery

Evaluates the frozen Action-Conditioned Recurrent World Model on PRIMARY_UNSEEN_TEST (Seeds 303, 404, 505, 606, 707):
- Gate 2.2A: Multi-Step Prediction Fidelity (H=1, 5, 10, 15, 30) with Sonar Dynamic (< 4.5m) filter
- Gate 2.2B: Counterfactual Collision Anticipation (250 randomized obstacle trials, ROC-AUC >= 0.88)
- Gate 2.2C: Traction / Friction Grounding Invariance (25-step rollout conditioned on 5-tick slip window)
- Gate 2.2D: Long-Horizon Autoregressive Stability (H=30, log-linear slope beta <= 0.06)
- Baseline Comparisons: Paired Wilcoxon signed-rank test (N=25 episodes, p < 0.01, d >= 0.50)
- Causal Ablations: Action-Zero, Recurrent-Zero, Action-Shuffle, Channel-Shuffle (> 30% degradation)

Outputs complete unrounded telemetry to evidence/stage2_2/stage2_2_scorecard.json
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
from scipy import stats

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
from brain.carl_stage2_2_world_model import (
    CarlStage2WorldModel,
    SensoryNormalizer,
    NaivePersistencePredictor,
    LinearActionPredictor
)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot < 1e-8:
        return 1.0 if ss_res < 1e-8 else 0.0
    return float(1.0 - (ss_res / ss_tot))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


class Stage2_2MasterTestSuite:
    def __init__(self, checkpoints_dir: Path, datasets_dir: Path, evidence_dir: Path):
        self.checkpoints_dir = checkpoints_dir
        self.datasets_dir = datasets_dir
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load Frozen Normalization Statistics
        norm_path = checkpoints_dir / "stage2_2_norm_stats.npz"
        assert norm_path.exists(), f"Missing {norm_path}"
        norm_data = np.load(norm_path)
        self.mu = norm_data["mu"]
        self.sigma = norm_data["sigma"]
        self.normalizer = SensoryNormalizer(self.mu, self.sigma)

        # 2. Load Frozen Model Checkpoint
        model_path = checkpoints_dir / "carl_stage2_2_world_model_frozen.pt"
        assert model_path.exists(), f"Missing {model_path}"
        self.model_path = model_path
        self.model_hash = compute_sha256(model_path)

        ckpt = torch.load(model_path, map_location="cpu")
        self.model = CarlStage2WorldModel(hidden_dim=ckpt["hidden_dim"], dt=ckpt["dt"])
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad = False

        # 3. Load Linear Baseline Weights
        linear_weights_path = checkpoints_dir / "stage2_2_linear_weights.npy"
        assert linear_weights_path.exists(), f"Missing {linear_weights_path}"
        self.linear_baseline = LinearActionPredictor()
        self.linear_baseline.W = np.load(linear_weights_path)
        self.persistence_baseline = NaivePersistencePredictor()

        # Unseen Test Partition
        self.test_seeds = [303, 404, 505, 606, 707]
        self.dt = 0.030

    def assert_model_integrity(self):
        """Asserts parameter hash is invariant."""
        current_hash = compute_sha256(self.model_path)
        assert current_hash == self.model_hash, "MODEL MUTATION DETECTED! Hard Freeze Violated."

    def evaluate_gate_2_2a_multistep(self, S_all: np.ndarray, V_hd_all: np.ndarray, U_all: np.ndarray) -> Dict[str, Any]:
        """
        Gate 2.2A: Multi-step prediction fidelity (H=1, 5, 10, 15, 30).
        Evaluates Gyro, Sonar Dynamic (< 4.5m), Proprioception, and Composite Active 24-D.
        """
        print("\n" + "=" * 60)
        print("RUNNING GATE 2.2A: MULTI-STEP PREDICTION BENCHMARK")
        print("=" * 60)

        horizons = [1, 5, 10, 15, 30]
        results = {}
        N_episodes, T, _ = S_all.shape

        for H in horizons:
            all_true_s = []
            all_pred_s = []

            for ep in range(N_episodes):
                s_ep = S_all[ep]        # (T, 25)
                v_ep = V_hd_all[ep]    # (T, 2)
                u_ep = U_all[ep]       # (T, 6)

                # Rollout every H steps
                for t in range(0, T - H, H):
                    h0 = torch.zeros(1, 1, self.model.hidden_dim)
                    s0 = torch.from_numpy(s_ep[t:t+1])
                    v0 = torch.from_numpy(v_ep[t:t+1])
                    u_seq = torch.from_numpy(u_ep[t:t+H]).unsqueeze(0)

                    with torch.no_grad():
                        s_pred, _, _ = self.model.rollout_mental_trajectory(
                            h0, s0, v0, u_seq, self.normalizer
                        )

                    all_true_s.append(s_ep[t+1:t+H+1])
                    all_pred_s.append(s_pred.squeeze(0).numpy())

            y_true = np.concatenate(all_true_s, axis=0)  # (N_steps, 25)
            y_pred = np.concatenate(all_pred_s, axis=0)  # (N_steps, 25)

            # 1. Gyro (channels 18, 19, 20)
            gyro_true = y_true[:, 18:21]
            gyro_pred = y_pred[:, 18:21]
            r2_gyro = compute_r2(gyro_true, gyro_pred)
            rmse_gyro = compute_rmse(gyro_true, gyro_pred)

            # 2. Sonar (channels 0:15) — All vs Dynamic (< 4.5m)
            sonar_true = y_true[:, :15]
            sonar_pred = y_pred[:, :15]
            r2_sonar_all = compute_r2(sonar_true, sonar_pred)
            rmse_sonar_all = compute_rmse(sonar_true, sonar_pred)

            # Dynamic Sonar Filter (< 4.5m)
            dyn_mask = (sonar_true < 4.5)
            if np.sum(dyn_mask) > 100:
                r2_sonar_dyn = compute_r2(sonar_true[dyn_mask], sonar_pred[dyn_mask])
                rmse_sonar_dyn = compute_rmse(sonar_true[dyn_mask], sonar_pred[dyn_mask])
            else:
                r2_sonar_dyn = r2_sonar_all
                rmse_sonar_dyn = rmse_sonar_all

            # 3. Proprioception (channels 21:24)
            proprio_true = y_true[:, 21:24]
            proprio_pred = y_pred[:, 21:24]
            r2_proprio = compute_r2(proprio_true, proprio_pred)
            rmse_proprio = compute_rmse(proprio_true, proprio_pred)

            # 4. Quiescent Battery (channel 24)
            batt_true = y_true[:, 24]
            batt_pred = y_pred[:, 24]
            mae_batt = compute_mae(batt_true, batt_pred)
            rmse_batt = compute_rmse(batt_true, batt_pred)

            # 5. Composite Active 24-D
            r2_comp = compute_r2(y_true[:, :24], y_pred[:, :24])
            rmse_comp = compute_rmse(y_true[:, :24], y_pred[:, :24])

            results[f"H_{H}"] = {
                "horizon": H,
                "r2_gyro": r2_gyro,
                "rmse_gyro": rmse_gyro,
                "r2_sonar_dynamic": r2_sonar_dyn,
                "rmse_sonar_dynamic": rmse_sonar_dyn,
                "r2_sonar_all": r2_sonar_all,
                "rmse_sonar_all": rmse_sonar_all,
                "r2_proprio": r2_proprio,
                "rmse_proprio": rmse_proprio,
                "mae_battery": mae_batt,
                "rmse_battery": rmse_batt,
                "r2_composite_24d": r2_comp,
                "rmse_composite_24d": rmse_comp
            }

            print(f"Horizon H={H:2d} | Gyro R2: {r2_gyro:.4f} | Sonar Dyn R2: {r2_sonar_dyn:.4f} | Proprio R2: {r2_proprio:.4f} | Comp R2: {r2_comp:.4f}")

        # Evaluate Pre-Registered Gate Criteria at H=10
        h10 = results["H_10"]
        pass_gyro = (h10["r2_gyro"] >= 0.70)
        pass_sonar = (h10["r2_sonar_dynamic"] >= 0.60)
        pass_proprio = (h10["r2_proprio"] >= 0.80)
        pass_composite = (h10["r2_composite_24d"] >= 0.65)
        gate_passed = pass_gyro and pass_sonar and pass_proprio and pass_composite

        results["gate_passed"] = bool(gate_passed)
        results["checks"] = {
            "gyro_ge_0_70": bool(pass_gyro),
            "sonar_dyn_ge_0_60": bool(pass_sonar),
            "proprio_ge_0_80": bool(pass_proprio),
            "composite_ge_0_65": bool(pass_composite)
        }
        print(f"\nGATE 2.2A STATUS: {'PASS' if gate_passed else 'FAIL'}")
        return results

    def evaluate_gate_2_2b_collision(self) -> Dict[str, Any]:
        """
        Gate 2.2B: Counterfactual Collision Anticipation across 250 randomized obstacle trials.
        Evaluates Proposal A (Collide: fwd=0.6) vs Proposal B (Evade: turn=0.7).
        Computes ROC-AUC and PR-AUC without leaking future state.
        """
        print("\n" + "=" * 60)
        print("RUNNING GATE 2.2B: COUNTERFACTUAL COLLISION BENCHMARK (250 TRIALS)")
        print("=" * 60)

        hal = CarlStage1HAL(open_space=False)
        trials_per_seed = 50
        all_pred_min_dist = []
        all_actual_collisions = []

        total_trials = len(self.test_seeds) * trials_per_seed
        trial_count = 0

        for seed in self.test_seeds:
            for t_idx in range(trials_per_seed):
                trial_rng = np.random.RandomState(seed * 5000 + t_idx)

                # Randomize distance to wall d0 in [0.25, 0.65] and angle offset [-60 deg, +60 deg]
                d0 = trial_rng.uniform(0.25, 0.65)
                heading_offset = trial_rng.uniform(-math.pi / 3.0, math.pi / 3.0)

                hal.reset()
                hal.set_floor_friction(1.0)

                # Align robot facing toward wall at distance d0
                # Robot spawns near origin, drive toward front arena wall (x=2.0)
                # Position x = 2.0 - d0, y in [-1.0, 1.0]
                y_pos = trial_rng.uniform(-0.8, 0.8)
                x_pos = 2.0 - d0
                yaw = heading_offset

                qa = int(hal.model.joint("spatial_identity").qposadr[0])
                hal.data.qpos[qa: qa + 2] = [x_pos, y_pos]
                # Set quaternion yaw
                hal.data.qpos[qa + 3: qa + 7] = [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]
                import mujoco
                mujoco.mj_forward(hal.model, hal.data)

                # Collect initial state
                s0 = hal.read_sensors()
                v_hd0 = np.array([math.cos(yaw), math.sin(yaw)], dtype=np.float32)

                # Test Branch A (Collide: forward drive burst for 20 ticks)
                # Test Branch B (Evade: pure turn in place for 20 ticks)
                branch = "A" if (t_idx % 2 == 0) else "B"

                if branch == "A":
                    u_proposal = np.zeros((20, 6), dtype=np.float32)
                    u_proposal[:, 0] = 0.6
                    u_proposal[:, 1] = 0.6
                else:
                    u_proposal = np.zeros((20, 6), dtype=np.float32)
                    u_proposal[:, 0] = -0.7
                    u_proposal[:, 1] = 0.7

                # 1. Mental Forward Rollout (Pure Neural, ZERO MuJoCo queries)
                h0 = torch.zeros(1, 1, self.model.hidden_dim)
                s0_t = torch.from_numpy(s0).unsqueeze(0).float()
                v0_t = torch.from_numpy(v_hd0).unsqueeze(0).float()
                u_seq_t = torch.from_numpy(u_proposal).unsqueeze(0).float()

                with torch.no_grad():
                    s_pred_seq, _, _ = self.model.rollout_mental_trajectory(
                        h0, s0_t, v0_t, u_seq_t, self.normalizer
                    )

                # Front sonar is channel 7 (center ray)
                pred_sonars = s_pred_seq[0, :15, :15].numpy()
                pred_front_min = float(np.min(pred_sonars[:, 7]))
                # Predicted collision risk score: 1.0 / (pred_front_min + 0.01)
                risk_score = float(1.0 - (pred_front_min / 5.0))
                all_pred_min_dist.append(risk_score)

                # 2. Physical Execution Ground Truth
                collided = False
                for step_k in range(20):
                    hal.step(u_proposal[step_k])
                    contacts = hal.get_carl_contact_info()
                    if contacts["carl_contacts"] > 0:
                        collided = True
                        break
                    s_step = hal.read_sensors()
                    if np.min(s_step[:15]) < 0.05:
                        collided = True
                        break

                all_actual_collisions.append(1 if collided else 0)
                trial_count += 1
                if trial_count % 50 == 0:
                    print(f"  [{trial_count}/{total_trials}] collision trials executed.")

        # Compute ROC-AUC and PR-AUC
        y_true_col = np.array(all_actual_collisions)
        y_scores = np.array(all_pred_min_dist)

        # ROC-AUC via rank-sum (Mann-Whitney U)
        pos = y_scores[y_true_col == 1]
        neg = y_scores[y_true_col == 0]

        if len(pos) > 0 and len(neg) > 0:
            u_stat, _ = stats.mannwhitneyu(pos, neg, alternative="greater")
            roc_auc = float(u_stat / (len(pos) * len(neg)))
        else:
            roc_auc = 0.5

        # Decision threshold at front sonar < 0.15m -> risk_score > 1.0 - 0.15/5.0 = 0.97
        pred_labels = (y_scores >= 0.90).astype(int)
        tp = np.sum((pred_labels == 1) & (y_true_col == 1))
        fp = np.sum((pred_labels == 1) & (y_true_col == 0))
        fn = np.sum((pred_labels == 0) & (y_true_col == 1))
        tn = np.sum((pred_labels == 0) & (y_true_col == 0))

        precision = float(tp / (tp + fp + 1e-9))
        recall = float(tp / (tp + fn + 1e-9))
        fpr = float(fp / (fp + tn + 1e-9))

        pass_auc = (roc_auc >= 0.88)
        gate_passed = pass_auc

        res = {
            "total_trials": total_trials,
            "actual_collisions": int(np.sum(y_true_col)),
            "actual_clearances": int(len(y_true_col) - np.sum(y_true_col)),
            "roc_auc": roc_auc,
            "precision": precision,
            "recall": recall,
            "false_positive_rate": fpr,
            "gate_passed": bool(gate_passed)
        }
        print(f"Gate 2.2B Results: ROC-AUC = {roc_auc:.4f} | Recall = {recall:.4f} | Precision = {precision:.4f} | FPR = {fpr:.4f}")
        print(f"GATE 2.2B STATUS: {'PASS' if gate_passed else 'FAIL'}")
        return res

    def evaluate_gate_2_2c_friction(self) -> Dict[str, Any]:
        """
        Gate 2.2C: Traction / Friction Grounding Invariance.
        Evaluates a 25-step forward rollout conditioned on a 5-tick observed slip window on glaze ice (mu=0.005).
        Predictor receives NO friction label. Must predict stationary sonars.
        """
        print("\n" + "=" * 60)
        print("RUNNING GATE 2.2C: FRICTION GROUNDING INVARIANCE (GLAZE ICE)")
        print("=" * 60)

        hal = CarlStage1HAL(open_space=False)
        seed_r2s = []

        for seed in self.test_seeds:
            hal.reset()
            hal.set_floor_friction(0.005)  # Glaze ice

            hd_ring = HeadDirectionRingAttractor(seed=seed, dt=self.dt)
            u_fwd = np.array([0.5, 0.5, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

            # 1. Mandatory 5-tick observed slip history window (150 ms)
            for _ in range(5):
                hal.step(u_fwd)
                s_obs = hal.read_sensors()
                hd_ring.step(float(s_obs[20]))

            # Current state at tick 5 on ice
            s_init = hal.read_sensors()
            theta_hd = hd_ring.decode_heading()
            v_hd_init = np.array([math.cos(theta_hd), math.sin(theta_hd)], dtype=np.float32)

            # 2. Mental Forward Rollout for 25 ticks (Pure Neural)
            h0 = torch.zeros(1, 1, self.model.hidden_dim)
            s0_t = torch.from_numpy(s_init).unsqueeze(0).float()
            v0_t = torch.from_numpy(v_hd_init).unsqueeze(0).float()
            u_seq = torch.from_numpy(np.repeat(u_fwd[np.newaxis, :], 25, axis=0)).unsqueeze(0).float()

            with torch.no_grad():
                s_pred_seq, _, _ = self.model.rollout_mental_trajectory(
                    h0, s0_t, v0_t, u_seq, self.normalizer
                )
            pred_sonars = s_pred_seq[0, :, :15].numpy()

            # 3. Physical Execution on Ice for 25 ticks
            actual_sonars = []
            for _ in range(25):
                hal.step(u_fwd)
                s_phys = hal.read_sensors()
                actual_sonars.append(s_phys[:15])

            actual_sonars = np.array(actual_sonars)
            r2_ice_seed = compute_r2(actual_sonars, pred_sonars)
            seed_r2s.append(r2_ice_seed)
            print(f"  Seed {seed} Ice Sonar R2: {r2_ice_seed:.4f}")

        mean_ice_r2 = float(np.mean(seed_r2s))
        pass_gate = (mean_ice_r2 >= 0.60)
        res = {
            "seed_r2s": seed_r2s,
            "mean_ice_r2": mean_ice_r2,
            "gate_passed": bool(pass_gate)
        }
        print(f"Gate 2.2C Mean Ice Sonar R2 = {mean_ice_r2:.4f} | Status: {'PASS' if pass_gate else 'FAIL'}")
        return res

    def evaluate_gate_2_2d_stability(self, S_all: np.ndarray, V_hd_all: np.ndarray, U_all: np.ndarray) -> Dict[str, Any]:
        """
        Gate 2.2D: Long-Horizon Autoregressive Stability (H=30).
        Evaluates error growth exponent beta <= 0.06 and zero NaNs/Infs.
        """
        print("\n" + "=" * 60)
        print("RUNNING GATE 2.2D: LONG-HORIZON AUTOREGRESSIVE STABILITY (H=30)")
        print("=" * 60)

        N_episodes, T, _ = S_all.shape
        H = 30
        horizon_rmses = []
        nan_count = 0
        bound_violations = 0

        for k_step in range(1, H + 1):
            step_errors = []
            for ep in range(N_episodes):
                s_ep = S_all[ep]
                v_ep = V_hd_all[ep]
                u_ep = U_all[ep]

                for t in range(0, T - H, H):
                    h0 = torch.zeros(1, 1, self.model.hidden_dim)
                    s0 = torch.from_numpy(s_ep[t:t+1])
                    v0 = torch.from_numpy(v_ep[t:t+1])
                    u_seq = torch.from_numpy(u_ep[t:t+k_step]).unsqueeze(0)

                    with torch.no_grad():
                        s_pred, _, _ = self.model.rollout_mental_trajectory(
                            h0, s0, v0, u_seq, self.normalizer
                        )
                    p_k = s_pred[0, -1, :].numpy()
                    y_k = s_ep[t + k_step]

                    if np.any(np.isnan(p_k)) or np.any(np.isinf(p_k)):
                        nan_count += 1
                    # Range check
                    if np.any(p_k[:15] < 0.0) or np.any(p_k[:15] > 5.0):
                        bound_violations += 1

                    step_errors.append((p_k[:24] - y_k[:24]) ** 2)

            rmse_k = float(np.sqrt(np.mean(step_errors)))
            horizon_rmses.append(rmse_k)

        # Fit log-linear model ln(RMSE_k) = alpha + beta * k
        x_horizons = np.arange(1, H + 1)
        ln_rmse = np.log(np.maximum(horizon_rmses, 1e-6))
        slope, intercept, r_val, p_val, std_err = stats.linregress(x_horizons, ln_rmse)

        rmse_ratio = float(horizon_rmses[-1] / (horizon_rmses[0] + 1e-9))
        pass_slope = (slope <= 0.06)
        pass_ratio = (rmse_ratio <= 3.5)
        pass_nans = (nan_count == 0) and (bound_violations == 0)

        gate_passed = pass_slope and pass_ratio and pass_nans
        res = {
            "horizon_rmses": horizon_rmses,
            "fitted_slope_beta": float(slope),
            "rmse_ratio_30_to_1": rmse_ratio,
            "nan_count": nan_count,
            "bound_violations": bound_violations,
            "gate_passed": bool(gate_passed)
        }
        print(f"Gate 2.2D: Error Growth Slope beta = {slope:.5f} (threshold <= 0.06) | Ratio RMSE30/1 = {rmse_ratio:.3f}")
        print(f"GATE 2.2D STATUS: {'PASS' if gate_passed else 'FAIL'}")
        return res

    def evaluate_baselines(self, S_all: np.ndarray, V_hd_all: np.ndarray, U_all: np.ndarray) -> Dict[str, Any]:
        """
        Mandatory Baseline Comparison: Persistence vs Linear vs Recurrent World Model.
        Paired Wilcoxon signed-rank test across N=25 episodes at H=10.
        """
        print("\n" + "=" * 60)
        print("RUNNING BASELINE COMPARISON (PAIRED WILCOXON N=25)")
        print("=" * 60)

        N_ep, T, _ = S_all.shape
        H = 10
        errors_wm = []
        errors_persist = []
        errors_linear = []

        for ep in range(N_ep):
            s_ep = S_all[ep]
            v_ep = V_hd_all[ep]
            u_ep = U_all[ep]

            ep_wm = []
            ep_p = []
            ep_l = []

            for t in range(0, T - H, H):
                s0 = s_ep[t]
                v0 = v_ep[t]
                u_seq = u_ep[t:t+H]
                target_seq = s_ep[t+1:t+H+1]

                # 1. World Model
                h0 = torch.zeros(1, 1, self.model.hidden_dim)
                s0_t = torch.from_numpy(s0).unsqueeze(0).float()
                v0_t = torch.from_numpy(v0).unsqueeze(0).float()
                u_t = torch.from_numpy(u_seq).unsqueeze(0).float()
                with torch.no_grad():
                    p_wm, _, _ = self.model.rollout_mental_trajectory(
                        h0, s0_t, v0_t, u_t, self.normalizer
                    )
                pred_wm = p_wm[0].numpy()

                # 2. Persistence
                pred_p = self.persistence_baseline.predict(s0, horizon=H)

                # 3. Linear Baseline
                pred_l = self.linear_baseline.predict(s0, v0, u_seq)

                ep_wm.append(np.mean((pred_wm[:, :24] - target_seq[:, :24])**2))
                ep_p.append(np.mean((pred_p[:, :24] - target_seq[:, :24])**2))
                ep_l.append(np.mean((pred_l[:, :24] - target_seq[:, :24])**2))

            errors_wm.append(float(np.sqrt(np.mean(ep_wm))))
            errors_persist.append(float(np.sqrt(np.mean(ep_p))))
            errors_linear.append(float(np.sqrt(np.mean(ep_l))))

        errors_wm = np.array(errors_wm)
        errors_persist = np.array(errors_persist)
        errors_linear = np.array(errors_linear)

        # Paired Wilcoxon Signed-Rank Tests (N=25)
        stat_p, p_val_p = stats.wilcoxon(errors_wm, errors_persist, alternative="less")
        stat_l, p_val_l = stats.wilcoxon(errors_wm, errors_linear, alternative="less")

        # Effect Size (Cohen's d on paired differences)
        diff_p = errors_persist - errors_wm
        d_persist = float(np.mean(diff_p) / (np.std(diff_p) + 1e-9))
        pct_imp_persist = float((np.mean(errors_persist) - np.mean(errors_wm)) / np.mean(errors_persist) * 100.0)

        diff_l = errors_linear - errors_wm
        d_linear = float(np.mean(diff_l) / (np.std(diff_l) + 1e-9))
        pct_imp_linear = float((np.mean(errors_linear) - np.mean(errors_wm)) / np.mean(errors_linear) * 100.0)

        pass_baselines = (p_val_p < 0.01) and (p_val_l < 0.01) and (pct_imp_persist >= 15.0) and (pct_imp_linear >= 15.0)

        res = {
            "mean_rmse_world_model": float(np.mean(errors_wm)),
            "mean_rmse_persistence": float(np.mean(errors_persist)),
            "mean_rmse_linear": float(np.mean(errors_linear)),
            "wilcoxon_p_vs_persistence": float(p_val_p),
            "wilcoxon_p_vs_linear": float(p_val_l),
            "cohens_d_vs_persistence": d_persist,
            "cohens_d_vs_linear": d_linear,
            "pct_improvement_vs_persistence": pct_imp_persist,
            "pct_improvement_vs_linear": pct_imp_linear,
            "gate_passed": bool(pass_baselines)
        }

        print(f"World Model RMSE: {res['mean_rmse_world_model']:.4f}")
        print(f"Persistence RMSE: {res['mean_rmse_persistence']:.4f} (p={p_val_p:.2e}, imp={pct_imp_persist:.1f}%)")
        print(f"Linear RMSE:      {res['mean_rmse_linear']:.4f} (p={p_val_l:.2e}, imp={pct_imp_linear:.1f}%)")
        print(f"BASELINE GATES:   {'PASS' if pass_baselines else 'FAIL'}")
        return res

    def evaluate_causal_ablations(self, S_all: np.ndarray, V_hd_all: np.ndarray, U_all: np.ndarray) -> Dict[str, Any]:
        """
        Causal Ablation Battery: Action-Zero, Recurrent-Zero, Action-Shuffle, Channel-Shuffle.
        Evaluates on identical episodes at H=10. Requires > 30% degradation.
        """
        print("\n" + "=" * 60)
        print("RUNNING CAUSAL ABLATION BATTERY (> 30% DEGRADATION REQUIRED)")
        print("=" * 60)

        N_ep, T, _ = S_all.shape
        H = 10
        baseline_errs = []
        act_zero_errs = []
        rec_zero_errs = []
        act_shuff_errs = []
        chan_shuff_errs = []

        perm_seed = 42
        rng = np.random.RandomState(perm_seed)
        perm_action = rng.permutation(H)
        perm_channels = rng.permutation(25)

        for ep in range(N_ep):
            s_ep = S_all[ep]
            v_ep = V_hd_all[ep]
            u_ep = U_all[ep]

            for t in range(0, T - H, H):
                s0 = s_ep[t]
                v0 = v_ep[t]
                u_seq = u_ep[t:t+H]
                target_seq = s_ep[t+1:t+H+1, :24]

                h0 = torch.zeros(1, 1, self.model.hidden_dim)
                s0_t = torch.from_numpy(s0).unsqueeze(0).float()
                v0_t = torch.from_numpy(v0).unsqueeze(0).float()
                u_t = torch.from_numpy(u_seq).unsqueeze(0).float()

                with torch.no_grad():
                    # 1. Intact Model
                    p_intact, _, _ = self.model.rollout_mental_trajectory(h0, s0_t, v0_t, u_t, self.normalizer)
                    baseline_errs.append(np.mean((p_intact[0, :, :24].numpy() - target_seq)**2))

                    # 2. Action Zeroed
                    u_zero = torch.zeros_like(u_t)
                    p_az, _, _ = self.model.rollout_mental_trajectory(h0, s0_t, v0_t, u_zero, self.normalizer)
                    act_zero_errs.append(np.mean((p_az[0, :, :24].numpy() - target_seq)**2))

                    # 3. Recurrent Zeroed (h0 clamped to 0 each step)
                    p_rz, _, _ = self.model.rollout_mental_trajectory(h0 * 0.0, s0_t, v0_t, u_t, self.normalizer)
                    # To test true zero-recurrent, zero hidden at every step
                    curr_s = s0_t
                    curr_v = v0_t
                    rz_preds = []
                    for k in range(H):
                        _, s_next = self.model.forward_step(h0 * 0.0, self.normalizer.normalize(curr_s), curr_v, u_t[:, k])
                        s_clamped = self.model.clamp_physical_bounds(self.normalizer.denormalize(s_next))
                        curr_s = s_clamped
                        rz_preds.append(curr_s.unsqueeze(1))
                    p_rz_full = torch.cat(rz_preds, dim=1)
                    rec_zero_errs.append(np.mean((p_rz_full[0, :, :24].numpy() - target_seq)**2))

                    # 4. Action Shuffled
                    u_shuff = u_t[:, perm_action, :]
                    p_as, _, _ = self.model.rollout_mental_trajectory(h0, s0_t, v0_t, u_shuff, self.normalizer)
                    act_shuff_errs.append(np.mean((p_as[0, :, :24].numpy() - target_seq)**2))

                    # 5. Channel Scrambled
                    s0_scrambled = s0_t[:, perm_channels]
                    p_cs, _, _ = self.model.rollout_mental_trajectory(h0, s0_scrambled, v0_t, u_t, self.normalizer)
                    chan_shuff_errs.append(np.mean((p_cs[0, :, :24].numpy() - target_seq)**2))

        rmse_intact = float(np.sqrt(np.mean(baseline_errs)))
        rmse_az = float(np.sqrt(np.mean(act_zero_errs)))
        rmse_rz = float(np.sqrt(np.mean(rec_zero_errs)))
        rmse_as = float(np.sqrt(np.mean(act_shuff_errs)))
        rmse_cs = float(np.sqrt(np.mean(chan_shuff_errs)))

        deg_az = float((rmse_az - rmse_intact) / rmse_intact * 100.0)
        deg_rz = float((rmse_rz - rmse_intact) / rmse_intact * 100.0)
        deg_as = float((rmse_as - rmse_intact) / rmse_intact * 100.0)
        deg_cs = float((rmse_cs - rmse_intact) / rmse_intact * 100.0)

        pass_ablations = (deg_az >= 30.0) and (deg_rz >= 30.0) and (deg_as >= 30.0) and (deg_cs >= 30.0)

        res = {
            "rmse_intact": rmse_intact,
            "rmse_action_zero": rmse_az,
            "degradation_action_zero_pct": deg_az,
            "rmse_recurrent_zero": rmse_rz,
            "degradation_recurrent_zero_pct": deg_rz,
            "rmse_action_shuffle": rmse_as,
            "degradation_action_shuffle_pct": deg_as,
            "rmse_channel_shuffle": rmse_cs,
            "degradation_channel_shuffle_pct": deg_cs,
            "gate_passed": bool(pass_ablations)
        }

        print(f"Intact Model RMSE: {rmse_intact:.4f}")
        print(f"Action Zeroed:     {rmse_az:.4f} (+{deg_az:.1f}% degradation)")
        print(f"Recurrent Zeroed:  {rmse_rz:.4f} (+{deg_rz:.1f}% degradation)")
        print(f"Action Shuffled:   {rmse_as:.4f} (+{deg_as:.1f}% degradation)")
        print(f"Channel Scrambled: {rmse_cs:.4f} (+{deg_cs:.1f}% degradation)")
        print(f"ABLATION GATES:    {'PASS' if pass_ablations else 'FAIL'}")
        return res

    def run_full_suite(self):
        print("\n" + "=" * 70)
        print("STAGE 2.2 MASTER ADVERSARIAL VERIFICATION SUITE")
        print("=" * 70)

        self.assert_model_integrity()

        # Load Primary Unseen Test Dataset
        test_dataset_path = self.datasets_dir / "unseen_test.npz"
        assert test_dataset_path.exists(), f"Missing {test_dataset_path}. Must generate at Step 8!"
        test_npz = np.load(test_dataset_path)
        S_all = test_npz["S"]
        V_hd_all = test_npz["V_hd"]
        U_all = test_npz["U"]

        scorecard = {
            "milestone": "Stage 2.2 Predictive World Model Official Evaluation",
            "model_file": str(self.model_path),
            "model_sha256": self.model_hash,
            "unseen_dataset_file": str(test_dataset_path),
            "unseen_dataset_sha256": compute_sha256(test_dataset_path),
            "unseen_seeds": self.test_seeds,
            "gates": {}
        }

        # 1. Gate 2.2A
        scorecard["gates"]["gate_2_2a"] = self.evaluate_gate_2_2a_multistep(S_all, V_hd_all, U_all)

        # 2. Gate 2.2B
        scorecard["gates"]["gate_2_2b"] = self.evaluate_gate_2_2b_collision()

        # 3. Gate 2.2C
        scorecard["gates"]["gate_2_2c"] = self.evaluate_gate_2_2c_friction()

        # 4. Gate 2.2D
        scorecard["gates"]["gate_2_2d"] = self.evaluate_gate_2_2d_stability(S_all, V_hd_all, U_all)

        # 5. Baseline Comparison
        scorecard["gates"]["baselines"] = self.evaluate_baselines(S_all, V_hd_all, U_all)

        # 6. Causal Ablations
        scorecard["gates"]["ablations"] = self.evaluate_causal_ablations(S_all, V_hd_all, U_all)

        # Check Final Model Integrity
        self.assert_model_integrity()

        # Overall Status
        all_passed = all(g.get("gate_passed", False) for g in scorecard["gates"].values())
        scorecard["overall_verdict"] = "PASS" if all_passed else "FAIL"

        scorecard_path = self.evidence_dir / "stage2_2_scorecard.json"
        with open(scorecard_path, "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2)

        print("\n" + "=" * 70)
        print(f"OFFICIAL SCORECARD SAVED TO: {scorecard_path}")
        print(f"OVERALL STAGE 2.2 VERDICT: {scorecard['overall_verdict']}")
        print("=" * 70)
        return scorecard


if __name__ == "__main__":
    suite = Stage2_2MasterTestSuite(
        checkpoints_dir=Path("checkpoints"),
        datasets_dir=Path("evidence/stage2_2/datasets"),
        evidence_dir=Path("evidence/stage2_2")
    )
    suite.run_full_suite()
