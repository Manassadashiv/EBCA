import sys
import json
import math
from pathlib import Path
import numpy as np
import torch

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

print(f"{'Pair':<5} | {'ep1':<3} {'t1':<4} | {'ep2':<3} {'t2':<4} | {'Pos Dist':<8} | {'ErrCons':<8} {'ErrSwap':<8} | {'Margin':<8} | {'Pass'}")

for k in range(len(pairs)):
    p = pairs[k]
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']

    x1, y1 = G_val[ep1, t1]
    th1 = math.atan2(V_val[ep1, t1, 1], V_val[ep1, t1, 0])
    x2, y2 = G_val[ep2, t2]
    th2 = math.atan2(V_val[ep2, t2, 1], V_val[ep2, t2, 0])

    pos_dist = math.sqrt((x1-x2)**2 + (y1-y2)**2)

    u_seq2 = U_val[ep2, t2:t2+10]
    s_true_2 = S_val[ep2, t2+1:t2+11, :15]

    p_cons = unroll_poses_param(u_seq2, p_init, s0_x=x2, s0_y=y2, s0_yaw=th2)
    p_swap = unroll_poses_param(u_seq2, p_init, s0_x=x1, s0_y=y1, s0_yaw=th1)

    t_cons = torch.tensor(p_cons, dtype=torch.float32)
    t_swap = torch.tensor(p_swap, dtype=torch.float32)

    with torch.no_grad():
        c_cons = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), t_cons).numpy(), 0.0, 5.0)
        c_swap = np.clip(mem.query_clearance(grid.repeat(10, 1, 1, 1), t_swap).numpy(), 0.0, 5.0)

    err_c = float(np.sqrt(np.mean((c_cons - s_true_2)**2)))
    err_s = float(np.sqrt(np.mean((c_swap - s_true_2)**2)))
    margin = err_s - err_c
    passed = err_c < err_s

    print(f"{k:<5d} | {ep1:<3d} {t1:<4d} | {ep2:<3d} {t2:<4d} | {pos_dist:<8.2f} | {err_c:<8.3f} {err_s:<8.3f} | {margin:<+8.3f} | {'PASS' if passed else 'FAIL'}")
