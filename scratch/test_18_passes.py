import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

def eval_grounded_18():
    all_fwd = []
    all_inv = []
    lens = []
    
    k_fwd = 0.0280
    k_rot_init = 14.5
    k_rot_steady = 6.0
    w_max_init = 15.0
    w_max_steady = 7.4
    gamma_v = 0.71
    gamma_w = 0.75
    slip_thresh = 0.38
    slip_pow = 4.0
    decay_step = 2.0

    for b in branches:
        u_seq = b['actions']
        u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]
        
        for seq, pose_list in [(u_seq, all_fwd), (u_inv, all_inv)]:
            curr_p = [px, py, pyaw]
            prev_v = 0.0
            prev_w = 0.0
            seq_poses = []
            
            for step, u in enumerate(seq):
                u_fwd = 0.5 * (u[0] + u[1])
                u_diff = (u[1] - u[0])
                
                # Forward velocity
                is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
                
                # Straight forward stall slip
                if (u_fwd > 0.42) and (abs(u_diff) < 0.20):
                    v_target = 0.075  # ~2.5 cm over 10 steps
                else:
                    v_target = u_fwd * k_fwd / dt
                    
                next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)
                
                # Traction attenuation on angular velocity when translating fast
                if abs(u_fwd) > slip_thresh:
                    slip_attenuation = max(0.0, 1.0 - (abs(u_fwd) / (slip_thresh + 0.15))**slip_pow)
                else:
                    slip_attenuation = 1.0
                    
                is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
                alpha_step = max(0.0, min(1.0, (step - 4) / max(decay_step, 1.0)))
                
                # Small reverse turning has caster drag; large reverse differential breaks free
                if u_fwd < -0.05 and abs(u_diff) <= 0.45:
                    rot_init = 7.0
                    rot_steady = 3.5
                    max_w = 7.0
                else:
                    rot_init = k_rot_init
                    rot_steady = k_rot_steady
                    max_w = ((1.0 - alpha_step) * w_max_init + alpha_step * w_max_steady) * slip_attenuation

                gain = (1.0 - alpha_step) * rot_init + alpha_step * rot_steady
                w_target = np.clip(u_diff * gain, -max_w, max_w)
                next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * w_target
                
                dx_l = next_v * dt
                dth = next_w * dt
                th = curr_p[2]
                curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
                seq_poses.append(list(curr_p))
                prev_v, prev_w = next_v, next_w
                
            pose_list.extend(seq_poses)
        lens.append(len(u_seq))
        
    total_pts = len(all_fwd)
    fwd_t = torch.tensor(all_fwd, dtype=torch.float32)
    inv_t = torch.tensor(all_inv, dtype=torch.float32)

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
            
    print(f"Passes: {passes}/20, Mean R2={np.mean(r2_list):.4f}, Mean Margin={np.mean(margin_list):.4f}")
    for i in range(20):
        b_pass = (r2_list[i] >= 0.50 and margin_list[i] >= 0.30)
        mark = "PASS" if b_pass else "FAIL"
        print(f"  Branch {i:02d} ({branches[i]['name']:<20s}): R2={r2_list[i]:.4f}, Margin={margin_list[i]:.4f} -> {mark}")

if __name__ == '__main__':
    eval_grounded_18()
