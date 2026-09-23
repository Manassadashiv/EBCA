"""
scratch/diagnose_stochastic_yaw_drift.py — Inspect why drift increases under initial yaw offset
Logs trajectory, heading tracking, and steering commands for Seed 101 and Seed 202.
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
from brain.test_stage2_1b_r1_aliasing_showdown import compute_steering_action

hal = CarlStage1HAL(open_space=True)

for seed in [101, 202]:
    rng = np.random.RandomState(seed)
    jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, seed)

    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    brain.k_eff = 4.0862
    brain.use_motor_efference = True

    multi_grid = MultiScaleGridToroid(seed=seed, dt=hal.dt, lambda1=0.80, lambda2=1.15)

    hal.reset()
    apply_carl_stochastic_initial_pose(hal, seed)
    brain.reset_at_birthplace()
    multi_grid.reset_at_birthplace()

    diag0 = hal.get_diagnostics()
    bx, by, byaw = diag0["pos_x"], diag0["pos_y"], diag0["yaw"]

    print(f"\n--- SEED {seed:3d}: Initial Physical Yaw = {math.degrees(byaw):+.2f} deg, Pose = ({bx:.3f}, {by:.3f}) ---")

    # Wander
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_cmd, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        v_wheel = 0.048 * (float(u_cmd[0]) + float(u_cmd[1])) * 12.5
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)
        multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)

    diag_w = hal.get_diagnostics()
    gt_wander_x = diag_w["pos_x"] - bx
    gt_wander_y = diag_w["pos_y"] - by
    gt_dist = math.sqrt(gt_wander_x**2 + gt_wander_y**2)

    dec_x = multi_res["displacement_x_meters"]
    dec_y = multi_res["displacement_y_meters"]
    dec_dist = math.sqrt(dec_x**2 + dec_y**2)

    # In body frame (rotated by initial yaw)
    c0 = math.cos(byaw)
    s0 = math.sin(byaw)
    gt_body_x = gt_wander_x * c0 + gt_wander_y * s0
    gt_body_y = -gt_wander_x * s0 + gt_wander_y * c0

    print(f"End Wander: True World Pos = ({gt_wander_x:.3f}, {gt_wander_y:.3f}), True Dist = {gt_dist:.3f}m")
    print(f"            True Body Pos  = ({gt_body_x:.3f}, {gt_body_y:.3f})")
    print(f"            Decoded Pos    = ({dec_x:.3f}, {dec_y:.3f}), Decoded Dist = {dec_dist:.3f}m")
    print(f"            Body vs Decoded Error = {math.sqrt((dec_x - gt_body_x)**2 + (dec_y - gt_body_y)**2):.3f}m")

    # Homing
    homing_ticks = 0
    for h_tick in range(600):
        disp_x = multi_res["displacement_x_meters"]
        disp_y = multi_res["displacement_y_meters"]
        dist_home = math.sqrt(disp_x**2 + disp_y**2)
        u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -disp_x, -disp_y, dist_home)
        if is_home:
            break
        s, diag = hal.step(u_h)
        s_noisy = inject_sensor_noise(s, rng)
        res_brain = brain.update_brain(u_h, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        v_wheel = 0.048 * (float(u_h[0]) + float(u_h[1])) * 12.5
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)
        multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)
        homing_ticks += 1

    final_diag = hal.get_diagnostics()
    final_drift = math.sqrt((final_diag["pos_x"] - bx)**2 + (final_diag["pos_y"] - by)**2)
    print(f"End Homing: Final Physical Drift = {final_drift:.3f}m | Ticks = {homing_ticks}")
