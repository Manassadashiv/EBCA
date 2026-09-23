import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import numpy as np
from brain.carl_stage1_hal import CarlStage1HAL
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)
q_addr = int(hal.model.joint("spatial_identity").qposadr[0])

print(f"=== FORENSIC PROBE: CARL vs TOY CUBE QPOS ===")
print(f"Spatial identity (CARL) qposadr: {q_addr}")

for seed in [303, 404, 505, 606, 707]:
    hal.reset()
    carl_qpos_reset = hal.data.qpos[q_addr:q_addr+7].copy()
    cube_qpos_reset = hal.data.qpos[0:7].copy()
    
    apply_stochastic_initial_pose(hal, seed)
    
    carl_qpos_after_jitter = hal.data.qpos[q_addr:q_addr+7].copy()
    cube_qpos_after_jitter = hal.data.qpos[0:7].copy()
    diag = hal.get_diagnostics()
    
    print(f"\n--- Seed {seed} ---")
    print(f"Cube qpos[0:3] before: {cube_qpos_reset[0:3]} -> after: {cube_qpos_after_jitter[0:3]}")
    print(f"Cube qpos[3:7] (quat) before: {cube_qpos_reset[3:7]} -> after: {cube_qpos_after_jitter[3:7]}")
    print(f"CARL qpos[22:25] before: {carl_qpos_reset[0:3]} -> after: {carl_qpos_after_jitter[0:3]}")
    print(f"CARL qpos[25:29] before: {carl_qpos_reset[3:7]} -> after: {carl_qpos_after_jitter[3:7]}")
    print(f"CARL diag yaw: {diag['yaw']:.6f} rad ({math.degrees(diag['yaw']):.4f} deg)")
