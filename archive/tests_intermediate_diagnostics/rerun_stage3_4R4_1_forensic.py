"""
tests/rerun_stage3_4R4_1_forensic.py — Part 10 Single Forensic Re-Run
Re-runs the 5 known failing Env2 configurations (Configs 20, 21, 22, 23, 24) under ARM-A
using the updated generic heading fusion and optimized deliberation engine.
Records exact metrics and compares with previous R4 results.
Saves to evidence/stage3_4R4_1/env2_rerun_forensic.json.
"""

import sys
import json
import math
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_stage1_hal import CarlStage1HAL

OUT_DIR = repo_root / "evidence" / "stage3_4R4_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENV2_XML = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
ENV2_GRID = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"

from tests.diagnose_env2_failures import build_50_matched_configurations

ALL_CONFIGS = build_50_matched_configurations()
TARGET_CONFIG_IDS = [20, 21, 22, 23, 24]
TARGET_CONFIGS = [c for c in ALL_CONFIGS if c["config_id"] in TARGET_CONFIG_IDS]


def run_forensic_rerun():
    print(f"=== PART 10: SINGLE FORENSIC RE-RUN FOR ENV2 (CONFIGS {TARGET_CONFIG_IDS}) ===")
    rerun_records = []

    for cfg in TARGET_CONFIGS:
        cfg_id = cfg["config_id"]
        seed = cfg["seed"]
        np.random.seed(seed)

        hal = CarlStage1HAL(xml_path=str(ENV2_XML))
        ctrl = CARLActiveInferenceEngine(
            grid_path=str(ENV2_GRID),
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless",
        )

        # Spawn pose with calibration perturbation
        sx = float(cfg["spawn_pos"][0])
        sy = float(cfg["spawn_pos"][1])
        syaw = float(cfg["spawn_yaw"])
        ctrl.initialize_pose(sx, sy, syaw)

        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        escaped = False
        had_collision = False
        timeout = False
        term_reason = "RUNNING"
        step_latencies = []
        heading_errors = []
        lateral_drifts = []
        rejection_rates = []
        min_clearances = []
        trajectory_poses = []
        selected_frontiers = []

        max_ticks = 220

        v_est = 0.0

        for tick in range(max_ticks):
            # 1. Unprivileged sensor read
            curr_sensors = hal.read_sensors()
            gyro_yaw = float(curr_sensors[20])
            ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

            # Ground truth pose for evaluator verification ONLY (never fed to ctrl)
            qa = int(hal.model.joint("spatial_identity").qposadr[0])
            true_x = float(hal.data.qpos[qa])
            true_y = float(hal.data.qpos[qa+1])
            q_rot = hal.data.qpos[qa+3:qa+7]
            true_yaw = math.atan2(2.0 * (q_rot[0]*q_rot[3] + q_rot[1]*q_rot[2]),
                                  1.0 - 2.0 * (q_rot[2]**2 + q_rot[3]**2))

            # Step Active Inference Deliberation
            t0 = time.perf_counter()
            u_star, telemetry = ctrl.select_action(curr_sensors, curr_v=v_est, curr_w=gyro_yaw)
            dt_ms = (time.perf_counter() - t0) * 1000.0

            step_latencies.append(dt_ms)
            rejection_rates.append(telemetry["rejected_candidates"] / telemetry["mppi_samples"])
            min_clearances.append(telemetry["min_predicted_hull_clearance"])

            est_x, est_y, est_yaw = ctrl.pose
            heading_err = abs(math.atan2(math.sin(est_yaw - true_yaw), math.cos(est_yaw - true_yaw)))
            heading_errors.append(math.degrees(heading_err))
            lateral_drifts.append(abs(est_x - true_x))
            trajectory_poses.append({"tick": tick, "true": [round(true_x, 4), round(true_y, 4), round(true_yaw, 4)],
                                     "est": [round(est_x, 4), round(est_y, 4), round(est_yaw, 4)]})

            # Check MuJoCo contact ground truth
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(u_star[0])
            cmd_6d[1] = float(u_star[1])
            hal.step(cmd_6d)

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

            contact_info = hal.get_carl_contact_info()
            if (contact_info["carl_contacts"] - contact_info["floor_contacts"]) > 0:
                had_collision = True
                term_reason = "COLLIDED"
                break

            # Env 2 Exit criterion: y <= -1.20 m (south branch escape opening)
            if true_y <= -1.20:
                escaped = True
                term_reason = "ESCAPED"
                break

        if not escaped and not had_collision:
            timeout = True
            term_reason = "TIMEOUT"

        rec = {
            "config_id": cfg_id,
            "env_id": 2,
            "seed": seed,
            "arm": "ARM-A",
            "spawn_pos": [sx, sy],
            "spawn_yaw": syaw,
            "escaped": escaped,
            "had_collision": had_collision,
            "timeout": timeout,
            "termination_reason": term_reason,
            "ticks_executed": len(step_latencies),
            "mean_latency_ms": round(float(np.mean(step_latencies)), 2),
            "p95_latency_ms": round(float(np.percentile(step_latencies, 95)), 2),
            "final_true_pose": [round(true_x, 4), round(true_y, 4)],
            "final_est_pose": [round(est_x, 4), round(est_y, 4)],
            "mean_heading_error_deg": round(float(np.mean(heading_errors)), 2),
            "max_heading_error_deg": round(float(np.max(heading_errors)), 2),
            "mean_lateral_drift_m": round(float(np.mean(lateral_drifts)), 4),
            "max_lateral_drift_m": round(float(np.max(lateral_drifts)), 4),
            "min_hull_clearance_m": round(float(np.min(min_clearances)), 4),
            "candidate_rejection_rate_mean": round(float(np.mean(rejection_rates)), 3),
            "trajectory_poses": trajectory_poses
        }
        rerun_records.append(rec)
        print(f"Config {cfg_id}: Outcome = {term_reason} | Ticks = {rec['ticks_executed']} | Final y = {rec['final_true_pose'][1]} | Latency p95 = {rec['p95_latency_ms']} ms | HErr max = {rec['max_heading_error_deg']} deg")

    out_file = OUT_DIR / "env2_rerun_forensic.json"
    with open(out_file, "w") as f:
        json.dump(rerun_records, f, indent=2)
    print(f"\nSaved Part 10 Forensic Re-run to {out_file}")
    return rerun_records


if __name__ == "__main__":
    run_forensic_rerun()
