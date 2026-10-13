import sys
sys.path.insert(0, ".")
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco, math

hal = CarlStage1HAL(xml_path=str(XML_PATH))
cfg = generate_matched_configs(5, seed=6001)[0]
sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa + 2] = [sx, sy]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path='world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt')
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path='world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt')

for t in range(95):
    res = agent.step_cognitive_cycle(hal)
    u = res['action_cmd']
    hal.step(u)
    diag = hal.get_diagnostics()
    if t >= 60:
        d = res['delib_telemetry']
        print(f"t={t:03d} x={diag['pos_x']:.2f} y={diag['pos_y']:.2f} yaw={math.degrees(diag['yaw']):.1f} th_des={math.degrees(d.get('th_des', 0)):.1f} min_sonar={res['sensory'].min_obstacle_dist:.2f} cmd=({u[0]:.2f}, {u[1]:.2f})")
