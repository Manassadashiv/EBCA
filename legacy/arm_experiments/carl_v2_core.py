"""
=============================================================================
CARL-v2 MASTER CORE: OPERATIONAL SPACE CONTROL + TACTILE ADMITTANCE ENGINE
=============================================================================
Author: Advanced Biomimetic Agentic AI
Architecture: Operational Space Control (OSC) + Force-Regulated Admittance
"""

import math
import numpy as np
import mujoco

class OperationalSpaceController:
    """
    Operational Space Controller (OSC / Differential Kinematics)
    Maps 3D Task-Space Velocities (v_x, v_y, v_z) to Joint Velocity Commands.
    """
    def __init__(self, model: mujoco.MjModel, site_name: str = "touch_site_L"):
        self.model = model
        self.site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        self.jacp = np.zeros((3, model.nv))
        self.jacr = np.zeros((3, model.nv))

    def compute_joint_velocities(self, data: mujoco.MjData, target_velocity_3d: np.ndarray, damping: float = 1e-4) -> np.ndarray:
        """
        Computes joint velocities via Damped Least Squares (DLS) Pseudo-Inverse:
        q_dot = J^T (J J^T + λ^2 I)^-1 v_target
        """
        mujoco.mj_jacSite(self.model, data, self.jacp, self.jacr, self.site_id)
        J = self.jacp[:, :5]  # 5 arm joint DOFs
        
        # Damped Least Squares Inversion
        JJT = J @ J.T + damping * np.eye(3)
        J_pinv = J.T @ np.linalg.inv(JJT)
        
        q_dot = J_pinv @ target_velocity_3d
        return q_dot


class TactileAdmittanceController:
    """
    Tactile Admittance Controller (Force-Regulated Clamping)
    Dynamically adjusts finger joint positions to regulate target contact force (F_target).
    """
    def __init__(self, k_adm: float = 0.002, d_adm: float = 0.01, max_clamp: float = 0.52):
        self.k_adm = k_adm
        self.d_adm = d_adm
        self.max_clamp = max_clamp
        self.current_clamp = 0.0

    def step(self, f_target: float, f_measured: float, dt: float = 0.01) -> float:
        """
        Admittance Control Step:
        Δpos = K_adm * (F_target - F_measured)
        """
        f_error = f_target - f_measured
        delta_pos = self.k_adm * f_error
        
        self.current_clamp = np.clip(self.current_clamp + delta_pos, 0.0, self.max_clamp)
        return float(self.current_clamp)


def run_carl_v2_control_step(model, data, osc_controller, admittance_controller, action_4d):
    """
    Executes a single CARL-v2 Operational Space + Admittance Control Step.
    
    Action Vector:
        action_4d[0:3] = [v_x, v_y, v_z]  (End-Effector Task Velocity)
        action_4d[3]   = F_target         (Target Finger Clamp Force in Newtons)
    """
    v_ee_target = action_4d[0:3]
    f_target = action_4d[3]

    # 1. Operational Space Control for Arm Joints
    q_dot_arm = osc_controller.compute_joint_velocities(data, v_ee_target)

    # 2. Tactile Admittance Control for Finger Joints
    touch_f1 = float(data.sensor("touch_L").data[0])
    touch_f2 = float(data.sensor("touch_bot_L").data[0])
    touch_f3 = float(data.sensor("touch_thumb_L").data[0])
    f_avg_measured = (touch_f1 + touch_f2 + touch_f3) / 3.0

    clamp_angle = admittance_controller.step(f_target, f_avg_measured)

    # 3. Construct Final Actuator Commands
    ctrl_out = np.zeros(model.nu)
    # Arm joint position integration: q_target = q_curr + q_dot * dt
    ctrl_out[0:4] = data.qpos[0:4] + q_dot_arm[0:4] * 0.01
    ctrl_out[4] = clamp_angle  # Top finger
    ctrl_out[5] = clamp_angle  # Thumb finger

    return ctrl_out
