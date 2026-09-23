import sys
sys.path.insert(0, '.')
import mujoco, numpy as np, math, json
import torch
import torch.nn.functional as F

from tests.test_stage3_4R2_remediation import build_50_matched_configurations
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

# 1. Setup Config 7
configs = build_50_matched_configurations()
cfg = configs[7]
print(f"Loaded Config {cfg['config_id']}: seed={cfg['seed']}, spawn={cfg['spawn_pos']}")

hal = CarlStage1HAL(xml_path=cfg['xml_path'])
ctrl = CARLActiveInferenceEngine(
    grid_path=cfg['grid_path'],
    w_info=1.0,
    frontier_mode='macro',
    norm_mode='dimensionless'
)

sx, sy = cfg['spawn_pos']
syaw = cfg['spawn_yaw']
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
mujoco.mj_forward(hal.model, hal.data)
ctrl.initialize_pose(sx, sy, syaw)

v_est = 0.0
target_tick = 121

for tick in range(target_tick):
    sensors = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=0.030)
    action, telem = ctrl.select_action(sensors[:15], curr_v=v_est, curr_w=float(sensors[20]))
    cmd_6d = np.zeros(6, dtype=np.float64)
    cmd_6d[0] = float(action[0])
    cmd_6d[1] = float(action[1])
    hal.step(cmd_6d)
    v_est = 0.70 * v_est + 0.30 * (0.5 * (cmd_6d[0] + cmd_6d[1]) * 0.30)

# We are now at tick 121.
# Let's inspect the current state:
sensors = hal.read_sensors()
sonars = sensors[:15]
gyro_yaw = float(sensors[20])
ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

q_curr = hal.data.qpos[qa:qa+7]
curr_px, curr_py = float(q_curr[0]), float(q_curr[1])
curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
curr_deg = math.degrees(curr_yaw)

print(f"\n================ AT TARGET TIMESTEP (Tick {target_tick}) ================")
print(f"Robot World Position:     x = {curr_px:.4f} m, y = {curr_py:.4f} m")
print(f"Robot Heading (Yaw):      {curr_deg:+.2f} deg (Facing Exit: {abs(curr_deg) >= 135.0})")
print(f"Estimated v_wheel:        {v_est:.4f} m/s")
print(f"Sonars: min={sonars.min():.2f}m, center={sonars[7]:.2f}m, left={sonars[14]:.2f}m, right={sonars[0]:.2f}m")

# Update occupancy memory
ctrl.update_occupancy_memory(sonars)
c_x, c_y, c_th = ctrl.pose
print(f"Controller Odometry Pose: x = {c_x:.4f} m, y = {c_y:.4f} m, th = {math.degrees(c_th):+.2f} deg")

# Sample candidates
u_batch = ctrl._sample_trajectories()  # (M, H, 2)
M, H = u_batch.shape[0], u_batch.shape[1]

# Rollout
poses_x, poses_y, poses_th = ctrl._vectorized_rollout(c_x, c_y, c_th, v_est, gyro_yaw, u_batch)

# Inspect macro frontier
macro_res = ctrl._compute_macro_frontier(c_x, c_y)
if macro_res is not None:
    f_star_x, f_star_y, current_geo_dist, dist_field = macro_res
    print(f"Selected Macro-Frontier:  x = {f_star_x:.4f} m, y = {f_star_y:.4f} m")
    print(f"Current Geodesic Dist:    {current_geo_dist:.4f} m")
else:
    f_star_x, f_star_y, current_geo_dist, dist_field = 0.0, 0.0, 99.0, np.zeros((128, 128))
    print("WARNING: Macro-frontier is None!")

# Evaluate costs
efe_costs, efe_debug = ctrl._evaluate_expected_free_energy(
    poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, sonars, None
)

# Detailed term decomposition
# Re-extract terms exactly as in _evaluate_expected_free_energy:
sub_x = poses_x[:, ctrl.chk_idx]
sub_y = poses_y[:, ctrl.chk_idx]
cat_qx = (sub_x.unsqueeze(-1) + ctrl.offset_x).view(M, -1)
cat_qy = (sub_y.unsqueeze(-1) + ctrl.offset_y).view(M, -1)
norm_x = (cat_qx / ctrl.half_size).clamp(-1.0, 1.0)
norm_y = (cat_qy / ctrl.half_size).clamp(-1.0, 1.0)
grid_coords = torch.stack([norm_x, norm_y], dim=-1).unsqueeze(1)
grid_b_ch0 = ctrl.grid[:, 0:1, :, :].expand(M, 1, ctrl.grid_size, ctrl.grid_size)
with torch.inference_mode():
    sampled_occ = F.grid_sample(
        grid_b_ch0, grid_coords, mode="bilinear", padding_mode="zeros", align_corners=True
    ).squeeze(1).squeeze(1)

max_occ_hits = torch.max(sampled_occ, dim=-1).values
collision_mask = (max_occ_hits > 0.85).numpy()

