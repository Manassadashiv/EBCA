"""
===============================================================================
  test_curiosity_curriculum.py — UNIT TEST SUITE FOR 3-FINGER MPPI ARCHITECTURE
===============================================================================
  Verifies:
  1. 12-Actuator 3-Finger Tripod Grippers.
  2. 1,000-Sample GPU MPPI Tensor Fusion.
  3. Weight Matrix Shape Migration (10 -> 12 actuators).
  4. Surprise Estimator δ(t) and Residual Torque Compensator.
===============================================================================
"""

import os
import pytest
import numpy as np

from brain.carl_reservoir import LiquidStateReservoir
from brain.carl_endocrine import EndocrineSystem
from brain.carl_mppi import MPPIParallelEngine
from brain.carl_mpc import SurpriseNoiseEstimator, ResidualTorqueCompensator
from brain.carl_osc_dmp import OperationalSpaceController, DynamicMovementPrimitive
from train_carl_curiosity_curriculum import solve_3finger_arm_ik


def test_12_actuator_reservoir_initialization():
    reservoir = LiquidStateReservoir(N=500, K=14)
    assert reservoir.K_arm == 12, "Reservoir K_arm must be 12 for 3-finger tripod grippers"
    assert len(reservoir.ARM_ACTUATOR_NAMES) == 12, "Must have 12 ARM_ACTUATOR_NAMES"
    assert len(reservoir.ARM_CTRL_RANGES) == 12, "Must have 12 ARM_CTRL_RANGES"


def test_weight_matrix_shape_migration(tmp_path):
    reservoir = LiquidStateReservoir(N=500, K=14)
    old_weights_path = os.path.join(tmp_path, "old_10_actuators.npz")
    
    # Save a legacy 10-actuator weight matrix
    old_W = np.ones((10, 500))
    np.savez(old_weights_path, W_out_arm=old_W)
    
    # Load into 12-actuator reservoir and verify auto-migration
    res = reservoir.load_arm_weights(old_weights_path)
    assert res is True
    assert reservoir.W_out_arm.shape == (12, 500), "Weight matrix must auto-migrate to shape (12, 500)"


def test_mppi_gpu_tensor_optimization():
    mppi = MPPIParallelEngine(num_samples=1000, horizon=50)
    current_q = np.zeros(12)
    target_q = np.zeros(12)
    target_3d = np.array([0.22, 0.0, 0.015])
    
    u_optimal = mppi.optimize_trajectory(current_q, target_q, target_3d, {"DA": 1.0, "NE": 0.1})
    assert u_optimal.shape == (12,), "Optimal MPPI control vector must have shape (12,)"
    assert not np.isnan(u_optimal).any(), "MPPI output must not contain NaNs"


def test_surprise_estimator_and_residual_compensator():
    surprise_est = SurpriseNoiseEstimator(surprise_threshold=0.015)
    compensator = ResidualTorqueCompensator(kp=15.0, kd=1.2)
    
    actual = np.zeros(12)
    predicted = np.ones(12) * 0.02
    
    delta = surprise_est.compute_surprise(actual, predicted)
    assert delta > 0.0, "Surprise delta must be positive"
    
    corr = compensator.compute_residual_correction(actual, predicted)
    assert corr.shape == (12,), "Residual correction vector must have shape (12,)"


def test_3finger_analytical_ik():
    s_yaw, s_pitch, elbow, wrist = solve_3finger_arm_ik(0.22, 0.0, 0.015, "L")
    assert -0.52 <= s_yaw <= 1.57, "Left shoulder yaw within joint limits"
    assert -1.8 <= s_pitch <= 1.8, "Shoulder pitch within forward-down joint limits"
    assert -2.44 <= elbow <= 0.0, "Elbow angle within flexion joint limits"
