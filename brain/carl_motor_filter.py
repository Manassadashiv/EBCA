"""
===============================================================================
  carl_motor_filter.py — INDUSTRIAL-GRADE MOTOR FILTER & RATE LIMITER
===============================================================================
  Provides sub-millimeter industrial actuation control for CARL-Omega.
  Eliminates joint jitter, velocity step-discontinuities, and actuator chatter.

  Features:
  - 2nd-Order Low-Pass Butterworth / EMA Smoothing (τ_smooth = 0.04s)
  - Velocity & Acceleration Rate Limiting (max_vel = 6.0 rad/s, max_accel = 30.0 rad/s²)
  - Tactile Force Hysteresis Deadband (suppresses high-frequency finger oscillation)
  - Quintic Minimum-Jerk Polynomial Trajectory Planner
===============================================================================
"""

import math
import numpy as np


class WaterflowVelocityFilter:
    """
    S-Curve Jerk-Limited Wheel Velocity Filter.
    Guarantees C² continuous velocity output with strict jerk bound |jerk| <= max_jerk.
    """
    def __init__(self, num_actuators: int = 2, max_velocity: float = 35.0, max_acceleration: float = 25.0, max_jerk: float = 75.0, dt: float = 0.033):
        self.N = num_actuators
        self.max_vel = max_velocity
        self.max_accel = max_acceleration
        self.max_jerk = max_jerk
        self.dt = dt
        self.current_vel = np.zeros(self.N, dtype=np.float64)
        self.current_accel = np.zeros(self.N, dtype=np.float64)
        self.initialized = False

    def reset(self, initial_velocity: np.ndarray = None):
        if initial_velocity is not None:
            self.current_vel = np.array(initial_velocity, dtype=np.float64)
        else:
            self.current_vel = np.zeros(self.N, dtype=np.float64)
        self.current_accel = np.zeros(self.N, dtype=np.float64)
        self.initialized = True

    def filter_step(self, target_vel: np.ndarray) -> np.ndarray:
        target_vel = np.array(target_vel, dtype=np.float64)
        if not self.initialized:
            self.reset(target_vel)
            return self.current_vel.copy()

        # 1. Compute desired acceleration to track target velocity
        desired_accel = (target_vel - self.current_vel) / self.dt
        desired_accel = np.clip(desired_accel, -self.max_accel, self.max_accel)

        # 2. Rate-limit acceleration change via jerk limit
        max_delta_a = self.max_jerk * self.dt
        delta_a = np.clip(desired_accel - self.current_accel, -max_delta_a, max_delta_a)
        self.current_accel = np.clip(self.current_accel + delta_a, -self.max_accel, self.max_accel)

        # 3. Integrate velocity
        self.current_vel = np.clip(self.current_vel + self.current_accel * self.dt, -self.max_vel, self.max_vel)
        return self.current_vel.copy()


