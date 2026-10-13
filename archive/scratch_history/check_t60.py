import sys
sys.path.insert(0, ".")
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco, math, torch

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

for t in range(60):
    res = agent.step_cognitive_cycle(hal)
    hal.step(res['action_cmd'])

# At t=60:
d = agent.deliberation
sens = hal.read_sensors()
sonars = sens[:15]
w_gyro = float(sens[20])
u_batch = d._sample_trajectories()
poses_x, poses_y, poses_th = d._vectorized_rollout(d.pose[0], d.pose[1], d.pose[2], d.v_hat, d.w_hat, u_batch)
costs, debug = d._evaluate_expected_free_energy(poses_x, poses_y, poses_th, u_batch, d.pose[0], d.pose[1], d.pose[2], sonars, None)

best_idx = int(torch.argmin(costs))
print(f"Candidate 0 (Nominal: {u_batch[0, 0].tolist()}): Cost = {costs[0].item():.2f}")
print(f"Candidate Best ({best_idx}, Cmd: {u_batch[best_idx, 0].tolist()}): Cost = {costs[best_idx].item():.2f}")
print(f"Candidate 1 (Forward 0.95: {u_batch[1, 0].tolist()}): Cost = {costs[1].item():.2f}")
print(f"Candidate 6 (Pivot Left: {u_batch[6, 0].tolist()}): Cost = {costs[6].item():.2f}")
print("Min sonar clearances:", debug["min_dists"][:8])
print("Collision mask:", debug["collision_mask"][:8])
