import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

def unroll_linear_model(u_seq, s0_x=px, s0_y=py, s0_yaw=pyaw):
    H = len(u_seq)
    pred_poses = []
    prev_v = 0.0
    prev_w = 0.0
    curr_p = [s0_x, s0_y, s0_yaw]

    for step in range(H):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        
        # Stall flag
        is_stall = 1.0 if (u_fwd > 0.40 and abs(u_diff) < 0.20) else 0.0
        
        # Zero check for coasting decay
        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        
        if is_fwd_zero:
            next_v = 0.70 * prev_v
        else:
            next_v = 0.4366 * u_fwd + 0.3902 * prev_v - 0.1543 * is_stall * u_fwd
            
        if is_diff_zero:
            next_w = 0.75 * prev_w
        else:
            diff_drag = u_diff * abs(u_fwd)
            next_w = 4.6113 * u_diff + 0.4560 * prev_w - 5.2388 * diff_drag

        dx_l = next_v * dt
        dth = next_w * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
        pred_poses.append(list(curr_p))
        prev_v, prev_w = next_v, next_w

    return pred_poses

all_fwd_poses = []
all_inv_poses = []
lens = []
for b_idx in range(len(branches)):
    u_seq = branches[b_idx]['actions']
    u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]
    poses = unroll_linear_model(u_seq)
    inv_poses = unroll_linear_model(u_inv)
    all_fwd_poses.extend(poses)
    all_inv_poses.extend(inv_poses)
    lens.append(len(poses))

total_pts = len(all_fwd_poses)
fwd_t = torch.tensor(all_fwd_poses, dtype=torch.float32)
inv_t = torch.tensor(all_inv_poses, dtype=torch.float32)

with torch.no_grad():
    clr_fwd = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), fwd_t).numpy(), 0.0, 5.0)
    clr_inv = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), inv_t).numpy(), 0.0, 5.0)

offset = 0
passes = 0
r2_list = []
margin_list = []

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

    b_pass = (r2 >= 0.50 and margin >= 0.30)
    if b_pass:
        passes += 1
    mark = "PASS" if b_pass else "FAIL"
    print(f"Branch {b_idx:02d} ({branches[b_idx]['name']:<20s}): R2={r2:.4f}, Margin={margin:.4f} -> {mark}")

print(f"\nTotal Passes: {passes}/20 | Mean R2 = {np.mean(r2_list):.4f}, Mean Margin = {np.mean(margin_list):.4f}")
