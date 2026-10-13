"""
tests/run_stage3_4R4_single_trace.py — Phase 2 Single-Episode Forensic Trace for Stage 3.4-R4
Records every control cycle for Config 0 (representative failure config from R3).
Saves output to evidence/stage3_4R4/r4_single_episode_trace.json.
"""

import sys
import math
import time
import json
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

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def compute_actual_hull_clearance_env1(x: float, y: float, theta: float) -> float:
    """
    Computes true distance from robot rectangular hull bumper (a=0.115, b=0.135)
    to corridor walls in Environment 1.
    Corridor is y in [-0.35, 0.35], dead-end at x = 0.825, opening at x = -0.70.
    Turning bay is at x in [0.0, 0.40], y in [0.35, 0.75].
    """
    a = 0.115
    b = 0.135
    # 4 bumper corners in world frame
    cos_th = math.cos(theta)
    sin_th = math.sin(theta)
    corners = [
        (x + a * cos_th - b * sin_th, y + a * sin_th + b * cos_th),
        (x + a * cos_th + b * sin_th, y + a * sin_th - b * cos_th),
        (x - a * cos_th - b * sin_th, y - a * sin_th + b * cos_th),
        (x - a * cos_th + b * sin_th, y - a * sin_th - b * cos_th),
    ]

    # In dead-end corridor region (x > 0.40 or y < 0.35):
    # south wall is y = -0.35, north wall is y = +0.35 (outside turning bay), east wall is x = 0.825
    min_dist = 999.0
    for cx, cy in corners:
        # Distance to south wall (y = -0.35)
        d_s = cy - (-0.35)
        if d_s < min_dist:
            min_dist = d_s
        # Distance to east wall (x = 0.825)
        d_e = 0.825 - cx
        if d_e < min_dist:
            min_dist = d_e
        # Distance to north wall (y = +0.35 for x < 0.0 or x > 0.40)
        if cx < 0.0 or cx > 0.40:
            d_n = 0.35 - cy
            if d_n < min_dist:
                min_dist = d_n
        else:
            # Inside turning bay opening (y extends to +0.75)
            d_tb_n = 0.75 - cy
            if d_tb_n < min_dist:
                min_dist = d_tb_n

    return float(min_dist)


def run_single_trace(config_id: int = 0) -> Dict[str, Any]:
    configs = build_50_matched_configurations()
    cfg = next(c for c in configs if c["config_id"] == config_id)

    xml_path = cfg["xml_path"]
    grid_path = cfg["grid_path"]
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]

    hal = CarlStage1HAL(xml_path=xml_path)
    hal.reset()

    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    controller = CARLActiveInferenceEngine(
        grid_path=grid_path,
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless",
    )
    controller.initialize_pose(sx, sy, syaw)

    gyro_only_heading = syaw
    cycle_records = []
    v_est = 0.0
    escaped = False
    had_collision = False

    max_ticks = 220
    for tick in range(max_ticks):
        # 1. Physical ground truth (evaluator only)
        q_curr = hal.data.qpos[qa:qa+7]
        true_x, true_y = float(q_curr[0]), float(q_curr[1])
        true_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        true_clearance = compute_actual_hull_clearance_env1(true_x, true_y, true_yaw)

        # 2. Sensors
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])
        gyro_only_heading += gyro_yaw * 0.030
        gyro_only_heading = math.atan2(math.sin(gyro_only_heading), math.cos(gyro_only_heading))

        # 3. Controller deliberation
        t0 = time.perf_counter()
        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        fused_heading = float(controller.pose[2])
        heading_err = math.atan2(math.sin(fused_heading - true_yaw), math.cos(fused_heading - true_yaw))
        gyro_err = math.atan2(math.sin(gyro_only_heading - true_yaw), math.cos(gyro_only_heading - true_yaw))

        # Record cycle
        rec = {
            "tick": tick,
            "physical_evaluator_pose": [true_x, true_y, float(true_yaw)],
            "internal_estimated_pose": [float(controller.pose[0]), float(controller.pose[1]), fused_heading],
            "gyro_only_heading": float(gyro_only_heading),
            "fused_heading": fused_heading,
            "heading_error_fused": float(heading_err),
            "heading_error_gyro": float(gyro_err),
            "lateral_offset": float(true_y),
            "predicted_hull_clearance": float(telem.get("min_predicted_hull_clearance", 0.0)),
            "actual_mujoco_clearance": true_clearance,
            "chosen_action": [float(action[0]), float(action[1])],
            "efe_total": float(telem.get("best_cost", 0.0)),
            "pragmatic_cost": float(telem.get("efe_pragmatic_mean", 0.0)),
            "epistemic_cost": float(telem.get("efe_epistemic_mean", 0.0)),
            "accepted_candidates": int(telem.get("accepted_candidates", 0)),
            "rejected_candidates": int(telem.get("rejected_candidates", 0)),
            "mppi_entropy": float(telem.get("ensemble_entropy", 0.0)),
            "selected_candidate_index": int(telem.get("best_sample_idx", 0)),
            "sonar_heading_confidence": float(telem.get("sonar_heading_confidence", 0.0)),
            "latency_ms": lat_ms,
        }
        cycle_records.append(rec)

        # 4. Step physics
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])
        hal.step(cmd_6d)

        # 5. Collision Check
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True
            break

        # 6. Escape Check
        if true_x <= -0.55:
            escaped = True
            break

        # Velocity tracking
        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

    trace_result = {
        "config_id": config_id,
        "env_id": 1,
        "env_name": cfg["env_name"],
        "spawn_pos": [sx, sy],
        "spawn_yaw": syaw,
        "escaped": escaped,
        "had_collision": had_collision,
        "ticks_executed": len(cycle_records),
        "mean_latency_ms": float(np.mean([r["latency_ms"] for r in cycle_records])),
        "p95_latency_ms": float(np.percentile([r["latency_ms"] for r in cycle_records], 95)),
        "min_actual_clearance": float(np.min([r["actual_mujoco_clearance"] for r in cycle_records])),
        "max_heading_error_gyro_deg": float(np.max([abs(math.degrees(r["heading_error_gyro"])) for r in cycle_records])),
        "max_heading_error_fused_deg": float(np.max([abs(math.degrees(r["heading_error_fused"])) for r in cycle_records])),
        "cycles": cycle_records,
    }

    out_file = EVIDENCE_DIR / "r4_single_episode_trace.json"
    with open(out_file, "w") as f:
        json.dump(trace_result, f, indent=2)

    print(f"Single Episode Trace Complete: config_id={config_id}")
    print(f"  Escaped: {escaped}, Collision: {had_collision}, Ticks: {len(cycle_records)}")
    print(f"  Min actual clearance: {trace_result['min_actual_clearance']:.4f} m")
    print(f"  Max Heading Error: Gyro={trace_result['max_heading_error_gyro_deg']:.2f} deg, Fused={trace_result['max_heading_error_fused_deg']:.2f} deg")
    print(f"  Latency: mean={trace_result['mean_latency_ms']:.2f} ms, p95={trace_result['p95_latency_ms']:.2f} ms")
    print(f"Saved to {out_file}")

    return trace_result


if __name__ == "__main__":
    run_single_trace(0)
