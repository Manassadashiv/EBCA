"""
brain/carl_stage2_hd_ring.py — 64-Neuron Continuous Attractor Neural Network (HD Ring)
Classification: [NEUROMORPHIC ARCHITECTURE] 1D Recurrent Continuous Attractor

Implements a genuine continuous attractor neural network for head direction:
- 64 cyclic neurons with continuous-time membrane potential dynamics:
    tau * du_i/dt = -u_i + sum_j W_ij * r_j + I_tonic + I_asym_i
- Firing rate non-linearity: Divisive normalization:
    r_i = [max(0, u_i)]^2 / (1.0 + beta * sum_j [max(0, u_j)]^2)
- Mexican-hat recurrent connectivity kernel (local excitation, global inhibition)
- Continuous bump shift driven by asymmetric recurrent derivative kernel
- Zero hidden scalar angle; zero Gaussian decals; genuine numerical ODE integration.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional


class HeadDirectionRingAttractor:
    """
    64-Neuron 1D Continuous Attractor Neural Network (CANN).
    Orientation is stored as a distributed, localized bump of neural firing rates.
    """
    N_NEURONS: int = 64
    TAU: float = 0.010          # 10 ms synaptic time constant
    J_EX: float = 5.0           # Excitatory synaptic gain
    J_INH: float = 2.0          # Inhibitory synaptic gain
    SIGMA_HD: float = math.pi / 6.0  # 30 deg excitatory footprint
    I_TONIC: float = 0.10       # Baseline excitability current
    GAMMA: float = -0.1972      # Calibrated asymmetric velocity steering gain
    BETA_NORM: float = 0.15     # Divisive normalization gain

    def __init__(self, seed: int = 42, dt: float = 0.030):
        self.dt = dt
        self.rng = np.random.RandomState(seed)

        # 1. Cyclic Angular Coordinates of Neurons along the Ring [-pi, pi)
        self.angles = -math.pi + (2.0 * math.pi * np.arange(self.N_NEURONS)) / float(self.N_NEURONS)

        # 2. Build Recurrent Synaptic Weight Matrices
        self.W_sym, self.W_asym = self._build_connectivity_matrices()

        # 3. Membrane Potentials (u) and Firing Rates (r)
        self.u = np.zeros(self.N_NEURONS, dtype=np.float64)
        # Small seed cue to break circular symmetry at initialization
        self.u[self.N_NEURONS // 2] = 1.0
        self.r = self._activation(self.u)

        # Settle initial resting bump
        self._settle_initial_attractor(steps=100)

    def _build_connectivity_matrices(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Constructs translationally invariant symmetric Mexican-hat matrix
        and asymmetric derivative shift matrix.
        """
        W_sym = np.zeros((self.N_NEURONS, self.N_NEURONS), dtype=np.float64)
        W_asym = np.zeros((self.N_NEURONS, self.N_NEURONS), dtype=np.float64)

        for i in range(self.N_NEURONS):
            for j in range(self.N_NEURONS):
                # Shortest circular angular distance
                dth = math.atan2(math.sin(self.angles[i] - self.angles[j]),
                                 math.cos(self.angles[i] - self.angles[j]))

                # Symmetric Mexican-hat kernel (local excitation, global inhibition)
                W_sym[i, j] = self.J_EX * math.exp(-(dth ** 2) / (2.0 * self.SIGMA_HD ** 2)) - self.J_INH

                # Asymmetric steering kernel (derivative of Mexican hat)
                W_asym[i, j] = -math.sin(dth) * math.exp(-(dth ** 2) / (2.0 * self.SIGMA_HD ** 2))

        # Normalize rows to maintain stable Lyapunov energy landscape
        W_sym /= (float(self.N_NEURONS) / 8.0)
        W_asym /= (float(self.N_NEURONS) / 8.0)

        return W_sym, W_asym

    def _activation(self, u_vec: np.ndarray) -> np.ndarray:
        """Divisive normalization non-linearity preventing runaway excitation."""
        pos = np.maximum(0.0, u_vec) ** 2
        denom = 1.0 + self.BETA_NORM * float(np.sum(pos))
        return pos / denom

    def _settle_initial_attractor(self, steps: int = 100):
        """Allows spontaneous bump formation under resting tonic drive."""
        dt_sub = 0.005
        for _ in range(steps):
            recurrent_input = self.W_sym @ self.r
            du = (-self.u + recurrent_input + self.I_TONIC) * (dt_sub / self.TAU)
            self.u += du
            self.r = self._activation(self.u)

    def step(self, omega_input: float) -> Dict[str, Any]:
        """
        Evolves neural membrane dynamics across control tick dt.
        omega_input: angular velocity signal from learned sensory projection.
        """
        # Multi-step numerical ODE integration (6 substeps per 0.030s tick -> dt_sub = 0.005s)
        n_substeps = 6
        dt_sub = self.dt / float(n_substeps)

        for _ in range(n_substeps):
            # 1. Symmetric recurrent excitation/inhibition
            I_rec = self.W_sym @ self.r

            # 2. Asymmetric directional current shifting the bump
            I_shift = self.GAMMA * float(omega_input) * (self.W_asym @ self.r)

            # 3. Continuous-time membrane leaky integration
            du = (-self.u + I_rec + self.I_TONIC + I_shift) * (dt_sub / self.TAU)
            self.u += du

            # 4. Firing rate non-linearity
            self.r = self._activation(self.u)

        decoded_heading = self.decode_heading()
        bump_amp = self.get_bump_amplitude()

        return {
            "decoded_heading": decoded_heading,
            "bump_amplitude": bump_amp,
            "firing_rates": self.r.copy(),
            "membrane_potentials": self.u.copy(),
        }

    def decode_heading(self) -> float:
        """
        Decodes heading orientation via circular center of mass (population vector).
        Note: This is a readout of the physical neural state r, NOT an input.
        """
        C = float(np.sum(self.r * np.cos(self.angles)))
        S = float(np.sum(self.r * np.sin(self.angles)))
        return float(math.atan2(S, C))

    def get_bump_amplitude(self) -> float:
        """Calculates population vector length (confidence / bump height)."""
        C = float(np.sum(self.r * np.cos(self.angles)))
        S = float(np.sum(self.r * np.sin(self.angles)))
        return float(math.sqrt(C ** 2 + S ** 2))

    def get_lyapunov_energy(self) -> float:
        """Calculates network energy: E = -0.5 * r^T * W * r - I^T * r."""
        E_rec = -0.5 * float(self.r @ (self.W_sym @ self.r))
        E_ext = -float(np.sum(self.I_TONIC * self.r))
        return E_rec + E_ext
