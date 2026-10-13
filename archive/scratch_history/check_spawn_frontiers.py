import sys
sys.path.insert(0, ".")
import torch
import numpy as np
from pathlib import Path
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

ENV_DIR = Path("world/stage3_4_environments")
GRID_PATH = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"

agent = CarlAutonomousOrganismAgent(
    dt=0.03,
    deliberation_mode="active_inference",
    grid_path=str(GRID_PATH)
)
spawn_x, spawn_y, spawn_yaw = 0.58, 0.0, 0.0
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

# Let's see what frontiers exist at spawn
c_x, c_y = spawn_x, spawn_y
free_explored = (agent.deliberation.grid_np[1] >= 0.50) & (agent.deliberation.grid_np[0] < 0.30)
unexplored = (agent.deliberation.grid_np[1] < 0.50)

from scipy.ndimage import binary_dilation, label
pad_unexp = np.pad(unexplored, 1, mode='constant', constant_values=False)
has_unexp_neighbor = (
    pad_unexp[:-2, :-2] | pad_unexp[:-2, 1:-1] | pad_unexp[:-2, 2:] |
    pad_unexp[1:-1, :-2]                        | pad_unexp[1:-1, 2:] |
    pad_unexp[2:, :-2]  | pad_unexp[2:, 1:-1]  | pad_unexp[2:, 2:]
)
obs_mask = (agent.deliberation.grid_np[0] >= 0.30)
near_obs = binary_dilation(obs_mask, structure=np.ones((5, 5), dtype=bool))
frontier_mask = free_explored & has_unexp_neighbor & (~near_obs)

lbl, num_features = label(frontier_mask, structure=np.ones((3, 3)))
print(f"Number of frontier clusters at spawn: {num_features}")

rc_ix = int(np.clip((c_x + agent.deliberation.half_size) / agent.deliberation.resolution, 0, agent.deliberation.grid_size - 1))
rc_iy = int(np.clip((c_y + agent.deliberation.half_size) / agent.deliberation.resolution, 0, agent.deliberation.grid_size - 1))
traversable = (agent.deliberation.grid_np[0] < 0.85)
robot_dist = agent.deliberation._compute_geodesic_field(traversable, rc_iy, rc_ix, max_iters=32)

for k in range(1, num_features + 1):
    py, px = np.where(lbl == k)
    geo_dists = robot_dist[py, px]
    min_geo = float(np.min(geo_dists))
    fwx = px * agent.deliberation.resolution - agent.deliberation.half_size
    fwy = py * agent.deliberation.resolution - agent.deliberation.half_size
    print(f"Cluster {k}: size={len(py)}, center=({fwx.mean():.2f}, {fwy.mean():.2f}), min_geo={min_geo:.2f}")
