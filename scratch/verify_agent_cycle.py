import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import numpy as np
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(headless=True)
agent = CarlAutonomousOrganismAgent(dt=hal.dt)
agent.initialize_spatial_grounding(spawn_x=0.0, spawn_y=0.0, spawn_yaw=0.0)

for t in range(5):
    res = agent.step_cognitive_cycle(hal)
    act_name = res["action_name"]
    cmd_L = res["cmd_L"]
    cmd_R = res["cmd_R"]
    tick = res["telemetry"].tick
    stage1 = res["stage1_slip_active"]
    stage2_1 = res["stage2_1_attractor_active"]
    stage2_2 = res["stage2_2_memory_active"]
    stage2_3 = res["stage2_3_delib_active"]
    print(f"Tick {tick}: Action={act_name} Cmd=({cmd_L:.3f}, {cmd_R:.3f}) | Organs: S1={stage1}, S2.1={stage2_1}, S2.2={stage2_2}, S2.3={stage2_3}")

print("CANONICAL_ORGANISM_CYCLE_PASS")
