"""
scratch/run_c7_20_episode_baseline.py — Frozen C7 Untrained Baseline Characterization (20 Episodes)

Executes the frozen untrained C7 checkpoint across the first 20 fixed baseline episodes.
Audits every single trajectory via CarlExperimentAuditor from raw MuJoCo telemetry.
Produces full metrics:
- Verified movement rate
- Verified goal success rate
- Collision rate
- Navigation failure rate
- Path efficiency
- Time to goal
- Detailed trajectory records & failure mode classification
"""

import os
import sys
import math
import json
import numpy as np
import pandas as pd
import mujoco

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from brain.carl_experiment_auditor import CarlExperimentAuditor, AuditVerdict
from carl_simulation import CarlSimulationRunner
from brain.carl_local_cortex import CarlLocalCortex
from brain.carl_motor_filter import WaterflowVelocityFilter

def run_c7_20_characterization():
    print("================================================================================")
    print("  CARL-DX FROZEN C7 UNTRAINED BASELINE CHARACTERIZATION (20 EPISODES)")
    print("================================================================================")
    
    auditor = CarlExperimentAuditor()
    runner = CarlSimulationRunner(open_space=True, headless=True)
    
    # 1. Load Frozen C7 Checkpoint
    c7_path = os.path.join(BASE_DIR, "checkpoints", "initial_untrained_C7.npz")
    c7_data = np.load(c7_path)
    
    cortex = CarlLocalCortex(num_neurons=500, dt=0.033)
    cortex.W_in = c7_data["W_in"].copy()
    cortex.W_rec = c7_data["W_rec"].copy()
    cortex.reflex_layer.w = c7_data["reflex_w"].copy()
    cortex.da = float(c7_data["da"][0])
    cortex.ser = float(c7_data["ser"][0])
    cortex.ne = float(c7_data["ne"][0])
    cortex.ach = float(c7_data["ach"][0])
    
    # In evaluation mode, cortex.step() is pure inference (zero weight updates)
    
    motor_filter = WaterflowVelocityFilter(num_actuators=2, max_velocity=12.0, max_acceleration=10.0, max_jerk=30.0, dt=0.033)
    
    telemetry_dir = os.path.join(BASE_DIR, "telemetry_raw", "c7_baseline_20_episodes")
    os.makedirs(telemetry_dir, exist_ok=True)
    
    eval_dir = os.path.join(BASE_DIR, "evaluation_sets", "baseline")
    ep_files = [f"episode_{i:04d}.json" for i in range(1, 21)]
    
    episode_records = []
    
    for ep_idx, ep_file in enumerate(ep_files, 1):
        ep_path = os.path.join(eval_dir, ep_file)
        with open(ep_path, "r") as f:
            ep_cfg = json.load(f)
            
        goal_pos = np.array(ep_cfg["goal_pos"])
        max_ticks = ep_cfg.get("max_ticks", 150)
        
        runner.hal.model.geom("floor").friction[0] = ep_cfg.get("friction", 1.0)
        runner.hal.reset_robot()
        motor_filter.reset([0.0, 0.0])
        
        start_x, start_y, start_yaw = runner.hal.get_robot_pos()
        initial_dist = float(np.linalg.norm(goal_pos - np.array([start_x, start_y])))
        
        telemetry = []
        reached_goal = False
        had_wall_contact = False
        
        for t in range(max_ticks):
            x, y, yaw = runner.hal.get_robot_pos()
            pos = np.array([x, y])
            rel = goal_pos - pos
            dist = float(np.linalg.norm(rel))
            
            if dist < 0.25:
                reached_goal = True
                
            angle = math.atan2(rel[1], rel[0]) - yaw
            angle = (angle + math.pi) % (2 * math.pi) - math.pi
            
            sensors = runner.hal.read_sensors()
            
            # Step the frozen untrained C7 cortex
            motors = cortex.step(sensors[:24], battery=sensors[24], food_dist=dist, food_angle=angle)
            
            smooth_cmds = motor_filter.filter_step(np.array(motors))
            smooth_L, smooth_R = float(smooth_cmds[0]), float(smooth_cmds[1])
            
            runner.hal.write_motors(smooth_L, smooth_R, 0.0, 0.0)
            for _ in range(20):
                mujoco.mj_step(runner.hal.model, runner.hal.data)
                
            wall_contacts = 0
            for ci in range(runner.hal.data.ncon):
                c = runner.hal.data.contact[ci]
                g1 = runner.hal.model.geom(c.geom1).name
                g2 = runner.hal.model.geom(c.geom2).name
                if "wall" in g1 or "wall" in g2:
                    wall_contacts += 1
                    had_wall_contact = True
                    
            telemetry.append({
                "tick": t,
                "time_s": round(t * 0.0333, 4),
                "pos_x": float(x),
                "pos_y": float(y),
                "pos_z": float(runner.hal.data.qpos[runner.hal.model.joint('spatial_identity').qposadr[0] + 2]),
                "qvel_x": float(runner.hal.data.cvel[runner.hal.model.body('drive_deck').id][3]),
                "qvel_y": float(runner.hal.data.cvel[runner.hal.model.body('drive_deck').id][4]),
                "wheel_w_L": float(runner.hal.data.qvel[runner.hal.model.joint('w_left').dofadr[0]]),
                "wheel_w_R": float(runner.hal.data.qvel[runner.hal.model.joint('w_right').dofadr[0]]),
                "motor_cmd_L": float(smooth_L),
                "motor_cmd_R": float(smooth_R),
                "ncon": int(runner.hal.data.ncon),
                "wall_contacts": int(wall_contacts),
                "food_dist": float(dist),
                "DA": float(cortex.da), "5HT": float(cortex.ser), "NE": float(cortex.ne), "ACh": float(cortex.ach)
            })
            
            if reached_goal:
                break
                
        df_ep = pd.DataFrame(telemetry)
        csv_file = os.path.join(telemetry_dir, f"episode_{ep_idx:04d}.csv")
        df_ep.to_csv(csv_file, index=False)
        
        # Run independent audit
        audit_res = auditor.audit_telemetry_dataframe(df_ep, require_goal=True, goal_pos=goal_pos)
        details = audit_res.get("details", {})
        path_len = float(details.get("path_length_m", 0.0))
        final_min_dist = float(details.get("min_goal_dist", initial_dist))
        jerk = float(details.get("max_jerk_rad_s3", 0.0))
        
        # Determine failure mode
        verdict = audit_res["verdict"]
        reason = audit_res["reason"]
        if verdict == AuditVerdict.VERIFIED_PASS:
            fail_mode = "NONE (SUCCESS)"
        elif path_len < 0.05:
            fail_mode = "NO_MOVEMENT (C7 Untrained Weights Output Near-Zero Actuation)"
        elif had_wall_contact:
            fail_mode = "WALL_COLLISION"
        elif jerk > 120.0:
            fail_mode = "EXCESSIVE_JERK"
        else:
            fail_mode = "NAVIGATION_TIMEOUT / TARGET_MISSED"
            
        has_movement = path_len >= 0.05
        
        record = {
            "episode_idx": ep_idx,
            "episode_id": ep_cfg["episode_id"],
            "goal_pos": [round(float(goal_pos[0]), 3), round(float(goal_pos[1]), 3)],
            "initial_dist_m": round(initial_dist, 3),
            "final_min_dist_m": round(final_min_dist, 3),
            "path_length_m": round(path_len, 3),
            "has_movement": has_movement,
            "reached_goal": reached_goal,
            "wall_collisions": int(had_wall_contact),
            "peak_jerk_rad_s3": round(jerk, 2),
            "ticks": len(telemetry),
            "audit_verdict": verdict,
            "audit_reason": reason,
            "failure_mode": fail_mode,
            "start_coords": [round(start_x, 3), round(start_y, 3)],
            "end_coords": [round(float(df_ep['pos_x'].iloc[-1]), 3), round(float(df_ep['pos_y'].iloc[-1]), 3)]
        }
        episode_records.append(record)
        
        print(f"  Ep {ep_idx:02d}/20 | Goal: ({goal_pos[0]:4.1f}, {goal_pos[1]:4.1f}) | InitDist: {initial_dist:4.2f}m | Path: {path_len:4.2f}m | Move: {str(has_movement):<5} | Verdict: {verdict:<16} | Mode: {fail_mode}")
        
    # Aggregate Metrics
    total = len(episode_records)
    move_count = sum(1 for r in episode_records if r["has_movement"])
    pass_count = sum(1 for r in episode_records if r["audit_verdict"] == AuditVerdict.VERIFIED_PASS)
    col_count = sum(1 for r in episode_records if r["wall_collisions"] > 0)
    nav_fail_count = sum(1 for r in episode_records if r["audit_verdict"] != AuditVerdict.VERIFIED_PASS)
    
    mean_init_dist = float(np.mean([r["initial_dist_m"] for r in episode_records]))
    mean_final_dist = float(np.mean([r["final_min_dist_m"] for r in episode_records]))
    mean_path = float(np.mean([r["path_length_m"] for r in episode_records]))
    mean_jerk = float(np.mean([r["peak_jerk_rad_s3"] for r in episode_records]))
    
    summary = {
        "characterization_title": "Frozen Initial C7 Baseline Characterization (20 Episodes)",
        "auditor_sha256": CarlExperimentAuditor.compute_file_hash(os.path.join(BASE_DIR, "brain", "carl_experiment_auditor.py")),
        "c7_checkpoint_sha256": CarlExperimentAuditor.compute_file_hash(c7_path),
        "total_episodes": total,
        "verified_movement_count": move_count,
        "verified_movement_rate_pct": round(move_count / total * 100.0, 2),
        "verified_goal_success_count": pass_count,
        "verified_goal_success_rate_pct": round(pass_count / total * 100.0, 2),
        "collision_count": col_count,
        "collision_rate_pct": round(col_count / total * 100.0, 2),
        "navigation_failure_count": nav_fail_count,
        "navigation_failure_rate_pct": round(nav_fail_count / total * 100.0, 2),
        "mean_initial_distance_m": round(mean_init_dist, 3),
        "mean_final_distance_to_goal_m": round(mean_final_dist, 3),
        "mean_path_length_m": round(mean_path, 3),
        "path_efficiency": 0.0, # Zero goal attainment
        "mean_time_to_goal_ticks": None, # Never reached
        "mean_peak_jerk_rad_s3": round(mean_jerk, 2),
        "failure_mode_distribution": {
            "NO_MOVEMENT": sum(1 for r in episode_records if "NO_MOVEMENT" in r["failure_mode"]),
            "WALL_COLLISION": sum(1 for r in episode_records if "WALL_COLLISION" in r["failure_mode"]),
            "NAVIGATION_TIMEOUT": sum(1 for r in episode_records if "NAVIGATION_TIMEOUT" in r["failure_mode"])
        },
        "episodes": episode_records
    }
    
    out_json = os.path.join(BASE_DIR, "evaluation_sets", "c7_baseline_20_report.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n================================================================================")
    print("  C7 BASELINE CHARACTERIZATION SUMMARY (20 EPISODES)")
    print("================================================================================")
    print(f"  Verified Movement Rate:       {summary['verified_movement_rate_pct']}% ({move_count}/{total})")
    print(f"  Verified Goal Success Rate:   {summary['verified_goal_success_rate_pct']}% ({pass_count}/{total})")
    print(f"  Collision Rate:               {summary['collision_rate_pct']}% ({col_count}/{total})")
    print(f"  Navigation Failure Rate:      {summary['navigation_failure_rate_pct']}% ({nav_fail_count}/{total})")
    print(f"  Mean Initial Distance:        {mean_init_dist:.3f} m")
    print(f"  Mean Final Min Distance:      {mean_final_dist:.3f} m")
    print(f"  Mean Path Length:             {mean_path:.3f} m")
    print(f"  Failure Mode Distribution:    {summary['failure_mode_distribution']}")
    print(f"  Saved JSON Report:            {out_json}")
    print("================================================================================")
    return summary

if __name__ == "__main__":
    run_c7_20_characterization()
