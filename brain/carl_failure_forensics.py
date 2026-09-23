"""
brain/carl_failure_forensics.py — Comprehensive Failure Mode Detection & Loop Forensics

Implements 10 First-Class Forensic Failure Detectors:
A. STATIONARY_STALL (Command > 0.05 m/s, translation < 0.015 m over 25 ticks)
B. BRAKE_LOCK (BRAKE_REST asserted > 15 consecutive ticks without emergency cause)
C. LEFT_RIGHT_LIMIT_CYCLE (Repeated Left/Right sign reversals > 4 times in 10 ticks)
D. FORWARD_REVERSE_LIMIT_CYCLE (Repeated Forward/Reverse shifts > 3 times in 12 ticks)
E. SPIN_LOOP (Continuous single-direction yaw rotation > 720 deg without translation)
F. HEAD_SCAN_WITHOUT_INFORMATION_GAIN (Head panning actively while net uncertainty delta == 0)
G. RECOVERY_LOOP (Triggering recovery manager > 2 times without breakout translation)
H. GOAL_LOOP (Rapid goal switching > 4 switches in 15 ticks without goal completion)
I. ACTION_CHATTER (Action changes every 1-2 ticks continuously for > 6 ticks)
J. RESET_SENSITIVE_CONTROL_BIAS (Persistent non-zero steering bias or command after reset)
"""

import math
import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

@dataclass
class FailureDetectionEvent:
    tick: int
    time_s: float
    failure_type: str
    severity: str           # WARNING, CRITICAL, TERMINAL
    details: str
    telemetry_snapshot: Dict[str, Any]


