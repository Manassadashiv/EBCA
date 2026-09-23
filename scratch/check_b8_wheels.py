import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import branches

b8 = branches[8]
actions = np.array(b8['actions'])
print("Branch 08 wheel commands:")
for s in range(len(actions)):
    print(f"  step {s:2d}: u0={actions[s,0]:.3f}, u1={actions[s,1]:.3f}")
