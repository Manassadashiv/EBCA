"""
scratch/test_ant_homing_alignment.py — Test alignment-gated forward homing (Cataglyphis pirouette)
"""

import os
import sys
import math
import numpy as np

BASE_DIR = "d:/ebca"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import MultiScaleGridToroid
from brain.test_stage2_1b_r2_efference import apply_carl_stochastic_initial_pose, inject_sensor_noise

hal = CarlStage1HAL(open_space=True)
DEV_SEEDS = [42, 101, 202]
UNSEEN_SEEDS = [303, 404, 505, 606, 707]
ALL_SEEDS = DEV_SEEDS + UNSEEN_SEEDS

def compute_ant_steering_action(r_hd, angles_hd, target_vec_x, target_vec_y, dist):
    if dist <= 0.04:
        return np.zeros(6, dtype=np.float64), True

    # Population vector cross-product torque
    neural_torque = float(np.sum(r_hd * (np.cos(angles_hd) * target_vec_y - np.sin(angles_hd) * target_vec_x)))
    forward_alignment = float(np.sum(r_hd * (np.cos(angles_hd) * target_vec_x + np.sin(angles_hd) * target_vec_y)))

    norm = math.sqrt(target_vec_x**2 + target_vec_y**2) + 1e-9
    cos_align = forward_alignment / (norm * (float(np.sum(r_hd)) + 1e-9))
    cos_align = float(np.clip(cos_align, -1.0, 1.0))

    # Pure turn in place if misaligned > 45 deg, smooth forward acceleration when aligned
    steer_cmd = np.clip(0.40 * (neural_torque / (norm * 5.0)), -0.12, 0.12)
    # Alignment gate: forward drive only when facing roughly towards home
    fwd_cmd = 0.12 * max(0.0, cos_align)**2

    u = np.zeros(6, dtype=np.float64)
    u[0] = np.clip(fwd_cmd - steer_cmd, -0.15, 0.15)
    u[1] = np.clip(fwd_cmd + steer_cmd, -0.15, 0.15)
    return u, False

print("Evaluating Alignment-Gated Homing across all 8 seeds (Uncalibrated v_scale=1.0):")
drifts_1 = []
passes_1 = 0
for s in ALL_SEEDS:
    rng = np.random.RandomState(s)
    apply_carl_stochastic_initial_pose(hal, s)

    brain = CarlStage2BIntegratedBrain(seed=s)
    brain.develop_from_babbling(rng.uniform(-0.15, 0.15, size=(400, 6)), np.array([hal.step(u)[0] for u in rng.uniform(-0.15, 0.15, size=(400, 6))]))
    brain.k_eff = 4.0862
    brain.use_motor_efference = True

    multi_grid = MultiScaleGridToroid(seed=s, dt=hal.dt, lambda1=0.80, lambda2=1.15)

    hal.reset()
    apply_carl_stochastic_initial_pose(hal, s)
    brain.reset_at_birthplace()
    multi_grid.reset_at_birthplace()

    d0 = hal.get_diagnostics()
    bx, by = d0["pos_x"], d0["pos_y"]

    # Wander
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=s * 0.01)
        s_obs, diag = hal.step(u_cmd)
        res_brain = brain.update_brain(u_cmd, inject_sensor_noise(s_obs, rng))
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]
        v_wheel = 0.048 * (float(u_cmd[0]) + float(u_cmd[1])) * 12.5
        multi_res = multi_grid.step(v_wheel * math.cos(current_heading), v_wheel * math.sin(current_heading), is_slipping)

    # Homing
    for h_tick in range(600):
        dx, dy = multi_res["displacement_x_meters"], multi_res["displacement_y_meters"]
        dist = math.sqrt(dx**2 + dy**2)
        u_h, is_home = compute_ant_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -dx, -dy, dist)
        if is_home:
            break
        s_obs, diag = hal.step(u_h)
        res_brain = brain.update_brain(u_h, inject_sensor_noise(s_obs, rng))
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]
        v_wheel = 0.048 * (float(u_h[0]) + float(u_h[1])) * 12.5
        multi_res = multi_grid.step(v_wheel * math.cos(current_heading), v_wheel * math.sin(current_heading), is_slipping)

    final_diag = hal.get_diagnostics()
    drift = math.sqrt((final_diag["pos_x"] - bx)**2 + (final_diag["pos_y"] - by)**2)
    drifts_1.append(drift)
    p = drift <= 0.22
    if p: passes_1 += 1
    print(f"  Seed {s:3d}: Drift = {drift:.3f}m [{'PASS' if p else 'FAIL'}]")

print(f"\nResult: Mean Drift = {np.mean(drifts_1):.3f}m | Passes = {passes_1}/8")
