import sys
import json
import math
from pathlib import Path
import numpy as np
import mujoco

repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
px, py, pyaw = -1.5, -1.8, -45.0 * math.pi / 180.0

# Reset and position
hal.reset()
hal.data.qpos[qa:qa+2] = [px, py]
hal.data.qpos[qa+3:qa+7] = [math.cos(pyaw/2), 0, 0, math.sin(pyaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

# Settle for 15 steps at u=0
for _ in range(15):
    hal.step([0]*6)

qpos_settled = hal.data.qpos.copy()
qvel_settled = hal.data.qvel.copy()

print(f"Settled contact info: {hal.get_carl_contact_info()}")
print(f"Settled pose: x={qpos_settled[qa]:.4f}, y={qpos_settled[qa+1]:.4f}, z={qpos_settled[qa+2]:.4f}")

# Now test Branch 7 with settled initial state
branches = json.load(open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json'))
u_seq = branches[7]['actions']

hal.reset(qpos=qpos_settled, qvel=qvel_settled)
print("\nRunning Branch 7 from settled equilibrium:")
for s, u in enumerate(u_seq):
    hal.step(u)
    info = hal.get_carl_contact_info()
    x = hal.data.qpos[qa]
    y = hal.data.qpos[qa+1]
    qw, qz = hal.data.qpos[qa+3], hal.data.qpos[qa+6]
    yaw = 2.0 * math.atan2(qz, qw) * 180.0 / math.pi
    print(f"s={s:2d}: pos=[{x:.3f}, {y:.3f}], yaw={yaw:6.1f} deg | tire contacts: {info['tire_floor_contacts']}")
