import sys
import math
import numpy as np
import mujoco
from pathlib import Path

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

def test_reflex_in_layout1():
    hal = CarlStage1HAL()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    engine = CARLStage2_3R1DeliberationEngine(mode="reflex")

    print("\n--- Testing Layout 1 Reflex Baseline ---")
    collisions = 0
    for i in range(10):
        x = -3.07 + np.random.uniform(-0.04, 0.04)
        y = -0.20 + np.random.uniform(-0.04, 0.04)
        yaw = -math.pi/2 + np.random.uniform(-0.03, 0.03)

        hal.reset()
        hal.data.qpos[qa:qa+2] = [x, y]
        hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)

        collided = False
        for t in range(60):
            s = hal.read_sensors()
            sonars = s[:15]
            act, telem = engine.select_action(sonars, 0.0, 0.0)
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
            print(f"  Trial {i}: SURVIVED (dist: {dist:.3f}m)")

    print(f"Layout 1 Reflex Collisions: {collisions}/10")

test_reflex_in_layout1()
