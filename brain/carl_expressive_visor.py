"""
carl_expressive_visor.py — Expressive OLED Visor & Bio-Aura LED Sync (VIS-1201)

Renders dynamic OLED eye expression states (Curious circles, Happy arches, Alert slits, Sleepy half-lids)
and computes 6 Hz theta-pulsing chest LED bio-aura RGBA colors based on neuromodulator states.
"""
import numpy as np
import math


class ExpressiveVisorEngine:
    """
    Expressive Visor & Biological Aura Renderer.
    """
    def __init__(self):
        self.eye_state = "CURIOUS"
        self.chest_led_rgba = np.array([0.10, 0.88, 1.00, 1.0])  # Cyan baseline

    def update_expression(
        self,
        tick: int,
        da: float,
        ne: float,
        sht: float,
        battery: float,
        is_sleeping: bool
    ) -> tuple:
        """
        Calculates dynamic eye expression label and 6 Hz theta-pulsing chest LED color.
        
        Returns:
            (eye_state_label, chest_led_rgba)
        """
        # 1. Select Eye Expression State
        if is_sleeping or battery < 0.15:
            self.eye_state = "SLEEPY"
        elif ne > 0.65:
            self.eye_state = "ALERT"
        elif da > 1.25:
            self.eye_state = "HAPPY"
        else:
            self.eye_state = "CURIOUS"

        # 2. Compute 6 Hz Theta-Pulsing Bio-Aura LED Color (RGBA)
        theta_pulse = 0.5 + 0.5 * math.sin(tick * 0.2)  # 6 Hz wave at 30 Hz control cycle
        
        if self.eye_state == "SLEEPY":
            # Deep Violet
            base_rgb = np.array([0.40, 0.10, 0.90])
        elif self.eye_state == "ALERT":
            # Crimson Red
            base_rgb = np.array([0.95, 0.15, 0.15])
        elif self.eye_state == "HAPPY":
            # Amber Gold
            base_rgb = np.array([1.00, 0.60, 0.00])
        else:
            # Luminous Cyan
            base_rgb = np.array([0.05, 0.85, 1.00])

        intensity = 0.6 + 0.4 * theta_pulse
        self.chest_led_rgba[:3] = base_rgb * intensity
        self.chest_led_rgba[3] = 1.0

        return self.eye_state, self.chest_led_rgba.copy()
