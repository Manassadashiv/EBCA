"""
tests/test_stage3_5_endocrine_adaptation.py — Verification Suite for Stage 3.5 Neuromorphic Endocrine & Slip Adaptation Engine
"""

import math
import numpy as np
import pytest

from brain.carl_endocrine_adaptation import CarlEndocrineAdaptationEngine


def test_slip_estimation_and_campaniform_choke():
    """
    Verifies that when wheels spin faster than forward chassis progress,
    the slip estimator triggers and the Campaniform Sensilla choke reflex
    throttles the motor command within the same 30ms cycle.
    """
    engine = CarlEndocrineAdaptationEngine(dt=0.030, slip_threshold=0.18, k_choke=0.65)
    engine.reset()

    # Case 1: Perfect traction (no slip)
    # cmd=0.80 -> omega_exp = 0.80 * 25.0 = 20.0 rad/s
    # v_wheel = 20.0 rad/s * 0.048m = 0.96 m/s; v_est = 0.96 m/s
    cmd = np.array([0.80, 0.80], dtype=np.float64)
    adapted, telem = engine.update_and_adapt(
        cmd_u=cmd, w_left_vel=20.0, w_right_vel=20.0, gyro_yaw_rate=0.0, v_est=0.96
    )
    assert telem["mean_slip"] == pytest.approx(0.0, abs=1e-3)
    assert not telem["reflex_active"]
    assert adapted[0] == pytest.approx(0.80, abs=1e-3)

    # Case 2: Severe wheel spin on ice patch (v_wheel = 0.96 m/s, but chassis v_est is only 0.10 m/s)
    adapted_ice, telem_ice = engine.update_and_adapt(
        cmd_u=cmd, w_left_vel=20.0, w_right_vel=20.0, gyro_yaw_rate=0.0, v_est=0.10
    )
    # Expected slip ratio: (0.96 - 0.10) / 0.96 = 0.8958 > 0.18 threshold
    assert telem_ice["mean_slip"] > 0.70
    assert telem_ice["reflex_active"]
    # Wheel command should be choked by ~50%
    assert adapted_ice[0] < 0.55
    assert adapted_ice[1] < 0.55


def test_endocrine_hormonal_kinetics_decay():
    """
    Verifies dual-timescale hormone accumulation during distress and smooth decay over seconds:
    - [NE] rises fast (tau = 1.0s).
    - [Cortisol] accumulates steadily and persists longer (tau = 2.5s).
    """
    engine = CarlEndocrineAdaptationEngine(dt=0.030, tau_ne=1.0, tau_cort=2.5)
    engine.reset()

    cmd = np.array([0.80, 0.80], dtype=np.float64)

    # Apply 20 ticks of slipping on ice
    for _ in range(20):
        engine.update_and_adapt(
            cmd_u=cmd, w_left_vel=12.0, w_right_vel=12.0, gyro_yaw_rate=0.0, v_est=0.05
        )

    ne_peak = engine.ne_level
    cort_peak = engine.cortisol_level
    assert ne_peak > 0.40, f"Expected elevated NE, got {ne_peak}"
    assert cort_peak > 0.30, f"Expected elevated Cortisol, got {cort_peak}"

    # Active inference modulation should reflect alertness and caution
    mods = engine.get_active_inference_modulation()
    assert mods["sigma_scale"] > 1.20   # Higher exploration variance
    assert mods["margin_scale"] > 1.15  # Wider obstacle margins
    assert mods["cruise_scale"] < 0.90  # Reduced cruise speed

    # Now drive on normal dry ground for 100 ticks (3.0 seconds) -> hormones should decay smoothly
    for _ in range(100):
        engine.update_and_adapt(
            cmd_u=cmd, w_left_vel=10.0, w_right_vel=10.0, gyro_yaw_rate=0.0, v_est=0.48
        )

    assert engine.ne_level < 0.10, f"NE did not decay as expected: {engine.ne_level}"
    assert engine.cortisol_level < cort_peak * 0.50, f"Cortisol did not decay: {engine.cortisol_level}"


def test_torque_asymmetry_disturbance_observer():
    """
    Verifies that when motor torque asymmetry induces uncommanded yaw drift,
    the observer applies trim compensation with dead-band gating.
    """
    engine = CarlEndocrineAdaptationEngine(dt=0.030)
    engine.reset()

    # Commanded straight drive [0.70, 0.70], but physical robot drifts left at +0.30 rad/s
    cmd = np.array([0.70, 0.70], dtype=np.float64)

    for _ in range(30):
        adapted, telem = engine.update_and_adapt(
            cmd_u=cmd, w_left_vel=7.0, w_right_vel=10.0, gyro_yaw_rate=0.30, v_est=0.40
        )

    # Observer should have built up positive trim to counteract the drift
    assert telem["torque_trim"] > 0.15, f"Expected torque trim, got {telem['torque_trim']}"
    # Left wheel should be boosted and right wheel throttled to steer back right
    assert adapted[0] > cmd[0]
    assert adapted[1] < cmd[1]


def test_ast_compliance_endocrine_engine():
    """Verifies that carl_endocrine_adaptation.py contains 0 simulator leaks."""
    import ast
    from pathlib import Path

    file_path = Path("brain/carl_endocrine_adaptation.py")
    tree = ast.parse(file_path.read_text(encoding="utf-8"))

    forbidden = {"mujoco", "qpos", "qvel", "geom_xpos", "mj_ray"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden
