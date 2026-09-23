"""
brain/carl_experiment_auditor.py — Independent Raw-Telemetry Experiment-Audit Engine

A decoupled, read-only verification engine that independently audits raw MuJoCo
simulation telemetry time-series without relying on agent self-reports or policy reward signals.

Verification States:
- VERIFIED_PASS: Raw continuous telemetry mathematically proves all criteria satisfied.
- VERIFIED_FAIL: Valid telemetry proves a failure condition (NO_PROGRESS, WALL_COLLISION, GOAL_TIMEOUT, EXCESSIVE_JERK).
- INVALID: Telemetry is physically impossible or corrupted (TELEPORTATION, VELOCITY_INCONSISTENCY, NAN_INF, CORRUPTED_DATA).
- INSUFFICIENT_EVIDENCE: Telemetry is truncated or missing required channels/timesteps.
"""

import os
import sys
import math
import hashlib
import numpy as np
import pandas as pd

class AuditVerdict:
    VERIFIED_PASS = "VERIFIED_PASS"
    VERIFIED_FAIL = "VERIFIED_FAIL"
    INVALID = "INVALID"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class CarlExperimentAuditor:
    def __init__(self,
                 max_physical_velocity: float = 2.5,
                 max_allowable_jerk: float = 120.0,
                 goal_capture_radius: float = 0.25,
                 min_required_timesteps: int = 30,
                 expected_dt: float = 0.0333):
        self.v_max_phys = max_physical_velocity
        self.jerk_max = max_allowable_jerk
        self.r_goal = goal_capture_radius
        self.min_ticks = min_required_timesteps
        self.dt_expected = expected_dt

    @staticmethod
    def compute_file_hash(filepath: str) -> str:
        """Computes SHA-256 hash of a file for immutable verification."""
        if not os.path.exists(filepath):
            return "FILE_NOT_FOUND"
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def audit_telemetry_dataframe(self, df: pd.DataFrame, require_goal: bool = False, goal_pos: tuple = None) -> dict:
        """
        Audits a pandas DataFrame containing raw simulation telemetry columns:
        [tick, time_s, pos_x, pos_y, pos_z, qvel_x, qvel_y, wheel_w_L, wheel_w_R,
         motor_cmd_L, motor_cmd_R, ncon, wall_contacts, food_dist, DA, 5HT, NE, ACh]
        """
        # 1. Check for Insufficient Evidence (Empty / Truncated / Missing essential columns)
        required_cols = ["tick", "time_s", "pos_x", "pos_y", "qvel_x", "qvel_y", "ncon", "wall_contacts"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return {
                "verdict": AuditVerdict.INSUFFICIENT_EVIDENCE,
                "reason": f"MISSING_CHANNELS: {missing_cols}",
                "details": {}
            }

        if len(df) < self.min_ticks:
            return {
                "verdict": AuditVerdict.INSUFFICIENT_EVIDENCE,
                "reason": f"TRUNCATED_TELEMETRY: Length {len(df)} < min required {self.min_ticks}",
                "details": {"num_ticks": len(df)}
            }

        # 2. Check for NaN / Inf Corruption
        numeric_cols = ["time_s", "pos_x", "pos_y", "qvel_x", "qvel_y", "ncon"]
        if df[numeric_cols].isnull().values.any() or np.isinf(df[numeric_cols].values).any():
            return {
                "verdict": AuditVerdict.INVALID,
                "reason": "NAN_INF_VALUES: Telemetry contains NaN or Infinite floating point values",
                "details": {}
            }

        # 3. Check Timestamp Monotonicity & Continuity
        times = df["time_s"].values
        dt_arr = np.diff(times)
        if (dt_arr <= 0.0).any():
            return {
                "verdict": AuditVerdict.INVALID,
                "reason": "TIMESTAMP_ANOMALY: Non-monotonic or negative time progression detected",
                "details": {"min_dt": float(np.min(dt_arr))}
            }

        if (dt_arr > 0.15).any():  # gap > 150ms
            return {
                "verdict": AuditVerdict.INSUFFICIENT_EVIDENCE,
                "reason": "TIMESTEP_GAP: Telemetry stream has missing/dropped interval > 150ms",
                "details": {"max_dt": float(np.max(dt_arr))}
            }

        # 4. Cross-Signal Kinematics Consistency: Position Displacements & Velocities
        x = df["pos_x"].values
        y = df["pos_y"].values
        step_dx = np.diff(x)
        step_dy = np.diff(y)
        step_disp = np.sqrt(step_dx**2 + step_dy**2)
        step_speeds = step_disp / np.maximum(dt_arr, 1e-4)

        max_observed_speed = float(np.max(step_speeds))
        if max_observed_speed > self.v_max_phys * 1.5:
            return {
                "verdict": AuditVerdict.INVALID,
                "reason": f"TELEPORTATION: Instantaneous speed {max_observed_speed:.2f}m/s exceeds max physical limit {self.v_max_phys}m/s",
                "details": {"max_speed_m_s": max_observed_speed}
            }

        # Check for single-step discontinuous jumps
        max_allowable_step = self.v_max_phys * np.max(dt_arr) + 0.10
        if (step_disp > max_allowable_step).any():
            return {
                "verdict": AuditVerdict.INVALID,
                "reason": f"TELEPORTATION: Single-step displacement {float(np.max(step_disp)):.3f}m exceeds kinematic envelope {max_allowable_step:.3f}m",
                "details": {"max_step_disp": float(np.max(step_disp))}
            }

        # Cross-signal check: If qvel columns exist, verify consistency with positional displacement
        if "qvel_x" in df.columns and "qvel_y" in df.columns:
            raw_vx = df["qvel_x"].values
            raw_vy = df["qvel_y"].values
            raw_speed = np.sqrt(raw_vx**2 + raw_vy**2)
            if (raw_speed > self.v_max_phys * 2.0).any():
                return {
                    "verdict": AuditVerdict.INVALID,
                    "reason": f"VELOCITY_INCONSISTENCY: Raw telemetry velocity {float(np.max(raw_speed)):.2f}m/s exceeds physical limit",
                    "details": {"max_raw_speed": float(np.max(raw_speed))}
                }
            # Check for gross mismatch between velocity signal and actual position movement
            mean_raw_speed = float(np.mean(raw_speed))
            mean_step_speed = float(np.mean(step_speeds))
            if mean_raw_speed > 1.0 and mean_step_speed < 0.05:
                return {
                    "verdict": AuditVerdict.INVALID,
                    "reason": "VELOCITY_INCONSISTENCY: Telemetry velocity indicates high speed but position remains stationary",
                    "details": {"mean_raw_speed": mean_raw_speed, "mean_step_speed": mean_step_speed}
                }

        # 5. Measure True Net Movement (Progress check)
        net_dist = math.sqrt((x[-1] - x[0])**2 + (y[-1] - y[0])**2)
        path_length = float(np.sum(step_disp))
        if path_length < 0.05:
            return {
                "verdict": AuditVerdict.VERIFIED_FAIL,
                "reason": "NO_PROGRESS: Robot produced zero net movement (< 0.05m)",
                "details": {"path_length": path_length}
            }

        # 6. Physical Wall Collision Audit
        wall_contacts = df["wall_contacts"].values
        total_wall_contacts = 0
        for wc in wall_contacts:
            if isinstance(wc, (int, float, np.number)):
                total_wall_contacts += int(wc)
            elif isinstance(wc, str):
                if wc.strip() and wc.strip() not in ["0", "False", "none", "[]"]:
                    total_wall_contacts += 1
            elif isinstance(wc, bool) and wc:
                total_wall_contacts += 1

        if total_wall_contacts > 0:
            return {
                "verdict": AuditVerdict.VERIFIED_FAIL,
                "reason": f"WALL_COLLISION: Detected {total_wall_contacts} physical wall contact events",
                "details": {"total_wall_contacts": total_wall_contacts}
            }

        # 7. Jerk Derivative Chain Audit (Actuator Commanded & Wheel Jerk in rad/s³)
        if "motor_cmd_L" in df.columns and "motor_cmd_R" in df.columns:
            uL = df["motor_cmd_L"].values
            uR = df["motor_cmd_R"].values
            jerk_L = np.gradient(np.gradient(uL, times), times)
            jerk_R = np.gradient(np.gradient(uR, times), times)
            jerk_mag = np.maximum(np.abs(jerk_L), np.abs(jerk_R))
        elif "wheel_w_L" in df.columns and "wheel_w_R" in df.columns:
            wL = df["wheel_w_L"].values
            wR = df["wheel_w_R"].values
            jerk_L = np.gradient(np.gradient(wL, times), times)
            jerk_R = np.gradient(np.gradient(wR, times), times)
            jerk_mag = np.maximum(np.abs(jerk_L), np.abs(jerk_R))
        else:
            vx_grad = np.gradient(x, times)
            vy_grad = np.gradient(y, times)
            ax_grad = np.gradient(vx_grad, times)
            ay_grad = np.gradient(vy_grad, times)
            jx_grad = np.gradient(ax_grad, times)
            jy_grad = np.gradient(ay_grad, times)
            jerk_mag = np.sqrt(jx_grad**2 + jy_grad**2)

        # Ignore initial 2 ticks and end 2 ticks transient from numerical gradient boundary
        if len(jerk_mag) > 4:
            eval_jerk = jerk_mag[2:-2]
        else:
            eval_jerk = jerk_mag

        max_jerk = float(np.max(eval_jerk)) if len(eval_jerk) > 0 else 0.0
        avg_jerk = float(np.mean(eval_jerk)) if len(eval_jerk) > 0 else 0.0

        if max_jerk > self.jerk_max:
            return {
                "verdict": AuditVerdict.VERIFIED_FAIL,
                "reason": f"EXCESSIVE_JERK: Peak jerk {max_jerk:.2f} rad/s³ exceeds threshold {self.jerk_max:.1f} rad/s³",
                "details": {"max_jerk": max_jerk, "avg_jerk": avg_jerk, "path_length_m": round(path_length, 3)}
            }

        # 8. Goal Attainment Verification (if required)
        if require_goal and goal_pos is not None:
            dist_to_goal = np.sqrt((x - goal_pos[0])**2 + (y - goal_pos[1])**2)
            min_dist = float(np.min(dist_to_goal))
            if min_dist > self.r_goal:
                return {
                    "verdict": AuditVerdict.VERIFIED_FAIL,
                    "reason": f"GOAL_TIMEOUT: Robot failed to reach goal (closest approach {min_dist:.3f}m > {self.r_goal:.3f}m)",
                    "details": {"closest_approach_m": min_dist, "goal_pos": goal_pos}
                }

        # ALL CRITERIA SATISFIED AND MATHEMATICALLY VERIFIED FROM RAW TELEMETRY
        return {
            "verdict": AuditVerdict.VERIFIED_PASS,
            "reason": "ALL_CRITERIA_VERIFIED_FROM_RAW_TELEMETRY",
            "details": {
                "path_length_m": round(path_length, 3),
                "net_displacement_m": round(net_dist, 3),
                "max_speed_m_s": round(float(np.max(step_speeds)), 3),
                "max_jerk_rad_s3": round(max_jerk, 2),
                "avg_jerk_rad_s3": round(avg_jerk, 2),
                "wall_collisions": 0,
                "ticks_audited": len(df)
            }
        }
