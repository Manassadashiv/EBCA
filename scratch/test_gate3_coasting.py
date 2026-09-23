import sys
import math
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
px, py, pyaw = -1.5, -1.8, -45.0 * math.pi / 180.0

grid = torch.load(repo_root / 'evidence' / 'stage2_2_r2' / 'arena_occupancy_grid.pt')
if grid.dim() == 3:
    grid = grid.unsqueeze(0)
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

# 1. Physical coasting
hal.reset()
hal.data.qpos[qa:qa+2] = [px, py]
hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

# Impulse step
hal.step(np.array([0.5, 0.5, 0, 0, 0, 0]))
s_coast = []
coast_poses = []
for _ in range(10):
    hal.step(np.zeros(6))
    s_coast.append(hal.read_sensors()[:15])
    qw, qz = hal.data.qpos[qa+3], hal.data.qpos[qa+6]
    coast_poses.append([hal.data.qpos[qa], hal.data.qpos[qa+1], 2.0*math.atan2(qz, qw)])
s_coast = np.array(s_coast)
coast_poses = np.array(coast_poses)

print("Physical Coasting Poses:")
for s in range(10):
    print(f"step {s}: pos=[{coast_poses[s,0]:.4f}, {coast_poses[s,1]:.4f}], dist={math.sqrt((coast_poses[s,0]-px)**2 + (coast_poses[s,1]-py)**2):.4f}m")

# Test mental coasting with different gamma_v and k_fwd
dt = 0.030
for kf in [0.0125, 0.0180, 0.0220, 0.0280]:
    for gv in [0.70, 0.80, 0.85, 0.90, 0.93, 0.95]:
        curr_p = [px, py, pyaw]
        pred_zero = []
        v_curr = 0.5 * kf / dt
        for step in range(10):
            v_curr = gv * v_curr
            dx = v_curr * dt * math.cos(curr_p[2])
            dy = v_curr * dt * math.sin(curr_p[2])
            curr_p = [curr_p[0] + dx, curr_p[1] + dy, curr_p[2]]
            c = mem.query_clearance(grid, torch.tensor([[curr_p[0], curr_p[1], curr_p[2]]]).float())[0].numpy()
            pred_zero.append(np.clip(c, 0.0, 5.0))
        pred_zero = np.array(pred_zero)

        r2_coast = float(1.0 - np.sum((s_coast - pred_zero)**2) / (np.sum((s_coast - np.mean(s_coast))**2) + 1e-8))
        if r2_coast > 0.60:
            print(f"SUCCESS: kf={kf:.4f}, gv={gv:.2f} -> Coasting R² = {r2_coast:.4f} (>= 0.60 target!)")
