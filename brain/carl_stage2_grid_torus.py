"""
brain/carl_stage2_grid_torus.py — 1,024-Neuron 2D Toroidal Continuous Attractor (Grid Sheet)
Classification: [NEUROMORPHIC ARCHITECTURE] 2D Toroidal Recurrent Continuous Attractor

Implements a genuine 2D continuous attractor neural network on a 2-torus T^2:
- 32 x 32 = 1,024 neurons arranged on a periodic 2D lattice.
- Membrane dynamics: tau * du_{ij}/dt = -u_{ij} + (W_sym * r)_{ij} + I_tonic + I_trans_{ij}
- Firing rate non-linearity: Divisive normalization across the 2D sheet:
    r_{ij} = [max(0, u_{ij})]^2 / (1.0 + beta * sum_{kl} [max(0, u_{kl})]^2)
- Recurrent connectivity: 2D Mexican-hat kernel convolved via 2D Fast Fourier Transform.
- Translational velocity injection: shifts 2D activity bump across the torus.
- Continuous phase readout via 2D circular population vector.
- Zero hidden classical (x, y) coordinates; genuine recurrent neural field integration.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional


class ToroidalGridCellAttractor:
    """
    1,024-Neuron (32x32) 2D Toroidal Continuous Attractor Neural Network.
    Spatial position is represented as the phase of a localized 2D neural activity bump.
    """
    GRID_N: int = 32             # 32 x 32 = 1,024 neurons
    TAU: float = 0.010           # 10 ms synaptic time constant
    J_EX: float = 6.0            # 2D Excitatory synaptic gain
    J_INH: float = 1.8           # 2D Inhibitory synaptic gain
    SIGMA_GRID: float = 3.0      # Spatial width of local excitation
    I_TONIC: float = 0.10        # Baseline excitability current
    BETA_NORM: float = 0.05      # Divisive normalization constant
    GRID_SCALE_METERS: float = 0.80  # Physical distance per torus wrap (periodicity scale)

    def __init__(self, seed: int = 42, dt: float = 0.030, scale_meters: float = 0.80):
        self.dt = dt
        self.GRID_SCALE_METERS = float(scale_meters)
        self.rng = np.random.RandomState(seed)

        # 1. 2D Coordinate Lattices
        self.X, self.Y = np.meshgrid(np.arange(self.GRID_N), np.arange(self.GRID_N), indexing='ij')

        # 2. Precompute Symmetric and Directional Shift Convolution Kernels
        self.F_W_sym, self.F_W_x, self.F_W_y = self._build_spectral_kernels()

        # 3. Membrane Potentials (u) and Firing Rates (r)
        self.u = np.zeros((self.GRID_N, self.GRID_N), dtype=np.float64)
        # Small seed cue at torus center to break spatial symmetry at birth
        self.u[self.GRID_N // 2, self.GRID_N // 2] = 2.0
        self.r = self._activation(self.u)

        # Settle resting 2D attractor bump
        self._settle_initial_attractor(steps=50)

        # Phase unwrapping accumulators (tracks integer wraps across torus)
        self.prev_phase_x = self._readout_phase_x()
        self.prev_phase_y = self._readout_phase_y()
        self.wrap_count_x = 0
        self.wrap_count_y = 0

    def _build_spectral_kernels(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Constructs 2D translationally invariant kernels on the 2-torus
        and precomputes their real-space 2D FFT transforms.
        """
        # Toroidal shortest distance from origin (0, 0)
        dx = np.minimum(np.abs(self.X), self.GRID_N - np.abs(self.X))
        dy = np.minimum(np.abs(self.Y), self.GRID_N - np.abs(self.Y))
        D = np.sqrt(dx ** 2 + dy ** 2)

        # Symmetric 2D Mexican-hat kernel
        W_sym = self.J_EX * np.exp(-(D ** 2) / (2.0 * self.SIGMA_GRID ** 2)) - self.J_INH

        # Directional gradient shift kernels
        dx_circ = np.sin(2.0 * math.pi * self.X / float(self.GRID_N)) * (self.GRID_N / (2.0 * math.pi))
        dy_circ = np.sin(2.0 * math.pi * self.Y / float(self.GRID_N)) * (self.GRID_N / (2.0 * math.pi))

        W_asym_x = -(dx_circ / (self.SIGMA_GRID ** 2)) * np.exp(-(D ** 2) / (2.0 * self.SIGMA_GRID ** 2))
        W_asym_y = -(dy_circ / (self.SIGMA_GRID ** 2)) * np.exp(-(D ** 2) / (2.0 * self.SIGMA_GRID ** 2))

        # FFTs
        F_W_sym = np.fft.rfft2(W_sym)
        F_W_x = np.fft.rfft2(W_asym_x)
        F_W_y = np.fft.rfft2(W_asym_y)

        return F_W_sym, F_W_x, F_W_y

    def _activation(self, u_mat: np.ndarray) -> np.ndarray:
        """2D Divisive normalization non-linearity."""
        pos = np.maximum(0.0, u_mat) ** 2
        denom = 1.0 + self.BETA_NORM * float(np.sum(pos))
        return pos / denom

    def _settle_initial_attractor(self, steps: int = 50):
        """Allows spontaneous 2D bump formation under resting drive."""
        dt_sub = 0.005
        for _ in range(steps):
            F_r = np.fft.rfft2(self.r)
            I_rec = np.fft.irfft2(self.F_W_sym * F_r, s=(self.GRID_N, self.GRID_N))
            du = (-self.u + I_rec + self.I_TONIC) * (dt_sub / self.TAU)
            self.u += du
            self.r = self._activation(self.u)

    def _readout_phase_x(self) -> float:
        """Decodes raw periodic phase along X axis [-pi, pi)."""
        angle_x = 2.0 * math.pi * self.X / float(self.GRID_N)
        C = float(np.sum(self.r * np.cos(angle_x)))
        S = float(np.sum(self.r * np.sin(angle_x)))
        return float(math.atan2(S, C))

    def _readout_phase_y(self) -> float:
        """Decodes raw periodic phase along Y axis [-pi, pi)."""
        angle_y = 2.0 * math.pi * self.Y / float(self.GRID_N)
        C = float(np.sum(self.r * np.cos(angle_y)))
        S = float(np.sum(self.r * np.sin(angle_y)))
        return float(math.atan2(S, C))

    def step(self, vx_input: float, vy_input: float, slip_gated: bool = False) -> Dict[str, Any]:
        """
        Evolves 2D neural membrane dynamics across control tick dt.
        vx_input, vy_input: directional translation velocity from grounded body signals.
        slip_gated: if True (wheel spinout on ice), velocity injection is suppressed.
        """
        n_substeps = 6
        dt_sub = self.dt / float(n_substeps)

        # Scale velocity to torus phase displacement (scaled inversely to spatial period)
        gain_trans = (-2.584 * (0.80 / self.GRID_SCALE_METERS)) if not slip_gated else 0.0

        for _ in range(n_substeps):
            F_r = np.fft.rfft2(self.r)

            # 1. Symmetric recurrent excitation & surround inhibition (via 2D FFT)
            I_rec = np.fft.irfft2(self.F_W_sym * F_r, s=(self.GRID_N, self.GRID_N))

            # 2. Directional velocity shift currents
            I_x = np.fft.irfft2(self.F_W_x * F_r, s=(self.GRID_N, self.GRID_N))
            I_y = np.fft.irfft2(self.F_W_y * F_r, s=(self.GRID_N, self.GRID_N))
            I_trans = gain_trans * (float(vx_input) * I_x + float(vy_input) * I_y)

            # 3. Continuous leaky integration
            du = (-self.u + I_rec + self.I_TONIC + I_trans) * (dt_sub / self.TAU)
            self.u += du

            # 4. Divisive normalization firing rate
            self.r = self._activation(self.u)

        # Update unwrapped spatial phase
        cur_ph_x = self._readout_phase_x()
        cur_ph_y = self._readout_phase_y()

        # Wrap detection
        d_ph_x = cur_ph_x - self.prev_phase_x
        d_ph_y = cur_ph_y - self.prev_phase_y
        if d_ph_x > math.pi:
            self.wrap_count_x -= 1
        elif d_ph_x < -math.pi:
            self.wrap_count_x += 1

        if d_ph_y > math.pi:
            self.wrap_count_y -= 1
        elif d_ph_y < -math.pi:
            self.wrap_count_y += 1

        self.prev_phase_x = cur_ph_x
        self.prev_phase_y = cur_ph_y

        unwrapped_x = (cur_ph_x + 2.0 * math.pi * self.wrap_count_x) / (2.0 * math.pi) * self.GRID_SCALE_METERS
        unwrapped_y = (cur_ph_y + 2.0 * math.pi * self.wrap_count_y) / (2.0 * math.pi) * self.GRID_SCALE_METERS

        return {
            "unwrapped_x_meters": float(unwrapped_x),
            "unwrapped_y_meters": float(unwrapped_y),
            "raw_phase_x": cur_ph_x,
            "raw_phase_y": cur_ph_y,
            "peak_firing_rate": float(np.max(self.r)),
            "bump_energy": float(-0.5 * np.sum(self.r * I_rec)),
        }


