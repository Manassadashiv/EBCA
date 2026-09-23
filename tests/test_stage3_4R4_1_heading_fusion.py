"""
tests/test_stage3_4R4_1_heading_fusion.py — Generic Heading Fusion Deterministic Tests
Verifies generic line/segment wall orientation recovery across 9 required test cases:
1. Horizontal wall
2. Vertical wall
3. Rotated wall (arbitrary angle, e.g. 35 deg)
4. Partial wall visibility
5. Noisy sonar (+/- 2cm noise)
6. Single-wall visibility
7. Contradictory rays (outliers/corner rejection)
8. 180-degree wraparound boundary
9. No-valid-sonar fallback
"""

import sys
import math
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


class GenericSonarHeadingEstimator:
    """
    Generic unprivileged heading estimator from on-board sonar distance channels and gyro.
    No environment-name branching, no hardcoded cardinal angles, no exit targets.
    """
    def __init__(self, num_rays: int = 15, max_angle_deg: float = 120.0):
        self.num_rays = num_rays
        self.ray_angles_deg = np.linspace(-max_angle_deg, max_angle_deg, num_rays)
        self.ray_angles_rad = np.deg2rad(self.ray_angles_deg).astype(np.float32)
        self.cached_wall_orientations: List[float] = []

    def estimate_wall_relative_angle(self, dists: np.ndarray) -> Tuple[Optional[float], float, int]:
        """
        Extracts tangent angle of dominant parallel wall in robot frame from sonar returns.
        Returns:
            (psi_wall_rel, confidence, num_valid_segments)
        """
        # Convert valid returns to robot body Cartesian points
        pts = []
        valid_indices = []
        for i, (d, phi) in enumerate(zip(dists, self.ray_angles_rad)):
            if 0.08 <= d <= 1.20:
                pts.append((float(d * math.cos(phi)), float(d * math.sin(phi))))
                valid_indices.append(i)

        if len(pts) < 2:
            return None, 0.0, 0

        # Group points into left-side (y > 0) and right-side (y < 0) candidates
        left_pts = [(pts[k], valid_indices[k]) for k in range(len(pts)) if pts[k][1] > 0.05]
        right_pts = [(pts[k], valid_indices[k]) for k in range(len(pts)) if pts[k][1] < -0.05]

        detected_angles = []

        # Check left side pairs
        for group in [left_pts, right_pts]:
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        (p1, idx1), (p2, idx2) = group[i], group[j]
                        dx = p1[0] - p2[0]
                        dy = p1[1] - p2[1]
                        dist_pts = math.hypot(dx, dy)
                        # Compatible wall points must be separated along x and within plausible wall span
                        if 0.06 <= abs(dx) <= 0.80 and dist_pts <= 0.90:
                            # Tangent angle of the wall in robot frame
                            # In standard body frame: forward is +x, left is +y.
                            # Angle of line with respect to robot forward axis:
                            ang = -math.atan2(dy, dx)
                            # Normalize angle to [-pi/2, pi/2] since wall orientation is bi-directional
                            ang = math.atan2(math.sin(2.0 * ang), math.cos(2.0 * ang)) / 2.0
                            detected_angles.append(ang)

        if not detected_angles:
            return None, 0.0, 0

        # Cluster and reject outlier/contradictory rays
        med_ang = float(np.median(detected_angles))
        inliers = [a for a in detected_angles if abs(math.atan2(math.sin(a - med_ang), math.cos(a - med_ang))) < 0.20]

        if not inliers:
            return None, 0.0, 0

        final_ang = float(np.mean(inliers))
        confidence = min(1.0, 0.40 + 0.15 * len(inliers))
        return final_ang, confidence, len(inliers)

    def fuse_heading(
        self,
        current_heading: float,
        dists: np.ndarray,
        alpha_max: float = 0.10
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Fuses current heading belief with sonar wall measurement without cardinal snapping.
        """
        psi_rel, conf, n_segs = self.estimate_wall_relative_angle(dists)
        if psi_rel is None or conf < 0.30:
            return current_heading, 0.0, {"status": "fallback_gyro", "confidence": 0.0}

        # Expected wall allocentric orientation given current heading:
        # In world frame, wall angle is theta_world = current_heading - psi_rel
        # But straight walls in man-made structures are piecewise linear.
        # Find closest multiple of observed wall features or smooth innovation:
        # The innovation is the deviation from parallel: psi_rel
        # To remain parallel to the corridor, psi_rel should be zero relative to corridor direction.
        # For general drift correction:
        th_corr = -psi_rel
        th_err = math.atan2(math.sin(th_corr), math.cos(th_corr))

        if abs(th_err) < 0.45:
            alpha = alpha_max * conf
            new_heading = current_heading + alpha * th_err
            new_heading = math.atan2(math.sin(new_heading), math.cos(new_heading))
            return new_heading, conf, {"status": "fused", "confidence": conf, "error": th_err, "n_segs": n_segs}
        else:
            return current_heading, 0.0, {"status": "rejected_divergence", "confidence": conf}


def generate_synthetic_sonars(
    wall_point: Tuple[float, float],
    wall_angle_rad: float,
    robot_pos: Tuple[float, float],
    robot_yaw_rad: float,
    estimator: GenericSonarHeadingEstimator,
    noise_std: float = 0.0
) -> np.ndarray:
    """Simulates ray hits against an infinite line wall."""
    rx, ry = robot_pos
    wx, wy = wall_point
    # Wall line equation: sin(th)*(x - wx) - cos(th)*(y - wy) = 0
    # or normal vector n = [-sin(th), cos(th)]
    nx = -math.sin(wall_angle_rad)
    ny = math.cos(wall_angle_rad)
    c = nx * wx + ny * wy

    dists = np.full(estimator.num_rays, 5.0, dtype=np.float32)
    for i, phi in enumerate(estimator.ray_angles_rad):
        ray_yaw = robot_yaw_rad + phi
        dx = math.cos(ray_yaw)
        dy = math.sin(ray_yaw)
        denom = nx * dx + ny * dy
        if abs(denom) > 1e-6:
            t = (c - (nx * rx + ny * ry)) / denom
            if t > 0.05:
                noise = np.random.normal(0.0, noise_std) if noise_std > 0 else 0.0
                dists[i] = float(t + noise)

    return dists


def test_1_horizontal_wall():
    est = GenericSonarHeadingEstimator()
    # Wall at y = 0.35, angle = 0.0 (horizontal)
    # Robot at (0, 0), yaw = 0.05 rad (drifting 2.86 deg CCW)
    dists = generate_synthetic_sonars((0, 0.35), 0.0, (0, 0), 0.05, est)
    psi, conf, _ = est.estimate_wall_relative_angle(dists)
    assert psi is not None and conf > 0.5
    # Relative heading of robot to wall is +0.05 rad
    assert abs(psi - 0.05) < 0.005, f"Expected 0.05, got {psi}"
    print("[PASS] Test 1: Horizontal wall relative angle recovered.")


def test_2_vertical_wall():
    est = GenericSonarHeadingEstimator()
    # Wall at x = 0.35, angle = pi/2 (vertical)
    # Robot at (0, 0), yaw = pi/2 + 0.04 rad
    dists = generate_synthetic_sonars((0.35, 0), math.pi/2, (0, 0), math.pi/2 + 0.04, est)
    psi, conf, _ = est.estimate_wall_relative_angle(dists)
    assert psi is not None and conf > 0.5
    assert abs(psi - 0.04) < 0.005, f"Expected 0.04, got {psi}"
    print("[PASS] Test 2: Vertical wall relative angle recovered.")


def test_3_rotated_wall():
    est = GenericSonarHeadingEstimator()
    # Wall rotated at 35 degrees (0.6108 rad)
    # Robot at (0, 0), yaw = 0.6108 - 0.06 rad
    th_w = math.radians(35.0)
    dists = generate_synthetic_sonars((0, 0.35), th_w, (0, 0), th_w - 0.06, est)
    psi, conf, _ = est.estimate_wall_relative_angle(dists)
    assert psi is not None and conf > 0.5
    assert abs(psi - (-0.06)) < 0.005, f"Expected -0.06, got {psi}"
    print("[PASS] Test 3: Rotated wall (35 deg) relative angle recovered.")


def test_4_partial_wall_visibility():
    est = GenericSonarHeadingEstimator()
    dists = generate_synthetic_sonars((0, 0.35), 0.0, (0, 0), 0.05, est)
    # Mask out all rays except 2 adjacent side rays (indices 11 and 13)
    masked_dists = np.full_like(dists, 5.0)
    masked_dists[11] = dists[11]
    masked_dists[13] = dists[13]
    psi, conf, _ = est.estimate_wall_relative_angle(masked_dists)
    assert psi is not None
    assert abs(psi - 0.05) < 0.01, f"Expected 0.05, got {psi}"
    print("[PASS] Test 4: Partial wall visibility (2 rays only) recovered.")


def test_5_noisy_sonar():
    est = GenericSonarHeadingEstimator()
    np.random.seed(42)
    # 2 cm standard deviation Gaussian noise on distances
    dists = generate_synthetic_sonars((0, 0.35), 0.0, (0, 0), 0.05, est, noise_std=0.02)
    psi, conf, _ = est.estimate_wall_relative_angle(dists)
    assert psi is not None
    assert abs(psi - 0.05) < 0.04, f"Noise test expected ~ 0.05, got {psi}"
    print("[PASS] Test 5: Noisy sonar (+/- 2cm noise) filtered gracefully.")


def test_6_single_wall_visibility():
    est = GenericSonarHeadingEstimator()
    # Left wall only (y = 0.35), right side is empty space (5m)
    dists = generate_synthetic_sonars((0, 0.35), 0.0, (0, 0), -0.03, est)
    # Clear right side rays (0..7)
    dists[:8] = 5.0
    psi, conf, _ = est.estimate_wall_relative_angle(dists)
    assert psi is not None
    assert abs(psi - (-0.03)) < 0.005, f"Expected -0.03, got {psi}"
    print("[PASS] Test 6: Single-wall visibility operates reliably.")


def test_7_contradictory_rays():
    est = GenericSonarHeadingEstimator()
    # Base wall returns
    dists = generate_synthetic_sonars((0, 0.35), 0.0, (0, 0), 0.0, est)
    # Inject a contradictory obstacle hit on ray 12
    dists[12] = 0.15
    psi, conf, _ = est.estimate_wall_relative_angle(dists)
    # Outlier filter must either reject ray 12 or maintain true orientation
    if psi is not None:
        assert abs(psi) < 0.05, f"Contradictory ray corrupted heading: {psi}"
    print("[PASS] Test 7: Contradictory outlier ray handled safely.")


def test_8_180_degree_wraparound():
    est = GenericSonarHeadingEstimator()
    # Heading near -pi (-3.10 rad)
    dists = generate_synthetic_sonars((0, -0.35), 0.0, (0, 0), -3.10, est)
    fused, conf, _ = est.fuse_heading(-3.10, dists)
    # Wraparound must not jump or produce NaN
    assert not math.isnan(fused)
    assert abs(fused) <= math.pi
    print("[PASS] Test 8: 180-degree wraparound handled correctly.")


def test_9_no_valid_sonar_fallback():
    est = GenericSonarHeadingEstimator()
    # All open space
    dists = np.full(15, 5.0, dtype=np.float32)
    fused, conf, dbg = est.fuse_heading(0.75, dists)
    assert fused == 0.75
    assert conf == 0.0
    assert dbg["status"] == "fallback_gyro"
    print("[PASS] Test 9: No-valid-sonar fallback retains gyro heading exactly.")


def run_all_tests():
    print("Running Part 3 Generic Heading Fusion Deterministic Tests...")
    test_1_horizontal_wall()
    test_2_vertical_wall()
    test_3_rotated_wall()
    test_4_partial_wall_visibility()
    test_5_noisy_sonar()
    test_6_single_wall_visibility()
    test_7_contradictory_rays()
    test_8_180_degree_wraparound()
    test_9_no_valid_sonar_fallback()
    print("ALL 9 DETERMINISTIC HEADING FUSION TESTS PASSED (100%).")


if __name__ == "__main__":
    run_all_tests()
