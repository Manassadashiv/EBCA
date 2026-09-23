"""
scratch/calibrate_dev_kfwd.py — Measure forward locomotion gain on DEV seeds [42, 101, 202]
Calculates physical body displacement vs commanded forward synergy (u_L + u_R) during developmental babbling.
"""

import os
import sys
BASE_DIR = "d:/ebca"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import math
import numpy as np
from brain.carl_stage1_hal import CarlStage1HAL
from brain.test_stage2_1b_r2_efference import apply_carl_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)
DEV_SEEDS = [42, 101, 202]

gains = []
for seed in DEV_SEEDS:
    rng = np.random.RandomState(seed)
    apply_carl_stochastic_initial_pose(hal, seed)

    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    fwd_cmds = []
    actual_dxs = []

    for u in U_babble:
        p0 = hal.get_diagnostics()
        s, diag = hal.step(u)
        p1 = hal.get_diagnostics()

        yaw = p0["yaw"]
        dx_world = p1["pos_x"] - p0["pos_x"]
        dy_world = p1["pos_y"] - p0["pos_y"]

        # Project into robot body forward frame
        dx_body = dx_world * math.cos(yaw) + dy_world * math.sin(yaw)
        vx_body = dx_body / hal.dt

        fwd_synergy = float(u[0] + u[1])
        fwd_cmds.append(fwd_synergy)
        actual_dxs.append(vx_body)

    fwd_cmds = np.array(fwd_cmds)
    actual_dxs = np.array(actual_dxs)

    # Least squares regression: vx_body = k_fwd * (u0 + u1)
    k_fwd = float(np.sum(fwd_cmds * actual_dxs) / (np.sum(fwd_cmds**2) + 1e-9))
    corr = float(np.corrcoef(fwd_cmds, actual_dxs)[0, 1])
    gains.append((k_fwd, corr))
    print(f"Dev Seed {seed:3d}: k_fwd = {k_fwd:.5f} m/s per unit | Corr = {corr:.4f}")

mean_k_fwd = float(np.mean([g[0] for g in gains]))
print(f"\nMean Developmental k_fwd across DEV seeds: {mean_k_fwd:.5f}")
# In the original uncalibrated code, gain was: 0.048 * 12.5 = 0.60000
print(f"Ratio to legacy 0.60: {mean_k_fwd / 0.600:.4f}")
