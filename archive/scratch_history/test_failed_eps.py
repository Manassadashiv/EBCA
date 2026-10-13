import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import mujoco, numpy as np, math

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
bumper_id = hal.model.geom("chassis_bumper").id

# Test on Ep 2, 4, 5, 6, 11, 13, 14, 16, 17, 18, 19, 25, 26
test_indices = [2, 4, 5, 6, 11, 13, 14, 16, 17, 18, 19, 25, 26]

for idx in test_indices:
    cfg = cfgs[idx]
    hal.reset()
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa + 2] = [sx, sy]
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    hal.set_floor_friction(0.20)

    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
    agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

    escaped = False
    for t in range(450):
        res = agent.step_cognitive_cycle(hal)
        u = res["action_cmd"]
        s, diag = hal.step(u)
        if diag["pos_x"] < -0.55:
            escaped = True
            break
    print(f"Ep {idx:2d}: escaped={escaped}, ticks={t+1}, final_x={diag['pos_x']:.2f}", flush=True)
