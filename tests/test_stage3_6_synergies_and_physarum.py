"""
tests/test_stage3_6_synergies_and_physarum.py — Stage 3.6 Unit & Pre-Registration Validation Suite
Classification: [STAGE 3.6 ACCEPTANCE SUITE] Behavioral Synergy Formation & Physarum Routing

Verifies:
1. Physarum dead-end & cul-de-sac hydraulic atrophy (Q=0 => dD/dt = -r*D).
2. Physarum target-inside-dead-end survival (user scenario: target in dead-end retains open conduit).
3. HDC D=2048 spatiotemporal trajectory encoding & associative cosine clustering.
4. Gate 7.1 Unsupervised Synergy Convergence (Variance Explained R^2 >= 0.820).
5. Gate 3 Smooth Bezier Slew-Rate Limiting (|Delta u| <= 0.08, zero jerk/wobble).
6. Gate 4 Real-time cycle latency budget (solve time <= 15.0 ms).
7. Gate 5 AST static decision pipeline quarantine (zero simulator coordinate leaks).
"""

import ast
import math
import os
import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brain.carl_physarum import CarlPhysarumRoutingEngine
from brain.carl_motor_synergies import CarlMotorSynergyEngine


def test_physarum_cul_de_sac_atrophy():
    """
    Validates that a cul-de-sac (dead-end) corridor with zero through-flux
    undergoes exponential conductivity atrophy and high hydraulic impedance.
    """
    engine = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4, decay_rate=0.30, dt=0.10)

    # Construct a U-shaped dead end in the upper half, with exit to the right
    # Arena grid: 32x32, center is (16, 16)
    # Walls surrounding dead end: left wall at j=10, right wall at j=22, back wall at i=25
    occ_grid = np.zeros((32, 32), dtype=np.float32)
    # Top back wall
    occ_grid[22, 10:22] = 1.0
    # Left wall
    occ_grid[10:23, 10] = 1.0
    # Right wall (leaves corridor open at bottom j in [11, 21])
    occ_grid[10:23, 21] = 1.0

    engine.update_occupancy(occ_grid, thresh=0.5)

    # Robot is inside the dead-end (center: 16, 16 -> world coords (0.0, 0.0))
    # Goal/Exit is outside the dead-end to the south-east (world coords (3.0, -3.0))
    src_pos = (0.0, 0.0)      # Inside cul-de-sac
    snk_pos = (3.0, -3.0)     # Outside open area

    # Step solver for 20 adaptation cycles
    for _ in range(20):
        engine.step(src_pos=src_pos, snk_pos=snk_pos)

    # Sample conductivity inside the closed back corner of the dead end (i=20, j=16)
    # versus the open corridor leading to the exit (i=8, j=25)
    d_dead_end = float(engine.D_h[20, 15])
    d_open = float(engine.D_h[8, 24])

    # Impedance inside dead-end must be substantially higher than in open channel
    z_dead_end = float(engine.impedance[20, 16])
    z_open = float(engine.impedance[8, 25])

    assert d_dead_end < d_open, f"Dead-end conductivity {d_dead_end} should be lower than open {d_open}"
    assert z_dead_end > z_open, f"Dead-end impedance {z_dead_end} should be higher than open {z_open}"

    # Verify topological current vector inside the cul-de-sac points downward (negative y) toward exit
    vx, vy, th_flow = engine.get_topological_current(0.0, 0.0)
    assert vy < 0.0 or th_flow < 0.0, f"Current vector vy={vy} should point south toward exit"


def test_physarum_target_in_dead_end_retains_conduit():
    """
    Validates user scenario: If the task/target is INSIDE the dead-end,
    the conduit to that target receives active flux (Q > 0) and stays reinforced.
    """
    engine = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4, decay_rate=0.25, dt=0.05)

    occ_grid = np.zeros((32, 32), dtype=np.float32)
    # U-shaped hallway
    occ_grid[22, 10:22] = 1.0
    occ_grid[10:23, 10] = 1.0
    occ_grid[10:23, 21] = 1.0
    engine.update_occupancy(occ_grid, thresh=0.5)

    # Robot is outside (0.0, -3.0)
    # Target is INSIDE the dead-end (0.0, 1.5)
    src_pos = (0.0, -3.0)
    snk_pos = (0.0, 1.5)

    for _ in range(15):
        engine.step(src_pos=src_pos, snk_pos=snk_pos)

    # Check conductivity along the path to the target inside the hallway
    gi, gj = engine.world_to_grid(0.0, 0.5)
    d_hallway = float(engine.D_v[gi, gj])

    # Path to target must NOT atrophy to d_min
    assert d_hallway > engine.d_min * 10.0, f"Target conduit atrophied prematurely: D={d_hallway}"
    assert engine.impedance[gi, gj] < 100.0, "Impedance to target should remain low and traversable"


