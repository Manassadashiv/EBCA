import os
import sys
sys.path.insert(0, ".")
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_trap.xml', headless=True)
hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [0.50, 0.0]
hal.data.qpos[qa + 3:qa + 7] = [1.0, 0.0, 0.0, 0.0]
mujoco.mj_forward(hal.model, hal.data)
hal.set_floor_friction(1.0)  # Nominal friction, 40% left torque loss

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path='world/stage3_4_environments/cul_de_sac_trap_grid.pt')
agent.initialize_spatial_grounding(0.50, 0.0, 0.0, grid_path='world/stage3_4_environments/cul_de_sac_trap_grid.pt')

print("Running diagnostic trace with 40% LEFT TORQUE LOSS...")
escaped = False
for t in range(350):
    res = agent.step_cognitive_cycle(hal)
    u = res['action_cmd'].copy()
    
    # Inject 40% torque loss on left wheel
    u[0] *= 0.60
    
    s_next, diag = hal.step(u)
    tel = res['delib_telemetry'].get('endocrine', {})
    c_info = hal.get_carl_contact_info()
    wall_c = c_info['carl_contacts'] - c_info['floor_contacts']
    est_pose = agent.deliberation.pose
    if t % 15 == 0 or wall_c > 0 or diag['pos_x'] < -0.55:
        print(f"t={t:3d} phys=({diag['pos_x']:.3f}, {diag['pos_y']:.3f}, yaw={diag['yaw']:.2f}) est=({est_pose[0]:.3f}, {est_pose[1]:.3f}, yaw={est_pose[2]:.2f}) u_cmd=({res['action_cmd'][0]:.2f}, {res['action_cmd'][1]:.2f}) wall_c={wall_c}")
    if diag['pos_x'] < -0.55:
        print(f"--> ESCAPED with 40% torque loss at tick {t}! Final pos: ({diag['pos_x']:.3f}, {diag['pos_y']:.3f})")
        escaped = True
        break

if not escaped:
    print(f"--> FINISHED at tick {t}, final pos: ({diag['pos_x']:.3f}, {diag['pos_y']:.3f})")
