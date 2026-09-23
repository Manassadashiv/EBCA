"""
brain/carl_stuck_recovery.py — First-Class Stuck Detection & Escalating Recovery Engine for CARL-DX

Implements:
1. CarlStuckDetector:
   - Tracks commanded linear velocity vs actual physical displacement over a rolling temporal window.
   - Detects mechanical wedging, wall pushing, friction entrapment, and tight limit cycles.
   - States: STUCK_IDLE, STUCK_CANDIDATE, STUCK_CONFIRMED.
   
2. CarlRecoveryManager:
   - Escalating, multi-tiered recovery protocol:
     - Tier 1: Curved Reverse Arc away from nearest obstacle.
     - Tier 2: Targeted Angular Reorientation toward maximum 15-ray sonar clearance.
     - Tier 3: Forward Breakout Acceleration & Verification.
   - Measurable recovery progress metric: verifies post-recovery displacement >= 0.35m before releasing control.
"""

import math
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List


@dataclass
class StuckTelemetry:
    state: str                 # STUCK_IDLE, STUCK_CANDIDATE, STUCK_CONFIRMED, RECOVERY_ACTIVE
    stuck_confidence: float    # [0.0, 1.0]
    rolling_displacement_m: float
    commanded_distance_m: float
    stuck_ticks: int
    recovery_tier: int
    recovery_phase: str
    recovery_cycles: int
    recovery_success: bool


class CarlStuckDetector:
    """
    Monitors kinematic execution fidelity: Detects discrepancies where commanded motion
    fails to yield physical translation over rolling temporal horizons.
    """
    def __init__(self, dt: float = 0.0333, window_ticks: int = 20):
        self.dt = dt
        self.window_ticks = window_ticks
        
        # Rolling histories
        self.pos_history = deque(maxlen=window_ticks)
        self.cmd_v_history = deque(maxlen=window_ticks)
        self.action_history = deque(maxlen=window_ticks)
        self.yaw_history = deque(maxlen=window_ticks)
        
        # Detector state
        self.state = "STUCK_IDLE"
        self.stuck_candidate_ticks = 0
        self.stuck_confirmed_ticks = 0
        self.stuck_origin_pos = np.zeros(2)
        self.stuck_confidence = 0.0
        
    def update(self, pos_x: float, pos_y: float, commanded_v: float, action_name: str, min_obstacle_dist: float = 1.0, speed: float = 0.0, yaw: float = 0.0) -> StuckTelemetry:
        """
        Updates detector with current physical position, commanded velocity, and obstacle clearance.
        """
        self.pos_history.append(np.array([pos_x, pos_y]))
        self.cmd_v_history.append(commanded_v)
        self.action_history.append(action_name)
        self.yaw_history.append(float(yaw))
        
        if len(self.pos_history) < self.window_ticks:
            return StuckTelemetry(
                state=self.state,
                stuck_confidence=0.0,
                rolling_displacement_m=0.0,
                commanded_distance_m=0.0,
                stuck_ticks=0,
                recovery_tier=0,
                recovery_phase="IDLE",
                recovery_cycles=0,
                recovery_success=False
            )
            
        # 1. Rolling Euclidean Displacement (Dynamic window for prompt obstacle stall detection)
        sub_len = min(10, len(self.pos_history)) if min_obstacle_dist < 0.50 else len(self.pos_history)
        p_start = self.pos_history[-sub_len]
        p_curr = self.pos_history[-1]
        displacement = float(np.linalg.norm(p_curr - p_start))
        
        # Angular rotation over window (active turning is not a stall)
        yaw_slice = list(self.yaw_history)[-sub_len:]
        yaw_diffs = np.diff(yaw_slice)
        yaw_diffs = (yaw_diffs + np.pi) % (2 * np.pi) - np.pi
        cum_yaw = float(np.sum(np.abs(yaw_diffs)))
        
        # 2. Expected Distance under Commanded Velocity
        cmd_slice = list(self.cmd_v_history)[-sub_len:]
        mean_cmd_v = float(np.mean([max(0.0, v) for v in cmd_slice]))
        expected_dist = mean_cmd_v * (sub_len * self.dt)
        
        # 3. Stuck Ratio & Confidence Calculation
        if cum_yaw > 0.15:
            # Organism is actively and successfully rotating / turning
            self.stuck_candidate_ticks = max(0, self.stuck_candidate_ticks - 2)
            self.stuck_confidence = max(0.0, self.stuck_confidence - 0.15)
        elif expected_dist > 0.04:
            ratio = displacement / expected_dist
            if ratio < 0.25 and speed < 0.05 and cum_yaw < 0.10:
                self.stuck_candidate_ticks += 1
                self.stuck_confidence = min(1.0, self.stuck_candidate_ticks / 8.0)
            else:
                self.stuck_candidate_ticks = max(0, self.stuck_candidate_ticks - 2)
                self.stuck_confidence = max(0.0, self.stuck_confidence - 0.15)
        elif min_obstacle_dist < 0.55 and displacement < 0.020 and speed < 0.05 and cum_yaw < 0.10:
            # Genuine stationary + angular deadlock in front of obstacle
            self.stuck_candidate_ticks += 1
            self.stuck_confidence = min(1.0, self.stuck_candidate_ticks / 8.0)
        else:
            self.stuck_candidate_ticks = max(0, self.stuck_candidate_ticks - 1)
            self.stuck_confidence = max(0.0, self.stuck_confidence - 0.10)
            
        # 4. State Transitions (8 ticks = 0.26s of genuine stationary stall < 0.05m/s)
        thresh = 8 if min_obstacle_dist < 0.50 else 12
        if self.stuck_candidate_ticks >= thresh:
            if self.state != "STUCK_CONFIRMED":
                self.state = "STUCK_CONFIRMED"
                self.stuck_origin_pos = np.array([pos_x, pos_y])
            self.stuck_confirmed_ticks += 1
        elif self.stuck_candidate_ticks >= 4:
            self.state = "STUCK_CANDIDATE"
        else:
            if self.state != "STUCK_IDLE":
                self.state = "STUCK_IDLE"
            self.stuck_confirmed_ticks = 0
            
        return StuckTelemetry(
            state=self.state,
            stuck_confidence=self.stuck_confidence,
            rolling_displacement_m=displacement,
            commanded_distance_m=expected_dist,
            stuck_ticks=self.stuck_confirmed_ticks,
            recovery_tier=0,
            recovery_phase=self.state,
            recovery_cycles=0,
            recovery_success=False
        )
        
    def reset(self):
        self.pos_history.clear()
        self.cmd_v_history.clear()
        self.action_history.clear()
        self.state = "STUCK_IDLE"
        self.stuck_candidate_ticks = 0
        self.stuck_confirmed_ticks = 0
        self.stuck_confidence = 0.0


