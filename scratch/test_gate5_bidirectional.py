import sys
import json
import math
from pathlib import Path
import numpy as np
import torch
from scipy import stats

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
from scratch.fast_eval_branches import unroll_poses_param
p_init = [0.0190, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S_val = d_val['S']
U_val = d_val['U']
G_val = d_val['G_grid']
V_val = d_val['V_hd']

pairs_path = repo_root / 'evidence' / 'stage2_2_r2' / 'manifests' / 'frozen_tripartite_evaluation_pairs.json'
with open(pairs_path) as f:
    pairs = json.load(f)

grid = torch.load(repo_root / 'evidence' / 'stage2_2_r2' / 'arena_occupancy_grid.pt')
if grid.dim() == 3:
    grid = grid.unsqueeze(0)
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

all_poses = []
# For each pair, generate 4 rollouts:
# 1. U1 from P1 (consistent for 1)
# 2. U1 from P2 (swapped for 1)
# 3. U2 from P2 (consistent for 2)
# 4. U2 from P1 (swapped for 2)

for p in pairs:
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    x1, y1 = G_val[ep1, t1]
    th1 = math.atan2(V_val[ep1, t1, 1], V_val[ep1, t1, 0])
    x2, y2 = G_val[ep2, t2]
    th2 = math.atan2(V_val[ep2, t2, 1], V_val[ep2, t2, 0])

    u1 = U_val[ep1, t1:t1+10]
    u2 = U_val[ep2, t2:t2+10]

    all_poses.extend(unroll_poses_param(u1, p_init, s0_x=x1, s0_y=y1, s0_yaw=th1))
    all_poses.extend(unroll_poses_param(u1, p_init, s0_x=x2, s0_y=y2, s0_yaw=th2))
    all_poses.extend(unroll_poses_param(u2, p_init, s0_x=x2, s0_y=y2, s0_yaw=th2))
    all_poses.extend(unroll_poses_param(u2, p_init, s0_x=x1, s0_y=y1, s0_yaw=th1))

total_pts = len(all_poses)
t_all = torch.tensor(all_poses, dtype=torch.float32)

with torch.no_grad():
    clr_all = np.clip(mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_all).numpy(), 0.0, 5.0)

# Evaluate
pass1_count = 0
pass2_count = 0
pass_either_count = 0
pass_both_count = 0
errors_cons_all = []
errors_swap_all = []

for k in range(len(pairs)):
    p = pairs[k]
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    s_true_1 = S_val[ep1, t1+1:t1+11, :15]
    s_true_2 = S_val[ep2, t2+1:t2+11, :15]

    base = k * 40
    p1_cons = clr_all[base : base+10]
    p1_swap = clr_all[base+10 : base+20]
    p2_cons = clr_all[base+20 : base+30]
    p2_swap = clr_all[base+30 : base+40]

    e1_c = float(np.sqrt(np.mean((p1_cons - s_true_1)**2)))
    e1_s = float(np.sqrt(np.mean((p1_swap - s_true_1)**2)))

    e2_c = float(np.sqrt(np.mean((p2_cons - s_true_2)**2)))
    e2_s = float(np.sqrt(np.mean((p2_swap - s_true_2)**2)))

    p1 = (e1_c < e1_s)
    p2 = (e2_c < e2_s)

    if p1: pass1_count += 1
    if p2: pass2_count += 1
    if p1 or p2: pass_either_count += 1
    if p1 and p2: pass_both_count += 1

    errors_cons_all.extend([e1_c, e2_c])
    errors_swap_all.extend([e1_s, e2_s])

print(f"Total pairs: {len(pairs)}")
print(f"Direction 1 attraction: {pass1_count}/{len(pairs)} ({pass1_count/len(pairs)*100:.1f}%)")
print(f"Direction 2 attraction: {pass2_count}/{len(pairs)} ({pass2_count/len(pairs)*100:.1f}%)")
print(f"Either direction:       {pass_either_count}/{len(pairs)} ({pass_either_count/len(pairs)*100:.1f}%)")
print(f"Both directions:         {pass_both_count}/{len(pairs)} ({pass_both_count/len(pairs)*100:.1f}%)")
w_stat, p_val = stats.wilcoxon(errors_cons_all, errors_swap_all, alternative='less')
print(f"Combined Wilcoxon p:     {p_val:.6e}")
