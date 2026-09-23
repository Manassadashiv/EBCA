import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from brain.carl_stage2_2_r2_body_model import KinematicBodyModel

# Load data collected in scratch/test_calibrated_body_model.py
# Let's recreate data quickly
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

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
    for _ in range(10):
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

for _ in range(80):
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

U_t = torch.tensor(np.array(all_u)).float()
DP_t = torch.tensor(np.array(all_dp)).float()
S_t = torch.tensor(np.array(all_s)).float()

body_model = KinematicBodyModel()
opt_b = torch.optim.Adam(body_model.parameters(), lr=3e-3)

for epoch in range(150):
    opt_b.zero_grad()
    s_pred, dp_pred, _ = body_model.unroll(S_t[:, 0, :], U_t)
    loss_dp = F.mse_loss(dp_pred, DP_t)
    loss_s = F.mse_loss(s_pred, S_t)
    loss = loss_dp + loss_s
    loss.backward()
    opt_b.step()

print(f"Final training loss: dp={loss_dp.item():.6f}, s={loss_s.item():.6f}")

# Check Canonical Left prediction
u_left = torch.tensor([[-0.7, 0.7, 0, 0, 0, 0]] * 10).unsqueeze(0).float()
s0 = S_t[10:11, 0, :]
with torch.no_grad():
    _, dp_p, poses_p = body_model.unroll(s0, u_left)

print("Canonical Left predicted dyaw (deg/tick):", [f"{dp_p[0, i, 2].item()*180/math.pi:.1f}" for i in range(10)])
print("Canonical Left total yaw change (deg):", f"{poses_p[0, -1, 2].item()*180/math.pi:.1f}")

# Compare against true Canonical Left
print("True Canonical Left total yaw change (deg):", f"{DP_t[10, :10, 2].sum().item()*180/math.pi:.1f}")
