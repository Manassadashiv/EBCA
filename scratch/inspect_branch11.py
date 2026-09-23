import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import phys_s_list, branches, unroll_poses_param, mem, grid
import torch

idx = 11
b = branches[idx]
u_seq = b['actions']
u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]

params = [0.0280, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]
poses_fwd = unroll_poses_param(u_seq, params)
poses_inv = unroll_poses_param(u_inv, params)

with torch.no_grad():
    clr_fwd = mem.query_clearance(grid.repeat(len(poses_fwd), 1, 1, 1), torch.tensor(poses_fwd, dtype=torch.float32)).numpy()
    clr_inv = mem.query_clearance(grid.repeat(len(poses_inv), 1, 1, 1), torch.tensor(poses_inv, dtype=torch.float32)).numpy()

phys_s = phys_s_list[idx]
print("Branch 11 Clearance comparison:")
print("Phys Sonar shape:", phys_s.shape)
print("Phys Sonar range:", np.min(phys_s), np.max(phys_s))
print("Grid Fwd range:", np.min(clr_fwd), np.max(clr_fwd))

phys_flat = phys_s.flatten()
grid_flat = clr_fwd.flatten()
r2 = 1.0 - np.sum((phys_flat - grid_flat)**2) / (np.sum((phys_flat - np.mean(phys_flat))**2) + 1e-8)
rmse_self = np.sqrt(np.mean((phys_s - clr_fwd)**2))
rmse_inv = np.sqrt(np.mean((phys_s - clr_inv)**2))
margin = rmse_inv - rmse_self
print(f"R2: {r2:.4f}, Margin: {margin:.4f} (Self RMSE: {rmse_self:.4f}, Inv RMSE: {rmse_inv:.4f})")

# Let's inspect each sonar sensor (15 beams) at step 0 and step -1
print("\nStep 0: Phys vs Pred (15 beams):")
print("Phys:", np.round(phys_s[0], 2))
print("Pred:", np.round(clr_fwd[0], 2))

print("\nFinal Step: Phys vs Pred (15 beams):")
print("Phys:", np.round(phys_s[-1], 2))
print("Pred:", np.round(clr_fwd[-1], 2))

# Also compare with true poses:
from scratch.fast_eval_branches import true_poses_list
true_poses = true_poses_list[idx]
with torch.no_grad():
    clr_true = mem.query_clearance(grid.repeat(len(true_poses), 1, 1, 1), torch.tensor(true_poses, dtype=torch.float32)).numpy()
r2_true = 1.0 - np.sum((phys_flat - clr_true.flatten())**2) / (np.sum((phys_flat - np.mean(phys_flat))**2) + 1e-8)
print(f"\nIf queried at TRUE POSES: R2 = {r2_true:.4f}")
