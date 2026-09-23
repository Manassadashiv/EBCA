import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

from brain.carl_stage1_hal import CarlStage1HAL
import json, math, mujoco

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
px, py, pyaw = -1.5, -1.8, -45.0 * math.pi / 180.0
hal.data.qpos[qa:qa+2] = [px, py]
hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

branches = json.load(open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json'))
u_seq = branches[7]['actions']

print("Running Branch 4...")
for s, u in enumerate(u_seq):
    hal.step(u)
    contacting = set()
    for i in range(hal.data.ncon):
        g1 = hal.model.geom(hal.data.contact[i].geom1).name
        g2 = hal.model.geom(hal.data.contact[i].geom2).name
        other = g1 if g2 == 'floor' else (g2 if g1 == 'floor' else f"{g1}<->{g2}")
        contacting.add(other)
    hip_p = hal.data.qpos[hal.model.joint('hip_pitch').qposadr[0]]
    hip_r = hal.data.qpos[hal.model.joint('hip_roll').qposadr[0]]
    print(f"s={s:2d}: contacting: {contacting} | hip_pitch={hip_p:.3f}, hip_roll={hip_r:.3f}")
