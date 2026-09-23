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

def eval_counter_rot(k_spin=14.2, k_trans=6.5, k_fwd=0.024, decay_step=2.5):
    all_fwd_poses = []
    all_inv_poses = []
    lens = []

    gamma_v = 0.71
    gamma_w = 0.75
    w_max_spin = 14.8
    w_max_trans = 8.5

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

                is_counter = (u[0] * u[1] <= 0.02)
                alpha_step = max(0.0, min(1.0, (step - 3) / max(decay_step, 1.0)))

                if is_counter:
                    # Counter-rotation: high torque spin
                    gain = (1.0 - alpha_step) * k_spin + alpha_step * (k_spin * 0.75)
                    max_w = (1.0 - alpha_step) * w_max_spin + alpha_step * 10.0
                else:
                    # Translation with turning: wheel slip and caster drag
                    gain = (1.0 - alpha_step) * k_trans + alpha_step * (k_trans * 0.70)
                    max_w = (1.0 - alpha_step) * w_max_trans + alpha_step * 6.5

                is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
                w_target = np.clip(u_diff * gain, -max_w, max_w)
                next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.20 * prev_w + 0.80 * w_target)

                dx_l = next_v * dt
                dth = next_w * dt
                th = curr_p[2]
                curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
                seq_poses.append(list(curr_p))
                prev_v, prev_w = next_v, next_w

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

for k_sp in [13.0, 14.0, 15.0]:
    for k_tr in [5.5, 6.5, 7.5]:
        p_cnt, r2s, mars = eval_counter_rot(k_spin=k_sp, k_trans=k_tr)
        print(f"k_spin={k_sp:.1f}, k_trans={k_tr:.1f} -> {p_cnt}/20 passes | Mean R2={np.mean(r2s):.4f}, Mean Margin={np.mean(mars):.3f}")
        if p_cnt >= 16:
            for i in range(20):
                b_pass = (r2s[i] >= 0.50 and mars[i] >= 0.30)
                mark = "PASS" if b_pass else "FAIL"
                print(f"  Branch {i:02d} ({branches[i]['name']:<20s}): R2={r2s[i]:.4f}, Margin={mars[i]:.4f} -> {mark}")
