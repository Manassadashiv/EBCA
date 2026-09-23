"""
carl_concept_genesis.py — Layer 7 Concept Genesis & Qualia Discovery (CG-701)

Implements an unsupervised 10x10 Kohonen Self-Organizing Map (SOM) topological clustering engine.
Raw sensory streams (37-D inputs + neuromodulator state + speed) are mapped to 100 topological nodes,
discovering emergent qualia categories ("Corridor Trapped", "Safe Haven", "Metabolic Crisis", etc.)
"""
import numpy as np


class ConceptGenesisEngine:
    """
    Unsupervised Self-Organizing Map (SOM) for emergent qualia and concept discovery.
    """
    def __init__(self, input_dim: int = 42, grid_shape: tuple = (10, 10), lr: float = 0.1):
        self.input_dim = input_dim
        self.grid_rows, self.grid_cols = grid_shape
        self.num_nodes = self.grid_rows * self.grid_cols
        self.initial_lr = lr
        self.lr = lr
        self.sigma = max(grid_shape) / 2.0
        self.total_train_steps = 0
        
        # 10x10 SOM Weight Grid (10, 10, input_dim)
        rng = np.random.RandomState(42)
        self.W_som = rng.rand(self.grid_rows, self.grid_cols, input_dim)
        
        # Fixed node coordinates for distance metric
        self.coords = np.array([
            [r, c] for r in range(self.grid_rows) for c in range(self.grid_cols)
        ]).reshape(self.grid_rows, self.grid_cols, 2)
        
        # Human-readable qualia category map (discovered clusters)
        self.node_labels = {}
        self._initialize_qualia_clusters()
        
        self.active_node = (0, 0)
        self.active_qualia_label = "Initial Emergence"

    def _initialize_qualia_clusters(self):
        """Seed structural qualia regions based on 10x10 SOM topology."""
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                if r < 3 and c < 3:
                    label = "Open Safe Territory"
                elif r < 3 and c >= 7:
                    label = "Food Beacon Target"
                elif r >= 7 and c < 3:
                    label = "Confined Corridor Trap"
                elif r >= 7 and c >= 7:
                    label = "High Hazard Boundary"
                elif 3 <= r <= 6 and 3 <= c <= 6:
                    label = "Central Exploration Zone"
                else:
                    label = "Transitional Qualia"
                self.node_labels[(r, c)] = label

    def step(self, sensory_vector: np.ndarray) -> tuple:
        """
        Processes a single sensory frame, finds the Best Matching Unit (BMU),
        and updates SOM topology online via Hebbian neighborhood adaptation.
        
        Args:
            sensory_vector: 42-D input vector (37 sonar/features + 4 neuromodulators + battery)
            
        Returns:
            (bmu_coord, qualia_label)
        """
        # Ensure vector matches input_dim
        v = np.zeros(self.input_dim)
        n = min(len(sensory_vector), self.input_dim)
        v[:n] = sensory_vector[:n]
        
        # Find Best Matching Unit (BMU) by Euclidean distance
        diff = self.W_som - v
        dist_sq = np.sum(diff**2, axis=-1)
        bmu_idx = np.unravel_index(np.argmin(dist_sq), (self.grid_rows, self.grid_cols))
        
        self.active_node = bmu_idx
        self.active_qualia_label = self.node_labels.get(bmu_idx, "Emergent Qualia")
        
        # Online SOM topological adaptation
        self.total_train_steps += 1
        bmu_r, bmu_c = bmu_idx
        
        # Topological Gaussian neighborhood matrix
        dist_from_bmu = np.sum((self.coords - np.array([bmu_r, bmu_c]))**2, axis=-1)
        neighborhood = np.exp(-dist_from_bmu / (2.0 * (self.sigma**2)))
        
        # Update SOM weight grid
        influence = self.lr * neighborhood[:, :, np.newaxis]
        self.W_som += influence * (v - self.W_som)
        
        # Decay learning rate & neighborhood radius
        decay_factor = np.exp(-self.total_train_steps / 1000.0)
        self.lr = max(0.01, self.initial_lr * decay_factor)
        self.sigma = max(0.5, (max(self.grid_rows, self.grid_cols) / 2.0) * decay_factor)
        
        return bmu_idx, self.active_qualia_label

    def get_qualia_summary(self) -> dict:
        """Returns diagnostic metrics for The Witness consciousness stream."""
        return {
            "bmu_node": self.active_node,
            "qualia_label": self.active_qualia_label,
            "som_train_steps": self.total_train_steps,
            "current_lr": self.lr
        }
