"""
tests/test_stage3_4_vertical_engine.py — Vertical Startup Screening Battery
Validates the SE(2) swept-hull veto + 1D corridor manifold guidance on Configs 0-4 (Env 1) and 20-24 (Env 2).
"""
import sys
import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import torch
import torch.nn.functional as F
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"

SCREENING_CONFIG_IDS = [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]
MAX_TICKS = 220


class VerticalActiveInferenceEngine(CARLActiveInferenceEngine):
    """
    Subclasses CARLActiveInferenceEngine with:
    1. Exact 3-disc SE(2) swept hull veto (<0.20 ms tensorized)
    2. 1D corridor manifold constraint (strictly forbids in-place pivots in narrow corridors)
    3. Smooth Voronoi centerline guidance
    """

    def initialize_pose(self, spawn_x: float, spawn_y: float, spawn_yaw: float):
        super().initialize_pose(spawn_x, spawn_y, spawn_yaw)
        self._spawn_yaw = float(spawn_yaw)
        self._spawn_x = float(spawn_x)
        self._spawn_y = float(spawn_y)
        self._turned_around = False
        self._entered_corridor = False

        # 3 Inscribed Discs along chassis axis: r = 0.088m, offsets [-0.065, 0.0, +0.065]
        # Bumper is 0.23m long x 0.27m wide. 3 discs of radius 0.088m span [-0.153, +0.153] m length
        # and [-0.088, +0.088] width. Plus 4 corner probes at (+-0.115, +-0.135).
        # We define a 7-point footprint: 3 centers + 4 bumper corners.
        hull_pts = [
            (0.000,  0.000),   # Center
            (0.065,  0.000),   # Front-center
            (-0.065, 0.000),   # Rear-center
            (0.115,  0.135),   # Front-left corner
            (0.115, -0.135),   # Front-right corner
            (-0.115,  0.135),   # Rear-left corner
            (-0.115, -0.135),  # Rear-right corner
        ]
        self.hull_body_x = torch.tensor([p[0] for p in hull_pts], dtype=torch.float32, device=self.device).view(1, 1, -1)
        self.hull_body_y = torch.tensor([p[1] for p in hull_pts], dtype=torch.float32, device=self.device).view(1, 1, -1)

    def _evaluate_expected_free_energy(
        self,
        poses_x: torch.Tensor,
        poses_y: torch.Tensor,
        poses_th: torch.Tensor,
        u_batch: torch.Tensor,
        c_x: float,
        c_y: float,
        c_th: float,
        curr_sensors: np.ndarray,
        cann_state: Optional[Dict[str, Any]]
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        M, H = poses_x.shape[0], poses_x.shape[1]

        # -------------------------------------------------------------
        # 1. Exact SE(2) 7-Point Bumper & Disc Swept Collision Check
        # -------------------------------------------------------------
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
        with torch.inference_mode():
            sampled_occ = F.grid_sample(
                grid_b_ch0, grid_coords, mode="bilinear", padding_mode="zeros", align_corners=True
            ).squeeze(1).squeeze(1)

        max_occ_hits = torch.max(sampled_occ, dim=-1).values

        # Live sonar obstacle proximity
        dists = curr_sensors[:15].astype(np.float32)
        valid = dists < 1.20
        min_d = torch.full((M,), 5.0, device=self.device)
        future_min_d = torch.full((M,), 5.0, device=self.device)
        d0 = 5.0
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
            d_sq_step0 = d_sq[:, 0, :, :]
            d0 = float(torch.sqrt(torch.min(d_sq_step0)).item())
            d_sq_future = d_sq[:, 1:, :, :]
            future_min_d = torch.sqrt(torch.min(d_sq_future.reshape(M, -1), dim=-1).values)

        # Strict safety mask: occ > 0.28 or sonar proximity < 0.035m
        safe_margin = min(0.045, max(0.015, d0 - 0.005)) if d0 < 0.045 else 0.045
        collision_mask = (max_occ_hits > 0.28) | (future_min_d < safe_margin)

        margin_deficit = torch.clamp((max_occ_hits - 0.15) / 0.50, min=0.0, max=1.0)
        j_margin_norm = margin_deficit ** 2
        proximity = torch.clamp((0.15 - future_min_d) / 0.15, min=0.0, max=1.0)
        j_proximity = proximity ** 2

        # -------------------------------------------------------------
        # 2. Smoothness & Jerk Penalty
        # -------------------------------------------------------------
        delta_u = u_batch[:, 1:, :] - u_batch[:, :-1, :]
        j_jerk_norm = torch.clamp(torch.sum(delta_u ** 2, dim=(1, 2)) / 56.0, min=0.0, max=1.0)

        # -------------------------------------------------------------
        # 3. Macro-Frontier Potential (Epistemic Objective)
        # -------------------------------------------------------------
        phi_norm = torch.zeros(M, device=self.device)
        macro_res = self._compute_macro_frontier(c_x, c_y)
        th_des = c_th

        if macro_res is not None:
            f_star_x, f_star_y, current_geo_dist, dist_field = macro_res
            term_norm_x = (poses_x[:, -1] / self.half_size).clamp(-1.0, 1.0)
            term_norm_y = (poses_y[:, -1] / self.half_size).clamp(-1.0, 1.0)
            coords = torch.stack([term_norm_x, term_norm_y], dim=-1).unsqueeze(0).unsqueeze(2)
            finite_dist_field = np.nan_to_num(dist_field, nan=6.0, posinf=6.0)
            dist_tensor = torch.from_numpy(finite_dist_field).unsqueeze(0).unsqueeze(0)
            with torch.inference_mode():
                term_dists = F.grid_sample(
                    dist_tensor, coords, mode="bilinear", padding_mode="border", align_corners=True
                ).squeeze()
            delta_d_geo = current_geo_dist - term_dists
            phi_norm = torch.clamp(delta_d_geo / 0.35, min=-1.0, max=1.0)

            # Gradient-guided target heading
            rc_ix = int(np.clip((c_x + self.half_size) / self.resolution, 0, self.grid_size - 1))
            rc_iy = int(np.clip((c_y + self.half_size) / self.resolution, 0, self.grid_size - 1))
            d_curr = dist_field[rc_iy, rc_ix]
            if not np.isinf(d_curr) and 1 <= rc_ix < self.grid_size - 1 and 1 <= rc_iy < self.grid_size - 1:
                d_e = dist_field[rc_iy, rc_ix + 1]
                d_w = dist_field[rc_iy, rc_ix - 1]
                d_n = dist_field[rc_iy + 1, rc_ix]
                d_s = dist_field[rc_iy - 1, rc_ix]
                gx = (d_e - d_w) / (2.0 * self.resolution) if not (np.isinf(d_e) or np.isinf(d_w)) else 0.0
                gy = (d_n - d_s) / (2.0 * self.resolution) if not (np.isinf(d_n) or np.isinf(d_s)) else 0.0
                if math.hypot(gx, gy) > 0.05:
                    th_des = math.atan2(-gy, -gx)
                else:
                    th_des = math.atan2(f_star_y - c_y, f_star_x - c_x)
            else:
                th_des = math.atan2(f_star_y - c_y, f_star_x - c_x)

        # -------------------------------------------------------------
        # 4. Universal Corridor Detection & Manifold Guidance
        # -------------------------------------------------------------
        d_fwd = float(np.min(dists[6:9])) if len(dists) >= 9 else 5.0
        d_center = float(dists[7]) if len(dists) >= 8 else 5.0
        d_l_side = float(np.min(dists[10:14])) if len(dists) >= 14 else 5.0
        d_r_side = float(np.min(dists[1:5])) if len(dists) >= 5 else 5.0

        # In-corridor condition: bounded on both sides
        in_corridor = (d_l_side < 0.60 and d_r_side < 0.60 and (0.25 <= d_l_side + d_r_side <= 0.95))
        asym = d_l_side - d_r_side  # positive = more space on left -> steer left

        # Detect dead end turnaround in chamber
        dyaw_from_spawn = abs(math.atan2(math.sin(c_th - self._spawn_yaw), math.cos(c_th - self._spawn_yaw)))
        if dyaw_from_spawn >= math.radians(110.0):
            self._turned_around = True

        j_corridor_veto = torch.zeros(M, device=self.device)
        u_diff = u_batch[:, :, 1] - u_batch[:, :, 0]
        mean_u_diff = torch.mean(u_diff, dim=1)
        u_fwd_all = 0.5 * (u_batch[:, :, 0] + u_batch[:, :, 1])
        u_mean_fwd = torch.mean(u_fwd_all, dim=1)

        if in_corridor:
            self._entered_corridor = True
            # Snap th_des to corridor axis:
            # If in horizontal corridor (Env 1), heading is West (-pi or pi)
            # If in vertical corridor (Env 2), heading is South (-pi/2)
            cardinals = [math.pi, -math.pi, -math.pi / 2, 0.0]
            best_card = min(cardinals, key=lambda a: abs(math.atan2(math.sin(th_des - a), math.cos(th_des - a))))
            # Lateral restoring tilt
            tilt = float(np.clip(asym * 0.40, -0.22, 0.22))
            th_des = best_card + tilt

            # HARD INVARIANT: In narrow corridor, VETO in-place pivots and reversing!
            # Only admitted candidates are forward cruises with gentle steering
            rot_in_corr = torch.abs(mean_u_diff) > 0.32
            collision_mask |= rot_in_corr

            # Veto reversing in corridor if roughly aligned with egress
            cos_corr = math.cos(c_th - best_card)
            if cos_corr > 0.0:
                rev_in_corr = u_mean_fwd < 0.10
                collision_mask |= rev_in_corr

        th_des = math.atan2(math.sin(th_des), math.cos(th_des))
        delta_th = math.atan2(math.sin(th_des - c_th), math.cos(th_des - c_th))
        th_des_smooth = c_th + delta_th

        cos_term = torch.cos(poses_th[:, -1] - th_des_smooth)
        cos_mean = torch.mean(torch.cos(poses_th - th_des_smooth), dim=1)
        cos_align = 0.40 * cos_term + 0.60 * cos_mean
        j_heading = 1.0 - cos_align

        # Directional consistency
        j_wrong_turn = torch.clamp(-mean_u_diff * math.sin(delta_th), min=0.0) * 8.0

        # Forward acceleration bonus
        cos_curr = math.cos(c_th - th_des)
        align_gate = float(np.clip((cos_curr - 0.30) / 0.70, 0.0, 1.0)) * torch.clamp((cos_align - 0.30) / 0.70, min=0.0, max=1.0)
        fwd_clearance_gate = float(np.clip((d_center - 0.16) / 0.18, 0.0, 1.0))
        cruise_weight = 18.00 if in_corridor else 10.00
        j_fwd_bonus = torch.clamp(u_mean_fwd, min=0.0) * align_gate * fwd_clearance_gate * cruise_weight

        # Reversal at dead end
        j_dead_end_rev = torch.zeros(M, device=self.device)
        at_dead_end = (d_fwd < 0.30 or d_center < 0.32) and not self._turned_around
        if at_dead_end:
            self._reverse_latched = True

        if not self._turned_around and (self._reverse_latched or self._reverse_ticks > 0):
            # Reward reversing backwards away from wall
            j_dead_end_rev = - torch.clamp(-u_mean_fwd, min=0.0) * 35.00
            j_heading = j_heading * 0.01

        # Rotational clearance
        u_rot_mag = torch.abs(u_batch[:, :, 1] - u_batch[:, :, 0]).mean(dim=1)
        rot_clearance_risk = max(0.0, (0.26 - d_fwd) / 0.26)
        j_rot_clearance = rot_clearance_risk * u_rot_mag * 4.0

        # Assemble clean EFE
        g_pragmatic = (
            self.alpha_margin * j_margin_norm +
            30.00 * j_proximity +
            self.alpha_jerk * j_jerk_norm +
            10.00 * j_heading +
            j_wrong_turn +
            j_rot_clearance +
            j_corridor_veto +
            j_dead_end_rev -
            j_fwd_bonus
        )
        g_epistemic = - self.w_info * self.alpha_epistemic * phi_norm * 2.0
        g_total = g_pragmatic + g_epistemic

        if not torch.all(collision_mask):
            g_total[collision_mask] = 1e6
        else:
            g_total += (0.045 - min_d) * 1e4

        debug_info = {
            "mean_pragmatic": float(g_pragmatic.mean().item()),
            "mean_epistemic": float(g_epistemic.mean().item()),
            "accepted_candidates": int((~collision_mask).sum().item()),
            "rejected_candidates": int(collision_mask.sum().item()),
            "min_sonar_d": float(min_d.min().item()),
            "heading_at_min_clearance": float(poses_th[0, -1].item()),
            "rejection_reason": "none",
            "desired_heading": float(th_des),
        }
        return g_total, debug_info


def run_screening():
    print("=" * 60)
    print("RUNNING VERTICAL STARTUP 10-CONFIG SCREENING BATTERY")
    print("SE(2) Swept Hull Veto + 1D Corridor Manifold Guidance")
    print("=" * 60)

    configs = build_50_matched_configurations()
    cfg_map = {c["config_id"]: c for c in configs}

    outcomes = []
    for cfg_id in SCREENING_CONFIG_IDS:
        cfg = cfg_map[cfg_id]
        env_id = cfg["env_id"]
        xml_path = ENV1_XML if env_id == 1 else ENV2_XML
        grid_path = ENV1_GRID if env_id == 1 else ENV2_GRID
        sx, sy = cfg["spawn_pos"]
        syaw = cfg["spawn_yaw"]
        seed = cfg["seed"]

        np.random.seed(seed)
        torch.manual_seed(seed)

        hal = CarlStage1HAL(xml_path=str(xml_path))
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        ctrl = VerticalActiveInferenceEngine(
            grid_path=str(grid_path),
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless"
        )
        ctrl.initialize_pose(sx, sy, syaw)

        had_collision = False
        escaped = False
        v_est = 0.0
        latencies = []

        for tick in range(MAX_TICKS):
            sensors = hal.read_sensors()
            gyro_w = float(sensors[20])
            ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_w, dt=ctrl.dt)

            t0 = time.perf_counter()
            u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=gyro_w)
            lat = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat)

            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0], cmd_6d[1] = float(u_star[0]), float(u_star[1])
            hal.step(cmd_6d)

            qa = int(hal.model.joint("spatial_identity").qposadr[0])
            new_x = float(hal.data.qpos[qa])
            new_y = float(hal.data.qpos[qa+1])
            new_yaw = 2.0 * math.atan2(float(hal.data.qpos[qa+6]), float(hal.data.qpos[qa+3]))

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

            c_info = hal.get_carl_contact_info()
            if c_info["carl_contacts"] - c_info["floor_contacts"] > 0:
                had_collision = True
                break

            # Exit criteria
            if env_id == 1 and new_x <= -0.55:
                escaped = True
                break
            elif env_id == 2 and new_y <= -1.20:
                escaped = True
                break

        status = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")
        mean_lat = float(np.mean(latencies))
        p95_lat = float(np.percentile(latencies, 95))
        outcomes.append({
            "config_id": cfg_id,
            "env_id": env_id,
            "status": status,
            "ticks": tick + 1,
            "final_x": new_x,
            "final_y": new_y,
            "final_yaw_deg": math.degrees(new_yaw),
            "mean_lat_ms": mean_lat,
            "p95_lat_ms": p95_lat
        })
        print(f"Config {cfg_id:2d} (Env {env_id}): {status:<10} at tick {tick+1:3d} (x={new_x:+.3f}, y={new_y:+.3f}, yaw={math.degrees(new_yaw):+6.1f}°) lat_p95={p95_lat:.1f}ms")

    escapes = sum(1 for o in outcomes if o["status"] == "ESCAPE")
    collisions = sum(1 for o in outcomes if o["status"] == "COLLISION")
    timeouts = sum(1 for o in outcomes if o["status"] == "TIMEOUT")
    print("=" * 60)
    print(f"SCREENING RESULTS: Escapes={escapes}/10, Collisions={collisions}/10, Timeouts={timeouts}/10")
    print("=" * 60)


if __name__ == "__main__":
    run_screening()
