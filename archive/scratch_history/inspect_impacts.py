import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, XML_PATH, CarlAutonomousOrganismAgent, GRID_PATH
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path=str(XML_PATH))
cfg = generate_matched_configs(1)[0]
sx, sy = cfg['spawn_pos']
syaw = cfg['spawn_yaw']

hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)
hal.set_floor_friction(0.20)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

max_fn = 0.0
max_penetration = 0.0
contact_ticks = 0

for t in range(200):
    r = agent.step_cognitive_cycle(hal)
    u = r['action_cmd']
    hal.step(u)

    c_info = hal.get_carl_contact_info()
    impact_info = hal.get_carl_impact_info()

    if impact_info['max_normal_force'] > max_fn:
        max_fn = impact_info['max_normal_force']

    wall_contacts = c_info['carl_contacts'] - c_info['floor_contacts']
    if wall_contacts > 0:
        contact_ticks += 1

    q = hal.data.qpos[qa:qa+7]
    if q[0] <= -0.55:
        print(f"Escaped at tick {t:3d}! pos=({q[0]:.3f}, {q[1]:.3f})")
        break

print(f"Max normal force: {max_fn:.3f} N (Threshold: 15.0 N)")
print(f"Contact ticks: {contact_ticks}/200")
print(f"Damaging impacts: {impact_info['damaging_impacts']}")
