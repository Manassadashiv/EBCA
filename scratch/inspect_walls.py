import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=False, headless=True)
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

# Let's inspect all geoms and their positions:
print("Labyrinth Geoms:")
for i in range(hal.model.ngeom):
    name = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, i)
    if name and (name.startswith("lwall_") or name.startswith("w_") or name.startswith("wg_") or "hazard" in name):
        pos = hal.model.geom_pos[i]
        size = hal.model.geom_size[i]
        print(f"  {name:15s}: pos=({pos[0]:6.2f}, {pos[1]:6.2f}, {pos[2]:5.2f}), size=({size[0]:5.2f}, {size[1]:5.2f}, {size[2]:5.2f})")
