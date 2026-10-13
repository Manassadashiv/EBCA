"""
tests/test_stage3_4R4_screening.py — 10-Configuration Matched Screening Battery for Stage 3.4-R4
Evaluates ARM-A (Full R4) vs ARM-B (Pragmatic-only) across 10 matched configurations:
  Configs 0–4 (Environment 1: Turning-Bay Cul-de-Sac)
  Configs 20–24 (Environment 2: Asymmetric T-Junction)
Saves:
  evidence/stage3_4R4/r4_raw_trials.json
  evidence/stage3_4R4/r4_screening_scorecard.json
  evidence/stage3_4R4/r4_latency.json
"""

import sys
import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.stats as stats
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations, compute_exact_mcnemar

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

SCREENING_CONFIG_IDS = [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]
MAX_TICKS = 260


def execute_screening_episode(
    arm: str,
    config: Dict[str, Any],
    hal: CarlStage1HAL
) -> Dict[str, Any]:
    env_id = config["env_id"]
    grid_path = config["grid_path"]
    sx, sy = config["spawn_pos"]
    syaw = config["spawn_yaw"]

    # 1. Physics Reset & Deterministic Seeds
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    # 2. Controller Instantiation
    w_info = 1.0 if arm == "ARM-A" else 0.0
    controller = CARLActiveInferenceEngine(
        grid_path=grid_path,
        w_info=w_info,
        frontier_mode="macro",
        norm_mode="dimensionless",
    )
    controller.initialize_pose(sx, sy, syaw)

    trajectory = []
    actions_taken = []
    cycle_latencies = []
    heading_errors = []
    lateral_offsets = []
    predicted_clearances = []
    candidate_rejection_fracs = []
    reversal_ticks = 0
    consecutive_rev = 0
    max_consec_rev = 0
    v_est = 0.0

    had_collision = False
    escaped = False

    # Gate 2 tracking
    phase1_reversal = False
    phase2_orientation = False
    phase3_channel_entry = False
    phase4_forward_egress = False
    consecutive_forward_egress = 0
    max_yaw_rot_deg = 0.0

    for tick in range(MAX_TICKS):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])

        t0 = time.perf_counter()
        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        cycle_latencies.append(lat_ms)

        # Telemetry metrics
        predicted_clearances.append(float(telem.get("min_predicted_hull_clearance", 0.0)))
        n_rej = telem.get("rejected_candidates", 0)
        n_tot = telem.get("accepted_candidates", 128) + n_rej
        candidate_rejection_fracs.append(n_rej / max(1, n_tot))

        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])
        actions_taken.append([float(action[0]), float(action[1])])

        hal.step(cmd_6d)

        # Evaluator Telemetry Firewall
        q_curr = hal.data.qpos[qa:qa+7]
        curr_pos = [float(q_curr[0]), float(q_curr[1])]
        trajectory.append(curr_pos)
        lateral_offsets.append(abs(curr_pos[1]))

        curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        rot_deg = math.degrees(abs(math.atan2(math.sin(curr_yaw - syaw), math.cos(curr_yaw - syaw))))
        if rot_deg > max_yaw_rot_deg:
            max_yaw_rot_deg = rot_deg

        h_err = abs(math.atan2(math.sin(float(controller.pose[2]) - curr_yaw), math.cos(float(controller.pose[2]) - curr_yaw)))
        heading_errors.append(h_err)

        # Wheel velocity
        w_l_id = hal.model.sensor("sens_vel_w_left").id
        w_r_id = hal.model.sensor("sens_vel_w_right").id
        w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
        w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
        wheel_spd = 0.5 * (w_left_vel + w_right_vel) * 0.048

        # Track reversals
        if wheel_spd < -0.05:
            reversal_ticks += 1
            consecutive_rev += 1
            if consecutive_rev > max_consec_rev:
                max_consec_rev = consecutive_rev
        else:
            consecutive_rev = 0

        if consecutive_rev >= 10:
            phase1_reversal = True

        if phase1_reversal and rot_deg >= 90.0:
            phase2_orientation = True

        if phase2_orientation:
            if env_id == 1 and curr_pos[0] <= 0.35:
                phase3_channel_entry = True
            elif env_id == 2 and curr_pos[1] <= -0.40:
                phase3_channel_entry = True

        if phase3_channel_entry:
            if wheel_spd >= 0.05:
                consecutive_forward_egress += 1
                if consecutive_forward_egress >= 15:
                    phase4_forward_egress = True
            else:
                consecutive_forward_egress = 0

        # Collision Check
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True
            break

        # Escape Check
        if env_id == 1 and curr_pos[0] <= -0.55:
            escaped = True
            break
        elif env_id == 2 and curr_pos[1] <= -1.20:
            escaped = True
            break

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.65 * v_est + 0.35 * (u_fwd * 0.35)

    timeout = not escaped and not had_collision
    gate2_emergent_complete = bool(
        phase1_reversal and phase2_orientation and phase3_channel_entry and phase4_forward_egress and not had_collision
    )

    return {
        "config_id": config["config_id"],
        "env_id": env_id,
        "env_name": config["env_name"],
        "seed": config["seed"],
        "arm": arm,
        "escaped": escaped,
        "had_collision": had_collision,
        "timeout": timeout,
        "ticks": len(trajectory),
        "mean_latency_ms": float(np.mean(cycle_latencies)) if cycle_latencies else 0.0,
        "p95_latency_ms": float(np.percentile(cycle_latencies, 95)) if cycle_latencies else 0.0,
        "latencies": cycle_latencies,
        "mean_heading_error_deg": float(math.degrees(np.mean(heading_errors))) if heading_errors else 0.0,
        "max_lateral_drift_m": float(np.max(lateral_offsets)) if lateral_offsets else 0.0,
        "mean_lateral_drift_m": float(np.mean(lateral_offsets)) if lateral_offsets else 0.0,
        "min_predicted_hull_clearance": float(np.min(predicted_clearances)) if predicted_clearances else 0.0,
        "mean_rejection_fraction": float(np.mean(candidate_rejection_fracs)) if candidate_rejection_fracs else 0.0,
        "max_consecutive_reversals": max_consec_rev,
        "max_yaw_rotation_deg": float(max_yaw_rot_deg),
        "gate2_emergent_complete": gate2_emergent_complete,
        "trajectory": trajectory,
        "actions": actions_taken,
    }


