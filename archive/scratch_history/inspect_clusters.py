import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
from scipy.ndimage import label, binary_dilation
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg5 = cfgs[5]

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(cfg5["spawn_pos"][0], cfg5["spawn_pos"][1], cfg5["spawn_yaw"], grid_path=str(GRID_PATH))

delib = agent.deliberation
free_explored = (delib.grid_np[1] >= 0.50) & (delib.grid_np[0] < 0.30)
unexplored = (delib.grid_np[1] < 0.50)
pad_unexp = np.pad(unexplored, 1, mode='constant', constant_values=False)
has_unexp_neighbor = (
    pad_unexp[:-2, :-2] | pad_unexp[:-2, 1:-1] | pad_unexp[:-2, 2:] |
    pad_unexp[1:-1, :-2]                        | pad_unexp[1:-1, 2:] |
    pad_unexp[2:, :-2]  | pad_unexp[2:, 1:-1]  | pad_unexp[2:, 2:]
)
obs_mask = (delib.grid_np[0] >= 0.30)
near_obs = binary_dilation(obs_mask, structure=np.ones((5, 5), dtype=bool))
frontier_mask = free_explored & has_unexp_neighbor & (~near_obs)

lbl, num_features = label(frontier_mask, structure=np.ones((3, 3)))
print(f"Number of frontier clusters: {num_features}")
for k in range(1, num_features + 1):
    py, px = np.where(lbl == k)
    fwx = px * delib.resolution - delib.half_size
    fwy = py * delib.resolution - delib.half_size
    mean_x = float(fwx.mean())
    mean_y = float(fwy.mean())
    dist = math.hypot(mean_x - delib.pose[0], mean_y - delib.pose[1])
    print(f"Cluster {k}: size={len(py)}, center=({mean_x:.2f}, {mean_y:.2f}), dist={dist:.2f}")
