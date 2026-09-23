import os
import sys
import numpy as np
import math

sys.path.insert(0, ".")

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import MultiScaleGridToroid
from brain.test_stage2_1b_r3_global_space import apply_carl_stochastic_initial_pose, inject_sensor_noise
from brain.test_stage2_1b_r1_aliasing_showdown import compute_steering_action

hal = CarlStage1HAL(open_space=True)
seed = 101
k_val = 1.088
rng = np.random.RandomState(seed)

hal.reset()
apply_carl_stochastic_initial_pose(hal, seed)

U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
S_babble = np.array([hal.step(u)[0] for u in U_babble])

brain = CarlStage2BIntegratedBrain(seed=seed)
brain.develop_from_babbling(U_babble, S_babble)
brain.k_eff = 4.0862
brain.use_motor_efference = True

multi_grid = MultiScaleGridToroid(lambda1=0.80, lambda2=1.15, dt=hal.dt, seed=seed)

hal.reset()
apply_carl_stochastic_initial_pose(hal, seed)
brain.reset_at_birthplace()
multi_grid.reset_at_birthplace()

diag0 = hal.get_diagnostics()
bx, by = diag0['pos_x'], diag0['pos_y']

for t in range(350):
    u_cmd = brain.compute_wander_action(t, seed_offset=seed * 0.01)
    s, diag = hal.step(u_cmd)
    s_noisy = inject_sensor_noise(s, rng)
    res_b = brain.update_brain(u_cmd, s_noisy)
    hd = res_b['hd_decoded_heading']
    is_slipping = res_b['is_slipping']
    v_wheel = (k_val * 0.5) * (float(u_cmd[0]) + float(u_cmd[1]))
    v_grounded = v_wheel if not is_slipping else 0.0
    multi_res = multi_grid.step(v_grounded * math.cos(hd), v_grounded * math.sin(hd), slip_gated=is_slipping)

dec_x = multi_res['displacement_x_meters']
dec_y = multi_res['displacement_y_meters']

slip_count = 0
cum_phys_h = 0.0
cum_int_h = 0.0
prev_px, prev_py = diag['pos_x'], diag['pos_y']

print("--- DETAILED HOMING TICKS 0 TO 50 ---")
for ht in range(430):
    dist_home = math.sqrt(dec_x**2 + dec_y**2)
    u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -dec_x, -dec_y, dist_home)
    
    s, diag = hal.step(u_h)
    s_noisy = inject_sensor_noise(s, rng)
    res_b = brain.update_brain(u_h, s_noisy)
    hd = res_b['hd_decoded_heading']
    is_slipping = res_b['is_slipping']
    if is_slipping:
        slip_count += 1
        
    v_wheel = (k_val * 0.5) * (float(u_h[0]) + float(u_h[1]))
    v_grounded = v_wheel if not is_slipping else 0.0
    multi_res = multi_grid.step(v_grounded * math.cos(hd), v_grounded * math.sin(hd), slip_gated=is_slipping)
    dec_x = multi_res['displacement_x_meters']
    dec_y = multi_res['displacement_y_meters']
    
    cur_px, cur_py = diag['pos_x'], diag['pos_y']
    d_p = math.sqrt((cur_px - prev_px)**2 + (cur_py - prev_py)**2)
    cum_phys_h += d_p
    cum_int_h += v_grounded * hal.dt
    prev_px, prev_py = cur_px, cur_py
    
    if ht in [0, 5, 10, 15, 20, 25, 30, 40, 50, 100, 200, 300, 400, 424]:
        pdist = math.sqrt((cur_px - bx)**2 + (cur_py - by)**2)
        target_ang = math.degrees(math.atan2(-dec_y, -dec_x))
        print(f"ht={ht:3d}: phys_dist={pdist:.3f}m, cum_phys={cum_phys_h:.3f}m, cum_int={cum_int_h:.3f}m | u=({u_h[0]:.2f},{u_h[1]:.2f}) | hd={math.degrees(hd):.1f}deg, target_ang={target_ang:.1f}deg | slipping={is_slipping}, slip_count={slip_count}")
