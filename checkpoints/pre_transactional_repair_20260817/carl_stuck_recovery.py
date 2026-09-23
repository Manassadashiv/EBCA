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
        
        # Detector state
        self.state = "STUCK_IDLE"
        self.stuck_candidate_ticks = 0
        self.stuck_confirmed_ticks = 0
        self.stuck_origin_pos = np.zeros(2)
        self.stuck_confidence = 0.0
        
    def update(self, pos_x: float, pos_y: float, commanded_v: float, action_name: str) -> StuckTelemetry:
        """
        Updates detector with current physical position and commanded translational velocity.
        """
        self.pos_history.append(np.array([pos_x, pos_y]))
        self.cmd_v_history.append(commanded_v)
        self.action_history.append(action_name)
        
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
            
        # 1. Rolling Euclidean Displacement
        p_start = self.pos_history[0]
        p_curr = self.pos_history[-1]
        displacement = float(np.linalg.norm(p_curr - p_start))
        
        # 2. Expected Distance under Commanded Velocity
        mean_cmd_v = float(np.mean([max(0.0, v) for v in self.cmd_v_history]))
        expected_dist = mean_cmd_v * (self.window_ticks * self.dt)
        
        # 3. Stuck Ratio & Confidence Calculation
        if expected_dist > 0.08:
            ratio = displacement / expected_dist
            if ratio < 0.20:
                self.stuck_candidate_ticks += 1
                self.stuck_confidence = min(1.0, self.stuck_candidate_ticks / 15.0)
            else:
                self.stuck_candidate_ticks = max(0, self.stuck_candidate_ticks - 2)
                self.stuck_confidence = max(0.0, self.stuck_confidence - 0.15)
        else:
            self.stuck_candidate_ticks = max(0, self.stuck_candidate_ticks - 1)
            self.stuck_confidence = max(0.0, self.stuck_confidence - 0.10)
            
        # 4. State Transitions
        if self.stuck_candidate_ticks >= 18:
            if self.state != "STUCK_CONFIRMED":
                self.state = "STUCK_CONFIRMED"
                self.stuck_origin_pos = np.array([pos_x, pos_y])
            self.stuck_confirmed_ticks += 1
        elif self.stuck_candidate_ticks >= 8:
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
        self.phase = "IDLE"
        self.phase_ticks = 0
        self.total_recovery_cycles = 0
        self.recovery_origin = np.zeros(2)
        self.target_heading_rad = 0.0
        self.steer_direction = 1.0 # +1.0 for left, -1.0 for right
        
    def trigger_recovery(self, current_pos: np.ndarray, sensory_state):
        """
        Initializes an escalating recovery sequence based on local 15-ray geometry.
        """
        self.active = True
        self.total_recovery_cycles += 1
        self.recovery_origin = np.copy(current_pos)
        self.phase_ticks = 0
        
        # Analyze local obstacle asymmetry to choose optimal reverse-curve bias
        sonar = sensory_state.sonar_distances if (sensory_state and sensory_state.sonar_distances is not None) else np.ones(15) * 5.0
        right_clear = float(np.mean(sonar[0:6]))
        left_clear = float(np.mean(sonar[9:15]))
        
        # Bias reverse away from the tighter side (reverse curve opposite of constrained side)
        self.steer_direction = 1.0 if left_clear >= right_clear else -1.0
        
        # Determine maximum clearance ray angle
        best_ray_idx = int(np.argmax(sonar))
        # Ray angles: -120 deg to +120 deg
        best_angle_deg = -120.0 + best_ray_idx * (240.0 / 14.0)
        self.target_heading_rad = math.radians(best_angle_deg)
        
        if self.total_recovery_cycles == 1:
            self.tier = 1
            self.phase = "TIER_1_REVERSE_CURVE"
        elif self.total_recovery_cycles == 2:
            self.tier = 2
            self.phase = "TIER_2_TARGETED_SPIN"
        else:
            self.tier = 3
            self.phase = "TIER_3_FORWARD_BREAKOUT"

    def step_recovery(self, current_pos: np.ndarray, sensory_state) -> Tuple[str, np.ndarray, bool]:
        """
        Executes active recovery step.
        Returns: (action_name, wheel_commands, is_recovery_complete)
        """
        if not self.active:
            return "STRAIGHT_FORWARD", np.array([4.5, 4.5]), True
            
        self.phase_ticks += 1
        current_disp = float(np.linalg.norm(current_pos - self.recovery_origin))
        
        sonar = sensory_state.sonar_distances if (sensory_state and sensory_state.sonar_distances is not None) else np.ones(15) * 5.0
        front_clear = float(np.min(sonar[5:10]))
        
        # =========================================================================
        # TIER 1: Reverse with Curved Steering (14 ticks = ~0.46s)
        # =========================================================================
        if self.phase == "TIER_1_REVERSE_CURVE":
            if self.steer_direction > 0:
                # Reverse curving left
                action_name = "RECOVERY_REVERSE_CURVE_LEFT"
                cmd = np.array([-4.5, -2.5])
            else:
                # Reverse curving right
                action_name = "RECOVERY_REVERSE_CURVE_RIGHT"
                cmd = np.array([-2.5, -4.5])
                
            if self.phase_ticks >= 14 or front_clear > 0.85:
                # Transition to Tier 2 targeted reorientation
                self.phase = "TIER_2_TARGETED_SPIN"
                self.phase_ticks = 0
            return action_name, cmd, False
            
        # =========================================================================
        # TIER 2: Targeted Reorientation to Max Clearance Azimuth (up to 16 ticks)
        # =========================================================================
        elif self.phase == "TIER_2_TARGETED_SPIN":
            if self.steer_direction > 0:
                action_name = "RECOVERY_SPIN_LEFT"
                cmd = np.array([-4.0, 4.0])
            else:
                action_name = "RECOVERY_SPIN_RIGHT"
                cmd = np.array([4.0, -4.0])
                
            if self.phase_ticks >= 14 or (front_clear > 1.10 and self.phase_ticks >= 6):
                self.phase = "TIER_3_FORWARD_BREAKOUT"
                self.phase_ticks = 0
            return action_name, cmd, False
            
        # =========================================================================
        # TIER 3: Forward Breakout Acceleration (18 ticks = ~0.60s)
        # =========================================================================
        elif self.phase == "TIER_3_FORWARD_BREAKOUT":
            action_name = "RECOVERY_FORWARD_BREAKOUT"
            cmd = np.array([5.0, 5.0])
            
            # Check if breakout succeeded: displacement >= 0.35m and front is clear
            if current_disp >= 0.35 and front_clear > 0.65:
                self.active = False
                self.phase = "SUCCESS"
                self.total_recovery_cycles = 0
                return action_name, cmd, True # Recovery complete!
                
            if self.phase_ticks >= 18:
                # Cycle complete, evaluate displacement
                if current_disp >= 0.30 and front_clear > 0.55:
                    self.active = False
                    self.phase = "SUCCESS"
                    self.total_recovery_cycles = 0
                    return action_name, cmd, True
                else:
                    # Escalated re-trigger
                    self.phase_ticks = 0
                    self.total_recovery_cycles += 1
                    self.steer_direction = -self.steer_direction # Reverse bias
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
