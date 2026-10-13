"""
tests/test_stage3_deliberation_regression.py — Stage 3 Default MPPI & Discrete Backend Regression Suite
Classification: [STAGE 3.4 ARCHITECTURAL INTEGRATION GATE 11]

Verifies:
1. Default deliberation_mode="mppi" preserves exact canonical behavioral substrate.
2. Underlying engine is CARLStage3_3MPPIDeliberationEngine with M=128, H=15, exact dt.
3. Candidate count, horizon, action dimensionality, and bounds remain strictly unmutated.
4. Discrete deliberation mode ("discrete") remains constructible and operable.
"""

import numpy as np
import pytest

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage1_hal import CarlStage1HAL


def test_default_mppi_deliberation_preservation():
    """Verifies default deliberation_mode="mppi" preserves all architectural invariants."""
    hal = CarlStage1HAL(headless=True)
    agent = CarlAutonomousOrganismAgent(dt=hal.dt)

    # 1. Deliberation mode default verification
    assert agent.deliberation_mode == "mppi", f"Expected default mode 'mppi', got '{agent.deliberation_mode}'"

    # 2. Engine class identity
    assert isinstance(agent.deliberation, CARLStage3_3MPPIDeliberationEngine), (
        f"Expected CARLStage3_3MPPIDeliberationEngine, got {type(agent.deliberation)}"
    )

    # 3. Parameter invariance
    engine = agent.deliberation
    assert engine.M == 128, f"Candidate count mutated: expected 128, got {engine.M}"
    assert engine.horizon == 15, f"Horizon mutated: expected 15, got {engine.horizon}"
    assert abs(engine.dt - hal.dt) < 1e-6, f"dt mutated: expected {hal.dt}, got {engine.dt}"
    assert engine.mode == "mppi"

    # 4. Action interface & execution
    agent.initialize_spatial_grounding(0.0, 0.0, 0.0)
    cycle_res = agent.step_cognitive_cycle(hal)

    assert "cmd_L" in cycle_res and "cmd_R" in cycle_res
    assert -1.0 <= cycle_res["cmd_L"] <= 1.0
    assert -1.0 <= cycle_res["cmd_R"] <= 1.0
    assert cycle_res["action_cmd"].shape == (6,)


def test_discrete_deliberation_fallback():
    """Verifies that discrete mode remains constructible and functional."""
    hal = CarlStage1HAL(headless=True)
    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="discrete")

    assert agent.deliberation_mode == "discrete"
    assert isinstance(agent.deliberation, CARLStage2_3R1DeliberationEngine)
    assert agent.deliberation.horizon == 10

    agent.initialize_spatial_grounding(0.0, 0.0, 0.0)
    cycle_res = agent.step_cognitive_cycle(hal)
    assert -1.0 <= cycle_res["cmd_L"] <= 1.0
    assert -1.0 <= cycle_res["cmd_R"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
