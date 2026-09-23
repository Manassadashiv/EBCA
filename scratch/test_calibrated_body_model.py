import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_body_model import KinematicBodyModel

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Collect data for all actions
rng = np.random.RandomState(42)
all_u, all_dp, all_s = [], [], []

# 1. Include specific canonical actions
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

# 2. Add random action sequences
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

print(f"Dataset shape: U={U_t.shape}, DP={DP_t.shape}, S={S_t.shape}")
print(f"Canonical Left dyaw mean: {DP_t[10:20, :, 2].mean().item()*180/math.pi:.1f} deg/tick")
print(f"Canonical Fwd dx mean: {DP_t[0:10, :, 0].mean().item():.4f} m/tick")
