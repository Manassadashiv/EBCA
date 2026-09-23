"""
tests/test_stage3_2RB_memory_necessity_battery.py — Stage 3.2-RB Spatial Memory Necessity Battery
Classification: [STAGE 3.2-RB BENCHMARK] 500-Episode Preregistered Double-Blind Memory Intervention Battery (Class B)

Evaluates the causal behavioral necessity of persistent allocentric spatial memory (M_env)
under double-blind state-cloning across 5 task families, 5 seeds, and 5 intervention arms:
1. ARM-I: Intact allocentric spatial memory (M_env retained)
2. ARM-A: Amnesic spatial memory (M_env = 0, live sonars/IMU/body model active)
3. ARM-S: Topographically scrambled memory (16x16 patch permutation)
4. ARM-PF: Artificial Potential Field reactive baseline
5. ARM-R: Scripted Reflex baseline

Pre-Registered Acceptance Gates (Class B):
- G6: Primary Effect Separation Delta-Success (ARM-I - ARM-A) >= +35.0%
- G7: Exact McNemar Significance p < 0.001 (one-sided)
- G8: Topographic Specificity Delta-Success (ARM-I - ARM-S) >= +25.0%, p < 0.010
- G9: Intact Safety Collision Rate CR_ARM-I <= 5.0%
"""

import sys
import os
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

EVIDENCE_DIR = repo_root / "evidence" / "stage3_2R"
RAW_DIR = EVIDENCE_DIR / "raw"
SCORE_DIR = EVIDENCE_DIR / "scorecard"
RAW_DIR.mkdir(parents=True, exist_ok=True)
SCORE_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [3001, 3002, 3003, 3004, 3005]
TRIALS_PER_SEED = 4  # 20 trials per family
EVAL_HORIZON = 70    # 70 ticks post-T_crit (2.10s)

TASK_CONFIGS = {
    "family_1": {
        "name": "Blind-Corner Connectivity Ambiguity",
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
        "t_crit": 40,
        "grid_A": "world/stage3_2R_environments/family1_condA_grid.pt",
        "grid_B": "world/stage3_2R_environments/family1_condB_grid.pt",
        "u_star_A": np.array([0.15, 0.80]),
        "u_star_B": np.array([0.80, 0.15]),
    },
    "family_2": {
        "name": "Symmetrical Y-Fork Funnel Trap",
        "nominal_pos": [-0.40, 0.0],
        "nominal_yaw": 0.0,
        "t_crit": 35,
        "grid_A": "world/stage3_2R_environments/family2_condA_grid.pt",
        "grid_B": "world/stage3_2R_environments/family2_condB_grid.pt",
        "u_star_A": np.array([0.65, 0.35]),
        "u_star_B": np.array([0.35, 0.65]),
    },
    "family_3": {
        "name": "Sonically Symmetric Locations (P1 vs P2)",
        "pos_A": [-1.50, 1.20],
        "pos_B": [ 1.50, -1.80],
        "nominal_yaw": 0.0,
        "t_crit": 50,
        "grid_A": "world/stage3_2R_environments/family3_layout_grid.pt",
        "grid_B": "world/stage3_2R_environments/family3_layout_grid.pt",
        "u_star_A": np.array([0.20, 0.65]),
        "u_star_B": np.array([0.65, 0.20]),
    },
    "family_4": {
        "name": "Occluded Dogleg Arterial vs Blind Detour",
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
        "t_crit": 45,
        "grid_A": "world/stage3_2R_environments/family4_condA_grid.pt",
        "grid_B": "world/stage3_2R_environments/family4_condB_grid.pt",
        "u_star_A": np.array([0.20, 0.75]),
        "u_star_B": np.array([0.75, 0.75]),
    },
    "family_5": {
        "name": "Multi-Turn Sensory Blackout / Sonic Corridor Symmetry",
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
        "t_crit": 60,
        "grid_A": "world/stage3_2R_environments/family5_layout_grid.pt",
        "grid_B": "world/stage3_2R_environments/family5_layout_grid.pt",
        "u_star_A": np.array([0.75, 0.25]),
        "u_star_B": np.array([0.25, 0.75]),
    },
}


