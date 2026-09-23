"""
tests/test_stage3_1_cann_causal_battery.py — Stage 3.1 Revised Pre-Registered CANN Causal Coupling Battery
Classification: [STAGE 3.1 CAUSAL GATING] 4-Arm Controlled Experimental Evaluation (Non-LOS Remediation)

Evaluates whether the 2,114-unit neuromorphic continuous attractor network causally
modulates downstream continuous action selection and navigation performance when
instantaneous local rangefinders are insufficient:
- ARM-A (Intact): Uncorrupted CANN ODE integration with registered arena coordinates and spawn-heading alignment.
- ARM-B (Frozen): Static attractor clamped to spawn state for all t > 0.
- ARM-C (Zeroed): Complete deprivation (r = 0, theta_hat = 0, p_hat = 0).
- ARM-D (Shuffled): Pre-registered deterministic permutation per episode seed (P_ep).

Sample Size: 100 paired episodes per arm (5 unseen seeds x 4 challenge layouts x 5 trials). Total = 400 episodes.
Metrics: Delta u (> 0.15), Delta C_hull (>= 0.05m), Collision Rate Difference, Spearman rho (<= 0.70).
Statistical Tests: Wilcoxon signed-rank test (alpha = 0.01), McNemar test, Cohen's d.
"""

import sys
import os
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import scipy.stats as stats
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain

EVIDENCE_DIR = repo_root / "evidence" / "stage3_1"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Frozen protocol parameters per evidence/stage3_1/REVISED_CANN_BATTERY_PROTOCOL.md
SEEDS = [2001, 2002, 2003, 2004, 2005]
LAYOUTS = [
    "layout_1_left_trap",
    "layout_2_right_trap",
    "layout_3_t_junction",
    "layout_4_corridor_slit",
]
TRIALS_PER_LAYOUT = 5

TASK_SPECS = {
    "layout_1_left_trap": {"max_ticks": 80, "blackout_range": (15, 40)},
    "layout_2_right_trap": {"max_ticks": 80, "blackout_range": (10, 30)},
    "layout_3_t_junction": {"max_ticks": 80, "blackout_range": (15, 35)},
    "layout_4_corridor_slit": {"max_ticks": 100, "blackout_range": (20, 40)},
}


def compute_cohens_d(group1: List[float], group2: List[float]) -> float:
    n1, n2 = len(group1), len(group2)
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_se = math.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / max(n1 + n2 - 2, 1)) + 1e-8
    return float((np.mean(group1) - np.mean(group2)) / pooled_se)


def generate_spawn_configs(seed: int) -> List[Dict[str, Any]]:
    """Generates 20 deterministic spawn configurations for the given seed (5 per layout)."""
    hal = CarlStage1HAL()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    rng = np.random.RandomState(seed)
    configs = []

    for layout_id in LAYOUTS:
        layout_configs = []
        attempts = 0
        while len(layout_configs) < TRIALS_PER_LAYOUT and attempts < 200:
            attempts += 1
            if layout_id == "layout_1_left_trap":
                x = float(rng.uniform(-3.05, -2.95))
                y = float(rng.uniform(-0.25, -0.15))
                yaw = float(-math.pi / 2.0 + rng.uniform(-0.04, 0.04))
            elif layout_id == "layout_2_right_trap":
                x = float(rng.uniform(-3.45, -3.35))
                y = float(rng.uniform(-0.68, -0.62))
                yaw = float(0.0 + rng.uniform(-0.03, 0.03))
            elif layout_id == "layout_3_t_junction":
                x = float(rng.uniform(-0.25, -0.15))
                y = float(rng.uniform(-2.55, -2.45))
                yaw = float(math.pi + rng.uniform(-0.04, 0.04))
            elif layout_id == "layout_4_corridor_slit":
                x = float(rng.uniform(-2.55, -2.45))
                y = float(rng.uniform(2.20, 2.30))
                yaw = float(0.0 + rng.uniform(-0.03, 0.03))
            else:
                raise ValueError(f"Unknown layout: {layout_id}")

            hal.reset()
            hal.data.qpos[qa:qa + 2] = [x, y]
            hal.data.qpos[qa + 3:qa + 7] = [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]
            hal.data.qvel[:] = 0.0
            mujoco.mj_forward(hal.model, hal.data)

            con = hal.get_carl_contact_info()
            if (con["carl_contacts"] - con["floor_contacts"]) > 0:
                continue

            layout_configs.append({
                "layout_id": layout_id,
                "pos": [x, y],
                "yaw": yaw,
                "seed": seed,
            })

        assert len(layout_configs) == TRIALS_PER_LAYOUT, f"Could not generate spawns for {layout_id}"
        configs.extend(layout_configs)

    return configs


