import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

d_train = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')

G_tr = d_train['G_grid']
V_tr = d_train['V_hd']
U_tr = d_train['U']
S_tr = d_train['S']

G_va = d_val['G_grid']
V_va = d_val['V_hd']
U_va = d_val['U']
S_va = d_val['S']

# Compute local displacements for train
th_tr = np.arctan2(V_tr[:, :, 1], V_tr[:, :, 0])
dx_g_tr = G_tr[:, 1:, 0] - G_tr[:, :-1, 0]
dy_g_tr = G_tr[:, 1:, 1] - G_tr[:, :-1, 1]
dth_tr = (th_tr[:, 1:] - th_tr[:, :-1] + np.pi) % (2 * np.pi) - np.pi
cos_tr = np.cos(th_tr[:, :-1])
sin_tr = np.sin(th_tr[:, :-1])
dx_l_tr = cos_tr * dx_g_tr + sin_tr * dy_g_tr
dy_l_tr = -sin_tr * dx_g_tr + cos_tr * dy_g_tr

disp_tr = np.stack([dx_l_tr, dy_l_tr, dth_tr], axis=-1)  # (60, 399, 3)

# Compute local displacements for val
th_va = np.arctan2(V_va[:, :, 1], V_va[:, :, 0])
dx_g_va = G_va[:, 1:, 0] - G_va[:, :-1, 0]
dy_g_va = G_va[:, 1:, 1] - G_va[:, :-1, 1]
dth_va = (th_va[:, 1:] - th_va[:, :-1] + np.pi) % (2 * np.pi) - np.pi
cos_va = np.cos(th_va[:, :-1])
sin_va = np.sin(th_va[:, :-1])
dx_l_va = cos_va * dx_g_va + sin_va * dy_g_va
dy_l_va = -sin_va * dx_g_va + cos_va * dy_g_va

disp_va = np.stack([dx_l_va, dy_l_va, dth_va], axis=-1)  # (20, 399, 3)

# Create small recurrent model to predict displacement from actions and previous state
class NeuralKinematics(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(input_size=6, hidden_size=64, num_layers=2, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(64, 64),
            nn.SiLU(),
            nn.Linear(64, 3)
        )
    def forward(self, u_seq):
        out, _ = self.gru(u_seq)
        return self.head(out)

model = NeuralKinematics()
opt = torch.optim.Adam(model.parameters(), lr=3e-3)

u_t = torch.from_numpy(U_tr[:, :-1]).float()
d_t = torch.from_numpy(disp_tr).float()

u_v = torch.from_numpy(U_va[:, :-1]).float()
d_v = torch.from_numpy(disp_va).float()

print("Training neural kinematic displacement predictor on DEV_TRAIN...")
for epoch in range(15):
    opt.zero_grad()
    pred = model(u_t)
    loss = F.mse_loss(pred[:, :, 0], d_t[:, :, 0]) * 100.0 + \
           F.mse_loss(pred[:, :, 1], d_t[:, :, 1]) * 200.0 + \
           F.mse_loss(pred[:, :, 2], d_t[:, :, 2]) * 50.0
    loss.backward()
    opt.step()

    if (epoch + 1) % 5 == 0:
        with torch.no_grad():
            pred_v = model(u_v)
            pv_np = pred_v.numpy()
            dv_np = d_v.numpy()
            r2_dx = 1.0 - np.sum((dv_np[:,:,0] - pv_np[:,:,0])**2) / np.sum((dv_np[:,:,0] - np.mean(dv_np[:,:,0]))**2)
            r2_dth = 1.0 - np.sum((dv_np[:,:,2] - pv_np[:,:,2])**2) / np.sum((dv_np[:,:,2] - np.mean(dv_np[:,:,2]))**2)
            print(f"Epoch {epoch+1:02d} | Val R2_dx={r2_dx:.4f}, Val R2_dth={r2_dth:.4f}")
