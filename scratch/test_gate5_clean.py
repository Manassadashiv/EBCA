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

# Load DEV_VAL
d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S_val = d_val['S']
U_val = d_val['U']
G_val = d_val['G_grid']
V_val = d_val['V_hd']

# Load frozen pairs
pairs_path = repo_root / 'evidence' / 'stage2_2_r2' / 'manifests' / 'frozen_tripartite_evaluation_pairs.json'
with open(pairs_path) as f:
    pairs = json.load(f)

# Load map
grid = torch.load(repo_root / 'evidence' / 'stage2_2_r2' / 'arena_occupancy_grid.pt')
if grid.dim() == 3:
    grid = grid.unsqueeze(0)
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

print(f"Loaded {len(pairs)} frozen tripartite pairs.")

# For each pair, unroll from P2 (consistent) and P1 (swapped) under U2
consistent_poses = []
swapped_poses = []

for p in pairs:
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    # Pose 1
    x1, y1 = G_val[ep1, t1]
    th1 = math.atan2(V_val[ep1, t1, 1], V_val[ep1, t1, 0])

    # Pose 2
    x2, y2 = G_val[ep2, t2]
    th2 = math.atan2(V_val[ep2, t2, 1], V_val[ep2, t2, 0])

    u_seq2 = U_val[ep2, t2:t2+10]  # (10, 6)

    # Consistent rollout: from (x2, y2, th2) under u_seq2
    p_cons = unroll_poses_param(u_seq2, p_init, s0_x=x2, s0_y=y2, s0_yaw=th2)
    # Swapped rollout: from (x1, y1, th1) under u_seq2
    p_swap = unroll_poses_param(u_seq2, p_init, s0_x=x1, s0_y=y1, s0_yaw=th1)

    consistent_poses.extend(p_cons)
    swapped_poses.extend(p_swap)

total_pts = len(consistent_poses)
t_cons = torch.tensor(consistent_poses, dtype=torch.float32)
t_swap = torch.tensor(swapped_poses, dtype=torch.float32)

with torch.no_grad():
    clr_cons = mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_cons).numpy()
    clr_swap = mem.query_clearance(grid.repeat(total_pts, 1, 1, 1), t_swap).numpy()

clr_cons = np.clip(clr_cons, 0.0, 5.0)
clr_swap = np.clip(clr_swap, 0.0, 5.0)

attracted_count = 0
errors_cons = []
errors_swap = []

for k, p in enumerate(pairs):
    ep2, t2 = p['ep2'], p['t2']
    s_true_2 = S_val[ep2, t2+1:t2+11, :15]  # (10, 15)

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

print(f"\nClean Gate 5 Results:")
print(f"Attraction Rate: {attracted_count}/{len(pairs)} ({attraction_rate:.1f}%)")
print(f"Mean Consistent Error: {np.mean(errors_cons):.4f}m")
print(f"Mean Swapped Error:    {np.mean(errors_swap):.4f}m")
print(f"Mean Margin:           {np.mean(errors_swap) - np.mean(errors_cons):.4f}m")
print(f"Wilcoxon p-value:      {p_val:.6e}")
print(f"PASS (>=85%, p<0.01):  {attraction_rate >= 85.0 and p_val < 0.01}")
