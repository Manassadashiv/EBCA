import sys
sys.path.insert(0, '.')
import mujoco, numpy as np, math, json
import torch
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from tests.test_stage3_4R2_remediation import build_50_matched_configurations
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

# 1. Setup Config 10
configs = build_50_matched_configurations()
cfg = configs[10]
print(f"Loaded Config {cfg['config_id']}: seed={cfg['seed']}, variation={cfg['variation_idx']}, spawn={cfg['spawn_pos']}")

torch.manual_seed(cfg['seed'])
np.random.seed(cfg['seed'])

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
target_tick = 165

# Step up to target_tick
for tick in range(target_tick):
    sensors = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=0.030)
    action, telem = ctrl.select_action(sensors[:15], curr_v=v_est, curr_w=float(sensors[20]))
    cmd_6d = np.zeros(6, dtype=np.float64)
    cmd_6d[0] = float(action[0])
    cmd_6d[1] = float(action[1])
    hal.step(cmd_6d)
    v_est = 0.70 * v_est + 0.30 * (0.5 * (cmd_6d[0] + cmd_6d[1]) * 0.30)

# We are now at tick 35.
sensors = hal.read_sensors()
sonars = sensors[:15]
gyro_yaw = float(sensors[20])
ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

q_curr = hal.data.qpos[qa:qa+7]
curr_px, curr_py = float(q_curr[0]), float(q_curr[1])
curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
curr_deg = math.degrees(curr_yaw)

# Update occupancy memory from live observation
ctrl.update_occupancy_memory(sonars)
c_x, c_y, c_th = ctrl.pose

# Generate M=128 candidate trajectories around nominal
u_batch = ctrl._sample_trajectories()
M, H = u_batch.shape[0], u_batch.shape[1]

# Rollout dynamics in odometry frame
poses_x_odom, poses_y_odom, poses_th_odom = ctrl._vectorized_rollout(c_x, c_y, c_th, v_est, gyro_yaw, u_batch)

# Transform poses to world frame for exact spatial analysis:
# Pose offset between world and odometry
dx_wo = curr_px - c_x
dy_wo = curr_py - c_y
dth_wo = curr_yaw - c_th

poses_x_world = poses_x_odom + dx_wo
poses_y_world = poses_y_odom + dy_wo
poses_th_world = poses_th_odom + dth_wo

# Macro-frontier extraction
macro_res = ctrl._compute_macro_frontier(c_x, c_y)
if macro_res is not None:
    f_star_x_odom, f_star_y_odom, current_geo_dist, dist_field = macro_res
    # World coordinates of macro frontier
    f_star_x_world = f_star_x_odom + dx_wo
    f_star_y_world = f_star_y_odom + dy_wo
else:
    f_star_x_odom, f_star_y_odom, current_geo_dist, dist_field = 0.0, 0.0, 99.0, np.zeros((128, 128))
    f_star_x_world, f_star_y_world = 0.0, 0.0

# Evaluate EFE
efe_costs, efe_debug = ctrl._evaluate_expected_free_energy(
    poses_x_odom, poses_y_odom, poses_th_odom, u_batch, c_x, c_y, c_th, sonars, None
)

# Detailed term decomposition
sub_x = poses_x_odom[:, ctrl.chk_idx]
sub_y = poses_y_odom[:, ctrl.chk_idx]
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
norm_tx = (poses_x_odom[:, -1] / ctrl.half_size).clamp(-1.0, 1.0)
norm_ty = (poses_y_odom[:, -1] / ctrl.half_size).clamp(-1.0, 1.0)
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

# Compute exact physical corridor wall clearance
WALL_SEGMENTS = [
    ((-0.60,  0.35), ( 0.35,  0.35)),
    ((-0.60, -0.35), ( 0.35, -0.35)),
    (( 0.35,  0.35), ( 0.35,  0.65)),
    (( 0.35, -0.35), ( 0.35, -0.65)),
    (( 0.35,  0.65), ( 0.85,  0.65)),
    (( 0.35, -0.65), ( 0.85, -0.65)),
    (( 0.85,  0.65), ( 0.85,  0.35)),
    (( 0.85, -0.65), ( 0.85, -0.35)),
    (( 0.85,  0.35), ( 1.20,  0.35)),
    (( 0.85, -0.35), ( 1.20, -0.35)),
    (( 1.20, -0.35), ( 1.20,  0.35)),
]

