"""
tests/diagnostic_stage3_3R_10_trials.py — Stage 3.3-R 10-Trial Forensic Stress Diagnostic

Evaluates Frozen Stage-2 Discrete Controller vs Stage-3.3 MPPI Controller
across 10 deterministic trials in Stage 3.2-R narrow-corridor, chicane, and blind-bend geometries.

Purpose:
Determine whether the existing Stage 3.2-R stress geometries break the baseline floor effect
(i.e. produce a non-zero collision rate for the discrete controller) and whether MPPI can
physically complete them without collision while satisfying the >= 1.0 m progress constraint.
"""

import sys
import math
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

ENV_DIR = "world/stage3_2R_environments"

DIAGNOSTIC_TRIALS = [
    {
        "id": "T01",
        "family": "Family 1 (Blind Corner)",
        "desc": "Blind-Corner Connectivity Ambiguity (Cond A - Left exit)",
        "xml": f"{ENV_DIR}/family1_condA.xml",
        "grid": f"{ENV_DIR}/family1_condA_grid.pt",
        "spawn_pos": [0.0, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T02",
        "family": "Family 1 (Blind Corner)",
        "desc": "Blind-Corner Connectivity Ambiguity (Cond B - Right exit)",
        "xml": f"{ENV_DIR}/family1_condB.xml",
        "grid": f"{ENV_DIR}/family1_condB_grid.pt",
        "spawn_pos": [0.0, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T03",
        "family": "Family 2 (Cul-de-Sac)",
        "desc": "Symmetrical Y-Fork Funnel Trap (Cond A - Lower branch)",
        "xml": f"{ENV_DIR}/family2_condA.xml",
        "grid": f"{ENV_DIR}/family2_condA_grid.pt",
        "spawn_pos": [-0.40, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T04",
        "family": "Family 2 (Cul-de-Sac)",
        "desc": "Symmetrical Y-Fork Funnel Trap (Cond B - Upper branch)",
        "xml": f"{ENV_DIR}/family2_condB.xml",
        "grid": f"{ENV_DIR}/family2_condB_grid.pt",
        "spawn_pos": [-0.40, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T05",
        "family": "Family 3 (Sonic Symmetry)",
        "desc": "Sonically Symmetric Maze (Position A - North exit)",
        "xml": f"{ENV_DIR}/family3_layout.xml",
        "grid": f"{ENV_DIR}/family3_layout_grid.pt",
        "spawn_pos": [-1.50, 1.20],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T06",
        "family": "Family 3 (Sonic Symmetry)",
        "desc": "Sonically Symmetric Maze (Position B - East exit)",
        "xml": f"{ENV_DIR}/family3_layout.xml",
        "grid": f"{ENV_DIR}/family3_layout_grid.pt",
        "spawn_pos": [1.50, -1.80],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T07",
        "family": "Family 4 (Dogleg Chicane)",
        "desc": "Occluded Dogleg Arterial (Cond A - Narrow S-bend)",
        "xml": f"{ENV_DIR}/family4_condA.xml",
        "grid": f"{ENV_DIR}/family4_condA_grid.pt",
        "spawn_pos": [0.0, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T08",
        "family": "Family 4 (Dogleg Chicane)",
        "desc": "Blind Detour Corridor (Cond B - Straight/Detour)",
        "xml": f"{ENV_DIR}/family4_condB.xml",
        "grid": f"{ENV_DIR}/family4_condB_grid.pt",
        "spawn_pos": [0.0, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T09",
        "family": "Family 5 (Labyrinth Hallways)",
        "desc": "Multi-Turn Labyrinth Hallways (Heading East)",
        "xml": f"{ENV_DIR}/family5_layout.xml",
        "grid": f"{ENV_DIR}/family5_layout_grid.pt",
        "spawn_pos": [0.0, 0.0],
        "spawn_yaw": 0.0,
    },
    {
        "id": "T10",
        "family": "Family 5 (Labyrinth Hallways)",
        "desc": "Multi-Turn Labyrinth Hallways (Heading West / 180°)",
        "xml": f"{ENV_DIR}/family5_layout.xml",
        "grid": f"{ENV_DIR}/family5_layout_grid.pt",
        "spawn_pos": [0.0, 0.0],
        "spawn_yaw": float(math.pi),
    },
]


def execute_single_trial(
    trial_spec: Dict[str, Any],
    controller_type: str,
    horizon_ticks: int = 60
) -> Dict[str, Any]:
    xml_path = trial_spec["xml"]
    grid_path = trial_spec["grid"]
    spawn_pos = trial_spec["spawn_pos"]
    spawn_yaw = trial_spec["spawn_yaw"]

    hal = CarlStage1HAL(xml_path=xml_path)
    qa = int(hal.model.joint("spatial_identity").qposadr[0])

    hal.reset()
    hal.data.qpos[qa:qa + 2] = spawn_pos
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    if controller_type == "discrete":
        controller = CARLStage2_3R1DeliberationEngine(
            mode="deliberative",
            horizon=10,
            grid_path=grid_path
        )
    elif controller_type == "mppi":
        controller = CARLStage3_3MPPIDeliberationEngine(
            num_samples=128,
            horizon=15,
            grid_path=grid_path
        )
    else:
        raise ValueError(f"Unknown controller type: {controller_type}")

    controller.initialize_pose(spawn_pos[0], spawn_pos[1], spawn_yaw)

    had_collision = False
    min_clearance = 5.0
    v_est = 0.0
    initial_pos = np.array([spawn_pos[0], spawn_pos[1]], dtype=np.float64)
    positions = [initial_pos]
    velocities = []

    collision_tick = None
    ticks_completed = 0

    for tick in range(horizon_ticks):
        ticks_completed += 1
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])

        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.03)

        min_son = float(np.min(sonars))
        if min_son < min_clearance:
            min_clearance = min_son

        act, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(act[0])
        cmd_6d[1] = float(act[1])

        s_next, diag = hal.step(cmd_6d)

        # Check contact with walls/obstacles
        contact_info = hal.get_carl_contact_info()
        wall_contacts = contact_info["carl_contacts"] - contact_info["floor_contacts"]
        if wall_contacts > 0 and not had_collision:
            had_collision = True
            collision_tick = tick + 1

        # Current position
        curr_pos = np.array([float(hal.data.qpos[qa]), float(hal.data.qpos[qa + 1])], dtype=np.float64)
        positions.append(curr_pos)

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        fwd_speed = u_fwd * 0.30  # approximate linear speed m/s
        v_est = 0.70 * v_est + 0.30 * fwd_speed
        velocities.append(v_est)

    final_pos = positions[-1]
    net_displacement = float(np.linalg.norm(final_pos - initial_pos))
    mean_velocity = float(np.mean(velocities)) if velocities else 0.0
    achieved_1m = bool(net_displacement >= 1.0)
    is_stalled = bool(net_displacement < 0.15 or mean_velocity < 0.05)
    completed_without_collision = bool(not had_collision)
    progress_qualified_success = bool(completed_without_collision and achieved_1m)

    return {
        "trial_id": trial_spec["id"],
        "controller": controller_type,
        "had_collision": had_collision,
        "collision_tick": collision_tick,
        "min_hull_clearance": min_clearance,
        "net_displacement": net_displacement,
        "mean_forward_velocity": mean_velocity,
        "ticks_completed": ticks_completed,
        "completed_without_collision": completed_without_collision,
        "achieved_1m_progress": achieved_1m,
        "is_stalled": is_stalled,
        "progress_qualified_success": progress_qualified_success,
        "final_pos": [float(final_pos[0]), float(final_pos[1])]
    }


def run_10_trial_diagnostic():
    print("=" * 90)
    print("      CARL STAGE 3.3-R 10-TRIAL FORENSIC DIAGNOSTIC SUITE")
    print("  Testing Frozen Discrete Baseline vs MPPI on Stage 3.2-R Stress Geometries")
    print("=" * 90)

    discrete_results = []
    mppi_results = []

    print("\nRunning comparative trials across 10 stress configurations...")
    print("-" * 90)
    header = f"{'Trial':<5} | {'Geometry / Description':<40} | {'Discrete Result':<18} | {'MPPI Result':<18}"
    print(header)
    print("-" * 90)

    for trial in DIAGNOSTIC_TRIALS:
        t_id = trial["id"]
        desc = trial["desc"][:40]

        # 1. Run Discrete
        d_res = execute_single_trial(trial, controller_type="discrete", horizon_ticks=60)
        discrete_results.append(d_res)

        # 2. Run MPPI
        m_res = execute_single_trial(trial, controller_type="mppi", horizon_ticks=60)
        mppi_results.append(m_res)

        d_status = f"{'COLLISION' if d_res['had_collision'] else 'OK'} (d={d_res['net_displacement']:.2f}m, c={d_res['min_hull_clearance']:.2f}m)"
        m_status = f"{'COLLISION' if m_res['had_collision'] else 'OK'} (d={m_res['net_displacement']:.2f}m, c={m_res['min_hull_clearance']:.2f}m)"

        print(f"{t_id:<5} | {desc:<40} | {d_status:<18} | {m_status:<18}")

    print("-" * 90)

    # Compute aggregate metrics
    d_colls = sum(1 for r in discrete_results if r["had_collision"])
    m_colls = sum(1 for r in mppi_results if r["had_collision"])
    total = len(DIAGNOSTIC_TRIALS)

    d_coll_rate = (d_colls / total) * 100.0
    m_coll_rate = (m_colls / total) * 100.0

    d_prog_success = sum(1 for r in discrete_results if r["progress_qualified_success"])
    m_prog_success = sum(1 for r in mppi_results if r["progress_qualified_success"])

    d_prog_rate = (d_prog_success / total) * 100.0
    m_prog_rate = (m_prog_success / total) * 100.0

    d_mean_clr = float(np.mean([r["min_hull_clearance"] for r in discrete_results]))
    m_mean_clr = float(np.mean([r["min_hull_clearance"] for r in mppi_results]))

    d_min_clr = float(np.min([r["min_hull_clearance"] for r in discrete_results]))
    m_min_clr = float(np.min([r["min_hull_clearance"] for r in mppi_results]))

    d_mean_disp = float(np.mean([r["net_displacement"] for r in discrete_results]))
    m_mean_disp = float(np.mean([r["net_displacement"] for r in mppi_results]))

    d_stalls = sum(1 for r in discrete_results if r["is_stalled"])
    m_stalls = sum(1 for r in mppi_results if r["is_stalled"])

    floor_effect_broken = bool(d_colls > 0)

    summary = {
        "diagnostic_id": "STAGE3_3R_10TRIAL_DIAGNOSTIC_2026-09-13",
        "total_trials": total,
        "floor_effect_broken": floor_effect_broken,
        "discrete_metrics": {
            "collisions": d_colls,
            "collision_rate_pct": d_coll_rate,
            "progress_qualified_successes": d_prog_success,
            "progress_qualified_success_rate_pct": d_prog_rate,
            "mean_min_clearance_m": d_mean_clr,
            "absolute_min_clearance_m": d_min_clr,
            "mean_net_displacement_m": d_mean_disp,
            "stall_count": d_stalls,
        },
        "mppi_metrics": {
            "collisions": m_colls,
            "collision_rate_pct": m_coll_rate,
            "progress_qualified_successes": m_prog_success,
            "progress_qualified_success_rate_pct": m_prog_rate,
            "mean_min_clearance_m": m_mean_clr,
            "absolute_min_clearance_m": m_min_clr,
            "mean_net_displacement_m": m_mean_disp,
            "stall_count": m_stalls,
        },
        "trials": {
            "discrete": discrete_results,
            "mppi": mppi_results
        }
    }

    out_file = repo_root / "evidence" / "stage3_3" / "stage3_3R_10trial_diagnostic.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 90)
    print("                    10-TRIAL DIAGNOSTIC SUMMARY")
    print("=" * 90)
    print(f"Discrete Baseline Collisions:      {d_colls}/{total} ({d_coll_rate:.1f}%)")
    print(f"MPPI Controller Collisions:        {m_colls}/{total} ({m_coll_rate:.1f}%)")
    print(f"Floor Effect Broken:               {'YES (Non-zero baseline collisions)' if floor_effect_broken else 'NO (Baseline collisions = 0)'}")
    print(f"Discrete Progress Success (>=1m):  {d_prog_success}/{total} ({d_prog_rate:.1f}%)")
    print(f"MPPI Progress Success (>=1m):      {m_prog_success}/{total} ({m_prog_rate:.1f}%)")
    print(f"Discrete Mean Clearance:           {d_mean_clr:.4f} m (Min: {d_min_clr:.4f} m)")
    print(f"MPPI Mean Clearance:               {m_mean_clr:.4f} m (Min: {m_min_clr:.4f} m)")
    print(f"Discrete Mean Displacement:        {d_mean_disp:.4f} m (Stalls: {d_stalls})")
    print(f"MPPI Mean Displacement:            {m_mean_disp:.4f} m (Stalls: {m_stalls})")
    print(f"Diagnostic Report Saved to:        {out_file}")
    print("=" * 90)

    return summary


if __name__ == "__main__":
    run_10_trial_diagnostic()
