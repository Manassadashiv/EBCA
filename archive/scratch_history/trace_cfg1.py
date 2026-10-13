import sys
sys.path.insert(0, ".")
import math
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco

cfg = generate_matched_configs(5, seed=6001)[1] # Config 1
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
agent.deliberation.enable_stage3_6_physarum = False
agent.deliberation.enable_stage3_6_synergies = False

print(f"Tracing Config 1 (spawn={sx:.2f}, {sy:.2f}):")
for tick in range(120):
    res = agent.step_cognitive_cycle(hal)
    u_cmd = res["action_cmd"]
    s_next, diag = hal.step(u_cmd)
    
    qx = float(hal.data.qpos[qa])
    qy = float(hal.data.qpos[qa + 1])
    qz = float(hal.data.qpos[qa + 2])
    qw, qx_r, qy_r, qz_r = hal.data.qpos[qa + 3:qa + 7]
    pitch = math.asin(np.clip(2 * (qw * qy_r - qz_r * qx_r), -1.0, 1.0))
    impact = hal.get_carl_impact_info()
    
    if tick % 10 == 0 or abs(pitch) > 0.20 or impact["damaging_impacts"] > 0:
        print(f"t={tick:03d} | pos=({qx:.2f}, {qy:.2f}, z={qz:.3f}) | pitch={pitch:.3f} rad | cmd=({u_cmd[0]:.2f}, {u_cmd[1]:.2f}) | dam_imp={impact['damaging_impacts']}")
        if abs(pitch) > 0.8:
            print("FLIPPED OVER!")
            break
