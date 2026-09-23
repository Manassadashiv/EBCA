"""
tests/run_stage3_4R4_3_screening.py — Stage 3.4-R4.3 Quick 10-Config Screening
Runs ARM-A on configs 0-4 (Env1) and 20-24 (Env2) to verify geodesic-gradient
heading alignment before launching the full 200-episode certification battery.
"""
import sys
import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4_3"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

SCREENING_CONFIG_IDS = [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]
MAX_TICKS = 220


def run_episode(cfg: Dict[str, Any], arm_w_info: float = 1.0) -> Dict[str, Any]:
    env_id = cfg["env_id"]
    xml_path = str(ENV1_XML if env_id == 1 else ENV2_XML)
    grid_path = str(ENV1_GRID if env_id == 1 else ENV2_GRID)

    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    seed = cfg["seed"]

    np.random.seed(seed)
    torch.manual_seed(seed)

    hal = CarlStage1HAL(xml_path=xml_path)
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    ctrl = CARLActiveInferenceEngine(
        grid_path=grid_path,
        w_info=arm_w_info,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    ctrl.initialize_pose(sx, sy, syaw)

    had_collision = False
    escaped = False
    v_est = 0.0
    latencies = []
    heading_errors = []
    veto_fracs = []
    stagnant = 0
    max_stagnant = 0
    prev_y = sy

    # Phase tracking
    reversed_ticks = 0
    max_turn_delta = 0.0
    entered_channel = False
    fwd_egress_ticks = 0

    for tick in range(MAX_TICKS):
        sensors = hal.read_sensors()
        gyro_w = float(sensors[20])
        dt = ctrl.dt

        ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_w, dt=dt)

        t0 = time.perf_counter()
        u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=gyro_w)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

        # Ground truth (evaluator only)
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        true_x, true_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        quat = hal.data.qpos[qa+3:qa+7]
        true_yaw = math.atan2(2.0 * (quat[0]*quat[3] + quat[1]*quat[2]),
                               1.0 - 2.0 * (quat[2]*quat[2] + quat[3]*quat[3]))

        fused_yaw = float(ctrl.pose[2])
        h_err = math.degrees(abs(math.atan2(math.sin(fused_yaw - true_yaw),
                                             math.cos(fused_yaw - true_yaw))))
        heading_errors.append(h_err)

        total_cand = telem.get("mppi_samples", 128)
        rej_cand = telem.get("rejected_candidates", 0)
        veto_fracs.append(rej_cand / total_cand)

        # Physics step
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(u_star[0])
        cmd_6d[1] = float(u_star[1])
        hal.step(cmd_6d)

        # Post-step
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        new_x, new_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        # Stagnation
        if env_id == 2:
            if new_y >= prev_y - 0.005:
                stagnant += 1
            else:
                stagnant = 0
        else:
            if abs(new_y - prev_y) < 0.005 and abs(new_x - true_x) < 0.005:
                stagnant += 1
            else:
                stagnant = 0
        max_stagnant = max(max_stagnant, stagnant)
        prev_y = new_y

        # Phase tracking
        if u_fwd < -0.05:
            reversed_ticks += 1
        new_quat = hal.data.qpos[qa+3:qa+7]
        new_yaw = math.atan2(2.0 * (new_quat[0]*new_quat[3] + new_quat[1]*new_quat[2]),
                              1.0 - 2.0 * (new_quat[2]*new_quat[2] + new_quat[3]*new_quat[3]))
        delta_th = abs(math.degrees(math.atan2(math.sin(new_yaw - syaw), math.cos(new_yaw - syaw))))
        max_turn_delta = max(max_turn_delta, delta_th)

        # Channel entry: y < -0.50 for Env2
        if env_id == 2 and new_y < -0.50:
            entered_channel = True
        elif env_id == 1 and new_y < -0.10:
            entered_channel = True

        if u_fwd > 0.05:
            fwd_egress_ticks += 1

        # Collision
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True

        # Escape check
        if env_id == 2 and new_y <= -1.20:
            escaped = True
        elif env_id == 1 and new_y <= -0.10:
            escaped = True

        if had_collision or escaped:
            break

    outcome = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")
    lat_arr = np.array(latencies)
    herr_arr = np.array(heading_errors)
    veto_arr = np.array(veto_fracs)

    phases = {
        "phase1_reversal": reversed_ticks >= 10,
        "phase2_orientation": max_turn_delta >= 80.0,
        "phase3_channel_entry": entered_channel,
        "phase4_forward_egress": fwd_egress_ticks >= 15,
    }

    return {
        "arm": "ARM-A",
        "config_id": cfg["config_id"],
        "env_id": env_id,
        "seed": seed,
        "outcome": outcome,
        "ticks_executed": tick + 1,
        "complete_maneuver": all(phases.values()),
        "mean_latency_ms": round(float(np.mean(lat_arr)), 2),
        "p95_latency_ms": round(float(np.percentile(lat_arr, 95)), 2),
        "mean_heading_error_deg": round(float(np.mean(herr_arr)), 2),
        "max_heading_error_deg": round(float(np.max(herr_arr)), 2),
        "p95_heading_error_deg": round(float(np.percentile(herr_arr, 95)), 2),
        "min_clearance_m": round(float(np.min(lat_arr) * 0 + telem.get("min_predicted_hull_clearance", 0.0)), 4),
        "mean_candidate_veto_frac": round(float(np.mean(veto_arr)), 3),
        "max_stagnant_ticks": max_stagnant,
        "final_y": round(new_y, 4),
        "final_x": round(new_x, 4),
        "phases": phases,
    }


