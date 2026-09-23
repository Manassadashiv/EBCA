"""
scratch/check_uturning_omega.py — Check physical omega during u_turning
"""
import sys
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)
u_turning = np.array([0.12, -0.06, 0, 0, 0, 0])

for seed in [42, 101, 202, 303, 404, 505, 606, 707]:
    hal.reset()
    apply_stochastic_initial_pose(hal, seed)

    # Step for 30 ticks normal driving
    omegas = []
    yaws = []
    for _ in range(40):
        s, diag = hal.step(u_turning)
        omegas.append(s[20])  # yaw gyro
        yaws.append(diag["yaw"])

    steady_omega = np.mean(omegas[10:])
    diff_u = u_turning[1] - u_turning[0]  # -0.06 - 0.12 = -0.18
    k_eff_direct = steady_omega / diff_u
    total_yaw_change = yaws[-1] - yaws[10]
    integrated_omega = steady_omega * 30 * hal.dt
    print(f"Seed {seed:3d}: diff_u={diff_u:+.2f}, steady_omega={steady_omega:+.4f} rad/s, "
          f"k_eff = {k_eff_direct:+.4f}, delta_yaw={total_yaw_change:+.4f} rad vs integ={integrated_omega:+.4f} rad")
