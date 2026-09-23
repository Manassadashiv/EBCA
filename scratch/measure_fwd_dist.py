import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import math, numpy as np, mujoco
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

for uf in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8]:
    hal.reset()
    hal.data.qpos[qa:qa+2] = [0.0, 0.0]
    hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    u = np.array([uf, uf, 0, 0, 0, 0])
    for s in range(10):
        hal.step(u)
    dist = math.sqrt(hal.data.qpos[qa]**2 + hal.data.qpos[qa+1]**2)
    print(f"u_fwd={uf:4.2f} | Dist in 10 steps: {dist:6.4f}m | Eff k_fwd: {dist/(10*uf):6.4f}")
