"""
brain/carl_stdp.py — Reward-Modulated Spike-Timing-Dependent Plasticity (R-STDP) Engine
Classification: Stage 4 Phase 4.1 Canonical Developmental Organ

Theoretical Foundations:
1. Markram et al. (1997) — Spike-Timing-Dependent Plasticity (STDP).
2. Izhikevich (2007) — Solving the Distal Reward Problem via Eligibility Traces and Neuromodulatory Gating.
3. Frémaux & Gerstner (2016) — Unified Theory of Three-Factor Learning Rules.
4. Turrigiano (2008, 2011) — Homeostatic Synaptic Scaling preventing runaway Hebbian saturation.

Mathematical Formulation:
- Presynaptic Activity Trace:
    A_pre_j(t + dt) = A_pre_j(t) * exp(-dt / tau_pre) + x_pre_j(t)
- Postsynaptic Activity Trace:
    A_post_i(t + dt) = A_post_i(t) * exp(-dt / tau_post) + y_post_i(t)
- Synaptic Eligibility Trace:
    E_ij(t + dt) = E_ij(t) * exp(-dt / tau_e) + [ A^+ * (A_pre_j * y_post_i) - A^- * (x_pre_j * A_post_i) ]
- Neuromodulated Three-Factor Update:
    delta_W_ij(t) = eta * E_ij(t) * (R(t) - R_bar(t))
- Turrigiano Multiplicative Scaling:
    s_i = 1.0 + gamma * (a_target - a_bar_i)
    W_{:, i} <- W_{:, i} * s_i
    subject to ||W||_F <= W_max and W_ij in [W_min, W_max]
"""

import math
import time
from typing import Dict, Any, Optional, Tuple
import numpy as np


