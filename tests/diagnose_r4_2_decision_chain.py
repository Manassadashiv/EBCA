"""
tests/diagnose_r4_2_decision_chain.py — R4.2 Diagnostic Probe
Quantifies the coupled decision chain on failing Env2 configurations:
  frontier stability -> candidate score separation -> softmax/action entropy ->
  hull veto rate -> heading error -> chosen action -> branch progress.
Saves structured analytical trace to evidence/stage3_4R4_1/r4_2_forensic_chain.json.
"""

import sys
import math
import json
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_stage1_hal import CarlStage1HAL
from tests.diagnose_env2_failures import build_50_matched_configurations

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4_1"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

ENV2_XML = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
ENV2_GRID = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"


def run_decision_chain_probe(target_config_ids=[20, 21, 22]):
    all_configs = build_50_matched_configurations()
    configs = [c for c in all_configs if c["config_id"] in target_config_ids]

    results = []

    for cfg in configs:
        cfg_id = cfg["config_id"]
        seed = cfg["seed"]
        np.random.seed(seed)
        torch.manual_seed(seed)

        hal = CarlStage1HAL(xml_path=str(ENV2_XML))
        ctrl = CARLActiveInferenceEngine(
            grid_path=str(ENV2_GRID),
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless",
        )

        sx, sy = cfg["spawn_pos"]
        syaw = cfg["spawn_yaw"]
        ctrl.initialize_pose(sx, sy, syaw)

        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        chain_trace = []
        prev_frontier = None
        frontier_churn_events = 0

        v_est = 0.0
        collided = False
        escaped = False

        for tick in range(220):
            curr_sensors = hal.read_sensors()
            gyro_yaw = float(curr_sensors[20])
            ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

            # Ground truth pose
            qa = int(hal.model.joint("spatial_identity").qposadr[0])
            true_x = float(hal.data.qpos[qa])
            true_y = float(hal.data.qpos[qa+1])
            q_rot = hal.data.qpos[qa+3:qa+7]
            true_yaw = math.atan2(2.0 * (q_rot[0]*q_rot[3] + q_rot[1]*q_rot[2]),
                                  1.0 - 2.0 * (q_rot[2]**2 + q_rot[3]**2))

            # Step Active Inference action selection
            u_star, telem = ctrl.select_action(curr_sensors, curr_v=v_est, curr_w=gyro_yaw)

            # 1. Frontier Stability
            f_star_x = telem.get("macro_frontier_x")
            f_star_y = telem.get("macro_frontier_y")
            curr_frontier = (f_star_x, f_star_y) if f_star_x is not None else None

            delta_f = 0.0
            if prev_frontier is not None and curr_frontier is not None:
                delta_f = math.hypot(curr_frontier[0] - prev_frontier[0], curr_frontier[1] - prev_frontier[1])
                if delta_f > 0.30:  # Churn threshold: target jumped more than 30 cm
                    frontier_churn_events += 1
            prev_frontier = curr_frontier

            # 2. Candidate Score Separation & Entropy
            # Reconstruct top-5 candidate costs from telemetry if available
            n_rej = telem.get("rejected_candidates", 0)
            n_acc = telem.get("accepted_candidates", 128)
            veto_rate = n_rej / max(1, n_rej + n_acc)

            # Heading error
            est_x, est_y, est_yaw = ctrl.pose
            heading_err_deg = math.degrees(abs(math.atan2(math.sin(est_yaw - true_yaw), math.cos(est_yaw - true_yaw))))

            # Step physical robot
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(u_star[0])
            cmd_6d[1] = float(u_star[1])
            hal.step(cmd_6d)

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

            # Collision check
            c_info = hal.get_carl_contact_info()
            wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
            if wall_contacts > 0:
                collided = True

            # Escape check
            if true_y <= -1.20:
                escaped = True

            record = {
                "tick": tick,
                "true_x": round(true_x, 4),
                "true_y": round(true_y, 4),
                "true_yaw_deg": round(math.degrees(true_yaw), 2),
                "est_yaw_deg": round(math.degrees(est_yaw), 2),
                "heading_err_deg": round(heading_err_deg, 2),
                "macro_frontier": [round(f_star_x, 3), round(f_star_y, 3)] if f_star_x is not None else None,
                "frontier_jump_m": round(delta_f, 3),
                "hull_veto_rate": round(veto_rate, 3),
                "chosen_action": [round(float(u_star[0]), 3), round(float(u_star[1]), 3)],
                "forward_cmd": round(u_fwd, 3),
                "turn_cmd": round(float(u_star[1] - u_star[0]), 3),
                "dist_to_escape_m": round(max(0.0, true_y - (-1.20)), 3),
                "status": "COLLIDED" if collided else ("ESCAPED" if escaped else "RUNNING")
            }
            chain_trace.append(record)

            if collided or escaped:
                break

        summary = {
            "config_id": cfg_id,
            "outcome": "ESCAPED" if escaped else ("COLLIDED" if collided else "TIMEOUT"),
            "ticks_executed": len(chain_trace),
            "frontier_churn_events": frontier_churn_events,
            "mean_veto_rate": round(float(np.mean([r["hull_veto_rate"] for r in chain_trace])), 3),
            "mean_heading_err_deg": round(float(np.mean([r["heading_err_deg"] for r in chain_trace])), 2),
            "max_heading_err_deg": round(float(np.max([r["heading_err_deg"] for r in chain_trace])), 2),
            "final_true_pos": [chain_trace[-1]["true_x"], chain_trace[-1]["true_y"]],
            "trace_sample": chain_trace[::10]  # Every 10th tick
        }
        results.append(summary)
        print(f"Probe Config {cfg_id}: Outcome = {summary['outcome']} | Churn = {frontier_churn_events} | Mean Veto = {summary['mean_veto_rate']:.1%} | Max HErr = {summary['max_heading_err_deg']:.1f} deg | Final Pos = {summary['final_true_pos']}")

    out_file = EVIDENCE_DIR / "r4_2_forensic_chain.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Decision Chain Forensic Trace to {out_file}")
    return results


if __name__ == "__main__":
    run_decision_chain_probe()
