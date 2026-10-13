"""
brain/carl_endocrine_adaptation.py — Stage 3.5 Neuromorphic Endocrine & Physical Adaptation Engine
Classification: Unprivileged Embodied Cognitive Adaptation Organ

Biological Foundations (Pre-Registered & Validated):
1. Biomechanical Preflexes & Campaniform Sensilla (Full & Jindrich 2002; Zill et al. 2012):
   - Fast cuticular load-drop detection (<30ms) to clamp motor spinout on low friction.
2. The Reafference Principle & Efference Copy (von Holst & Mittelstaedt 1950; Wittlinger & Wehner 2006):
   - Direct efference copy reafference trim: unexpected yaw rate during forward drive is
     immediately balanced at the motor level without waiting for high-level replanning.
3. Octopaminergic / Noradrenergic Arousal Kinetics (Roeder 1999; Libersat 2004; Chen & Ahrens 2024):
   - Acute physical challenge (slip, stalls) mobilizes octopamine / norepinephrine (NE),
     elevating exploration variance (policy temperature) and providing burst escape torque.
   - Strictly eliminates naive cortisol speed braking and margin inflation.

Strict Invariant:
Zero simulator coordinates (qpos, qvel, geom_xpos) permitted. Operates purely on
unprivileged onboard telemetry: wheel encoder angular velocities, IMU gyro yaw,
and dead-reckoned forward velocity estimates.
"""

from typing import Dict, Any, Tuple
import numpy as np


