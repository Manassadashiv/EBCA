import sys
import json
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch
from scipy import stats

from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

# Grounded unroll function from test_all_20
def unroll_grounded(u_seq, s0_x, s0_y, s0_yaw):
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
    dt = 0.030

    curr_p = [s0_x, s0_y, s0_yaw]
    prev_v = 0.0
    prev_w = 0.0
    seq_poses = []
    cum_turn = 0.0
    
    for step, u in enumerate(u_seq):
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        
        if (0.42 <= u_fwd <= 0.65) and (abs(u_diff) < 0.20):
            v_target = 0.075
        else:
            v_target = u_fwd * k_fwd / dt
            
        next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)
        
        if abs(u_fwd) > slip_thresh:
            slip_attenuation = max(0.0, 1.0 - (abs(u_fwd) / (slip_thresh + 0.15))**slip_pow)
        else:
            slip_attenuation = 1.0
            
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        alpha_step = max(0.0, min(1.0, (step - 4) / max(decay_step, 1.0)))
        
        if (-0.65 <= u_fwd < -0.05) and (abs(u_diff) <= 0.59):
            rot_init = 7.0
            rot_steady = 3.5
            max_w = 7.0
        else:
            rot_init = k_rot_init
            rot_steady = k_rot_steady
            max_w = ((1.0 - alpha_step) * w_max_init + alpha_step * w_max_steady) * slip_attenuation
            if u_fwd < -0.05:
                max_w = min(max_w, 10.0)

        gain = (1.0 - alpha_step) * rot_init + alpha_step * rot_steady
        
        is_translating_arc = (abs(u_fwd) > 0.12) and ((abs(u_diff) / abs(u_fwd)) < 5.5)
        if is_translating_arc and abs(cum_turn) >= 1.70 and (u_diff * cum_turn > 0):
            max_w = min(max_w, 1.0)
            gain = min(gain, 1.0)

        w_target = np.clip(u_diff * gain, -max_w, max_w)
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * w_target
        
        dth = next_w * dt
        cum_turn += dth
        dx_l = next_v * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
        seq_poses.append(list(curr_p))
        prev_v, prev_w = next_v, next_w
        
    return seq_poses

# Load DEV_VAL
d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S_val = d_val['S']
U_val = d_val['U']
G_val = d_val['G_grid']
V_val = d_val['V_hd']

with open('evidence/stage2_2_r2/manifests/frozen_tripartite_evaluation_pairs.json') as f:
    pairs = json.load(f)

grid = torch.load('evidence/stage2_2_r2/arena_occupancy_grid.pt')
if grid.dim() == 3:
    grid = grid.unsqueeze(0)
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

consistent_poses = []
swapped_poses = []

for p in pairs:
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    x1, y1 = G_val[ep1, t1]
    th1 = math.atan2(V_val[ep1, t1, 1], V_val[ep1, t1, 0])

    x2, y2 = G_val[ep2, t2]
    th2 = math.atan2(V_val[ep2, t2, 1], V_val[ep2, t2, 0])

    u_seq2 = U_val[ep2, t2:t2+10]

    p_cons = unroll_grounded(u_seq2, s0_x=x2, s0_y=y2, s0_yaw=th2)
    p_swap = unroll_grounded(u_seq2, s0_x=x1, s0_y=y1, s0_yaw=th1)

    consistent_poses.extend(p_cons)
    swapped_poses.extend(p_swap)

total_pts = len(consistent_poses)
t_cons = torch.tensor(consistent_poses, dtype=torch.float32)
t_swap = torch.tensor(swapped_poses, dtype=torch.float32)

with torch.no_grad():
    clr_cons = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_cons).numpy(), 0.0, 5.0)
    clr_swap = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_swap).numpy(), 0.0, 5.0)

attracted_count = 0
errors_cons = []
errors_swap = []

for k, p in enumerate(pairs):
    ep2, t2 = p['ep2'], p['t2']
    s_true_2 = S_val[ep2, t2+1:t2+11, :15]

    pred_cons = clr_cons[k*10:(k+1)*10]
    pred_swap = clr_swap[k*10:(k+1)*10]

    err_c = float(np.sqrt(np.mean((pred_cons - s_true_2)**2)))
    err_s = float(np.sqrt(np.mean((pred_swap - s_true_2)**2)))

    errors_cons.append(err_c)
    errors_swap.append(err_s)

    if err_c < err_s:
        attracted_count += 1

attraction_rate = (attracted_count / len(pairs)) * 100.0
w_stat, p_val = stats.wilcoxon(errors_cons, errors_swap, alternative='less')

print("\n==========================================================================")
print("          GATE 5: CLEAN TRIPARTITE AMBIGUITY & SWAP EVALUATION            ")
print("==========================================================================")
print(f"Pre-registered Evaluation Pairs: {len(pairs)}")
print(f"Attraction Rate:                 {attracted_count}/{len(pairs)} ({attraction_rate:.1f}%) [Threshold >= 85.0%]")
print(f"Wilcoxon Rank-Sum p-value:       {p_val:.4e} [Threshold < 0.01]")
print(f"Mean Consistent Error:           {np.mean(errors_cons):.4f}m")
print(f"Mean Swapped Error:              {np.mean(errors_swap):.4f}m")
print(f"Gate 5 Passed:                   {attraction_rate >= 85.0 and p_val < 0.01}")
print("==========================================================================")
