"""
===============================================================================
  carl_cerebellum.py — CEREBELLAR FORWARD MODEL (CFM-501)
===============================================================================
  Biomimetic Predictive Motor Architecture:

  The biological cerebellum performs ONE core computation:
    PREDICT the sensory consequences of motor commands BEFORE they happen.

  This is called the "efference copy" mechanism:
    1. Motor cortex sends a command to move the arm
    2. Cerebellum receives a COPY of that command (efference copy)
    3. Cerebellum PREDICTS what the sensors will read after the movement
    4. When actual sensors arrive, the PREDICTION ERROR drives learning

  Key Insight: Prediction error IS the curiosity signal.
    - Large prediction error → novel situation → NE surge → explore more
    - Small prediction error → familiar situation → exploit current strategy
    - Sudden prediction error spike → something unexpected happened (slip!)

  Architecture:
    Input:  current_joints(12) + motor_command(12) + touch(2) + target(3) = 29
    Output: predicted_next_touch(2) + predicted_next_position_error(3) = 5

  This module enables:
    - Slip ANTICIPATION (not just detection): predict touch decrease before it happens
    - Collision AVOIDANCE: predict position overshoot before contact
    - Curiosity-driven exploration: prediction error → NE → exploration
    - Motor planning: "if I do X, Y will happen" internal simulation

  References:
    - Wolpert, Miall & Kawato (1998): Internal models in the cerebellum
    - Ito (2008): Control and learning by the cerebellum
    - Bastian (2006): Learning to predict the future: the cerebellum
===============================================================================
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque


class CerebellarForwardModel(nn.Module):
    """
    Cerebellar Forward Model — predicts sensory consequences of motor commands.

    The model learns the mapping:
        (current_state, motor_command) → predicted_next_state

    where:
        current_state  = [joints(12), touch(2), target(3)]  = 17 dims
        motor_command  = [actuator_commands(12)]              = 12 dims
        predicted_next = [next_touch(2), position_error(3)]   = 5 dims

    Training is online: every timestep, the model predicts, then the actual
    next state arrives, and the prediction error updates the weights.

    The prediction error is exposed to the endocrine system:
        - High prediction error → large NE surge (novelty/arousal)
        - Low prediction error  → small NE signal (familiar territory)
    """

    INPUT_DIM = 29   # joints(12) + command(12) + touch(2) + target(3)
    OUTPUT_DIM = 5   # predicted_next_touch(2) + predicted_position_error(3)

    def __init__(self, lr: float = 1e-3, device: str = None):
        super().__init__()

        self.device = torch.device(
            device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        )

        # ── Granule Cell Layer (biological: massive expansion layer) ──────
        # In the real cerebellum, granule cells outnumber all other brain
        # neurons COMBINED. They create a high-dimensional sparse encoding
        # of the input, making pattern separation easier.
        self.forward_model = nn.Sequential(
            nn.Linear(self.INPUT_DIM, 128),    # Mossy fiber → Granule cell
            nn.ReLU(),
            nn.Linear(128, 64),                 # Granule cell → Purkinje cell
            nn.ReLU(),
            nn.Linear(64, self.OUTPUT_DIM),     # Purkinje cell → Deep nuclei output
        ).to(self.device)

        self.optimizer = optim.Adam(self.parameters(), lr=lr)

        # ── Online learning buffer (mini-batch of recent transitions) ─────
        self.transition_buffer = deque(maxlen=512)
        self.batch_size = 32

        # ── Prediction error tracking ────────────────────────────────────
        self.last_prediction = None
        self.last_input = None
        self.prediction_error_ema = 0.0   # Exponential moving average
        self.prediction_error_alpha = 0.05
        self.total_updates = 0

        # ── Slip anticipation state ──────────────────────────────────────
        self.predicted_touch_trend = [0.0, 0.0]  # [left_trend, right_trend]
        self.touch_history = deque(maxlen=10)     # Last 10 touch readings

        print(f"[CFM-501] Cerebellar Forward Model initialized: {self.INPUT_DIM}->128->64->{self.OUTPUT_DIM} "
              f"on {self.device.type.upper()}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.forward_model(x)

    def predict_next_state(self, current_joints: np.ndarray, motor_command: np.ndarray,
                           touch_sensors: np.ndarray, target_3d: np.ndarray) -> dict:
        """
        Generate efference-copy-based prediction of next sensory state.

        Args:
            current_joints: Current actuator positions ∈ R^12
            motor_command: Motor command being sent ∈ R^12
            touch_sensors: [touch_L, touch_R] ∈ R^2
            target_3d: [x, y, z] target ∈ R^3

        Returns:
            dict with:
                'predicted_touch': [predicted_touch_L, predicted_touch_R]
                'predicted_pos_error': [dx, dy, dz] predicted residual
                'slip_risk': float 0-1 (higher = more likely to slip)
                'prediction_confidence': float (lower error = higher confidence)
        """
        input_vec = np.concatenate([current_joints, motor_command, touch_sensors, target_3d])
        input_tensor = torch.from_numpy(input_vec).float().unsqueeze(0).to(self.device)

        # Store for later error computation
        self.last_input = input_vec.copy()

        with torch.no_grad():
            prediction = self.forward(input_tensor).squeeze(0).cpu().numpy()

        self.last_prediction = prediction.copy()

        predicted_touch = prediction[:2]
        predicted_pos_error = prediction[2:]

        # ── Slip Risk Assessment ──────────────────────────────────────
        # Track touch trends: if predicted touch is decreasing, slip risk rises
        self.touch_history.append(touch_sensors.copy())

        slip_risk = 0.0
        if len(self.touch_history) >= 3:
            recent_touch = np.array(list(self.touch_history))[-3:]
            touch_trend_L = recent_touch[-1, 0] - recent_touch[0, 0]
            touch_trend_R = recent_touch[-1, 1] - recent_touch[0, 1]

            # If current touch is positive but predicted to decrease → slip imminent
            if touch_sensors[0] > 0.05 and predicted_touch[0] < touch_sensors[0] * 0.7:
                slip_risk = max(slip_risk, 0.8)
            if touch_sensors[1] > 0.05 and predicted_touch[1] < touch_sensors[1] * 0.7:
                slip_risk = max(slip_risk, 0.8)

            # Declining touch trend also signals slip
            if touch_trend_L < -0.02 and touch_sensors[0] > 0.01:
                slip_risk = max(slip_risk, 0.5)
            if touch_trend_R < -0.02 and touch_sensors[1] > 0.01:
                slip_risk = max(slip_risk, 0.5)

        return {
            'predicted_touch': predicted_touch,
            'predicted_pos_error': predicted_pos_error,
            'slip_risk': float(slip_risk),
            'prediction_confidence': float(max(0.0, 1.0 - self.prediction_error_ema))
        }

    def update_with_actual(self, actual_touch: np.ndarray, actual_pos_error: np.ndarray) -> float:
        """
        Compare prediction with actual sensory outcome. Compute prediction error.
        This is the climbing fiber signal in the biological cerebellum.

        Args:
            actual_touch: Actual touch sensor readings [L, R] ∈ R^2
            actual_pos_error: Actual position error [dx, dy, dz] ∈ R^3

        Returns:
            prediction_error: Scalar prediction error (drives curiosity/NE)
        """
        if self.last_prediction is None or self.last_input is None:
            return 0.0

        actual = np.concatenate([actual_touch, actual_pos_error])
        prediction_error = float(np.mean((self.last_prediction - actual) ** 2))

        # Update EMA of prediction error
        self.prediction_error_ema = (
            (1 - self.prediction_error_alpha) * self.prediction_error_ema +
            self.prediction_error_alpha * prediction_error
        )

        # Store transition for batch training
        self.transition_buffer.append({
            'input': self.last_input.copy(),
            'target': actual.copy()
        })

        # Train on mini-batch if buffer has enough samples
        if len(self.transition_buffer) >= self.batch_size:
            self._train_batch()

        return prediction_error

    def _train_batch(self):
        """Train forward model on a mini-batch from the transition buffer."""
        # Sample batch
        indices = np.random.choice(len(self.transition_buffer), self.batch_size, replace=False)
        batch = [self.transition_buffer[i] for i in indices]

        inputs = torch.tensor(np.array([t['input'] for t in batch]), dtype=torch.float32).to(self.device)
        targets = torch.tensor(np.array([t['target'] for t in batch]), dtype=torch.float32).to(self.device)

        # Forward pass
        predictions = self.forward(inputs)
        loss = nn.functional.mse_loss(predictions, targets)

        # Backward + optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
        self.optimizer.step()

        self.total_updates += 1

    def get_curiosity_signal(self) -> float:
        """
        Returns a normalized curiosity signal based on prediction error.
        High prediction error → high curiosity → more exploration needed.
        Maps to NE (Norepinephrine) in the endocrine system.

        Returns:
            curiosity: float in [0, 1], where 1 = maximum novelty
        """
        return float(np.clip(self.prediction_error_ema * 10.0, 0.0, 1.0))

    def get_grip_force_adjustment(self, slip_risk: float, current_grip: float) -> float:
        """
        Compute preemptive grip force adjustment based on slip prediction.

        If the forward model predicts touch is about to decrease (slip),
        this returns a POSITIVE adjustment to increase grip force BEFORE
        the slip actually happens.

        Args:
            slip_risk: Float 0-1 from predict_next_state()
            current_grip: Current grip actuator value

        Returns:
            grip_adjustment: Additional grip force to apply (0 if no risk)
        """
        if slip_risk > 0.3:
            # Proportional preemptive grip increase
            adjustment = slip_risk * 0.15  # Max additional grip = 0.15
            # Don't exceed actuator limits
            max_adjustment = 0.52 - current_grip
            return float(min(adjustment, max(0.0, max_adjustment)))
        return 0.0

    def save(self, path: str):
        """Save forward model weights."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        torch.save({
            'model_state_dict': self.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'total_updates': self.total_updates,
            'prediction_error_ema': self.prediction_error_ema,
        }, path)
        print(f"[CFM-501] Cerebellar forward model saved to {path} ({self.total_updates} updates)")

    def load(self, path: str) -> bool:
        """Load forward model weights."""
        if os.path.exists(path):
            checkpoint = torch.load(path, map_location=self.device, weights_only=False)
            self.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.total_updates = checkpoint.get('total_updates', 0)
            self.prediction_error_ema = checkpoint.get('prediction_error_ema', 0.0)
            print(f"[CFM-501] Cerebellar forward model loaded from {path} ({self.total_updates} prior updates)")
            return True
        return False
