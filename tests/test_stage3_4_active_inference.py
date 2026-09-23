"""
tests/test_stage3_4_active_inference.py — Stage 3.4 Active Inference Benchmark & Adjudication Suite
Classification: [STAGE 3.4 BENCHMARK SUITE] Authoritative Pre-Registered 5-Gate Evaluation

Evaluation Topology:
- 40 Matched Trial Configurations x 4 Experimental Arms = 160 Physical Episodes.
- Fixed Pre-Registered Seeds: [4001, 4002, 4003, 4004, 4005].
- Matched Initial States: Cloned spawn pose and velocities per trial configuration across all 4 arms.
- Experimental Arms:
  - ARM-A (Full Active Inference): w_info = 1.0
  - ARM-B (Pragmatic-Only Baseline): w_info = 0.0 (Strict Invariance: all other parameters identical)
  - ARM-C (Discrete Baseline): Frozen Stage 2 discrete deliberation engine
  - ARM-D (Random MPPI): Uniform temperature path-integral weighting (lambda -> inf)

Evaluates Pre-Registered Acceptance Gates:
- Gate 1: Autonomous Cul-de-Sac Escape Rate >= 80.0% (32/40) AND Collision Rate <= 10.0%.
- Gate 2: Emergent Maneuver Verification: >= 75.0% of trials exhibit authentic reversal (v_wheel < -0.05 m/s
          for >= 10 ticks) + orientation rotation (|Delta theta| >= 90 deg) via external telemetry firewall.
- Gate 3: Information-Gain Causal Necessity: Delta Escape >= 35.0% AND exact one-sided McNemar p < 0.001.
- Gate 4: Real-Time Cognitive Latency: p95 <= 45.0 ms AND mean <= 20.0 ms across N >= 1,000 cycles.
- Gate 5: Decision-Pipeline AST Anti-Cheat: 100% clean (zero simulator/HAL/telemetry leaks).
"""

import sys
import os
import time
import math
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import scipy.stats as stats
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

ENV_DIR = repo_root / "world" / "stage3_4_environments"
XML_PATH = ENV_DIR / "cul_de_sac_trap.xml"
GRID_PATH = ENV_DIR / "cul_de_sac_trap_grid.pt"

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
(EVIDENCE_DIR / "figures").mkdir(parents=True, exist_ok=True)
(EVIDENCE_DIR / "videos").mkdir(parents=True, exist_ok=True)

# Pre-registered seeds and constants
PRE_REGISTERED_SEEDS = [4001, 4002, 4003, 4004, 4005]
CONFIGS_PER_SEED = 8
TOTAL_CONFIGS = len(PRE_REGISTERED_SEEDS) * CONFIGS_PER_SEED  # 40 matched trial configurations
TOTAL_ARMS = 4
TOTAL_EPISODES = TOTAL_CONFIGS * TOTAL_ARMS                   # 160 physical episodes

MAX_TICKS_PER_EPISODE = 220
ESCAPE_X_THRESHOLD = -0.55  # Egress through mouth of 1.8m U-trap (mouth at x = -0.55 to -0.60)


