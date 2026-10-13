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

for t in range(120):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    hal.step(u)
    imp = hal.get_carl_impact_info()
    if imp["damaging_impacts"] > 0:
        print(f"Damaging impact at tick {t}! Max fn = {imp['max_normal_force']:.2f} N")
        # Find which geom had this impact
        c_force = np.zeros(6, dtype=np.float64)
        for i in range(hal.data.ncon):
            c = hal.data.contact[i]
            in1 = c.geom1 in hal.carl_geom_ids
            in2 = c.geom2 in hal.carl_geom_ids
            if (in1 and not in2) or (in2 and not in1):
                other = c.geom2 if in1 else c.geom1
                if other != hal.floor_geom_id:
                    mujoco.mj_contactForce(hal.model, hal.data, i, c_force)
                    fn = float(abs(c_force[0]))
                    g1 = hal.model.geom(c.geom1).name
                    g2 = hal.model.geom(c.geom2).name
                    print(f"   Contact {i}: {g1} <-> {g2}, fn={fn:.2f} N, dist={c.dist:.5f}")
        break
