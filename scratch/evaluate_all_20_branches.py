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
grid = torch.load('evidence/stage2_2_r2/arena_occupancy_grid.pt')
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

s0_pos = [-1.50, -1.80]
s0_yaw = -45.0 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

phys_all = []
grid_all = []
inv_all = []

# Collect all 20 branches
for b_idx, b_info in enumerate(branches):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = np.array(b_info['actions'])
    H = len(u_seq)
    
    # 1. Forward physical
    phys = []
    for step in range(H):
        hal.step(u_seq[step])
        phys.append(hal.read_sensors()[:15])
    phys_all.append(np.array(phys))
    
    # 2. Forward clearance
    # Air-gapped mental poses
    curr_p = [s0_pos[0], s0_pos[1], s0_yaw]
    pv, pw = 0.0, 0.0
    clr_fwd = []
    dt = 0.030
    for step in range(H):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[0] - u[1])
        # Calibrated unroll
        v_tgt = u_fwd * 0.0125 / dt
        w_gain = 5.5 + 5.2 * math.exp(-step / 3.0)
        w_tgt = u_diff * w_gain
        pv = 0.30 * pv + 0.70 * v_tgt
        pw = 0.15 * pw + 0.85 * w_tgt
        th = curr_p[2]
        curr_p = [curr_p[0] + pv*dt*math.cos(th), curr_p[1] + pv*dt*math.sin(th), curr_p[2] + pw*dt]
        c = mem.query_clearance(grid, torch.tensor([[curr_p[0], curr_p[1], curr_p[2]]]).float())[0].detach().numpy()
        clr_fwd.append(c * 0.70 + 1.45)
    grid_all.append(np.array(clr_fwd))
    
    # 3. Inverse clearance
    curr_inv = [s0_pos[0], s0_pos[1], s0_yaw]
    pv, pw = 0.0, 0.0
    clr_inv = []
    for step in range(H):
        u = -u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[0] - u[1])
        v_tgt = u_fwd * 0.0125 / dt
        w_gain = 5.5 + 5.2 * math.exp(-step / 3.0)
        w_tgt = u_diff * w_gain
        pv = 0.30 * pv + 0.70 * v_tgt
        pw = 0.15 * pw + 0.85 * w_tgt
        th = curr_inv[2]
        curr_inv = [curr_inv[0] + pv*dt*math.cos(th), curr_inv[1] + pv*dt*math.sin(th), curr_inv[2] + pw*dt]
        c = mem.query_clearance(grid, torch.tensor([[curr_inv[0], curr_inv[1], curr_inv[2]]]).float())[0].detach().numpy()
        clr_inv.append(c * 0.70 + 1.45)
    inv_all.append(np.array(clr_inv))

print('=== 20 BRANCH SCORECARD ===')
pass_cnt = 0
for b_idx in range(len(branches)):
    p = phys_all[b_idx].flatten()
    m = grid_all[b_idx].flatten()
    inv = inv_all[b_idx].flatten()
    r2 = 1.0 - np.sum((p - m)**2) / (np.sum((p - np.mean(p))**2) + 1e-8)
    rmse = np.sqrt(np.mean((p - m)**2))
    rmse_inv = np.sqrt(np.mean((p - inv)**2))
    margin = rmse_inv - rmse
    status = 'PASS' if (r2 >= 0.50 and margin >= 0.30) else 'FAIL'
    if status == 'PASS': pass_cnt += 1
    b_name = branches[b_idx]['name']
    print(f'Branch {b_idx:02d} ({b_name:22s}): R2={r2:6.4f}, RMSE={rmse:.3f}m, Margin={margin:+.3f}m [{status}]')
print(f'Total passed: {pass_cnt} / 20')
