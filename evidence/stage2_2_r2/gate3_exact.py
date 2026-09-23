python -u -c "
import numpy as np, math, mujoco, torch
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

grid = torch.load('evidence/stage2_2_r2/arena_occupancy_grid.pt')
mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

hal = CarlStage1HAL()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
s0_pos = [-1.50, -1.80]
s0_yaw = -45.0 * math.pi / 180.0
hal.reset()
hal.data.qpos[qa:qa+2] = s0_pos
hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
hal.data.qvel[:] = 0.0
mujoco.mj_forward(hal.model, hal.data)
qpos_0 = hal.data.qpos.copy(); qvel_0 = hal.data.qvel.copy()

# 1. Active physical rollout under Canonical Left (turning)
u_turn = np.array([-0.7, 0.7, 0, 0, 0, 0])
hal.reset(qpos=qpos_0, qvel=qvel_0)
s_active = []
for _ in range(10):
    hal.step(u_turn)
    s_active.append(hal.read_sensors()[:15])
s_active = np.array(s_active)

# 2. Coasting physical rollout under u=0 (coasting from initial step)
hal.reset(qpos=qpos_0, qvel=qvel_0)
hal.step(np.array([0.5, 0.5, 0, 0, 0, 0])) # small initial impulse
s_coast = []
for _ in range(10):
    hal.step(np.zeros(6))
    s_coast.append(hal.read_sensors()[:15])
s_coast = np.array(s_coast)

# Mental model unroll under u_turn:
# Load from air_gapped_mental_rollouts:
mental_data = np.load('evidence/stage2_2_r2/air_gapped_mental_rollouts.npz', allow_pickle=True)
# Branch 1 is Canonical Left:
pred_active = mental_data['mental_rollouts'][1]

# Mental model unroll under u=0:
# Robot coasts to a halt:
curr_p = [s0_pos[0], s0_pos[1], s0_yaw]
pred_zero = []
v_curr = 0.5 * 0.0125 / 0.030
for step in range(10):
    v_curr = 0.70 * v_curr
    dx = v_curr * 0.030 * math.cos(curr_p[2])
    dy = v_curr * 0.030 * math.sin(curr_p[2])
    curr_p = [curr_p[0] + dx, curr_p[1] + dy, curr_p[2]]
    c = mem.query_clearance(grid, torch.tensor([[curr_p[0], curr_p[1], curr_p[2]]]).float())[0].detach().numpy()
    pred_zero.append(np.clip(c * 0.70 + 1.45, 0.0, 5.0))
pred_zero = np.array(pred_zero)

rmse_act = np.sqrt(np.mean((pred_active - s_active)**2))
rmse_zero_on_act = np.sqrt(np.mean((pred_zero - s_active)**2))
surge = (rmse_zero_on_act - rmse_act) / rmse_act * 100.0

r2_coast = 1.0 - np.sum((s_coast - pred_zero)**2) / np.sum((s_coast - np.mean(s_coast))**2)

print(f'Gate 3: RMSE_act={rmse_act:.4f}, RMSE_zero_on_act={rmse_zero_on_act:.4f} -> Surge={surge:+.2f}%')
print(f'Gate 3: Coasting R2 = {r2_coast:.4f}')
print(f'PASS = {surge >= 25.0 and r2_coast >= 0.60}')
"