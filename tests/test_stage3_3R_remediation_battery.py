"""
tests/test_stage3_3R_remediation_battery.py — Stage 3.3-R 40-Trial Continuous Motor Remediation Battery

Classification: [STAGE 3.3-R REMEDIATION BATTERY] Pre-Registered Stress Evaluation
Governing Document: CARL_STAGE3_3_PREREGISTERED_PROTOCOL.md (Frozen Criteria)

Acceptance Criteria (Strictly Frozen):
1. Relative Collision Reduction >= 50.0% vs Frozen Stage-2 Discrete Baseline
2. MPPI Safety Ceiling: Collision Rate <= 10.0%
3. Clearance Gain: Delta C_hull > 0
4. Progress Constraint: Net displacement >= 1.0 m (or goal egress) within evaluation horizon

Protocol Structure:
- 40 deterministic trials (8 trials x 5 task families across 4 random seeds)
- Approach phase to T_crit ensures robot enters the narrow bottleneck at velocity
- At T_crit: comparative bifurcation between discrete baseline and MPPI controller
- Evaluates for 70 ticks post-T_crit
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

ENV_DIR = repo_root / "world" / "stage3_2R_environments"

SEEDS = [3001, 3002, 3003, 3004]  # 4 seeds x 2 conditions = 8 trials per family (40 total)
EVAL_HORIZON = 70  # 70 ticks post-T_crit

FAMILIES = {
    "family_1": {
        "name": "Blind-Corner Connectivity Ambiguity",
        "t_crit": 40,
        "xml_A": str(ENV_DIR / "family1_condA.xml"),
        "xml_B": str(ENV_DIR / "family1_condB.xml"),
        "grid_A": str(ENV_DIR / "family1_condA_grid.pt"),
        "grid_B": str(ENV_DIR / "family1_condB_grid.pt"),
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
    },
    "family_2": {
        "name": "Symmetrical Y-Fork Funnel Trap",
        "t_crit": 35,
        "xml_A": str(ENV_DIR / "family2_condA.xml"),
        "xml_B": str(ENV_DIR / "family2_condB.xml"),
        "grid_A": str(ENV_DIR / "family2_condA_grid.pt"),
        "grid_B": str(ENV_DIR / "family2_condB_grid.pt"),
        "nominal_pos": [-0.40, 0.0],
        "nominal_yaw": 0.0,
    },
    "family_3": {
        "name": "Sonically Symmetric Locations (P1 vs P2)",
        "t_crit": 50,
        "xml_A": str(ENV_DIR / "family3_layout.xml"),
        "xml_B": str(ENV_DIR / "family3_layout.xml"),
        "grid_A": str(ENV_DIR / "family3_layout_grid.pt"),
        "grid_B": str(ENV_DIR / "family3_layout_grid.pt"),
        "pos_A": [-1.50, 1.20],
        "pos_B": [1.50, -1.80],
        "nominal_yaw": 0.0,
    },
    "family_4": {
        "name": "Occluded Dogleg Arterial vs Blind Detour",
        "t_crit": 45,
        "xml_A": str(ENV_DIR / "family4_condA.xml"),
        "xml_B": str(ENV_DIR / "family4_condB.xml"),
        "grid_A": str(ENV_DIR / "family4_condA_grid.pt"),
        "grid_B": str(ENV_DIR / "family4_condB_grid.pt"),
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
    },
    "family_5": {
        "name": "Multi-Turn Sensory Blackout / Sonic Corridor Symmetry",
        "t_crit": 60,
        "xml_A": str(ENV_DIR / "family5_layout.xml"),
        "xml_B": str(ENV_DIR / "family5_layout.xml"),
        "grid_A": str(ENV_DIR / "family5_layout_grid.pt"),
        "grid_B": str(ENV_DIR / "family5_layout_grid.pt"),
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
    },
}


def build_40_trial_manifest() -> List[Dict[str, Any]]:
    """Builds the deterministic 40-trial evaluation schedule."""
    trials = []
    trial_counter = 0

    for fam_key, spec in FAMILIES.items():
        for seed in SEEDS:
            for cond in ["A", "B"]:
                trial_counter += 1
                rng = np.random.RandomState(seed + (100 if cond == "B" else 0))
                dx = float(rng.uniform(-0.010, 0.010))
                dy = float(rng.uniform(-0.010, 0.010))
                dyaw = float(rng.uniform(-0.008, 0.008))

                if fam_key == "family_3":
                    base_pos = spec["pos_A"] if cond == "A" else spec["pos_B"]
                else:
                    base_pos = spec["nominal_pos"]

                spawn_pos = [base_pos[0] + dx, base_pos[1] + dy]
                spawn_yaw = spec["nominal_yaw"] + dyaw
                xml_path = spec["xml_A"] if cond == "A" else spec["xml_B"]
                grid_path = spec["grid_A"] if cond == "A" else spec["grid_B"]

                trials.append({
                    "trial_idx": trial_counter,
                    "family": fam_key,
                    "condition": cond,
                    "seed": seed,
                    "xml_path": xml_path,
                    "grid_path": grid_path,
                    "spawn_pos": spawn_pos,
                    "spawn_yaw": spawn_yaw,
                    "t_crit": spec["t_crit"]
                })

    assert len(trials) == 40, f"Expected 40 trials, got {len(trials)}"
    return trials


def run_single_eval_arm(
    hal: CarlStage1HAL,
    controller: Any,
    cloned_qpos: np.ndarray,
    cloned_qvel: np.ndarray,
    cloned_time: float,
    cloned_pose: np.ndarray,
    cloned_v_hat: float,
    cloned_w_hat: float,
    spawn_pos: np.ndarray,
    eval_horizon: int = EVAL_HORIZON
) -> Dict[str, Any]:
    """Runs a single post-T_crit evaluation arm for a controller from exact cloned state."""
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.reset()
    hal.data.qpos[:] = np.copy(cloned_qpos)
    hal.data.qvel[:] = np.copy(cloned_qvel)
    hal.data.time = cloned_time
    mujoco.mj_forward(hal.model, hal.data)

    p_crit = np.array([float(cloned_qpos[qa]), float(cloned_qpos[qa+1])], dtype=np.float64)
    controller.pose = np.copy(cloned_pose)
    controller.v_hat = float(cloned_v_hat)
    controller.w_hat = float(cloned_w_hat)

    had_collision = False
    collision_tick = None
    min_clearance = 5.0
    v_est = float(cloned_v_hat)
    positions = [p_crit]
    velocities = []
    actions_taken = []

    for step in range(eval_horizon):
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
        actions_taken.append([float(act[0]), float(act[1])])

        hal.step(cmd_6d)

        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True
            collision_tick = step + 1
            break

        curr_p = np.array([float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])], dtype=np.float64)
        positions.append(curr_p)

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)
        velocities.append(v_est)

    final_p = positions[-1]
    post_crit_displacement = float(np.linalg.norm(final_p - p_crit))
    total_displacement = float(np.linalg.norm(final_p - spawn_pos))
    mean_velocity = float(np.mean(velocities)) if velocities else 0.0
    completed_without_collision = bool(not had_collision)
    is_stalled = bool(not had_collision and (post_crit_displacement < 0.15 or mean_velocity < 0.05))
    timed_out = bool(len(velocities) == eval_horizon and not had_collision)
    progress_success = bool(not had_collision and total_displacement >= 1.0)

    return {
        "had_collision": had_collision,
        "collision_tick": collision_tick,
        "min_clearance": min_clearance,
        "post_crit_displacement": post_crit_displacement,
        "total_displacement": total_displacement,
        "mean_velocity": mean_velocity,
        "ticks_completed": len(velocities),
        "completed_without_collision": completed_without_collision,
        "is_stalled": is_stalled,
        "timed_out": timed_out,
        "progress_success": progress_success,
        "final_pos": [float(final_p[0]), float(final_p[1])],
        "trajectory": [[float(p[0]), float(p[1])] for p in positions],
        "actions_taken": actions_taken
    }


def execute_40_trial_remediation_battery() -> Dict[str, Any]:
    """
    Executes the 40-trial Stage 3.3-R remediation battery comparing Discrete vs MPPI.
    Evaluates strictly against frozen Gate 3 criteria:
    - >= 50.0% relative collision reduction vs discrete baseline
    - MPPI collision rate <= 10.0%
    - Delta hull clearance > 0
    - Minimum progress requirement >= 1.0 m over complete evaluation horizon
    """
    trials = build_40_trial_manifest()
    print("=" * 90)
    print(f"  CARL STAGE 3.3-R REMEDIATION BATTERY: EXECUTING {len(trials)} MATCHED TRIALS")
    print("  Comparing Frozen Discrete Baseline vs MPPI Deliberation Engine")
    print("=" * 90)

    discrete_collisions = 0
    mppi_collisions = 0
    discrete_clearances = []
    mppi_clearances = []
    discrete_total_displacements = []
    mppi_total_displacements = []
    discrete_progress_successes = 0
    mppi_progress_successes = 0
    discrete_stalls = 0
    mppi_stalls = 0

    contingency = {
        "n11_both_safe": 0,
        "n10_mppi_safe_discrete_coll": 0,
        "n01_discrete_safe_mppi_coll": 0,
        "n00_both_coll": 0
    }

    per_family_stats: Dict[str, Dict[str, Any]] = {}
    records = []

    print(f"{'Trial':<5} | {'Family / Cond':<16} | {'Seed':<5} | {'Discrete Outcome':<24} | {'MPPI Outcome':<24}")
    print("-" * 90)

    for trial in trials:
        t_idx = trial["trial_idx"]
        fam_key = trial["family"]
        cond = trial["condition"]
        seed = trial["seed"]

        if fam_key not in per_family_stats:
            per_family_stats[fam_key] = {
                "total": 0,
                "discrete_collisions": 0,
                "mppi_collisions": 0,
                "discrete_clearances": [],
                "mppi_clearances": [],
                "discrete_progress": 0,
                "mppi_progress": 0
            }
        per_family_stats[fam_key]["total"] += 1

        hal = CarlStage1HAL(xml_path=trial["xml_path"])
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        spawn_p = np.array(trial["spawn_pos"], dtype=np.float64)

        # 1. Approach phase to T_crit with odometry tracking in master deliberation engine
        hal.reset()
        hal.data.qpos[qa:qa+2] = trial["spawn_pos"]
        hal.data.qpos[qa+3:qa+7] = [math.cos(trial["spawn_yaw"]/2.0), 0.0, 0.0, math.sin(trial["spawn_yaw"]/2.0)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)

        delib_master = CARLStage2_3R1DeliberationEngine(grid_path=trial["grid_path"], mode="deliberative")
        delib_master.initialize_pose(spawn_p[0], spawn_p[1], trial["spawn_yaw"])

        u_app = np.array([0.65, 0.65, 0.0, 0.0, 0.0, 0.0])
        for _ in range(trial["t_crit"]):
            sensors = hal.read_sensors()
            curr_v = float(sensors[21])
            curr_w = float(sensors[20])
            delib_master.update_odometry(curr_v, curr_w, dt=0.030)
            hal.step(u_app)

        # Clone exact physical and cognitive state at T_crit
        cloned_qpos = np.copy(hal.data.qpos)
        cloned_qvel = np.copy(hal.data.qvel)
        cloned_time = float(hal.data.time)
        cloned_pose = np.copy(delib_master.pose)
        cloned_v_hat = float(delib_master.v_hat)
        cloned_w_hat = float(delib_master.w_hat)

        # 2. Discrete Controller Arm
        discrete_eng = CARLStage2_3R1DeliberationEngine(
            grid_path=trial["grid_path"],
            mode="deliberative",
            horizon=10
        )
        d_res = run_single_eval_arm(
            hal, discrete_eng,
            cloned_qpos, cloned_qvel, cloned_time,
            cloned_pose, cloned_v_hat, cloned_w_hat,
            spawn_pos=spawn_p
        )

        if d_res["had_collision"]:
            discrete_collisions += 1
            per_family_stats[fam_key]["discrete_collisions"] += 1
        if d_res["progress_success"]:
            discrete_progress_successes += 1
            per_family_stats[fam_key]["discrete_progress"] += 1
        if d_res["is_stalled"]:
            discrete_stalls += 1
        discrete_clearances.append(d_res["min_clearance"])
        discrete_total_displacements.append(d_res["total_displacement"])
        per_family_stats[fam_key]["discrete_clearances"].append(d_res["min_clearance"])

        # 3. MPPI Controller Arm
        mppi_eng = CARLStage3_3MPPIDeliberationEngine(
            grid_path=trial["grid_path"],
            num_samples=128,
            horizon=15
        )
        m_res = run_single_eval_arm(
            hal, mppi_eng,
            cloned_qpos, cloned_qvel, cloned_time,
            cloned_pose, cloned_v_hat, cloned_w_hat,
            spawn_pos=spawn_p
        )

        if m_res["had_collision"]:
            mppi_collisions += 1
            per_family_stats[fam_key]["mppi_collisions"] += 1
        if m_res["progress_success"]:
            mppi_progress_successes += 1
            per_family_stats[fam_key]["mppi_progress"] += 1
        if m_res["is_stalled"]:
            mppi_stalls += 1
        mppi_clearances.append(m_res["min_clearance"])
        mppi_total_displacements.append(m_res["total_displacement"])
        per_family_stats[fam_key]["mppi_clearances"].append(m_res["min_clearance"])

        # Matched contingency
        d_safe = not d_res["had_collision"]
        m_safe = not m_res["had_collision"]
        if d_safe and m_safe:
            contingency["n11_both_safe"] += 1
        elif not d_safe and m_safe:
            contingency["n10_mppi_safe_discrete_coll"] += 1
        elif d_safe and not m_safe:
            contingency["n01_discrete_safe_mppi_coll"] += 1
        else:
            contingency["n00_both_coll"] += 1

        d_str = f"{'COLLISION' if d_res['had_collision'] else 'SAFE'} (c={d_res['min_clearance']:.2f}m, d={d_res['total_displacement']:.2f}m)"
        m_str = f"{'COLLISION' if m_res['had_collision'] else 'SAFE'} (c={m_res['min_clearance']:.2f}m, d={m_res['total_displacement']:.2f}m)"
        print(f"T{t_idx:02d}  | {fam_key[-4:]} Cond{cond:<3} | {seed:<5} | {d_str:<24} | {m_str:<24}")

        records.append({
            "trial_idx": t_idx,
            "family": fam_key,
            "condition": cond,
            "seed": seed,
            "spawn_pos": trial["spawn_pos"],
            "spawn_yaw": trial["spawn_yaw"],
            "discrete": d_res,
            "mppi": m_res
        })

    total = len(trials)
    d_coll_rate = (discrete_collisions / total) * 100.0
    m_coll_rate = (mppi_collisions / total) * 100.0

    # Exact relative reduction: (d - m) / d * 100%
    if d_coll_rate > 0.0:
        rel_red = ((d_coll_rate - m_coll_rate) / d_coll_rate) * 100.0
    else:
        rel_red = 0.0 if m_coll_rate == 0.0 else -100.0

    delta_clr = float(np.mean(mppi_clearances) - np.mean(discrete_clearances))
    d_mean_clr = float(np.mean(discrete_clearances))
    m_mean_clr = float(np.mean(mppi_clearances))

    d_prog_rate = (discrete_progress_successes / total) * 100.0
    m_prog_rate = (mppi_progress_successes / total) * 100.0

    # Strict frozen Gate 3 checks: NO OR conditions, NO fallbacks
    pass_rel_red = bool(rel_red >= 50.0)
    pass_mppi_ceil = bool(m_coll_rate <= 10.0)
    pass_clearance = bool(delta_clr > 0.0)
    pass_progress = bool(m_prog_rate >= 80.0)

    gate3_passed = bool(pass_rel_red and pass_mppi_ceil and pass_clearance and pass_progress)

    summary = {
        "milestone": "Stage 3.3-R Remediation Battery (40 Trials)",
        "total_trials": total,
        "discrete_summary": {
            "collisions": discrete_collisions,
            "collision_rate_pct": d_coll_rate,
            "mean_clearance_m": d_mean_clr,
            "min_clearance_m": float(np.min(discrete_clearances)),
            "mean_total_displacement_m": float(np.mean(discrete_total_displacements)),
            "progress_successes": discrete_progress_successes,
            "progress_success_rate_pct": d_prog_rate,
            "stall_count": discrete_stalls
        },
        "mppi_summary": {
            "collisions": mppi_collisions,
            "collision_rate_pct": m_coll_rate,
            "mean_clearance_m": m_mean_clr,
            "min_clearance_m": float(np.min(mppi_clearances)),
            "mean_total_displacement_m": float(np.mean(mppi_total_displacements)),
            "progress_successes": mppi_progress_successes,
            "progress_success_rate_pct": m_prog_rate,
            "stall_count": mppi_stalls
        },
        "comparative_metrics": {
            "relative_collision_reduction_pct": rel_red,
            "delta_clearance_m": delta_clr,
            "contingency_table": contingency
        },
        "gate_checks": {
            "relative_reduction_ge_50": {"metric": rel_red, "threshold": ">= 50.0%", "passed": pass_rel_red},
            "mppi_collision_le_10": {"metric": m_coll_rate, "threshold": "<= 10.0%", "passed": pass_mppi_ceil},
            "delta_clearance_gt_0": {"metric": delta_clr, "threshold": "> 0.0 m", "passed": pass_clearance},
            "progress_qualified_success_ge_80": {"metric": m_prog_rate, "threshold": ">= 80.0%", "passed": pass_progress},
            "gate3_composite_verdict": "PASS" if gate3_passed else "FAIL"
        },
        "per_family_stats": per_family_stats,
        "records": records
    }

    out_file = repo_root / "evidence" / "stage3_3" / "stage3_3R_40trial_battery_scorecard.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 90)
    print("                 STAGE 3.3-R 40-TRIAL BATTERY ADJUDICATION")
    print("=" * 90)
    print(f"Discrete Baseline Collisions:      {discrete_collisions}/{total} ({d_coll_rate:.1f}%)")
    print(f"MPPI Controller Collisions:        {mppi_collisions}/{total} ({m_coll_rate:.1f}%)")
    print(f"Relative Collision Reduction:      {rel_red:.1f}% (Required: >= 50.0%) -> {'PASS' if pass_rel_red else 'FAIL'}")
    print(f"MPPI Collision Ceiling:            {m_coll_rate:.1f}% (Required: <= 10.0%) -> {'PASS' if pass_mppi_ceil else 'FAIL'}")
    print(f"Delta Hull Clearance:              {delta_clr:+.4f} m (Required: > 0.0 m) -> {'PASS' if pass_clearance else 'FAIL'}")
    print(f"MPPI Progress Success (>=1m):      {mppi_progress_successes}/{total} ({m_prog_rate:.1f}%) (Required: >= 80.0%) -> {'PASS' if pass_progress else 'FAIL'}")
    print(f"Contingency (N={total}):           Safe Both: {contingency['n11_both_safe']}, MPPI Safe/Disc Coll: {contingency['n10_mppi_safe_discrete_coll']}, Disc Safe/MPPI Coll: {contingency['n01_discrete_safe_mppi_coll']}, Both Coll: {contingency['n00_both_coll']}")
    print(f"FINAL GATE 3 VERDICT:              {'PASS' if gate3_passed else 'FAIL'}")
    print("=" * 90)

    return summary


if __name__ == "__main__":
    execute_40_trial_remediation_battery()
