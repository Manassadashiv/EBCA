import sys
sys.path.insert(0, '.')
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
print("Number of geoms:", hal.model.ngeom)
print("Number of bodies:", hal.model.nbody)

for i in range(hal.model.ngeom):
    name = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, i)
    body_id = hal.model.geom_bodyid[i]
    body_name = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
    pos = hal.model.geom_pos[i]
    size = hal.model.geom_size[i]
    gtype = hal.model.geom_type[i]
    if body_id not in hal.carl_body_ids and name != "floor":
        print(f"Geom {i:2d} ({name:20s}) in Body {body_id:2d} ({body_name:20s}): pos={pos}, size={size[:3]}, type={gtype}")
