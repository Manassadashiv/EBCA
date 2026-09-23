import sys
sys.path.insert(0, '.')
import json
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

hal = CarlStage1HAL()
hal.reset()
hal.set_floor_friction(1.0)
qa = int(hal.model.joint('spatial_identity').qposadr[0])

s0_pos = [-0.15, 0.96]
s0_yaw = -95.4 * math.pi / 180.0

hal.reset()
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

print("=== PHYSICAL TRAJECTORIES FOR 20 BRANCHES ===")
for b in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = np.array(branches[b]['actions'])
    H = len(u_seq)
    
    poses = []
    for step in range(H):
        hal.step(u_seq[step])
        qw = hal.data.qpos[qa+3]
        qz = hal.data.qpos[qa+6]
        yaw = 2.0 * np.arctan2(qz, qw)
        x = hal.data.qpos[qa]
        y = hal.data.qpos[qa+1]
        poses.append([x, y, yaw])
    poses = np.array(poses)
    dx_tot = poses[-1, 0] - s0_pos[0]
    dy_tot = poses[-1, 1] - s0_pos[1]
    dyaw_tot = (poses[-1, 2] - s0_yaw + np.pi) % (2*np.pi) - np.pi
    dist = np.sqrt(dx_tot**2 + dy_tot**2)
    print(f"Branch {b:02d} ({branches[b]['name']:22s}): dist={dist:.3f}m, dx={dx_tot:+.3f}m, dy={dy_tot:+.3f}m, dyaw={dyaw_tot*180/math.pi:+.1f} deg")
