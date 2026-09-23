"""
tests/test_stage3_2A_trajectory_fidelity.py — Stage 3.2A Counterfactual Trajectory Rollout Fidelity Benchmark
Classification: [STAGE 3.2A BENCHMARK] Preregistered Trajectory-Fidelity Double-Blind Evaluation

Evaluates internal forward kinematic unroll against physical MuJoCo rigid-body dynamics
over horizon H=10 (dt=0.030s) across 24 continuous action profiles and 5 evaluation seeds (N=120 rollouts).

Preregistered Gates:
- G1: Mean Terminal Position Error <= 0.080 m
- G2: 95th Percentile Terminal Error <= 0.120 m
- G3: Mean Trajectory RMSE <= 0.050 m
- G4: Mean Terminal Heading Error <= 0.100 rad (5.73 deg)
- G5: Coasting Momentum Envelope R^2_v >= 0.80
"""

import sys
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

EVIDENCE_DIR = repo_root / "evidence" / "stage3_2"
RAW_DIR = EVIDENCE_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [3001, 3002, 3003, 3004, 3005]

PROFILES = [
    ("P01", "Straight", "straight_full", [0.80, 0.80]),
    ("P02", "Straight", "straight_cruise", [0.60, 0.60]),
    ("P03", "Straight", "straight_trim_L", [0.75, 0.80]),
    ("P04", "Straight", "straight_trim_R", [0.80, 0.75]),
    ("P05", "Curved Left", "gentle_left", [0.65, 0.75]),
    ("P06", "Curved Left", "soft_left_mod", [0.40, 0.55]),
    ("P07", "Curved Left", "soft_left_fast", [0.55, 0.80]),
    ("P08", "Curved Left", "med_left_mod", [0.25, 0.50]),
    ("P09", "Curved Left", "med_left_fast", [0.35, 0.80]),
    ("P10", "Curved Left", "hard_left_fast", [0.15, 0.80]),
    ("P11", "Curved Right", "gentle_right", [0.75, 0.65]),
    ("P12", "Curved Right", "soft_right_mod", [0.55, 0.40]),
    ("P13", "Curved Right", "soft_right_fast", [0.80, 0.55]),
    ("P14", "Curved Right", "med_right_mod", [0.50, 0.25]),
    ("P15", "Curved Right", "med_right_fast", [0.80, 0.35]),
    ("P16", "Curved Right", "hard_right_fast", [0.80, 0.15]),
    ("P17", "In-Place Pivot", "pivot_left_hard", [-0.60, 0.60]),
    ("P18", "In-Place Pivot", "pivot_right_hard", [0.60, -0.60]),
    ("P19", "In-Place Pivot", "pivot_left_mod", [-0.35, 0.35]),
    ("P20", "Reverse", "reverse_straight", [-0.35, -0.35]),
    ("P21", "Reverse-Hook", "reverse_hook_left", [-0.40, -0.15]),
    ("P22", "Reverse-Hook", "reverse_hook_right", [-0.15, -0.40]),
    ("P23", "Accel/Decel Ramp", "throttle_step", "step_accel"),
    ("P24", "Coasting / Decay", "inertial_coast", "step_coast"),
]


