"""
brain/carl_stage2_2_world_model.py — Stage 2.2 Action-Conditioned Recurrent World Model
Classification: [NEUROMORPHIC / RECURRENT WORLD MODEL] Pure Neural Forward Simulation

Predicts future 25-D sensory states hat{s}_{t+k} given candidate motor commands u_{t:t+k-1}
and internal spatial heading v_HD = [cos(theta_HD), sin(theta_HD)] without querying MuJoCo simulator internals.

Strict Anti-Cheat Invariant:
- Zero imports of mujoco
- Zero references to CarlStage1HAL, mj_ray, data.qpos, data.qvel, data.contact
- Operates entirely in PyTorch/NumPy tensor space.
"""

import math
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import torch
import torch.nn as nn


class SensoryNormalizer:
    """
    Frozen sensor normalization module computed strictly on DEV_TRAIN.
    Standardizes 25-D sensor observations: s_norm = (s - mu) / sigma.
    """
    def __init__(self, mu: np.ndarray, sigma: np.ndarray):
        assert len(mu) == 25 and len(sigma) == 25, "Normalizer must have 25 dimensions"
        self.mu = torch.from_numpy(mu.astype(np.float32))
        self.sigma = torch.from_numpy(np.maximum(sigma, 1e-6).astype(np.float32))

    def normalize(self, s: torch.Tensor) -> torch.Tensor:
        mu = self.mu.to(s.device)
        sigma = self.sigma.to(s.device)
        return (s - mu) / sigma

    def denormalize(self, s_norm: torch.Tensor) -> torch.Tensor:
        mu = self.mu.to(s_norm.device)
        sigma = self.sigma.to(s_norm.device)
        return (s_norm * sigma) + mu


