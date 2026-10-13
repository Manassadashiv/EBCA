"""
tests/test_stage3_4R4_2_heading_fusion.py — Deterministic Test Suite for R4.2 Heading Fusion
Tests all 12 required cases (A through L):
  A. Flat wall -> valid sonar heading with high confidence.
  B. Rotated planar wall (35 deg) -> valid heading with low residual.
  C. T-junction -> low confidence or rejection.
  D. 90-degree corner -> rejection/downweighting rather than false single-wall orientation.
  E. Contradictory sonar points -> rejection.
  F. Sparse sonar -> safe fallback to gyro prediction.
  G. No sonar -> gyro-only propagation.
  H. High angular velocity (abs(w) >= 0.20 rad/s) -> sonar measurement does not overwrite heading.
  I. Low angular velocity + reliable wall -> sonar correction allowed.
  J. Angle wraparound near +/- pi.
  K. No discontinuity -> continuous fusion without sudden jumps.
  L. Anti-cheat -> zero simulator coordinates in cognitive loop.
"""

import math
import ast
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from brain.carl_active_inference import GenericSonarHeadingEstimator as GenericSonarHeadingEstimatorR42


def run_deterministic_tests():
    estimator = GenericSonarHeadingEstimatorR42(num_rays=15, max_angle_deg=120.0)

    print("=== RUNNING R4.2 DETERMINISTIC HEADING FUSION TESTS (A–L) ===")

    # Test A: Flat Wall
    # Wall at y = 0.40m parallel to robot axis. d_i = 0.40 / sin(phi_i) for phi_i > 0
    dists_flat = np.full(15, 2.0, dtype=np.float32)
    for i, phi in enumerate(estimator.ray_angles_rad):
        if 0.15 < phi < 1.45:
            dists_flat[i] = 0.40 / math.sin(phi)
    diag_a = estimator.analyze_sonar_geometry(dists_flat, omega=0.0)
    assert diag_a["sonar_heading_valid"], "Test A Failed: Flat wall should be valid."
    assert diag_a["sonar_heading_confidence"] > 0.60, "Test A Failed: Confidence should be high."
    assert abs(diag_a["sonar_wall_angle"]) < 0.05, f"Test A Failed: Angle should be near 0, got {diag_a['sonar_wall_angle']}"
    print("[PASS] Test A: Flat wall accepted with high confidence.")

    # Test B: Rotated Planar Wall (35 deg)
    dists_rot = np.full(15, 2.0, dtype=np.float32)
    th_wall = math.radians(35.0)
    # Line equation in robot frame: y - x * tan(35) = 0.40
    for i, phi in enumerate(estimator.ray_angles_rad):
        den = math.sin(phi) - math.cos(phi) * math.tan(th_wall)
        if den > 0.2:
            d = 0.40 / den
            if 0.08 <= d <= 1.20:
                dists_rot[i] = d
    diag_b = estimator.analyze_sonar_geometry(dists_rot, omega=0.0)
    assert diag_b["sonar_heading_valid"], "Test B Failed: Rotated wall should be valid."
    assert abs(diag_b["sonar_wall_angle"] - th_wall) < 0.08, f"Test B Failed: Expected {th_wall}, got {diag_b['sonar_wall_angle']}"
    print("[PASS] Test B: Rotated planar wall (35 deg) recovered with low residual.")

    # Test C: T-Junction Returns
    # Front dividing wall at x = 0.50, side walls at y = +/- 0.40
    dists_t = np.full(15, 2.0, dtype=np.float32)
    for i, phi in enumerate(estimator.ray_angles_rad):
        # Ray to front wall at x=0.50
        if abs(phi) < 0.5:
            dists_t[i] = 0.50 / math.cos(phi)
        elif phi > 0.8:
            dists_t[i] = 0.40 / math.sin(phi)
        elif phi < -0.8:
            dists_t[i] = -0.40 / math.sin(phi)
    diag_c = estimator.analyze_sonar_geometry(dists_t, omega=0.0)
    assert not diag_c["sonar_heading_valid"], "Test C Failed: T-Junction should be rejected."
    print(f"[PASS] Test C: T-Junction rejected ({diag_c['sonar_geometry_condition']}).")

    # Test D: 90-Degree Corner (L-shape on left side)
    # Points on horizontal wall (y=0.30, x in [0.0, 0.40]) and perpendicular wall (x=0.40, y in [0.30, 0.80])
    dists_corner = np.full(15, 2.0, dtype=np.float32)
    for i, phi in enumerate(estimator.ray_angles_rad):
        if 0.2 < phi < 0.8:
            # hits vertical wall x=0.40
            dists_corner[i] = 0.40 / math.cos(phi)
        elif 0.8 <= phi < 1.4:
            # hits horizontal wall y=0.30
            dists_corner[i] = 0.30 / math.sin(phi)
    diag_d = estimator.analyze_sonar_geometry(dists_corner, omega=0.0)
    assert not diag_d["sonar_heading_valid"], "Test D Failed: 90-degree corner must be rejected."
    assert "corner" in diag_d["sonar_geometry_condition"], f"Test D Failed: condition was {diag_d['sonar_geometry_condition']}"
    print(f"[PASS] Test D: 90-degree corner rejected ({diag_d['sonar_geometry_condition']}).")

    # Test E: Contradictory Sonar Points (Orthogonal walls on left and right)
    dists_contra = np.full(15, 2.0, dtype=np.float32)
    # Left side hits horizontal wall y=0.40
    for i, phi in enumerate(estimator.ray_angles_rad):
        if 0.4 < phi < 1.4:
            dists_contra[i] = 0.40 / math.sin(phi)
        elif -1.4 < phi < -0.4:
            # Right side hits 45-degree slanted wall
            dists_contra[i] = 0.40 / (math.sin(-phi) + math.cos(-phi))
    diag_e = estimator.analyze_sonar_geometry(dists_contra, omega=0.0)
    assert not diag_e["sonar_heading_valid"], "Test E Failed: Contradictory walls must be rejected."
    print(f"[PASS] Test E: Contradictory sonar walls rejected ({diag_e['sonar_geometry_condition']}).")

    # Test F: Sparse Sonar (1 ray only)
    dists_sparse = np.full(15, 2.0, dtype=np.float32)
    dists_sparse[7] = 0.35
    diag_f = estimator.analyze_sonar_geometry(dists_sparse, omega=0.0)
    assert not diag_f["sonar_heading_valid"], "Test F Failed: Single ray must be rejected."
    print("[PASS] Test F: Sparse sonar safely falls back.")

    # Test G: No Sonar (all max range)
    dists_none = np.full(15, 2.5, dtype=np.float32)
    th_res, conf, diag_g = estimator.fuse_heading(0.50, dists_none, omega=0.10, dt=0.030)
    expected_g = 0.50 + 0.10 * 0.030
    assert abs(th_res - expected_g) < 1e-5, "Test G Failed: Should propagate gyro alone."
    assert conf == 0.0, "Test G Failed: Confidence should be 0."
    print("[PASS] Test G: No sonar falls back to pure gyro propagation.")

    # Test H: High Angular Velocity (abs(w) >= 0.20 rad/s)
    # Even with a perfectly flat wall, high rotation invalidates sonar overwrite
    th_h, conf_h, diag_h = estimator.fuse_heading(0.0, dists_flat, omega=0.35, dt=0.030)
    expected_h = 0.0 + 0.35 * 0.030
    assert abs(th_h - expected_h) < 1e-5, f"Test H Failed: High omega should block sonar correction. Expected {expected_h}, got {th_h}"
    assert diag_h["sonar_geometry_condition"] == "angular_rate_exceeded", "Test H Failed: Condition mismatch."
    print("[PASS] Test H: High angular velocity (w=0.35 rad/s) invalidates sonar overwrite.")

    # Test I: Low Angular Velocity + Reliable Wall
    th_i, conf_i, diag_i = estimator.fuse_heading(0.05, dists_flat, omega=0.05, dt=0.030)
    assert diag_i["status"] == "fused", "Test I Failed: Low omega + flat wall should fuse."
    assert conf_i > 0.60, "Test I Failed: Confidence should be high."
    print(f"[PASS] Test I: Low angular velocity (w=0.05 rad/s) allows sonar correction (conf={conf_i:.2f}).")

    # Test J: Angle Wraparound near +/- pi
    th_j, conf_j, diag_j = estimator.fuse_heading(math.pi - 0.02, dists_none, omega=1.0, dt=0.050)
    # Should wrap cleanly to negative angle
    assert -math.pi <= th_j <= math.pi, "Test J Failed: Heading must be in [-pi, pi]."
    assert abs(th_j - (-math.pi + 0.03)) < 1e-4, f"Test J Failed: Expected -pi+0.03, got {th_j}"
    print("[PASS] Test J: Angle wraparound near +/- pi operates continuously.")

    # Test K: No Discontinuity
    # When transition occurs from valid wall to rejected corner, heading does not jump
    th_k1, _, _ = estimator.fuse_heading(0.10, dists_flat, omega=0.0, dt=0.030)
    th_k2, _, _ = estimator.fuse_heading(th_k1, dists_corner, omega=0.0, dt=0.030)
    step_jump = abs(th_k2 - th_k1)
    assert step_jump < 0.01, f"Test K Failed: Discontinuity detected on corner rejection ({step_jump} rad)."
    print(f"[PASS] Test K: No discontinuity on corner transition (jump = {step_jump:.5f} rad).")

    # Test L: AST Anti-Cheat Check
    pipeline_files = [
        Path("brain/carl_active_inference.py"),
    ]
    forbidden_symbols = {"qpos", "qvel", "qacc", "geom_xpos", "site_xpos", "mj_ray"}
    for pf in pipeline_files:
        if pf.exists():
            tree = ast.parse(pf.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in forbidden_symbols:
                    assert False, f"Anti-Cheat Violation in {pf}: forbidden attribute '{node.attr}' found."
                elif isinstance(node, ast.Name) and node.id in forbidden_symbols:
                    assert False, f"Anti-Cheat Violation in {pf}: forbidden name '{node.id}' found."
    print("[PASS] Test L: AST Anti-Cheat Scan clean (zero simulator coordinates).")

    print("\nALL 12 DETERMINISTIC TESTS PASSED (100%).")


if __name__ == "__main__":
    run_deterministic_tests()
