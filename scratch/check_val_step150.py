import numpy as np

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S = d_val['S']
U = d_val['U']

# Steps 150 to 160
# Gyro yaw: S[:, 150:160, 20]
# U: U[:, 150:160, :]

for ep in range(20):
    gyros = S[ep, 150:160, 20]
    u0 = U[ep, 150:160, 0]
    u1 = U[ep, 150:160, 1]
    udiff = u1 - u0
    print(f"Ep {ep:02d}: gyros mean={np.mean(gyros):+.3f}, std={np.std(gyros):.3f} | udiff mean={np.mean(udiff):+.3f}, std={np.std(udiff):.3f}")
