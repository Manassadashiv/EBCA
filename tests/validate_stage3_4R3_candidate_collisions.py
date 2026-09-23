"""
tests/validate_stage3_4R3_candidate_collisions.py — Deterministic Candidate-Veto Cross-Validation
Compares CARL's internal collision veto against ground-truth MuJoCo physical collision detection
for all 128 MPPI candidate trajectories at the Config-10 Tick-165 stall.
"""

import sys
from pathlib import Path
import math
import json
import numpy as np
import torch
import torch.nn.functional as F
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.test_stage3_4R2_remediation import build_50_matched_configurations
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine


def run_cross_validation():
    print("=" * 75)
    print("STAGE 3.4-R3 DETERMINISTIC CANDIDATE-VETO CROSS-VALIDATION")
    print("=" * 75)

    configs = build_50_matched_configurations()
    cfg = configs[10]
    seed = int(cfg["seed"])
    torch.manual_seed(seed)
    np.random.seed(seed)

    hal = CarlStage1HAL(xml_path=cfg["xml_path"])
    ctrl = CARLActiveInferenceEngine(
        grid_path=cfg["grid_path"],
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )

    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    ctrl.initialize_pose(sx, sy, syaw)

    v_est = 0.0
    target_tick = 165

    print(f"Rolling out Config 10 up to Tick {target_tick}...")
    for tick in range(target_tick):
        sensors = hal.read_sensors()
        ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=0.030)
        action, telem = ctrl.select_action(sensors[:15], curr_v=v_est, curr_w=float(sensors[20]))
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])
        hal.step(cmd_6d)
        v_est = 0.70 * v_est + 0.30 * (0.5 * (cmd_6d[0] + cmd_6d[1]) * 0.30)

    # State at Tick 165
    qpos_snap = hal.data.qpos.copy()
    qvel_snap = hal.data.qvel.copy()
    act_snap = hal.data.act.copy() if hal.data.act is not None else None
    v_est_snap = float(v_est)

    q_curr = hal.data.qpos[qa:qa+7]
    curr_px, curr_py = float(q_curr[0]), float(q_curr[1])
    curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
    c_x, c_y, c_th = ctrl.pose

    print(f"Arrived at Tick {target_tick}:")
    print(f"  MuJoCo Pose:     x = {curr_px:.4f} m, y = {curr_py:.4f} m, yaw = {math.degrees(curr_yaw):+.2f} deg")
    print(f"  Odometry Pose:   x = {c_x:.4f} m, y = {c_y:.4f} m, yaw = {math.degrees(c_th):+.2f} deg")
    print(f"  Drift Magnitude: {math.hypot(curr_px - c_x, curr_py - c_y):.4f} m")

    # Sample candidate trajectories from frozen R3 controller
    u_batch = ctrl._sample_trajectories()  # (128, 15, 2)
    M, H = u_batch.shape[0], u_batch.shape[1]

    # Evaluate CARL's internal collision veto on Channel 0 using Oriented Rectangular Hull (OBB)
    poses_x_odom, poses_y_odom, poses_th_odom = ctrl._vectorized_rollout(
        c_x, c_y, c_th, v_est_snap, float(sensors[20]), u_batch
    )
    sub_x = poses_x_odom[:, ctrl.chk_idx]
    sub_y = poses_y_odom[:, ctrl.chk_idx]
    sub_th = poses_th_odom[:, ctrl.chk_idx]
    cos_th = torch.cos(sub_th).unsqueeze(-1)
    sin_th = torch.sin(sub_th).unsqueeze(-1)
    rot_dx = ctrl.hull_body_x * cos_th - ctrl.hull_body_y * sin_th
    rot_dy = ctrl.hull_body_x * sin_th + ctrl.hull_body_y * cos_th
    cat_qx = (sub_x.unsqueeze(-1) + rot_dx).view(M, -1)
    cat_qy = (sub_y.unsqueeze(-1) + rot_dy).view(M, -1)
    norm_x = (cat_qx / ctrl.half_size).clamp(-1.0, 1.0)
    norm_y = (cat_qy / ctrl.half_size).clamp(-1.0, 1.0)
    grid_coords = torch.stack([norm_x, norm_y], dim=-1).unsqueeze(1)
    grid_b_ch0 = ctrl.grid[:, 0:1, :, :].expand(M, 1, ctrl.grid_size, ctrl.grid_size)
    with torch.inference_mode():
        sampled_occ = F.grid_sample(
            grid_b_ch0, grid_coords, mode="bilinear", padding_mode="zeros", align_corners=True
        ).squeeze(1).squeeze(1)

    max_occ_hits = torch.max(sampled_occ, dim=-1).values
    carl_veto_mask = (max_occ_hits > 0.85).cpu().numpy()

    # Now perform deterministic MuJoCo physical rollouts for all 128 candidates
    print(f"\nExecuting {M} deterministic physical rollouts in MuJoCo...")
    results = []

    for m in range(M):
        # 1. Restore exact MuJoCo snapshot
        hal.data.qpos[:] = qpos_snap
        hal.data.qvel[:] = qvel_snap
        if act_snap is not None:
            hal.data.act[:] = act_snap
        mujoco.mj_forward(hal.model, hal.data)

        # 2. Step candidate through 15 control steps in MuJoCo
        mujoco_collided = False
        collision_events = []
        traj_px = [curr_px]
        traj_py = [curr_py]

        u_candidate = u_batch[m].cpu().numpy()  # (15, 2)
        v_est_sim = v_est_snap

        for h in range(H):
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(u_candidate[h, 0])
            cmd_6d[1] = float(u_candidate[h, 1])

            # Advance by 3 physics substeps of 0.010s
            hal.write_actuators(cmd_6d)
            for sub in range(3):
                mujoco.mj_step(hal.model, hal.data)

                # Check contacts at every sub-step
                for i in range(hal.data.ncon):
                    c = hal.data.contact[i]
                    in1 = c.geom1 in hal.carl_geom_ids
                    in2 = c.geom2 in hal.carl_geom_ids
                    if (in1 and not in2) or (in2 and not in1):
                        other_geom = c.geom2 if in1 else c.geom1
                        if other_geom != hal.floor_geom_id:
                            # Obstacle collision!
                            carl_geom_name = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1 if in1 else c.geom2) or "carl_geom"
                            obs_geom_name = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, other_geom) or "obs_geom"
                            mujoco_collided = True
                            collision_events.append({
                                "step": h,
                                "substep": sub,
                                "carl_geom": carl_geom_name,
                                "obs_geom": obs_geom_name,
                                "penetration_dist": float(c.dist)
                            })

            v_est_sim = 0.70 * v_est_sim + 0.30 * (0.5 * (cmd_6d[0] + cmd_6d[1]) * 0.30)
            cur_x = float(hal.data.qpos[qa])
            cur_y = float(hal.data.qpos[qa+1])
            traj_px.append(cur_x)
            traj_py.append(cur_y)

        term_px = traj_px[-1]
        term_py = traj_py[-1]
        enters_corr = bool(term_px <= 0.35)

        results.append({
            "idx": m,
            "carl_veto": bool(carl_veto_mask[m]),
            "max_occ_hit": float(max_occ_hits[m].item()),
            "mujoco_collided": bool(mujoco_collided),
            "collision_event_count": len(collision_events),
            "first_collision_event": collision_events[0] if collision_events else None,
            "enters_corridor": enters_corr,
            "term_px": term_px,
            "term_py": term_py,
            "first_action": [float(u_candidate[0, 0]), float(u_candidate[0, 1])],
            "traj_px": traj_px,
            "traj_py": traj_py,
        })

    # Confusion Matrix Calculation
    # Classes:
    # TP: CARL Veto = True,  MuJoCo Collided = True  (Genuine physical constraint)
    # FP: CARL Veto = True,  MuJoCo Collided = False (False Positive / Veto Bug / Footprint Mismatch)
    # FN: CARL Veto = False, MuJoCo Collided = True  (Safety Veto Bug)
    # TN: CARL Veto = False, MuJoCo Collided = False (Valid Candidate)
    tp = sum(1 for r in results if r["carl_veto"] and r["mujoco_collided"])
    fp = sum(1 for r in results if r["carl_veto"] and not r["mujoco_collided"])
    fn = sum(1 for r in results if not r["carl_veto"] and r["mujoco_collided"])
    tn = sum(1 for r in results if not r["carl_veto"] and not r["mujoco_collided"])

    # Subset: enters_corridor == True
    corr_results = [r for r in results if r["enters_corridor"]]
    tp_corr = sum(1 for r in corr_results if r["carl_veto"] and r["mujoco_collided"])
    fp_corr = sum(1 for r in corr_results if r["carl_veto"] and not r["mujoco_collided"])
    fn_corr = sum(1 for r in corr_results if not r["carl_veto"] and r["mujoco_collided"])
    tn_corr = sum(1 for r in corr_results if not r["carl_veto"] and not r["mujoco_collided"])

    print("\n" + "=" * 75)
    print("FOUR-WAY CONFUSION MATRIX: CARL COLLISION VETO vs MUJOCO GROUND TRUTH")
    print("=" * 75)
    print(f"Total MPPI Candidates Evaluated: {M}")
    print(f"  CARL Vetoed:   {sum(1 for r in results if r['carl_veto'])} ({sum(1 for r in results if r['carl_veto'])/M*100:.1f}%)")
    print(f"  MuJoCo Collided: {sum(1 for r in results if r['mujoco_collided'])} ({sum(1 for r in results if r['mujoco_collided'])/M*100:.1f}%)")

    print("\n--- ALL CANDIDATES (N=128) ---")
    print(f"  True Positives  (CARL Veto=YES, MuJoCo=COLLISION):    {tp:3d} ({tp/M*100:5.1f}%) [Genuine Physical Constraints]")
    print(f"  False Positives (CARL Veto=YES, MuJoCo=NO COLLISION): {fp:3d} ({fp/M*100:5.1f}%) [CARL FALSE-ALARM VETOES]")
    print(f"  False Negatives (CARL Veto=NO,  MuJoCo=COLLISION):    {fn:3d} ({fn/M*100:5.1f}%) [Safety Failures]")
    print(f"  True Negatives  (CARL Veto=NO,  MuJoCo=NO COLLISION): {tn:3d} ({tn/M*100:5.1f}%) [Valid Admissible Paths]")

    print(f"\n--- CORRIDOR-ENTERING CANDIDATES (N={len(corr_results)}) ---")
    if corr_results:
        N_c = len(corr_results)
        print(f"  True Positives  (CARL Veto=YES, MuJoCo=COLLISION):    {tp_corr:3d} ({tp_corr/N_c*100:5.1f}%)")
        print(f"  False Positives (CARL Veto=YES, MuJoCo=NO COLLISION): {fp_corr:3d} ({fp_corr/N_c*100:5.1f}%) [CRITICAL FALSE POSITIVES]")
        print(f"  False Negatives (CARL Veto=NO,  MuJoCo=COLLISION):    {fn_corr:3d} ({fn_corr/N_c*100:5.1f}%)")
        print(f"  True Negatives  (CARL Veto=NO,  MuJoCo=NO COLLISION): {tn_corr:3d} ({tn_corr/N_c*100:5.1f}%)")
    else:
        print("  None entered corridor.")

    # Detailed Inspection of False Positive Corridor-Entering Candidates
    fp_corr_list = [r for r in corr_results if r["carl_veto"] and not r["mujoco_collided"]]
    print(f"\nDetailed Inspection of False-Positive Corridor Candidates (Count = {len(fp_corr_list)}):")
    for r in fp_corr_list[:10]:
        print(f"  Candidate idx {r['idx']:3d}: term_pos=({r['term_px']:.3f}, {r['term_py']:.3f}) | "
              f"act=[{r['first_action'][0]:+.2f}, {r['first_action'][1]:+.2f}] | "
              f"max_occ_hit={r['max_occ_hit']:.2f} | MuJoCo Collided={r['mujoco_collided']}")

    # Identify the primary bottleneck:
    if fp > 0 and fp_corr > 0:
        bottleneck = "A"
        diag_desc = (
            f"(A) FALSE-POSITIVE COLLISION VETO: {fp_corr} corridor-entering trajectories are physically "
            f"100% collision-free in MuJoCo, but CARL's internal collision veto rejects them due to "
            f"odometry-drift induced phantom hits in the internal occupancy grid."
        )
    elif tp_corr == len(corr_results) and len(corr_results) > 0:
        bottleneck = "B"
        diag_desc = (
            "(B) GENUINE PHYSICAL INFEASIBILITY: All corridor-entering candidates genuinely collide with "
            "the corridor mouth in MuJoCo physics."
        )
    else:
        bottleneck = "C"
        diag_desc = (
            "(C) ACTION SAMPLING / DYNAMICS MISMATCH: No feasible corridor-entering candidates exist in candidate ensemble."
        )

    print("\n" + "=" * 75)
    print(f"PRIMARY BOTTLENECK CLASSIFICATION: {bottleneck}")
    print(f"Description: {diag_desc}")
    print("=" * 75)

    # Save artifact JSON
    out_dir = repo_root / "evidence" / "stage3_4R2"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidate_collision_cross_validation.json"

    report_data = {
        "config_id": 10,
        "seed": seed,
        "tick": target_tick,
        "robot_world_pose": [curr_px, curr_py, math.degrees(curr_yaw)],
        "robot_odom_pose": [c_x, c_y, math.degrees(c_th)],
        "odometry_drift_m": math.hypot(curr_px - c_x, curr_py - c_y),
        "total_candidates": M,
        "confusion_matrix_all": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn
        },
        "confusion_matrix_corridor_entering": {
            "total_corridor_entering": len(corr_results),
            "true_positives": tp_corr,
            "false_positives": fp_corr,
            "false_negatives": fn_corr,
            "true_negatives": tn_corr
        },
        "bottleneck_classification": bottleneck,
        "bottleneck_description": diag_desc,
        "sample_false_positives": fp_corr_list[:15]
    }

    with open(out_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nSaved cross-validation results to: {out_path}")


if __name__ == "__main__":
    run_cross_validation()
