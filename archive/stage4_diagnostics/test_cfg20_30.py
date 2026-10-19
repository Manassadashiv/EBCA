import sys, math, numpy as np, torch, mujoco
from pathlib import Path
REPO_ROOT = Path(".").resolve()
sys.path.insert(0, str(REPO_ROOT))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage4_1_complete_battery import generate_paired_configs, execute_single_run, XML_PATH, GRID_PATH

hal = CarlStage1HAL(xml_path=str(XML_PATH))
configs = generate_paired_configs(num_configs=30, seed=4001)

for idx in [19, 29]:
    cfg = configs[idx]
    print(f"=== CONFIG {idx+1}: {cfg['quadrant']}, {cfg['spawn_pos']}, yaw={cfg['spawn_yaw']:.2f} ===")
    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
    r1 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    r2 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    print(f"T1: ticks={r1['ticks']}, esc={r1['escaped']}, col={r1['had_collision']}")
    print(f"T2: ticks={r2['ticks']}, esc={r2['escaped']}, col={r2['had_collision']}")
