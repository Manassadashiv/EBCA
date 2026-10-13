import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, CarlAutonomousOrganismAgent, GRID_PATH
)
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs = generate_matched_configs(num_configs=20, seed=5201)
cfg = configs[6]  # Ep 6 (left loss)

sx, sy = cfg['spawn_pos']
syaw = cfg['spawn_yaw']

hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

for t in range(50):
    r = agent.step_cognitive_cycle(hal)
    u = r['action_cmd'].copy()
    u[0] *= 0.60  # Left torque loss
    hal.step(u)

    q = hal.data.qpos[qa:qa+7]
    yaw_deg = math.degrees(2.0 * math.atan2(float(q[6]), float(q[3])))
    d = r['delib_telemetry']
    delib = agent.deliberation
    if t in [15, 20, 25, 30, 35, 40]:
        print(f"t={t:2d}: pos=({q[0]:.3f}, {q[1]:.3f}), yaw={yaw_deg:5.1f}deg, agent_pose=({delib.pose[0]:.3f}, {delib.pose[1]:.3f}, {math.degrees(delib.pose[2]):.1f}deg)")
        print(f"      macro_frontier={delib._cached_macro_frontier}, reverse_done={delib._reverse_done}, reverse_ticks={delib._reverse_ticks}")
