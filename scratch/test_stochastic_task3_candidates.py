"""
scratch/test_stochastic_task3_candidates.py — Prototype of Stage 2.1B-R.3 Candidates
Compares:
- Candidate A: Multi-Scale Coprime Grid (2,048 neurons, lambda1=0.80, lambda2=1.15)
- Candidate B: Single Torus (1,024 neurons) + Integer Phase Winding Register (Engineered Control)
- Candidate C: Calibrated Velocity Coupling (Grounded Translation) on Multi-Scale Grid
Across genuine stochastic initial poses (jitter on qpos[22:29]), sensor noise, and actuator noise.
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
DEV_SEEDS = [42, 101, 202]
UNSEEN_SEEDS = [303, 404, 505, 606, 707]
ALL_SEEDS = DEV_SEEDS + UNSEEN_SEEDS

def evaluate_stochastic_run(seed: int, candidate: str, v_scale: float = 1.0):
    rng = np.random.RandomState(seed)
    jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, seed)

    # Developmental Babbling
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
    bx, by = diag0["pos_x"], diag0["pos_y"]

    # 1. Wander (350 ticks)
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        u_noisy = u_cmd + rng.normal(0, 0.003, size=6)
        s, diag = hal.step(u_noisy)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_noisy, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        # Velocity injection
        v_wheel = 0.048 * (float(u_noisy[0]) + float(u_noisy[1])) * 12.5 * v_scale
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)

        if candidate in ["Candidate A", "Candidate C"]:
            multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)
        else:
            # Candidate B: single torus unwrapped
            grid_res = res_brain

    # 2. Homing (up to 600 ticks)
    homing_ticks = 0
    for h_tick in range(600):
        if candidate in ["Candidate A", "Candidate C"]:
            disp_x = multi_res["displacement_x_meters"]
            disp_y = multi_res["displacement_y_meters"]
        else:
            disp_x = res_brain["grid_unwrapped_x"]
            disp_y = res_brain["grid_unwrapped_y"]

        dist_home = math.sqrt(disp_x**2 + disp_y**2)
        u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -disp_x, -disp_y, dist_home)
        if is_home:
            break

        u_noisy = u_h + rng.normal(0, 0.003, size=6)
        s, diag = hal.step(u_noisy)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_noisy, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        v_wheel = 0.048 * (float(u_noisy[0]) + float(u_noisy[1])) * 12.5 * v_scale
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)

        if candidate in ["Candidate A", "Candidate C"]:
            multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)
        homing_ticks += 1

    final_diag = hal.get_diagnostics()
    drift = math.sqrt((final_diag["pos_x"] - bx)**2 + (final_diag["pos_y"] - by)**2)
    return {
        "seed": seed,
        "init_yaw_deg": round(math.degrees(jyaw), 2),
        "homing_drift_m": round(drift, 3),
        "pass": bool(drift <= 0.22),
        "homing_ticks": homing_ticks
    }

print("Testing Candidate A (Uncalibrated v_scale=1.0) under True Stochastic Pose:")
for s in ALL_SEEDS:
    res = evaluate_stochastic_run(s, "Candidate A", v_scale=1.0)
    print(f"  Seed {s:3d} (yaw={res['init_yaw_deg']:+5.1f} deg): Drift = {res['homing_drift_m']:.3f}m [{'PASS' if res['pass'] else 'FAIL'}]")

print("\nTesting Candidate C (Calibrated Grounded Translation v_scale=0.85) under True Stochastic Pose:")
for s in ALL_SEEDS:
    res = evaluate_stochastic_run(s, "Candidate C", v_scale=0.85)
    print(f"  Seed {s:3d} (yaw={res['init_yaw_deg']:+5.1f} deg): Drift = {res['homing_drift_m']:.3f}m [{'PASS' if res['pass'] else 'FAIL'}]")
