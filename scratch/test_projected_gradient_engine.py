import sys, math, numpy as np, torch, mujoco
from pathlib import Path

repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg_map = {c['config_id']: c for c in configs}

class ProjectedGradientEngine(CARLActiveInferenceEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temperature = 0.015

    def _sample_trajectories(self):
        torch.manual_seed(42)
        M, H = self.M, self.horizon
        u_candidates = self.fixed_candidate_template.clone()

        self.nominal_u[:-1] = self.nominal_u[1:].clone()
        self.nominal_u[-1] = self.nominal_u[-2].clone()

        # Partition 1: Forward Geodesic Tracking (M1 = 48)
        fwd_base = self.nominal_u if self._reverse_done and not self._pivot_done else torch.clamp(self.nominal_u, min=0.0, max=1.0)
        fwd_noise = torch.randn(48, H, 2, device=self.device) * 0.03
        u_candidates[:48] = torch.clamp(fwd_base.unsqueeze(0) + fwd_noise, -1.0, 1.0)
        
        # Core forward speeds
        u_candidates[0] = self.nominal_u
        u_candidates[1, :, :] = 1.00
        u_candidates[2, :, :] = 0.95
        u_candidates[3, :, :] = 0.90
        u_candidates[4, :, :] = 0.85
        u_candidates[5, :, :] = 0.75

        # Steering Pulse Candidates: nudge heading for 2-4 ticks, then cruise straight
        idx = 6
        for dur in [2, 4]:
            for diff in [0.06, 0.12, 0.18]:
                if idx < 42:
                    # Turn right, then straight
                    u_candidates[idx, :, :] = 0.92
                    u_candidates[idx, :dur, 0] = 0.92 + diff / 2
                    u_candidates[idx, :dur, 1] = 0.92 - diff / 2
                    idx += 1
                    # Turn left, then straight
                    u_candidates[idx, :, :] = 0.92
                    u_candidates[idx, :dur, 0] = 0.92 - diff / 2
                    u_candidates[idx, :dur, 1] = 0.92 + diff / 2
                    idx += 1

        # Gentle forward creeps
        u_candidates[42, :, :] = 0.60
        u_candidates[43, :, :] = 0.45
        u_candidates[44, :, :] = 0.35
        u_candidates[45, :, 0] = 0.60; u_candidates[45, :, 1] = 0.50
        u_candidates[46, :, 0] = 0.50; u_candidates[46, :, 1] = 0.60
        u_candidates[47, :, 0] = 0.40; u_candidates[47, :, 1] = 0.50

        # Partition 4: Controlled Reversal (M4 = 24, indices 96..119)
        rev_v = torch.clamp(-0.45 + torch.randn(24, H, device=self.device) * 0.04, -0.60, -0.35)
        u_candidates[96:120, :, 0] = rev_v
        u_candidates[96:120, :, 1] = rev_v
        u_candidates[96, :, :] = -0.40
        u_candidates[97, :, :] = -0.45
        u_candidates[98, :, :] = -0.50

        # Partition 5: Braking & Slow Rotation
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
            
            proximity = torch.clamp((0.15 - min_d) / 0.15, min=0.0, max=1.0)
            j_proximity = proximity ** 2

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
            d_l_side = float(curr_sensors[12]) if len(curr_sensors) >= 15 else 5.0
            d_r_side = float(curr_sensors[2]) if len(curr_sensors) >= 15 else 5.0

            # Desired heading determination: Topologically Constrained Gradient Projection
            th_des = c_th
            if macro_res is not None:
                rc_ix = int(np.clip((c_x + self.half_size) / self.resolution, 0, self.grid_size - 1))
                rc_iy = int(np.clip((c_y + self.half_size) / self.resolution, 0, self.grid_size - 1))
                
                # Measure free span along X and Y from internal occupancy memory (current cell + 2 cells ahead)
                def get_spans(iy, ix):
                    iy = int(np.clip(iy, 0, self.grid_size - 1))
                    ix = int(np.clip(ix, 0, self.grid_size - 1))
                    dw = 0
                    while ix - dw > 0 and self.grid_np[0, iy, ix - dw] < 0.50 and dw < 15:
                        dw += 1
                    de = 0
                    while ix + de < self.grid_size - 1 and self.grid_np[0, iy, ix + de] < 0.50 and de < 15:
                        de += 1
                    ds = 0
                    while iy - ds > 0 and self.grid_np[0, iy - ds, ix] < 0.50 and ds < 15:
                        ds += 1
                    dn = 0
                    while iy + dn < self.grid_size - 1 and self.grid_np[0, iy + dn, ix] < 0.50 and dn < 15:
                        dn += 1
                    return (dw + de) * self.resolution, (ds + dn) * self.resolution, dw, de, ds, dn

                span_x_curr, span_y_curr, dw_cells, de_cells, ds_cells, dn_cells = get_spans(rc_iy, rc_ix)
                span_x_south, _, dw_s, de_s, _, _ = get_spans(rc_iy - 3, rc_ix)
                _, span_y_west, _, _, ds_w, dn_w = get_spans(rc_iy, rc_ix - 3)

                min_span_x = min(span_x_curr, span_x_south)
                min_span_y = min(span_y_curr, span_y_west)

                if 2 <= rc_ix < self.grid_size - 2 and 2 <= rc_iy < self.grid_size - 2:
                    d_e = dist_field[rc_iy, rc_ix + 1]
                    d_w = dist_field[rc_iy, rc_ix - 1]
                    d_n = dist_field[rc_iy + 1, rc_ix]
                    d_s = dist_field[rc_iy - 1, rc_ix]
                    if not (np.isinf(d_e) or np.isinf(d_w) or np.isinf(d_n) or np.isinf(d_s)):
                        grad_x = (d_e - d_w) / (2.0 * self.resolution)
                        grad_y = (d_n - d_s) / (2.0 * self.resolution)

                        # Lookahead corridor constraint projection:
                        in_ns = (min_span_x < 0.85 and span_y_curr > 1.0 * min_span_x and self._reverse_done)
                        in_ew = (min_span_y < 0.85 and span_x_curr > 1.0 * min_span_y and self._reverse_done)

                        if in_ns:
                            # Constrained to North-South travel -> project out grad_x!
                            grad_x = 0.0
                            th_raw = math.atan2(-grad_y, -grad_x)
                            # Use corridor aperture walls for centerline error
                            use_de = de_cells if span_x_curr < 0.85 else de_s
                            use_dw = dw_cells if span_x_curr < 0.85 else dw_s
                            ex = 0.5 * (use_de - use_dw) * self.resolution
                            tilt = float(np.clip(1.0 * ex, -0.12, 0.12))
                            th_des = th_raw + (tilt if th_raw < 0 else -tilt)
                        elif in_ew:
                            # Constrained to East-West travel -> project out grad_y!
                            grad_y = 0.0
                            th_raw = math.atan2(-grad_y, -grad_x)
                            use_dn = dn_cells if span_y_curr < 0.85 else dn_w
                            use_ds = ds_cells if span_y_curr < 0.85 else ds_w
                            ey = 0.5 * (use_dn - use_ds) * self.resolution
                            tilt = float(np.clip(1.0 * ey, -0.12, 0.12))
                            th_des = math.pi - tilt if abs(th_raw) > 1.5 else tilt
                        else:
                            # Open space: full 2D gradient
                            grad_mag = math.sqrt(grad_x**2 + grad_y**2)
                            if grad_mag > 0.3:
                                th_des = math.atan2(-grad_y, -grad_x)
                            else:
                                th_des = math.atan2(f_star_y - c_y, f_star_x - c_x)

            cos_term = torch.cos(poses_th[:, -1] - th_des)
            cos_mean = torch.mean(torch.cos(poses_th - th_des), dim=1)
            cos_align = 0.40 * cos_term + 0.60 * cos_mean
            j_heading = 1.0 - cos_align

            delta_th = math.atan2(math.sin(th_des - c_th), math.cos(th_des - c_th))
            u_diff = u_batch[:, :, 1] - u_batch[:, :, 0]
            mean_u_diff = torch.mean(u_diff, dim=1)
            j_wrong_turn = torch.clamp(-mean_u_diff * math.sin(delta_th), min=0.0) * 8.0

            # Forward Acceleration: Balanced gate
            cos_curr = math.cos(c_th - th_des)
            curr_gate = float(np.clip((cos_curr - 0.20) / 0.80, 0.0, 1.0))
            term_gate = torch.clamp((cos_align - 0.20) / 0.80, min=0.0, max=1.0)
            align_gate = curr_gate * term_gate

            u_fwd_all = 0.5 * (u_batch[:, :, 0] + u_batch[:, :, 1])
            u_mean_fwd = torch.mean(u_fwd_all, dim=1)
            fwd_clearance_gate = float(np.clip((d_center - 0.15) / 0.15, 0.0, 1.0))
            j_fwd_bonus = torch.clamp(u_mean_fwd, min=0.0) * align_gate * fwd_clearance_gate * 9.00

            # Reversal affordance: Single reversal lock
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
                35.00 * j_proximity +
                self.alpha_jerk * j_jerk_norm +
                10.00 * j_heading +
                j_wrong_turn +
                j_rot_clearance +
                j_retreat +
                non_rev_penalty -
                4.00 * j_fwd_bonus
            )
            g_epistemic = - self.w_info * self.alpha_epistemic * phi_norm
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

