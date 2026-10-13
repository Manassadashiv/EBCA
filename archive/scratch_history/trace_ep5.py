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

for t in range(90):
    res = agent.step_cognitive_cycle(hal)
    u = res["action_cmd"]
    s, diag = hal.step(u)
    imp = hal.get_carl_impact_info()
    if t >= 70:
        dists = s[:15]
        d_fwd = float(np.min(dists[6:9]))
        print(f"t={t:2d}: pos=({diag['pos_x']:.3f}, {diag['pos_y']:.3f}), yaw={diag['yaw']:.2f}, u=({u[0]:.2f}, {u[1]:.2f}), fn={imp['max_normal_force']:.1f}, d_fwd={d_fwd:.2f}, sonars[min]={float(np.min(dists)):.2f}")
