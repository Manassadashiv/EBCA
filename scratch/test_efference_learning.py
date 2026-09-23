"""
scratch/test_efference_learning.py — Test least-squares motor efference learning and held-out validation
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)

for seed in [42, 101, 202]:
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    # Dataset 1: 400 steps babbling
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)

    # Compute k_eff via least squares:
    # diff_u = u_R - u_L (channel 1 - channel 0)
    diff_u = U_babble[:, 1] - U_babble[:, 0]
    omega_sensory = np.array([float(s @ brain.w_rot) for s in S_babble])

    k_eff = float(np.sum(diff_u * omega_sensory) / (np.sum(diff_u ** 2) + 1e-9))

    # Dataset 2: 200 novel held-out babbling steps
    U_val = rng.uniform(-0.15, 0.15, size=(200, 6))
    S_val = np.array([hal.step(u)[0] for u in U_val])

    diff_u_val = U_val[:, 1] - U_val[:, 0]
    omega_sensory_val = np.array([float(s @ brain.w_rot) for s in S_val])
    omega_pred_val = k_eff * diff_u_val

    ss_res = float(np.sum((omega_sensory_val - omega_pred_val) ** 2))
    ss_tot = float(np.sum((omega_sensory_val - np.mean(omega_sensory_val)) ** 2))
    r2 = 1.0 - (ss_res / (ss_tot + 1e-9))

    print(f"Seed {seed:3d}: dominant w_rot channel = {np.argmax(np.abs(brain.w_rot))} (sign = {brain.w_rot[np.argmax(np.abs(brain.w_rot))]})")
    print(f"         k_eff = {k_eff:+.4f}, Held-Out R^2 = {r2:.4f} (Gate >= 0.85)")
