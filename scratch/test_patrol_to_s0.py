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
va = int(hal.model.joint('spatial_identity').dofadr[0])

mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128, dtype=torch.float32)

# We track dead-reckoned pose:
pose_hat = np.array([0.0, 0.0, 0.0], dtype=np.float64)
dt = hal.dt

# Let's test waypoints navigation using a simple P-controller on wheel speeds:
# Waypoints to visit from (0, 0):
# 1. Turn north to (0, 1.2)
# 2. Go west to (-1.5, 1.2)
# 3. Go south along corridor to (-1.5, -1.8) [S0!]
# 4. Go south to (-1.5, -2.5)
# 5. Rotate in place 360 deg at (-1.5, -1.8) to map all surrounding walls!

waypoints = [
    (0.0, 1.2),
    (-1.5, 1.2),
    (-1.5, -1.8),
    (-1.5, -2.8),
    (-1.5, -1.8),
    (0.0, -1.8),
    (0.0, 0.0),
    (1.5, 0.0),
    (1.5, 1.5),
    (0.0, 0.0)
]

print("Starting autonomous exploration across labyrinth corridors...")
wp_idx = 0
total_ticks = 0

for wp in waypoints:
    target_x, target_y = wp
    print(f"Navigating to waypoint {wp_idx}: ({target_x:.2f}, {target_y:.2f})")
    
    # Drive towards waypoint until within 0.15m
    for step in range(600):
        # Current true qpos
        true_x = float(hal.data.qpos[qa])
        true_y = float(hal.data.qpos[qa+1])
        qw = float(hal.data.qpos[qa+3])
        qz = float(hal.data.qpos[qa+6])
        true_yaw = 2.0 * math.atan2(qz, qw)
        
        # Dead reckoned pose:
        dx = target_x - pose_hat[0]
        dy = target_y - pose_hat[1]
        dist = math.hypot(dx, dy)
        if dist < 0.15:
            print(f"Reached WP {wp_idx} at tick {total_ticks}! True: ({true_x:.2f}, {true_y:.2f}), Hat: ({pose_hat[0]:.2f}, {pose_hat[1]:.2f})")
            break
            
        target_angle = math.atan2(dy, dx)
        angle_err = math.atan2(math.sin(target_angle - pose_hat[2]), math.cos(target_angle - pose_hat[2]))
        
        u = np.zeros(6, dtype=np.float64)
        if abs(angle_err) > 0.2:
            # Turn in place
            rot_spd = 0.25 if angle_err > 0 else -0.25
            u[0] = -rot_spd
            u[1] = rot_spd
        else:
            # Drive forward with minor steering
            fwd_spd = min(0.25, max(0.10, dist * 0.5))
            steer = np.clip(angle_err * 0.5, -0.1, 0.1)
            u[0] = fwd_spd - steer
            u[1] = fwd_spd + steer
            
        s_curr = hal.read_sensors()
        sonars = s_curr[:15]
        
        # Accumulate observations into memory every 3 ticks
        if total_ticks % 3 == 0:
            p_tensor = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
            son_tensor = torch.tensor(sonars, dtype=torch.float32).unsqueeze(0)
            grid = mem.accumulate_observations(grid, p_tensor, son_tensor)
            
        # Step physics
        s_next, _ = hal.step(u)
        omega_z = s_next[20]
        
        # Integrate dead reckoning
        pose_hat[2] += omega_z * dt
        pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))
        
        # Linear velocity: calibrated linear gain 0.9875
        # Since u[0] and u[1] drive wheels, let's verify actual displacement:
        u_fwd = 0.5 * (u[0] + u[1])
        # Actual speed from HAL dt
        v_fwd = u_fwd * 1.19
        dx_loc = v_fwd * dt
        pose_hat[0] += dx_loc * math.cos(pose_hat[2])
        pose_hat[1] += dx_loc * math.sin(pose_hat[2])
        
        total_ticks += 1
        
    wp_idx += 1

print(f"Patrol complete in {total_ticks} ticks.")
# In-place 360 rotation to scan surrounding walls:
for r_step in range(120):
    u = np.zeros(6, dtype=np.float64)
    u[0] = -0.25
    u[1] = 0.25
    s_curr = hal.read_sensors()
    if r_step % 3 == 0:
        p_tensor = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
        son_tensor = torch.tensor(s_curr[:15], dtype=torch.float32).unsqueeze(0)
        grid = mem.accumulate_observations(grid, p_tensor, son_tensor)
    s_next, _ = hal.step(u)
    omega_z = s_next[20]
    pose_hat[2] += omega_z * dt
    pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))
    total_ticks += 1

# Check what the grid predicts at S0:
s0_pose = torch.tensor([[-1.50, -1.80, -45.0 * np.pi / 180.0]]).float()
pred_clearance = mem.query_clearance(grid, s0_pose)[0].detach().cpu().numpy()
print("\n--- Evaluation at S0 ---")
print("Grounded Pred Clearance at S0:", np.round(pred_clearance, 2))
