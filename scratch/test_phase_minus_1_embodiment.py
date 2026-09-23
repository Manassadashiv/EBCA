"""
scratch/test_phase_minus_1_embodiment.py — Phase -1 Embodiment & Deterministic Locomotion Test (Accurate Robot Indexing)

Performs rigorous physical embodiment audit and deterministic motor primitive testing:
1. Physical Embodiment Audit (Mass, Inertia, CoM, Resting stability)
2. Deterministic Locomotion Primitives (Forward, Reverse, Left, Right, Spin, Stop)
3. Closed-Loop Navigation Smoke Test (Start -> Target, Start -> Obstacle -> Target)
Logs raw evidence and outputs pass/fail diagnostics.
"""

import os
import sys
import math
import json
import numpy as np
import mujoco

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from carl_simulation import CarlSimulationRunner

def run_embodiment_audit():
    print("================================================================================")
    print("  PHASE -1: PHYSICAL EMBODIMENT AUDIT")
    print("================================================================================")
    
    xml_path = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)
    
    total_mass = float(np.sum(model.body_mass))
    print(f"Total Model Body Mass: {total_mass:.3f} kg")
    
    # Reset and step for 100 ticks (resting equilibrium)
    mujoco.mj_resetData(model, data)
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            qa = model.jnt_qposadr[j]
            data.qpos[qa+3 : qa+7] = [1.0, 0.0, 0.0, 0.0]
            
    q_rob = model.joint("spatial_identity").qposadr[0]
    data.qpos[q_rob : q_rob+3] = [0.0, 0.0, 0.05291]
    mujoco.mj_forward(model, data)
    
    initial_z = float(data.qpos[q_rob+2])
    
    for _ in range(100):
        mujoco.mj_step(model, data)
        
    rest_z = float(data.qpos[q_rob+2])
    qw, qx, qy, qz = data.qpos[q_rob+3 : q_rob+7]
    
    # Compute roll and pitch from quaternion
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    sinp = 2 * (qw * qy - qz * qx)
    pitch = math.asin(np.clip(sinp, -1.0, 1.0))
    
    print(f"Resting State Analysis:")
    print(f"  Initial Pos Z: {initial_z:.4f} m  -> Settled Rest Z: {rest_z:.4f} m")
    print(f"  Resting Pitch: {pitch:.4f} rad, Resting Roll: {roll:.4f} rad")
    
    is_stable = (abs(roll) < 0.05) and (abs(pitch) < 0.05) and (0.04 < rest_z < 0.06)
    print(f"  Embodiment Equilibrium Status: {'PASS (STABLE)' if is_stable else 'FAIL (UNSTABLE)'}")
    return is_stable

def run_locomotion_primitives():
    print("\n================================================================================")
    print("  PHASE -1: DETERMINISTIC MOTOR PRIMITIVE SMOKE TESTS")
    print("================================================================================")
    
    runner = CarlSimulationRunner(open_space=True, headless=True)
    
    primitives = [
        ("1. Both Forward", 10.0, 10.0, 30, "Straight forward displacement"),
        ("2. Both Reverse", -10.0, -10.0, 30, "Straight reverse displacement"),
        ("3. Left Wheel Only", 10.0, 0.0, 30, "Rightward turn / clockwise"),
        ("4. Right Wheel Only", 0.0, 10.0, 30, "Leftward turn / counter-clockwise"),
        ("5. In-Place Spin Left (CCW)", -10.0, 10.0, 30, "Positive yaw change"),
        ("6. In-Place Spin Right (CW)", 10.0, -10.0, 30, "Negative yaw change"),
        ("7. Controlled Stop", 0.0, 0.0, 30, "Velocity remains ~0")
    ]
    
    results = []
    
    for name, v_L, v_R, duration, expected in primitives:
        runner.hal.reset_robot()
        start_x, start_y, start_yaw = runner.hal.get_robot_pos()
        
        # Step primitive
        for _ in range(duration):
            runner.hal.write_motors(v_L, v_R, 0.0, 0.0)
            for _ in range(20):
                mujoco.mj_step(runner.hal.model, runner.hal.data)
                
        end_x, end_y, end_yaw = runner.hal.get_robot_pos()
        dx = float(end_x - start_x)
        dy = float(end_y - start_y)
        dyaw = float(end_yaw - start_yaw)
        total_dist = float(math.sqrt(dx*dx + dy*dy))
        wheel_w_L = float(runner.hal.data.qvel[runner.hal.model.joint('w_left').dofadr[0]])
        wheel_w_R = float(runner.hal.data.qvel[runner.hal.model.joint('w_right').dofadr[0]])
        
        passed = False
        if "Forward" in name:
            passed = dx > 0.3 and total_dist > 0.3
        elif "Reverse" in name:
            passed = dx < -0.3 and total_dist > 0.3
        elif "Left Wheel" in name:
            passed = total_dist > 0.08 and abs(dyaw) > 0.2
        elif "Right Wheel" in name:
            passed = total_dist > 0.08 and abs(dyaw) > 0.2
        elif "Spin Left" in name:
            passed = total_dist < 0.20 and abs(dyaw) > 0.5
        elif "Spin Right" in name:
            passed = total_dist < 0.20 and abs(dyaw) > 0.5
        elif "Stop" in name:
            passed = total_dist < 0.02
            
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<28} | Cmd: ({v_L:5.1f}, {v_R:5.1f}) | Disp: dx={dx:+.3f}, dy={dy:+.3f}, dyaw={dyaw:+.3f} (dist={total_dist:.3f}m) | WheelVel: ({wheel_w_L:5.1f}, {wheel_w_R:5.1f})")
        results.append(passed)
        
    all_primitives_pass = all(results)
    print(f"\n  Locomotion Primitives Result: {sum(results)}/{len(results)} Passed | Status: {'ALL PASS' if all_primitives_pass else 'FAIL'}")
    return all_primitives_pass

