"""
brain/carl_structural_plasticity.py — Stage 6.1 Autopoietic Structural Plasticity & Synaptogenesis Engine
Classification: Stage 6 Phase 6.1 Canonical Neuromorphic Developmental Organ

Theoretical Foundations:
1. Chklovskii, Mel & Svoboda (2004) — Cortical rewiring and information storage through synaptic turnover.
2. Holtmaat & Svoboda (2009) — Experience-dependent structural synaptic plasticity in the mammalian brain.
3. SpiNNaker Neuromorphic Systems (2018) — Structural Plasticity on Many-Core Neuromorphic Architectures.
4. Tononi & Cirelli (2003, 2014) — Synaptic Homeostasis Hypothesis (SHY): Sleep-dependent spine pruning.
5. Turrigiano (2011) — Homeostatic Synaptic Scaling preventing runaway metabolic proliferation.

Mathematical Formulation:
1. Dynamic Sparse Synaptic Graph:
   G_t = (V_t, E_t), with connectivity mask M_ij in {0, 1} and weight matrix W_ij in R.
2. Pairwise Co-activation Tracking:
   C_ij(t) = beta_sprout * C_ij(t - dt) + (1 - beta_sprout) * [x_pre_i(t) * y_post_j(t)]
3. Distress-Gated Synaptogenesis (Sprouting):
   If M_ij == 0 and C_ij(t) > theta_sprout and Distress(t) > theta_distress:
       M_ij <- 1, W_ij <- W_init
4. NREM SWR Sleep Spine Pruning (Apoptosis):
   U_ij(t) = beta_prune * U_ij(t - dt) + (1 - beta_prune) * |W_ij(t)|
   If M_ij == 1 and U_ij(t) < epsilon_prune during sleep:
       M_ij <- 0, W_ij <- 0.0
5. Global Metabolic Resource Ceiling:
   sum_ij M_ij <= K_max_edges
   ||W||_F <= W_frobenius_max
"""

import math
import time
from typing import Dict, Any, Optional, Tuple, List
import numpy as np


