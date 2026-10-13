import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import mujoco, numpy as np, math

# Test Ep 5 with current XML vs solref=0.015 in default geom
hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg5 = cfgs[5]

spawn_x, spawn_y = cfg5["spawn_pos"]
spawn_yaw = cfg5["spawn_yaw"]

hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)
hal.set_floor_friction(0.20)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

max_fn = 0.0
for t in range(100):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    hal.step(u)
    imp = hal.get_carl_impact_info()
    if imp["max_normal_force"] > max_fn:
        max_fn = imp["max_normal_force"]
    if imp["damaging_impacts"] > 0:
        print(f"Damaging impact at t={t}, fn={imp['max_normal_force']:.2f} N")

print(f"Max normal force over 100 ticks: {max_fn:.2f} N")
