import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import true_poses_list, branches, px, py, pyaw, dt

# Let's test unrolling Branch 15 with different angle caps
b15 = branches[15]
true_p = np.array(true_poses_list[15])
u_seq = b15['actions']

for cap in [1.5, 1.6, 1.7, 1.8, 1.9, 1.95, 2.0]:
    curr_p = [px, py, pyaw]
    prev_v, prev_w = 0.0, 0.0
    cum_turn = 0.0
    pred = []
    for step, u in enumerate(u_seq):
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        v_target = u_fwd * 0.0280 / dt
        next_v = 0.30 * prev_v + 0.70 * v_target
        
        alpha_step = max(0.0, min(1.0, (step - 4) / 2.0))
        gain = (1.0 - alpha_step) * 14.5 + alpha_step * 6.0
        max_w = ((1.0 - alpha_step) * 15.0 + alpha_step * 7.4)
        
        if abs(cum_turn) >= cap and (u_diff * cum_turn > 0):
            max_w = 1.0
            gain = 1.0
            
        w_target = np.clip(u_diff * gain, -max_w, max_w)
        next_w = w_target
        dth = next_w * dt
        cum_turn += dth
        dx_l = next_v * dt
        th = curr_p[2]
        curr_p = [curr_p[0] + dx_l * np.cos(th), curr_p[1] + dx_l * np.sin(th), curr_p[2] + dth]
        pred.append(list(curr_p))
        prev_v, prev_w = next_v, next_w
        
    pred = np.array(pred)
    err_yaw = np.abs(np.unwrap(true_p[:, 2]) - np.unwrap(pred[:, 2]))
    print(f"cap={cap:.2f} rad -> Max yaw err: {np.degrees(np.max(err_yaw)):.1f}°, Mean yaw err: {np.degrees(np.mean(err_yaw)):.1f}°")
