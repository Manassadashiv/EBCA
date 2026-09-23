"""
tests/forensic_channel_entry_analysis.py — Forensic Analysis of Channel Entry Instant (Configs 20-24)

Measures physical and algorithmic variables at the exact moment CARL enters or attempts to enter
the narrow south channel in Environment 2:
  x_entry, y_entry, theta_entry, v_entry, omega_entry, d_L, d_R, d_min, veto_frac, N_feas
Classifies failures into:
  L = lateral misalignment
  Y = yaw misalignment
  V = excessive entry velocity
  H = candidate/hull starvation
  C = coupled
Separates latency into:
  Cold-start (tick 0) vs Steady-state (ticks >= 1)
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
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4_3"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CONFIG_IDS = [20, 21, 22, 23, 24]
MAX_TICKS = 220
CHANNEL_ENTRY_Y_THRESHOLD = -0.35  # South corridor entrance transition zone
CHANNEL_CENTERLINE_X = 0.825       # Midpoint between West wall (0.50) and East wall (1.15)
TARGET_YAW_SOUTH = -math.pi / 2.0  # -1.5708 rad (-90 deg)


def run_forensic_episode(cfg: Dict[str, Any]) -> Dict[str, Any]:
    cfg_id = cfg["config_id"]
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    seed = cfg["seed"]

    np.random.seed(seed)
    torch.manual_seed(seed)

    hal = CarlStage1HAL(xml_path=str(ENV2_XML))
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    ctrl = CARLActiveInferenceEngine(
        grid_path=str(ENV2_GRID),
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    ctrl.initialize_pose(sx, sy, syaw)

    had_collision = False
    escaped = False
    v_est = 0.0
    
    ticks_data = []
    latencies_all = []
    latencies_steady = []
    cold_start_lat_ms = 0.0

    entry_instant_record = None
    min_y_reached = sy

    for tick in range(MAX_TICKS):
        sensors = hal.read_sensors()
        gyro_w = float(sensors[20])
        dt = ctrl.dt

        ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_w, dt=dt)

        t0 = time.perf_counter()
        u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=gyro_w)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies_all.append(lat_ms)
        if tick == 0:
            cold_start_lat_ms = lat_ms
        else:
            latencies_steady.append(lat_ms)

        # Ground truth evaluation
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        true_x, true_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        quat = hal.data.qpos[qa+3:qa+7]
        true_yaw = math.atan2(2.0 * (quat[0]*quat[3] + quat[1]*quat[2]),
                               1.0 - 2.0 * (quat[2]*quat[2] + quat[3]*quat[3]))

        fused_x, fused_y, fused_yaw = float(ctrl.pose[0]), float(ctrl.pose[1]), float(ctrl.pose[2])
        h_err_deg = math.degrees(abs(math.atan2(math.sin(fused_yaw - true_yaw), math.cos(fused_yaw - true_yaw))))

        d_sonars = sensors[0:15]
        d_L = float(sensors[12])  # Ray 12 (+85.7 deg left)
        d_R = float(sensors[2])   # Ray 2 (-85.7 deg right)
        d_min = float(np.min(d_sonars))

        total_cand = telem.get("mppi_samples", 128)
        rej_cand = telem.get("rejected_candidates", 0)
        veto_frac = rej_cand / total_cand
        n_feas = total_cand - rej_cand
        th_des = telem.get("th_des", 0.0)

        # Physics step
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(u_star[0])
        cmd_6d[1] = float(u_star[1])
        hal.step(cmd_6d)

        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        new_x, new_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        # Check contact
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True

        if new_y <= -1.20:
            escaped = True

        tick_rec = {
            "tick": tick,
            "x": round(new_x, 4),
            "y": round(new_y, 4),
            "yaw_deg": round(math.degrees(true_yaw), 2),
            "fused_yaw_deg": round(math.degrees(fused_yaw), 2),
            "heading_err_deg": round(h_err_deg, 2),
            "v_est": round(v_est, 4),
            "gyro_w": round(gyro_w, 4),
            "u_fwd": round(u_fwd, 4),
            "u_diff": round(float(cmd_6d[1] - cmd_6d[0]), 4),
            "d_L": round(d_L, 4),
            "d_R": round(d_R, 4),
            "d_min": round(d_min, 4),
            "veto_frac": round(veto_frac, 3),
            "n_feas": n_feas,
            "th_des_deg": round(math.degrees(th_des), 2),
            "wall_contacts": wall_contacts,
        }
        ticks_data.append(tick_rec)

        if new_y < min_y_reached:
            min_y_reached = new_y

        # Detect channel entry instant: first time crossing y <= CHANNEL_ENTRY_Y_THRESHOLD
        if entry_instant_record is None and new_y <= CHANNEL_ENTRY_Y_THRESHOLD:
            entry_instant_record = dict(tick_rec)
            entry_instant_record["event"] = "ENTRY_THRESHOLD_CROSSED"

        if had_collision or escaped:
            break

    # If never crossed entry threshold, take the instant of maximum southward progression (lowest y)
    if entry_instant_record is None:
        best_idx = int(np.argmin([t["y"] for t in ticks_data]))
        entry_instant_record = dict(ticks_data[best_idx])
        entry_instant_record["event"] = "CLOSEST_APPROACH_TO_CHANNEL"

    # Terminal record
    terminal_record = ticks_data[-1]
    outcome = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")

    # Diagnostic classification at entry instant
    entry_x = entry_instant_record["x"]
    entry_yaw = entry_instant_record["yaw_deg"]
    entry_v = entry_instant_record["v_est"]
    entry_veto = entry_instant_record["veto_frac"]
    entry_nfeas = entry_instant_record["n_feas"]

    # Target heading South is -90 deg
    yaw_err_to_south = abs(math.atan2(math.sin(math.radians(entry_yaw) - TARGET_YAW_SOUTH),
                                      math.cos(math.radians(entry_yaw) - TARGET_YAW_SOUTH)))
    yaw_err_deg = math.degrees(yaw_err_to_south)

    # Lateral distance to channel centerline (0.825m)
    lat_err_m = abs(entry_x - CHANNEL_CENTERLINE_X)

    # Classification flags
    is_L = lat_err_m > 0.10     # Lateral misalignment (> 10 cm off center)
    is_Y = yaw_err_deg > 18.0   # Yaw misalignment (> 18 deg off -90 deg)
    is_V = entry_v > 0.15       # Excessive speed
    is_H = entry_veto > 0.65 or entry_nfeas < 25  # Severe candidate starvation

    causes = []
    if is_L: causes.append("L")
    if is_Y: causes.append("Y")
    if is_V: causes.append("V")
    if is_H: causes.append("H")

    if len(causes) > 1:
        primary_class = f"C({'/'.join(causes)})"
    elif len(causes) == 1:
        primary_class = causes[0]
    else:
        primary_class = "NOMINAL"

    return {
        "config_id": cfg_id,
        "seed": seed,
        "outcome": outcome,
        "ticks_total": len(ticks_data),
        "terminal_state": terminal_record,
        "entry_instant": entry_instant_record,
        "classification": primary_class,
        "classification_flags": {
            "lateral_misalignment_L": is_L,
            "lateral_offset_m": round(lat_err_m, 4),
            "yaw_misalignment_Y": is_Y,
            "yaw_error_to_south_deg": round(yaw_err_deg, 2),
            "excessive_velocity_V": is_V,
            "entry_v": round(entry_v, 4),
            "hull_starvation_H": is_H,
            "entry_veto_frac": round(entry_veto, 3),
            "entry_n_feas": entry_nfeas,
        },
        "latency_metrics": {
            "cold_start_tick0_ms": round(cold_start_lat_ms, 2),
            "steady_state_mean_ms": round(float(np.mean(latencies_steady)), 2) if latencies_steady else 0.0,
            "steady_state_p95_ms": round(float(np.percentile(latencies_steady, 95)), 2) if latencies_steady else 0.0,
            "steady_state_max_ms": round(float(np.max(latencies_steady)), 2) if latencies_steady else 0.0,
            "all_mean_ms": round(float(np.mean(latencies_all)), 2),
            "all_p95_ms": round(float(np.percentile(latencies_all, 95)), 2),
        },
        "ticks_trace": ticks_data,
    }


def main():
    print("=" * 70)
    print("STAGE 3.4-R4.3 FORENSIC CHANNEL-ENTRY INSTANT ANALYSIS (CONFIGS 20-24)")
    print("=" * 70)

    configs = build_50_matched_configurations()
    cfg_map = {c["config_id"]: c for c in configs}

    forensic_reports = []

    for cfg_id in TARGET_CONFIG_IDS:
        cfg = cfg_map[cfg_id]
        print(f"\nAnalyzing Config {cfg_id}... ", flush=True)
        rep = run_forensic_episode(cfg)
        ent = rep["entry_instant"]
        term = rep["terminal_state"]
        flags = rep["classification_flags"]
        lat = rep["latency_metrics"]

        print(f"  Outcome: {rep['outcome']} (at tick {rep['ticks_total']})")
        print(f"  Entry Instant (Tick {ent['tick']}, event={ent['event']}):")
        print(f"    x={ent['x']:.4f}m (offset from 0.825m = {flags['lateral_offset_m']:+.4f}m)")
        print(f"    y={ent['y']:.4f}m")
        print(f"    theta={ent['yaw_deg']:.1f}° (err to -90° = {flags['yaw_error_to_south_deg']:.1f}°)")
        print(f"    v_est={ent['v_est']:.4f} m/s, omega={ent['gyro_w']:.4f} rad/s")
        print(f"    d_L={ent['d_L']:.3f}m, d_R={ent['d_R']:.3f}m, d_min={ent['d_min']:.3f}m")
        print(f"    n_feas={ent['n_feas']}/128 (veto_frac={ent['veto_frac']:.2f})")
        print(f"  Classification: {rep['classification']}")
        print(f"  Latency: ColdStart={lat['cold_start_tick0_ms']:.1f}ms | SteadyMean={lat['steady_state_mean_ms']:.1f}ms | SteadyP95={lat['steady_state_p95_ms']:.1f}ms")
        
        forensic_reports.append(rep)

    # Save structured json (without massive ticks_trace for compact summary, plus full)
    summary_reports = []
    for r in forensic_reports:
        r_sum = dict(r)
        r_sum.pop("ticks_trace")
        summary_reports.append(r_sum)

    out_sum = EVIDENCE_DIR / "r4_3_channel_entry_forensics_summary.json"
    with open(out_sum, "w") as f:
        json.dump(summary_reports, f, indent=2)

    out_full = EVIDENCE_DIR / "r4_3_channel_entry_forensics_full.json"
    with open(out_full, "w") as f:
        json.dump(forensic_reports, f, indent=2)

    print("\n" + "=" * 70)
    print("FORENSIC SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Cfg':<4} | {'Outcome':<9} | {'Event':<22} | {'x_ent':<7} | {'y_ent':<7} | {'th_ent':<7} | {'v_ent':<6} | {'w_ent':<6} | {'d_L':<5} | {'d_R':<5} | {'d_min':<5} | {'Veto':<5} | {'Class':<12}")
    print("-" * 115)
    for r in forensic_reports:
        e = r["entry_instant"]
        print(f"{r['config_id']:<4} | {r['outcome']:<9} | {e['event'][:22]:<22} | {e['x']:<7.3f} | {e['y']:<7.3f} | {e['yaw_deg']:<7.1f} | {e['v_est']:<6.3f} | {e['gyro_w']:<6.3f} | {e['d_L']:<5.3f} | {e['d_R']:<5.3f} | {e['d_min']:<5.3f} | {e['veto_frac']:<5.2f} | {r['classification']:<12}")

    print("\n" + "=" * 70)
    print("LATENCY DECOMPOSITION")
    print("=" * 70)
    cold_starts = [r["latency_metrics"]["cold_start_tick0_ms"] for r in forensic_reports]
    steady_means = [r["latency_metrics"]["steady_state_mean_ms"] for r in forensic_reports]
    steady_p95s = [r["latency_metrics"]["steady_state_p95_ms"] for r in forensic_reports]
    steady_maxs = [r["latency_metrics"]["steady_state_max_ms"] for r in forensic_reports]

    print(f"Cold-Start (Tick 0) Latency:    Mean = {np.mean(cold_starts):.2f} ms | Max = {np.max(cold_starts):.2f} ms")
    print(f"Steady-State (Ticks 1+) Latency: Mean = {np.mean(steady_means):.2f} ms | p95 = {np.mean(steady_p95s):.2f} ms | Max = {np.max(steady_maxs):.2f} ms")
    print(f"\nSaved forensics to:\n  {out_sum}\n  {out_full}")


if __name__ == "__main__":
    main()
