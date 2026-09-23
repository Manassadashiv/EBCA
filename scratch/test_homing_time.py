"""
scratch/test_homing_time.py — Test if homing reaches origin with adequate tick budget
"""
import sys
import math
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import MultiScaleGridToroid
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose, inject_sensor_noise
from brain.test_stage2_1b_r1_aliasing_showdown import compute_steering_action

hal = CarlStage1HAL(open_space=True)
seed = 42
rng = np.random.RandomState(seed)
apply_stochastic_initial_pose(hal, seed)

# Baby developmental babbling
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
birth_x, birth_y = diag0["pos_x"], diag0["pos_y"]

# 350 ticks wander
for tick in range(350):
    u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
    s, diag = hal.step(u_cmd)
    res_brain = brain.update_brain(u_cmd, inject_sensor_noise(s, rng))
    current_heading = res_brain["hd_decoded_heading"]
    is_slipping = res_brain["is_slipping"]
    v_wheel = 0.048 * (float(u_cmd[0]) + float(u_cmd[1])) * 12.5
    v_grounded = v_wheel if not is_slipping else 0.0
    vx = v_grounded * math.cos(current_heading)
    vy = v_grounded * math.sin(current_heading)
    multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)

wander_dist = math.sqrt((diag["pos_x"] - birth_x)**2 + (diag["pos_y"] - birth_y)**2)
print(f"Distance at start of homing: {wander_dist:.3f}m")

# Homing with 700 ticks
distances = []
for h_tick in range(700):
    disp_x = multi_res["displacement_x_meters"]
    disp_y = multi_res["displacement_y_meters"]
    dist_home = math.sqrt(disp_x**2 + disp_y**2)

    u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -disp_x, -disp_y, dist_home)
    if is_home:
        print(f"Reached birthplace target at tick {h_tick}!")
        break

    s, diag = hal.step(u_h)
    res_brain = brain.update_brain(u_h, inject_sensor_noise(s, rng))
    current_heading = res_brain["hd_decoded_heading"]
    is_slipping = res_brain["is_slipping"]

    v_wheel = 0.048 * (float(u_h[0]) + float(u_h[1])) * 12.5
    v_grounded = v_wheel if not is_slipping else 0.0
    vx = v_grounded * math.cos(current_heading)
    vy = v_grounded * math.sin(current_heading)
    multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)

    curr_actual_dist = math.sqrt((diag["pos_x"] - birth_x)**2 + (diag["pos_y"] - birth_y)**2)
    distances.append(curr_actual_dist)
    if (h_tick + 1) % 50 == 0:
        print(f"Homing tick {h_tick+1:3d}: actual_dist = {curr_actual_dist:.3f}m, decoded_dist = {dist_home:.3f}m")

final_diag = hal.get_diagnostics()
final_dist = math.sqrt((final_diag["pos_x"] - birth_x)**2 + (final_diag["pos_y"] - birth_y)**2)
print(f"Final Drift after homing: {final_dist:.3f}m (Min achieved: {min(distances):.3f}m)")
