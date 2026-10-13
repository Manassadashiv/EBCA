import math
import time
import json
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

repo_root = Path(__file__).resolve().parent.parent
import sys
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

def run_r4_5_p0_offline_replay():
    print("=" * 70)
    print("R4.5-P0: OFFLINE CANDIDATE REPLAY & PREDICTIVE SAFETY COMPARISON")
    print("=" * 70)

    # Load Environment 2 (Asymmetric T-Junction / 0.65m Corridor)
    env2_xml = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
    env2_grid = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"

    config_20 = {
        "x0": 0.4908, "y0": 0.0087, "th0": 0.0056, "seed": 5001
    }

    import mujoco
    hal = CarlStage1HAL(xml_path=str(env2_xml))
    engine = CARLActiveInferenceEngine(grid_path=str(env2_grid))
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [config_20["x0"], config_20["y0"]]
    syaw = config_20["th0"]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    engine.initialize_pose(config_20["x0"], config_20["y0"], config_20["th0"])

    print("Stepping CARL to channel entry point (tick 0 to 75)...")
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    
    # Run until CARL has reversed, rotated, and is positioned at the corridor mouth (y ≈ -0.35m to -0.45m)
    corridor_decision_state = None
    v_est = 0.0
    
    for tick in range(120):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])
        
        q_curr = hal.data.qpos[qa:qa+7]
        curr_y = float(q_curr[1])
        curr_x = float(q_curr[0])
        curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        
        if tick % 10 == 0:
            print(f"  Tick {tick:3d}: x={curr_x:+.4f}, y={curr_y:+.4f}, yaw={math.degrees(curr_yaw):+.1f}°, v_est={v_est:.3f}")
        
        # Capture at exact Tick 80 corridor entry state:
        if tick == 80 and corridor_decision_state is None:
            corridor_decision_state = {
                "tick": tick,
                "x": curr_x,
                "y": curr_y,
                "yaw": curr_yaw,
                "v_est": v_est,
                "gyro_yaw": gyro_yaw,
                "sensors": sensors.copy()
            }
            print(f"\n---> CAPTURED CORRIDOR DECISION STEP at tick {tick}:")
            print(f"     Position: ({curr_x:.4f}, {curr_y:.4f}), Yaw: {math.degrees(curr_yaw):.1f} deg")
            print(f"     Left Sonar (sens 12): {sensors[12]:.3f} m, Right Sonar (sens 2): {sensors[2]:.3f} m")
            print(f"     Corridor width estimate: {sensors[12] + sensors[2] + 0.36:.3f} m")
            print(f"     Centerline offset e_c: {(sensors[12] - sensors[2]) / 2.0 * 100:.1f} cm")
            break
            
        engine.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, _ = engine.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])
        hal.step(cmd_6d)
        
        u_fwd = 0.5 * (cmd_6d[0] + cmd_6d[1])
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

    if corridor_decision_state is None:
        print("Failed to reach corridor mouth within 120 ticks!")
        return

    # Now run the offline replay on the CAPTURED decision state:
    c_x = corridor_decision_state["x"]
    c_y = corridor_decision_state["y"]
    c_th = corridor_decision_state["yaw"]
    curr_v = corridor_decision_state["v_est"]
    curr_w = corridor_decision_state["gyro_yaw"]
    curr_sensors = corridor_decision_state["sensors"]
    
    # 1. Sample the exact M=128 candidate trajectories from this pose
    torch.manual_seed(42) # Deterministic comparison
    u_batch = engine._sample_trajectories() # (M=128, H=15, 2)
    poses_x, poses_y, poses_th = engine._vectorized_rollout(c_x, c_y, c_th, curr_v, curr_w, u_batch)
    
    # Analyze candidate candidate properties:
    M, H = poses_x.shape[0], poses_x.shape[1]
    u_fwd_cands = 0.5 * (u_batch[:, :, 0] + u_batch[:, :, 1]).mean(dim=1).numpy()
    u_rot_cands = (u_batch[:, :, 1] - u_batch[:, :, 0]).mean(dim=1).numpy()
    
    print(f"\nGenerated M={M} candidate trajectories:")
    print(f"  Forward speed range: min={u_fwd_cands.min():.2f}, max={u_fwd_cands.max():.2f}, mean={u_fwd_cands.mean():.2f}")
    print(f"  Rotation rate range: min={u_rot_cands.min():.2f}, max={u_rot_cands.max():.2f}, mean={u_rot_cands.mean():.2f}")
    
    # Count how many fast candidates exist:
    fast_straight = (u_fwd_cands >= 0.40) & (np.abs(u_rot_cands) <= 0.15)
    print(f"  Number of Fast Straight candidates (u_fwd >= 0.40, |u_rot| <= 0.15): {np.sum(fast_straight)} / {M}")
    
    # Evaluate under Formulation A: R4.3 Baseline (Isotropic 0.15m proximity, 35.0 weight)
    efe_a, dbg_a = engine._evaluate_expected_free_energy(poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, curr_sensors, None)
    weights_a = torch.exp(-(efe_a - efe_a.min()) / engine.temperature)
    weights_a /= (weights_a.sum() + 1e-8)
    u_star_a = torch.sum(weights_a.unsqueeze(1) * u_batch[:, 0, :], dim=0).numpy()
    
    # Evaluate under Formulation B: R4.5 Predictive Safety (Centerline + Approach Rate + Rotational Risk)
    # Let's compute the components:
    d_l_side = float(curr_sensors[12])
    d_r_side = float(curr_sensors[2])
    e_center = (d_l_side - d_r_side) / 2.0 # Positive if closer to right wall, negative if closer to left
    
    # Generic Wall Normal & Corridor Tangent from Sonar TLS Fit
    dists = curr_sensors[:15].astype(np.float32)
    heading_diag = engine.heading_estimator.analyze_sonar_geometry(dists, omega=0.0)
    
    wall_valid = heading_diag["sonar_heading_valid"]
    local_wall_angle = heading_diag["sonar_wall_angle"] # Angle of wall in robot body frame (rad)
    wall_conf = heading_diag["sonar_heading_confidence"]
    
    print(f"\nGeneric Sonar Wall Estimation at Tick {corridor_decision_state['tick']}:")
    print(f"  Wall fit valid: {wall_valid}, confidence: {wall_conf:.2f}, condition: {heading_diag.get('sonar_geometry_condition')}")
    print(f"  Local wall angle in body frame: {math.degrees(local_wall_angle):+.1f} deg")
    
    # Inferred corridor tangent in world frame:
    # Wall runs along robot heading + local_wall_angle
    th_wall_world = c_th + local_wall_angle
    # Ensure tangent points generally toward forward macro goal
    th_goal = math.atan2(poses_y[0, -1] - c_y, poses_x[0, -1] - c_x)
    if math.cos(th_wall_world - th_goal) < 0:
        th_corridor = math.atan2(math.sin(th_wall_world + math.pi), math.cos(th_wall_world + math.pi))
    else:
        th_corridor = th_wall_world
        
    print(f"  Inferred corridor tangent: {math.degrees(th_corridor):+.1f} deg (Goal direction: {math.degrees(th_goal):+.1f} deg)")
    
    # Corridor width & Centerline offset e_c from lateral sonars:
    d_l_side = float(curr_sensors[12])
    d_r_side = float(curr_sensors[2])
    e_center = (d_l_side - d_r_side) / 2.0  # (meters)
    in_corridor = (d_l_side < 0.65 and d_r_side < 0.65 and (0.35 <= d_l_side + d_r_side <= 0.95))
    print(f"  In Corridor: {in_corridor}, d_L: {d_l_side:.3f}m, d_R: {d_r_side:.3f}m, Centerline offset e_c: {e_center*100:+.1f}cm")
    
    # Wall normal vectors in world frame:
    # Corridor tangent is along th_corridor. Left normal is +90 deg, Right normal is -90 deg.
    n_left = np.array([-math.sin(th_corridor), math.cos(th_corridor)])
    n_right = np.array([math.sin(th_corridor), -math.cos(th_corridor)])
    
    # -------------------------------------------------------------
    # Formulation B: R4.5-P1 Predictive Safety (Zero Forward-Bonus Modification)
    # -------------------------------------------------------------
    # Candidate velocity vector over horizon check steps:
    dt_total = H * engine.dt
    dx_cand = (poses_x[:, -1] - poses_x[:, 0]).numpy()
    dy_cand = (poses_y[:, -1] - poses_y[:, 0]).numpy()
    v_vec = np.stack([dx_cand / dt_total, dy_cand / dt_total], axis=-1) # (M, 2)
    
    # 1. Wall-normal closing rates:
    v_normal_left = np.dot(v_vec, n_left)    # Positive if moving toward left wall
    v_normal_right = np.dot(v_vec, n_right)  # Positive if moving toward right wall
    
    closing_left = np.maximum(0.0, v_normal_left)
    closing_right = np.maximum(0.0, v_normal_right)
    j_closing = 25.0 * (closing_left**2 + closing_right**2)
    
    # 2. Predicted Centerline Offset:
    # Project candidate lateral shift onto wall normal
    shift_normal = np.dot(np.stack([dx_cand, dy_cand], axis=-1), n_left)
    pred_e_c = e_center + shift_normal
    j_center = 15.0 * (pred_e_c / 0.08)**2
    
    # 3. Rotational Swept Hull Risk:
    j_rot = 12.0 * np.abs(u_rot_cands) * np.exp(-dbg_a["min_dists"] / 0.07)
    
    # 4. Corridor Alignment:
    # Angle error relative to inferred corridor tangent
    cand_yaws = poses_th[:, -1].numpy()
    heading_err_corridor = np.abs(np.arctan2(np.sin(cand_yaws - th_corridor), np.cos(cand_yaws - th_corridor)))
    j_corridor_align = 10.0 * (1.0 - np.cos(heading_err_corridor))
    
    # Total R4.5-P1 EFE:
    # Replace the isotropic proximity penalty (35.0 * j_proximity) with predictive terms:
    efe_b = (
        efe_a.numpy()
        - 35.00 * (np.maximum(0.0, (0.15 - dbg_a["min_dists"]) / 0.15)**2)  # Strip isotropic proximity penalty
        + j_closing
        + j_center
        + j_rot
        + j_corridor_align
    )
    # Maintain hard rectangular collision shield
    efe_b[dbg_a["collision_mask"]] = 1e6
    efe_b = torch.from_numpy(efe_b).float()
    
    weights_b = torch.exp(-(efe_b - efe_b.min()) / engine.temperature)
    weights_b /= (weights_b.sum() + 1e-8)
    u_star_b = torch.sum(weights_b.unsqueeze(1) * u_batch[:, 0, :], dim=0).numpy()
    
    print("\n" + "=" * 70)
    print("REPLAY COMPARISON RESULTS AT CORRIDOR ENTRY")
    print("=" * 70)
    print(f"Metric                        Formulation A (R4.3 Baseline)   Formulation B (R4.5 Predictive Safety)")
    print("-" * 70)
    print(f"Selected u_L*:                {u_star_a[0]:+8.3f}                        {u_star_b[0]:+8.3f}")
    print(f"Selected u_R*:                {u_star_a[1]:+8.3f}                        {u_star_b[1]:+8.3f}")
    
    u_fwd_a = 0.5 * (u_star_a[0] + u_star_a[1])
    u_fwd_b = 0.5 * (u_star_b[0] + u_star_b[1])
    u_turn_a = u_star_a[1] - u_star_a[0]
    u_turn_b = u_star_b[1] - u_star_b[0]
    
    print(f"Commanded Forward Velocity:   {u_fwd_a:8.3f} m/s                     {u_fwd_b:8.3f} m/s  (diff = {u_fwd_b - u_fwd_a:+.3f})")
    print(f"Commanded Turn Rate:          {u_turn_a:8.3f} rad/s                   {u_turn_b:8.3f} rad/s (diff = {u_turn_b - u_turn_a:+.3f})")
    
    top5_a = torch.topk(weights_a, 5).indices.numpy()
    top5_b = torch.topk(weights_b, 5).indices.numpy()
    
    print(f"\nTop 5 Candidates Picked by Formulation A (R4.3):")
    for idx in top5_a:
        print(f"  Candidate {idx:3d}: weight={weights_a[idx]:.3f}, u_fwd={u_fwd_cands[idx]:+.2f}, u_rot={u_rot_cands[idx]:+.2f}, min_d={dbg_a['min_dists'][idx]:.3f}m")
        
    print(f"\nTop 5 Candidates Picked by Formulation B (R4.5 Predictive):")
    for idx in top5_b:
        print(f"  Candidate {idx:3d}: weight={weights_b[idx]:.3f}, u_fwd={u_fwd_cands[idx]:+.2f}, u_rot={u_rot_cands[idx]:+.2f}, min_d={dbg_a['min_dists'][idx]:.3f}m, v_normal_left={v_normal_left[idx]:+.3f}m/s")
    
    # Verification of Hypothesis:
    print("\n" + "=" * 70)
    print("HYPOTHESIS VERIFICATION:")
    if u_fwd_b > u_fwd_a + 0.10:
        print(f"  [PASS] Predictive Safety successfully unlocked cruise speed ({u_fwd_b:.2f} vs {u_fwd_a:.2f} m/s).")
    else:
        print(f"  [FAIL] Speed not unlocked ({u_fwd_b:.2f} vs {u_fwd_a:.2f} m/s).")
        
    if np.abs(u_turn_b) < np.abs(u_turn_a) or np.abs(u_turn_b) < 0.10:
        print(f"  [PASS] Centering stability achieved (turn rate {u_turn_b:.3f} rad/s).")
    else:
        print(f"  [FAIL] Yaw instability detected ({u_turn_b:.3f} rad/s).")
    print("=" * 70)

if __name__ == "__main__":
    run_r4_5_p0_offline_replay()
