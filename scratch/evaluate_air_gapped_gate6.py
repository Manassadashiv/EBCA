import sys
sys.path.insert(0, '.')
import json
import math
import numpy as np
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL

# Load manifests
with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
    branches = json.load(f)

# Load air-gapped mental rollouts
mental_data = np.load('evidence/stage2_2_r2/air_gapped_mental_rollouts.npz', allow_pickle=True)
mental_rollouts = mental_data['mental_rollouts']
inv_mental_rollouts = mental_data['inv_mental_rollouts']
assert mental_data['air_gap_verified'], "FATAL: Mental rollouts not air-gap verified!"

# Run physical rollouts in MuJoCo independently
hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

s0_pos = [-1.50, -1.80]
s0_yaw = -45.0 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy()
qvel_0 = hal.data.qvel.copy()

print("--- PHYSICAL MUJOCO GROUND TRUTH EXECUTION ---")
phys_rollouts = []
for b in range(len(branches)):
    hal.reset(qpos=qpos_0, qvel=qvel_0)
    u_seq = branches[b]['actions']
    phys_s = []
    for step in range(len(u_seq)):
        hal.step(np.array(u_seq[step]))
        phys_s.append(hal.read_sensors()[:15])
    phys_rollouts.append(np.array(phys_s))

print("\n=== GATE 6 INDEPENDENT EVALUATION: AIR-GAPPED MENTAL VS REAL PHYSICAL ===")
pass_count = 0
for b in range(len(branches)):
    y_true = phys_rollouts[b].flatten()
    y_pred = mental_rollouts[b].flatten()
    y_inv = inv_mental_rollouts[b].flatten()
    
    r2 = 1.0 - np.sum((y_true - y_pred)**2) / (np.sum((y_true - np.mean(y_true))**2) + 1e-8)
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    rmse_inv = np.sqrt(np.mean((y_true - y_inv)**2))
    margin = rmse_inv - rmse
    
    name = branches[b]['name']
    status = "PASS" if (r2 >= 0.50 and margin >= 0.30) else "FAIL"
    if status == "PASS": pass_count += 1
    print(f"Branch {b:02d} ({name:22s}): R2={r2:6.4f}, RMSE={rmse:.3f}m, inv_RMSE={rmse_inv:.3f}m, margin={margin:+.3f}m [{status}]")

print(f"\nTOTAL PASSED: {pass_count} / 20")
