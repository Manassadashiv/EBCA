import numpy as np
import math
from scipy.optimize import minimize

d = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
G = d['G_grid']  # (60, 400, 2)
V = d['V_hd']    # (60, 400, 2)
U = d['U']       # (60, 400, 6)
S = d['S']       # (60, 400, 25)
dt = 0.030

# Extract headings
th = np.arctan2(V[:, :, 1], V[:, :, 0])  # (60, 400)

# Global displacements
dx_g = G[:, 1:, 0] - G[:, :-1, 0]  # (60, 399)
dy_g = G[:, 1:, 1] - G[:, :-1, 1]  # (60, 399)
dth = th[:, 1:] - th[:, :-1]
dth = (dth + np.pi) % (2 * np.pi) - np.pi  # (60, 399)

# Rotate to local frame
cos_th = np.cos(th[:, :-1])
sin_th = np.sin(th[:, :-1])
dx_l = cos_th * dx_g + sin_th * dy_g  # (60, 399)
dy_l = -sin_th * dx_g + cos_th * dy_g # (60, 399)

# Action features
u_fwd = 0.5 * (U[:, :-1, 0] + U[:, :-1, 1])
u_diff = U[:, :-1, 1] - U[:, :-1, 0]

# Flatten
u_fwd_f = u_fwd.flatten()
u_diff_f = u_diff.flatten()
dx_l_f = dx_l.flatten()
dy_l_f = dy_l.flatten()
dth_f = dth.flatten()
w_gyro_f = S[:, 1:, 20].flatten()  # gyro yaw rate

# Filter out collision / stuck steps where motion was blocked
# In normal free motion:
free_mask = (np.abs(u_fwd_f) > 0.05) | (np.abs(u_diff_f) > 0.05)

print(f"Total transitions: {len(u_fwd_f)}, free motion transitions: {np.sum(free_mask)}")

# 1. Fit linear forward gain k_fwd: dx_l = k_fwd * u_fwd
# using least squares
k_fwd_fit = np.linalg.lstsq(u_fwd_f[:, None], dx_l_f, rcond=None)[0][0]
r2_fwd = 1.0 - np.sum((dx_l_f - k_fwd_fit * u_fwd_f)**2) / np.sum((dx_l_f - np.mean(dx_l_f))**2)
print(f"Linear gain k_fwd: {k_fwd_fit:.6f} m/unit (R² = {r2_fwd:.4f})")
print(f"Implied velocity gain k_fwd / dt: {k_fwd_fit / dt:.4f} m/s per unit command")

# 2. Fit angular velocity gain k_rot: dth = k_rot * u_diff
k_rot_fit = np.linalg.lstsq(u_diff_f[:, None], dth_f, rcond=None)[0][0]
r2_rot = 1.0 - np.sum((dth_f - k_rot_fit * u_diff_f)**2) / np.sum((dth_f - np.mean(dth_f))**2)
print(f"Angular displacement gain k_rot: {k_rot_fit:.6f} rad/unit (R² = {r2_rot:.4f})")
print(f"Implied angular velocity gain k_rot / dt: {k_rot_fit / dt:.4f} rad/s per unit command")

# 3. Fit Gyro yaw rate: w_gyro = k_gyro * u_diff
k_gyro_fit = np.linalg.lstsq(u_diff_f[:, None], w_gyro_f, rcond=None)[0][0]
r2_gyro = 1.0 - np.sum((w_gyro_f - k_gyro_fit * u_diff_f)**2) / np.sum((w_gyro_f - np.mean(w_gyro_f))**2)
print(f"Gyro yaw rate gain: {k_gyro_fit:.4f} (rad/s)/unit (R² = {r2_gyro:.4f})")
