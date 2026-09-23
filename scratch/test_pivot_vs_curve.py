import sys
import math
import numpy as np
import mujoco
from pathlib import Path

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL

def test_pivot_vs_curve():
    hal = CarlStage1HAL()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])

    for maneuver in ["curve_right", "pivot_right"]:
        print(f"\n--- Testing {maneuver} from tight spawn x = -2.98, y = -0.20, yaw = -pi/2 ---")
        hal.reset()
        x, y, yaw = -2.98, -0.20, -math.pi/2
        hal.data.qpos[qa:qa+2] = [x, y]
        hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)

        # Drive forward until y = -0.50, then execute maneuver
        collided = False
        for t in range(50):
            cy = hal.data.qpos[qa+1]
            if cy > -0.50:
                act = np.array([0.6, 0.6, 0, 0, 0, 0])
            else:
                if maneuver == "curve_right":
                    act = np.array([0.7, 0.1, 0, 0, 0, 0])
                else: # pivot_right
                    act = np.array([0.6, -0.6, 0, 0, 0, 0])
            hal.step(act)
            con = hal.get_carl_contact_info()
            if (con['carl_contacts'] - con['floor_contacts']) > 0:
                collided = True
                print(f"  {maneuver} COLLIDED at tick {t}, pos: {hal.data.qpos[qa:qa+2].round(3)}")
                break

        if not collided:
            print(f"  {maneuver} SURVIVED! Final pos: {hal.data.qpos[qa:qa+2].round(3)}")

test_pivot_vs_curve()
