import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(1, seed=5101)
cfg0 = cfgs[0]

hal.reset()
sx, sy = cfg0['spawn_pos']
syaw = cfg0['spawn_yaw']
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path='brain/spatial_memory/grid_cells/saved_weights/sdr_grid_weights_20260408_012803.npz')
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path='brain/spatial_memory/grid_cells/saved_weights/sdr_grid_weights_20260408_012803.npz')

# Pivot for 30 steps
for t in range(35):
    # Pure pivot
    s, diag = hal.step(np.array([0.8, -0.8, 0, 0, 0, 0]))
    agent.deliberation.update_odometry(v_wheel=0.0, w_gyro=-3.5, dt=hal.dt)
    agent.deliberation.update_occupancy_memory(s[:15])

delib = agent.deliberation
print(f"After pivot: pos=({diag['pos_x']:.2f}, {diag['pos_y']:.2f}), yaw={diag['yaw']:.2f}, delib_th={delib.pose[2]:.2f}")
macro = delib._compute_macro_frontier(delib.pose[0], delib.pose[1])
print("Macro frontier after pivot:", macro[:3] if macro else None)
if macro:
    fx, fy, d_curr, field = macro
    rc_ix = int(np.clip((delib.pose[0] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))
    rc_iy = int(np.clip((delib.pose[1] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))
    d_e = field[rc_iy, rc_ix + 1]
    d_w = field[rc_iy, rc_ix - 1]
    d_n = field[rc_iy + 1, rc_ix]
    d_s = field[rc_iy - 1, rc_ix]
    gx = (d_e - d_w) / (2.0 * delib.resolution)
    gy = (d_n - d_s) / (2.0 * delib.resolution)
    print(f"Gradient: gx={gx:.2f}, gy={gy:.2f}, angle={math.atan2(-gy, -gx):.2f} rad ({math.degrees(math.atan2(-gy, -gx)):.1f} deg)")
