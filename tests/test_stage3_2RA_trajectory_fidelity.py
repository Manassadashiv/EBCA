"""
tests/test_stage3_2RA_trajectory_fidelity.py — Stage 3.2-RA Counterfactual Trajectory Rollout Fidelity Benchmark
Classification: [STAGE 3.2-RA BENCHMARK] Preregistered Trajectory-Fidelity Double-Blind Evaluation (Class A)

Evaluates internal forward kinematic unroll against physical MuJoCo rigid-body dynamics
over horizon H=10 (dt=0.030s) across 24 continuous action profiles and 5 evaluation seeds (N=120 rollouts).

Class A Pre-Registered Gates:
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

EVIDENCE_DIR = repo_root / "evidence" / "stage3_2R"
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


def run_stage3_2RA_trajectory_fidelity_benchmark() -> Dict[str, Any]:
    print("=========================================================================")
    print("CARL-DX STAGE 3.2-RA: COUNTERFACTUAL TRAJECTORY ROLLOUT FIDELITY BENCHMARK")
    print("Status: EXECUTING SUB-GATE 3.2-RA (N=120 ROLLOUTS, CLASS A)")
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

    for pid, family, pname, cmd in PROFILES:
        print(f"Profiling {pid}: {pname} ({family})...")
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

            term_errors.append(e_term)
            p95_pool.append(e_term)
            rmse_errors.append(rmse_xy)
            heading_errors.append(e_theta)

            if pid == "P24":
                # Coasting decay evaluation (steps 5..9)
                coast_v_phys.extend(phys_vs[5:])
                # Pred v is approximated from consecutive step displacements
                pred_vs = [
                    float(np.linalg.norm(np.array(pred_poses[h][:2]) - np.array(pred_poses[h-1][:2])) / 0.030)
                    for h in range(1, 10)
                ]
                coast_v_pred.extend(pred_vs[4:])

            rollout_records.append({
                "pid": pid,
                "family": family,
                "pname": pname,
                "seed": s,
                "settled_start": [float(settled_x), float(settled_y), float(settled_yaw)],
                "e_term": e_term,
                "rmse_xy": rmse_xy,
                "e_theta": e_theta,
                "pred_trajectory": [[float(x) for x in p] for p in pred_poses],
                "phys_trajectory": [[float(x) for x in p] for p in phys_poses],
            })

    # Summary Statistics
    mean_term = float(np.mean(term_errors))
    p95_term = float(np.percentile(p95_pool, 95))
    mean_rmse = float(np.mean(rmse_errors))
    mean_theta = float(np.mean(heading_errors))

    # Coasting R^2_v
    if len(coast_v_phys) > 0 and np.var(coast_v_phys) > 1e-6:
        ss_res = np.sum((np.array(coast_v_phys) - np.array(coast_v_pred))**2)
        ss_tot = np.sum((np.array(coast_v_phys) - np.mean(coast_v_phys))**2)
        r2_v = float(1.0 - (ss_res / ss_tot))
    else:
        r2_v = 1.0

    # Evaluate Class A Gates
    pass_g1 = bool(mean_term <= 0.080)
    pass_g2 = bool(p95_term <= 0.120)
    pass_g3 = bool(mean_rmse <= 0.050)
    pass_g4 = bool(mean_theta <= 0.100)
    pass_g5 = bool(r2_v >= 0.80)

    class_a_passed = bool(pass_g1 and pass_g2 and pass_g3 and pass_g4 and pass_g5)

    scorecard = {
        "subgate": "3.2-RA",
        "title": "Counterfactual Trajectory Rollout Fidelity Benchmark (Class A)",
        "total_rollouts": len(rollout_records),
        "profiles_tested": 24,
        "seeds_tested": len(SEEDS),
        "metrics": {
            "mean_term_error_m": mean_term,
            "p95_term_error_m": p95_term,
            "mean_rmse_xy_m": mean_rmse,
            "mean_heading_error_rad": mean_theta,
            "mean_heading_error_deg": float(np.degrees(mean_theta)),
            "coasting_r2_v": r2_v,
        },
        "gates": {
            "G1_mean_terminal_error": {"metric": mean_term, "threshold": "<= 0.080 m", "passed": pass_g1},
            "G2_p95_terminal_error": {"metric": p95_term, "threshold": "<= 0.120 m", "passed": pass_g2},
            "G3_mean_rmse_xy": {"metric": mean_rmse, "threshold": "<= 0.050 m", "passed": pass_g3},
            "G4_mean_heading_error": {"metric": mean_theta, "threshold": "<= 0.100 rad", "passed": pass_g4},
            "G5_coasting_r2_v": {"metric": r2_v, "threshold": ">= 0.80", "passed": pass_g5},
        },
        "class_a_validity": "VALID" if class_a_passed else "INVALID_MODEL",
    }

    raw_file = RAW_DIR / "stage3_2RA_fidelity_data.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump({"summary": scorecard, "rollouts": rollout_records}, f, indent=2)

    print("\n=========================================================================")
    print("STAGE 3.2-RA SCORECARD (CLASS A: MODEL/CONTROLLER VALIDITY)")
    print("=========================================================================")
    print(f"G1: Mean Terminal Pos Error : {mean_term:.4f} m (threshold <= 0.080 m) -> {'PASS' if pass_g1 else 'FAIL'}")
    print(f"G2: p95 Terminal Pos Error  : {p95_term:.4f} m (threshold <= 0.120 m) -> {'PASS' if pass_g2 else 'FAIL'}")
    print(f"G3: Mean Trajectory RMSE    : {mean_rmse:.4f} m (threshold <= 0.050 m) -> {'PASS' if pass_g3 else 'FAIL'}")
    print(f"G4: Mean Heading Error      : {mean_theta:.4f} rad ({np.degrees(mean_theta):.2f} deg) (threshold <= 0.100 rad) -> {'PASS' if pass_g4 else 'FAIL'}")
    print(f"G5: Coasting Velocity R^2_v : {r2_v:.4f} (threshold >= 0.80) -> {'PASS' if pass_g5 else 'FAIL'}")
    print("-------------------------------------------------------------------------")
    print(f"CLASS A MODEL VALIDITY STATUS: {scorecard['class_a_validity']}")
    print(f"Saved Raw Data: {raw_file}")
    print("=========================================================================\n")

    return scorecard


if __name__ == "__main__":
    run_stage3_2RA_trajectory_fidelity_benchmark()
