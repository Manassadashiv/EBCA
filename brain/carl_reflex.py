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
                    self.w[0, j] = 2.0
                    self.w[1, j] = 2.0

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
        
        # Proactive wall evasion trigger (1.20m) and proactive emergency backup (0.55m)
        d_trigger = 1.20
        collision_limit = 0.55

        # Check if direct frontal collision is imminent (wider sector check)
        min_front_dist = np.min(sensor_dists[9:15])
        imminent_collision = min_front_dist < collision_limit

        # Check if rear collision is imminent
        min_rear_dist = min(sensor_dists[0], sensor_dists[1], sensor_dists[23])
        imminent_rear_collision = min_rear_dist < 0.30

        # Trigger backup timer and select clear path on new frontal collision
        if imminent_collision and self.backup_timer == 0:
            self.backup_timer = 25  # Back up for 25 ticks (~0.8 seconds)
            # Check average clearance of front-left (6:12) vs front-right (12:18)
            left_clear = np.mean(sensor_dists[6:12])
            right_clear = np.mean(sensor_dists[12:18])
            self.backup_spin_dir = 1.0 if left_clear > right_clear else -1.0

        # Potential-field continuous repelling force for smooth proactive 1.2m evasion
        left_sector = np.mean(sensor_dists[6:12])   # Front-Left
        right_sector = np.mean(sensor_dists[12:18]) # Front-Right
        front_min = np.min(sensor_dists[9:15])       # Direct Front

        for j in range(self.num_sensors):
            d = sensor_dists[j]
            if d < d_trigger:
                p = nu_max * (1.0 - d / d_trigger) * self.dt
                if np.random.rand() < min(1.0, p):
                    spikes_pre[j] = 1.0

        # LIF integration (membrane tau = 0.1s for smoother integration)
        self.mem_decay = math.exp(-self.dt / 0.1)
        current_inputs = np.dot(self.w, spikes_pre) + reservoir_bias
        self.V = self.V * self.mem_decay + current_inputs

        spikes_post = np.zeros(self.num_motors)
        for i in range(self.num_motors):
            if self.V[i] >= self.V_th:
                spikes_post[i] = 1.0
                self.V[i] = 0.0  # reset

        # Decaying old outputs
        self.reflex_outputs *= self.motor_decay

        # Proactive potential field calculation:
        if front_min < 1.20:
            turn_intensity = (1.20 - front_min) / 1.20 * 12.0
            if left_sector < right_sector:
                # Wall is more to the left, steer right
                self.reflex_outputs[0] += turn_intensity
                self.reflex_outputs[1] -= turn_intensity
            else:
                # Wall is more to the right, steer left
                self.reflex_outputs[0] -= turn_intensity
                self.reflex_outputs[1] += turn_intensity

        # Apply differential1.2m SNN spikes if active
        reflex_strength = 6.0
        clamp_limit = 18.0

        if spikes_post[0] > 0:
            self.reflex_outputs[0] -= reflex_strength
            self.reflex_outputs[1] += reflex_strength

        if spikes_post[1] > 0:
            self.reflex_outputs[0] += reflex_strength
            self.reflex_outputs[1] -= reflex_strength

        # Emergency overrides with backup timer
        if self.backup_timer > 0:
            self.backup_timer -= 1
            if imminent_rear_collision:
                # Blocked both front and back: Spin in place
                self.reflex_outputs[0] = 10.0 * self.backup_spin_dir
                self.reflex_outputs[1] = -10.0 * self.backup_spin_dir
            else:
                # Gentle backup and swing
                if self.backup_spin_dir > 0:
                    self.reflex_outputs[0] = -12.0
                    self.reflex_outputs[1] = -4.0
                else:
                    self.reflex_outputs[0] = -4.0
                    self.reflex_outputs[1] = -12.0
        elif imminent_rear_collision:
            self.reflex_outputs[0] = 8.0
            self.reflex_outputs[1] = 8.0

        # Clamp accumulated reflex output
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
