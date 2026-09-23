import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128)
vps = [(-1.5, -1.5), (-1.5, 0), (-1.5, 1.5), (0, -1.5), (0, 0), (0, 1.5), (1.5, -1.5), (1.5, 0), (1.5, 1.5)]
for vx, vy in vps:
    for angle in np.linspace(-np.pi, np.pi, 24, endpoint=False):
        hal.data.qpos[qa:qa+2] = [vx, vy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(angle/2), 0, 0, math.sin(angle/2)]
        mujoco.mj_forward(hal.model, hal.data)
        s = hal.read_sensors()[:15]
        grid = mem.accumulate_observations(grid, torch.tensor([[vx, vy, angle]]).float(), torch.tensor(s).unsqueeze(0).float())

s0_pos = [-2.00, -1.60]
s0_yaw = 67.5 * math.pi / 180.0

hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)

print("--- CANONICAL FORWARD STEP-BY-STEP FORENSICS ---")
u_fwd = np.array([0.8, 0.8, 0, 0, 0, 0])

curr_pose = [s0_pos[0], s0_pos[1], s0_yaw]
dt = 0.030
k_fwd = 0.0125
gamma_v = 0.70
prev_v = 0.0

for step in range(10):
    hal.step(u_fwd)
    qw = hal.data.qpos[qa+3]
    qz = hal.data.qpos[qa+6]
    yaw_p = 2.0 * np.arctan2(qz, qw)
    xp = hal.data.qpos[qa]
    yp = hal.data.qpos[qa+1]
    s_phys = hal.read_sensors()[:15]
    
    # Mental
    v_target = 0.8 * k_fwd / dt
    next_v = 0.30 * prev_v + 0.70 * v_target
    dx_l = next_v * dt
    th = curr_pose[2]
    curr_pose = [curr_pose[0] + dx_l * math.cos(th), curr_pose[1] + dx_l * math.sin(th), curr_pose[2]]
    prev_v = next_v
    
    clr = mem.query_clearance(grid, torch.tensor([[curr_pose[0], curr_pose[1], curr_pose[2]]]).float())[0].detach().numpy()
    
    # Also query at physical pose to see if error is from pose or from map!
    clr_at_phys = mem.query_clearance(grid, torch.tensor([[xp, yp, yaw_p]]).float())[0].detach().numpy()
    
    err_mental = np.mean(np.abs(s_phys - clr))
    err_phys_pose = np.mean(np.abs(s_phys - clr_at_phys))
    pose_err = math.sqrt((xp - curr_pose[0])**2 + (yp - curr_pose[1])**2)
    
    print(f"Step {step:02d}: pos_err={pose_err:.3f}m | Sonar Err (Mental Pose)={err_mental:.3f}m | Sonar Err (Phys Pose)={err_phys_pose:.3f}m")
    if step == 9:
        print("  s_phys:", [round(x, 2) for x in s_phys[:8]])
        print("  clr_mental:", [round(x, 2) for x in clr[:8]])
        print("  clr_phys:", [round(x, 2) for x in clr_at_phys[:8]])
