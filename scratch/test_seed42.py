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
seed = 42

for k_trans in [1.200, 1.088]:
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
        v_est = (k_trans * 0.5) * (float(u_cmd[0]) + float(u_cmd[1]))
        multi_res = multi_grid.step(v_est * math.cos(hd), v_est * math.sin(hd), slip_gated=False)
        
    dec_x = multi_res['displacement_x_meters']
    dec_y = multi_res['displacement_y_meters']
    dw = hal.get_diagnostics()
    p_dist = math.sqrt((dw['pos_x']-bx)**2 + (dw['pos_y']-by)**2)
    i_dist = math.sqrt(dec_x**2 + dec_y**2)
    print(f"k={k_trans}: Wander end phys=({dw['pos_x']-bx:.3f}, {dw['pos_y']-by:.3f}) dist={p_dist:.3f} | int=({dec_x:.3f}, {dec_y:.3f}) dist={i_dist:.3f}")

    for ht in range(600):
        dist_home = math.sqrt(dec_x**2 + dec_y**2)
        u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -dec_x, -dec_y, dist_home)
        if is_home:
            break
        s, diag = hal.step(u_h)
        s_noisy = inject_sensor_noise(s, rng)
        res_b = brain.update_brain(u_h, s_noisy)
        hd = res_b['hd_decoded_heading']
        v_est = (k_trans * 0.5) * (float(u_h[0]) + float(u_h[1]))
        multi_res = multi_grid.step(v_est * math.cos(hd), v_est * math.sin(hd), slip_gated=False)
        dec_x = multi_res['displacement_x_meters']
        dec_y = multi_res['displacement_y_meters']

    df = hal.get_diagnostics()
    fdrift = math.sqrt((df['pos_x']-bx)**2 + (df['pos_y']-by)**2)
    print(f"k={k_trans}: Homing end drift={fdrift:.3f}m, int=({dec_x:.3f}, {dec_y:.3f}) dist={math.sqrt(dec_x**2+dec_y**2):.3f} in {ht} ticks")
