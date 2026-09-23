import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import phys_s_list, branches, grid, mem, px, py, pyaw, dt

# Let's directly run unroll from test_18_passes and test_all_20 on Branch 07
from scratch.test_18_passes import eval_grounded_18
print("Running test_18_passes on branch 7...")
from scratch.test_all_20 import eval_all_20
print("Running test_all_20 on branch 7...")
