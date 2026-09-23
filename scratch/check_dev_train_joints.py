import numpy as np

d = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
S = d['S']
U = d['U']

print("S shape:", S.shape)
print("U shape:", U.shape)

# Let's inspect step-to-step changes in joints vs U
# s_body is S[:, :, 15:24]
# Channels 6, 7, 8 are S[:, :, 21:24]
for ch in range(3):
    j_vals = S[0, :20, 21+ch]
    u_vals = U[0, :20, ch]
    print(f"Channel {ch}:")
    print("  Joint:", [f"{v:.4f}" for v in j_vals[:8]])
    print("  U:    ", [f"{v:.4f}" for v in u_vals[:8]])

print("\nCorrelations between U channels and delta Joint channels:")
dj = np.diff(S[:, :, 21:24], axis=1) # (60, 399, 3)
u_slice = U[:, :-1, :] # (60, 399, 6)

for j_idx in range(3):
    j_name = ["Hip", "Neck", "Head"][j_idx]
    corrs = []
    for u_idx in range(6):
        c = np.corrcoef(dj[:, :, j_idx].flatten(), u_slice[:, :, u_idx].flatten())[0, 1]
        corrs.append(f"u{u_idx}={c:+.3f}")
    print(f"{j_name:5s} diff correlation with U: " + ", ".join(corrs))

print("\nWhat are the 9 channels of S[:, :, 15:24]?")
for ch in range(9):
    vals = S[:, :, 15+ch].flatten()
    print(f"Channel {ch:2d}: mean={np.mean(vals):+.4f}, std={np.std(vals):.4f}, min={np.min(vals):+.4f}, max={np.max(vals):+.4f}")
