"""
tests/diagnostic_stage3_4R_preflight.py — Stage 3.4-R Pre-Flight Factorial Diagnostic
Classification: [STAGE 3.4-R DIAGNOSTIC] Non-Binding Factorial Assessment (N = 10 Trials)

Evaluates Stage 3.4 Local EFE (w_info=1.0, lambda_frontier=0.0) in the 1.30m Turning Bay environment
across the 10 pre-registered frozen configurations:
- Seed 5001: Configs 0, 1
- Seed 5002: Configs 4, 5
- Seed 5003: Configs 8, 9
- Seed 5004: Configs 12, 13
- Seed 5005: Configs 16, 17

Scientific Question Answered:
"Does physical turning clearance ALONE enable complete multi-step escape under local EFE?"

Strict Governance Rule:
This diagnostic is exploratory and non-binding. Outcomes SHALL NOT alter, relax, or re-tune
certification gates, weights, geometry, or sample allocations.
"""

import sys
import os
import time
import math
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

ENV_DIR = repo_root / "world" / "stage3_4_environments"
XML_PATH = ENV_DIR / "cul_de_sac_turning_bay.xml"
GRID_PATH = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

PRE_REGISTERED_SEEDS = [5001, 5002, 5003, 5004, 5005]
DIAGNOSTIC_CONFIG_IDS = [0, 1, 4, 5, 8, 9, 12, 13, 16, 17]
MAX_TICKS = 220
ESCAPE_X_THRESHOLD = -0.55


def build_env1_configurations() -> List[Dict[str, Any]]:
    """Builds the 20 matched configurations for Environment 1."""
    base_variations = [
        {"dx": 0.00, "dy":  0.00, "dth":  0.00},
        {"dx": 0.08, "dy":  0.05, "dth":  0.08},
        {"dx": 0.08, "dy": -0.05, "dth": -0.08},
        {"dx": 0.15, "dy":  0.00, "dth":  0.05},
    ]
    base_x = 0.50
    manifest = []
    config_id = 0

    for seed in PRE_REGISTERED_SEEDS:
        rng = np.random.RandomState(seed)
        for v_idx, var in enumerate(base_variations):
            jx = float(rng.uniform(-0.015, 0.015))
            jy = float(rng.uniform(-0.010, 0.010))
            jth = float(rng.uniform(-0.020, 0.020))

            x0 = float(np.clip(base_x + var["dx"] + jx, 0.40, 0.75))
            y0 = float(np.clip(var["dy"] + jy, -0.12, 0.12))
            th0 = float(np.clip(var["dth"] + jth, -0.18, 0.18))

            manifest.append({
                "config_id": config_id,
                "seed": seed,
                "variation_idx": v_idx,
                "spawn_pos": [x0, y0],
                "spawn_yaw": th0,
            })
            config_id += 1

    return manifest


