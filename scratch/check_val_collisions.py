import numpy as np

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
coll = d_val['collision'] # (20, 400)

for ep in range(20):
    c_slice = coll[ep, 140:170]
    print(f"Ep {ep:02d}: collisions around t=150: sum={np.sum(c_slice)}, hits={np.where(c_slice > 0)[0]}")
