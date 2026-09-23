"""
brain/carl_stage1_reservoir.py — Canonical 1026-Neuron Liquid State Machine (LSM)
Classification: [SCIENTIFIC HYPOTHESIS] 1026-Neuron Reservoir Criticality & Capacity Target

Implements the 1026-neuron recurrent echo-state substrate with continuous intrinsic plasticity:
- N = 1026 state neurons (95.6% asymptotic memory capacity knee)
- Spectral radius initialization: rho(W_res) = 0.98, sparsity = 0.10
- Local continuous intrinsic plasticity: g_t dynamically adapts neural gain without external supervision
- Zero-copy view into S_unified[25:1051]
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any


class CarlStage1Reservoir:
    """
    1026-Neuron LSM Recurrent Reservoir with Continuous Homeostatic Intrinsic Plasticity.
    """
    # [SCIENTIFIC HYPOTHESIS] 1026-neuron scaling target
    N_NEURONS: int = 1026
    SENSORY_DIM: int = 25
    MOTOR_DIM: int = 6

    # [NUMERICAL / CONSTANT] Reservoir hyper-parameters
    SPECTRAL_RADIUS: float = 0.98
    SPARSITY: float = 0.10
    LEAK_RATE: float = 0.30  # alpha in [0, 1]
    SIGMA_IN: float = 0.15
    SIGMA_MOTOR: float = 0.15
    
    # [ARCHITECTURAL INVARIANT] Local Intrinsic Plasticity parameters
    TARGET_ACTIVITY: float = 0.15  # a_target
    ETA_GAIN: float = 1e-5         # gain adaptation rate

    def __init__(self, seed: int = 42, s_unified_view: Optional[np.ndarray] = None):
        """
        Initializes 1026-neuron recurrent weight matrices with controlled spectral radius.
        """
        self.seed = seed
        self.rng = np.random.RandomState(seed)

        # 1. Sensory Input Weight Matrix (1026 x 25)
        self.W_in = self.rng.randn(self.N_NEURONS, self.SENSORY_DIM) * self.SIGMA_IN

        # 2. Motor Input Weight Matrix (1026 x 6)
        self.W_motor = self.rng.randn(self.N_NEURONS, self.MOTOR_DIM) * self.SIGMA_MOTOR

        # 3. Recurrent Weight Matrix (1026 x 1026) with Spectral Scaling
        W_raw = self.rng.randn(self.N_NEURONS, self.N_NEURONS)
        mask = (self.rng.rand(self.N_NEURONS, self.N_NEURONS) < self.SPARSITY).astype(float)
        W_raw *= mask

        # Scale to target spectral radius rho = 0.98
        eigenvalues = np.linalg.eigvals(W_raw)
        current_radius = float(np.max(np.abs(eigenvalues)))
        if current_radius > 0:
            self.W_res = W_raw * (self.SPECTRAL_RADIUS / current_radius)
        else:
            self.W_res = W_raw
        
        self.actual_spectral_radius = float(np.max(np.abs(np.linalg.eigvals(self.W_res))))

        # 4. State vector x(t) ∈ R^1026
        if s_unified_view is not None:
            assert s_unified_view.shape == (self.N_NEURONS,), f"View must have shape ({self.N_NEURONS},)"
            self.x = s_unified_view
        else:
            self.x = np.zeros(self.N_NEURONS, dtype=np.float64)

        # 5. Intrinsic Gain and Bias State
        self.gain: float = 1.0
        self.bias = np.zeros(self.N_NEURONS, dtype=np.float64)
        
        # 6. Empirical Diagnostics
        self.step_count: int = 0
        self.last_norm: float = 0.0

    def reset(self):
        """Resets dynamic activations to zero while preserving fixed connectivity matrices."""
        self.x.fill(0.0)
        self.gain = 1.0
        self.bias.fill(0.0)
        self.step_count = 0
        self.last_norm = 0.0

    def step(self, s: np.ndarray, u: np.ndarray) -> np.ndarray:
        """
        Updates reservoir state via continuous leaky integrator dynamics:
        x(t+1) = (1 - alpha)*x(t) + alpha * tanh( g_t * (W_res x(t) + W_in s(t) + W_motor u(t)) + b_t )
        """
        assert len(s) == self.SENSORY_DIM, f"s must be {self.SENSORY_DIM}-D"
        assert len(u) == self.MOTOR_DIM, f"u must be {self.MOTOR_DIM}-D"

        # Linear pre-activation
        pre_act = (self.W_res @ self.x) + (self.W_in @ s) + (self.W_motor @ u)
        
        # Gain-modulated non-linear activation
        act = np.tanh(self.gain * pre_act + self.bias)

        # Leaky integration update
        self.x[:] = (1.0 - self.LEAK_RATE) * self.x + self.LEAK_RATE * act

        # [ARCHITECTURAL INVARIANT] Local Continuous Intrinsic Plasticity
        mean_activity = float(np.mean(np.abs(self.x)))
        self.gain += self.ETA_GAIN * (self.TARGET_ACTIVITY - mean_activity)
        self.gain = float(np.clip(self.gain, 0.1, 5.0))

        self.step_count += 1
        self.last_norm = float(np.linalg.norm(self.x))

        return self.x

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns neural state diagnostics for stability and capacity verification."""
        norm_val = float(np.linalg.norm(self.x))
        # Participation Ratio: PR = (sum x_i^2)^2 / sum x_i^4
        x_sq = self.x ** 2
        sum_sq = float(np.sum(x_sq))
        sum_quad = float(np.sum(self.x ** 4))
        participation_ratio = (sum_sq ** 2) / max(1e-12, sum_quad)

        return {
            "step_count": self.step_count,
            "spectral_radius": self.actual_spectral_radius,
            "state_norm": norm_val,
            "mean_activity": float(np.mean(np.abs(self.x))),
            "intrinsic_gain": self.gain,
            "participation_ratio": participation_ratio,
        }
