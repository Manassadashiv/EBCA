import sys
import math
import numpy as np
import torch
import mujoco
from pathlib import Path
from scipy.ndimage import label, binary_dilation

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg_map = {c["config_id"]: c for c in configs}

class CertifiedEngine(CARLActiveInferenceEngine):
    def _sample_trajectories(self):
        M, H = self.M, self.horizon
        u_candidates = self.fixed_candidate_template.clone()

        self.nominal_u[:-1] = self.nominal_u[1:].clone()
        self.nominal_u[-1] = self.nominal_u[-2].clone()

        # Partition 1: Forward Geodesic Tracking (M1 = 48)
        fwd_base = self.nominal_u if self._reverse_done and not self._pivot_done else torch.clamp(self.nominal_u, min=0.0, max=1.0)
        fwd_noise = torch.randn(48, H, 2, device=self.device) * 0.05
        u_candidates[:48] = torch.clamp(fwd_base.unsqueeze(0) + fwd_noise, -1.0, 1.0)
        u_candidates[0] = self.nominal_u
        u_candidates[1, :, :] = 1.00
        u_candidates[2, :, :] = 0.85
        # Differential steering candidates (curving rather than in-place spinning)
        u_candidates[3, :, 0] = 1.00; u_candidates[3, :, 1] = 0.70
        u_candidates[4, :, 0] = 0.70; u_candidates[4, :, 1] = 1.00
        u_candidates[5, :, 0] = 0.90; u_candidates[5, :, 1] = 0.75
        u_candidates[6, :, 0] = 0.75; u_candidates[6, :, 1] = 0.90
        u_candidates[7, :, 0] = 0.80; u_candidates[7, :, 1] = 0.60
        u_candidates[8, :, 0] = 0.60; u_candidates[8, :, 1] = 0.80
        # Gentle forward creep
        u_candidates[9, :, :] = 0.40
        u_candidates[10, :, :] = 0.30

        # Partition 4: Controlled Gentle Reversal (M4 = 24, indices 96..119)
        rev_v = torch.clamp(-0.32 + torch.randn(24, H, device=self.device) * 0.03, -0.40, -0.25)
        u_candidates[96:120, :, 0] = rev_v
        u_candidates[96:120, :, 1] = rev_v
        u_candidates[96, :, :] = -0.30
        u_candidates[97, :, :] = -0.33
        u_candidates[98, :, :] = -0.35

        # Partition 5: Braking & Rotation
        u_candidates[120, :, :] = 0.0
        u_candidates[121, :, 0] = -0.15; u_candidates[121, :, 1] = 0.15
        u_candidates[122, :, 0] = -0.22; u_candidates[122, :, 1] = 0.22
        u_candidates[123, :, 0] = -0.30; u_candidates[123, :, 1] = 0.30
        u_candidates[124, :, 0] = 0.15; u_candidates[124, :, 1] = -0.15
        u_candidates[125, :, 0] = 0.22; u_candidates[125, :, 1] = -0.22
        u_candidates[126, :, 0] = 0.30; u_candidates[126, :, 1] = -0.30
        u_candidates[127, :, :] = 0.0

        return u_candidates

    def _evaluate_expected_free_energy(
        self, poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, curr_sensors, cann_state
    ):
        with torch.inference_mode():
            M, H = poses_x.shape
            
            sub_x = poses_x[:, self.chk_idx]
            sub_y = poses_y[:, self.chk_idx]
            sub_th = poses_th[:, self.chk_idx]

            cos_th = torch.cos(sub_th).unsqueeze(-1)
            sin_th = torch.sin(sub_th).unsqueeze(-1)
            rot_dx = self.hull_body_x * cos_th - self.hull_body_y * sin_th
            rot_dy = self.hull_body_x * sin_th + self.hull_body_y * cos_th

            cat_qx = (sub_x.unsqueeze(-1) + rot_dx).view(M, -1)
            cat_qy = (sub_y.unsqueeze(-1) + rot_dy).view(M, -1)
            norm_x = (cat_qx / self.half_size).clamp(-1.0, 1.0)
            norm_y = (cat_qy / self.half_size).clamp(-1.0, 1.0)
            grid_coords = torch.stack([norm_x, norm_y], dim=-1).unsqueeze(1)

            grid_b_ch0 = self.grid[:, 0:1, :, :].expand(M, 1, self.grid_size, self.grid_size)
            sampled_occ = torch.nn.functional.grid_sample(
                grid_b_ch0, grid_coords, mode="bilinear", padding_mode="zeros", align_corners=True
            ).squeeze(1).squeeze(1)
            max_occ_hits = torch.max(sampled_occ, dim=-1).values

            dists = curr_sensors[:15].astype(np.float32)
            valid = dists < 1.20
            min_d = torch.full((M,), 5.0, device=self.device)
            if np.any(valid):
                sonar_r = dists[valid] + 0.14
                ray_angles = c_th + self.sonar_angles_rad[valid]
                obs_x = torch.from_numpy(c_x + sonar_r * np.cos(ray_angles)).float().to(self.device)
                obs_y = torch.from_numpy(c_y + sonar_r * np.sin(ray_angles)).float().to(self.device)
                cand_x = sub_x.unsqueeze(-1) + rot_dx
                cand_y = sub_y.unsqueeze(-1) + rot_dy
                dx = cand_x.unsqueeze(-1) - obs_x.view(1, 1, 1, -1)
                dy = cand_y.unsqueeze(-1) - obs_y.view(1, 1, 1, -1)
                d_sq = dx**2 + dy**2
                min_d = torch.sqrt(torch.min(d_sq.view(M, -1), dim=-1).values)

            collision_mask = (max_occ_hits > 0.25) | (min_d < 0.055)
            margin_deficit = torch.clamp((max_occ_hits - 0.15) / 0.50, min=0.0, max=1.0)
            j_margin_norm = margin_deficit ** 2
            
            # Smooth proximity buffer (18cm)
            proximity = torch.clamp((0.18 - min_d) / 0.18, min=0.0, max=1.0)
            j_proximity = proximity ** 1.5

            delta_u = u_batch[:, 1:, :] - u_batch[:, :-1, :]
            j_jerk_norm = torch.clamp(torch.sum(delta_u ** 2, dim=(1, 2)) / 56.0, min=0.0, max=1.0)

            phi_norm = torch.zeros(M, device=self.device)
            macro_res = self._compute_macro_frontier(c_x, c_y)
            if macro_res is not None:
                f_star_x, f_star_y, current_geo_dist, dist_field = macro_res
                term_norm_x = (poses_x[:, -1] / self.half_size).clamp(-1.0, 1.0)
                term_norm_y = (poses_y[:, -1] / self.half_size).clamp(-1.0, 1.0)
                coords = torch.stack([term_norm_x, term_norm_y], dim=-1).unsqueeze(0).unsqueeze(2)
                finite_dist_field = np.nan_to_num(dist_field, nan=6.0, posinf=6.0)
                dist_tensor = torch.from_numpy(finite_dist_field).unsqueeze(0).unsqueeze(0)
                term_dists = torch.nn.functional.grid_sample(
                    dist_tensor, coords, mode="bilinear", padding_mode="border", align_corners=True
                ).squeeze()
                delta_d_geo = current_geo_dist - term_dists
                phi_norm = torch.clamp(delta_d_geo / 0.35, min=-1.0, max=1.0)

            d_fwd = float(np.min(dists[6:9])) if len(dists) >= 9 else 5.0
            d_center = float(dists[7]) if len(dists) >= 8 else 5.0

            # Heading determination
            th_des = c_th
            if macro_res is not None:
                geo_valid = False
                rc_ix = int(np.clip((c_x + self.half_size) / self.resolution, 0, self.grid_size - 1))
                rc_iy = int(np.clip((c_y + self.half_size) / self.resolution, 0, self.grid_size - 1))
                if 2 <= rc_ix < self.grid_size - 2 and 2 <= rc_iy < self.grid_size - 2:
                    d_e = dist_field[rc_iy, rc_ix + 1]
                    d_w = dist_field[rc_iy, rc_ix - 1]
                    d_n = dist_field[rc_iy + 1, rc_ix]
                    d_s = dist_field[rc_iy - 1, rc_ix]
                    if not (np.isinf(d_e) or np.isinf(d_w) or np.isinf(d_n) or np.isinf(d_s)):
                        grad_x = (d_e - d_w) / (2.0 * self.resolution)
                        grad_y = (d_n - d_s) / (2.0 * self.resolution)
                        grad_mag = math.sqrt(grad_x**2 + grad_y**2)
                        if grad_mag > 0.3:
                            th_des = math.atan2(-grad_y, -grad_x)
                            geo_valid = True
                if not geo_valid:
                    th_des = math.atan2(f_star_y - c_y, f_star_x - c_x)

            # Bilateral lateral centering: push away from walls within 25cm
            d_l_side = float(curr_sensors[12]) if len(curr_sensors) >= 15 else 5.0
            d_r_side = float(curr_sensors[2]) if len(curr_sensors) >= 15 else 5.0
            if (d_l_side < 0.65 and d_r_side < 0.65 and (0.35 <= d_l_side + d_r_side <= 0.90)):
                tilt = float(np.clip(1.2 * (d_l_side - d_r_side), -0.22, 0.22))
                th_des = th_des + tilt
            elif d_l_side < 0.25:
                th_des = th_des - float(np.clip(1.5 * (0.25 - d_l_side), 0.0, 0.25))
            elif d_r_side < 0.25:
                th_des = th_des + float(np.clip(1.5 * (0.25 - d_r_side), 0.0, 0.25))

            cos_term = torch.cos(poses_th[:, -1] - th_des)
            cos_mean = torch.mean(torch.cos(poses_th - th_des), dim=1)
            cos_align = 0.40 * cos_term + 0.60 * cos_mean
            j_heading = 1.0 - cos_align

            delta_th = math.atan2(math.sin(th_des - c_th), math.cos(th_des - c_th))
            u_diff = u_batch[:, :, 1] - u_batch[:, :, 0]
            mean_u_diff = torch.mean(u_diff, dim=1)
            j_wrong_turn = torch.clamp(-mean_u_diff * math.sin(delta_th), min=0.0) * 8.0

            # Inhibit pure in-place pivots when roughly aligned in corridors
            cos_curr = math.cos(c_th - th_des)
            is_corridor = (d_l_side < 0.60 or d_r_side < 0.60)
            is_aligned = (cos_curr > 0.70)
            u_fwd_all = 0.5 * (u_batch[:, :, 0] + u_batch[:, :, 1])
            u_mean_fwd = torch.mean(u_fwd_all, dim=1)
            is_pivot_cand = (u_batch[:, :, 0] * u_batch[:, :, 1] < -0.05).any(dim=1)
            
            j_corridor_spin = torch.zeros(M, device=self.device)
            if is_corridor and is_aligned and self._reverse_done:
                j_corridor_spin = is_pivot_cand.float() * 30.0

            # Forward Acceleration: Smooth gate requiring alignment
            curr_gate = float(np.clip((cos_curr - 0.50) / 0.50, 0.0, 1.0))
            term_gate = torch.clamp((cos_align - 0.50) / 0.50, min=0.0, max=1.0)
            align_gate = curr_gate * term_gate

            fwd_clearance_gate = float(np.clip((d_center - 0.18) / 0.18, 0.0, 1.0))
            j_fwd_bonus = torch.clamp(u_mean_fwd, min=0.0) * align_gate * fwd_clearance_gate * 10.00

            # Reversal affordance: Only triggered on initial dead-end encounter, never inside exit corridor
            j_retreat = torch.zeros(M, device=self.device)
            non_rev_penalty = torch.zeros(M, device=self.device)
            at_dead_end = (d_center < 0.38 and d_fwd < 0.35 and not self._reverse_done)

            if at_dead_end:
                self._reverse_latched = True

            if not self._reverse_done and (self._reverse_latched or self._reverse_ticks > 0):
                j_retreat = - torch.clamp(-u_mean_fwd, min=0.0) * 45.00
                non_rev_penalty = torch.clamp(u_mean_fwd + 0.15, min=0.0) * 150.0
                j_heading = j_heading * 0.001

            u_rot_mag = torch.abs(u_batch[:, :, 1] - u_batch[:, :, 0]).mean(dim=1)
            rot_clearance_risk = max(0.0, (0.28 - d_fwd) / 0.28)
            j_rot_clearance = rot_clearance_risk * u_rot_mag * 3.0

            g_pragmatic = (
                self.alpha_margin * j_margin_norm +
                22.00 * j_proximity +
                self.alpha_jerk * j_jerk_norm +
                8.00 * j_heading +
                j_wrong_turn +
                j_rot_clearance +
                j_retreat +
                non_rev_penalty +
                j_corridor_spin -
                3.50 * j_fwd_bonus
            )
            g_epistemic = - self.w_info * self.alpha_epistemic * phi_norm * float(np.clip(cos_curr, 0.0, 1.0))
            g_total = g_pragmatic + g_epistemic

            if not torch.all(collision_mask):
                g_total[collision_mask] = 1e6
            else:
                g_total += (0.050 - min_d) * 1e4

            debug_info = {
                "mean_pragmatic": float(g_pragmatic.mean().item()),
                "mean_epistemic": float(g_epistemic.mean().item()),
                "accepted_candidates": int((~collision_mask).sum().item()),
                "rejected_candidates": int(collision_mask.sum().item()),
                "min_sonar_d": float(min_d.min().item()),
                "heading_at_min_clearance": float(poses_th[0, -1].item()),
                "rejection_reason": "none",
            }
            return g_total, debug_info

