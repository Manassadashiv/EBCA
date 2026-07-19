"""
carl_endocrine.py — Neuromodulatory Endocrine Kinetics (END-201..204)
Integrated into unified SoC state slices.
"""
import numpy as np


class EndocrineSystem:
    BASELINE_DA  = 1.0
    BASELINE_NE  = 0.1
    BASELINE_SHT = 0.8
    BASELINE_ACH = 0.5

    DECAY_DA  = 2.0
    DECAY_NE  = 3.0
    DECAY_SHT = 1.0
    DECAY_ACH = 2.5

    PI_0      = 1.0
    GAMMA_ACH = 0.6
    GAMMA_NE  = 0.4
    GAMMA_SHT = 0.3

    MAX_NM = 3.0
    MIN_NM = 0.0

    def __init__(self):
        self.DA  = self.BASELINE_DA
        self.NE  = self.BASELINE_NE
        self.SHT = self.BASELINE_SHT
        self.ACh = self.BASELINE_ACH
        self.reward_avg = 0.0
        self.reward_avg_alpha = 0.01
        self.last_surge_event = ""

    def step(self, dt: float = 0.033):
        """Advance all neuromodulator levels by one timestep using first-order decay kinetics.

        Each modulator decays exponentially toward its biological baseline:
            dX/dt = -DECAY_X * (X - BASELINE_X)
        All values are clamped to [MIN_NM, MAX_NM] after each update.

        Args:
            dt: Timestep in seconds (default 0.033 s = 30 Hz control loop)
        """
        self.DA  += -self.DECAY_DA  * (self.DA  - self.BASELINE_DA)  * dt
        self.NE  += -self.DECAY_NE  * (self.NE  - self.BASELINE_NE)  * dt
        self.SHT += -self.DECAY_SHT * (self.SHT - self.BASELINE_SHT) * dt
        self.ACh += -self.DECAY_ACH * (self.ACh - self.BASELINE_ACH) * dt

        self.DA  = np.clip(self.DA,  self.MIN_NM, self.MAX_NM)
        self.NE  = np.clip(self.NE,  self.MIN_NM, self.MAX_NM)
        self.SHT = np.clip(self.SHT, self.MIN_NM, self.MAX_NM)
        self.ACh = np.clip(self.ACh, self.MIN_NM, self.MAX_NM)

    def surge_da(self, amount: float = 0.35):
        """Inject a dopamine surge (reward signal, approach motivation).

        Called on food detection, successful approach, or predicted reward.
        Clamping to MAX_NM is applied on the next step().
        Args:
            amount: DA increase (default 0.35 — moderate reward signal)
        """
        self.DA += amount
        self.last_surge_event = f"DA+{amount:.2f}"

    def surge_ne(self, amount: float = 0.4):
        """Inject a norepinephrine surge (alertness, danger/threat response).

        Called on obstacle detection, boundary breach, or threat proximity.
        High NE also gates theta-mediated plasticity (suppresses RLS updates).
        Args:
            amount: NE increase (default 0.4 — strong alerting signal)
        """
        self.NE += amount
        self.last_surge_event = f"NE+{amount:.2f}"

    def surge_sht(self, amount: float = 0.15):
        """Inject a serotonin surge (satiation, behavioral inhibition, calm).

        Called after eating — rises post-food to reduce further food-seeking urgency.
        High 5-HT reduces precision weight (inhibits sensory attention).
        Args:
            amount: 5-HT increase (default 0.15 — moderate satiation signal)
        """
        self.SHT += amount
        self.last_surge_event = f"5HT+{amount:.2f}"

    def surge_ach(self, amount: float = 0.25):
        """Inject an acetylcholine surge (attention, sensory gain, plasticity).

        Called in novel environments or during active sensing. High ACh boosts
        precision weight and Hebbian grid-to-place learning rate.
        Args:
            amount: ACh increase (default 0.25 — moderate attentional boost)
        """
        self.ACh += amount
        self.last_surge_event = f"ACh+{amount:.2f}"

    def get_precision_weight(self) -> float:
        """Compute the Bayesian precision weight π for sensory input weighting.

        π = π₀ × (1 + γ_ACh × ACh + γ_NE × NE - γ_5HT × 5HT)

        ACh and NE boost sensory precision (sharpen attention).
        5-HT inhibits it (calm/satiated states trust priors more than sensors).

        Returns:
            Precision weight, floored at 0.1 (never fully ignores sensors)
        """
        pi = self.PI_0 * (
            1.0
            + self.GAMMA_ACH * self.ACh
            + self.GAMMA_NE  * self.NE
            - self.GAMMA_SHT * self.SHT
        )
        return max(0.1, pi)

    def get_exploration_noise_scale(self) -> float:
        """Return the exploration noise amplitude σ_η, scaled by NE level.

        High NE (alertness/stress) increases stochastic exploration.
        This is biologically motivated: the locus coeruleus (NE source) gates
        between exploitative (low NE) and exploratory (high NE) behavioral modes.

        Returns:
            Noise scale factor, floored at 0.01 (always some baseline noise)
        """
        return max(0.01, self.NE)

    def get_reward_prediction_error(self) -> float:
        """Compute the dopaminergic Reward Prediction Error (RPE).

        RPE = DA - running_average(DA)

        Positive RPE: DA is higher than expected — better-than-predicted outcome.
        Negative RPE: DA is lower than expected — worse-than-predicted outcome.
        This is the temporal difference signal that gates RLS weight updates.

        Side-effect: updates the exponential running average of DA.

        Returns:
            Scalar RPE (unbounded; typically in [-3.0, +3.0])
        """
        rpe = self.DA - self.reward_avg
        self.reward_avg += self.reward_avg_alpha * (self.DA - self.reward_avg)
        return rpe

    def get_behavioral_mode(self, battery_level: float, food_visible: bool) -> str:
        """
        Determines high-level behavioral mode:
          - EXPLOIT: Food is in camera FOV -> lock on and approach
          - SURVIVE: Battery < 0.15 (critical hunger) and no food visible -> desperate search
          - EXPLORE: Battery OK, no food visible -> search via novelty-seeking + replay blend
        """
        if food_visible:
            return "EXPLOIT"
        elif battery_level < 0.15 or self.NE > 2.0:
            return "SURVIVE"
        else:
            return "EXPLORE"

    def get_hunger_drive(self, battery_level: float) -> float:
        """
        Continuous hunger signal (0.0 = satiated, 1.0 = starving).
        Used to blend replay navigation strength into ALL modes.
        Animals don't suddenly start navigating toward food at a threshold —
        hunger builds continuously and proportionally increases food-seeking behavior.
        """
        return float(np.clip(1.0 - battery_level, 0.0, 1.0))

    def get_replay_blend_weight(self, battery_level: float, max_nav_value: float) -> float:
        """
        How strongly replay navigation should influence motor output.
        Blends hunger drive with how strong the replay signal is.
        Even at full battery, if there's a strong nav gradient, follow it mildly.
        As battery drops, follow it urgently.
        """
        hunger = self.get_hunger_drive(battery_level)
        signal_strength = float(np.clip(max_nav_value / 2.0, 0.0, 1.0))
        # Always some replay influence when signal exists; hunger amplifies it
        return float(np.clip(signal_strength * (0.3 + 0.7 * hunger), 0.0, 1.0))

    def __repr__(self):
        return (f"DA={self.DA:.2f}, NE={self.NE:.2f}, "
                f"5HT={self.SHT:.2f}, ACh={self.ACh:.2f}, "
                f"pi={self.get_precision_weight():.2f}")
