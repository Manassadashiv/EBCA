import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import branches

b11 = branches[11]
actions = np.array(b11['actions'])
u_fwd = 0.5 * (actions[:, 0] + actions[:, 1])
u_diff = actions[:, 1] - actions[:, 0]
print("Branch 11 actions:")
for s in range(len(actions)):
    print(f"  step {s:2d}: u0={actions[s,0]:.3f}, u1={actions[s,1]:.3f}, u_fwd={u_fwd[s]:.3f}, u_diff={u_diff[s]:.3f}")
