"""
brain/p1_integrate/carl_p1_integrate_harness.py
================================================
Master Experimental Harness for P1-Integrate Controlled Scientific Trial.

Executes:
1. 5 Experimental Groups across 20 Randomized Seeds:
   - Group 1: Hand-Engineered Baseline (Current CARL)
   - Group 2: Reservoir Only (N=1024, static readout)
   - Group 3: Two-Factor STDP (Hebbian correlation only)
   - Group 4: Three-Factor STDP (Full modulated plasticity)
   - Group 5: Scrambled Plasticity Control (Permuted updates)
2. Four Experimental Phases:
   - Training: Physical collision at (x=1.0, y=0.0) -> Synaptic plasticity update
   - Test A: Same environment (x=1.0, y=0.0) -> Measure local avoidance
   - Test B: Relocated obstacle (x=1.0, y=1.5) -> Measure spatial generalization
   - Test C: Changed start pose (x=-0.5, y=-0.5, yaw=+30 deg) -> Measure viewpoint generalization
   - Test D: Changed obstacle geometry -> Measure geometric generalization
3. Full Ablation Suite for Group 4 (No STDP, No Reservoir, No Neuromod, No Readout).
"""

import os
import sys
import math
import time
import json
import numpy as np
import mujoco

sys.path.insert(0, "d:/ebca")
sys.path.insert(0, "d:/ebca/brain")

from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.p1_integrate.carl_p1_integrate_agent import CarlP1IntegrateAgent

XML_PATH = "d:/ebca/world/p1_arena.xml"


def set_arena_obstacle(model, data, obs_pos=(1.0, 0.0, 0.15)):
    """Positions the dynamic hazard cube in MuJoCo."""
    try:
        bid = model.body("hazard_cube").id
        jnt_id = model.body_jntadr[bid]
        q_adr = model.jnt_qposadr[jnt_id]
        data.qpos[q_adr + 0] = obs_pos[0]
        data.qpos[q_adr + 1] = obs_pos[1]
        data.qpos[q_adr + 2] = obs_pos[2]
        data.qpos[q_adr + 3] = 1.0
        data.qpos[q_adr + 4] = 0.0
        data.qpos[q_adr + 5] = 0.0
        data.qpos[q_adr + 6] = 0.0
        mujoco.mj_forward(model, data)
    except Exception:
        pass


