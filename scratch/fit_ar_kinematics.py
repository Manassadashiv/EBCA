import numpy as np
from scipy.optimize import minimize

d = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
G = d['G_grid']  # (60, 400, 2)
V = d['V_hd']    # (60, 400, 2)
U = d['U']       # (60, 400, 6)
S = d['S']       # (60, 400, 25)
dt = 0.030

th = np.arctan2(V[:, :, 1], V[:, :, 0])
dx_g = G[:, 1:, 0] - G[:, :-1, 0]
dy_g = G[:, 1:, 1] - G[:, :-1, 1]
dth = (th[:, 1:] - th[:, :-1] + np.pi) % (2 * np.pi) - np.pi

cos_th = np.cos(th[:, :-1])
sin_th = np.sin(th[:, :-1])
dx_l = cos_th * dx_g + sin_th * dy_g
v_true = dx_l / dt
w_true = dth / dt
w_gyro = S[:, 1:, 20]

u_fwd = 0.5 * (U[:, :-1, 0] + U[:, :-1, 1])
u_diff = U[:, :-1, 1] - U[:, :-1, 0]

# Fit AR(1) for v: v_{t+1} = a * v_t + b * u_fwd_t
v_prev = v_true[:, :-1].flatten()
v_curr = v_true[:, 1:].flatten()
u_fwd_sub = u_fwd[:, 1:].flatten()

X_v = np.stack([v_prev, u_fwd_sub], axis=-1)
coeff_v = np.linalg.lstsq(X_v, v_curr, rcond=None)[0]
r2_v = 1.0 - np.sum((v_curr - X_v @ coeff_v)**2) / np.sum((v_curr - np.mean(v_curr))**2)
print(f"AR(1) v: v_{{t+1}} = {coeff_v[0]:.4f} * v_t + {coeff_v[1]:.4f} * u_fwd (R² = {r2_v:.4f})")

# Fit AR(1) for w: w_{t+1} = a * w_t + b * u_diff_t
w_prev = w_true[:, :-1].flatten()
w_curr = w_true[:, 1:].flatten()
u_diff_sub = u_diff[:, 1:].flatten()

X_w = np.stack([w_prev, u_diff_sub], axis=-1)
coeff_w = np.linalg.lstsq(X_w, w_curr, rcond=None)[0]
r2_w = 1.0 - np.sum((w_curr - X_w @ coeff_w)**2) / np.sum((w_curr - np.mean(w_curr))**2)
print(f"AR(1) w: w_{{t+1}} = {coeff_w[0]:.4f} * w_t + {coeff_w[1]:.4f} * u_diff (R² = {r2_w:.4f})")

# Fit Gyro AR(1)
wg_prev = w_gyro[:, :-1].flatten()
wg_curr = w_gyro[:, 1:].flatten()
X_wg = np.stack([wg_prev, u_diff_sub], axis=-1)
coeff_wg = np.linalg.lstsq(X_wg, wg_curr, rcond=None)[0]
r2_wg = 1.0 - np.sum((wg_curr - X_wg @ coeff_wg)**2) / np.sum((wg_curr - np.mean(wg_curr))**2)
print(f"AR(1) Gyro: w_gyro_{{t+1}} = {coeff_wg[0]:.4f} * w_gyro_t + {coeff_wg[1]:.4f} * u_diff (R² = {r2_wg:.4f})")
