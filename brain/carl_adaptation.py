"""
carl_adaptation.py — Morphological Self-Healing & Autopoietic Adaptation (ADP-1101)

Implements online System ID tracking wheel slip, motor friction drag, and inclination tilt.
Dynamically recalibrates motor torque scale and CPG sway frequencies on-the-fly when physical anomalies occur.
"""
import numpy as np


class MorphologicalAdaptationEngine:
    """
    Autopoietic System ID & Physical Self-Healing Adaptation Engine.
    """
    def __init__(self):
        self.left_wheel_friction_scale = 1.0
        self.right_wheel_friction_scale = 1.0
        self.cpg_sway_frequency = 0.10
        
        self.slip_counter_left = 0
        self.slip_counter_right = 0
        self.adaptation_events = 0

    def step_adaptation(
        self,
        commanded_speeds: np.ndarray,
        actual_wheel_vels: np.ndarray,
        imu_pitch_deg: float
    ) -> tuple:
        """
        Monitors discrepancy between commanded motor speeds and actual wheel joint velocities.
        Dynamically adjusts torque scales to compensate for slip or friction drag.
        
        Args:
            commanded_speeds: [left_cmd, right_cmd]
            actual_wheel_vels: [left_vel, right_vel]
            imu_pitch_deg: Current chassis pitch angle
            
        Returns:
            (left_scale, right_scale, cpg_freq)
        """
        err_left = commanded_speeds[0] - actual_wheel_vels[0]
        err_right = commanded_speeds[1] - actual_wheel_vels[1]
        
        # Detect Left Wheel Drag/Slip
        if abs(err_left) > 3.0:
            self.slip_counter_left += 1
            if self.slip_counter_left > 15:
                # Boost left torque to overcome drag
                self.left_wheel_friction_scale = min(1.5, self.left_wheel_friction_scale + 0.02)
                self.adaptation_events += 1
        else:
            self.slip_counter_left = max(0, self.slip_counter_left - 1)
            self.left_wheel_friction_scale = max(1.0, self.left_wheel_friction_scale - 0.005)

        # Detect Right Wheel Drag/Slip
        if abs(err_right) > 3.0:
            self.slip_counter_right += 1
            if self.slip_counter_right > 15:
                # Boost right torque to overcome drag
                self.right_wheel_friction_scale = min(1.5, self.right_wheel_friction_scale + 0.02)
                self.adaptation_events += 1
        else:
            self.slip_counter_right = max(0, self.slip_counter_right - 1)
            self.right_wheel_friction_scale = max(1.0, self.right_wheel_friction_scale - 0.005)

        # Adapt CPG Sway Frequency on Inclination (high pitch slows sway to maintain low CoM)
        if abs(imu_pitch_deg) > 5.0:
            self.cpg_sway_frequency = 0.05  # slow, stable sway
        else:
            self.cpg_sway_frequency = 0.10  # normal walking gait sway

        return (
            self.left_wheel_friction_scale,
            self.right_wheel_friction_scale,
            self.cpg_sway_frequency
        )
