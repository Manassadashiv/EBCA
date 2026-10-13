import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import math, mujoco, numpy as np

cfgs = generate_matched_configs(30, seed=5101)
cfg2 = cfgs[2]

agent = CarlAutonomousOrganismAgent(dt=0.03, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(cfg2["spawn_pos"][0], cfg2["spawn_pos"][1], cfg2["spawn_yaw"], grid_path=str(GRID_PATH))
delib = agent.deliberation

macro = delib._compute_macro_frontier(delib.pose[0], delib.pose[1])
fx, fy, d_curr, dist_field = macro
rc_ix = int(np.clip((delib.pose[0] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))
rc_iy = int(np.clip((delib.pose[1] + delib.half_size) / delib.resolution, 0, delib.grid_size - 1))

print(f"Target f*: ({fx}, {fy})")
print("Distance field 5x5 (center is robot):")
patch = dist_field[rc_iy - 2:rc_iy + 3, rc_ix - 2:rc_ix + 3]
print(np.round(patch, 2))
