import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import math, numpy as np, mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

def test_turn(u_fwd, u_diff, steps=10):
    hal.reset()
    hal.data.qpos[qa:qa+2] = [0.0, 0.0]
    hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    u_L = u_fwd - 0.5 * u_diff
    u_R = u_fwd + 0.5 * u_diff
    u = np.array([u_L, u_R, 0, 0, 0, 0])

    yaws = []
    w_gyros = []
    for s in range(steps):
        hal.step(u)
        qw, qz = hal.data.qpos[qa+3], hal.data.qpos[qa+6]
        yaws.append(2.0 * math.atan2(qz, qw) * 180.0 / math.pi)
        w_gyros.append(hal.read_sensors()[20])
    return yaws, w_gyros

y_fwd, w_fwd = test_turn(0.3, 0.8)
y_rev, w_rev = test_turn(-0.3, 0.8)
y_spin, w_spin = test_turn(0.0, 0.8)

print("FORWARD + TURN (u_fwd=+0.3, u_diff=+0.8):")
print(f"Total yaw turned: {y_fwd[-1]:.1f} deg | Mean wz: {np.mean(w_fwd):.2f} rad/s")

print("\nREVERSE + TURN (u_fwd=-0.3, u_diff=+0.8):")
print(f"Total yaw turned: {y_rev[-1]:.1f} deg | Mean wz: {np.mean(w_rev):.2f} rad/s")

print("\nIN-PLACE SPIN (u_fwd=0.0, u_diff=+0.8):")
print(f"Total yaw turned: {y_spin[-1]:.1f} deg | Mean wz: {np.mean(w_spin):.2f} rad/s")