if __name__ == "__main__":
    print("=== SCREENING WITH CERTIFIED ENGINE ===", flush=True)
    results = []
    for cfg_id in [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]:
        cfg = cfg_map[cfg_id]
        env_id = cfg["env_id"]
        xml_path = cfg["xml_path"]
        grid_path = cfg["grid_path"]
        sx, sy = cfg["spawn_pos"]
        syaw = cfg["spawn_yaw"]
        seed = cfg["seed"]

        np.random.seed(seed); torch.manual_seed(seed)
        hal = CarlStage1HAL(xml_path=xml_path)
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        ctrl = CertifiedEngine(grid_path=grid_path, w_info=1.0)
        ctrl.initialize_pose(sx, sy, syaw)

        had_collision, escaped = False, False
        v_est = 0.0
        for tick in range(220):
            sensors = hal.read_sensors()
            ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=ctrl.dt)
            u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=float(sensors[20]))
            cmd_6d = np.zeros(6)
            cmd_6d[0], cmd_6d[1] = float(u_star[0]), float(u_star[1])
            hal.step(cmd_6d)
            qa = int(hal.model.joint("spatial_identity").qposadr[0])
            new_x, new_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
            u_fwd = float(0.5*(cmd_6d[0]+cmd_6d[1]))
            v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
            c_info = hal.get_carl_contact_info()
            if c_info["carl_contacts"] - c_info["floor_contacts"] > 0:
                had_collision = True; break
            
            if env_id == 1 and new_x <= -0.55:
                escaped = True; break
            elif env_id == 2 and new_y <= -1.20:
                escaped = True; break

        outcome = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")
        print(f"Config {cfg_id:2d} (Env{env_id}): {outcome:<10} ticks={tick+1:3d} final_x={new_x:.3f} final_y={new_y:.3f}", flush=True)
        results.append({"cfg_id": cfg_id, "env_id": env_id, "outcome": outcome})

    print("\n=== SUMMARY ===", flush=True)
    e1 = [r for r in results if r["env_id"] == 1]
    e2 = [r for r in results if r["env_id"] == 2]
    esc1 = sum(1 for r in e1 if r["outcome"] == "ESCAPE")
    col1 = sum(1 for r in e1 if r["outcome"] == "COLLISION")
    esc2 = sum(1 for r in e2 if r["outcome"] == "ESCAPE")
    col2 = sum(1 for r in e2 if r["outcome"] == "COLLISION")
    print(f"Env1 Escapes: {esc1}/5, Collisions: {col1}/5", flush=True)
    print(f"Env2 Escapes: {esc2}/5, Collisions: {col2}/5", flush=True)
