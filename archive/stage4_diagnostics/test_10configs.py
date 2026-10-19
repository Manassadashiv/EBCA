import sys, math, numpy as np, torch, mujoco
from pathlib import Path
REPO_ROOT = Path('.').resolve()
sys.path.insert(0, str(REPO_ROOT))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage4_1_complete_battery import generate_paired_configs, execute_single_run, XML_PATH, GRID_PATH
import scipy.stats as stats

hal = CarlStage1HAL(xml_path=str(XML_PATH))
configs = generate_paired_configs(num_configs=10, seed=4001)

t1_all, t2_all = [], []
for idx, cfg in enumerate(configs):
    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
    r1 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    r2 = execute_single_run(agent, cfg, hal, enable_plasticity=True)
    t1_all.append(r1['ticks'])
    t2_all.append(r2['ticks'])
    gain = (r1['ticks'] - r2['ticks']) / max(1, r1['ticks']) * 100.0
    print(f"Cfg {idx+1:02d} ({cfg['quadrant']}): T1={r1['ticks']} -> T2={r2['ticks']} (Gain: {gain:+.1f}%), col1={r1['had_collision']}, col2={r2['had_collision']}", flush=True)

s1, s2 = sum(t1_all), sum(t2_all)
net = (s1 - s2) / s1 * 100.0
print(f"Summary: T1={s1} -> T2={s2}, Net Gain = {net:+.1f}%", flush=True)
