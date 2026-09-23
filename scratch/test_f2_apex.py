import sys
sys.path.insert(0, '.')
import mujoco, numpy as np
from brain.carl_stage1_hal import CarlStage1HAL

with open('world/stage3_2_environments/family2_condA.xml') as f:
    xml_A = f.read()
with open('world/stage3_2_environments/family2_condB.xml') as f:
    xml_B = f.read()

# Replace apex pos
xml_A = xml_A.replace('pos="0.20 0.00 0.25"', 'pos="0.35 0.00 0.25"')
xml_B = xml_B.replace('pos="0.20 0.00 0.25"', 'pos="0.35 0.00 0.25"')
xml_A = xml_A.replace('pos="0.75  0.40 0.25"', 'pos="0.85  0.35 0.25"')
xml_A = xml_A.replace('pos="0.75 -0.40 0.25"', 'pos="0.85 -0.35 0.25"')
xml_B = xml_B.replace('pos="0.75  0.40 0.25"', 'pos="0.85  0.35 0.25"')
xml_B = xml_B.replace('pos="0.75 -0.40 0.25"', 'pos="0.85 -0.35 0.25"')

with open('world/stage3_2R_environments/family2_condA.xml', 'w') as f:
    f.write(xml_A)
with open('world/stage3_2R_environments/family2_condB.xml', 'w') as f:
    f.write(xml_B)

hal_A = CarlStage1HAL(xml_path='world/stage3_2R_environments/family2_condA.xml')
hal_B = CarlStage1HAL(xml_path='world/stage3_2R_environments/family2_condB.xml')
qa = int(hal_A.model.joint('spatial_identity').qposadr[0])

for name, hal in [('A', hal_A), ('B', hal_B)]:
    hal.reset()
    hal.data.qpos[qa:qa+2] = [0.0, 0.0]
    mujoco.mj_forward(hal.model, hal.data)
    wall_contacts = [
        (mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, hal.data.contact[i].geom1),
         mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, hal.data.contact[i].geom2))
        for i in range(hal.data.ncon)
        if 'floor' not in (mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, hal.data.contact[i].geom1) or '')
        and 'floor' not in (mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, hal.data.contact[i].geom2) or '')
    ]
    print(f'Cond {name} wall contacts: {len(wall_contacts)}', wall_contacts)

s_A = hal_A.read_sensors()[:15]
s_B = hal_B.read_sensors()[:15]
print('F2 Ds =', np.linalg.norm(s_A - s_B), 'max =', np.max(np.abs(s_A - s_B)))