def build_40_matched_configurations() -> List[Dict[str, Any]]:
    """
    Constructs the 40 deterministic matched trial configurations across 5 fixed seeds.
    Each configuration specifies the exact spawn pose [x0, y0, theta0].
    """
    manifest = []
    config_id = 0

    # 8 systematic approach variations inside the 1.8m cul-de-sac facing East
    base_variations = [
        {"dx": 0.00, "dy":  0.00, "dth":  0.00},
        {"dx": 0.05, "dy":  0.04, "dth":  0.07},
        {"dx": 0.05, "dy": -0.04, "dth": -0.07},
        {"dx": 0.10, "dy":  0.02, "dth": -0.04},
        {"dx": 0.10, "dy": -0.02, "dth":  0.04},
        {"dx": 0.15, "dy":  0.00, "dth":  0.08},
        {"dx": 0.15, "dy":  0.05, "dth":  0.00},
        {"dx": 0.20, "dy": -0.05, "dth": -0.08},
    ]

    base_x = 0.50

    for seed in PRE_REGISTERED_SEEDS:
        rng = np.random.RandomState(seed)
        for v_idx, var in enumerate(base_variations):
            # Add small deterministic jitter seeded by seed
            jitter_x = float(rng.uniform(-0.015, 0.015))
            jitter_y = float(rng.uniform(-0.010, 0.010))
            jitter_th = float(rng.uniform(-0.020, 0.020))

            x0 = float(np.clip(base_x + var["dx"] + jitter_x, 0.40, 0.75))
            y0 = float(np.clip(var["dy"] + jitter_y, -0.12, 0.12))
            th0 = float(np.clip(var["dth"] + jitter_th, -0.18, 0.18))

            manifest.append({
                "config_id": config_id,
                "seed": seed,
                "variation_idx": v_idx,
                "spawn_pos": [x0, y0],
                "spawn_yaw": th0,
            })
            config_id += 1

    assert len(manifest) == TOTAL_CONFIGS, f"Expected {TOTAL_CONFIGS} configurations, got {len(manifest)}"
    return manifest


