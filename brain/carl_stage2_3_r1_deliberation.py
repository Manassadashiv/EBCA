"""
brain/carl_stage2_3_r1_deliberation.py — Stage 2.3-R1 Full Action Deliberation Engine
Classification: [STAGE 2.3-R1 FULL DELIBERATION] Continuous Action Space & Unprivileged Localization

Core Capabilities:
1. Continuous Action Candidate Generation (K=24 arcs over horizon H=10):
   - Curvature fan with differential velocity combinations.
   - High-speed forward sweeps with fine steering trims.
   - In-place pivots (pure rotation).
   - Reverse-turn escape trajectories.
2. Unprivileged Internal Dead-Reckoning Localization:
   - Tracks (x_hat, y_hat, theta_hat) internally from wheel velocity and gyro yaw rate.
   - Zero qpos reads during active deliberation cycles.
3. Vectorized Bilinear Clearance Evaluation:
   - Parallel mental unrolls of all K=24 candidate trajectories in PyTorch.
   - Batched query to SpatialOccupancyMemory against arena_occupancy_grid.pt.
4. Five Comparative Decision Modes:
   - 'deliberative': Full Stage 2.3-R1 continuous lookahead + spatial memory.
   - 'reflex': Naive scripted reactive obstacle avoidance ("if front < 0.5m, turn left").
   - 'amnesic': Deliberation with erased spatial memory (M_env = 0).
   - 'random': Stochastic selection among continuous candidates.
   - 'potential_field': Memoryless continuous potential field controller.
"""

import sys
import time
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import torch

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.train_stage2_2_grounded_body_model import GroundedKinematicBodyModel
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory


