import sys, math
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import execute_physical_episode, generate_matched_configs, CarlStage1HAL, XML_PATH, CarlAutonomousOrganismAgent, GRID_PATH

hal = CarlStage1HAL(xml_path=str(XML_PATH))
cfg = generate_matched_configs(1)[0]
sx, sy = cfg['spawn_pos']
syaw = cfg['spawn_yaw']

# Test A: Exactly like our script
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
import mujoco
mujoco.mj_forward(hal.model, hal.data)

agentA = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
agentA.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

print("=== Running Script A ===")
for t in range(60):
    r = agentA.step_cognitive_cycle(hal)
    u = r['action_cmd']
    hal.step(u)
    if t in [10, 20, 30, 40, 50, 59]:
        q = hal.data.qpos[qa:qa+7]
        print(f"Script A tick {t:2d}: pos=({q[0]:.3f}, {q[1]:.3f}), u=[{u[0]:.2f}, {u[1]:.2f}]")

# Test B: Exactly execute_physical_episode
print("\n=== Running Script B (execute_physical_episode) ===")
resB = execute_physical_episode(cfg, hal, floor_friction=1.0)
print("Script B total ticks:", resB['total_ticks'], "escaped:", resB['escaped'])
