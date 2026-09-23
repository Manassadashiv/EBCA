"""
scratch/test_ou_parameters.py — Test babbling regimes for optimal motor efference R^2
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage1_babbler import CarlStage1Babbler

hal = CarlStage1HAL(open_space=True)

for regime_name, regime in [
    ("COUPLED_SYNERGY", CarlStage1Babbler.REGIME_COUPLED_SYNERGY),
    ("ORNSTEIN_UHLENBECK", CarlStage1Babbler.REGIME_ORNSTEIN_UHLENBECK),
    ("STEP_REVERSAL", CarlStage1Babbler.REGIME_STEP_REVERSAL),
]:
    for seed in [42, 101, 202]:
        b_train = CarlStage1Babbler(seed=seed, regime=regime)
        if regime == CarlStage1Babbler.REGIME_ORNSTEIN_UHLENBECK:
            b_train.theta_ou = 0.08
            b_train.sigma_ou = 0.03
        U_train = np.array([b_train.generate_command() for _ in range(400)])
        hal.reset()
        S_train = np.array([hal.step(u)[0] for u in U_train])

        brain = CarlStage2BIntegratedBrain(seed=seed)
        brain.develop_from_babbling(U_train, S_train)

        diff_u = U_train[:, 1] - U_train[:, 0]
        omega_train = np.array([float(s @ brain.w_rot) for s in S_train])
        k_eff = float(np.sum(diff_u * omega_train) / (np.sum(diff_u ** 2) + 1e-9))

        b_val = CarlStage1Babbler(seed=seed + 500, regime=regime)
        if regime == CarlStage1Babbler.REGIME_ORNSTEIN_UHLENBECK:
            b_val.theta_ou = 0.08
            b_val.sigma_ou = 0.03
        U_val = np.array([b_val.generate_command() for _ in range(200)])
        S_val = np.array([hal.step(u)[0] for u in U_val])
        diff_u_val = U_val[:, 1] - U_val[:, 0]
        omega_val = np.array([float(s @ brain.w_rot) for s in S_val])

        pred = k_eff * diff_u_val
        ss_res = float(np.sum((omega_val - pred) ** 2))
        ss_tot = float(np.sum((omega_val - np.mean(omega_val)) ** 2))
        r2 = 1.0 - ss_res / (ss_tot + 1e-9)
        corr = float(np.corrcoef(diff_u_val, omega_val)[0, 1])

        print(f"[{regime_name}] Seed {seed}: k_eff = {k_eff:+.4f}, corr = {corr:+.4f}, R^2 = {r2:.4f}")