def run_screening_battery() -> Dict[str, Any]:
    all_configs = build_50_matched_configurations()
    screening_configs = [c for c in all_configs if c["config_id"] in SCREENING_CONFIG_IDS]

    # Preload HALs for each environment
    env1_xml = screening_configs[0]["xml_path"]
    env2_xml = next(c["xml_path"] for c in screening_configs if c["env_id"] == 2)
    hal_env1 = CarlStage1HAL(xml_path=env1_xml)
    hal_env2 = CarlStage1HAL(xml_path=env2_xml)

    trials = []
    print(f"Starting Stage 3.4-R4 Matched Screening Battery (10 configs x 2 arms = 20 episodes)...")

    for cfg in screening_configs:
        hal = hal_env1 if cfg["env_id"] == 1 else hal_env2
        for arm in ["ARM-A", "ARM-B"]:
            t0 = time.time()
            res = execute_screening_episode(arm, cfg, hal)
            dur = time.time() - t0
            trials.append(res)
            status = "ESCAPED" if res["escaped"] else ("COLLIDED" if res["had_collision"] else "TIMEOUT")
            print(f"  Cfg {cfg['config_id']:02d} ({cfg['env_name'][:10]}) | {arm} -> {status} (ticks={res['ticks']}, lat={res['mean_latency_ms']:.1f}ms, p95={res['p95_latency_ms']:.1f}ms) [{dur:.1f}s]")

    # Save raw trials
    with open(EVIDENCE_DIR / "r4_raw_trials.json", "w") as f:
        json.dump(trials, f, indent=2)

    # Compute matched metrics
    arm_a_trials = [t for t in trials if t["arm"] == "ARM-A"]
    arm_b_trials = [t for t in trials if t["arm"] == "ARM-B"]

    n_screen = len(arm_a_trials)
    esc_a = sum(1 for t in arm_a_trials if t["escaped"])
    col_a = sum(1 for t in arm_a_trials if t["had_collision"])
    to_a = sum(1 for t in arm_a_trials if t["timeout"])
    g2_a = sum(1 for t in arm_a_trials if t["gate2_emergent_complete"])

    esc_b = sum(1 for t in arm_b_trials if t["escaped"])
    col_b = sum(1 for t in arm_b_trials if t["had_collision"])
    to_b = sum(1 for t in arm_b_trials if t["timeout"])
    g2_b = sum(1 for t in arm_b_trials if t["gate2_emergent_complete"])

    # McNemar on paired escapes
    esc_flags_a = [t["escaped"] for t in arm_a_trials]
    esc_flags_b = [t["escaped"] for t in arm_b_trials]
    b, c, delta_pct, mcnemar_p = compute_exact_mcnemar(esc_flags_a, esc_flags_b)

    # Action divergence between ARM-A and ARM-B on common ticks
    divergences = []
    for ta, tb in zip(arm_a_trials, arm_b_trials):
        min_len = min(len(ta["actions"]), len(tb["actions"]))
        if min_len > 0:
            act_a = np.array(ta["actions"][:min_len])
            act_b = np.array(tb["actions"][:min_len])
            div = np.mean(np.linalg.norm(act_a - act_b, axis=1))
            divergences.append(float(div))
    mean_divergence = float(np.mean(divergences)) if divergences else 0.0

    # Latency collection across all cycles
    all_latencies_a = [lat for t in arm_a_trials for lat in t["latencies"]]
    mean_lat = float(np.mean(all_latencies_a))
    p50_lat = float(np.median(all_latencies_a))
    p95_lat = float(np.percentile(all_latencies_a, 95))
    p99_lat = float(np.percentile(all_latencies_a, 99))
    max_lat = float(np.max(all_latencies_a))

    latency_summary = {
        "sample_count": len(all_latencies_a),
        "mean_ms": mean_lat,
        "median_ms": p50_lat,
        "p95_ms": p95_lat,
        "p99_ms": p99_lat,
        "max_ms": max_lat,
        "budget_mean_pass": bool(mean_lat <= 20.0),
        "budget_p95_pass": bool(p95_lat <= 45.0),
    }
    with open(EVIDENCE_DIR / "r4_latency.json", "w") as f:
        json.dump(latency_summary, f, indent=2)

    scorecard = {
        "benchmark_type": "DIAGNOSTIC SCREENING — NOT CERTIFICATION",
        "sample_size": n_screen,
        "tested_configs": SCREENING_CONFIG_IDS,
        "arm_a": {
            "escaped": esc_a,
            "escape_rate_pct": (esc_a / n_screen) * 100.0,
            "collided": col_a,
            "collision_rate_pct": (col_a / n_screen) * 100.0,
            "timeout": to_a,
            "timeout_rate_pct": (to_a / n_screen) * 100.0,
            "gate2_complete": g2_a,
            "gate2_rate_pct": (g2_a / n_screen) * 100.0,
            "mean_heading_error_deg": float(np.mean([t["mean_heading_error_deg"] for t in arm_a_trials])),
            "mean_lateral_drift_m": float(np.mean([t["mean_lateral_drift_m"] for t in arm_a_trials])),
            "min_hull_clearance_m": float(np.min([t["min_predicted_hull_clearance"] for t in arm_a_trials])),
            "mean_candidate_rejection_frac": float(np.mean([t["mean_rejection_fraction"] for t in arm_a_trials])),
        },
        "arm_b": {
            "escaped": esc_b,
            "escape_rate_pct": (esc_b / n_screen) * 100.0,
            "collided": col_b,
            "collision_rate_pct": (col_b / n_screen) * 100.0,
            "timeout": to_b,
            "timeout_rate_pct": (to_b / n_screen) * 100.0,
            "gate2_complete": g2_b,
            "gate2_rate_pct": (g2_b / n_screen) * 100.0,
        },
        "comparative": {
            "delta_escape_pct": delta_pct,
            "mcnemar_b": b,
            "mcnemar_c": c,
            "mcnemar_p_value": mcnemar_p,
            "mean_action_divergence": mean_divergence,
        },
        "latency": latency_summary,
    }

    with open(EVIDENCE_DIR / "r4_screening_scorecard.json", "w") as f:
        json.dump(scorecard, f, indent=2)

    print("\n================ SCREENING SCORECARD ================")
    print(f"ARM-A Escapes: {esc_a}/{n_screen} ({scorecard['arm_a']['escape_rate_pct']:.1f}%), Collisions: {col_a}/{n_screen} ({scorecard['arm_a']['collision_rate_pct']:.1f}%)")
    print(f"ARM-B Escapes: {esc_b}/{n_screen} ({scorecard['arm_b']['escape_rate_pct']:.1f}%), Collisions: {col_b}/{n_screen} ({scorecard['arm_b']['collision_rate_pct']:.1f}%)")
    print(f"Delta: {delta_pct:+.1f}%, McNemar p: {mcnemar_p:.4f}, Action Div: {mean_divergence:.3f}")
    print(f"Latency: Mean={mean_lat:.2f} ms (budget <= 20 ms: {latency_summary['budget_mean_pass']}), p95={p95_lat:.2f} ms (budget <= 45 ms: {latency_summary['budget_p95_pass']})")
    print(f"Scorecard saved to {EVIDENCE_DIR / 'r4_screening_scorecard.json'}")

    return scorecard


if __name__ == "__main__":
    run_screening_battery()
