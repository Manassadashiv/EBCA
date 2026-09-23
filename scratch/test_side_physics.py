import sys
import os
import math
import numpy as np
import mujoco

sys.path.insert(0, 'd:/ebca')
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=True)
hal.reset()

q_addr = int(hal.model.joint("spatial_identity").qposadr[0])

# 1. On its side (roll = 90 degrees):
# Quat for 90 deg roll around x: [cos(pi/4), sin(pi/4), 0, 0] = [0.7071, 0.7071, 0, 0]
hal.data.qpos[q_addr: q_addr + 3] = [0.0, 0.0, 0.15]
hal.data.qpos[q_addr + 3: q_addr + 7] = [0.7071068, 0.7071068, 0.0, 0.0]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

for _ in range(30):
    mujoco.mj_step(hal.model, hal.data)

init_x = float(hal.data.qpos[q_addr])
for t in range(60):
    s, diag = hal.step(np.array([0.20, 0.20, 0.0, 0.0, 0.0, 0.0]))

dx_side = float(hal.data.qpos[q_addr]) - init_x
w_vel_side = float(hal.data.qvel[hal.model.joint("w_left").dofadr[0]])
print(f"ON ITS SIDE (90° Roll): dx={dx_side:.4f}m, wheel_vel={w_vel_side:.3f} rad/s, roll={math.degrees(diag['roll']):.1f}°, contacts={diag['ncon']}")

# 2. Elevated / Airborne (wheels completely off ground):
hal.reset()
hal.data.qpos[q_addr + 2] = 0.50  # 50cm in the air
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

init_x = float(hal.data.qpos[q_addr])
for t in range(60):
    # keep z elevated
    hal.data.qpos[q_addr + 2] = 0.50
    hal.data.qvel[q_addr + 2] = 0.0
    s, diag = hal.step(np.array([0.20, 0.20, 0.0, 0.0, 0.0, 0.0]))

dx_air = float(hal.data.qpos[q_addr]) - init_x
w_vel_air = float(hal.data.qvel[hal.model.joint("w_left").dofadr[0]])
print(f"AIRBORNE (No Ground Contact): dx={dx_air:.4f}m, wheel_vel={w_vel_air:.3f} rad/s, contacts={diag['ncon']}")