def disambiguate_coprime_phases(
    phi1: float,
    phi2: float,
    lambda1: float = 0.80,
    lambda2: float = 1.15,
    max_range: float = 9.0
) -> Tuple[float, float]:
    """
    Biological Chinese Remainder Theorem / phase intersection on coprime spatial scales:
    Finds the unique continuous coordinate x in [-max_range, max_range]
    from two periodic phases (phi1, phi2) with coprime spatial periods (lambda1, lambda2).
    Exact common period: 23 * 0.80 = 16 * 1.15 = 18.40m.
    """
    k1_min = int(np.floor(-max_range / lambda1)) - 1
    k1_max = int(np.ceil(max_range / lambda1)) + 1
    k2_min = int(np.floor(-max_range / lambda2)) - 1
    k2_max = int(np.ceil(max_range / lambda2)) + 1

    best_dist = 1e9
    best_x = 0.0

    for k1 in range(k1_min, k1_max + 1):
        x1 = (phi1 / (2.0 * math.pi) + k1) * lambda1
        if abs(x1) > max_range + 0.5:
            continue
        for k2 in range(k2_min, k2_max + 1):
            x2 = (phi2 / (2.0 * math.pi) + k2) * lambda2
            diff = abs(x1 - x2)
            if diff < best_dist:
                best_dist = diff
                best_x = 0.5 * (x1 + x2)

    return float(best_x), float(best_dist)


