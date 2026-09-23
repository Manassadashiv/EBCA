import numpy as np

d = np.load('evidence/stage2_2_diag/datasets/DEV_TRAIN.npz')
S = d['S'] # (60, 400, 25)
U = d['U'] # (60, 400, 6)

# Test first-order position servo tracking
# s[:, 21] is hip, s[:, 22] is neck, s[:, 23] is head
# u[:, 4] is hip, u[:, 3] is neck, u[:, 2] is head

for name, s_idx, u_idx, gain in [("Hip", 21, 4, 0.45), ("Neck", 22, 3, 0.50), ("Head", 23, 2, 1.20)]:
    q_true = S[:, :, s_idx]
    u = U[:, :, u_idx]
    
    best_gamma = 0.0
    best_r2 = -999.0
    for gamma in np.linspace(0.5, 0.99, 50):
        # Unroll 10 steps
        q_pred = np.zeros_like(q_true)
        q_pred[:, 0] = q_true[:, 0]
        for t in range(1, 400):
            target = u[:, t-1] * gain
            q_pred[:, t] = gamma * q_pred[:, t-1] + (1 - gamma) * target
        
        # Compute R2 over 10-step unrolls from t=150 to 160
        true_10 = q_true[:, 150:160].flatten()
        pred_10 = q_pred[:, 150:160].flatten()
        r2 = 1.0 - np.sum((true_10 - pred_10)**2) / (np.sum((true_10 - np.mean(true_10))**2) + 1e-8)
        if r2 > best_r2:
            best_r2 = r2
            best_gamma = gamma
    print(f"{name:5s} (u{u_idx} -> s{s_idx}): best_gamma={best_gamma:.3f}, 10-step R2 = {best_r2:.4f}")
