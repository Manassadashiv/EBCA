import sys
sys.path.insert(0, '.')
import json
import math
import numpy as np
import torch
import torch.nn.functional as F
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_body_model import KinematicBodyModel

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Collect training data for body model
rng = np.random.RandomState(42)
all_u, all_dp, all_s = [], [], []

canonical_actions = [
    [0.8, 0.8, 0, 0, 0, 0],
    [-0.7, 0.7, 0, 0, 0, 0],
    [0.7, -0.7, 0, 0, 0, 0],
    [-0.6, -0.6, 0, 0, 0, 0],
    [0.0, 0.0, 0, 0, 0, 0],
]
for act in canonical_actions:
    for _ in range(12):
        hal.reset()
        u_seq, dp_seq, s_seq = [], [], []
        for t in range(12):
            qw0, qz0 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
            yaw0 = 2.0 * np.arctan2(qz0, qw0)
            x0, y0 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
            s_b = hal.read_sensors()[15:24]
            hal.step(np.array(act))
            qw1, qz1 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
            yaw1 = 2.0 * np.arctan2(qz1, qw1)
            x1, y1 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
            dx_g, dy_g = x1 - x0, y1 - y0
            dyaw = (yaw1 - yaw0 + np.pi) % (2*np.pi) - np.pi
            dx_l = dx_g * np.cos(yaw0) + dy_g * np.sin(yaw0)
            dy_l = -dx_g * np.sin(yaw0) + dy_g * np.cos(yaw0)
            u_seq.append(act)
            dp_seq.append([dx_l, dy_l, dyaw])
            s_seq.append(s_b)
        all_u.append(u_seq)
        all_dp.append(dp_seq)
        all_s.append(s_seq)

for _ in range(100):
    hal.reset()
    u_seq, dp_seq, s_seq = [], [], []
    u_base = rng.uniform(-1.0, 1.0, size=6)
    for t in range(12):
        if rng.rand() < 0.2:
            u_base = rng.uniform(-1.0, 1.0, size=6)
        u_t = u_base.copy()
        qw0, qz0 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
        yaw0 = 2.0 * np.arctan2(qz0, qw0)
        x0, y0 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
        s_b = hal.read_sensors()[15:24]
        hal.step(u_t)
        qw1, qz1 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
        yaw1 = 2.0 * np.arctan2(qz1, qw1)
        x1, y1 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
        dx_g, dy_g = x1 - x0, y1 - y0
        dyaw = (yaw1 - yaw0 + np.pi) % (2*np.pi) - np.pi
        dx_l = dx_g * np.cos(yaw0) + dy_g * np.sin(yaw0)
        dy_l = -dx_g * np.sin(yaw0) + dy_g * np.cos(yaw0)
        u_seq.append(u_t)
        dp_seq.append([dx_l, dy_l, dyaw])
        s_seq.append(s_b)
    all_u.append(u_seq)
    all_dp.append(dp_seq)
    all_s.append(s_seq)

body_model = KinematicBodyModel()
opt_b = torch.optim.Adam(body_model.parameters(), lr=3e-3)
U_t = torch.tensor(np.array(all_u)).float()
DP_t = torch.tensor(np.array(all_dp)).float()
S_t = torch.tensor(np.array(all_s)).float()
for epoch in range(150):
    opt_b.zero_grad()
    s_pred, dp_pred, _ = body_model.unroll(S_t[:, 0, :], U_t)
    loss_dp = F.mse_loss(dp_pred, DP_t)
    loss_s = F.mse_loss(s_pred[:, :, 5:], S_t[:, :, 5:])
    loss = loss_dp + 0.1 * loss_s
    loss.backward()
    opt_b.step()

# Now compare unroll vs true MuJoCo trajectory for all 20 branches
s0_pos = [-2.00, -1.60]
s0_yaw = 67.5 * math.pi / 180.0
hal.reset()
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()
s0_body = torch.tensor(hal.read_sensors()[15:24]).unsqueeze(0).float()
pose_0 = torch.tensor([[s0_pos[0], s0_pos[1], s0_yaw]]).float()

print("=== BODY MODEL TRAJECTORY TRACKING VS MUJOCO TRUTH ===")
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
    
    # Body model prediction
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
    
    pos_err = np.sqrt((phys_poses[:, 0] - pred_poses[:, 0])**2 + (phys_poses[:, 1] - pred_poses[:, 1])**2)
    yaw_err = np.abs((phys_poses[:, 2] - pred_poses[:, 2] + np.pi) % (2*np.pi) - np.pi) * 180 / math.pi
    name = branches[b]['name']
    print(f"Branch {b:02d} ({name:22s}): Final pos_err={pos_err[-1]:.3f}m, max_pos_err={np.max(pos_err):.3f}m, final_yaw_err={yaw_err[-1]:.1f} deg, max_yaw_err={np.max(yaw_err):.1f} deg")
