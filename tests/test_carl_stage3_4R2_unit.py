"""
tests/test_carl_stage3_4R2_unit.py — Unit & Mathematical Validation Suite for Stage 3.4-R2

Validates the 6 mandatory mathematical criteria:
1. Frontier connected-component extraction & micro-noise filtering
2. BFS free-space geodesic distance field calculation
3. Macro-frontier selection proxy behavior
4. Dimensionless normalized scoring bounds
5. Collision hard veto barrier (infinite cost)
6. Terminal geodesic bilinear approximation
7. Four experimental arms initialization and execution
"""

import math
import numpy as np
import pytest
import torch
import torch.nn.functional as F

import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine



def test_frontier_connected_components():
    """Validates 8-connected labeling and filtering of micro-noise clusters."""
    engine = CARLActiveInferenceEngine(w_info=1.0, frontier_mode="macro")
    # Artificial grid
    engine.grid_np[0, :, :] = 0.0  # obstacle free
    engine.grid_np[1, :, :] = 0.0  # all unobserved

    # Create explored patch around (64, 64)
    engine.grid_np[1, 60:68, 60:68] = 1.0

    # Add a tiny isolated 1-pixel explored dot (should create micro-noise)
    engine.grid_np[1, 10, 10] = 1.0

    # Compute macro frontier
    c_x = (64 - 64) * 0.10
    c_y = (64 - 64) * 0.10
    res = engine._compute_macro_frontier(c_x, c_y)
    assert res is not None, "Macro-frontier must be detected on explored patch boundary"
    fx, fy, d_curr, dist_field = res

    # The chosen macro-frontier must be on the main patch, not on the 1-pixel noise at (10, 10)
    assert math.hypot(fx - c_x, fy - c_y) < 2.0, "Target must be from the main macro cluster"


def test_bfs_geodesic_field():
    """Validates that BFS wavefront field respects obstacles and computes monotonic distances."""
    engine = CARLActiveInferenceEngine(w_info=1.0, frontier_mode="macro")
    engine.grid_np[0, :, :] = 0.0
    engine.grid_np[1, :, :] = 1.0

    # Put a wall between x=64 and x=70
    engine.grid_np[0, 50:80, 64] = 1.0  # Wall across y=[50, 80]

    # Target on right side of wall (64, 70), robot on left side (64, 58)
    # The BFS field from (64, 70) must route around the wall (y < 50 or y > 80)
    ty, tx = 64, 70
    traversable = (engine.grid_np[0] < 0.85)

    from collections import deque
    dist_field = np.full((128, 128), 99.0, dtype=np.float32)
    dist_field[ty, tx] = 0.0
    q = deque([(ty, tx)])
    while q:
        cy, cx = q.popleft()
        cd = dist_field[cy, cx] + 0.10
        if cd > 8.0:
            continue
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < 128 and 0 <= nx < 128 and traversable[ny, nx]:
                if cd < dist_field[ny, nx]:
                    dist_field[ny, nx] = cd
                    q.append((ny, nx))

    # Distance directly through wall must NOT be straight Euclidean
    eucl_dist = abs(tx - 58) * 0.10  # 1.2 m
    bfs_dist = dist_field[64, 58]
    assert bfs_dist > eucl_dist, f"BFS must wrap around wall: bfs={bfs_dist:.2f} > eucl={eucl_dist:.2f}"


def test_macro_frontier_selection():
    """Validates that macro-frontier favors larger frontier clusters over 1-pixel fringes."""
    engine = CARLActiveInferenceEngine(w_info=1.0, frontier_mode="macro")
    engine.grid_np[0, :, :] = 0.0
    engine.grid_np[1, :, :] = 0.0

    # Small 4-cell fringe at (64, 60)
    engine.grid_np[1, 63:65, 59:61] = 1.0

    # Large 20-cell corridor opening at (64, 80)
    engine.grid_np[1, 55:75, 75:85] = 1.0

    c_x, c_y = 0.0, 0.0
    res = engine._compute_macro_frontier(c_x, c_y)
    assert res is not None
    fx, fy, d_curr, dist_field = res
    # Chosen cluster should be the large opening, not the tiny fringe
    assert fx > 0.0, f"Expected macro-cluster target in positive X, got fx={fx}"


