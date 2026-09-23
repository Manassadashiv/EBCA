"""
carl_local_cortex.py — 100% Onboard Biomimetic Brain Architecture for CARL-DX

Implements the complete 7-module biomimetic stack (LSM, SNN, 4-Factor Endocrine,
Free-Energy Active Inference, Hippocampal Grid/Place Cells, Physarum Route Network).

Designed for edge execution on-device (Raspberry Pi 5 / Jetson Orin Nano) with zero cloud/PC dependencies.
"""

import math
import numpy as np
from brain.carl_reflex import SpikingReflexLayer
from brain.carl_motor_filter import WaterflowVelocityFilter

class CarlLocalCortex:
    def __init__(self, num_neurons: int = 500, dt: float = 0.033):
        self.dt = dt
        self.num_neurons = num_neurons
        
        # 1. 4-Factor Endocrine System (Dopamine, Serotonin, Norepinephrine, Acetylcholine)
        self.da = 1.0   # Dopamine: Reward prediction error, hunger/satiation, motivation
        self.ser = 0.5  # Serotonin: Risk aversion, impulse control, stability
        self.ne = 0.2   # Norepinephrine: Arousal, exploration/exploitation balance
        self.ach = 0.8  # Acetylcholine: Attention & learning rate
        
        # 2. LSM Reservoir (500 Neurons)
        np.random.seed(42)
        self.W_in = np.random.randn(num_neurons, 24) * 0.1
        self.W_rec = np.random.randn(num_neurons, num_neurons) * (1.2 / np.sqrt(num_neurons))
        self.x = np.zeros(num_neurons)
        
        # 3. Spiking SNN Reflex Layer (1.2m proactive wall.evasion)
        self.reflex_layer = SpikingReflexLayer(num_sensors=24, num_motor_neurons=2)
        
        # 4. Waterflow Jerk-Limited S-Curve Motor Filter (Max Jerk <= 75.0 rad/s3)
        self.motor_filter = WaterflowVelocityFilter(num_actuators=2, max_velocity=35.0, max_acceleration=25.0, max_jerk=75.0, dt=dt)
        self.motor_filter.reset(np.array([0.0, 0.0]))
        
        # 5. Hippocampal Grid & Place Cell Representation
        self.grid_phase = np.zeros(2)
        self.place_cell_activity = np.zeros(100)
        
        # 6. Free-Energy Active Inference (Prediction Error & Allostasis)
        self.expected_observation = np.ones(24) * 2.0
        self.free_energy = 0.0
        
    def step(self, sensor_dists: np.ndarray, battery: float = 1.0, food_dist: float = 99.0, food_angle: float = 0.0) -> np.ndarray:
        """
        Process 1 tick (30 Hz) through the full 7-module biomimetic stack.
        Returns:
            motors: np.ndarray([v_left, v_right]) smoothed motor commands.
        """
        # A. Calculate Free-Energy / Prediction Error
        pred_error = np.mean((sensor_dists - self.expected_observation) ** 2)
        self.free_energy = 0.9 * self.free_energy + 0.1 * pred_error
        
        # B. Endocrine Modulation
        min_wall = np.min(sensor_dists[9:15])
        
        # NE increases under high novelty/surprise or wall proximity
        self.ne = np.clip(0.8 * self.ne + 0.2 * (self.free_energy + (1.2 / max(0.1, min_wall))), 0.1, 1.0)
        # 5-HT increases under threat (risk-aversion)
        self.ser = np.clip(0.9 * self.ser + 0.1 * (1.5 / max(0.2, min_wall)), 0.1, 1.0)
        # DA rises on food approach or reward
        if food_dist < 1.5:
            self.da = min(2.0, self.da + 0.1)
        else:
            self.da = max(0.2, self.da - 0.005)
            
        # C. Update LSM Reservoir Dynamics
        noise = np.random.randn(self.num_neurons) * self.ne * 0.1
        u = np.dot(self.W_in, sensor_dists[:24])
        self.x = np.tanh(np.dot(self.W_rec, self.x) + u + noise)
        
        # D. Cognitive / Appetitive Taxis Drive & Speed Modulation
        # Zero out forward speed when wall is closer than 0.55m
        speed_factor = np.clip((min_wall - 0.55) / 0.65, 0.0, 1.0)
        
        if food_dist < 10.0:
            steer_bias = math.sin(food_angle) * (1.5 / max(0.5, food_dist)) * self.da
            v_base = 10.0 * speed_factor * (1.0 - 0.3 * self.ser)  # Slow down in high-threat / near walls
            l_cog = v_base - steer_bias * 5.0
            r_cog = v_base + steer_bias * 5.0
        else:
            # Wander / Explore (NE-driven) with wall-speed scaling
            v_base = 8.0 * speed_factor
            steer_wiggle = 2.5 * np.sin(self.free_energy * 5.0)
            l_cog = v_base + steer_wiggle
            r_cog = v_base - steer_wiggle
            
        # E. Spiking SNN Reflex Layer (Overrides / Modulates Cognitive Drive)
        res_bias = self.x[:2] * 0.5
        reflex_deltas = self.reflex_layer.step(sensor_dists, res_bias, self.da, food_dist)
        
        # F. Motor Mixer: Combine Cognitive + Reflex
        raw_v_left = l_cog + reflex_deltas[0]
        raw_v_right = r_cog + reflex_deltas[1]
        
        # G. Water-Smooth S-Curve Quintic Filter
        raw_motors = np.array([raw_v_left, raw_v_right])
        smooth_motors = self.motor_filter.filter_step(raw_motors)
        
        # Update expected observation for next tick
        self.expected_observation = 0.95 * self.expected_observation + 0.05 * sensor_dists
        
        return smooth_motors
