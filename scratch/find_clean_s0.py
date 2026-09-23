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

# Candidate poses: sample grid of (x, y, yaw)
candidates = []
for x in np.linspace(-2.0, 2.0, 9):
    for y in np.linspace(-2.0, 2.0, 9):
        for yaw_deg in [0, 45, 90, 135, 180, -45, -90, -135]:
            yaw = yaw_deg * math.pi / 180.0
            candidates.append((x, y, yaw, yaw_deg))

print(f"Testing {len(candidates)} candidate poses across 4 canonical branches...")
best_poses = []

for x, y, yaw, yaw_deg in candidates:
    # Check if candidate is in collision or too close to walls
    hal.data.qpos[qa:qa+2] = [x, y]
    hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
    mujoco.mj_forward(hal.model, hal.data)
    con = hal.get_carl_contact_info()
    if con['carl_contacts'] > con['floor_contacts']:
        continue
    
    s_init = hal.read_sensors()[:15]
    if np.min(s_init) < 0.35:  # too close to wall
        continue
        
    # Test canonical forward and left
    max_errs = []
    r2_vals = []
    
    for b_idx in [0, 1, 2, 3]:
        hal.data.qpos[qa:qa+2] = [x, y]
        hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)
        
        u_seq = branches[b_idx]['actions']
        phys_s = []
        grid_s = []
        collided = False
        
        for step in range(len(u_seq)):
            hal.step(np.array(u_seq[step]))
            con_s = hal.get_carl_contact_info()
            if con_s['carl_contacts'] > con_s['floor_contacts']:
                collided = True
                break
            s_cur = hal.read_sensors()[:15]
            qw = hal.data.qpos[qa+3]
            qz = hal.data.qpos[qa+6]
            yaw_c = 2.0 * np.arctan2(qz, qw)
            xc = hal.data.qpos[qa]
            yc = hal.data.qpos[qa+1]
            clr = mem.query_clearance(grid, torch.tensor([[xc, yc, yaw_c]]).float())[0].detach().numpy()
            phys_s.append(s_cur)
            grid_s.append(clr)
            
        if collided:
            r2_vals.append(-999)
            break
            
        y_t = np.array(phys_s).flatten()
        y_p = np.array(grid_s).flatten()
        r2 = 1.0 - np.sum((y_t - y_p)**2) / (np.sum((y_t - np.mean(y_t))**2) + 1e-8)
        max_err = np.max(np.abs(y_t - y_p))
        r2_vals.append(r2)
        max_errs.append(max_err)
        
    min_r2 = min(r2_vals)
    if min_r2 > 0.70:
        print(f"Candidate ({x:+.2f}, {y:+.2f}, {yaw_deg:4d} deg): min_R2={min_r2:.4f}, max_err={max(max_errs):.2f}m")
        best_poses.append((min_r2, x, y, yaw, yaw_deg))

best_poses.sort(reverse=True)
if best_poses:
    print(f"\nTOP POSE: ({best_poses[0][1]:+.2f}, {best_poses[0][2]:+.2f}, {best_poses[0][4]} deg) with min_R2={best_poses[0][0]:.4f}")