def reset_cann_clean(brain: CarlStage2BIntegratedBrain):
    """
    Ensures complete, zero-leak reset of both continuous attractor sub-networks.
    Re-centers the HD ring bump to index 32 (heading 0.0) and grid torus to (16, 16).
    Clears unprivileged phase wrap-around counters and epoch history.
    """
    brain.tick_count = 0
    brain.hd_ring.u[:] = 0.0
    brain.hd_ring.u[32] = 1.0
    brain.hd_ring.r = brain.hd_ring._activation(brain.hd_ring.u)
    brain.hd_ring._settle_initial_attractor(100)

    brain.grid_torus.u[:] = 0.0
    brain.grid_torus.u[16, 16] = 2.0
    brain.grid_torus.r = brain.grid_torus._activation(brain.grid_torus.u)
    brain.grid_torus._settle_initial_attractor(50)
    brain.grid_torus.wrap_count_x = 0
    brain.grid_torus.wrap_count_y = 0
    brain.grid_torus.prev_phase_x = brain.grid_torus._readout_phase_x()
    brain.grid_torus.prev_phase_y = brain.grid_torus._readout_phase_y()

    brain.birth_grid_phase = np.array([brain.grid_torus.prev_phase_x, brain.grid_torus.prev_phase_y], dtype=np.float64)
    brain.birth_hd_phase = brain.hd_ring.decode_heading()
    brain.ax_history.clear()


