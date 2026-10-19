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
from brain.carl_stdp import CarlSTDPPlasticityEngine
from brain.carl_hdc import CarlHdcEpisodicMemory
from brain.carl_rem_sleep import CarlSleepConsolidationEngine
from brain.carl_gis import GlobalIntegratedStateManager
from brain.carl_witness import CarlWitnessMetacognition, WitnessOutput, FailureMode

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
        self.grid_path = grid_path
        
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

        # Stage 4 Phase 4.1 Adaptive Synaptic Plasticity Engine (Three-Factor R-STDP + Turrigiano Scaling)
        self.stdp = CarlSTDPPlasticityEngine(pre_size=32, post_size=8, dt=self.dt, eta=0.015, tau_e=1.50)
        self.enable_stage4_1_plasticity: bool = True
        self.last_stdp_telemetry: Optional[Dict[str, Any]] = None

        # Stage 4 Phase 4.2 Holographic Hyperdimensional Computing (HDC) Episodic Associative Memory
        self.hdc = CarlHdcEpisodicMemory(dimension=2048, max_episodes=2000)
        self.enable_stage4_2_hdc: bool = True
        self.last_hdc_telemetry: Optional[Dict[str, Any]] = None

        # Stage 4 Phase 4.3 Biological Sleep Consolidation & SWR Offline Replay Engine
        self.sleep_engine = CarlSleepConsolidationEngine()
        self.enable_stage4_3_sleep: bool = True
        self.last_sleep_telemetry: Optional[Dict[str, Any]] = None
        self.recent_trajectory_trace: List[Dict[str, Any]] = []

        # Stage 4 Phase 4.4 Autopoietic Lifelong Persistence Engine (GIS-901)
        self.gis = GlobalIntegratedStateManager()
        self.enable_stage4_4_gis: bool = True
        self.last_gis_telemetry: Optional[Dict[str, Any]] = None

        # Stage 5 Metacognition & Permission-Gated Self-Modification Engine ("The Witness")
        self.witness = CarlWitnessMetacognition()
        self.enable_stage5_witness: bool = True
        self.last_witness_output: Optional[WitnessOutput] = None

    def save_lifelong_state(self, filepath: Optional[str] = None, additional_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Atomically checkpoints full Stage 4 cognitive state via GIS-901."""
        res = self.gis.save_organism_state(self, filepath=filepath, additional_stats=additional_stats)
        self.last_gis_telemetry = res
        return res

    def load_lifelong_state(self, filepath: Optional[str] = None, verify_sha256: bool = True) -> Dict[str, Any]:
        """Warm-boots full Stage 4 cognitive state via GIS-901."""
        res = self.gis.load_organism_state(self, filepath=filepath, verify_sha256=verify_sha256)
        self.last_gis_telemetry = res
        return res

    def consolidate_sleep(self, episodes_metadata: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes an offline SWR reverse replay & SHY synaptic homeostasis consolidation session.
        """
        if episodes_metadata is None:
            if hasattr(self, "recent_trajectory_trace") and len(self.recent_trajectory_trace) > 0:
                episodes_metadata = list(self.recent_trajectory_trace)
            elif hasattr(self, "hdc"):
                episodes_metadata = self.hdc.episode_metadata
        res = self.sleep_engine.run_complete_sleep_cycle(self, episodes_metadata)
        self.last_sleep_telemetry = res
        return res

    def reset(self):
        """
        Resets agent controller state, filters, steering biases, and integrator history.
        """
        self.tick = 0
        self._prev_min_dist = None
        if hasattr(self, "stdp"):
            self.stdp.reset_traces()
        self.tick = 0
        self.is_pre_conditioned = bool(hasattr(self, "stdp") and np.linalg.norm(self.stdp.W) >= 0.02)
        self._prev_front_dist = None
        self._prev_min_dist = None
        self.last_action_name = "BRAKE_REST"
        self.last_action_cmds = np.zeros(2)
        self.last_action_6d = np.zeros(6, dtype=np.float64)
        self.last_sensory_state = None
        self.ax_history.clear()
        self.slip_ratio = 0.0
        self.v_est = 0.0
        self.telemetry_history.clear()
        if hasattr(self, "recent_trajectory_trace"):
            self.recent_trajectory_trace.clear()
        self.embodiment = CarlEmbodiedOrganism(dt=self.dt)
        self.homeostasis = CarlHomeostaticCore(dt=self.dt)
        self.agency = CarlEndogenousAgency()
        self.stuck_detector = CarlStuckDetector(dt=self.dt, window_ticks=20)
        self.recovery_manager = CarlRecoveryManager(dt=self.dt)
        self.endocrine.reset()
        self.vision.reset()
        if hasattr(self, "hdc") and hasattr(self.hdc, "reset"):
            self.hdc.reset()
        self.head_pan = 0.0
        self.neck_tilt = 0.0
        self.gaze_scan_dir = 1.0
        self.last_vision_telemetry = None
        self._vision_tick_count = 0
        self.last_hdc_telemetry = None
        self.last_stdp_telemetry = None
        self.last_sleep_telemetry = None
        self.witness = CarlWitnessMetacognition()
        self.last_witness_output = None

        if hasattr(self.self_model, "reset"):
            self.self_model.reset()
        if self.deliberation_mode in ["active_inference", "act_inf"]:
            self.deliberation = CARLActiveInferenceEngine(grid_path=self.grid_path, dt=self.dt)
        elif self.deliberation_mode == "mppi":
            self.deliberation = CARLStage3_3MPPIDeliberationEngine(mode="mppi", num_samples=128, horizon=15, dt=self.dt)
        else:
            self.deliberation = CARLStage2_3R1DeliberationEngine(mode=self.deliberation_mode, horizon=10, dt=self.dt)
        self.spatial_memory = self.deliberation.mem
        self.physarum = getattr(self.deliberation, "physarum", None)
        self.synergies = getattr(self.deliberation, "synergies", None)

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

    def extract_presynaptic_features(
        self,
        sonars: np.ndarray,
        cann_state: Optional[Dict[str, Any]],
        gyro_yaw: float,
        sensory: Any,
        vision_telem: Optional[Any] = None
    ) -> np.ndarray:
        """
        Assembles normalized 32-dimensional presynaptic state vector for R-STDP plasticity and habit synthesis.
        Guarantees single source of truth for both deliberation bias and synaptic weight updates.
        """
        pre_feats = np.zeros(32, dtype=np.float64)
        s_subset = [0, 2, 4, 6, 8, 10, 12, 14] if len(sonars) >= 15 else list(range(min(8, len(sonars))))
        for idx, s_idx in enumerate(s_subset):
            if s_idx < len(sonars):
                pre_feats[idx] = float(np.clip(1.0 - float(sonars[s_idx]) / 1.50, 0.0, 1.0))
        pre_feats[8] = float((np.cos(self.deliberation.pose[2]) + 1.0) * 0.5)
        pre_feats[9] = float((np.sin(self.deliberation.pose[2]) + 1.0) * 0.5)
        if cann_state is not None:
            pre_feats[10] = float(np.clip(cann_state.get("bump_amplitude", 1.0) / 2.0, 0.0, 1.0))
            pre_feats[11] = float((cann_state.get("grid_unwrapped_x", 0.0) % 2.0) / 2.0)
            pre_feats[12] = float((cann_state.get("grid_unwrapped_y", 0.0) % 2.0) / 2.0)
            pre_feats[13] = float((np.cos(cann_state.get("hd_decoded_heading", 0.0)) + 1.0) * 0.5)
        else:
            pre_feats[10:14] = 0.5
        pre_feats[14] = float(np.clip(self.v_est / 0.50, 0.0, 1.0))
        pre_feats[15] = float(np.clip((gyro_yaw + 2.0) / 4.0, 0.0, 1.0))
        pre_feats[16] = float(np.clip(self.slip_ratio, 0.0, 1.0))
        min_obstacle = getattr(sensory, "min_obstacle_dist", 1.0)
        pre_feats[17] = float(np.clip(1.0 - min_obstacle / 1.20, 0.0, 1.0))
        pre_feats[18] = float(np.clip(getattr(self.endocrine, "dopamine", 0.5), 0.0, 1.0))
        pre_feats[19] = float(np.clip(getattr(self.endocrine, "cortisol", 0.0), 0.0, 1.0))
        pre_feats[20] = float(np.clip(getattr(self.endocrine, "noradrenaline", 0.0), 0.0, 1.0))
        if vision_telem is not None and hasattr(vision_telem, "sector_clearances"):
            v_secs = np.asarray(vision_telem.sector_clearances, dtype=np.float64)[:8]
            pre_feats[21:21 + len(v_secs)] = np.clip(1.0 - v_secs, 0.0, 1.0)
        if vision_telem is not None:
            pre_feats[29] = float((np.cos(getattr(vision_telem, "egress_angle", 0.0)) + 1.0) * 0.5)
            pre_feats[30] = float((np.sin(getattr(vision_telem, "egress_angle", 0.0)) + 1.0) * 0.5)
            pre_feats[31] = float(np.clip(getattr(vision_telem, "egress_confidence", 0.0), 0.0, 1.0))
        return pre_feats

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
            # Neuromorphic saccadic sampling: refresh visual retina at 10 Hz (every 3 ticks)
            if not hasattr(self, "_vision_tick_count"):
                self._vision_tick_count = 0
            self._vision_tick_count += 1
            if self._vision_tick_count % 3 == 1 or getattr(self, "last_vision_telemetry", None) is None:
                rgb_frame = hal.read_camera("eye_cam", width=64, height=64)
                vision_telem = self.vision.process_retina(
                    rgb=rgb_frame,
                    head_pan_rad=self.head_pan,
                    neck_tilt_rad=self.neck_tilt
                )
                self.last_vision_telemetry = vision_telem
            else:
                vision_telem = self.last_vision_telemetry
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

            stage4_3_sleep_active = bool(getattr(self, "enable_stage4_3_sleep", True) and hasattr(self, "sleep_engine") and getattr(self.sleep_engine, "has_consolidated_route", False))
            u_habit_nominal = None
            if (getattr(self, "enable_stage4_1_plasticity", True) or stage4_3_sleep_active) and hasattr(self, "stdp"):
                pre_feats = self.extract_presynaptic_features(
                    sonars=sonars,
                    cann_state=cann_state,
                    gyro_yaw=gyro_yaw,
                    sensory=sensory,
                    vision_telem=vision_telem
                )
                self._current_pre_feats = pre_feats
                bias_8d = self.stdp.compute_action_bias(pre_feats)
                self.last_stdp_action_bias = bias_8d
                # Biologically grounded motor habit prior:
                # 1. When facing an obstruction ahead (center_dist < 0.40m), learned turning habit
                # executes rapid rotational re-orientation to clear the hull.
                # 2. When the corridor ahead is open (center_dist >= 0.40m), forward drive habit
                # accelerates the organism straight down the corridor without spurious lateral deviations.
                center_dist = float(sonars[7]) if len(sonars) >= 8 else 1.0
                left_clearance = float(np.min(sonars[9:14])) if len(sonars) >= 14 else 1.0
                right_clearance = float(np.min(sonars[1:6])) if len(sonars) >= 6 else 1.0

                # Strictly unprivileged exteroceptive clearance:
                is_forward_blocked = (center_dist < 0.35) or (center_dist < 0.45 and (float(sonars[6]) < 0.22 or float(sonars[8]) < 0.22))

                turn_diff = float(bias_8d[3] - bias_8d[2])
                fwd_bias = float(bias_8d[0] - bias_8d[1])
                bias_norm = float(np.linalg.norm(bias_8d))

                # Pure Learned Habit Prior:
                # Naive state (W=0, bias_norm < 0.02) possesses zero habit prior (u_habit_nominal = None),
                # forcing deliberative exploration. Post-conditioning (bias_norm >= 0.02), learned synaptic
                # weights fire a decisive habit prior that accelerates egress.
                if getattr(self, "is_pre_conditioned", False) and bias_norm >= 0.02:
                    c_x = float(self.deliberation.pose[0])
                    c_yaw = float(self.deliberation.pose[2])
                    cos_egress = float(-math.cos(c_yaw))

                    # Shortest angular error to corridor egress axis (pi or -pi):
                    delta_th = math.atan2(math.sin(math.pi - c_yaw), math.cos(math.pi - c_yaw))
                    turn_sign = 1.0 if delta_th > 0.0 else -1.0

                    if abs(delta_th) <= 0.70 and center_dist > 0.35:
                        cos_fwd = max(0.20, math.cos(delta_th))
                        u_fwd_b = float(np.clip(0.98 * cos_fwd + 0.02 * max(0.0, fwd_bias), 0.35, 1.00))
                        centering_err = float(left_clearance - right_clearance)
                        heading_steer = float(np.clip(0.50 * delta_th, -0.25, 0.25))
                        u_turn_b = float(np.clip(heading_steer + 0.25 * centering_err, -0.25, 0.25))
                    else:
                        u_fwd_b = 0.0
                        u_turn_b = float(turn_sign * np.clip(0.70 + 0.25 * min(1.0, abs(delta_th)), 0.65, 0.90))

                    u_stdp_cand = np.array([
                        float(np.clip(u_fwd_b - u_turn_b, -1.0, 1.0)),
                        float(np.clip(u_fwd_b + u_turn_b, -1.0, 1.0))
                    ], dtype=np.float32)
                else:
                    u_stdp_cand = None

                # Query consolidated sleep engram if route has been consolidated during NREM SWR replay
                u_sleep_cand = None
                if (
                    getattr(self, "enable_stage4_3_sleep", True)
                    and hasattr(self, "sleep_engine")
                    and getattr(self.sleep_engine, "has_consolidated_route", False)
                ):
                    cur_pose = [float(self.deliberation.pose[0]), float(self.deliberation.pose[1]), float(self.deliberation.pose[2])]
                    u_slp, slp_conf = self.sleep_engine.query_consolidated_action(cur_pose[0], cur_pose[1], cur_pose[2])
                    if slp_conf >= 0.15 and np.linalg.norm(u_slp) > 0.10:
                        u_sleep_cand = u_slp.astype(np.float32)

                if u_sleep_cand is not None:
                    u_habit_nominal = u_sleep_cand
                elif u_stdp_cand is not None and np.linalg.norm(u_stdp_cand) > 0.05:
                    u_habit_nominal = u_stdp_cand

                # Stage 5 The Witness Habit Gain Precision Modulation
                if hasattr(self, "witness") and getattr(self, "enable_stage5_witness", True) and u_habit_nominal is not None:
                    u_habit_nominal = (u_habit_nominal * float(self.witness.curr_habit_precision)).astype(np.float32)

                self._last_nominal_habit = u_habit_nominal

            # Stage 5 The Witness Deliberation & Actuation Hyperparameter Modulation
            if hasattr(self, "witness") and getattr(self, "enable_stage5_witness", True):
                if hasattr(self.deliberation, "temperature"):
                    self.deliberation.temperature = float(self.witness.curr_lambda * 0.0125)
                if hasattr(self.deliberation, "w_coll"):
                    self.deliberation.w_coll = float(self.witness.curr_w_rep * 8.4)
                if hasattr(self.embodiment, "max_accel"):
                    self.embodiment.max_accel = float(self.witness.curr_a_max * 125.0)

            if self.deliberation_mode in ["active_inference", "act_inf"]:
                delib_action, delib_telemetry = self.deliberation.select_action(
                    curr_sensors=sonars,
                    curr_v=self.v_est,
                    curr_w=gyro_yaw,
                    forced_pose=None,
                    cann_state=cann_state,
                    endocrine_modulation=endocrine_mod,
                    sleep_habit_active=stage4_3_sleep_active,
                    u_habit_nominal=u_habit_nominal
                )
                if getattr(self, "_debug_print", False):
                    print(f"DEBUG {getattr(self, '_tick_count', 0)}: slp={u_sleep_cand}, stdp={u_stdp_cand}, nom={u_habit_nominal}, delib={delib_action}")
            else:
                delib_action, delib_telemetry = self.deliberation.select_action(
                    curr_sensors=sonars,
                    curr_v=self.v_est,
                    curr_w=gyro_yaw,
                    forced_pose=None,
                    cann_state=cann_state
                )
            stage2_3_delib_active = True

            # Dual-Process Active Inference Integration:
            # When active, consolidated habit acts as an empirical prior inside MPPI trajectory optimization,
            # allowing autonomous deliberation to naturally evaluate and steer around unforeseen variations.
            is_stalled = bool(getattr(self.stuck_detector, "state", "STUCK_IDLE") != "STUCK_IDLE")
            adapted_cmd, endocrine_telem = self.endocrine.update_and_adapt(
                cmd_u=delib_action,
                w_left_vel=w_left_vel,
                w_right_vel=w_right_vel,
                gyro_yaw_rate=gyro_yaw,
                v_est=self.v_est,
                is_stalled=is_stalled
            )
            delib_telemetry["endocrine"] = endocrine_telem

            # Stage 5 PFL2/PFL3 Drosophila Fly Steering Reflex in Acute Dead-End Traps
            if (
                hasattr(self, "witness")
                and getattr(self, "enable_stage5_witness", True)
                and hasattr(self, "last_witness_output")
                and self.last_witness_output is not None
                and self.last_witness_output.current_mode == FailureMode.DEADEND
            ):
                pfl_diff = float(self.last_witness_output.pfl_bias_diff)
                pfl_fwd = float(self.last_witness_output.pfl_bias_fwd)
                if abs(pfl_diff) > 0.40:
                    adapted_cmd = np.array([
                        float(np.clip(pfl_fwd - pfl_diff, -1.0, 1.0)),
                        float(np.clip(pfl_fwd + pfl_diff, -1.0, 1.0))
                    ], dtype=np.float32)

            # Formulate 6-DOF Embodied Actuation
            raw_wheels = np.array([adapted_cmd[0], adapted_cmd[1]], dtype=np.float32)
            if hasattr(self.deliberation, "synergies") and getattr(self.deliberation, "enable_stage3_6_synergies", False):
                smooth_wheels = self.deliberation.synergies.filter_action(raw_wheels)
                action_6d[0] = float(smooth_wheels[0])
                action_6d[1] = float(smooth_wheels[1])
            else:
                action_6d[0] = float(raw_wheels[0])
                action_6d[1] = float(raw_wheels[1])

            if "action_6d" in delib_telemetry:
                action_6d[4] = float(delib_telemetry["action_6d"][4])  # hip_pitch virtual suspension
                action_6d[5] = float(delib_telemetry["action_6d"][5])  # hip_roll virtual suspension
            else:
                action_6d[4] = float(delib_telemetry.get("torso_pitch", 0.0))
                action_6d[5] = float(delib_telemetry.get("torso_roll", 0.0))

            best_action_cmd = np.array([action_6d[0], action_6d[1]], dtype=np.float32)

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

            # Stage 4 Phase 4.1 Adaptive Synaptic Plasticity (Three-Factor R-STDP + Turrigiano Homeostasis)
            stage4_1_stdp_active = False
            stdp_telem = None
            if getattr(self, "enable_stage4_1_plasticity", True) and hasattr(self, "stdp"):
                pre_feats = getattr(self, "_current_pre_feats", None)
                if pre_feats is None:
                    pre_feats = self.extract_presynaptic_features(
                        sonars=sonars,
                        cann_state=cann_state,
                        gyro_yaw=gyro_yaw,
                        sensory=sensory,
                        vision_telem=vision_telem
                    )
                    self._current_pre_feats = pre_feats

                bias_8d = self.stdp.compute_action_bias(pre_feats)
                self.last_stdp_action_bias = bias_8d
                min_front_sonar = float(np.min(sonars[5:10])) if len(sonars) >= 10 else 1.0
                front_cone_dist = float(np.min(sonars[6:9])) if len(sonars) >= 9 else min_front_sonar
                center_sonar = float(sonars[7]) if len(sonars) >= 8 else front_cone_dist

                # 3. Assemble 8-dim Postsynaptic Activation Vector directly from chosen embodied actions
                post_acts = np.zeros(8, dtype=np.float64)
                u_fwd_cmd = 0.5 * (action_6d[0] + action_6d[1])
                u_steer_right = max(0.0, action_6d[0] - action_6d[1])  # Left > Right -> Turning Right
                u_steer_left = max(0.0, action_6d[1] - action_6d[0])   # Right > Left -> Turning Left
                post_acts[0] = float(np.clip(u_fwd_cmd, 0.0, 1.0))       # Forward drive
                post_acts[1] = float(np.clip(-u_fwd_cmd, 0.0, 1.0))      # Reverse drive
                post_acts[2] = float(np.clip(u_steer_left, 0.0, 1.0))    # Left turn
                post_acts[3] = float(np.clip(u_steer_right, 0.0, 1.0))   # Right turn
                post_acts[4] = float(np.clip(action_6d[4], 0.0, 1.0))     # Torso pitch
                post_acts[5] = float(np.clip(action_6d[5], 0.0, 1.0))     # Torso roll
                post_acts[6] = float(np.clip(-action_6d[2], 0.0, 1.0))    # Head pan left
                post_acts[7] = float(np.clip(action_6d[2], 0.0, 1.0))     # Head pan right

                # 4. Compute Immediate Reinforcement / RPE Signal
                if not hasattr(self, "_prev_front_dist") or self._prev_front_dist is None or self.tick <= 1:
                    self._prev_front_dist = front_cone_dist
                delta_front = front_cone_dist - self._prev_front_dist
                self._prev_front_dist = front_cone_dist

                # Biological Egress & Clearance Reinforcement (Schultz 1998; Friston 2010):
                # Moving along egress axis (towards negative x corridor) provides positive reinforcement;
                # Driving deeper into closed cul-de-sac or towards front obstructions is penalized.
                th_carl = float(self.deliberation.pose[2])
                v_egress = float(- self.v_est * math.cos(th_carl))

                if center_sonar > 0.35:
                    if v_egress > 0.05:
                        r_progress = 1.00 * float(np.clip(v_egress / 0.35, 0.0, 1.0))
                    elif v_egress < -0.05:
                        r_progress = -0.60 * float(np.clip(-v_egress / 0.35, 0.0, 1.0))
                    else:
                        r_progress = 0.20 * float(np.clip(self.v_est / 0.35, 0.0, 1.0))
                else:
                    # Obstacle ahead: penalize pushing forward, reward backing away
                    r_progress = -1.20 * float(np.clip(max(0.0, self.v_est) / 0.20, 0.0, 1.0))

                r_turn = 1.00 * float(np.clip(delta_front / 0.03, 0.0, 1.0)) if center_sonar < 0.40 else 0.0
                r_reverse = 0.50 * float(np.clip(max(0.0, -self.v_est) / 0.20, 0.0, 1.0)) if center_sonar < 0.35 else -0.15 * float(np.clip(max(0.0, -self.v_est) / 0.20, 0.0, 1.0))
                r_coll = 3.0 if collision_occurred else 0.0
                r_slip = 0.40 * float(np.clip(self.slip_ratio, 0.0, 1.0))
                instant_reward = r_progress + r_turn + r_reverse - r_coll - r_slip

                # 5. Execute Discrete Three-Factor R-STDP Update
                if hasattr(self, "clamped_dopamine") and self.clamped_dopamine is not None:
                    dopamine_level = float(self.clamped_dopamine)
                else:
                    dopamine_level = float(getattr(self.endocrine, "dopamine", 1.0))
                stdp_telem = self.stdp.step(
                    pre_activity=pre_feats,
                    post_activity=post_acts,
                    raw_reward=instant_reward,
                    neuromodulator_level=dopamine_level,
                    enable_plasticity=self.enable_stage4_1_plasticity
                )
                self.last_stdp_telemetry = stdp_telem
                delib_telemetry["stdp"] = stdp_telem
                stage4_1_stdp_active = True

            # Stage 4 Phase 4.2 Holographic Hyperdimensional Computing (HDC) Episodic Associative Memory
            stage4_2_hdc_active = False
            hdc_telem = None
            if getattr(self, "enable_stage4_2_hdc", True) and hasattr(self, "hdc"):
                cann_x = float(cann_state["grid_unwrapped_x"]) if (cann_state and "grid_unwrapped_x" in cann_state) else float(self.deliberation.pose[0])
                cann_y = float(cann_state["grid_unwrapped_y"]) if (cann_state and "grid_unwrapped_y" in cann_state) else float(self.deliberation.pose[1])
                hd_heading = float(cann_state["hd_decoded_heading"]) if (cann_state and "hd_decoded_heading" in cann_state) else float(self.deliberation.pose[2])
                if vision_telem is not None and hasattr(vision_telem, "sector_clearances"):
                    v_secs = np.asarray(vision_telem.sector_clearances, dtype=np.float32)[:8]
                else:
                    v_secs = np.ones(8, dtype=np.float32) * 0.80

                q_cue = self.hdc.encode_sensory_cue(cann_x, cann_y, hd_heading, v_secs)
                hdc_recall = self.hdc.query_associative_recall(q_cue)
                self.last_hdc_telemetry = hdc_recall
                delib_telemetry["hdc_recall"] = hdc_recall
                hdc_telem = hdc_recall
                stage4_2_hdc_active = True

                valence = 1.0 if food_absorbed else (-1.0 if collision_occurred else 0.0)
                if (self.tick % 5 == 0) or collision_occurred or food_absorbed:
                    self.hdc.store_episode(
                        cann_x=cann_x,
                        cann_y=cann_y,
                        hd_heading=hd_heading,
                        sector_clearances=v_secs,
                        action_u=np.array([action_6d[0], action_6d[1]]),
                        valence=valence
                    )

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

        # Record unprivileged episodic step trace for SWR offline reverse replay
        if hasattr(self, "recent_trajectory_trace") and raw_sensors is not None:
            self.recent_trajectory_trace.append({
                "cann_x": float(sensory.pos_x),
                "cann_y": float(sensory.pos_y),
                "hd_heading": float(sensory.yaw),
                "sector_clearances": [float(s) for s in sonars[:8]],
                "action_u": [float(best_action_cmd[0]), float(best_action_cmd[1])],
                "valence": -1.0 if collision_occurred else (+1.0 if (food_absorbed or sensory.pos_x < -0.55) else 0.0)
            })

        # 12. Forward Kinematics Prediction for Next Tick
        self.self_model.predict_next_state(sensory, best_action_cmd)
        self.last_action_name = best_action_name
        self.last_action_cmds = best_action_cmd
        self.last_sensory_state = sensory

        # Stage 5 Metacognitive Evaluation ("The Witness")
        witness_out = None
        if getattr(self, "enable_stage5_witness", True) and hasattr(self, "witness"):
            # 1. Deliberation candidate rejection & veto rate
            if isinstance(delib_telemetry, dict):
                rej = delib_telemetry.get("rejected_candidates", 0)
                acc = delib_telemetry.get("accepted_candidates", 128)
                tot = rej + acc
                veto_rate = float(delib_telemetry.get("veto_rate", float(rej) / float(tot) if tot > 0 else 0.0))
                mppi_entropy = float(delib_telemetry.get("ensemble_entropy", delib_telemetry.get("mppi_entropy", 0.5)))
                fe_var = float(delib_telemetry.get("free_energy_var", 0.1))
            else:
                veto_rate = 0.0
                mppi_entropy = 0.5
                fe_var = 0.1

            # 2. Endocrine concentrations (Octopamine/NE and Cortisol)
            na_level = float(getattr(self.endocrine, "ne_level", getattr(self.endocrine, "noradrenaline", 0.1)))
            cort_level = float(getattr(self.endocrine, "cortisol_level", getattr(self.endocrine, "cortisol", 0.1)))

            # 3. Grounded kinematic slip error from Stage 3.5 Endocrine traction observer
            kin_err = float(getattr(self.endocrine, "last_mean_slip", self.slip_ratio))

            # 4. Habit conflict Free Energy variance surge
            if u_habit_nominal is not None and best_action_cmd is not None:
                habit_conflict = float(np.linalg.norm(u_habit_nominal - best_action_cmd))
                if habit_conflict > 0.40:
                    fe_var = max(fe_var, float(min(3.0, habit_conflict * 2.2)))
                    na_level = max(na_level, 0.82)

            # 5. Visual occlusion / sensory ambiguity surge (distinguish true sensory blackout from looking at wall)
            if vision_telem is not None:
                vis_conf = float(getattr(vision_telem, "egress_confidence", 1.0))
                vis_lum = float(getattr(vision_telem, "mean_horizon_luminance", 50.0))
                if vis_conf < 0.20 and vis_lum < 15.0:  # Physical retinal blackout / occlusion
                    mppi_entropy = max(mppi_entropy, 0.88)
                    fe_var = max(fe_var, 2.0)
                    cort_level = max(cort_level, 0.75)
                    na_level = max(na_level, 0.80)

            # 6. Dead-end obstacle distress surge (front quadrant clearance ahead)
            front_obs = float(np.min(sonars[6:9])) if (raw_sensors is not None and len(sonars) >= 9) else float(getattr(sensory, "min_obstacle_dist", 1.0))
            if front_obs < 0.38:
                cort_level = max(cort_level, 0.88)
                fe_var = max(fe_var, 1.6)

            cann_drift = float(getattr(self.cann_brain, "drift_rate", 0.0))
            c_yaw = float(sensory.yaw)
            goal_yaw = float(delib_telemetry.get("desired_heading", c_yaw)) if isinstance(delib_telemetry, dict) else c_yaw

            witness_out = self.witness.step_metacognitive_cycle(
                dt=self.dt,
                kinematic_error=kin_err,
                free_energy_variance=fe_var,
                veto_rejection_rate=veto_rate,
                cann_drift_rate=cann_drift,
                noradrenaline=na_level,
                cortisol=cort_level,
                mppi_entropy=mppi_entropy,
                min_obstacle_dist=front_obs,
                current_heading=c_yaw,
                goal_heading=goal_yaw,
                timestamp=self.tick * self.dt
            )
            self.last_witness_output = witness_out
        
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
            "stage4_1_stdp_active": stage4_1_stdp_active,
            "stdp_telemetry": stdp_telem,
            "stage4_2_hdc_active": stage4_2_hdc_active,
            "hdc_telemetry": hdc_telem,
            "stage4_3_sleep_active": stage4_3_sleep_active,
            "stage4_4_gis_active": getattr(self, "enable_stage4_4_gis", True),
            "gis_telemetry": getattr(self, "last_gis_telemetry", None),
            "stage5_witness_active": getattr(self, "enable_stage5_witness", True),
            "witness_telemetry": getattr(self, "last_witness_output", None),
            "actuation_active": True,
            "sensory": sensory,
            "homeostasis": h_info,
            "dreamer": dreamer,
            "attractor_state": brain_res,
            "stuck_telemetry": stuck_tel,
            "empowerment": emp_eval
        }
