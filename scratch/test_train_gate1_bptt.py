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

# Subsequences of length 10
sub_s0, sub_u, sub_target_gyro, sub_target_joints = [], [], [], []
for ep in range(60):
    for t in range(0, 385, 5):
        sub_s0.append(S_tr[ep, t, 15:24])
        sub_u.append(U_tr[ep, t:t+10])
        sub_target_gyro.append(S_tr[ep, t:t+10, 20])
        sub_target_joints.append(S_tr[ep, t:t+10, 21:24])

sub_s0 = torch.stack(sub_s0)
sub_u = torch.stack(sub_u)
sub_target_gyro = torch.stack(sub_target_gyro)
sub_target_joints = torch.stack(sub_target_joints)

class Gate1Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Linear(9 + 6, 128)
        self.gru = nn.GRU(128, 128, batch_first=True)
        self.head_gyro = nn.Linear(128, 1)
        self.head_joints = nn.Linear(128, 3)
        self.head_all = nn.Linear(128, 9)
        
    def forward(self, s0, u_seq):
        B, H, _ = u_seq.shape
        curr_s = s0
        hidden = None
        all_s = []
        for t in range(H):
            inp = torch.cat([curr_s, u_seq[:, t, :]], dim=-1)
            feat = F.silu(self.enc(inp)).unsqueeze(1)
            out, hidden = self.gru(feat, hidden)
            delta = self.head_all(out.squeeze(1))
            next_s = curr_s + delta
            all_s.append(next_s.unsqueeze(1))
            curr_s = next_s
        return torch.cat(all_s, dim=1)

model = Gate1Model()
opt = torch.optim.Adam(model.parameters(), lr=3e-3)

for ep in range(50):
    perm = torch.randperm(sub_s0.shape[0])
    total_loss = 0.0
    for i in range(0, sub_s0.shape[0], 64):
        idx = perm[i:i+64]
        opt.zero_grad()
        pred_s = model(sub_s0[idx], sub_u[idx])
        loss_g = F.mse_loss(pred_s[:, :, 5], sub_target_gyro[idx])
        loss_j = F.mse_loss(pred_s[:, :, 6:], sub_target_joints[idx])
        loss = 5.0 * loss_g + 50.0 * loss_j
        loss.backward()
        opt.step()
        total_loss += loss.item()

# Evaluate on DEV_VAL at step 150:160
val_s0 = S_val[:, 149, 15:24]
val_u = U_val[:, 150:160, :]
val_target = S_val[:, 150:160, 15:24]

with torch.no_grad():
    val_pred = model(val_s0, val_u)

true_gyro = val_target[:, :, 5].numpy().flatten()
pred_gyro = val_pred[:, :, 5].numpy().flatten()
r2_gyro = 1.0 - np.sum((true_gyro - pred_gyro)**2) / (np.sum((true_gyro - np.mean(true_gyro))**2) + 1e-8)

true_joints = val_target[:, :, 6:].numpy().flatten()
pred_joints = val_pred[:, :, 6:].numpy().flatten()
r2_joints = 1.0 - np.sum((true_joints - pred_joints)**2) / (np.sum((true_joints - np.mean(true_joints))**2) + 1e-8)

print(f"Gate 1 Evaluation on DEV_VAL:")
print(f"  Gyro Yaw R2: {r2_gyro:.4f} (target >= 0.75)")
print(f"  Joints Proprio R2: {r2_joints:.4f} (target >= 0.85)")