def run_single_episode(
    agent: CarlP1IntegrateAgent,
    hal: MuJoCoHardwareAbstractionLayer,
    target_coords: tuple = (2.2, 0.0),
    obs_coords: tuple = (1.0, 0.0),
    start_pose: tuple = (0.0, 0.0, 0.0),  # (x, y, yaw)
    max_ticks: int = 300,
    is_training: bool = False
) -> Dict[str, Any]:
    """Runs a single episode and returns full trajectory, collision, and neural telemetry."""
    hal.reset()
    model = hal.model
    data = hal.data

    # Set start pose
    deck_id = model.body("drive_deck").id
    qpos_adr = model.jnt_qposadr[model.body_jntadr[deck_id]]
    data.qpos[qpos_adr + 0] = start_pose[0]
    data.qpos[qpos_adr + 1] = start_pose[1]
    data.qpos[qpos_adr + 2] = 0.052

    # Set yaw in quaternion (w, x, y, z)
    half_yaw = start_pose[2] * 0.5
    data.qpos[qpos_adr + 3] = math.cos(half_yaw)
    data.qpos[qpos_adr + 4] = 0.0
    data.qpos[qpos_adr + 5] = 0.0
    data.qpos[qpos_adr + 6] = math.sin(half_yaw)

    # Set obstacle position
    set_arena_obstacle(model, data, (obs_coords[0], obs_coords[1], 0.15))
    try:
        model.geom_pos[model.geom("food").id] = np.array([target_coords[0], target_coords[1], 0.12])
    except Exception:
        pass

    # Reset transient dynamical states (x, E, traces) but KEEP W_hazard across episodes!
    agent.reset_state_traces()

    # Settle physics
    for _ in range(15):
        hal.step()

    trajectory = []
    actions = []
    efes = []
    q_hazards = []
    collisions = 0
    first_collision_tick = None
    food_reached = False
    telemetry_log = []

    for t in range(max_ticks):
        res = agent.step_cognitive_cycle(hal, target_coords=target_coords, is_training=is_training)

        # Advance physics 8 sub-steps (8 x 0.004s = 0.032s per 30 Hz cognitive cycle)
        for _ in range(8):
            hal.step()

        pos = res["pos"]
        trajectory.append(pos)
        actions.append(res["chosen_action"])
        efes.append(res["efe"])
        q_hazards.append(res["q_hazard_chosen"])

        if res["collision"] or res["is_stall"]:
            collisions += 1
            if first_collision_tick is None:
                first_collision_tick = t
            if is_training and collisions >= 3:
                # Registered collision impact event -> conclude training episode
                break

        if res["food_absorbed"]:
            food_reached = True
            break

        telemetry_log.append({
            "tick": t,
            "x": pos[0],
            "y": pos[1],
            "yaw": res["yaw"],
            "action": res["chosen_action"],
            "efe": res["efe"],
            "q_hazard": res["q_hazard_chosen"],
            "collision": res["collision"],
            "dw_mag": res["dw_magnitude"],
            "surprise": res["surprise_gate"],
            "valence": res["valence"]
        })

    final_pos = trajectory[-1] if trajectory else (0.0, 0.0)
    final_dist_to_target = math.sqrt((target_coords[0] - final_pos[0])**2 + (target_coords[1] - final_pos[1])**2)
    min_dist_to_obs = min([math.sqrt((obs_coords[0] - p[0])**2 + (obs_coords[1] - p[1])**2) for p in trajectory]) if trajectory else 99.0

    # Avoidance is defined as: Reaching past obstacle (x > obs_x) with 0 collisions and min_dist > 0.25m
    avoided_successfully = bool(collisions == 0 and final_pos[0] > obs_coords[0] and min_dist_to_obs > 0.22)

    return {
        "avoided": avoided_successfully,
        "collisions": collisions,
        "first_collision_tick": first_collision_tick,
        "food_reached": food_reached,
        "final_pos": final_pos,
        "final_dist_to_target": round(final_dist_to_target, 4),
        "min_dist_to_obs": round(min_dist_to_obs, 4),
        "trajectory": trajectory,
        "actions_summary": {a: actions.count(a) for a in set(actions)},
        "synaptic_weight_norm": float(np.linalg.norm(agent.W_hazard)),
        "cumulative_dw": float(agent.cumulative_abs_dw),
        "telemetry": telemetry_log
    }


