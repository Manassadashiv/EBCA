"""
scratch/test_babble_holding.py — Test babbling with command holding duration
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)

def generate_held_babbling(rng, n_ticks=400, hold_ticks=8):
    """Generates piecewise-constant random motor babbling."""
    n_blocks = int(np.ceil(n_ticks / hold_ticks))
    blocks = rng.uniform(-0.15, 0.15, size=(n_blocks, 6))
    commands = np.repeat(blocks, hold_ticks, axis=0)[:n_ticks]
    return commands

for hold in [1, 4, 8, 12]:
    r2_dev = []
    k_eff_dev = []
    for seed in [42, 101, 202]:
        rng = np.random.RandomState(seed)
        apply_stochastic_initial_pose(hal, seed)

        U_train = generate_held_babbling(rng, n_ticks=400, hold_ticks=hold)
        S_train = np.array([hal.step(u)[0] for u in U_train])

        brain = CarlStage2BIntegratedBrain(seed=seed)
        brain.develop_from_babbling(U_train, S_train)

        diff_u_train = U_train[:, 1] - U_train[:, 0]
        omega_train = np.array([float(s @ brain.w_rot) for s in S_train])
        k_eff = float(np.sum(diff_u_train * omega_train) / (np.sum(diff_u_train ** 2) + 1e-9))

        # Held-out dataset (seed + 1000)
        rng_val = np.random.RandomState(seed + 1000)
        U_val = generate_held_babbling(rng_val, n_ticks=200, hold_ticks=hold)
        S_val = np.array([hal.step(u)[0] for u in U_val])
        diff_u_val = U_val[:, 1] - U_val[:, 0]
        omega_val = np.array([float(s @ brain.w_rot) for s in S_val])

        pred = k_eff * diff_u_val
        ss_res = float(np.sum((omega_val - pred) ** 2))
        ss_tot = float(np.sum((omega_val - np.mean(omega_val)) ** 2))
        r2 = 1.0 - ss_res / (ss_tot + 1e-9)

        r2_dev.append(r2)
        k_eff_dev.append(k_eff)

    print(f"Hold {hold:2d} ticks: k_eff = {np.mean(k_eff_dev):+.4f} (std={np.std(k_eff_dev):.4f}), "
          f"Held-Out R^2 = {np.mean(r2_dev):.4f} (min={np.min(r2_dev):.4f})")
