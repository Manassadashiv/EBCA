import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import math, mujoco, numpy as np

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
cfg0 = cfgs[0]

hal.reset()
sx, sy = cfg0['spawn_pos']
syaw = cfg0['spawn_yaw']
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)
hal.set_floor_friction(0.20)

agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode='active_inference', grid_path='brain/spatial_memory/grid_cells/saved_weights/sdr_grid_weights_20260408_012803.npz')
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path='brain/spatial_memory/grid_cells/saved_weights/sdr_grid_weights_20260408_012803.npz')

for t in range(400):
    r = agent.step_cognitive_cycle(hal)
    u = r['action_cmd']
    s, diag = hal.step(u)
    delib = agent.deliberation
    dists = s[:15]
    d_fwd = float(np.min(dists[6:9]))
    d_center = float(dists[7])
    print(f"t={t:3d}: pos=({diag['pos_x']:.2f}, {diag['pos_y']:.2f}), yaw={diag['yaw']:.2f}, u=({u[0]:.2f}, {u[1]:.2f}), th_des={getattr(delib, '_last_th_des', 0.0):.2f}")
    if diag['pos_x'] < -0.55:
        print(f"ESCAPED at t={t}!")
        break
