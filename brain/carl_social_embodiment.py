"""
brain/carl_social_embodiment.py
CARL-DX Stage 7: Social Embodiment, Affective Prosody & Epistemic Companion Organ.

Connects internal latent states (Witness Introspection, Endocrine Hormones,
Active Inference Free Energy) to outward non-verbal expressions:
1. Acoustic Prosody & Frequency Modulation (R2-D2 Voice)
2. Photonic Mood Halo (24-bit RGB HSV Display)
3. Somatic Motor Shudder (Kinematic Frustration Dither)
4. Human-Aware Proxemic Deceleration (Ankle Safety Bubble @ 0.35m)
5. 2-DOF Pan-Tilt Visuomotor Gaze Controller (Eye Contact & Ground Inspection)
6. One-Shot HDC Filial Imprinting & Recognition (Show-and-Tell)
7. Social Referencing State Machine (Epistemic Caregiver Query)
8. Bi-Directional Internal Monologue Stream (Live Chatbox Telemetry)

Strictly quarantined under Stage Invariants:
- Zero simulator coordinates in active decision loop.
- No arbitrary canned animations; all outputs are direct continuous functions
  of internal neuromorphic latent states.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import time

class CarlAffectiveTelemetry:
    """
    Translates internal autonomic and cognitive metrics into continuous
    Arousal-Valence space, driving acoustic synthesis, mood glow, and motor dither.
    """
    def __init__(self, f_base: float = 220.0, delta_f: float = 680.0):
        self.f_base = f_base
        self.delta_f = delta_f
        self.last_audio_freq = f_base
        self.last_mood_rgb = (0, 255, 0)
        self.last_mood_label = "CALM"

    def update(
        self,
        witness_distress: float,
        endocrine_cortisol: float,
        g_pragmatic: float,
        g_epistemic: float,
        is_sleeping: bool = False,
        is_stuck: bool = False
    ) -> Dict[str, Any]:
        """
        Computes 1:1 continuous mapping from latent brain states to outward expression.
        """
        # 1. Arousal A in [0, 1]
        arousal = float(np.clip(0.65 * witness_distress + 0.35 * endocrine_cortisol, 0.0, 1.0))
        if is_stuck:
            arousal = max(arousal, 0.85)

        # 2. Valence V in [-1, 1]
        v_raw = 1.20 - g_pragmatic - 0.80 * g_epistemic - 2.5 * witness_distress
        if is_stuck:
            v_raw -= 1.0
        valence = float(np.tanh(v_raw))

        # 3. Acoustic Frequency (Hz)
        if is_sleeping:
            freq_hz = 175.0 + 15.0 * np.sin(time.time() * 1.5)  # Soft breathing oscillation
            mood_label = "SLEEP"
            rgb = (148, 0, 211)  # Pulsing Violet
            shudder_amp = 0.0
            thought = "Deep NREM sleep... consolidating topological memory."
        elif is_stuck or (valence < -0.3 and arousal > 0.6):
            freq_hz = self.f_base + self.delta_f * arousal + 25.0 * np.sin(time.time() * 25.0)  # Agitated jitter
            mood_label = "ALARM"
            rgb = (255, 20, 20)  # Flashing Crimson
            shudder_amp = float(np.clip(0.4 * arousal, 0.1, 0.5))  # Physical wheel tremor
            thought = "Kinematic stall! PFL2 triggering 180° escape pivot."
        elif g_epistemic > 0.55 and valence >= -0.1:
            freq_hz = 600.0 + 800.0 * g_epistemic  # Bright curious chirps
            mood_label = "CURIOUS"
            rgb = (0, 180, 255)  # Cyan
            shudder_amp = 0.0
            thought = f"High novelty detected (Epistemic {g_epistemic:.2f}). Scanning room..."
        elif valence > 0.3:
            freq_hz = self.f_base + 80.0 * valence  # Low rhythmic purr
            mood_label = "CONTENT"
            rgb = (30, 230, 50)  # Vibrant Emerald Green
            shudder_amp = 0.0
            thought = "Navigating smoothly. Homeostatic equilibrium nominal."
        else:
            freq_hz = 350.0 + 150.0 * arousal
            mood_label = "CAUTION"
            rgb = (255, 180, 0)  # Amber
            shudder_amp = 0.0
            thought = "Uncertain path or slippery surface. Moderating velocity."

        self.last_audio_freq = freq_hz
        self.last_mood_rgb = rgb
        self.last_mood_label = mood_label

        return {
            "arousal": arousal,
            "valence": valence,
            "carrier_freq_hz": float(freq_hz),
            "mood_label": mood_label,
            "mood_rgb": rgb,
            "shudder_amplitude": shudder_amp,
            "thought_message": thought
        }


class CarlProxemicController:
    """
    Regulates interpersonal space (Proxemics) based on Edward T. Hall's taxonomy.
    Enforces a strict 0.35m 'Ankle Safety Bubble' to guarantee zero physical contact.
    """
    def __init__(self, d_intimate: float = 0.35, d_personal: float = 1.20, sigma_comfort: float = 0.25):
        self.d_intimate = d_intimate
        self.d_personal = d_personal
        self.sigma_comfort = sigma_comfort

    def compute_approach_velocity(self, current_distance: float, max_v: float = 0.40) -> Tuple[float, str]:
        """
        Computes progressive human-aware deceleration curve:
        - Free approach at max_v when distance > 1.20m
        - Smooth exponential deceleration between 1.20m and 0.35m
        - Complete kinematic halt at 0.35m
        """
        if current_distance <= self.d_intimate:
            return 0.0, "HALTED_SAFE_PROXEMIC_BUBBLE"
        elif current_distance > self.d_personal:
            return max_v, "CRUISING_TOWARDS_HUMAN"
        else:
            # Smooth S-curve deceleration
            ratio = (current_distance - self.d_intimate) / (self.d_personal - self.d_intimate)
            v_cmd = max_v * (ratio ** 1.5)
            return float(np.clip(v_cmd, 0.05, max_v)), "DECELERATING_INTO_PERSONAL_SPACE"

    def compute_head_gaze(self, distance_to_human: float, is_at_feet: bool = False) -> Tuple[float, float]:
        """
        Computes 2-DOF Pan-Tilt angles (pan, tilt in radians).
        When arriving at human feet, tilts camera UP (+0.60 rad / +35°) for eye contact.
        """
        pan = 0.0
        if is_at_feet or distance_to_human <= self.d_intimate + 0.10:
            tilt = 0.61  # +35 degrees looking UP into human face
        else:
            tilt = -0.10  # Slightly angled forward/down for path inspection
        return pan, tilt


class CarlOneShotImprinter:
    """
    2,048-Dimensional Hyperdimensional Computing (HDC) Filial Imprinting Engine.
    Enables one-shot, zero-cloud learning of user, friends, and objects via Show-and-Tell.
    """
    def __init__(self, dim: int = 2048, feat_dim: int = 64, seed: int = 42):
        self.dim = dim
        self.feat_dim = feat_dim
        rng = np.random.RandomState(seed)
        # Static Gaussian projection matrix
        self.proj_matrix = rng.randn(dim, feat_dim)
        # Memory storage: Name -> Bipolar Hypervector
        self.memory: Dict[str, np.ndarray] = {}

    def extract_hypervector(self, feature_vector: np.ndarray) -> np.ndarray:
        """Projects raw 64-D visual features into 2,048-D bipolar vector {-1, +1}."""
        f_norm = feature_vector / (np.linalg.norm(feature_vector) + 1e-8)
        proj = np.dot(self.proj_matrix, f_norm)
        return np.where(proj >= 0, 1.0, -1.0)

    def imprint(self, label: str, feature_vector: np.ndarray) -> Dict[str, Any]:
        """Learns and permanently binds an entity in 1 shot."""
        h_vec = self.extract_hypervector(feature_vector)
        self.memory[label.lower()] = h_vec
        return {
            "status": "IMPRINTED",
            "label": label,
            "stored_units": self.dim,
            "total_entities": len(self.memory)
        }

    def match(self, feature_vector: np.ndarray, threshold: float = 0.70) -> Tuple[Optional[str], float]:
        """
        Queries memory using cosine similarity.
        Returns (best_label, similarity_score).
        """
        if not self.memory:
            return None, 0.0

        q_vec = self.extract_hypervector(feature_vector)
        best_label = None
        best_sim = -1.0

        for label, stored_vec in self.memory.items():
            sim = float(np.dot(q_vec, stored_vec) / self.dim)
            if sim > best_sim:
                best_sim = sim
                best_label = label

        if best_sim >= threshold:
            return best_label, best_sim
        return None, best_sim


class CarlSocialReferencing:
    """
    State machine for child-like Social Referencing.
    When facing high epistemic uncertainty on an obstacle, CARL pauses, looks back at the
    caregiver, emits an inquiry chirp, and waits for affirmative or negative feedback.
    """
    STATE_IDLE = "IDLE"
    STATE_UNCERTAIN = "UNCERTAIN_PAUSE"
    STATE_QUERYING = "QUERYING_CAREGIVER"
    STATE_RESOLVED = "RESOLVED"

    def __init__(self, entropy_threshold: float = 0.75):
        self.entropy_threshold = entropy_threshold
        self.state = self.STATE_IDLE
        self.last_query_time = 0.0

    def evaluate(
        self,
        obstacle_entropy: float,
        user_cue: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes current perception and user feedback.
        user_cue: 'YES' / 'WAVE' (affirmative) or 'NO' / 'PALM' (negative) or None.
        """
        action = "CONTINUE"
        message = ""

        if self.state == self.STATE_IDLE:
            if obstacle_entropy >= self.entropy_threshold:
                self.state = self.STATE_UNCERTAIN
                self.last_query_time = time.time()
                action = "HALT_AND_LOOK_AT_CAREGIVER"
                message = "🤖 CARL: Strange obstacle ahead. Manas, is it safe to proceed?"
        elif self.state == self.STATE_UNCERTAIN:
            if user_cue in ["YES", "WAVE", "APPROVE"]:
                self.state = self.STATE_RESOLVED
                action = "PROCEED_BYPASS"
                message = "🤖 CARL: Affirmative received! Proceeding around obstacle."
            elif user_cue in ["NO", "PALM", "STOP"]:
                self.state = self.STATE_RESOLVED
                action = "RETREAT_PFL2"
                message = "🤖 CARL: Negative received! Marking static hazard and retreating."
            else:
                action = "WAIT_INQUIRY_CHIRP"
                message = "🤖 CARL: [Awaiting confirmation... tilt head, chirp upward]"
        elif self.state == self.STATE_RESOLVED:
            self.state = self.STATE_IDLE
            action = "RESUME_NOMINAL"

        return {
            "state": self.state,
            "action": action,
            "message": message
        }
