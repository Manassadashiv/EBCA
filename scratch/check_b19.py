import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

# 1. From test_k_fwd_margin
from scratch.test_k_fwd_margin import eval_k_fwd

# Let's run test_k_fwd_margin specifically for branch 19
# We'll print poses and sensor clearance
from scratch.test_k_fwd_margin import unroll_poses_param
b19 = branches[19]
u_seq = b19['actions']
u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]

print("Branch 19 action summary:")
u_fwds = [0.5 * (u[0] + u[1]) for u in u_seq]
u_diffs = [u[1] - u[0] for u in u_seq]
print("u_fwds:", np.round(u_fwds, 2))
print("u_diffs:", np.round(u_diffs, 2))
