import sys
sys.path.insert(0, '.')
import json
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_body_model import KinematicBodyModel

# Load DEV_TRAIN
d_train = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
S = torch.from_numpy(d_train['S']).float()
U = torch.from_numpy(d_train['U']).float()
G = torch.from_numpy(d_train['G_grid']).float()
V = torch.from_numpy(d_train['V_hd']).float()

num_eps, T, _ = S.shape

# Compute physical target_dp
theta_hd = torch.atan2(V[:, :, 1], V[:, :, 0])
dtheta = torch.diff(theta_hd, dim=1)
dtheta = (dtheta + math.pi) % (2 * math.pi) - math.pi

dG = torch.diff(G, dim=1)
cos_th = torch.cos(theta_hd[:, :-1])
sin_th = torch.sin(theta_hd[:, :-1])
dx_local = dG[:, :, 0] * cos_th + dG[:, :, 1] * sin_th
dy_local = -dG[:, :, 0] * sin_th + dG[:, :, 1] * cos_th
target_dp = torch.stack([dx_local, dy_local, dtheta], dim=-1) # (60, 399, 3)

s_body = S[:, :, 15:24] # (60, 400, 9)

# Extract subsequences of length 10
sub_s0, sub_u, sub_dp, sub_s_target = [], [], [], []
for ep in range(num_eps):
    for t in range(0, 380, 10):
        sub_s0.append(s_body[ep, t])
        sub_u.append(U[ep, t:t+10])
        sub_dp.append(target_dp[ep, t:t+10])
        sub_s_target.append(s_body[ep, t+1:t+11])

sub_s0 = torch.stack(sub_s0) # (N, 9)
sub_u = torch.stack(sub_u)   # (N, 10, 6)
sub_dp = torch.stack(sub_dp) # (N, 10, 3)
sub_s_target = torch.stack(sub_s_target) # (N, 10, 9)

print(f"Dataset prepared: {sub_s0.shape[0]} sequences of length 10")

body_model = KinematicBodyModel()
opt = torch.optim.Adam(body_model.parameters(), lr=2e-3)

for ep in range(30):
    perm = torch.randperm(sub_s0.shape[0])
    total_loss = 0.0
    for i in range(0, sub_s0.shape[0], 64):
        idx = perm[i:i+64]
        opt.zero_grad()
        s_pred, dp_pred, _ = body_model.unroll(sub_s0[idx], sub_u[idx])
        loss_dp = F.mse_loss(dp_pred, sub_dp[idx])
        loss_gyro = F.mse_loss(s_pred[:, :, 5], sub_s_target[idx, :, 5])
        loss_joints = F.mse_loss(s_pred[:, :, 6:], sub_s_target[idx, :, 6:])
        loss = 10.0 * loss_dp + 1.0 * loss_gyro + 10.0 * loss_joints
        loss.backward()
        opt.step()
        total_loss += loss.item()
    if (ep + 1) % 10 == 0:
        print(f"Epoch {ep+1}/30: loss_dp={loss_dp.item():.6f}, loss_gyro={loss_gyro.item():.6f}, loss_joints={loss_joints.item():.6f}")

# Test on 20 frozen branches
with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
s0_pos = [-2.00, -1.60]
s0_yaw = 67.5 * math.pi / 180.0
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()
s0_body = torch.tensor(hal.read_sensors()[15:24]).unsqueeze(0).float()
pose_0 = torch.tensor([[s0_pos[0], s0_pos[1], s0_yaw]]).float()

print("\n=== EVALUATING BODY MODEL ON 20 BRANCHES ===")
pos_errors, yaw_errors = [], []
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
    
    u_b_t = torch.tensor(u_seq).unsqueeze(0).float()
    with torch.no_grad():
        _, _, rel_poses = body_model.unroll(s0_body, u_b_t)
        pred_poses = []
        for step in range(H):
            dx_rel = rel_poses[0, step, 0].item()
            dy_rel = rel_poses[0, step, 1].item()
            dtheta_rel = rel_poses[0, step, 2].item()
            th_0 = pose_0[0, 2].item()
            abs_x = pose_0[0, 0].item() + dx_rel * math.cos(th_0) - dy_rel * math.sin(th_0)
            abs_y = pose_0[0, 1].item() + dx_rel * math.sin(th_0) + dy_rel * math.cos(th_0)
            abs_th = pose_0[0, 2].item() + dtheta_rel
            pred_poses.append([abs_x, abs_y, abs_th])
    pred_poses = np.array(pred_poses)
    
    final_pos_err = np.sqrt((phys_poses[-1, 0] - pred_poses[-1, 0])**2 + (phys_poses[-1, 1] - pred_poses[-1, 1])**2)
    final_yaw_err = np.abs((phys_poses[-1, 2] - pred_poses[-1, 2] + np.pi) % (2*np.pi) - np.pi) * 180 / math.pi
    pos_errors.append(final_pos_err)
    yaw_errors.append(final_yaw_err)
    name = branches[b]['name']
    print(f"Branch {b:02d} ({name:22s}): final_pos_err={final_pos_err:.3f}m, final_yaw_err={final_yaw_err:.1f} deg")

print(f"\nMean final position error: {np.mean(pos_errors):.3f}m")
print(f"Mean final yaw error: {np.mean(yaw_errors):.1f} deg")
