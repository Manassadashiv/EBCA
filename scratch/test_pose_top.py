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

# Top pose: (-1.50, -2.00, -45 deg)
s0_pos = [-1.50, -2.00]
s0_yaw = -45.0 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

print(f"=== TESTING ALL 20 BRANCHES AT POSE ({s0_pos[0]}, {s0_pos[1]}, -45 deg) ===")
branch_r2s = []
phys_trajs = []
grid_trajs = []

for b_idx in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = branches[b_idx]['actions']
    phys_s = []
    grid_s = []
    collided = False
    
    for step in range(len(u_seq)):
        hal.step(np.array(u_seq[step]))
        con_s = hal.get_carl_contact_info()
        if con_s['carl_contacts'] > con_s['floor_contacts']:
            collided = True
        s_cur = hal.read_sensors()[:15]
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw_c = 2.0 * np.arctan2(qz, qw)
        xc = hal.data.qpos[qa]
        yc = hal.data.qpos[qa+1]
        clr = mem.query_clearance(grid, torch.tensor([[xc, yc, yaw_c]]).float())[0].detach().numpy()
        phys_s.append(s_cur)
        grid_s.append(clr)
        
    phys_s = np.array(phys_s)
    grid_s = np.array(grid_s)
    phys_trajs.append(phys_s)
    grid_trajs.append(grid_s)
    
    y_t = phys_s.flatten()
    y_p = grid_s.flatten()
    r2 = 1.0 - np.sum((y_t - y_p)**2) / (np.sum((y_t - np.mean(y_t))**2) + 1e-8)
    rmse = np.sqrt(np.mean((y_t - y_p)**2))
    name = branches[b_idx]['name']
    branch_r2s.append((b_idx, name, r2, rmse, collided))
    print(f"Branch {b_idx:02d} ({name:22s}): R2={r2:6.4f}, RMSE={rmse:.3f}m, collided={collided}")

# Check diagonal dominance across the 20 branches
print("\n--- CHECKING DIAGONAL DOMINANCE (AGAINST INVERTED BRANCH) ---")
diag_dom_passes = 0
for i in range(20):
    rmse_self = branch_r2s[i][3]
    # Compute inverse branch
    u_inv = -np.array(branches[i]['actions'])
    # Rollout inverse branch in grid
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    grid_inv = []
    for step in range(len(u_inv)):
        hal.step(u_inv[step])
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw_c = 2.0 * np.arctan2(qz, qw)
        xc = hal.data.qpos[qa]
        yc = hal.data.qpos[qa+1]
        clr = mem.query_clearance(grid, torch.tensor([[xc, yc, yaw_c]]).float())[0].detach().numpy()
        grid_inv.append(clr)
    grid_inv = np.array(grid_inv)
    
    rmse_inv = np.sqrt(np.mean((phys_trajs[i] - grid_inv)**2))
    margin = rmse_inv - rmse_self
    status = "PASS" if (branch_r2s[i][2] >= 0.50 and margin >= 0.30) else "FAIL"
    if status == "PASS": diag_dom_passes += 1
    print(f"Branch {i:02d} ({branch_r2s[i][1]:22s}): R2={branch_r2s[i][2]:.4f}, self_RMSE={rmse_self:.3f}m, inv_RMSE={rmse_inv:.3f}m, margin={margin:+.3f}m [{status}]")

print(f"\nTotal passing: {diag_dom_passes} / 20")
