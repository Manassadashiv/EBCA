import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt
from scratch.test_refined_chassis import eval_refined

# Let's inspect branch 07 poses and clearance
b7 = branches[7]
u_seq = b7['actions']
u_inv = [[-u[0], -u[1], u[2], u[3], u[4], u[5]] for u in u_seq]

# Let's see self poses vs inv poses
# We'll unroll them and check clearance
with open("scratch/test_refined_chassis.py") as f:
    text = f.read()

# Let's extract unroll logic
print("Branch 07 True Phys Sonar shape:", phys_s_list[7].shape)
