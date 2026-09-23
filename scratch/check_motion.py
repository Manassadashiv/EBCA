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
hal.data.qpos[qa:qa+2] = [-3.05, -0.20]
yaw = -math.pi/2
hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

for t in range(20):
    s, _ = hal.step(np.array([0.8, 0.8, 0, 0, 0, 0]))
    pos = hal.data.qpos[qa:qa+2].round(3)
    front_sonar = s[7]
    print(f"Tick {t:2d}: pos={pos}, front_sonar={front_sonar:.3f}")
