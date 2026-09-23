import sys
import math
import numpy as np
import mujoco
from pathlib import Path

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
engine = CARLStage2_3R1DeliberationEngine(mode="deliberative")

print("\n--- Testing Layout 2 (Right Trap) Deliberative ---")
collisions = 0
for i in range(10):
    x = -3.40 + np.random.uniform(-0.04, 0.04)
    y = -0.65 + np.random.uniform(-0.03, 0.03)
    yaw = 0.0 + np.random.uniform(-0.03, 0.03)

    hal.reset()
    hal.data.qpos[qa:qa+2] = [x, y]
    hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    engine.initialize_pose(x, y, yaw)
    collided = False
    v_est = 0.0
    last_u = np.zeros(6)

    for t in range(60):
        s = hal.read_sensors()
        sonars = s[:15]
        gyro_yaw = float(s[20])
        u_fwd = float(0.5 * (last_u[0] + last_u[1]))
        v_target = u_fwd * (engine.k_fwd / 0.030)
        v_est = 0.70 * v_est + 0.30 * v_target
        engine.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

        act, telem = engine.select_action(sonars, v_est, gyro_yaw)
        last_u = act
        hal.step(act)

        con = hal.get_carl_contact_info()
        if (con['carl_contacts'] - con['floor_contacts']) > 0:
            collided = True
            break

    if collided:
        collisions += 1
        print(f"  Trial {i}: COLLIDED at tick {t} (pos: {hal.data.qpos[qa:qa+2].round(3)})")
    else:
        final_pos = hal.data.qpos[qa:qa+2].round(3)
        dist = np.linalg.norm(final_pos - np.array([x, y]))
        print(f"  Trial {i}: SURVIVED (dist: {dist:.3f}m, branch: {telem['selected_branch']})")

print(f"Layout 2 Deliberative Collisions: {collisions}/10")