class MultiScaleGridToroid:
    """
    Candidate A: Multi-Scale Coprime Toroidal Grid Continuous Attractor.
    Module 1: 32x32 = 1,024 neurons, lambda_1 = 0.80m
    Module 2: 32x32 = 1,024 neurons, lambda_2 = 1.15m
    Total Neurons: 2,048 biological units.
    Exact Common Period: 18.40 meters (zero ghost origins within 9.2m radius).
    """
    TOTAL_NEURONS: int = 2048

    def __init__(self, seed: int = 42, dt: float = 0.030, lambda1: float = 0.80, lambda2: float = 1.15):
        self.lambda1 = float(lambda1)
        self.lambda2 = float(lambda2)
        self.common_period = 18.40  # 23 * 0.80 = 16 * 1.15 = 18.40m

        self.mod1 = ToroidalGridCellAttractor(seed=seed, dt=dt, scale_meters=lambda1)
        self.mod2 = ToroidalGridCellAttractor(seed=seed + 1000, dt=dt, scale_meters=lambda2)

        # Birthplace phase pairs
        self.birth_phi1_x = self.mod1.prev_phase_x
        self.birth_phi1_y = self.mod1.prev_phase_y
        self.birth_phi2_x = self.mod2.prev_phase_x
        self.birth_phi2_y = self.mod2.prev_phase_y

    def reset_at_birthplace(self):
        """Stores origin phase pair at birth."""
        self.mod1.prev_phase_x = self.mod1._readout_phase_x()
        self.mod1.prev_phase_y = self.mod1._readout_phase_y()
        self.mod1.wrap_count_x = 0
        self.mod1.wrap_count_y = 0

        self.mod2.prev_phase_x = self.mod2._readout_phase_x()
        self.mod2.prev_phase_y = self.mod2._readout_phase_y()
        self.mod2.wrap_count_x = 0
        self.mod2.wrap_count_y = 0

        self.birth_phi1_x = self.mod1.prev_phase_x
        self.birth_phi1_y = self.mod1.prev_phase_y
        self.birth_phi2_x = self.mod2.prev_phase_x
        self.birth_phi2_y = self.mod2.prev_phase_y

    def step(self, vx_input: float, vy_input: float, slip_gated: bool = False) -> Dict[str, Any]:
        """Steps both continuous neural sheets simultaneously."""
        res1 = self.mod1.step(vx_input, vy_input, slip_gated)
        res2 = self.mod2.step(vx_input, vy_input, slip_gated)

        # Compute relative phase displacement from birthplace on both tori
        dphi1_x = math.atan2(math.sin(self.mod1.prev_phase_x - self.birth_phi1_x),
                             math.cos(self.mod1.prev_phase_x - self.birth_phi1_x))
        dphi1_y = math.atan2(math.sin(self.mod1.prev_phase_y - self.birth_phi1_y),
                             math.cos(self.mod1.prev_phase_y - self.birth_phi1_y))

        dphi2_x = math.atan2(math.sin(self.mod2.prev_phase_x - self.birth_phi2_x),
                             math.cos(self.mod2.prev_phase_x - self.birth_phi2_x))
        dphi2_y = math.atan2(math.sin(self.mod2.prev_phase_y - self.birth_phi2_y),
                             math.cos(self.mod2.prev_phase_y - self.birth_phi2_y))

        # Disambiguate global displacement from joint coprime phase pair
        disp_x, res_x = disambiguate_coprime_phases(dphi1_x, dphi2_x, self.lambda1, self.lambda2)
        disp_y, res_y = disambiguate_coprime_phases(dphi1_y, dphi2_y, self.lambda1, self.lambda2)

        return {
            "displacement_x_meters": disp_x,
            "displacement_y_meters": disp_y,
            "distance_to_birthplace": math.sqrt(disp_x ** 2 + disp_y ** 2),
            "mod1_res": res1,
            "mod2_res": res2,
            "disambiguation_residual": max(res_x, res_y),
            "total_neurons": self.TOTAL_NEURONS,
        }
