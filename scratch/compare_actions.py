import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

with open("scratch/run_all_eval.py") as f:
    f1 = f.read()
with open("scratch/test_k_fwd_margin.py") as f:
    f2 = f.read()

# Let's see what actions are in branches 4, 8, 11, 12
from scratch.fast_eval_branches import branches

for idx in [4, 5, 7, 8, 11, 12, 15]:
    b = branches[idx]
    actions = np.array(b['actions'])
    u_fwds = 0.5 * (actions[:, 0] + actions[:, 1])
    u_diffs = actions[:, 1] - actions[:, 0]
    print(f"Branch {idx:02d} ({b['name'][:18]:18s}): N={len(actions):2d}, mean_fwd={np.mean(u_fwds):.2f}, min_fwd={np.min(u_fwds):.2f}, mean_diff={np.mean(u_diffs):.2f}")
