"""
scratch/inspect_homing_trajectory.py — Step-by-step trace of homing phase in Seed 101
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
seed = 101
rng = np.random.RandomState(seed)
apply_carl_stochastic_initial_pose(hal, seed)

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

print("--- START OF HOMING ---")
# Trace every 50 ticks of homing
for h_tick in range(600):
    disp_x = multi_res["displacement_x_meters"]
    disp_y = multi_res["displacement_y_meters"]
    dist_home = math.sqrt(disp_x**2 + disp_y**2)

    u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -disp_x, -disp_y, dist_home)
    cur_diag = hal.get_diagnostics()
    phys_dist = math.sqrt((cur_diag["pos_x"] - bx)**2 + (cur_diag["pos_y"] - by)**2)

    if h_tick % 50 == 0 or is_home:
        print(f"Homing Tick {h_tick:3d}: Decoded Home Dist = {dist_home:.3f}m | Phys Dist to Birth = {phys_dist:.3f}m | u_h = [{u_h[0]:.2f}, {u_h[1]:.2f}] | HD = {math.degrees(res_brain['hd_decoded_heading']):.1f} deg | True Yaw = {math.degrees(cur_diag['yaw']):.1f} deg")

    if is_home:
        print(f"STOPPED at tick {h_tick}: Decoded Home Dist = {dist_home:.3f}m, Phys Dist = {phys_dist:.3f}m")
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
