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

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

for t in range(120):
    r = agent.step_cognitive_cycle(hal)
    u = r['action_cmd'].copy()
    # Apply 40% left torque degradation
    u[0] *= 0.60
    hal.step(u)

    endo = r['delib_telemetry'].get('endocrine', {})
    q = hal.data.qpos[qa:qa+7]
    yaw_deg = math.degrees(2.0 * math.atan2(float(q[6]), float(q[3])))

    if t in [10, 20, 30, 40, 50, 60, 80, 100]:
        print(f"Tick {t:3d}: pos=({q[0]:.3f}, {q[1]:.3f}), yaw={yaw_deg:5.1f}deg, u=[{u[0]:.2f}, {u[1]:.2f}], trim={endo.get('torque_trim', 0.0):.3f}, reaff_err={endo.get('reafference_error', 0.0):.3f}")