def run_episode(
    hal: CarlStage1HAL,
    delib: CARLStage2_3R1DeliberationEngine,
    cann: CarlStage2BIntegratedBrain,
    arm: str,
    spawn_pos: List[float],
    spawn_yaw: float,
    layout_id: str,
    ep_seed: int
) -> Dict[str, Any]:
    spec = TASK_SPECS[layout_id]
    max_ticks = spec["max_ticks"]
    blackout_start, blackout_end = spec["blackout_range"]

    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.reset()
    hal.data.qpos[qa:qa + 2] = spawn_pos
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    delib.initialize_pose(spawn_pos[0], spawn_pos[1], spawn_yaw)
    reset_cann_clean(cann)

    # Pre-generate frozen permutation for ARM-D (deterministic per episode)
    rng_ep = np.random.RandomState(ep_seed)
    P_ep_hd = rng_ep.permutation(64)

    # Initial CANN state at spawn
    spawn_sensors = hal.read_sensors()
    initial_res = cann.update_brain(u_executed=np.zeros(6), s_current=spawn_sensors)
    initial_heading = float(initial_res["hd_decoded_heading"])
    initial_x = float(initial_res["grid_unwrapped_x"])
    initial_y = float(initial_res["grid_unwrapped_y"])
    k_shift = int(round(spawn_yaw / (2.0 * math.pi / 64.0)))

    v_est = 0.0
    last_action = np.zeros(6, dtype=np.float64)
    collision = False
    collision_tick = max_ticks
    actions = []
    min_hull_clearances = []
    candidate_utilities_history = []
    selected_branches = []

    for t in range(max_ticks):
        sensors = hal.read_sensors()
        sonars = sensors[:15].copy()
        
        # Ground truth clearance for scoring
        min_sonar = float(np.min(sensors[:15]))
        min_hull_clearances.append(min_sonar)

        # Sensory Blackout: simulate temporary sensory occlusion (sonar reads 5.0m)
        is_blackout = (blackout_start <= t <= blackout_end)
        if is_blackout:
            sonars[:] = 5.0

        gyro_yaw = float(sensors[20]) if len(sensors) > 20 else 0.0

        # Grounded kinematic forward speed integration
        u_fwd = float(0.5 * (last_action[0] + last_action[1]))
        v_target = u_fwd * (delib.k_fwd / 0.030)
        v_est = 0.70 * v_est + 0.30 * v_target

        # Update unprivileged dead reckoning
        delib.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

        # Build CANN state according to intervention Arm
        if arm == "ARM-A_Intact":
            res = cann.update_brain(u_executed=last_action, s_current=sensors)
            hd_rel = float(res["hd_decoded_heading"]) - initial_heading
            hd_arena = math.atan2(math.sin(spawn_yaw + hd_rel), math.cos(spawn_yaw + hd_rel))
            
            dx_rel = float(res["grid_unwrapped_x"]) - initial_x
            dy_rel = float(res["grid_unwrapped_y"]) - initial_y
            dx_arena = dx_rel * math.cos(spawn_yaw) - dy_rel * math.sin(spawn_yaw)
            dy_arena = dx_rel * math.sin(spawn_yaw) + dy_rel * math.cos(spawn_yaw)
            
            r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
            cann_state = {
                "hd_decoded_heading": hd_arena,
                "grid_unwrapped_x": float(spawn_pos[0] + dx_arena),
                "grid_unwrapped_y": float(spawn_pos[1] + dy_arena),
                "hd_rates": r_hd_shifted,
                "bump_amplitude": float(res["hd_bump_amplitude"]),
            }
        elif arm == "ARM-B_Frozen":
            # Static attractor clamped to spawn state
            r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
            cann_state = {
                "hd_decoded_heading": spawn_yaw,
                "grid_unwrapped_x": float(spawn_pos[0]),
                "grid_unwrapped_y": float(spawn_pos[1]),
                "hd_rates": r_hd_shifted,
                "bump_amplitude": 1.0,
            }
        elif arm == "ARM-C_Zeroed":
            # Complete deprivation of neural representation
            cann_state = {
                "hd_decoded_heading": 0.0,
                "grid_unwrapped_x": 0.0,
                "grid_unwrapped_y": 0.0,
                "hd_rates": np.zeros(64, dtype=np.float64),
                "bump_amplitude": 0.0,
            }
        elif arm == "ARM-D_Shuffled":
            # Update CANN dynamics normally, but permute the population representation
            res = cann.update_brain(u_executed=last_action, s_current=sensors)
            dx_rel = float(res["grid_unwrapped_x"]) - initial_x
            dy_rel = float(res["grid_unwrapped_y"]) - initial_y
            dx_arena = dx_rel * math.cos(spawn_yaw) - dy_rel * math.sin(spawn_yaw)
            dy_arena = dx_rel * math.sin(spawn_yaw) + dy_rel * math.cos(spawn_yaw)
            
            r_shuf = cann.hd_ring.r[P_ep_hd].copy()
            r_shuf_shifted = np.roll(r_shuf, k_shift)
            cann_state = {
                "hd_decoded_heading": float(rng_ep.uniform(-math.pi, math.pi)),
                "grid_unwrapped_x": float(spawn_pos[0] + dx_arena),
                "grid_unwrapped_y": float(spawn_pos[1] + dy_arena),
                "hd_rates": r_shuf_shifted,
                "bump_amplitude": float(res["hd_bump_amplitude"]),
            }
        else:
            raise ValueError(f"Unknown arm: {arm}")

        # Deliberation action selection ingesting CANN state
        action, tel = delib.select_action(
            curr_sensors=sonars,
            curr_v=v_est,
            curr_w=gyro_yaw,
            forced_pose=None,
            cann_state=cann_state
        )

        actions.append(action[:2].copy())
        candidate_utilities_history.append(tel["all_utilities"])
        selected_branches.append(tel["selected_branch"])
        last_action = action

        # Step physical simulator
        hal.step(action)

        # Check physical collision
        con = hal.get_carl_contact_info()
        if (con["carl_contacts"] - con["floor_contacts"]) > 0:
            collision = True
            collision_tick = t + 1
            break

    return {
        "arm": arm,
        "collision": collision,
        "collision_tick": collision_tick,
        "min_clearance": float(np.min(min_hull_clearances)) if min_hull_clearances else 0.0,
        "mean_clearance": float(np.mean(min_hull_clearances)) if min_hull_clearances else 0.0,
        "actions": np.array(actions, dtype=np.float64),
        "candidate_utilities": candidate_utilities_history,
        "selected_branches": selected_branches,
    }


