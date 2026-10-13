import sys
sys.path.insert(0, ".")
import math
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco

cfg = generate_matched_configs(5, seed=6001)[2] # Config 2
sx, sy = cfg["spawn_pos"]
syaw = cfg["spawn_yaw"]

hal = CarlStage1HAL(xml_path=str(XML_PATH))
hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [sx, sy]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(
    dt=hal.dt,
    deliberation_mode="active_inference",
    grid_path=str(GRID_PATH)
)
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

print(f"Tracing Config 2 ticks 180 to 205:")
for tick in range(210):
    res = agent.step_cognitive_cycle(hal)
    u_cmd = res["action_cmd"]
    s_next, diag = hal.step(u_cmd)
    
    qx = float(hal.data.qpos[qa])
    qy = float(hal.data.qpos[qa + 1])
    qw, qx_r, qy_r, qz_r = hal.data.qpos[qa + 3:qa + 7]
    yaw = math.atan2(2 * (qw * qz_r + qx_r * qy_r), 1 - 2 * (qy_r**2 + qz_r**2))
    impact = hal.get_carl_impact_info()
    
    if tick >= 180:
        d_l_side = float(res["sensory"].sonar_distances[12]) if len(res["sensory"].sonar_distances) >= 15 else 0
        d_r_side = float(res["sensory"].sonar_distances[2]) if len(res["sensory"].sonar_distances) >= 15 else 0
        print(f"t={tick:03d} | pos=({qx:.2f}, {qy:.2f}, yaw={yaw:.2f}) | cmd=({u_cmd[0]:.2f}, {u_cmd[1]:.2f}) | sonars=(L={d_l_side:.2f}, R={d_r_side:.2f}) | imp={impact['damaging_impacts']}")
        if impact["damaging_impacts"] > 0:
            break
