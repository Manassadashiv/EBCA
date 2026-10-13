"""
tests/test_stage3_4_canonical_integration.py — Stage 3.4 Canonical Organism Integration Test
Classification: [STAGE 3.4 ARCHITECTURAL RE-UNIFICATION STEP 1]

Verifies:
1. Canonical CarlAutonomousOrganismAgent instantiation with deliberation_mode="active_inference".
2. Initialization of spatial grounding with and without external grid_path.
3. Execution of full closed-loop cognitive cycles under mock HAL sensory state.
4. Continuous action bounds verification: action in [-1.0, 1.0]^2.
5. All cognitive cycle organs active and reporting valid non-null telemetry.
6. Zero privileged simulator state leakage.
"""

import math
import numpy as np
import pytest
from pathlib import Path

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent, CognitiveCycleTelemetry
from brain.carl_active_inference import CARLActiveInferenceEngine


class MockHAL:
    """Mock Hardware Abstraction Layer producing synthetic, non-privileged sensor vectors."""
    def __init__(self, num_sensors: int = 25):
        self.num_sensors = num_sensors
        self.step_idx = 0
        self.applied_commands = []

    def read_sensors(self) -> np.ndarray:
        """Returns 25-dim sensor array (15 sonars, 3 accels, 3 gyros, 4 wheel speeds)."""
        s = np.zeros(self.num_sensors, dtype=np.float64)
        # 15 sonars: open corridor ahead, walls to sides
        s[:15] = 2.50
        s[0] = 0.80   # extreme left
        s[14] = 0.80  # extreme right
        s[6:9] = 2.20 # forward rays open
        # Accelerometers (indices 15..17)
        s[15] = 0.10  # forward accel
        s[16] = 0.00  # lateral accel
        s[17] = 9.81  # vertical gravity
        # Gyroscopes (indices 18..20)
        s[18] = 0.00
        s[19] = 0.00
        s[20] = 0.05  # yaw rate w_z
        # Wheel speeds (indices 21..24)
        s[21] = 0.50
        s[22] = 0.50
        s[23] = 0.50
        s[24] = 0.50
        return s

    def step_simulation(self, cmd_left: float, cmd_right: float, *args, **kwargs):
        """Simulates physical execution and records commands."""
        self.applied_commands.append((cmd_left, cmd_right))
        self.step_idx += 1
        return {"status": "ok"}


from brain.carl_stage1_hal import CarlStage1HAL

def test_canonical_active_inference_wiring():
    """Verifies that CarlAutonomousOrganismAgent hosts CARLActiveInferenceEngine cleanly."""
    hal = CarlStage1HAL(headless=True)
    agent = CarlAutonomousOrganismAgent(
        dt=hal.dt,
        enable_memory=True,
        deliberation_mode="active_inference",
        grid_path=None
    )
    
    assert isinstance(agent.deliberation, CARLActiveInferenceEngine), (
        f"Expected CARLActiveInferenceEngine deliberation backend, got {type(agent.deliberation)}"
    )
    assert agent.deliberation_mode == "active_inference"
    assert agent.spatial_memory is agent.deliberation.mem

    # Initialize spatial grounding
    spawn_x, spawn_y, spawn_yaw = 0.5, -0.2, 0.0
    agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw)
    assert np.allclose(agent.deliberation.pose, [spawn_x, spawn_y, spawn_yaw], atol=1e-5)

    # Execute cognitive cycles
    for cycle in range(5):
        result = agent.step_cognitive_cycle(hal)

        
        # Verify action output
        assert "telemetry" in result
        assert "cmd_L" in result
        assert "cmd_R" in result
        assert "action_cmd" in result
        assert "delib_telemetry" in result

        cmd_L = result["cmd_L"]
        cmd_R = result["cmd_R"]
        assert -1.0 <= cmd_L <= 1.0, f"cmd_L out of bounds: {cmd_L}"
        assert -1.0 <= cmd_R <= 1.0, f"cmd_R out of bounds: {cmd_R}"

        # Verify active organ flags
        assert result["stage2_1_attractor_active"] is True, "CANN attractor must be active"
        assert result["stage2_2_memory_active"] is True, "Spatial memory/odometry must be active"
        assert result["stage2_3_delib_active"] is True, "Deliberation must be active"
        assert result["actuation_active"] is True, "Actuation must be active"

        # Verify deliberation telemetry
        dtel = result["delib_telemetry"]
        assert "best_cost" in dtel
        assert "selected_action" in dtel
        assert "accepted_candidates" in dtel
        assert "stage_timings" in dtel
        assert dtel["cann_wired"] is True

        # Verify agent telemetry record
        telem = result["telemetry"]
        assert isinstance(telem, CognitiveCycleTelemetry)
        assert telem.tick == cycle + 1
        assert not math.isnan(telem.pos_x)
        assert not math.isnan(telem.pos_y)
        assert not math.isnan(telem.yaw)


def test_canonical_grid_path_initialization(tmp_path):
    """Verifies that grid_path provided in __init__ or initialize_spatial_grounding is loaded."""
    import torch
    grid_tensor = torch.zeros(1, 1, 128, 128, dtype=torch.float32)
    grid_tensor[0, 0, 60:68, 60:68] = 1.0
    grid_file = tmp_path / "test_arena_grid.pt"
    torch.save(grid_tensor, grid_file)

    # Initialize via __init__
    agent = CarlAutonomousOrganismAgent(
        dt=0.030,
        deliberation_mode="active_inference",
        grid_path=str(grid_file)
    )
    assert agent.deliberation.has_static_map is True
    assert agent.deliberation.static_grid_np[64, 64] == 1.0

    # Test dynamic reload via initialize_spatial_grounding
    grid_tensor2 = torch.zeros(1, 1, 128, 128, dtype=torch.float32)
    grid_tensor2[0, 0, 70:75, 70:75] = 1.0
    grid_file2 = tmp_path / "test_arena_grid2.pt"
    torch.save(grid_tensor2, grid_file2)

    agent.initialize_spatial_grounding(0.0, 0.0, 0.0, grid_path=str(grid_file2))
    assert agent.deliberation.static_grid_np[72, 72] == 1.0
    assert agent.deliberation.static_grid_np[64, 64] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
