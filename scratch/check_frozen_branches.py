import json
import numpy as np

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

for b in branches:
    u = np.array(b['actions'])
    u_fwd = 0.5 * (u[:, 0] + u[:, 1])
    u_turn = u[:, 1] - u[:, 0]
    print(f"Branch {b['branch_id']:2d} ({b['name']:22s}): H={b['horizon']:2d}, mean_fwd={np.mean(u_fwd):+.2f}, mean_turn={np.mean(u_turn):+.2f}")
