import math
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

repo_root = Path("d:/ebca")
import sys
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
import mujoco

def sample_piecewise_sobol_candidates(M=128, H=15, nominal_u=None, device="cpu"):
    """
    R4.5-P2: Piecewise-continuous low-discrepancy (Sobol) candidate generation.
    Replaces rigid manual partitions with continuous wheel-space coverage.
    """
    # 3 control knots: t=0, t=7, t=14
    num_knots = 3
    sobol = torch.quasirandom.SobolEngine(dimension=num_knots * 2, scramble=True, seed=42)
    # Draw Sobol samples in [-1.0, 1.0]
    raw_knots = (sobol.draw(M) * 2.0 - 1.0).view(M, num_knots, 2).to(device)
    
    # Linearly interpolate knots across horizon H=15
    # Input to F.interpolate: (M, 2, num_knots) -> Output: (M, 2, H)
    interp_u = F.interpolate(raw_knots.permute(0, 2, 1), size=H, mode='linear', align_corners=True).permute(0, 2, 1)
    
    # Reserve slot 0 for warm-started nominal trajectory
    if nominal_u is not None:
        interp_u[0] = nominal_u
        # Add 12 localized perturbations around nominal
        for k in range(1, 13):
            noise = torch.randn(H, 2, device=device) * 0.05
            interp_u[k] = torch.clamp(nominal_u + noise, -1.0, 1.0)
            
    return torch.clamp(interp_u, -1.0, 1.0)

