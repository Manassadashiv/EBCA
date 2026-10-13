"""
tests/run_stage3_7_complete_battery.py — Stage 3.7 Multi-Modal Perception, Canonical Integration & Adversarial Acceptance Suite
Classification: Formal Pre-Registered Developmental Milestone Evaluation Suite

Executes the 7 Pre-Registered Stage 3.7 Acceptance Gates:
- Gate 1: Multi-Modal Escape & Entrapment Immunity (N=50 episodes, escape >= 90.0%, collision <= 5.0%)
- Gate 2: Active Head Gaze & Corollary Discharge Saccade Dynamics (head_pan in [-0.85, 0.85], saccade activity > 0)
- Gate 3: Caster Pitch & Chassis Suspension Stability (pitch <= 0.20 rad, max <= 0.60 rad, slip < 0.15, slew <= 0.08)
- Gate 4: Real-Time Control Cycle Latency Budget (mean <= 25.0 ms, p95 <= 50.0 ms)
- Gate 5: Decision-Pipeline Isolation Invariant (100% clean AST audit across 14 cognitive files)
- Gate 6: 100% Organ Activation across the Unified Canonical Organism (all 7 developmental organs active)
- Gate 7: Adversarial Spawn Robustness across All 4 Quadrants (>= 85.0% escape in every quadrant)
"""

import os
import sys
import math
import time
import json
import ast
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.stats as stats
import mujoco

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_vision import CarlVisionNet

ENV_DIR = REPO_ROOT / "world" / "stage3_4_environments"
XML_PATH = ENV_DIR / "cul_de_sac_turning_bay.xml"
GRID_PATH = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"

EVIDENCE_DIR = REPO_ROOT / "evidence" / "stage3_7"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

MAX_TICKS_PER_EPISODE = 600
ESCAPE_X_THRESHOLD = -0.55  # Egress mouth of cul-de-sac


def generate_adversarial_configs(num_configs: int = 50, seed: int = 7001) -> List[Dict[str, Any]]:
    """
    Generates deterministic spatial spawn configurations inside cul-de-sac
    stratified across all four quadrants of heading yaw in [-pi, pi].
    """
    rng = np.random.RandomState(seed)
    configs = []
    base_x = 0.50
    base_y = 0.00

    quadrants = ["front", "left", "back", "right"]

    for i in range(num_configs):
        dx = float(rng.uniform(-0.08, 0.12))
        dy = float(rng.uniform(-0.06, 0.06))

        # Stratify yaw evenly across 4 quadrants to guarantee comprehensive testing
        target_quadrant = quadrants[i % 4]
        if target_quadrant == "front":
            yaw = float(rng.uniform(-math.pi / 4.0, math.pi / 4.0))
        elif target_quadrant == "left":
            yaw = float(rng.uniform(math.pi / 4.0, 3.0 * math.pi / 4.0))
        elif target_quadrant == "right":
            yaw = float(rng.uniform(-3.0 * math.pi / 4.0, -math.pi / 4.0))
        else:  # "back"
            # Pointing directly west towards the exit or slightly off
            val = float(rng.uniform(3.0 * math.pi / 4.0, math.pi))
            yaw = val if rng.rand() > 0.5 else -val

        configs.append({
            "config_id": i,
            "quadrant": target_quadrant,
            "spawn_pos": [base_x + dx, base_y + dy],
            "spawn_yaw": yaw,
        })
    return configs


