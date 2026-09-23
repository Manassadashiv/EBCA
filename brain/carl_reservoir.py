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

    def __init__(self, N: int = 500, M: int = 37, K: int = 3,
                 spectral_radius: float = 1.0, sparsity: float = 0.15,
                 tau: float = 0.1, sigma_in: float = 0.1, seed: int = 42,
                 profile: str = "sim"):
        """
        Args:
            N: Reservoir size (500 for 'sim', 250 for 'hardware')
            M: Input dimension (sensory vector size)
            K: Output dimension (motor commands: left, right, neck)
            profile: Compute profile ('sim' or 'hardware')
        """
        if profile == "hardware":
            N = 250
            sparsity = 0.075  # 7.5% sparsity for Cortex-A / Pi L1/L2 cache
            
        self.N = N
        self.M = M
        self.K = K
        self.tau = tau
        self.profile = profile
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
        self.W_out = np.zeros((K, N))

        # ── Reservoir state x(t) ─────────────────────────────────────────
        self.x = np.zeros(N)

        # ── RLS variables ─────────────────────────────────────────────────
        self.rls_alpha = 1.0   # initial P scale
        self.rls_lambda = 0.999  # forgetting factor
        self.P = np.eye(N) * self.rls_alpha

        # ── Arm & Finger Readout Matrix (K_arm = 12 × N) ─────────────────
        # 12 actuators: 4 joints + 2 3-finger tripod grippers per arm (L & R)
        self.K_arm = 12
        self.W_out_arm = np.zeros((self.K_arm, N))
        self.P_arm = np.eye(N) * self.rls_alpha
        self.total_arm_rls_updates = 0

        self.ARM_ACTUATOR_NAMES = [
            "act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L",
            "act_shoulder_yaw_R", "act_shoulder_R", "act_elbow_R", "act_wrist_R", "act_grip_R", "act_grip_thumb_R"
        ]

        self.ARM_CTRL_RANGES = [
            (-0.52, 1.57), (-1.8, 1.8), (-2.44, 0.0), (-1.57, 1.57), (0.0, 0.52), (0.0, 0.52),
            (-1.57, 0.52), (-1.8, 1.8), (-2.44, 0.0), (-1.57, 1.57), (0.0, 0.52), (0.0, 0.52)
        ]

        # ── Metrics ───────────────────────────────────────────────────────
        self.total_rls_updates = 0
        self.last_prediction_error = np.zeros(K)
        self.last_arm_prediction_error = np.zeros(self.K_arm)

        # ── Homeostatic Intrinsic Plasticity ──────────────────────────────
        self.thresholds = np.zeros(N, dtype=float)
        self.firing_rates = np.zeros(N, dtype=float)
        self.target_rate = 0.10
        self.tau_homeostasis = 0.999
        self.eta_homeostasis = 0.001

        # ── Reward-Modulated STDP Trace ──────────────────────────────────
        self.eligibility_trace = np.zeros((N, N), dtype=float)
        self.r_stdp_lr = 0.0002

        print(f"[LSM-211] Reservoir initialized: {N} neurons, "
              f"spectral radius = {actual_sr:.4f}, "
              f"sparsity = {np.count_nonzero(mask)}/{N*N} "
              f"({100*np.count_nonzero(mask)/(N*N):.1f}%), "
              f"tau = {tau}s")

    def step(self, u: np.ndarray, noise_scale: float = 0.02, dt: float = 0.033) -> np.ndarray:
        """
        Single reservoir update step at 30 Hz with homeostatic threshold adaptation.

        Args:
            u: Sensory input vector (M,) — precision-weighted
            noise_scale: Exploration noise amplitude (from NE level)
            dt: Timestep in seconds

        Returns:
            y: Motor command vector (K,) = W_out @ x(t)
        """
        # Noise injection: η ~ N(0, σ₀² × NE)
        eta = np.random.randn(self.N) * self.sigma_noise_base * noise_scale

        # Leaky integrator state update with Homeostatic Threshold:
        # drive = tanh(W_res @ x + W_in @ u + η - θ)
        leak = dt / self.tau
        drive = np.tanh(self.W_res @ self.x + self.W_in @ u + eta - self.thresholds)
        self.x = (1.0 - leak) * self.x + leak * drive

        # Update Homeostatic Intrinsic Thresholds (maintaining target sensitivity)
        active = (np.abs(self.x) > 0.10).astype(float)
        self.firing_rates = self.tau_homeostasis * self.firing_rates + (1.0 - self.tau_homeostasis) * active
        self.thresholds += self.eta_homeostasis * (self.firing_rates - self.target_rate)
        self.thresholds = np.clip(self.thresholds, -0.5, 0.5)

        # Update STDP Eligibility Traces: E_ij = 0.95 * E_ij + x_i * x_j
        outer_activity = np.outer(self.x, self.x)
        self.eligibility_trace = 0.95 * self.eligibility_trace + 0.05 * outer_activity

        # NaN/Inf safeguard
        if np.isnan(self.x).any() or np.isinf(self.x).any():
            print("[WARNING][LSM-211] Reservoir state NaN/Inf detected. Soft-resetting.")
            self.x = np.nan_to_num(self.x, nan=0.0, posinf=0.5, neginf=-0.5)

        # Readout: y(t) = W_out @ x(t)
        y = self.W_out @ self.x

        # Clamp output to safe motor range
        y = np.clip(y, -1.0, 1.0)

        return y

    def r_stdp_step(self, dopamine_surge: float):
        """
        Reward-Modulated STDP: Applies dopamine-gated weight updates to recurrent reservoir connections.
        ΔW_res = η_R * (DA - 1.0) * Eligibility_Trace
        """
        if abs(dopamine_surge) > 0.1:
            delta_w = self.r_stdp_lr * dopamine_surge * self.eligibility_trace
            self.W_res += delta_w
            # Rescale spectral radius periodically to maintain stability
            sr = np.max(np.abs(np.linalg.eigvals(self.W_res)))
            if sr > 1.25 or sr < 0.75:
                self.W_res *= (1.0 / max(1e-5, sr))

    def predict_arm_and_fingers(self) -> dict:
        """
        Computes neural spiking predictions for dual arms and grippers.
        Clamps outputs to exact hardware physical limits (ctrlrange).

        Returns:
            dict mapping actuator_name -> ctrl_val
        """
        raw_out = self.W_out_arm @ self.x
        targets = {}
        for i, name in enumerate(self.ARM_ACTUATOR_NAMES):
            min_v, max_v = self.ARM_CTRL_RANGES[i]
            targets[name] = float(np.clip(raw_out[i], min_v, max_v))
        return targets

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

    def rls_update_arm(self, y_target_arm: np.ndarray):
        """
        FORCE/RLS update for the 10-DOF dual arm and finger readout weights (W_out_arm).

        Args:
            y_target_arm: Target joint angles and finger squeeze levels (10,)
        """
        if len(y_target_arm) != self.K_arm:
            raise ValueError(f"Expected y_target_arm of length {self.K_arm}, got {len(y_target_arm)}")

        phi = self.x

        # Prediction error: e = y_target_arm - W_out_arm @ phi
        y_pred = self.W_out_arm @ phi
        error = y_target_arm - y_pred
        self.last_arm_prediction_error = error.copy()

        # Gain vector using P_arm: k = P_arm @ phi / (λ + phi^T @ P_arm @ phi)
        P_phi = self.P_arm @ phi
        denom = self.rls_lambda + phi @ P_phi
        if abs(denom) < 1e-12:
            return
        gain = P_phi / denom

        # Update inverse correlation matrix for arm
        self.P_arm = (self.P_arm - np.outer(gain, phi @ self.P_arm)) / self.rls_lambda

        # Clamp P_arm to prevent numerical explosion
        p_norm = np.linalg.norm(self.P_arm)
        if p_norm > 1e6:
            self.P_arm *= (1e6 / p_norm)

        # Update arm readout weights
        for k_idx in range(self.K_arm):
            self.W_out_arm[k_idx] += error[k_idx] * gain

        self.total_arm_rls_updates += 1

    def get_state_norm(self) -> float:
        """Returns the L2 norm of the reservoir state (activity level indicator)."""
        return float(np.linalg.norm(self.x))

    def save(self, path: str):
        """Serialize reservoir state and learned weights to disk."""
        np.savez(path,
                 x=self.x, W_out=self.W_out, P=self.P,
                 W_in=self.W_in, W_res=self.W_res,
                 W_out_arm=self.W_out_arm, P_arm=self.P_arm,
                 total_rls_updates=self.total_rls_updates,
                 total_arm_rls_updates=self.total_arm_rls_updates)
        print(f"[GIS-901] Reservoir saved to {path}")

    def load(self, path: str):
        """Restore reservoir state and learned weights from disk."""
        if os.path.exists(path):
            data = np.load(path)
            self.x = data['x']
            self.W_out = data['W_out']
            self.P = data['P']
            self.W_in = data['W_in']
            self.M = self.W_in.shape[1]
            self.W_res = data['W_res']
            self.total_rls_updates = int(data['total_rls_updates'])
            if 'W_out_arm' in data:
                self.W_out_arm = data['W_out_arm']
            if 'P_arm' in data:
                self.P_arm = data['P_arm']
            if 'total_arm_rls_updates' in data:
                self.total_arm_rls_updates = int(data['total_arm_rls_updates'])
            print(f"[GIS-901] Reservoir loaded from {path} "
                  f"({self.total_rls_updates} prior RLS updates, {self.total_arm_rls_updates} arm updates)")
            return True
        return False

    def save_arm_weights(self, path: str):
        """Dedicated export for arm and finger readout weights."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        np.savez(path,
                 W_out_arm=self.W_out_arm,
                 P_arm=self.P_arm,
                 total_arm_rls_updates=self.total_arm_rls_updates)
        print(f"[ARM-301] Arm & finger weights saved to {path}")

    def load_arm_weights(self, path: str) -> bool:
        """Dedicated import for arm and finger readout weights with auto-migration."""
        if os.path.exists(path):
            data = np.load(path)
            loaded_W = data['W_out_arm']
            if loaded_W.shape[0] == 10 and self.K_arm == 12:
                # Shape migration: 10 -> 12 actuators (copy top/bot grips to thumb)
                self.W_out_arm = np.zeros((12, self.N))
                self.W_out_arm[:5, :] = loaded_W[:5, :]      # Left arm joints + top finger
                self.W_out_arm[5, :] = loaded_W[4, :]       # Left thumb = left top finger
                self.W_out_arm[6:11, :] = loaded_W[5:10, :] # Right arm joints + top finger
                self.W_out_arm[11, :] = loaded_W[9, :]      # Right thumb = right top finger
                print(f"[ARM-301] Migrated weight matrix shape from 10 to 12 actuators cleanly!")
            elif loaded_W.shape == self.W_out_arm.shape:
                self.W_out_arm = loaded_W
            if 'P_arm' in data:
                loaded_P = data['P_arm']
                if loaded_P.shape == self.P_arm.shape:
                    self.P_arm = loaded_P
            if 'total_arm_rls_updates' in data:
                self.total_arm_rls_updates = int(data['total_arm_rls_updates'])
            print(f"[ARM-301] Arm & finger weights loaded from {path} ({self.total_arm_rls_updates} RLS updates)")
            return True
        return False

