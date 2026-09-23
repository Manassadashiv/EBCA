"""
brain/carl_stage2_dead_reckoning.py — Stage 2.1A: Simplest Spatial Self-Localization
Classification: [SPATIAL MEMORY] Dead-Reckoning Integrator

The simplest possible internal spatial state: three numbers (x, y, θ).
No neural networks. No ring attractors. No grid cells.

Each tick:
    1. Update heading:  θ += ω_z × dt
    2. If NOT slipping:
        x += v × cos(θ) × dt
        y += v × sin(θ) × dt
    3. If slipping:
        Position integration halted (wheels spinning, not going anywhere)

This module is SENSOR-AGNOSTIC: it takes v_hat_x and omega_z as inputs.
It does NOT know which sensor channel those came from. The caller is
responsible for extracting the right signals from the organism.
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional


class DeadReckoningModule:
    """
    Minimal dead-reckoning spatial integrator for Stage 2.1A.
    Maintains internal position (x, y) and heading (theta) estimates
    using grounded velocity and yaw rate inputs.
    """

    def __init__(self, dt: float = 0.03333):
        """
        Args:
            dt: Control timestep in seconds (default 30 Hz = 0.0333s)
        """
        self.dt = dt

        # Internal spatial state — the three numbers
        self.x: float = 0.0
        self.y: float = 0.0
        self.theta: float = 0.0  # radians, world frame

        # Slip gating
        self.slip_gate_enabled: bool = True
        self.slip_threshold: float = 0.50

        # Telemetry
        self.tick_count: int = 0
        self.total_distance_integrated: float = 0.0
        self.total_ticks_gated: int = 0  # ticks where position was frozen
        self.history: List[Dict[str, Any]] = []

    def reset(self):
        """Zeros out all internal state."""
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.tick_count = 0
        self.total_distance_integrated = 0.0
        self.total_ticks_gated = 0
        self.history.clear()

    def update(
        self,
        v_hat_x: float,
        omega_z: float,
        slip_ratio: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Integrates one timestep of spatial dead reckoning.

        Args:
            v_hat_x: Grounded forward velocity estimate (m/s) from Stage 1.6.
                     Already accounts for traction coupling.
            omega_z: Observed yaw rate (rad/s) from IMU gyro.
            slip_ratio: Traction slip ratio σ from Stage 1.6 kinematic estimator.
                       When σ > slip_threshold, position integration is halted.

        Returns:
            Dict with current spatial state and integration metadata.
        """
        # 1. Always update heading (gyro-based heading works even on ice)
        self.theta += omega_z * self.dt
        # Normalize to [-π, π]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # 2. Position integration — gated by slip
        is_gated = False
        dx = 0.0
        dy = 0.0

        if self.slip_gate_enabled and slip_ratio > self.slip_threshold:
            # Wheels are spinning but robot isn't going anywhere
            # Freeze position estimate
            is_gated = True
            self.total_ticks_gated += 1
        else:
            # Normal integration
            dx = v_hat_x * math.cos(self.theta) * self.dt
            dy = v_hat_x * math.sin(self.theta) * self.dt
            self.x += dx
            self.y += dy
            self.total_distance_integrated += abs(v_hat_x) * self.dt

        self.tick_count += 1

        record = {
            "tick": self.tick_count,
            "x": self.x,
            "y": self.y,
            "theta": self.theta,
            "theta_deg": math.degrees(self.theta),
            "v_hat_x": v_hat_x,
            "omega_z": omega_z,
            "slip_ratio": slip_ratio,
            "dx": dx,
            "dy": dy,
            "is_gated": is_gated,
            "distance_from_origin": self.get_distance_from_origin(),
        }
        self.history.append(record)
        return record

    def get_position(self) -> Tuple[float, float, float]:
        """Returns current internal spatial estimate (x, y, theta)."""
        return self.x, self.y, self.theta

    def get_distance_from_origin(self) -> float:
        """Euclidean distance from the origin (starting position)."""
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def get_heading_deg(self) -> float:
        """Returns current heading in degrees."""
        return math.degrees(self.theta)

    def get_trajectory_xy(self) -> Tuple[List[float], List[float]]:
        """Returns lists of x and y coordinates from integration history."""
        xs = [r["x"] for r in self.history]
        ys = [r["y"] for r in self.history]
        return xs, ys

    def get_summary(self) -> Dict[str, Any]:
        """Returns a summary of the dead reckoning session."""
        return {
            "final_x": self.x,
            "final_y": self.y,
            "final_theta_deg": math.degrees(self.theta),
            "total_ticks": self.tick_count,
            "total_distance_integrated_m": self.total_distance_integrated,
            "total_ticks_gated": self.total_ticks_gated,
            "gated_fraction": self.total_ticks_gated / max(1, self.tick_count),
            "distance_from_origin_m": self.get_distance_from_origin(),
        }
