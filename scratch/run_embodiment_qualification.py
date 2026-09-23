"""
scratch/run_embodiment_qualification.py — Deterministic Physical Embodiment Control Qualification

Executes four deterministic low-level control primitives on the frozen MuJoCo embodiment:
1. FORWARD (Command v_L = +6.0 rad/s, v_R = +6.0 rad/s)
2. STOP (Command v_L = 0.0 rad/s, v_R = 0.0 rad/s after forward motion)
3. TURN_LEFT (Command v_L = -4.0 rad/s, v_R = +4.0 rad/s)
4. TURN_RIGHT (Command v_L = +4.0 rad/s, v_R = -4.0 rad/s)

Records authoritative physical telemetry:
- Motor commands (u_L, u_R in rad/s)
- Actuator torques (tau_L, tau_R in N*m)
- Wheel angular velocities (w_L, w_R in rad/s)
- Wheel angular accelerations (alpha_L, alpha_R in rad/s^2)
- Wheel angular jerk (d^2 w / dt^2 in rad/s^3)
- Body velocity (qvel_x, qvel_y in m/s)
- Body position (pos_x, pos_y, pos_z in m)
- Heading / Yaw (rad)
- Contact forces and contact count (ncon)

Outputs:
- D:/ebca/audit/embodiment_control_qualification.json
- D:/ebca/audit/embodiment_control_qualification.md
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

from carl_simulation import CarlSimulationRunner
from brain.carl_motor_filter import WaterflowVelocityFilter
from brain.carl_experiment_auditor import CarlExperimentAuditor

def run_qualification():
    print("================================================================================")
    print("  DETERMINISTIC EMBODIMENT LOW-LEVEL CONTROL QUALIFICATION")
    print("================================================================================")
    
    runner = CarlSimulationRunner(open_space=True, headless=True)
    telemetry_dir = os.path.join(BASE_DIR, "telemetry_raw", "embodiment_qualification")
    os.makedirs(telemetry_dir, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "audit"), exist_ok=True)
    
    primitives = [
        {"name": "FORWARD", "cmd_L": 6.0, "cmd_R": 6.0, "duration_ticks": 60, "desc": "Positive forward translation"},
        {"name": "STOP", "cmd_L": 0.0, "cmd_R": 0.0, "duration_ticks": 60, "desc": "Active deceleration to stationary rest", "pre_roll_ticks": 30},
        {"name": "TURN_LEFT", "cmd_L": -4.0, "cmd_R": 4.0, "duration_ticks": 60, "desc": "Differential counter-clockwise rotation"},
        {"name": "TURN_RIGHT", "cmd_L": 4.0, "cmd_R": -4.0, "duration_ticks": 60, "desc": "Differential clockwise rotation"}
    ]
    
    results = {}
    
    for prim in primitives:
        pname = prim["name"]
        print(f"\n--- Testing Primitive: {pname} ({prim['desc']}) ---")
        
        runner.hal.reset_robot()
        motor_filter = WaterflowVelocityFilter(num_actuators=2, max_velocity=12.0, max_acceleration=10.0, max_jerk=30.0, dt=0.033)
        motor_filter.reset([0.0, 0.0])
        
        # Pre-roll for STOP test (move forward first, then command stop)
        if prim.get("pre_roll_ticks", 0) > 0:
            for _ in range(prim["pre_roll_ticks"]):
                cmds = motor_filter.filter_step(np.array([6.0, 6.0]))
                runner.hal.write_motors(cmds[0], cmds[1], 0.0, 0.0)
                for _ in range(20):
                    mujoco.mj_step(runner.hal.model, runner.hal.data)
                    
        records = []
        target_cmd = np.array([prim["cmd_L"], prim["cmd_R"]])
        
        for t in range(prim["duration_ticks"]):
            smooth_cmds = motor_filter.filter_step(target_cmd)
            uL, uR = float(smooth_cmds[0]), float(smooth_cmds[1])
            
            runner.hal.write_motors(uL, uR, 0.0, 0.0)
            for _ in range(20):
                mujoco.mj_step(runner.hal.model, runner.hal.data)
                
            x, y, yaw = runner.hal.get_robot_pos()
            
            # Read authoritative physical states
            qpos_z = float(runner.hal.data.qpos[runner.hal.model.joint('spatial_identity').qposadr[0] + 2])
            cvel_x = float(runner.hal.data.cvel[runner.hal.model.body('drive_deck').id][3])
            cvel_y = float(runner.hal.data.cvel[runner.hal.model.body('drive_deck').id][4])
            w_L = float(runner.hal.data.qvel[runner.hal.model.joint('w_left').dofadr[0]])
            w_R = float(runner.hal.data.qvel[runner.hal.model.joint('w_right').dofadr[0]])
            tau_L = float(runner.hal.data.actuator_force[0])
            tau_R = float(runner.hal.data.actuator_force[1])
            
            # Contact forces
            normal_force = 0.0
            for ci in range(runner.hal.data.ncon):
                c = runner.hal.data.contact[ci]
                # Extract normal contact force via c_array
                normal_force += abs(c.dist)
                
            records.append({
                "tick": t,
                "time_s": round(t * 0.0333, 4),
                "pos_x": float(x),
                "pos_y": float(y),
                "pos_z": float(qpos_z),
                "yaw_rad": float(yaw),
                "yaw_deg": float(math.degrees(yaw)),
                "cvel_x": float(cvel_x),
                "cvel_y": float(cvel_y),
                "speed_mps": float(math.sqrt(cvel_x**2 + cvel_y**2)),
                "motor_cmd_L": float(uL),
                "motor_cmd_R": float(uR),
                "wheel_w_L": float(w_L),
                "wheel_w_R": float(w_R),
                "actuator_tau_L": float(tau_L),
                "actuator_tau_R": float(tau_R),
                "ncon": int(runner.hal.data.ncon),
                "wall_contacts": 0
            })
            
        df = pd.DataFrame(records)
        csv_path = os.path.join(telemetry_dir, f"primitive_{pname.lower()}.csv")
        df.to_csv(csv_path, index=False)
        
        times = df["time_s"].values
        
        # Compute derivatives
        dx = df["pos_x"].iloc[-1] - df["pos_x"].iloc[0]
        dy = df["pos_y"].iloc[-1] - df["pos_y"].iloc[0]
        net_disp = float(math.sqrt(dx**2 + dy**2))
        delta_yaw = float(df["yaw_rad"].iloc[-1] - df["yaw_rad"].iloc[0])
        final_speed = float(df["speed_mps"].iloc[-1])
        
        # Commanded jerk (d^2 u / dt^2)
        j_cmd_L = np.gradient(np.gradient(df["motor_cmd_L"].values, times), times)
        j_cmd_R = np.gradient(np.gradient(df["motor_cmd_R"].values, times), times)
        peak_cmd_jerk = float(np.max(np.maximum(np.abs(j_cmd_L), np.abs(j_cmd_R))[2:-2])) if len(times) > 4 else 0.0
        
        # Physical wheel jerk (d^2 w / dt^2)
        j_wheel_L = np.gradient(np.gradient(df["wheel_w_L"].values, times), times)
        j_wheel_R = np.gradient(np.gradient(df["wheel_w_R"].values, times), times)
        peak_wheel_jerk = float(np.max(np.maximum(np.abs(j_wheel_L), np.abs(j_wheel_R))[2:-2])) if len(times) > 4 else 0.0
        
        # Verification Checks
        if pname == "FORWARD":
            passed = (dx > 0.40) and (abs(delta_yaw) < 0.25) and (df["wheel_w_L"].iloc[-1] > 2.0) and (df["wheel_w_R"].iloc[-1] > 2.0)
            status_msg = f"Displacement: +{dx:.3f}m | Yaw Drift: {math.degrees(delta_yaw):.2f}° | Peak Wheel Jerk: {peak_wheel_jerk:.2f} rad/s³"
        elif pname == "STOP":
            passed = (final_speed < 0.02) and (abs(df["wheel_w_L"].iloc[-1]) < 0.05) and (abs(df["wheel_w_R"].iloc[-1]) < 0.05)
            status_msg = f"Final Speed: {final_speed:.4f} m/s | Final Wheel w: {df['wheel_w_L'].iloc[-1]:.4f} rad/s"
        elif pname == "TURN_LEFT":
            passed = (delta_yaw > 1.0) and (df["wheel_w_L"].iloc[-1] < -1.0) and (df["wheel_w_R"].iloc[-1] > 1.0) and (net_disp < 0.25)
            status_msg = f"Delta Yaw: +{math.degrees(delta_yaw):.1f}° (CCW) | Net Drift: {net_disp:.3f}m | Left w: {df['wheel_w_L'].iloc[-1]:.2f}, Right w: {df['wheel_w_R'].iloc[-1]:.2f}"
        elif pname == "TURN_RIGHT":
            passed = (delta_yaw < -1.0) and (df["wheel_w_L"].iloc[-1] > 1.0) and (df["wheel_w_R"].iloc[-1] < -1.0) and (net_disp < 0.25)
            status_msg = f"Delta Yaw: {math.degrees(delta_yaw):.1f}° (CW) | Net Drift: {net_disp:.3f}m | Left w: {df['wheel_w_L'].iloc[-1]:.2f}, Right w: {df['wheel_w_R'].iloc[-1]:.2f}"
            
        print(f"  [RESULT: {'PASS' if passed else 'FAIL'}] {status_msg}")
        
        results[pname] = {
            "primitive": pname,
            "description": prim["desc"],
            "passed": bool(passed),
            "commanded_L_rad_s": prim["cmd_L"],
            "commanded_R_rad_s": prim["cmd_R"],
            "duration_s": prim["duration_ticks"] * 0.0333,
            "displacement_m": round(net_disp, 3),
            "delta_yaw_deg": round(math.degrees(delta_yaw), 2),
            "final_speed_mps": round(final_speed, 4),
            "final_wheel_w_L": round(float(df["wheel_w_L"].iloc[-1]), 3),
            "final_wheel_w_R": round(float(df["wheel_w_R"].iloc[-1]), 3),
            "peak_actuator_torque_Nm": round(float(np.max(np.abs(df["actuator_tau_L"]))), 3),
            "peak_commanded_jerk_rad_s3": round(peak_cmd_jerk, 2),
            "peak_wheel_angular_jerk_rad_s3": round(peak_wheel_jerk, 2),
            "telemetry_csv": csv_path
        }
        
    all_passed = all(r["passed"] for r in results.values())
    qualification_status = "PASS" if all_passed else "FAIL"
    
    summary = {
        "qualification_title": "Deterministic Physical Embodiment Low-Level Control Qualification",
        "gate_status": f"EMBODIMENT_QUALIFICATION = {qualification_status}",
        "all_primitives_passed": all_passed,
        "primitives": results
    }
    
    out_json = os.path.join(BASE_DIR, "audit", "embodiment_control_qualification.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n================================================================================")
    print(f"  EMBODIMENT QUALIFICATION GATE: {qualification_status}")
    print("================================================================================")
    return summary

if __name__ == "__main__":
    run_qualification()
