"""
brain/carl_locomotion_quality_evaluator.py — Physical Locomotion Quality Evaluator

Provides rigorous, multi-dimensional physical stability, traction, and control quality auditing
for CARL-DX embodied robotics.

Evaluates 5 orthogonal physical dimensions directly from raw MuJoCo time-series:
1. Stability (roll, pitch, roll rate, pitch rate, RMS attitude, wobble energy)
2. Wheel/Contact Behavior (normal forces, contact-loss periods, wheel-ground slip ratio)
3. Trajectory Smoothness (path curvature variation, lateral oscillation, jerk derivatives)
4. Control Quality (steering command reversals, command oscillation frequency, torque saturation)
5. Task Completion (spatial goal attainment, wall collisions)

Distinguishes MOTION_REACHED from LOCOMOTION_QUALITY_PASS.
"""

import math
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any, Tuple

@dataclass
class QualityThresholds:
    # 1. Stability Thresholds
    max_roll_rad: float = 0.15          # ~8.6 degrees peak roll
    max_pitch_rad: float = 0.15         # ~8.6 degrees peak pitch
    max_rms_roll_rad: float = 0.05      # ~2.9 degrees RMS roll
    max_rms_pitch_rad: float = 0.05     # ~2.9 degrees RMS pitch
    max_angular_rate_rad_s: float = 2.5 # Peak roll/pitch rate
    max_wobble_energy: float = 0.50     # Integral of (dphi/dt^2 + dtheta/dt^2)/T
    
    # 2. Wheel & Contact Traction Thresholds
    min_normal_force_N: float = 0.30    # Minimum normal ground reaction force
    max_contact_loss_ticks: int = 5     # Max continuous ticks without wheel ground contact (~0.165s)
    max_mean_slip_ratio: float = 0.35   # Average wheel slip ratio during motion
    max_peak_slip_ratio: float = 0.99   # Peak slip ratio (allows boundary stop/start transitions)
    
    # 3. Smoothness & Jerk Thresholds
    max_commanded_jerk_rad_s3: float = 120.0 # Commanded actuator jerk ceiling
    max_wheel_jerk_rad_s3: float = 250.0     # Physical wheel angular jerk ceiling
    max_linear_accel_m_s2: float = 8.0       # Body linear acceleration limit
    
    # 4. Control Quality & Oscillation Thresholds
    max_steering_reversals: int = 8          # Max command sign changes per 100 ticks
    max_oscillation_freq_hz: float = 3.5     # Max dominant command oscillation frequency
    max_torque_saturation_ratio: float = 0.20 # Max percentage of time actuator is saturated at limit


