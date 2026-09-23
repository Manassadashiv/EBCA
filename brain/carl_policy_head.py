"""
===============================================================================
  carl_policy_head.py — BASAL GANGLIA NEURAL POLICY HEAD (BG-401)
===============================================================================
  Biomimetic Dual-Pathway Motor Learning Architecture:

  The biological motor system uses TWO parallel learning pathways:
    1. Cerebellum (→ RLS W_out_arm): Supervised error correction from teacher
    2. Basal Ganglia (→ THIS MODULE): Reward-driven policy optimization

  This module implements Pathway #2:
    - Input: Reservoir state x(t) ∈ R^500 + sensory context ∈ R^17
    - Architecture: 517 → 128 → 64 → 12 (ReLU + tanh output)
    - Training: Dense reward signal modulated by Dopamine (DA)
    - Purpose: Discover grasping/lifting strategies the IK teacher CANNOT teach

  The policy head can surpass the teacher because it learns from REWARD,
  not from imitation. If a novel finger configuration produces higher DA,
  the policy head reinforces it — even if the teacher never demonstrated it.

  References:
    - Doya (2000): Complementary roles of basal ganglia and cerebellum
    - Schultz (1997): Dopamine reward prediction error signal
    - Silver et al. (2014): Residual policy learning
===============================================================================
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


class NeuralPolicyHead(nn.Module):
    """
    Basal Ganglia-inspired Neural Policy Head.

    Sits on top of the LSM reservoir state vector and learns reward-driven
    motor corrections through gradient descent. Dopamine (DA) gates the
    learning rate — high DA amplifies plasticity (reward-driven LTP),
    low DA suppresses it (punishment-driven LTD).

    Input vector (517 dimensions):
        - Reservoir state x(t):          500 dims (temporal memory from LSM)
        - 3D target position:              3 dims (where to reach)
        - Current joint positions:        12 dims (proprioceptive feedback)
        - Touch sensor readings:           2 dims (tactile feedback)

    Output vector (12 dimensions):
        - Correction δu for each actuator (added to MPPI output)
    """

    # Input feature dimensions
    RESERVOIR_DIM = 500
    TARGET_DIM = 3
    JOINT_DIM = 12
    TOUCH_DIM = 2
    TOTAL_INPUT_DIM = RESERVOIR_DIM + TARGET_DIM + JOINT_DIM + TOUCH_DIM  # 517

    # Output dimension (12 actuators)
    OUTPUT_DIM = 12

    def __init__(self, lr: float = 3e-4, device: str = None):
        super().__init__()

        self.device = torch.device(
            device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        )

        # ── Striatal Network (Basal Ganglia policy approximator) ──────────
        # 517 → 128 → 64 → 12
        # Uses LayerNorm for training stability (biological: lateral inhibition)
        self.network = nn.Sequential(
            nn.Linear(self.TOTAL_INPUT_DIM, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, self.OUTPUT_DIM),
            nn.Tanh()  # Output in [-1, 1], scaled to actuator ranges
        ).to(self.device)

        # ── Optimizer (Adam with low LR for stable policy updates) ────────
        self.base_lr = lr
        self.optimizer = optim.Adam(self.parameters(), lr=lr, weight_decay=1e-5)

        # ── Actuator output scaling (maps tanh [-1,1] to actuator ranges) ─
        self.output_scale = torch.tensor([
            0.3, 0.3, 0.3, 0.3, 0.15, 0.15,
            0.3, 0.3, 0.3, 0.3, 0.15, 0.15
        ], device=self.device, dtype=torch.float32)

        # ── Training metrics ─────────────────────────────────────────────
        self.total_updates = 0
        self.running_loss = 0.0
        self.running_reward = 0.0

        print(f"[BG-401] Neural Policy Head initialized: {self.TOTAL_INPUT_DIM}->128->64->{self.OUTPUT_DIM} "
              f"on {self.device.type.upper()}, lr={lr}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through striatal network.
        Returns scaled motor corrections δu ∈ R^12.
        """
        raw = self.network(x)
        return raw * self.output_scale

    def compute_correction(self, reservoir_state: np.ndarray, target_3d: np.ndarray,
                           current_joints: np.ndarray, touch_sensors: np.ndarray) -> np.ndarray:
        """
        Compute policy correction from current sensory context.

        Args:
            reservoir_state: LSM state vector x(t) ∈ R^500
            target_3d: Target position [x, y, z] ∈ R^3
            current_joints: Current actuator positions ∈ R^12
            touch_sensors: [touch_L, touch_R] ∈ R^2

        Returns:
            delta_u: Motor correction vector ∈ R^12
        """
        # Construct 517-dim input vector
        input_vec = np.concatenate([reservoir_state, target_3d, current_joints, touch_sensors])
        input_tensor = torch.from_numpy(input_vec).float().unsqueeze(0).to(self.device)

        with torch.no_grad():
            delta_u = self.forward(input_tensor).squeeze(0)

        return delta_u.cpu().numpy()

    def train_step(self, reservoir_state: np.ndarray, target_3d: np.ndarray,
                   current_joints: np.ndarray, touch_sensors: np.ndarray,
                   reward: float, actual_outcome: np.ndarray,
                   dopamine: float = 1.0):
        """
        Dopamine-gated policy gradient update.

        The learning rate is modulated by dopamine level:
            effective_lr = base_lr × (0.1 + DA)
        High DA (reward) → strong plasticity → reinforce this action
        Low DA (penalty) → weak plasticity → suppress this action

        Args:
            reservoir_state: LSM state x(t) ∈ R^500
            target_3d: Target position ∈ R^3
            current_joints: Joint positions ∈ R^12
            touch_sensors: Touch readings ∈ R^2
            reward: Dense reward signal (continuous, not binary)
            actual_outcome: The actual control that was applied ∈ R^12
            dopamine: Current DA level (gates learning rate)
        """
        # Dopamine-gated learning rate modulation
        da_modulation = max(0.1, min(dopamine, 3.0))
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = self.base_lr * da_modulation

        # Construct input
        input_vec = np.concatenate([reservoir_state, target_3d, current_joints, touch_sensors])
        input_tensor = torch.from_numpy(input_vec).float().unsqueeze(0).to(self.device)
        target_tensor = torch.from_numpy(actual_outcome).float().unsqueeze(0).to(self.device)

        # Forward pass
        predicted_correction = self.forward(input_tensor)

        # Reward-weighted MSE loss
        # When reward is high → minimize distance to actual_outcome (reinforce)
        # When reward is low → the weak LR already handles suppression
        reward_weight = max(0.01, reward)
        loss = reward_weight * nn.functional.mse_loss(predicted_correction, target_tensor)

        # Backward pass + gradient step
        self.optimizer.zero_grad()
        loss.backward()

        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)

        self.optimizer.step()

        # Update metrics
        self.total_updates += 1
        self.running_loss = 0.95 * self.running_loss + 0.05 * loss.item()
        self.running_reward = 0.95 * self.running_reward + 0.05 * reward

    def save(self, path: str):
        """Save policy head weights and optimizer state."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        torch.save({
            'model_state_dict': self.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'total_updates': self.total_updates,
            'running_loss': self.running_loss,
            'running_reward': self.running_reward,
        }, path)
        print(f"[BG-401] Policy head saved to {path} ({self.total_updates} updates)")

    def load(self, path: str) -> bool:
        """Load policy head weights and optimizer state."""
        if os.path.exists(path):
            checkpoint = torch.load(path, map_location=self.device, weights_only=False)
            self.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.total_updates = checkpoint.get('total_updates', 0)
            self.running_loss = checkpoint.get('running_loss', 0.0)
            self.running_reward = checkpoint.get('running_reward', 0.0)
            print(f"[BG-401] Policy head loaded from {path} ({self.total_updates} prior updates)")
            return True
        return False
