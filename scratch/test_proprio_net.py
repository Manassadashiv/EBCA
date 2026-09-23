import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

d = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S = torch.from_numpy(d['S']).float()
U = torch.from_numpy(d['U']).float()

# Gyro yaw is S[:, :, 20] (channel 5 of s_body)
gyro_yaw = S[:, 150:160, 20] # (20, 10)
u_fwd = 0.5 * (U[:, 150:160, 0] + U[:, 150:160, 1])
u_diff = U[:, 150:160, 1] - U[:, 150:160, 0]

print("Gyro yaw mean:", gyro_yaw.mean().item(), "std:", gyro_yaw.std().item())
print("Correlation between u_diff and gyro_yaw:", np.corrcoef(u_diff.numpy().flatten(), gyro_yaw.numpy().flatten())[0, 1])

# Train a 1-layer linear / GRU predictor of gyro_yaw and joints from (s_0, u_seq)
class BodyProprioNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(6, 64, batch_first=True)
        self.head_gyro = nn.Linear(64, 1)
        self.head_joints = nn.Linear(64, 3)
    def forward(self, u_seq):
        feat, _ = self.gru(u_seq)
        pred_gyro = self.head_gyro(feat)
        pred_joints = self.head_joints(feat)
        return pred_gyro.squeeze(-1), pred_joints

d_train = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
S_tr = torch.from_numpy(d_train['S']).float()
U_tr = torch.from_numpy(d_train['U']).float()

# Extract H=10 slices from DEV_TRAIN
train_u = []
train_gyro = []
train_joints = []
for ep in range(60):
    for t in range(0, 390, 10):
        train_u.append(U_tr[ep, t:t+10])
        train_gyro.append(S_tr[ep, t:t+10, 20])
        train_joints.append(S_tr[ep, t:t+10, 21:24])

train_u = torch.stack(train_u)
train_gyro = torch.stack(train_gyro)
train_joints = torch.stack(train_joints)

net = BodyProprioNet()
opt = torch.optim.Adam(net.parameters(), lr=3e-3)
for ep in range(100):
    opt.zero_grad()
    pg, pj = net(train_u)
    loss = F.mse_loss(pg, train_gyro) + 10.0 * F.mse_loss(pj, train_joints)
    loss.backward()
    opt.step()

with torch.no_grad():
    val_pg, val_pj = net(U[:, 150:160, :])
    true_g = gyro_yaw.numpy().flatten()
    pred_g = val_pg.numpy().flatten()
    r2_g = 1.0 - np.sum((true_g - pred_g)**2) / (np.sum((true_g - np.mean(true_g))**2) + 1e-8)
    
    true_j = S[:, 150:160, 21:24].numpy().flatten()
    pred_j = val_pj.numpy().flatten()
    r2_j = 1.0 - np.sum((true_j - pred_j)**2) / (np.sum((true_j - np.mean(true_j))**2) + 1e-8)

print(f"ProprioNet Validation: Gyro R2 = {r2_g:.4f}, Joints R2 = {r2_j:.4f}")