def scramble_grid_16x16(grid: torch.Tensor, seed: int) -> torch.Tensor:
    """Partitions 128x128 grid into 64 patches of size 16x16 and applies uniform permutation."""
    rng = np.random.RandomState(seed)
    perm = rng.permutation(64)
    scrambled = grid.clone()

    patches = []
    for r in range(8):
        for c in range(8):
            patch = grid[:, :, r*16:(r+1)*16, c*16:(c+1)*16]
            patches.append(patch)

    for idx, p_idx in enumerate(perm):
        r = idx // 8
        c = idx % 8
        scrambled[:, :, r*16:(r+1)*16, c*16:(c+1)*16] = patches[p_idx]

    return scrambled


def check_goal_reached(fam_key: str, cond: str, pos: Tuple[float, float]) -> bool:
    x, y = pos
    if fam_key == "family_1":
        # Cond A: North branch (y >= 0.50); Cond B: South branch (y <= -0.50)
        return (y >= 0.50) if cond == "A" else (y <= -0.50)
    elif fam_key == "family_2":
        # Cond A: SE branch (x >= 0.25, y <= -0.15); Cond B: NE branch (x >= 0.25, y >= 0.15)
        return (x >= 0.25 and y <= -0.15) if cond == "A" else (x >= 0.25 and y >= 0.15)
    elif fam_key == "family_3":
        # Cond A (P1): North corridor (y >= 1.75); Cond B (P2): East corridor (x >= 2.05)
        return (y >= 1.75) if cond == "A" else (x >= 2.05)
    elif fam_key == "family_4":
        # Cond A: Detour corridor (y >= 0.45); Cond B: Straight corridor (x >= 0.65)
        return (y >= 0.45) if cond == "A" else (x >= 0.65)
    elif fam_key == "family_5":
        # Cond A: Right aperture (y <= -0.40); Cond B: Left aperture (y >= 0.40)
        return (y <= -0.40) if cond == "A" else (y >= 0.40)
    return False


def run_single_arm_trial(
    hal: CarlStage1HAL,
    delib: CARLStage2_3R1DeliberationEngine,
    cloned_qpos: np.ndarray,
    cloned_qvel: np.ndarray,
    cloned_time: float,
    cloned_pose: np.ndarray,
    cloned_v_hat: float,
    cloned_w_hat: float,
    fam_key: str,
    cond: str,
    horizon: int = EVAL_HORIZON
) -> Dict[str, Any]:
    qa = int(hal.model.joint("spatial_identity").qposadr[0])

    # Restore exact cloned simulation state
    hal.data.qpos[:] = np.copy(cloned_qpos)
    hal.data.qvel[:] = np.copy(cloned_qvel)
    hal.data.time = cloned_time
    mujoco.mj_forward(hal.model, hal.data)

    # Restore exact cognitive engine dead reckoning state
    delib.pose = np.copy(cloned_pose)
    delib.v_hat = cloned_v_hat
    delib.w_hat = cloned_w_hat

    trajectory = []
    collision_occurred = False
    success = False
    ticks_to_goal = None
    latencies = []
    actions_taken = []

    for step in range(horizon):
        # 1. Read anonymous local sensors s in R^25
        sensors = hal.read_sensors()
        sonar_rays = sensors[:15]
        curr_v = float(sensors[21])
        curr_w = float(sensors[18])

        # 2. Check collision against walls
        for i in range(hal.data.ncon):
            c = hal.data.contact[i]
            g1 = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1) or ""
            g2 = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2) or ""
            if "floor" not in g1 and "floor" not in g2:
                collision_occurred = True
                break

        if collision_occurred:
            break

        # 3. Check goal reached
        px, py = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        trajectory.append([px, py])

        if check_goal_reached(fam_key, cond, (px, py)):
            success = True
            ticks_to_goal = step + 1
            break

        # 4. Cognitive decision step
        t0 = time.perf_counter()
        action, telem = delib.select_action(sonar_rays, curr_v=curr_v, curr_w=curr_w)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt_ms)
        actions_taken.append([float(action[0]), float(action[1])])

        # 5. Physics step
        hal.step(action)

    final_pos = [float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])]

    return {
        "success": success,
        "collision": collision_occurred,
        "ticks_to_goal": ticks_to_goal,
        "final_pos": final_pos,
        "trajectory": trajectory,
        "mean_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        "p95_latency_ms": float(np.percentile(latencies, 95)) if latencies else 0.0,
        "first_action": actions_taken[0] if actions_taken else [0.0, 0.0],
    }


