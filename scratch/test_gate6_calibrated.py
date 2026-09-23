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
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Map arena thoroughly
print("Mapping arena...")
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

s0_pos = [-2.00, -1.60]
s0_yaw = 67.5 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

print("\n--- ROLLING OUT PHYSICAL TRUTHS AND AIR-GAPPED PREDICTIONS ---")
phys_trajs = []
mental_trajs = []
inv_mental_trajs = []

dt = 0.030
k_fwd = 0.0125
gamma_v = 0.70
gamma_w = 0.75

def rollout_mental_poses(u_seq):
    H = len(u_seq)
    pred_poses = []
    prev_v = 0.0
    prev_w = 0.0
    curr_pose = [s0_pos[0], s0_pos[1], s0_yaw]
    for step in range(H):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        
        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        v_target = u_fwd * k_fwd / dt
        next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)
        
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        w_gain = 5.5 + 5.2 * math.exp(-step / 3.0)
        w_target = u_diff * w_gain
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.15 * prev_w + 0.85 * w_target)
        
        dx_local = next_v * dt
        dy_local = 0.0
        dtheta = next_w * dt
        
        th = curr_pose[2]
        dx_g = dx_local * math.cos(th) - dy_local * math.sin(th)
        dy_g = dx_local * math.sin(th) + dy_local * math.cos(th)
        
        curr_pose = [curr_pose[0] + dx_g, curr_pose[1] + dy_g, curr_pose[2] + dtheta]
        pred_poses.append(list(curr_pose))
        prev_v = next_v
        prev_w = next_w
    return pred_poses

for b in range(len(branches)):
    # Physical
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = np.array(branches[b]['actions'])
    H = len(u_seq)
    phys = []
    for step in range(H):
        hal.step(u_seq[step])
        phys.append(hal.read_sensors()[:15])
    phys_trajs.append(np.array(phys))
    
    # Mental (air-gapped: pose unroll -> memory query)
    pred_poses = rollout_mental_poses(u_seq)
    mental = []
    for step in range(H):
        p = pred_poses[step]
        clr = mem.query_clearance(grid, torch.tensor([[p[0], p[1], p[2]]]).float())[0].detach().numpy()
        mental.append(clr)
    mental_trajs.append(np.array(mental))
    
    # Inverted mental
    u_inv = -u_seq
    inv_poses = rollout_mental_poses(u_inv)
    inv_mental = []
    for step in range(H):
        p = inv_poses[step]
        clr = mem.query_clearance(grid, torch.tensor([[p[0], p[1], p[2]]]).float())[0].detach().numpy()
        inv_mental.append(clr)
    inv_mental_trajs.append(np.array(inv_mental))

print("\n=== GATE 6 BENCHMARK SCORECARD: ALL 20 BRANCHES ===")
pass_count = 0
for b in range(len(branches)):
    y_true = phys_trajs[b].flatten()
    y_pred = mental_trajs[b].flatten()
    r2 = 1.0 - np.sum((y_true - y_pred)**2) / (np.sum((y_true - np.mean(y_true))**2) + 1e-8)
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    rmse_inv = np.sqrt(np.mean((phys_trajs[b] - inv_mental_trajs[b])**2))
    margin = rmse_inv - rmse
    name = branches[b]['name']
    status = "PASS" if (r2 >= 0.50 and margin >= 0.30) else "FAIL"
    if status == "PASS": pass_count += 1
    print(f"Branch {b:02d} ({name:22s}): R2={r2:6.4f}, RMSE={rmse:.3f}m, inv_RMSE={rmse_inv:.3f}m, margin={margin:+.3f}m [{status}]")

print(f"\nTOTAL PASSED: {pass_count} / 20")
