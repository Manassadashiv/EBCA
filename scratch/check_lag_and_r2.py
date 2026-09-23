"""
scratch/check_lag_and_r2.py — Analyze motor efference regression with lag and filtering
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)
seed = 42
rng = np.random.RandomState(seed)
apply_stochastic_initial_pose(hal, seed)

# Dataset 1: 400 steps
U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
S_babble = np.array([hal.step(u)[0] for u in U_babble])

brain = CarlStage2BIntegratedBrain(seed=seed)
brain.develop_from_babbling(U_babble, S_babble)

diff_u = U_babble[:, 1] - U_babble[:, 0]
omega_sensory = np.array([float(s @ brain.w_rot) for s in S_babble])

# Test Dataset 2: 200 steps
U_val = rng.uniform(-0.15, 0.15, size=(200, 6))
S_val = np.array([hal.step(u)[0] for u in U_val])
diff_u_val = U_val[:, 1] - U_val[:, 0]
omega_val = np.array([float(s @ brain.w_rot) for s in S_val])

print(f"w_rot channel: {np.argmax(np.abs(brain.w_rot))}")
print(f"diff_u std: {np.std(diff_u):.4f}, omega std: {np.std(omega_sensory):.4f}")

for lag in [0, 1, 2, 3]:
    if lag == 0:
        u_train = diff_u
        y_train = omega_sensory
        u_test = diff_u_val
        y_test = omega_val
    else:
        u_train = diff_u[:-lag]
        y_train = omega_sensory[lag:]
        u_test = diff_u_val[:-lag]
        y_test = omega_val[lag:]

    k_eff = float(np.sum(u_train * y_train) / (np.sum(u_train ** 2) + 1e-9))
    pred = k_eff * u_test
    ss_res = float(np.sum((y_test - pred) ** 2))
    ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
    r2 = 1.0 - ss_res / (ss_tot + 1e-9)
    corr = float(np.corrcoef(u_test, y_test)[0, 1])
    print(f"Lag {lag}: k_eff = {k_eff:+.4f}, corr = {corr:+.4f}, R^2 = {r2:.4f}")

# Also test: what if babbling uses continuous trajectories (e.g. Ornstein-Uhlenbeck or smooth turning bursts)?
from brain.carl_stage1_babbler import CarlStage1Babbler
babbler = CarlStage1Babbler(seed=seed, regime=CarlStage1Babbler.REGIME_ORNSTEIN_UHLENBECK)
U_ou = np.array([babbler.generate_command() for _ in range(400)])
hal.reset()
S_ou = np.array([hal.step(u)[0] for u in U_ou])
diff_u_ou = U_ou[:, 1] - U_ou[:, 0]
omega_ou = np.array([float(s @ brain.w_rot) for s in S_ou])

babbler_val = CarlStage1Babbler(seed=seed + 999, regime=CarlStage1Babbler.REGIME_ORNSTEIN_UHLENBECK)
U_ou_val = np.array([babbler_val.generate_command() for _ in range(200)])
S_ou_val = np.array([hal.step(u)[0] for u in U_ou_val])
diff_u_ou_val = U_ou_val[:, 1] - U_ou_val[:, 0]
omega_ou_val = np.array([float(s @ brain.w_rot) for s in S_ou_val])

print("\n--- Ornstein-Uhlenbeck (Continuous Smooth Babbling) ---")
for lag in [0, 1, 2]:
    if lag == 0:
        u_train = diff_u_ou
        y_train = omega_ou
        u_test = diff_u_ou_val
        y_test = omega_ou_val
    else:
        u_train = diff_u_ou[:-lag]
        y_train = omega_ou[lag:]
        u_test = diff_u_ou_val[:-lag]
        y_test = omega_ou_val[lag:]

    k_eff = float(np.sum(u_train * y_train) / (np.sum(u_train ** 2) + 1e-9))
    pred = k_eff * u_test
    ss_res = float(np.sum((y_test - pred) ** 2))
    ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
    r2 = 1.0 - ss_res / (ss_tot + 1e-9)
    corr = float(np.corrcoef(u_test, y_test)[0, 1])
    print(f"OU Lag {lag}: k_eff = {k_eff:+.4f}, corr = {corr:+.4f}, R^2 = {r2:.4f}")