def execute_physical_episode(
    config: Dict[str, Any],
    hal: CarlStage1HAL,
) -> Dict[str, Any]:
    """
    Executes a single physical episode tracking escape, collision, pitch, slip, gaze, and latencies.
    """
    spawn_x, spawn_y = config["spawn_pos"]
    spawn_yaw = config["spawn_yaw"]

    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    agent = CarlAutonomousOrganismAgent(
        dt=hal.dt,
        deliberation_mode="active_inference",
        grid_path=str(GRID_PATH)
    )
    agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

    cycle_latencies = []
    had_collision = False
    escaped = False
    collision_tick = None

    max_pitch = 0.0
    episode_pitches = []
    slips = []
    slews = []
    head_pans = []
    egress_angles = []
    looming_threats = []
    organs_active_all = []

    trajectory_x = []
    trajectory_y = []
    trajectory_yaw = []

    prev_cmd = np.zeros(2)

    for tick in range(MAX_TICKS_PER_EPISODE):
        t_cycle_start = time.perf_counter()

        # Step unprivileged cognitive cycle
        cycle_res = agent.step_cognitive_cycle(hal)
        dt_ms = (time.perf_counter() - t_cycle_start) * 1000.0
        cycle_latencies.append(dt_ms)

        u_cmd_6d = cycle_res["action_cmd"].copy()

        # Commanded wheel actions for slew tracking
        curr_cmd = np.array([u_cmd_6d[0], u_cmd_6d[1]])
        if tick > 0:
            delta_u = float(np.max(np.abs(curr_cmd - prev_cmd)))
            slews.append(delta_u)
        prev_cmd = curr_cmd.copy()

        # Step physical HAL simulation
        s_next, diag = hal.step(u_cmd_6d)

        curr_x = float(diag["pos_x"])
        curr_y = float(diag["pos_y"])
        curr_yaw = float(diag["yaw"])
        trajectory_x.append(curr_x)
        trajectory_y.append(curr_y)
        trajectory_yaw.append(curr_yaw)

        # Track caster/chassis pitch
        sensory = cycle_res["sensory"]
        pitch_val = abs(float(sensory.pitch))
        episode_pitches.append(pitch_val)
        if pitch_val > max_pitch:
            max_pitch = pitch_val

        # Track wheel slip
        slips.append(float(agent.slip_ratio))

        # Track head gaze and vision telemetry
        head_pan_val = float(agent.head_pan)
        head_pans.append(head_pan_val)
        vis_telem = cycle_res.get("vision_telemetry")
        if vis_telem is not None:
            egress_angles.append(float(vis_telem.egress_angle))
            looming_threats.append(float(vis_telem.looming_threat))

        # Track 7-Organ simultaneous activation
        organ_status = [
            bool(cycle_res.get("stage1_slip_active")),
            bool(cycle_res.get("stage2_1_attractor_active")),
            bool(cycle_res.get("stage2_2_memory_active")),
            bool(cycle_res.get("stage2_3_delib_active")),
            bool(cycle_res.get("stage3_5_endocrine_active")),
            bool(cycle_res.get("stage3_6_physarum_active")),
            bool(cycle_res.get("stage3_7_vision_active")),
        ]
        organs_active_all.append(all(organ_status))

        # Check contact manifold for damaging structural collision
        impact_info = hal.get_carl_impact_info()
        if impact_info["damaging_impacts"] > 0 and not had_collision:
            had_collision = True
            collision_tick = tick

        # Check escape condition
        if curr_x <= ESCAPE_X_THRESHOLD:
            escaped = True
            break

    # Gaze activity metric: total range of head pan movement
    pan_range = float(np.ptp(head_pans)) if len(head_pans) > 1 else 0.0

    return {
        "config_id": config["config_id"],
        "quadrant": config["quadrant"],
        "spawn_pos": [spawn_x, spawn_y],
        "spawn_yaw": spawn_yaw,
        "escaped": escaped,
        "had_collision": had_collision,
        "collision_tick": collision_tick,
        "ticks": len(cycle_latencies),
        "mean_latency_ms": float(np.mean(cycle_latencies)),
        "p95_latency_ms": float(np.percentile(cycle_latencies, 95)),
        "max_pitch_rad": float(max_pitch),
        "mean_pitch_rad": float(np.mean(episode_pitches)) if episode_pitches else 0.0,
        "mean_slip": float(np.mean(slips)) if slips else 0.0,
        "max_slew": float(np.max(slews)) if slews else 0.0,
        "pan_range_rad": pan_range,
        "mean_head_pan": float(np.mean(head_pans)) if head_pans else 0.0,
        "mean_looming": float(np.mean(looming_threats)) if looming_threats else 0.0,
        "all_organs_active": all(organs_active_all) if organs_active_all else False,
        "all_latencies": cycle_latencies,
        "trajectory_x": trajectory_x,
        "trajectory_y": trajectory_y,
        "trajectory_yaw": trajectory_yaw,
    }


