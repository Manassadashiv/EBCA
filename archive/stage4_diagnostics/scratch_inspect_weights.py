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
    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
    r1 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    r2 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    print(f"Cfg {idx+1} ({cfg['quadrant']}): T1={r1['ticks']} -> T2={r2['ticks']}")
    print("  Mean abs W:", np.mean(np.abs(agent.stdp.W)))
    print("  Post weights mean per channel:", np.round(np.mean(agent.stdp.W, axis=0), 4))
    print("  Active synapses (>0.01):", agent.stdp.get_active_synapses_fraction(0.01))
