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

print("Running Forensic Trajectory & Error Decomposition Probe...")
for k_label, k_val in [("1.200 (Previous)", 1.200), ("1.088 (Learned)", 1.088)]:
    print(f"\n========================================================")
    print(f"MODEL: {k_label}")
    print(f"========================================================")
    for seed in [42, 101, 202, 303, 404, 505, 606, 707]:
        rng = np.random.RandomState(seed)
        hal.reset()
        apply_carl_stochastic_initial_pose(hal, seed)
        
        # Babbling
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
        bx, by, byaw = diag0['pos_x'], diag0['pos_y'], diag0['yaw']
        
        # Wander
        wander_phys_dist = 0.0
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
            
            pdist = math.sqrt((diag['pos_x'] - bx)**2 + (diag['pos_y'] - by)**2)
            if pdist > wander_phys_dist:
                wander_phys_dist = pdist
                
        dec_x = multi_res['displacement_x_meters']
        dec_y = multi_res['displacement_y_meters']
        diag_w = hal.get_diagnostics()
        px_w = diag_w['pos_x'] - bx
        py_w = diag_w['pos_y'] - by
        p_dist_w = math.sqrt(px_w**2 + py_w**2)
        int_dist_w = math.sqrt(dec_x**2 + dec_y**2)
        hd_w = brain.hd_ring.decode_heading()
        yaw_w = diag_w['yaw']
        hd_err_w = math.degrees(math.atan2(math.sin(hd_w - yaw_w), math.cos(hd_w - yaw_w)))
        
        # Homing
        stopped = False
        homing_ticks = 0
        min_pdist = p_dist_w
        for ht in range(600):
            dist_home = math.sqrt(dec_x**2 + dec_y**2)
            u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, -dec_x, -dec_y, dist_home)
            if is_home:
                stopped = True
                break
            s, diag = hal.step(u_h)
            s_noisy = inject_sensor_noise(s, rng)
            res_b = brain.update_brain(u_h, s_noisy)
            hd = res_b['hd_decoded_heading']
            is_slipping = res_b['is_slipping']
            
            v_wheel = (k_val * 0.5) * (float(u_h[0]) + float(u_h[1]))
            v_grounded = v_wheel if not is_slipping else 0.0
            multi_res = multi_grid.step(v_grounded * math.cos(hd), v_grounded * math.sin(hd), slip_gated=is_slipping)
            dec_x = multi_res['displacement_x_meters']
            dec_y = multi_res['displacement_y_meters']
            
            cur_pdist = math.sqrt((diag['pos_x'] - bx)**2 + (diag['pos_y'] - by)**2)
            if cur_pdist < min_pdist:
                min_pdist = cur_pdist
            homing_ticks += 1
            
        diag_f = hal.get_diagnostics()
        px_f = diag_f['pos_x'] - bx
        py_f = diag_f['pos_y'] - by
        final_phys_drift = math.sqrt(px_f**2 + py_f**2)
        final_int_dist = math.sqrt(dec_x**2 + dec_y**2)
        hd_f = brain.hd_ring.decode_heading()
        yaw_f = diag_f['yaw']
        hd_err_f = math.degrees(math.atan2(math.sin(hd_f - yaw_f), math.cos(hd_f - yaw_f)))
        
        # Decompose error: is final drift due to premature stop, heading error, or overshoot?
        # Vector from final pos to birthplace: (-px_f, -py_f)
        # Vector along initial return direction: (-px_w, -py_w)
        # Projection of final pos onto return path
        dot_path = (px_f * px_w + py_f * py_w) / (p_dist_w**2 + 1e-9)
        # If dot_path > 0, it means robot stopped short (between wander end and origin).
        # If dot_path < 0, robot overshot past the origin.
        # Lateral error: perpendicular distance from origin-wander line
        perp_err = abs(px_f * py_w - py_f * px_w) / (p_dist_w + 1e-9)
        along_err = dot_path * p_dist_w
        
        part = "DEV" if seed in [42, 101, 202] else "UNSEEN"
        pass_str = "PASS" if final_phys_drift <= 0.22 else "FAIL"
        print(f"Seed {seed:3d} ({part:6s}) [{pass_str:4s}]:")
        print(f"   Wander Max Dist: {wander_phys_dist:.3f}m | Wander End Phys Dist: {p_dist_w:.3f}m | Int Dist: {int_dist_w:.3f}m (ratio int/phys = {int_dist_w/p_dist_w:.3f})")
        print(f"   Wander Heading Err: {hd_err_w:+.2f} deg | Final Heading Err: {hd_err_f:+.2f} deg")
        print(f"   Final Phys Drift: {final_phys_drift:.3f}m | Min Phys Dist Achieved: {min_pdist:.3f}m")
        print(f"   Final Int Dist: {final_int_dist:.3f}m | Stopped Cleanly: {stopped} ({homing_ticks} ticks)")
        print(f"   Error Breakdown: Along-path: {along_err:+.3f}m ({'SHORT' if along_err > 0 else 'OVERSHOOT'}), Lateral: {perp_err:.3f}m")
