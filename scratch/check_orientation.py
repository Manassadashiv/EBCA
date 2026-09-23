import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

for angle_deg in [0, 90, -90, 180]:
    angle = angle_deg * math.pi / 180.0
    hal.reset()
    hal.data.qpos[qa:qa+2] = [0.0, 0.0]
    hal.data.qpos[qa+3:qa+7] = [math.cos(angle/2), 0, 0, math.sin(angle/2)]
    mujoco.mj_forward(hal.model, hal.data)
    
    # Check orientation from quaternion
    qw = hal.data.qpos[qa+3]
    qz = hal.data.qpos[qa+6]
    yaw = 2.0 * np.arctan2(qz, qw)
    
    # Step forward
    hal.step(np.array([0.8, 0.8, 0, 0, 0, 0]))
    x1, y1 = hal.data.qpos[qa], hal.data.qpos[qa+1]
    dx = x1 - 0.0
    dy = y1 - 0.0
    print(f"Angle={angle_deg:4d} deg: yaw={yaw*180/math.pi:6.1f} deg, dx={dx:+.4f}, dy={dy:+.4f}, expected dx={0.0104*math.cos(angle):+.4f}, dy={0.0104*math.sin(angle):+.4f}")
