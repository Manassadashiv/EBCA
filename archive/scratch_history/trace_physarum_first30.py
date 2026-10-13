import math
import numpy as np
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

print("=== DIAGNOSTIC RUN (FIRST 30 TICKS) ===")
for tick in range(30):
    c_x, c_y, c_th = agent.deliberation.pose
    macro = agent.deliberation._compute_macro_frontier(c_x, c_y)
    if macro:
        fx, fy, dist, _ = macro
        vx, vy, thf = agent.deliberation.physarum.get_topological_current(c_x, c_y)
        si, sj = agent.deliberation.physarum.world_to_grid(c_x, c_y)
        ti, tj = agent.deliberation.physarum.world_to_grid(fx, fy)
        print(f"t={tick:02d} | pos=({c_x:.2f},{c_y:.2f}, th={c_th:.2f}) | f*=({fx:.2f},{fy:.2f}, d={dist:.2f}) [src=({si},{sj}), snk=({ti},{tj})] | flow=({vx:.3f},{vy:.3f}, th={thf:.2f})")
    else:
        print(f"t={tick:02d} | pos=({c_x:.2f},{c_y:.2f}) | NO MACRO FRONTIER")
    
    res = agent.step_cognitive_cycle(hal)
    hal.step(res["action_cmd"])
