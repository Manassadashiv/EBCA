import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import branches

for idx in [8, 10, 19]:
    b = branches[idx]
    actions = np.array(b['actions'])
    u_fwd = 0.5 * (actions[:, 0] + actions[:, 1])
    u_diff = actions[:, 1] - actions[:, 0]
    print(f"\nBranch {idx:02d}: {b['name']}")
    for s in range(len(actions)):
        print(f"  step {s:2d}: u_fwd={u_fwd[s]:.3f}, u_diff={u_diff[s]:.3f}")
