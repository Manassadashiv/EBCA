import sys
sys.path.insert(0, '.')
import math
import json
import numpy as np
import torch
import mujoco
from pathlib import Path

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

manifest_path = Path("evidence/stage2_2_r2/manifests/frozen_branch_sequences.json")
with open(manifest_path, "r") as f:
    branches = json.load(f)

hal = CarlStage1HAL(open_space=False, headless=True)
qa = int(hal.model.joint('spatial_identity').qposadr[0])
s0_pos = [-1.50, -1.80]
s0_yaw = -45.0 * math.pi / 180.0
hal.reset()
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

phys_rollouts = []
for b in branches:
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_b = np.array(b["actions"], dtype=np.float64)
    bp = []
    for step in range(len(u_b)):
        hal.step(u_b[step])
        bp.append(hal.read_sensors()[:15])
    phys_rollouts.append(np.array(bp))

oracle_grid = torch.load("evidence/stage2_2_r2/arena_occupancy_grid.pt")
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

dt = 0.03
for b_idx, b in enumerate(branches):
    u_seq = b["actions"]
    curr_pose = [-1.50, -1.80, s0_yaw]
    prev_v = 0.0
    prev_w = 0.0
    pred_poses = []
    
    for step in range(len(u_seq)):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        
        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        v_target = u_fwd * (0.0125 / dt)
        next_v = is_fwd_zero * (0.70 * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)
        
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        w_gain = 5.50 + 5.20 * math.exp(-step / 3.0)
        w_target = u_diff * w_gain
        next_w = is_diff_zero * (0.75 * prev_w) + (1.0 - is_diff_zero) * (0.15 * prev_w + 0.85 * w_target)
        
        dx_loc = next_v * dt
        dth = next_w * dt
        th = curr_pose[2]
        curr_pose = [
            curr_pose[0] + dx_loc * math.cos(th),
            curr_pose[1] + dx_loc * math.sin(th),
            curr_pose[2] + dth
        ]
        pred_poses.append(list(curr_pose))
        prev_v = next_v
        prev_w = next_w
        
    poses_tensor = torch.tensor(pred_poses, dtype=torch.float32)
    with torch.no_grad():
        clearance = mem.query_clearance(oracle_grid.repeat(len(pred_poses), 1, 1, 1), poses_tensor)
    pred_sonar = clearance.numpy().flatten()
    true_sonar = phys_rollouts[b_idx].flatten()
    
    r2 = float(1.0 - np.sum((true_sonar - pred_sonar)**2) / (np.sum((true_sonar - np.mean(true_sonar))**2) + 1e-8))
    rmse = float(np.sqrt(np.mean((true_sonar - pred_sonar)**2)))
    print(f"Branch {b_idx:02d} ({b['name']:20s}): R^2={r2:7.4f}, RMSE={rmse:.3f}")
