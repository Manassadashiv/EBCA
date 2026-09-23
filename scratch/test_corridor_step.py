import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=False, headless=True)
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Place at WP 1: (-1.5, 1.2, yaw = -pi/2)
hal.data.qpos[qa:qa+2] = [-1.5, 1.2]
yaw = -math.pi / 2
hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
mujoco.mj_forward(hal.model, hal.data)

print("Starting from WP 1:", hal.data.qpos[qa:qa+2])
s = hal.read_sensors()
sonars = s[:15]
print("Sonars facing south from (-1.5, 1.2):", np.round(sonars, 2))

# Drive south for 50 steps:
dt = hal.dt
pose_hat = np.array([-1.5, 1.2, yaw])
for step in range(50):
    u = np.zeros(6)
    u[0] = 0.20
    u[1] = 0.20
    s_next, _ = hal.step(u)
    omega_z = s_next[20]
    pose_hat[2] += omega_z * dt
    dx = 0.20 * 0.9875 * dt
    pose_hat[0] += dx * math.cos(pose_hat[2])
    pose_hat[1] += dx * math.sin(pose_hat[2])
    if step % 10 == 0:
        true_pos = hal.data.qpos[qa:qa+2]
        print(f"Step {step}: True=({true_pos[0]:.3f}, {true_pos[1]:.3f}), Hat=({pose_hat[0]:.3f}, {pose_hat[1]:.3f}), Gyro={omega_z:.4f}")
