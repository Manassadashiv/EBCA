"""
tools/p1_r2/p1r2_experiment_runner.py — Master Orchestrator for CARL-DX P1-R2 Pilot Campaign

Executes the 45-episode pilot across:
- Conditions: FULL_P1_R2, P0_CONTROL, NO_MEMORY
- Seeds: 42, 101, 2024
- Episodes: 1 to 5 per sequence
  - Ep 1-2: Both routes open
  - Ep 3: Route 1 blocked (barrier at (0.55, +0.45)), Route 2 open
  - Ep 4: Both routes open
  - Ep 5: Route 1 blocked again (recurrence test)

Logs complete per-tick telemetry CSVs, run JSONs, renders the 4 canonical HD 720p MP4 videos,
executes the AST anti-engineering audit, and classifies empirical emergence.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import csv
import json
import time
import math
import numpy as np
from typing import Dict, Any, List

from brain.p1_r2.carl_p1r2_developmental_agent import CarlP1R2DevelopmentalAgent
from brain.p1_r2.carl_p1r2_developmental_lab import CarlP1R2DevelopmentalLab
from tools.p1_r2.p1r2_visual_pipeline import P1R2VisualPipeline
from tools.p1_r2.p1r2_anti_engineering_auditor import run_p1r2_source_audit
from tools.p1_r2.p1r2_independent_classifier import classify_p1r2_emergence


CONDITIONS = ["FULL_P1_R2", "P0_CONTROL", "NO_MEMORY"]
SEEDS = [42, 101, 2024]
EPISODES_PER_RUN = 5
MAX_TICKS = 500
DT = 0.0333


def run_single_episode(
    lab: CarlP1R2DevelopmentalLab,
    agent: CarlP1R2DevelopmentalAgent,
    condition: str,
    seed: int,
    episode_num: int,
    video_recorder: P1R2VisualPipeline = None,
    output_dir: str = "d:/ebca/evidence/p1_r2"
) -> Dict[str, Any]:
    """
    Executes one physical simulation episode in the bifurcation environment.
    """
    np.random.seed(seed + episode_num * 17)
    
    # Configure physical environment (divider + optional perturbation barrier)
    lab.configure_environment(episode_num=episode_num)
    
    # Start at origin with tiny jitter
    x_init = 0.0 + np.random.uniform(-0.01, 0.01)
    y_init = 0.0 + np.random.uniform(-0.01, 0.01)
    yaw_init = 0.0 + np.random.uniform(-0.02, 0.02)
    lab.reset_robot_pose(x_init, y_init, yaw_init)
    
    # Reset agent controller state (preserving memory across episodes if enabled)
    agent.reset_for_episode(
        episode_num=episode_num,
        seed=seed,
        condition=condition,
        preserve_memory=(condition == "FULL_P1_R2")
    )
    
    # Telemetry logging setup
    telemetry_dir = os.path.join(output_dir, "telemetry")
    os.makedirs(telemetry_dir, exist_ok=True)
    telemetry_file = os.path.join(telemetry_dir, f"telemetry_{condition}_s{seed}_ep{episode_num}.csv")
    
    csv_fields = [
        "tick", "time_s", "pos_x", "pos_y", "yaw", "speed", "yaw_rate",
        "selected_action", "selected_sequence", "best_efe", "dist_food",
        "pred_error", "min_obstacle_dist", "memory_writes", "memory_retrievals",
        "episodes_in_memory", "route_channel", "collision_occurred", "food_absorbed"
    ]
    
    telemetry_rows = []
    
    acquired = False
    acquisition_tick = None
    acquisition_time_s = None
    total_collisions = 0
    route_chosen = "UNDECIDED"
    switch_latency_ticks = None
    
    for tick in range(MAX_TICKS):
        sim_time = tick * DT
        
        # In P0_CONTROL, agent uses single-step horizon (horizon_steps=1)
        # In FULL_P1_R2 and NO_MEMORY, agent uses multi-step horizon (horizon_steps=12)
        res = agent.step(lab.hal, target_coords=lab.food_coords)
        sensory = res["sensory"]
        
        # Route channel identification
        if sensory.pos_x > 0.35 and route_chosen == "UNDECIDED":
            if sensory.pos_y > 0.15:
                route_chosen = "NORTH_CORRIDOR_ROUTE1"
            elif sensory.pos_y < -0.15:
                route_chosen = "SOUTH_CORRIDOR_ROUTE2"
                
        # Track switch latency (ticks to commit to South route when North is blocked)
        if episode_num in (3, 5) and switch_latency_ticks is None:
            if sensory.pos_y < -0.20 and sensory.pos_x > 0.20:
                switch_latency_ticks = tick
                
        if res["collision_occurred"]:
            total_collisions += 1
            
        if res["food_absorbed"] and not acquired:
            acquired = True
            acquisition_tick = tick
            acquisition_time_s = sim_time
            
        # Log telemetry row
        row = {
            "tick": tick,
            "time_s": round(sim_time, 3),
            "pos_x": round(sensory.pos_x, 4),
            "pos_y": round(sensory.pos_y, 4),
            "yaw": round(sensory.yaw, 4),
            "speed": round(sensory.speed, 4),
            "yaw_rate": round((sensory.wheel_w_R - sensory.wheel_w_L) * 0.048 / 0.23, 4),
            "selected_action": res["best_action"],
            "selected_sequence": res["best_sequence"],
            "best_efe": round(res["best_efe"], 2),
            "dist_food": round(res["dist_food"], 4),
            "pred_error": round(res["prediction_error"], 4),
            "min_obstacle_dist": round(sensory.min_obstacle_dist, 4),
            "memory_writes": res["memory_writes"],
            "memory_retrievals": res["memory_retrievals"],
            "episodes_in_memory": res["episodes_in_memory"],
            "route_channel": route_chosen,
            "collision_occurred": int(res["collision_occurred"]),
            "food_absorbed": int(res["food_absorbed"])
        }
        telemetry_rows.append(row)
        
        # Record video frame if active
        if video_recorder is not None:
            frame = lab.render_frame()
            video_recorder.add_frame(
                rgb_frame=frame,
                tick=tick,
                sim_time=sim_time,
                condition=condition,
                seed=seed,
                episode=episode_num,
                action=res["best_action"],
                sequence=res["best_sequence"],
                efe=res["best_efe"],
                dist_food=res["dist_food"],
                pred_error=res["prediction_error"],
                memory_episodes=res["episodes_in_memory"],
                memory_writes=res["memory_writes"],
                memory_retrievals=res["memory_retrievals"],
                acquired=acquired
            )
            
        if acquired:
            # Hold for a few frames after acquisition
            if video_recorder is not None:
                for _ in range(15):
                    frame = lab.render_frame()
                    video_recorder.add_frame(
                        rgb_frame=frame,
                        tick=tick,
                        sim_time=sim_time,
                        condition=condition,
                        seed=seed,
                        episode=episode_num,
                        action="BRAKE_REST",
                        sequence="ACQUIRED",
                        efe=0.0,
                        dist_food=res["dist_food"],
                        pred_error=0.0,
                        memory_episodes=res["episodes_in_memory"],
                        memory_writes=res["memory_writes"],
                        memory_retrievals=res["memory_retrievals"],
                        acquired=True
                    )
            break
            
    # Write telemetry CSV
    with open(telemetry_file, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(telemetry_rows)
        
    # Consolidate offline replay memory between episodes
    agent.end_episode_consolidation()
    
    switch_latency_s = switch_latency_ticks * DT if switch_latency_ticks is not None else None
    
    return {
        "condition": condition,
        "seed": seed,
        "episode": episode_num,
        "acquired": acquired,
        "acquisition_tick": acquisition_tick,
        "acquisition_time_s": acquisition_time_s,
        "total_ticks": len(telemetry_rows),
        "total_collisions": total_collisions,
        "route_chosen": route_chosen,
        "switch_latency_ticks": switch_latency_ticks,
        "switch_latency_s": switch_latency_s,
        "memory_writes": res["memory_writes"],
        "memory_retrievals": res["memory_retrievals"],
        "episodes_in_memory": res["episodes_in_memory"],
        "final_dist_food": round(telemetry_rows[-1]["dist_food"], 4),
        "final_pos": [round(telemetry_rows[-1]["pos_x"], 3), round(telemetry_rows[-1]["pos_y"], 3)]
    }


def execute_p1r2_pilot_campaign(base_dir: str = "d:/ebca") -> Dict[str, Any]:
    """
    Orchestrates the complete 45-episode P1-R2 pilot campaign.
    """
    output_dir = os.path.join(base_dir, "evidence", "p1_r2")
    runs_dir = os.path.join(output_dir, "runs")
    videos_dir = os.path.join(output_dir, "videos")
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(runs_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    lab = CarlP1R2DevelopmentalLab()
    
    print("=" * 80)
    print("CARL-DX PHASE 1-R2 PILOT CAMPAIGN: GOAL-PRESERVING DETOUR EMERGENCE")
    print("Conditions: FULL_P1_R2, P0_CONTROL, NO_MEMORY")
    print(f"Seeds: {SEEDS} | Episodes per condition: {EPISODES_PER_RUN} (Total: {len(CONDITIONS) * len(SEEDS) * EPISODES_PER_RUN} runs)")
    print("=" * 80)
    
    all_results = []
    
    # Video configurations
    video_targets = {
        ("FULL_P1_R2", 42, 1): os.path.join(videos_dir, "p1r2_full_before_perturbation_ep1.mp4"),
        ("FULL_P1_R2", 42, 3): os.path.join(videos_dir, "p1r2_full_during_discovery_ep3.mp4"),
        ("FULL_P1_R2", 42, 5): os.path.join(videos_dir, "p1r2_full_after_adaptation_ep5.mp4"),
        ("NO_MEMORY", 42, 3): os.path.join(videos_dir, "p1r2_nomem_comparison_ep3.mp4")
    }
    
    for cond in CONDITIONS:
        enable_mem = (cond == "FULL_P1_R2")
        h_steps = 1 if cond == "P0_CONTROL" else 18
        
        for seed in SEEDS:
            agent = CarlP1R2DevelopmentalAgent(
                dt=DT,
                enable_memory=enable_mem,
                enable_adaptation=True,
                enable_need=True,
                horizon_steps=h_steps
            )
            
            for ep in range(1, EPISODES_PER_RUN + 1):
                # Check if video recording is requested for this run
                vrec = None
                vkey = (cond, seed, ep)
                if vkey in video_targets:
                    vrec = P1R2VisualPipeline(output_filepath=video_targets[vkey])
                    
                t_start = time.time()
                res = run_single_episode(
                    lab=lab,
                    agent=agent,
                    condition=cond,
                    seed=seed,
                    episode_num=ep,
                    video_recorder=vrec,
                    output_dir=output_dir
                )
                duration = time.time() - t_start
                
                if vrec is not None:
                    vrec.close()
                    print(f"[VIDEO] Generated canonical HD video: {os.path.basename(video_targets[vkey])}")
                    
                all_results.append(res)
                
                # Save run JSON
                run_json_path = os.path.join(runs_dir, f"run_{cond}_s{seed}_ep{ep}.json")
                with open(run_json_path, "w", encoding="utf-8") as fp:
                    json.dump(res, fp, indent=2)
                    
                status_str = "ACQUIRED" if res["acquired"] else "TIMEOUT"
                acq_t = f"{res['acquisition_time_s']:.2f}s" if res["acquisition_time_s"] is not None else "--"
                print(f"[{cond:11s} | S{seed:4d} | Ep{ep}] -> {status_str:7s} (t={acq_t}, route={res['route_chosen']}, mem_ep={res['episodes_in_memory']}) [{duration:.2f}s]")
                
    # Aggregate Metrics per Condition
    summary_by_cond = {}
    for cond in CONDITIONS:
        cond_runs = [r for r in all_results if r["condition"] == cond]
        total_episodes = len(cond_runs)
        acquisitions = [r for r in cond_runs if r["acquired"]]
        acq_times = [r["acquisition_time_s"] for r in acquisitions if r["acquisition_time_s"] is not None]
        ep3_runs = [r for r in cond_runs if r["episode"] == 3]
        ep5_runs = [r for r in cond_runs if r["episode"] == 5]
        
        ep3_acqs = sum(1 for r in ep3_runs if r["acquired"])
        ep5_acqs = sum(1 for r in ep5_runs if r["acquired"])
        
        ep5_latencies = [r["switch_latency_s"] for r in ep5_runs if r["switch_latency_s"] is not None]
        
        # Check seeds where all 5 episodes acquired
        seeds_successful = 0
        for s in SEEDS:
            s_runs = [r for r in cond_runs if r["seed"] == s]
            if all(r["acquired"] for r in s_runs):
                seeds_successful += 1
                
        summary_by_cond[cond] = {
            "total_episodes": total_episodes,
            "acquisitions": len(acquisitions),
            "acquisition_rate": len(acquisitions) / total_episodes if total_episodes > 0 else 0.0,
            "mean_time_to_target": float(np.mean(acq_times)) if len(acq_times) > 0 else 99.0,
            "std_time_to_target": float(np.std(acq_times)) if len(acq_times) > 0 else 0.0,
            "ep3_acquisition_rate": ep3_acqs / len(ep3_runs) if len(ep3_runs) > 0 else 0.0,
            "ep5_acquisition_rate": ep5_acqs / len(ep5_runs) if len(ep5_runs) > 0 else 0.0,
            "mean_ep5_switch_latency_s": float(np.mean(ep5_latencies)) if len(ep5_latencies) > 0 else 99.0,
            "total_collisions": sum(r["total_collisions"] for r in cond_runs),
            "total_memory_writes": sum(r["memory_writes"] for r in cond_runs),
            "total_memory_retrievals": sum(r["memory_retrievals"] for r in cond_runs),
            "max_episodes_in_memory": max(r["episodes_in_memory"] for r in cond_runs),
            "seeds_successful": seeds_successful
        }
        
    # Run AST Anti-Engineering Static Audit
    audit_report = run_p1r2_source_audit(base_dir)
    ast_passed = (audit_report["verdict"] == "ZERO BEHAVIOR-SPECIFIC SOLUTION RULES")
    
    # Classify Emergence
    classification = classify_p1r2_emergence(summary_by_cond, ast_audit_passed=ast_passed)
    
    # Write Master Pilot Report JSON
    master_report = {
        "experiment_name": "CARL-DX P1-R2 PILOT EXPERIMENTAL CAMPAIGN",
        "total_runs": len(all_results),
        "conditions": CONDITIONS,
        "seeds": SEEDS,
        "episodes_per_seed": EPISODES_PER_RUN,
        "condition_summaries": summary_by_cond,
        "ast_audit": audit_report,
        "emergence_classification": classification,
        "raw_results": all_results
    }
    
    master_report_path = os.path.join(base_dir, "CARL_P1R2_PILOT_REPORT.json")
    with open(master_report_path, "w", encoding="utf-8") as fp:
        json.dump(master_report, fp, indent=2)
        
    print("\n" + "=" * 80)
    print("PILOT CAMPAIGN COMPLETE — RAW RESULTS SUMMARY:")
    for cond, s in summary_by_cond.items():
        print(f"  {cond:12s}: Acq={s['acquisitions']}/{s['total_episodes']} ({s['acquisition_rate']*100:.1f}%), Mean Time={s['mean_time_to_target']:.2f}s, Ep3={s['ep3_acquisition_rate']*100:.0f}%, Ep5={s['ep5_acquisition_rate']*100:.0f}%, Collisions={s['total_collisions']}")
    print(f"  AST AUDIT: {audit_report['verdict']}")
    print(f"  CLASSIFICATION: {classification['classification_tier']} ({classification['criteria_passed_count']}/8 criteria passed)")
    print(f"  RATIONALE: {classification['rationale']}")
    print("=" * 80)
    
    return master_report


if __name__ == "__main__":
    execute_p1r2_pilot_campaign()
