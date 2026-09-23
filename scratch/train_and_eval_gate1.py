import sys
sys.path.insert(0, '.')
from pathlib import Path
import json
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from brain.carl_stage2_2_r2_modular_world_model import CARLModularPredictiveWorldModel

dev_train_path = Path("evidence/stage2_2_diag/datasets/DEV_TRAIN.npz")
dev_val_path = Path("evidence/stage2_2_diag/datasets/DEV_VAL.npz")

d_train = np.load(dev_train_path)
S_train = torch.from_numpy(d_train["S"]).float()
U_train = torch.from_numpy(d_train["U"]).float()
G_train = torch.from_numpy(d_train["G_grid"]).float()
V_train = torch.from_numpy(d_train["V_hd"]).float()

d_val = np.load(dev_val_path)
S_val = torch.from_numpy(d_val["S"]).float()
U_val = torch.from_numpy(d_val["U"]).float()

arch1 = CARLModularPredictiveWorldModel()
opt_body = torch.optim.Adam(arch1.body_model.parameters(), lr=2e-3)

# Extract sub-sequences of length 12 for training
num_eps, T, _ = S_train.shape
s_body_all = S_train[:, :, 15:24]

# Prepare training samples
sub_s, sub_u, sub_target_s = [], [], []
for ep in range(num_eps):
    for t_start in range(0, T - 15, 10):
        sub_s.append(s_body_all[ep, t_start:t_start+12])
        sub_u.append(U_train[ep, t_start:t_start+12])

sub_s = torch.stack(sub_s)  # (N, 12, 9)
sub_u = torch.stack(sub_u)  # (N, 12, 6)

print(f"Training body model on {sub_s.shape[0]} sequences of length 12...")

batch_size = 64
for epoch in range(25):
    perm = torch.randperm(sub_s.shape[0])
    total_loss = 0.0
    for i in range(0, sub_s.shape[0], batch_size):
        idx = perm[i:i+batch_size]
        opt_body.zero_grad()
        b_s = sub_s[idx]
        b_u = sub_u[idx]
        pred_s, pred_dp, _ = arch1.body_model.unroll(b_s[:, 0, :], b_u)
        
        # Weighted loss: high weight on gyro (ch 5) and joints (ch 6, 7, 8)
        loss_gyro = F.mse_loss(pred_s[:, :, 5], b_s[:, :, 5])
        loss_joints = F.mse_loss(pred_s[:, :, 6:], b_s[:, :, 6:])
        loss_all_s = F.mse_loss(pred_s, b_s)
        loss = 2.0 * loss_gyro + 5.0 * loss_joints + loss_all_s
        loss.backward()
        opt_body.step()
        total_loss += loss.item()

print(f"Epoch 25 complete, loss={total_loss/(sub_s.shape[0]/batch_size):.4f}")

# Evaluate Gate 1 on DEV_VAL
s_body_val = S_val[:, :, 15:24]
test_u = U_val[:, 150:160, :]
test_body_0 = s_body_val[:, 149, :]
true_future_body = s_body_val[:, 150:160, :]

with torch.no_grad():
    pred_body_traj, _, _ = arch1.body_model.unroll(test_body_0, test_u)

true_gyro = true_future_body[:, :, 5].numpy().flatten()
pred_gyro = pred_body_traj[:, :, 5].numpy().flatten()
r2_gyro = float(1.0 - np.sum((true_gyro - pred_gyro)**2) / (np.sum((true_gyro - np.mean(true_gyro))**2) + 1e-8))

true_proprio_all = true_future_body.numpy().flatten()
pred_proprio_all = pred_body_traj.numpy().flatten()
r2_proprio = float(1.0 - np.sum((true_proprio_all - pred_proprio_all)**2) / (np.sum((true_proprio_all - np.mean(true_proprio_all))**2) + 1e-8))

# Joint proprioception specifically (hip, neck, head)
true_joints = true_future_body[:, :, 6:].numpy().flatten()
pred_joints = pred_body_traj[:, :, 6:].numpy().flatten()
r2_joints = float(1.0 - np.sum((true_joints - pred_joints)**2) / (np.sum((true_joints - np.mean(true_joints))**2) + 1e-8))

print(f"Gate 1 Post-Training:")
print(f"  Gyro Yaw R2: {r2_gyro:.4f} (target >= 0.75)")
print(f"  Joint Proprio R2: {r2_joints:.4f} (target >= 0.85)")
print(f"  All Proprio R2: {r2_proprio:.4f}")
print(f"  Gate 1 Pass: {r2_gyro >= 0.75 and r2_joints >= 0.85}")
