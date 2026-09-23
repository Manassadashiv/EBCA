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
# Flip CARL upside down: roll = 180 degrees -> quat = [0, 1, 0, 0]
# Height = 0.35m so top rests on floor and wheels point into the ceiling
hal.data.qpos[q_addr: q_addr + 3] = [0.0, 0.0, 0.35]
hal.data.qpos[q_addr + 3: q_addr + 7] = [0.0, 1.0, 0.0, 0.0]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

# Settle for 30 physics steps so it rests upside down on the floor
for _ in range(30):
    mujoco.mj_step(hal.model, hal.data)

diag = hal.get_diagnostics()
print(f"Upside down resting state: pos=({diag['pos_x']:.3f}, {diag['pos_y']:.3f}, {diag['pos_z']:.3f}), roll={math.degrees(diag['roll']):.1f}°, pitch={math.degrees(diag['pitch']):.1f}°, contacts={diag['ncon']}")

# Now command the wheels to spin at 0.20
init_x = diag['pos_x']
for t in range(60):
    s, diag = hal.step(np.array([0.20, 0.20, 0.0, 0.0, 0.0, 0.0]))

dx = diag['pos_x'] - init_x
w_vel = float(hal.data.qvel[hal.model.joint("w_left").dofadr[0]])
print(f"After 60 ticks of wheel spinning: dx={dx:.4f}m, wheel_vel={w_vel:.3f} rad/s, roll={math.degrees(diag['roll']):.1f}°, contacts={diag['ncon']}")
