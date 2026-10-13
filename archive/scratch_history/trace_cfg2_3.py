import sys
sys.path.insert(0, ".")
import math
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco

for cfg_idx in [2, 3]:
    cfg = generate_matched_configs(5, seed=6001)[cfg_idx]
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]

    hal = CarlStage1HAL(xml_path=str(XML_PATH))
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa + 2] = [sx, sy]
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    agent = CarlAutonomousOrganismAgent(
        dt=hal.dt,
        deliberation_mode="active_inference",
        grid_path=str(GRID_PATH)
    )
    agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

    print(f"\n--- TRACING CONFIG {cfg_idx} (spawn={sx:.2f}, {sy:.2f}, yaw={syaw:.2f}) ---")
    for tick in range(250):
        res = agent.step_cognitive_cycle(hal)
        u_cmd = res["action_cmd"]
        s_next, diag = hal.step(u_cmd)
        
        qx = float(hal.data.qpos[qa])
        qy = float(hal.data.qpos[qa + 1])
        impact = hal.get_carl_impact_info()
        
        if impact["damaging_impacts"] > 0:
            print(f"COLLISION at tick {tick}: pos=({qx:.2f}, {qy:.2f}) | max_fn={impact['max_normal_force']:.2f} N")
            for c_i in range(hal.data.ncon):
                con = hal.data.contact[c_i]
                g1 = hal.model.geom(con.geom1).name
                g2 = hal.model.geom(con.geom2).name
                if "chassis" in g1 or "chassis" in g2 or "torso" in g1 or "torso" in g2:
                    print(f"  Geoms: {g1} <-> {g2} (dist={con.dist:.4f})")
            break
        if qx <= -0.55:
            print(f"ESCAPED at tick {tick}! pos=({qx:.2f}, {qy:.2f})")
            break
