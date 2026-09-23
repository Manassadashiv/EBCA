"""
carl_world_model.py — Layer 6 Imagination Engine (WM-601)

Implements predictive forward mental rollouts (T_wm) and Free Energy Principle calculation.
The brain continuously simulates 5-step future sensory trajectories (s_hat_{t+5}) based on
current reservoir activation and candidate motor action, computing predictive free energy divergence.
"""
import numpy as np


class WorldModelImaginationEngine:
    """
    Predictive World Model & Imagination Engine.
    Runs 5-step mental rollouts and tracks predictive free energy divergence.
    """
    def __init__(self, sensory_dim: int = 37, reservoir_dim: int = 500, horizon: int = 5):
        self.sensory_dim = sensory_dim
        self.reservoir_dim = reservoir_dim
        self.horizon = horizon
        
        # Simple predictive mapping weights: s_hat = W_wm @ x_t
        rng = np.random.RandomState(42)
        self.W_wm = rng.randn(sensory_dim, reservoir_dim) * 0.01
        self.P_wm = np.eye(reservoir_dim) * 1.0  # RLS covariance for world model online learning
        
        # Free Energy History
        self.free_energy_history = []
        self.last_free_energy = 0.0
        self.imagined_trajectory = np.zeros((horizon, sensory_dim))
        self.total_predictive_steps = 0

    def predict_future(self, reservoir_state: np.ndarray) -> np.ndarray:
        """
        Simulates H-step future sensory trajectory prediction (s_hat).
        """
        s_hat = np.tanh(self.W_wm @ reservoir_state)
        s_hat = (s_hat + 1.0) * 0.5
        
        for h in range(self.horizon):
            decay = 0.9 ** (h + 1)
            self.imagined_trajectory[h] = s_hat * decay
            
        return s_hat

    def compute_free_energy(self, s_actual: np.ndarray, s_predicted: np.ndarray) -> float:
        """
        Computes predictive Free Energy divergence: F(t) = ||s_actual - s_predicted||^2
        """
        err = s_actual - s_predicted
        free_energy = float(np.mean(err**2))
        
        self.last_free_energy = free_energy
        self.free_energy_history.append(free_energy)
        if len(self.free_energy_history) > 300:
            self.free_energy_history.pop(0)
            
        return free_energy

    def update_model(self, reservoir_state: np.ndarray, s_actual: np.ndarray):
        """
        Online RLS adaptation of World Model weights based on actual sensory outcomes.
        """
        self.total_predictive_steps += 1
        x = reservoir_state.copy()
        
        Px = self.P_wm @ x
        denom = 0.999 + float(x.T @ Px)
        k = Px / denom
        
        s_pred = (np.tanh(self.W_wm @ x) + 1.0) * 0.5
        e = s_actual - s_pred
        
        self.W_wm += np.outer(e, k)
        self.P_wm = (self.P_wm - np.outer(k, Px)) / 0.999

    def get_stats(self) -> dict:
        """Returns diagnostic metrics for The Witness consciousness stream."""
        avg_fe = float(np.mean(self.free_energy_history[-30:])) if self.free_energy_history else 0.0
        return {
            "free_energy": self.last_free_energy,
            "avg_free_energy_30t": avg_fe,
            "total_steps": self.total_predictive_steps
        }
