import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import numpy as np
from brain.carl_stage1_hal import CarlStage1HAL
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)
q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
print(f"spatial_identity q_addr: {q_addr}")
for j in range(hal.model.njnt):
    name = hal.model.joint(j).name
    qa = hal.model.jnt_qposadr[j]
    print(f"Joint {j}: {name}, qposadr: {qa}")

for seed in [303, 404, 505, 606, 707]:
    hal.reset()
    s0, d0 = hal.step(np.zeros(6))
    qpos_before = hal.data.qpos.copy()
    yaw_before = d0["yaw"]
    
    apply_stochastic_initial_pose(hal, seed)
    s1, d1 = hal.step(np.zeros(6))
    qpos_after = hal.data.qpos.copy()
    yaw_after = d1["yaw"]
    
    print(f"Seed {seed}:")
    print(f"  qpos[0:3] before: {qpos_before[0:3]}, yaw before: {yaw_before:.4f}")
    print(f"  qpos[0:3] after:  {qpos_after[0:3]}, yaw after:  {yaw_after:.4f}")
    print(f"  qpos[3:7] after (quaternion): {qpos_after[3:7]}")
