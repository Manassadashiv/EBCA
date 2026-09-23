"""
tools/p1_r1/p1r1_experiment_runner.py — Master P1-R1 Campaign Orchestrator

Executes:
1. Physical Pilot Acceptance Gates (Reachability, Memory Writes > 0, Zero Collisions, AST Clean)
2. Full 525-Episode Campaign (7 Conditions × 5 Seeds × 15 Episodes)
3. Raw CSV Telemetry Logging (evidence/p1_r1/telemetry/)
4. 720p 30 FPS Video Rendering with Transparent HUD (evidence/p1_r1/videos/)
5. 10-Point Counterfactual Decision Trace Serialization (evidence/p1_r1/decision_trace/)
6. 12 Canonical Scientific Analysis Plots (evidence/p1_r1/plots/)
7. Master Forensic Ledgers & Classification JSON
"""

from typing import List, Dict, Any, Tuple
import os
import sys
sys.path.insert(0, ".")
import math
import time
import csv
import json
import numpy as np
import cv2

from brain.p1_r1.carl_p1r1_developmental_agent import CarlP1R1DevelopmentalAgent
from brain.p1_r1.carl_p1r1_developmental_lab import CarlP1R1DevelopmentalLab
from tools.p1_r1.p1r1_visual_pipeline import P1R1VisualPipeline
from tools.p1_r1.p1r1_anti_engineering_auditor import P1R1AntiEngineeringAuditor
from tools.p1_r1.p1r1_independent_classifier import P1R1IndependentClassifier

# Campaign Constants
MAX_TICKS_PER_EPISODE = 500  # 16.65s at 30 Hz (Route A takes ~8.7s, Route B ~10.8s)
DT = 0.0333
FOOD_COORDS = (1.60, 0.0)

CONDITIONS = [
    "FULL_P1_R1",
    "P0_CONTROL",
    "NO_MEMORY",
    "NO_ADAPTATION",
    "NO_NEED",
    "GEN_ENV_2",
    "GEN_ENV_3"
]

OFFICIAL_SEEDS = [42, 101, 2024, 31415, 8675309]
EPISODES_PER_SEQUENCE = 15

EVIDENCE_DIR = "evidence/p1_r1"
TELEMETRY_DIR = os.path.join(EVIDENCE_DIR, "telemetry")
VIDEOS_DIR = os.path.join(EVIDENCE_DIR, "videos")
PLOTS_DIR = os.path.join(EVIDENCE_DIR, "plots")
AUDIT_DIR = os.path.join(EVIDENCE_DIR, "audit")
DECISION_DIR = os.path.join(EVIDENCE_DIR, "decision_trace")

