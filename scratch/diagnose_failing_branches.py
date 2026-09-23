import sys
import json
import math
from pathlib import Path
import numpy as np

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scratch.fast_eval_branches import true_poses_list, branches, unroll_poses_param

p_init = [0.0190, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]

failing = [4, 5, 7, 8, 12, 15]

for b_idx in failing:
    b_name = branches[b_idx]['name']
    u_seq = branches[b_idx]['actions']
    true_p = true_poses_list[b_idx]
    pred_p = np.array(unroll_poses_param(u_seq, p_init))
    
    print(f"\n==================== {b_name} (Branch {b_idx}) ====================")
    u_fwd_arr = [0.5*(u[0]+u[1]) for u in u_seq]
    u_diff_arr = [(u[1]-u[0]) for u in u_seq]
    print(f"u_fwd: min={min(u_fwd_arr):.2f}, max={max(u_fwd_arr):.2f}")
    print(f"u_diff: min={min(u_diff_arr):.2f}, max={max(u_diff_arr):.2f}")
    print(f"Step | True X     Y    Yaw(deg) | Pred X     Y    Yaw(deg) | Error: pos(m), yaw(deg)")
    for step in range(len(u_seq)):
        tx, ty, tyaw = true_p[step]
        px, py, pyaw = pred_p[step]
        pos_err = math.sqrt((tx-px)**2 + (ty-py)**2)
        yaw_err = abs((tyaw - pyaw + math.pi) % (2*math.pi) - math.pi) * 180.0 / math.pi
        print(f"{step:4d} | {tx:6.2f} {ty:6.2f} {tyaw*180/math.pi:7.1f} | {px:6.2f} {py:6.2f} {pyaw*180/math.pi:7.1f} | pos={pos_err:5.2f}m, yaw={yaw_err:5.1f}d")