def run_preflight_diagnostic() -> Dict[str, Any]:
    print("=" * 80)
    print("STAGE 3.4-R PRE-FLIGHT FACTORIAL DIAGNOSTIC (N = 10 TRIALS)")
    print("Geometry: 1.30m Turning Bay (cul_de_sac_turning_bay.xml)")
    print("Controller: Stage 3.4 Local EFE (w_info=1.0, lambda_frontier=0.0)")
    print("=" * 80)

    configs = build_env1_configurations()
    diag_configs = [c for c in configs if c["config_id"] in DIAGNOSTIC_CONFIG_IDS]
    assert len(diag_configs) == 10, f"Expected 10 diagnostic configurations, got {len(diag_configs)}"

    hal = CarlStage1HAL(xml_path=str(XML_PATH))
    results = []

    for idx, cfg in enumerate(diag_configs):
        cid = cfg["config_id"]
        seed = cfg["seed"]
        sx, sy = cfg["spawn_pos"]
        syaw = cfg["spawn_yaw"]

        # Reset MuJoCo physics
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        # Stage 3.4 Local EFE controller (no frontier potential)
        controller = CARLActiveInferenceEngine(grid_path=str(GRID_PATH), w_info=1.0)
        controller.initialize_pose(sx, sy, syaw)

        trajectory = []
        had_collision = False
        escaped = False
        reversal_ticks = 0
        consecutive_rev = 0
        max_consec_rev = 0
        v_est = 0.0
        max_yaw_rot_deg = 0.0

        for tick in range(MAX_TICKS):
            sensors = hal.read_sensors()
            sonars = sensors[:15]
            gyro_yaw = float(sensors[20])

            controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
            action, _ = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)

            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(action[0])
            cmd_6d[1] = float(action[1])
            hal.step(cmd_6d)

            # Evaluator telemetry
            q_curr = hal.data.qpos[qa:qa+7]
            curr_pos = [float(q_curr[0]), float(q_curr[1])]
            trajectory.append(curr_pos)

            curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
            rot_deg = math.degrees(abs(math.atan2(math.sin(curr_yaw - syaw), math.cos(curr_yaw - syaw))))
            if rot_deg > max_yaw_rot_deg:
                max_yaw_rot_deg = rot_deg

            # Wheel speed
            w_l_id = hal.model.sensor("sens_vel_w_left").id
            w_r_id = hal.model.sensor("sens_vel_w_right").id
            w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
            w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
            wheel_spd = 0.5 * (w_left_vel + w_right_vel) * 0.048

            if wheel_spd < -0.05:
                reversal_ticks += 1
                consecutive_rev += 1
                if consecutive_rev > max_consec_rev:
                    max_consec_rev = consecutive_rev
            else:
                consecutive_rev = 0

            # Contacts
            c_info = hal.get_carl_contact_info()
            wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
            if wall_contacts > 0:
                had_collision = True
                break

            # Escape
            if curr_pos[0] <= ESCAPE_X_THRESHOLD:
                escaped = True
                break

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        res = {
            "config_id": cid,
            "seed": seed,
            "escaped": escaped,
            "had_collision": had_collision,
            "ticks": tick + 1,
            "max_consecutive_reversals": max_consec_rev,
            "max_yaw_rotation_deg": float(max_yaw_rot_deg),
            "final_pos": trajectory[-1] if trajectory else [sx, sy],
        }
        results.append(res)
        status = "ESCAPED" if escaped else ("COLLISION" if had_collision else "TIMEOUT/STALL")
        print(f"  Trial {idx+1:2d}/10 [Config {cid:2d}, Seed {seed}]: {status:<15} (ticks={tick+1}, rot={max_yaw_rot_deg:5.1f}°, rev_ticks={max_consec_rev})")

    # Summary
    num_escaped = sum(1 for r in results if r["escaped"])
    num_collision = sum(1 for r in results if r["had_collision"])
    num_stall = 10 - num_escaped - num_collision

    summary = {
        "milestone": "Stage 3.4-R Pre-Flight Factorial Diagnostic",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_size": 10,
        "controller": "Stage 3.4 Local EFE (w_info=1.0, lambda_frontier=0.0)",
        "geometry": "1.30m Turning Bay (cul_de_sac_turning_bay.xml)",
        "escaped_count": num_escaped,
        "escape_rate_pct": float(num_escaped / 10.0 * 100.0),
        "collision_count": num_collision,
        "collision_rate_pct": float(num_collision / 10.0 * 100.0),
        "stall_count": num_stall,
        "stall_rate_pct": float(num_stall / 10.0 * 100.0),
        "trials": results,
    }

    out_path = EVIDENCE_DIR / "stage3_4R_preflight_diagnostic.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("PRE-FLIGHT DIAGNOSTIC OUTCOME:")
    print(f"  Escaped:    {num_escaped}/10 ({summary['escape_rate_pct']:.1f}%)")
    print(f"  Collision:  {num_collision}/10 ({summary['collision_rate_pct']:.1f}%)")
    print(f"  Stall:      {num_stall}/10 ({summary['stall_rate_pct']:.1f}%)")
    print(f"Saved diagnostic report to: {out_path}")
    print("=" * 80)
    return summary


if __name__ == "__main__":
    run_preflight_diagnostic()