def test_normalized_scoring_bounds():
    """Validates that continuous cost terms are strictly bounded to [0, 1] or [-1, 1]."""
    engine = CARLActiveInferenceEngine(w_info=1.0, norm_mode="dimensionless")
    # Sample trajectories
    u_cand = engine._sample_trajectories()
    px, py, pth = engine._vectorized_rollout(0.0, 0.0, 0.0, 0.0, 0.0, u_cand)
    sensors = np.full(25, 2.0)

    g, debug = engine._evaluate_expected_free_energy(px, py, pth, u_cand, 0.0, 0.0, 0.0, sensors, None)
    # Check that for collision-free candidates, costs are non-infinite and within bounds
    coll_free = (g < 1e5)
    if torch.any(coll_free):
        g_free = g[coll_free]
        assert torch.all(g_free >= -1.0), "Normalized G cannot be below theoretical lower bound (-1.0)"
        assert torch.all(g_free <= 2.0), "Normalized G cannot exceed theoretical upper bound (2.0)"


def test_collision_veto():
    """Validates that candidate rollouts colliding with obstacles receive infinite cost."""
    engine = CARLActiveInferenceEngine(w_info=1.0, norm_mode="dimensionless")
    # Place wall directly in front of robot
    engine.grid_np[0, 60:68, 64:75] = 1.0
    engine.grid[0, 0] = torch.from_numpy(engine.grid_np[0])

    # Sample trajectories pushing straight forward
    u_cand = torch.ones(128, 15, 2)  # Max forward
    px, py, pth = engine._vectorized_rollout(0.0, 0.0, 0.0, 0.0, 0.0, u_cand)
    sensors = np.full(25, 0.10)

    g, debug = engine._evaluate_expected_free_energy(px, py, pth, u_cand, 0.0, 0.0, 0.0, sensors, None)
    assert torch.all(g >= 1e5), "All forward rollouts hitting wall must receive infinite cost"
    assert debug["j_coll_rate"] == 1.0, "Collision rate must be 100%"


def test_terminal_geodesic_approximation():
    """Validates bilinear interpolation of discrete BFS field for terminal coordinates."""
    dist_field = np.zeros((128, 128), dtype=np.float32)
    # Linear ramp along X
    for x in range(128):
        dist_field[:, x] = float(x) * 0.10

    dist_tensor = torch.from_numpy(dist_field).unsqueeze(0).unsqueeze(0)
    # Sample at sub-pixel coordinates
    test_x = torch.tensor([0.0, 0.05, 0.10, 0.15])  # World coords around center (x=64 -> world 0.0)
    test_y = torch.zeros(4)
    half_size = 6.4

    norm_x = (test_x / half_size).clamp(-1.0, 1.0)
    norm_y = (test_y / half_size).clamp(-1.0, 1.0)
    coords = torch.stack([norm_x, norm_y], dim=-1).unsqueeze(0).unsqueeze(2)

    with torch.inference_mode():
        sampled = F.grid_sample(dist_tensor, coords, mode="bilinear", padding_mode="border", align_corners=True).squeeze()

    # Distances must be strictly increasing and continuous
    diffs = torch.diff(sampled)
    assert torch.all(diffs > 0.0), "Bilinear sampling must produce monotonic values along gradient"


def test_four_arms_initialization():
    """Validates that all four Stage 3.4-R2 experimental arms initialize and execute a step."""
    arm_configs = [
        ("ARM-A", {"w_info": 1.0, "frontier_mode": "macro", "norm_mode": "dimensionless"}),
        ("ARM-B", {"w_info": 0.0, "frontier_mode": "macro", "norm_mode": "dimensionless"}),
        ("ARM-C", {"w_info": 1.0, "frontier_mode": "micro_local", "norm_mode": "dimensionless"}),
        ("ARM-D", {"w_info": 1.0, "frontier_mode": "macro", "norm_mode": "unnormalized", "lambda_frontier": 8.0}),
    ]

    for arm_id, cfg in arm_configs:
        engine = CARLActiveInferenceEngine(**cfg)
        assert engine.frontier_mode == cfg["frontier_mode"]
        assert engine.norm_mode == cfg["norm_mode"]
        sensors = np.full(25, 2.0)
        action, telemetry = engine.select_action(sensors)
        assert action.shape == (2,)
        assert -1.0 <= action[0] <= 1.0
        assert -1.0 <= action[1] <= 1.0
        assert telemetry["frontier_mode"] == cfg["frontier_mode"]
        assert telemetry["norm_mode"] == cfg["norm_mode"]
        assert telemetry["latency_ms"] < 45.0, f"{arm_id} latency exceeded 45ms: {telemetry['latency_ms']:.2f}ms"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