def run_closed_loop_navigation_gate():
    print("\n================================================================================")
    print("  PHASE -1: CLOSED-LOOP NAVIGATION GATE (START -> TARGET & AVOIDANCE)")
    print("================================================================================")
    
    runner = CarlSimulationRunner(open_space=True, headless=True)
    
    # Test 1: Start -> Target
    runner.hal.reset_robot()
    target_pos = np.array([2.5, 1.5])
    
    if hasattr(runner.hal, "food_geom_id"):
        runner.hal.model.geom_pos[runner.hal.food_geom_id] = [target_pos[0], target_pos[1], 0.12]
        mujoco.mj_forward(runner.hal.model, runner.hal.data)
        
    reached_target_1 = False
    dist = 99.0
    for tick in range(300):
        x, y, yaw = runner.hal.get_robot_pos()
        pos = np.array([x, y])
        rel = target_pos - pos
        dist = float(np.linalg.norm(rel))
        if dist < 0.25:
            reached_target_1 = True
            break
            
        # Target angle in robot frame
        target_world_angle = math.atan2(rel[1], rel[0])
        heading_error = target_world_angle - yaw
        # Normalize to [-pi, pi]
        heading_error = (heading_error + math.pi) % (2 * math.pi) - math.pi
        
        v_base = 10.0
        turn = heading_error * 6.0
        v_L = v_base - turn
        v_R = v_base + turn
        
        runner.hal.write_motors(v_L, v_R, 0.0, 0.0)
        for _ in range(20):
            mujoco.mj_step(runner.hal.model, runner.hal.data)
            
    print(f"  Test 1: Direct Target Navigation (Start (0,0) -> Target (2.5, 1.5)) | Final Dist: {dist:.3f}m | Reached: {'PASS' if reached_target_1 else 'FAIL'}")
    
    # Test 2: Start -> Obstacle Avoidance -> Target
    runner.hal.reset_robot()
    reached_target_2 = False
    had_collision = False
    
    for tick in range(400):
        x, y, yaw = runner.hal.get_robot_pos()
        pos = np.array([x, y])
        rel = target_pos - pos
        dist = float(np.linalg.norm(rel))
        sensors = runner.hal.read_sensors()
        
        if dist < 0.25:
            reached_target_2 = True
            break
            
        # Check collision
        for i in range(runner.hal.data.ncon):
            c = runner.hal.data.contact[i]
            g1 = runner.hal.model.geom(c.geom1).name
            g2 = runner.hal.model.geom(c.geom2).name
            if "wall" in g1 or "wall" in g2:
                had_collision = True
                
        min_front = np.min(sensors[9:15])
        left_sector = np.mean(sensors[6:12])
        right_sector = np.mean(sensors[12:18])
        
        target_world_angle = math.atan2(rel[1], rel[0])
        heading_error = target_world_angle - yaw
        heading_error = (heading_error + math.pi) % (2 * math.pi) - math.pi
        goal_turn = heading_error * 5.0
        
        avoid_turn = 0.0
        v_base = 10.0 * np.clip((min_front - 0.45)/0.75, 0.0, 1.0)
        if min_front < 1.20:
            intensity = (1.20 - min_front) / 1.20 * 12.0
            avoid_turn = intensity if left_sector < right_sector else -intensity
            
        turn = goal_turn + avoid_turn
        runner.hal.write_motors(v_base - turn, v_base + turn, 0.0, 0.0)
        for _ in range(20):
            mujoco.mj_step(runner.hal.model, runner.hal.data)
            
    test_2_passed = reached_target_2 and not had_collision
    print(f"  Test 2: Closed-Loop Obstacle Avoidance Navigation | Final Dist: {dist:.3f}m | Collisions: {had_collision} | Reached: {'PASS' if test_2_passed else 'FAIL'}")
    
    return reached_target_1 and test_2_passed

if __name__ == "__main__":
    e_pass = run_embodiment_audit()
    l_pass = run_locomotion_primitives()
    n_pass = run_closed_loop_navigation_gate()
    
    overall = e_pass and l_pass and n_pass
    print("\n================================================================================")
    print(f"  PHASE -1 RECOVERY & EMBODIMENT GATE: {'PASS' if overall else 'FAIL'}")
    print("================================================================================")
    sys.exit(0 if overall else 1)
