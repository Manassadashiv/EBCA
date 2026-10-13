import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(1, seed=5101)
cfg0 = cfgs[0]

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path='brain/spatial_memory/grid_cells/saved_weights/sdr_grid_weights_20260408_012803.npz')
agent.initialize_spatial_grounding(cfg0['spawn_pos'][0], cfg0['spawn_pos'][1], cfg0['spawn_yaw'], grid_path='brain/spatial_memory/grid_cells/saved_weights/sdr_grid_weights_20260408_012803.npz')

delib = agent.deliberation
# Update occupancy memory with initial sensor read
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = cfg0['spawn_pos']
hal.data.qpos[qa+3:qa+7] = [math.cos(cfg0['spawn_yaw']/2), 0, 0, math.sin(cfg0['spawn_yaw']/2)]
mujoco.mj_forward(hal.model, hal.data)
s, _ = hal.step(np.zeros(6))
delib.update_occupancy_memory(s[:15])

macro = delib._compute_macro_frontier(delib.pose[0], delib.pose[1])
print("Macro frontier:", macro[:3] if macro else None)
if macro:
    fx, fy, d_curr, field = macro
    # Check gradient at robot position
    rc_ix = int(np.clip((delib.pose[0] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))
    rc_iy = int(np.clip((delib.pose[1] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))
    d_e = field[rc_iy, rc_ix + 1]
    d_w = field[rc_iy, rc_ix - 1]
    d_n = field[rc_iy + 1, rc_ix]
    d_s = field[rc_iy - 1, rc_ix]
    print(f"Cell ({rc_ix}, {rc_iy}): dist={d_curr:.2f}, E={d_e:.2f}, W={d_w:.2f}, N={d_n:.2f}, S={d_s:.2f}")
    gx = (d_e - d_w) / (2.0 * delib.resolution)
    gy = (d_n - d_s) / (2.0 * delib.resolution)
    print(f"Gradient: gx={gx:.2f}, gy={gy:.2f}, angle={math.atan2(-gy, -gx):.2f} rad ({math.degrees(math.atan2(-gy, -gx)):.1f} deg)")