class CARLStage2_3R1DeliberationEngine:
    """
    Full Closed-Loop Deliberation Engine for CARL Stage 2.3-R1.
    Evaluates continuous action fans under unprivileged internal dead reckoning.
    """
    def __init__(
        self,
        grid_path: str = "evidence/stage2_2_grounded/arena_occupancy_grid.pt",
        body_model_path: str = "checkpoints/stage2_2_grounded/grounded_body_model.pt",
        horizon: int = 10,
        dt: float = 0.030,
        hazard_clearance_threshold: float = 0.28,
        mode: str = "deliberative"
    ):
        self.horizon = horizon
        self.dt = dt
        self.hazard_thresh = hazard_clearance_threshold
        self.mode = mode.lower()

        # Load Certified Allocentric Grid
        grid_file = repo_root / grid_path
        if grid_file.exists():
            grid = torch.load(grid_file, map_location="cpu")
            if isinstance(grid, np.ndarray):
                grid = torch.from_numpy(grid).float()
            if grid.dim() == 3:
                grid = grid.unsqueeze(0)
            self.grid = grid
            self.mem = SpatialOccupancyMemory(grid_size=grid.shape[-1], resolution=0.10)
        else:
            print(f"Warning: Grid not found at {grid_file}, initializing blank memory")
            self.grid = torch.zeros(1, 1, 128, 128)
            self.mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)

        # In amnesic mode, spatial memory is explicitly erased (M_env = 0)
        if self.mode == "amnesic":
            self.grid = torch.zeros_like(self.grid)

        # Load Certified Grounded Body Dynamics Model
        self.body_model = GroundedKinematicBodyModel()
        body_file = repo_root / body_model_path
        if body_file.exists():
            self.body_model.load_state_dict(torch.load(body_file, map_location="cpu"))
        self.body_model.eval()

        # Calibrated Physical Constants (Empirical Grounded Kinematics)
        self.k_fwd = 0.0091  # Empirical linear displacement gain per tick under wheel control (0.3033 m/s * 0.03s)
        self.k_rot = float(self.body_model.k_rot.item())
        self.gamma_v = float(self.body_model.gamma_v.item())
        self.gamma_w = float(self.body_model.gamma_w.item())
        self.w_base = float(self.body_model.w_base.item())
        self.w_transient = float(self.body_model.w_transient.item())
        self.w_decay = float(self.body_model.w_decay.item())

        # Internal Dead-Reckoning State (x_hat, y_hat, theta_hat, v_hat, w_hat)
        self.pose = np.zeros(3, dtype=np.float64)  # [x, y, theta]
        self.v_hat = 0.0
        self.w_hat = 0.0

        # Pre-configured geometric ray parameters for ultra-fast vectorized clearance queries
        self.grid_ch0 = self.grid[:, 0:1, :, :].contiguous()
        self.num_samples_per_ray = 40  # RC-4 FIX: halved from 80 for latency (0.125m resolution still << 0.25m alignment)
        self.max_range = 5.0
        self.half_size = 6.4
        self.r_hull = 0.14
        self.sonar_angles = torch.deg2rad(torch.linspace(-120.0, 120.0, 15))

        # Continuous Candidate Action Sequences (K=24, H=10)
        self.candidates = self._generate_continuous_candidate_fan()

        # Warmup forward unroll and clearance pipelines to eliminate cold-start JIT latency
        if self.mode == "deliberative":
            dummy_s = np.ones(15, dtype=np.float32) * 0.40
            self.select_action(dummy_s)

    def initialize_pose(self, spawn_x: float, spawn_y: float, spawn_yaw: float):
        """Initializes internal dead reckoning at trial start. No further qpos reads allowed."""
        self.pose = np.array([spawn_x, spawn_y, spawn_yaw], dtype=np.float64)
        self.v_hat = 0.0
        self.w_hat = 0.0

    def update_odometry(self, v_wheel: float, w_gyro: float, dt: Optional[float] = None):
        """
        Unprivileged internal dead-reckoning integration:
        Integrates IMU gyro yaw rate and wheel velocity into internal pose estimate.
        """
        d_time = self.dt if dt is None else dt
        self.w_hat = float(w_gyro)
        self.v_hat = float(v_wheel)

        # Yaw integration from gyroscope
        self.pose[2] += self.w_hat * d_time
        # Normalize yaw to [-pi, pi]
        self.pose[2] = math.atan2(math.sin(self.pose[2]), math.cos(self.pose[2]))

        # Displacement integration in internal frame
        dx = self.v_hat * math.cos(self.pose[2]) * d_time
        dy = self.v_hat * math.sin(self.pose[2]) * d_time
        self.pose[0] += dx
        self.pose[1] += dy

    def _generate_continuous_candidate_fan(self) -> Dict[str, np.ndarray]:
        """
        Generates K=24 continuous candidate action trajectories over horizon H:
        - 14 continuous curvature arcs (differential forward drive)
        - 4 straight/trim sweeps
        - 3 in-place pivots
        - 3 reverse-turn recovery arcs
        """
        H = self.horizon
        fan = {}

        # 1. Continuous Curvature Steering Fan (14 arcs)
        curvatures = [
            ("hard_left_fast", 0.15, 0.80),
            ("hard_left_mod",  0.10, 0.50),
            ("med_left_fast",  0.35, 0.80),
            ("med_left_mod",   0.25, 0.50),
            ("soft_left_fast", 0.55, 0.80),
            ("soft_left_mod",  0.40, 0.55),
            ("gentle_left",    0.65, 0.75),
            ("gentle_right",   0.75, 0.65),
            ("soft_right_mod", 0.55, 0.40),
            ("soft_right_fast",0.80, 0.55),
            ("med_right_mod",  0.50, 0.25),
            ("med_right_fast", 0.80, 0.35),
            ("hard_right_mod", 0.50, 0.10),
            ("hard_right_fast",0.80, 0.15),
        ]
        for name, uL, uR in curvatures:
            seq = np.zeros((H, 6), dtype=np.float32)
            seq[:, 0] = uL
            seq[:, 1] = uR
            fan[name] = seq

        # 2. High-Speed Straight & Fine Trims (4 arcs)
        trims = [
            ("straight_full",  0.80, 0.80),
            ("straight_cruise",0.60, 0.60),
            ("straight_trim_L",0.75, 0.80),
            ("straight_trim_R",0.80, 0.75),
        ]
        for name, uL, uR in trims:
            seq = np.zeros((H, 6), dtype=np.float32)
            seq[:, 0] = uL
            seq[:, 1] = uR
            fan[name] = seq

        # 3. In-Place Pivots (3 arcs)
        pivots = [
            ("pivot_left_hard", -0.60,  0.60),
            ("pivot_right_hard", 0.60, -0.60),
            ("pivot_left_mod",  -0.35,  0.35),
        ]
        for name, uL, uR in pivots:
            seq = np.zeros((H, 6), dtype=np.float32)
            seq[:, 0] = uL
            seq[:, 1] = uR
            fan[name] = seq

        # 4. Reverse Escape Arcs (3 arcs)
        reverses = [
            ("reverse_straight", -0.35, -0.35),
            ("reverse_hook_left",-0.40, -0.15),
            ("reverse_hook_right",-0.15,-0.40),
        ]
        for name, uL, uR in reverses:
            seq = np.zeros((H, 6), dtype=np.float32)
            seq[:, 0] = uL
            seq[:, 1] = uR
            fan[name] = seq

        assert len(fan) == 24, f"Expected 24 candidates, got {len(fan)}"
        return fan

    def _mental_unroll_poses(
        self,
        curr_x: float,
        curr_y: float,
        curr_yaw: float,
        u_seq: np.ndarray,
        init_v: float = 0.0,
        init_w: float = 0.0
    ) -> List[List[float]]:
        """Prospective mental rollout of body poses using learned dynamics."""
        poses = []
        c_x, c_y, c_th = curr_x, curr_y, curr_yaw
        prev_v = init_v
        prev_w = init_w

        for step in range(self.horizon):
            u = u_seq[step]
            u_fwd = 0.5 * (u[0] + u[1])
            u_diff = (u[1] - u[0])

            is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
            v_target = u_fwd * self.k_fwd / self.dt
            next_v = is_fwd_zero * (self.gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)

            is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
            w_gain = self.w_base + self.w_transient * math.exp(-step / max(self.w_decay, 0.1))
            w_target = u_diff * w_gain
            next_w = is_diff_zero * (self.gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.15 * prev_w + 0.85 * w_target)

            dx_loc = next_v * self.dt
            dy_loc = 0.0
            dtheta = next_w * self.dt

            dx_g = dx_loc * math.cos(c_th) - dy_loc * math.sin(c_th)
            dy_g = dx_loc * math.sin(c_th) + dy_loc * math.cos(c_th)

            c_x += dx_g
            c_y += dy_g
            c_th += dtheta
            poses.append([c_x, c_y, c_th])
            prev_v = next_v
            prev_w = next_w

        return poses

    def select_action(
        self,
        curr_sensors: np.ndarray,
        curr_v: float = 0.0,
        curr_w: float = 0.0,
        forced_pose: Optional[Tuple[float, float, float]] = None,
        cann_state: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Selects continuous motor action using the configured deliberation mode.
        If forced_pose is provided, uses forced_pose.
        Else if cann_state is provided, grounds orientation and displacement in CANN attractor state.
        Else uses internal dead-reckoned self.pose (UNPRIVILEGED).
        """
        t_start = time.perf_counter()
        front_sonar = float(np.min(curr_sensors[6:9])) if len(curr_sensors) >= 15 else 5.0

        if forced_pose is not None:
            c_x, c_y, c_th = forced_pose
        elif cann_state is not None:
            # Ground pose in 2,114-unit neuromorphic continuous attractor
            hd_head = cann_state.get("hd_decoded_heading", None)
            if hd_head is None:
                hd_head = cann_state.get("cann_heading", self.pose[2])
            c_th = float(hd_head)
            c_x = float(cann_state.get("grid_unwrapped_x", self.pose[0]))
            c_y = float(cann_state.get("grid_unwrapped_y", self.pose[1]))
        else:
            c_x, c_y, c_th = self.pose

        # ---------------------------------------------------------------------
        # MODE 1: RANDOM BASELINE (Stochastic candidate selection)
        # ---------------------------------------------------------------------
        if self.mode == "random":
            candidate_names = list(self.candidates.keys())
            chosen = str(np.random.choice(candidate_names))
            action = self.candidates[chosen][0].copy()
            lat_ms = (time.perf_counter() - t_start) * 1000.0
            return action, {"latency_ms": lat_ms, "selected_branch": chosen, "utility": 0.0}

        # ---------------------------------------------------------------------
        # MODE 2: SCRIPTED REFLEX BASELINE ("If front < 0.5m, turn left")
        # ---------------------------------------------------------------------
        elif self.mode == "reflex":
            if front_sonar < 0.50:
                action = self.candidates["hard_left_fast"][0].copy()
                branch_name = "reflex_left"
            else:
                action = self.candidates["straight_full"][0].copy()
                branch_name = "reflex_fwd"
            lat_ms = (time.perf_counter() - t_start) * 1000.0
            return action, {"latency_ms": lat_ms, "selected_branch": branch_name, "utility": 0.0}

        # ---------------------------------------------------------------------
        # MODE 3: ARTIFICIAL POTENTIAL FIELD BASELINE (Memoryless Continuous)
        # ---------------------------------------------------------------------
        elif self.mode == "potential_field":
            # Repulsive field from 15 sonar rays
            # Rays 0..14 at angles [-120 to +120 deg]
            angles = np.linspace(-math.radians(120), math.radians(120), 15)
            repulsion_x, repulsion_y = 0.0, 0.0
            for r_dist, r_ang in zip(curr_sensors[:15], angles):
                if r_dist < 1.0:
                    weight = (1.0 / max(r_dist, 0.05) - 1.0)
                    repulsion_x -= weight * math.cos(r_ang)
                    repulsion_y -= weight * math.sin(r_ang)

            target_heading_change = math.atan2(repulsion_y, max(0.2, 1.0 + repulsion_x))
            target_steer = np.clip(target_heading_change * 1.5, -0.8, 0.8)
            fwd_speed = 0.70 if front_sonar >= 0.50 else 0.20

            action = np.zeros(6, dtype=np.float64)
            action[0] = np.clip(fwd_speed - target_steer * 0.5, -0.6, 0.8)
            action[1] = np.clip(fwd_speed + target_steer * 0.5, -0.6, 0.8)
            lat_ms = (time.perf_counter() - t_start) * 1000.0
            return action, {"latency_ms": lat_ms, "selected_branch": "potential_field", "utility": 0.0}

        # ---------------------------------------------------------------------
        # MODE 4 & 5: FULL DELIBERATIVE (or AMNESIC with M_env = 0)
        # ---------------------------------------------------------------------
        # RC-1 FIX: No shortcircuit bypass — ALWAYS run full K=24 prospective deliberation.
        # The straight_full candidate will naturally win when corridor is clear.
        # This ensures the deliberator is never blind-sided by traps it didn't evaluate.
        # (In amnesic mode, self.grid is all zeros, so all prospective clearances appear open)
        branch_utilities = {}
        branch_clearances = {}
        step1_preds = {}

        # Vectorized batch evaluation across all K=24 continuous candidates
        all_poses = []
        candidate_keys = list(self.candidates.keys())
        for k_name in candidate_keys:
            u_seq = self.candidates[k_name]
            p_seq = self._mental_unroll_poses(c_x, c_y, c_th, u_seq, curr_v, curr_w)
            all_poses.append(p_seq)

        # RC-3 FIX: Dense check steps across full horizon including step 0 to catch immediate collisions
        check_indices = [0, 2, 4, 6, 8, 9]
        sampled_poses = [p_seq[idx] for p_seq in all_poses for idx in check_indices]
        poses_tensor = torch.tensor(sampled_poses, dtype=torch.float32)

        B = len(sampled_poses)
        x_p = poses_tensor[:, 0:1]
        y_p = poses_tensor[:, 1:2]
        theta_p = poses_tensor[:, 2:3]
        radii = torch.linspace(0.05, self.max_range, self.num_samples_per_ray)
        K = self.num_samples_per_ray
        ray_dirs = theta_p + self.sonar_angles.unsqueeze(0)
        ox = x_p.unsqueeze(1) + self.r_hull * torch.cos(ray_dirs).unsqueeze(-1)
        oy = y_p.unsqueeze(1) + self.r_hull * torch.sin(ray_dirs).unsqueeze(-1)
        sample_x = ox + radii.view(1, 1, K) * torch.cos(ray_dirs).unsqueeze(-1)
        sample_y = oy + radii.view(1, 1, K) * torch.sin(ray_dirs).unsqueeze(-1)
        query_coords = torch.stack([(sample_x / self.half_size).clamp(-1.0, 1.0), (sample_y / self.half_size).clamp(-1.0, 1.0)], dim=-1)

        # RC-4 FIX: use inference_mode for faster execution
        grid_b = self.grid_ch0.expand(B, 1, self.grid_ch0.shape[-2], self.grid_ch0.shape[-1])
        with torch.inference_mode():
            sampled_occ = torch.nn.functional.grid_sample(grid_b, query_coords, mode="bilinear", padding_mode="zeros", align_corners=True).squeeze(1)

        detected = (sampled_occ > 1.0).float()
        has_hit = (detected.sum(dim=-1) > 0).float()
        first_hit = torch.argmax(detected, dim=-1)
        hit_dists = radii[first_hit]
        c_flat = torch.where(has_hit > 0.5, hit_dists, torch.full_like(hit_dists, self.max_range)).numpy()
        c_batched = c_flat.reshape(len(candidate_keys), len(check_indices), 15)

        # Check immediate lateral proximity from live sensors (rays 2..5 = right forward flank, rays 9..12 = left forward flank)
        min_live_sonar = float(np.min(curr_sensors[:15])) if len(curr_sensors) >= 15 else 5.0
        live_right_dist = float(np.min(curr_sensors[2:6])) if len(curr_sensors) >= 15 else 5.0
        live_left_dist = float(np.min(curr_sensors[9:13])) if len(curr_sensors) >= 15 else 5.0

        # Forward progress reward: when front is open (>= 0.45m), actively reward driving forward down corridors
        fwd_w = 40.0 if front_sonar >= 0.45 else 0.5

        # Grid-based spatial free-space bias: query terminal position occupancy
        # In deliberative mode, the grid has real wall data; in amnesic mode it's all zeros.
        # This gives the deliberative agent a planning advantage by biasing toward mapped free space.
        terminal_xs = torch.tensor([all_poses[i][-1][0] for i in range(len(candidate_keys))], dtype=torch.float32)
        terminal_ys = torch.tensor([all_poses[i][-1][1] for i in range(len(candidate_keys))], dtype=torch.float32)
        # Also query occupancy at mid-horizon for gradient signal
        mid_h = self.horizon // 2
        mid_xs = torch.tensor([all_poses[i][mid_h][0] for i in range(len(candidate_keys))], dtype=torch.float32)
        mid_ys = torch.tensor([all_poses[i][mid_h][1] for i in range(len(candidate_keys))], dtype=torch.float32)

        # Batch query grid occupancy at terminal and mid positions (3x3 neighborhood for robustness)
        grid_bias_scores = np.zeros(len(candidate_keys), dtype=np.float64)
        offsets = [(-0.10, 0.0), (0.10, 0.0), (0.0, -0.10), (0.0, 0.10), (0.0, 0.0)]
        for dx_off, dy_off in offsets:
            for use_mid in [False, True]:
                qx = (mid_xs if use_mid else terminal_xs) + dx_off
                qy = (mid_ys if use_mid else terminal_ys) + dy_off
                norm_x = (qx / self.half_size).clamp(-1.0, 1.0)
                norm_y = (qy / self.half_size).clamp(-1.0, 1.0)
                grid_coords = torch.stack([norm_x, norm_y], dim=-1).view(1, -1, 1, 2)
                with torch.inference_mode():
                    occ_vals = torch.nn.functional.grid_sample(
                        self.grid_ch0, grid_coords, mode='bilinear',
                        padding_mode='zeros', align_corners=True
                    ).squeeze().numpy()
                # Penalty for heading toward occupied cells, bonus for heading toward free cells
                grid_bias_scores -= occ_vals * (1.5 if not use_mid else 0.75)

        for i, k_name in enumerate(candidate_keys):
            c_k = c_batched[i]  # (num_checks, 15)
            p_k = all_poses[i]  # H poses

            final_front_clr = float(np.min(c_k[-1, 6:9]))  # at last check step
            final_mean_clr = float(np.mean(c_k[-1]))
            min_cone_clr = float(np.min(c_k[:, 6:9]))  # min front cone across ALL check steps
            min_hull_clr = float(np.min(c_k))  # min across ALL 15 rays and ALL check steps

            # Lateral clearance metrics for graduated centering utility
            # In HAL, negative angles (0:4, -120 to -51.4 deg) are RIGHT; positive angles (11:15, +51.4 to +120 deg) are LEFT
            min_left_clr = float(np.min(c_k[:, 11:15])) # left-side rays across all checks
            min_right_clr = float(np.min(c_k[:, 0:4]))   # right-side rays across all checks
            min_side_clr = min(min_left_clr, min_right_clr)

            # Front cone collision veto at 0.16m, hull clearance veto at 0.10m
            # (Physical chassis radius is 0.14m; rays begin at hull radius. Distance < 0.10m is near-contact)
            is_collision_predicted = bool(min_cone_clr < 0.16 or min_hull_clr < 0.10 or final_front_clr < 0.16)
            collision_penalty = 800.0 if is_collision_predicted else 0.0

            # Forward progress in local heading frame
            final_dx = p_k[-1][0] - c_x
            final_dy = p_k[-1][1] - c_y
            fwd_progress = final_dx * math.cos(c_th) + final_dy * math.sin(c_th)

            # Reverse penalty (prefer forward evasions over reversing unless front is blocked)
            is_reverse = 0.0 if front_sonar < 0.35 else (15.0 if ("reverse" in k_name or fwd_progress < -0.05) else 0.0)

            # In-place pivot penalty: in-place spinning is an escape maneuver for when front is blocked (< 0.40m),
            # never a cruising action when hallways are open.
            pivot_penalty = 25.0 if ("pivot" in k_name and front_sonar >= 0.40) else 0.0

            # Wide-margin corridor bonus (graduated lateral clearance reward)
            wide_margin_bonus = 2.0 * min(0.40, min_side_clr)

            # Corridor centering bonus: reward staying equidistant from walls in tight channels (< 0.45m)
            centering_bonus = 0.0
            if min_left_clr < 0.45 and min_right_clr < 0.45:
                centering_bonus = -abs(min_left_clr - min_right_clr) * 2.5

            # Active lateral evasion from live sensor proximity
            u_diff = float(self.candidates[k_name][0, 1] - self.candidates[k_name][0, 0])
            lateral_evasion = 0.0
            if live_right_dist < 0.22:
                # Hazard on right: reward steering left (u_diff > 0 = left), penalize straight/right
                lateral_evasion += 40.0 * (0.22 - live_right_dist) * max(u_diff, 0.0)
                if u_diff < 0.10:
                    lateral_evasion -= 25.0 * (0.22 - live_right_dist)
            if live_left_dist < 0.22:
                # Hazard on left: reward steering right (u_diff < 0 = right), penalize straight/left
                lateral_evasion += 40.0 * (0.22 - live_left_dist) * max(-u_diff, 0.0)
                if u_diff > -0.10:
                    lateral_evasion -= 25.0 * (0.22 - live_left_dist)

            # Penalize steering into tight flank walls
            margin_penalty = 0.0
            if min_left_clr < 0.25 and u_diff > 0.0:
                margin_penalty += 30.0 * (0.25 - min_left_clr) * u_diff
            if min_right_clr < 0.25 and u_diff < 0.0:
                margin_penalty += 30.0 * (0.25 - min_right_clr) * (-u_diff)

            # Spatial free-space bias from grid memory (zero in amnesic mode)
            spatial_bias = float(grid_bias_scores[i])

            # CANN Population Vector Directional Coherence
            cann_alignment_score = 0.0
            if cann_state is not None and "hd_rates" in cann_state:
                r_hd = np.asarray(cann_state["hd_rates"], dtype=np.float64)
                if len(r_hd) == 64:
                    angles_hd = np.linspace(-math.pi, math.pi, 64, endpoint=False)
                    cand_terminal_heading = p_k[-1][2]
                    coherence = float(np.sum(r_hd * np.cos(cand_terminal_heading - angles_hd)))
                    cann_alignment_score = coherence * 0.25

            # Multi-objective Prospective Utility per locked specification
            utility = (
                final_front_clr * 4.0
                + final_mean_clr * 2.0
                + fwd_progress * fwd_w
                + min_hull_clr * 2.0
                + min_side_clr * 1.5
                + wide_margin_bonus
                + centering_bonus
                + lateral_evasion
                + spatial_bias
                + cann_alignment_score
                - margin_penalty
                - collision_penalty
                - is_reverse
                - pivot_penalty
            )

            branch_utilities[k_name] = utility
            branch_clearances[k_name] = final_front_clr

            # Predicted step-1 physical sonar (for Predict -> Act -> Compare verification)
            # Evaluates next-step heading rotation dtheta by blending gyro momentum with command target,
            # sweeping the front cone (-17.1 deg to +17.1 deg) across the 15-ray sonar array.
            u_cand = self.candidates[k_name][0]
            u_diff = float(u_cand[1] - u_cand[0])
            u_fwd = float(0.5 * (u_cand[0] + u_cand[1]))
            w_cmd_target = u_diff * (8.0 if "pivot" in k_name else 2.5)
            w_next = 0.65 * curr_w + 0.35 * w_cmd_target
            dtheta = w_next * self.dt

            angles = np.linspace(-math.radians(120), math.radians(120), 15)
            front_cone_targets = np.clip(np.array([-0.2992, 0.0, 0.2992]) + dtheta, -math.radians(120), math.radians(120))
            pred_rays = np.interp(front_cone_targets, angles, curr_sensors[:15])
            v_next = 0.70 * curr_v + 0.30 * (u_fwd * self.k_fwd / self.dt)
            fwd_disp = v_next * self.dt
            pred_s1 = float(np.clip(np.min(pred_rays) - fwd_disp, 0.05, 5.0))
            step1_preds[k_name] = pred_s1

        # Select candidate maximizing prospective utility
        best_branch = max(branch_utilities.keys(), key=lambda k: branch_utilities[k])
        action = self.candidates[best_branch][0].copy()
        lat_ms = (time.perf_counter() - t_start) * 1000.0

        telemetry = {
            "latency_ms": lat_ms,
            "selected_branch": best_branch,
            "utility": branch_utilities[best_branch],
            "all_utilities": branch_utilities,
            "min_clearances": branch_clearances,
            "predicted_step1_clearance": step1_preds[best_branch],
            "cann_wired": cann_state is not None,
            "cann_heading": c_th,
            "real_time_budget_passed": bool(lat_ms <= 50.0)
        }

        return action, telemetry
