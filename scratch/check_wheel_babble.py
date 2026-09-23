"""
scratch/check_wheel_babble.py — Check correlation when wheel babbling vs full body
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)
seed = 42
rng = np.random.RandomState(seed)
apply_stochastic_initial_pose(hal, seed)

# 1. Wheel-only babbling (channels 0 and 1 active, rest 0)
n_ticks = 400
U_wheel = np.zeros((n_ticks, 6))
# Piecewise continuous turns (e.g. held for 8 ticks)
blocks_L = rng.uniform(-0.15, 0.15, size=50)
blocks_R = rng.uniform(-0.15, 0.15, size=50)
U_wheel[:, 0] = np.repeat(blocks_L, 8)[:n_ticks]
U_wheel[:, 1] = np.repeat(blocks_R, 8)[:n_ticks]

S_wheel = np.array([hal.step(u)[0] for u in U_wheel])
diff_u_wheel = U_wheel[:, 1] - U_wheel[:, 0]

r_wheel = float(np.corrcoef(diff_u_wheel, S_wheel[:, 20])[0, 1])
print(f"Wheel-only babbling (held 8 ticks): r = {r_wheel:+.4f}, R^2 = {r_wheel**2:.4f}")

# 2. What about smooth continuous differential turning (e.g. sum of sines or Ornstein-Uhlenbeck)?
t = np.arange(n_ticks)
diff_smooth = 0.12 * np.sin(t * 0.05) + 0.05 * np.cos(t * 0.12)
U_smooth = np.zeros((n_ticks, 6))
U_smooth[:, 0] = -0.5 * diff_smooth + 0.05
U_smooth[:, 1] = +0.5 * diff_smooth + 0.05

hal.reset()
S_smooth = np.array([hal.step(u)[0] for u in U_smooth])
diff_u_smooth = U_smooth[:, 1] - U_smooth[:, 0]

r_smooth = float(np.corrcoef(diff_u_smooth, S_smooth[:, 20])[0, 1])
k_eff_smooth = float(np.sum(diff_u_smooth * S_smooth[:, 20]) / (np.sum(diff_u_smooth**2) + 1e-9))
pred = k_eff_smooth * diff_u_smooth
ss_res = float(np.sum((S_smooth[:, 20] - pred)**2))
ss_tot = float(np.sum((S_smooth[:, 20] - np.mean(S_smooth[:, 20]))**2))
r2_smooth = 1.0 - ss_res / (ss_tot + 1e-9)

print(f"Smooth continuous turning: k_eff = {k_eff_smooth:+.4f}, r = {r_smooth:+.4f}, R^2 = {r2_smooth:.4f}")
