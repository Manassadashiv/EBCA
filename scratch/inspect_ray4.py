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
qa = int(hal.model.joint('spatial_identity').qposadr[0])

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

# Step 5 pose: (-0.151, 0.960, +17.6 deg)
x = -0.151
y = 0.960
yaw = 17.6 * math.pi / 180.0
thc = yaw

phi_4 = mem.sonar_angles[4].item()
ray_angle = thc + phi_4
print(f"Ray 4 absolute angle: {ray_angle*180/math.pi:.1f} deg")

# Sample along ray 4 every 2cm from r=0 to r=3.5m
for r in np.linspace(0.1, 3.5, 35):
    cx = x + (mem.r_hull + r) * math.cos(ray_angle)
    cy = y + (mem.r_hull + r) * math.sin(ray_angle)
    c_ix = int((cx + mem.half_size) / mem.resolution)
    c_iy = int((cy + mem.half_size) / mem.resolution)
    val = grid[0, 0, c_iy, c_ix].item()
    seen = grid[0, 1, c_iy, c_ix].item()
    if val > 0.05 or (1.0 <= r <= 1.3):
        print(f"r={r:.2f}m: pos=({cx:+.3f}, {cy:+.3f}), grid=({c_ix}, {c_iy}), occ_val={val:.2f}, seen={seen:.1f}")
