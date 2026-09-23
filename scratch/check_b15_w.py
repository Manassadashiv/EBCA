import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import true_poses_list, branches

b15 = branches[15]
true_p = np.array(true_poses_list[15])
actions = b15['actions']
print("Branch 15 true yaws and step angular velocities:")
for s in range(len(actions)):
    th = true_p[s, 2]
    th_deg = np.degrees(th)
    if s > 0:
        dth = th - true_p[s-1, 2]
        dth = (dth + np.pi) % (2*np.pi) - np.pi
        w = dth / 0.030
        print(f"  step {s:2d}: th={th_deg:6.1f}° | w={w:6.2f} rad/s")
    else:
        print(f"  step {s:2d}: th={th_deg:6.1f}°")