class CarlStage2WorldModel(nn.Module):
    """
    Action-Conditioned Recurrent Forward World Model (Stage 2.2).
    
    Architecture:
    - Input Vector x_t in R^33: [s_norm_25; cos(theta_HD); sin(theta_HD); u_6]
    - Recurrent Core: GRU(input_dim=33, hidden_dim=128)
    - Sensory Decoder: MLP(128 -> 128 -> 25) with SiLU activations
    - Clamping: Physical channel range bounds [s_min, s_max]
    """
    SENSORY_DIM: int = 25
    HEADING_DIM: int = 2
    ACTION_DIM: int = 6
    INPUT_DIM: int = 33  # 25 + 2 + 6
    HIDDEN_DIM: int = 128
    DT: float = 0.030  # Control tick 33.33 Hz

    def __init__(self, hidden_dim: int = 128, dt: float = 0.030):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dt = dt

        # Recurrent Forward Transition Core
        self.gru = nn.GRU(
            input_size=self.INPUT_DIM,
            hidden_size=self.hidden_dim,
            batch_first=True
        )

        # Sensory Synthesis Decoder MLP
        self.decoder = nn.Sequential(
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.SiLU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.SiLU(),
            nn.Linear(self.hidden_dim, self.SENSORY_DIM)
        )

        # Physical Sensor Bounds for Clamping
        # [0:15] = sonars [0.0, 5.0]
        # [15:18] = linear accel [-50.0, 50.0]
        # [18:21] = angular gyro [-20.0, 20.0]
        # [21:24] = joint angles [-pi, pi]
        # [24] = battery [0.0, 1.0]
        bounds_min = np.array([0.0]*15 + [-50.0]*3 + [-20.0]*3 + [-math.pi]*3 + [0.0], dtype=np.float32)
        bounds_max = np.array([5.0]*15 + [50.0]*3 + [20.0]*3 + [math.pi]*3 + [1.0], dtype=np.float32)
        self.register_buffer("bounds_min", torch.from_numpy(bounds_min))
        self.register_buffer("bounds_max", torch.from_numpy(bounds_max))

    def forward_step(
        self,
        h_t: torch.Tensor,
        s_norm_t: torch.Tensor,
        v_hd_t: torch.Tensor,
        u_t: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Single-step forward transition:
        Takes (h_t, s_norm_t, v_hd_t, u_t), steps GRU, decodes s_norm_hat_{t+1}.
        """
        # Assemble 33-D input vector
        x_t = torch.cat([s_norm_t, v_hd_t, u_t], dim=-1).unsqueeze(1)  # (batch, 1, 33)
        out, h_next = self.gru(x_t, h_t)  # out: (batch, 1, hidden), h_next: (1, batch, hidden)
        s_norm_hat = self.decoder(out.squeeze(1))  # (batch, 25)
        return h_next, s_norm_hat

    def clamp_physical_bounds(self, s: torch.Tensor) -> torch.Tensor:
        """Clamps decoded sensor values to strict physical limits."""
        return torch.max(torch.min(s, self.bounds_max), self.bounds_min)

    def rollout_mental_trajectory(
        self,
        h_0: torch.Tensor,
        s_0: torch.Tensor,
        v_hd_0: torch.Tensor,
        u_seq: torch.Tensor,
        normalizer: SensoryNormalizer
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Pure autoregressive multi-step forward rollout (ZERO teacher forcing).
        
        Args:
            h_0: Initial belief state (1, batch, hidden_dim)
            s_0: Initial raw physical observation (batch, 25)
            v_hd_0: Initial heading unit vector [cos(theta), sin(theta)] (batch, 2)
            u_seq: Candidate future motor actions (batch, H, 6)
            normalizer: Frozen SensoryNormalizer instance
            
        Returns:
            s_pred_seq: (batch, H, 25) predicted raw sensory trajectory
            v_hd_pred_seq: (batch, H, 2) predicted heading unit vectors
            h_final: (1, batch, hidden_dim) final recurrent state
        """
        batch_size, horizon, action_dim = u_seq.shape
        assert action_dim == self.ACTION_DIM, f"Expected action dim {self.ACTION_DIM}"

        s_preds = []
        v_hd_preds = []

        curr_h = h_0
        curr_s = s_0
        curr_v_hd = v_hd_0

        for k in range(horizon):
            u_k = u_seq[:, k, :]  # (batch, 6)
            s_norm_k = normalizer.normalize(curr_s)  # (batch, 25)

            # Step recurrent core and decode next normalized sensor observation
            curr_h, s_norm_hat_next = self.forward_step(curr_h, s_norm_k, curr_v_hd, u_k)

            # Denormalize and clamp to physical range bounds
            s_hat_raw = normalizer.denormalize(s_norm_hat_next)
            s_hat_clamped = self.clamp_physical_bounds(s_hat_raw)

            # Internal heading update: integrate predicted angular velocity (gyro z is channel 20)
            # omega_z in rad/s, delta_theta = omega_z * dt
            omega_z = s_hat_clamped[:, 20]  # (batch,)
            delta_theta = omega_z * self.DT
            cos_dt = torch.cos(delta_theta)
            sin_dt = torch.sin(delta_theta)

            # 2D rotation of current unit heading vector
            v_x = curr_v_hd[:, 0] * cos_dt - curr_v_hd[:, 1] * sin_dt
            v_y = curr_v_hd[:, 0] * sin_dt + curr_v_hd[:, 1] * cos_dt
            v_norm = torch.sqrt(v_x**2 + v_y**2 + 1e-9)
            curr_v_hd = torch.stack([v_x / v_norm, v_y / v_norm], dim=-1)

            # Autoregressive feedback: model's own clamped prediction becomes next step's input
            curr_s = s_hat_clamped

            s_preds.append(curr_s.unsqueeze(1))
            v_hd_preds.append(curr_v_hd.unsqueeze(1))

        s_pred_seq = torch.cat(s_preds, dim=1)        # (batch, H, 25)
        v_hd_pred_seq = torch.cat(v_hd_preds, dim=1)  # (batch, H, 2)
        return s_pred_seq, v_hd_pred_seq, curr_h


class NaivePersistencePredictor:
    """
    Baseline A: Naive Persistence Predictor.
    Predicts that future sensory states remain identical to the initial observation:
        hat{s}_{t+k} = s_t for all k.
    """
    def predict(self, s_0: np.ndarray, horizon: int) -> np.ndarray:
        """
        Args:
            s_0: (batch, 25) or (25,)
            horizon: H steps
        Returns:
            s_pred_seq: (batch, H, 25) or (H, 25)
        """
        if s_0.ndim == 1:
            return np.repeat(s_0[np.newaxis, :], horizon, axis=0)
        else:
            return np.repeat(s_0[:, np.newaxis, :], horizon, axis=1)


class LinearActionPredictor:
    """
    Baseline B: Linear Action-Conditioned Predictor.
    Standard ridge regression fitting:
        hat{s}_{t+1} = W_s @ s_t + W_hd @ v_HD_t + W_u @ u_t + b
    Rolled out autoregressively for H steps.
    """
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.W = None  # Shape (25, 34) including bias
        self.dt = 0.030

    def fit(self, S: np.ndarray, V_hd: np.ndarray, U: np.ndarray, S_next: np.ndarray):
        """Fits Ridge Regression weights on DEV_TRAIN."""
        assert len(S) == len(S_next), "Inputs must match length"
        X = np.concatenate([S, V_hd, U, np.ones((len(S), 1))], axis=1)  # (N, 34)
        Y = S_next  # (N, 25)

        d = X.shape[1]
        reg = self.alpha * np.eye(d)
        reg[-1, -1] = 0.0  # Do not regularize bias
        self.W = np.linalg.solve(X.T @ X + reg, X.T @ Y).T  # (25, 34)

    def predict(self, s_0: np.ndarray, v_hd_0: np.ndarray, u_seq: np.ndarray) -> np.ndarray:
        """Autoregressive rollout of linear model."""
        assert self.W is not None, "Model must be fitted before predict"
        horizon = len(u_seq)
        s_preds = np.zeros((horizon, 25), dtype=np.float64)

        curr_s = s_0.copy()
        curr_v_hd = v_hd_0.copy()

        for k in range(horizon):
            u_k = u_seq[k]
            x_k = np.concatenate([curr_s, curr_v_hd, u_k, [1.0]])
            s_next = self.W @ x_k
            s_next[:15] = np.clip(s_next[:15], 0.0, 5.0)  # clamp sonars

            # Update heading
            omega_z = s_next[20]
            dtheta = omega_z * self.dt
            cos_dt, sin_dt = math.cos(dtheta), math.sin(dtheta)
            vx = curr_v_hd[0] * cos_dt - curr_v_hd[1] * sin_dt
            vy = curr_v_hd[0] * sin_dt + curr_v_hd[1] * cos_dt
            norm_v = math.hypot(vx, vy) + 1e-9
            curr_v_hd = np.array([vx / norm_v, vy / norm_v])

            curr_s = s_next
            s_preds[k] = curr_s

        return s_preds
