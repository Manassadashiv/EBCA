import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import mujoco, numpy as np, math

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

for t in range(89):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    hal.step(u)

# Inspect tick 88 contacts
print(f"Number of contacts: {hal.data.ncon}")
c_force = np.zeros(6, dtype=np.float64)
for i in range(hal.data.ncon):
    c = hal.data.contact[i]
    mujoco.mj_contactForce(hal.model, hal.data, i, c_force)
    g1 = hal.model.geom(c.geom1).name
    g2 = hal.model.geom(c.geom2).name
    print(f"Contact {i}: {g1} <-> {g2}, dist={c.dist:.6f}, c_force={c_force}, solref={c.solref}")
