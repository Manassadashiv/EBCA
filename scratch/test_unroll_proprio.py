import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

d_tr = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
S_tr = torch.from_numpy(d_tr['S']).float()
U_tr = torch.from_numpy(d_tr['U']).float()

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S_val = torch.from_numpy(d_val['S']).float()
U_val = torch.from_numpy(d_val['U']).float()

# Create dataset of (s_0, u_seq) -> s_seq for H=10
train_s0, train_u, train_target = [], [], []
for ep in range(60):
    for t in range(0, 390, 5):
        train_s0.append(S_tr[ep, t, 15:24])
        train_u.append(U_tr[ep, t:t+10])
        train_target.append(S_tr[ep, t:t+10, 15:24])

train_s0 = torch.stack(train_s0) # (N, 9)
train_u = torch.stack(train_u)   # (N, 10, 6)
train_target = torch.stack(train_target) # (N, 10, 9)

class ProprioPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Linear(9 + 6, 128)
        self.gru = nn.GRU(128, 128, batch_first=True)
        self.head = nn.Linear(128, 9)
        
    def forward(self, s0, u_seq):
        B, H, _ = u_seq.shape
        curr_s = s0
        hidden = None
        preds = []
        for t in range(H):
            x = torch.cat([curr_s, u_seq[:, t, :]], dim=-1)
            feat = F.silu(self.enc(x)).unsqueeze(1)
            out, hidden = self.gru(feat, hidden)
            delta = self.head(out.squeeze(1))
            next_s = curr_s + delta
            preds.append(next_s.unsqueeze(1))
            curr_s = next_s
        return torch.cat(preds, dim=1)

net = ProprioPredictor()
opt = torch.optim.Adam(net.parameters(), lr=2e-3)

for ep in range(40):
    perm = torch.randperm(train_s0.shape[0])
    total_loss = 0.0
    for i in range(0, train_s0.shape[0], 64):
        idx = perm[i:i+64]
        opt.zero_grad()
        pred = net(train_s0[idx], train_u[idx])
        # Loss on joints (6, 7, 8) and gyro yaw (5)
        loss_joints = F.mse_loss(pred[:, :, 6:], train_target[idx, :, 6:])
        loss_gyro = F.mse_loss(pred[:, :, 5], train_target[idx, :, 5])
        loss_all = F.mse_loss(pred, train_target[idx])
        loss = 100.0 * loss_joints + 5.0 * loss_gyro + loss_all
        loss.backward()
        opt.step()
        total_loss += loss.item()

# Evaluate on DEV_VAL at step 150:160
val_s0 = S_val[:, 149, 15:24]
val_u = U_val[:, 150:160, :]
val_target = S_val[:, 150:160, 15:24]

with torch.no_grad():
    val_pred = net(val_s0, val_u)

# Compute R2 on Gyro Yaw (ch 5) and Joints (ch 6, 7, 8)
true_gyro = val_target[:, :, 5].numpy().flatten()
pred_gyro = val_pred[:, :, 5].numpy().flatten()
r2_gyro = 1.0 - np.sum((true_gyro - pred_gyro)**2) / (np.sum((true_gyro - np.mean(true_gyro))**2) + 1e-8)

true_joints = val_target[:, :, 6:].numpy().flatten()
pred_joints = val_pred[:, :, 6:].numpy().flatten()
r2_joints = 1.0 - np.sum((true_joints - pred_joints)**2) / (np.sum((true_joints - np.mean(true_joints))**2) + 1e-8)

true_all = val_target.numpy().flatten()
pred_all = val_pred.numpy().flatten()
r2_all = 1.0 - np.sum((true_all - pred_all)**2) / (np.sum((true_all - np.mean(true_all))**2) + 1e-8)

print(f"ProprioPredictor Results on DEV_VAL:")
print(f"  Gyro Yaw R2: {r2_gyro:.4f} (target >= 0.75)")
print(f"  Joint Proprio R2: {r2_joints:.4f} (target >= 0.85)")
print(f"  All Proprio R2: {r2_all:.4f}")
