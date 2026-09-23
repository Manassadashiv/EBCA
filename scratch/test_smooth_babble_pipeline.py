"""
scratch/test_smooth_babble_pipeline.py — Test full pipeline with smooth babbling
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)

def generate_developmental_babbling(seed: int, n_ticks: int = 400):
    rng = np.random.RandomState(seed)
    t = np.arange(n_ticks) * 0.030
    
    # Smooth continuous turning commands + forward drift + random exploratory perturbation
    # Multi-frequency smooth turning trajectory
    turn_cmd = (0.08 * np.sin(t * 1.5 + rng.uniform(0, 2*np.pi)) +
                0.05 * np.sin(t * 3.2 + rng.uniform(0, 2*np.pi)) +
                0.03 * np.sin(t * 0.7 + rng.uniform(0, 2*np.pi)))
    fwd_cmd = 0.08 + 0.04 * np.sin(t * 0.8 + rng.uniform(0, 2*np.pi))

    U = np.zeros((n_ticks, 6), dtype=np.float64)
    # Differential drive: Left = fwd - turn, Right = fwd + turn
    U[:, 0] = np.clip(fwd_cmd - turn_cmd, -0.15, 0.15)
    U[:, 1] = np.clip(fwd_cmd + turn_cmd, -0.15, 0.15)
    # Mild exploration on head/torso (small amplitude so it doesn't destabilize base)
    U[:, 2] = 0.05 * np.sin(t * 2.1)
    U[:, 3] = 0.03 * np.cos(t * 1.7)

    return U

for seed in [42, 101, 202]:
    hal.reset()
    apply_stochastic_initial_pose(hal, seed)

    U_train = generate_developmental_babbling(seed, 400)
    S_train = np.array([hal.step(u)[0] for u in U_train])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_train, S_train)

    ch_rot = np.argmax(np.abs(brain.w_rot))
    sign_rot = brain.w_rot[ch_rot]

    diff_u_train = U_train[:, 1] - U_train[:, 0]
    omega_train = np.array([float(s @ brain.w_rot) for s in S_train])
    k_eff = float(np.sum(diff_u_train * omega_train) / (np.sum(diff_u_train ** 2) + 1e-9))

    # Held-out dataset 2 (200 novel steps on unseen random seeds)
    U_val = generate_developmental_babbling(seed + 9999, 200)
    S_val = np.array([hal.step(u)[0] for u in U_val])
    diff_u_val = U_val[:, 1] - U_val[:, 0]
    omega_val = np.array([float(s @ brain.w_rot) for s in S_val])

    pred_val = k_eff * diff_u_val
    ss_res = float(np.sum((omega_val - pred_val) ** 2))
    ss_tot = float(np.sum((omega_val - np.mean(omega_val)) ** 2))
    r2_val = 1.0 - ss_res / (ss_tot + 1e-9)

    print(f"Seed {seed:3d}: w_rot channel = {ch_rot} (sign={sign_rot:+.1f}), k_eff = {k_eff:+.4f}, Held-Out R^2 = {r2_val:.4f}")
