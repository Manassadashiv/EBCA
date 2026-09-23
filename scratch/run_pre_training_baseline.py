"""
scratch/run_pre_training_baseline.py — Pre-Training Baseline Evaluation (P_pre)

Executes the frozen untrained C7 checkpoint across all 100 immutable baseline evaluation episodes.
Every episode is audited by the independent CarlExperimentAuditor from raw MuJoCo telemetry.
Saves:
1. Raw telemetry CSV for every episode in telemetry_raw/baseline_pre/
2. Summary metric vector P_pre in evaluation_sets/baseline_results_pre.json
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

def run_baseline_evaluation():
    print("================================================================================")
    print("  EXECUTING PRE-TRAINING BASELINE EVALUATION (100 EPISODES, C7 UNTRAINED)")
    print("================================================================================")
    
    auditor = CarlExperimentAuditor()
    runner = CarlSimulationRunner(open_space=True, headless=True)
    
    # Load C7 Checkpoint
    c7_path = os.path.join(BASE_DIR, "checkpoints", "initial_untrained_C7.npz")
    c7_data = np.load(c7_path)
    
    cortex = CarlLocalCortex(num_neurons=500, dt=0.033)
    cortex.W_in = c7_data["W_in"]
    cortex.W_rec = c7_data["W_rec"]
    cortex.reflex_layer.w = c7_data["reflex_w"]
    cortex.da = float(c7_data["da"][0])
    cortex.ser = float(c7_data["ser"][0])
    cortex.ne = float(c7_data["ne"][0])
    cortex.ach = float(c7_data["ach"][0])
    
    motor_filter = WaterflowVelocityFilter(num_actuators=2, max_velocity=12.0, max_acceleration=10.0, max_jerk=30.0, dt=0.033)
    
    telemetry_dir = os.path.join(BASE_DIR, "telemetry_raw", "baseline_pre")
    os.makedirs(telemetry_dir, exist_ok=True)
    
    episode_results = []
    
    for ep_idx in range(1, 101):
        ep_file = os.path.join(BASE_DIR, "evaluation_sets", "baseline", f"episode_{ep_idx:04d}.json")
        with open(ep_file, "r") as f:
            ep_cfg = json.load(f)
            
        goal_pos = np.array(ep_cfg["goal_pos"])
        max_ticks = ep_cfg.get("max_ticks", 150)
        
        # Set environment friction
        runner.hal.model.geom("floor").friction[0] = ep_cfg.get("friction", 1.0)
        runner.hal.reset_robot()
        motor_filter.reset([0.0, 0.0])
        
        start_x, start_y, _ = runner.hal.get_robot_pos()
        initial_dist = float(np.linalg.norm(goal_pos - np.array([start_x, start_y])))
        
        records = []
        reached_goal = False
        
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
            # Untrained cortex step
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
                    
            records.append({
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
                
        df_ep = pd.DataFrame(records)
        csv_path = os.path.join(telemetry_dir, f"episode_{ep_idx:04d}.csv")
        df_ep.to_csv(csv_path, index=False)
        
        audit_res = auditor.audit_telemetry_dataframe(df_ep, require_goal=True, goal_pos=goal_pos)
        
        details = audit_res.get("details", {})
        path_len = float(details.get("path_length_m", 0.0))
        final_dist = float(details.get("min_goal_dist", initial_dist))
        jerk = float(details.get("max_jerk_rad_s3", 0.0))
        collisions = int(details.get("wall_collisions", 0))
        
        ep_summary = {
            "episode_id": ep_cfg["episode_id"],
            "verdict": audit_res["verdict"],
            "reason": audit_res["reason"],
            "initial_dist_m": round(initial_dist, 3),
            "final_min_dist_m": round(final_dist, 3),
            "path_length_m": round(path_len, 3),
            "efficiency": round(initial_dist / max(0.01, path_len), 3) if path_len > 0.05 else 0.0,
            "max_jerk_rad_s3": round(jerk, 2),
            "wall_collisions": collisions,
            "ticks": len(records),
            "telemetry_csv": csv_path
        }
        episode_results.append(ep_summary)
        
        if ep_idx % 10 == 0 or ep_idx == 1:
            print(f"  Episode {ep_idx:03d}/100: Verdict={audit_res['verdict']:<18} | InitialDist={initial_dist:.2f}m | MinDist={final_dist:.2f}m | Path={path_len:.2f}m")
            
    # Compute Aggregate Baseline Vector P_pre
    verdicts = [r["verdict"] for r in episode_results]
    passes = sum(1 for v in verdicts if v == AuditVerdict.VERIFIED_PASS)
    collisions_total = sum(r["wall_collisions"] for r in episode_results)
    mean_final_dist = float(np.mean([r["final_min_dist_m"] for r in episode_results]))
    mean_path_len = float(np.mean([r["path_length_m"] for r in episode_results]))
    mean_jerk = float(np.mean([r["max_jerk_rad_s3"] for r in episode_results]))
    
    p_pre_vector = {
        "evaluation_name": "Pre-Training Baseline Evaluation (P_pre)",
        "checkpoint": "checkpoints/initial_untrained_C7.npz",
        "total_episodes": len(episode_results),
        "verified_pass_count": passes,
        "verified_pass_rate_pct": round(passes / len(episode_results) * 100.0, 2),
        "mean_final_distance_to_goal_m": round(mean_final_dist, 3),
        "mean_path_length_m": round(mean_path_len, 3),
        "total_wall_collisions": collisions_total,
        "collision_rate_pct": round(sum(1 for r in episode_results if r["wall_collisions"] > 0) / len(episode_results) * 100.0, 2),
        "mean_peak_actuator_jerk_rad_s3": round(mean_jerk, 2),
        "episodes": episode_results
    }
    
    results_path = os.path.join(BASE_DIR, "evaluation_sets", "baseline_results_pre.json")
    with open(results_path, "w") as f:
        json.dump(p_pre_vector, f, indent=2)
        
    print("\n================================================================================")
    print("  PRE-TRAINING BASELINE (P_pre) METRICS SUMMARY")
    print("================================================================================")
    print(f"  Verified Pass Rate:      {p_pre_vector['verified_pass_rate_pct']}% ({passes}/100)")
    print(f"  Mean Final Goal Dist:    {mean_final_dist:.3f} m")
    print(f"  Mean Path Length:        {mean_path_len:.3f} m")
    print(f"  Wall Collision Rate:     {p_pre_vector['collision_rate_pct']}%")
    print(f"  Mean Peak Jerk:          {mean_jerk:.2f} rad/s³")
    print(f"  Saved Results JSON:      {results_path}")
    print("================================================================================")
    return p_pre_vector

if __name__ == "__main__":
    run_baseline_evaluation()
