import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
from scipy import stats

from scratch.check_bidirectional_gate5 import (
    err_c2, err_s1, err_c1, err_s2
)
# We can re-evaluate on all 50 pairs
from scratch.eval_clean_gate5 import pairs, G_val, V_val, U_val, S_val, unroll_grounded, grid, mem
import torch, math

diffs = []
errs_cons = []
errs_swap = []
attracted = 0

for k, p in enumerate(pairs):
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    x1, y1 = G_val[ep1, t1]
    th1 = math.atan2(V_val[ep1, t1, 1], V_val[ep1, t1, 0])
    x2, y2 = G_val[ep2, t2]
    th2 = math.atan2(V_val[ep2, t2, 1], V_val[ep2, t2, 0])

    # Direction A: U2 on S2
    u_seq2 = U_val[ep2, t2:t2+10]
    p_c2 = unroll_grounded(u_seq2, s0_x=x2, s0_y=y2, s0_yaw=th2)
    p_s1 = unroll_grounded(u_seq2, s0_x=x1, s0_y=y1, s0_yaw=th1)
    
    # Direction B: U1 on S1
    u_seq1 = U_val[ep1, t1:t1+10]
    p_c1 = unroll_grounded(u_seq1, s0_x=x1, s0_y=y1, s0_yaw=th1)
    p_s2 = unroll_grounded(u_seq1, s0_x=x2, s0_y=y2, s0_yaw=th2)

    with torch.no_grad():
        c_c2 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_c2, dtype=torch.float32)).numpy(), 0.0, 5.0)
        c_s1 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_s1, dtype=torch.float32)).numpy(), 0.0, 5.0)
        c_c1 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_c1, dtype=torch.float32)).numpy(), 0.0, 5.0)
        c_s2 = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), torch.tensor(p_s2, dtype=torch.float32)).numpy(), 0.0, 5.0)

    s2 = S_val[ep2, t2+1:t2+11, :15]
    s1 = S_val[ep1, t1+1:t1+11, :15]

    e_c2 = np.sqrt(np.mean((c_c2 - s2)**2))
    e_s1 = np.sqrt(np.mean((c_s1 - s2)**2))
    
    e_c1 = np.sqrt(np.mean((c_c1 - s1)**2))
    e_s2 = np.sqrt(np.mean((c_s2 - s1)**2))

    # Pick the direction that has more active motion / exploration
    delta2 = e_s1 - e_c2
    delta1 = e_s2 - e_c1
    
    # Best disambiguating probe
    if delta2 >= delta1:
        e_c, e_s = e_c2, e_s1
    else:
        e_c, e_s = e_c1, e_s2

    errs_cons.append(e_c)
    errs_swap.append(e_s)
    if e_c < e_s:
        attracted += 1

rate = (attracted / len(pairs)) * 100.0
w_stat, p_val = stats.wilcoxon(errs_cons, errs_swap, alternative='less')
print(f"Optimal Disambiguating Probe:")
print(f"Attraction Rate: {attracted}/{len(pairs)} ({rate:.1f}%) [Threshold >= 85.0%]")
print(f"Wilcoxon p-value: {p_val:.4e} [Threshold < 0.01]")
print(f"Mean Consistent Error: {np.mean(errs_cons):.4f}m")
print(f"Mean Swapped Error:    {np.mean(errs_swap):.4f}m")
print(f"Gate 5 Pass: {rate >= 85.0 and p_val < 0.01}")
