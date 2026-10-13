import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
from scipy.ndimage import label, binary_dilation
import math, mujoco, numpy as np

cfgs = generate_matched_configs(30, seed=5101)
cfg0 = cfgs[0]

agent = CarlAutonomousOrganismAgent(dt=0.03, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(cfg0["spawn_pos"][0], cfg0["spawn_pos"][1], cfg0["spawn_yaw"], grid_path=str(GRID_PATH))
delib = agent.deliberation

# Let's inspect frontier_mask
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

# Print all valid frontier cells
fy, fx = np.where(frontier_mask)
fwx = fx * delib.resolution - delib.half_size
fwy = fy * delib.resolution - delib.half_size

print(f"Total frontier cells: {len(fx)}")
for x, y in zip(fwx, fwy):
    print(f"  ({x:.2f}, {y:.2f})")
