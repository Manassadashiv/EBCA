import sys, math, numpy as np, torch, mujoco
from pathlib import Path
REPO_ROOT = Path(".").resolve()
sys.path.insert(0, str(REPO_ROOT))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage4_1_complete_battery import generate_paired_configs, execute_single_run, XML_PATH, GRID_PATH

hal = CarlStage1HAL(xml_path=str(XML_PATH))
configs = generate_paired_configs(num_configs=30, seed=4001)

cfg = configs[3] # Pair 4
print(f"=== CONFIG 4: {cfg['quadrant']}, {cfg['spawn_pos']}, yaw={cfg['spawn_yaw']:.2f} ===")

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
r1 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
print(f"T1: ticks={r1['ticks']}, esc={r1['escaped']}")
for t in range(40, len(r1['trajectory_x'])):
    print(f"T1 t={t:03d}: pos=({r1['trajectory_x'][t]:.2f}, {r1['trajectory_y'][t]:.2f}), yaw={r1['trajectory_yaw'][t]:.2f}")

# Now let's trace T2 step by step:
spawn_x, spawn_y = cfg["spawn_pos"]
spawn_yaw = cfg["spawn_yaw"]
hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent.reset()
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))
agent.enable_stage4_1_plasticity = True
if hasattr(agent, "stdp"):
    agent.stdp.reset_traces()

for tick in range(70):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    s_next, diag = hal.step(u)
    cx, cy, cyaw = diag["pos_x"], diag["pos_y"], diag["yaw"]
    if tick % 5 == 0 or cx <= -0.55:
        nom = getattr(agent, "_last_nominal_habit", None)
        print(f"t={tick:03d}: pos=({cx:.2f}, {cy:.2f}), yaw={cyaw:.2f}, u=({u[0]:.2f}, {u[1]:.2f}), nom={nom}")
