import sys
sys.path.insert(0, '.')
import json
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

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

s0_pos = [-1.50, -2.00]
s0_yaw = -45.0 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

# 1. Execute physical rollouts for all 20 branches
phys_trajs = []
for b in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = branches[b]['actions']
    phys = []
    for step in range(len(u_seq)):
        hal.step(np.array(u_seq[step]))
        phys.append(hal.read_sensors()[:15])
    phys_trajs.append(np.array(phys))

# 2. Execute mental rollouts in grid
mental_trajs = []
for b in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = branches[b]['actions']
    mental = []
    for step in range(len(u_seq)):
        hal.step(np.array(u_seq[step]))
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw_c = 2.0 * np.arctan2(qz, qw)
        xc = hal.data.qpos[qa]
        yc = hal.data.qpos[qa+1]
        clr = mem.query_clearance(grid, torch.tensor([[xc, yc, yaw_c]]).float())[0].detach().numpy()
        mental.append(clr)
    mental_trajs.append(np.array(mental))

print("=== 20x20 CONFUSION MATRIX & SPECIFICATION DIAGONAL DOMINANCE ===")
pass_count = 0
for k in range(20):
    # Length of branch k
    H_k = len(mental_trajs[k])
    pred_k = mental_trajs[k].flatten()
    true_k = phys_trajs[k][:H_k].flatten()
    
    r2_k = 1.0 - np.sum((true_k - pred_k)**2) / (np.sum((true_k - np.mean(true_k))**2) + 1e-8)
    rmse_self = np.sqrt(np.mean((true_k - pred_k)**2))
    
    # Compare against competing physical branches j != k
    competing_rmses = []
    for j in range(20):
        if j == k: continue
        # Truncate to common horizon min(H_k, H_j)
        H_common = min(H_k, len(phys_trajs[j]))
        pred_sub = mental_trajs[k][:H_common].flatten()
        comp_sub = phys_trajs[j][:H_common].flatten()
        rmse_j = np.sqrt(np.mean((comp_sub - pred_sub)**2))
        competing_rmses.append(rmse_j)
        
    min_competing_rmse = min(competing_rmses)
    margin = min_competing_rmse - rmse_self
    
    status = "PASS" if (r2_k >= 0.50 and margin >= 0.30) else "FAIL"
    if status == "PASS": pass_count += 1
    name = branches[k]['name']
    print(f"Branch {k:02d} ({name:22s}): R2={r2_k:.4f}, self_RMSE={rmse_self:.3f}m, min_comp_RMSE={min_competing_rmse:.3f}m, margin={margin:+.3f}m [{status}]")

print(f"\nTOTAL PASSED UNDER PROTOCOL 1: {pass_count} / 20")
