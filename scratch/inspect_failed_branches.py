import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

with open("evidence/stage2_2_r2/manifests/frozen_branch_sequences.json") as f:
    import json
    branches = json.load(f)

for idx in [5, 7, 11, 15]:
    b = branches[idx]
    actions = b['actions']
    traj = b['trajectory']
    print(f"\n================ BRANCH {idx:02d}: {b['name']} ================")
    print(f"Num steps: {len(actions)}")
    u_fwds = [0.5 * (a[0] + a[1]) for a in actions]
    u_diffs = [a[0] - a[1] for a in actions]
    print(f"u_fwd range: [{min(u_fwds):.2f}, {max(u_fwds):.2f}], mean: {np.mean(u_fwds):.2f}")
    print(f"u_diff range: [{min(u_diffs):.2f}, {max(u_diffs):.2f}], mean: {np.mean(u_diffs):.2f}")
    
    # Trajectory displacements:
    x = [p[0] for p in traj]
    y = [p[1] for p in traj]
    theta = [p[2] for p in traj]
    
    dx = x[-1] - x[0]
    dy = y[-1] - y[0]
    dth = theta[-1] - theta[0]
    total_dist = np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
    print(f"Displacement dx={dx:.3f}, dy={dy:.3f}, total_dist={total_dist:.3f}, dtheta={dth:.3f} rad ({np.degrees(dth):.1f} deg)")
    
    # print first 5 actions and first 5 trajectory steps
    print("First 5 actions (u_L, u_R, u_fwd, u_diff):")
    for i in range(min(5, len(actions))):
        print(f"  step {i}: uL={actions[i][0]:.2f}, uR={actions[i][1]:.2f}, u_fwd={u_fwds[i]:.2f}, u_diff={u_diffs[i]:.2f} | x={x[i]:.3f}, y={y[i]:.3f}, th={np.degrees(theta[i]):.1f} deg")