def compute_exact_mcnemar(n10: int, n01: int) -> float:
    """Computes exact one-sided McNemar binomial p-value for H1: p(n10) > p(n01)."""
    nd = n10 + n01
    if nd == 0:
        return 1.0
    from scipy.stats import binom
    # Probability of getting >= n10 successes under Binomial(nd, 0.5)
    p_val = float(binom.sf(n10 - 1, nd, 0.5))
    return p_val


def run_stage3_2RB_memory_necessity_battery() -> Dict[str, Any]:
    print("=========================================================================")
    print("CARL-DX STAGE 3.2-RB: SPATIAL MEMORY NECESSITY BATTERY (500 EPISODES)")
    print("Classification: [STAGE 3.2-RB BENCHMARK] Pre-Registered Double-Blind Protocol")
    print("=========================================================================")

    all_trial_records = []
    contingency_I_A = {"n11": 0, "n10": 0, "n01": 0, "n00": 0}
    contingency_I_S = {"n11": 0, "n10": 0, "n01": 0, "n00": 0}

    arm_successes = {"ARM-I": 0, "ARM-A": 0, "ARM-S": 0, "ARM-PF": 0, "ARM-R": 0}
    arm_collisions = {"ARM-I": 0, "ARM-A": 0, "ARM-S": 0, "ARM-PF": 0, "ARM-R": 0}
    delta_u_I_A = []
    all_p95_latencies = []

    pair_idx = 0

    for fam_key, task_spec in TASK_CONFIGS.items():
        print(f"\n=========================================================================")
        print(f"EVALUATING TASK: {fam_key.upper()} — {task_spec['name']}")
        print(f"=========================================================================")

        for seed in SEEDS:
            rng = np.random.RandomState(seed)
            for trial in range(TRIALS_PER_SEED):
                pair_idx += 1
                cond = "A" if (pair_idx % 2 == 1) else "B"
                fam_str = fam_key.replace("_", "")
                xml_name = f"{fam_str}_cond{cond}.xml" if fam_key not in ["family_3", "family_5"] else f"{fam_str}_layout.xml"
                xml_path = repo_root / "world" / "stage3_2R_environments" / xml_name
                grid_path = task_spec["grid_A"] if cond == "A" else task_spec["grid_B"]

                # 1. Setup HAL and approach phase
                hal = CarlStage1HAL(xml_path=str(xml_path))
                qa = int(hal.model.joint("spatial_identity").qposadr[0])

                dx = float(rng.uniform(-0.010, 0.010))
                dy = float(rng.uniform(-0.010, 0.010))
                dyaw = float(rng.uniform(-0.008, 0.008))

                if fam_key == "family_3":
                    nominal_spawn = task_spec["pos_A"] if cond == "A" else task_spec["pos_B"]
                else:
                    nominal_spawn = task_spec["nominal_pos"]

                spawn_x = nominal_spawn[0] + dx
                spawn_y = nominal_spawn[1] + dy
                spawn_yaw = task_spec["nominal_yaw"] + dyaw

                hal.reset()
                hal.data.qpos[qa:qa+2] = [spawn_x, spawn_y]
                hal.data.qpos[qa+3:qa+7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
                hal.data.qvel[:] = 0.0
                hal.data.ctrl[:] = 0.0
                mujoco.mj_forward(hal.model, hal.data)

                # Initialize cognitive deliberative agent
                delib_master = CARLStage2_3R1DeliberationEngine(grid_path=grid_path, mode="deliberative")
                delib_master.initialize_pose(spawn_x, spawn_y, spawn_yaw)

                # 2. Advance approach phase to T_crit
                t_crit = task_spec["t_crit"]
                u_approach = np.array([0.65, 0.65, 0.0, 0.0, 0.0, 0.0])
                for t in range(t_crit):
                    sensors = hal.read_sensors()
                    curr_v = float(sensors[21])
                    curr_w = float(sensors[18])
                    delib_master.update_odometry(curr_v, curr_w, dt=0.030)
                    hal.step(u_approach)

                # 3. AT T_CRIT: DEEP CLONE PHYSICAL AND CONTROLLER STATE
                cloned_qpos = np.copy(hal.data.qpos)
                cloned_qvel = np.copy(hal.data.qvel)
                cloned_time = float(hal.data.time)
                cloned_pose = np.copy(delib_master.pose)
                cloned_v_hat = float(delib_master.v_hat)
                cloned_w_hat = float(delib_master.w_hat)

                # 4. INSTANTIATE THE 5 INTERVENTION ARMS
                # ARM-I: Intact memory
                delib_I = CARLStage2_3R1DeliberationEngine(grid_path=grid_path, mode="deliberative")
                res_I = run_single_arm_trial(hal, delib_I, cloned_qpos, cloned_qvel, cloned_time, cloned_pose, cloned_v_hat, cloned_w_hat, fam_key, cond)

                # ARM-A: Amnesic memory (M_env = 0)
                delib_A = CARLStage2_3R1DeliberationEngine(grid_path=grid_path, mode="amnesic")
                res_A = run_single_arm_trial(hal, delib_A, cloned_qpos, cloned_qvel, cloned_time, cloned_pose, cloned_v_hat, cloned_w_hat, fam_key, cond)

                # ARM-S: Topographically scrambled memory
                delib_S = CARLStage2_3R1DeliberationEngine(grid_path=grid_path, mode="deliberative")
                delib_S.grid = scramble_grid_16x16(delib_S.grid, seed=seed)
                res_S = run_single_arm_trial(hal, delib_S, cloned_qpos, cloned_qvel, cloned_time, cloned_pose, cloned_v_hat, cloned_w_hat, fam_key, cond)

                # ARM-PF: Potential field reactive baseline
                delib_PF = CARLStage2_3R1DeliberationEngine(grid_path=grid_path, mode="potential_field")
                res_PF = run_single_arm_trial(hal, delib_PF, cloned_qpos, cloned_qvel, cloned_time, cloned_pose, cloned_v_hat, cloned_w_hat, fam_key, cond)

                # ARM-R: Scripted reflex baseline
                delib_R = CARLStage2_3R1DeliberationEngine(grid_path=grid_path, mode="reflex")
                res_R = run_single_arm_trial(hal, delib_R, cloned_qpos, cloned_qvel, cloned_time, cloned_pose, cloned_v_hat, cloned_w_hat, fam_key, cond)

                # 5. Record Results
                du = float(np.linalg.norm(np.array(res_I["first_action"]) - np.array(res_A["first_action"])))
                delta_u_I_A.append(du)
                all_p95_latencies.append(res_I["p95_latency_ms"])

                # Update Successes & Collisions
                for arm_name, r in [("ARM-I", res_I), ("ARM-A", res_A), ("ARM-S", res_S), ("ARM-PF", res_PF), ("ARM-R", res_R)]:
                    if r["success"]: arm_successes[arm_name] += 1
                    if r["collision"]: arm_collisions[arm_name] += 1

                # Update Contingency Tables
                sI = res_I["success"]
                sA = res_A["success"]
                sS = res_S["success"]

                if sI and sA: contingency_I_A["n11"] += 1
                elif sI and not sA: contingency_I_A["n10"] += 1
                elif not sI and sA: contingency_I_A["n01"] += 1
                else: contingency_I_A["n00"] += 1

                if sI and sS: contingency_I_S["n11"] += 1
                elif sI and not sS: contingency_I_S["n10"] += 1
                elif not sI and sS: contingency_I_S["n01"] += 1
                else: contingency_I_S["n00"] += 1

                trial_record = {
                    "pair_idx": pair_idx,
                    "family": fam_key,
                    "condition": cond,
                    "seed": seed,
                    "trial_in_seed": trial,
                    "delta_u_I_A": du,
                    "ARM-I": {"success": res_I["success"], "collision": res_I["collision"], "ticks": res_I["ticks_to_goal"], "final_pos": res_I["final_pos"]},
                    "ARM-A": {"success": res_A["success"], "collision": res_A["collision"], "ticks": res_A["ticks_to_goal"], "final_pos": res_A["final_pos"]},
                    "ARM-S": {"success": res_S["success"], "collision": res_S["collision"], "ticks": res_S["ticks_to_goal"], "final_pos": res_S["final_pos"]},
                    "ARM-PF": {"success": res_PF["success"], "collision": res_PF["collision"], "ticks": res_PF["ticks_to_goal"], "final_pos": res_PF["final_pos"]},
                    "ARM-R": {"success": res_R["success"], "collision": res_R["collision"], "ticks": res_R["ticks_to_goal"], "final_pos": res_R["final_pos"]},
                }
                all_trial_records.append(trial_record)

                print(f"Pair {pair_idx:3d}/100 [{fam_key} Cond {cond} Seed {seed}] | I:{'WIN' if sI else '---'} A:{'WIN' if sA else '---'} S:{'WIN' if sS else '---'} | ||Du||={du:.3f}")

    # 6. COMPUTE FINAL METRICS & SCORECARD
    total_pairs = 100
    p_I = arm_successes["ARM-I"] / total_pairs
    p_A = arm_successes["ARM-A"] / total_pairs
    p_S = arm_successes["ARM-S"] / total_pairs
    p_PF = arm_successes["ARM-PF"] / total_pairs
    p_R = arm_successes["ARM-R"] / total_pairs

    delta_I_A = p_I - p_A
    delta_I_S = p_I - p_S

    cr_I = arm_collisions["ARM-I"] / total_pairs
    p_val_I_A = compute_exact_mcnemar(contingency_I_A["n10"], contingency_I_A["n01"])
    p_val_I_S = compute_exact_mcnemar(contingency_I_S["n10"], contingency_I_S["n01"])

    pass_g6 = bool(delta_I_A >= 0.350)
    pass_g7 = bool(p_val_I_A < 0.001)
    pass_g8 = bool(delta_I_S >= 0.250 and p_val_I_S < 0.010)
    pass_g9 = bool(cr_I <= 0.050)

    class_b_passed = bool(pass_g6 and pass_g7 and pass_g8 and pass_g9)

    scorecard = {
        "subgate": "3.2-RB",
        "title": "Spatial Memory Necessity under Non-Line-of-Sight Conditions (Class B)",
        "total_episodes_evaluated": 500,
        "total_matched_pairs": 100,
        "sample_counts": {
            "episodes_per_arm": 100,
            "arms_evaluated": ["ARM-I", "ARM-A", "ARM-S", "ARM-PF", "ARM-R"],
            "pairs_per_family": 20,
            "total_families": 5,
        },
        "success_rates": {
            "ARM-I": f"{p_I*100:.1f}% ({arm_successes['ARM-I']}/100)",
            "ARM-A": f"{p_A*100:.1f}% ({arm_successes['ARM-A']}/100)",
            "ARM-S": f"{p_S*100:.1f}% ({arm_successes['ARM-S']}/100)",
            "ARM-PF": f"{p_PF*100:.1f}% ({arm_successes['ARM-PF']}/100)",
            "ARM-R": f"{p_R*100:.1f}% ({arm_successes['ARM-R']}/100)",
        },
        "collision_rates": {
            "ARM-I": f"{cr_I*100:.1f}% ({arm_collisions['ARM-I']}/100)",
            "ARM-A": f"{arm_collisions['ARM-A']/total_pairs*100:.1f}% ({arm_collisions['ARM-A']}/100)",
            "ARM-S": f"{arm_collisions['ARM-S']/total_pairs*100:.1f}% ({arm_collisions['ARM-S']}/100)",
            "ARM-PF": f"{arm_collisions['ARM-PF']/total_pairs*100:.1f}% ({arm_collisions['ARM-PF']}/100)",
            "ARM-R": f"{arm_collisions['ARM-R']/total_pairs*100:.1f}% ({arm_collisions['ARM-R']}/100)",
        },
        "contingency_table_I_vs_A": contingency_I_A,
        "contingency_table_I_vs_S": contingency_I_S,
        "effect_sizes": {
            "delta_success_I_A": delta_I_A,
            "exact_mcnemar_p_I_A": p_val_I_A,
            "delta_success_I_S": delta_I_S,
            "exact_mcnemar_p_I_S": p_val_I_S,
            "mean_delta_u_I_A": float(np.mean(delta_u_I_A)),
            "p95_latency_ms": float(np.percentile(all_p95_latencies, 95)),
        },
        "gates": {
            "G6_primary_effect": {"metric": delta_I_A, "threshold": ">= 35.0%", "passed": pass_g6},
            "G7_exact_mcnemar_significance": {"metric": p_val_I_A, "threshold": "< 0.001", "passed": pass_g7},
            "G8_topographic_specificity": {"metric_delta": delta_I_S, "metric_p": p_val_I_S, "threshold": "Delta >= 25.0%, p < 0.010", "passed": pass_g8},
            "G9_intact_collision_rate": {"metric": cr_I, "threshold": "<= 5.0%", "passed": pass_g9},
        },
        "class_b_certification": "CERTIFIED" if class_b_passed else "FAILED_CLOSED",
    }

    # Save outputs
    raw_path = RAW_DIR / "stage3_2RB_raw_trials.json"
    score_path = SCORE_DIR / "stage3_2R_scorecard.json"

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"summary": scorecard, "trials": all_trial_records}, f, indent=2)

    with open(score_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    print("\n=========================================================================")
    print("STAGE 3.2-RB MASTER SCORECARD (CLASS B: SPATIAL MEMORY NECESSITY)")
    print("=========================================================================")
    print(f"ARM-I Success Rate : {scorecard['success_rates']['ARM-I']}")
    print(f"ARM-A Success Rate : {scorecard['success_rates']['ARM-A']}")
    print(f"ARM-S Success Rate : {scorecard['success_rates']['ARM-S']}")
    print(f"ARM-PF Success Rate: {scorecard['success_rates']['ARM-PF']}")
    print(f"ARM-R Success Rate : {scorecard['success_rates']['ARM-R']}")
    print("-------------------------------------------------------------------------")
    print(f"G6: Delta-Success (I - A)     : {delta_I_A*100:+.1f}% (threshold >= +35.0%) -> {'PASS' if pass_g6 else 'FAIL'}")
    print(f"G7: Exact McNemar Significance : p = {p_val_I_A:.2e} (threshold < 0.001)   -> {'PASS' if pass_g7 else 'FAIL'}")
    print(f"G8: Topographic Specificity   : Delta = {delta_I_S*100:+.1f}%, p = {p_val_I_S:.2e} -> {'PASS' if pass_g8 else 'FAIL'}")
    print(f"G9: Intact Collision Rate     : {cr_I*100:.1f}% (threshold <= 5.0%)        -> {'PASS' if pass_g9 else 'FAIL'}")
    print("-------------------------------------------------------------------------")
    print(f"CLASS B CAUSAL CERTIFICATION  : {scorecard['class_b_certification']}")
    print(f"Saved Raw Trials Ledger       : {raw_path}")
    print(f"Saved Authoritative Scorecard : {score_path}")
    print("=========================================================================\n")

    return scorecard


if __name__ == "__main__":
    run_stage3_2RB_memory_necessity_battery()
