import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import pandas as pd
# Pure numpy regression

from scratch.fit_kinematics import df

# Add lagged variables prev_v, prev_w
df['prev_v'] = df.groupby('b_idx')['v_true'].shift(1).fillna(0.0)
df['prev_w'] = df.groupby('b_idx')['w_true'].shift(1).fillna(0.0)

# 1. Forward velocity model
# Notice that when |u_fwd| > 0.40 and |u_diff| < 0.2 (like in Branch 07), there is caster slip/stall.
df['high_fwd_stall'] = ((df['u_fwd'] > 0.40) & (df['u_diff'].abs() < 0.2)).astype(float)

X_v = np.column_stack([
    np.ones(len(df)),
    df['u_fwd'],
    df['prev_v'],
    df['high_fwd_stall'] * df['u_fwd']
])
y_v = df['v_true'].values

w_v, _, _, _ = np.linalg.lstsq(X_v, y_v, rcond=None)
pred_v = X_v @ w_v
r2_v = 1.0 - np.sum((y_v - pred_v)**2) / np.sum((y_v - np.mean(y_v))**2)
print(f"Forward velocity R2: {r2_v:.4f}")
print(f"Coefficients: intercept={w_v[0]:.4f}, u_fwd={w_v[1]:.4f}, prev_v={w_v[2]:.4f}, stall={w_v[3]:.4f}")

# 2. Angular velocity model
df['diff_drag'] = df['u_diff'] * df['u_fwd'].abs()

X_w = np.column_stack([
    np.ones(len(df)),
    df['u_diff'],
    df['prev_w'],
    df['diff_drag']
])
y_w = df['w_true'].values

w_w, _, _, _ = np.linalg.lstsq(X_w, y_w, rcond=None)
pred_w = X_w @ w_w
r2_w = 1.0 - np.sum((y_w - pred_w)**2) / np.sum((y_w - np.mean(y_w))**2)
print(f"\nAngular velocity R2: {r2_w:.4f}")
print(f"Coefficients: intercept={w_w[0]:.4f}, u_diff={w_w[1]:.4f}, prev_w={w_w[2]:.4f}, diff_drag={w_w[3]:.4f}")
