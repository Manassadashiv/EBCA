"""
carl_cig.py — Constraint Interaction Graph (CIG-301)

Implements real-time structural boundary mapping of coupled environmental and physical constraints:
1. Obstacle proximity (collision envelope)
2. Metabolic energy depletion (battery depletion)
3. Motor speed/torque saturation
4. Movement stall / velocity rut

References:
  - EBCA Master Roadmap Pillar II (Constraint-Driven Computational Ecology)
  - Technical Specifications Section 5 (CIG-301)
"""

import numpy as np


class ConstraintInteractionGraph:
    """
    Constraint Interaction Graph (CIG-301).
    Tracks coupled physical failure boundaries dynamically to prevent catastrophic organism failure.
    """

    CONSTRAINT_NAMES = [
        "OBSTACLE_PROXIMITY",  # Ray distance < 0.25m
        "LOW_BATTERY",        # Charge < 0.20
        "MOTOR_SATURATION",   # |u| > 30.0 rad/s
        "MOVEMENT_STALL"      # High command, zero displacement
    ]

    def __init__(self, num_constraints: int = 4, learning_rate: float = 0.05):
        self.Mc = num_constraints
        self.eta = learning_rate
        self.A_CIG = np.zeros((self.Mc, self.Mc), dtype=np.float32)
        self.co_occurrences = 0
        self.last_active_flags = np.zeros(self.Mc, dtype=bool)

    def evaluate_constraints(self, min_sonar: float, battery_level: float,
                             motor_commands: np.ndarray, current_velocity: float) -> np.ndarray:
        """
        Evaluates active physical/metabolic constraints at the current tick.
        Returns a boolean array of shape (Mc,).
        """
        flags = np.zeros(self.Mc, dtype=bool)

        # 0: Obstacle proximity
        if min_sonar < 0.25:
            flags[0] = True

        # 1: Low battery
        if battery_level < 0.20:
            flags[1] = True

        # 2: Motor saturation
        if motor_commands is not None and np.max(np.abs(motor_commands[:2])) > 30.0:
            flags[2] = True

        # 3: Movement stall (high throttle but near-zero displacement)
        if motor_commands is not None and np.mean(np.abs(motor_commands[:2])) > 5.0 and abs(current_velocity) < 0.01:
            flags[3] = True

        self.last_active_flags = flags

        # Update co-occurrence matrix
        active_indices = np.where(flags)[0]
        if len(active_indices) > 1:
            self.co_occurrences += 1
            for i in active_indices:
                for j in active_indices:
                    if i != j:
                        self.A_CIG[i, j] += self.eta

        return flags

    def get_risk_factor(self) -> float:
        """
        Returns an acute compound risk score [0.0, 1.0] scaling with simultaneous constraint severity.
        """
        num_active = np.sum(self.last_active_flags)
        if num_active <= 1:
            return 0.0
        
        # Calculate sub-matrix coupling energy
        sub_coupling = 0.0
        active_idx = np.where(self.last_active_flags)[0]
        for i in active_idx:
            for j in active_idx:
                if i != j:
                    sub_coupling += self.A_CIG[i, j]

        risk = float(np.clip((num_active - 1) * 0.3 + sub_coupling * 0.1, 0.0, 1.0))
        return risk
