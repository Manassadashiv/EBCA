import sys
import math
import numpy as np
import mujoco
from pathlib import Path

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.reset()
x, y, yaw = -3.40, -0.672, 0.0
hal.data.qpos[qa:qa+2] = [x, y]
hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

print(f"Number of contacts: {hal.data.ncon}")
for i in range(hal.data.ncon):
    c = hal.data.contact[i]
    g1 = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1)
    g2 = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)
    dist = c.dist
    print(f"  Contact {i}: {g1} <-> {g2}, dist={dist:.5f}")
