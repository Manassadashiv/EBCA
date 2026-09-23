"""
brain/carl_episodic_memory.py — Episodic Autobiographical Memory & Hippocampal HDC Replay Engine

Encodes and retrieves autobiographical experiences using Hyperdimensional Computing (HDC):
1. Episodic Tuples: ("I was at (x,y)", "My need was N", "I took action A", "Outcome was O", "Hazard encountered H")
2. Associative HDC Binding & Memory Indexing
3. Memory-Guided Decision Biasing (Warns against known hazards, recalls proven trajectories)
4. Offline Consolidation & Experience Replay Buffer
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class AutobiographicalEpisode:
    episode_id: int
    pos_x: float
    pos_y: float
    active_need: str
    action_taken: str
    outcome_valence: float  # +1.0 (successful food/cooling), -1.0 (collision/starvation)
    hazard_encountered: bool
    prediction_error: float
    timestamp_tick: int


class CarlEpisodicMemory:
    """
    Episodic memory store using Hyperdimensional Computing (HDC) representations.
    """
    def __init__(self, hdc_dim: int = 2048):
        self.dim = hdc_dim
        
        # Base Orthogonal Basis Vectors for HDC Binding
        np.random.seed(42)
        self.basis_x = np.random.choice([-1, 1], size=(50, self.dim))
        self.basis_y = np.random.choice([-1, 1], size=(50, self.dim))
        self.basis_needs = {
            "SEEK_ENERGY": np.random.choice([-1, 1], size=self.dim),
            "COOL_MOTORS": np.random.choice([-1, 1], size=self.dim),
            "REST_FATIGUE": np.random.choice([-1, 1], size=self.dim),
            "RESTORE_SAFETY": np.random.choice([-1, 1], size=self.dim),
            "REDUCE_UNCERTAINTY": np.random.choice([-1, 1], size=self.dim),
            "EXPLORE_NOVELTY": np.random.choice([-1, 1], size=self.dim)
        }
        self.basis_actions = {
            "STRAIGHT_FORWARD": np.random.choice([-1, 1], size=self.dim),
            "CURVE_LEFT_SLIGHT": np.random.choice([-1, 1], size=self.dim),
            "CURVE_LEFT_MODERATE": np.random.choice([-1, 1], size=self.dim),
            "CURVE_LEFT_STRONG": np.random.choice([-1, 1], size=self.dim),
            "CURVE_LEFT_TIGHT": np.random.choice([-1, 1], size=self.dim),
            "CURVE_RIGHT_SLIGHT": np.random.choice([-1, 1], size=self.dim),
            "CURVE_RIGHT_MODERATE": np.random.choice([-1, 1], size=self.dim),
            "CURVE_RIGHT_STRONG": np.random.choice([-1, 1], size=self.dim),
            "CURVE_RIGHT_TIGHT": np.random.choice([-1, 1], size=self.dim),
            "SLOW_CREEP_FORWARD": np.random.choice([-1, 1], size=self.dim),
            "EMERGENCY_REVERSE": np.random.choice([-1, 1], size=self.dim),
            "EMERGENCY_SPIN_LEFT": np.random.choice([-1, 1], size=self.dim),
            "EMERGENCY_SPIN_RIGHT": np.random.choice([-1, 1], size=self.dim),
            "BRAKE_REST": np.random.choice([-1, 1], size=self.dim),
            "GENTLE_LEFT": np.random.choice([-1, 1], size=self.dim),
            "GENTLE_RIGHT": np.random.choice([-1, 1], size=self.dim),
            "IN_PLACE_SPIN_LEFT": np.random.choice([-1, 1], size=self.dim),
            "IN_PLACE_SPIN_RIGHT": np.random.choice([-1, 1], size=self.dim)
        }
        
        # Episodic Experience Buffer
        self.episodes: List[AutobiographicalEpisode] = []
        self.hdc_memory_matrix = np.zeros(self.dim)
        self.recalled_count = 0

    def _normalize_need(self, need: str) -> str:
        mapping = {
            "VIABILITY": "RESTORE_SAFETY",
            "SAFETY": "RESTORE_SAFETY",
            "ENERGY": "SEEK_ENERGY",
            "CURIOSITY": "EXPLORE_NOVELTY",
            "FATIGUE": "REST_FATIGUE",
            "THERMAL": "COOL_MOTORS"
        }
        return mapping.get(need, need)

    def encode_spatial_hdc(self, x: float, y: float) -> np.ndarray:
        """
        Quantizes (x, y) into a bound Hyperdimensional Vector: H_pos = Bind(H_x, H_y).
        """
        idx_x = int(np.clip((x + 5.0) * 5.0, 0, 49))
        idx_y = int(np.clip((y + 5.0) * 5.0, 0, 49))
        
        vx = self.basis_x[idx_x]
        vy = self.basis_y[idx_y]
        return vx * vy # Element-wise XOR/multiplication binding

    def store_episode(self, pos_x: float, pos_y: float, active_need: str, action: str, outcome_valence: float, hazard: bool, pred_err: float, tick: int):
        """
        Stores an autobiographical experience into episodic memory.
        """
        norm_need = self._normalize_need(active_need)
        ep = AutobiographicalEpisode(
            episode_id=len(self.episodes),
            pos_x=pos_x,
            pos_y=pos_y,
            active_need=norm_need,
            action_taken=action,
            outcome_valence=outcome_valence,
            hazard_encountered=hazard,
            prediction_error=pred_err,
            timestamp_tick=tick
        )
        self.episodes.append(ep)
        
        # HDC Memory Encoding: M = M + valence * (H_pos * H_need * H_action)
        h_pos = self.encode_spatial_hdc(pos_x, pos_y)
        h_need = self.basis_needs.get(norm_need, np.ones(self.dim))
        h_act = self.basis_actions.get(action, np.ones(self.dim))
        
        h_episode = h_pos * h_need * h_act
        self.hdc_memory_matrix += outcome_valence * h_episode

    def query_associative_memory(self, current_x: float, current_y: float, active_need: str) -> Dict[str, Any]:
        """
        Queries episodic memory for past experiences at current location:
        Returns recommended actions (positive valence) and hazardous actions to avoid.
        """
        if len(self.episodes) == 0:
            return {"recommended_action": None, "warn_hazard": False, "memory_valence": 0.0}
            
        norm_need = self._normalize_need(active_need)
        h_pos = self.encode_spatial_hdc(current_x, current_y)
        h_need = self.basis_needs.get(norm_need, np.ones(self.dim))
        
        # Unbind probe: H_probe = H_pos * H_need
        h_probe = h_pos * h_need
        
        # Query similarity with all actions
        best_act = None
        best_score = -999.0
        worst_score = 999.0
        worst_act = None
        
        for act_name, h_act in self.basis_actions.items():
            h_hypo = h_probe * h_act
            # Cosine similarity with memory matrix
            sim = float(np.dot(self.hdc_memory_matrix, h_hypo) / (np.linalg.norm(self.hdc_memory_matrix) + 1e-6))
            if sim > best_score:
                best_score = sim
                best_act = act_name
            if sim < worst_score:
                worst_score = sim
                worst_act = act_name
                
        # Check nearby episodic hazard history
        nearby_hazards = [
            ep for ep in self.episodes
            if math.sqrt((ep.pos_x - current_x)**2 + (ep.pos_y - current_y)**2) < 0.8 and ep.hazard_encountered
        ]
        
        self.recalled_count += 1
        return {
            "recommended_action": best_act if best_score > 0.05 else None,
            "avoid_action": worst_act if worst_score < -0.05 else None,
            "warn_hazard": len(nearby_hazards) > 0,
            "memory_valence": float(best_score),
            "recalled_episodes_count": len(nearby_hazards)
        }

    def consolidate_replay(self, max_replays: int = 10) -> int:
        """
        Offline Replay Consolidation:
        Replays high-surprise / high-valence memories to strengthen consolidated pathways.
        """
        if len(self.episodes) == 0:
            return 0
            
        # Sort episodes by prediction error (surprise)
        sorted_episodes = sorted(self.episodes, key=lambda ep: ep.prediction_error, reverse=True)
        replay_set = sorted_episodes[:max_replays]
        
        for ep in replay_set:
            h_pos = self.encode_spatial_hdc(ep.pos_x, ep.pos_y)
            h_need = self.basis_needs.get(ep.active_need, np.ones(self.dim))
            h_act = self.basis_actions.get(ep.action_taken, np.ones(self.dim))
            # Reinforce memory trace
            self.hdc_memory_matrix += 0.5 * ep.outcome_valence * (h_pos * h_need * h_act)
            
        return len(replay_set)
