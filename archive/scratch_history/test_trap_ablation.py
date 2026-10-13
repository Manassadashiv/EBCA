import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, ENV_DIR, CarlAutonomousOrganismAgent
)
import math, mujoco, numpy as np, scipy.stats as stats

TRAP_XML = ENV_DIR / "cul_de_sac_trap.xml"
TRAP_GRID = ENV_DIR / "cul_de_sac_trap_grid.pt"

hal = CarlStage1HAL(xml_path=str(TRAP_XML), headless=True)
configs = generate_matched_configs(num_configs=10, seed=5301)

int_esc = 0
abl_esc = 0

for idx in range(10):
    cfg = configs[idx]
    side = "left" if idx % 2 == 0 else "right"
    for en in [True, False]:
        hal.reset()
        qa = int(hal.model.joint('spatial_identity').qposadr[0])
        sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
        mujoco.mj_forward(hal.model, hal.data)
        hal.set_floor_friction(0.20)
        ag = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(TRAP_GRID))
        ag.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(TRAP_GRID))
        if not en: ag.endocrine.enabled = False
        esc = False
        for t in range(350):
            r = ag.step_cognitive_cycle(hal)
            u = r['action_cmd'].copy()
            if side == "left": u[0] *= 0.60
            else: u[1] *= 0.60
            hal.step(u)
            if hal.data.qpos[qa] < -0.55:
                esc = True; break
        if en and esc: int_esc += 1
        if not en and esc: abl_esc += 1
        print(f"Ep {idx:2d} ({side}) en={str(en):5s}: {'ESC' if esc else 'NO '}", flush=True)

print(f"Trap Summary: Intact={int_esc}/10, Ablated={abl_esc}/10")
