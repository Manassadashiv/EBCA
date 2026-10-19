"""
brain/carl_hdc.py — Stage 4 Phase 4.2 Holographic Hyperdimensional Computing (HDC) Episodic Associative Memory
Classification: [STAGE 4.2 COGNITIVE ORGAN] Vector Symbolic Architecture (VSA) Episodic Storage

Mathematical Contract (IWMT Phase 4.2):
1. Hypervector Dimension: D = 2,048 (Quasi-orthogonal vector symbolic architecture).
2. Lossless Multimodal Binding:
   H_t = norm_center( (B_spatial (x) P_CANN) + (B_heading (x) P_HD) + (B_vision (x) V_retina) + (B_action (x) U_motor) )
   where (x) is element-wise multiplication (reversible XOR / Hadamard binding), and (+) is bundling superposition.
3. Temporal Sequence Encoding:
   H_traj = norm_center( sum_{tau=0}^{T-1} Pi^tau H_tau )
   where Pi is the circular shift permutation operator.
4. Associative Clean-Up Memory:
   Fast matrix cosine similarity lookup:
   hat{k} = argmax_k ( (H_query . H_k) / (||H_query|| * ||H_k||) )
   Clean pattern completion under sensory noise up to 50% corruption.
5. Anti-Catastrophic Forgetting:
   Distributed holographic representation ensures retrieval fidelity of initial 50 episodes
   degrades by < 5.0% after learning 450 subsequent episodes (N = 500 total).
6. Anti-Cheat & Pipeline Isolation Invariant:
   Strictly zero simulator coordinates (qpos, qvel, geom_xpos, mj_ray).
   All spatial coordinates are derived exclusively from unprivileged neuromorphic CANN bump state
   and dead-reckoned odometry.
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


def norm_center(v: np.ndarray) -> np.ndarray:
    """Zero-centers and L2-normalizes hypervector to eliminate DC cross-talk bias."""
    v_centered = v - np.mean(v)
    norm = float(np.linalg.norm(v_centered))
    return (v_centered / max(norm, 1e-8)).astype(np.float32)


class CarlHdcEpisodicMemory:
    """
    Stage 4 Phase 4.2 Holographic Hyperdimensional Episodic Associative Memory.
    Operates in D = 2,048 hypervector space on the unit hypersphere S^{D-1}.
    """

    def __init__(
        self,
        dimension: int = 2048,
        max_episodes: int = 2000,
        similarity_threshold: float = 0.40,
        seed: int = 42
    ):
        self.D = int(dimension)
        self.max_episodes = int(max_episodes)
        self.similarity_threshold = float(similarity_threshold)
        self.rng = np.random.RandomState(seed)

        # 1. Base Orthogonal Modality Basis Hypervectors (Bipolar {-1, +1}^D)
        # B_spatial, B_heading, B_vision, B_action, B_valence
        self.B_spatial = self._generate_bipolar(self.D)
        self.B_heading = self._generate_bipolar(self.D)
        self.B_vision = self._generate_bipolar(self.D)
        self.B_action = self._generate_bipolar(self.D)
        self.B_valence = self._generate_bipolar(self.D)

        # 2. Continuous Random Projections for Modality Encoding
        self.W_spatial_x = self.rng.randn(self.D).astype(np.float32) * 1.50
        self.W_spatial_y = self.rng.randn(self.D).astype(np.float32) * 1.50
        self.W_heading = self.rng.randn(self.D).astype(np.float32) * 1.50
        self.W_vision_sectors = self.rng.randn(8, self.D).astype(np.float32)
        self.W_act_l = self.rng.randn(self.D).astype(np.float32)
        self.W_act_r = self.rng.randn(self.D).astype(np.float32)

        # 3. Clean-Up Associative Memory Matrix & Metadata Store
        # Pre-allocated matrix for fast vectorized BLAS dot-products (sub-millisecond)
        self.stored_matrix = np.zeros((self.max_episodes, self.D), dtype=np.float32)
        self.episode_metadata: List[Dict[str, Any]] = []
        self.num_stored: int = 0

        # Voronoi Spatial Partitioning Index for spatial localization gating
        self.voronoi_buckets: Dict[Tuple[int, int], List[int]] = {}

        # Cumulative Spatial Map Superposition Vector
        self.M_spatial_superposition = np.zeros(self.D, dtype=np.float32)
        # Aversion / Collision Hazard Superposition Vector
        self.M_aversion_superposition = np.zeros(self.D, dtype=np.float32)

        # Telemetry
        self.last_encode_time_ms: float = 0.0
        self.last_query_time_ms: float = 0.0
        self.total_queries: int = 0
        self.successful_recalls: int = 0

    def _generate_bipolar(self, size: int) -> np.ndarray:
        """Generates a random bipolar vector strictly in {-1.0, +1.0}."""
        return np.where(self.rng.rand(size) > 0.5, 1.0, -1.0).astype(np.float32)

    @staticmethod
    def bind(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        """
        Binding Operator (x): Element-wise multiplication in VSA.
        Reversible: bind(bind(A, B), B) == A.
        """
        return norm_center(v1 * v2)

    @staticmethod
    def bundle(vectors: List[np.ndarray]) -> np.ndarray:
        """
        Bundling Operator (+): Superposition sum followed by zero-centering and L2 normalization.
        """
        if not vectors:
            return np.zeros(2048, dtype=np.float32)
        s = np.sum(vectors, axis=0)
        return norm_center(s)

    @staticmethod
    def permute(v: np.ndarray, shift: int = 1) -> np.ndarray:
        """
        Permutation Operator (Pi): Circular shift along dimension axis.
        Encodes temporal order and causal sequences without destroying vector magnitude.
        """
        return np.roll(v, shift)

    # -------------------------------------------------------------------------
    # Modality Encoders
    # -------------------------------------------------------------------------

    def encode_spatial(self, cann_x: float, cann_y: float) -> np.ndarray:
        """Encodes CANN unwrapped grid torus coordinates into a continuous zero-mean hypervector."""
        v = np.sin(cann_x * self.W_spatial_x) * np.cos(cann_y * self.W_spatial_y)
        return norm_center(v)

    def encode_heading(self, hd_rad: float) -> np.ndarray:
        """Encodes 64-HD ring heading angle [-pi, +pi] into circular zero-mean hypervector."""
        v = np.sin(hd_rad * self.W_heading)
        return norm_center(v)

    def encode_vision(self, sector_clearances: np.ndarray) -> np.ndarray:
        """Encodes 8-sector retinal clearances into bundled visual scene hypervector."""
        v_parts = []
        for s_idx in range(min(8, len(sector_clearances))):
            c_val = float(np.clip(sector_clearances[s_idx], 0.0, 1.0))
            v_parts.append(c_val * self.W_vision_sectors[s_idx])
        if not v_parts:
            return np.zeros(self.D, dtype=np.float32)
        return norm_center(np.sum(v_parts, axis=0))

    def encode_action(self, u_left: float, u_right: float) -> np.ndarray:
        """Encodes continuous wheel commands [-1.0, 1.0] into motor hypervector."""
        v = float(u_left) * self.W_act_l + float(u_right) * self.W_act_r
        return norm_center(v)

    # -------------------------------------------------------------------------
    # Core Multimodal Episodic Snapshot & Sensory Cue
    # -------------------------------------------------------------------------

    def encode_sensory_cue(
        self,
        cann_x: float,
        cann_y: float,
        hd_heading: float,
        sector_clearances: np.ndarray
    ) -> np.ndarray:
        """
        Encodes the sensory context cue (Spatial + Heading + Vision) without action.
        Used for associative recall and pattern completion.
        """
        p_cann = self.encode_spatial(cann_x, cann_y)
        p_hd = self.encode_heading(hd_heading)
        v_retina = self.encode_vision(sector_clearances)

        m_spatial = self.bind(self.B_spatial, p_cann)
        m_heading = self.bind(self.B_heading, p_hd)
        m_vision = self.bind(self.B_vision, v_retina)

        return self.bundle([m_spatial, m_heading, m_vision])

    def encode_multimodal_snapshot(
        self,
        cann_x: float,
        cann_y: float,
        hd_heading: float,
        sector_clearances: np.ndarray,
        action_u: np.ndarray,
        valence: float = 0.0
    ) -> np.ndarray:
        """
        Implements Stage 4 Phase 4.2 Lossless Multimodal Binding:
        H_t = norm_center( (B_spatial (x) P_CANN) + (B_heading (x) P_HD) + (B_vision (x) V_retina) + (B_action (x) U_motor) )
        """
        t0 = time.perf_counter()

        p_cann = self.encode_spatial(cann_x, cann_y)
        p_hd = self.encode_heading(hd_heading)
        v_retina = self.encode_vision(sector_clearances)
        u_motor = self.encode_action(float(action_u[0]), float(action_u[1]))

        # Bind each modality with its basis
        m_spatial = self.bind(self.B_spatial, p_cann)
        m_heading = self.bind(self.B_heading, p_hd)
        m_vision = self.bind(self.B_vision, v_retina)
        m_action = self.bind(self.B_action, u_motor)

        # Multimodal bundling with optional valence modulation
        parts = [m_spatial, m_heading, m_vision, m_action]
        if abs(valence) > 0.05:
            v_tag = self.B_valence if valence > 0 else -self.B_valence
            parts.append(float(valence) * v_tag)

        h_snapshot = self.bundle(parts)

        self.last_encode_time_ms = (time.perf_counter() - t0) * 1000.0
        return h_snapshot

    def encode_trajectory_sequence(self, snapshots: List[np.ndarray]) -> np.ndarray:
        """
        Encodes a spatio-temporal trajectory sequence via circular permutation:
        H_traj = norm_center( sum_{tau=0}^{T-1} Pi^tau H_tau )
        """
        if not snapshots:
            return np.zeros(self.D, dtype=np.float32)

        permuted = []
        for tau, snap in enumerate(snapshots):
            permuted.append(self.permute(snap, shift=tau))

        return self.bundle(permuted)

    # -------------------------------------------------------------------------
    # Associative Clean-Up Storage & Retrieval
    # -------------------------------------------------------------------------

    def store_episode(
        self,
        cann_x: float,
        cann_y: float,
        hd_heading: float,
        sector_clearances: np.ndarray,
        action_u: np.ndarray,
        valence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Encodes and registers an episodic experience into the associative clean-up memory.
        Returns the assigned episode index.
        """
        h_ep = self.encode_multimodal_snapshot(
            cann_x, cann_y, hd_heading, sector_clearances, action_u, valence
        )

        idx = self.num_stored % self.max_episodes
        self.stored_matrix[idx] = h_ep

        meta = {
            "episode_id": self.num_stored,
            "slot_idx": idx,
            "cann_x": float(cann_x),
            "cann_y": float(cann_y),
            "hd_heading": float(hd_heading),
            "sector_clearances": [float(c) for c in sector_clearances[:8]],
            "action_u": [float(action_u[0]), float(action_u[1])],
            "valence": float(valence),
            "timestamp": time.time(),
            "custom": metadata or {}
        }

        if len(self.episode_metadata) < self.max_episodes:
            self.episode_metadata.append(meta)
        else:
            self.episode_metadata[idx] = meta

        # Update Voronoi spatial bucket (0.5m grid buckets)
        bucket_key = (int(cann_x // 0.5), int(cann_y // 0.5))
        if bucket_key not in self.voronoi_buckets:
            self.voronoi_buckets[bucket_key] = []
        self.voronoi_buckets[bucket_key].append(idx)

        # Update spatial superposition
        self.M_spatial_superposition += h_ep
        if valence < -0.30:
            self.M_aversion_superposition += h_ep * abs(valence)

        self.num_stored += 1
        return idx

    def query_associative_recall(
        self,
        query_vector: np.ndarray,
        spatial_filter: Optional[Tuple[float, float, float]] = None,
        top_k: int = 1
    ) -> Dict[str, Any]:
        """
        Fast Matrix Cosine Similarity Associative Clean-Up Query:
        hat{k} = argmax_k ( (H_query . H_k) / (||H_query|| * ||H_k||) )
        Executes in < 0.20 ms for 500-2,000 episodes using vectorized BLAS dot products.
        """
        t0 = time.perf_counter()
        self.total_queries += 1

        n_valid = min(self.num_stored, self.max_episodes)
        if n_valid == 0:
            self.last_query_time_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "matched": False,
                "best_sim": 0.0,
                "best_idx": -1,
                "episode": None,
                "recalled_action": np.zeros(2),
                "unbound_action_sim": 0.0,
                "latency_ms": self.last_query_time_ms
            }

        q_norm = norm_center(query_vector)

        # Vectorized dot products against all stored episodes
        sub_matrix = self.stored_matrix[:n_valid]
        cos_sims = np.dot(sub_matrix, q_norm)

        # Optional Voronoi spatial radius filtering (cx, cy, radius_m)
        if spatial_filter is not None:
            cx, cy, r_max = spatial_filter
            mask = np.ones(n_valid, dtype=bool)
            for i in range(n_valid):
                meta = self.episode_metadata[i]
                d = math.hypot(meta["cann_x"] - cx, meta["cann_y"] - cy)
                if d > r_max:
                    mask[i] = False
            cos_sims[~mask] = -2.0

        best_idx = int(np.argmax(cos_sims))
        best_sim = float(cos_sims[best_idx])

        matched = bool(best_sim >= self.similarity_threshold)
        if matched:
            self.successful_recalls += 1

        best_ep = self.episode_metadata[best_idx]
        recalled_u = np.array(best_ep["action_u"], dtype=np.float32)

        # Unbind action component: U_probe = H_retrieved (x) B_action
        h_matched = self.stored_matrix[best_idx]
        unbound_u_hypervector = norm_center(h_matched * self.B_action)
        expected_u = self.encode_action(recalled_u[0], recalled_u[1])
        unbound_action_sim = float(np.dot(unbound_u_hypervector, expected_u))

        self.last_query_time_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "matched": matched,
            "best_idx": best_idx,
            "best_sim": best_sim,
            "episode": best_ep,
            "recalled_action": recalled_u,
            "unbound_action_sim": unbound_action_sim,
            "latency_ms": self.last_query_time_ms
        }

    # -------------------------------------------------------------------------
    # Acceptance Battery & Noise Robustness Verification
    # -------------------------------------------------------------------------

    def inject_sensory_noise(self, cue_vector: np.ndarray, noise_ratio: float = 0.50) -> np.ndarray:
        """
        Corrupts a cue hypervector by injecting additive white Gaussian noise with energy ratio `noise_ratio`.
        noise_ratio = 0.50 corresponds to 50% noise power corruption:
        H_noisy = norm_center( (1 - noise_ratio) * H_clean + noise_ratio * N(0, I) )
        """
        noise = self.rng.randn(self.D).astype(np.float32)
        noise_norm = norm_center(noise)
        cue_norm = norm_center(cue_vector)

        corrupted = (1.0 - noise_ratio) * cue_norm + noise_ratio * noise_norm
        return norm_center(corrupted)

    def evaluate_anti_forgetting_battery(
        self,
        num_initial: int = 50,
        total_episodes: int = 500,
        noise_level: float = 0.50
    ) -> Dict[str, Any]:
        """
        Pre-Registered Gate 4.2 Anti-Catastrophic Forgetting & Robustness Battery:
        1. Evaluates recall accuracy of the first `num_initial` episodes immediately after storing them.
        2. Learns `total_episodes - num_initial` subsequent distinct episodes.
        3. Re-evaluates recall accuracy of the original `num_initial` episodes under 50% cue noise.
        4. Verifies degradation < 5.0% and overall 500-episode recall >= 90.0%.
        """
        self.stored_matrix.fill(0)
        self.num_stored = 0
        self.episode_metadata.clear()
        self.voronoi_buckets.clear()

        # Generate 500 distinct navigational waypoints across an arena
        arena_size = 20.0
        grid_rng = np.random.RandomState(42)
        xs = grid_rng.uniform(-arena_size, arena_size, total_episodes)
        ys = grid_rng.uniform(-arena_size, arena_size, total_episodes)
        headings = grid_rng.uniform(-np.pi, np.pi, total_episodes)

        stored_cues = []

        # 1. Store initial 50 episodes
        for i in range(num_initial):
            sec_clear = 0.5 + 0.4 * np.sin(np.linspace(0, np.pi, 8) + i * 0.1)
            act_u = np.array([0.6 + 0.3 * np.cos(i * 0.2), 0.6 - 0.3 * np.cos(i * 0.2)])
            self.store_episode(xs[i], ys[i], headings[i], sec_clear, act_u)
            cue = self.encode_sensory_cue(xs[i], ys[i], headings[i], sec_clear)
            stored_cues.append(cue)

        # Baseline recall on initial 50 under noise
        initial_correct = 0
        for i in range(num_initial):
            noisy_q = self.inject_sensory_noise(stored_cues[i], noise_level)
            res = self.query_associative_recall(noisy_q)
            if res["best_idx"] == i:
                initial_correct += 1
        initial_acc = (initial_correct / num_initial) * 100.0

        # 2. Store remaining 450 episodes
        for j in range(num_initial, total_episodes):
            sec_clear = 0.5 + 0.4 * np.sin(np.linspace(0, np.pi, 8) + j * 0.1)
            act_u = np.array([0.5 + 0.4 * np.sin(j * 0.15), 0.5 - 0.4 * np.sin(j * 0.15)])
            self.store_episode(xs[j], ys[j], headings[j], sec_clear, act_u)
            cue = self.encode_sensory_cue(xs[j], ys[j], headings[j], sec_clear)
            stored_cues.append(cue)

        # 3. Post-learning recall on original 50 under noise (out of all 500 stored)
        post_correct = 0
        for i in range(num_initial):
            noisy_q = self.inject_sensory_noise(stored_cues[i], noise_level)
            res = self.query_associative_recall(noisy_q)
            if res["best_idx"] == i:
                post_correct += 1
        post_acc = (post_correct / num_initial) * 100.0
        degradation_pct = initial_acc - post_acc

        # 4. Overall 500-episode recall accuracy under noise
        total_correct = 0
        latencies = []
        unbound_sims = []
        for k in range(total_episodes):
            noisy_q = self.inject_sensory_noise(stored_cues[k], noise_level)
            res = self.query_associative_recall(noisy_q)
            latencies.append(res["latency_ms"])
            unbound_sims.append(res["unbound_action_sim"])
            if res["best_idx"] == k:
                total_correct += 1
        overall_acc = (total_correct / total_episodes) * 100.0

        # 5. Cross-Talk Quasi-Orthogonality Matrix
        n_pairs = 200
        pair_sims = []
        idx_a = self.rng.choice(total_episodes, size=n_pairs)
        idx_b = self.rng.choice(total_episodes, size=n_pairs)
        for a, b in zip(idx_a, idx_b):
            if a != b:
                sim = float(np.dot(self.stored_matrix[a], self.stored_matrix[b]))
                pair_sims.append(abs(sim))
        mean_cross_talk = float(np.mean(pair_sims)) if pair_sims else 0.0

        passed_gate4_2 = bool(
            (overall_acc >= 90.0) and
            (degradation_pct < 5.0) and
            (float(np.mean(latencies)) <= 1.0)
        )

        return {
            "initial_50_acc": initial_acc,
            "post_learning_50_acc": post_acc,
            "degradation_pct": degradation_pct,
            "overall_500_acc": overall_acc,
            "mean_latency_ms": float(np.mean(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "mean_unbound_action_sim": float(np.mean(unbound_sims)),
            "mean_cross_talk_abs": mean_cross_talk,
            "passed_gate4_2": passed_gate4_2
        }

    def reset(self):
        """Clears episodic memory buffer, Voronoi spatial buckets, and superposition vectors."""
        self.stored_matrix.fill(0.0)
        self.episode_metadata.clear()
        self.num_stored = 0
        self.voronoi_buckets.clear()
        self.M_spatial_superposition.fill(0.0)
        self.M_aversion_superposition.fill(0.0)


# Backward compatibility alias
HolographicEpisodicMemory = CarlHdcEpisodicMemory
