import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import true_poses_list, branches, px, py, pyaw

for idx in [4, 5, 7, 8, 11, 12, 15]:
    b = branches[idx]
    true_p = true_poses_list[idx]
    dx = true_p[-1][0] - px
    dy = true_p[-1][1] - py
    dth = np.degrees(true_p[-1][2] - pyaw)
    dth = (dth + 180) % 360 - 180
    print(f"Branch {idx:02d} ({b['name'][:18]:18s}): N={len(b['actions']):2d} | dx={dx:+.3f}, dy={dy:+.3f}, dtheta={dth:+.1f} deg")
