import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import math, numpy as np, mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

for ud in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]:
    hal.reset()
    hal.data.qpos[qa:qa+2] = [0.0, 0.0]
    hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    u_L = -0.2 - 0.5 * ud
    u_R = -0.2 + 0.5 * ud
    u = np.array([u_L, u_R, 0, 0, 0, 0])

    w_list = []
    for s in range(10):
        hal.step(u)
        w_list.append(hal.read_sensors()[20])
    print(f"u_diff={ud:4.1f} | Mean wz={np.mean(w_list):6.2f} | Ratio wz/ud={np.mean(w_list)/ud:6.2f}")
