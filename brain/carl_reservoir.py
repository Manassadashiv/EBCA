"""
carl_reservoir.py — Liquid State Machine (LSM) Reservoir Brain (LSM-211, LSM-212)

The cognitive core of CARL. A 500-neuron recurrent reservoir with sparse connectivity,
scaled to critical spectral radius ≈ 1.0, driven by 25-dimensional sensory input.

Architecture follows EBCA Technical Specification §1-2:
    x(t+dt) = (1 - dt/τ) x(t) + (dt/τ) tanh(W_res @ x(t) + W_in @ u(t) + η(t))
    y(t) = W_out @ x(t)

W_out is trained online via Recursive Least Squares (RLS) at ≤5 Hz.
W_res and W_in are fixed (reservoir computing paradigm — only the readout learns).

Reservoir Properties:
    - 500 neurons with 15% sparse recurrent connectivity
    - Spectral radius ≈ 1.0 (edge of chaos — maximum computational capacity)
    - Leaking time constant τ ∈ [0.05, 0.5] (mixed fast/slow dynamics)
    - Exploration noise η(t) scaled by Norepinephrine (from endocrine system)

References:
    - Maass, Natschläger, Markram (2002): Real-time computing without stable states
    - Jaeger (2001): The "echo state" approach to recurrent neural network training
    - Sussillo & Abbott (2009): FORCE learning (RLS for reservoir readout)
"""
import numpy as np
import os


