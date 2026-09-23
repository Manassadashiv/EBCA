"""
tests/diagnostic_arm_i_baseline.py — Baseline Capability Test for ARM-I
Audits whether intact CARL can move, steer, avoid obstacles, and reach goals
on reachable baseline layouts.
"""

import sys
import math
from pathlib import Path
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

def run_baseline_battery():
    print("=========================================================================")
    print("DIAGNOSTIC REQUIREMENT A: BASELINE CAPABILITY TEST FOR ARM-I")
    print("=========================================================================")
    
    # Use clean_arena.xml (open arena)
    hal = CarlStage1HAL(xml_path="world/clean_arena.xml")
    grid_p = "world/stage3_2_environments/family3_layout_grid.pt"
    engine = CARLStage2_3R1DeliberationEngine(grid_path=grid_p, mode="deliberative")
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    
    # 3 Baseline Task Scenarios (5 seeds each = 15 episodes total)
    # Scenario 1: Straight goal at (0.60, 0.00), budget 50 ticks (1.5s)
    # Scenario 2: Left-offset goal at (0.50, 0.40), budget 60 ticks (1.8s)
    # Scenario 3: Right-offset goal at (0.50, -0.40), budget 60 ticks (1.8s)
    
    scenarios = [
        {"name": "Straight Reachable Target", "target": (0.60, 0.00), "yaw0": 0.0, "max_ticks": 50},
        {"name": "Left Curved Reachable Target", "target": (0.50, 0.35), "yaw0": 0.0, "max_ticks": 60},
        {"name": "Right Curved Reachable Target", "target": (0.50, -0.35), "yaw0": 0.0, "max_ticks": 60},
    ]
    
    seeds = [3001, 3002, 3003, 3004, 3005]
    results = []
    
    for sc in scenarios:
        print(f"\n--- Scenario: {sc['name']} [Target: {sc['target']}, Budget: {sc['max_ticks']} ticks] ---")
        sc_succ = 0
        for s in seeds:
            hal.reset()
            hal.data.qpos[qa:qa+2] = [0.0, 0.0]
            hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
            hal.data.qvel[:] = 0.0
            mujoco.mj_forward(hal.model, hal.data)
            for _ in range(10):
                hal.step(np.zeros(6))
                
            engine.initialize_pose(0.0, 0.0, 0.0)
            
            v_est = 0.0
            last_u = np.zeros(6)
            success = False
            collision = False
            
            tx, ty = sc["target"]
            for t in range(sc["max_ticks"]):
                sensors = hal.read_sensors()
                sonars = sensors[:15]
                gyro_yaw = float(sensors[20])
                
                u_fwd = float(0.5 * (last_u[0] + last_u[1]))
                v_target = u_fwd * (engine.k_fwd / 0.030)
                v_est = 0.70 * v_est + 0.30 * v_target
                engine.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
                
                action, _ = engine.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
                last_u = action
                hal.step(action)
                
                cur_x, cur_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
                dist_to_target = math.hypot(cur_x - tx, cur_y - ty)
                
                contacts = hal.get_carl_contact_info()
                if (contacts["carl_contacts"] - contacts["floor_contacts"]) > 0:
                    collision = True
                    break
                    
                if dist_to_target <= 0.15:  # Within 15cm of target
                    success = True
                    break
                    
            if success:
                sc_succ += 1
            print(f"  Seed {s}: Success={success} | Final Pos=({cur_x:.2f}, {cur_y:.2f}) | DistToTarget={dist_to_target:.2f}m | Ticks={t+1}")
            results.append({"scenario": sc["name"], "seed": s, "success": success, "collision": collision, "dist": dist_to_target, "ticks": t+1})
            
        print(f"  Scenario Success Rate: {sc_succ}/{len(seeds)} ({sc_succ/len(seeds)*100:.1f}%)")
        
    total_succ = sum(1 for r in results if r["success"])
    print(f"\n=========================================================================")
    print(f"BASELINE TEST SUMMARY: {total_succ}/{len(results)} Successes ({total_succ/len(results)*100:.1f}%)")
    print(f"Total Collisions: {sum(1 for r in results if r['collision'])}/{len(results)}")
    print("=========================================================================")

if __name__ == "__main__":
    run_baseline_battery()
