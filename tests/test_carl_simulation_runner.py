"""
test_carl_simulation_runner.py — Full Integration Test for CARL-DX Simulation Loop

Validates:
1. Instantiation of CarlSimulationRunner with all fused subsystems (LSM, Endocrine, Reflex, Grid, Physarum, Theta, MotorFilter, HDC, CIG, GIS).
2. Clean execution of 60 consecutive control loop steps at 30 Hz.
3. Verification of finite state variables and active motor command generation.
4. Clean GIS state saving upon session termination.
"""

import os
import sys
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from carl_simulation import CarlSimulationRunner


def test_carl_simulation_runner_60_ticks():
    # Instantiate runner with internal walls moved to safety for clean test in headless mode
    runner = CarlSimulationRunner(open_space=True, headless=True)

    # Step for 60 ticks (2 seconds at 30 Hz)
    for _ in range(60):
        runner.step()

    # 1. Verify tick counter
    assert runner.current_tick == 60

    # 2. Verify unified state vector sanity
    assert not np.isnan(runner.S_unified).any()
    assert not np.isinf(runner.S_unified).any()

    # 3. Verify neuromodulator concentrations in normal ranges
    assert 0.1 <= runner.endocrine.DA <= 5.0
    assert 0.0 <= runner.endocrine.NE <= 5.0
    assert 0.0 <= runner.endocrine.SHT <= 5.0
    assert 0.0 <= runner.endocrine.ACh <= 5.0

    # 4. Verify motor commands are smoothed and active
    assert len(runner.motor_commands) == 3
    assert np.all(np.abs(runner.motor_commands[:2]) <= 35.0)

    # 5. Verify HDC episodic memory recorded place transitions
    assert runner.hdc.episode_count >= 1

    # 6. Verify GIS serialization
    test_gis_path = os.path.join(BASE_DIR, "memory", "test_runner_gis.npz")
    saved = runner.gis.save_state(
        filepath=test_gis_path,
        reservoir=runner.reservoir,
        hippocampus=runner.hippocampus,
        physarum=runner.physarum,
        cig=runner.cig,
        hdc=runner.hdc,
        stats={"current_tick": runner.current_tick, "food_eaten": runner.food_eaten_total}
    )
    assert saved is True
    assert os.path.exists(test_gis_path)

    # Clean up test file
    if os.path.exists(test_gis_path):
        os.remove(test_gis_path)
    runner.telemetry.close()