def run_stage3_2A_trajectory_fidelity_benchmark() -> Dict[str, Any]:
    print("=========================================================================")
    print("CARL-DX STAGE 3.2A: COUNTERFACTUAL TRAJECTORY ROLLOUT FIDELITY BENCHMARK")
    print("Status: EXECUTING FROZEN SUB-GATE 3.2A (N=120 ROLLOUTS)")
    print("=========================================================================")

    hal = CarlStage1HAL(xml_path="world/clean_arena.xml")
    delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
    qa = int(hal.model.joint("spatial_identity").qposadr[0])

    rollout_records = []
    term_errors = []
    p95_pool = []
    rmse_errors = []
    heading_errors = []
    coast_v_phys = []
    coast_v_pred = []
    pearson_r_list = []
    cos_sim_list = []

    for pid, family, pname, cmd in PROFILES:
        print(f"\n--- Profiling {pid}: {pname} ({family}) ---")
        for s in SEEDS:
            rng = np.random.RandomState(s)
            init_x = float(rng.uniform(-0.010, 0.010))
            init_y = float(rng.uniform(-0.010, 0.010))
            init_yaw = float(rng.uniform(-0.008, 0.008))

            # Construct action sequence u_seq (H=10, 6)
            u_seq = np.zeros((10, 6), dtype=np.float32)
            if pid == "P23":
                u_seq[:5, :2] = [0.20, 0.20]
                u_seq[5:, :2] = [0.80, 0.80]
            elif pid == "P24":
                u_seq[:5, :2] = [0.80, 0.80]
                u_seq[5:, :2] = [0.00, 0.00]
            else:
                u_seq[:, :2] = cmd

            # Setup MuJoCo physical state
            hal.reset()
            hal.data.qpos[qa:qa+2] = [init_x, init_y]
            hal.data.qpos[qa+3:qa+7] = [math.cos(init_yaw / 2.0), 0.0, 0.0, math.sin(init_yaw / 2.0)]
            hal.data.qvel[:] = 0.0
            hal.data.ctrl[:] = 0.0
            import mujoco
            mujoco.mj_forward(hal.model, hal.data)

            # Settle physical contacts (10 zero-torque ticks)
            for _ in range(10):
                hal.step(np.zeros(6))

            # Record settled starting pose
            qw, qx, qy, qz = hal.data.qpos[qa+3:qa+7]
            settled_x, settled_y = hal.data.qpos[qa:qa+2]
            settled_yaw = 2.0 * math.atan2(qz, qw)

            # Prospective mental unroll in cognitive engine
            pred_poses = delib._mental_unroll_poses(settled_x, settled_y, settled_yaw, u_seq, init_v=0.0, init_w=0.0)

            # Step physical MuJoCo simulation
            phys_poses = []
            phys_vs = []
            for h in range(10):
                hal.step(u_seq[h])
                px, py = hal.data.qpos[qa:qa+2]
                qw, qx, qy, qz = hal.data.qpos[qa+3:qa+7]
                yaw = 2.0 * math.atan2(qz, qw)
                v_long = float(hal.data.qvel[qa] * math.cos(yaw) + hal.data.qvel[qa+1] * math.sin(yaw))
                phys_poses.append([float(px), float(py), float(yaw)])
                phys_vs.append(v_long)

            # Metric Calculations
            p_pred_term = np.array(pred_poses[-1][:2])
            p_phys_term = np.array(phys_poses[-1][:2])
            e_term = float(np.linalg.norm(p_pred_term - p_phys_term))

            step_sq_errs = [
                np.linalg.norm(np.array(pred_poses[h][:2]) - np.array(phys_poses[h][:2]))**2
                for h in range(10)
            ]
            rmse_xy = float(math.sqrt(np.mean(step_sq_errs)))

            th_pred = pred_poses[-1][2]
            th_phys = phys_poses[-1][2]
            e_theta = float(abs(math.atan2(math.sin(th_pred - th_phys), math.cos(th_pred - th_phys))))

            # Pearson r and Cosine Similarity
            traj_pred_flat = np.array([p[:2] for p in pred_poses]).flatten()
            traj_phys_flat = np.array([p[:2] for p in phys_poses]).flatten()
            r_val = float(np.corrcoef(traj_pred_flat, traj_phys_flat)[0, 1]) if np.std(traj_pred_flat) > 1e-6 and np.std(traj_phys_flat) > 1e-6 else 1.0
            cos_sim = float(np.dot(traj_pred_flat, traj_phys_flat) / (np.linalg.norm(traj_pred_flat) * np.linalg.norm(traj_phys_flat) + 1e-8))

            term_errors.append(e_term)
            p95_pool.append(e_term)
            rmse_errors.append(rmse_xy)
            heading_errors.append(e_theta)
            pearson_r_list.append(r_val)
            cos_sim_list.append(cos_sim)

            # Record coasting velocities for P24
            if pid == "P24":
                # Compute pred velocities
                prev_v = 0.0
                pred_vs = []
                for step in range(10):
                    u = u_seq[step]
                    u_fwd = 0.5 * (u[0] + u[1])
                    is_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
                    v_target = u_fwd * delib.k_fwd / delib.dt
                    nv = is_zero * (delib.gamma_v * prev_v) + (1.0 - is_zero) * (0.30 * prev_v + 0.70 * v_target)
                    pred_vs.append(nv)
                    prev_v = nv

                # Steps 5..9 are coasting phase
                for h in range(5, 10):
                    coast_v_phys.append(phys_vs[h])
                    coast_v_pred.append(pred_vs[h])

            rollout_records.append({
                "profile_id": pid,
                "profile_name": pname,
                "family": family,
                "seed": s,
                "command": [float(u_seq[0, 0]), float(u_seq[0, 1])],
                "e_term": e_term,
                "rmse_xy": rmse_xy,
                "e_theta": e_theta,
                "pearson_r": r_val,
                "cosine_similarity": cos_sim,
                "terminal_pred_pos": [float(p_pred_term[0]), float(p_pred_term[1])],
                "terminal_phys_pos": [float(p_phys_term[0]), float(p_phys_term[1])],
                "terminal_pred_yaw": float(th_pred),
                "terminal_phys_yaw": float(th_phys),
            })

    # Summary Statistics
    mean_term = float(np.mean(term_errors))
    p95_term = float(np.percentile(p95_pool, 95))
    mean_rmse = float(np.mean(rmse_errors))
    mean_theta = float(np.mean(heading_errors))
    mean_r = float(np.mean(pearson_r_list))
    mean_cos = float(np.mean(cos_sim_list))

    # Coasting R^2
    arr_phys = np.array(coast_v_phys)
    arr_pred = np.array(coast_v_pred)
    ss_res = float(np.sum((arr_phys - arr_pred)**2))
    ss_tot = float(np.sum((arr_phys - np.mean(arr_phys))**2)) + 1e-8
    r2_v = float(1.0 - (ss_res / ss_tot))

    # Gate Evaluations
    g1_pass = bool(mean_term <= 0.080)
    g2_pass = bool(p95_term <= 0.120)
    g3_pass = bool(mean_rmse <= 0.050)
    g4_pass = bool(mean_theta <= 0.100)
    g5_pass = bool(r2_v >= 0.80)

    overall_subgate_pass = bool(g1_pass and g2_pass and g3_pass and g4_pass and g5_pass)

    scorecard = {
        "subgate": "3.2A",
        "title": "Counterfactual Trajectory Rollout Fidelity",
        "total_rollouts_evaluated": len(rollout_records),
        "metrics": {
            "mean_terminal_pos_error_m": mean_term,
            "p95_terminal_pos_error_m": p95_term,
            "mean_trajectory_rmse_m": mean_rmse,
            "mean_terminal_heading_error_rad": mean_theta,
            "mean_terminal_heading_error_deg": float(np.degrees(mean_theta)),
            "coasting_r2_v": r2_v,
            "mean_pearson_r": mean_r,
            "mean_cosine_similarity": mean_cos,
        },
        "gates": {
            "G1_mean_terminal_error": {"metric": mean_term, "threshold": "<= 0.080 m", "passed": g1_pass},
            "G2_p95_terminal_error": {"metric": p95_term, "threshold": "<= 0.120 m", "passed": g2_pass},
            "G3_mean_trajectory_rmse": {"metric": mean_rmse, "threshold": "<= 0.050 m", "passed": g3_pass},
            "G4_mean_heading_error": {"metric": mean_theta, "threshold": "<= 0.100 rad", "passed": g4_pass},
            "G5_coasting_r2_v": {"metric": r2_v, "threshold": ">= 0.80", "passed": g5_pass},
        },
        "verdict": "PASSED" if overall_subgate_pass else "FAILED_CLOSED",
        "rollout_records": rollout_records,
    }

    # Save data
    out_path = RAW_DIR / "stage3_2A_fidelity_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    print("\n" + "="*80)
    print("STAGE 3.2A EVALUATION RESULTS SUMMARY")
    print("="*80)
    print(f"Total Rollouts:                    {len(rollout_records)}")
    print(f"G1 — Mean Terminal Error:          {mean_term:.4f} m   (Gate <= 0.080 m)  -> {'PASS' if g1_pass else 'FAIL'}")
    print(f"G2 — 95th Pct Terminal Error:      {p95_term:.4f} m   (Gate <= 0.120 m)  -> {'PASS' if g2_pass else 'FAIL'}")
    print(f"G3 — Mean Trajectory RMSE:         {mean_rmse:.4f} m   (Gate <= 0.050 m)  -> {'PASS' if g3_pass else 'FAIL'}")
    print(f"G4 — Mean Heading Error:           {mean_theta:.4f} rad ({np.degrees(mean_theta):.2f} deg) (Gate <= 0.100 rad) -> {'PASS' if g4_pass else 'FAIL'}")
    print(f"G5 — Coasting Envelope R^2_v:      {r2_v:.4f}      (Gate >= 0.80)     -> {'PASS' if g5_pass else 'FAIL'}")
    print(f"Mean Pearson r:                    {mean_r:.4f}")
    print(f"Mean Cosine Similarity:            {mean_cos:.4f}")
    print(f"Sub-Gate 3.2A Verdict:             {scorecard['verdict']}")
    print(f"Saved Raw Data:                    {out_path}")
    print("="*80 + "\n")

    return scorecard


if __name__ == "__main__":
    res = run_stage3_2A_trajectory_fidelity_benchmark()
    if res["verdict"] != "PASSED":
        print(">>> SUB-GATE 3.2A FAILED CLOSED UNDER PREREGISTERED THRESHOLDS <<<")
