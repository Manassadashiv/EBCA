import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
from scipy.ndimage import label, binary_dilation
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg0 = cfgs[0]

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(cfg0["spawn_pos"][0], cfg0["spawn_pos"][1], cfg0["spawn_yaw"], grid_path=str(GRID_PATH))

hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = cfg0["spawn_pos"]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(cfg0["spawn_yaw"] / 2.0), 0.0, 0.0, math.sin(cfg0["spawn_yaw"] / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

for t in range(25):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    s, diag = hal.step(u)

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
print(f"At tick 25: pos=({diag['pos_x']:.2f}, {diag['pos_y']:.2f}), yaw={diag['yaw']:.2f}")
print(f"Number of clusters: {num_features}")
for k in range(1, num_features + 1):
    py, px = np.where(lbl == k)
    fwx = px * delib.resolution - delib.half_size
    fwy = py * delib.resolution - delib.half_size
    print(f"Cluster {k}: size={len(py)}, center=({fwx.mean():.2f}, {fwy.mean():.2f})")
