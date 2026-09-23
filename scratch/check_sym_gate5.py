import sys
import json
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch
from scipy import stats

from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
from scratch.eval_clean_gate5 import unroll_grounded, d_val, S_val, U_val, G_val, V_val, pairs, grid, mem

# Let's compute symmetric tripartite error for all 50 pairs
sym_pass = 0
errs_c = []
errs_s = []

for k, p in enumerate(pairs):
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    x1, y1 = G_val[ep1, t1]
    th1 = math.atan2(V_val[ep1, t1, 1], V_val[ep1, t1, 0])
    x2, y2 = G_val[ep2, t2]
    th2 = math.atan2(V_val[ep2, t2, 1], V_val[ep2, t2, 0])

    # Direction 2: U2
    u_seq2 = U_val[ep2, t2:t2+10]
    p_c2 = unroll_grounded(u_seq2, s0_x=x2, s0_y=y2, s0_yaw=th2)
    p_s1 = unroll_grounded(u_seq2, s0_x=x1, s0_y=y1, s0_yaw=th1)
    
    # Direction 1: U1
    u_seq1 = U_val[ep1, t1:t1+10]
    p_c1 = unroll_grounded(u_seq1, s0_x=x1, s0_y=y1, s0_yaw=th1)
    p_s2 = unroll_grounded(u_seq1, s0_x=x2, s0_y=y2, s0_yaw=th2)

    with torch.no_grad():
        c_c2 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_c2, dtype=torch.float32)).numpy(), 0.0, 5.0)
        c_s1 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_s1, dtype=torch.float32)).numpy(), 0.0, 5.0)
        c_c1 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_c1, dtype=torch.float32)).numpy(), 0.0, 5.0)
        c_s2 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_s2, dtype=torch.float32)).numpy(), 0.0, 5.0)

    s_true_2 = S_val[ep2, t2+1:t2+11, :15]
    s_true_1 = S_val[ep1, t1+1:t1+11, :15]

    err_c2 = float(np.sqrt(np.mean((c_c2 - s_true_2)**2)))
    err_s1 = float(np.sqrt(np.mean((c_s1 - s_true_2)**2)))
    err_c1 = float(np.sqrt(np.mean((c_c1 - s_true_1)**2)))
    err_s2 = float(np.sqrt(np.mean((c_s2 - s_true_1)**2)))

    # Symmetric pair evaluation
    err_c_sym = 0.5 * (err_c1 + err_c2)
    err_s_sym = 0.5 * (err_s1 + err_s2)

    errs_c.append(err_c_sym)
    errs_s.append(err_s_sym)

    if err_c_sym < err_s_sym:
        sym_pass += 1

rate = (sym_pass / len(pairs)) * 100.0
w_stat, p_val = stats.wilcoxon(errs_c, errs_s, alternative='less')
print(f"Symmetric Attraction Rate: {sym_pass}/{len(pairs)} ({rate:.1f}%)")
print(f"Wilcoxon p-value:          {p_val:.4e}")
print(f"Mean Consistent Error:     {np.mean(errs_c):.4f}m")
print(f"Mean Swapped Error:        {np.mean(errs_s):.4f}m")
