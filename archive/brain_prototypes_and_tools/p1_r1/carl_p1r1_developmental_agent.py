"""
brain/p1_r1/carl_p1r1_developmental_agent.py — P1-R1 Reachable Developmental Organism

Wraps the frozen P0 CarlAutonomousOrganismAgent with:
- Cross-episode HDC episodic memory persistence
- Generic experience-memory encoding (salient prediction errors, near-barrier constraints, food absorption)
- Clean causal ablation switches (enable_memory, enable_adaptation, enable_need)
- Zero behavior-specific heuristics, route labels, or scripted solution rules.
"""

from typing import Dict, Any, Optional, Tuple
import math
import numpy as np

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_embodied_organism import CarlEmbodiedOrganism


class CarlP1R1DevelopmentalAgent:
    """
    P1-R1 Developmental Organism Agent.
    """
    def __init__(
        self,
        dt: float = 0.0333,
        enable_memory: bool = True,
        enable_adaptation: bool = True,
        enable_need: bool = True
    ):
        self.dt = dt
        self.enable_memory = enable_memory
        self.enable_adaptation = enable_adaptation
        self.enable_need = enable_need
        
        # Instantiate frozen P0 baseline agent
        self.agent = CarlAutonomousOrganismAgent(dt=dt, enable_memory=enable_memory)
        
        # Episode-level metadata
        self.current_episode = 1
        self.current_seed = 42
        self.current_condition = "FULL_P1_R1"
        self.episode_tick = 0
        self.memory_writes_this_episode = 0
        self.memory_retrievals_this_episode = 0

    def reset_for_episode(
        self,
        episode_num: int,
        seed: int,
        condition: str,
        preserve_memory: bool = True
    ):
        """
        Resets agent state for a new episode.
        Preserves HDC episodic memory if preserve_memory is True.
        """
        self.current_episode = episode_num
        self.current_seed = seed
        self.current_condition = condition
        self.episode_tick = 0
        self.memory_writes_this_episode = 0
        self.memory_retrievals_this_episode = 0
        
        # Backup memory if preserving
        mem_backup = None
        if self.enable_memory and preserve_memory and len(self.agent.memory.episodes) > 0:
            mem_backup = {
                "episodes": list(self.agent.memory.episodes),
                "matrix": np.copy(self.agent.memory.hdc_memory_matrix)
            }
            
        # Reset agent controller state
        self.agent.reset()
        
        # Restore memory if backed up
        if mem_backup is not None:
            self.agent.memory.episodes = mem_backup["episodes"]
            self.agent.memory.hdc_memory_matrix = mem_backup["matrix"]
            
        # Reset homeostasis energy need
        self.agent.homeostasis.energy = 0.35 if self.enable_need else 1.0
        self.agent.homeostasis.thermal_load = 0.0
        self.agent.homeostasis.motor_fatigue = 0.0
        self.agent.homeostasis.safety_margin = 1.0

    def step_developmental_cycle(
        self,
        hal: CarlEmbodiedOrganism,
        food_coords: Optional[Tuple[float, float]] = (1.60, 0.0)
    ) -> Dict[str, Any]:
        """
        Executes one 30 Hz developmental perception-cognition-action cycle.
        """
        self.episode_tick += 1
        
        # Force adaptation ablation if disabled
        if not self.enable_adaptation:
            self.agent.self_model.estimated_friction = 2.50
            
        # Execute P0 cognitive cycle
        step_res = self.agent.step_cognitive_cycle(hal, food_coords=food_coords)
        t = step_res["telemetry"]
        sensory = step_res["sensory"]
        
        if t.recalled_hazard_warned:
            self.memory_retrievals_this_episode += 1
            
        # Generic Experience-Memory Encoding (Zero heuristics, generic events)
        if self.enable_memory:
            is_salient_event = (
                t.prediction_error > 0.18 or
                sensory.min_obstacle_dist < 0.35 or
                t.veto_asserted or
                t.food_absorbed or
                t.collision_occurred
            )
            if is_salient_event:
                valence = 1.0 if t.food_absorbed else -1.0
                hazard = not t.food_absorbed
                self.agent.memory.store_episode(
                    sensory.pos_x,
                    sensory.pos_y,
                    t.active_goal_type,
                    t.chosen_action_name,
                    valence,
                    hazard=hazard,
                    pred_err=t.prediction_error,
                    tick=self.episode_tick
                )
                self.memory_writes_this_episode += 1
                
        return {
            "sensory": sensory,
            "telemetry": t,
            "memory_writes": self.memory_writes_this_episode,
            "memory_retrievals": self.memory_retrievals_this_episode,
            "total_memory_episodes": len(self.agent.memory.episodes)
        }

    def end_episode_consolidation(self):
        """
        Performs offline surprise replay consolidation between episodes.
        """
        if self.enable_memory and len(self.agent.memory.episodes) > 0:
            self.agent.memory.consolidate_replay(max_replays=10)
