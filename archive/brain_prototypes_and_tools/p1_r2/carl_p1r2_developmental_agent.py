"""
brain/p1_r2/carl_p1r2_developmental_agent.py — Isolated Phase 1-R2 Developmental Organism

Wraps CARL's embodied foundation with a Generic Short-Horizon Multi-Step Action Rollout
evaluator over the differential-drive locomotion primitives.

ZERO BEHAVIOR-SPECIFIC HEURISTICS:
- No hardcoded route preferences (no left/right bias).
- No waypoint tables or pre-baked trajectories.
- Evaluates composite multi-step action sequences [a1, a2] inside the predictive forward model.
- Evaluates Expected Free Energy:
    G(S) = Distance_Cost + Heading_Alignment + Curvature_Effort + Forward_TTC_Risk - Velocity_Bonus - Associative_Memory.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_episodic_memory import AutobiographicalEpisode


class CarlP1R2DevelopmentalAgent:
    """
    P1-R2 Developmental Agent with Short-Horizon Multi-Step Action Sequence Rollouts.
    """
    def __init__(
        self,
        dt: float = 0.0333,
        enable_memory: bool = True,
        enable_adaptation: bool = True,
        enable_need: bool = True,
        horizon_steps: int = 18
    ):
        self.dt = dt
        self.enable_memory = enable_memory
        self.enable_adaptation = enable_adaptation
        self.enable_need = enable_need
        self.horizon_steps = horizon_steps
        
        # Instantiate frozen baseline organism agent
        self.agent = CarlAutonomousOrganismAgent(
            dt=self.dt,
            enable_memory=self.enable_memory
        )
        
        # Continuous curvature action primitive library
        self.candidate_actions = {
            "STRAIGHT_FORWARD": {"cmd": np.array([5.5, 5.5]), "curv": 0.0, "v": 0.275},
            "CURVE_LEFT_SLIGHT": {"cmd": np.array([4.8, 5.8]), "curv": +0.40, "v": 0.265},
            "CURVE_LEFT_MODERATE": {"cmd": np.array([3.8, 6.0]), "curv": +1.00, "v": 0.245},
            "CURVE_RIGHT_SLIGHT": {"cmd": np.array([5.8, 4.8]), "curv": -0.40, "v": 0.265},
            "CURVE_RIGHT_MODERATE": {"cmd": np.array([6.0, 3.8]), "curv": -1.00, "v": 0.245}
        }
        
        # Differential drive kinematic constants
        self.wheel_radius = 0.048
        self.track_width = 0.23
        self.sonar_angles = np.linspace(-math.radians(120), math.radians(120), 15)
        
        # Precompute 2-segment sequence library (5 x 5 = 25 candidate sequences)
        self.prim_names = list(self.candidate_actions.keys())
        self.sequence_library = [(a1, a2) for a1 in self.prim_names for a2 in self.prim_names]
        
        # Diagnostic tracking
        self.last_selected_sequence = ("STRAIGHT_FORWARD", "STRAIGHT_FORWARD")
        self.last_candidate_efes = {}
        self.memory_writes_this_episode = 0
        self.memory_retrievals_this_episode = 0

    def reset_for_episode(self, episode_num: int, seed: int, condition: str, preserve_memory: bool = True):
        """
        Resets agent controller state for a new episode while preserving episodic memory
        across episodes if preserve_memory=True and enable_memory=True.
        """
        mem_backup = None
        if self.enable_memory and preserve_memory and len(self.agent.memory.episodes) > 0:
            mem_backup = {
                "episodes": list(self.agent.memory.episodes),
                "matrix": np.copy(self.agent.memory.hdc_memory_matrix)
            }
            
        self.agent.reset()
        
        if mem_backup is not None:
            self.agent.memory.episodes = mem_backup["episodes"]
            self.agent.memory.hdc_memory_matrix = mem_backup["matrix"]
            
        self.agent.homeostasis.energy = 0.35 if self.enable_need else 1.0
        self.memory_writes_this_episode = 0
        self.memory_retrievals_this_episode = 0
        self.last_selected_sequence = ("STRAIGHT_FORWARD", "STRAIGHT_FORWARD")
        self.last_candidate_efes = {}

    def evaluate_sequence_rollouts(
        self,
        sensory,
        target_pos: Tuple[float, float] = (1.80, 0.0)
    ) -> Tuple[Tuple[str, str], float, Dict[str, float]]:
        """
        Evaluates candidate 2-segment multi-step sequences [a1, a2] inside the internal forward model.
        Returns ((best_a1, best_a2), best_efe, all_candidate_efes).
        """
        sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 5.0
        
        # 1. Project sensed sonar points into 2D world space
        sensed_points = []
        for d_ray, ang in zip(sonar, self.sonar_angles):
            if d_ray < 2.5:
                pt_x = sensory.pos_x + d_ray * math.cos(sensory.yaw + ang)
                pt_y = sensory.pos_y + d_ray * math.sin(sensory.yaw + ang)
                sensed_points.append((pt_x, pt_y))
                
        best_seq = self.sequence_library[0]
        min_efe = float("inf")
        candidate_efes = {}
        
        r = self.wheel_radius
        b = self.track_width
        dt = self.dt
        k_steps = self.horizon_steps
        
        for a1, a2 in self.sequence_library:
            seq_name = f"{a1}->{a2}"
            seq = [self.candidate_actions[a1], self.candidate_actions[a2]]
            
            sim_x = float(sensory.pos_x)
            sim_y = float(sensory.pos_y)
            sim_yaw = float(sensory.yaw)
            
            risk = 0.0
            effort = 0.0
            
            for act_data in seq:
                cmd = act_data["cmd"]
                curv = act_data["curv"]
                v_lin = act_data["v"]
                w_yaw = (cmd[1] - cmd[0]) * r / b
                effort += (curv ** 2) * 0.05
                
                for step in range(1, k_steps + 1):
                    sim_x += v_lin * math.cos(sim_yaw) * dt
                    sim_y += v_lin * math.sin(sim_yaw) * dt
                    sim_yaw += w_yaw * dt
                    
                    # Forward-Hemisphere Sensed Obstacle Clearance & Time-To-Collision (TTC) Risk
                    for px, py in sensed_points:
                        dx = px - sim_x
                        dy = py - sim_y
                        d_pt = math.sqrt(dx**2 + dy**2)
                        
                        is_ahead = (dx * math.cos(sim_yaw) + dy * math.sin(sim_yaw)) > 0
                        if is_ahead:
                            if d_pt < 0.28:
                                risk += (0.28 - d_pt) * 60.0
                            if d_pt < 0.08:
                                risk += 600.0
                            v_app = v_lin * (dx * math.cos(sim_yaw) + dy * math.sin(sim_yaw)) / (d_pt + 1e-4)
                            if v_app > 0.0 and d_pt < 1.0:
                                risk += (v_app / (d_pt + 0.1)**2) * 5.0
                        else:
                            if d_pt < 0.16:
                                risk += (0.16 - d_pt) * 80.0
                                
                    bd = min(4.8 - abs(sim_x), 4.8 - abs(sim_y))
                    if bd < 0.35:
                        risk += (0.35 - bd) * 100.0
            
            final_dist = math.sqrt((target_pos[0] - sim_x)**2 + (target_pos[1] - sim_y)**2)
            target_bearing = math.atan2(target_pos[1] - sim_y, target_pos[0] - sim_x)
            final_head_err = abs(math.atan2(math.sin(sim_yaw - target_bearing), math.cos(sim_yaw - target_bearing)))
            
            # Expected Free Energy: Distance + Alignment + Effort + Risk - Velocity
            dist_cost = final_dist * 80.0
            align_cost = final_head_err * 12.0
            vel_bonus = (seq[0]["v"] + seq[1]["v"]) * 30.0
            
            efe = dist_cost + align_cost + effort + risk - vel_bonus
            
            # Associative Episodic Memory Bias
            if self.enable_memory and len(self.agent.memory.episodes) > 0:
                q = self.agent.memory.query_associative_memory(sim_x, sim_y, "SEEK_ENERGY")
                self.memory_retrievals_this_episode += 1
                if q.get("warn_hazard", False) and q.get("avoid_action") == a1:
                    efe += 35.0
                if q.get("recommended_action") == a1:
                    efe -= 15.0
                    
            candidate_efes[seq_name] = float(efe)
            if efe < min_efe:
                min_efe = efe
                best_seq = (a1, a2)
                
        return best_seq, min_efe, candidate_efes

    def step(self, hal, target_coords: Tuple[float, float] = (1.80, 0.0)) -> Dict[str, Any]:
        """
        Steps one 30 Hz cognitive perception-rollout-actuation cycle.
        """
        sensory = self.agent.embodiment.read_proprioception(hal)
        
        # 1. Multi-Step Action Sequence Evaluation
        best_seq, best_efe, candidate_efes = self.evaluate_sequence_rollouts(sensory, target_pos=target_coords)
        self.last_selected_sequence = best_seq
        self.last_candidate_efes = candidate_efes
        
        best_a1 = best_seq[0]
        act_cmd = self.candidate_actions[best_a1]["cmd"]
        
        # 2. Step embodied motor filter
        self.agent.embodiment.target_w_L = float(act_cmd[0])
        self.agent.embodiment.target_w_R = float(act_cmd[1])
        
        # Active gaze tracking
        target_bearing = math.atan2(target_coords[1] - sensory.pos_y, target_coords[0] - sensory.pos_x) - sensory.yaw
        target_bearing = (target_bearing + math.pi) % (2 * math.pi) - math.pi
        self.agent.embodiment.target_head_yaw = float(np.clip(target_bearing, -1.2, 1.2))
        
        self.agent.embodiment.step_embodiment(hal)
        for _ in range(3):
            hal.step()
        self.agent.tick += 1
            
        # 3. Compute Prediction Error
        r = self.wheel_radius
        v_est = float((act_cmd[0] + act_cmd[1]) * 0.5 * r)
        pred_error = abs(sensory.speed - v_est)
        
        # 4. Check Food Absorption & Collision
        dist_food = math.sqrt((target_coords[0] - sensory.pos_x)**2 + (target_coords[1] - sensory.pos_y)**2)
        food_absorbed = (dist_food < 0.30)
        collision_occurred = sensory.has_body_collision
        
        # 5. Generic Experience-Memory Encoding (Real collisions and goal acquisitions)
        if self.enable_memory:
            if food_absorbed:
                self.agent.memory.store_episode(
                    pos_x=float(sensory.pos_x),
                    pos_y=float(sensory.pos_y),
                    active_need="SEEK_ENERGY",
                    action=best_a1,
                    outcome_valence=1.0,
                    hazard=False,
                    pred_err=float(pred_error),
                    tick=int(self.agent.tick)
                )
                self.memory_writes_this_episode += 1
            elif collision_occurred or (pred_error > 0.20 and sensory.speed < 0.05):
                self.agent.memory.store_episode(
                    pos_x=float(sensory.pos_x),
                    pos_y=float(sensory.pos_y),
                    active_need="SEEK_ENERGY",
                    action=best_a1,
                    outcome_valence=-1.0,
                    hazard=True,
                    pred_err=float(pred_error),
                    tick=int(self.agent.tick)
                )
                self.memory_writes_this_episode += 1
                
        return {
            "sensory": sensory,
            "best_action": best_a1,
            "best_sequence": f"{best_seq[0]}->{best_seq[1]}",
            "best_efe": float(best_efe),
            "candidate_efes": candidate_efes,
            "prediction_error": float(pred_error),
            "food_absorbed": food_absorbed,
            "collision_occurred": collision_occurred,
            "dist_food": float(dist_food),
            "memory_writes": self.memory_writes_this_episode,
            "memory_retrievals": self.memory_retrievals_this_episode,
            "episodes_in_memory": len(self.agent.memory.episodes) if self.enable_memory else 0
        }

    def end_episode_consolidation(self):
        """
        Performs offline surprise replay consolidation between episodes.
        """
        if self.enable_memory and len(self.agent.memory.episodes) > 0:
            self.agent.memory.consolidate_replay(max_replays=10)
