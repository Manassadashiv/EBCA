import numpy as np

d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
U_val = d_val['U']
S_val = d_val['S']

print("DEV_VAL U stats across 20 eps:")
for i in range(6):
    u_i = U_val[:, :, i].flatten()
    print(f"U[{i}]: mean={np.mean(u_i):+.4f}, std={np.std(u_i):.4f}, min={np.min(u_i):+.4f}, max={np.max(u_i):+.4f}")

print("\nWhat are the actions doing in DEV_VAL?")
print("Ep 0 steps 145-155 U:")
print(U_val[0, 145:155])

print("\nEp 0 steps 145-155 s_body (channels 15 to 24):")
print(S_val[0, 145:155, 15:24])

# Let's inspect HAL channel routing in carl_stage2_2_data_collector.py
