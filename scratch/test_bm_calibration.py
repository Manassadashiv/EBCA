import sys
sys.path.insert(0, '.')
import json
import math
import numpy as np
import torch

from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

s0_pos = [-2.00, -1.60]
s0_yaw = 67.5 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
import mujoco
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

print("Testing 2-Phase Friction Decay Kinematic Model:")
final_pos_errs = []
final_yaw_errs = []

for b in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = np.array(branches[b]['actions'])
    H = len(u_seq)
    
    phys_poses = []
    for step in range(H):
        hal.step(u_seq[step])
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw = 2.0 * np.arctan2(qz, qw)
        x = hal.data.qpos[qa]
        y = hal.data.qpos[qa+1]
        phys_poses.append([x, y, yaw])
    phys_poses = np.array(phys_poses)
    
    dt = 0.030
    k_fwd = 0.0125
    gamma_v = 0.70
    gamma_w = 0.75
    
    pred_poses = []
    prev_v = 0.0
    prev_w = 0.0
    curr_pose = [s0_pos[0], s0_pos[1], s0_yaw]
    
    for step in range(H):
        u = u_seq[step]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = (u[1] - u[0])
        
        is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
        v_target = u_fwd * k_fwd / dt
        next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)
        
        is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
        # Friction slip decay from static push (10.7 rad/s per u_diff) to dynamic slip (5.5 rad/s per u_diff)
        w_gain = 5.5 + 5.2 * math.exp(-step / 3.0)
        w_target = u_diff * w_gain
        next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.15 * prev_w + 0.85 * w_target)
        
        dx_local = next_v * dt
        dy_local = 0.0
        dtheta = next_w * dt
        
        th = curr_pose[2]
        dx_g = dx_local * math.cos(th) - dy_local * math.sin(th)
        dy_g = dx_local * math.sin(th) + dy_local * math.cos(th)
        
        curr_pose = [curr_pose[0] + dx_g, curr_pose[1] + dy_g, curr_pose[2] + dtheta]
        pred_poses.append(list(curr_pose))
        prev_v = next_v
        prev_w = next_w
        
    pred_poses = np.array(pred_poses)
    final_pos_err = np.sqrt((phys_poses[-1, 0] - pred_poses[-1, 0])**2 + (phys_poses[-1, 1] - pred_poses[-1, 1])**2)
    final_yaw_err = np.abs((phys_poses[-1, 2] - pred_poses[-1, 2] + np.pi) % (2*np.pi) - np.pi) * 180 / math.pi
    final_pos_errs.append(final_pos_err)
    final_yaw_errs.append(final_yaw_err)
    name = branches[b]['name']
    print(f"Branch {b:02d} ({name:22s}): final_pos_err={final_pos_err:.3f}m, final_yaw_err={final_yaw_err:.1f} deg")

print(f"\nMean final position error: {np.mean(final_pos_errs):.3f}m")
print(f"Mean final yaw error: {np.mean(final_yaw_errs):.1f} deg")
