import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
import torch
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL(open_space=False, headless=True)
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128, dtype=torch.float32)

pose_hat = np.array([0.0, 0.0, 0.0], dtype=np.float64)
dt = hal.dt

# Corridor path:
# 1. (0.0, 1.2) - Drive North along open central corridor
# 2. (-1.5, 1.2) - Cut West into the corridor
# 3. (-1.5, -1.8) - Drive South along western corridor to S0
# 4. (-1.5, -2.8) - Drive South to end of corridor
# 5. (-1.5, -1.8) - Drive North back to S0

waypoints = [
    (0.0, 1.2),
    (-1.5, 1.2),
    (-1.5, -1.8),
    (-1.5, -2.8),
    (-1.5, -1.8)
]

total_ticks = 0

# 1. Initial 360-degree panoramic sonar scan at spawn (0, 0):
print("Performing initial 360-degree panoramic scan at spawn (0, 0)...")
for r in range(160):
    u_rot = np.zeros(6)
    u_rot[0] = -0.20
    u_rot[1] = 0.20
    s_curr = hal.read_sensors()
    if r % 2 == 0:
        p_t = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
        s_t = torch.tensor(s_curr[:15], dtype=torch.float32).unsqueeze(0)
        grid = mem.accumulate_observations(grid, p_t, s_t)
    s_next, _ = hal.step(u_rot)
    omega_z = s_next[20]
    pose_hat[2] += omega_z * dt
    pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))
    total_ticks += 1

for wp_idx, (tx, ty) in enumerate(waypoints):
    print(f"\n--- Navigating to Waypoint {wp_idx}: ({tx:.2f}, {ty:.2f}) ---")
    for step in range(600):
        dx = tx - pose_hat[0]
        dy = ty - pose_hat[1]
        dist = math.hypot(dx, dy)
        
        true_x = float(hal.data.qpos[qa])
        true_y = float(hal.data.qpos[qa+1])
        
        if dist < 0.12:
            print(f"Reached WP {wp_idx} at tick {total_ticks}! True: ({true_x:.2f}, {true_y:.2f}), Hat: ({pose_hat[0]:.2f}, {pose_hat[1]:.2f}), Err: {math.hypot(true_x-pose_hat[0], true_y-pose_hat[1]):.3f}m")
            break
            
        target_ang = math.atan2(dy, dx)
        ang_err = math.atan2(math.sin(target_ang - pose_hat[2]), math.cos(target_ang - pose_hat[2]))
        
        u = np.zeros(6, dtype=np.float64)
        if abs(ang_err) > 0.35:
            # Turn in place towards waypoint
            rot = 0.22 if ang_err > 0 else -0.22
            u[0] = -rot
            u[1] = rot
        else:
            # Drive forward with proportional heading correction
            fwd = min(0.20, max(0.08, dist * 0.4))
            steer = np.clip(ang_err * 0.35, -0.10, 0.10)
            u[0] = fwd - steer
            u[1] = fwd + steer
            
        # Accumulate sonars
        s_curr = hal.read_sensors()
        sonars = s_curr[:15]
        if total_ticks % 2 == 0:
            p_t = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
            s_t = torch.tensor(sonars, dtype=torch.float32).unsqueeze(0)
            grid = mem.accumulate_observations(grid, p_t, s_t)
            
        # Step physics
        s_next, _ = hal.step(u)
        omega_z = s_next[20]
        
        # Dead reckoning integration:
        pose_hat[2] += omega_z * dt
        pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))
        
        # Measure linear displacement from wheel action
        u_fwd = 0.5 * (u[0] + u[1])
        v_fwd = u_fwd * 1.1207
        dx_loc = v_fwd * dt
        pose_hat[0] += dx_loc * math.cos(pose_hat[2])
        pose_hat[1] += dx_loc * math.sin(pose_hat[2])
        
        total_ticks += 1

    # If this is WP 2 (S0), do an in-place 360 scan right here:
    if wp_idx == 2:
        print("At S0 (-1.50, -1.80): performing 360-degree panoramic sonar scan...")
        for r in range(160):
            u_rot = np.zeros(6)
            u_rot[0] = -0.20
            u_rot[1] = 0.20
            s_curr = hal.read_sensors()
            if r % 2 == 0:
                p_t = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
                s_t = torch.tensor(s_curr[:15], dtype=torch.float32).unsqueeze(0)
                grid = mem.accumulate_observations(grid, p_t, s_t)
            s_next, _ = hal.step(u_rot)
            omega_z = s_next[20]
            pose_hat[2] += omega_z * dt
            pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))
            total_ticks += 1

print(f"\nExploration completed in {total_ticks} ticks.")
true_x = float(hal.data.qpos[qa])
true_y = float(hal.data.qpos[qa+1])
print(f"Final Pose -> True: ({true_x:.3f}, {true_y:.3f}), Hat: ({pose_hat[0]:.3f}, {pose_hat[1]:.3f}), Error: {math.hypot(true_x-pose_hat[0], true_y-pose_hat[1]):.3f}m")

# Evaluate clearance prediction at S0:
s0_pose = torch.tensor([[-1.50, -1.80, -45.0 * np.pi / 180.0]]).float()
pred_clearance = mem.query_clearance(grid, s0_pose)[0].detach().cpu().numpy()

# True sonars at S0:
hal.reset()
s0_pos = [-1.50, -1.80]
s0_yaw = -45.0 * math.pi / 180.0
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
mujoco.mj_forward(hal.model, hal.data)
true_sonars_s0 = hal.read_sensors()[:15]

print("\n--- S0 Validation ---")
print("True Sonars at S0:     ", np.round(true_sonars_s0, 2))
print("Grounded Map at S0:    ", np.round(pred_clearance, 2))
rmse = np.sqrt(np.mean((true_sonars_s0 - pred_clearance)**2))
r2 = float(1.0 - np.sum((true_sonars_s0 - pred_clearance)**2) / (np.sum((true_sonars_s0 - np.mean(true_sonars_s0))**2) + 1e-8))
print(f"RMSE at S0: {rmse:.4f} m")
print(f"R^2 at S0:  {r2:.4f}")
