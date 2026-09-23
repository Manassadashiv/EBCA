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

print("=" * 80)
print("TESTING WITHOUT FALSE SLIP GATING ON OPEN SPACE FLOOR (mu=0.8)")
print("=" * 80)

for label, k_trans in [("1.200 (Previous)", 1.200), ("1.088 (Learned)", 1.088)]:
    print(f"\n--- MODEL: {label} ---")
    drifts = []
    for seed in [42, 101, 202, 303, 404, 505, 606, 707]:
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
        
        homing_ticks = 0
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
            homing_ticks += 1
            
        diag_f = hal.get_diagnostics()
        final_drift = math.sqrt((diag_f['pos_x'] - bx)**2 + (diag_f['pos_y'] - by)**2)
        drifts.append(final_drift)
        p_str = "PASS" if final_drift <= 0.22 else "FAIL"
        part = "DEV" if seed in [42, 101, 202] else "UNSEEN"
        print(f"Seed {seed:3d} ({part:6s}): drift={final_drift:.3f}m [{p_str:4s}] in {homing_ticks:3d} ticks")
        
    drifts = np.array(drifts)
    dev = drifts[:3]
    unseen = drifts[3:]
    print(f"OVERALL: Mean={np.mean(drifts):.3f}m, Passes={np.sum(drifts <= 0.22)}/8")
    print(f"UNSEEN:  Mean={np.mean(unseen):.3f}m, Median={np.median(unseen):.3f}m, Passes={np.sum(unseen <= 0.22)}/5")
