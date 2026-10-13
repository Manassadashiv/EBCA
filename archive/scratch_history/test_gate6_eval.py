import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, CarlAutonomousOrganismAgent, GRID_PATH
)
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs = generate_matched_configs(num_configs=5, seed=5701)

deltas = []
entropies = []

for cfg in configs:
    sx, sy = cfg['spawn_pos']
    syaw = cfg['spawn_yaw']

    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
    mujoco.mj_forward(hal.model, hal.data)

    ag_int = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
    ag_int.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

    ag_abl = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
    ag_abl.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))
    ag_abl.deliberation.w_info = 0.0

    # Step both agents through the exact same initial state for 10 ticks
    for t in range(10):
        r_int = ag_int.step_cognitive_cycle(hal)
        r_abl = ag_abl.step_cognitive_cycle(hal)
        u = r_int['action_cmd']
        hal.step(u)

    u_int = np.array(r_int['action_cmd'][:2])
    u_abl = np.array(r_abl['action_cmd'][:2])
    diff = float(np.linalg.norm(u_int - u_abl))
    deltas.append(diff)
    
    # Path integral candidate distribution entropy across candidate costs
    telem = r_int['delib_telemetry']
    print(f"Cfg diff={diff:.4f}, entropy={telem.get('ensemble_entropy', 0.0):.4f}, ep_mean={telem.get('efe_epistemic_mean', 0.0):.4f}")
