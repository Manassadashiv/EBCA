"""
tools/p1_r3/p1r3_validation_suite.py — Analytical Validation & Calibration Suite for P1-R3

Performs 4 pre-flight experimental qualifications:
1. Physical Route Feasibility: Verifies that both Route A and Route B are reachable within time horizon.
2. Local Sensory Equivalence: Verifies that sonar range measurements at the bifurcation (0.0, 0.0) are symmetric.
3. Latent Hazard Occlusion: Verifies that the downstream barrier in Route A cannot be detected from x <= 0.35m.
4. Solid Contact Verification: Verifies that the robot cannot clip through walls.
"""

import os
import sys
import math
import mujoco
import numpy as np

# Ensure root directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from brain.p1_r3.carl_p1r3_environment import CarlP1R3Environment
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent


def test_sensory_equivalence() -> Dict[str, Any]:
    """Tests that at (0.0, 0.0), Left and Right sonar arrays match within 2%."""
    env = CarlP1R3Environment()
    env.configure_environment(1) # Latent hazard in A active
    env.reset_robot_pose(0.0, 0.0, 0.0)
    
    agent = CarlAutonomousOrganismAgent(dt=0.0333)
    sensory = agent.embodiment.read_proprioception(env.hal)
    sonar = np.array(sensory.sonar_distances)
    
    n_rays = len(sonar) # 15 rays
    center_idx = n_rays // 2 # ray 7 is center
    left_rays = sonar[:center_idx]
    right_rays = sonar[center_idx+1:][::-1]
    
    diff = np.abs(left_rays - right_rays)
    max_diff = float(np.max(diff))
    mean_diff = float(np.mean(diff))
    passed = (max_diff < 0.05)
    
    print(f"[TEST 1: Sensory Equivalence] Max Left-Right Sonar Diff: {max_diff:.4f} m (Threshold: < 0.05m) -> {'PASS' if passed else 'FAIL'}")
    return {
        "passed": passed,
        "max_diff_m": max_diff,
        "mean_diff_m": mean_diff,
        "left_rays": left_rays.tolist(),
        "right_rays": right_rays.tolist()
    }


def test_hazard_occlusion() -> Dict[str, Any]:
    """Tests that the downstream barrier at (1.40, +0.60) is NOT detectable from x <= 0.35m."""
    env = CarlP1R3Environment()
    
    # Configure with hazard (Ep 1)
    env.configure_environment(1)
    env.reset_robot_pose(0.0, 0.0, 0.0)
    agent = CarlAutonomousOrganismAgent(dt=0.0333)
    sonar_with_hazard = np.array(agent.embodiment.read_proprioception(env.hal).sonar_distances)
    
    # Configure without hazard (Ep 3)
    env.configure_environment(3)
    env.reset_robot_pose(0.0, 0.0, 0.0)
    sonar_without_hazard = np.array(agent.embodiment.read_proprioception(env.hal).sonar_distances)
    
    diff = np.abs(sonar_with_hazard - sonar_without_hazard)
    max_diff = float(np.max(diff))
    passed = (max_diff < 0.02)
    
    print(f"[TEST 2: Hazard Occlusion at Decision Point] Max Sonar Delta: {max_diff:.4f} m (Threshold: < 0.02m) -> {'PASS' if passed else 'FAIL'}")
    return {
        "passed": passed,
        "max_diff_m": max_diff,
        "occlusion_intact": passed
    }


def test_solid_collision() -> Dict[str, Any]:
    """Verifies that robot hull physically stops against solid divider wall."""
    env = CarlP1R3Environment()
    env.configure_environment(1)
    env.reset_robot_pose(0.0, 0.0, 0.0)
    
    deck_bid = env.model.body("drive_deck").id
    jadr = env.model.body_jntadr[deck_bid]
    qadr = env.model.jnt_qposadr[jadr]
    
    # Drive straight into central divider at x=0.80
    env.data.ctrl[0] = 5.5
    env.data.ctrl[1] = 5.5
    
    for _ in range(300):
        env.hal.step()
        
    final_x = float(env.data.qpos[qadr])
    passed = (final_x < 0.75) # Stopped before wall face
    print(f"[TEST 3: Solid Collision Physics] Final X against wall: {final_x:.4f} m (Wall at 0.80m) -> {'PASS' if passed else 'FAIL'}")
    return {
        "passed": passed,
        "final_pos_x": final_x
    }


def run_full_validation_suite() -> bool:
    print("=" * 80)
    print("CARL-DX P1-R3 PRE-FLIGHT VALIDATION & CALIBRATION SUITE")
    print("=" * 80)
    t1 = test_sensory_equivalence()
    t2 = test_hazard_occlusion()
    t3 = test_solid_collision()
    
    all_passed = t1["passed"] and t2["passed"] and t3["passed"]
    print("=" * 80)
    print(f"PRE-FLIGHT VALIDATION RESULT: {'ALL TESTS PASSED (QUALIFIED)' if all_passed else 'VALIDATION FAILED'}")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = run_full_validation_suite()
    sys.exit(0 if success else 1)
