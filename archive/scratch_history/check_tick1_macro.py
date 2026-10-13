import sys
sys.path.insert(0, ".")
import math
import mujoco
from pathlib import Path
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

ENV_DIR = Path("world/stage3_4_environments")
XML_PATH = ENV_DIR / "cul_de_sac_turning_bay.xml"
GRID_PATH = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"

hal = CarlStage1HAL(xml_path=str(XML_PATH))
hal.reset()
spawn_x, spawn_y, spawn_yaw = 0.58, 0.0, 0.0
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(
    dt=hal.dt,
    deliberation_mode="active_inference",
    grid_path=str(GRID_PATH)
)
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

# Update one sensory cycle
sonars = hal.read_sensors()
agent.deliberation.update_occupancy_memory(sonars)
c_x, c_y, c_th = agent.deliberation.pose

macro = agent.deliberation._compute_macro_frontier(c_x, c_y)
print(f"After tick 1 sensory update:")
if macro:
    fx, fy, dist, _ = macro
    print(f"f* = ({fx:.2f}, {fy:.2f}), dist={dist:.2f}")
else:
    print("NO MACRO FRONTIER")
