"""
brain/carl_homeostatic_core.py — Interoception, Homeostasis & Viability Regulation Engine

Maintains continuous organismic physiological state and drives autonomous self-preservation:
1. Physiological State Vector h(t) = [Energy, Thermal Load, Motor Fatigue, Safety Margin, Uncertainty, Curiosity]
2. Homeostatic Viability Envelope & Target Vector h*
3. Deviation D_h(t) = ||h(t) - h*|| driving endogenous motivation
4. Bio-energetic metabolic dynamics (Joule heating, cooling, energy expenditure, food absorption, fatigue recovery)
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple

@dataclass
class HomeostaticVector:
    energy: float = 1.0          # Metabolic energy reserve [0.0, 1.0] (1.0 = full, 0.0 = starved/depleted)
    thermal_load: float = 0.0    # Actuator/internal thermal load [0.0, 1.0] (0.0 = cool, 1.0 = overheating)
    motor_fatigue: float = 0.0   # Viscoelastic/mechanical fatigue [0.0, 1.0] (0.0 = fresh, 1.0 = exhausted)
    safety_margin: float = 1.0   # Structural safety & stability margin [0.0, 1.0] (1.0 = safe, 0.0 = critical hazard)
    uncertainty: float = 0.5     # Epistemic/world model uncertainty [0.0, 1.0] (0.0 = fully certain, 1.0 = complete unknown)
    curiosity_drive: float = 0.5 # Intrinsic information seeking pressure [0.0, 1.0] (1.0 = high novelty need)


class CarlHomeostaticCore:
    """
    Interoceptive and homeostatic regulatory core.
    """
    def __init__(self, dt: float = 0.0333):
        self.dt = dt
        
        # Target homeostatic state h*
        self.target = HomeostaticVector(
            energy=1.0,
            thermal_load=0.0,
            motor_fatigue=0.0,
            safety_margin=1.0,
            uncertainty=0.1,
            curiosity_drive=0.4
        )
        
        # Current physiological state h(t)
        self.state = HomeostaticVector()
        
        # Biological constants
        self.basal_metabolic_rate = 0.0008  # Energy drain per tick just being active
        self.motor_power_coefficient = 0.00015 # Energy drain per Watt-second
        self.thermal_joule_coefficient = 0.0005 # Heating from torque
        self.thermal_cooling_rate = 0.015    # Newton cooling coefficient
        self.fatigue_rate = 0.0004           # Fatigue accumulation under load
        self.fatigue_recovery_rate = 0.008   # Recovery rate when resting
        self.boredom_accumulation_rate = 0.003 # Curiosity pressure growth when idle
        
        # Weights for homeostatic deviation D_h
        self.weights = {
            "energy": 3.0,
            "thermal_load": 2.5,
            "motor_fatigue": 1.5,
            "safety_margin": 4.0,
            "uncertainty": 1.2,
            "curiosity_drive": 1.0
        }
        
        # Telemetry history
        self.deviation_history = []

    def update_interoception(self, sensory_state, food_eaten: bool = False, prediction_error: float = 0.0) -> Dict[str, Any]:
        """
        Updates internal physiological variables based on physical effort, sensor telemetry, and interactions.
        """
        # 1. Mechanical Work & Power Output: P = |tau_L * w_L| + |tau_R * w_R| + joint torques
        power_output = (
            abs(sensory_state.tau_wheel_L * sensory_state.wheel_w_L) +
            abs(sensory_state.tau_wheel_R * sensory_state.wheel_w_R) +
            abs(sensory_state.tau_hip_pitch) + abs(sensory_state.tau_neck)
        )
        
        # 2. Energy Dynamics
        energy_drain = (self.basal_metabolic_rate + self.motor_power_coefficient * power_output) * self.dt
        self.state.energy = max(0.0, self.state.energy - energy_drain)
        if food_eaten:
            self.state.energy = min(1.0, self.state.energy + 0.40) # Metabolic nourishment from target beacon
            
        # 3. Thermal Dynamics: dT/dt = k_joule * tau^2 - gamma_cooling * T
        tau_sq = sensory_state.tau_wheel_L**2 + sensory_state.tau_wheel_R**2
        dT = (self.thermal_joule_coefficient * tau_sq - self.thermal_cooling_rate * self.state.thermal_load) * self.dt
        self.state.thermal_load = float(np.clip(self.state.thermal_load + dT, 0.0, 1.0))
        
        # 4. Motor Fatigue Dynamics
        if power_output > 2.0:
            self.state.motor_fatigue = min(1.0, self.state.motor_fatigue + self.fatigue_rate * power_output * self.dt)
        else:
            self.state.motor_fatigue = max(0.0, self.state.motor_fatigue - self.fatigue_recovery_rate * self.dt)
            
        # 5. Safety Margin Dynamics (function of obstacle clearance and tilt stability)
        tilt_magnitude = math.sqrt(sensory_state.roll**2 + sensory_state.pitch**2)
        tilt_penalty = np.clip(tilt_magnitude / math.radians(15.0), 0.0, 1.0)
        proximity_penalty = np.clip((0.6 - sensory_state.min_obstacle_dist) / 0.6, 0.0, 1.0) if sensory_state.min_obstacle_dist < 0.6 else 0.0
        wall_penalty = 1.0 if sensory_state.ncon > 4 else 0.0
        
        target_safety = 1.0 - (0.4 * tilt_penalty + 0.4 * proximity_penalty + 0.2 * wall_penalty)
        self.state.safety_margin = float(np.clip(0.8 * self.state.safety_margin + 0.2 * target_safety, 0.0, 1.0))
        
        # 6. Epistemic Uncertainty (reduced by sensory observations and low prediction error)
        self.state.uncertainty = float(np.clip(0.95 * self.state.uncertainty + 0.05 * np.clip(prediction_error, 0.0, 1.0), 0.05, 1.0))
        
        # 7. Curiosity / Novelty Drive (grows during stationary lack of stimuli, satisfied by new experiences)
        if sensory_state.speed < 0.05 and prediction_error < 0.05:
            self.state.curiosity_drive = min(1.0, self.state.curiosity_drive + self.boredom_accumulation_rate * self.dt)
        else:
            self.state.curiosity_drive = max(0.1, self.state.curiosity_drive - 0.02 * (sensory_state.speed + prediction_error) * self.dt)
            
        # 8. Compute Total Homeostatic Deviation D_h(t)
        dev = (
            self.weights["energy"] * (self.target.energy - self.state.energy)**2 +
            self.weights["thermal_load"] * (self.state.thermal_load - self.target.thermal_load)**2 +
            self.weights["motor_fatigue"] * (self.state.motor_fatigue - self.target.motor_fatigue)**2 +
            self.weights["safety_margin"] * (self.target.safety_margin - self.state.safety_margin)**2 +
            self.weights["uncertainty"] * (self.state.uncertainty - self.target.uncertainty)**2 +
            self.weights["curiosity_drive"] * (self.state.curiosity_drive - self.target.curiosity_drive)**2
        )
        self.deviation_history.append(dev)
        
        # 9. Compute Dominant Need / Drive Vector
        needs = {
            "SEEK_ENERGY": self.weights["energy"] * (self.target.energy - self.state.energy),
            "COOL_MOTORS": self.weights["thermal_load"] * self.state.thermal_load,
            "REST_FATIGUE": self.weights["motor_fatigue"] * self.state.motor_fatigue,
            "RESTORE_SAFETY": self.weights["safety_margin"] * (1.0 - self.state.safety_margin),
            "REDUCE_UNCERTAINTY": self.weights["uncertainty"] * self.state.uncertainty,
            "EXPLORE_NOVELTY": self.weights["curiosity_drive"] * self.state.curiosity_drive
        }
        dominant_need = max(needs, key=needs.get)
        
        return {
            "state": self.state,
            "homeostatic_deviation": dev,
            "power_output_watts": power_output,
            "needs": needs,
            "dominant_need": dominant_need,
            "is_viable": self.state.energy > 0.05 and self.state.thermal_load < 0.90 and self.state.safety_margin > 0.15
        }
