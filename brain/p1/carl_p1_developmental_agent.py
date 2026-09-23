"""
brain/p1/carl_p1_developmental_agent.py — Phase 1 Developmental Artificial Organism Cognitive Engine

Extends the qualified P0 cognitive foundation for developmental and emergence experiments:
- Preserves untouched P0 core modules via composition.
- Supports cross-episode episodic memory consolidation and retrieval.
- Supports controlled ablations: no-memory, no-adaptation, no-homeostatic-need.
- Provides comprehensive telemetry for experience -> error -> adaptation -> memory -> action chain.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent, CognitiveCycleTelemetry
from brain.carl_embodied_organism import EmbodiedSensoryState
from brain.carl_homeostatic_core import HomeostaticVector
from brain.carl_generative_self_model import CarlGenerativeSelfModel
from brain.carl_episodic_memory import CarlEpisodicMemory


@dataclass
class P1DetailedTelemetry:
    tick: int
    time_s: float
    pos_x: float
    pos_y: float
    yaw: float
    velocity: float
    speed: float
    obstacle_clearance: float
    action: str
    active_goal: str
    goal_type: str
    homeostatic_state: str
    energy: float
    thermal_load: float
    motor_fatigue: float
    safety_margin: float
    curiosity_drive: float
    homeostatic_deviation: float
    prediction_error: float
    efe_chosen: float
    candidate_action_scores: Dict[str, float]
    memory_retrieval_event: bool
    memory_avoid_action: Optional[str]
    memory_recommended_action: Optional[str]
    memory_valence: float
    memory_write_event: bool
    episodes_in_memory: int
    recovery_state: str
    recovery_active: bool
    recovery_tier: int
    friction_estimate: float
    target_distance: float
    target_acquisition: bool
    collision_occurred: bool
    veto_asserted: bool
    veto_reason: str
    empowerment_nats: float
    episode_number: int
    seed: int
    environment_id: str


class CarlP1DevelopmentalAgent:
    """
    Phase 1 Developmental Organism Cognitive Agent.
    Wraps the P0 baseline cognitive components with developmental lifecycle management.
    """
    def __init__(
        self,
        dt: float = 0.0333,
        enable_memory: bool = True,
        enable_adaptation: bool = True,
        enable_need: bool = True,
        initial_energy: float = 0.35
    ):
        self.dt = dt
        self.enable_memory = enable_memory
        self.enable_adaptation = enable_adaptation
        self.enable_need = enable_need
        self.initial_energy = initial_energy
        
        # P0 Cognitive Agent Core
        self.agent = CarlAutonomousOrganismAgent(dt=dt, enable_memory=enable_memory)
        
        # Cross-Episode Persistent HDC Memory
        if self.enable_memory:
            self.memory = CarlEpisodicMemory(hdc_dim=2048)
            self.agent.memory = self.memory
        else:
            self.memory = None
            self.agent.enable_memory = False
            
        # Cumulative Developmental Stats
        self.total_lifetime_ticks = 0
        self.total_food_absorbed = 0
        self.total_collisions = 0
        self.current_episode = 1
        self.current_seed = 42
        self.current_env_id = "ENV_1_BIFURCATION_CANONICAL"
        
        self.episode_telemetry: List[P1DetailedTelemetry] = []

    def reset_for_episode(self, episode_num: int, seed: int, env_id: str, preserve_memory: bool = True):
        """
        Resets physical and transient state for a new episode while preserving consolidated memory
        and self-model adaptation if enabled.
        """
        self.current_episode = episode_num
        self.current_seed = seed
        self.current_env_id = env_id
        self.episode_telemetry.clear()
        
        # Preserve consolidated memory matrix across episodes if enabled
        stored_episodes = self.memory.episodes if (self.memory and preserve_memory) else []
        stored_matrix = self.memory.hdc_memory_matrix.copy() if (self.memory and preserve_memory) else None
        
        # Preserve adapted friction estimate if adaptation is enabled
        stored_mu = self.agent.self_model.self_params.estimated_friction_coeff if self.enable_adaptation else 2.50
        
        # Reset transient agent states
        self.agent.reset()
        
        if self.enable_memory and preserve_memory and stored_matrix is not None:
            self.agent.memory.episodes = stored_episodes
            self.agent.memory.hdc_memory_matrix = stored_matrix
            self.agent.enable_memory = True
        elif not self.enable_memory:
            self.agent.enable_memory = False
            
        if self.enable_adaptation:
            self.agent.self_model.self_params.estimated_friction_coeff = stored_mu
        else:
            # Frozen static friction estimate (Ablation: No Adaptation)
            self.agent.self_model.self_params.estimated_friction_coeff = 2.50
            
        # Initialize Homeostatic Energy Deficit (Foraging Drive)
        if self.enable_need:
            self.agent.homeostasis.state.energy = self.initial_energy
        else:
            # Ablation: No Need (Fully saturated neutral state)
            self.agent.homeostasis.state.energy = 1.0

    def step_developmental_cycle(self, hal, food_coords: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Executes one 30 Hz developmental cognitive step and records structured telemetry.
        """
        self.total_lifetime_ticks += 1
        
        # Freeze adaptation if disabled in ablation
        if not self.enable_adaptation:
            self.agent.self_model.self_params.estimated_friction_coeff = 2.50
            
        # Overwrite need if disabled in ablation
        if not self.enable_need:
            self.agent.homeostasis.state.energy = 1.0
            
        # Step underlying cognitive loop
        res = self.agent.step_cognitive_cycle(hal, food_coords=food_coords)
        telem = res["telemetry"]
        sensory = res["sensory"]
        dreamer = res["dreamer"]
        h_info = res["homeostasis"]
        
        if telem.food_absorbed:
            self.total_food_absorbed += 1
        if telem.collision_occurred:
            self.total_collisions += 1
            
        # Extract candidate action EFE scores
        candidate_scores = {}
        if "candidates" in dreamer:
            for act_k, act_v in dreamer["candidates"].items():
                candidate_scores[act_k] = round(float(act_v.get("expected_free_energy", 0.0)), 2)
                
        # Calculate target distance
        dist_to_food = 0.0
        if food_coords is not None:
            dist_to_food = math.sqrt((food_coords[0] - sensory.pos_x)**2 + (food_coords[1] - sensory.pos_y)**2)
            
        # Memory query details
        mem_warn = False
        mem_avoid = None
        mem_rec = None
        mem_val = 0.0
        if self.enable_memory and self.agent.memory:
            mq = self.agent.memory.query_associative_memory(sensory.pos_x, sensory.pos_y, h_info["dominant_need"])
            mem_warn = mq.get("warn_hazard", False)
            mem_avoid = mq.get("avoid_action", None)
            mem_rec = mq.get("recommended_action", None)
            mem_val = mq.get("memory_valence", 0.0)
            
        mem_written = bool(telem.collision_occurred or telem.food_absorbed)
        
        det_telem = P1DetailedTelemetry(
            tick=self.agent.tick,
            time_s=round(self.agent.tick * self.dt, 4),
            pos_x=round(float(sensory.pos_x), 4),
            pos_y=round(float(sensory.pos_y), 4),
            yaw=round(float(sensory.yaw), 4),
            velocity=round(float(sensory.speed), 4),
            speed=round(float(sensory.speed), 4),
            obstacle_clearance=round(float(sensory.min_obstacle_dist), 4),
            action=telem.chosen_action_name,
            active_goal=telem.active_goal_id,
            goal_type=telem.active_goal_type,
            homeostatic_state=telem.affect_state,
            energy=round(float(telem.energy), 4),
            thermal_load=round(float(telem.thermal_load), 4),
            motor_fatigue=round(float(telem.motor_fatigue), 4),
            safety_margin=round(float(telem.safety_margin), 4),
            curiosity_drive=round(float(telem.curiosity_drive), 4),
            homeostatic_deviation=round(float(telem.homeostatic_deviation), 4),
            prediction_error=round(float(telem.prediction_error), 4),
            efe_chosen=round(float(dreamer.get("best_expected_free_energy", 0.0)), 2),
            candidate_action_scores=candidate_scores,
            memory_retrieval_event=mem_warn,
            memory_avoid_action=mem_avoid,
            memory_recommended_action=mem_rec,
            memory_valence=round(float(mem_val), 4),
            memory_write_event=mem_written,
            episodes_in_memory=len(self.agent.memory.episodes) if (self.enable_memory and self.agent.memory) else 0,
            recovery_state=telem.stuck_state,
            recovery_active=telem.recovery_active,
            recovery_tier=telem.recovery_tier,
            friction_estimate=round(float(self.agent.self_model.self_params.estimated_friction_coeff), 4),
            target_distance=round(float(dist_to_food), 4),
            target_acquisition=telem.food_absorbed,
            collision_occurred=telem.collision_occurred,
            veto_asserted=telem.veto_asserted,
            veto_reason=telem.veto_reason,
            empowerment_nats=round(float(telem.empowerment_nats), 4),
            episode_number=self.current_episode,
            seed=self.current_seed,
            environment_id=self.current_env_id
        )
        self.episode_telemetry.append(det_telem)
        
        return {
            "telemetry": det_telem,
            "cmd_L": res["cmd_L"],
            "cmd_R": res["cmd_R"],
            "sensory": sensory,
            "dreamer": dreamer
        }

    def end_episode_consolidation(self) -> int:
        """
        Executes offline memory consolidation and surprise-weighted replay between episodes.
        """
        if self.enable_memory and self.agent.memory:
            return self.agent.memory.consolidate_replay(max_replays=10)
        return 0