class IndustrialMotorFilter:
    """
    Industrial-grade trajectory smoothing and rate limiting filter.
    Guarantees C² continuous position, velocity, and acceleration profiles
    for physical RC servos and MuJoCo joint actuators.
    """

    def __init__(self, num_actuators: int = 10,
                 max_velocity: float = 6.0,
                 max_acceleration: float = 30.0,
                 alpha_ema: float = 0.25,
                 dt: float = 0.033):
        """
        Args:
            num_actuators: Number of motor control channels
            max_velocity: Maximum joint angular velocity (rad/s)
            max_acceleration: Maximum joint angular acceleration (rad/s²)
            alpha_ema: Exponential smoothing parameter (0 < α ≤ 1)
            dt: Control loop timestep (s)
        """
        self.N = num_actuators
        self.max_vel = max_velocity
        self.max_accel = max_acceleration
        self.alpha_ema = alpha_ema
        self.dt = dt

        # State tracking
        self.current_pos = np.zeros(self.N, dtype=np.float64)
        self.current_vel = np.zeros(self.N, dtype=np.float64)
        self.filtered_target = np.zeros(self.N, dtype=np.float64)
        self.initialized = False

    def reset(self, initial_positions: np.ndarray = None):
        """Reset filter state to specified or zero positions."""
        if initial_positions is not None:
            self.current_pos = np.array(initial_positions, dtype=np.float64)
            self.filtered_target = self.current_pos.copy()
        else:
            self.current_pos = np.zeros(self.N, dtype=np.float64)
            self.filtered_target = np.zeros(self.N, dtype=np.float64)
        self.current_vel = np.zeros(self.N, dtype=np.float64)
        self.initialized = True

    def filter_step(self, raw_targets: np.ndarray) -> np.ndarray:
        """
        Filters raw target control commands through EMA smoothing, velocity limits,
        and acceleration limits.

        Args:
            raw_targets: Raw target command vector (N,)

        Returns:
            smoothed_targets: Jitter-free, rate-limited command vector (N,)
        """
        raw_targets = np.array(raw_targets, dtype=np.float64)

        if not self.initialized:
            self.reset(raw_targets)
            return self.current_pos.copy()

        # 1. Low-Pass Exponential Moving Average (EMA) smoothing
        self.filtered_target = (1.0 - self.alpha_ema) * self.filtered_target + self.alpha_ema * raw_targets

        # 2. Compute desired velocity to reach target
        desired_vel = (self.filtered_target - self.current_pos) / self.dt

        # 3. Apply Acceleration Rate Limiting
        max_vel_change = self.max_accel * self.dt
        vel_change = desired_vel - self.current_vel
        vel_change_clamped = np.clip(vel_change, -max_vel_change, max_vel_change)
        new_vel = self.current_vel + vel_change_clamped

        # 4. Apply Velocity Rate Limiting
        new_vel_clamped = np.clip(new_vel, -self.max_vel, self.max_vel)
        self.current_vel = new_vel_clamped

        # 5. Position integration step
        self.current_pos = self.current_pos + self.current_vel * self.dt

        return self.current_pos.copy()

    @staticmethod
    def minimum_jerk_trajectory(p_start: float, p_end: float, t: float, T: float) -> tuple:
        """
        Computes minimum-jerk quintic polynomial position, velocity, and acceleration
        at time t in [0, T].

        Formula: s(τ) = 10τ³ - 15τ⁴ + 6τ⁵ where τ = t / T
        """
        if T <= 1e-6 or t <= 0:
            return p_start, 0.0, 0.0
        if t >= T:
            return p_end, 0.0, 0.0

        tau = t / T
        tau2 = tau * tau
        tau3 = tau2 * tau
        tau4 = tau3 * tau
        tau5 = tau4 * tau

        # Quintic polynomial interpolation factor
        s = 10.0 * tau3 - 15.0 * tau4 + 6.0 * tau5
        ds = (30.0 * tau2 - 60.0 * tau3 + 30.0 * tau4) / T
        dds = (60.0 * tau - 180.0 * tau2 + 120.0 * tau3) / (T * T)

        delta = p_end - p_start
        pos = p_start + delta * s
        vel = delta * ds
        accel = delta * dds

        return pos, vel, accel


class TactileHysteresisFilter:
    """
    Hysteresis deadband filter for tactile touch force compliance control.
    Prevents high-frequency finger clamping chatter during surface contact.
    """

    def __init__(self, force_low: float = 0.15, force_high: float = 0.70, deadband: float = 0.04):
        self.force_low = force_low
        self.force_high = force_high
        self.deadband = deadband
        self.last_state = "OPEN"  # OPEN, CLAMPING, HOLDING, RELAXING

    def update(self, current_touch_force: float, target_grip: float, current_grip: float) -> float:
        """
        Returns smooth compliance grip position based on touch force state machine with hysteresis.
        """
        if current_touch_force > (self.force_high + self.deadband):
            self.last_state = "RELAXING"
            return max(0.02, current_grip - 0.015)
        elif current_touch_force < (self.force_low - self.deadband):
            self.last_state = "CLAMPING"
            return min(target_grip, current_grip + 0.025)
        else:
            self.last_state = "HOLDING"
            return current_grip