margin_deficit = torch.clamp((max_occ_hits - 0.20) / 0.65, min=0.0, max=1.0)
j_margin_norm = (margin_deficit ** 2).numpy()

delta_u = u_batch[:, 1:, :] - u_batch[:, :-1, :]
jerk_max_norm = float((H - 1) * 4.0)
j_jerk_norm = torch.clamp(torch.sum(delta_u ** 2, dim=(1, 2)) / jerk_max_norm, min=0.0, max=1.0).numpy()

live_right = float(np.min(sonars[1:6]))
live_left = float(np.min(sonars[9:14]))
u_diff_step0 = u_batch[:, 0, 1] - u_batch[:, 0, 0]
right_deficit = max(0.0, 0.30 - live_right)
left_deficit = max(0.0, 0.30 - live_left)
target_steer = np.clip((right_deficit - left_deficit) * 3.0, -0.60, 0.60)
steer_norm = torch.clamp(((u_diff_step0 - target_steer) / 2.0) ** 2, min=0.0, max=1.0).numpy()

# Frontier progress
norm_tx = (poses_x[:, -1] / ctrl.half_size).clamp(-1.0, 1.0)
norm_ty = (poses_y[:, -1] / ctrl.half_size).clamp(-1.0, 1.0)
coords = torch.stack([norm_tx, norm_ty], dim=-1).unsqueeze(0).unsqueeze(2)
dist_tensor = torch.from_numpy(dist_field).unsqueeze(0).unsqueeze(0)
with torch.inference_mode():
    term_dists = F.grid_sample(
        dist_tensor, coords, mode="bilinear", padding_mode="border", align_corners=True
    ).squeeze().numpy()

delta_d_geo = current_geo_dist - term_dists
d_max = 0.30 * H * 0.030  # 0.135m
phi_norm = np.clip(delta_d_geo / d_max, -1.0, 1.0)

g_total = efe_costs.numpy()

# Wall clearance computation helper
def compute_wall_clearance(px, py):
    # Envelope of cul_de_sac_turning_bay:
    # Corridor x in [-0.60, 0.35], walls at y = +/-0.35
    # Turning bay x in [0.35, 0.85], walls at y = +/-0.65
    # Pocket x in [0.85, 1.20], walls at y = +/-0.35
    # Cap at x = 1.20
    r_hull = 0.14
    if px <= 0.35:
        dy = 0.35 - abs(py)
        dx = px - (-0.60)
        return min(dy, dx) - r_hull
    elif 0.35 < px <= 0.85:
        dy = 0.65 - abs(py)
        # also check distance to entrance shoulder corner at (0.35, +/-0.35)
        d_shoulder = math.hypot(px - 0.35, max(0.0, abs(py) - 0.35))
        return min(dy, d_shoulder) - r_hull
    else:
        dy = 0.35 - abs(py)
        dx = 1.20 - px
        return min(dy, dx) - r_hull

candidates_data = []
for m in range(M):
    tx = float(poses_x[m, -1].item())
    ty = float(poses_y[m, -1].item())
    tth = float(poses_th[m, -1].item())
    
    # Check minimum corridor clearance along the 15-step rollout
    traj_x = poses_x[m].numpy()
    traj_y = poses_y[m].numpy()
    min_clr = min(compute_wall_clearance(traj_x[s], traj_y[s]) for s in range(H))
    
    # Enters corridor: terminal x <= 0.35 (the shoulder boundary)
    enters_corr = bool(tx <= 0.35)
    
    candidates_data.append({
        "idx": m,
        "collision": bool(collision_mask[m]),
        "j_margin": float(j_margin_norm[m]),
        "j_jerk": float(j_jerk_norm[m]),
        "steer": float(steer_norm[m]),
        "phi_frontier": float(phi_norm[m]),
        "geodesic_reward": float(ctrl.alpha_epistemic * phi_norm[m]),
        "g_total": float(g_total[m]),
        "term_x": tx,
        "term_y": ty,
        "term_yaw_deg": math.degrees(tth),
        "term_geo_dist": float(term_dists[m]),
        "first_action": [float(u_batch[m, 0, 0].item()), float(u_batch[m, 0, 1].item())],
        "min_clearance_m": float(min_clr),
        "enters_corridor": enters_corr,
        "traj_x": traj_x.tolist(),
        "traj_y": traj_y.tolist(),
    })

# Save candidate data to scratch
with open("scratch/mppi_128_candidates_tick121.json", "w") as f:
    json.dump({
        "tick": target_tick,
        "robot_world_pos": [curr_px, curr_py],
        "robot_world_yaw_deg": curr_deg,
        "robot_odom_pos": [c_x, c_y],
        "macro_frontier": [float(f_star_x), float(f_star_y)],
        "current_geo_dist": float(current_geo_dist),
        "candidates": candidates_data
    }, f, indent=2)

print(f"Successfully evaluated and dumped all {M} candidate trajectories.")
