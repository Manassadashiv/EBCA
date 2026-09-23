import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import true_poses_list, branches, dt

print(f"Number of branches: {len(branches)}")

# For each branch, compute step-by-step true linear velocity and true angular velocity
records = []
for b_idx in range(len(branches)):
    b = branches[b_idx]
    actions = b['actions']
    true_p = true_poses_list[b_idx]
    
    for s in range(len(actions)):
        u = actions[s]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        
        # True displacement
        if s == 0:
            p_prev = [-1.5, -1.8, -np.radians(45.0)]
        else:
            p_prev = true_p[s-1]
        p_curr = true_p[s]
        
        dx = p_curr[0] - p_prev[0]
        dy = p_curr[1] - p_prev[1]
        th_mid = 0.5 * (p_curr[2] + p_prev[2])
        # Body frame forward dx:
        dx_body = dx * np.cos(th_mid) + dy * np.sin(th_mid)
        v_true = dx_body / dt
        
        # Angular velocity
        dth = p_curr[2] - p_prev[2]
        # wrap dth
        dth = (dth + np.pi) % (2 * np.pi) - np.pi
        w_true = dth / dt
        
        records.append({
            'b_idx': b_idx,
            'step': s,
            'u0': u[0],
            'u1': u[1],
            'u_fwd': u_fwd,
            'u_diff': u_diff,
            'v_true': v_true,
            'w_true': w_true
        })

import pandas as pd
df = pd.DataFrame(records)
print("Total transition steps:", len(df))
print("\nCorrelation with v_true:")
print(df[['u_fwd', 'v_true']].corr())
print("\nCorrelation with w_true:")
print(df[['u_diff', 'w_true']].corr())

# Let's see w_true vs u_diff
df['u_diff_round'] = df['u_diff'].round(1)
print("\nMean w_true by u_diff:")
print(df.groupby('u_diff_round')[['w_true', 'v_true']].mean().head(15))
