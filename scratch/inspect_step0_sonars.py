import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Map arena
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128)
vps = [(-1.5, -1.5), (-1.5, 0), (-1.5, 1.5), (0, -1.5), (0, 0), (0, 1.5), (1.5, -1.5), (1.5, 0), (1.5, 1.5)]
for vx, vy in vps:
    for angle in np.linspace(-np.pi, np.pi, 24, endpoint=False):
        hal.data.qpos[qa:qa+2] = [vx, vy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(angle/2), 0, 0, math.sin(angle/2)]
        mujoco.mj_forward(hal.model, hal.data)
        s = hal.read_sensors()[:15]
        grid = mem.accumulate_observations(grid, torch.tensor([[vx, vy, angle]]).float(), torch.tensor(s).unsqueeze(0).float())

s0_pos = [-2.00, -1.60]
s0_yaw = 67.5 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

phys_s = hal.read_sensors()[:15]
grid_s = mem.query_clearance(grid, torch.tensor([[s0_pos[0], s0_pos[1], s0_yaw]]).float())[0].detach().numpy()

print("--- STEP 0 SONAR COMPARISON AT S_0 = (-2.0, -1.6, 67.5 deg) ---")
for i in range(15):
    err = abs(phys_s[i] - grid_s[i])
    print(f"Ray {i:02d} ({i*12-84:+3d} deg): Phys={phys_s[i]:.2f}m, Grid={grid_s[i]:.2f}m, Diff={err:.2f}m")

print(f"\nOverall Mean Error at Step 0: {np.mean(np.abs(phys_s - grid_s)):.3f}m")
