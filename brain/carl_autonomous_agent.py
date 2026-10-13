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
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_endocrine_adaptation import CarlEndocrineAdaptationEngine
from brain.carl_vision import CarlVisionNet, CarlVisionTelemetry

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
    def __init__(self, dt: float = 0.0333, enable_memory: bool = True, deliberation_mode: str = "mppi", grid_path: Optional[str] = None):
        self.dt = dt
        self.enable_memory = enable_memory
        self.deliberation_mode = deliberation_mode.lower()
        
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
        self.last_action_6d = np.zeros(6, dtype=np.float64)
        self.last_sensory_state = None
        self.telemetry_history: List[CognitiveCycleTelemetry] = []

        # Stage 1 Slip & Traction Observer
        self.ax_history: List[float] = []
        self.slip_ratio: float = 0.0
        self.v_est: float = 0.0

        # Stage 2.1 Neuromorphic 2,114-Neuron Attractor Architecture (HD Ring + Grid Torus)
        self.cann_brain = CarlStage2BIntegratedBrain(dt=self.dt)
        self.cann_brain.w_rot[20] = 1.0
        self.cann_brain.w_fwd[15] = 1.0
        self.cann_brain.is_developmentally_trained = True

        # Stage 3.4 Active Inference / Stage 3.3 Continuous MPPI / Stage 2.3 Discrete fallback
        if self.deliberation_mode in ["active_inference", "act_inf"]:
            self.deliberation = CARLActiveInferenceEngine(grid_path=grid_path, dt=self.dt)
        elif self.deliberation_mode == "mppi":
            self.deliberation = CARLStage3_3MPPIDeliberationEngine(mode="mppi", num_samples=128, horizon=15, dt=self.dt)
        else:
            self.deliberation = CARLStage2_3R1DeliberationEngine(mode=self.deliberation_mode, horizon=10, dt=self.dt)
        self.spatial_memory = self.deliberation.mem

        # Stage 3.5 Endocrine & Physical Adaptation Engine (Slip Reflex + Hormonal Kinetics + Torque Trim)
        self.endocrine = CarlEndocrineAdaptationEngine(dt=self.dt)

        # Stage 3.6 Physarum Topological Routing & HDC Motor Synergy Engines
        self.physarum = getattr(self.deliberation, "physarum", None)
        self.synergies = getattr(self.deliberation, "synergies", None)

        # Stage 3.7 Multi-Modal Vision & Active Head Gaze Scanning
        self.vision = CarlVisionNet(height=64, width=64, num_sectors=8)
        self.enable_stage3_7_vision: bool = True
        self.enable_stage3_7_gaze: bool = True
        self.head_pan: float = 0.0
        self.neck_tilt: float = 0.0
        self.gaze_scan_dir: float = 1.0
        self.last_vision_telemetry: Optional[CarlVisionTelemetry] = None

    def reset(self):
        """
        Resets agent controller state, filters, steering biases, and integrator history.
        """
        self.tick = 0
        self.last_action_name = "BRAKE_REST"
        self.last_action_cmds = np.zeros(2)
        self.last_action_6d = np.zeros(6, dtype=np.float64)
        self.last_sensory_state = None
        self.ax_history.clear()
        self.slip_ratio = 0.0
        self.v_est = 0.0
        self.telemetry_history.clear()
        self.embodiment = CarlEmbodiedOrganism(dt=self.dt)
        self.homeostasis = CarlHomeostaticCore(dt=self.dt)
        self.agency = CarlEndogenousAgency()
        self.stuck_detector = CarlStuckDetector(dt=self.dt, window_ticks=20)
        self.recovery_manager = CarlRecoveryManager(dt=self.dt)
        self.endocrine.reset()
        self.vision.reset()
        self.head_pan = 0.0
        self.neck_tilt = 0.0
        self.gaze_scan_dir = 1.0
        self.last_vision_telemetry = None
        if hasattr(self.self_model, "reset"):
            self.self_model.reset()

    def initialize_spatial_grounding(self, spawn_x: float, spawn_y: float, spawn_yaw: float, grid_path: Optional[str] = None):
        """
        Initializes internal unprivileged dead-reckoning and birthplace in 2,114-neuron brain at spawn.
        Strict anti-cheat invariant: zero qpos reads permitted after spawn initialization.
        """
        if grid_path is not None and hasattr(self.deliberation, "load_grid"):
            self.deliberation.load_grid(grid_path)
        self.deliberation.initialize_pose(spawn_x, spawn_y, spawn_yaw)
        self.cann_brain.reset_at_birthplace()
        self.v_est = 0.0
        self.last_action_6d = np.zeros(6, dtype=np.float64)

    def step_cognitive_cycle(self, hal, external_command: Optional[np.ndarray] = None, food_coords: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Executes one complete unscripted cognitive cycle.
        """
        self.tick += 1
        
        # 1. Proprioceptive & Exteroceptive Perception (Fine-grained contact filtering)
        sensory = self.embodiment.read_proprioception(hal)
        sensory.pos_x = float(self.deliberation.pose[0])
        sensory.pos_y = float(self.deliberation.pose[1])
        sensory.yaw = float(self.deliberation.pose[2])
        sensory.speed = float(self.v_est)

        # 1b. Stage 3.7 Neuromorphic Retinal Ingestion (Optic Tectum Saliency)
        vision_telem = None
        stage3_7_vision_active = False
        if getattr(self, "enable_stage3_7_vision", True) and hal is not None and hasattr(hal, "read_camera"):
            rgb_frame = hal.read_camera("eye_cam", width=64, height=64)
            vision_telem = self.vision.process_retina(
                rgb=rgb_frame,
                head_pan_rad=self.head_pan,
                neck_tilt_rad=self.neck_tilt
            )
            self.last_vision_telemetry = vision_telem
            stage3_7_vision_active = True
        
        # 1c. Real-Time Stuck Detection (Tracks command vs physical translation and stationary obstacle stalls)
        r = self.self_model.self_params.estimated_wheel_radius_m
        cmd_v = float((self.last_action_cmds[0] + self.last_action_cmds[1]) * 0.5 * r)
        stuck_tel = self.stuck_detector.update(
            sensory.pos_x, sensory.pos_y, cmd_v, self.last_action_name,
            min_obstacle_dist=sensory.min_obstacle_dist,
            speed=sensory.speed,
            yaw=sensory.yaw
        )
        if stuck_tel.state == "STUCK_CONFIRMED" and not self.recovery_manager.active:
            self.recovery_manager.trigger_recovery(np.array([sensory.pos_x, sensory.pos_y]), sensory)
            
        # 1c. Information-Theoretic Empowerment & Future Controllability Evaluation
        if getattr(self, "deliberation", None) is not None:
            emp_eval = self.empowerment_core.last_evaluation
        else:
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
            
        # 8. Counterfactual Imagination (Bypassed in favor of Stage 2.3 Deliberation Engine)
        target_coords_arr = None
        if food_coords is not None:
            target_coords_arr = np.array(food_coords)
        elif active_goal.target_coordinates is not None:
            target_coords_arr = np.array(active_goal.target_coordinates)
            
        prev_act = getattr(self, "last_action_name", "STRAIGHT_FORWARD")
        best_action_name = prev_act
        best_action_cmd = np.zeros(2, dtype=np.float32)
        chosen_eval = {}
        dreamer = None
        
        if getattr(self, "deliberation", None) is None:
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
        
        # ---------------------------------------------------------------------
        # UNIFIED STAGE 1 & STAGE 2 COGNITIVE ORGAN PIPELINE
        # ---------------------------------------------------------------------
        raw_sensors = hal.read_sensors() if hasattr(hal, "read_sensors") else None
        
        # 1. Stage 1 Organ: Traction Loss & Wheel Slip Observation
        stage1_slip_active = False
        if raw_sensors is not None and len(raw_sensors) >= 18:
            ax_val = float(raw_sensors[15])
            self.ax_history.append(ax_val)
            if len(self.ax_history) > 6:
                self.ax_history.pop(0)
            ax_std = float(np.std(self.ax_history)) if len(self.ax_history) >= 4 else 1.2
            # Query unprivileged physical wheel velocities from HAL or sensory history
            w_left_vel = 0.0
            w_right_vel = 0.0
            if hal is not None:
                if hasattr(hal, "read_wheel_encoders"):
                    w_left_vel, w_right_vel = hal.read_wheel_encoders()
                elif hasattr(hal, "model") and hasattr(hal, "data") and hasattr(hal.data, "sensordata"):
                    try:
                        w_l_id = hal.model.sensor("sens_vel_w_left").id
                        w_r_id = hal.model.sensor("sens_vel_w_right").id
                        w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
                        w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
                    except Exception:
                        w_left_vel = float(self.last_action_6d[0] * 25.0)
                        w_right_vel = float(self.last_action_6d[1] * 25.0)
            else:
                w_left_vel = float(self.last_action_6d[0] * 25.0)
                w_right_vel = float(self.last_action_6d[1] * 25.0)

            v_encoder = float(0.5 * (w_left_vel + w_right_vel) * 0.048)
            u_fwd = float(0.5 * (self.last_action_6d[0] + self.last_action_6d[1]))
            v_cmd_lin = float(u_fwd * 1.20)
            self.v_est = 0.65 * self.v_est + 0.35 * v_encoder
            if abs(v_encoder) > 0.05 and abs(u_fwd) > 0.05:
                self.slip_ratio = float(np.clip(abs(v_encoder - v_cmd_lin) / max(abs(v_encoder), abs(v_cmd_lin), 0.10), 0.0, 1.0))
            else:
                self.slip_ratio = 0.0
            stage1_slip_active = True

        # 2. Stage 2.1 Organ: 2,114-Neuron Neuromorphic Attractor (HD Ring + Grid Torus)
        stage2_1_attractor_active = False
        brain_res = None
        cann_state = None
        if raw_sensors is not None:
            brain_res = self.cann_brain.update_brain(
                u_executed=self.last_action_6d,
                s_current=raw_sensors
            )
            stage2_1_attractor_active = True
            cann_state = {
                "hd_decoded_heading": float(brain_res["hd_decoded_heading"]),
                "grid_unwrapped_x": float(brain_res["grid_unwrapped_x"]),
                "grid_unwrapped_y": float(brain_res["grid_unwrapped_y"]),
                "hd_rates": self.cann_brain.hd_ring.r.copy(),
                "bump_amplitude": float(brain_res["hd_bump_amplitude"]),
            }

        # 3. Stage 2.2 Organ: Spatial Occupancy Memory & Unprivileged Odometry
        stage2_2_memory_active = False
        if raw_sensors is not None and len(raw_sensors) >= 21:
            gyro_yaw = float(raw_sensors[20])
            self.deliberation.update_odometry(v_wheel=self.v_est, w_gyro=gyro_yaw, dt=self.dt)
            stage2_2_memory_active = True

        # 4. Stage 3.5 Endocrine Adaptation & Stage 3.4 Active Inference Organ
        stage2_3_delib_active = False
        delib_telemetry = {}
        action_6d = np.zeros(6, dtype=np.float64)
        if raw_sensors is not None:
            sonars = raw_sensors[:15]
            gyro_yaw = float(raw_sensors[20]) if len(raw_sensors) > 20 else 0.0

            # Query unprivileged physical wheel velocities from HAL or sensory history
            w_left_vel = 0.0
            w_right_vel = 0.0
            if hal is not None:
                if hasattr(hal, "read_wheel_encoders"):
                    w_left_vel, w_right_vel = hal.read_wheel_encoders()
                elif hasattr(hal, "model") and hasattr(hal, "data") and hasattr(hal.data, "sensordata"):
                    try:
                        w_l_id = hal.model.sensor("sens_vel_w_left").id
                        w_r_id = hal.model.sensor("sens_vel_w_right").id
                        w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
                        w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
                    except Exception:
                        w_left_vel = float(self.last_action_6d[0] * 25.0)
                        w_right_vel = float(self.last_action_6d[1] * 25.0)
            else:
                w_left_vel = float(self.last_action_6d[0] * 25.0)
                w_right_vel = float(self.last_action_6d[1] * 25.0)

            # Endocrine modulation state into Active Inference Deliberation
            endocrine_mod = self.endocrine.get_active_inference_modulation()

            if self.deliberation_mode in ["active_inference", "act_inf"]:
                delib_action, delib_telemetry = self.deliberation.select_action(
                    curr_sensors=sonars,
                    curr_v=self.v_est,
                    curr_w=gyro_yaw,
                    forced_pose=None,
                    cann_state=cann_state,
                    endocrine_modulation=endocrine_mod
                )
            else:
                delib_action, delib_telemetry = self.deliberation.select_action(
                    curr_sensors=sonars,
                    curr_v=self.v_est,
                    curr_w=gyro_yaw,
                    forced_pose=None,
                    cann_state=cann_state
                )
            stage2_3_delib_active = True

            # Stage 3.5 Physical Adaptation: Fast Campaniform Sensilla reflex + Endocrine kinetics + Torque trim
            is_stalled = bool(getattr(self.stuck_detector, "stuck_detected", False))
            adapted_cmd, endocrine_telem = self.endocrine.update_and_adapt(
                cmd_u=delib_action,
                w_left_vel=w_left_vel,
                w_right_vel=w_right_vel,
                gyro_yaw_rate=gyro_yaw,
                v_est=self.v_est,
                is_stalled=is_stalled
            )
            delib_telemetry["endocrine"] = endocrine_telem

            # Formulate 6-DOF Embodied Actuation
            raw_wheels = np.array([adapted_cmd[0], adapted_cmd[1]], dtype=np.float32)
            if hasattr(self.deliberation, "synergies") and getattr(self.deliberation, "enable_stage3_6_synergies", False):
                smooth_wheels = self.deliberation.synergies.filter_action(raw_wheels)
                action_6d[0] = float(smooth_wheels[0])
                action_6d[1] = float(smooth_wheels[1])
            else:
                action_6d[0] = adapted_cmd[0]
                action_6d[1] = adapted_cmd[1]

            if "action_6d" in delib_telemetry:
                action_6d[4] = float(delib_telemetry["action_6d"][4])  # hip_pitch virtual suspension
                action_6d[5] = float(delib_telemetry["action_6d"][5])  # hip_roll virtual suspension
            else:
                action_6d[4] = float(delib_telemetry.get("torso_pitch", 0.0))
                action_6d[5] = float(delib_telemetry.get("torso_roll", 0.0))

            # Stage 3.7 Active Visual Head Gaze Scanning (Head Pan = channel 2, Neck Tilt = channel 3)
            # Inspired by Superior Colliculus saccadic exploration & corollary discharge
            if getattr(self, "enable_stage3_7_gaze", True):
                min_front_sonar = float(np.min(sonars[5:10])) if len(sonars) >= 10 else 1.0
                if min_front_sonar < 0.45:
                    # Wall immediately ahead: initiate active saccadic head sweep to seek egress opening
                    self.head_pan += float(0.18 * self.gaze_scan_dir)
                    if self.head_pan > 0.85:
                        self.head_pan = 0.85
                        self.gaze_scan_dir = -1.0
                    elif self.head_pan < -0.85:
                        self.head_pan = -0.85
                        self.gaze_scan_dir = 1.0

                    # If visual egress detected with confidence, bias gaze toward egress
                    if vision_telem is not None and vision_telem.egress_confidence > 0.25:
                        target_pan = float(np.clip(vision_telem.egress_angle * 0.75, -0.85, 0.85))
                        self.head_pan = float(0.65 * target_pan + 0.35 * self.head_pan)
                else:
                    # Open pathway ahead: smoothly recenter gaze
                    self.head_pan *= 0.75

                # Commanded head pan servo (HAL range ±1.20 rad)
                action_6d[2] = float(np.clip(self.head_pan / 1.20, -1.0, 1.0))
                action_6d[3] = float(np.clip(self.neck_tilt / 0.50, -1.0, 1.0))
            else:
                action_6d[2] = 0.0
                action_6d[3] = 0.0

            self.last_action_6d = action_6d.copy()
            actuation_active = True

            best_action_name = delib_telemetry.get("selected_branch", "DELIB_ACTION")
            best_action_cmd = np.array([action_6d[0], action_6d[1]])

        # 9. Operational Action Veto Evaluation (Internal & External & Recovery Override)
        veto_asserted = False
        veto_reason = "ACTION_SAFE"
        
        if self.deliberation_mode not in ["active_inference", "act_inf"] and self.recovery_manager.active:
            # Active Recovery Override (for discrete Stage 2.3 only; disabled under continuous Active Inference)
            rec_action_name, rec_cmd, rec_done = self.recovery_manager.step_recovery(
                np.array([sensory.pos_x, sensory.pos_y]), sensory
            )
            best_action_name = rec_action_name
            best_action_cmd = rec_cmd
            action_6d[0] = rec_cmd[0]
            action_6d[1] = rec_cmd[1]
            veto_asserted = True
            veto_reason = f"STUCK_RECOVERY_{self.recovery_manager.phase}"
            if rec_done:
                self.stuck_detector.reset()
        elif external_command is not None:
            best_action_name = "EXTERNAL_ACCEPTED"
            best_action_cmd = external_command
            action_6d[0] = external_command[0]
            action_6d[1] = external_command[1]
                
        self.last_action_name = best_action_name
        self.agency.update_steering_persistence(best_action_name)
        
        # 10. Autonomous Motor Execution via Embodiment
        if self.deliberation_mode not in ["active_inference", "act_inf"]:
            self.embodiment.target_w_L = float(best_action_cmd[0])
            self.embodiment.target_w_R = float(best_action_cmd[1])
            if stage2_3_delib_active:
                self.embodiment.target_head_yaw = float(action_6d[2])
            cmds = self.embodiment.step_embodiment(hal)
        else:
            cmds = {"cmd_w_L": float(action_6d[0]), "cmd_w_R": float(action_6d[1])}
        
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
            pred_dist_0_25s=delib_telemetry.get("min_clearances", {}).get(best_action_name, 5.0) if stage2_3_delib_active else chosen_eval.get("pred_dist_0_25s", 5.0),
            pred_dist_0_50s=delib_telemetry.get("min_clearances", {}).get(best_action_name, 5.0) if stage2_3_delib_active else chosen_eval.get("pred_dist_0_50s", 5.0),
            pred_dist_1_00s=delib_telemetry.get("min_clearances", {}).get(best_action_name, 5.0) if stage2_3_delib_active else chosen_eval.get("pred_dist_1_00s", 5.0),
            collision_probability=0.0 if stage2_3_delib_active else chosen_eval.get("collision_probability", 0.0),
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
            "action_cmd": action_6d if stage2_3_delib_active else np.array([cmds["cmd_w_L"], cmds["cmd_w_R"], 0.0, 0.0, 0.0, 0.0]),
            "action_name": best_action_name,
            "delib_telemetry": delib_telemetry,
            "stage1_slip_active": stage1_slip_active,
            "stage2_1_attractor_active": stage2_1_attractor_active,
            "stage2_2_memory_active": stage2_2_memory_active,
            "stage2_3_delib_active": stage2_3_delib_active,
            "stage3_5_endocrine_active": True,
            "stage3_6_physarum_active": True,
            "stage3_7_vision_active": stage3_7_vision_active,
            "vision_telemetry": vision_telem,
            "actuation_active": True,
            "sensory": sensory,
            "homeostasis": h_info,
            "dreamer": dreamer,
            "attractor_state": brain_res,
            "stuck_telemetry": stuck_tel,
            "empowerment": emp_eval
        }
