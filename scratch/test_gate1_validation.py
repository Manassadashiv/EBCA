import sys
sys.path.insert(0, '.')
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from brain.carl_stage2_2_r2_body_model import KinematicBodyModel

d_train = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
S_tr = torch.from_numpy(d_train['S']).float()
U_tr = torch.from_numpy(d_train['U']).float()
G_tr = torch.from_numpy(d_train['G_grid']).float()
V_tr = torch.from_numpy(d_train['V_hd']).float()

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S_val = torch.from_numpy(d_val['S']).float()
U_val = torch.from_numpy(d_val['U']).float()

# Prepare training subsequences
sub_s0, sub_u, sub_target_s = [], [], []
for ep in range(60):
    for t in range(0, 380, 8):
        sub_s0.append(S_tr[ep, t, 15:24])
        sub_u.append(U_tr[ep, t:t+10])
        sub_target_s.append(S_tr[ep, t+1:t+11, 15:24])

sub_s0 = torch.stack(sub_s0)
sub_u = torch.stack(sub_u)
sub_target_s = torch.stack(sub_target_s)

bm = KinematicBodyModel()
opt = torch.optim.Adam(bm.parameters(), lr=3e-3)

print("Training KinematicBodyModel with BPTT on DEV_TRAIN...")
for epoch in range(40):
    perm = torch.randperm(sub_s0.shape[0])
    for i in range(0, sub_s0.shape[0], 64):
        idx = perm[i:i+64]
        opt.zero_grad()
        pred_s, _, _ = bm.unroll(sub_s0[idx], sub_u[idx])
        loss_gyro = F.mse_loss(pred_s[:, :, 5], sub_target_s[idx, :, 5])
        loss_joints = F.mse_loss(pred_s[:, :, 6:], sub_target_s[idx, :, 6:])
        loss_accel = F.mse_loss(pred_s[:, :, :3], sub_target_s[idx, :, :3])
        loss = 2.0 * loss_gyro + 100.0 * loss_joints + 0.1 * loss_accel
        loss.backward()
        opt.step()

# Evaluate on DEV_VAL step 150:160
val_s0 = S_val[:, 149, 15:24]
val_u = U_val[:, 150:160, :]
val_target = S_val[:, 150:160, 15:24]

with torch.no_grad():
    val_pred, _, _ = bm.unroll(val_s0, val_u)

true_gyro = val_target[:, :, 5].numpy().flatten()
pred_gyro = val_pred[:, :, 5].numpy().flatten()
r2_gyro = 1.0 - np.sum((true_gyro - pred_gyro)**2) / (np.sum((true_gyro - np.mean(true_gyro))**2) + 1e-8)

true_joints = val_target[:, :, 6:].numpy().flatten()
pred_joints = val_pred[:, :, 6:].numpy().flatten()
r2_joints = 1.0 - np.sum((true_joints - pred_joints)**2) / (np.sum((true_joints - np.mean(true_joints))**2) + 1e-8)

true_all = val_target.numpy().flatten()
pred_all = val_pred.numpy().flatten()
r2_proprio = 1.0 - np.sum((true_all - pred_all)**2) / (np.sum((true_all - np.mean(true_all))**2) + 1e-8)

print(f"\nGate 1 Verification Results on DEV_VAL:")
print(f"  Gyro Yaw R2: {r2_gyro:.4f} (target >= 0.75)")
print(f"  Joints Proprio R2: {r2_joints:.4f} (target >= 0.85)")
print(f"  All Proprio R2: {r2_proprio:.4f} (target >= 0.85)")
