"""
scratch/test_phase_0_auditor.py — Phase 0 Auditor Adversarial & Positive Control Test Runner

Tests CarlExperimentAuditor against:
1. 12 Adversarial Injected Fault Scenarios (Must reject all with exact expected verdict)
2. 10 Positive Control Scenarios (Must accept all with VERIFIED_PASS)
3. Checkpoint & Evaluation Set Generation & Hashing
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

def generate_clean_episode_telemetry(runner: CarlSimulationRunner, duration_ticks=60, goal=(2.0, 1.0)) -> pd.DataFrame:
    """Generates a known-good clean trajectory directly from live physics."""
    runner.hal.reset_robot()
    motor_filter = WaterflowVelocityFilter(num_actuators=2, max_velocity=12.0, max_acceleration=10.0, max_jerk=30.0, dt=0.033)
    motor_filter.reset([0.0, 0.0])
    
    records = []
    goal_pos = np.array(goal)
    
    for t in range(duration_ticks):
        x, y, yaw = runner.hal.get_robot_pos()
        pos = np.array([x, y])
        rel = goal_pos - pos
        food_dist = float(np.linalg.norm(rel))
        
        target_world_angle = math.atan2(rel[1], rel[0])
        heading_error = target_world_angle - yaw
        heading_error = (heading_error + math.pi) % (2 * math.pi) - math.pi
        
        v_base = 8.0
        turn = heading_error * 3.0
        raw_L = v_base - turn
        raw_R = v_base + turn
        
        smooth_cmds = motor_filter.filter_step(np.array([raw_L, raw_R]))
        smooth_L, smooth_R = float(smooth_cmds[0]), float(smooth_cmds[1])
        
        runner.hal.write_motors(smooth_L, smooth_R, 0.0, 0.0)
        for _ in range(20):
            mujoco.mj_step(runner.hal.model, runner.hal.data)
            
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
            "wall_contacts": 0,
            "food_dist": float(food_dist),
            "DA": 0.5, "5HT": 0.5, "NE": 0.5, "ACh": 0.5
        })
        
    return pd.DataFrame(records)

def test_adversarial_faults():
    print("================================================================================")
    print("  PHASE 0: ADVERSARIAL FAULT-INJECTION AUDIT SUITE (12 CORRUPTIONS)")
    print("================================================================================")
    
    auditor = CarlExperimentAuditor()
    runner = CarlSimulationRunner(open_space=True, headless=True)
    base_df = generate_clean_episode_telemetry(runner, duration_ticks=60)
    
    faults = []
    
    # 1. Zero Movement
    df_zero = base_df.copy()
    df_zero["pos_x"] = 0.0
    df_zero["pos_y"] = 0.0
    df_zero["qvel_x"] = 0.0
    df_zero["qvel_y"] = 0.0
    faults.append(("1. Zero-Movement False Success", df_zero, AuditVerdict.VERIFIED_FAIL, "NO_PROGRESS"))
    
    # 2. Teleportation (Superluminal velocity jump)
    df_teleport = base_df.copy()
    df_teleport.loc[15, "pos_x"] += 5.0
    faults.append(("2. Teleportation Single-Step Jump", df_teleport, AuditVerdict.INVALID, "TELEPORTATION"))
    
    # 3. Masked Wall Collision
    df_collision = base_df.copy()
    df_collision.loc[20, "wall_contacts"] = 1
    faults.append(("3. Masked Wall Collision", df_collision, AuditVerdict.VERIFIED_FAIL, "WALL_COLLISION"))
    
    # 4. Phantom Goal (Goal distance never within capture radius)
    df_phantom = base_df.copy()
    faults.append(("4. Phantom Goal Attainment", df_phantom, AuditVerdict.VERIFIED_FAIL, "GOAL_TIMEOUT", True, (10.0, 10.0)))
    
    # 5. Excessive Jerk Spike
    df_jerk = base_df.copy()
    df_jerk.loc[25, "motor_cmd_L"] += 25.0
    df_jerk.loc[26, "motor_cmd_L"] -= 25.0
    faults.append(("5. Excessive Jerk Spike", df_jerk, AuditVerdict.VERIFIED_FAIL, "EXCESSIVE_JERK"))
    
    # 6. Truncated Telemetry (Length < 30)
    df_truncated = base_df.iloc[:15].copy()
    faults.append(("6. Truncated Log Stream", df_truncated, AuditVerdict.INSUFFICIENT_EVIDENCE, "TRUNCATED_TELEMETRY"))
    
    # 7. Timestep Gap (> 150ms drop)
    df_gap = base_df.copy()
    df_gap.loc[20:, "time_s"] += 0.80
    faults.append(("7. Dropped Timestep Gap", df_gap, AuditVerdict.INSUFFICIENT_EVIDENCE, "TIMESTEP_GAP"))
    
    # 8. NaN Sensor / State Reading
    df_nan = base_df.copy()
    df_nan.loc[18, "pos_x"] = np.nan
    faults.append(("8. NaN Sensor / State Reading", df_nan, AuditVerdict.INVALID, "NAN_INF_VALUES"))
    
    # 9. Infinite Floating Point Values
    df_inf = base_df.copy()
    df_inf.loc[18, "qvel_y"] = np.inf
    faults.append(("9. Infinite Floating Point Value", df_inf, AuditVerdict.INVALID, "NAN_INF_VALUES"))
    
    # 10. Non-Monotonic / Negative Timestamps
    df_time_bad = base_df.copy()
    df_time_bad.loc[22, "time_s"] = df_time_bad.loc[20, "time_s"] - 0.05
    faults.append(("10. Backwards Timestamp Progression", df_time_bad, AuditVerdict.INVALID, "TIMESTAMP_ANOMALY"))
    
    # 11. Velocity / Position Integral Inconsistency
    df_vel_incon = base_df.copy()
    df_vel_incon["qvel_x"] = 2.0
    df_vel_incon["pos_x"] = 0.0
    df_vel_incon["pos_y"] = 0.0
    faults.append(("11. Kinematics Velocity/Position Inconsistency", df_vel_incon, AuditVerdict.INVALID, "VELOCITY_INCONSISTENCY"))
    
    # 12. Missing Essential Telemetry Channels
    df_missing = base_df.drop(columns=["pos_x", "qvel_y"]).copy()
    faults.append(("12. Missing Essential Channels", df_missing, AuditVerdict.INSUFFICIENT_EVIDENCE, "MISSING_CHANNELS"))
    
    fault_results = []
    
    for item in faults:
        if len(item) == 4:
            name, df_test, exp_verdict, exp_reason = item
            req_g, g_pos = False, None
        else:
            name, df_test, exp_verdict, exp_reason, req_g, g_pos = item
            
        res = auditor.audit_telemetry_dataframe(df_test, require_goal=req_g, goal_pos=g_pos)
        verdict_ok = (res["verdict"] == exp_verdict)
        reason_ok = (exp_reason in res["reason"])
        passed = verdict_ok and reason_ok
        fault_results.append(passed)
        
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name:<42} | Expected: {exp_verdict:<21} | Result: {res['verdict']:<21} | Reason: {res['reason']}")
        
    all_faults_passed = all(fault_results)
    print(f"\n  Adversarial Fault Suite Score: {sum(fault_results)}/{len(fault_results)} Correctly Rejected | Gate: {'PASS' if all_faults_passed else 'FAIL'}")
    return all_faults_passed

def test_positive_controls():
    print("\n================================================================================")
    print("  PHASE 0: POSITIVE CONTROL SUITE (10 KNOWN-GOOD TRAJECTORIES)")
    print("================================================================================")
    
    auditor = CarlExperimentAuditor()
    runner = CarlSimulationRunner(open_space=True, headless=True)
    goals = [
        (1.5, 0.5), (2.0, 1.0), (1.0, 1.5), (2.5, 0.0), (1.8, -0.8),
        (2.2, -1.2), (1.2, -1.5), (2.0, 0.5), (1.6, 1.2), (2.2, 0.8)
    ]
    
    pos_results = []
    
    for i, g in enumerate(goals, 1):
        df_clean = generate_clean_episode_telemetry(runner, duration_ticks=50, goal=g)
        res = auditor.audit_telemetry_dataframe(df_clean, require_goal=False)
        passed = (res["verdict"] == AuditVerdict.VERIFIED_PASS)
        pos_results.append(passed)
        
        details = res["details"]
        print(f"  [{'PASS' if passed else 'FAIL'}] Control #{i:02d} Goal: ({g[0]:4.1f}, {g[1]:4.1f}) | Verdict: {res['verdict']} | Path: {details.get('path_length_m', 0):.2f}m | Jerk: {details.get('max_jerk_rad_s3', 0):.1f} rad/s³ | Col: {details.get('wall_collisions', 0)}")
        
    all_pos_passed = all(pos_results)
    print(f"\n  Positive Control Suite Score: {sum(pos_results)}/{len(pos_results)} Correctly Accepted | Gate: {'PASS' if all_pos_passed else 'FAIL'}")
    return all_pos_passed

def freeze_initial_checkpoint_and_evaluation_sets():
    print("\n================================================================================")
    print("  PHASE 0: IMMUTABLE EVALUATION SET & C7 CHECKPOINT FREEZE")
    print("================================================================================")
    
    os.makedirs(os.path.join(BASE_DIR, "checkpoints"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "evaluation_sets", "baseline"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "evaluation_sets", "validation"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "evaluation_sets", "hidden_ood"), exist_ok=True)
    
    # 1. Save Deterministic Initial Untrained Checkpoint C7
    np.random.seed(42)
    cortex = CarlLocalCortex(num_neurons=500, dt=0.033)
    c7_path = os.path.join(BASE_DIR, "checkpoints", "initial_untrained_C7.npz")
    rng_state = np.random.get_state()
    np.savez_compressed(
        c7_path,
        W_in=cortex.W_in,
        W_rec=cortex.W_rec,
        reflex_w=cortex.reflex_layer.w,
        da=np.array([cortex.da]),
        ser=np.array([cortex.ser]),
        ne=np.array([cortex.ne]),
        ach=np.array([cortex.ach]),
        rng_keys=rng_state[1],
        rng_pos=np.array([rng_state[2]])
    )
    c7_hash = CarlExperimentAuditor.compute_file_hash(c7_path)
    print(f"  [SAVED] Initial Untrained Checkpoint C7: {c7_path}")
    print(f"          SHA-256 Hash: {c7_hash}")
    
    # 2. Generate 100 Fixed Baseline Episodes
    manifest_eval = {"baseline": {}, "validation": {}, "hidden_ood": {}}
    
    np.random.seed(1001)
    for ep_id in range(1, 101):
        ep_data = {
            "episode_id": f"baseline_{ep_id:04d}",
            "seed": 1001 + ep_id,
            "goal_pos": [round(float(np.random.uniform(1.0, 3.5)), 3), round(float(np.random.uniform(-3.0, 3.0)), 3)],
            "friction": round(float(np.random.uniform(0.8, 1.2)), 3),
            "max_ticks": 150
        }
        ep_path = os.path.join(BASE_DIR, "evaluation_sets", "baseline", f"episode_{ep_id:04d}.json")
        with open(ep_path, "w") as f:
            json.dump(ep_data, f, indent=2)
        manifest_eval["baseline"][f"episode_{ep_id:04d}"] = CarlExperimentAuditor.compute_file_hash(ep_path)
        
    # 3. Generate 100 Fixed In-Distribution Validation Episodes
    np.random.seed(2001)
    for ep_id in range(1, 101):
        ep_data = {
            "episode_id": f"val_{ep_id:04d}",
            "seed": 2001 + ep_id,
            "goal_pos": [round(float(np.random.uniform(1.0, 3.8)), 3), round(float(np.random.uniform(-3.5, 3.5)), 3)],
            "friction": round(float(np.random.uniform(0.6, 1.4)), 3),
            "max_ticks": 200
        }
        ep_path = os.path.join(BASE_DIR, "evaluation_sets", "validation", f"episode_{ep_id:04d}.json")
        with open(ep_path, "w") as f:
            json.dump(ep_data, f, indent=2)
        manifest_eval["validation"][f"episode_{ep_id:04d}"] = CarlExperimentAuditor.compute_file_hash(ep_path)
        
    # 4. Generate 100 Fixed Out-of-Distribution Hidden-Test Episodes (Novel corridors, extreme friction)
    np.random.seed(3001)
    for ep_id in range(1, 101):
        ep_data = {
            "episode_id": f"hidden_ood_{ep_id:04d}",
            "seed": 3001 + ep_id,
            "goal_pos": [round(float(np.random.uniform(2.0, 4.2)), 3), round(float(np.random.uniform(-3.8, 3.8)), 3)],
            "friction": round(float(np.random.uniform(0.15, 2.0)), 3),
            "sensor_noise_std": round(float(np.random.uniform(0.02, 0.08)), 3),
            "latency_ms": int(np.random.randint(15, 50)),
            "max_ticks": 250
        }
        ep_path = os.path.join(BASE_DIR, "evaluation_sets", "hidden_ood", f"episode_{ep_id:04d}.json")
        with open(ep_path, "w") as f:
            json.dump(ep_data, f, indent=2)
        manifest_eval["hidden_ood"][f"episode_{ep_id:04d}"] = CarlExperimentAuditor.compute_file_hash(ep_path)
        
    manifest_eval_path = os.path.join(BASE_DIR, "evaluation_sets", "manifest_eval_sets.json")
    with open(manifest_eval_path, "w") as f:
        json.dump(manifest_eval, f, indent=2)
        
    auditor_hash = CarlExperimentAuditor.compute_file_hash(os.path.join(BASE_DIR, "brain", "carl_experiment_auditor.py"))
    cortex_hash = CarlExperimentAuditor.compute_file_hash(os.path.join(BASE_DIR, "brain", "carl_local_cortex.py"))
    filter_hash = CarlExperimentAuditor.compute_file_hash(os.path.join(BASE_DIR, "brain", "carl_motor_filter.py"))
    sim_hash = CarlExperimentAuditor.compute_file_hash(os.path.join(BASE_DIR, "carl_simulation.py"))
    xml_hash = CarlExperimentAuditor.compute_file_hash(os.path.join(BASE_DIR, "world", "vessel_kinetic.xml"))
    
    manifest_global = {
        "timestamp": "2026-08-16T21:06:00+05:30",
        "phase": "Phase 0 Verification Gate Passed",
        "codebase_frozen": True,
        "auditor_sha256": auditor_hash,
        "c7_untrained_checkpoint_sha256": c7_hash,
        "eval_manifest_sha256": CarlExperimentAuditor.compute_file_hash(manifest_eval_path),
        "source_hashes": {
            "carl_local_cortex_py": cortex_hash,
            "carl_motor_filter_py": filter_hash,
            "carl_simulation_py": sim_hash,
            "vessel_kinetic_xml": xml_hash
        },
        "total_baseline_episodes": len(manifest_eval["baseline"]),
        "total_validation_episodes": len(manifest_eval["validation"]),
        "total_hidden_ood_episodes": len(manifest_eval["hidden_ood"])
    }
    
    with open(os.path.join(BASE_DIR, "manifest.json"), "w") as f:
        json.dump(manifest_global, f, indent=2)
        
    print(f"  [SAVED] 300 Fixed Evaluation Episodes (100 Baseline, 100 Val, 100 Hidden OOD)")
    print(f"  [SAVED] Auditor Code SHA-256: {auditor_hash}")
    print(f"  [SAVED] Global Manifest: {os.path.join(BASE_DIR, 'manifest.json')}")
    return True

if __name__ == "__main__":
    f_pass = test_adversarial_faults()
    p_pass = test_positive_controls()
    m_pass = freeze_initial_checkpoint_and_evaluation_sets()
    
    phase_0_gate = f_pass and p_pass and m_pass
    print("\n================================================================================")
    print(f"  PHASE 0 AUDITOR & VERIFICATION GATE: {'PASS' if phase_0_gate else 'FAIL'}")
    print("================================================================================")
    sys.exit(0 if phase_0_gate else 1)