class LiquidStateReservoir:
    """
    500-neuron LSM reservoir with RLS-trained readout.
    No backpropagation, no gradient descent — just echo state dynamics and online learning.
    """

    def __init__(self, N: int = 500, M: int = 25, K: int = 3,
                 spectral_radius: float = 1.0, sparsity: float = 0.15,
                 tau: float = 0.1, sigma_in: float = 0.1, seed: int = 42):
        """
        Args:
            N: Reservoir size (number of neurons)
            M: Input dimension (sensory vector size)
            K: Output dimension (motor commands: left, right, neck)
            spectral_radius: Target spectral radius for W_res (edge of chaos ≈ 1.0)
            sparsity: Fraction of non-zero connections in W_res
            tau: Leaking time constant (seconds)
            sigma_in: Input weight standard deviation
            seed: Random seed for reproducible reservoir topology
        """
        self.N = N
        self.M = M
        self.K = K
        self.tau = tau
        self.sigma_noise_base = 0.02  # base exploration noise σ₀

        rng = np.random.RandomState(seed)

        # ── W_in: Input weight matrix (N × M), dense Gaussian ────────────
        self.W_in = rng.randn(N, M) * sigma_in

        # ── W_res: Recurrent weight matrix (N × N), sparse, spectral-scaled
        W_raw = rng.randn(N, N)
        # Apply sparsity mask
        mask = (rng.rand(N, N) < sparsity).astype(float)
        W_raw *= mask
        # Scale to target spectral radius
        eigenvalues = np.linalg.eigvals(W_raw)
        current_radius = np.max(np.abs(eigenvalues))
        if current_radius > 0:
            self.W_res = W_raw * (spectral_radius / current_radius)
        else:
            self.W_res = W_raw
        actual_sr = np.max(np.abs(np.linalg.eigvals(self.W_res)))

        # ── W_out: Readout weight matrix (K × N), initialized to zero ────
        # RLS will train this online. Starting at zero means CARL has no
        # cognitive motor commands initially — only innate CPG + reflexes.
        self.W_out = np.zeros((K, N))

        # ── Reservoir state x(t) ─────────────────────────────────────────
        self.x = np.zeros(N)

        # ── RLS variables ─────────────────────────────────────────────────
        # P: Inverse correlation matrix (N × N), initialized to α*I
        self.rls_alpha = 1.0   # initial P scale
        self.rls_lambda = 0.999  # forgetting factor
        self.P = np.eye(N) * self.rls_alpha

        # ── Metrics ───────────────────────────────────────────────────────
        self.total_rls_updates = 0
        self.last_prediction_error = np.zeros(K)

        print(f"[LSM-211] Reservoir initialized: {N} neurons, "
              f"spectral radius = {actual_sr:.4f}, "
              f"sparsity = {np.count_nonzero(mask)}/{N*N} "
              f"({100*np.count_nonzero(mask)/(N*N):.1f}%), "
              f"tau = {tau}s")

    def step(self, u: np.ndarray, noise_scale: float = 0.02, dt: float = 0.033) -> np.ndarray:
        """
        Single reservoir update step at 30 Hz.

        Args:
            u: Sensory input vector (M,) — precision-weighted
            noise_scale: Exploration noise amplitude (from NE level)
            dt: Timestep in seconds

        Returns:
            y: Motor command vector (K,) = W_out @ x(t)
        """
        # Noise injection: η ~ N(0, σ₀² × NE)
        eta = np.random.randn(self.N) * self.sigma_noise_base * noise_scale

        # Leaky integrator state update (EBCA Spec §1):
        # x(t+dt) = (1 - dt/τ)x(t) + (dt/τ) tanh(W_res @ x(t) + W_in @ u(t) + η(t))
        leak = dt / self.tau
        drive = np.tanh(self.W_res @ self.x + self.W_in @ u + eta)
        self.x = (1.0 - leak) * self.x + leak * drive

        # NaN/Inf safeguard
        if np.isnan(self.x).any() or np.isinf(self.x).any():
            print("[WARNING][LSM-211] Reservoir state NaN/Inf detected. Soft-resetting.")
            self.x = np.nan_to_num(self.x, nan=0.0, posinf=0.5, neginf=-0.5)

        # Readout: y(t) = W_out @ x(t)
        y = self.W_out @ self.x

        # Clamp output to safe motor range
        y = np.clip(y, -2.0, 2.0)

        return y

    def rls_update(self, y_target: np.ndarray):
        """
        Recursive Least Squares readout weight update (EBCA Spec §2A).
        Called at ≤5 Hz (scheduled by the runner).

        This is the ONLY learning mechanism for higher-level behavior.
        The reservoir weights (W_res, W_in) are fixed — only W_out changes.

        Args:
            y_target: Target motor command (K,) — what CARL "should" have done
        """
        phi = self.x  # current reservoir state

        # Prediction error: e = y_target - W_out @ phi
        y_pred = self.W_out @ phi
        error = y_target - y_pred
        self.last_prediction_error = error.copy()

        # Gain vector: k = P @ phi / (λ + phi^T @ P @ phi)
        P_phi = self.P @ phi
        denom = self.rls_lambda + phi @ P_phi
        if abs(denom) < 1e-12:
            return  # numerical protection
        gain = P_phi / denom

        # Update inverse correlation matrix: P = (P - k @ phi^T @ P) / λ
        self.P = (self.P - np.outer(gain, phi @ self.P)) / self.rls_lambda

        # Clamp P to prevent numerical explosion
        p_norm = np.linalg.norm(self.P)
        if p_norm > 1e6:
            self.P *= (1e6 / p_norm)

        # Update readout weights: W_out += e @ k^T (outer product)
        for k_idx in range(self.K):
            self.W_out[k_idx] += error[k_idx] * gain

        self.total_rls_updates += 1

    def get_state_norm(self) -> float:
        """Returns the L2 norm of the reservoir state (activity level indicator)."""
        return float(np.linalg.norm(self.x))

    def save(self, path: str):
        """Serialize reservoir state and learned weights to disk."""
        np.savez(path,
                 x=self.x, W_out=self.W_out, P=self.P,
                 W_in=self.W_in, W_res=self.W_res,
                 total_rls_updates=self.total_rls_updates)
        print(f"[GIS-901] Reservoir saved to {path}")

    def load(self, path: str):
        """Restore reservoir state and learned weights from disk."""
        if os.path.exists(path):
            data = np.load(path)
            self.x = data['x']
            self.W_out = data['W_out']
            self.P = data['P']
            self.W_in = data['W_in']
            self.W_res = data['W_res']
            self.total_rls_updates = int(data['total_rls_updates'])
            print(f"[GIS-901] Reservoir loaded from {path} "
                  f"({self.total_rls_updates} prior RLS updates)")
            return True
        return False
