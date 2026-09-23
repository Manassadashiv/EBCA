"""
carl_audio_synth.py — Procedural Emotional Audio Synthesizer for CARL-DX

Generates lightweight, real-time Wall-E / R2-D2 style chattering, chirps, and trills
mapped directly to internal neuro-endocrine transitions:
- Joy / Food Eaten: Ascending celebratory multi-tone trill
- Curiosity: Inquisitive rising harmonic warble
- Startle / Threat: Rapid high-frequency frequency-modulated chirrup
- Anger / Frustration: Low frequency warning rumble / growl pulse
- Low Battery: Gentle descending sleepy murmur
"""

import os
import math
import wave
import struct
import tempfile
import threading
import numpy as np

# Audio playback handling (Windows winsound fallback or non-blocking worker)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class EmotionalAudioSynthesizer:
    """
    Thread-safe, non-blocking procedural audio generator for emotional companion vocalizations.
    """
    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        self.sound_cache = {}
        self.lock = threading.Lock()
        self._precompute_sounds()

    def _generate_wav_bytes(self, samples: np.ndarray) -> bytes:
        """Encodes float array [-1.0, 1.0] into 16-bit PCM WAV bytes."""
        samples_int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
        import io
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sr)
            wf.writeframes(samples_int16.tobytes())
        return buf.getvalue()

    def _precompute_sounds(self):
        """Synthesizes procedural wave patterns for all emotional states."""
        # 1. Joy Trill (Ascending happy arpeggio: 600 -> 900 -> 1400 Hz)
        t = np.linspace(0, 0.25, int(self.sr * 0.25), endpoint=False)
        freq_env = np.linspace(600, 1400, len(t))
        joy_samples = 0.5 * np.sin(2 * np.pi * freq_env * t) * (1.0 - t / 0.25)
        # Add soft harmonic
        joy_samples += 0.25 * np.sin(4 * np.pi * freq_env * t) * (1.0 - t / 0.25)
        self.sound_cache["joy"] = self._generate_wav_bytes(joy_samples)

        # 2. Curious Chirp (Two-tone inquisitive warble: 520 -> 720 Hz)
        t = np.linspace(0, 0.18, int(self.sr * 0.18), endpoint=False)
        curious_samples = 0.45 * np.sin(2 * np.pi * (520 + 200 * t) * t) * np.sin(np.pi * t / 0.18)
        self.sound_cache["curious"] = self._generate_wav_bytes(curious_samples)

        # 3. Startle Alarm (Sharp descending alert: 1500 -> 800 Hz)
        t = np.linspace(0, 0.12, int(self.sr * 0.12), endpoint=False)
        startle_samples = 0.6 * np.sin(2 * np.pi * (1500 - 700 * (t / 0.12)**2) * t)
        self.sound_cache["startle"] = self._generate_wav_bytes(startle_samples)

        # 4. Anger / Frustration Rumble (Low square-wave modulated growl: 140-180 Hz)
        t = np.linspace(0, 0.30, int(self.sr * 0.30), endpoint=False)
        growl = 0.5 * np.sign(np.sin(2 * np.pi * 160 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 25 * t))
        self.sound_cache["anger"] = self._generate_wav_bytes(growl)

        # 5. Low Battery / Sleepy (Descending soft tone: 380 -> 220 Hz)
        t = np.linspace(0, 0.35, int(self.sr * 0.35), endpoint=False)
        tired = 0.4 * np.sin(2 * np.pi * np.linspace(380, 220, len(t)) * t) * (1.0 - t / 0.35)
        self.sound_cache["tired"] = self._generate_wav_bytes(tired)

    def play(self, sound_name: str):
        """Non-blocking audio trigger."""
        if sound_name not in self.sound_cache:
            return

        def _play_async():
            if HAS_WINSOUND:
                try:
                    winsound.PlaySound(
                        self.sound_cache[sound_name],
                        winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                    )
                except Exception:
                    pass

        threading.Thread(target=_play_async, daemon=True).start()

    def trigger_endocrine_voice(self, da: float, ne: float, sht: float, ach: float, battery: float):
        """Automatically selects vocalization based on active neuro-endocrine dynamics."""
        if da > 1.25:
            self.play("joy")
        elif ne > 0.50:
            self.play("startle")
        elif sht < 0.25 and ne > 0.35:
            self.play("anger")
        elif ach > 0.85:
            self.play("curious")
        elif battery < 0.20:
            self.play("tired")
