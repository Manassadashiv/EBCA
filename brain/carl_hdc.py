"""
carl_hdc.py — Holographic Hyperdimensional Memory (MEM-102)

Implements event-driven Bipolar Hyperdimensional Computing (HDC) algebra in D = 10,000 dimensions:
- Bipolar Vectors: {-1, +1}^D
- Binding (⊗): Element-wise multiplication (XOR / Association)
- Bundling (⊕): Majority vote / sign-sum (Superposition / Accumulation)
- Associative Similarity: Normalized Cosine Dot-Product

References:
  - Kanerva (2009): Hyperdimensional Computing
  - Technical Specifications Section 4 (MEM-102)
"""

import numpy as np


class HolographicEpisodicMemory:
    """
    10,000-D Bipolar Holographic Working & Long-Term Episodic Memory (MEM-102).
    Bundles multi-modal snapshots (Place ⊗ Sonar ⊗ Endocrine) on event boundaries.
    """

    def __init__(self, dimension: int = 10000, n_places: int = 400, seed: int = 42):
        self.D = dimension
        self.rng = np.random.RandomState(seed)

        # Pre-allocated orthogonal base hypervectors
        self.place_bases = self._generate_bipolar((n_places, self.D))
        self.sonar_bases = self._generate_bipolar((24, self.D))
        self.endocrine_bases = self._generate_bipolar((4, self.D))  # DA, NE, 5-HT, ACh

        # Long-Term Memory Superposition Vector (Positive / Spatial Knowledge)
        self.M_spatial = np.zeros(self.D, dtype=np.float32)
        # Aversion / Distress Memory Superposition Vector (High NE / Low Battery / Collisions)
        self.M_aversion = np.zeros(self.D, dtype=np.float32)
        self.episode_count = 0
        self.aversion_count = 0
        self.last_encoded_place = -1

    def _generate_bipolar(self, shape) -> np.ndarray:
        """Generates random hypervectors with values strictly in {-1.0, +1.0}."""
        return np.where(self.rng.rand(*shape) > 0.5, 1.0, -1.0).astype(np.float32)

    @staticmethod
    def bind(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        """Binding (⊗): Reversible element-wise multiplication."""
        return v1 * v2

    @staticmethod
    def bundle(vectors: list) -> np.ndarray:
        """Bundling (⊕): Superposition via signed element-wise summation."""
        if not vectors:
            return np.zeros(1, dtype=np.float32)
        s = np.sum(vectors, axis=0)
        return np.where(s >= 0, 1.0, -1.0).astype(np.float32)

    def encode_episode(self, place_idx: int, sonar_dists: np.ndarray,
                       endocrine_states: np.ndarray) -> np.ndarray:
        """
        Binds [Place ⊗ Sonar ⊗ Endocrine] into a single 10,000-D episodic hypervector.
        """
        # 1. Place Vector
        p_vec = self.place_bases[place_idx % len(self.place_bases)]

        # 2. Sonar Summary Vector (continuous distance weighting)
        s_weighted = []
        for i in range(min(24, len(sonar_dists))):
            d_norm = float(np.clip(sonar_dists[i] / 5.0, 0.0, 1.0))
            s_weighted.append(self.sonar_bases[i] * (1.0 - d_norm))
        s_vec = self.bundle(s_weighted)

        # 3. Endocrine Summary Vector
        e_weighted = []
        for j in range(min(4, len(endocrine_states))):
            e_val = float(endocrine_states[j])
            e_weighted.append(self.endocrine_bases[j] * e_val)
        e_vec = self.bundle(e_weighted)

        # Bind all three modalities
        h_episode = self.bind(p_vec, self.bind(s_vec, e_vec))
        return h_episode

    def record_place_transition(self, place_idx: int, sonar_dists: np.ndarray,
                                endocrine_states: np.ndarray) -> bool:
        """
        Event-driven memory write: triggers ONLY when active place index changes.
        """
        if place_idx == self.last_encoded_place or place_idx < 0:
            return False

        h_ep = self.encode_episode(place_idx, sonar_dists, endocrine_states)
        self.M_spatial += h_ep
        self.episode_count += 1

        # If entering high stress/panic state (NE > 0.40), also stamp into Aversion Subspace
        if len(endocrine_states) >= 2 and endocrine_states[1] > 0.40:
            self.M_aversion += h_ep
            self.aversion_count += 1

        self.last_encoded_place = place_idx
        return True

    def record_trauma_episode(self, place_idx: int, sonar_dists: np.ndarray,
                              endocrine_states: np.ndarray):
        """Explicitly records an acute collision/panic episode into aversion memory."""
        h_ep = self.encode_episode(place_idx, sonar_dists, endocrine_states)
        self.M_aversion += h_ep * 2.0
        self.aversion_count += 1

    def evaluate_episodic_threat(self, place_idx: int, sonar_dists: np.ndarray,
                                 endocrine_states: np.ndarray) -> float:
        """
        Closed-Loop Episodic Recall: Evaluates cosine similarity of current state against
        historical aversion/trauma memory. Returns a repulsive threat factor [0.0, 1.0].
        """
        if self.aversion_count == 0:
            return 0.0
        h_current = self.encode_episode(place_idx, sonar_dists, endocrine_states)
        norm_a = np.linalg.norm(self.M_aversion)
        norm_c = np.linalg.norm(h_current)
        if norm_a < 1e-6 or norm_c < 1e-6:
            return 0.0
        cos_sim = float(np.dot(self.M_aversion, h_current) / (norm_a * norm_c))
        # Scale into threat activation above threshold (0.2)
        threat_factor = float(np.clip((cos_sim - 0.20) / 0.50, 0.0, 1.0))
        return threat_factor

    def query_similarity(self, query_vec: np.ndarray) -> float:
        """
        Computes cosine similarity between query hypervector and cumulative spatial memory.
        """
        norm_m = np.linalg.norm(self.M_spatial)
        norm_q = np.linalg.norm(query_vec)
        if norm_m < 1e-6 or norm_q < 1e-6:
            return 0.0
        return float(np.dot(self.M_spatial, query_vec) / (norm_m * norm_q))
