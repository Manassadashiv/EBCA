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
configs = generate_matched_configs(num_configs=6, seed=5301)

for idx in range(6):
    cfg = configs[idx]
    side = "left" if idx % 2 == 0 else "right"
    # Test 50% loss (u *= 0.50)
    for en in [True, False]:
        hal.reset()
        qa = int(hal.model.joint('spatial_identity').qposadr[0])
        sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
        mujoco.mj_forward(hal.model, hal.data)
        hal.set_floor_friction(0.20)
        ag = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
        ag.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))
        if not en: ag.endocrine.enabled = False
        esc = False
        for t in range(400):
            r = ag.step_cognitive_cycle(hal)
            u = r['action_cmd'].copy()
            if side == "left": u[0] *= 0.50
            else: u[1] *= 0.50
            hal.step(u)
            if hal.data.qpos[qa] < -0.55:
                esc = True; break
        print(f"Ep {idx} en={str(en):5s}: {'ESCAPED' if esc else 'FAILED '} (t={t})", flush=True)