def run_stage3_1_battery():
    print("=" * 70)
    print("CARL-DX STAGE 3.1: REVISED PRE-REGISTERED CANN CAUSAL BATTERY")
    print("Testing 2,114-Unit Continuous Attractor Neural Network Causal Coupling")
    print("Under Pre-Registered Non-LOS & Sensory Ambiguity Protocol")
    print("Sample Size: 100 paired trials x 4 arms = 400 total episodes")
    print("=" * 70)

    hal = CarlStage1HAL()
    delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
    cann = CarlStage2BIntegratedBrain(dt=0.030)
    cann.w_rot[20] = 1.0
    cann.w_fwd[15] = 1.0
    cann.is_developmentally_trained = True

    arms = ["ARM-A_Intact", "ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
    all_configs = []
    for s in SEEDS:
        all_configs.extend(generate_spawn_configs(s))

    assert len(all_configs) == 100, f"Expected 100 configs, got {len(all_configs)}"

    # Results storage
    trial_records = []
    delta_u_records = {"ARM-B_Frozen": [], "ARM-C_Zeroed": [], "ARM-D_Shuffled": []}
    clearance_records = {arm: [] for arm in arms}
    collision_counts = {arm: 0 for arm in arms}
    spearman_rho_records = {"ARM-B_Frozen": [], "ARM-C_Zeroed": [], "ARM-D_Shuffled": []}

    t0 = time.time()

    for idx, cfg in enumerate(all_configs):
        sp_pos = cfg["pos"]
        sp_yaw = cfg["yaw"]
        layout_id = cfg["layout_id"]
        ep_seed = cfg["seed"] * 1000 + idx

        # Run ARM-A (Intact) first to establish baseline
        res_intact = run_episode(hal, delib, cann, "ARM-A_Intact", sp_pos, sp_yaw, layout_id, ep_seed)
        clearance_records["ARM-A_Intact"].append(res_intact["min_clearance"])
        if res_intact["collision"]:
            collision_counts["ARM-A_Intact"] += 1

        actions_intact = res_intact["actions"]
        util_intact = res_intact["candidate_utilities"]

        trial_data = {
            "trial_id": idx,
            "seed": cfg["seed"],
            "layout_id": layout_id,
            "intact_collision": res_intact["collision"],
            "intact_clearance": res_intact["min_clearance"],
            "ablations": {}
        }

        # Run Ablation arms on the exact same initial state
        for arm in ["ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]:
            res_abl = run_episode(hal, delib, cann, arm, sp_pos, sp_yaw, layout_id, ep_seed)
            clearance_records[arm].append(res_abl["min_clearance"])
            if res_abl["collision"]:
                collision_counts[arm] += 1

            actions_abl = res_abl["actions"]
            util_abl = res_abl["candidate_utilities"]

            # Compute Delta u: Mean L2 norm divergence between paired action commands
            min_len = min(len(actions_intact), len(actions_abl))
            if min_len > 0:
                diffs = np.linalg.norm(actions_intact[:min_len] - actions_abl[:min_len], axis=1)
                delta_u = float(np.mean(diffs))
            else:
                delta_u = 0.0
            delta_u_records[arm].append(delta_u)

            # Compute Spearman rank correlation on candidate utilities at tick 0
            if len(util_intact) > 0 and len(util_abl) > 0:
                keys = sorted(util_intact[0].keys())
                ranks_intact = [util_intact[0][k] for k in keys]
                ranks_abl = [util_abl[0][k] for k in keys]
                rho, _ = stats.spearmanr(ranks_intact, ranks_abl)
                spearman_rho_records[arm].append(float(rho))
            else:
                spearman_rho_records[arm].append(1.0)

            trial_data["ablations"][arm] = {
                "collision": res_abl["collision"],
                "clearance": res_abl["min_clearance"],
                "delta_u": delta_u,
            }

        trial_records.append(trial_data)

        if (idx + 1) % 10 == 0 or idx == len(all_configs) - 1:
            elapsed = time.time() - t0
            print(f"Progress: [{idx + 1}/100] trials completed ({elapsed:.1f}s elapsed)")

    # Aggregate Statistics
    summary = {
        "n_trials": len(all_configs),
        "arms": {},
        "comparisons": {}
    }

    mean_intact_clr = float(np.mean(clearance_records["ARM-A_Intact"]))
    coll_intact = collision_counts["ARM-A_Intact"]

    summary["arms"]["ARM-A_Intact"] = {
        "collision_rate_pct": float(coll_intact / 100.0 * 100.0),
        "mean_hull_clearance_m": mean_intact_clr,
        "std_hull_clearance_m": float(np.std(clearance_records["ARM-A_Intact"])),
    }

    print("\n" + "=" * 70)
    print("STAGE 3.1 EMPIRICAL RESULTS SUMMARY (REVISED PROTOCOL)")
    print("=" * 70)
    print(f"Intact CANN: Collision Rate = {summary['arms']['ARM-A_Intact']['collision_rate_pct']:.1f}%, Mean Clearance = {mean_intact_clr:.3f} m")

    passed_all_gates = True

    for arm in ["ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]:
        mean_clr = float(np.mean(clearance_records[arm]))
        coll_rate = float(collision_counts[arm] / 100.0 * 100.0)
        delta_u_mean = float(np.mean(delta_u_records[arm]))
        delta_u_std = float(np.std(delta_u_records[arm]))
        delta_clr = mean_intact_clr - mean_clr
        mean_rho = float(np.mean(spearman_rho_records[arm]))

        # Statistical Tests
        paired_diffs = np.array(clearance_records["ARM-A_Intact"]) - np.array(clearance_records[arm])
        jitter = np.random.RandomState(42).normal(0, 1e-9, len(paired_diffs))
        _, wilcox_p = stats.wilcoxon(paired_diffs + jitter)
        wilcox_p = float(wilcox_p)

        d_clr = compute_cohens_d(clearance_records["ARM-A_Intact"], clearance_records[arm])

        summary["arms"][arm] = {
            "collision_rate_pct": coll_rate,
            "mean_hull_clearance_m": mean_clr,
            "std_hull_clearance_m": float(np.std(clearance_records[arm])),
        }

        # Passing checks per locked protocol:
        # 1. Delta u > 0.15
        pass_delta_u = bool(delta_u_mean > 0.15)
        # 2. Delta C_hull >= 0.05m
        pass_delta_clr = bool(delta_clr >= 0.05)
        # 3. p < 0.01
        pass_p_val = bool(wilcox_p < 0.01)
        # 4. Rank correlation rho <= 0.70
        pass_rho = bool(mean_rho <= 0.70)
        # 5. Collision rate increase >= 0.0%
        coll_diff = coll_rate - summary["arms"]["ARM-A_Intact"]["collision_rate_pct"]
        pass_coll = bool(coll_diff >= 0.0)

        arm_passed = pass_delta_u and pass_delta_clr and pass_p_val and pass_rho and pass_coll
        if not arm_passed:
            passed_all_gates = False

        summary["comparisons"][arm] = {
            "mean_delta_u": delta_u_mean,
            "std_delta_u": delta_u_std,
            "delta_hull_clearance_m": delta_clr,
            "wilcoxon_p_value": wilcox_p,
            "cohens_d": d_clr,
            "mean_spearman_rho": mean_rho,
            "collision_increase_pct": coll_diff,
            "gate_passed": arm_passed,
            "gate_checks": {
                "delta_u_gt_0_15": pass_delta_u,
                "delta_clearance_gte_0_05": pass_delta_clr,
                "p_lt_0_01": pass_p_val,
                "spearman_rho_lte_0_70": pass_rho,
                "collision_increase_gte_0": pass_coll,
            }
        }

        print(f"\n[{arm}] vs [ARM-A_Intact]:")
        print(f"  Delta u:                {delta_u_mean:.4f} +/- {delta_u_std:.4f} (Required > 0.1500) -> {'PASS' if pass_delta_u else 'FAIL'}")
        print(f"  Delta Clearance:        {delta_clr:.4f} m (Required >= 0.0500 m) -> {'PASS' if pass_delta_clr else 'FAIL'}")
        print(f"  Wilcoxon p-value:       {wilcox_p:.2e} (Required < 0.0100) -> {'PASS' if pass_p_val else 'FAIL'}")
        print(f"  Cohen's d:              {d_clr:.3f}")
        print(f"  Candidate Spearman rho: {mean_rho:.4f} (Required <= 0.7000) -> {'PASS' if pass_rho else 'FAIL'}")
        print(f"  Collision Rate:         {coll_rate:.1f}% vs {summary['arms']['ARM-A_Intact']['collision_rate_pct']:.1f}% ({coll_diff:+.1f}%) -> {'PASS' if pass_coll else 'FAIL'}")
        print(f"  Arm Overall Status:     {'CERTIFIED PASS' if arm_passed else 'FAILED CLOSED'}")

    summary["overall_stage3_1_certified"] = passed_all_gates

    # Save detailed JSON scorecard
    scorecard_path = EVIDENCE_DIR / "stage3_1_scorecard.json"
    with open(scorecard_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nScorecard saved to: {scorecard_path}")

    # Save raw trial data for visualization
    raw_data_path = EVIDENCE_DIR / "stage3_1_raw_trials.json"
    with open(raw_data_path, "w") as f:
        json.dump({
            "summary": summary,
            "delta_u_records": delta_u_records,
            "clearance_records": clearance_records,
            "collision_counts": collision_counts,
            "spearman_rho_records": spearman_rho_records,
            "trials": trial_records,
        }, f, indent=2)
    print(f"Raw data saved to: {raw_data_path}")

    print("\n" + "=" * 70)
    if passed_all_gates:
        print("STAGE 3.1 CANN CAUSAL COUPLING: CERTIFIED SUCCESSFUL [PASS]")
        print("The 2,114-unit neuromorphic continuous attractor network demonstrates")
        print("statistically significant, behaviorally indispensable downstream necessity.")
    else:
        print("STAGE 3.1 CANN CAUSAL COUPLING: FAILS CLOSED [FAIL]")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    run_stage3_1_battery()
