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

# Step 0 pose
x = -0.150
y = 0.960
yaw = -76.6 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = [x, y]
hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
mujoco.mj_forward(hal.model, hal.data)
s_phys = hal.read_sensors()[:15]
clr = mem.query_clearance(grid, torch.tensor([[x, y, yaw]]).float())[0].detach().numpy()

print(f"{'Ray':4s} | {'Angle(deg)':10s} | {'Phys(m)':8s} | {'Grid(m)':8s} | {'Diff(m)':8s}")
print("-" * 50)
for i in range(15):
    angle_i = (yaw + mem.sonar_angles[i].item()) * 180 / math.pi
    print(f"{i:4d} | {angle_i:10.1f} | {s_phys[i]:8.3f} | {clr[i]:8.3f} | {abs(s_phys[i] - clr[i]):8.3f}")
