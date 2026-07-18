"""
carl_reflex.py — Spiking Neural Network LIF Obstacle Avoidance Layer (END-205)

Implements Leaky Integrate-and-Fire (LIF) reflex mechanics.
Uses a differential steering connectivity profile:
  - Obstacles on the left excite the left-turn reflex (slowing the left wheel, speeding up the right).
  - Obstacles on the right excite the right-turn reflex (slowing the right wheel, speeding up the left).
  - If a front collision is imminent (d < 0.35m), triggers a backup-and-spin sequence to prevent getting stuck.
"""
import math
import numpy as np


class SpikingReflexLayer:
    """
    Leaky Integrate-and-Fire (LIF) obstacle avoidance reflex layer.
    Outputs differential wheel speeds to steer CARL away from obstacles.
    """
    def __init__(self, num_sensors=24, num_motor_neurons=2):
        self.num_sensors = num_sensors
        self.num_motors = num_motor_neurons  # [0]: Turn Left, [1]: Turn Right

        self.V = np.zeros(self.num_motors)
        self.V_th = 1.0
        self.tau_m = 0.02  # 20 ms membrane time constant
        self.dt = 0.033    # 30 Hz control cycle

        # Set up connections:
        # We map the 24 LiDAR ray angles to steer weights.
        # Motor 0 = Turn Left (slows left wheel, speeds up right wheel)
        # Motor 1 = Turn Right (slows right wheel, speeds up left wheel)
        self.w = np.zeros((self.num_motors, self.num_sensors))
        angles = np.linspace(-np.pi, np.pi, num_sensors, endpoint=False)

        for j in range(num_sensors):
            a = angles[j]
            # Front sector is roughly [-pi/2, pi/2]
            if -np.pi/2 <= a <= np.pi/2:
                # If obstacle is on front-right (a < 0), excite Turn Left (0)
                if a < 0:
                    self.w[0, j] = 3.0 * (1.0 - abs(a) / (np.pi/2))
                # If obstacle is on front-left (a > 0), excite Turn Right (1)
                elif a > 0:
                    self.w[1, j] = 3.0 * (1.0 - a / (np.pi/2))
                # Directly in front (a == 0) excites both equally to trigger reverse
                else:
                    self.w[0, j] = 1.8
                    self.w[1, j] = 2.2

        # R-STDP variables
        self.trace_pre = np.zeros(self.num_sensors)
        self.trace_post = np.zeros(self.num_motors)
        self.eligibility = np.zeros((self.num_motors, self.num_sensors))

        self.tau_stdp = 0.02
        self.tau_e = 0.1
        self.eta_stdp = 0.01

        self.pre_decay = math.exp(-self.dt / self.tau_stdp)
        self.post_decay = math.exp(-self.dt / self.tau_stdp)
        self.elig_decay = math.exp(-self.dt / self.tau_e)
        self.mem_decay = math.exp(-self.dt / self.tau_m)

        # Output speeds
        self.reflex_outputs = np.zeros(2)  # [speed_left_delta, speed_right_delta]
        self.tau_motor = 0.1
        self.motor_decay = math.exp(-self.dt / self.tau_motor)
        self.backup_timer = 0
        self.backup_spin_dir = 1.0

    def step(self, sensor_dists: np.ndarray, reservoir_bias: np.ndarray, da: float, food_dist: float = 99.0) -> np.ndarray:
        """
        Step SNN reflex. Returns [left_speed_delta, right_speed_delta].
        """
        spikes_pre = np.zeros(self.num_sensors)
        nu_max = 100.0
        
        # Lower SNN warning and backup thresholds globally to fit narrow 1.0m-1.2m corridors
        # Physical wall contact occurs at ~0.23m, so we must trigger backups above that boundary.
        d_trigger = 0.45
        collision_limit = 0.28
        if food_dist < 1.0:
            d_trigger = 0.32      # even lower near food to allow close-range targeting
            collision_limit = 0.20

        # Check if direct frontal collision is imminent (wider sector check)
        min_front_dist = np.min(sensor_dists[9:15])
        imminent_collision = min_front_dist < collision_limit

        # Check if rear collision is imminent
        min_rear_dist = min(sensor_dists[0], sensor_dists[1], sensor_dists[23])
        imminent_rear_collision = min_rear_dist < 0.25

        # Trigger backup timer and select clear path on new frontal collision
        if imminent_collision and self.backup_timer == 0:
            self.backup_timer = 20  # Back up for 20 ticks (~0.6 seconds)
            # Check average clearance of front-left (6:12) vs front-right (12:18)
            left_clear = np.mean(sensor_dists[6:12])
            right_clear = np.mean(sensor_dists[12:18])
            self.backup_spin_dir = 1.0 if left_clear > right_clear else -1.0

        for j in range(self.num_sensors):
            d = sensor_dists[j]
            if d < d_trigger:
                p = nu_max * (1.0 - d / d_trigger) * self.dt
                if np.random.rand() < min(1.0, p):
                    spikes_pre[j] = 1.0

        # LIF integration
        current_inputs = np.dot(self.w, spikes_pre) + reservoir_bias
        self.V = self.V * self.mem_decay + current_inputs

        spikes_post = np.zeros(self.num_motors)
        for i in range(self.num_motors):
            if self.V[i] >= self.V_th:
                spikes_post[i] = 1.0
                self.V[i] = 0.0  # reset

        # Decaying old outputs
        self.reflex_outputs *= self.motor_decay

        # Dynamic reflex strength: highly aggressive during exploration, suppressed close to food
        reflex_strength = 5.0
        clamp_limit = 6.0
        if food_dist < 1.2:
            reflex_strength = 1.0
            clamp_limit = 1.5

        # Apply differential speeds based on post-synaptic firing:
        if spikes_post[0] > 0:
            self.reflex_outputs[0] -= reflex_strength
            self.reflex_outputs[1] += reflex_strength

        # Motor 1 fires (Turn Right) -> accelerate left wheel, reverse/slow right wheel
        if spikes_post[1] > 0:
            self.reflex_outputs[0] += reflex_strength
            self.reflex_outputs[1] -= reflex_strength

        # Emergency overrides with backup timer
        if self.backup_timer > 0:
            self.backup_timer -= 1
            if imminent_rear_collision:
                # Blocked both front and back: Spin in place to escape in clear direction
                self.reflex_outputs[0] = 3.5 * self.backup_spin_dir
                self.reflex_outputs[1] = -3.5 * self.backup_spin_dir
            else:
                # Gentle backup and swing front in the clear direction
                if self.backup_spin_dir > 0:
                    self.reflex_outputs[0] = -4.5
                    self.reflex_outputs[1] = -1.5
                else:
                    self.reflex_outputs[0] = -1.5
                    self.reflex_outputs[1] = -4.5
        elif imminent_rear_collision:
            # Blocked only from behind: Push forward
            self.reflex_outputs[0] = 3.0
            self.reflex_outputs[1] = 3.0

        # Clamp accumulated reflex output dynamically
        self.reflex_outputs = np.clip(self.reflex_outputs, -clamp_limit, clamp_limit)

        # R-STDP traces
        self.trace_pre = self.trace_pre * self.pre_decay + spikes_pre
        self.trace_post = self.trace_post * self.post_decay + spikes_post

        for i in range(self.num_motors):
            for j in range(self.num_sensors):
                self.eligibility[i, j] = (self.eligibility[i, j] * self.elig_decay +
                                          (self.trace_pre[j] * spikes_post[i] -
                                           self.trace_post[i] * spikes_pre[j]))

        da_error = da - 1.0
        self.w += self.eta_stdp * self.eligibility * da_error
        self.w = np.clip(self.w, -3.0, 3.0)

        return self.reflex_outputs.copy()