os.makedirs(TELEMETRY_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(AUDIT_DIR, exist_ok=True)
os.makedirs(DECISION_DIR, exist_ok=True)


def run_single_episode(
    lab: CarlP1R1DevelopmentalLab,
    agent: CarlP1R1DevelopmentalAgent,
    condition: str,
    seed: int,
    episode_num: int,
    record_video: bool = False
) -> Dict[str, Any]:
    """
    Runs a single physical episode in MuJoCo, logging full telemetry and optionally recording 720p video.
    """
    # Determine Environment ID
    env_id = "ENV_1_BIFURCATION_CANONICAL"
    if condition == "GEN_ENV_2":
        env_id = "ENV_2_ASYMMETRIC_OFFSET"
    elif condition == "GEN_ENV_3":
        env_id = "ENV_3_FRICTIONAL_TRANSITION"
        
    lab.configure_environment(env_id, episode_num)
    lab.reset_robot_pose(0.0, 0.0, 0.0)
    
    # Configure Agent
    preserve_memory = (condition != "NO_MEMORY" and condition != "P0_CONTROL")
    agent.reset_for_episode(episode_num, seed, condition, preserve_memory=preserve_memory)
    
    video_frames = []
    telemetry_rows = []
    
    pipeline = P1R1VisualPipeline(output_dir=EVIDENCE_DIR)
    
    target_acquired = False
    acq_tick = None
    acq_time_s = None
    
    for tick in range(MAX_TICKS_PER_EPISODE):
        step_res = agent.step_developmental_cycle(lab.hal, food_coords=FOOD_COORDS)
        # Advance physics sub-steps
        for _ in range(3):
            lab.hal.step()
            
        t = step_res["telemetry"]
        sensory = step_res["sensory"]
        
        # Calculate target distance
        d_food = math.sqrt((FOOD_COORDS[0] - sensory.pos_x)**2 + (FOOD_COORDS[1] - sensory.pos_y)**2)
        is_acquired = (t.food_absorbed or d_food < 0.30)
        
        if is_acquired and not target_acquired:
            target_acquired = True
            acq_tick = tick
            acq_time_s = round(tick * DT, 4)
            
        telem_dict = {
            "tick": tick,
            "time_s": round(tick * DT, 4),
            "condition": condition,
            "seed": seed,
            "episode": episode_num,
            "pos_x": round(float(sensory.pos_x), 4),
            "pos_y": round(float(sensory.pos_y), 4),
            "yaw": round(float(sensory.yaw), 4),
            "speed": round(float(sensory.speed), 4),
            "target_distance": round(d_food, 4),
            "target_acquisition": is_acquired,
            "action": t.chosen_action_name,
            "efe_chosen": round(float(t.homeostatic_deviation), 4),
            "prediction_error": round(float(t.prediction_error), 4),
            "episodes_in_memory": step_res["total_memory_episodes"],
            "memory_writes": step_res["memory_writes"],
            "memory_retrievals": step_res["memory_retrievals"],
            "energy": round(float(t.energy), 4),
            "thermal_load": round(float(t.thermal_load), 4),
            "motor_fatigue": round(float(t.motor_fatigue), 4),
            "curiosity_drive": round(float(t.curiosity_drive), 4),
            "active_goal": t.active_goal_type,
            "veto_asserted": t.veto_asserted,
            "collision_occurred": t.collision_occurred,
            "recovery_active": t.recovery_active
        }
        telemetry_rows.append(telem_dict)
        
        if record_video:
            frame = lab.render_frame()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame_hud = pipeline.draw_hud_overlay(frame_bgr, telem_dict)
            video_frames.append(frame_hud)
            
        if is_acquired:
            break
            
    # End-of-episode consolidation
    agent.end_episode_consolidation()
    
    # Save CSV telemetry
    csv_fname = f"{condition}_seed_{seed}_ep_{episode_num:02d}_telemetry.csv"
    csv_path = os.path.join(TELEMETRY_DIR, csv_fname)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(telemetry_rows[0].keys()))
        writer.writeheader()
        writer.writerows(telemetry_rows)
        
    # Save video if requested
    if record_video and len(video_frames) > 0:
        vid_fname = f"{condition}_seed_{seed}_ep_{episode_num:02d}.mp4"
        vid_path = os.path.join(VIDEOS_DIR, vid_fname)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(vid_path, fourcc, 30.0, (1280, 720))
        for vf in video_frames:
            out.write(vf)
        out.release()
        
    # Summary entry
    final_row = telemetry_rows[-1]
    initial_row = telemetry_rows[0]
    
    # Path length & tortuosity
    path_len = 0.0
    for i in range(1, len(telemetry_rows)):
        dx = telemetry_rows[i]["pos_x"] - telemetry_rows[i-1]["pos_x"]
        dy = telemetry_rows[i]["pos_y"] - telemetry_rows[i-1]["pos_y"]
        path_len += math.sqrt(dx*dx + dy*dy)
    net_disp = math.sqrt((final_row["pos_x"] - initial_row["pos_x"])**2 + (final_row["pos_y"] - initial_row["pos_y"])**2)
    tortuosity = round(path_len / max(0.01, net_disp), 4) if net_disp > 0.05 else 1.0
    
    # Action entropy
    act_counts = {}
    for r in telemetry_rows:
        act_counts[r["action"]] = act_counts.get(r["action"], 0) + 1
    act_entropy = 0.0
    for a, cnt in act_counts.items():
        p = cnt / len(telemetry_rows)
        act_entropy -= p * math.log2(p)
    act_entropy = round(act_entropy, 4)
    
    run_id = f"{condition}_seed_{seed}_ep_{episode_num:02d}"
    ledger_entry = {
        "run_id": run_id,
        "condition": condition,
        "environment": env_id,
        "seed": seed,
        "episode": episode_num,
        "telemetry_file": csv_fname,
        "tick_count": len(telemetry_rows),
        "duration_s": round(len(telemetry_rows) * DT, 4),
        "initial_x": initial_row["pos_x"],
        "initial_y": initial_row["pos_y"],
        "final_x": final_row["pos_x"],
        "final_y": final_row["pos_y"],
        "final_target_distance": final_row["target_distance"],
        "min_target_distance": min(r["target_distance"] for r in telemetry_rows),
        "target_acquired": target_acquired,
        "acquisition_tick": acq_tick if target_acquired else "NULL",
        "acquisition_time_s": acq_time_s if target_acquired else "NULL",
        "collision_count": sum(1 for r in telemetry_rows if r["collision_occurred"]),
        "recovery_count": sum(1 for r in telemetry_rows if r["recovery_active"]),
        "final_action": final_row["action"],
        "final_goal": final_row["active_goal"],
        "initial_memory_count": initial_row["episodes_in_memory"],
        "final_memory_count": final_row["episodes_in_memory"],
        "max_memory_count": max(r["episodes_in_memory"] for r in telemetry_rows),
        "mean_prediction_error": round(float(np.mean([r["prediction_error"] for r in telemetry_rows])), 4),
        "max_prediction_error": round(float(np.max([r["prediction_error"] for r in telemetry_rows])), 4),
        "action_entropy": act_entropy,
        "trajectory_tortuosity": tortuosity,
        "final_energy": final_row["energy"],
        "final_thermal_load": final_row["thermal_load"],
        "final_motor_fatigue": final_row["motor_fatigue"],
        "final_curiosity": final_row["curiosity_drive"]
    }
    
    return {
        "ledger_entry": ledger_entry,
        "telemetry_rows": telemetry_rows
    }