print("=== SCREENING PROJECTED GRADIENT ENGINE ===", flush=True)
results = []
for cid in [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]:
    cfg = cfg_map[cid]
    hal = CarlStage1HAL(xml_path=cfg['xml_path'])
    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
    mujoco.mj_forward(hal.model, hal.data)
    ctrl = ProjectedGradientEngine(grid_path=cfg['grid_path'], w_info=1.0)
    ctrl.initialize_pose(sx, sy, syaw)
    v_est = 0.0
    coll, esc = False, False
    for tick in range(220):
        sens = hal.read_sensors()
        ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
        u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
        cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
        hal.step(cmd)
        qa = int(hal.model.joint('spatial_identity').qposadr[0])
        nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = 0.5*(u[0]+u[1])
        v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
        c_info = hal.get_carl_contact_info()
        if c_info['carl_contacts'] - c_info['floor_contacts'] > 0:
            coll = True; break
        if cfg['env_id'] == 1 and nx <= -0.55: esc = True; break
        elif cfg['env_id'] == 2 and ny <= -1.20: esc = True; break
    out = 'ESCAPE' if esc else ('COLLISION' if coll else 'TIMEOUT')
    print(f"Config {cid:2d} (Env {cfg['env_id']}): {out:<10} at tick {tick+1:3d}, x={nx:.3f}, y={ny:.3f}", flush=True)
    results.append({'cid': cid, 'env_id': cfg['env_id'], 'out': out})

e1 = [r for r in results if r['env_id'] == 1]
e2 = [r for r in results if r['env_id'] == 2]
print(f"\nEnv 1: Escapes={sum(1 for r in e1 if r['out'] == 'ESCAPE')}/5, Collisions={sum(1 for r in e1 if r['out'] == 'COLLISION')}/5", flush=True)
print(f"Env 2: Escapes={sum(1 for r in e2 if r['out'] == 'ESCAPE')}/5, Collisions={sum(1 for r in e2 if r['out'] == 'COLLISION')}/5", flush=True)
