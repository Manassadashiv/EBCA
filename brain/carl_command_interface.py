"""
carl_command_interface.py — Natural Language Command Parser & Interactive Laser Pointer

Enables:
1. Natural language instruction parsing ("find food", "follow laser", "dance", "sleep", "guard", "jump").
2. Dynamic target tracking (following an interactive mouse laser pointer).
3. Biasing high-level neuro-endocrine and behavioral setpoints based on user intent.
"""

import math
import queue
import numpy as np
from typing import Optional, Tuple, Dict, Any


class CommandInterface:
    """
    Parses natural language directives and manages interactive laser pointer tracking.
    """
    def __init__(self):
        self.command_queue = queue.Queue()
        self.active_override: Optional[str] = None
        self.override_timer: int = 0
        self.laser_pos: Optional[Tuple[float, float]] = None
        self.laser_active: bool = False

    def send_command(self, text: str):
        """Dispatches a natural language directive string into the agent's cognition."""
        clean_text = text.strip().lower()
        print(f"[USER-COMMAND] Received directive: '{text}'")
        self.command_queue.put(clean_text)

    def set_laser_target(self, x: float, y: float, active: bool = True):
        """Updates the interactive mouse laser pointer coordinate."""
        self.laser_pos = (float(x), float(y))
        self.laser_active = active

    def step(self) -> Dict[str, Any]:
        """
        Processes pending commands and returns active behavioral biases.
        """
        # Drain command queue
        while not self.command_queue.empty():
            cmd = self.command_queue.get_nowait()
            if any(k in cmd for k in ["food", "forage", "eat", "hungry"]):
                self.active_override = "SEEK_FOOD"
                self.override_timer = 150  # ~5 seconds
            elif any(k in cmd for k in ["follow", "laser", "chase", "come"]):
                self.active_override = "FOLLOW_LASER"
                self.override_timer = 200
            elif any(k in cmd for k in ["dance", "celebrate", "happy", "wiggle"]):
                self.active_override = "CELEBRATE"
                self.override_timer = 30
            elif any(k in cmd for k in ["sleep", "rest", "nap"]):
                self.active_override = "SLEEP"
                self.override_timer = 300
            elif any(k in cmd for k in ["guard", "angry", "alert", "threat"]):
                self.active_override = "GUARD"
                self.override_timer = 120
            elif any(k in cmd for k in ["jump", "hop", "pop"]):
                self.active_override = "TORQUE_POP"
                self.override_timer = 15

        if self.override_timer > 0:
            self.override_timer -= 1
            if self.override_timer == 0:
                self.active_override = None

        return {
            "override": self.active_override,
            "laser_pos": self.laser_pos if self.laser_active else None,
            "laser_active": self.laser_active
        }
