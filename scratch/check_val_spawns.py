import numpy as np

d = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
print("Keys:", d.files)
if 'G_grid' in d:
    g = d['G_grid']
    print("DEV_VAL spawn positions (first step):")
    for ep in range(len(g)):
        print(f"Ep {ep:02d}: pos=({g[ep, 0, 0]:+.2f}, {g[ep, 0, 1]:+.2f})")
