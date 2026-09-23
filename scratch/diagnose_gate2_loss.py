import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.test_k_fwd_margin import phys_s_list, branches, grid, mem
from scratch.fast_eval_branches import unroll_poses_param

all_fwd = []
lens = []
for b in branches:
    all_fwd.extend(unroll_poses_param(b['actions'], [0.0280, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]))
    lens.append(len(b['actions']))

t_fwd = torch.tensor(all_fwd, dtype=torch.float32)
with torch.no_grad():
    clr = np.clip(mem.query_clearance(grid.repeat(len(all_fwd), 1, 1, 1), t_fwd).numpy(), 0.0, 5.0)

offset = 0
for b_idx, b in enumerate(branches):
    H = lens[b_idx]
    true_s = phys_s_list[b_idx]
    pred_s = clr[offset:offset+H]
    offset += H

    delta_s = np.abs(np.diff(true_s, axis=0))
    dyn_mask = (delta_s >= 0.15)
    t_d = true_s[1:][dyn_mask]
    p_d = pred_s[1:][dyn_mask]
    if len(t_d) > 0:
        mse = np.mean((t_d - p_d)**2)
        r2_d = 1.0 - np.sum((t_d - p_d)**2) / (np.sum((t_d - np.mean(t_d))**2) + 1e-8)
        print(f"Branch {b_idx:02d} ({b['name'][:18]:18s}): N_dyn={len(t_d):2d}, MSE={mse:.4f}, Dynamic R²={r2_d:.4f}")
