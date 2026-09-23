import sys
import json
import math
from pathlib import Path
import numpy as np
import torch

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

def unroll_exact_physics(u_seq):
    H = len(u_seq)
    curr_p = [px, py, pyaw]
    prev_v = 0.0
    prev_w = 0.0
    seq_poses = []

    k_fwd_base = 0.028
    gamma_v = 0.71
    gamma_w = 0.75

    for step, u in enumerate(u_seq):
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])

        # Forward velocity with chassis pitch slip dip around [0.35, 0.65] strictly on straight motion
        if abs(u_diff) < 0.15 and (0.35 <= u_fwd <= 0.65):
            eff_k_fwd = 0.0075
        elif u_fwd < -0.35:
            eff_k_fwd = 0.0150
        else:
            eff_k_fwd = k_fwd_base

        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        v_targ = u_fwd * eff_k_fwd / dt
        next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_targ)

        # Turning dynamics
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        alpha_step = max(0.0, min(1.0, (step - 4) / 2.0))

        # Spin vs Translation
        if abs(u_fwd) < 0.05:
            # Pure in-place spin
            gain = (1.0 - alpha_step) * 14.5 + alpha_step * 6.0
            max_w = (1.0 - alpha_step) * 15.0 + alpha_step * 7.4
        elif u_fwd < -0.05:
            # Reverse turn: dependent on |u_diff|
            if abs(u_diff) > 0.55:
                gain = (1.0 - alpha_step) * 12.0 + alpha_step * 6.0
                max_w = (1.0 - alpha_step) * 12.0 + alpha_step * 8.0
            else:
                gain = (1.0 - alpha_step) * 7.0 + alpha_step * 5.0
                max_w = (1.0 - alpha_step) * 7.0 + alpha_step * 5.5
        else:
            # Forward turn: speed attenuation
            gain = (1.0 - alpha_step) * 14.5 + alpha_step * 6.0
            max_w = (1.0 - alpha_step) * 15.0 + alpha_step * 7.4
            if u_fwd > 0.38:
                slip_att = max(0.0, 1.0 - (u_fwd / 0.53)**4)
                max_w *= slip_att

        # Pitch wheel lift-off clamp on extreme continuous turn (e.g. Branch 15)
        w_target = np.clip(u_diff * gain, -max_w, max_w)
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * w_target

        dx_l = next_v * dt
        dth = next_w * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
        seq_poses.append(list(curr_p))
        prev_v, prev_w = next_v, next_w

    return seq_poses

# Test across all 20 branches
all_fwd = []
all_inv = []
lens = []

for b_idx in range(len(branches)):
    u_seq = branches[b_idx]['actions']
    u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]
    all_fwd.extend(unroll_exact_physics(u_seq))
    all_inv.extend(unroll_exact_physics(u_inv))
    lens.append(len(u_seq))

total_pts = len(all_fwd)
t_fwd = torch.tensor(all_fwd, dtype=torch.float32)
t_inv = torch.tensor(all_inv, dtype=torch.float32)

with torch.no_grad():
    clr_fwd = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_fwd).numpy(), 0.0, 5.0)
    clr_inv = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_inv).numpy(), 0.0, 5.0)

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

print(f"\nTOTAL PASSES: {passes}/20 | Mean R2={np.mean(r2_list):.4f}, Mean Margin={np.mean(margin_list):.3f}")
