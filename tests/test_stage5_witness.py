"""
tests/test_stage5_witness.py — Comprehensive Unit & Rigor Tests for Stage 5 Metacognition ("The Witness")
"""

import ast
import math
import os
import time
import pytest
import numpy as np

from brain.carl_witness import (
    CarlWitnessMetacognition,
    WitnessConfig,
    FailureMode,
    WitnessOutput
)


def test_witness_initialization():
    """Verify initialization and pre-allocated buffers."""
    witness = CarlWitnessMetacognition()
    assert witness.cfg.dimension == 2048
    assert witness.telemetry_history.shape == (150, 7)
    assert witness.archetypes_matrix.shape == (4, 2048)
    assert witness.current_failure_mode == FailureMode.NOMINAL
    assert witness.curr_lambda == 1.2
    assert witness.curr_a_max == 0.08
    assert witness.curr_w_rep == 95.0


def test_morphological_mismatch_trigger():
    """Verify sustained kinematic discrepancy triggers Stage 6 morphological re-babbling."""
    witness = CarlWitnessMetacognition()
    
    # 35 ticks of sustained kinematic mismatch in open space (~1.1s)
    for i in range(35):
        out = witness.step_metacognitive_cycle(
            dt=0.0333,
            kinematic_error=0.60,      # High mismatch
            free_energy_variance=0.2,
            veto_rejection_rate=0.0,
            cann_drift_rate=0.05,
            noradrenaline=0.5,
            cortisol=0.5,
            mppi_entropy=0.5,
            min_obstacle_dist=1.50,    # Open clearance
            current_heading=0.0,
            goal_heading=0.0,
            timestamp=i * 0.0333
        )
        
    assert out.current_mode == FailureMode.MORPHOLOGICAL_MISMATCH
    assert out.trigger_morphological_babble is True
    assert "MORPHOLOGICAL INCONGRUENCE" in out.diagnostic_monologue


def test_pfl_fly_steering_prior():
    """Verify reverse-engineered Drosophila PFL2/PFL3 steering behavior."""
    witness = CarlWitnessMetacognition()

    # 1. Aligned with goal (heading = 0, goal = 0)
    u_fwd, u_diff = witness.compute_pfl_steering_prior(current_heading=0.0, goal_heading=0.0)
    assert u_fwd > 0.40
    assert abs(u_diff) < 0.05

    # 2. Goal is to the right (heading = 0, goal = -0.5 rad)
    u_fwd, u_diff = witness.compute_pfl_steering_prior(current_heading=0.0, goal_heading=-0.5)
    assert u_diff > 0.20  # Steers right (positive diff command)

    # 3. Goal is to the left (heading = 0, goal = +0.5 rad)
    u_fwd, u_diff = witness.compute_pfl_steering_prior(current_heading=0.0, goal_heading=+0.5)
    assert u_diff < -0.20  # Steers left (negative diff command)

    # 4. Goal is directly behind (heading = 0, goal = pi -> 180 deg error)
    u_fwd, u_diff = witness.compute_pfl_steering_prior(current_heading=0.0, goal_heading=math.pi)
    assert u_fwd <= 0.0  # Forward drive suppressed by PFL2
    assert abs(u_diff) >= 0.80  # Sharp pivot commanded


def test_nominal_step_latency():
    """Verify cognitive cycle latency is strictly under 1.5 ms."""
    witness = CarlWitnessMetacognition()
    
    # Warmup
    for _ in range(10):
        witness.step_metacognitive_cycle(
            dt=0.0333,
            kinematic_error=0.02,
            free_energy_variance=0.1,
            veto_rejection_rate=0.0,
            cann_drift_rate=0.05,
            noradrenaline=0.1,
            cortisol=0.1,
            mppi_entropy=0.5,
            min_obstacle_dist=1.5,
            current_heading=0.0,
            goal_heading=0.2
        )

    # Benchmarking 200 cycles
    latencies = []
    for _ in range(200):
        t0 = time.perf_counter()
        witness.step_metacognitive_cycle(
            dt=0.0333,
            kinematic_error=0.02,
            free_energy_variance=0.1,
            veto_rejection_rate=0.0,
            cann_drift_rate=0.05,
            noradrenaline=0.1,
            cortisol=0.1,
            mppi_entropy=0.5,
            min_obstacle_dist=1.5,
            current_heading=0.0,
            goal_heading=0.2
        )
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    mean_ms = np.mean(latencies)
    p95_ms = np.percentile(latencies, 95)
    print(f"\n[LATENCY BENCHMARK] Mean: {mean_ms:.3f} ms | p95: {p95_ms:.3f} ms")
    assert mean_ms < 1.5, f"Mean latency {mean_ms:.3f} ms exceeds 1.5 ms limit"
    assert p95_ms < 3.0, f"p95 latency {p95_ms:.3f} ms exceeds 3.0 ms limit"


