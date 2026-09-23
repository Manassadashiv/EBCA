import sys
import json
import math
import time
from pathlib import Path
import numpy as np
import torch
from scipy.optimize import minimize

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scratch.fast_eval_branches import (
    phys_s_list, branches, grid, mem, px, py, pyaw, dt,
    true_poses_list
)

def unroll_poses_full(u_seq, params, s0_x=px, s0_y=py, s0_yaw=pyaw):
    k_fwd, gamma_v, k_rot_init, k_rot_steady, w_max_init, w_max_steady, slip_thresh, c_v, decay_step = params
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

        # Speed-dependent turning attenuation
        slip_attenuation = 1.0 / (1.0 + max(0.0, c_v) * abs(u_fwd))

        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        alpha_step = max(0.0, min(1.0, (step - 3) / max(decay_step, 1.0)))
        gain = (1.0 - alpha_step) * k_rot_init + alpha_step * k_rot_steady
        max_w = ((1.0 - alpha_step) * w_max_init + alpha_step * w_max_steady) * slip_attenuation

        w_target = np.clip(u_diff * gain * slip_attenuation, -max_w, max_w)
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.25 * prev_w + 0.75 * w_target)

        dx_l = next_v * dt
        dth = next_w * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
        pred_poses.append(list(curr_p))
        prev_v, prev_w = next_v, next_w

    return pred_poses

def fast_eval_full(params):
    all_fwd_poses = []
    all_inv_poses = []
    lens = []
    for b_idx in range(len(branches)):
        u_seq = branches[b_idx]['actions']
        u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]
        poses = unroll_poses_full(u_seq, params)
        inv_poses = unroll_poses_full(u_inv, params)
        all_fwd_poses.extend(poses)
        all_inv_poses.extend(inv_poses)
        lens.append(len(poses))

    total_pts = len(all_fwd_poses)
    fwd_t = torch.tensor(all_fwd_poses, dtype=torch.float32)
    inv_t = torch.tensor(all_inv_poses, dtype=torch.float32)

    with torch.no_grad():
        clr_fwd = mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), fwd_t).numpy()
        clr_inv = mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), inv_t).numpy()

    clr_fwd = np.clip(clr_fwd, 0.0, 5.0)
    clr_inv = np.clip(clr_inv, 0.0, 5.0)

    offset = 0
    passes = 0
    r2_list = []
    margin_list = []
    smooth_loss = 0.0

    for b_idx in range(len(branches)):
        H = lens[b_idx]
        grid_s = clr_fwd[offset:offset+H]
        grid_inv = clr_inv[offset:offset+H]
        offset += H

        phys_s = phys_s_list[b_idx]
        phys_flat = phys_s.flatten()
        grid_flat = grid_s.flatten()

        r2 = 1.0 - np.sum((phys_flat - grid_flat)**2) / (np.sum((phys_flat - np.mean(phys_flat))**2) + 1e-8)
        rmse_self = np.sqrt(np.mean((phys_s - grid_s)**2))
        rmse_inv = np.sqrt(np.mean((phys_s - grid_inv)**2))
        margin = rmse_inv - rmse_self

        r2_list.append(r2)
        margin_list.append(margin)

        r2_def = max(0.0, 0.50 - r2)
        mar_def = max(0.0, 0.30 - margin)
        smooth_loss += 50.0 * (r2_def**2) + 20.0 * (mar_def**2) - 0.5 * r2

        if r2 >= 0.50 and margin >= 0.30:
            passes += 1

    return smooth_loss, passes, r2_list, margin_list

# Test initial
p0 = [0.0190, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 0.5, 2.0]
loss0, passes0, r2s0, mar0 = fast_eval_full(p0)
print(f"Initial: {passes0}/20 passes, Loss={loss0:.4f}")

# Optimize
t0 = time.time()
best_p = p0
best_passes = passes0
best_loss = loss0

# Grid search / Powell / Nelder-Mead hybrid
bounds = [
    (0.015, 0.030),  # k_fwd
    (0.50, 0.85),    # gamma_v
    (10.0, 20.0),    # k_rot_init
    (4.0, 10.0),     # k_rot_steady
    (10.0, 18.0),    # w_max_init
    (5.0, 10.0),     # w_max_steady
    (0.10, 0.60),    # slip_thresh
    (0.0, 4.0),      # c_v
    (1.0, 5.0)       # decay_step
]

res = minimize(
    lambda p: fast_eval_full(p)[0],
    p0,
    method='Powell',
    bounds=bounds,
    options={'maxiter': 20, 'disp': True}
)

t1 = time.time()
print(f"Optimization finished in {t1-t0:.2f}s!")
opt_loss, opt_passes, opt_r2s, opt_mars = fast_eval_full(res.x)
print(f"Optimized: {opt_passes}/20 passes, Loss={opt_loss:.4f}")
print(f"Parameters: {list(res.x)}")

for i in range(20):
    b_pass = (opt_r2s[i] >= 0.50 and opt_mars[i] >= 0.30)
    mark = "PASS" if b_pass else "FAIL"
    print(f"Branch {i:02d} ({branches[i]['name']:<20s}): R2={opt_r2s[i]:.4f}, Margin={opt_mars[i]:.4f} -> {mark}")
