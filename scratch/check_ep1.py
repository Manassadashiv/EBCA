import numpy as np

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
S = d_val['S']
U = d_val['U']

print("Ep 1 steps 145-155 U:")
print(U[1, 145:155])

print("Ep 1 steps 145-155 S[:, 15:24]:")
print(S[1, 145:155, 15:24])
