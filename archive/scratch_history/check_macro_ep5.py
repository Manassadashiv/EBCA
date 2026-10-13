import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg5 = cfgs[5]

spawn_x, spawn_y = cfg5["spawn_pos"]
spawn_yaw = cfg5["spawn_yaw"]

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

delib = agent.deliberation
print("Spawn:", spawn_x, spawn_y, spawn_yaw)
macro = delib._compute_macro_frontier(delib.pose[0], delib.pose[1])
print("Macro frontier at spawn:", macro[:3] if macro else None)
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
    print(f"Gradient: gx={gx:.2f}, gy={gy:.2f}, th_des={math.atan2(-gy, -gx):.2f} ({math.degrees(math.atan2(-gy, -gx)):.1f} deg)")
