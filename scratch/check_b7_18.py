import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

# Let's run test_18_passes unroll on branch 07
from scratch.test_18_passes import eval_grounded_18
b7 = branches[7]

# Let's inspect poses from test_18_passes on branch 7
with open("scratch/test_18_passes.py") as f:
    text18 = f.read()

# Let's execute and see margin
