"""
scratch/deep_forensic_failure_analysis.py — Tick-by-tick forensic diagnosis of failing seeds (101, 202, 303)
Checks:
1. Did coprime phase disambiguation ever choose an incorrect integer wrap?
2. What was the residual |x1 - x2| at every tick?
3. What was the wheel odometry error vs true ground speed (dx_body, dy_body)?
4. What was the heading error's contribution to position drift?
5. Did the failure happen in Phase Disambiguation, Dead Reckoning Integration, or Steering?
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
from brain.carl_stage2_grid_torus import MultiScaleGridToroid, disambiguate_coprime_phases
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose, inject_sensor_noise
from brain.test_stage2_1b_r1_aliasing_showdown import compute_steering_action

hal = CarlStage1HAL(open_space=True)

for seed in [42, 101, 202, 303]:
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    brain.k_eff = 4.0862
    brain.use_motor_efference = True

    multi_grid = MultiScaleGridToroid(seed=seed, dt=hal.dt, lambda1=0.80, lambda2=1.15)

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    brain.reset_at_birthplace()
    multi_grid.reset_at_birthplace()

    diag0 = hal.get_diagnostics()
    bx, by = diag0["pos_x"], diag0["pos_y"]

    max_resid = 0.0
    wrong_wrap_count = 0
    total_ticks = 0

    wheel_v_accum = 0.0
    true_v_accum = 0.0
    prev_px, prev_py = bx, by

    # Track during wander + homing
    multi_res = None
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_cmd, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        # Wheel velocity
        v_wheel = 0.048 * (float(u_cmd[0]) + float(u_cmd[1])) * 12.5
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)
        multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)

        # Ground truth
        gt_x = diag["pos_x"] - bx
        gt_y = diag["pos_y"] - by
        dec_x = multi_res["displacement_x_meters"]
        dec_y = multi_res["displacement_y_meters"]

        # Check disambiguation residual
        resid = multi_res["disambiguation_residual"]
        if resid > max_resid:
            max_resid = resid

        # Check if decoded pos was within 0.40m of true pos (0.80m/2)
        # If err > 0.40m, it might be a wrap error
        err = math.sqrt((dec_x - gt_x)**2 + (dec_y - gt_y)**2)
        if err > 0.40:
            wrong_wrap_count += 1

        # Physical step
        cur_px, cur_py = diag["pos_x"], diag["pos_y"]
        true_step = math.sqrt((cur_px - prev_px)**2 + (cur_py - prev_py)**2)
        wheel_step = abs(v_grounded) * hal.dt
        wheel_v_accum += wheel_step
        true_v_accum += true_step
        prev_px, prev_py = cur_px, cur_py
        total_ticks += 1

    wander_err = err
    # Now run homing
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

        gt_x = diag["pos_x"] - bx
        gt_y = diag["pos_y"] - by
        dec_x = multi_res["displacement_x_meters"]
        dec_y = multi_res["displacement_y_meters"]
        resid = multi_res["disambiguation_residual"]
        if resid > max_resid:
            max_resid = resid
        err = math.sqrt((dec_x - gt_x)**2 + (dec_y - gt_y)**2)
        if err > 0.40:
            wrong_wrap_count += 1

        cur_px, cur_py = diag["pos_x"], diag["pos_y"]
        true_step = math.sqrt((cur_px - prev_px)**2 + (cur_py - prev_py)**2)
        wheel_step = abs(v_grounded) * hal.dt
        wheel_v_accum += wheel_step
        true_v_accum += true_step
        prev_px, prev_py = cur_px, cur_py
        homing_ticks += 1

    final_diag = hal.get_diagnostics()
    final_drift = math.sqrt((final_diag["pos_x"] - bx)**2 + (final_diag["pos_y"] - by)**2)

    print(f"=== SEED {seed:3d} ===")
    print(f"  Final Physical Drift:   {final_drift:6.3f} m (Pass <= 0.22m: {final_drift <= 0.22})")
    print(f"  Wander End Error:       {wander_err:6.3f} m")
    print(f"  Final Decoded Error:    {err:6.3f} m")
    print(f"  Max Disambig Residual:  {max_resid:6.4f} m")
    print(f"  Wrong Wrap Ticks (>0.4m): {wrong_wrap_count} / {total_ticks + homing_ticks}")
    print(f"  Wheel Odom Dist:        {wheel_v_accum:6.3f} m")
    print(f"  True Ground Dist:       {true_v_accum:6.3f} m (Ratio: {wheel_v_accum / (true_v_accum + 1e-9):.4f})")
    print(f"  Homing Ticks:           {homing_ticks}")
