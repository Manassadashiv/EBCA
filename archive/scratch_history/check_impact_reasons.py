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

for idx in [2, 6, 15]:
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

    for t in range(500):
        r = agent.step_cognitive_cycle(hal)
        u = r['action_cmd'].copy()
        if side == "left":
            u[0] *= 0.60
        else:
            u[1] *= 0.60
        hal.step(u)

        impact_info = hal.get_carl_impact_info()
        if impact_info["damaging_impacts"] > 0:
            c_force = np.zeros(6)
            for i in range(hal.data.ncon):
                c = hal.data.contact[i]
                in1 = c.geom1 in hal.carl_geom_ids
                in2 = c.geom2 in hal.carl_geom_ids
                if (in1 and not in2) or (in2 and not in1):
                    other = c.geom2 if in1 else c.geom1
                    if other != hal.floor_geom_id:
                        mujoco.mj_contactForce(hal.model, hal.data, i, c_force)
                        fn = float(abs(c_force[0]))
                        dist = float(c.dist)
                        geom_name = hal.model.geom(other).name
                        carl_geom = hal.model.geom(c.geom1 if in1 else c.geom2).name
                        print(f"Ep {idx} tick {t}: carl={carl_geom}, other={geom_name}, dist={dist:.5f}, Fn={fn:.2f}")
            break