def run_r4_5_p2a_replay():
    print("=" * 70)
    print("R4.5-P2a: PIECEWISE SOBOL CANDIDATE REPLAY & PREDICTIVE SAFETY")
    print("=" * 70)

    env2_xml = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
    env2_grid = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"

    hal = CarlStage1HAL(xml_path=str(env2_xml))
    engine = CARLActiveInferenceEngine(grid_path=str(env2_grid))

    config_20 = {"x0": 0.4908, "y0": 0.0087, "th0": 0.0056, "seed": 5001}
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [config_20["x0"], config_20["y0"]]
    syaw = config_20["th0"]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    engine.initialize_pose(config_20["x0"], config_20["y0"], config_20["th0"])

    curr_x = 0.8639
    curr_y = -0.5041
    curr_yaw = math.radians(-56.8)
    v_est = 0.28
    
    hal.data.qpos[qa:qa+2] = [curr_x, curr_y]
    hal.data.qpos[qa+3:qa+7] = [math.cos(curr_yaw / 2.0), 0.0, 0.0, math.sin(curr_yaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    engine.initialize_pose(curr_x, curr_y, curr_yaw)
    sensors = hal.read_sensors()
    dists = sensors[:15].astype(np.float32)

    print(f"\nTick 80 Physical State:")
    print(f"  Position: ({curr_x:.4f}, {curr_y:.4f})")
    print(f"  Yaw: {math.degrees(curr_yaw):+.1f} deg (Goal corridor is South: -90.0 deg)")
    print(f"  Heading error: {abs(math.degrees(curr_yaw) - (-90.0)):.1f} deg")
    print(f"  Left Sonar (12): {sensors[12]:.3f} m, Right Sonar (2): {sensors[2]:.3f} m")
    print(f"  All 15 Sonars: {np.round(dists, 3)}")
    print(f"  Sonar Angles (deg): {np.round(np.degrees(engine.sonar_angles_rad), 1)}")

    # Inferred corridor tangent from Sonar TLS
    heading_diag = engine.heading_estimator.analyze_sonar_geometry(dists, omega=0.0)
    
    # Sample M=128 candidates using the NEW Piecewise Sobol generator:
    M, H = 128, 15
    u_batch_sobol = sample_piecewise_sobol_candidates(M=M, H=H, nominal_u=engine.nominal_u, device="cpu")
    poses_x, poses_y, poses_th = engine._vectorized_rollout(curr_x, curr_y, curr_yaw, v_est, float(sensors[20]), u_batch_sobol)

    u_fwds = 0.5 * (u_batch_sobol[:, :, 0] + u_batch_sobol[:, :, 1]).mean(dim=1).numpy()
    u_rots = (u_batch_sobol[:, :, 1] - u_batch_sobol[:, :, 0]).mean(dim=1).numpy()
    term_yaws = poses_th[:, -1].numpy()
    term_xs = poses_x[:, -1].numpy()
    term_ys = poses_y[:, -1].numpy()

    delta_yaws = np.degrees(term_yaws - curr_yaw)
    
    # Evaluate under Predictive Safety:
    # 1. Base EFE from engine (evaluates macro-frontier, jerk, etc.)
    efe_base, dbg = engine._evaluate_expected_free_energy(poses_x, poses_y, poses_th, u_batch_sobol, curr_x, curr_y, curr_yaw, sensors, None)
    
    macro_res = engine._compute_macro_frontier(curr_x, curr_y)
    if macro_res is not None:
        f_x, f_y, d_cur, dist_field = macro_res
        print(f"Macro frontier target: ({f_x:.2f}, {f_y:.2f}), current geodesic dist: {d_cur:.2f}")
        rc_ix = int(np.clip((curr_x + engine.half_size) / engine.resolution, 0, engine.grid_size - 1))
        rc_iy = int(np.clip((curr_y + engine.half_size) / engine.resolution, 0, engine.grid_size - 1))
        d_e = dist_field[rc_iy, rc_ix + 1]
        d_w = dist_field[rc_iy, rc_ix - 1]
        d_n = dist_field[rc_iy + 1, rc_ix]
        d_s = dist_field[rc_iy - 1, rc_ix]
        grad_x = (d_e - d_w) / (2.0 * engine.resolution)
        grad_y = (d_n - d_s) / (2.0 * engine.resolution)
        # Channel corridor axis projection: if bounded laterally by obstacles in occupancy memory,
        # zero out the transverse gradient component that points into the walls
        has_obs_w = np.any(engine.grid_np[0, rc_iy, max(0, rc_ix-4):rc_ix] > 0.3)
        has_obs_e = np.any(engine.grid_np[0, rc_iy, rc_ix:min(engine.grid_size, rc_ix+5)] > 0.3)
        has_obs_s = np.any(engine.grid_np[0, max(0, rc_iy-4):rc_iy, rc_ix] > 0.3)
        has_obs_n = np.any(engine.grid_np[0, rc_iy:min(engine.grid_size, rc_iy+5), rc_ix] > 0.3)
        
        if has_obs_w and has_obs_e:
            # North-South corridor: transverse X motion blocked by walls
            grad_x = 0.0
        elif has_obs_s and has_obs_n:
            # East-West corridor: transverse Y motion blocked by walls
            grad_y = 0.0
            
        th_grad = math.atan2(-grad_y, -grad_x)
        print(f"Bounded Corridor Check: East-West walls={has_obs_w and has_obs_e}, North-South walls={has_obs_s and has_obs_n}")
        print(f"Filtered Grad: ({grad_x:.2f}, {grad_y:.2f}), Projected th_des: {math.degrees(th_grad):.1f} deg")
    
    # 2. Wall-normal closing rate from live sonar rays:
    # For each detected obstacle point p_k at distance d_k and angle phi_k:
    # Normal pointing toward robot: n_k = [-cos(phi_k), -sin(phi_k)]
    # Candidate velocity in body frame: v_body = [v_x_body, v_y_body]
    # Approach rate toward obstacle k: -d_dot_k = -v_body . n_k = v_x_body * cos(phi_k) + v_y_body * sin(phi_k)
    cos_c = math.cos(curr_yaw)
    sin_c = math.sin(curr_yaw)
    dx_world = (poses_x[:, -1] - poses_x[:, 0]).numpy()
    dy_world = (poses_y[:, -1] - poses_y[:, 0]).numpy()
    dt_total = H * engine.dt
    dx_body = dx_world * cos_c + dy_world * sin_c
    dy_body = -dx_world * sin_c + dy_world * cos_c
    v_x_body = dx_body / dt_total
    v_y_body = dy_body / dt_total
    
    valid_rays = (dists < 1.20)
    ray_angles = engine.sonar_angles_rad[valid_rays]
    ray_dists = dists[valid_rays]
    
    # Vectorized approach rate across all valid rays: shape (M, num_rays)
    v_xb = v_x_body[:, None]
    v_yb = v_y_body[:, None]
    cos_phi = np.cos(ray_angles)[None, :]
    sin_phi = np.sin(ray_angles)[None, :]
    
    closing_rates = v_xb * cos_phi + v_yb * sin_phi  # -d_dot_k
    pos_closing = np.maximum(0.0, closing_rates)
    
    # Distance weighting: walls close by (< 0.35m) dominate
    dist_weights = np.exp(-ray_dists[None, :] / 0.15)
    w_a = 60.0
    j_closing = w_a * np.sum((pos_closing**2) * dist_weights, axis=1)
    
    d_L = float(sensors[12])
    d_R = float(sensors[2])
    
    # 3. Centerline restoring cost: e_c = (d_L - d_R) / 2
    # At start, lateral error is e_c0 = (d_L - d_R) / 2.
    # At terminal, displacement dy_body shifts robot laterally:
    e_c0 = (d_L - d_R) / 2.0
    e_c_term = e_c0 - dy_body
    s_c = 0.08
    j_center = 20.0 * (e_c_term / s_c)**2
    
    # 4. Rotational hull clearance risk: J_rot = w_rot * |omega| * exp(-min_d / s_d)
    w_rot = 12.0
    s_d = 0.07
    j_rot = w_rot * np.abs(u_rots) * np.exp(-dbg["min_dists"] / s_d)
    
    # Recompute heading alignment and forward bonus with the projected corridor th_des:
    th_des = th_grad
    cos_term = np.cos(term_yaws - th_des)
    cos_mean = np.mean(np.cos(poses_th.numpy() - th_des), axis=1)
    cos_align = 0.40 * cos_term + 0.60 * cos_mean
    j_heading = 1.0 - cos_align
    
    # Directional turn consistency
    delta_th = math.atan2(math.sin(th_des - curr_yaw), math.cos(th_des - curr_yaw))
    u_diff = (u_batch_sobol[:, :, 1] - u_batch_sobol[:, :, 0]).mean(dim=1).numpy()
    j_wrong_turn = np.maximum(0.0, -u_diff * math.sin(delta_th)) * 8.0
    
    # Forward acceleration reward (unchanged weight 3.50 * 8.00):
    # Fix the 78% wall-charge leak diagnosed in R4.5-P0:
    # A candidate must physically align with the corridor axis by the end of its rollout (within 20 deg)
    # to earn forward cruise reward, preventing full throttle while misaligned
    cos_curr = math.cos(curr_yaw - th_des)
    curr_gate = float(np.clip((cos_curr - 0.50) / 0.50, 0.0, 1.0))
    # Terminal alignment threshold: cos(20 deg) = 0.940
    term_gate = np.clip((cos_term - 0.85) / 0.15, 0.0, 1.0)
    align_gate = curr_gate * term_gate
    j_fwd_bonus = np.maximum(0.0, u_fwds) * align_gate * 8.00
    
    # Macro-frontier progress
    phi_norm = dbg.get("phi_norm", np.zeros(M))
    
    # Jerk
    delta_u = u_batch_sobol[:, 1:, :] - u_batch_sobol[:, :-1, :]
    j_jerk_norm = np.clip(np.sum((delta_u.numpy())**2, axis=(1, 2)) / 56.0, 0.0, 1.0)
    
    # Total R4.5-P2 EFE:
    efe_r4_5 = (
        8.00 * j_heading +
        j_wrong_turn +
        0.15 * j_jerk_norm -
        3.50 * j_fwd_bonus +
        j_closing +
        j_center +
        j_rot
    )
    
    print("\n--- Diagnostic Cost Comparison (Cand 32 vs Cand 47) ---")
    for c_id in [32, 47]:
        print(f"Cand {c_id}:")
        print(f"  j_heading (x8):  {8.00 * j_heading[c_id]:.3f} (cos_align: {cos_align[c_id]:.3f})")
        print(f"  j_wrong_turn:    {j_wrong_turn[c_id]:.3f}")
        print(f"  j_fwd_bonus:     {-3.50 * j_fwd_bonus[c_id]:.3f} (align_gate: {align_gate[c_id]:.3f}, u_fwd: {u_fwds[c_id]:.3f})")
        print(f"  j_closing:       {j_closing[c_id]:.3f}")
        print(f"  j_center:        {j_center[c_id]:.3f} (e_c_term: {e_c_term[c_id]:.3f})")
        print(f"  j_rot:           {j_rot[c_id]:.3f}")
        print(f"  Total efe:       {efe_r4_5[c_id]:.3f}")
    
    # Hard collision shield veto
    efe_r4_5[dbg["collision_mask"]] = 1e6
    efe_r4_5 = torch.from_numpy(efe_r4_5).float()
    
    weights = torch.exp(-(efe_r4_5 - efe_r4_5.min()) / engine.temperature)
    weights /= (weights.sum() + 1e-8)
    u_optimal = torch.sum(weights.unsqueeze(1) * u_batch_sobol[:, 0, :], dim=0).numpy()
    
    best_idx = int(torch.argmax(weights).item())
    
    print("\n" + "=" * 70)
    print("R4.5-P2a REPLAY EVALUATION RESULTS")
    print("=" * 70)
    print(f"Optimal Action Selected: u_L* = {u_optimal[0]:+.3f}, u_R* = {u_optimal[1]:+.3f}")
    u_fwd_star = 0.5 * (u_optimal[0] + u_optimal[1])
    u_rot_star = u_optimal[1] - u_optimal[0]
    print(f"Commanded Forward Speed: {u_fwd_star:.3f} m/s")
    print(f"Commanded Turn Rate:     {u_rot_star:+.3f} rad/s")
    
    print(f"\nTop Selected Candidate ({best_idx}):")
    print(f"  Weight: {weights[best_idx]:.4f}")
    print(f"  Forward speed: {u_fwds[best_idx]:.3f} m/s")
    print(f"  Turn rate: {u_rots[best_idx]:+.3f} rad/s")
    print(f"  Start Yaw -> End Yaw: {math.degrees(curr_yaw):.1f} deg -> {math.degrees(term_yaws[best_idx]):.1f} deg (delta_theta = {delta_yaws[best_idx]:+.1f} deg)")
    print(f"  Start X -> End X:     {curr_x:.3f}m -> {term_xs[best_idx]:.3f}m (Centerline is 0.825m)")
    print(f"  Min clearance:        {dbg['min_dists'][best_idx]:.3f} m")
    print(f"  Closing cost J_closing: {j_closing[best_idx]:.3f}")
    print(f"  Collision Veto:       {dbg['collision_mask'][best_idx]}")
    
    print("\nTop 5 Candidates Picked by Softmax:")
    top5 = torch.topk(weights, 5).indices.numpy()
    for rank, idx in enumerate(top5):
        print(f"  #{rank+1} (Cand {idx:3d}): weight={weights[idx]:.3f}, u_fwd={u_fwds[idx]:+.2f}m/s, delta_theta={delta_yaws[idx]:+.1f} deg, End X={term_xs[idx]:.3f}m, Min d={dbg['min_dists'][idx]:.3f}m")
        
    print("\n" + "=" * 70)
    print("CANONICAL ORGANISM select_action() EXECUTION AT TICK 80:")
    print("=" * 70)
    action_can, telem = engine.select_action(sensors[:15], curr_v=v_est, curr_w=float(sensors[20]))
    u_fwd_can = 0.5 * (action_can[0] + action_can[1])
    u_rot_can = action_can[1] - action_can[0]
    print(f"Canonical Action: u_L = {action_can[0]:+.3f}, u_R = {action_can[1]:+.3f}")
    print(f"Forward Speed:    {u_fwd_can:.3f} m/s")
    print(f"Turn Rate:        {u_rot_can:+.3f} rad/s")
    print(f"Best Sample Idx:  {telem['best_sample_idx']}")
    print(f"Latency:          {telem['latency_ms']:.2f} ms")
    print("=" * 70)

if __name__ == "__main__":
    run_r4_5_p2a_replay()

