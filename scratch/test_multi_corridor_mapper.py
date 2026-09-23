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
print("Spawn:", hal.data.qpos[qa:qa+3])

mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128, dtype=torch.float32)

pose_hat = np.array([0.0, 0.0, 0.0], dtype=np.float64)
dt = hal.dt
linear_gain = 1.1207

# Complete multi-corridor autonomous patrol:
# Covers central arena, western corridor (containing S0), and central-south arena
waypoints = [
    (0.0, 1.2, True),     # North central
    (-1.5, 1.2, True),    # Cross west to corridor entrance
    (-1.5, -0.5, False),  # Mid western corridor
    (-1.5, -1.8, True),   # S0 benchmark pose
    (-1.5, -2.8, True),   # South western corridor
    (-1.5, -1.8, True),   # Return to S0
    (-1.5, 0.0, False),   # Return north
    (0.0, 0.0, True),     # Return to origin
    (0.0, -1.8, True),    # South central corridor (maps east face of lwall_v_3_1)
    (0.0, 0.0, False)     # Return home
]

total_ticks = 0

for wp_idx, (tx, ty, do_scan) in enumerate(waypoints):
    print(f"Navigating to waypoint {wp_idx}: ({tx:.2f}, {ty:.2f})...", flush=True)
    for step in range(600):
        dx = tx - pose_hat[0]
        dy = ty - pose_hat[1]
        dist = math.hypot(dx, dy)
        if dist < 0.14:
            true_x = float(hal.data.qpos[qa])
            true_y = float(hal.data.qpos[qa+1])
            err = math.hypot(true_x - pose_hat[0], true_y - pose_hat[1])
            print(f"  Reached WP {wp_idx} at tick {total_ticks}! True: ({true_x:.2f}, {true_y:.2f}), Hat: ({pose_hat[0]:.2f}, {pose_hat[1]:.2f}), Err: {err:.3f}m", flush=True)
            break

        target_ang = math.atan2(dy, dx)
        ang_err = math.atan2(math.sin(target_ang - pose_hat[2]), math.cos(target_ang - pose_hat[2]))

        u = np.zeros(6, dtype=np.float64)
        if abs(ang_err) > 0.35:
            rot = 0.22 if ang_err > 0 else -0.22
            u[0] = -rot
            u[1] = rot
        else:
            fwd = min(0.20, max(0.08, dist * 0.4))
            steer = np.clip(ang_err * 0.35, -0.10, 0.10)
            u[0] = fwd - steer
            u[1] = fwd + steer

        s_curr = hal.read_sensors()
        sonars = s_curr[:15]
        if total_ticks % 2 == 0:
            p_t = torch.tensor([[pose_hat[0], pose_hat[1], pose_hat[2]]], dtype=torch.float32)
            s_t = torch.tensor(sonars, dtype=torch.float32).unsqueeze(0)
            grid = mem.accumulate_observations(grid, p_t, s_t)

        s_next, _ = hal.step(u)
        omega_z = s_next[20]
        pose_hat[2] += omega_z * dt
        pose_hat[2] = math.atan2(math.sin(pose_hat[2]), math.cos(pose_hat[2]))

        u_fwd = 0.5 * (u[0] + u[1])
        v_fwd = u_fwd * linear_gain
        dx_loc = v_fwd * dt
        pose_hat[0] += dx_loc * math.cos(pose_hat[2])
        pose_hat[1] += dx_loc * math.sin(pose_hat[2])

        total_ticks += 1

    if do_scan:
        print(f"  Performing panoramic 360 scan at WP {wp_idx}...", flush=True)
        for r in range(120):
            u_rot = np.zeros(6)
            u_rot[0] = -0.22
            u_rot[1] = 0.22
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

print(f"\nMulti-corridor mapping completed in {total_ticks} ticks.", flush=True)
torch.save(grid, "evidence/stage2_2_grounded/grounded_occupancy_grid.pt")
print("Saved to evidence/stage2_2_grounded/grounded_occupancy_grid.pt", flush=True)
