"""
brain/carl_stage2_2_r2_body_model.py — Module 1: Kinematic Body & Ego-Dynamics Predictor
Classification: [CORE COMPONENT] Causal Kinematic Chassis Forward Model (Stage 2.2-R2)

Role:
Predicts how CARL's physical chassis moves in response to motor efference copy (actions u_t)
and proprioceptive state (wheel speeds, IMU acceleration, and gyro yaw rate).

Causal Invariants Enforced:
1. Zero Sensory Leak: Strictly isolated from sonar channels, external geometry, and MuJoCo qpos/qvel.
2. Dynamic Coasting Physics: When u_t = 0, the body model predicts continuous mechanical deceleration
   governed by inertia and ground friction, not an artificial instantaneous halt.
3. Multi-Step Propagation: Emits predicted proprioceptive state and incremental relative displacement
   (Δx, Δy, Δθ) in the robot's local body frame.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional


class KinematicBodyModel(nn.Module):
    """
    Module 1 (M_body): Kinematic Body & Ego-Dynamics Predictor.
    
    Inputs:
    - s_body_t: 9-D proprioceptive state [IMU accel (3), IMU gyro (3), joints (3)]
    - u_t: 6-D motor efference copy (wheel commands and auxiliary actuators)
    
    Outputs:
    - next_s_body: Predicted next proprioceptive state (9-D)
    - delta_p: Predicted local body-frame displacement [Δx, Δy, Δθ] (3-D)
    """
    def __init__(
        self,
        proprio_dim: int = 9,
        action_dim: int = 6,
        hidden_dim: int = 128,
        dt: float = 0.030
    ):
        super().__init__()
        self.proprio_dim = proprio_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.dt = dt

        # Shared feature extractor for proprioception and motor efference
        self.encoder = nn.Sequential(
            nn.Linear(proprio_dim + action_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU()
        )

        # Recurrent state for tracking momentum / velocity history during coasting
        self.rnn = nn.GRUCell(hidden_dim, hidden_dim)

        # Proprioceptive delta head (predicts Δs_body)
        self.head_proprio = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Linear(hidden_dim // 2, proprio_dim)
        )

        # Kinematic displacement head (predicts local [Δx, Δy, Δθ])
        self.head_displacement = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Linear(hidden_dim // 2, 3)
        )

        # Physical wheel-to-chassis parameters (calibrated against MuJoCo physics)
        self.k_fwd = nn.Parameter(torch.tensor([0.0125], dtype=torch.float32))
        self.k_rot = nn.Parameter(torch.tensor([0.321], dtype=torch.float32))
        self.gamma_v = 0.70  # linear coasting decay under u=0
        self.gamma_w = 0.75  # angular coasting decay under u=0
        self.beta_w = 10.70  # yaw rate action torque response (rad/s per u_diff)

    def forward(
        self,
        s_body: torch.Tensor,
        u: torch.Tensor,
        hidden: Optional[torch.Tensor] = None,
        prev_v: Optional[torch.Tensor] = None,
        prev_w: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Single-step forward prediction with physical momentum and deceleration coasting.
        
        Args:
            s_body: (batch, proprio_dim)
            u: (batch, action_dim)
            hidden: (batch, hidden_dim) or None
            prev_v: (batch, 1) prior forward speed or None
            prev_w: (batch, 1) prior yaw rate or None
            
        Returns:
            next_s_body: (batch, proprio_dim)
            delta_p: (batch, 3) local displacement [Δx, Δy, Δθ]
            next_hidden: (batch, hidden_dim)
            next_v: (batch, 1)
            next_w: (batch, 1)
        """
        batch_size = s_body.size(0)
        device = s_body.device

        x_in = torch.cat([s_body, u], dim=-1)
        feat = self.encoder(x_in)

        if hidden is None:
            hidden = torch.zeros(batch_size, self.hidden_dim, device=device)

        next_hidden = self.rnn(feat, hidden)

        # Residual proprioceptive prediction
        delta_proprio = self.head_proprio(next_hidden)

        # Joint servo velocity integration priors (Channels 6, 7, 8 in s_body)
        # Actuator mapping: u[:, 4] is hip pitch, u[:, 3] is neck tilt, u[:, 2] is head pan
        joint_priors = torch.zeros(batch_size, 9, device=device)
        joint_priors[:, 6] = 0.0097 * u[:, 4]
        joint_priors[:, 7] = 0.0061 * u[:, 3]
        joint_priors[:, 8] = 0.0145 * u[:, 2]

        # 1st-order momentum filters for linear velocity v and yaw rate w
        u_L = u[:, 0:1]
        u_R = u[:, 1:2]
        u_fwd = 0.5 * (u_L + u_R)
        u_diff = (u_R - u_L)

        if prev_v is None:
            prev_v = u_fwd * self.k_fwd / self.dt
        if prev_w is None:
            prev_w = s_body[:, 5:6]

        # Momentum & Deceleration under u=0:
        is_fwd_zero = (torch.abs(u_fwd) < 1e-4).float()
        v_target = u_fwd * self.k_fwd / self.dt
        next_v = is_fwd_zero * (self.gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)

        is_diff_zero = (torch.abs(u_diff) < 1e-4).float()
        w_target = u_diff * self.k_rot / self.dt
        next_w = is_diff_zero * (self.gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.15 * prev_w + 0.85 * w_target)

        # Update yaw rate channel (channel 5 of s_body)
        joint_priors[:, 5:6] = next_w - s_body[:, 5:6]

        next_s_body = s_body + joint_priors + 0.1 * delta_proprio

        # Neural kinematic displacement in body frame
        delta_p_neural = self.head_displacement(next_hidden)

        # Analytical differential drive displacement with momentum
        fwd_prior = next_v * self.dt
        yaw_prior = next_w * self.dt
        
        # Combined displacement [Δx (fwd), Δy (lateral drift), Δθ (yaw change)]
        delta_x = fwd_prior + 0.1 * delta_p_neural[:, 0:1]
        delta_y = 0.05 * delta_p_neural[:, 1:2]
        delta_theta = yaw_prior + 0.1 * delta_p_neural[:, 2:3]

        delta_p = torch.cat([delta_x, delta_y, delta_theta], dim=-1)

        return next_s_body, delta_p, next_hidden, next_v, next_w

    def unroll(
        self,
        s_body_0: torch.Tensor,
        actions: torch.Tensor,
        hidden: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Autoregressive multi-step kinematic rollout.
        
        Args:
            s_body_0: (batch, proprio_dim) initial proprioception
            actions: (batch, horizon, action_dim) motor sequence
            hidden: initial hidden state or None
            
        Returns:
            s_body_traj: (batch, horizon, proprio_dim)
            delta_p_traj: (batch, horizon, 3) local displacements at each step
            cumulative_poses: (batch, horizon, 3) accumulated prospective pose [x, y, θ]
        """
        batch_size, horizon, _ = actions.shape
        device = s_body_0.device

        s_body_list = []
        delta_p_list = []
        pose_list = []

        curr_s_body = s_body_0
        curr_hidden = hidden
        curr_v = None
        curr_w = None
        curr_pose = torch.zeros(batch_size, 3, device=device)  # relative to origin [0, 0, 0]

        for t in range(horizon):
            u_t = actions[:, t, :]
            next_s_body, delta_p, curr_hidden, curr_v, curr_w = self.forward(
                curr_s_body, u_t, curr_hidden, curr_v, curr_w
            )

            # Accumulate pose in 2D allocentric frame
            # delta_p is in current body frame [dx_local, dy_local, dtheta]
            dx_local = delta_p[:, 0:1]
            dy_local = delta_p[:, 1:2]
            dtheta = delta_p[:, 2:3]

            theta = curr_pose[:, 2:3]
            cos_t = torch.cos(theta)
            sin_t = torch.sin(theta)

            dx_global = dx_local * cos_t - dy_local * sin_t
            dy_global = dx_local * sin_t + dy_local * cos_t

            new_x = curr_pose[:, 0:1] + dx_global
            new_y = curr_pose[:, 1:2] + dy_global
            new_theta = curr_pose[:, 2:3] + dtheta

            curr_pose = torch.cat([new_x, new_y, new_theta], dim=-1)

            s_body_list.append(next_s_body.unsqueeze(1))
            delta_p_list.append(delta_p.unsqueeze(1))
            pose_list.append(curr_pose.unsqueeze(1))

            curr_s_body = next_s_body

        s_body_traj = torch.cat(s_body_list, dim=1)
        delta_p_traj = torch.cat(delta_p_list, dim=1)
        cumulative_poses = torch.cat(pose_list, dim=1)

        return s_body_traj, delta_p_traj, cumulative_poses
