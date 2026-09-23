import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from brain.carl_stage1_hal import CarlStage1HAL
import mujoco

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
px, py, pyaw_deg = -1.5, -1.8, -45.0
pyaw = pyaw_deg * math.pi / 180.0
hal.data.qpos[qa:qa+2] = [px, py]
hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

with open("evidence/stage2_2_r2/manifests/frozen_branch_sequences.json") as f:
    import json
    branches = json.load(f)

b7_actions = branches[7]['actions']
print(f"Branch 07: {len(b7_actions)} steps")

for step in range(len(b7_actions)):
    u = b7_actions[step]
    hal.step(u)
    # Check contacts
    ncon = hal.data.ncon
    contacts = []
    for c in range(ncon):
        con = hal.data.contact[c]
        g1 = hal.model.geom(con.geom1).name
        g2 = hal.model.geom(con.geom2).name
        contacts.append(f"{g1} <-> {g2}")
    
    pos = hal.data.qpos[qa:qa+2]
    print(f"step {step:2d}: pos=({pos[0]:.3f}, {pos[1]:.3f}) | ncon={ncon}, contacts={contacts[:2]}")
