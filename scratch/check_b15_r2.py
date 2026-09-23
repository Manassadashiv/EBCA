import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

b15 = branches[15]
u_seq = b15['actions']
u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]

for cap in [1.60, 1.70, 1.75]:
    for seq, name in [(u_seq, 'fwd'), (u_inv, 'inv')]:
        curr_p = [px, py, pyaw]
        prev_v, prev_w = 0.0, 0.0
        cum_turn = 0.0
        poses = []
        for step, u in enumerate(seq):
            u_fwd = 0.5 * (u[0] + u[1])
            u_diff = (u[1] - u[0])
            v_target = u_fwd * 0.0280 / dt
            next_v = 0.30 * prev_v + 0.70 * v_target
            
            alpha_step = max(0.0, min(1.0, (step - 4) / 2.0))
            gain = (1.0 - alpha_step) * 14.5 + alpha_step * 6.0
            max_w = ((1.0 - alpha_step) * 15.0 + alpha_step * 7.4)
            
            if abs(cum_turn) >= cap and (u_diff * cum_turn > 0):
                max_w = 1.0
                gain = 1.0
                
            w_target = np.clip(u_diff * gain, -max_w, max_w)
            next_w = w_target
            dth = next_w * dt
            cum_turn += dth
            dx_l = next_v * dt
            th = curr_p[2]
            curr_p = [curr_p[0] + dx_l * np.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
            poses.append(list(curr_p))
            prev_v, prev_w = next_v, next_w
        if name == 'fwd':
            poses_fwd = poses
        else:
            poses_inv = poses
            
    with torch.no_grad():
        clr_fwd = np.clip(mem.query_clearance(grid.repeat(len(poses_fwd), 1, 1, 1), torch.tensor(poses_fwd, dtype=torch.float32)).numpy(), 0.0, 5.0)
        clr_inv = np.clip(mem.query_clearance(grid.repeat(len(poses_inv), 1, 1, 1), torch.tensor(poses_inv, dtype=torch.float32)).numpy(), 0.0, 5.0)
        
    phys_s = phys_s_list[15]
    phys_flat = phys_s.flatten()
    grid_flat = clr_fwd.flatten()
    r2 = 1.0 - np.sum((phys_flat - grid_flat)**2) / (np.sum((phys_flat - np.mean(phys_flat))**2) + 1e-8)
    margin = np.sqrt(np.mean((phys_s - clr_inv)**2)) - np.sqrt(np.mean((phys_s - clr_fwd)**2))
    print(f"cap={cap:.2f} -> Branch 15: R2={r2:.4f}, Margin={margin:.4f}")
