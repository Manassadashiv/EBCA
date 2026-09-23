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
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

print(f"=== FULL DETAILED 20-BRANCH VERIFICATION AT (-2.00, -1.60, 67.5 deg) ===")
pass_count = 0

for b_idx in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = branches[b_idx]['actions']
    phys_s, grid_s, grid_inv = [], [], []
    u_inv = -np.array(u_seq)
    
    for step in range(len(u_seq)):
        hal.step(np.array(u_seq[step]))
        s_cur = hal.read_sensors()[:15]
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw_c = 2.0 * np.arctan2(qz, qw)
        xc = hal.data.qpos[qa]
        yc = hal.data.qpos[qa+1]
        clr = mem.query_clearance(grid, torch.tensor([[xc, yc, yaw_c]]).float())[0].detach().numpy()
        phys_s.append(s_cur)
        grid_s.append(clr)
        
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    for step in range(len(u_inv)):
        hal.step(u_inv[step])
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw_c = 2.0 * np.arctan2(qz, qw)
        xc = hal.data.qpos[qa]
        yc = hal.data.qpos[qa+1]
        clr = mem.query_clearance(grid, torch.tensor([[xc, yc, yaw_c]]).float())[0].detach().numpy()
        grid_inv.append(clr)
        
    phys_s = np.array(phys_s)
    grid_s = np.array(grid_s)
    grid_inv = np.array(grid_inv)
    
    y_t = phys_s.flatten()
    y_p = grid_s.flatten()
    r2 = 1.0 - np.sum((y_t - y_p)**2) / (np.sum((y_t - np.mean(y_t))**2) + 1e-8)
    rmse_self = np.sqrt(np.mean((phys_s - grid_s)**2))
    rmse_inv = np.sqrt(np.mean((phys_s - grid_inv)**2))
    margin = rmse_inv - rmse_self
    status = "PASS" if (r2 >= 0.50 and margin >= 0.30) else "FAIL"
    if status == "PASS": pass_count += 1
    name = branches[b_idx]['name']
    print(f"Branch {b_idx:02d} ({name:22s}): R2={r2:6.4f}, RMSE={rmse_self:.3f}m, inv_RMSE={rmse_inv:.3f}m, margin={margin:+.3f}m [{status}]")

print(f"\nOVERALL RESULT: {pass_count} / 20 PASSED!")
