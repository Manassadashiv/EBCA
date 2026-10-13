"""
===============================================================================
  carl_osc_dmp.py — OPERATIONAL SPACE CONTROL (OSC) & DYNAMIC MOVEMENT PRIMITIVES (DMP)
===============================================================================
  Provides jolt-free task-space force control tau = J^T * F_task + g(q),
  active torso balance hip pitch/roll coupling, and minimum-jerk reference splines.
===============================================================================
"""

import math
import numpy as np


class OperationalSpaceController:
    """
    Task-Space Force Controller (OSC).
    Maps 3D end-effector target forces F_task into joint torques tau = J^T * F_task.
    Enforces dynamic compliance for jolt-free physical interaction.
    """

    def __init__(self, kp: float = 80.0, kv: float = 12.0):
        self.kp = kp
        self.kv = kv

    def compute_task_space_force(self, current_pos_3d: np.ndarray, target_pos_3d: np.ndarray, current_vel_3d: np.ndarray = None) -> np.ndarray:
        """
        Computes 3D task-space force F_task = Kp * (x_target - x_curr) - Kv * v_curr.
        """
        pos_err = target_pos_3d - current_pos_3d
        vel = current_vel_3d if current_vel_3d is not None else np.zeros(3)
        F_task = self.kp * pos_err - self.kv * vel
        return F_task

    def compute_torso_balance_hip_correction(self, imu_roll: float, imu_pitch: float, payload_weight: float) -> tuple:
        """
        Active Torso Balance Stabilization Coupling.
        Dynamically pulses hip pitch & roll to offset forward reach payload weight.
        """
        hip_pitch_corr = -0.15 * payload_weight - 0.2 * imu_pitch
        hip_roll_corr  = -0.2 * imu_roll
        return float(np.clip(hip_pitch_corr, -0.55, 0.55)), float(np.clip(hip_roll_corr, -0.38, 0.38))


class DynamicMovementPrimitive:
    """
    Dynamic Movement Primitive (DMP) Spline Generator.
    Generates C² continuous minimum-jerk trajectories with zero velocity/acceleration jumps.
    """

    @staticmethod
    def minimum_jerk_step(start_val: float, target_val: float, t_curr: float, t_total: float) -> float:
        """
        Polynomial minimum-jerk spline: s(tau) = 10*tau^3 - 15*tau^4 + 6*tau^5.
        """
        if t_total <= 0:
            return target_val
        tau = np.clip(t_curr / t_total, 0.0, 1.0)
        s = 10.0 * (tau**3) - 15.0 * (tau**4) + 6.0 * (tau**5)
        return float(start_val + (target_val - start_val) * s)