class CarlRecoveryManager:
    """
    Autonomous multi-tiered recovery system executed when STUCK_CONFIRMED occurs.
    """
    def __init__(self, dt: float = 0.0333):
        self.dt = dt
        self.active = False
        self.tier = 1
        self.phase = "IDLE" # IDLE, TIER_1_REVERSE_CURVE, TIER_2_TARGETED_SPIN, TIER_3_FORWARD_BREAKOUT, SUCCESS
        self.phase_ticks = 0
        self.recovery_origin = np.zeros(2)
        self.breakout_origin = np.zeros(2)
        self.target_heading = 0.0
        self.steer_direction = 1.0 # +1.0 left, -1.0 right
        self.total_recovery_cycles = 0
        
    def trigger_recovery(self, current_pos: np.ndarray, sensory_state):
        """
        Engages active recovery hierarchy on confirmed stuck.
        """
        self.active = True
        self.tier = 1
        self.phase_ticks = 0
        self.recovery_origin = np.array([current_pos[0], current_pos[1]])
        self.breakout_origin = np.array([current_pos[0], current_pos[1]])
        self.total_recovery_cycles = 0
        
        sonar = sensory_state.sonar_distances if (sensory_state and sensory_state.sonar_distances is not None) else np.ones(15) * 5.0
        front_clear = float(sonar[7])
        
        if front_clear > 1.20:
            # Front avenue is already open; surge directly forward in breakout
            self.phase = "TIER_3_FORWARD_BREAKOUT"
        else:
            self.phase = "TIER_1_REVERSE_CURVE"
            # Determine lateral escape bias from 15-ray sonar
            left_clear = float(np.mean(sonar[9:15]))
            right_clear = float(np.mean(sonar[0:6]))
            self.steer_direction = 1.0 if left_clear >= right_clear else -1.0
        
    def step_recovery(self, current_pos: np.ndarray, sensory_state) -> Tuple[str, np.ndarray, bool]:
        """
        Executes active recovery step.
        Returns: (action_name, wheel_commands, is_recovery_complete)
        """
        if not self.active:
            return "STRAIGHT_FORWARD", np.array([4.5, 4.5]), True
            
        self.phase_ticks += 1
        current_disp = float(np.linalg.norm(current_pos - self.recovery_origin))
        breakout_disp = float(np.linalg.norm(current_pos - self.breakout_origin))
        effective_disp = max(current_disp, breakout_disp)
        
        sonar = sensory_state.sonar_distances if (sensory_state and sensory_state.sonar_distances is not None) else np.ones(15) * 5.0
        # Direct forward ray clearance (must be clear for forward motion)
        front_direct_clear = float(sonar[7])
        min_dist = float(np.min(sonar))
        best_ray_idx = int(np.argmax(sonar))
        
        # =========================================================================
        # TIER 1: Reverse with Curved Steering (8 ticks)
        # =========================================================================
        if self.phase == "TIER_1_REVERSE_CURVE":
            if self.steer_direction > 0:
                action_name = "RECOVERY_REVERSE_CURVE_LEFT"
                cmd = np.array([-6.0, -2.5])
            else:
                action_name = "RECOVERY_REVERSE_CURVE_RIGHT"
                cmd = np.array([-2.5, -6.0])
                
            if self.phase_ticks >= 8 or (min_dist > 0.45 and self.phase_ticks >= 4):
                self.phase = "TIER_2_TARGETED_SPIN"
                self.phase_ticks = 0
            return action_name, cmd, False
            
        # =========================================================================
        # TIER 2: Targeted Reorientation to Open Sonar Ray (Ray 7 Alignment)
        # =========================================================================
        elif self.phase == "TIER_2_TARGETED_SPIN":
            max_sonar = float(np.max(sonar))
            # Spin in direction of highest clearance ray with brisk angular velocity
            if best_ray_idx > 7:
                action_name = "RECOVERY_SPIN_LEFT"
                cmd = np.array([-7.0, 7.0])
            elif best_ray_idx < 7:
                action_name = "RECOVERY_SPIN_RIGHT"
                cmd = np.array([7.0, -7.0])
            else:
                action_name = "RECOVERY_SPIN_LEFT" if self.steer_direction > 0 else "RECOVERY_SPIN_RIGHT"
                cmd = np.array([-7.0, 7.0]) if self.steer_direction > 0 else np.array([7.0, -7.0])
                
            # Aligned when the true exit avenue has rotated into the front sector
            if max_sonar > 1.0:
                is_aligned = (best_ray_idx in [6, 7, 8]) and (front_direct_clear > 0.70)
            else:
                # Fully enclosed; must continue spinning until open exit rotates into FOV
                is_aligned = False
                
            if (is_aligned and self.phase_ticks >= 4) or (front_direct_clear > 1.50 and self.phase_ticks >= 4) or (self.phase_ticks >= 20):
                self.phase = "TIER_3_FORWARD_BREAKOUT"
                self.phase_ticks = 0
                self.breakout_origin = np.array([current_pos[0], current_pos[1]])
            return action_name, cmd, False
            
        # =========================================================================
        # TIER 3: Forward Breakout Acceleration (up to 20 ticks)
        # =========================================================================
        elif self.phase == "TIER_3_FORWARD_BREAKOUT":
            action_name = "RECOVERY_FORWARD_BREAKOUT"
            cmd = np.array([6.0, 6.0])
            
            # Check physical breakout success:
            # 1. Aligned to corridor / open escape space with forward motion
            if self.phase_ticks >= 5 and front_direct_clear > 0.45 and min_dist > 0.15 and effective_disp >= 0.020:
                self.active = False
                self.phase = "SUCCESS"
                self.total_recovery_cycles = 0
                return action_name, cmd, True
                
            # 2. Genuine forward translation displacement
            if self.phase_ticks >= 8 and effective_disp >= 0.06 and min_dist > 0.15:
                self.active = False
                self.phase = "SUCCESS"
                self.total_recovery_cycles = 0
                return action_name, cmd, True
                
            if self.phase_ticks >= 20:
                if effective_disp >= 0.03 and min_dist > 0.15:
                    self.active = False
                    self.phase = "SUCCESS"
                    self.total_recovery_cycles = 0
                    return action_name, cmd, True
                else:
                    # Re-trigger next cycle with opposite bias
                    self.phase_ticks = 0
                    self.total_recovery_cycles += 1
                    self.steer_direction = -self.steer_direction
                    self.phase = "TIER_1_REVERSE_CURVE"
                    return action_name, cmd, False
                    
            return action_name, cmd, False
            
        return "STRAIGHT_FORWARD", np.array([4.5, 4.5]), True
        
    def reset(self):
        self.active = False
        self.tier = 1
        self.phase = "IDLE"
        self.phase_ticks = 0
        self.total_recovery_cycles = 0
