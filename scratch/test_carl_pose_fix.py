import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor

def apply_carl_stochastic_initial_pose(hal: CarlStage1HAL, seed: int):
    rng = np.random.RandomState(seed)
    jitter_x = rng.uniform(-0.06, 0.06)
    jitter_y = rng.uniform(-0.06, 0.06)
    jitter_yaw = rng.uniform(-math.pi / 3.0, math.pi / 3.0)  # [-60 deg, +60 deg]
    q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[q_addr] = jitter_x
    hal.data.qpos[q_addr + 1] = jitter_y
    hal.data.qpos[q_addr + 2] = 0.05291
    hal.data.qpos[q_addr + 3] = math.cos(jitter_yaw / 2.0)
    hal.data.qpos[q_addr + 4] = 0.0
    hal.data.qpos[q_addr + 5] = 0.0
    hal.data.qpos[q_addr + 6] = math.sin(jitter_yaw / 2.0)
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)
    hal.step(np.zeros(6))
    return jitter_x, jitter_y, jitter_yaw

hal = CarlStage1HAL(open_space=True)
print("Verifying apply_carl_stochastic_initial_pose across unseen seeds [303, 404, 505, 606, 707]:")
for seed in [303, 404, 505, 606, 707]:
    hal.reset()
    jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, seed)
    diag = hal.get_diagnostics()
    print(f"Seed {seed:3d}: Target (x={jx:+.4f}, y={jy:+.4f}, yaw={math.degrees(jyaw):+6.2f}°) | "
          f"Diag (x={diag['pos_x']:+.4f}, y={diag['pos_y']:+.4f}, yaw={math.degrees(diag['yaw']):+6.2f}°, z={diag['pos_z']:.4f})")
