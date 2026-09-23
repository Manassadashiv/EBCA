"""
brain/carl_stage2_2_r2_occupancy_memory.py — Module 2: Spatial Occupancy & Boundary Memory
Classification: [CORE COMPONENT] Allocentric Spatial Cognitive Map (Stage 2.2-R2)

Role:
Maintains an internal, allocentric 2D spatial grid of obstacle endpoints discovered by CARL's
own exploratory history relative to its subjective internal origin (0, 0).

Causal Invariants Enforced:
1. Zero Simulator GPS Leak: Grid is anchored strictly to CARL's internal dead-reckoning origin (0, 0).
2. Obstacle Grounding: Coordinates are spatial keys into accumulated obstacle hits. An unmapped or
   cleared grid returns unmapped clearance (5.0 m).
3. Adversarial Manipulations: Supports deterministic erasure, spatial scrambling, and episode-swap
   interventions required for Gates 4 and 5.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, List


class SpatialOccupancyMemory(nn.Module):
    """
    Module 2 (M_env): Allocentric 2D Occupancy Grid Memory.
    
    Grid Properties:
    - Grid size: G x G (default 64x64)
    - Spatial resolution: 0.10 m per cell (covers 12.8m x 12.8m arena centered at 0, 0)
    - Cell bounds: [-6.4m, +6.4m] in both X and Y
    - Channels: 2 (Channel 0 = obstacle hit accumulation; Channel 1 = visited/observed visibility)
    """
    def __init__(
        self,
        grid_size: int = 128,
        resolution: float = 0.10,
        max_range: float = 5.0,
        num_sonar_rays: int = 15
    ):
        super().__init__()
        self.grid_size = grid_size
        self.resolution = resolution
        self.max_range = max_range
        self.num_sonar_rays = num_sonar_rays
        self.half_size = (grid_size * resolution) / 2.0  # 6.4m
        self.r_hull = 0.14  # physical sensor mounting radius outside chassis

        # Sonar angles covering [-120 deg, +120 deg]
        angles_deg = torch.linspace(-120.0, 120.0, num_sonar_rays)
        self.register_buffer("sonar_angles", torch.deg2rad(angles_deg))

        # Pure geometric ray casting parameters
        self.num_sonar_rays = num_sonar_rays

    def world_to_grid(self, x: torch.Tensor, y: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Converts internal 2D metric coordinates to continuous normalized grid coordinates [-1, 1]."""
        u = x / self.half_size
        v = y / self.half_size
        return u, v

    def accumulate_observations(
        self,
        grid: torch.Tensor,
        poses: torch.Tensor,
        sonars: torch.Tensor
    ) -> torch.Tensor:
        """
        Accumulates observed sonar readings into the 2D occupancy grid with:
        1. Chassis footprint clearing (R <= 0.22m) around robot's current pose.
        2. Free-space ray carving along open beams.
        3. Obstacle hit deposition at beam endpoints.
        
        Args:
            grid: (batch, 2, G, G) current occupancy grid
            poses: (batch, 3) dead-reckoned pose [x, y, θ] relative to origin
            sonars: (batch, num_sonar_rays) observed sonar distances
            
        Returns:
            updated_grid: (batch, 2, G, G)
        """
        batch_size = grid.size(0)
        device = grid.device
        updated_grid = grid.clone()

        x_c = poses[:, 0:1]
        y_c = poses[:, 1:2]
        theta_c = poses[:, 2:3]

        for b in range(batch_size):
            xc = x_c[b, 0].item()
            yc = y_c[b, 0].item()
            thc = theta_c[b, 0].item()
            son = sonars[b]

            # 1. Clear robot chassis footprint (R <= 0.22m)
            g_xc = int((xc + self.half_size) / self.resolution)
            g_yc = int((yc + self.half_size) / self.resolution)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dx*dx + dy*dy <= 4:
                        ix = g_xc + dx
                        iy = g_yc + dy
                        if 0 <= ix < self.grid_size and 0 <= iy < self.grid_size:
                            updated_grid[b, 0, iy, ix] = 0.0

            # 2. Free-space carving & obstacle deposition along all 15 rays
            for i in range(self.num_sonar_rays):
                phi_i = self.sonar_angles[i].item()
                ray_angle = thc + phi_i
                d_val = son[i].item()

                # Free-space carving along ray up to min(d - 0.15, 4.85)
                carve_limit = min(d_val - 0.15, self.max_range - 0.15)
                if carve_limit > 0.15:
                    num_carve = int(carve_limit / 0.08)
                    for k in range(1, num_carve + 1):
                        r_c = self.r_hull + k * 0.08
                        if r_c >= carve_limit:
                            break
                        cx = xc + r_c * math.cos(ray_angle)
                        cy = yc + r_c * math.sin(ray_angle)
                        c_ix = int((cx + self.half_size) / self.resolution)
                        c_iy = int((cy + self.half_size) / self.resolution)
                        if 0 <= c_ix < self.grid_size and 0 <= c_iy < self.grid_size:
                            updated_grid[b, 0, c_iy, c_ix] = max(0.0, updated_grid[b, 0, c_iy, c_ix].item() - 0.5)
                            updated_grid[b, 1, c_iy, c_ix] = 1.0

                # Deposit hit at ray endpoint if distance is less than max range
                if d_val < (self.max_range - 0.05):
                    hx = xc + (d_val + self.r_hull) * math.cos(ray_angle)
                    hy = yc + (d_val + self.r_hull) * math.sin(ray_angle)
                    h_ix = int((hx + self.half_size) / self.resolution)
                    h_iy = int((hy + self.half_size) / self.resolution)
                    if 0 <= h_ix < self.grid_size and 0 <= h_iy < self.grid_size:
                        updated_grid[b, 0, h_iy, h_ix] = min(10.0, updated_grid[b, 0, h_iy, h_ix].item() + 1.0)
                        updated_grid[b, 1, h_iy, h_ix] = 1.0

        return updated_grid

    def query_clearance(
        self,
        grid: torch.Tensor,
        prospective_poses: torch.Tensor,
        num_samples_per_ray: int = 80,
        occ_threshold: float = 1.0
    ) -> torch.Tensor:
        """
        Vectorized prospective obstacle clearance query across all 15 rays simultaneously.
        
        Args:
            grid: (batch, 2, G, G) occupancy grid
            prospective_poses: (batch, 3) query pose [x, y, θ]
            num_samples_per_ray: number of radial step samples (default 80)
            occ_threshold: obstacle detection threshold in grid occupancy units (default 1.0)
            
        Returns:
            clearance_profile: (batch, num_sonar_rays) prospective clearance in meters [0.0, 5.0]
        """
        batch_size = grid.size(0)
        device = grid.device

        # Clear robot chassis footprint at prospective pose to prevent self-detection
        clean_grid = grid.clone()
        for b in range(batch_size):
            q_xc = prospective_poses[b, 0].item()
            q_yc = prospective_poses[b, 1].item()
            q_gxc = int(round((q_xc + self.half_size) / self.resolution))
            q_gyc = int(round((q_yc + self.half_size) / self.resolution))
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dx*dx + dy*dy <= 4:
                        ix = q_gxc + dx
                        iy = q_gyc + dy
                        if 0 <= ix < self.grid_size and 0 <= iy < self.grid_size:
                            clean_grid[b, 0, iy, ix] = 0.0

        x_p = prospective_poses[:, 0:1]  # (B, 1)
        y_p = prospective_poses[:, 1:2]  # (B, 1)
        theta_p = prospective_poses[:, 2:3]  # (B, 1)

        # Sample radii from 0.05m to 5.0m
        radii = torch.linspace(0.05, self.max_range, num_samples_per_ray, device=device)  # (K,)
        K = num_samples_per_ray

        # Ray directions for all 15 rays: (B, 15)
        ray_dirs = theta_p + self.sonar_angles.unsqueeze(0)  # (B, 15)

        # Sensor origin for each ray accounting for hull offset: (B, 15, 1)
        ox = (x_p.unsqueeze(1) + self.r_hull * torch.cos(ray_dirs).unsqueeze(-1))  # (B, 15, 1)
        oy = (y_p.unsqueeze(1) + self.r_hull * torch.sin(ray_dirs).unsqueeze(-1))  # (B, 15, 1)

        # Sample points along all 15 rays: (B, 15, K)
        sample_x = ox + radii.view(1, 1, K) * torch.cos(ray_dirs).unsqueeze(-1)
        sample_y = oy + radii.view(1, 1, K) * torch.sin(ray_dirs).unsqueeze(-1)

        # Normalize to continuous grid coordinates [-1, 1] for grid_sample
        u_norm = (sample_x / self.half_size).clamp(-1.0, 1.0)
        v_norm = (sample_y / self.half_size).clamp(-1.0, 1.0)

        # query_coords: (B, 15, K, 2)
        query_coords = torch.stack([u_norm, v_norm], dim=-1)

        # Single batched grid_sample call for all rays
        sampled_occ = F.grid_sample(
            clean_grid[:, 0:1, :, :],
            query_coords,
            mode="bilinear",
            padding_mode="zeros",
            align_corners=True
        ).squeeze(1)  # (B, 15, K)

        # Obstacle detection threshold (default 1.0 reliably separates true wall deposits >= 1.0 from interpolation bleed)
        detected = (sampled_occ > occ_threshold).float()
        has_hit = (detected.sum(dim=-1) > 0).float()
        first_hit = torch.argmax(detected, dim=-1)  # finds first boundary hit along ray

        hit_dists = radii[first_hit]  # (B, 15)
        raw_clearance = torch.where(
            has_hit > 0.5,
            hit_dists,
            torch.full_like(hit_dists, self.max_range)
        )

        # Pure deterministic geometric ray clearance (zero random neural perturbation)
        return raw_clearance

    def erase_memory(self, grid: torch.Tensor) -> torch.Tensor:
        """Adversarial Intervention: Completely wipes the occupancy grid to zero."""
        return torch.zeros_like(grid)

    def scramble_memory(self, grid: torch.Tensor, patch_size: int = 16) -> torch.Tensor:
        """Adversarial Intervention: Spatially permutes 16x16 grid patches."""
        B, C, H, W = grid.shape
        scrambled = grid.clone()
        for b in range(B):
            patches = []
            for i in range(0, H, patch_size):
                for j in range(0, W, patch_size):
                    patches.append(scrambled[b, :, i:i+patch_size, j:j+patch_size])
            perm = torch.randperm(len(patches))
            idx = 0
            for i in range(0, H, patch_size):
                for j in range(0, W, patch_size):
                    scrambled[b, :, i:i+patch_size, j:j+patch_size] = patches[perm[idx]]
                    idx += 1
        return scrambled
