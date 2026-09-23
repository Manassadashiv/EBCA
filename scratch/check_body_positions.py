import sys
sys.path.insert(0, '.')
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
hal.reset()
for b_id in range(hal.model.nbody):
    name = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_BODY, b_id)
    pos = hal.data.xpos[b_id]
    print(f"Body {b_id:2d} ({name:20s}): xpos={pos}")
