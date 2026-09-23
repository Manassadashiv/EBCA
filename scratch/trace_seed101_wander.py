import os
import sys
import numpy as np
import math

sys.path.insert(0, ".")

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import MultiScaleGridToroid
from brain.test_stage2_1b_r3_global_space import apply_carl_stochastic_initial_pose, inject_sensor_noise

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

print("--- WANDER TRACE SEED 101 ---")
cum_phys_dist = 0.0
cum_int_dist = 0.0
prev_px, prev_py = bx, by

for t in range(350):
    u_cmd = brain.compute_wander_action(t, seed_offset=seed * 0.01)
    s, diag = hal.step(u_cmd)
    s_noisy = inject_sensor_noise(s, rng)
    res_b = brain.update_brain(u_cmd, s_noisy)
    hd = res_b['hd_decoded_heading']
    is_slipping = res_b['is_slipping']
    
    fwd_cmd = 0.5 * (float(u_cmd[0]) + float(u_cmd[1]))
    v_est = k_val * fwd_cmd
    v_grounded = v_est if not is_slipping else 0.0
    multi_res = multi_grid.step(v_grounded * math.cos(hd), v_grounded * math.sin(hd), slip_gated=is_slipping)
    
    cur_px, cur_py = diag['pos_x'], diag['pos_y']
    d_phys = math.sqrt((cur_px - prev_px)**2 + (cur_py - prev_py)**2)
    cum_phys_dist += d_phys
    cum_int_dist += v_grounded * hal.dt
    prev_px, prev_py = cur_px, cur_py
    
    if t % 50 == 0 or t == 349:
        disp_p = math.sqrt((cur_px - bx)**2 + (cur_py - by)**2)
        disp_i = math.sqrt(multi_res['displacement_x_meters']**2 + multi_res['displacement_y_meters']**2)
        yaw_phys = diag['yaw']
        hd_can = hd
        print(f"t={t:3d}: cum_phys={cum_phys_dist:.3f}m, cum_int={cum_int_dist:.3f}m | disp_phys={disp_p:.3f}m, disp_int={disp_i:.3f}m | phys_speed={diag['speed']:.3f}, v_est={v_grounded:.3f} | yaw_p={math.degrees(yaw_phys):.1f}, hd_c={math.degrees(hd_can):.1f}")
