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

# 1. Load the frozen branches
manifest_path = Path("evidence/stage2_2_r2/manifests/frozen_branch_sequences.json")
with open(manifest_path, "r") as f:
    branches = json.load(f)

# 2. Run physical rollouts from S0
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

print("Physical rollouts complete.")

# 3. Load grounded grid from task-1680 (let's run the mapper to get the grid tensor):
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
# Let's see what oracle grid gives first as benchmark:
oracle_grid = torch.load("evidence/stage2_2_r2/arena_occupancy_grid.pt")
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

# Evaluate mental rollouts using learned dynamics:
# Let's test different k_fwd values:
for k_fwd_val in [0.0125, 0.025, 0.03362]:
    dt = 0.03
    v_target_factor = k_fwd_val / dt
    r2_list = []
    
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
            v_target = u_fwd * v_target_factor
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
        r2_list.append(r2)
        
    print(f"k_fwd={k_fwd_val:.5f} (v_factor={v_target_factor:.3f}): Mean R^2={np.mean(r2_list):.4f}, Min R^2={np.min(r2_list):.4f}")
