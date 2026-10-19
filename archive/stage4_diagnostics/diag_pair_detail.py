import sys
from pathlib import Path
import math
import numpy as np
import torch
import mujoco

PROJECT_ROOT = Path("D:/ebca")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage4_1_complete_battery import generate_paired_configs, execute_single_run

XML_PATH = PROJECT_ROOT / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"
GRID_PATH = PROJECT_ROOT / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt"
hal = CarlStage1HAL(xml_path=str(XML_PATH))
configs = generate_paired_configs(30, seed=4001)

for cfg_idx in [19, 29]:
    cfg = configs[cfg_idx]
    quad = cfg["quadrant"]
    sp = cfg["spawn_pos"]
    sy = cfg["spawn_yaw"]
    print(f"\n=== CONFIG {cfg_idx+1} ({quad}, spawn={sp}, yaw={sy:.2f}) ===")
    agent = CarlAutonomousOrganismAgent()
    r1 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    print(f"Trial 1: Ticks = {r1['ticks']}, Escaped = {r1['escaped']}, Col = {r1['had_collision']}")
    r2 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    print(f"Trial 2: Ticks = {r2['ticks']}, Escaped = {r2['escaped']}, Col = {r2['had_collision']}")
    print(f"T1 trajectory end: x={r1['trajectory_x'][-1]:.3f}, y={r1['trajectory_y'][-1]:.3f}, yaw={r1['trajectory_yaw'][-1]:.3f}")
    print(f"T2 trajectory end: x={r2['trajectory_x'][-1]:.3f}, y={r2['trajectory_y'][-1]:.3f}, yaw={r2['trajectory_yaw'][-1]:.3f}")