def main():
    print("=" * 60)
    print("STAGE 3.4-R4.3 SCREENING (10 CONFIGS, ARM-A)")
    print("=" * 60)
    print()

    configs = build_50_matched_configurations()
    cfg_map = {c["config_id"]: c for c in configs}

    results = []
    for cfg_id in SCREENING_CONFIG_IDS:
        cfg = cfg_map[cfg_id]
        env_name = "Env1" if cfg["env_id"] == 1 else "Env2"
        print(f"Running config {cfg_id} ({env_name})... ", end="", flush=True)
        t0 = time.time()
        result = run_episode(cfg)
        elapsed = time.time() - t0
        print(f"{result['outcome']:10s} ticks={result['ticks_executed']:3d} final_y={result['final_y']:.3f} "
              f"lat={result['mean_latency_ms']:.1f}ms veto={result['mean_candidate_veto_frac']:.2f} "
              f"phases={result['phases']} ({elapsed:.1f}s)")
        results.append(result)

    # Save
    out_file = EVIDENCE_DIR / "r4_3_screening_trials.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    env1 = [r for r in results if r["env_id"] == 1]
    env2 = [r for r in results if r["env_id"] == 2]

    print()
    print("=" * 60)
    print("SCREENING SUMMARY")
    print("=" * 60)
    print(f"Env1 ({len(env1)}): escapes={sum(1 for r in env1 if r['outcome']=='ESCAPE')}"
          f" collisions={sum(1 for r in env1 if r['outcome']=='COLLISION')}"
          f" timeouts={sum(1 for r in env1 if r['outcome']=='TIMEOUT')}")
    print(f"Env2 ({len(env2)}): escapes={sum(1 for r in env2 if r['outcome']=='ESCAPE')}"
          f" collisions={sum(1 for r in env2 if r['outcome']=='COLLISION')}"
          f" timeouts={sum(1 for r in env2 if r['outcome']=='TIMEOUT')}")
    print(f"Env2 phase3_channel_entry: {sum(1 for r in env2 if r['phases']['phase3_channel_entry'])}/{len(env2)}")

    scorecard = {
        "n_trials": len(results),
        "escapes": sum(1 for r in results if r["outcome"] == "ESCAPE"),
        "collisions": sum(1 for r in results if r["outcome"] == "COLLISION"),
        "timeouts": sum(1 for r in results if r["outcome"] == "TIMEOUT"),
        "env2_escapes": sum(1 for r in env2 if r["outcome"] == "ESCAPE"),
        "env2_collisions": sum(1 for r in env2 if r["outcome"] == "COLLISION"),
        "env2_timeouts": sum(1 for r in env2 if r["outcome"] == "TIMEOUT"),
        "env2_channel_entry_rate": sum(1 for r in env2 if r["phases"]["phase3_channel_entry"]) / max(1, len(env2)),
        "mean_latency_ms": round(float(np.mean([r["mean_latency_ms"] for r in results])), 2),
        "p95_latency_ms": round(float(np.max([r["p95_latency_ms"] for r in results])), 2),
    }

    sc_file = EVIDENCE_DIR / "r4_3_screening_scorecard.json"
    with open(sc_file, "w") as f:
        json.dump(scorecard, f, indent=2)

    print(f"\nSaved: {out_file}")
    print(f"Saved: {sc_file}")


if __name__ == "__main__":
    main()
