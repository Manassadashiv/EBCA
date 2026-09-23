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
k_trans = 1.088
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
print(f"diag0 yaw: {math.degrees(diag0['yaw']):.2f} deg")

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
diag_w = hal.get_diagnostics()
pyaw_w = math.degrees(diag_w['yaw'])
hd_w = math.degrees(hd)
print(f"Wander end: phys_yaw={pyaw_w:.1f}deg, decoded_hd={hd_w:.1f}deg, diff={pyaw_w - hd_w:.1f}deg")

for ht in range(430):
    dist_home = math.sqrt(dec_x**2 + dec_y**2)
    u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -dec_x, -dec_y, dist_home)
    if is_home:
        print(f"Stopped at ht={ht}")
        break
    s, diag = hal.step(u_h)
    s_noisy = inject_sensor_noise(s, rng)
    res_b = brain.update_brain(u_h, s_noisy)
    hd = res_b['hd_decoded_heading']
    v_est = (k_trans * 0.5) * (float(u_h[0]) + float(u_h[1]))
    multi_res = multi_grid.step(v_est * math.cos(hd), v_est * math.sin(hd), slip_gated=False)
    dec_x = multi_res['displacement_x_meters']
    dec_y = multi_res['displacement_y_meters']
    if ht in [0, 50, 100, 200, 300, 400, 420]:
        diag_cur = hal.get_diagnostics()
        pdist = math.sqrt((diag_cur['pos_x'] - bx)**2 + (diag_cur['pos_y'] - by)**2)
        pyaw = math.degrees(diag_cur['yaw'])
        hdeg = math.degrees(hd)
        print(f"ht={ht:3d}: pdist={pdist:.3f}m, phys_yaw={pyaw:.1f}deg, hd={hdeg:.1f}deg, diff={pyaw - hdeg:.1f}deg")
