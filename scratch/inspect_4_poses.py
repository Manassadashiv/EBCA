import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

from scratch.fast_eval_branches import true_poses_list, branches
import numpy as np

for i in [5, 7, 11, 15]:
    p = true_poses_list[i]
    print(f"\nBranch {i:02d} ({branches[i]['name']}):")
    for s in range(len(p)):
        yaw_deg = p[s, 2] * 180.0 / np.pi
        print(f"  step {s:2d}: pos=[{p[s,0]:.3f}, {p[s,1]:.3f}], yaw={yaw_deg:6.1f} deg")