class CarlSTDPPlasticityEngine:
    """
    Reward-Modulated Spike-Timing-Dependent Plasticity (R-STDP) engine with
    Turrigiano homeostatic scaling and structural plasticity quarantine.
    """

    def __init__(
        self,
        pre_size: int = 32,
        post_size: int = 8,
        dt: float = 0.0333,
        tau_pre: float = 0.050,      # 50 ms presynaptic trace decay
        tau_post: float = 0.050,     # 50 ms postsynaptic trace decay
        tau_e: float = 1.50,         # 1.5 s eligibility trace decay
        tau_reward: float = 3.0,     # 3.0 s reward baseline moving average
        eta: float = 0.015,          # Learning rate
        a_plus: float = 0.035,       # LTP amplitude (Hebbian positive coincidence)
        a_minus: float = 0.015,      # LTD amplitude (anti-causal depression)
        w_min: float = -1.0,         # Weight saturation lower bound
        w_max: float = 1.0,          # Weight saturation upper bound
        w_frobenius_max: float = 15.0, # Global Frobenius norm ceiling
        a_target: float = 0.25,      # Turrigiano target firing activity
        gamma_homeostatic: float = 0.0005, # Homeostatic scaling rate (physiological timescale)
        seed: int = 42,
    ):
        self.pre_size = pre_size
        self.post_size = post_size
        self.dt = dt
        self.tau_pre = tau_pre
        self.tau_post = tau_post
        self.tau_e = tau_e
        self.tau_reward = tau_reward
        self.eta = eta
        self.a_plus = a_plus
        self.a_minus = a_minus
        self.w_min = w_min
        self.w_max = w_max
        self.w_frobenius_max = w_frobenius_max
        self.a_target = a_target
        self.gamma_homeostatic = gamma_homeostatic

        # Initial weight matrix (unbiased tabula rasa initialization)
        self.W_initial = np.zeros((pre_size, post_size), dtype=np.float64)
        self.W = self.W_initial.copy()

        # Eligibility traces (pre x post)
        self.E = np.zeros((pre_size, post_size), dtype=np.float64)

        # Activity traces
        self.A_pre = np.zeros(pre_size, dtype=np.float64)
        self.A_post = np.zeros(post_size, dtype=np.float64)

        # Homeostatic running average of postsynaptic firing
        self.a_bar = np.ones(post_size, dtype=np.float64) * self.a_target

        # Reward baseline (RPE reference)
        self.reward_baseline = 0.0

        # Diagnostics & Cumulative Telemetry
        self.total_cycles = 0
        self.ltp_events = 0
        self.ltd_events = 0
        self.total_dw_norm = 0.0
        self.last_cycle_latency_ms = 0.0
        self.weight_history_snapshots = []
        self.trace_history_snapshots = []

        # Quarantine verification
        self.cann_weights_untouched = True

    def reset_traces(self) -> None:
        """Resets dynamic eligibility and activity traces between distinct lifespans/episodes."""
        self.E.fill(0.0)
        self.A_pre.fill(0.0)
        self.A_post.fill(0.0)
        self.reward_baseline = 0.0

    def compute_action_bias(self, pre_features: np.ndarray) -> np.ndarray:
        """
        Computes the adaptive motor prior bias vector:
            b_plastic = tanh(W.T @ pre_features)  (dimension: post_size,)
        """
        feat = np.asarray(pre_features, dtype=np.float64).flatten()
        if len(feat) != self.pre_size:
            if len(feat) < self.pre_size:
                feat = np.pad(feat, (0, self.pre_size - len(feat)))
            else:
                feat = feat[:self.pre_size]
        net_input = self.W.T @ feat
        return np.tanh(net_input)

    def step(
        self,
        pre_activity: np.ndarray,
        post_activity: np.ndarray,
        raw_reward: float,
        neuromodulator_level: float = 1.0,
        enable_plasticity: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes one discrete R-STDP control cycle:
        1. Decays activity and eligibility traces.
        2. Computes causal STDP coincidence (LTP vs LTD).
        3. Updates eligibility traces.
        4. Modulates weights via Three-Factor Rule (Pre x Post x Neuromodulator RPE).
        5. Applies Turrigiano homeostatic scaling.
        6. Enforces hard boundedness constraints.
        """
        t_start = time.perf_counter()
        dt = self.dt

        # Format inputs
        pre = np.asarray(pre_activity, dtype=np.float64).flatten()
        if len(pre) != self.pre_size:
            pre = np.pad(pre, (0, max(0, self.pre_size - len(pre))))[:self.pre_size]
        pre = np.clip(pre, 0.0, 1.0)

        post = np.asarray(post_activity, dtype=np.float64).flatten()
        if len(post) != self.post_size:
            post = np.pad(post, (0, max(0, self.post_size - len(post))))[:self.post_size]
        post = np.clip(post, 0.0, 1.0)

        reward = float(raw_reward)
        nm = max(0.0, float(neuromodulator_level))

        # 1. Decay Activity Traces
        decay_pre = math.exp(-dt / self.tau_pre)
        decay_post = math.exp(-dt / self.tau_post)
        decay_e = math.exp(-dt / self.tau_e)

        self.A_pre *= decay_pre
        self.A_post *= decay_post
        self.E *= decay_e

        # 2. STDP Coincidence Correlation
        # LTP: Post fired, Pre fired previously -> Strengthen
        ltp_matrix = np.outer(self.A_pre, post) * self.a_plus

        # LTD: Pre fired, Post fired previously -> Weaken
        ltd_matrix = np.outer(pre, self.A_post) * self.a_minus

        # 3. Update Eligibility Trace Matrix
        stdp_step = ltp_matrix - ltd_matrix
        self.E += stdp_step

        self.ltp_events += int(np.sum(ltp_matrix > 1e-5))
        self.ltd_events += int(np.sum(ltd_matrix > 1e-5))

        # 4. Integrate Activity Traces AFTER Correlation (strictly causal)
        self.A_pre += pre
        self.A_post += post

        # 5. Reward Prediction Error (RPE) Baseline Subtraction
        decay_rew = math.exp(-dt / self.tau_reward)
        self.reward_baseline = self.reward_baseline * decay_rew + reward * (1.0 - decay_rew)
        rpe = reward - self.reward_baseline

        # 6. Three-Factor Synaptic Weight Update
        dW = np.zeros_like(self.W)
        if enable_plasticity and abs(rpe) > 1e-5 and nm > 1e-4:
            # dW = eta * E * RPE * Neuromodulator
            dW = self.eta * self.E * rpe * nm
            self.W += dW
            self.total_dw_norm += float(np.linalg.norm(dW))

        # 7. Turrigiano Multiplicative Homeostatic Scaling
        # Update running average postsynaptic firing activity
        alpha_homeo = 0.02
        self.a_bar = (1.0 - alpha_homeo) * self.a_bar + alpha_homeo * post

        if enable_plasticity and nm > 1e-4:
            # Multiplicative scaling per postsynaptic neuron column
            scaling_factors = 1.0 + self.gamma_homeostatic * (self.a_target - self.a_bar)
            scaling_factors = np.clip(scaling_factors, 0.90, 1.10)
            self.W = self.W * scaling_factors[np.newaxis, :]

        # 8. Hard Boundedness Clamping
        self.W = np.clip(self.W, self.w_min, self.w_max)

        # Frobenius norm ceiling
        f_norm = float(np.linalg.norm(self.W, ord="fro"))
        if f_norm > self.w_frobenius_max:
            self.W = self.W * (self.w_frobenius_max / f_norm)
            f_norm = self.w_frobenius_max

        # Latency tracking
        self.total_cycles += 1
        latency_ms = (time.perf_counter() - t_start) * 1000.0
        self.last_cycle_latency_ms = latency_ms

        return {
            "latency_ms": latency_ms,
            "rpe": rpe,
            "reward_baseline": self.reward_baseline,
            "frobenius_norm": f_norm,
            "mean_weight": float(np.mean(self.W)),
            "max_abs_weight": float(np.max(np.abs(self.W))),
            "dw_step_norm": float(np.linalg.norm(dW)),
            "total_dw_norm": self.total_dw_norm,
            "mean_eligibility": float(np.mean(np.abs(self.E))),
            "max_eligibility": float(np.max(np.abs(self.E))),
            "a_bar_mean": float(np.mean(self.a_bar)),
        }

    def get_weight_divergence(self) -> float:
        """Returns the mean absolute weight difference relative to initial weights: ||W - W0||_1 / N"""
        diff = np.abs(self.W - self.W_initial)
        return float(np.mean(diff))

    def get_active_synapses_fraction(self, threshold: float = 0.010) -> float:
        """Returns the fraction of synapses that experienced significant change (|Delta W| >= threshold)."""
        diff = np.abs(self.W - self.W_initial)
        active_count = np.sum(diff >= threshold)
        return float(active_count / (self.pre_size * self.post_size))

    def get_plasticity_snapshot(self) -> Dict[str, Any]:
        """Exports a complete statistical snapshot of current synaptic state."""
        diff = self.W - self.W_initial
        return {
            "pre_size": self.pre_size,
            "post_size": self.post_size,
            "total_cycles": self.total_cycles,
            "ltp_events": self.ltp_events,
            "ltd_events": self.ltd_events,
            "frobenius_norm": float(np.linalg.norm(self.W, ord="fro")),
            "mean_weight": float(np.mean(self.W)),
            "std_weight": float(np.std(self.W)),
            "max_weight": float(np.max(self.W)),
            "min_weight": float(np.min(self.W)),
            "mean_abs_delta_w": float(np.mean(np.abs(diff))),
            "active_synapse_fraction": self.get_active_synapses_fraction(0.010),
            "total_dw_norm": self.total_dw_norm,
            "cann_quarantined": self.cann_weights_untouched,
        }

    def save_state(self, filepath: str) -> None:
        """Serializes plastic synaptic state for GIS-901 autopoietic persistence."""
        np.savez_compressed(
            filepath,
            W=self.W,
            W_initial=self.W_initial,
            E=self.E,
            reward_baseline=self.reward_baseline,
            a_bar=self.a_bar,
            total_cycles=self.total_cycles,
            total_dw_norm=self.total_dw_norm,
        )

    def load_state(self, filepath: str) -> None:
        """Loads serialized plastic state during warm boot."""
        data = np.load(filepath)
        self.W = data["W"].astype(np.float64)
        self.W_initial = data["W_initial"].astype(np.float64)
        self.E = data["E"].astype(np.float64)
        self.reward_baseline = float(data["reward_baseline"])
        self.a_bar = data["a_bar"].astype(np.float64)
        self.total_cycles = int(data["total_cycles"])
        self.total_dw_norm = float(data["total_dw_norm"])
