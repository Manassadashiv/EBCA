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

def eval_combined(c_v=1.5, k_fwd=0.0190, gamma_v=0.71, k_rot_init=14.5, k_rot_steady=6.0, w_max_init=15.0, w_max_steady=7.4, decay_step=2.0):
    all_fwd_poses = []
    all_inv_poses = []
    lens = []
    gamma_w = 0.75

    for b_idx in range(len(branches)):
        u_seq = branches[b_idx]['actions']
        u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]

        for seq, pose_list in [(u_seq, all_fwd_poses), (u_inv, all_inv_poses)]:
            curr_p = [px, py, pyaw]
            prev_v = 0.0
            prev_w = 0.0
            seq_poses = []
            for step, u in enumerate(seq):
                u_fwd = 0.5 * (u[0] + u[1])
                u_diff = (u[1] - u[0])

                is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
                v_targ = u_fwd * k_fwd / dt
                next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_targ)

                # Speed-dependent turning attenuation
                slip_atten = 1.0 / (1.0 + c_v * abs(u_fwd))

                is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
                alpha_step = max(0.0, min(1.0, (step - 4) / max(decay_step, 1.0)))
                gain = (1.0 - alpha_step) * k_rot_init + alpha_step * k_rot_steady
                max_w = ((1.0 - alpha_step) * w_max_init + alpha_step * w_max_steady) * slip_atten

                w_targ = np.clip(u_diff * gain * slip_atten, -max_w, max_w)
                next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.25 * prev_w + 0.75 * w_targ)

                dx = next_v * dt * math.cos(curr_p[2])
                dy = next_v * dt * math.sin(curr_p[2])
                dth = next_w * dt
                curr_p = [curr_p[0] + dx, curr_p[1] + dy, curr_p[2] + dth]
                seq_poses.append(list(curr_p))
                prev_v = next_v
                prev_w = next_w

            pose_list.extend(seq_poses)
        lens.append(len(u_seq))

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

        if r2 >= 0.50 and margin >= 0.30:
            passes += 1

    return passes, r2_list, margin_list

for cv_val in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    p_cnt, r2s, mars = eval_combined(c_v=cv_val)
    print(f"c_v={cv_val:.1f} -> {p_cnt}/20 passes | Mean R2={np.mean(r2s):.4f}, Mean Margin={np.mean(mars):.3f}")
