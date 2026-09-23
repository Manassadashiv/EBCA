"""
brain/test_stage2_2_robustness_battery.py — Grounded Spatial & Kinematic Robustness Battery
Classification: [STAGE 2.2 SCIENTIFIC CLOSURE] Robustness & Drift Quantification

Evaluates:
1. Dead-Reckoning Drift across T=50, T=100, T=200 ticks against ground truth physics.
2. Sensor Noise Perturbations (Gaussian noise sigma=0.02, 0.05 and 5% ray dropouts).
3. Graceful degradation quantification (no catastrophic failure under realistic noise).
"""

import sys
import json
import math
from pathlib import Path
import numpy as np
import torch

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.train_stage2_2_grounded_body_model import GroundedKinematicBodyModel
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
import mujoco

GROUNDED_CHECKPOINT = repo_root / "checkpoints" / "stage2_2_grounded" / "grounded_body_model.pt"
GROUNDED_GRID = repo_root / "evidence" / "stage2_2_grounded" / "grounded_occupancy_grid.pt"
EVIDENCE_DIR = repo_root / "evidence" / "stage2_2_grounded"


def run_robustness_battery():
    print("==================================================================", flush=True)
    print("STAGE 2.2 SCIENTIFIC CLOSURE: GROUNDED ROBUSTNESS BATTERY", flush=True)
    print("==================================================================", flush=True)

    assert GROUNDED_CHECKPOINT.exists(), f"Missing checkpoint: {GROUNDED_CHECKPOINT}"
    assert GROUNDED_GRID.exists(), f"Missing grid: {GROUNDED_GRID}"

    body_model = GroundedKinematicBodyModel()
    body_model.load_state_dict(torch.load(GROUNDED_CHECKPOINT, map_location="cpu"))
    body_model.eval()

    grid = torch.load(GROUNDED_GRID, map_location="cpu")
    if isinstance(grid, np.ndarray):
        grid = torch.from_numpy(grid).float()
    if grid.dim() == 3:
        grid = grid.unsqueeze(0)
    mem = SpatialOccupancyMemory(grid_size=grid.shape[-1], resolution=0.10)

    hal = CarlStage1HAL()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])

    # -------------------------------------------------------------------------
    # TEST 1: Dead-Reckoning Drift vs Ground Truth MuJoCo Physics (T=50, 100, 200)
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Cumulative Dead-Reckoning Drift Quantification ---", flush=True)
    drift_results = {}
    horizons = [50, 100, 200]

    np.random.seed(42)
    for H in horizons:
        trial_drifts = []
        for trial in range(5):
            trial_seed = 42 + trial * 137
            rng = np.random.RandomState(trial_seed)
            hal.reset()
            # Spawn at origin
            hal.data.qpos[qa:qa+2] = [0.0, 0.0]
            hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
            hal.data.qvel[:] = 0.0
            mujoco.mj_forward(hal.model, hal.data)

            # Generate smooth random actions with genuine trial variation
            phase_fwd = float(rng.uniform(0, 2 * math.pi))
            phase_turn = float(rng.uniform(0, 2 * math.pi))
            freq_turn = float(rng.uniform(0.06, 0.10))
            u_seq = []
            for t in range(H):
                # Gentle meandering drive
                u_fwd = 0.4 + 0.1 * math.sin(t * 0.1 + phase_fwd)
                u_turn = 0.2 * math.cos(t * freq_turn + phase_turn)
                u_seq.append([u_fwd - u_turn, u_fwd + u_turn, 0.0, 0.0, 0.0, 0.0])
            u_seq = np.array(u_seq, dtype=np.float32)

            # Ground truth simulation
            for t in range(H):
                hal.step(u_seq[t])
            true_pos = hal.data.qpos[qa:qa+2].copy()

            # Internal dead reckoning via learned body model
            s0 = torch.zeros(1, 9)
            u_tensor = torch.from_numpy(u_seq).unsqueeze(0)
            with torch.no_grad():
                _, _, poses = body_model.unroll(s0, u_tensor)
            pred_pos = poses[0, -1, :2].numpy()

            drift = float(np.linalg.norm(true_pos - pred_pos))
            trial_drifts.append(drift)

        mean_drift = float(np.mean(trial_drifts))
        drift_rate = mean_drift / H  # meters per tick
        drift_results[f"T_{H}"] = {
            "horizon_ticks": H,
            "mean_drift_meters": mean_drift,
            "drift_rate_m_per_tick": drift_rate,
            "trials": trial_drifts
        }
        print(f"Horizon T={H:03d}: Mean Drift = {mean_drift:.3f}m ({drift_rate:.4f} m/tick)", flush=True)

    # -------------------------------------------------------------------------
    # TEST 2: Sensor Noise Perturbations (Gaussian Noise & Dropouts)
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Sensor Noise Injection & Graceful Degradation ---", flush=True)
    noise_results = {}
    perturbation_levels = [
        {"name": "clean", "sigma": 0.0, "dropout_prob": 0.0},
        {"name": "mild_gaussian", "sigma": 0.02, "dropout_prob": 0.0},
        {"name": "heavy_gaussian", "sigma": 0.05, "dropout_prob": 0.0},
        {"name": "dropout_5pct", "sigma": 0.0, "dropout_prob": 0.05},
        {"name": "combined_harsh", "sigma": 0.05, "dropout_prob": 0.05}
    ]

    # Evaluate query robustness across a grid of sample points
    test_points = torch.tensor([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.5],
        [-1.0, 0.5, -0.5],
        [0.5, -1.0, 1.0],
        [-0.5, -0.5, -1.2]
    ], dtype=torch.float32)

    with torch.no_grad():
        base_clearance = mem.query_clearance(grid.repeat(len(test_points), 1, 1, 1), test_points).numpy()

    for p in perturbation_levels:
        pert_grid = grid.clone()
        if p["sigma"] > 0:
            noise = torch.randn_like(pert_grid) * p["sigma"]
            pert_grid = torch.clamp(pert_grid + noise, 0.0, 10.0)
        if p["dropout_prob"] > 0:
            mask = (torch.rand_like(pert_grid) > p["dropout_prob"]).float()
            pert_grid = pert_grid * mask

        with torch.no_grad():
            pert_clearance = mem.query_clearance(pert_grid.repeat(len(test_points), 1, 1, 1), test_points).numpy()

        diff = np.abs(pert_clearance - base_clearance)
        mean_abs_err = float(np.mean(diff))
        max_abs_err = float(np.max(diff))

        noise_results[p["name"]] = {
            "sigma": p["sigma"],
            "dropout_prob": p["dropout_prob"],
            "mean_abs_error_m": mean_abs_err,
            "max_abs_error_m": max_abs_err,
            "graceful_degradation": bool(mean_abs_err < 0.25)
        }
        print(f"Condition '{p['name']:15s}': Mean Abs Error = {mean_abs_err:.4f}m (Max: {max_abs_err:.4f}m) -> Graceful: {mean_abs_err < 0.25}", flush=True)

    robustness_report = {
        "status": "BATTERY_COMPLETE",
        "dead_reckoning_drift": drift_results,
        "sensor_perturbation_tests": noise_results,
        "all_tests_passed": all(res["graceful_degradation"] for res in noise_results.values())
    }

    out_file = EVIDENCE_DIR / "grounded_robustness_scorecard.json"
    with open(out_file, "w") as f:
        json.dump(robustness_report, f, indent=2)
    print(f"\nRobustness scorecard saved to {out_file}", flush=True)

    return robustness_report


if __name__ == "__main__":
    run_robustness_battery()