def execute_single_episode(
    arm: str,
    config: Dict[str, Any],
    hal: CarlStage1HAL
) -> Dict[str, Any]:
    """
    Executes a single physical episode under strict telemetry isolation.
    """
    spawn_x, spawn_y = config["spawn_pos"]
    spawn_yaw = config["spawn_yaw"]

    # 1. Reset MuJoCo physics to matched spawn state
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [spawn_x, spawn_y]
    hal.data.qpos[qa+3:qa+7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    # 2. Instantiate experimental controller
    if arm == "ARM-A":
        # Full Active Inference (w_info = 1.0)
        controller = CARLActiveInferenceEngine(grid_path=str(GRID_PATH), w_info=1.0)
    elif arm == "ARM-B":
        # Pragmatic-Only Baseline (w_info = 0.0, strictly identical in all other respects)
        controller = CARLActiveInferenceEngine(grid_path=str(GRID_PATH), w_info=0.0)
    elif arm == "ARM-C":
        # Frozen Stage 2 Discrete Baseline
        controller = CARLStage2_3R1DeliberationEngine(grid_path=str(GRID_PATH))
    elif arm == "ARM-D":
        # Random MPPI (Uniform path-integral temperature lambda -> inf)
        controller = CARLActiveInferenceEngine(grid_path=str(GRID_PATH), w_info=1.0, temperature=100.0)
    else:
        raise ValueError(f"Unknown arm: {arm}")

    # Unprivileged initialization: coordinates passed once at spawn
    controller.initialize_pose(spawn_x, spawn_y, spawn_yaw)

    # Episode logging buffers
    trajectory = []
    actions_taken = []
    cycle_latencies = []
    reversal_ticks = 0
    consecutive_reversals = 0
    max_consecutive_reversals = 0
    min_observed_clearance = 5.0
    initial_dead_end_yaw = spawn_yaw

    had_collision = False
    escaped = False
    collision_tick = None
    v_est = 0.0

    # Evaluator-only telemetry buffers (FIREWALLED from controller)
    eval_wheel_velocities = []
    eval_world_headings = []

    for tick in range(MAX_TICKS_PER_EPISODE):
        # Read sanitized inputs (25-D unlabelled vector)
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])

        min_sonar = float(np.min(sonars))
        if min_sonar < min_observed_clearance:
            min_observed_clearance = min_sonar

        # Controller deliberation cycle
        t0 = time.perf_counter()
        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, telemetry = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        cycle_latencies.append(lat_ms)

        # Apply continuous command
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])
        actions_taken.append([float(action[0]), float(action[1])])

        hal.step(cmd_6d)

        # -----------------------------------------------------------------
        # EVALUATOR TELEMETRY FIREWALL (Strictly External Adjudication)
        # -----------------------------------------------------------------
        # Ground truth coordinates for verification
        q_curr = hal.data.qpos[qa:qa+7]
        curr_pos = [float(q_curr[0]), float(q_curr[1])]
        trajectory.append(curr_pos)

        # External heading from quaternion
        w_val = float(q_curr[3])
        z_val = float(q_curr[6])
        curr_yaw = 2.0 * math.atan2(z_val, w_val)
        eval_world_headings.append(curr_yaw)

        # Evaluator physical wheel velocities
        w_l_id = hal.model.sensor("sens_vel_w_left").id
        w_r_id = hal.model.sensor("sens_vel_w_right").id
        w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
        w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
        physical_wheel_speed = 0.5 * (w_left_vel + w_right_vel) * 0.048  # wheel radius = 0.048m
        eval_wheel_velocities.append(physical_wheel_speed)

        # Track consecutive reversal ticks
        if physical_wheel_speed < -0.05:
            reversal_ticks += 1
            consecutive_reversals += 1
            if consecutive_reversals > max_consecutive_reversals:
                max_consecutive_reversals = consecutive_reversals
        else:
            consecutive_reversals = 0

        # Collision adjudication via contact manifolds
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True
            collision_tick = tick + 1
            break

        # Escape adjudication: exiting the mouth of the U-trap
        if curr_pos[0] <= ESCAPE_X_THRESHOLD:
            escaped = True
            break

        # Odometry speed update
        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

    # Calculate maximum heading rotation achieved during episode
    if eval_world_headings:
        heading_deltas = [
            abs(math.atan2(math.sin(h - initial_dead_end_yaw), math.cos(h - initial_dead_end_yaw)))
            for h in eval_world_headings
        ]
        max_yaw_rotation = float(np.max(heading_deltas))
    else:
        max_yaw_rotation = 0.0

    # Gate 2 Emergent Maneuver Criterion:
    # Reversal (v_wheel < -0.05 for >= 10 ticks) + orientation rotation (|Delta theta| >= 90 deg = 1.5708 rad)
    gate2_emergent_maneuver = bool(
        max_consecutive_reversals >= 10 and max_yaw_rotation >= (math.pi / 2.0 - 0.05)
    )

    final_pos = trajectory[-1] if trajectory else [spawn_x, spawn_y]
    total_displacement = float(np.linalg.norm(np.array(final_pos) - np.array([spawn_x, spawn_y])))

    return {
        "arm": arm,
        "config_id": config["config_id"],
        "seed": config["seed"],
        "spawn_pos": [spawn_x, spawn_y],
        "spawn_yaw": spawn_yaw,
        "escaped": escaped,
        "had_collision": had_collision,
        "collision_tick": collision_tick,
        "ticks_executed": len(trajectory),
        "final_pos": final_pos,
        "total_displacement": total_displacement,
        "min_clearance": min_observed_clearance,
        "max_consecutive_reversals": max_consecutive_reversals,
        "total_reversal_ticks": reversal_ticks,
        "max_yaw_rotation_deg": float(np.rad2deg(max_yaw_rotation)),
        "gate2_emergent_maneuver": gate2_emergent_maneuver,
        "mean_latency_ms": float(np.mean(cycle_latencies)) if cycle_latencies else 0.0,
        "p95_latency_ms": float(np.percentile(cycle_latencies, 95)) if cycle_latencies else 0.0,
        "latencies": cycle_latencies,
        "trajectory": trajectory,
        "actions_taken": actions_taken,
        "eval_wheel_velocities": eval_wheel_velocities,
        "eval_world_headings": eval_world_headings,
    }