class CarlStructuralPlasticityEngine:
    """
    Stage 6.1 Structural Plasticity & Synaptogenesis Organ.
    Enables dynamic graph topology remodeling (synaptogenesis and spine pruning)
    over the striatal motor synergy and associative projection layers.
    """

    def __init__(
        self,
        pre_size: int = 32,
        post_size: int = 8,
        initial_density: float = 0.35,  # 35% sparse baseline connectivity
        dt: float = 0.0333,
        beta_sprout: float = 0.92,      # Co-activation moving average factor
        theta_sprout: float = 0.40,     # Co-activation threshold for synaptogenesis
        theta_distress: float = 0.30,   # Witness distress gate threshold
        w_init_sprout: float = 0.08,    # Initial nascent synaptic strength
        beta_prune: float = 0.95,       # Synaptic utilization persistence factor
        epsilon_prune: float = 0.015,   # Minimum utilization threshold for survival
        k_max_edges: int = 160,         # Maximum metabolic synaptic edge ceiling (32x8=256 max)
        w_min: float = -1.0,
        w_max: float = 1.0,
        w_frobenius_max: float = 15.0,
        seed: int = 42,
    ):
        self.pre_size = pre_size
        self.post_size = post_size
        self.dt = dt
        self.beta_sprout = beta_sprout
        self.theta_sprout = theta_sprout
        self.theta_distress = theta_distress
        self.w_init_sprout = w_init_sprout
        self.beta_prune = beta_prune
        self.epsilon_prune = epsilon_prune
        self.k_max_edges = k_max_edges
        self.w_min = w_min
        self.w_max = w_max
        self.w_frobenius_max = w_frobenius_max

        rng = np.random.RandomState(seed)

        # 1. Connectivity Mask M_ij in {0, 1}
        rand_prob = rng.rand(pre_size, post_size)
        self.M = (rand_prob < initial_density).astype(np.int32)
        # Ensure at least 1 connection per postsynaptic motor primitive
        for j in range(post_size):
            if np.sum(self.M[:, j]) == 0:
                self.M[rng.randint(0, pre_size), j] = 1

        # Enforce initial k_max_edges ceiling
        while np.sum(self.M) > self.k_max_edges:
            active_idx = np.argwhere(self.M == 1)
            pruned_init = False
            for idx in active_idx:
                if np.sum(self.M[:, idx[1]]) > 1:
                    self.M[idx[0], idx[1]] = 0
                    pruned_init = True
                    break
            if not pruned_init:
                break

        # 2. Continuous Synaptic Weight Matrix W_ij
        self.W = np.zeros((pre_size, post_size), dtype=np.float64)
        for i in range(pre_size):
            for j in range(post_size):
                if self.M[i, j] == 1:
                    self.W[i, j] = rng.uniform(0.05, 0.20)

        # 3. Dynamic Tracking State
        self.C_coact = np.zeros((pre_size, post_size), dtype=np.float64)  # Co-activation
        self.U_util = np.abs(self.W).copy()                              # Utilization history
        self.protected_engram_mask = np.zeros((pre_size, post_size), dtype=bool)

        # 4. Telemetry and Audit Records
        self.total_sprouted_edges = 0
        self.total_pruned_edges = 0
        self.sprout_history: List[Dict[str, Any]] = []
        self.prune_history: List[Dict[str, Any]] = []
        self.last_cycle_ms = 0.0

    @property
    def num_active_edges(self) -> int:
        return int(np.sum(self.M))

    @property
    def synaptic_density(self) -> float:
        return float(np.sum(self.M)) / float(self.pre_size * self.post_size)

    def mark_engram_protection(self, pre_idx: int, post_idx: int, protect: bool = True):
        """Flags critical associative connections as consolidated engrams immune to routine decay."""
        if 0 <= pre_idx < self.pre_size and 0 <= post_idx < self.post_size:
            self.protected_engram_mask[pre_idx, post_idx] = protect

    def forward_pass(self, x_pre: np.ndarray) -> np.ndarray:
        """
        Computes postsynaptic drive y = W^T * x using current active dynamic graph topology.
        Non-existent edges (M_ij == 0) transmit zero current.
        """
        effective_w = self.W * self.M
        return np.dot(effective_w.T, x_pre)

    def step_awake_plasticity(
        self,
        x_pre: np.ndarray,
        y_post: np.ndarray,
        distress_level: float = 0.0,
        reward_rpe: float = 0.0,
        eta: float = 0.020,
    ) -> Dict[str, Any]:
        """
        Executes one awake step of combined structural and functional plasticity:
        1. Updates co-activation correlation.
        2. Evaluates distress-gated synaptogenesis.
        3. Updates active synaptic weights via Three-Factor R-STDP.
        4. Updates long-term utilization metrics.
        """
        t0 = time.perf_counter()
        x_pre = np.asarray(x_pre, dtype=np.float64).flatten()
        y_post = np.asarray(y_post, dtype=np.float64).flatten()

        # Update Pairwise Co-activation Matrix
        outer_act = np.outer(x_pre, y_post)
        self.C_coact = self.beta_sprout * self.C_coact + (1.0 - self.beta_sprout) * outer_act

        # -------------------------------------------------------------
        # SYNAPTOGENESIS (Sprouting Nascent Connections)
        # -------------------------------------------------------------
        sprouted_this_step = 0
        if distress_level >= self.theta_distress:
            # Candidate vacant edges with high co-activation
            candidates = (self.M == 0) & (self.C_coact >= self.theta_sprout)
            cand_indices = np.argwhere(candidates)

            for idx in cand_indices:
                i, j = int(idx[0]), int(idx[1])
                # Check metabolic resource budget
                if self.num_active_edges >= self.k_max_edges:
                    # Competitive displacement: prune weakest unprotected active edge with redundancy
                    unprotected_active = (self.M == 1) & (~self.protected_engram_mask)
                    pruned = False
                    if np.any(unprotected_active):
                        util_vals = np.where(unprotected_active, self.U_util, np.inf)
                        sorted_flat = np.argsort(util_vals.flatten())
                        for flat_k in sorted_flat:
                            weak_i, weak_j = np.unravel_index(flat_k, self.U_util.shape)
                            if self.M[weak_i, weak_j] == 1 and not self.protected_engram_mask[weak_i, weak_j]:
                                if np.sum(self.M[:, weak_j]) > 1 or weak_j == j:
                                    self.M[weak_i, weak_j] = 0
                                    self.W[weak_i, weak_j] = 0.0
                                    self.total_pruned_edges += 1
                                    pruned = True
                                    break
                    if not pruned:
                        continue  # Cannot add without violating metabolic ceiling

                # Sprout new connection
                self.M[i, j] = 1
                self.W[i, j] = self.w_init_sprout
                self.U_util[i, j] = self.w_init_sprout
                self.total_sprouted_edges += 1
                sprouted_this_step += 1
                self.sprout_history.append({
                    "pre": i, "post": j,
                    "coact": float(self.C_coact[i, j]),
                    "distress": float(distress_level)
                })

        # -------------------------------------------------------------
        # FUNCTIONAL WEIGHT ADAPTATION (Three-Factor Hebbian on Active Edges)
        # -------------------------------------------------------------
        dW = eta * outer_act * reward_rpe * self.M
        self.W = np.clip(self.W + dW, self.w_min, self.w_max) * self.M

        # Enforce global Frobenius ceiling
        f_norm = np.linalg.norm(self.W)
        if f_norm > self.w_frobenius_max:
            self.W = (self.W / f_norm) * self.w_frobenius_max

        # Update utilization history
        self.U_util = self.beta_prune * self.U_util + (1.0 - self.beta_prune) * np.abs(self.W)

        self.last_cycle_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "sprouted_count": sprouted_this_step,
            "active_edges": self.num_active_edges,
            "density": self.synaptic_density,
            "frobenius_norm": float(np.linalg.norm(self.W)),
            "cycle_ms": self.last_cycle_ms
        }

    def consolidate_nrem_sleep_pruning(self) -> Dict[str, Any]:
        """
        Executes NREM Sleep Spine Pruning according to the Synaptic Homeostasis Hypothesis (SHY).
        Permanently eliminates underutilized, non-engram connections to minimize metabolic cost.
        """
        pruned_this_sleep = 0
        prunable = (self.M == 1) & (~self.protected_engram_mask) & (self.U_util < self.epsilon_prune)
        prune_indices = np.argwhere(prunable)

        for idx in prune_indices:
            i, j = int(idx[0]), int(idx[1])
            # Ensure we do not leave any postsynaptic motor primitive with 0 inputs
            if np.sum(self.M[:, j]) > 1:
                self.M[i, j] = 0
                self.W[i, j] = 0.0
                self.U_util[i, j] = 0.0
                self.total_pruned_edges += 1
                pruned_this_sleep += 1
                self.prune_history.append({
                    "pre": i, "post": j,
                    "final_util": float(self.U_util[i, j])
                })

        # Global homeostatic downscaling (10% synaptic downscaling)
        self.W *= 0.90

        return {
            "pruned_count": pruned_this_sleep,
            "remaining_edges": self.num_active_edges,
            "density": self.synaptic_density,
            "frobenius_norm": float(np.linalg.norm(self.W))
        }

    def get_topology_state(self) -> Dict[str, Any]:
        return {
            "pre_size": self.pre_size,
            "post_size": self.post_size,
            "active_edges": self.num_active_edges,
            "synaptic_density": self.synaptic_density,
            "total_sprouted": self.total_sprouted_edges,
            "total_pruned": self.total_pruned_edges,
            "frobenius_norm": float(np.linalg.norm(self.W)),
            "mask_sha256": hex(hash(self.M.tobytes()))
        }
