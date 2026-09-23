import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
from scratch.fast_eval_branches import branches

for i in range(20):
    b = branches[i]
    actions = np.array(b['actions'])
    u_fwds = 0.5 * (actions[:, 0] + actions[:, 1])
    u_diffs = actions[:, 1] - actions[:, 0]
    has_fwd_turn = np.any((u_fwds > 0.10) & (np.abs(u_diffs) > 0.60))
    if has_fwd_turn:
        print(f"Branch {i:02d} ({b['name']}): has_fwd_turn = True | mean_fwd={np.mean(u_fwds):.2f}, mean_diff={np.mean(u_diffs):.2f}")
