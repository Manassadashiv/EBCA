"""
test_physarum_and_omega.py — Unit Tests for Physarum, Theta Gate, Allostasis, and IndustrialMotorFilter

Validates:
1. PhysarumPolycephalum shortest-route harmonic pressure solver and obstacle avoidance.
2. ThetaGate 6 Hz phase progression, learning lambda scaling, and ACh exploration boost.
3. PredictiveAllostasis forward stress prediction.
4. IndustrialMotorFilter EMA smoothing, acceleration rate clamping, and velocity limiting.
"""

import os
import sys
import math
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.carl_physarum import PhysarumMaze
from brain.carl_omega_extensions import ThetaGate, PredictiveAllostasis
from brain.carl_motor_filter import IndustrialMotorFilter


def test_physarum_solver_and_heading():
    phys = PhysarumMaze(rows=10, cols=10)

    # Put an obstacle at (5, 5)
    danger_map = np.zeros((10, 10))
    danger_map[5, 5] = 0.95
    phys.update_obstacles(danger_map, danger_thresh=0.7)
    assert bool(phys.obstacle[5, 5]) is True

    # Step solver from (0, 0) to (9, 9)
    phys.step(src_cell=(0, 0), snk_cell=(9, 9))
    assert phys.pressure[0] > 0.5   # Source pressure near 1.0
    assert phys.pressure[-1] < 0.1  # Sink pressure near 0.0

    # Heading generation in world coordinates
    heading = phys.get_heading(xw=-4.0, yw=-4.0, goal_xw=4.0, goal_yw=4.0,
                               MAP_XMIN=-5.0, MAP_XMAX=5.0, MAP_YMIN=-5.0, MAP_YMAX=5.0)
    assert isinstance(heading, float)
    assert not math.isnan(heading)


def test_theta_gate_and_allostasis():
    tg = ThetaGate(freq_hz=6.0)
    assert 0.0 <= tg.gate <= 1.0

    # Step 10 ticks (0.33s = ~2 full 6Hz cycles)
    phases = []
    gates = []
    for _ in range(10):
        tg.step(0.033)
        phases.append(tg.phase)
        gates.append(tg.gate)

    assert max(gates) > min(gates)
    assert 0.970 <= tg.learning_lambda() <= 0.999
    assert tg.explore_boost(nm_ACh=0.8) >= 1.0

    # Predictive Allostasis
    allo = PredictiveAllostasis(sdim=5, horizon=10)
    allo.update(actual_load=0.4)
    assert allo.anticipatory_avoidance_cost() >= 0.0


def test_industrial_motor_filter():
    filter_mod = IndustrialMotorFilter(
        num_actuators=3, max_velocity=20.0, max_acceleration=50.0, alpha_ema=0.3, dt=0.033
    )
    filter_mod.reset(np.zeros(3))

    # Step input from 0 to 30.0 (violates max velocity and max acceleration)
    raw_step = np.array([30.0, 30.0, 1.0])
    smoothed = filter_mod.filter_step(raw_step)

    # First step should be smoothly rate-limited
    assert smoothed[0] < 30.0
    assert filter_mod.current_vel[0] <= filter_mod.max_vel
    assert filter_mod.current_vel[0] <= filter_mod.max_accel * 0.033 + 1e-5

    # Run for 50 ticks, should asymptotically reach target
    for _ in range(50):
        smoothed = filter_mod.filter_step(raw_step)
    assert np.allclose(smoothed, raw_step, atol=0.1)
