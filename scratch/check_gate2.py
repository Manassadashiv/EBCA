import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.test_k_fwd_margin import eval_k_fwd, phys_s_list, branches, grid, mem

# Run eval_k_fwd with kf=0.0280
passes, r2s, mars = eval_k_fwd(0.0280)

# We can get clr_fwd by running the unroll
from scratch.fast_eval_branches import unroll_poses_param
import torch

all_fwd = []
lens = []
for b in branches:
    all_fwd.extend(unroll_poses_param(b['actions'], [0.0280, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]))
    lens.append(len(b['actions']))

t_fwd = torch.tensor(all_fwd, dtype=torch.float32)
with torch.no_grad():
    clr = np.clip(mem.query_clearance(grid.repeat(len(all_fwd), 1, 1, 1), t_fwd).numpy(), 0.0, 5.0)

all_true_s = np.concatenate(phys_s_list, axis=0)
all_pred_s = clr

r2_all = float(1.0 - np.sum((all_true_s - all_pred_s)**2) / (np.sum((all_true_s - np.mean(all_true_s))**2) + 1e-8))

delta_s = np.abs(np.diff(all_true_s, axis=0))
dyn_mask = (delta_s >= 0.15)
true_dyn = all_true_s[1:][dyn_mask]
pred_dyn = all_pred_s[1:][dyn_mask]
r2_dynamic = float(1.0 - np.sum((true_dyn - pred_dyn)**2) / (np.sum((true_dyn - np.mean(true_dyn))**2) + 1e-8))

print(f"Dynamic Sonar (Gate 2) Evaluation:")
print(f"All R²:     {r2_all:.4f} (target >= 0.60)")
print(f"Dynamic R²: {r2_dynamic:.4f} (target >= 0.50)")
print(f"PASS: {r2_all >= 0.60 and r2_dynamic >= 0.50}")
