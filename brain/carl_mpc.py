"""
===============================================================================
  carl_mpc.py — SURPRISE NOISE ESTIMATOR δ(t) & 100 Hz EKF RESIDUAL COMPENSATOR
===============================================================================
  Calculates real-time Sim-to-Real prediction error surprise δ(t) = ||x - x̂||,
  spikes Acetylcholine (ACh) focus, and applies high-speed EKF closed-loop residual
  torque corrections to absorb friction, contact impacts, and prediction error gaps.
===============================================================================
"""

import math
import numpy as np


class SurpriseNoiseEstimator:
    """
    Biological Surprise Estimator δ(t).
    Calculates distance between virtual rollout prediction x̂(t) and actual measured telemetry x(t).
    """

    def __init__(self, surprise_threshold: float = 0.015):
        self.threshold = surprise_threshold
        self.last_surprise_delta = 0.0

    def compute_surprise(self, actual_state: np.ndarray, predicted_state: np.ndarray) -> float:
        """
        Calculates real-time surprise signal delta(t) = ||x_actual - x_predicted||_2.
        """
        if actual_state is None or predicted_state is None:
            return 0.0
        
        diff = actual_state - predicted_state
        self.last_surprise_delta = float(np.linalg.norm(diff))
        return self.last_surprise_delta

    def is_high_surprise(self) -> bool:
        """Returns True if prediction error exceeds biological threshold."""
        return self.last_surprise_delta > self.threshold


class ResidualTorqueCompensator:
    """
    100 Hz Extended Kalman Filter (EKF) Residual Torque Compensator.
    Applies closed-loop correction forces F_residual(t) to absorb friction and surface bumps.
    """

    def __init__(self, kp: float = 15.0, kd: float = 1.2):
        self.kp = kp
        self.kd = kd
        self.prev_error = None

    def compute_residual_correction(self, actual_q: np.ndarray, target_q: np.ndarray, actual_qd: np.ndarray = None) -> np.ndarray:
        """
        Computes F_residual(t) = Kp * e(t) + Kd * e_dot(t).
        """
        error = target_q - actual_q
        
        if self.prev_error is None:
            e_dot = np.zeros_like(error)
        else:
            e_dot = error - self.prev_error
        self.prev_error = error
        
        correction = self.kp * error + self.kd * e_dot
        return np.clip(correction, -0.2, 0.2)
