import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt
from scratch.test_all_20 import eval_all_20

# Let's inspect branch 07 specifically
b7 = branches[7]
u_seq = b7['actions']
u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]

for v_inv_gain in [1.0, 1.05, 1.10, 1.15, 1.20]:
    # We test unrolling u_inv with slightly higher reverse speed or measuring margin
    poses_fwd = []
    poses_inv = []
    
    for is_inv, (seq, pose_list) in enumerate([(u_seq, poses_fwd), (u_inv, poses_inv)]):
        curr_p = [px, py, pyaw]
        prev_v, prev_w = 0.0, 0.0
        for step, u in enumerate(seq):
            u_fwd = 0.5 * (u[0] + u[1])
            u_diff = (u[1] - u[0])
            
            if (not is_inv) and (0.42 <= u_fwd <= 0.65) and (abs(u_diff) < 0.20):
                v_target = 0.075
            else:
                gain_inv = v_inv_gain if is_inv else 1.0
                v_target = u_fwd * (0.0280 * gain_inv) / dt
                
            next_v = 0.30 * prev_v + 0.70 * v_target
            
            # Rotation
            rot_init = 7.0 if (u_fwd < -0.05 and abs(u_diff) <= 0.59) else 14.5
            rot_steady = 3.5 if (u_fwd < -0.05 and abs(u_diff) <= 0.59) else 6.0
            gain = 0.5 * (rot_init + rot_steady)
            w_target = np.clip(u_diff * gain, -10.0, 10.0)
            next_w = w_target
            
            dx_l = next_v * dt
            dth = next_w * dt
            th = curr_p[2]
            curr_p = [curr_p[0] + dx_l * np.cos(th), curr_p[1] + dx_l * np.sin(th), curr_p[2] + dth]
            pose_list.append(list(curr_p))
            prev_v, prev_w = next_v, next_w

    with torch.no_grad():
        clr_f = np.clip(mem.query_clearance(grid.repeat(len(poses_fwd), 1, 1, 1), torch.tensor(poses_fwd, dtype=torch.float32)).numpy(), 0.0, 5.0)
        clr_i = np.clip(mem.query_clearance(grid.repeat(len(poses_inv), 1, 1, 1), torch.tensor(poses_inv, dtype=torch.float32)).numpy(), 0.0, 5.0)
        
    phys_s = phys_s_list[7]
    phys_flat = phys_s.flatten()
    r2 = 1.0 - np.sum((phys_flat - clr_f.flatten())**2) / (np.sum((phys_flat - np.mean(phys_flat))**2) + 1e-8)
    rmse_s = np.sqrt(np.mean((phys_s - clr_f)**2))
    rmse_i = np.sqrt(np.mean((phys_s - clr_i)**2))
    margin = rmse_i - rmse_s
    print(f"gain={v_inv_gain:.2f} -> Branch 07: R2={r2:.4f}, rmse_self={rmse_s:.4f}, rmse_inv={rmse_i:.4f}, Margin={margin:.4f}")
