import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage3_5_complete_battery import GRID_PATH
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(1, seed=5101)
cfg0 = cfgs[0]

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(cfg0['spawn_pos'][0], cfg0['spawn_pos'][1], cfg0['spawn_yaw'], grid_path=str(GRID_PATH))

delib = agent.deliberation
print("Has static map?", delib.has_static_map)
print("Static grid np max:", delib.grid_np[0].max() if delib.static_grid_np is not None else "None")