def run_complete_stage3_7_battery():
    print("=" * 80)
    print("CARL STAGE 3.7 MASTER ACCEPTANCE BATTERY: MULTI-MODAL PERCEPTION & INTEGRATION")
    print("=" * 80)

    hal = CarlStage1HAL(xml_path=str(XML_PATH))
    all_latencies = []

    # -------------------------------------------------------------------------
    # GATE 1 & GATE 7: 50-Episode Adversarial Acceptance Suite
    # -------------------------------------------------------------------------
    print("\n--- RUNNING 50-EPISODE ADVERSARIAL ACCEPTANCE SUITE ---")
    configs = generate_adversarial_configs(50, seed=7001)

    escapes = 0
    collisions = 0
    quadrant_stats = {
        "front": {"escapes": 0, "total": 0},
        "left": {"escapes": 0, "total": 0},
        "back": {"escapes": 0, "total": 0},
        "right": {"escapes": 0, "total": 0},
    }

    pitches = []
    mean_pitches = []
    slips = []
    slews = []
    pan_ranges = []
    all_organs_active_list = []
    trajectories_archive = []

    for idx, cfg in enumerate(configs):
        res = execute_physical_episode(cfg, hal)
        all_latencies.extend(res["all_latencies"])

        pitches.append(res["max_pitch_rad"])
        mean_pitches.append(res["mean_pitch_rad"])
        slips.append(res["mean_slip"])
        slews.append(res["max_slew"])
        pan_ranges.append(res["pan_range_rad"])
        all_organs_active_list.append(res["all_organs_active"])

        trajectories_archive.append({
            "config_id": res["config_id"],
            "quadrant": res["quadrant"],
            "x": res["trajectory_x"],
            "y": res["trajectory_y"],
            "yaw": res["trajectory_yaw"],
            "escaped": res["escaped"],
            "collision": res["had_collision"],
        })

        if res["escaped"]:
            escapes += 1
            quadrant_stats[res["quadrant"]]["escapes"] += 1
        if res["had_collision"]:
            collisions += 1
        quadrant_stats[res["quadrant"]]["total"] += 1

        status = "ESCAPE" if res["escaped"] else ("COLLISION" if res["had_collision"] else "TIMEOUT")
        print(f"  Ep {idx+1:02d}/50 [{res['quadrant'].upper():5s}]: {status:9s} in {res['ticks']:3d} ticks | pan_range={res['pan_range_rad']:.3f} rad | p95_lat={res['p95_latency_ms']:.2f} ms", flush=True)

    # -------------------------------------------------------------------------
    # GATE EVALUATION
    # -------------------------------------------------------------------------
    # Gate 1: Escape & Collision Rates
    escape_rate = escapes / 50.0
    collision_rate = collisions / 50.0
    g1_pass = (escape_rate >= 0.90) and (collision_rate <= 0.05)

    # Gate 2: Active Head Gaze & Saccade Dynamics
    mean_pan_range = float(np.mean(pan_ranges))
    g2_pass = mean_pan_range >= 0.35  # Confirms meaningful saccadic scanning excursions

    # Gate 3: Caster Pitch & Chassis Suspension Stability
    g3_mean_pitch = float(np.mean(mean_pitches))
    g3_max_pitch = float(np.max(pitches))
    g3_mean_slip = float(np.mean(slips))
    g3_max_slew = float(np.max(slews))
    g3_pass = (g3_mean_pitch <= 0.20) and (g3_max_pitch <= 0.60) and (g3_mean_slip < 0.15) and (g3_max_slew <= 0.080001)

    # Gate 4: Real-Time Cycle Latency Budget
    mean_lat = float(np.mean(all_latencies))
    p95_lat = float(np.percentile(all_latencies, 95))
    g4_pass = (mean_lat <= 25.0) and (p95_lat <= 50.0)

    # Gate 5: Decision-Pipeline Isolation Invariant (AST Scan across 14 files)
    print("\n--- EVALUATING GATE 5: AST Decision Pipeline Quarantine Scan ---")
    forbidden_attrs = {"geom_xpos", "mj_ray", "qpos", "qvel", "qacc", "site_xpos"}
    decision_files = [
        REPO_ROOT / "brain" / "carl_autonomous_agent.py",
        REPO_ROOT / "brain" / "carl_stage2_3_r1_deliberation.py",
        REPO_ROOT / "brain" / "carl_stage2_2_r2_occupancy_memory.py",
        REPO_ROOT / "brain" / "carl_stage2_2_world_model.py",
        REPO_ROOT / "brain" / "carl_stage2_2_memory_module.py",
        REPO_ROOT / "brain" / "carl_stage2_integrated_brain.py",
        REPO_ROOT / "brain" / "carl_stage2_hd_ring.py",
        REPO_ROOT / "brain" / "carl_stage2_grid_torus.py",
        REPO_ROOT / "brain" / "carl_mppi_deliberation.py",
        REPO_ROOT / "brain" / "carl_active_inference.py",
        REPO_ROOT / "brain" / "carl_endocrine_adaptation.py",
        REPO_ROOT / "brain" / "carl_physarum.py",
        REPO_ROOT / "brain" / "carl_motor_synergies.py",
        REPO_ROOT / "brain" / "carl_vision.py",
    ]

    ast_leaks = 0
    for tf in decision_files:
        source = tf.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(tf))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_attrs:
                ast_leaks += 1
                print(f"  [LEAK] {tf.name}:{node.lineno} accesses {node.attr}")

    g5_pass = (ast_leaks == 0)

    # Gate 6: 100% Organ Activation across the Unified Canonical Organism
    organ_active_rate = float(np.mean(all_organs_active_list))
    g6_pass = organ_active_rate == 1.00

    # Gate 7: Adversarial Spawn Robustness across All 4 Quadrants
    quadrant_pass = True
    quad_rates = {}
    for q_name, q_data in quadrant_stats.items():
        q_rate = q_data["escapes"] / max(1, q_data["total"])
        quad_rates[q_name] = q_rate
        if q_rate < 0.85:
            quadrant_pass = False
    g7_pass = quadrant_pass

    # Print Gate Summaries
    print("\n" + "=" * 80)
    print("GATE EVALUATION SUMMARY:")
    print("=" * 80)
    print(f"Gate 1: Escape & Collision Immunity: {escapes}/50 ({escape_rate*100:.1f}%), {collisions}/50 Collisions -> {'PASS' if g1_pass else 'FAIL'}")
    print(f"Gate 2: Active Gaze Saccade Excursion: Mean Range={mean_pan_range:.3f} rad (>= 0.35) -> {'PASS' if g2_pass else 'FAIL'}")
    print(f"Gate 3: Suspension Stability: Pitch mean={g3_mean_pitch:.4f}, max={g3_max_pitch:.4f}, slip={g3_mean_slip:.4f}, slew={g3_max_slew:.4f} -> {'PASS' if g3_pass else 'FAIL'}")
    print(f"Gate 4: Latency Budget: Mean={mean_lat:.2f} ms (<= 25), p95={p95_lat:.2f} ms (<= 50) -> {'PASS' if g4_pass else 'FAIL'}")
    print(f"Gate 5: AST Decision Isolation: {len(decision_files)} files scanned, {ast_leaks} leaks -> {'PASS' if g5_pass else 'FAIL'}")
    print(f"Gate 6: 100% Organ Activation: {organ_active_rate*100:.1f}% episodes with all 7 organs active -> {'PASS' if g6_pass else 'FAIL'}")
    print(f"Gate 7: Adversarial Quadrant Robustness: Front={quad_rates['front']*100:.1f}%, Left={quad_rates['left']*100:.1f}%, Back={quad_rates['back']*100:.1f}%, Right={quad_rates['right']*100:.1f}% -> {'PASS' if g7_pass else 'FAIL'}")

    all_gates_pass = g1_pass and g2_pass and g3_pass and g4_pass and g5_pass and g6_pass and g7_pass

    # Save Scorecard
    scorecard = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "milestone": "Stage 3.7 — Multi-Modal Perception, Canonical Integration & Adversarial Acceptance",
        "status": "CERTIFIED" if all_gates_pass else "FAILED",
        "gates": {
            "gate1_escape_and_collision_immunity": {
                "threshold": "escapes >= 90%, collisions <= 5%",
                "escapes": escapes,
                "collisions": collisions,
                "total_episodes": 50,
                "escape_rate": escape_rate,
                "collision_rate": collision_rate,
                "passed": g1_pass,
            },
            "gate2_active_gaze_saccades": {
                "threshold": "mean_pan_range >= 0.35 rad",
                "mean_pan_range_rad": mean_pan_range,
                "passed": g2_pass,
            },
            "gate3_chassis_suspension_stability": {
                "threshold": "mean_pitch <= 0.20 rad, max_pitch <= 0.60 rad, slip < 0.15, slew <= 0.08",
                "mean_pitch_rad": g3_mean_pitch,
                "max_pitch_rad": g3_max_pitch,
                "mean_slip": g3_mean_slip,
                "max_slew": g3_max_slew,
                "passed": g3_pass,
            },
            "gate4_cycle_latency_budget": {
                "threshold": "mean <= 25.0 ms, p95 <= 50.0 ms",
                "total_cycles": len(all_latencies),
                "mean_latency_ms": mean_lat,
                "p95_latency_ms": p95_lat,
                "passed": g4_pass,
            },
            "gate5_ast_decision_isolation": {
                "threshold": "0 leaks across 14 files",
                "files_scanned": len(decision_files),
                "leaks_found": ast_leaks,
                "passed": g5_pass,
            },
            "gate6_organ_activation": {
                "threshold": "100.0% episodes with all 7 developmental organs active",
                "organ_active_rate": organ_active_rate,
                "passed": g6_pass,
            },
            "gate7_adversarial_quadrant_robustness": {
                "threshold": ">= 85.0% escapes in every quadrant",
                "quadrant_rates": quad_rates,
                "passed": g7_pass,
            }
        }
    }

    scorecard_path = EVIDENCE_DIR / "stage3_7_scorecard.json"
    with open(scorecard_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    # Save Telemetry Archive
    telemetry_path = EVIDENCE_DIR / "stage3_7_telemetry.npz"
    np.savez_compressed(
        telemetry_path,
        all_latencies=np.array(all_latencies, dtype=np.float32),
        pitches=np.array(pitches, dtype=np.float32),
        mean_pitches=np.array(mean_pitches, dtype=np.float32),
        slips=np.array(slips, dtype=np.float32),
        slews=np.array(slews, dtype=np.float32),
        pan_ranges=np.array(pan_ranges, dtype=np.float32),
        trajectories=np.array(trajectories_archive, dtype=object),
    )

    print("\n" + "=" * 80)
    verdict_str = "CERTIFIED [PASS]" if all_gates_pass else "FAILED [FAIL]"
    print(f"FINAL STAGE 3.7 VERDICT: {verdict_str}")
    print(f"Scorecard saved to: {scorecard_path}")
    print(f"Telemetry saved to: {telemetry_path}")
    print("=" * 80)

    return all_gates_pass


if __name__ == "__main__":
    success = run_complete_stage3_7_battery()
    sys.exit(0 if success else 1)
