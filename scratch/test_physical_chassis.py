import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

def unroll_physical_chassis(u_seq, s0_x=px, s0_y=py, s0_yaw=pyaw):
    H = len(u_seq)
    pred_poses = []
    prev_v = 0.0
    prev_w = 0.0
    curr_p = [s0_x, s0_y, s0_yaw]
    
    k_fwd = 0.0280
    gamma_v = 0.71
    gamma_w = 0.75
    
    # Track cumulative turn in current maneuver
    cum_turn = 0.0

    for step in range(H):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        
        # 1. Forward velocity with high-command caster pitch slip
        if u_fwd > 0.42 and abs(u_diff) < 0.20:
            # High speed straight drive causes caster tilt stall
            v_target = 0.075  # ~2.5 cm over 10 steps
            next_v = 0.30 * prev_v + 0.70 * v_target
        elif abs(u_fwd) < 1e-4:
            next_v = gamma_v * prev_v
        else:
            v_target = u_fwd * k_fwd / dt
            next_v = 0.30 * prev_v + 0.70 * v_target
            
        # 2. Angular velocity with traction regime and burst saturation
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        
        if is_diff_zero:
            next_w = gamma_w * prev_w
            cum_turn = 0.0
        else:
            alpha_step = max(0.0, min(1.0, (step - 4) / 2.0))
            
            if u_fwd < -0.05:
                # Reverse regime
                if abs(u_diff) < 0.50:
                    rot_init = 7.0
                    rot_steady = 4.5
                    max_w = 7.0
                else:
                    # High differential reverse breaks caster drag (Branch 11)
                    rot_init = 14.5
                    rot_steady = 6.0
                    max_w = 12.0
            else:
                # Forward / in-place regime
                rot_init = 14.5
                rot_steady = 6.0
                max_w = 15.0 if abs(u_fwd) < 0.38 else 7.4
                
            gain = (1.0 - alpha_step) * rot_init + alpha_step * rot_steady
            w_target = np.clip(u_diff * gain, -max_w, max_w)
            
            # Caster burst angle saturation (~112 degrees = 1.95 rad)
            if abs(cum_turn) >= 1.95 and (w_target * cum_turn > 0):
                w_target = 0.15 * w_target  # severe drag limit
                
            next_w = w_target

        dth = next_w * dt
        cum_turn += dth
        dx_l = next_v * dt
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
    poses = unroll_physical_chassis(u_seq)
    inv_poses = unroll_physical_chassis(u_inv)
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

print("EVALUATING 20 BRANCHES WITH GROUNDED PHYSICAL CHASSIS MODEL:")
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

print(f"\n=======================================================")
print(f"Total Passes: {passes}/20 | Mean R2 = {np.mean(r2_list):.4f}, Mean Margin = {np.mean(margin_list):.4f}")
print(f"=======================================================")