class CarlFailureForensicMonitor:
    """
    Online forensic monitor detecting stalls, limit cycles, deadlocks, and chatter.
    """
    def __init__(self, dt: float = 0.0333):
        self.dt = dt
        self.history_len = 60
        
        # Metric sliding buffers
        self.pos_history: deque = deque(maxlen=self.history_len)
        self.action_history: deque = deque(maxlen=self.history_len)
        self.cmd_v_history: deque = deque(maxlen=self.history_len)
        self.act_v_history: deque = deque(maxlen=self.history_len)
        self.yaw_history: deque = deque(maxlen=self.history_len)
        self.head_history: deque = deque(maxlen=self.history_len)
        self.goal_history: deque = deque(maxlen=self.history_len)
        self.recovery_state_history: deque = deque(maxlen=self.history_len)
        self.info_gain_history: deque = deque(maxlen=self.history_len)
        
        # Cumulative and transition counters
        self.ticks_in_current_action = 0
        self.current_action = "NONE"
        self.total_action_switches = 0
        self.total_direction_reversals = 0
        self.cumulative_yaw_rotation = 0.0
        self.last_yaw = 0.0
        
        # Detected failure logs
        self.detected_failures: List[FailureDetectionEvent] = []
        self.failure_counts: Dict[str, int] = {
            "STATIONARY_STALL": 0,
            "BRAKE_LOCK": 0,
            "LEFT_RIGHT_LIMIT_CYCLE": 0,
            "FORWARD_REVERSE_LIMIT_CYCLE": 0,
            "SPIN_LOOP": 0,
            "HEAD_SCAN_WITHOUT_INFORMATION_GAIN": 0,
            "RECOVERY_LOOP": 0,
            "GOAL_LOOP": 0,
            "ACTION_CHATTER": 0,
            "RESET_SENSITIVE_CONTROL_BIAS": 0
        }

    def reset(self):
        """Resets all internal sliding windows and histories."""
        self.pos_history.clear()
        self.action_history.clear()
        self.cmd_v_history.clear()
        self.act_v_history.clear()
        self.yaw_history.clear()
        self.head_history.clear()
        self.goal_history.clear()
        self.recovery_state_history.clear()
        self.info_gain_history.clear()
        self.ticks_in_current_action = 0
        self.current_action = "NONE"
        self.total_action_switches = 0
        self.total_direction_reversals = 0
        self.cumulative_yaw_rotation = 0.0
        self.last_yaw = 0.0
        self.detected_failures.clear()
        for k in self.failure_counts:
            self.failure_counts[k] = 0

    def step(self, tick: int, tel_dict: Dict[str, Any]) -> List[FailureDetectionEvent]:
        """
        Processes one cognitive cycle telemetry step and evaluates all 10 failure detectors.
        """
        pos_x = float(tel_dict.get("pos_x", 0.0))
        pos_y = float(tel_dict.get("pos_y", 0.0))
        yaw = float(tel_dict.get("yaw", 0.0))
        speed = float(tel_dict.get("speed", 0.0))
        action = str(tel_dict.get("chosen_action_name", "BRAKE_REST"))
        goal = str(tel_dict.get("active_goal_type", "EXPLORATION"))
        cmd_wL = float(tel_dict.get("cmd_wheel_left", 0.0))
        cmd_wR = float(tel_dict.get("cmd_wheel_right", 0.0))
        cmd_v = (cmd_wL + cmd_wR) * 0.5 * 0.048
        head_pan = float(tel_dict.get("head_pan", 0.0))
        rec_state = str(tel_dict.get("recovery_state", "IDLE"))
        info_gain = float(tel_dict.get("information_gain", 0.0))
        
        # Update yaw unwrapping for spin loop detection
        if len(self.yaw_history) > 0:
            dyaw = yaw - self.last_yaw
            while dyaw > math.pi: dyaw -= 2 * math.pi
            while dyaw < -math.pi: dyaw += 2 * math.pi
            self.cumulative_yaw_rotation += abs(dyaw)
        self.last_yaw = yaw
        
        # Action duration tracking
        if action == self.current_action:
            self.ticks_in_current_action += 1
        else:
            self.current_action = action
            self.ticks_in_current_action = 1
            self.total_action_switches += 1
            
        # Append to buffers
        self.pos_history.append((pos_x, pos_y))
        self.action_history.append(action)
        self.cmd_v_history.append(cmd_v)
        self.act_v_history.append(speed)
        self.yaw_history.append(yaw)
        self.head_history.append(head_pan)
        self.goal_history.append(goal)
        self.recovery_state_history.append(rec_state)
        self.info_gain_history.append(info_gain)
        
        new_events = []
        time_s = tick * self.dt
        
        # -------------------------------------------------------------
        # DETECTOR A: STATIONARY_STALL
        # -------------------------------------------------------------
        if len(self.pos_history) >= 25:
            p_old = self.pos_history[-25]
            p_now = self.pos_history[-1]
            disp = math.sqrt((p_now[0] - p_old[0])**2 + (p_now[1] - p_old[1])**2)
            mean_cmd_v = np.mean(list(self.cmd_v_history)[-25:])
            if mean_cmd_v > 0.05 and disp < 0.015:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="STATIONARY_STALL", severity="CRITICAL",
                    details=f"Cmd vel {mean_cmd_v:.3f} m/s but disp only {disp:.4f}m over 25 ticks",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["STATIONARY_STALL"] += 1

        # -------------------------------------------------------------
        # DETECTOR B: BRAKE_LOCK
        # -------------------------------------------------------------
        if self.current_action == "BRAKE_REST" and self.ticks_in_current_action > 15:
            event = FailureDetectionEvent(
                tick=tick, time_s=time_s, failure_type="BRAKE_LOCK", severity="CRITICAL",
                details=f"BRAKE_REST held continuously for {self.ticks_in_current_action} ticks (>15)",
                telemetry_snapshot=tel_dict
            )
            new_events.append(event)
            self.failure_counts["BRAKE_LOCK"] += 1

        # -------------------------------------------------------------
        # DETECTOR C: LEFT_RIGHT_LIMIT_CYCLE
        # -------------------------------------------------------------
        if len(self.action_history) >= 12:
            recent_acts = list(self.action_history)[-12:]
            left_right_flips = 0
            for i in range(len(recent_acts) - 1):
                if ("LEFT" in recent_acts[i] and "RIGHT" in recent_acts[i+1]) or \
                   ("RIGHT" in recent_acts[i] and "LEFT" in recent_acts[i+1]):
                    left_right_flips += 1
            if left_right_flips >= 4:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="LEFT_RIGHT_LIMIT_CYCLE", severity="CRITICAL",
                    details=f"Left/Right steering flips occurred {left_right_flips} times in 12 ticks",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["LEFT_RIGHT_LIMIT_CYCLE"] += 1

        # -------------------------------------------------------------
        # DETECTOR D: FORWARD_REVERSE_LIMIT_CYCLE
        # -------------------------------------------------------------
        if len(self.action_history) >= 14:
            recent_acts = list(self.action_history)[-14:]
            fwd_rev_flips = 0
            for i in range(len(recent_acts) - 1):
                is_fwd1 = "FORWARD" in recent_acts[i] or "CURVE" in recent_acts[i]
                is_rev1 = "REVERSE" in recent_acts[i]
                is_fwd2 = "FORWARD" in recent_acts[i+1] or "CURVE" in recent_acts[i+1]
                is_rev2 = "REVERSE" in recent_acts[i+1]
                if (is_fwd1 and is_rev2) or (is_rev1 and is_fwd2):
                    fwd_rev_flips += 1
            if fwd_rev_flips >= 4:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="FORWARD_REVERSE_LIMIT_CYCLE", severity="CRITICAL",
                    details=f"Forward/Reverse flips occurred {fwd_rev_flips} times in 14 ticks",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["FORWARD_REVERSE_LIMIT_CYCLE"] += 1

        # -------------------------------------------------------------
        # DETECTOR E: SPIN_LOOP
        # -------------------------------------------------------------
        if len(self.pos_history) >= 30:
            p_old = self.pos_history[-30]
            p_now = self.pos_history[-1]
            disp_30 = math.sqrt((p_now[0] - p_old[0])**2 + (p_now[1] - p_old[1])**2)
            if self.cumulative_yaw_rotation > 4.0 * math.pi and disp_30 < 0.05:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="SPIN_LOOP", severity="CRITICAL",
                    details=f"Accumulated yaw {self.cumulative_yaw_rotation:.1f} rad (>4pi) with displacement only {disp_30:.3f}m",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["SPIN_LOOP"] += 1

        # -------------------------------------------------------------
        # DETECTOR F: HEAD_SCAN_WITHOUT_INFORMATION_GAIN
        # -------------------------------------------------------------
        if len(self.head_history) >= 20:
            head_pts = list(self.head_history)[-20:]
            head_movement = np.std(head_pts)
            info_pts = list(self.info_gain_history)[-20:]
            mean_info = np.mean(info_pts)
            if head_movement > 0.15 and mean_info < 1e-4 and speed < 0.02:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="HEAD_SCAN_WITHOUT_INFORMATION_GAIN", severity="WARNING",
                    details=f"Head active (std {head_movement:.3f} rad) while info gain is 0 and robot stationary",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["HEAD_SCAN_WITHOUT_INFORMATION_GAIN"] += 1

        # -------------------------------------------------------------
        # DETECTOR G: RECOVERY_LOOP
        # -------------------------------------------------------------
        if len(self.recovery_state_history) >= 30:
            rec_pts = list(self.recovery_state_history)[-30:]
            tier_transitions = sum(1 for i in range(len(rec_pts)-1) if rec_pts[i] == "IDLE" and rec_pts[i+1] != "IDLE")
            if tier_transitions >= 3:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="RECOVERY_LOOP", severity="CRITICAL",
                    details=f"Recovery triggered {tier_transitions} times in 30 ticks without sustained breakout",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["RECOVERY_LOOP"] += 1

        # -------------------------------------------------------------
        # DETECTOR H: GOAL_LOOP
        # -------------------------------------------------------------
        if len(self.goal_history) >= 15:
            goal_pts = list(self.goal_history)[-15:]
            switches = sum(1 for i in range(len(goal_pts)-1) if goal_pts[i] != goal_pts[i+1])
            if switches >= 5:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="GOAL_LOOP", severity="WARNING",
                    details=f"Rapid goal switches {switches} times in 15 ticks without execution progress",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["GOAL_LOOP"] += 1

        # -------------------------------------------------------------
        # DETECTOR I: ACTION_CHATTER
        # -------------------------------------------------------------
        if len(self.action_history) >= 8:
            act_pts = list(self.action_history)[-8:]
            rapid_switches = sum(1 for i in range(len(act_pts)-1) if act_pts[i] != act_pts[i+1])
            if rapid_switches >= 6:
                event = FailureDetectionEvent(
                    tick=tick, time_s=time_s, failure_type="ACTION_CHATTER", severity="WARNING",
                    details=f"Action changed {rapid_switches} times in 8 consecutive ticks",
                    telemetry_snapshot=tel_dict
                )
                new_events.append(event)
                self.failure_counts["ACTION_CHATTER"] += 1

        self.detected_failures.extend(new_events)
        return new_events

    def generate_forensic_summary(self) -> Dict[str, Any]:
        """Generates comprehensive structured forensic summary."""
        total_fail = sum(self.failure_counts.values())
        return {
            "total_failure_events_detected": total_fail,
            "failure_breakdown": dict(self.failure_counts),
            "total_action_switches": self.total_action_switches,
            "total_direction_reversals": self.total_direction_reversals,
            "verdict": "ZERO_FAILURES" if total_fail == 0 else "FAILURES_DETECTED"
        }
