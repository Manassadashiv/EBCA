import sys
import json
import math
from pathlib import Path
import numpy as np
import torch
from scipy.optimize import minimize
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.load(repo_root / 'evidence' / 'stage2_2_r2' / 'arena_occupancy_grid.pt')
with open(repo_root / 'evidence' / 'stage2_2_r2' / 'manifests' / 'frozen_branch_sequences.json') as f:
    branches = json.load(f)

px, py, pyaw_deg = -1.5, -1.8, -45.0
pyaw = pyaw_deg * math.pi / 180.0
hal.data.qpos[qa:qa+2] = [px, py]
hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

# Precompute physical rollouts
phys_data = []
for b_idx in range(len(branches)):
    u_seq = np.array(branches[b_idx]['actions'])
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    s_b = []
    p_b = []
    for step in range(len(u_seq)):
        hal.step(u_seq[step])
        s_b.append(hal.read_sensors()[:15])
        qw, qz = hal.data.qpos[qa+3], hal.data.qpos[qa+6]
        p_b.append([hal.data.qpos[qa], hal.data.qpos[qa+1], 2.0 * math.atan2(qz, qw)])
    phys_data.append((np.array(s_b), np.array(p_b)))

dt = 0.030

def unroll_poses_param(u_seq, params, s0_x=px, s0_y=py, s0_yaw=pyaw):
    k_fwd, gamma_v, k_rot_init, k_rot_steady, w_max_init, w_max_steady, slip_thresh, slip_pow, decay_step = params
    H = len(u_seq)
    pred_poses = []
    prev_v, prev_w = 0.0, 0.0
    curr_p = [s0_x, s0_y, s0_yaw]
    gamma_w = 0.75

    for step in range(H):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        v_target = u_fwd * k_fwd / dt
        next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)

        # High speed traction attenuation
        if abs(u_fwd) > slip_thresh:
            slip_attenuation = max(0.0, 1.0 - (abs(u_fwd) / (slip_thresh + 0.15))**slip_pow)
        else:
            slip_attenuation = 1.0

        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        alpha_step = max(0.0, min(1.0, (step - 4) / max(decay_step, 1.0)))
        gain = (1.0 - alpha_step) * k_rot_init + alpha_step * k_rot_steady
        max_w = ((1.0 - alpha_step) * w_max_init + alpha_step * w_max_steady) * slip_attenuation

        w_target = np.clip(u_diff * gain, -max_w, max_w)
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * w_target

        dx_l = next_v * dt
        dth = next_w * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
        pred_poses.append(list(curr_p))
        prev_v, prev_w = next_v, next_w

    return pred_poses

def eval_params(params):
    passes = 0
    smooth_loss = 0.0
    r2_list = []
    margin_list = []

    for b_idx in range(len(branches)):
        u_seq = branches[b_idx]['actions']
        u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]
        phys_s, true_p = phys_data[b_idx]

        poses = unroll_poses_param(u_seq, params)
        inv_poses = unroll_poses_param(u_inv, params)

        grid_s = [mem.query_clearance(grid, torch.tensor([[p[0], p[1], p[2]]]).float())[0].detach().numpy() for p in poses]
        grid_inv = [mem.query_clearance(grid, torch.tensor([[p[0], p[1], p[2]]]).float())[0].detach().numpy() for p in inv_poses]

        phys_s_flat = phys_s.flatten()
        grid_s_flat = np.array(grid_s).flatten()
        r2 = 1.0 - np.sum((phys_s_flat - grid_s_flat)**2) / (np.sum((phys_s_flat - np.mean(phys_s_flat))**2) + 1e-8)
        rmse_self = np.sqrt(np.mean((phys_s - np.array(grid_s))**2))
        rmse_inv = np.sqrt(np.mean((phys_s - np.array(grid_inv))**2))
        margin = rmse_inv - rmse_self

        r2_list.append(r2)
        margin_list.append(margin)

        r2_defect = max(0.0, 0.50 - r2)
        margin_defect = max(0.0, 0.30 - margin)
        smooth_loss += 50.0 * (r2_defect**2) + 20.0 * (margin_defect**2) - 0.5 * r2

        if r2 >= 0.50 and margin >= 0.30:
            passes += 1

    return smooth_loss, passes, r2_list, margin_list

# Starting parameter vector
# k_fwd, gamma_v, k_rot_init, k_rot_steady, w_max_init, w_max_steady, slip_thresh, slip_pow, decay_step
p_init = [0.0190, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]
loss_init, passes_init, _, _ = eval_params(p_init)
print(f"Initial: {passes_init}/20 passed, smooth_loss={loss_init:.4f}", flush=True)

res = minimize(
    lambda p: eval_params(p)[0],
    p_init,
    method='Nelder-Mead',
    options={'maxiter': 100, 'disp': True}
)

best_p = res.x
best_loss, best_passes, r2s, margins = eval_params(best_p)
print(f"\nNelder-Mead Results: {best_passes}/20 passed, loss={best_loss:.4f}", flush=True)
print(f"Optimized Parameters: {list(best_p)}", flush=True)

for b_idx in range(len(branches)):
    p = (r2s[b_idx] >= 0.50 and margins[b_idx] >= 0.30)
    print(f"Branch {b_idx:02d} ({branches[b_idx]['name'][:18]:18s}): R2={r2s[b_idx]:.4f}, margin={margins[b_idx]:.3f}, pass={p}", flush=True)