def dist_point_to_segment(px, py, p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

def compute_corridor_wall_clearance(px, py):
    r_hull = 0.14
    d_wall = min(dist_point_to_segment(px, py, p1, p2) for p1, p2 in WALL_SEGMENTS)
    return d_wall - r_hull

# Action weighting
min_cost = torch.min(efe_costs)
scaled_costs = efe_costs - min_cost
weights = torch.exp(-scaled_costs / ctrl.temperature)
weights_sum = torch.sum(weights) + 1e-8
norm_weights = (weights / weights_sum).numpy()
u_optimal = torch.sum((weights / weights_sum).unsqueeze(1) * u_batch[:, 0, :], dim=0)
u_star = u_optimal.clamp(-1.0, 1.0).numpy()

candidates = []
for m in range(M):
    tx_w = float(poses_x_world[m, -1].item())
    ty_w = float(poses_y_world[m, -1].item())
    tth_w = float(poses_th_world[m, -1].item())
    
    traj_xw = poses_x_world[m].numpy()
    traj_yw = poses_y_world[m].numpy()
    min_clr = min(compute_corridor_wall_clearance(traj_xw[s], traj_yw[s]) for s in range(H))
    enters_corr = bool(tx_w <= 0.35)
    
    candidates.append({
        "idx": m,
        "collision": bool(collision_mask[m]),
        "j_margin": float(j_margin_norm[m]),
        "j_jerk": float(j_jerk_norm[m]),
        "steer": float(steer_norm[m]),
        "phi_frontier": float(phi_norm[m]),
        "geodesic_reward": float(ctrl.alpha_epistemic * phi_norm[m]),
        "g_total": float(g_total[m]),
        "weight": float(norm_weights[m]),
        "term_x": tx_w,
        "term_y": ty_w,
        "term_yaw_deg": math.degrees(tth_w),
        "term_geo_dist": float(term_dists[m]),
        "first_action": [float(u_batch[m, 0, 0].item()), float(u_batch[m, 0, 1].item())],
        "min_clearance_m": float(min_clr),
        "enters_corridor": enters_corr,
        "traj_x": traj_xw.tolist(),
        "traj_y": traj_yw.tolist(),
    })

# Analysis & Classification
corr_candidates = [c for c in candidates if c["enters_corridor"] and not c["collision"]]
bay_candidates = [c for c in candidates if not c["enters_corridor"] and not c["collision"]]
coll_candidates = [c for c in candidates if c["collision"]]

best_corr = min(corr_candidates, key=lambda c: c["g_total"]) if corr_candidates else None
best_bay = min(bay_candidates, key=lambda c: c["g_total"]) if bay_candidates else None

# Check macro-frontier physical location:
# Intended downstream unexplored region: x <= 0.35 (corridor and arena heading to exit at x <= -0.55)
downstream_ok = bool(f_star_x_world <= 0.35)

print(f"\n================ FORENSIC ANALYSIS SUMMARY ================")
print(f"Episode / Config:     Config {cfg['config_id']} (Seed {cfg['seed']}, Variation {cfg['variation_idx']})")
print(f"Stall Timestep:       Tick {target_tick} (dt=0.030s, elapsed=1.05s)")
print(f"Robot World Pose:     x = {curr_px:.4f} m, y = {curr_py:.4f} m, yaw = {curr_deg:+.2f} deg")
print(f"Inside Turning Bay:   {bool(0.35 <= curr_px <= 0.85 and abs(curr_py) <= 0.65)}")
print(f"Facing Exit Corridor: {bool(math.cos(curr_yaw) < -0.80)} (cos(yaw) = {math.cos(curr_yaw):.3f})")
print(f"Selected Macro-Frontier: World ({f_star_x_world:.3f}, {f_star_y_world:.3f}) | Odom ({f_star_x_odom:.3f}, {f_star_y_odom:.3f})")
print(f"Macro-Frontier Physically in Downstream Region: {downstream_ok}")
print(f"Current Geodesic Dist to Frontier: {current_geo_dist:.3f} m")
print(f"Total MPPI Candidates:           {M}")
print(f"  Inadmissible (Collision Veto): {len(coll_candidates)} ({len(coll_candidates)/M*100:.1f}%)")
print(f"  Feasible Corridor-Entering:    {len(corr_candidates)}")
print(f"  Feasible Bay-Remaining:        {len(bay_candidates)}")

if best_corr:
    print(f"\nBest Corridor-Entering Candidate (idx={best_corr['idx']}):")
    print(f"  Terminal Pos:      x_H = {best_corr['term_x']:.4f} m, y_H = {best_corr['term_y']:.4f} m")
    print(f"  Terminal Geo Dist: {best_corr['term_geo_dist']:.3f} m (delta_geo = {current_geo_dist - best_corr['term_geo_dist']:+.3f} m)")
    print(f"  Cost Decomposition:")
    print(f"    Margin Cost:     {best_corr['j_margin']:.4f}")
    print(f"    Jerk Cost:       {best_corr['j_jerk']:.4f}")
    print(f"    Steer Cost:      {best_corr['steer']:.4f}")
    print(f"    Geodesic Reward: {best_corr['geodesic_reward']:+.4f}")
    print(f"    TOTAL G:         {best_corr['g_total']:+.4f}")
    print(f"  First Action:      [{best_corr['first_action'][0]:+.3f}, {best_corr['first_action'][1]:+.3f}]")
    print(f"  Min Wall Clearance: {best_corr['min_clearance_m']:.4f} m")
    print(f"  Softmax Weight:    {best_corr['weight']:.4e}")

if best_bay:
    print(f"\nBest Bay-Remaining Candidate (idx={best_bay['idx']}):")
    print(f"  Terminal Pos:      x_H = {best_bay['term_x']:.4f} m, y_H = {best_bay['term_y']:.4f} m")
    print(f"  Terminal Geo Dist: {best_bay['term_geo_dist']:.3f} m (delta_geo = {current_geo_dist - best_bay['term_geo_dist']:+.3f} m)")
    print(f"  Cost Decomposition:")
    print(f"    Margin Cost:     {best_bay['j_margin']:.4f}")
    print(f"    Jerk Cost:       {best_bay['j_jerk']:.4f}")
    print(f"    Steer Cost:      {best_bay['steer']:.4f}")
    print(f"    Geodesic Reward: {best_bay['geodesic_reward']:+.4f}")
    print(f"    TOTAL G:         {best_bay['g_total']:+.4f}")
    print(f"  First Action:      [{best_bay['first_action'][0]:+.3f}, {best_bay['first_action'][1]:+.3f}]")
    print(f"  Min Wall Clearance: {best_bay['min_clearance_m']:.4f} m")
    print(f"  Softmax Weight:    {best_bay['weight']:.4e}")

print(f"\nSelected MPPI Action u*: [{u_star[0]:+.3f}, {u_star[1]:+.3f}]")

# Core Question Evaluation
core_question_ans = bool(best_corr and best_bay and best_corr["g_total"] < best_bay["g_total"])
print(f"\nCore Diagnostic Question:")
print(f"  \"Does there exist at least one collision-free candidate trajectory that enters")
print(f"   the corridor and has lower total G than the best trajectory that remains in the turning bay?\"")
print(f"  -> ANSWER: {'YES' if core_question_ans else 'NO'}")

# Classification Verdict
if not downstream_ok:
    verdict_letter = "D"
    verdict = "D) Macro-frontier is not actually downstream/relevant. Diagnosis: frontier representation/map problem."
elif len(corr_candidates) == 0:
    verdict_letter = "C"
    verdict = "C) NO — no collision-free corridor-entering trajectory exists in the candidate set. Diagnosis: action sampling / dynamics / horizon / geometry problem."
elif best_corr["g_total"] < best_bay["g_total"]:
    verdict_letter = "A"
    verdict = "A) YES — feasible corridor-entering trajectory exists and is lower-cost. Diagnosis: selection / temporal credit-assignment problem."
else:
    verdict_letter = "B"
    verdict = "B) NO — feasible corridor-entering trajectory exists but is higher-cost. Diagnosis: objective formulation / cost-scale / terminal-value problem."

print(f"\n>>> FINAL CLASSIFICATION VERDICT: <<<\n{verdict}")

# Save detailed JSON
out_json = {
    "config_id": cfg["config_id"],
    "seed": cfg["seed"],
    "tick": target_tick,
    "robot_world_pos": [curr_px, curr_py],
    "robot_world_yaw_deg": curr_deg,
    "robot_odom_pos": [c_x, c_y],
    "macro_frontier_world": [float(f_star_x_world), float(f_star_y_world)],
    "macro_frontier_odom": [float(f_star_x_odom), float(f_star_y_odom)],
    "macro_frontier_downstream_verified": downstream_ok,
    "current_geo_dist": float(current_geo_dist),
    "selected_action": u_star.tolist(),
    "core_question_answer": "YES" if core_question_ans else "NO",
    "classification_letter": verdict_letter,
    "classification_verdict": verdict,
    "best_corridor_entering": best_corr,
    "best_bay_remaining": best_bay,
    "candidates": candidates
}
with open("evidence/stage3_4R2/forensic_stall_candidates.json", "w") as f:
    json.dump(out_json, f, indent=2)
print("Saved evidence/stage3_4R2/forensic_stall_candidates.json")

# Generate Plot 1: Total G vs Terminal Longitudinal Position x_H
fig1, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
tx_all = [c["term_x"] for c in candidates]
g_all = [c["g_total"] for c in candidates]
coll_all = [c["collision"] for c in candidates]

# Plot collisions
coll_tx = [tx for tx, cl in zip(tx_all, coll_all) if cl]
coll_g = [0.85 for _ in coll_tx]
ax1.scatter(coll_tx, coll_g, color="#e41a1c", marker="x", s=50, alpha=0.7, label=f"Inadmissible Collision Veto (N={len(coll_tx)}, G=1e6)")

# Plot collision-free
free_tx = [tx for tx, cl in zip(tx_all, coll_all) if not cl]
free_g = [g for g, cl in zip(g_all, coll_all) if not cl]
free_corr = [tx <= 0.35 for tx in free_tx]

ax1.scatter([tx for tx, cr in zip(free_tx, free_corr) if cr],
            [g for g, cr in zip(free_g, free_corr) if cr],
            color="#2ca02c", marker="o", s=70, alpha=0.9, label=f"Feasible Corridor-Entering (N={sum(free_corr)}, x_H <= 0.35m)")

ax1.scatter([tx for tx, cr in zip(free_tx, free_corr) if not cr],
            [g for g, cr in zip(free_g, free_corr) if not cr],
            color="#377eb8", marker="o", s=60, alpha=0.9, label=f"Feasible Bay-Remaining (N={len(free_tx)-sum(free_corr)}, x_H > 0.35m)")

if best_corr:
    ax1.scatter([best_corr["term_x"]], [best_corr["g_total"]], color="#2ca02c", marker="*", s=280, edgecolor="black", zorder=6, label=f"Best Corridor Candidate (G={best_corr['g_total']:.4f})")
if best_bay:
    ax1.scatter([best_bay["term_x"]], [best_bay["g_total"]], color="#377eb8", marker="*", s=280, edgecolor="black", zorder=6, label=f"Best Bay Candidate (G={best_bay['g_total']:.4f})")

ax1.axvline(0.35, color="black", linestyle="--", lw=1.8, label="Corridor Entrance Boundary (x=0.35m)")
ax1.axvline(curr_px, color="gray", linestyle=":", lw=1.5, label=f"Current Robot Pos (x={curr_px:.3f}m)")

ax1.set_title(f"Expected Free Energy G vs Terminal Longitudinal Position x_H\nConfig 10 (Seed 5003), Tick {target_tick} at Corridor-Mouth Stall", fontsize=11, fontweight="bold")
ax1.set_xlabel("Terminal Longitudinal Position x_H (m) [Corridor <= 0.35m < Bay]", fontsize=10.5)
ax1.set_ylabel("Total Expected Free Energy G(tau)", fontsize=10.5)
ax1.set_ylim(-0.45, 1.05)
ax1.set_xlim(0.20, 0.65)
ax1.legend(loc="upper right", fontsize=8.0, frameon=True)
ax1.grid(True, alpha=0.3)
plt.tight_layout()
fig1_path = "evidence/stage3_4R2/figures/fig_forensic_g_vs_terminal_x.png"
fig1.savefig(fig1_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated {fig1_path}")

# Generate Plot 2: Trajectory Fan Visualization
fig2, ax2 = plt.subplots(figsize=(10, 8), dpi=300)

# Draw walls
# Approach corridor x in [-0.60, 0.35], y = +/-0.35
ax2.plot([-0.60, 0.35], [0.35, 0.35], color="black", lw=3.0)
ax2.plot([-0.60, 0.35], [-0.35, -0.35], color="black", lw=3.0)
# Shoulders at x=0.35
ax2.plot([0.35, 0.35], [0.35, 0.65], color="black", lw=3.0)
ax2.plot([0.35, 0.35], [-0.35, -0.65], color="black", lw=3.0)
# Bay walls x in [0.35, 0.85], y = +/-0.65
ax2.plot([0.35, 0.85], [0.65, 0.65], color="black", lw=3.0)
ax2.plot([0.35, 0.85], [-0.65, -0.65], color="black", lw=3.0)
# Exit shoulders at x=0.85
ax2.plot([0.85, 0.85], [0.65, 0.35], color="black", lw=3.0)
ax2.plot([0.85, 0.85], [-0.65, -0.35], color="black", lw=3.0)
# Dead end cap
ax2.plot([0.85, 1.20], [0.35, 0.35], color="black", lw=3.0)
ax2.plot([0.85, 1.20], [-0.35, -0.35], color="black", lw=3.0)
ax2.plot([1.20, 1.20], [-0.35, 0.35], color="black", lw=3.0)

ax2.axvline(0.35, color="purple", linestyle="--", lw=1.5, alpha=0.7, label="Corridor Entrance (x=0.35m)")

# Plot all candidate trajectories
for c in candidates:
    xs = [curr_px] + c["traj_x"]
    ys = [curr_py] + c["traj_y"]
    if c["collision"]:
        ax2.plot(xs, ys, color="#e41a1c", alpha=0.12, lw=0.9)
    elif c["enters_corridor"]:
        ax2.plot(xs, ys, color="#2ca02c", alpha=0.45, lw=1.5)
    else:
        ax2.plot(xs, ys, color="#377eb8", alpha=0.20, lw=0.9)

# Highlight Best Corridor, Best Bay, and Selected u*
if best_corr:
    ax2.plot([curr_px] + best_corr["traj_x"], [curr_py] + best_corr["traj_y"], color="#2ca02c", lw=3.2, label=f"Best Corridor Candidate (G={best_corr['g_total']:.4f})")
if best_bay:
    ax2.plot([curr_px] + best_bay["traj_x"], [curr_py] + best_bay["traj_y"], color="#377eb8", lw=3.0, linestyle="--", label=f"Best Bay Candidate (G={best_bay['g_total']:.4f})")

# Plot robot pose
ax2.scatter([curr_px], [curr_py], color="red", s=110, zorder=6, label=f"Robot Pose ({curr_px:.3f}, {curr_py:.3f})")
# Heading arrow
arrow_len = 0.08
arrow_dx = arrow_len * math.cos(curr_yaw)
arrow_dy = arrow_len * math.sin(curr_yaw)
ax2.arrow(curr_px, curr_py, arrow_dx, arrow_dy, head_width=0.03, head_length=0.03, fc="red", ec="red", zorder=7)

# Plot selected macro-frontier
frontier_tag = "[DOWNSTREAM]" if downstream_ok else "[BEHIND DEAD-END!]"
ax2.scatter([f_star_x_world], [f_star_y_world], color="gold", marker="*", s=300, edgecolor="black", zorder=8, label=f"Selected Macro-Frontier ({f_star_x_world:.2f}, {f_star_y_world:.2f}) {frontier_tag}")

ax2.set_title(f"MPPI 128-Candidate Trajectory Fan at Corridor-Mouth Stall\nConfig 10 (Seed 5003), Tick {target_tick} (Pose: [{curr_px:.3f}, {curr_py:.3f}], Heading: {curr_deg:+.1f}°)", fontsize=11, fontweight="bold")
ax2.set_xlabel("World X (m)", fontsize=10.5); ax2.set_ylabel("World Y (m)", fontsize=10.5)
ax2.set_aspect("equal")
ax2.set_xlim(-2.5, 1.4)
ax2.set_ylim(-1.2, 1.2)
ax2.legend(loc="lower left", fontsize=8.0, frameon=True)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
fig2_path = "evidence/stage3_4R2/figures/fig_forensic_trajectory_fan_stall.png"
fig2.savefig(fig2_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated {fig2_path}")
