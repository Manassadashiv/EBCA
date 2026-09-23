import numpy as np

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S = d_val['S']
U = d_val['U']

print("Ep 19 steps 145-155 U:")
print(U[19, 145:155])

print("\nEp 19 steps 145-155 Gyro Z (col 20):")
print(S[19, 145:155, 20])
