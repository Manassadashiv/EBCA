import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Canonical Left: u = [-0.7, 0.7]
yaws = []
for step in range(10):
    hal.step(np.array([-0.7, 0.7, 0, 0, 0, 0]))
    qw = hal.data.qpos[qa+3]
    qz = hal.data.qpos[qa+6]
    yaw = 2.0 * np.arctan2(qz, qw)
    yaws.append(yaw)

print("Canonical Left yaws (rad):", [f"{y:.3f}" for y in yaws])
print("Canonical Left dyaw (deg/tick):", [f"{(yaws[i] - (yaws[i-1] if i > 0 else 0))*180/math.pi:.1f}" for i in range(len(yaws))])
