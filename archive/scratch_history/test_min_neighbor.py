import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg2 = cfgs[2]

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(cfg2["spawn_pos"][0], cfg2["spawn_pos"][1], cfg2["spawn_yaw"], grid_path=str(GRID_PATH))
delib = agent.deliberation

macro = delib._compute_macro_frontier(delib.pose[0], delib.pose[1])
fx, fy, d_curr, dist_field = macro
rc_ix = int(np.clip((delib.pose[0] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))
rc_iy = int(np.clip((delib.pose[1] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))

best_d = dist_field[rc_iy, rc_ix]
best_dx, best_dy = 0, 0
for dy_step in [-1, 0, 1]:
    for dx_step in [-1, 0, 1]:
        if dx_step == 0 and dy_step == 0:
            continue
        ny = int(np.clip(rc_iy + dy_step, 0, delib.grid_size - 1))
        nx = int(np.clip(rc_ix + dx_step, 0, delib.grid_size - 1))
        d_neigh = dist_field[ny, nx]
        if not np.isinf(d_neigh) and d_neigh < best_d:
            best_d = d_neigh
            best_dx, best_dy = dx_step, dy_step

th_des = math.atan2(best_dy, best_dx)
print(f"Spawn pos: ({delib.pose[0]:.2f}, {delib.pose[1]:.2f})")
print(f"Best neighbor: dx={best_dx}, dy={best_dy}, th_des={th_des:.2f} rad ({math.degrees(th_des):.1f} deg)")
