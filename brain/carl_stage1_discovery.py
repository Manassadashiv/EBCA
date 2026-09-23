"""
brain/carl_stage1_discovery.py — Statistical Sensorimotor Contingency Discovery Engine
Classification: [ARCHITECTURAL INVARIANT] Statistical Discovery Pipeline

Implements rigorous, hypothesis-free sensorimotor body discovery for CARL Stage 1:
- Measures delayed cross-channel contingencies: u(t) -> s(t + tau)
- Generates N_surr = 100,000 IAAFT (Iterative Amplitude Adjusted Fourier Transform) surrogates
- Controls Family-Wise Error Rate at alpha_FWER = 0.01 via Holm-Bonferroni step-down across 150 channel pairs
- Discovers locomotion wheels, gaze pan/tilt, and torso axes without human semantic labels
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional


class CarlSensorimotorDiscoveryEngine:
    """
    Statistical Discovery Core for Sensorimotor Contingency Mapping.
    Discovers body schema topology purely from autonomous babbling experience.
    """
    # [NUMERICAL / CONSTANT] Statistical Parameters
    N_ACTUATORS: int = 6
    N_SENSORS: int = 25
    TOTAL_COMPARISONS: int = 150  # 6 * 25
    ALPHA_FWER: float = 0.01      # Family-Wise Error Rate ceiling
    DEFAULT_N_SURROGATES: int = 100000

    def __init__(self, max_lag_ticks: int = 30, n_surrogates: int = DEFAULT_N_SURROGATES, seed: int = 42):
        """
        Initializes discovery engine with specified temporal lag window and surrogate budget.
        """
        self.max_lag = max_lag_ticks
        self.n_surrogates = n_surrogates
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def compute_cross_correlation_tensor(self, U: np.ndarray, S: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes delayed cross-correlation between all actuator channels u_i and sensor channels s_j:
        C_ij(tau) = 1/T sum (u_i(t) - mean(u_i)) * (s_j(t+tau) - mean(s_j)) / (std(u_i) * std(s_j))
        
        Args:
            U: (T, 6) Actuator command history
            S: (T, 25) Sensor observation history
            
        Returns:
            C_max: (6, 25) Peak absolute correlation
            optimal_lags: (6, 25) Integer lag tau* achieving peak correlation
        """
        T = len(U)
        assert len(S) == T, "U and S must have identical sequence lengths"
        assert T > self.max_lag + 10, "Sequence length must exceed max lag"

        C_max = np.zeros((self.N_ACTUATORS, self.N_SENSORS), dtype=np.float64)
        optimal_lags = np.zeros((self.N_ACTUATORS, self.N_SENSORS), dtype=int)

        # Normalize signals
        U_norm = (U - np.mean(U, axis=0, keepdims=True)) / (np.std(U, axis=0, keepdims=True) + 1e-9)
        S_norm = (S - np.mean(S, axis=0, keepdims=True)) / (np.std(S, axis=0, keepdims=True) + 1e-9)

        for i in range(self.N_ACTUATORS):
            u_i = U_norm[:, i]
            for j in range(self.N_SENSORS):
                s_j = S_norm[:, j]
                best_corr = 0.0
                best_lag = 0
                for tau in range(self.max_lag + 1):
                    if tau == 0:
                        corr = float(np.mean(u_i * s_j))
                    else:
                        corr = float(np.mean(u_i[:-tau] * s_j[tau:]))
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = tau
                C_max[i, j] = best_corr
                optimal_lags[i, j] = best_lag

        return C_max, optimal_lags

    def compute_mutual_information_matrix(self, C_max: np.ndarray) -> np.ndarray:
        """
        Computes Gaussian Copula Mutual Information estimator:
        I(u_i; s_j) = -0.5 * ln(1 - rho^2) (in nats)
        """
        rho_clamped = np.clip(np.abs(C_max), 0.0, 0.9999)
        MI = -0.5 * np.log(1.0 - rho_clamped ** 2)
        return MI

    def generate_iaaft_surrogates(self, x: np.ndarray, n_surr: int, max_iter: int = 20) -> np.ndarray:
        """
        [ARCHITECTURAL INVARIANT] Generates Iterative Amplitude Adjusted Fourier Transform (IAAFT)
        surrogate time series (Schreiber & Schmitz, 1996) using high-performance vectorized batch FFTs.
        
        Preserves:
        1. Exact marginal distribution / histogram of values
        2. Exact linear autocorrelation / power spectral density
        Destroys:
        - Cross-channel nonlinear coupling and phase synchronization.
        
        Args:
            x: (T,) 1D time series
            n_surr: Number of independent surrogate traces to generate
            max_iter: Maximum rank-matching iterations (typically 15-25)
            
        Returns:
            surrogates: (n_surr, T) Array of surrogate series
        """
        T = len(x)
        sorted_x = np.sort(x)
        target_amplitudes = np.abs(np.fft.rfft(x))  # shape (F,)
        
        # Batch size for memory efficiency and cache locality
        batch_size = min(n_surr, 5000)
        surrogates = np.zeros((n_surr, T), dtype=np.float64)

        for start_idx in range(0, n_surr, batch_size):
            end_idx = min(start_idx + batch_size, n_surr)
            b_size = end_idx - start_idx

            # Batch white noise initialization
            s_curr = self.rng.randn(b_size, T)

            for _ in range(max_iter):
                # 1. Fourier phase match across batch axis 1
                fft_curr = np.fft.rfft(s_curr, axis=1)
                phases = np.angle(fft_curr)
                adjusted_fft = target_amplitudes[None, :] * np.exp(1j * phases)
                s_spectral = np.fft.irfft(adjusted_fft, n=T, axis=1)

                # 2. Amplitude rank match across batch axis 1
                ranks = np.argsort(np.argsort(s_spectral, axis=1), axis=1)
                s_curr = sorted_x[ranks]

            surrogates[start_idx:end_idx] = s_curr

        return surrogates

    def run_surrogate_significance_test(
        self, U: np.ndarray, S: np.ndarray, n_surr: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes full statistical discovery pipeline with 100,000 IAAFT surrogates
        and Holm-Bonferroni FWER step-down error control.
        """
        if n_surr is None:
            n_surr = self.n_surrogates

        T = len(U)
        # 1. Observed Cross-Correlations and Mutual Information
        C_obs, optimal_lags = self.compute_cross_correlation_tensor(U, S)
        MI_obs = self.compute_mutual_information_matrix(C_obs)

        # 2. Vectorized IAAFT Surrogate Null Distribution
        # To maintain high performance for 100,000 surrogates across 150 channels,
        # we generate surrogate sensor series and evaluate the null distribution of correlations.
        p_values = np.zeros((self.N_ACTUATORS, self.N_SENSORS), dtype=np.float64)
        null_distributions: Dict[Tuple[int, int], np.ndarray] = {}

        U_norm = (U - np.mean(U, axis=0, keepdims=True)) / (np.std(U, axis=0, keepdims=True) + 1e-9)

        # Precompute surrogates for all 25 sensor channels
        for j in range(self.N_SENSORS):
            s_j = S[:, j]
            s_surrogates = self.generate_iaaft_surrogates(s_j, n_surr=n_surr, max_iter=25)
            s_surr_norm = (s_surrogates - np.mean(s_surrogates, axis=1, keepdims=True)) / (
                np.std(s_surrogates, axis=1, keepdims=True) + 1e-9
            )

            for i in range(self.N_ACTUATORS):
                u_i = U_norm[:, i]
                tau = optimal_lags[i, j]
                
                # Compute surrogate correlation under the optimal lag
                if tau == 0:
                    null_corrs = np.mean(s_surr_norm * u_i[None, :], axis=1)
                else:
                    null_corrs = np.mean(s_surr_norm[:, tau:] * u_i[None, :-tau], axis=1)
                
                null_mi = -0.5 * np.log(1.0 - np.clip(np.abs(null_corrs), 0.0, 0.9999) ** 2)
                observed_mi = MI_obs[i, j]

                # Exact empirical p-value strictly bounded by surrogate count (Phase 4 fix: no Gaussian extrapolation)
                exceedances = int(np.sum(null_mi >= observed_mi))
                emp_p = (1.0 + exceedances) / (n_surr + 1.0)
                p_values[i, j] = emp_p
                
                # Store sample of null distribution for plotting
                null_distributions[(i, j)] = null_mi[:1000]

        # 3. Holm-Bonferroni FWER Step-Down Correction
        p_flat = p_values.flatten()
        sort_indices = np.argsort(p_flat)
        m = len(p_flat)  # 150 comparisons
        
        is_significant_flat = np.zeros(m, dtype=bool)
        adjusted_thresholds_flat = np.zeros(m, dtype=np.float64)

        for rank, idx in enumerate(sort_indices):
            # Holm-Bonferroni threshold for rank k (1-indexed)
            k = rank + 1
            alpha_k = self.ALPHA_FWER / (m - k + 1)
            adjusted_thresholds_flat[idx] = alpha_k

            if p_flat[idx] <= alpha_k:
                is_significant_flat[idx] = True
            else:
                # Once a test fails, all subsequent hypotheses cannot be rejected
                break

        is_significant = is_significant_flat.reshape((self.N_ACTUATORS, self.N_SENSORS))
        adjusted_thresholds = adjusted_thresholds_flat.reshape((self.N_ACTUATORS, self.N_SENSORS))

        # 4. Topological Inference (Phase 3 fix: 100% Anonymous Sensor Discovery)
        discovered_topology = self.infer_body_topology(is_significant, MI_obs, optimal_lags)

        return {
            "C_max": C_obs,
            "optimal_lags": optimal_lags,
            "MI_observed": MI_obs,
            "p_values": p_values,
            "adjusted_thresholds": adjusted_thresholds,
            "is_significant": is_significant,
            "null_distributions": null_distributions,
            "discovered_topology": discovered_topology,
            "n_surrogates": n_surr,
            "alpha_fwer": self.ALPHA_FWER,
            "total_significant_couplings": int(np.sum(is_significant)),
        }

    def infer_body_topology(
        self, is_sig: np.ndarray, MI: np.ndarray, lags: np.ndarray
    ) -> Dict[str, Any]:
        """
        Discovers functional kinematic groupings from anonymous sensorimotor couplings.
        [ARCHITECTURAL INVARIANT]: Operates on anonymous channel indices with ZERO sensor semantics.
        
        - Locomotion Drive Pair: The bilateral actuator pair sharing the highest mutual information
          coupling to an identical distributed body sensor (differential drive chassis rotation).
        - Articulation Servos: Actuators with dominant localized coupling to individual sensors.
        - Inert / LED Channels: Actuators with minimum or zero coupling.
        """
        # Find which pair of actuators shares the highest joint coupling to any anonymous sensor
        best_pair = None
        max_shared_mi = -1.0
        shared_sensor = -1

        for j in range(self.N_SENSORS):
            sorted_act = np.argsort(MI[:, j])[::-1]
            top_2 = sorted_act[:2]
            shared_mi = min(MI[top_2[0], j], MI[top_2[1], j])
            if shared_mi > max_shared_mi:
                max_shared_mi = shared_mi
                best_pair = sorted(top_2.tolist())
                shared_sensor = int(j)

        locomotion_candidates = best_pair if best_pair is not None else [0, 1]

        # Articulation channels: remaining actuators sorted by their individual peak MI
        other_channels = [i for i in range(self.N_ACTUATORS) if i not in locomotion_candidates]
        other_max_mi = [(i, float(np.max(MI[i]))) for i in other_channels]
        other_max_mi.sort(key=lambda x: x[1], reverse=True)

        articulation_candidates = [x[0] for x in other_max_mi if x[1] > 0.008]
        inert_candidates = [x[0] for x in other_max_mi if x[1] <= 0.008]

        breadth = np.sum(is_sig, axis=1)
        total_mi = np.sum(MI, axis=1)

        return {
            "discovered_drive_channels": sorted(locomotion_candidates),
            "discovered_articulation_channels": sorted(articulation_candidates),
            "discovered_inert_channels": sorted(inert_candidates),
            "shared_locomotion_sensor": shared_sensor,
            "max_shared_locomotion_mi": float(max_shared_mi),
            "sensor_breadth": breadth.tolist(),
            "total_coupling_mi": total_mi.tolist(),
        }
