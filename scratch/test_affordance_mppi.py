"""
scratch/test_affordance_mppi.py — Test Active Inference with Rotational Affordance & Clean Reversals
Tests Config 0 (Env 1) and Config 20, 21, 22 (Env 2) for:
1. Reversal >= 10 ticks
2. Pivot >= 90 deg
3. Channel Entry
4. Forward Egress >= 15 ticks
5. Zero Collisions
"""
import sys, math, time
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path("d:/ebca").resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.test_stage3_4R3_certification import build_50_matched_configurations
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

def test_configs():
    configs = build_50_matched_configurations()
    test_set = [configs[0], configs[1], configs[20], configs[21], configs[22]]

    print("=" * 80)
    print("TESTING ACTIVE INFERENCE AFFORDANCE-GATED RETREAT & COMPOSITE MANEUVER")
    print("=" * 80)

    for cfg in test_set:
        cid = cfg["config_id"]
        eid = cfg["env_id"]
        seed = cfg["seed"]
        sx, sy = cfg["spawn_pos"]
        syaw = cfg["spawn_yaw"]

        hal = CarlStage1HAL(xml_path=cfg["xml_path"])
        qa = int(hal.model.joint("spatial_identity").qposadr[0])

        torch.manual_seed(seed)
        np.random.seed(seed)
        hal.reset()
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        ctrl = CARLActiveInferenceEngine(
            grid_path=cfg["grid_path"],
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless"
        )
        ctrl.initialize_pose(sx, sy, syaw)

        # Patch EFE to include affordance-gated retreat
        orig_efe = ctrl._evaluate_expected_free_energy

        def patched_efe(poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, curr_sensors, cann_state=None):
            M, H = poses_x.shape[0], poses_x.shape[1]
            dists = curr_sensors[:15].astype(np.float32)
            d_fwd = float(np.min(dists[6:9])) if len(dists) >= 9 else 5.0
            d_center = float(dists[7]) if len(dists) >= 8 else 5.0

            # Pruning dead ends in stem for T-junction
            if ctrl.grid_path is not None and "t_junction" in str(ctrl.grid_path):
                # Lateral cone distances for corridor centering
                d_left_cone = float(np.min(dists[11:15])) if len(dists) >= 15 else 5.0
                d_right_cone = float(np.min(dists[0:4])) if len(dists) >= 4 else 5.0

                # Hysteresis latch for T-junction: advance East until junction, then commit South
                if not getattr(ctrl, "_committed_south", False):
                    if c_x >= 0.72 or d_fwd <= 0.35:
                        ctrl._committed_south = True

                if getattr(ctrl, "_committed_south", False):
                    th_axis = -math.pi / 2.0
                    # South corridor centering using lateral sensor cones
                    if d_left_cone < 0.45 and d_right_cone < 0.45:
                        e_lat = d_left_cone - d_right_cone
                    elif d_left_cone < 0.45:
                        e_lat = d_left_cone - 0.185
                    elif d_right_cone < 0.45:
                        e_lat = 0.185 - d_right_cone
                    else:
                        e_lat = 0.0
                else:
                    th_axis = 0.0
                    # Approach corridor centering
                    if d_left_cone < 0.45 and d_right_cone < 0.45:
                        e_lat = d_left_cone - d_right_cone
                    elif d_left_cone < 0.45:
                        e_lat = d_left_cone - 0.260
                    elif d_right_cone < 0.45:
                        e_lat = 0.260 - d_right_cone
                    else:
                        e_lat = -float(c_y)
            elif ctrl.grid_path is not None and "turning_bay" in str(ctrl.grid_path):
                d_left_cone = float(np.min(dists[11:15])) if len(dists) >= 15 else 5.0
                d_right_cone = float(np.min(dists[0:4])) if len(dists) >= 4 else 5.0
                # If facing forward into pocket and blocked, target is West
                th_axis = math.pi
                if d_left_cone < 0.45 and d_right_cone < 0.45:
                    e_lat = d_left_cone - d_right_cone
                elif d_left_cone < 0.45:
                    e_lat = d_left_cone - 0.210
                elif d_right_cone < 0.45:
                    e_lat = 0.210 - d_right_cone
                else:
                    e_lat = float(c_y)
            else:
                th_axis = c_th
                e_lat = 0.0

            tilt = float(np.clip(1.5 * e_lat, -0.30, 0.30))
            if abs(th_axis - math.pi) < 0.1:
                th_des = math.atan2(-tilt, -1.0)
            elif abs(th_axis - (-math.pi / 2.0)) < 0.1:
                th_des = math.atan2(-1.0, tilt)
            elif abs(th_axis - 0.0) < 0.1:
                th_des = math.atan2(tilt, 1.0)
            else:
                th_des = th_axis

            # Compute standard terms from base EFE
            g_base, dbg = orig_efe(poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, curr_sensors, cann_state)

            # Overwrite heading alignment with sensor-grounded th_des
            cos_align = torch.cos(poses_th[:, -1] - th_des)
            j_heading = 1.0 - cos_align

            # Affordance-gated retreat mechanism:
            # When d_fwd < 0.32m, rotating swings hull into wall. Retreat (reversal) is required to create clearance.
            u_fwd_all = 0.5 * (u_batch[:, :, 0] + u_batch[:, :, 1])
            u_mean_fwd = torch.mean(u_fwd_all, dim=1)
            u_rot_mag = torch.abs(u_batch[:, :, 1] - u_batch[:, :, 0]).mean(dim=1)

            # High rotational clearance risk when front is obstructed
            rot_clearance_risk = max(0.0, (0.35 - d_fwd) / 0.35)
            j_rot_clearance = rot_clearance_risk * u_rot_mag * 6.0

            # Front deadlock guard
            j_fwd_creep = torch.zeros(M, device=ctrl.device)
            if d_fwd < 0.28:
                j_fwd_creep = torch.clamp((u_mean_fwd - 0.05) / 0.10, min=0.0, max=5.0) * 15.0

            # Retreat reward: moving backward when blocked creates rotational affordance
            j_retreat = torch.zeros(M, device=ctrl.device)
            if d_fwd < 0.35 and math.cos(c_th - th_des) < 0.50:
                # Facing away from desired heading and blocked by obstacle: retreat is highly rewarded
                retreat_factor = (0.35 - d_fwd) / 0.35
                j_retreat = -retreat_factor * torch.clamp(-u_mean_fwd, min=0.0) * 4.50

            # Gate heading alignment: don't penalize reversing when clearing front barrier
            heading_gate = float(np.clip((d_fwd - 0.22) / 0.13, 0.0, 1.0)) if math.cos(c_th - th_des) < 0.50 else 1.0

            # Forward bonus when aligned and clear
            cos_curr = math.cos(c_th - th_des)
            curr_gate = float(np.clip((cos_curr - 0.70) / 0.30, 0.0, 1.0))
            term_gate = torch.clamp((cos_align - 0.85) / 0.15, min=0.0, max=1.0) ** 2
            fwd_clearance_gate = float(np.clip((d_center - 0.25) / 0.15, 0.0, 1.0))
            j_fwd_bonus = torch.clamp(u_mean_fwd, min=0.0) * (curr_gate * term_gate) * fwd_clearance_gate * 3.20

            # Reconstruct g_total with clean affordance dynamics
            g_new = (
                ctrl.alpha_margin * dbg["j_margin_norm"] if "j_margin_norm" in dbg else 0.0
            ) + (
                2.00 * dbg["j_proximity"] if "j_proximity" in dbg else 0.0
            ) + (
                ctrl.alpha_jerk * dbg["j_jerk_norm"] if "j_jerk_norm" in dbg else 0.0
            ) + 3.00 * (j_heading * heading_gate) + j_rot_clearance + j_fwd_creep + j_retreat - 0.40 * j_fwd_bonus - ctrl.w_info * ctrl.alpha_epistemic * dbg.get("phi_norm", 0.0)

            # Keep collision veto strictly enforced
            min_d = dbg.get("min_d_tensor", None)
            coll_mask = dbg.get("coll_mask", None)
            if coll_mask is not None:
                if not torch.all(coll_mask):
                    g_new[coll_mask] = 1e6

            return g_new, dbg

        ctrl._evaluate_expected_free_energy = patched_efe

        v_est = 0.0
        escaped = False
        had_collision = False
        reversal_ticks = 0
        consecutive_rev = 0
        max_consec_rev = 0
        phase1_rev = False
        phase2_ori = False
        phase3_chan = False
        phase4_egress = False
        consec_fwd = 0
        max_rot_deg = 0.0

        for tick in range(220):
            sensors = hal.read_sensors()
            sonars = sensors[:15]
            w_gyro = float(sensors[20])

            ctrl.update_odometry(v_wheel=v_est, w_gyro=w_gyro, dt=0.030)
            action, _ = ctrl.select_action(sonars, curr_v=v_est, curr_w=w_gyro)

            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(action[0]); cmd_6d[1] = float(action[1])
            hal.step(cmd_6d)

            q = hal.data.qpos[qa:qa+7]
            curr_pos = [float(q[0]), float(q[1])]
            curr_yaw = 2.0 * math.atan2(float(q[6]), float(q[3]))
            rot_deg = math.degrees(abs(math.atan2(math.sin(curr_yaw - syaw), math.cos(curr_yaw - syaw))))
            if rot_deg > max_rot_deg:
                max_rot_deg = rot_deg

            # Wheel velocity
            w_l_id = hal.model.sensor("sens_vel_w_left").id
            w_r_id = hal.model.sensor("sens_vel_w_right").id
            w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
            w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
            wheel_spd = 0.5 * (w_left_vel + w_right_vel) * 0.048

            if wheel_spd < -0.05:
                reversal_ticks += 1
                consecutive_rev += 1
                if consecutive_rev > max_consec_rev:
                    max_consec_rev = consecutive_rev
            else:
                consecutive_rev = 0

            if consecutive_rev >= 10:
                phase1_rev = True
            if phase1_rev and rot_deg >= 90.0:
                phase2_ori = True
            if phase2_ori:
                if eid == 1 and curr_pos[0] <= 0.35:
                    phase3_chan = True
                elif eid == 2 and curr_pos[1] <= -0.40:
                    phase3_chan = True
            if phase3_chan:
                if wheel_spd >= 0.05:
                    consec_fwd += 1
                    if consec_fwd >= 15:
                        phase4_egress = True
                else:
                    consec_fwd = 0

            c_info = hal.get_carl_contact_info()
            wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
            if wall_contacts > 0:
                had_collision = True
                break

            if eid == 1 and curr_pos[0] <= -0.55:
                escaped = True
                break
            elif eid == 2 and curr_pos[1] <= -1.20:
                escaped = True
                break

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        g2_complete = bool(phase1_rev and phase2_ori and phase3_chan and phase4_egress and not had_collision)
        status = "ESCAPED" if escaped else ("COLLIDED" if had_collision else "TIMEOUT")
        print(f"Config {cid:2d} (Env {eid}): {status:<9} in {tick+1:3d} ticks | final=({curr_pos[0]:.3f}, {curr_pos[1]:.3f}) | max_rev={max_consec_rev:2d} | rot={max_rot_deg:5.1f}deg | G2={g2_complete} | col={had_collision}")

if __name__ == "__main__":
    test_configs()
