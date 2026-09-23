import json
import math
from pathlib import Path
import numpy as np
import mujoco
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
qv = int(hal.model.joint('spatial_identity').dofadr[0])
px, py, pyaw = -1.5, -1.8, -45.0 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = [px, py]
hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

for b_idx in [4, 5, 7, 8, 15]:
    b_name = branches[b_idx]['name']
    u_seq = branches[b_idx]['actions']
    hal.data.qpos[qa:qa+2] = [px, py]
    hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    print(f"\n--- Branch {b_idx}: {b_name} ---")
    for s in range(len(u_seq)):
        w_gyro = hal.read_sensors()[20]
        # read chassis body velocity
        vx, vy, vz = hal.data.qvel[qv:qv+3]
        wx, wy, wz = hal.data.qvel[qv+3:qv+6]
        u = u_seq[s]
        u_fwd = 0.5 * (u[0] + u[1])
        u_diff = u[1] - u[0]
        print(f"s={s:2d} | u_fwd={u_fwd:5.2f} u_diff={u_diff:5.2f} | w_gyro={w_gyro:6.2f} wz={wz:6.2f} | ncon={hal.data.ncon}")
        hal.step(u)
