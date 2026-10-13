"""
tests/diagnose_env2_failures.py — Deep Forensic Diagnosis for Environment 2 Failures
Runs Configs 20, 21, 22, 23, 24 across ARM-A and ARM-B, logging full telemetry at every tick.
Classifies each failure into:
  A. TARGET FAILURE
  B. ACTION FAILURE
  C. GEOMETRIC FEASIBILITY FAILURE
  D. STATE-ESTIMATION FAILURE
  E. COMPUTATIONAL FAILURE
  F. PERCEPTION / MEMORY FAILURE
Saves to evidence/stage3_4R4_1/env2_failure_taxonomy.json.
"""

import sys
import math
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

OUT_DIR = repo_root / "evidence" / "stage3_4R4_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def diagnose_episode(arm: str, config: Dict[str, Any]) -> Dict[str, Any]:
    xml_path = config["xml_path"]
    grid_path = config["grid_path"]
    sx, sy = config["spawn_pos"]
    syaw = config["spawn_yaw"]

    hal = CarlStage1HAL(xml_path=xml_path)
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    w_info = 1.0 if arm == "ARM-A" else 0.0
    controller = CARLActiveInferenceEngine(
        grid_path=grid_path,
        w_info=w_info,
        frontier_mode="macro",
        norm_mode="dimensionless",
    )
    controller.initialize_pose(sx, sy, syaw)

    trajectory = []
    gyro_heading = syaw
    v_est = 0.0
    records = []
    had_collision = False
    escaped = False

    max_ticks = 220
    for tick in range(max_ticks):
        # Ground truth evaluator pose
        q_curr = hal.data.qpos[qa:qa+7]
        true_x, true_y = float(q_curr[0]), float(q_curr[1])
        true_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        trajectory.append([true_x, true_y])

        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])
        gyro_heading += gyro_yaw * 0.030
        gyro_heading = math.atan2(math.sin(gyro_heading), math.cos(gyro_heading))

        t0 = time.perf_counter()
        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        # Extract macro-frontier info
        macro_info = controller._compute_macro_frontier(controller.pose[0], controller.pose[1])
        if macro_info:
            f_x, f_y, d_geo, _ = macro_info
        else:
            f_x, f_y, d_geo = None, None, None

        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0]); cmd_6d[1] = float(action[1])
        hal.step(cmd_6d)

        # Contact check
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True

        # Escape check
        if true_y <= -1.20:
            escaped = True

        # Candidate stats
        n_rej = telem.get("rejected_candidates", 0)
        n_acc = telem.get("accepted_candidates", 128)

        rec = {
            "tick": tick,
            "true_pos": [round(true_x, 4), round(true_y, 4)],
            "true_yaw_deg": round(math.degrees(true_yaw), 2),
            "est_pos": [round(float(controller.pose[0]), 4), round(float(controller.pose[1]), 4)],
            "est_yaw_deg": round(math.degrees(float(controller.pose[2])), 2),
            "gyro_yaw_deg": round(math.degrees(gyro_heading), 2),
            "heading_err_deg": round(abs(math.degrees(math.atan2(math.sin(float(controller.pose[2]) - true_yaw), math.cos(float(controller.pose[2]) - true_yaw)))), 2),
            "selected_frontier": [round(f_x, 3), round(f_y, 3)] if f_x is not None else None,
            "dist_to_frontier": round(d_geo, 3) if d_geo is not None else None,
            "feasible_candidates": n_acc,
            "rejected_candidates": n_rej,
            "chosen_action": [round(float(action[0]), 3), round(float(action[1]), 3)],
            "efe_total": round(float(telem.get("best_cost", 0.0)), 3),
            "efe_pragmatic": round(float(telem.get("efe_pragmatic_mean", 0.0)), 3),
            "efe_epistemic": round(float(telem.get("efe_epistemic_mean", 0.0)), 3),
            "min_pred_clearance": round(float(telem.get("min_predicted_hull_clearance", 0.0)), 4),
            "sonar_heading_confidence": round(float(telem.get("sonar_heading_confidence", 0.0)), 2),
            "latency_ms": round(lat_ms, 2),
        }
        records.append(rec)

        if had_collision or escaped:
            break

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

    # Classify failure
    failure_class = "NONE (ESCAPED)"
    term_reason = "ESCAPED" if escaped else ("COLLIDED" if had_collision else "TIMEOUT")

    if not escaped:
        if had_collision:
            # Check if state estimation was wrong
            last_rec = records[-1]
            if last_rec["heading_err_deg"] > 15.0 or abs(last_rec["est_pos"][0] - last_rec["true_pos"][0]) > 0.15:
                failure_class = "D. STATE-ESTIMATION FAILURE"
            elif last_rec["min_pred_clearance"] > 0.03:
                # Controller predicted clearance was safe, but physical body collided
                failure_class = "C. GEOMETRIC FEASIBILITY FAILURE"
            else:
                failure_class = "B. ACTION FAILURE"
        else: # TIMEOUT
            # Inspect what robot was doing in the second half
            final_recs = records[len(records)//2:]
            frontiers = [r["selected_frontier"] for r in final_recs if r["selected_frontier"] is not None]
            # In Env 2, exit is at y <= -1.20. Target frontier y should be <= -0.50
            if frontiers and any(f[1] > 0.30 for f in frontiers):
                # Targeted the dead-end north branch instead of south exit
                failure_class = "A. TARGET FAILURE"
            elif all(r["feasible_candidates"] < 15 for r in final_recs):
                # Trapped because hull feasibility rejected all candidates
                failure_class = "C. GEOMETRIC FEASIBILITY FAILURE"
            elif any(r["heading_err_deg"] > 25.0 for r in final_recs):
                failure_class = "D. STATE-ESTIMATION FAILURE"
            else:
                # Robot was pointed towards exit or in corridor, but moved too slowly / oscillated actions
                failure_class = "B. ACTION FAILURE"

    summary = {
        "config_id": config["config_id"],
        "env_id": 2,
        "env_name": "Asymmetric T-Junction",
        "arm": arm,
        "seed": config["seed"],
        "spawn_pos": config["spawn_pos"],
        "spawn_yaw": config["spawn_yaw"],
        "escaped": escaped,
        "had_collision": had_collision,
        "timeout": not escaped and not had_collision,
        "termination_reason": term_reason,
        "failure_class": failure_class,
        "ticks_executed": len(records),
        "mean_latency_ms": round(float(np.mean([r["latency_ms"] for r in records])), 2),
        "p95_latency_ms": round(float(np.percentile([r["latency_ms"] for r in records], 95)), 2),
        "final_pose_true": records[-1]["true_pos"],
        "final_pose_est": records[-1]["est_pos"],
        "final_heading_err_deg": records[-1]["heading_err_deg"],
        "selected_macro_frontier_final": records[-1]["selected_frontier"],
        "dist_to_frontier_final": records[-1]["dist_to_frontier"],
        "feasible_candidates_mean": round(float(np.mean([r["feasible_candidates"] for r in records])), 1),
        "rejected_candidates_mean": round(float(np.mean([r["rejected_candidates"] for r in records])), 1),
        "min_predicted_hull_clearance": round(float(np.min([r["min_pred_clearance"] for r in records])), 4),
        "records_sample": [records[i] for i in range(0, len(records), max(1, len(records)//8))],
    }
    return summary


def main():
    all_configs = build_50_matched_configurations()
    env2_configs = [c for c in all_configs if c["config_id"] in [20, 21, 22, 23, 24]]

    taxonomy = []
    print("Running forensic diagnosis of Env 2 configurations...")
    for cfg in env2_configs:
        for arm in ["ARM-A", "ARM-B"]:
            t0 = time.time()
            diag = diagnose_episode(arm, cfg)
            dur = time.time() - t0
            taxonomy.append(diag)
            print(f"Cfg {diag['config_id']} | {arm} -> {diag['termination_reason']} | Class: {diag['failure_class']} (ticks={diag['ticks_executed']}, lat={diag['mean_latency_ms']}ms) [{dur:.1f}s]")

    out_file = OUT_DIR / "env2_failure_taxonomy.json"
    with open(out_file, "w") as f:
        json.dump(taxonomy, f, indent=2)
    print(f"\nTaxonomy saved to {out_file}")


if __name__ == "__main__":
    main()
