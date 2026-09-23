import sys
sys.path.insert(0, '.')
import json
import math
import numpy as np
import torch
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Map arena thoroughly
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128)
import torch
vps = [(-1.5, -1.5), (-1.5, 0), (-1.5, 1.5), (0, -1.5), (0, 0), (0, 1.5), (1.5, -1.5), (1.5, 0), (1.5, 1.5)]
for vx, vy in vps:
    for angle in np.linspace(-np.pi, np.pi, 24, endpoint=False):
        hal.data.qpos[qa:qa+2] = [vx, vy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(angle/2), 0, 0, math.sin(angle/2)]
        mujoco.mj_forward(hal.model, hal.data)
        s = hal.read_sensors()[:15]
        grid = mem.accumulate_observations(grid, torch.tensor([[vx, vy, angle]]).float(), torch.tensor(s).unsqueeze(0).float())

s0_pos = [-0.15, 0.96]
s0_yaw = -95.4 * math.pi / 180.0

hal.reset()
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
mujoco.mj_forward(hal.model, hal.data)

# Let's inspect Canonical Left (branch 1)
print("=== CANONICAL LEFT FORENSICS ===")
for step in range(10):
    hal.step(np.array([-0.7, 0.7, 0, 0, 0, 0]))
    qw = hal.data.qpos[qa+3]
    qz = hal.data.qpos[qa+6]
    yaw = 2.0 * np.arctan2(qz, qw)
    x = hal.data.qpos[qa]
    y = hal.data.qpos[qa+1]
    s_phys = hal.read_sensors()[:15]
    
    # Query clearance at EXACT physical pose
    clr = mem.query_clearance(grid, torch.tensor([[x, y, yaw]]).float())[0].detach().numpy()
    err = np.abs(s_phys - clr)
    print(f"Step {step:02d}: pose=({x:+.3f}, {y:+.3f}, {yaw*180/math.pi:+.1f} deg) | Mean Error={np.mean(err):.3f}m, Max Error={np.max(err):.3f}m, r2_step={1.0 - np.sum((s_phys-clr)**2)/(np.sum((s_phys-np.mean(s_phys))**2)+1e-8):.4f}")
    if step == 5:
        print("  Phys sonar:", [f"{v:.2f}" for v in s_phys[:8]])
        print("  Grid sonar:", [f"{v:.2f}" for v in clr[:8]])
