"""
scratch/test_error_breakdown.py — Decompose position error into:
1. CANN bump speed vs commanded velocity (is ToroidalGridCellAttractor gain_trans accurate?)
2. Commanded velocity vs true body velocity (forward speed model error)
3. Heading error accumulation (integral of heading error * speed)
4. Phase readout discretization error
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
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose, inject_sensor_noise

hal = CarlStage1HAL(open_space=True)

for seed in [101, 202, 303]:
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

    # Accumulators for hypothetical ideal integrators:
    # 1. Ideal heading + commanded speed
    ideal_head_x, ideal_head_y = 0.0, 0.0
    # 2. Decoded heading + true body forward speed
    true_speed_x, true_speed_y = 0.0, 0.0
    # 3. Pure dead reckoning (ideal continuous integral of vx, vy fed to grid)
    pure_dr_x, pure_dr_y = 0.0, 0.0

    prev_x, prev_y = bx, by

    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_cmd, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        # True displacement
        cur_x, cur_y = diag["pos_x"], diag["pos_y"]
        true_dx = cur_x - prev_x
        true_dy = cur_y - prev_y
        true_step = math.sqrt(true_dx**2 + true_dy**2)
        true_yaw = diag["yaw"]

        # Commanded velocity injected into grid
        v_wheel = 0.048 * (float(u_cmd[0]) + float(u_cmd[1])) * 12.5
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)
        multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)

        # 1. Pure DR (Euler integration of vx, vy)
        pure_dr_x += vx * hal.dt
        pure_dr_y += vy * hal.dt

        # 2. Ideal heading (true_yaw) + commanded speed
        ideal_head_x += v_grounded * math.cos(true_yaw) * hal.dt
        ideal_head_y += v_grounded * math.sin(true_yaw) * hal.dt

        # 3. Decoded heading + true body speed
        true_speed_x += true_step * math.cos(current_heading)
        true_speed_y += true_step * math.sin(current_heading)

        prev_x, prev_y = cur_x, cur_y

    gt_x = cur_x - bx
    gt_y = cur_y - by
    gt_dist = math.sqrt(gt_x**2 + gt_y**2)

    dec_x = multi_res["displacement_x_meters"]
    dec_y = multi_res["displacement_y_meters"]

    cann_drift = math.sqrt((dec_x - pure_dr_x)**2 + (dec_y - pure_dr_y)**2)
    heading_drift = math.sqrt((pure_dr_x - ideal_head_x)**2 + (pure_dr_y - ideal_head_y)**2)
    speed_drift = math.sqrt((ideal_head_x - gt_x)**2 + (ideal_head_y - gt_y)**2)
    total_err = math.sqrt((dec_x - gt_x)**2 + (dec_y - gt_y)**2)

    print(f"=== SEED {seed:3d} (Wander End, True Dist = {gt_dist:.3f}m) ===")
    print(f"  Total Position Error:       {total_err:6.3f} m")
    print(f"  CANN vs Pure DR Lag:        {cann_drift:6.3f} m")
    print(f"  Heading Error Contribution: {heading_drift:6.3f} m")
    print(f"  Speed Model Contribution:   {speed_drift:6.3f} m")
    print(f"  Decoded vs Pure DR: dec=({dec_x:.3f}, {dec_y:.3f}), dr=({pure_dr_x:.3f}, {pure_dr_y:.3f})")
    print(f"  True Pos: ({gt_x:.3f}, {gt_y:.3f})")
