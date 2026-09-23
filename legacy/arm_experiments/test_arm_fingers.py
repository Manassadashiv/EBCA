"""
===============================================================================
  test_arm_fingers.py — UNIT TEST SUITE FOR CARL ARM & FINGER TRAINING
===============================================================================
  Tests reservoir arm readout initialization, analytical IK solver precision,
  tactile grip force compliance controller, FORCE/RLS weight updates, and weight
  saving/loading.
===============================================================================
"""

import os
import sys
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.carl_reservoir import LiquidStateReservoir
from train_carl_arm_fingers import solve_arm_ik, compute_tactile_grip


def test_reservoir_arm_readout_initialization():
    """Verify LiquidStateReservoir has 12 arm readout outputs and correct actuator names."""
    res = LiquidStateReservoir(N=100, M=37, K=3, seed=42)
    assert hasattr(res, "W_out_arm")
    assert res.W_out_arm.shape == (12, 100)
    assert len(res.ARM_ACTUATOR_NAMES) == 12
    assert len(res.ARM_CTRL_RANGES) == 12
    assert res.total_arm_rls_updates == 0


def test_predict_arm_and_fingers_clamping():
    """Verify predict_arm_and_fingers outputs a dict clamped to exact ctrlranges."""
    res = LiquidStateReservoir(N=100, M=37, K=3, seed=42)
    # Set arbitrary large weights
    res.W_out_arm = np.ones((12, 100)) * 5.0
    res.x = np.ones(100)
    
    preds = res.predict_arm_and_fingers()
    assert isinstance(preds, dict)
    assert len(preds) == 12
    
    for i, name in enumerate(res.ARM_ACTUATOR_NAMES):
        min_val, max_val = res.ARM_CTRL_RANGES[i]
        val = preds[name]
        assert min_val <= val <= max_val, f"{name} output {val} out of bounds [{min_val}, {max_val}]"


def test_analytical_ik_solver_bounds():
    """Verify analytical IK solver outputs stay strictly within physical MuJoCo joint limits."""
    targets = [
        (0.20, 0.05, 0.02),
        (0.30, -0.10, 0.15),
        (0.15, 0.12, 0.25),
        (0.35, 0.0, 0.05)
    ]
    for x, y, z in targets:
        for side in ["L", "R"]:
            s_yaw, s_pitch, elbow, wrist = solve_arm_ik(x, y, z, side=side)
            assert -1.57 <= s_yaw <= 1.57
            assert -2.0 <= s_pitch <= 2.0
            assert -2.44 <= elbow <= 0.0
            assert -1.57 <= wrist <= 1.57


def test_tactile_grip_compliance():
    """Verify closed-loop tactile force compliance controller behavior."""
    target_grip = 0.45
    
    # 1. No contact -> increases grip
    g1 = compute_tactile_grip(touch_val=0.0, target_grip=target_grip, current_grip=0.10)
    assert g1 > 0.10
    
    # 2. Optimal contact -> maintains grip
    g2 = compute_tactile_grip(touch_val=0.35, target_grip=target_grip, current_grip=0.25)
    assert g2 == 0.25
    
    # 3. High contact -> relaxes grip slightly to protect hardware
    g3 = compute_tactile_grip(touch_val=0.90, target_grip=target_grip, current_grip=0.30)
    assert g3 < 0.30


def test_arm_rls_updates_and_weight_persistence(tmp_path):
    """Verify FORCE/RLS updates reduce prediction error and weights save/load correctly."""
    res = LiquidStateReservoir(N=100, M=37, K=3, seed=42)
    u_sensory = np.random.randn(37)
    res.step(u_sensory)
    
    y_target = np.array([0.2, 0.4, -0.8, 0.0, 0.3, 0.3, -0.2, 0.4, -0.8, 0.0, 0.3, 0.3])
    
    initial_err = np.linalg.norm(y_target - res.W_out_arm @ res.x)
    for _ in range(20):
        res.rls_update_arm(y_target)
    
    final_err = np.linalg.norm(y_target - res.W_out_arm @ res.x)
    assert final_err < initial_err, f"RLS failed to converge: initial={initial_err}, final={final_err}"
    assert res.total_arm_rls_updates == 20
    
    # Test saving and loading weights
    save_file = str(tmp_path / "carl_arm_test_weights.npz")
    res.save_arm_weights(save_file)
    assert os.path.exists(save_file)
    
    res2 = LiquidStateReservoir(N=100, M=37, K=3, seed=42)
    success = res2.load_arm_weights(save_file)
    assert success is True
    assert res2.total_arm_rls_updates == 20
    np.testing.assert_array_almost_equal(res.W_out_arm, res2.W_out_arm)


def test_industrial_motor_filter_velocity_limit():
    """Verify IndustrialMotorFilter strictly enforces max velocity rate limits."""
    from brain.carl_motor_filter import IndustrialMotorFilter
    
    filt = IndustrialMotorFilter(num_actuators=10, max_velocity=2.0, dt=0.033)
    filt.reset(np.zeros(10))
    
    # Input huge step target
    step_target = np.ones(10) * 10.0
    out = filt.filter_step(step_target)
    
    # Velocity step should not exceed max_velocity * dt = 2.0 * 0.033 = 0.066 rad
    diff = np.max(np.abs(out))
    assert diff <= 0.07, f"Velocity limit exceeded: step diff {diff} > 0.07"


def test_minimum_jerk_trajectory_smoothness():
    """Verify minimum-jerk trajectory starts at p_start, ends at p_end, and has zero end velocities."""
    from brain.carl_motor_filter import IndustrialMotorFilter
    
    p0, v0, a0 = IndustrialMotorFilter.minimum_jerk_trajectory(0.0, 1.5, 0.0, 2.0)
    p_mid, v_mid, a_mid = IndustrialMotorFilter.minimum_jerk_trajectory(0.0, 1.5, 1.0, 2.0)
    p1, v1, a1 = IndustrialMotorFilter.minimum_jerk_trajectory(0.0, 1.5, 2.0, 2.0)
    
    assert p0 == 0.0 and v0 == 0.0
    assert p1 == 1.5 and v1 == 0.0
    assert 0.70 < p_mid < 0.80  # S-curve midpoint is 0.75
    assert v_mid > 0.0  # Peak velocity at midpoint

