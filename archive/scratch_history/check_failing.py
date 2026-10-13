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
configs = generate_matched_configs(num_configs=20, seed=5201)

# Test the 5 failed episodes: 2, 6, 8, 11, 15
for idx in [1, 2, 6, 8, 11, 15]:
    cfg = configs[idx]
    side = "left" if idx % 2 == 0 else "right"
    sx, sy = cfg['spawn_pos']
    syaw = cfg['spawn_yaw']

    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
    mujoco.mj_forward(hal.model, hal.data)

    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path=str(GRID_PATH))
    agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

    # Monkey-patch or test: if c_x > -0.45, guide egress towards pi
    orig_eval = agent.deliberation._evaluate_expected_free_energy
    
    escaped = False
    collided = False
    for t in range(500):
        # We step
        r = agent.step_cognitive_cycle(hal)
        u = r['action_cmd'].copy()
        if side == "left":
            u[0] *= 0.60
        else:
            u[1] *= 0.60
        hal.step(u)

        impact_info = hal.get_carl_impact_info()
        if impact_info["damaging_impacts"] > 0 and not collided:
            collided = True

        q = hal.data.qpos[qa:qa+7]
        if q[0] < -0.55:
            escaped = True
            break
    status = "ESCAPED" if escaped else ("COLLIDED" if collided else "TIMEOUT")
    print(f"Ep {idx:2d} ({side:5s}): {status:8s} ticks={t:3d} final_pos=({q[0]:.3f}, {q[1]:.3f})")
