import sys, math, numpy as np, torch, mujoco
from pathlib import Path
REPO_ROOT = Path('.').resolve()
sys.path.insert(0, str(REPO_ROOT))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage4_1_complete_battery import generate_paired_configs, execute_single_run, XML_PATH, GRID_PATH

hal = CarlStage1HAL(xml_path=str(XML_PATH))
configs = generate_paired_configs(num_configs=5, seed=4001)

for idx, cfg in enumerate(configs):
    # Test with corrected steering logic directly
    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
    r1 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    
    # Run 2 with same agent
    r2 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    gain = (r1['ticks'] - r2['ticks']) / max(1, r1['ticks']) * 100.0
    print(f"Cfg {idx+1} ({cfg['quadrant']}): T1={r1['ticks']} -> T2={r2['ticks']} (Gain: {gain:+.1f}%), col1={r1['had_collision']}, col2={r2['had_collision']}")