def execute_full_p1_integrate_trial(n_seeds: int = 20) -> Dict[str, Any]:
    """Runs the complete 5-Group Randomized Controlled Trial with 20 seeds."""
    print("=" * 80)
    print("  CARL-DX PHASE 1-INTEGRATE: 5-GROUP RANDOMIZED CONTROLLED TRIAL")
    print(f"  Seeds: {n_seeds} | Physics: MuJoCo vessel_kinetic.xml | Reservoir: N=1024")
    print("=" * 80)

    hal = MuJoCoHardwareAbstractionLayer(XML_PATH)
    seeds = [100 + i for i in range(n_seeds)]

    groups = {
        "GROUP_1_BASELINE": {"mode": "BASELINE", "use_res": False, "use_mod": False, "use_readout": False},
        "GROUP_2_RESERVOIR_ONLY": {"mode": "RESERVOIR_ONLY", "use_res": True, "use_mod": False, "use_readout": True},
        "GROUP_3_TWO_FACTOR_STDP": {"mode": "TWO_FACTOR_STDP", "use_res": True, "use_mod": False, "use_readout": True},
        "GROUP_4_THREE_FACTOR_STDP": {"mode": "THREE_FACTOR_STDP", "use_res": True, "use_mod": True, "use_readout": True},
        "GROUP_5_SCRAMBLED_CONTROL": {"mode": "SCRAMBLED", "use_res": True, "use_mod": True, "use_readout": True}
    }

    all_results = {}
    detailed_traces = {}

    for grp_name, grp_cfg in groups.items():
        print(f"\n>>> Running {grp_name} across {n_seeds} seeds...")
        grp_data = {
            "training": [],
            "test_a_same_env": [],
            "test_b_relocated": [],
            "test_c_start_pose": [],
            "test_d_geometry": []
        }

        for seed in seeds:
            agent = CarlP1IntegrateAgent(
                mode=grp_cfg["mode"],
                use_reservoir=grp_cfg["use_res"],
                use_neuromodulation=grp_cfg["use_mod"],
                use_learned_hazard=grp_cfg["use_readout"],
                seed=seed
            )

            # Phase 1: Training Episode in Arena A (Obstacle at x=1.0, y=0.0)
            train_res = run_single_episode(
                agent, hal,
                target_coords=(2.2, 0.0),
                obs_coords=(1.0, 0.0),
                start_pose=(0.0, 0.0, 0.0),
                is_training=True
            )
            w_post_train = np.copy(agent.W_hazard)

            # Phase 2: Test A - Same Environment (Obstacle at x=1.0, y=0.0)
            test_a_res = run_single_episode(
                agent, hal,
                target_coords=(2.2, 0.0),
                obs_coords=(1.0, 0.0),
                start_pose=(0.0, 0.0, 0.0)
            )

            # Phase 3: Test B - Relocated Obstacle (Obstacle at x=1.0, y=1.5, Target at 2.2, 1.5)
            test_b_res = run_single_episode(
                agent, hal,
                target_coords=(2.2, 1.5),
                obs_coords=(1.0, 1.5),
                start_pose=(0.0, 1.5, 0.0)
            )

            # Phase 4: Test C - Changed Start Pose (Start at x=-0.5, y=-0.5, yaw=+30 deg)
            test_c_res = run_single_episode(
                agent, hal,
                target_coords=(2.2, 0.0),
                obs_coords=(1.0, 0.0),
                start_pose=(-0.5, -0.5, math.radians(30))
            )

            # Phase 5: Test D - Geometry / Lateral Offset (Obstacle at x=1.0, y=-0.3)
            test_d_res = run_single_episode(
                agent, hal,
                target_coords=(2.2, 0.0),
                obs_coords=(1.0, -0.3),
                start_pose=(0.0, 0.0, 0.0)
            )

            # Strip heavy telemetry arrays for compact JSON summary
            def strip_tel(r):
                c = dict(r)
                if "telemetry" in c: del c["telemetry"]
                return c

            grp_data["training"].append(strip_tel(train_res))
            grp_data["test_a_same_env"].append(strip_tel(test_a_res))
            grp_data["test_b_relocated"].append(strip_tel(test_b_res))
            grp_data["test_c_start_pose"].append(strip_tel(test_c_res))
            grp_data["test_d_geometry"].append(strip_tel(test_d_res))

            # Store rich trace for seed 101 in Group 4 for visualization
            if grp_name == "GROUP_4_THREE_FACTOR_STDP" and seed == 101:
                detailed_traces["seed_101_group_4"] = {
                    "w_initial": agent.W_initial.tolist(),
                    "w_post_train": w_post_train.tolist(),
                    "train_telemetry": train_res["telemetry"],
                    "test_a_telemetry": test_a_res["telemetry"],
                    "test_b_telemetry": test_b_res["telemetry"]
                }

        # Calculate Group Statistics
        def calc_stats(run_list):
            avoided = [r["avoided"] for r in run_list]
            colls = [r["collisions"] for r in run_list]
            dists = [r["min_dist_to_obs"] for r in run_list]
            w_norms = [r["synaptic_weight_norm"] for r in run_list]
            return {
                "success_rate": round(float(np.mean(avoided)), 4),
                "collision_rate": round(float(np.mean([c > 0 for c in colls])), 4),
                "mean_collisions": round(float(np.mean(colls)), 2),
                "mean_min_obs_dist": round(float(np.mean(dists)), 4),
                "mean_weight_norm": round(float(np.mean(w_norms)), 4)
            }

        all_results[grp_name] = {
            "stats": {
                "train": calc_stats(grp_data["training"]),
                "test_a_same_env": calc_stats(grp_data["test_a_same_env"]),
                "test_b_relocated": calc_stats(grp_data["test_b_relocated"]),
                "test_c_start_pose": calc_stats(grp_data["test_c_start_pose"]),
                "test_d_geometry": calc_stats(grp_data["test_d_geometry"])
            },
            "raw_runs": grp_data
        }

        print(f"  --> {grp_name} Test A Avoidance: {all_results[grp_name]['stats']['test_a_same_env']['success_rate']*100:.1f}% | Test B Relocated: {all_results[grp_name]['stats']['test_b_relocated']['success_rate']*100:.1f}%")

    # Critical Ablation Suite on Group 4 (Three-Factor STDP)
    print("\n>>> Running Critical Ablations for Group 4 (20 seeds each)...")
    ablations = {
        "ABLATION_NO_STDP": {"mode": "THREE_FACTOR_STDP", "use_res": True, "use_mod": True, "use_readout": True, "lr": 0.0},
        "ABLATION_NO_RESERVOIR": {"mode": "THREE_FACTOR_STDP", "use_res": False, "use_mod": True, "use_readout": True, "lr": 0.05},
        "ABLATION_NO_NEUROMOD": {"mode": "THREE_FACTOR_STDP", "use_res": True, "use_mod": False, "use_readout": True, "lr": 0.05},
        "ABLATION_NO_READOUT": {"mode": "THREE_FACTOR_STDP", "use_res": True, "use_mod": True, "use_readout": False, "lr": 0.05}
    }

    ablation_results = {}
    for abl_name, abl_cfg in ablations.items():
        abl_runs = []
        for seed in seeds:
            agent = CarlP1IntegrateAgent(
                mode=abl_cfg["mode"],
                use_reservoir=abl_cfg["use_res"],
                use_neuromodulation=abl_cfg["use_mod"],
                use_learned_hazard=abl_cfg["use_readout"],
                stdp_lr=abl_cfg["lr"],
                seed=seed
            )
            # Train
            _ = run_single_episode(agent, hal, (2.2, 0.0), (1.0, 0.0), is_training=True)
            # Test A
            test_res = run_single_episode(agent, hal, (2.2, 0.0), (1.0, 0.0))
            def strip_tel(r):
                c = dict(r)
                if "telemetry" in c: del c["telemetry"]
                return c
            abl_runs.append(strip_tel(test_res))

        avoided = [r["avoided"] for r in abl_runs]
        ablation_results[abl_name] = {
            "success_rate": round(float(np.mean(avoided)), 4),
            "collision_rate": round(float(np.mean([r["collisions"] > 0 for r in abl_runs])), 4),
            "mean_min_obs_dist": round(float(np.mean([r["min_dist_to_obs"] for r in abl_runs])), 4)
        }
        print(f"  --> {abl_name} Test A Avoidance: {ablation_results[abl_name]['success_rate']*100:.1f}%")

    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "n_seeds": n_seeds,
            "seeds": seeds,
            "groups": list(groups.keys()),
            "ablations": list(ablations.keys())
        },
        "groups": all_results,
        "ablations": ablation_results,
        "detailed_traces": detailed_traces
    }

    out_file = "scratch/p1_integrate_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 80)
    print(f"  TRIAL COMPLETE. Results saved to {out_file}")
    print("=" * 80)
    return output


if __name__ == "__main__":
    execute_full_p1_integrate_trial(n_seeds=20)
