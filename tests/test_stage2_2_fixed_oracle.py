"""
tests/test_stage2_2_fixed_oracle.py — Verification of Floor-Contact Subtracted Collision Oracle
Classification: [PRE-EXECUTION HARNESS VERIFICATION]

Verifies that the corrected collision detection oracle:
1. Yields strictly 0 collisions during normal floor driving/rolling (where carl_contacts == floor_contacts).
2. Correctly flags collisions (> 0) when CARL contacts a wall or obstacle pillar.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL


def test_floor_rolling_has_zero_obstacle_collisions():
    """
    Verifies that when CARL drives on open floor with no walls/obstacles in range,
    the contact-subtracted collision oracle strictly reports 0.
    """
    hal = CarlStage1HAL(open_space=True)
    hal.reset()
    
    # Drive straight for 50 ticks
    obstacle_collisions = []
    for _ in range(50):
        hal.step(np.array([0.5, 0.5, 0.0, 0.0, 0.0, 0.0]))
        contact_info = hal.get_carl_contact_info()
        carl_contacts = contact_info["carl_contacts"]
        floor_contacts = contact_info["floor_contacts"]
        
        # Oracle formula: external contacts minus floor contacts
        obs_contact = max(0, carl_contacts - floor_contacts)
        obstacle_collisions.append(obs_contact)
    
    total_floor_contacts = sum(1 for _ in range(50) if hal.get_carl_contact_info()["floor_contacts"] > 0)
    assert sum(obstacle_collisions) == 0, (
        f"Floor rolling produced {sum(obstacle_collisions)} false-positive obstacle collisions! "
        "Oracle must subtract floor contacts."
    )
    print("Test passed: Normal floor rolling produces exactly 0 obstacle collisions.")


def test_wall_impact_registers_collision():
    """
    Verifies that driving directly into a wall in an enclosed arena registers
    a true positive obstacle collision once contact occurs.
    """
    hal = CarlStage1HAL(open_space=False)
    hal.reset()
    
    # Drive directly forward into the boundary wall for 150 ticks
    collision_detected = False
    for _ in range(150):
        hal.step(np.array([0.9, 0.9, 0.0, 0.0, 0.0, 0.0]))
        contact_info = hal.get_carl_contact_info()
        carl_contacts = contact_info["carl_contacts"]
        floor_contacts = contact_info["floor_contacts"]
        
        if (carl_contacts - floor_contacts) > 0:
            collision_detected = True
            break
            
    assert collision_detected, "Driving into wall must trigger an obstacle collision in the fixed oracle."
    print("Test passed: Wall impact correctly triggered true positive obstacle collision.")


if __name__ == "__main__":
    test_floor_rolling_has_zero_obstacle_collisions()
    test_wall_impact_registers_collision()
    print("All collision oracle verification tests PASSED.")
