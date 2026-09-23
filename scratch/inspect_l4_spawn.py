import sys
import math
from pathlib import Path
import numpy as np

repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
import mujoco

hal = CarlStage1HAL()
qa = int(hal.model.joint("spatial_identity").qposadr[0])

# Place at layout 4 spawn
x, y, yaw = -2.50, 2.25, 0.0
hal.reset()
hal.data.qpos[qa:qa + 2] = [x, y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

s = hal.read_sensors()
sonars = s[:15]
print("Layout 4 initial sonars:", np.round(sonars, 3))
print("Front sonars (6,7,8):", np.round(sonars[6:9], 3))
print("Right flank (0:4):", np.round(sonars[0:4], 3))
print("Left flank (11:15):", np.round(sonars[11:15], 3))

# Look at contacts
con = hal.get_carl_contact_info()
print("Contacts at spawn:", con)
