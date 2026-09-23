import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

print("--- MEASURING LINEAR DRIVE DYNAMICS ---")
for u_val in [0.2, 0.4, 0.6, 0.8, 1.0]:
    hal.reset()
    dxs = []
    for _ in range(10):
        x0 = hal.data.qpos[qa]
        hal.step(np.array([u_val, u_val, 0, 0, 0, 0]))
        dxs.append(hal.data.qpos[qa] - x0)
    print(f"u={u_val:.1f}: mean dx/tick = {np.mean(dxs):.5f} m, steady dx/tick = {dxs[-1]:.5f} m")

print("\n--- MEASURING DIFFERENTIAL TURN DYNAMICS ---")
for diff_val in [0.2, 0.4, 0.7, 1.0, 1.4]: # u_diff = u_R - u_L
    u_L = -diff_val / 2.0
    u_R = diff_val / 2.0
    hal.reset()
    dyaws = []
    for _ in range(10):
        qw0 = hal.data.qpos[qa+3]
        qz0 = hal.data.qpos[qa+6]
        yaw0 = 2.0 * np.arctan2(qz0, qw0)
        hal.step(np.array([u_L, u_R, 0, 0, 0, 0]))
        qw1 = hal.data.qpos[qa+3]
        qz1 = hal.data.qpos[qa+6]
        yaw1 = 2.0 * np.arctan2(qz1, qw1)
        dyaw = (yaw1 - yaw0 + np.pi) % (2*np.pi) - np.pi
        dyaws.append(dyaw)
    print(f"u_diff={diff_val:.1f}: first dyaw = {dyaws[0]:.4f} rad ({dyaws[0]*180/math.pi:.1f} deg), steady dyaw = {dyaws[-1]:.4f} rad ({dyaws[-1]*180/math.pi:.1f} deg)")

print("\n--- MEASURING COASTING (u=0) DECAY ---")
# Accelerate then coast
hal.reset()
for _ in range(5):
    hal.step(np.array([0.8, 0.8, 0, 0, 0, 0]))
dxs_coast = []
for _ in range(10):
    x0 = hal.data.qpos[qa]
    hal.step(np.zeros(6))
    dxs_coast.append(hal.data.qpos[qa] - x0)
print("Coasting dx/tick after forward:", [f"{d:.5f}" for d in dxs_coast])

hal.reset()
for _ in range(5):
    hal.step(np.array([-0.7, 0.7, 0, 0, 0, 0]))
dyaws_coast = []
for _ in range(10):
    qw0 = hal.data.qpos[qa+3]
    qz0 = hal.data.qpos[qa+6]
    yaw0 = 2.0 * np.arctan2(qz0, qw0)
    hal.step(np.zeros(6))
    qw1 = hal.data.qpos[qa+3]
    qz1 = hal.data.qpos[qa+6]
    yaw1 = 2.0 * np.arctan2(qz1, qw1)
    dyaw = (yaw1 - yaw0 + np.pi) % (2*np.pi) - np.pi
    dyaws_coast.append(dyaw)
print("Coasting dyaw/tick after turn:", [f"{d:.5f}" for d in dyaws_coast])
