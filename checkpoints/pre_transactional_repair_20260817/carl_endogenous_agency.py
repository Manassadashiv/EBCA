"""
brain/carl_endogenous_agency.py — Endogenous Goal Generation, Operational Will & Autonomous Action Veto

1. Endogenous Goal Generator: Creates self-directed objectives (VIABILITY, EXPLORE, UNCERTAINTY_REDUCTION, REST_COOL)
2. Competing Goal Conflict Arbitration: Resolves internal trade-offs (e.g., Energy vs Curiosity)
3. Operational "Will" / Action Selection: Initiates self-directed behavior without external tasks
4. Action Veto: Evaluates external prompts against homeostatic survival and vetoes hazardous instructions
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional

@dataclass
class EndogenousGoal:
    goal_id: str
    goal_type: str              # VIABILITY, EXPLORATION, UNCERTAINTY, REST, NOVELTY
    priority_weight: float      # [0.0, 1.0]
    target_coordinates: Optional[Tuple[float, float]] = None
    target_behavior: str = "WALK"
    rationale: str = ""


class CarlEndogenousAgency:
    """
    Autonomous agency core generating endogenous goals and arbitrating action decisions.
    """
    def __init__(self):
        self.active_goal: Optional[EndogenousGoal] = None
        self.candidate_goals: List[EndogenousGoal] = []
        
        # Operational Will & Veto Metrics
        self.endogenous_action_count = 0
        self.veto_count = 0
        self.goal_switches = 0
        self.goal_persistence_ticks = 0
        self.active_steering_bias: float = 0.0
        self.steering_hold_ticks: int = 0

    def update_steering_persistence(self, chosen_action_name: str):
        """
        Maintains temporal steering persistence to prevent high-frequency direction chatter.
        """
        if "LEFT" in chosen_action_name:
            self.active_steering_bias = 1.0
            self.steering_hold_ticks = 10
        elif "RIGHT" in chosen_action_name:
            self.active_steering_bias = -1.0
            self.steering_hold_ticks = 10
        else:
            if self.steering_hold_ticks > 0:
                self.steering_hold_ticks -= 1
            else:
                self.active_steering_bias *= 0.8
                if abs(self.active_steering_bias) < 0.05:
                    self.active_steering_bias = 0.0

    def generate_endogenous_goals(self, homeostatic_state, sensory_state) -> List[EndogenousGoal]:
        """
        Generates candidate internal goals derived from physiological drives and environmental perceptions.
        No hardcoded external coordinates or pre-known beacon locations.
        """
        goals = []
        
        # 1. Primary Survival Need: Energy Deficit -> Foraging
        if homeostatic_state.energy < 0.50:
            urgency = (1.0 - homeostatic_state.energy) * 1.5
            goals.append(EndogenousGoal(
                goal_id="GOAL_FORAGE_RESOURCE",
                goal_type="VIABILITY",
                priority_weight=urgency,
                target_coordinates=None,
                target_behavior="FORAGE",
                rationale=f"Low energy reserve ({homeostatic_state.energy:.2f} < 0.50)"
            ))
            
        # 2. Thermal / Fatigue Overload -> Rest & Cool
        if homeostatic_state.thermal_load > 0.70 or homeostatic_state.motor_fatigue > 0.70:
            urgency = max(homeostatic_state.thermal_load, homeostatic_state.motor_fatigue) * 1.2
            goals.append(EndogenousGoal(
                goal_id="GOAL_THERMAL_REGULATION",
                goal_type="REST",
                priority_weight=urgency,
                target_coordinates=None,
                target_behavior="REST",
                rationale=f"High internal stress (thermal: {homeostatic_state.thermal_load:.2f}, fatigue: {homeostatic_state.motor_fatigue:.2f})"
            ))
            
        # 3. Curiosity / Exploration Drive
        if homeostatic_state.curiosity_drive > 0.40:
            goals.append(EndogenousGoal(
                goal_id="GOAL_EXPLORE_UNKNOWN",
                goal_type="EXPLORATION",
                priority_weight=0.40 + 0.35 * homeostatic_state.curiosity_drive,
                target_coordinates=None,
                target_behavior="EXPLORE",
                rationale=f"High intrinsic curiosity drive ({homeostatic_state.curiosity_drive:.2f})"
            ))
            
        # 4. Epistemic Need: Reduce Spatial Uncertainty
        if homeostatic_state.uncertainty > 0.40:
            goals.append(EndogenousGoal(
                goal_id="GOAL_INSPECT_SURROUNDINGS",
                goal_type="UNCERTAINTY",
                priority_weight=0.35 + 0.30 * homeostatic_state.uncertainty,
                target_coordinates=None,
                target_behavior="INSPECT",
                rationale=f"World model uncertainty ({homeostatic_state.uncertainty:.2f}) exceeds threshold"
            ))
            
        self.candidate_goals = goals
        return goals

    def arbitrate_active_goal(self, homeostatic_state, sensory_state) -> EndogenousGoal:
        """
        Arbitrates among competing internal drives and selects the highest-priority goal.
        """
        goals = self.generate_endogenous_goals(homeostatic_state, sensory_state)
        if len(goals) == 0:
            selected = EndogenousGoal(
                goal_id="GOAL_IDLE_EXPLORE",
                goal_type="EXPLORATION",
                priority_weight=0.20,
                target_coordinates=None,
                target_behavior="WALK",
                rationale="Equilibrium maintenance exploration"
            )
        else:
            selected = max(goals, key=lambda g: g.priority_weight)
            
        if self.active_goal is None or selected.goal_id != self.active_goal.goal_id:
            self.goal_switches += 1
            self.goal_persistence_ticks = 0
            self.active_goal = selected
        else:
            self.goal_persistence_ticks += 1
            
        self.endogenous_action_count += 1
        return self.active_goal

    def evaluate_internal_action_veto(self, candidate_cmd: np.ndarray, sensory_state, homeostatic_core, self_model) -> Dict[str, Any]:
        """
        Internal Operational Action Veto:
        Monitors self-generated policy commands to prevent impending wall or obstacle collisions.
        Applies smooth continuous curved escape rather than in-place spinning during open avoidance.
        """
        uL, uR = float(candidate_cmd[0]), float(candidate_cmd[1])
        r = self_model.self_params.estimated_wheel_radius_m
        b = self_model.self_params.estimated_track_width_m
        
        v_proj = (uL + uR) * 0.5 * r
        
        # Sensed sonar profile (15 rays)
        sonar_rays = sensory_state.sonar_distances if sensory_state.sonar_distances is not None else np.ones(15) * 5.0
        n_rays = len(sonar_rays)
        if n_rays == 15:
            front_clearance = float(np.min(sonar_rays[5:10]))
            right_clearance = float(np.mean(sonar_rays[0:6]))
            left_clearance = float(np.mean(sonar_rays[9:15]))
        else:
            mid = n_rays // 2
            front_clearance = float(np.min(sonar_rays[max(0, mid-2):min(n_rays, mid+2)]))
            right_clearance = float(np.mean(sonar_rays[:mid]))
            left_clearance = float(np.mean(sonar_rays[mid:]))
        
        # Horizon projection (0.5s forward)
        pred_x = sensory_state.pos_x + v_proj * math.cos(sensory_state.yaw) * 0.5
        pred_y = sensory_state.pos_y + v_proj * math.sin(sensory_state.yaw) * 0.5
        
        veto = False
        veto_reason = ""
        
        # 1. Dead-End Enclosure Veto (Front blocked and both sides constrained)
        is_dead_end = (front_clearance < 1.10 and left_clearance < 1.40 and right_clearance < 1.40)
        
        # 2. Narrow Passage Open Ahead (Centering along corridor)
        in_open_narrow_passage = (left_clearance < 0.75 and right_clearance < 0.75 and front_clearance > 1.05)
        
        if is_dead_end and v_proj > 0.02:
            veto = True
            veto_reason = f"DEAD_END_ENCLOSURE (front {front_clearance:.2f}m, left {left_clearance:.2f}m, right {right_clearance:.2f}m)"
        elif not in_open_narrow_passage and (front_clearance < 0.55 or sensory_state.min_obstacle_dist < 0.40) and v_proj > 0.05:
            veto = True
            veto_reason = f"IMMINENT_OBSTACLE_COLLISION (front clearance {front_clearance:.2f}m, min_dist {sensory_state.min_obstacle_dist:.2f}m)"
        # 3. Arena Boundary Wall Horizon Veto
        elif (abs(pred_x) > 2.35 or abs(pred_y) > 2.35) and v_proj > 0.05:
            veto = True
            veto_reason = f"BOUNDARY_WALL_PROJECTION (horizon pos ({pred_x:.2f}, {pred_y:.2f}) near wall)"
        # 4. Critical Thermal Load
        elif homeostatic_core.state.thermal_load > 0.85 and (abs(uL) + abs(uR)) > 8.0:
            veto = True
            veto_reason = f"THERMAL_OVERLOAD_PREVENTION ({homeostatic_core.state.thermal_load:.2f} > 0.85)"
            
        recommended_action = "STRAIGHT_FORWARD"
        recommended_cmd = candidate_cmd
        
        # Reset steering hold if obstacle has been safely cleared
        if sensory_state.min_obstacle_dist > 0.75 and front_clearance > 0.85:
            self.active_steering_bias = 0.0
            self.steering_hold_ticks = 0
        elif self.steering_hold_ticks > 0:
            self.steering_hold_ticks -= 1
            if self.steering_hold_ticks == 0:
                self.active_steering_bias = 0.0
                
        if veto:
            self.veto_count += 1
            if "DEAD_END" in veto_reason:
                recommended_action = "EMERGENCY_SPIN_LEFT"
                recommended_cmd = np.array([-4.0, 4.0])
            elif "OBSTACLE" in veto_reason or "BOUNDARY" in veto_reason:
                # Continuous curved steering with directional hysteresis
                # Prefer existing steering bias to avoid left/right chatter
                if self.active_steering_bias > 0.1 or (left_clearance + 0.10 >= right_clearance and self.active_steering_bias >= -0.1):
                    recommended_action = "CURVE_LEFT_MODERATE"
                    recommended_cmd = np.array([3.2, 5.8])
                    self.active_steering_bias = 1.0
                    self.steering_hold_ticks = 6
                else:
                    recommended_action = "CURVE_RIGHT_MODERATE"
                    recommended_cmd = np.array([5.8, 3.2])
                    self.active_steering_bias = -1.0
                    self.steering_hold_ticks = 6
            else:
                recommended_action = "BRAKE_REST"
                recommended_cmd = np.array([0.0, 0.0])
                
        return {
            "veto_asserted": veto,
            "veto_reason": veto_reason if veto else "INTERNAL_ACTION_SAFE",
            "recommended_action_name": recommended_action,
            "recommended_cmd": recommended_cmd,
            "left_clearance": left_clearance,
            "right_clearance": right_clearance,
            "front_clearance": front_clearance
        }

    def evaluate_external_command_veto(self, external_cmd_w: np.ndarray, sensory_state, homeostatic_core, self_model) -> Dict[str, Any]:
        """
        Evaluates an external command for safety and homeostatic viability.
        """
        return self.evaluate_internal_action_veto(external_cmd_w, sensory_state, homeostatic_core, self_model)
