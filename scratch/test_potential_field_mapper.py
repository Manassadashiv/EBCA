import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL(open_space=False, headless=True)
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128, dtype=torch.float32)

pose_hat = np.array([0.0, 0.0, 0.0], dtype=np.float64)
dt = hal.dt

# Target waypoints to explore the entire central and western corridor:
# 1. Turn to north open corridor (0.0, 1.2)
# 2. Cut west into the corridor (-1.5, 1.2)
# 3. Head south through S0 (-1.5, -1.8)
# 4. Turn around and explore the southern intersection (-1.5, -2.8)
# 5. Return to S0 (-1.5, -1.8) and do a full 360 scan!

waypoints = [
    (0.0, 1.2),
    (-1.5, 1.2),
    (-1.5, -1.8),
    (-1.5, -2.8),
    (-1.5, -1.8)
]

sonar_angles = np.linspace(-2.0944, 2.0944, 15)  # [-120 deg, +120 deg]

total_ticks = 0
for wp_idx, (tx, ty) in enumerate(waypoints):
    print(f"\n--- Navigating to WP {wp_idx}: ({tx:.2f}, {ty:.2f}) ---")
    for step in range(500):
        # Read sensors
        s = hal.read_sensors()
        sonars = s[:15]
        
        # Current dead reckoned pose
        x_h, y_h, th_h = pose_hat
        true_x, true_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        
        dx = tx - x_h
        dy = ty - y_h
        dist = math.hypot(dx, dy)
        if dist < 0.20:
            print(f"Reached WP {wp_idx} at tick {total_ticks} (step {step})! Error: {math.hypot(true_x - x_h, true_y - y_h):.3f}m")
            break
            
        # Target attraction vector in body frame:
        target_world_ang = math.atan2(dy, dx)
        target_rel_ang = math.atan2(math.sin(target_world_ang - th_h), math.cos(target_world_ang - th_h))
        attract_fwd = math.cos(target_rel_ang)
        attract_lat = math.sin(target_rel_ang)
        
        # Sonar repulsion vector in body frame:
        repulse_fwd = 0.0
        repulse_lat = 0.0
        for i, (dist_i, ang_i) in enumerate(zip(sonars, sonar_angles)):
            if dist_i < 0.60:
                # Repulsive force inversely proportional to distance
                rep_mag = (0.60 - dist_i) / 0.60
                repulse_fwd -= rep_mag * math.cos(ang_i)
                repulse_lat -= rep_mag * math.sin(ang_i)
                
        # Net direction
        net_fwd = attract_fwd + 1.8 * repulse_fwd
        net_lat = attract_lat + 1.8 * repulse_lat
        desired_rel_ang = math.atan2(net_lat, net_fwd)
        
        # Frontal clearance (center 5 rays)
        front_dist = min(sonars[5:10])
        
        u = np.zeros(6, dtype=np.float64)
        if front_dist < 0.30:
            # STOP forward drive completely to prevent contact & wheel slip!
            # Pure in-place rotation
            rot = 0.25 if net_lat > 0 else -0.25
            u[0] = -rot
            u[1] = rot
        elif abs(desired_rel_ang) > 0.6:
            # Heading error large: turn in place
            rot = 0.25 if desired_rel_ang > 0 else -0.25
            u[0] = -rot
            u[1] = rot
        else:
            # Forward drive with proportional steering
            fwd_scale = min(1.0, max(0.1, (front_dist - 0.30) / 0.50))
            fwd = 0.20 * fwd_scale
            steer = np.clip(desired_rel_ang * 0.4, -0.15, 0.15)
            u[0] = fwd - steer
            u[1] = fwd + steer
            
        # Map accumulation
        if total_ticks % 3 == 0:
            p_tensor = torch.tensor([[x_h, y_h, th_h]], dtype=torch.float32)
            son_tensor = torch.tensor(sonars, dtype=torch.float32).unsqueeze(0)
            grid = mem.accumulate_observations(grid, p_tensor, son_tensor)
            
        # Step HAL
        s_next, _ = hal.step(u)
        omega_z = s_next[20]
        
        # Dead reckoning update:
        pose_hat[2] += omega_z * dt
        pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))
        
        u_fwd = 0.5 * (u[0] + u[1])
        # Calibrated steady-state speed (0.9875 eliminates over-integration)
        v_fwd = u_fwd * 0.9875
        dx_loc = v_fwd * dt
        pose_hat[0] += dx_loc * math.cos(pose_hat[2])
        pose_hat[1] += dx_loc * math.sin(pose_hat[2])
        
        total_ticks += 1

print(f"\nExploration complete in {total_ticks} ticks.")
true_x, true_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
print(f"Final Pose -> True: ({true_x:.2f}, {true_y:.2f}), Hat: ({pose_hat[0]:.2f}, {pose_hat[1]:.2f}), Error: {math.hypot(true_x - pose_hat[0], true_y - pose_hat[1]):.3f}m")

# Now do in-place 360 rotation at final pose to build 360 degree sonar coverage
print("Scanning 360 degrees in place...")
for r in range(150):
    u = np.zeros(6, dtype=np.float64)
    u[0] = -0.25
    u[1] = 0.25
    s_curr = hal.read_sensors()
    if r % 2 == 0:
        p_tensor = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
        son_tensor = torch.tensor(s_curr[:15], dtype=torch.float32).unsqueeze(0)
        grid = mem.accumulate_observations(grid, p_tensor, son_tensor)
    s_next, _ = hal.step(u)
    omega_z = s_next[20]
    pose_hat[2] += omega_z * dt
    pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))

# Evaluate clearance prediction at S0:
s0_pose = torch.tensor([[-1.50, -1.80, -45.0 * np.pi / 180.0]]).float()
pred_clearance = mem.query_clearance(grid, s0_pose)[0].detach().cpu().numpy()
print("\n--- S0 Comparison ---")
# True sonars at S0:
hal.reset()
s0_pos = [-1.50, -1.80]
s0_yaw = -45.0 * math.pi / 180.0
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
mujoco.mj_forward(hal.model, hal.data)
true_sonars_s0 = hal.read_sensors()[:15]
print("True Sonars at S0:     ", np.round(true_sonars_s0, 2))
print("Grounded Map at S0:    ", np.round(pred_clearance, 2))
rmse = np.sqrt(np.mean((true_sonars_s0 - pred_clearance)**2))
print(f"RMSE at S0: {rmse:.4f} m")