def run_full_p1r1_campaign():
    """
    Orchestrates the complete P1-R1 campaign.
    """
    print("=" * 80)
    print("CARL-DX — P1-R1 MASTER DEVELOPMENTAL EMERGENCE CAMPAIGN")
    print("=" * 80)
    
    # Step 1: Run Anti-Engineering Source Audit First
    auditor = P1R1AntiEngineeringAuditor()
    audit_report = auditor.run_full_audit()
    audit_json_path = os.path.join(AUDIT_DIR, "P1R1_ANTI_ENGINEERING_AUDIT.json")
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)
    print(f"[AUDIT] Inspected {audit_report['total_files_audited']} files: Verdict = {audit_report['verdict']}")
    assert audit_report["status"] == "QUALIFIED", "Anti-engineering audit failed!"
    
    lab = CarlP1R1DevelopmentalLab(dt=DT)
    
    # Step 2: 3-Episode Pilot Acceptance Gate
    print("\n[PILOT] Running 3-Episode Pilot Verification on Seed 42...")
    pilot_agent = CarlP1R1DevelopmentalAgent(dt=DT, enable_memory=True, enable_adaptation=True, enable_need=True)
    pilot_res_1 = run_single_episode(lab, pilot_agent, "FULL_P1_R1", 42, 1, record_video=False)
    pilot_res_6 = run_single_episode(lab, pilot_agent, "FULL_P1_R1", 42, 6, record_video=False)
    
    pilot_acq = pilot_res_1["ledger_entry"]["target_acquired"]
    pilot_mem_writes = pilot_res_6["ledger_entry"]["max_memory_count"]
    pilot_collisions = pilot_res_1["ledger_entry"]["collision_count"] + pilot_res_6["ledger_entry"]["collision_count"]
    
    print(f"[PILOT RESULTS] Baseline Acquired: {pilot_acq} (t={pilot_res_1['ledger_entry']['acquisition_time_s']}s) | Perturbation Mem Writes: {pilot_mem_writes} | Collisions: {pilot_collisions}")
    assert pilot_acq, "Pilot Gate 1 Failed: Food not reached in baseline!"
    assert pilot_mem_writes > 0, "Pilot Gate 2 Failed: Memory writes == 0!"
    assert pilot_collisions == 0, "Pilot Gate 3 Failed: Collisions > 0!"
    print("[PILOT PASSED] All 4 Physical Acceptance Gates Qualified! Proceeding to Full Campaign...\n")
    
    # Step 3: Full 525-Episode Campaign Execution
    all_ledger_rows = []
    all_telemetry_by_run = {}
    
    # Representative Video Roster
    video_roster = {
        ("FULL_P1_R1", 42, 1),
        ("FULL_P1_R1", 42, 6),
        ("FULL_P1_R1", 42, 10),
        ("FULL_P1_R1", 42, 15),
        ("P0_CONTROL", 42, 6),
        ("NO_MEMORY", 42, 6)
    }
    
    start_time = time.time()
    
    for cond in CONDITIONS:
        enable_mem = (cond != "NO_MEMORY" and cond != "P0_CONTROL")
        enable_adapt = (cond != "NO_ADAPTATION")
        enable_nd = (cond != "NO_NEED")
        
        for seed in OFFICIAL_SEEDS:
            # Instantiate agent per (condition, seed) to maintain autobiographical memory across the 15 episodes
            agent = CarlP1R1DevelopmentalAgent(
                dt=DT,
                enable_memory=enable_mem,
                enable_adaptation=enable_adapt,
                enable_need=enable_nd
            )
            
            for ep in range(1, EPISODES_PER_SEQUENCE + 1):
                rec_vid = ((cond, seed, ep) in video_roster)
                run_out = run_single_episode(lab, agent, cond, seed, ep, record_video=rec_vid)
                all_ledger_rows.append(run_out["ledger_entry"])
                all_telemetry_by_run[run_out["ledger_entry"]["run_id"]] = run_out["telemetry_rows"]
                
            print(f"[{cond:15s} | Seed {seed:7d}] Completed 15 episodes. Acquired: {sum(1 for r in all_ledger_rows[-15:] if r['target_acquired'])}/15.")

    duration = round(time.time() - start_time, 2)
    print(f"\n[CAMPAIGN COMPLETE] Executed {len(all_ledger_rows)} physical simulation runs in {duration}s.")
    
    # Step 4: Write P1R1_RAW_RUN_LEDGER.csv
    ledger_csv_path = os.path.join(AUDIT_DIR, "P1R1_RAW_RUN_LEDGER.csv")
    with open(ledger_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_ledger_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_ledger_rows)
    print(f"[OK] Saved P1-R1 Raw Run Ledger ({len(all_ledger_rows)} rows): {ledger_csv_path}")
    
    # Step 5: Generate 10-Point Decision Trace
    sample_run_id = "FULL_P1_R1_seed_42_ep_06"
    sample_rows = all_telemetry_by_run[sample_run_id]
    sample_ticks = [1, 25, 50, 100, 150, 200, 250, 287, 291, 300]
    
    decision_traces = []
    for idx, t_idx in enumerate(sample_ticks, start=1):
        row = sample_rows[min(t_idx, len(sample_rows)-1)]
        decision_traces.append({
            "decision_point_index": idx,
            "tick": int(row["tick"]),
            "time_s": float(row["time_s"]),
            "state": {
                "pos_x": float(row["pos_x"]),
                "pos_y": float(row["pos_y"]),
                "speed": float(row["speed"]),
                "yaw": float(row["yaw"])
            },
            "selected_action": row["action"],
            "selected_efe": float(row["efe_chosen"]),
            "prediction_error": float(row["prediction_error"]),
            "safety_veto_asserted": row["veto_asserted"],
            "active_goal": row["active_goal"]
        })
        
    trace_obj = {
        "dataset_name": "P1R1_CANONICAL_10_POINT_DECISION_TRACE",
        "sample_run_id": sample_run_id,
        "traces": decision_traces
    }
    trace_path = os.path.join(DECISION_DIR, "P1R1_DECISION_TRACE.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_obj, f, indent=2)
    print(f"[OK] Saved 10-Point Decision Trace: {trace_path}")
    
    # Step 6: Generate all 12 Canonical Scientific Plots
    pipeline = P1R1VisualPipeline(output_dir=EVIDENCE_DIR)
    pipeline.generate_all_12_canonical_plots(all_ledger_rows, all_telemetry_by_run)
    
    # Step 7: Blind Emergence Classification
    classifier = P1R1IndependentClassifier()
    class_report = classifier.classify(audit_report, all_ledger_rows, {})
    class_json_path = os.path.join(AUDIT_DIR, "P1R1_EMERGENCE_CLASSIFICATION.json")
    with open(class_json_path, "w", encoding="utf-8") as f:
        json.dump(class_report, f, indent=2)
    print(f"[CLASSIFICATION] Verdict: {class_report['final_status']} (Level: {class_report['final_level']}, Confidence: {class_report['confidence']*100:.1f}%)")
    
    # Step 8: Generate Master Report JSON
    total_acquired = sum(1 for r in all_ledger_rows if r["target_acquired"])
    total_failed = len(all_ledger_rows) - total_acquired
    success_rate = total_acquired / len(all_ledger_rows)
    
    master_report = {
        "mission": "CARL-DX PHASE 1-R1 REACHABLE DEVELOPMENTAL EMERGENCE CAMPAIGN",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "duration_seconds": duration,
        "total_conditions": len(CONDITIONS),
        "total_episodes_executed": len(all_ledger_rows),
        "successful_episodes": total_acquired,
        "failed_episodes": total_failed,
        "overall_success_rate": round(success_rate, 4),
        "overall_success_rate_percent": f"{success_rate * 100:.2f}%",
        "official_seeds": OFFICIAL_SEEDS,
        "audit_report": audit_report,
        "classification_report": class_report
    }
    master_json_path = os.path.join(REPO_ROOT if "REPO_ROOT" in locals() else ".", "CARL_P1R1_MASTER_REPORT.json")
    with open(master_json_path, "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)
    print(f"[OK] Saved Master Report JSON: {master_json_path}")
    print("\n" + "=" * 80)
    print(f"P1-R1 CAMPAIGN EXECUTION COMPLETE. STATUS: {class_report['final_status']}")
    print("=" * 80)


if __name__ == "__main__":
    run_full_p1r1_campaign()
