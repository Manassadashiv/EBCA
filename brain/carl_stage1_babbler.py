"""
brain/carl_stage1_babbler.py — Safe Autonomous Motor-Babbling Engine
Classification: [VALIDATION CRITERION] Safe Dynamic Motor Babbling

Implements controlled exploratory motor babbling strictly constrained within the physical safety envelope:
- Max bound: ||u_babble||_inf <= 0.150 (max_i |u_i| <= 0.150)
- Excitation regimes: Single channel sweeps, coupled synergies, Ornstein-Uhlenbeck diffusion, worst-case step reversals
- Fully deterministic and reproducible from integer seed
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any


class CarlStage1Babbler:
    """
    Exploratory Motor Babbling Generator for Stage 1 Sensorimotor Discovery.
    Enforces strict physical safety bound ||u_babble||_inf <= 0.150.
    """
    # [ARCHITECTURAL INVARIANT] Stage 1 Babbling Safety Ceiling
    MAX_AMPLITUDE: float = 0.150
    ACTUATOR_DIM: int = 6

    # Excitation Regime Constants
    REGIME_SINGLE_CHANNEL: int = 0
    REGIME_COUPLED_SYNERGY: int = 1
    REGIME_ORNSTEIN_UHLENBECK: int = 2
    REGIME_STEP_REVERSAL: int = 3

    def __init__(self, seed: int = 42, regime: int = REGIME_ORNSTEIN_UHLENBECK):
        """
        Initializes babbling generator with deterministic seed and specified excitation regime.
        """
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        self.regime = regime

        # Ornstein-Uhlenbeck parameters
        self.theta_ou: float = 0.15   # mean reversion rate
        self.sigma_ou: float = 0.04   # diffusion volatility
        self.dt: float = 0.03333333333333333
        self.ou_state = np.zeros(self.ACTUATOR_DIM, dtype=np.float64)

        # Pulse / Step schedule state
        self.tick_count: int = 0
        self.pulse_channel: int = 0
        self.pulse_sign: float = 1.0
        self.pulse_duration: int = 30  # ticks per pulse (1.0s)
        self.pulse_timer: int = 0

    def reset(self, seed: Optional[int] = None):
        """Resets babbler state and optionally updates random seed."""
        if seed is not None:
            self.seed = seed
        self.rng = np.random.RandomState(self.seed)
        self.ou_state.fill(0.0)
        self.tick_count = 0
        self.pulse_channel = 0
        self.pulse_sign = 1.0
        self.pulse_timer = 0

    def generate_command(self) -> np.ndarray:
        """
        Generates next continuous 6-D motor command vector u_proposed.
        Guarantees max_i |u_i| <= 0.150 under all conditions.
        """
        u = np.zeros(self.ACTUATOR_DIM, dtype=np.float64)

        if self.regime == self.REGIME_SINGLE_CHANNEL:
            # Pulse one channel at a time, cycle through all 6 with +/- signs
            u[self.pulse_channel] = self.pulse_sign * self.MAX_AMPLITUDE
            self.pulse_timer += 1
            if self.pulse_timer >= self.pulse_duration:
                self.pulse_timer = 0
                if self.pulse_sign > 0:
                    self.pulse_sign = -1.0
                else:
                    self.pulse_sign = 1.0
                    self.pulse_channel = (self.pulse_channel + 1) % self.ACTUATOR_DIM

        elif self.regime == self.REGIME_COUPLED_SYNERGY:
            # Explore paired channel interactions (e.g. differential vs common drive)
            phase = (self.tick_count // 45) % 6
            if phase == 0:
                # In-phase pair 0 & 1
                u[0] = self.MAX_AMPLITUDE
                u[1] = self.MAX_AMPLITUDE
            elif phase == 1:
                # Anti-phase pair 0 & 1 (differential spin)
                u[0] = self.MAX_AMPLITUDE
                u[1] = -self.MAX_AMPLITUDE
            elif phase == 2:
                # Anti-phase reverse
                u[0] = -self.MAX_AMPLITUDE
                u[1] = self.MAX_AMPLITUDE
            elif phase == 3:
                # Channels 2 & 3 (Head scan)
                u[2] = self.MAX_AMPLITUDE * np.sin(self.tick_count * 0.1)
                u[3] = self.MAX_AMPLITUDE * np.cos(self.tick_count * 0.1)
            elif phase == 4:
                # Channel 4 (Torso pitch swing)
                u[4] = self.MAX_AMPLITUDE * np.sin(self.tick_count * 0.08)
            else:
                # Full multi-channel harmonic excitation
                for i in range(self.ACTUATOR_DIM):
                    u[i] = self.MAX_AMPLITUDE * np.sin(self.tick_count * 0.05 * (i + 1))

        elif self.regime == self.REGIME_STEP_REVERSAL:
            # Worst-case step reversal: +0.150 -> -0.150 every 30 ticks
            reversal_phase = (self.tick_count // 30) % 2
            sign = 1.0 if reversal_phase == 0 else -1.0
            u[0] = sign * self.MAX_AMPLITUDE
            u[1] = -sign * self.MAX_AMPLITUDE  # max differential torque
            u[4] = sign * self.MAX_AMPLITUDE   # simultaneous torso swing

        else:
            # REGIME_ORNSTEIN_UHLENBECK (Default continuous stochastic walk)
            # dx = -theta * x * dt + sigma * sqrt(dt) * dW
            noise = self.rng.randn(self.ACTUATOR_DIM)
            dx = -self.theta_ou * self.ou_state * self.dt + self.sigma_ou * np.sqrt(self.dt) * noise
            self.ou_state += dx
            u = np.clip(self.ou_state, -self.MAX_AMPLITUDE, self.MAX_AMPLITUDE)

        # Enforce strict safety clamping
        u_safe = np.clip(u, -self.MAX_AMPLITUDE, self.MAX_AMPLITUDE)
        self.tick_count += 1

        return u_safe

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns babbler internal telemetry."""
        return {
            "tick": self.tick_count,
            "regime": self.regime,
            "max_amplitude": self.MAX_AMPLITUDE,
            "ou_norm": float(np.linalg.norm(self.ou_state)),
        }
