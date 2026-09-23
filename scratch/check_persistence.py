import numpy as np

d = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S = d['S']
# True 10-step horizon: t=150 to 160
# If pred is persistence from t=149:
true_joints = S[:, 150:160, 21:24]
pred_joints = np.repeat(S[:, 149:150, 21:24], 10, axis=1)

y_t = true_joints.flatten()
y_p = pred_joints.flatten()
r2_persist = 1.0 - np.sum((y_t - y_p)**2) / (np.sum((y_t - np.mean(y_t))**2) + 1e-8)
print(f"Joints persistence R2 over H=10: {r2_persist:.4f}")

# And all proprio (IMU accel + gyro + joints = channels 15 to 24)
true_proprio = S[:, 150:160, 15:24]
pred_proprio = np.repeat(S[:, 149:150, 15:24], 10, axis=1)
r2_proprio_persist = 1.0 - np.sum((true_proprio.flatten() - pred_proprio.flatten())**2) / (np.sum((true_proprio.flatten() - np.mean(true_proprio.flatten()))**2) + 1e-8)
print(f"All proprio persistence R2 over H=10: {r2_proprio_persist:.4f}")
