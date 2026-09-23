"""
scratch/inspect_sensor_correlations.py — Inspect correlations of all 25 sensor channels with diff_u
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

# Generate babbling with 12-tick holds (0.36s sustained actions)
n_blocks = 35
blocks = rng.uniform(-0.15, 0.15, size=(n_blocks, 6))
U = np.repeat(blocks, 12, axis=0)[:400]
S = np.array([hal.step(u)[0] for u in U])

diff_u = U[:, 1] - U[:, 0]
diff_u_norm = (diff_u - np.mean(diff_u)) / (np.std(diff_u) + 1e-9)

print("Channel correlations with diff_u (u_R - u_L):")
for j in range(25):
    c = float(np.corrcoef(diff_u, S[:, j])[0, 1])
    if abs(c) > 0.1:
        print(f"  Channel {j:2d}: r = {c:+.4f}, std = {np.std(S[:, j]):.4f}")

# Also check gyro channels 18, 19, 20:
print(f"Channel 18 (roll rate):  r = {float(np.corrcoef(diff_u, S[:, 18])[0, 1]):+.4f}")
print(f"Channel 19 (pitch rate): r = {float(np.corrcoef(diff_u, S[:, 19])[0, 1]):+.4f}")
print(f"Channel 20 (yaw rate):   r = {float(np.corrcoef(diff_u, S[:, 20])[0, 1]):+.4f}")
