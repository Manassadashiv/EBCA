import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=True, headless=True)
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Step forward with u = 0.20 for 100 ticks:
u = np.zeros(6)
u[0] = 0.20
u[1] = 0.20

x0 = float(hal.data.qpos[qa])
y0 = float(hal.data.qpos[qa+1])
dt = hal.dt

for t in range(100):
    hal.step(u)

x1 = float(hal.data.qpos[qa])
y1 = float(hal.data.qpos[qa+1])
dx = math.hypot(x1 - x0, y1 - y0)
total_time = 100 * dt
v_meas = dx / total_time
linear_gain = v_meas / 0.20

print(f"Total time: {total_time:.3f} s, dx: {dx:.4f} m")
print(f"Measured forward velocity: {v_meas:.4f} m/s")
print(f"Linear gain (v / u): {linear_gain:.4f}")