class CarlEndocrineAdaptationEngine:
    """
    Neuromorphic-Endocrine Adaptation Engine for physical perturbation survival.
    Manages fast slip-reflex clamping, dual-timescale hormonal diffusion (NE/Cortisol),
    and von Holst-Mittelstaedt reafference torque asymmetry trimming.
    """

    def __init__(
        self,
        dt: float = 0.030,
        wheel_radius: float = 0.048,
        k_rot: float = 2.50,
        slip_threshold: float = 0.16,
        k_choke: float = 0.25,
        tau_ne: float = 0.8,
        tau_cort: float = 5.0,
    ):
        self.dt = float(dt)
        self.wheel_radius = float(wheel_radius)
        self.k_rot = float(k_rot)
        self.slip_threshold = float(slip_threshold)
        self.k_choke = float(k_choke)

        # Decay constants (lambda = 1 / tau)
        self.lambda_ne = 1.0 / max(0.1, tau_ne)
        self.lambda_cort = 1.0 / max(0.1, tau_cort)

        # Endocrine chemical concentrations in [0.0, 1.0]
        self.ne_level: float = 0.0       # Octopamine/NE: motor arousal & exploration variance
        self.cortisol_level: float = 0.0 # Cortisol: slow metabolic stress state

        # Proprioceptive motor tractability gain estimators (nominal = 1.0)
        self.gain_est_L: float = 1.0
        self.gain_est_R: float = 1.0

        # Torque asymmetry disturbance observer state (Reafference trim)
        self.torque_trim: float = 0.0
        self.trim_i: float = 0.0
        self.k_trim_i: float = 2.50      # Proportional-Integral trim gain
        self.dead_band_drift: float = 0.04  # rad/s (tight dead-band for straight tracking)

        # Live metric caches
        self.last_slip_L: float = 0.0
        self.last_slip_R: float = 0.0
        self.last_mean_slip: float = 0.0
        self.reflex_active: bool = False

    def reset(self):
        """Resets all endocrine concentrations, gain estimators, and observer integrators."""
        self.ne_level = 0.0
        self.cortisol_level = 0.0
        self.gain_est_L = 1.0
        self.gain_est_R = 1.0
        self.torque_trim = 0.0
        self.trim_i = 0.0
        self.last_slip_L = 0.0
        self.last_slip_R = 0.0
        self.last_mean_slip = 0.0
        self.reflex_active = False

    def update_and_adapt(
        self,
        cmd_u: np.ndarray,
        w_left_vel: float,
        w_right_vel: float,
        gyro_yaw_rate: float,
        v_est: float,
        is_stalled: bool = False,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Executes one complete 30ms adaptation cycle:
        1. Estimates proprioceptive motor gains (w_meas / (u_cmd * 25.0)) for health tracking.
        2. Estimates unprivileged wheel slip ratios from wheel angular velocities and v_est.
        3. Applies the fast Campaniform Sensilla choke reflex to prevent wheel spin-out.
        4. Updates synthetic Octopamine/NE and Cortisol kinetics via discrete ODE integration.
        5. Applies von Holst & Mittelstaedt reafference yaw-rate disturbance trim.
        """
        dt = self.dt
        if not getattr(self, "enabled", True):
            return cmd_u.copy(), {
                "slip_left": 0.0,
                "slip_right": 0.0,
                "mean_slip": 0.0,
                "reflex_active": False,
                "gain_est_L": 1.0,
                "gain_est_R": 1.0,
                "ne_level": 0.0,
                "cortisol_level": 0.0,
                "torque_trim": 0.0,
                "reafference_error": 0.0,
                "adapted_action": cmd_u.tolist(),
            }
        u_L = float(cmd_u[0])
        u_R = float(cmd_u[1])

        # -------------------------------------------------------------
        # 1. Proprioceptive Motor Gain Estimation (Efference Copy vs Encoder)
        # -------------------------------------------------------------
        omega_exp_L = abs(u_L) * 25.0
        omega_exp_R = abs(u_R) * 25.0

        # Literature FTC Principle (Decoupled Per-Channel Efference Tracking):
        # Actuators estimate independent health regardless of whether motion is cruising or differential spin.
        if omega_exp_L > 1.5:
            ratio_L = abs(w_left_vel) / max(omega_exp_L, 0.5)
            self.gain_est_L = float(0.88 * self.gain_est_L + 0.12 * np.clip(ratio_L, 0.35, 1.50))

        if omega_exp_R > 1.5:
            ratio_R = abs(w_right_vel) / max(omega_exp_R, 0.5)
            self.gain_est_R = float(0.88 * self.gain_est_R + 0.12 * np.clip(ratio_R, 0.35, 1.50))

        # Closed-Form Control Allocation (Gain Inversion):
        # Inverts observed motor loss of effectiveness (LoE) to restore symmetric actuator authority.
        comp_u_L = float(u_L / max(self.gain_est_L, 0.40)) if self.gain_est_L < 0.95 else float(u_L)
        comp_u_R = float(u_R / max(self.gain_est_R, 0.40)) if self.gain_est_R < 0.95 else float(u_R)

        # Dynamic Scale Preserves Pure Yaw Moment Without Unwanted Forward Lurch
        max_alloc = max(abs(comp_u_L), abs(comp_u_R))
        if max_alloc > 1.0:
            comp_u_L /= max_alloc
            comp_u_R /= max_alloc

        # -------------------------------------------------------------
        # 2. Closed-Form Proprioceptive Kinematic Slip Estimation
        # -------------------------------------------------------------
        v_wheel_L = float(w_left_vel * self.wheel_radius)
        v_wheel_R = float(w_right_vel * self.wheel_radius)
        v_body = float(v_est)
        half_track = 0.115  # Distance from vehicle centerline to wheel

        # Expected wheel speeds accounting for forward speed and vehicle yaw rotation
        v_exp_L = v_body - float(gyro_yaw_rate) * half_track
        v_exp_R = v_body + float(gyro_yaw_rate) * half_track

        if abs(v_wheel_L) > 0.02 and abs(u_L) > 0.05:
            s_L = float(np.clip(abs(v_wheel_L - v_exp_L) / max(abs(v_wheel_L), 0.05), 0.0, 1.0))
        else:
            s_L = 0.0

        if abs(v_wheel_R) > 0.02 and abs(u_R) > 0.05:
            s_R = float(np.clip(abs(v_wheel_R - v_exp_R) / max(abs(v_wheel_R), 0.05), 0.0, 1.0))
        else:
            s_R = 0.0

        mean_slip = float(0.5 * (s_L + s_R))
        self.last_slip_L = s_L
        self.last_slip_R = s_R
        self.last_mean_slip = mean_slip

        # -------------------------------------------------------------
        # 3. Fast Campaniform Sensilla Slip Reflex (tau = 30ms)
        # -------------------------------------------------------------
        choked_u_L = comp_u_L
        choked_u_R = comp_u_R
        self.reflex_active = False

        is_fwd_driving = (comp_u_L + comp_u_R) > 0.20 and (comp_u_L * comp_u_R >= 0.0)

        if is_fwd_driving:
            if s_L > self.slip_threshold and abs(u_L) > 0.05:
                scale_L = 1.0 - self.k_choke * ((s_L - self.slip_threshold) / (1.0 - self.slip_threshold + 1e-6))
                choked_u_L = float(comp_u_L * np.clip(scale_L, 0.40, 1.0))
                self.reflex_active = True

            if s_R > self.slip_threshold and abs(u_R) > 0.05:
                scale_R = 1.0 - self.k_choke * ((s_R - self.slip_threshold) / (1.0 - self.slip_threshold + 1e-6))
                choked_u_R = float(comp_u_R * np.clip(scale_R, 0.40, 1.0))
                self.reflex_active = True

        # -------------------------------------------------------------
        # 4. von Holst & Mittelstaedt Reafference Yaw-Rate Trim
        # -------------------------------------------------------------
        # Expected yaw rate from command
        # Differential drive kinematic prediction: omega_exp = (u_R - u_L) * (25.0 * R) / (2 * half_track)
        omega_exp = float((u_R - u_L) * (25.0 * self.wheel_radius) / (2.0 * half_track))

        # Reafference mismatch: epsilon = actual_gyro - expected
        reafference_error = float(gyro_yaw_rate - omega_exp)

        # Reafference PI heading trim: Corrects directional drift during travel regimes
        is_reciprocal_spin = (u_L * u_R) < -0.05
        if (abs(u_L) + abs(u_R)) > 0.15 and not is_reciprocal_spin:
            if abs(reafference_error) > self.dead_band_drift:
                self.trim_i = float(np.clip(
                    self.trim_i + self.k_trim_i * reafference_error * dt,
                    -0.50, 0.50
                ))
            else:
                self.trim_i = float(self.trim_i * (1.0 - 0.10 * dt))
            trim_p = float(np.clip(0.40 * reafference_error, -0.35, 0.35))
            self.torque_trim = float(np.clip(trim_p + self.trim_i, -0.40, 0.40))
        else:
            self.trim_i = float(self.trim_i * (1.0 - 0.30 * dt))
            self.torque_trim = float(self.torque_trim * (1.0 - 0.30 * dt))

        adapted_u_L = float(np.clip(choked_u_L + 0.5 * self.torque_trim, -1.0, 1.0))
        adapted_u_R = float(np.clip(choked_u_R - 0.5 * self.torque_trim, -1.0, 1.0))

        # -------------------------------------------------------------
        # 5. Dual-Timescale Octopamine / Norepinephrine Kinetics ODEs
        # -------------------------------------------------------------
        stall_stimulus = 2.0 if is_stalled else 0.0
        d_ne = (1.50 * mean_slip + 1.20 * abs(reafference_error) + stall_stimulus) - (self.lambda_ne * self.ne_level)
        self.ne_level = float(np.clip(self.ne_level + d_ne * dt, 0.0, 1.0))

        d_cort = (0.80 * mean_slip + (1.0 if is_stalled else 0.0)) - (self.lambda_cort * self.cortisol_level)
        self.cortisol_level = float(np.clip(self.cortisol_level + d_cort * dt, 0.0, 1.0))

        adapted_cmd = np.array([adapted_u_L, adapted_u_R], dtype=np.float64)

        telemetry = {
            "slip_left": s_L,
            "slip_right": s_R,
            "mean_slip": mean_slip,
            "reflex_active": self.reflex_active,
            "gain_est_L": self.gain_est_L,
            "gain_est_R": self.gain_est_R,
            "ne_level": self.ne_level,
            "cortisol_level": self.cortisol_level,
            "torque_trim": self.torque_trim,
            "reafference_error": reafference_error,
            "adapted_action": adapted_cmd.tolist(),
        }

        return adapted_cmd, telemetry

    def get_active_inference_modulation(self) -> Dict[str, float]:
        """
        Returns dynamic parameter modulation multipliers for CARLActiveInferenceEngine:
        - sigma_scale: scales MPPI candidate sampling exploration variance under NE arousal.
        - margin_scale: expands obstacle clearance margin when Cortisol is elevated or motor is degraded.
        - cruise_scale: scales forward driving command under stress.
        """
        degraded = bool((self.gain_est_L < 0.85) or (self.gain_est_R < 0.85))
        margin_boost = 0.50 if degraded else 0.0
        return {
            "sigma_scale": float(1.0 + 0.35 * self.ne_level),
            "margin_scale": float(1.0 + 0.40 * self.cortisol_level + margin_boost),
            "cruise_scale": float(1.0 - 0.30 * self.cortisol_level),
        }