def test_hdc_synergy_encoding_and_recall():
    """
    Validates that D=2048 spatiotemporal HDC encoding produces high cosine
    similarity for matched trajectories and low similarity for distinct ones.
    """
    engine = CarlMotorSynergyEngine(dimension=2048, horizon=15)

    # Trajectory A: Straight forward cruising
    traj_a = np.ones((15, 2), dtype=np.float32) * 0.80
    # Trajectory A_noisy: Slightly perturbed cruising
    traj_a_noisy = traj_a + np.random.randn(15, 2) * 0.04
    # Trajectory B: Pure left pivot
    traj_b = np.zeros((15, 2), dtype=np.float32)
    traj_b[:, 0] = -0.75
    traj_b[:, 1] = 0.75

    h_a = engine.encode_trajectory(traj_a)
    h_a_noisy = engine.encode_trajectory(traj_a_noisy)
    h_b = engine.encode_trajectory(traj_b)

    sim_same = float(np.dot(h_a, h_a_noisy))
    sim_diff = float(np.dot(h_a, h_b))

    assert sim_same > 0.80, f"Similar trajectories should have high cosine similarity: {sim_same}"
    assert sim_diff < 0.35, f"Orthogonal behaviors should have low cosine similarity: {sim_diff}"


def test_gate7_1_unsupervised_synergy_convergence():
    """
    Pre-Registered Gate 7.1:
    Verifies that K=3 self-organized HDC centroids explain >= 82% of trajectory variance
    across multi-phase continuous navigation traces without hardcoded templates.
    """
    engine = CarlMotorSynergyEngine(dimension=2048, num_synergies=3, horizon=15, learning_rate=0.20)

    # Generate synthetic diverse continuous trajectories
    rng = np.random.RandomState(123)
    dataset = []
    # 20 cruise variants
    for _ in range(20):
        spd = 0.60 + 0.30 * rng.rand()
        t = np.ones((15, 2), dtype=np.float32) * spd + rng.randn(15, 2) * 0.03
        dataset.append(t)
    # 20 arc curves
    for _ in range(20):
        diff = 0.30 + 0.30 * rng.rand()
        t = np.zeros((15, 2), dtype=np.float32)
        t[:, 0] = 0.80 - diff / 2
        t[:, 1] = 0.80 + diff / 2
        dataset.append(t + rng.randn(15, 2) * 0.03)
    # 20 pivots
    for _ in range(20):
        pspd = 0.50 + 0.35 * rng.rand()
        t = np.zeros((15, 2), dtype=np.float32)
        t[:, 0] = -pspd
        t[:, 1] = pspd
        dataset.append(t + rng.randn(15, 2) * 0.03)

    # Train HDC memory via online experience updates
    for traj in dataset:
        engine.update_online_experience(traj)

    r2 = engine.compute_variance_explained(dataset)
    assert r2 >= 0.820, f"Gate 7.1 FAILED: Variance explained {r2:.4f} < 0.820 threshold"


def test_gate3_bezier_slew_rate_limiting():
    """
    Pre-Registered Gate 3:
    Verifies that C^1 cubic Bezier ramp blending guarantees strict acceleration
    slew rate |Delta u| <= 0.08 under abrupt synergy switching (zero caster bounce).
    """
    engine = CarlMotorSynergyEngine(horizon=15, max_slew_rate=0.08)

    # Start at cruise (Centroid 0)
    engine.select_synergy(target_heading_err=0.0, obstacle_proximity=2.0)
    for _ in range(10):
        engine.step_smooth_blending()

    # Abruptly trigger emergency pivot (Centroid 2)
    engine.select_synergy(target_heading_err=2.5, obstacle_proximity=0.15, is_dead_end=True)

    max_delta = 0.0
    for _ in range(20):
        prev = engine.last_u.copy()
        curr = engine.step_smooth_blending()
        delta = float(np.max(np.abs(curr - prev)))
        if delta > max_delta:
            max_delta = delta

    assert max_delta <= 0.080001, f"Gate 3 FAILED: Slew rate {max_delta:.5f} exceeded 0.08 bound"


def test_gate4_physarum_solve_latency():
    """
    Pre-Registered Gate 4:
    Verifies that the Physarum sparse Poisson solver executes within the real-time budget
    (p95 <= 15.0 ms, mean <= 8.0 ms).
    """
    import time
    engine = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4)
    times = []

    for k in range(30):
        sx = float(np.sin(k * 0.2) * 2.0)
        sy = float(np.cos(k * 0.2) * 2.0)
        t0 = time.perf_counter()
        engine.step(src_pos=(sx, sy), snk_pos=(3.0, 3.0))
        times.append((time.perf_counter() - t0) * 1000.0)

    p95 = float(np.percentile(times, 95))
    mean_lat = float(np.mean(times))

    assert p95 <= 15.0, f"Gate 4 FAILED: p95 latency {p95:.2f} ms > 15.0 ms"
    assert mean_lat <= 8.0, f"Gate 4 FAILED: mean latency {mean_lat:.2f} ms > 8.0 ms"


def test_gate5_ast_decision_pipeline_isolation():
    """
    Pre-Registered Gate 5:
    Verifies that both Stage 3.6 modules contain ZERO forbidden simulator coordinates
    (qpos, qvel, geom_xpos, mj_ray).
    """
    forbidden_attrs = {"geom_xpos", "mj_ray", "qpos", "qvel", "qacc", "site_xpos"}
    target_files = [
        REPO_ROOT / "brain" / "carl_physarum.py",
        REPO_ROOT / "brain" / "carl_motor_synergies.py",
    ]

    for tf in target_files:
        assert tf.exists(), f"Missing file: {tf}"
        source = tf.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(tf))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_attrs, (
                    f"FORBIDDEN SIMULATOR ATTRIBUTE: '{node.attr}' in {tf.name} line {node.lineno}"
                )
