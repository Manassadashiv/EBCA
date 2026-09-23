"""
brain/carl_autonomous_agent.py — Integrated Autonomous Artificial Organism Cognitive Engine

Executes the fully closed-loop, unscripted cognitive cycle:
SENSORS -> PROPRIOCEPTION -> INTEROCEPTION & HOMEOSTASIS -> GENERATIVE SELF-MODEL
-> EPISODIC MEMORY -> ENDOGENOUS GOAL GENERATION -> COUNTERFACTUAL DREAMER ROLLOUTS
-> OPERATIONAL ACTION SELECTION & VETO -> 6-DOF EMBODIED ACTUATION -> LEARNING
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from brain.carl_embodied_organism import CarlEmbodiedOrganism, EmbodiedSensoryState
from brain.carl_homeostatic_core import CarlHomeostaticCore, HomeostaticVector
from brain.carl_generative_self_model import CarlGenerativeSelfModel
from brain.carl_episodic_memory import CarlEpisodicMemory
from brain.carl_endogenous_agency import CarlEndogenousAgency, EndogenousGoal
from brain.carl_stuck_recovery import CarlStuckDetector, CarlRecoveryManager, StuckTelemetry
from brain.carl_empowerment import CarlEmpowermentCore, EmpowermentEvaluation

@dataclass
class CognitiveCycleTelemetry:
    tick: int
    pos_x: float
    pos_y: float
    yaw: float
    speed: float
    energy: float
    thermal_load: float
    motor_fatigue: float
    safety_margin: float
    curiosity_drive: float
    homeostatic_deviation: float
    active_goal_id: str
    active_goal_type: str
    goal_source: str
    chosen_action_name: str
    commanded_w_L: float
    commanded_w_R: float
    prediction_error: float
    recalled_hazard_warned: bool
    episodes_in_memory: int
    veto_asserted: bool
    veto_reason: str
    pred_dist_0_25s: float
    pred_dist_0_50s: float
    pred_dist_1_00s: float
    collision_probability: float
    affect_state: str
    food_absorbed: bool
    collision_occurred: bool
    stuck_state: str = "STUCK_IDLE"
    stuck_confidence: float = 0.0
    recovery_active: bool = False
    recovery_tier: int = 0
    recovery_phase: str = "IDLE"
    empowerment_nats: float = 0.0
    controllability_index: float = 1.0
    is_entropy_collapse: bool = False


class CarlAutonomousOrganismAgent:
    """
    Unified cognitive organism executing autonomous perception-action-learning loops without external scripting.
    """
    def __init__(self, dt: float = 0.0333, enable_memory: bool = True):
        self.dt = dt
        self.enable_memory = enable_memory
        
        self.embodiment = CarlEmbodiedOrganism(dt=dt)
        self.homeostasis = CarlHomeostaticCore(dt=dt)
        self.self_model = CarlGenerativeSelfModel(dt=dt)
        self.memory = CarlEpisodicMemory(hdc_dim=2048)
        self.agency = CarlEndogenousAgency()
        self.stuck_detector = CarlStuckDetector(dt=dt, window_ticks=20)
        self.recovery_manager = CarlRecoveryManager(dt=dt)
        self.empowerment_core = CarlEmpowermentCore(dt=dt)
        
        self.tick = 0
        self.last_action_name = "BRAKE_REST"
        self.last_action_cmds = np.zeros(2)
        self.last_sensory_state = None
        self.telemetry_history: List[CognitiveCycleTelemetry] = []

    def reset(self):
        """
        Resets agent controller state, filters, steering biases, and integrator history.
        """
        self.tick = 0
        self.last_action_name = "BRAKE_REST"
        self.last_action_cmds = np.zeros(2)
        self.last_sensory_state = None
        self.telemetry_history.clear()
        self.embodiment = CarlEmbodiedOrganism(dt=self.dt)
        self.homeostasis = CarlHomeostaticCore(dt=self.dt)
        self.agency = CarlEndogenousAgency()
        self.stuck_detector = CarlStuckDetector(dt=self.dt, window_ticks=20)
        self.recovery_manager = CarlRecoveryManager(dt=self.dt)
        if hasattr(self.self_model, "reset"):
            self.self_model.reset()

    def step_cognitive_cycle(self, hal, external_command: Optional[np.ndarray] = None, food_coords: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Executes one complete unscripted cognitive cycle.
        """
        self.tick += 1
        
        # 1. Proprioceptive & Exteroceptive Perception (Fine-grained contact filtering)
        sensory = self.embodiment.read_proprioception(hal)
        
        # 1b. Real-Time Stuck Detection (Tracks command vs physical translation)
        r = self.self_model.self_params.estimated_wheel_radius_m
        cmd_v = float((self.last_action_cmds[0] + self.last_action_cmds[1]) * 0.5 * r)
        stuck_tel = self.stuck_detector.update(sensory.pos_x, sensory.pos_y, cmd_v, self.last_action_name)
        if stuck_tel.state == "STUCK_CONFIRMED" and not self.recovery_manager.active:
            self.recovery_manager.trigger_recovery(np.array([sensory.pos_x, sensory.pos_y]), sensory)
            
        # 1c. Information-Theoretic Empowerment & Future Controllability Evaluation
        emp_eval = self.empowerment_core.evaluate_empowerment(
            sensory, self.self_model, min_clearance=sensory.min_obstacle_dist
        )
        
        # 2. Check Physical Interactions (Food absorption / Physical body collisions)
        food_absorbed = False
        if food_coords is not None:
            dist_food = math.sqrt((food_coords[0] - sensory.pos_x)**2 + (food_coords[1] - sensory.pos_y)**2)
            food_absorbed = (dist_food < 0.30)
            
        collision_occurred = sensory.has_body_collision
        
        # 3. Update Forward Self-Model & Compute Prediction Error
        pred_error = 0.0
        if self.tick > 1 and self.last_sensory_state is not None:
            pred_error = self.self_model.update_with_observation(sensory)
            
        # 4. Update Interoception & Homeostasis
        h_info = self.homeostasis.update_interoception(sensory, food_eaten=food_absorbed, prediction_error=pred_error)
        h_state = self.homeostasis.state
        
        # 5. Endogenous Affect Posture Mapping
        if collision_occurred or sensory.min_obstacle_dist < 0.30:
            self.embodiment.set_affect_state("THREAT_AVERSION", 1.0)
        elif self.recovery_manager.active:
            self.embodiment.set_affect_state("CAUTIOUS", 0.9)
        elif h_state.energy < 0.40:
            self.embodiment.set_affect_state("CAUTIOUS", 0.8)
        elif h_state.thermal_load > 0.70 or h_state.motor_fatigue > 0.70:
            self.embodiment.set_affect_state("CAUTIOUS", 0.5)
        elif food_absorbed or (h_state.energy > 0.85 and h_info["homeostatic_deviation"] < 0.35):
            self.embodiment.set_affect_state("SATISFACTION", 1.0)
        elif h_state.curiosity_drive > 0.50:
            self.embodiment.set_affect_state("CURIOUS", float(h_state.curiosity_drive))
        else:
            self.embodiment.set_affect_state("NEUTRAL", 0.5)
            
        # 6. Endogenous Goal Generation & Arbitration
        active_goal = self.agency.arbitrate_active_goal(h_state, sensory)
        goal_source = "HOMEOSTATIC" if active_goal.goal_type in ["VIABILITY", "REST"] else "CURIOSITY"
        
        # 7. Episodic Memory Query
        recalled_hazard = False
        avoid_action = None
        current_episodes_count = len(self.memory.episodes) if self.enable_memory else 0
        if self.enable_memory:
            mem_query = self.memory.query_associative_memory(sensory.pos_x, sensory.pos_y, h_info["dominant_need"])
            recalled_hazard = mem_query.get("warn_hazard", False)
            avoid_action = mem_query.get("avoid_action", None)
            
        # 8. Counterfactual Imagination (Dreamer Rollout Evaluation)
        target_coords_arr = None
        if food_coords is not None:
            target_coords_arr = np.array(food_coords)
        elif active_goal.target_coordinates is not None:
            target_coords_arr = np.array(active_goal.target_coordinates)
            
        prev_act = getattr(self, "last_action_name", "STRAIGHT_FORWARD")
        dreamer = self.self_model.imagine_counterfactual_rollouts(
            sensory,
            self.homeostasis,
            target_pos=target_coords_arr,
            last_action_name=prev_act,
            active_steering_bias=self.agency.active_steering_bias,
            horizon_steps=20
        )
        
        candidate_evals = dreamer["candidates"]
        for act_name, act_eval in candidate_evals.items():
            if recalled_hazard and act_name == avoid_action:
                act_eval["expected_free_energy"] += 25.0
                
        best_action_name = min(candidate_evals, key=lambda k: candidate_evals[k]["expected_free_energy"])
        best_action_cmd = candidate_evals[best_action_name]["action"]
        chosen_eval = candidate_evals[best_action_name]
        
        # 9. Operational Action Veto Evaluation (Internal & External & Recovery Override)
        veto_asserted = False
        veto_reason = "ACTION_SAFE"
        
        if self.recovery_manager.active:
            # Active Recovery Override
            rec_action_name, rec_cmd, rec_done = self.recovery_manager.step_recovery(
                np.array([sensory.pos_x, sensory.pos_y]), sensory
            )
            best_action_name = rec_action_name
            best_action_cmd = rec_cmd
            veto_asserted = True
            veto_reason = f"STUCK_RECOVERY_{self.recovery_manager.phase}"
            if rec_done:
                self.stuck_detector.reset()
        elif external_command is not None:
            veto_check = self.agency.evaluate_external_command_veto(external_command, sensory, self.homeostasis, self.self_model)
            if veto_check["veto_asserted"]:
                veto_asserted = True
                veto_reason = veto_check["veto_reason"]
                best_action_name = veto_check["recommended_action_name"]
                best_action_cmd = veto_check["recommended_cmd"]
            else:
                best_action_name = "EXTERNAL_ACCEPTED"
                best_action_cmd = external_command
        else:
            veto_check = self.agency.evaluate_internal_action_veto(best_action_cmd, sensory, self.homeostasis, self.self_model)
            if veto_check["veto_asserted"]:
                veto_asserted = True
                veto_reason = veto_check["veto_reason"]
                best_action_name = veto_check["recommended_action_name"]
                best_action_cmd = veto_check["recommended_cmd"]
                
        self.last_action_name = best_action_name
        self.agency.update_steering_persistence(best_action_name)
        
        # 10. Autonomous Motor Execution via Embodiment
        self.embodiment.target_w_L = float(best_action_cmd[0])
        self.embodiment.target_w_R = float(best_action_cmd[1])
        
        # Active Visual Gaze & Head Scanning
        if sensory.target_visible and sensory.target_bearing is not None:
            self.embodiment.target_head_yaw = float(np.clip(sensory.target_bearing, -1.2, 1.2))
        elif sensory.min_obstacle_dist < 1.0:
            # Active obstacle investigation scan
            self.embodiment.target_head_yaw = 0.60 * math.sin(self.tick * 0.25)
        elif active_goal.target_coordinates is not None:
            tx, ty = active_goal.target_coordinates
            head_yaw_des = math.atan2(ty - sensory.pos_y, tx - sensory.pos_x) - sensory.yaw
            head_yaw_des = (head_yaw_des + math.pi) % (2 * math.pi) - math.pi
            self.embodiment.target_head_yaw = float(np.clip(head_yaw_des, -1.2, 1.2))
        else:
            self.embodiment.target_head_yaw = 0.40 * math.sin(self.tick * 0.10)
            
        cmds = self.embodiment.step_embodiment(hal)
        
        # 11. Store Autobiographical Episode on Collision or Food Absorption
        if self.enable_memory:
            if collision_occurred:
                self.memory.store_episode(
                    sensory.pos_x, sensory.pos_y, h_info["dominant_need"],
                    best_action_name, -1.0, hazard=True, pred_err=pred_error, tick=self.tick
                )
            elif food_absorbed:
                self.memory.store_episode(
                    sensory.pos_x, sensory.pos_y, h_info["dominant_need"],
                    best_action_name, +1.0, hazard=False, pred_err=pred_error, tick=self.tick
                )
                
        # 12. Forward Kinematics Prediction for Next Tick
        self.self_model.predict_next_state(sensory, best_action_cmd)
        self.last_action_name = best_action_name
        self.last_action_cmds = best_action_cmd
        self.last_sensory_state = sensory
        
        telemetry = CognitiveCycleTelemetry(
            tick=self.tick,
            pos_x=round(sensory.pos_x, 4),
            pos_y=round(sensory.pos_y, 4),
            yaw=round(sensory.yaw, 4),
            speed=round(sensory.speed, 4),
            energy=round(h_state.energy, 4),
            thermal_load=round(h_state.thermal_load, 4),
            motor_fatigue=round(h_state.motor_fatigue, 4),
            safety_margin=round(h_state.safety_margin, 4),
            curiosity_drive=round(h_state.curiosity_drive, 4),
            homeostatic_deviation=round(h_info["homeostatic_deviation"], 4),
            active_goal_id=active_goal.goal_id,
            active_goal_type=active_goal.goal_type,
            goal_source=goal_source,
            chosen_action_name=best_action_name,
            commanded_w_L=round(cmds["cmd_w_L"], 3),
            commanded_w_R=round(cmds["cmd_w_R"], 3),
            prediction_error=round(pred_error, 4),
            recalled_hazard_warned=recalled_hazard,
            episodes_in_memory=current_episodes_count,
            veto_asserted=veto_asserted,
            veto_reason=veto_reason,
            pred_dist_0_25s=chosen_eval.get("pred_dist_0_25s", 5.0),
            pred_dist_0_50s=chosen_eval.get("pred_dist_0_50s", 5.0),
            pred_dist_1_00s=chosen_eval.get("pred_dist_1_00s", 5.0),
            collision_probability=chosen_eval.get("collision_probability", 0.0),
            affect_state=self.embodiment.affect_state,
            food_absorbed=food_absorbed,
            collision_occurred=collision_occurred,
            stuck_state=stuck_tel.state,
            stuck_confidence=round(stuck_tel.stuck_confidence, 4),
            recovery_active=self.recovery_manager.active,
            recovery_tier=self.recovery_manager.tier,
            recovery_phase=self.recovery_manager.phase,
            empowerment_nats=emp_eval.empowerment_nats,
            controllability_index=emp_eval.controllability_index,
            is_entropy_collapse=emp_eval.is_entropy_collapse
        )
        self.telemetry_history.append(telemetry)
        
        return {
            "telemetry": telemetry,
            "cmd_L": cmds["cmd_w_L"],
            "cmd_R": cmds["cmd_w_R"],
            "sensory": sensory,
            "homeostasis": h_info,
            "dreamer": dreamer,
            "stuck_telemetry": stuck_tel,
            "empowerment": emp_eval
        }
