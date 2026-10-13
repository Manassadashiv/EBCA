import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import mujoco, numpy as np, math

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg7 = cfgs[7]

spawn_x, spawn_y = cfg7["spawn_pos"]
spawn_yaw = cfg7["spawn_yaw"]

hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)
hal.set_floor_friction(0.20)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

print(f"Ep 7 Spawn: pos=({spawn_x:.3f}, {spawn_y:.3f}), yaw={spawn_yaw:.3f}")
for t in range(250):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    s, diag = hal.step(u)
    if t % 20 == 0:
        print(f"t={t:3d}: pos=({diag['pos_x']:.3f}, {diag['pos_y']:.3f}), yaw={diag['yaw']:.2f}, u=({u[0]:.2f}, {u[1]:.2f})")
    if diag["pos_x"] < -0.55:
        print(f"ESCAPED at t={t}!")
        break
