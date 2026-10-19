import sys, math, numpy as np, torch, mujoco
from pathlib import Path
REPO_ROOT = Path('.').resolve()
sys.path.insert(0, str(REPO_ROOT))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage4_1_complete_battery import generate_paired_configs, execute_single_run, XML_PATH, GRID_PATH

hal = CarlStage1HAL(xml_path=str(XML_PATH))
configs = generate_paired_configs(num_configs=14, seed=4001)
cfg = configs[13] # Pair 14

def trace_run(agent, tag):
    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    hal.data.qpos[qa:qa + 2] = cfg['spawn_pos']
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(cfg['spawn_yaw'] / 2.0), 0.0, 0.0, math.sin(cfg['spawn_yaw'] / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    agent.reset()
    agent.initialize_spatial_grounding(cfg['spawn_pos'][0], cfg['spawn_pos'][1], cfg['spawn_yaw'], grid_path=str(GRID_PATH))
    agent.enable_stage4_1_plasticity = True
    agent.stdp.reset_traces()

    print(f"\n--- {tag} ---")
    for tick in range(80):
        res = agent.step_cognitive_cycle(hal)
        cmd = res["action_cmd"]
        s_next, diag = hal.step(cmd)
        px, py, pyaw = diag["pos_x"], diag["pos_y"], diag["yaw"]
        hab = agent._last_nominal_habit
        hab_s = f"[{hab[0]:.2f}, {hab[1]:.2f}]" if hab is not None else "None"
        if tick < 15 or tick % 5 == 0 or px <= -0.55:
            print(f"[{tag}] t={tick:02d}: x={px:.2f}, y={py:.2f}, yaw={pyaw:.2f}, cmd=[{cmd[0]:.2f}, {cmd[1]:.2f}], hab={hab_s}")
        if px <= -0.55:
            print(f"[{tag}] Escaped at tick {tick}!")
            break

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
trace_run(agent, "RUN 1 (Naive)")
trace_run(agent, "RUN 2 (Plastic)")
