"""
brain/p1_integrate/carl_p1_integrate_agent.py — Audited CARL-DX P1 Biological Plasticity Agent

Integrates:
1. 1024-Neuron Recurrent Echo State Reservoir (spectral radius 0.95, leak tau 0.10s)
2. Rate-Coded Rectified Biological Firing Rates: r(t) = max(0, tanh(x(t))) in [0, 1]
3. Three-Factor STDP Synaptic Plasticity Engine (Pre-Post Eligibility + Noradrenaline + Valence)
4. Grounded Hazard Readout: Q_hazard(a_k) = tanh(max(0, W_hazard[:, k]^T * r * 0.05))
5. Active Free-Energy Kinematic Action Selection with Tangent Flank Affordance & Heading Alignment
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent


class CarlP1IntegrateAgent:
    """
    Audited P1-Integrate Autonomous Cyber-Organism Agent.
    """

    def __init__(
        self,
        dt: float = 0.0333,
        reservoir_size: int = 1024,
        spectral_radius: float = 0.95,
        reservoir_sparsity: float = 0.15,
        reservoir_tau: float = 0.10,
        mode: str = "THREE_FACTOR_STDP",  # "BASELINE", "RESERVOIR_ONLY", "TWO_FACTOR_STDP", "THREE_FACTOR_STDP", "SCRAMBLED"
        stdp_lr: float = 0.08,
        stdp_tau_e: float = 0.80,        # 800 ms eligibility time constant
        stdp_tau_trace: float = 0.040,   # 40 ms spike trace time constant
        hazard_weight: float = 180.0,    # Weight of learned hazard in EFE
        use_reservoir: bool = True,
        use_neuromodulation: bool = True,
        use_learned_hazard: bool = True,
        seed: int = 42
    ):
        self.dt = dt
        self.mode = mode
        self.N = reservoir_size
        self.M = 22  # Input feature dimension
        self.use_reservoir = use_reservoir
        self.use_neuromodulation = use_neuromodulation
        self.use_learned_hazard = use_learned_hazard
        self.stdp_lr = stdp_lr
        self.stdp_tau_e = stdp_tau_e
        self.stdp_tau_trace = stdp_tau_trace
        self.hazard_weight = hazard_weight
        self.seed = seed

        # Underlying hardware and kinematics interface
        self.base_agent = CarlAutonomousOrganismAgent(dt=self.dt, enable_memory=False)

        # 7 Discrete Action Primitives
        self.candidate_actions = {
            "STRAIGHT_FORWARD": {"cmd": np.array([4.5, 4.5]), "curv": 0.00, "v": 0.225},
            "CURVE_LEFT_GENTLE": {"cmd": np.array([3.8, 5.2]), "curv": 0.70, "v": 0.225},
            "CURVE_LEFT_SHARP": {"cmd": np.array([2.5, 6.5]), "curv": 1.80, "v": 0.225},
            "SWERVE_LEFT": {"cmd": np.array([2.0, 7.0]), "curv": 2.20, "v": 0.225},
            "CURVE_RIGHT_GENTLE": {"cmd": np.array([5.2, 3.8]), "curv": -0.70, "v": 0.225},
            "CURVE_RIGHT_SHARP": {"cmd": np.array([6.5, 2.5]), "curv": -1.80, "v": 0.225},
            "SWERVE_RIGHT": {"cmd": np.array([7.0, 2.0]), "curv": -2.20, "v": 0.225}
        }
        self.action_names = list(self.candidate_actions.keys())
        self.K = len(self.action_names)
        self.action_to_idx = {name: idx for idx, name in enumerate(self.action_names)}

        # 1. Initialize 1024-Neuron Recurrent Reservoir
        rng = np.random.RandomState(seed)
        self.W_in = rng.randn(self.N, self.M) * 0.10
        W_raw = rng.randn(self.N, self.N)
        mask = (rng.rand(self.N, self.N) < reservoir_sparsity).astype(float)
        W_raw *= mask

        # Power iteration spectral radius scaling
        v = rng.randn(self.N)
        v /= np.linalg.norm(v) + 1e-12
        for _ in range(25):
            v = W_raw @ v
            v /= np.linalg.norm(v) + 1e-12
        curr_rad = float(np.abs(v @ (W_raw @ v)))
        if curr_rad > 1e-6:
            self.W_res = W_raw * (spectral_radius / curr_rad)
        else:
            self.W_res = W_raw

        self.tau_res = reservoir_tau
        self.x = np.zeros(self.N, dtype=float)

        # 2. Plastic Hazard Readout Weights W_hazard [N x K]
        self.W_hazard = np.zeros((self.N, self.K), dtype=float)
        self.W_initial = np.copy(self.W_hazard)

        # 3. STDP Traces
        self.trace_pre = np.zeros(self.N, dtype=float)
        self.trace_post = np.zeros(self.K, dtype=float)
        self.E = np.zeros((self.N, self.K), dtype=float)

        # Latched Flank Waypoint for clean circumnavigation
        self.latched_flank = None

        # Telemetry & Diagnostics
        self.tick = 0
        self.last_surprise = 0.0
        self.last_valence = 0.0
        self.last_dw = np.zeros((self.N, self.K), dtype=float)
        self.cumulative_abs_dw = 0.0
        self.ltp_count = 0
        self.ltd_count = 0
        self.last_hazard_predictions = np.zeros(self.K, dtype=float)
        self.history_x = []
        self.history_w = []

    def reset_state_traces(self):
        """Resets dynamic temporal states between episodes while preserving learned W_hazard."""
        self.x = np.zeros(self.N, dtype=float)
        self.E = np.zeros((self.N, self.K), dtype=float)
        self.trace_pre = np.zeros(self.N, dtype=float)
        self.trace_post = np.zeros(self.K, dtype=float)
        self.latched_flank = None
        self.tick = 0

    def encode_sensors(self, sensory, target_coords: Tuple[float, float]) -> np.ndarray:
        """Encodes 22-dimensional continuous sensory vector in [0, 1]."""
        u = np.zeros(self.M, dtype=float)
        # 0: Forward Speed
        u[0] = np.clip(sensory.speed / 0.40, 0.0, 1.0)
        # 1: Yaw Rate
        yaw_rate = (sensory.wheel_w_R - sensory.wheel_w_L) * (0.048 / 0.230)
        u[1] = np.clip(abs(yaw_rate) / 3.0, 0.0, 1.0)
        # 2: Target Bearing Error
        tb = math.atan2(target_coords[1] - sensory.pos_y, target_coords[0] - sensory.pos_x) - sensory.yaw
        tb_err = abs(math.atan2(math.sin(tb), math.cos(tb)))
        u[2] = np.clip(tb_err / math.pi, 0.0, 1.0)
        # 3..17: 15 Raycast Sonar Rays
        sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 3.0
        for i in range(15):
            d_ray = float(sonar[i])
            u[3 + i] = np.clip((3.0 - d_ray) / 3.0, 0.0, 1.0)
        # 18..21: Directional TTC Sector Proximities
        u[18] = np.max(u[3:6])    # Left sector
        u[19] = np.max(u[6:9])    # Front-Left
        u[20] = np.max(u[9:12])   # Front-Right
        u[21] = np.max(u[12:15])  # Right sector
        return u

    def step_reservoir(self, u: np.ndarray) -> np.ndarray:
        """Steps the 1024-neuron recurrent reservoir forward by dt."""
        if not self.use_reservoir:
            self.x = np.pad(u, (0, self.N - self.M), mode='constant')
            return self.x

        leak = self.dt / self.tau_res
        drive = np.tanh(self.W_res @ self.x + self.W_in @ u)
        self.x = (1.0 - leak) * self.x + leak * drive
        return self.x

    def get_firing_rates(self, x: np.ndarray) -> np.ndarray:
        """Rate-coded rectified non-negative biological neural firing rate in [0, 1]."""
        return np.maximum(0.0, np.tanh(x))

    def predict_hazard_qualities(self, state_x: np.ndarray) -> np.ndarray:
        """
        Computes learned hazard likelihood for all K candidate actions:
        Q_hazard(a_k) = tanh(max(0, W_hazard[:, k]^T * r(x) * 0.05)) in [0, 1]
        """
        if not self.use_learned_hazard or self.mode == "BASELINE":
            return np.zeros(self.K, dtype=float)

        r = self.get_firing_rates(state_x)
        raw_activation = self.W_hazard.T @ r
        probs = np.tanh(np.maximum(0.0, raw_activation * 0.05))
        self.last_hazard_predictions = probs
        return probs

    def step_stdp_learning(
        self,
        state_x: np.ndarray,
        chosen_action_idx: int,
        collision_occurred: bool,
        is_stall: bool = False,
        prediction_error: float = 0.0
    ) -> Tuple[np.ndarray, float]:
        """
        Three-Factor STDP Synaptic Update:
        Delta W_ik = eta * Surprise_Gate * Outcome_Valence * E_ik
        """
        if self.mode in ("BASELINE", "RESERVOIR_ONLY"):
            return np.zeros_like(self.W_hazard), 0.0

        r = self.get_firing_rates(state_x)

        # Post-synaptic action spike
        y_post = np.zeros(self.K, dtype=float)
        y_post[chosen_action_idx] = 1.0

        # 1. Update Spiking Activity Traces
        decay_trace = math.exp(-self.dt / self.stdp_tau_trace)
        self.trace_pre = self.trace_pre * decay_trace + (1.0 - decay_trace) * r
        self.trace_post = self.trace_post * decay_trace + (1.0 - decay_trace) * y_post

        # 2. Update Synaptic Eligibility Trace: dE/dt = -E/tau_e + pre * post
        decay_e = math.exp(-self.dt / self.stdp_tau_e)
        self.E = self.E * decay_e + np.outer(self.trace_pre, y_post)

        # 3. Factor 2: Surprise Gate (Noradrenergic Arousal)
        if self.use_neuromodulation:
            if collision_occurred or is_stall:
                surprise_gate = 1.0
            else:
                surprise_gate = float(np.tanh(abs(prediction_error) * 2.0))
        else:
            surprise_gate = 1.0

        # 4. Factor 3: Outcome Valence
        if self.use_neuromodulation:
            if collision_occurred or is_stall:
                valence = +1.0
            else:
                valence = -0.05
        else:
            valence = 1.0 if (collision_occurred or is_stall) else 0.0

        self.last_surprise = surprise_gate
        self.last_valence = valence

        # 5. Compute Weight Update Delta W
        dW = self.stdp_lr * surprise_gate * valence * self.E

        # Group 5: Scrambled Control
        if self.mode == "SCRAMBLED":
            flat_dw = dW.flatten()
            np.random.shuffle(flat_dw)
            dW = flat_dw.reshape(dW.shape)

        self.W_hazard = np.clip(self.W_hazard + dW, 0.0, 10.0)
        self.last_dw = dW

        mag = float(np.sum(np.abs(dW)))
        self.cumulative_abs_dw += mag
        if mag > 1e-5:
            if valence > 0: self.ltp_count += 1
            else: self.ltd_count += 1

        return dW, mag

    def step_cognitive_cycle(
        self,
        hal,
        target_coords: Tuple[float, float] = (2.2, 0.0),
        is_training: bool = True
    ) -> Dict[str, Any]:
        """
        Executes full cognitive cycle:
        Sensors -> Reservoir -> Plastic Readout -> EFE Decision -> HAL Actuation -> Plasticity
        """
        self.tick += 1

        # A. Proprioception & sensory encoding
        sensory = self.base_agent.embodiment.read_proprioception(hal)
        u = self.encode_sensors(sensory, target_coords)

        # B. 1024-Neuron Reservoir
        x_t = self.step_reservoir(u)

        # C. Predict Learned Hazard
        Q_hazard = self.predict_hazard_qualities(x_t)

        # D. Sensory Clearance Asymmetry & Hazard Level
        sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 3.0
        left_clearance = float(np.mean(sonar[0:6]))
        right_clearance = float(np.mean(sonar[9:15]))
        clearance_bias = (left_clearance - right_clearance) / 3.0

        hazard_level = float(np.max(Q_hazard))
        front_obstacle = bool(min(sonar[6:9]) < 1.20)

        # Latch Tangent Flank Waypoint when obstacle is directly blocking forward line-of-sight
        if (hazard_level > 0.15 or front_obstacle) and sensory.pos_x < 1.25:
            if self.latched_flank is None:
                # Decisive flank selection (favors left or clearer side)
                self.latched_flank = +1.0 if clearance_bias >= -0.05 else -1.0
            nav_target = (1.15, target_coords[1] + self.latched_flank * 0.65)
        else:
            self.latched_flank = None
            nav_target = target_coords

        # E. Expected Free Energy (EFE) Evaluation
        best_act_name = "STRAIGHT_FORWARD"
        min_efe = float('inf')
        candidate_scores = {}

        for idx, (act_name, act_info) in enumerate(self.candidate_actions.items()):
            cmd = act_info["cmd"]
            v = act_info["v"]
            curv = act_info["curv"]

            # Kinematic forward rollout
            dt_sim = 0.033
            h_steps = 15
            yaw_sim = sensory.yaw
            pos_x_sim = sensory.pos_x
            pos_y_sim = sensory.pos_y

            w_L, w_R = cmd[0], cmd[1]
            v_k = (w_L + w_R) * 0.5 * 0.048
            omega_k = (w_R - w_L) * (0.048 / 0.230)

            for _ in range(h_steps):
                yaw_sim += omega_k * dt_sim
                pos_x_sim += v_k * math.cos(yaw_sim) * dt_sim
                pos_y_sim += v_k * math.sin(yaw_sim) * dt_sim

            # 1. Goal Progress Cost to nav_target
            init_dist = math.sqrt((nav_target[0] - sensory.pos_x)**2 + (nav_target[1] - sensory.pos_y)**2)
            final_dist = math.sqrt((nav_target[0] - pos_x_sim)**2 + (nav_target[1] - pos_y_sim)**2)
            goal_cost = (final_dist - init_dist) * 25.0

            # 2. Heading Alignment Cost to nav_target
            tb = math.atan2(nav_target[1] - pos_y_sim, nav_target[0] - pos_x_sim) - yaw_sim
            tb_err = abs(math.atan2(math.sin(tb), math.cos(tb)))
            heading_cost = (tb_err / math.pi) * 6.0

            # 3. Curvature Effort Penalty
            effort_cost = 0.8 * (curv ** 2)

            # 4. Straight Action Bias
            straight_bias = -2.0 if act_name == "STRAIGHT_FORWARD" else 0.0

            # 5. Learned Hazard Penalty
            if self.mode == "BASELINE":
                front_clearance = min(sensory.sonar_distances[6:9]) if sensory.sonar_distances is not None else 3.0
                hazard_cost = max(0.0, (1.0 - front_clearance) * 80.0) if "STRAIGHT" in act_name else 0.0
            else:
                hazard_cost = self.hazard_weight * Q_hazard[idx]

            total_efe = goal_cost + heading_cost + effort_cost + straight_bias + hazard_cost
            candidate_scores[act_name] = {
                "efe": total_efe,
                "goal_cost": goal_cost,
                "heading_cost": heading_cost,
                "hazard_cost": hazard_cost,
                "q_hazard": float(Q_hazard[idx]),
                "cmd": cmd
            }

            if total_efe < min_efe:
                min_efe = total_efe
                best_act_name = act_name

        chosen_act = self.candidate_actions[best_act_name]
        chosen_idx = self.action_to_idx[best_act_name]

        # F. Motor Command Dispatch to HAL
        self.base_agent.embodiment.target_w_L = float(chosen_act["cmd"][0])
        self.base_agent.embodiment.target_w_R = float(chosen_act["cmd"][1])
        self.base_agent.embodiment.step_embodiment(hal)

        # G. Genuine Physical Collision & Stall Detection
        collision = bool(sensory.has_body_collision or sensory.robot_obstacle_contacts > 0 or sensory.robot_wall_contacts > 0)
        is_stall = bool(self.tick > 15 and sensory.speed < 0.02 and abs(chosen_act["cmd"][0]) > 2.0)
        food_absorbed = bool(math.sqrt((target_coords[0] - sensory.pos_x)**2 + (target_coords[1] - sensory.pos_y)**2) < 0.30)

        # H. Plasticity Update Step (active during training)
        pred_error = 1.0 if (collision or is_stall) else 0.0
        if is_training:
            dW, dW_mag = self.step_stdp_learning(x_t, chosen_idx, collision, is_stall, pred_error)
        else:
            dW_mag = 0.0

        return {
            "tick": self.tick,
            "pos": (sensory.pos_x, sensory.pos_y),
            "yaw": sensory.yaw,
            "speed": sensory.speed,
            "chosen_action": best_act_name,
            "chosen_idx": chosen_idx,
            "efe": min_efe,
            "q_hazard_chosen": float(Q_hazard[chosen_idx]),
            "q_hazard_all": Q_hazard.tolist(),
            "collision": collision,
            "is_stall": is_stall,
            "food_absorbed": food_absorbed,
            "dw_magnitude": dW_mag,
            "surprise_gate": self.last_surprise,
            "valence": self.last_valence,
            "candidate_scores": candidate_scores
        }
