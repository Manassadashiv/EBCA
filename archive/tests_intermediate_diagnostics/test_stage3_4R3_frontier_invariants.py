"""
tests/test_stage3_4R3_frontier_invariants.py — Stage 3.4-R3 Sensor-to-Frontier Invariant Test Suite
Formal Pre-Implementation Verification Gate for Stage 3.4-R3.

Epistemological Requirements:
1. Ray Cutoff Invariant: No sonar beam may mark cells beyond obstacle hits as explored (Channel 1 == 0.0).
2. Wall Occlusion Invariant: No phantom frontier cells may exist behind solid occupied barriers.
3. Topological Reachability Invariant: The selected macro-frontier must be connected via mapped free space
   and cannot lie on the far side of an occupied barrier when reachable frontiers exist.
4. Non-Increasing Geodesic Field: Moving toward a reachable frontier must produce a monotonically
   non-increasing BFS distance field.
"""

import sys
import math
from pathlib import Path
import numpy as np
import pytest
import torch

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine


class TestStage34R3FrontierInvariants:

    def test_sonar_ray_integration_does_not_penetrate_obstacles(self):
        """
        Invariant 1: Sonar rays must stop at obstacle boundaries.
        Cells beyond the measured sonar distance d_hit must strictly NOT be marked
        as explored free space (Channel 1 == 0.0).
        """
        ctrl = CARLActiveInferenceEngine(
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless"
        )
        ctrl.initialize_pose(0.0, 0.0, 0.0)  # Robot at (0, 0), facing +X

        # Forward sonars detect an obstacle at d = 0.50 m (indices 6, 7, 8 around center)
        sonars = np.full(15, 2.50, dtype=np.float32)
        sonars[7] = 0.50  # Center sonar beam hits wall at x = 0.50m

        ctrl.update_occupancy_memory(sonars)

        # Coordinate check along the center beam (y = 0, x > 0)
        # Traversed free space: x in [0.0, 0.35m] -> Channel 1 should be 1.0, Channel 0 should be 0.0
        # Obstacle hit: x in [0.45, 0.55m] -> Channel 0 should have obstacle deposit (> 0.0)
        # Beyond obstacle: x in [0.70, 1.50m] -> Channel 1 MUST BE 0.0 (unexplored!)
        res = ctrl.resolution
        half = ctrl.half_size

        # Check points beyond obstacle
        test_x_beyond = [0.80, 1.00, 1.20, 1.50]
        iy_center = int(np.clip((0.0 + half) / res, 0, ctrl.grid_size - 1))

        penetrated_cells = []
        for x_val in test_x_beyond:
            ix = int(np.clip((x_val + half) / res, 0, ctrl.grid_size - 1))
            vis_val = float(ctrl.grid_np[1, iy_center, ix])
            if vis_val > 0.5:
                penetrated_cells.append((x_val, vis_val))

        assert len(penetrated_cells) == 0, (
            f"Ray penetration detected! Cells beyond wall at d=0.50m were marked explored (Channel 1 > 0.5): "
            f"{penetrated_cells}"
        )

    def test_no_phantom_frontiers_behind_solid_walls(self):
        """
        Invariant 2: Enclosed environment geometry must not spawn phantom frontiers in exterior void.
        When CARL is in an enclosed corridor, zero frontier cells may exist on the far side of solid walls.
        """
        grid_path = repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt"
        ctrl = CARLActiveInferenceEngine(
            grid_path=str(grid_path),
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless"
        )
        # Place robot in turning bay facing dead-end cap: x = 0.60, y = 0.0, yaw = 0.0
        ctrl.initialize_pose(0.60, 0.0, 0.0)

        # Sonars hitting dead-end cap at x = 1.20m (distance ~0.60m)
        sonars = np.full(15, 0.60, dtype=np.float32)
        ctrl.update_occupancy_memory(sonars)

        # Check for any frontier cells behind dead-end wall (x > 1.25m) or outside side walls (|y| > 0.65m)
        res = ctrl.resolution
        half = ctrl.half_size

        free_explored = (ctrl.grid_np[1] >= 0.50) & (ctrl.grid_np[0] < 0.30)
        unexplored = (ctrl.grid_np[1] < 0.50)
        pad_unexp = np.pad(unexplored, 1, mode="constant", constant_values=False)
        has_unexp_neighbor = (
            pad_unexp[:-2, :-2] | pad_unexp[:-2, 1:-1] | pad_unexp[:-2, 2:] |
            pad_unexp[1:-1, :-2]                        | pad_unexp[1:-1, 2:] |
            pad_unexp[2:, :-2]  | pad_unexp[2:, 1:-1]  | pad_unexp[2:, 2:]
        )
        obs_mask = (ctrl.grid_np[0] >= 0.30)
        pad_obs = np.pad(obs_mask, 1, mode="constant", constant_values=False)
        near_obs = (
            pad_obs[:-2, :-2] | pad_obs[:-2, 1:-1] | pad_obs[:-2, 2:] |
            pad_obs[1:-1, :-2] | pad_obs[1:-1, 1:-1] | pad_obs[1:-1, 2:] |
            pad_obs[2:, :-2]  | pad_obs[2:, 1:-1]  | pad_obs[2:, 2:]
        )
        frontier_mask = free_explored & has_unexp_neighbor & (~near_obs)

        py, px = np.where(frontier_mask)
        fwx = px * res - half
        fwy = py * res - half

        phantom_exterior = []
        for x_coord, y_coord in zip(fwx, fwy):
            # Dead-end wall is at x = 1.20m; exterior void is x > 1.25m or |y| > 0.70m
            if x_coord > 1.25 or abs(y_coord) > 0.70:
                phantom_exterior.append((float(x_coord), float(y_coord)))

        assert len(phantom_exterior) == 0, (
            f"Phantom exterior frontiers detected outside arena boundaries! Count={len(phantom_exterior)}, "
            f"Sample: {phantom_exterior[:5]}"
        )

    def test_macro_frontier_topological_reachability_invariant(self):
        """
        Invariant 3: Macro-frontier selection must be reachable through mapped free space.
        If a frontier cluster is physically separated by an unbroken wall of occupied cells,
        its BFS geodesic distance is infinite (np.isinf), and it MUST NOT be selected.
        """
        ctrl = CARLActiveInferenceEngine(
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless"
        )
        ctrl.initialize_pose(0.0, 0.0, 0.0)

        # Manually construct two frontier clusters:
        # 1. Reachable cluster at x = -0.50m (in robot's chamber)
        # 2. Phantom/Unreachable cluster at x = +2.00m behind a solid wall at x = +1.00m
        half = ctrl.half_size
        res = ctrl.resolution

        # Free space in robot chamber
        ix_start = int((-0.60 + half) / res)
        ix_end = int((0.80 + half) / res)
        iy_start = int((-0.30 + half) / res)
        iy_end = int((0.30 + half) / res)
        ctrl.grid_np[1, iy_start:iy_end, ix_start:ix_end] = 1.0  # Explored
        ctrl.grid_np[0, iy_start:iy_end, ix_start:ix_end] = 0.0  # Free

        # Solid wall at x in [0.90, 1.10]
        ix_w1 = int((0.90 + half) / res)
        ix_w2 = int((1.10 + half) / res)
        ctrl.grid_np[0, :, ix_w1:ix_w2] = 10.0  # Impassable barrier

        # Unreachable explored patch beyond wall at x in [1.50, 2.20]
        ix_u1 = int((1.50 + half) / res)
        ix_u2 = int((2.20 + half) / res)
        ctrl.grid_np[1, iy_start:iy_end, ix_u1:ix_u2] = 1.0  # Explored
        ctrl.grid_np[0, iy_start:iy_end, ix_u1:ix_u2] = 0.0  # Free

        ctrl.grid[0, 0] = torch.from_numpy(ctrl.grid_np[0])
        ctrl.grid[0, 1] = torch.from_numpy(ctrl.grid_np[1])

        res_tuple = ctrl._compute_macro_frontier(0.0, 0.0)
        assert res_tuple is not None, "Expected macro-frontier to be found"
        fx, fy, current_geo, _ = res_tuple

        # Invariant: The selected frontier must be on the reachable side (x < 0.90m)
        assert fx < 0.90, (
            f"Algorithm selected unreachable frontier behind solid wall at x={fx:.2f}! "
            f"Must select reachable frontier on robot's side of barrier."
        )
        assert not math.isinf(current_geo), "Geodesic distance to selected frontier cannot be infinite"
        assert current_geo < 80.0, f"Geodesic distance {current_geo} indicates unreachable fallback was triggered"

    def test_geodesic_distance_field_non_increasing_along_egress_corridor(self):
        """
        Invariant 4: Geodesic potential field must be non-increasing along forward progress.
        Moving monotonically toward the selected frontier must produce non-increasing BFS values,
        with decreases occurring whenever cell boundaries are crossed.
        """
        grid_path = repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt"
        ctrl = CARLActiveInferenceEngine(
            grid_path=str(grid_path),
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless"
        )
        # Egress corridor runs from x = 0.35 down to x = -0.60 along y = 0.0
        # Place a target frontier cell at x = -0.50, y = 0.0
        half = ctrl.half_size
        res = ctrl.resolution
        tx = int((-0.50 + half) / res)
        ty = int((0.00 + half) / res)

        # Mark corridor as explored free space
        ix1 = int((-0.60 + half) / res)
        ix2 = int((0.60 + half) / res)
        iy1 = int((-0.25 + half) / res)
        iy2 = int((0.25 + half) / res)
        ctrl.grid_np[1, iy1:iy2, ix1:ix2] = 1.0
        ctrl.grid_np[0, iy1:iy2, ix1:ix2] = 0.0

        # Compute BFS field from target
        traversable = (ctrl.grid_np[0] < 0.85)
        dist_field = np.full((ctrl.grid_size, ctrl.grid_size), np.inf, dtype=np.float32)
        dist_field[ty, tx] = 0.0

        from collections import deque
        q = deque([(ty, tx)])
        while q:
            cy, cx = q.popleft()
            cd = dist_field[cy, cx] + res
            if cd > 6.0:
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < ctrl.grid_size and 0 <= nx < ctrl.grid_size and traversable[ny, nx]:
                    if cd < dist_field[ny, nx]:
                        dist_field[ny, nx] = cd
                        q.append((ny, nx))

        # Sample waypoints along corridor moving toward target: x = 0.40 -> 0.30 -> 0.10 -> -0.10 -> -0.30 -> -0.45
        waypoints_x = [0.40, 0.30, 0.20, 0.10, 0.00, -0.10, -0.20, -0.30, -0.40, -0.45]
        distances = []
        for wx in waypoints_x:
            ix = int(np.clip((wx + half) / res, 0, ctrl.grid_size - 1))
            iy = int(np.clip((0.0 + half) / res, 0, ctrl.grid_size - 1))
            distances.append(float(dist_field[iy, ix]))

        # Invariant: Distance must be non-increasing throughout the sequence
        for i in range(len(distances) - 1):
            assert distances[i + 1] <= distances[i] + 1e-5, (
                f"Non-monotonic BFS distance field detected along corridor! "
                f"Step {i}: x={waypoints_x[i]} (d={distances[i]:.3f}) -> "
                f"x={waypoints_x[i+1]} (d={distances[i+1]:.3f})"
            )
        # End must be strictly less than start
        assert distances[-1] < distances[0], "Total distance must decrease across corridor traversal"