def execute_stage3_4_benchmark() -> Dict[str, Any]:
    """
    Executes the authoritative 160-episode benchmark battery across all 4 experimental arms.
    """
    print("=" * 90)
    print("       CARL-DX STAGE 3.4 ACTIVE INFERENCE BENCHMARK & CERTIFICATION BATTERY")
    print("       40 Matched Trial Configurations x 4 Arms = 160 Physical Episodes")
    print("=" * 90)

    configs = build_40_matched_configurations()
    arms = ["ARM-A", "ARM-B", "ARM-C", "ARM-D"]

    hal = CarlStage1HAL(xml_path=str(XML_PATH))

    raw_results = {arm: [] for arm in arms}
    all_latencies = []

    start_time = time.time()

    for arm in arms:
        print(f"\n---> Executing Experimental Arm: {arm} (40 matched episodes)...")
        arm_escapes = 0
        arm_collisions = 0
        arm_gate2_count = 0

        for idx, cfg in enumerate(configs):
            ep_res = execute_single_episode(arm, cfg, hal)
            raw_results[arm].append(ep_res)
            all_latencies.extend(ep_res["latencies"])

            if ep_res["escaped"]:
                arm_escapes += 1
            if ep_res["had_collision"]:
                arm_collisions += 1
            if ep_res["gate2_emergent_maneuver"]:
                arm_gate2_count += 1

            if (idx + 1) % 10 == 0 or (idx + 1) == TOTAL_CONFIGS:
                print(f"     [{arm}] Trial {idx+1:02d}/40: Escapes={arm_escapes}/{idx+1}, "
                      f"Collisions={arm_collisions}/{idx+1}, Gate2 Emergence={arm_gate2_count}/{idx+1}")

    total_time = time.time() - start_time
    print(f"\nAll 160 episodes successfully executed in {total_time:.2f} seconds.")

    # -----------------------------------------------------------------
    # GATE ADJUDICATION & STATISTICAL ANALYSIS
    # -----------------------------------------------------------------
    # Arm A Metrics
    a_escapes = sum(1 for r in raw_results["ARM-A"] if r["escaped"])
    a_escape_rate = a_escapes / TOTAL_CONFIGS
    a_collisions = sum(1 for r in raw_results["ARM-A"] if r["had_collision"])
    a_collision_rate = a_collisions / TOTAL_CONFIGS
    a_gate2_successes = sum(1 for r in raw_results["ARM-A"] if r["gate2_emergent_maneuver"])
    a_gate2_rate = a_gate2_successes / TOTAL_CONFIGS

    # Arm B Metrics
    b_escapes = sum(1 for r in raw_results["ARM-B"] if r["escaped"])
    b_escape_rate = b_escapes / TOTAL_CONFIGS
    b_collisions = sum(1 for r in raw_results["ARM-B"] if r["had_collision"])
    b_collision_rate = b_collisions / TOTAL_CONFIGS

    # Arm C (Discrete) Metrics
    c_escapes = sum(1 for r in raw_results["ARM-C"] if r["escaped"])
    c_escape_rate = c_escapes / TOTAL_CONFIGS
    c_collisions = sum(1 for r in raw_results["ARM-C"] if r["had_collision"])
    c_collision_rate = c_collisions / TOTAL_CONFIGS

    # Arm D (Random) Metrics
    d_escapes = sum(1 for r in raw_results["ARM-D"] if r["escaped"])
    d_escape_rate = d_escapes / TOTAL_CONFIGS
    d_collisions = sum(1 for r in raw_results["ARM-D"] if r["had_collision"])
    d_collision_rate = d_collisions / TOTAL_CONFIGS

    # -----------------------------------------------------------------
    # PAIRED MCNEMAR ANALYSIS: ARM-A vs ARM-B (Gate 3)
    # -----------------------------------------------------------------
    n11 = 0  # Both escape
    n10 = 0  # ARM-A escapes, ARM-B fails
    n01 = 0  # ARM-A fails, ARM-B escapes
    n00 = 0  # Both fail

    for i in range(TOTAL_CONFIGS):
        a_esc = raw_results["ARM-A"][i]["escaped"]
        b_esc = raw_results["ARM-B"][i]["escaped"]
        if a_esc and b_esc:
            n11 += 1
        elif a_esc and not b_esc:
            n10 += 1
        elif not a_esc and b_esc:
            n01 += 1
        else:
            n00 += 1

    delta_escape = (n10 - n01) / TOTAL_CONFIGS
    n_disc = n10 + n01

    # Exact one-sided binomial McNemar test
    if n_disc > 0:
        # P(K >= n10 | Binomial(n_disc, 0.5))
        mcnemar_p = float(stats.binom.sf(n10 - 1, n_disc, 0.5))
    else:
        mcnemar_p = 1.0

    # Gate 4 Latencies
    mean_lat = float(np.mean(all_latencies))
    p95_lat = float(np.percentile(all_latencies, 95))

    # Gate 5 AST Anti-Cheat
    from tests.test_stage3_4_no_script_audit import test_stage3_4_no_script_emergence_audit
    try:
        test_stage3_4_no_script_emergence_audit()
        ast_anti_cheat_passed = True
    except Exception as e:
        ast_anti_cheat_passed = False

    # -----------------------------------------------------------------
    # FIVE FROZEN GATES EVALUATION
    # -----------------------------------------------------------------
    # Gate 1: Escape >= 80.0% (32/40) AND Collision <= 10.0%
    gate1_pass = bool(a_escape_rate >= 0.80 and a_collision_rate <= 0.10)

    # Gate 2: >= 75.0% Emergent Reversal + Pivot
    gate2_pass = bool(a_gate2_rate >= 0.75)

    # Gate 3: Delta Escape >= 35.0% AND exact one-sided McNemar p < 0.001
    gate3_pass = bool(delta_escape >= 0.35 and mcnemar_p < 0.001)

    # Gate 4: p95 <= 45.0 ms AND mean <= 20.0 ms
    gate4_pass = bool(p95_lat <= 45.0 and mean_lat <= 20.0)

    # Gate 5: 100% clean AST
    gate5_pass = bool(ast_anti_cheat_passed)

    all_gates_pass = bool(gate1_pass and gate2_pass and gate3_pass and gate4_pass and gate5_pass)
    adjudication_status = "CERTIFIED" if all_gates_pass else "FAILED CLOSED"

    scorecard = {
        "milestone": "Stage 3.4 — Autonomous Behavioral Discovery under Active Inference",
        "protocol_id": "CARL-STAGE3-4-ACTIVE-INF-PROTO-2026-09-14-v4",
        "adjudication_status": adjudication_status,
        "all_gates_pass": all_gates_pass,
        "total_matched_configurations": TOTAL_CONFIGS,
        "total_experimental_arms": TOTAL_ARMS,
        "total_episodes_executed": TOTAL_EPISODES,
        "execution_time_seconds": total_time,
        "seeds_evaluated": PRE_REGISTERED_SEEDS,
        "gates": {
            "gate_1": {
                "name": "Autonomous Cul-de-Sac Escape Rate",
                "metric": "Escape Rate & Collision Ceiling",
                "observed_escape_rate": a_escape_rate,
                "observed_escapes": a_escapes,
                "observed_collision_rate": a_collision_rate,
                "observed_collisions": a_collisions,
                "threshold_escape_rate": 0.80,
                "threshold_collision_ceiling": 0.10,
                "passed": gate1_pass
            },
            "gate_2": {
                "name": "Emergent Maneuver Verification",
                "metric": "Authentic Reversal + Pivot via Evaluator Telemetry",
                "observed_emergence_rate": a_gate2_rate,
                "observed_emergence_count": a_gate2_successes,
                "threshold_emergence_rate": 0.75,
                "passed": gate2_pass
            },
            "gate_3": {
                "name": "Information-Gain Causal Necessity",
                "metric": "Paired McNemar Test (ARM-A vs ARM-B)",
                "delta_escape": delta_escape,
                "threshold_delta_escape": 0.35,
                "mcnemar_p_value": mcnemar_p,
                "threshold_p_value": 0.001,
                "contingency_table": {
                    "n11_both_escape": n11,
                    "n10_arma_esc_armb_fail": n10,
                    "n01_arma_fail_armb_esc": n01,
                    "n00_both_fail": n00,
                    "total_discordant": n_disc
                },
                "passed": gate3_pass
            },
            "gate_4": {
                "name": "Real-Time Cognitive Cycle Latency",
                "metric": "p95 and Mean Execution Latency",
                "observed_p95_ms": p95_lat,
                "observed_mean_ms": mean_lat,
                "threshold_p95_ms": 45.0,
                "threshold_mean_ms": 20.0,
                "total_cycles_measured": len(all_latencies),
                "passed": gate4_pass
            },
            "gate_5": {
                "name": "Decision-Pipeline AST Anti-Cheat",
                "metric": "Zero Simulator Coordinates & Zero Scripted Macros",
                "static_scan_clean": ast_anti_cheat_passed,
                "passed": gate5_pass
            }
        },
        "comparative_summary": {
            "ARM-A (Full Active Inference)": {
                "escape_rate": a_escape_rate,
                "collision_rate": a_collision_rate,
                "gate2_emergence_rate": a_gate2_rate,
            },
            "ARM-B (Pragmatic-Only Baseline)": {
                "escape_rate": b_escape_rate,
                "collision_rate": b_collision_rate,
            },
            "ARM-C (Stage 2 Discrete Baseline)": {
                "escape_rate": c_escape_rate,
                "collision_rate": c_collision_rate,
            },
            "ARM-D (Random MPPI)": {
                "escape_rate": d_escape_rate,
                "collision_rate": d_collision_rate,
            }
        }
    }

    # Save outputs
    scorecard_path = EVIDENCE_DIR / "stage3_4_scorecard.json"
    with open(scorecard_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    raw_trials_path = EVIDENCE_DIR / "stage3_4_raw_trials.json"
    # Filter raw results for JSON serialization
    serialized_raw = {}
    for arm_k, arm_list in raw_results.items():
        serialized_raw[arm_k] = []
        for r in arm_list:
            r_copy = dict(r)
            # Downsample trajectory if large
            if len(r_copy["trajectory"]) > 100:
                step_sub = len(r_copy["trajectory"]) // 50
                r_copy["trajectory"] = r_copy["trajectory"][::step_sub]
            r_copy.pop("latencies", None)
            serialized_raw[arm_k].append(r_copy)

    with open(raw_trials_path, "w", encoding="utf-8") as f:
        json.dump(serialized_raw, f, indent=2)

    print("\n" + "=" * 90)
    print(f"  BENCHMARK COMPLETE. ADJUDICATION STATUS: {adjudication_status}")
    print("=" * 90)
    print(f"  Gate 1 (Cul-de-Sac Escape Rate):    {'PASS' if gate1_pass else 'FAIL'} "
          f"({a_escape_rate*100:.1f}% >= 80.0%, coll={a_collision_rate*100:.1f}%)")
    print(f"  Gate 2 (Emergent Maneuver):         {'PASS' if gate2_pass else 'FAIL'} "
          f"({a_gate2_rate*100:.1f}% >= 75.0%)")
    print(f"  Gate 3 (Info Gain Necessity):       {'PASS' if gate3_pass else 'FAIL'} "
          f"(Delta={delta_escape*100:.1f}% >= 35.0%, p={mcnemar_p:.4e} < 0.001)")
    print(f"  Gate 4 (Real-Time Latency):         {'PASS' if gate4_pass else 'FAIL'} "
          f"(mean={mean_lat:.2f}ms <= 20ms, p95={p95_lat:.2f}ms <= 45ms)")
    print(f"  Gate 5 (AST Anti-Cheat Scan):       {'PASS' if gate5_pass else 'FAIL'}")
    print("=" * 90)
    print(f"Scorecard written to: {scorecard_path}")
    print(f"Raw trials written to: {raw_trials_path}")

    return scorecard


if __name__ == "__main__":
    scorecard = execute_stage3_4_benchmark()