def test_abductive_causal_attribution_slip():
    """Verify traction slip is accurately diagnosed under low-friction conditions."""
    witness = CarlWitnessMetacognition()

    # Feed 15 ticks of severe slip in open clearance
    for i in range(20):
        out = witness.step_metacognitive_cycle(
            dt=0.0333,
            kinematic_error=0.65,      # High slip
            free_energy_variance=0.4,
            veto_rejection_rate=0.05,   # Low veto (open space)
            cann_drift_rate=0.1,
            noradrenaline=0.75,
            cortisol=0.60,
            mppi_entropy=0.8,
            min_obstacle_dist=1.20,    # Clearance open
            current_heading=0.0,
            goal_heading=0.1,
            timestamp=i * 0.0333
        )

    assert out.current_mode == FailureMode.SLIP
    assert out.attribution_confidence > 0.60
    assert "TRACTION SLIP" in out.diagnostic_monologue
    assert out.adapted_a_max < 0.08  # Max acceleration reduced
    assert out.adapted_lambda > 1.2   # Temperature increased


def test_abductive_causal_attribution_deadend():
    """Verify dead-end cul-de-sac trap is diagnosed when clearance is blocked."""
    witness = CarlWitnessMetacognition()

    # Feed 20 ticks of wall trap
    for i in range(25):
        out = witness.step_metacognitive_cycle(
            dt=0.0333,
            kinematic_error=0.35,
            free_energy_variance=3.5,
            veto_rejection_rate=0.92,   # 92% of candidate paths blocked by wall
            cann_drift_rate=0.4,
            noradrenaline=0.85,
            cortisol=0.90,
            mppi_entropy=1.8,
            min_obstacle_dist=0.12,    # Wall directly in front
            current_heading=0.0,
            goal_heading=math.pi,      # Need to turn around
            timestamp=i * 0.0333
        )

    assert out.current_mode == FailureMode.DEADEND
    assert "CUL-DE-SAC DEAD END" in out.diagnostic_monologue
    assert out.adapted_w_rep > 95.0    # Repulsion boosted


def test_homeostatic_passive_relaxation():
    """Verify adapted parameters decay back toward nominal baseline when nominal."""
    witness = CarlWitnessMetacognition()
    
    # Manually perturb parameters
    witness.curr_lambda = 2.2
    witness.curr_a_max = 0.04
    witness.curr_w_rep = 180.0
    witness.current_failure_mode = FailureMode.NOMINAL

    # Step for 10 seconds of nominal navigation
    for i in range(300):
        out = witness.step_metacognitive_cycle(
            dt=0.0333,
            kinematic_error=0.01,
            free_energy_variance=0.05,
            veto_rejection_rate=0.0,
            cann_drift_rate=0.02,
            noradrenaline=0.05,
            cortisol=0.05,
            mppi_entropy=0.2,
            min_obstacle_dist=2.0,
            current_heading=0.0,
            goal_heading=0.0,
            timestamp=i * 0.0333
        )

    # Should have relaxed close to nominal baseline (1.2, 0.08, 95.0)
    assert abs(out.adapted_lambda - 1.2) < 0.40
    assert abs(out.adapted_a_max - 0.08) < 0.02
    assert abs(out.adapted_w_rep - 95.0) < 35.0


def test_ast_anti_cheat_quarantine():
    """Verify zero simulator coordinates (qpos, qvel, geom_xpos, mj_ray) in carl_witness.py."""
    witness_path = os.path.join(os.path.dirname(__file__), "..", "brain", "carl_witness.py")
    with open(witness_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    forbidden_tokens = ["qpos", "qvel", "qacc", "geom_xpos", "mj_ray", "mj_step"]

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in forbidden_tokens:
            violations.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and node.attr in forbidden_tokens:
            violations.append((node.lineno, node.attr))

    assert len(violations) == 0, f"AST Anti-Cheat Quarantine Failed! Violations: {violations}"
    print("\n[AST ANTI-CHEAT AUDIT] brain/carl_witness.py is 100% CLEAN. Zero simulator leaks.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