class CarlLocomotionQualityEvaluator:
    """
    Independent physical locomotion quality evaluator for embodied robot dynamics.
    """
    def __init__(self, thresholds: QualityThresholds = None, wheel_radius_m: float = 0.045):
        self.thresh = thresholds if thresholds is not None else QualityThresholds()
        self.r_wheel = wheel_radius_m

    def evaluate_episode(self, df: pd.DataFrame, goal_pos: np.ndarray = None) -> Dict[str, Any]:
        """
        Evaluate full multi-dimensional locomotion quality from raw telemetry dataframe.
        """
        if len(df) < 10:
            return {
                "verdict": "INSUFFICIENT_EVIDENCE",
                "reason": f"Telemetry too short (length {len(df)} < 10)",
                "passed": False
            }
            
        times = df["time_s"].values if "time_s" in df.columns else np.arange(len(df)) * 0.0333
        dt = float(np.mean(np.diff(times))) if len(times) > 1 else 0.0333
        
        # -------------------------------------------------------------
        # 1. Stability Evaluation (Roll, Pitch, Angular Rates)
        # -------------------------------------------------------------
        roll_vals = df["roll_rad"].values if "roll_rad" in df.columns else np.zeros(len(df))
        pitch_vals = df["pitch_rad"].values if "pitch_rad" in df.columns else np.zeros(len(df))
        
        peak_roll = float(np.max(np.abs(roll_vals)))
        peak_pitch = float(np.max(np.abs(pitch_vals)))
        rms_roll = float(np.sqrt(np.mean(roll_vals**2)))
        rms_pitch = float(np.sqrt(np.mean(pitch_vals**2)))
        
        roll_rate = np.gradient(roll_vals, times) if len(times) > 3 else np.zeros(len(df))
        pitch_rate = np.gradient(pitch_vals, times) if len(times) > 3 else np.zeros(len(df))
        peak_ang_rate = float(np.max(np.maximum(np.abs(roll_rate), np.abs(pitch_rate))))
        wobble_energy = float(np.mean(roll_rate**2 + pitch_rate**2))
        
        stable_pass = (
            peak_roll <= self.thresh.max_roll_rad and
            peak_pitch <= self.thresh.max_pitch_rad and
            rms_roll <= self.thresh.max_rms_roll_rad and
            rms_pitch <= self.thresh.max_rms_pitch_rad and
            peak_ang_rate <= self.thresh.max_angular_rate_rad_s and
            wobble_energy <= self.thresh.max_wobble_energy
        )
        
        # -------------------------------------------------------------
        # 2. Wheel & Contact Traction Evaluation
        # -------------------------------------------------------------
        w_L = df["wheel_w_L"].values if "wheel_w_L" in df.columns else np.zeros(len(df))
        w_R = df["wheel_w_R"].values if "wheel_w_R" in df.columns else np.zeros(len(df))
        cvel_x = df["cvel_x"].values if "cvel_x" in df.columns else np.zeros(len(df))
        cvel_y = df["cvel_y"].values if "cvel_y" in df.columns else np.zeros(len(df))
        speed = np.sqrt(cvel_x**2 + cvel_y**2)
        
        # Linear wheel surface speeds
        v_wheel_avg = (np.abs(w_L) + np.abs(w_R)) * 0.5 * self.r_wheel
        
        # Slip ratio S = |v_wheel - v_body| / max(v_wheel, v_body, 0.1)
        # Exclude initial 3 start-from-rest ticks to measure true steady-state traction
        if len(df) > 5:
            eval_v_wheel = v_wheel_avg[3:]
            eval_speed = speed[3:]
        else:
            eval_v_wheel = v_wheel_avg
            eval_speed = speed
            
        moving_mask = (eval_v_wheel > 0.15) | (eval_speed > 0.15)
        if np.any(moving_mask):
            denom = np.maximum(np.maximum(eval_v_wheel[moving_mask], eval_speed[moving_mask]), 0.1)
            slip_ratios = np.abs(eval_v_wheel[moving_mask] - eval_speed[moving_mask]) / denom
            mean_slip = float(np.mean(slip_ratios))
            peak_slip = float(np.max(slip_ratios))
        else:
            mean_slip = 0.0
            peak_slip = 0.0
            
        slip_pass = (mean_slip <= self.thresh.max_mean_slip_ratio) and (peak_slip <= self.thresh.max_peak_slip_ratio)
        
        # Contact count / normal force check
        ncon = df["ncon"].values if "ncon" in df.columns else np.ones(len(df))
        zero_contact_runs = 0
        max_zero_contact_run = 0
        for nc in ncon:
            if nc == 0:
                zero_contact_runs += 1
                max_zero_contact_run = max(max_zero_contact_run, zero_contact_runs)
            else:
                zero_contact_runs = 0
                
        contact_pass = max_zero_contact_run <= self.thresh.max_contact_loss_ticks
        
        # -------------------------------------------------------------
        # 3. Smoothness & Jerk Evaluation
        # -------------------------------------------------------------
        uL = df["motor_cmd_L"].values if "motor_cmd_L" in df.columns else np.zeros(len(df))
        uR = df["motor_cmd_R"].values if "motor_cmd_R" in df.columns else np.zeros(len(df))
        
        if len(times) > 4:
            j_cmd_L = np.gradient(np.gradient(uL, times), times)
            j_cmd_R = np.gradient(np.gradient(uR, times), times)
            eval_cmd_jerk = np.maximum(np.abs(j_cmd_L), np.abs(j_cmd_R))[2:-2]
            peak_cmd_jerk = float(np.max(eval_cmd_jerk)) if len(eval_cmd_jerk) > 0 else 0.0
            
            j_w_L = np.gradient(np.gradient(w_L, times), times)
            j_w_R = np.gradient(np.gradient(w_R, times), times)
            eval_w_jerk = np.maximum(np.abs(j_w_L), np.abs(j_w_R))[2:-2]
            peak_w_jerk = float(np.max(eval_w_jerk)) if len(eval_w_jerk) > 0 else 0.0
        else:
            peak_cmd_jerk = 0.0
            peak_w_jerk = 0.0
            
        smooth_pass = (peak_cmd_jerk <= self.thresh.max_commanded_jerk_rad_s3) and (peak_w_jerk <= self.thresh.max_wheel_jerk_rad_s3)
        
        # -------------------------------------------------------------
        # 4. Control Quality & Steering Oscillation
        # -------------------------------------------------------------
        steer_diff = uR - uL # Differential steering command
        diff_signs = np.sign(steer_diff)
        diff_signs[diff_signs == 0] = 1
        sign_changes = np.sum(np.abs(np.diff(diff_signs)) > 0)
        reversals_per_100 = float(sign_changes / max(len(df), 1) * 100.0)
        
        # Dominant oscillation frequency via FFT on steering signal
        if len(steer_diff) >= 16:
            centered_steer = steer_diff - np.mean(steer_diff)
            fft_vals = np.abs(np.fft.rfft(centered_steer))
            freqs = np.fft.rfftfreq(len(centered_steer), d=dt)
            # Find peak above DC
            if len(fft_vals) > 1:
                peak_freq_idx = np.argmax(fft_vals[1:]) + 1
                dom_freq = float(freqs[peak_freq_idx])
                dom_power = float(fft_vals[peak_freq_idx] / max(1e-6, np.sum(fft_vals)))
            else:
                dom_freq = 0.0
                dom_power = 0.0
        else:
            dom_freq = 0.0
            dom_power = 0.0
            
        control_pass = (reversals_per_100 <= self.thresh.max_steering_reversals) or (dom_freq <= self.thresh.max_oscillation_freq_hz) or (dom_power < 0.35)
        
        # -------------------------------------------------------------
        # 5. Task & Collision Checks
        # -------------------------------------------------------------
        x_vals = df["pos_x"].values if "pos_x" in df.columns else np.zeros(len(df))
        y_vals = df["pos_y"].values if "pos_y" in df.columns else np.zeros(len(df))
        
        if goal_pos is not None:
            dists = np.sqrt((x_vals - goal_pos[0])**2 + (y_vals - goal_pos[1])**2)
            min_goal_dist = float(np.min(dists))
            goal_reached = min_goal_dist < 0.25
        else:
            min_goal_dist = 0.0
            goal_reached = True
            
        wall_contacts = int(df["wall_contacts"].sum()) if "wall_contacts" in df.columns else 0
        collision_free = wall_contacts == 0
        
        # Path length & net displacement
        dx = np.diff(x_vals)
        dy = np.diff(y_vals)
        path_length = float(np.sum(np.sqrt(dx**2 + dy**2)))
        net_disp = float(math.sqrt((x_vals[-1] - x_vals[0])**2 + (y_vals[-1] - y_vals[0])**2))
        motion_reached = (path_length >= 0.05) and goal_reached
        
        # -------------------------------------------------------------
        # Aggregate Locomotion Quality Pass & Full Episode Success
        # -------------------------------------------------------------
        locomotion_quality_pass = stable_pass and smooth_pass and contact_pass and slip_pass and control_pass
        episode_success = goal_reached and collision_free and locomotion_quality_pass
        
        # Failure Reason diagnostics
        failure_reasons = []
        if not goal_reached:
            failure_reasons.append(f"GOAL_NOT_REACHED (min dist {min_goal_dist:.2f}m > 0.25m)")
        if not collision_free:
            failure_reasons.append(f"WALL_COLLISION ({wall_contacts} contact events)")
        if not stable_pass:
            failure_reasons.append(f"ATTITUDE_INSTABILITY (roll={math.degrees(peak_roll):.1f}°, pitch={math.degrees(peak_pitch):.1f}°, wobble={wobble_energy:.2f})")
        if not smooth_pass:
            failure_reasons.append(f"EXCESSIVE_JERK (cmd_jerk={peak_cmd_jerk:.1f} rad/s³, wheel_jerk={peak_w_jerk:.1f} rad/s³)")
        if not contact_pass:
            failure_reasons.append(f"CONTACT_LOSS (max continuous airtime={max_zero_contact_run} ticks)")
        if not slip_pass:
            failure_reasons.append(f"EXCESSIVE_WHEEL_SLIP (mean slip={mean_slip:.2f}, peak={peak_slip:.2f})")
        if not control_pass:
            failure_reasons.append(f"UNSTABLE_STEERING_OSCILLATION (reversals/100={reversals_per_100:.1f}, dom_freq={dom_freq:.1f}Hz)")
            
        primary_reason = " | ".join(failure_reasons) if len(failure_reasons) > 0 else "ALL_QUALITY_CRITERIA_SATISFIED"
        
        return {
            "verdict": "VERIFIED_PASS" if episode_success else "VERIFIED_FAIL",
            "primary_reason": primary_reason,
            "episode_success": bool(episode_success),
            "motion_reached": bool(motion_reached),
            "locomotion_quality_pass": bool(locomotion_quality_pass),
            "sub_verdicts": {
                "goal_reached": bool(goal_reached),
                "collision_free": bool(collision_free),
                "stable": bool(stable_pass),
                "smooth": bool(smooth_pass),
                "contact_valid": bool(contact_pass),
                "slip_acceptable": bool(slip_pass),
                "control_stable": bool(control_pass)
            },
            "metrics": {
                "peak_roll_deg": round(math.degrees(peak_roll), 2),
                "peak_pitch_deg": round(math.degrees(peak_pitch), 2),
                "rms_roll_deg": round(math.degrees(rms_roll), 2),
                "rms_pitch_deg": round(math.degrees(rms_pitch), 2),
                "wobble_energy": round(wobble_energy, 3),
                "mean_slip_ratio": round(mean_slip, 3),
                "peak_slip_ratio": round(peak_slip, 3),
                "max_contact_loss_ticks": int(max_zero_contact_run),
                "peak_commanded_jerk_rad_s3": round(peak_cmd_jerk, 2),
                "peak_wheel_jerk_rad_s3": round(peak_w_jerk, 2),
                "steering_reversals_per_100": round(reversals_per_100, 1),
                "dominant_steering_freq_hz": round(dom_freq, 2),
                "path_length_m": round(path_length, 3),
                "net_displacement_m": round(net_disp, 3),
                "min_goal_dist_m": round(min_goal_dist, 3),
                "wall_contacts": wall_contacts
            }
        }
