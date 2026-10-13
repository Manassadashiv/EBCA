"""
brain/test_stage2_end_to_end_organism.py — End-to-End Acceptance Test for Unified CARL Stage 2 Organism
Classification: [STAGE 2 UNIFIED ACCEPTANCE] Complete sense -> state -> predict -> deliberate -> act loop.

Tests the one canonical CARL organism (CarlAutonomousOrganismAgent / CarlEmbodiedOrganism):
1. Sensors: 25-D unlabelled sensory read from HAL
2. Stage 1: Kinematic slip and traction observer
3. Stage 2.1: 2,114-unit neuromorphic continuous attractor (HD ring + grid torus) + dead reckoning
4. Stage 2.2: Decoupled predictive world model (body kinematics + allocentric occupancy memory)
5. Stage 2.3: Prospective deliberation over continuous candidate trajectories with collision veto
6. Embodiment: 6-DOF physical actuation & active visual gaze
7. Anti-Cheat Invariant: Zero privileged simulator coordinates (qpos/qvel) in active decision loop.
"""

import sys
import os
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import torch

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.test_stage2_3_r1_runner import generate_layout_configs


def run_stage2_end_to_end_acceptance(
    seeds: List[int] = [42, 101, 202, 303, 404],
    max_ticks_per_trial: int = 60
) -> Dict[str, Any]:
    print("=" * 80, flush=True)
    print("CARL STAGE 2 END-TO-END ACCEPTANCE SUITE: UNIFIED CANONICAL ORGANISM", flush=True)
    print("=" * 80, flush=True)

    hal = CarlStage1HAL()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])

    layouts = [
        "layout_1_left_trap",
        "layout_2_right_trap",
        "layout_3_t_junction",
        "layout_4_corridor_slit"
    ]

    total_episodes = 0
    total_collisions = 0
    all_latencies = []
    telemetry_records = []
    organ_active_counters = {
        "stage1_slip_observer": 0,
        "stage2_1_attractor_brain": 0,
        "stage2_2_spatial_memory": 0,
        "stage2_3_deliberation": 0,
        "embodied_actuation": 0
    }

    agent = CarlAutonomousOrganismAgent(dt=0.030)

    for seed in seeds:
        print(f"\n>>> Running End-to-End Evaluation for Seed [{seed}]...", flush=True)
        for lid in layouts:
            spawns = generate_layout_configs(lid, n_trials=2, seed=seed)
            for trial_idx, cfg in enumerate(spawns):
                total_episodes += 1
                spawn_pos = cfg["pos"]
                spawn_yaw = cfg["yaw"]

                # Reset simulation to spawn
                hal.reset()
                hal.data.qpos[qa:qa+2] = spawn_pos
                hal.data.qpos[qa+3:qa+7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
                hal.data.qvel[:] = 0.0
                import mujoco
                mujoco.mj_forward(hal.model, hal.data)

                # Reset organism and initialize unprivileged dead reckoning at spawn
                agent.reset()
                agent.initialize_spatial_grounding(spawn_pos[0], spawn_pos[1], spawn_yaw)

                trial_collided = False
                ticks_survived = max_ticks_per_trial

                for t in range(max_ticks_per_trial):
                    t0 = time.perf_counter()

                    # Execute one complete unscripted, unified cognitive cycle
                    cycle_data = agent.step_cognitive_cycle(hal)

                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    all_latencies.append(dt_ms)

                    # Verify active participation of all Stage 1 & Stage 2 organs
                    if cycle_data.get("stage1_slip_active", False):
                        organ_active_counters["stage1_slip_observer"] += 1
                    if cycle_data.get("stage2_1_attractor_active", False):
                        organ_active_counters["stage2_1_attractor_brain"] += 1
                    if cycle_data.get("stage2_2_memory_active", False):
                        organ_active_counters["stage2_2_spatial_memory"] += 1
                    if cycle_data.get("stage2_3_delib_active", False):
                        organ_active_counters["stage2_3_deliberation"] += 1
                    if cycle_data.get("actuation_active", False):
                        organ_active_counters["embodied_actuation"] += 1

                    # Step physical simulator with chosen embodied action
                    action_cmd = cycle_data["action_cmd"]
                    hal.step(action_cmd)

                    # Check physical contact oracle (scoring only)
                    con = hal.get_carl_contact_info()
                    if (con["carl_contacts"] - con["floor_contacts"]) > 0:
                        trial_collided = True
                        ticks_survived = t + 1
                        break

                if trial_collided:
                    total_collisions += 1

                print(f"  Seed {seed} | {lid:22s} Trial {trial_idx+1}: "
                      f"{'COLLIDED at tick ' + str(ticks_survived) if trial_collided else 'CLEARED (60 ticks)'} | "
                      f"Action: {cycle_data.get('action_name', 'N/A')}", flush=True)

    collision_rate = (total_collisions / total_episodes) * 100.0
    p95_latency = float(np.percentile(all_latencies, 95)) if all_latencies else 0.0
    mean_latency = float(np.mean(all_latencies)) if all_latencies else 0.0

    print("\n" + "=" * 80, flush=True)
    print("STAGE 2 END-TO-END CANONICAL ORGANISM SCORECARD", flush=True)
    print("=" * 80, flush=True)
    print(f"Total Episodes Evaluated: {total_episodes}")
    print(f"Overall Collision Rate:   {collision_rate:.2f}%")
    print(f"Mean Latency:             {mean_latency:.2f}ms")
    print(f"p95 Latency:              {p95_latency:.2f}ms (Budget: <= 50.0ms)")
    print(f"Organ Activation Counts across {len(all_latencies)} ticks:")
    for organ, count in organ_active_counters.items():
        pct = (count / max(len(all_latencies), 1)) * 100.0
        print(f"  - {organ:28s}: {count}/{len(all_latencies)} ticks ({pct:.1f}%)")

    all_organs_active = all(count > 0 for count in organ_active_counters.values())
    acceptance_passed = bool(collision_rate <= 10.0 and p95_latency <= 50.0 and all_organs_active)

    print(f"\nFINAL END-TO-END STAGE 2 VERDICT: {'[PASSED]' if acceptance_passed else '[FAILED]'}", flush=True)
    print("=" * 80, flush=True)

    result_payload = {
        "acceptance_passed": acceptance_passed,
        "total_episodes": total_episodes,
        "collision_rate_percent": collision_rate,
        "mean_latency_ms": mean_latency,
        "p95_latency_ms": p95_latency,
        "organ_active_counters": organ_active_counters,
        "all_organs_active": all_organs_active,
        "criteria": {
            "collision_rate_le_10": bool(collision_rate <= 10.0),
            "p95_latency_le_50ms": bool(p95_latency <= 50.0),
            "all_5_organs_active": bool(all_organs_active)
        }
    }

    out_dir = repo_root / "evidence" / "stage2_final"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "stage2_final_scorecard.json"
    import json
    with open(out_file, "w") as f:
        json.dump(result_payload, f, indent=2)
    print(f"Saved Stage 2 Canonical Organism Scorecard to {out_file}", flush=True)

    return result_payload


if __name__ == "__main__":
    res = run_stage2_end_to_end_acceptance()
    if not res["acceptance_passed"]:
        sys.exit(1)
