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
hal.reset()
x, y, yaw = -3.05, -0.20, -math.pi/2
hal.data.qpos[qa:qa+2] = [x, y]
hal.data.qpos[qa+3:qa+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

engine = CARLStage2_3R1DeliberationEngine(mode="deliberative")
engine.initialize_pose(x, y, yaw)

v_est = 0.0
last_u = np.zeros(6)

for t in range(50):
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

    pos = hal.data.qpos[qa:qa+2].round(3)
    con = hal.get_carl_contact_info()
    col = (con['carl_contacts'] - con['floor_contacts']) > 0
    print(f"Tick {t:2d}: pos={pos}, branch={telem['selected_branch']:16s}, front={sonars[7]:.3f}, col={col}")
    if col:
        print(f"COLLISION at tick {t}!")
        break
