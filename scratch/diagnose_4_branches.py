import sys
import json
import math
from pathlib import Path
import numpy as np

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scratch.fast_eval_branches import true_poses_list, branches, px, py, pyaw, dt

def unroll_branch(u_seq, k_fwd=0.028, k_rot_rev=7.0):
    gamma_v = 0.71
    k_rot_init = 14.5
    k_rot_steady = 6.0
    w_max_init = 15.0
    w_max_steady = 7.4
    decay_step = 2.0
    gamma_w = 0.75
    slip_thresh = 0.38
    slip_pow = 4.0

    curr_p = [px, py, pyaw]
    prev_v = 0.0
    prev_w = 0.0
    seq_poses = []
    for step, u in enumerate(u_seq):
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])

        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        v_targ = u_fwd * k_fwd / dt
        next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_targ)

        if abs(u_fwd) > slip_thresh:
            slip_attenuation = max(0.0, 1.0 - (abs(u_fwd) / (slip_thresh + 0.15))**slip_pow)
        else:
            slip_attenuation = 1.0

        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        alpha_step = max(0.0, min(1.0, (step - 4) / max(decay_step, 1.0)))

        rot_init = k_rot_rev if u_fwd < -0.05 else k_rot_init
        rot_steady = (k_rot_rev * 0.5) if u_fwd < -0.05 else k_rot_steady

        gain = (1.0 - alpha_step) * rot_init + alpha_step * rot_steady
        max_w = ((1.0 - alpha_step) * w_max_init + alpha_step * w_max_steady) * slip_attenuation
        if u_fwd < -0.05:
            max_w = min(max_w, 6.0)

        w_target = np.clip(u_diff * gain, -max_w, max_w)
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * w_target

        dx_l = next_v * dt
        dth = next_w * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * math.cos(th), curr_p[1] + dx_l * math.sin(th), curr_p[2] + dth]
        seq_poses.append(list(curr_p))
        prev_v, prev_w = next_v, next_w

    return seq_poses

for b_idx in [5, 7, 11, 15]:
    b_name = branches[b_idx]['name']
    u_seq = branches[b_idx]['actions']
    true_p = true_poses_list[b_idx]
    pred_p = unroll_branch(u_seq)

    print(f"\n==================== {b_name} (Branch {b_idx}) ====================")
    for s in range(len(u_seq)):
        tx, ty, tyaw = true_p[s]
        px_s, py_s, pyaw_s = pred_p[s]
        pos_err = math.sqrt((tx - px_s)**2 + (ty - py_s)**2)
        yaw_err = abs((tyaw - pyaw_s + math.pi) % (2 * math.pi) - math.pi) * 180.0 / math.pi
        print(f"s={s:2d} | True: [{tx:5.2f}, {ty:5.2f}], yaw={tyaw*180/math.pi:6.1f} | Pred: [{px_s:5.2f}, {py_s:5.2f}], yaw={pyaw_s*180/math.pi:6.1f} | pos_err={pos_err:.3f}m, yaw_err={yaw_err:5.1f}d")
