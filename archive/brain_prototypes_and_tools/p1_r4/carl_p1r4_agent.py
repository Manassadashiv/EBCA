"""
brain/p1_r4/carl_p1r4_agent.py — Phase 1-R4 Three-Factor STDP Synaptic Plasticity Organism

Re-connects biological Three-Factor Spike-Timing-Dependent Plasticity (STDP) into CARL's
embodied active inference decision architecture:
1. Pre-Synaptic Population (M=22): Continuous sensorimotor & temporal state representation.
2. Post-Synaptic Population (K=7): Curvature action primitives.
3. Plastic Synaptic Matrix (W ∈ R^(22 × 7)): 154 plastic synapses.
4. Three-Factor Gating: ΔW_ij = η · Eligibility_ij · Surprise_PE · Valence.
5. Downstream EFE Integration: G(a) = G_kinematic(a) + G_HDC(a) - λ_stdp · Q_stdp(S, a).

ZERO BEHAVIOR-SPECIFIC RULES:
- Pure associative Hebbian/anti-Hebbian temporal weight evolution.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_episodic_memory import AutobiographicalEpisode


class CarlP1R4Agent:
    """
    Phase 1-R4 Developmental Agent with Active Three-Factor STDP Plasticity.
    """
    def __init__(
        self,
        dt: float = 0.0333,
        enable_stdp: bool = True,
        enable_hdc_memory: bool = True,
        shuffle_stdp_timing: bool = False,
        horizon_steps: int = 18,
        stdp_lr: float = 0.015,
        stdp_lambda: float = 45.0
    ):
        self.dt = dt
        self.enable_stdp = enable_stdp
        self.enable_hdc_memory = enable_hdc_memory
        self.shuffle_stdp_timing = shuffle_stdp_timing
        self.horizon_steps = horizon_steps
        self.stdp_lr = stdp_lr
        self.stdp_lambda = stdp_lambda
        
        # Instantiate frozen baseline organism agent
        self.agent = CarlAutonomousOrganismAgent(
            dt=self.dt,
            enable_memory=self.enable_hdc_memory
        )
        
        # Candidate Curvature Action Primitive Library (7 Primitives)
        self.candidate_actions = {
            "STRAIGHT_FORWARD": {"cmd": np.array([5.5, 5.5]), "curv": 0.0, "v": 0.275},
            "CURVE_LEFT_GENTLE": {"cmd": np.array([4.8, 5.8]), "curv": +0.50, "v": 0.265},
            "CURVE_LEFT_SHARP": {"cmd": np.array([3.6, 6.2]), "curv": +1.50, "v": 0.245},
            "SWERVE_LEFT": {"cmd": np.array([2.5, 6.5]), "curv": +2.20, "v": 0.225},
            "CURVE_RIGHT_GENTLE": {"cmd": np.array([5.8, 4.8]), "curv": -0.50, "v": 0.265},
            "CURVE_RIGHT_SHARP": {"cmd": np.array([6.2, 3.6]), "curv": -1.50, "v": 0.245},
            "SWERVE_RIGHT": {"cmd": np.array([6.5, 2.5]), "curv": -2.20, "v": 0.225}
        }
        self.action_names = list(self.candidate_actions.keys())
        self.action_to_idx = {name: idx for idx, name in enumerate(self.action_names)}
        self.sequence_library = [(a1, a2) for a1 in self.action_names for a2 in self.action_names]
        
        # Differential drive kinematic constants
        self.wheel_radius = 0.048
        self.track_width = 0.23
        self.sonar_angles = np.linspace(-math.radians(120), math.radians(120), 15)
        
        # ── Three-Factor STDP Plastic Synaptic Architecture ───────────
        # M = 22 pre-synaptic features: [speed, yaw_rate, target_bearing_err, 15 sonars, 4 directional TTCs]
        self.pre_dim = 22
        self.post_dim = len(self.action_names)  # K = 7
        
        # Persistent synaptic weight matrix W ∈ R^(22 × 7)
        self.W = np.zeros((self.pre_dim, self.post_dim), dtype=float)
        self.W_initial = np.copy(self.W)
        
        # Synaptic eligibility traces & activity history
        self.E = np.zeros((self.pre_dim, self.post_dim), dtype=float)
        self.A_pre = np.zeros(self.pre_dim, dtype=float)
        self.A_post = np.zeros(self.post_dim, dtype=float)
        
        # Diagnostic & Plasticity Tracking
        self.v_expected = 0.0
        self.last_surprise_gate = 0.0
        self.last_valence = 0.0
        self.ltp_events = 0
        self.ltd_events = 0
        self.cumulative_dw = 0.0
        self.last_dw = np.zeros((self.pre_dim, self.post_dim))
        self.last_delta_t = 0.0
        self.memory_writes_this_episode = 0
        self.memory_retrievals_this_episode = 0



    def encode_presynaptic_state(self, sensory, target_coords: Tuple[float, float]) -> np.ndarray:
        """Encodes 22-dimensional continuous pre-synaptic feature rates in [0, 1]."""
        pre = np.zeros(self.pre_dim, dtype=float)
        # 0: Normalized Forward Speed
        pre[0] = np.clip(sensory.speed / 0.35, 0.0, 1.0)
        # 1: Normalized Yaw Rate (from differential wheel velocities)
        yaw_rate = (sensory.wheel_w_R - sensory.wheel_w_L) * (self.wheel_radius / self.track_width)
        pre[1] = np.clip(abs(yaw_rate) / 2.5, 0.0, 1.0)
        # 2: Target Bearing Alignment Error
        tb = math.atan2(target_coords[1] - sensory.pos_y, target_coords[0] - sensory.pos_x) - sensory.yaw
        tb_err = abs(math.atan2(math.sin(tb), math.cos(tb)))
        pre[2] = np.clip(tb_err / math.pi, 0.0, 1.0)
        # 3..17: 15 Sensed Sonar Rays (Inverted range: 1.0 = immediate obstacle, 0.0 = clear)
        sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 5.0
        for i in range(15):
            d_ray = float(sonar[i])
            pre[3 + i] = np.clip((3.0 - d_ray) / 3.0, 0.0, 1.0)
        # 18..21: Directional Proximity / TTC (Left, Center-Left, Center-Right, Right)
        pre[18] = np.max(pre[3:6])    # Left sector
        pre[19] = np.max(pre[6:9])    # Front-Left
        pre[20] = np.max(pre[9:12])   # Front-Right
        pre[21] = np.max(pre[12:15])  # Right sector
        return pre

    def end_episode_consolidation(self):
        """Offline inter-episode consolidation for HDC memory and synaptic traces."""
        # Reset eligibility and activity traces between episodes, keeping persistent synaptic matrix W
        self.E[:] = 0.0
        self.A_pre[:] = 0.0
        self.A_post[:] = 0.0


    def predict_stdp_action_qualities(self, pre_features: np.ndarray) -> np.ndarray:
        """Computes STDP-learned action quality vector Q_stdp(S) ∈ [-1, 1]^K."""
        if not self.enable_stdp:
            return np.zeros(self.post_dim, dtype=float)
        # Forward synaptic pass: Q = tanh(W^T · Pre)
        return np.tanh(self.W.T @ pre_features)

    def step_stdp_plasticity(
        self,
        pre_features: np.ndarray,
        chosen_action_idx: int,
        prediction_error: float,
        collision_occurred: bool,
        is_stall: bool = False,
        food_absorbed: bool = False
    ) -> Tuple[np.ndarray, float]:

        """
        Updates three-factor STDP synaptic matrix:
        ΔW_ij = η · Eligibility_ij · Modulatory_Gate(Surprise, Outcome)
        """
        if not self.enable_stdp:
            return np.zeros_like(self.W), 0.0
            
        post_spikes = np.zeros(self.post_dim, dtype=float)
        post_spikes[chosen_action_idx] = 1.0
        
        # 1. Decay Activity Traces (tau = 20ms equivalent)
        decay_pre = math.exp(-self.dt / 0.020)
        decay_post = math.exp(-self.dt / 0.020)
        decay_e = math.exp(-self.dt / 0.050)
        
        self.A_pre *= decay_pre
        self.A_post *= decay_post
        self.E *= decay_e
        
        # 2. STDP Temporal Correlation & Eligibility
        if self.shuffle_stdp_timing:
            # Control condition: Shuffle timing correlation
            ltp = np.outer(np.random.permutation(self.A_pre), post_spikes) * 0.01
            ltd = np.outer(pre_features, np.random.permutation(self.A_post)) * (-0.012)
        else:
            # Biologically correct timing: Pre before Post -> LTP, Post before Pre -> LTD
            ltp = np.outer(self.A_pre, post_spikes) * 0.01
            ltd = np.outer(pre_features, self.A_post) * (-0.012)
            
        self.E += (ltp + ltd)
        
        self.A_pre += pre_features
        self.A_post += post_spikes
        
        # 3. Third Factor: Neuromodulatory Surprise & Outcome Valence Gate
        # Genuine adverse encounter: physical collision or physical stall against obstacle
        valence = 0.0
        surprise_gate = 0.0
        is_adverse_stall = collision_occurred or (prediction_error > 0.15 and is_stall)
        
        if food_absorbed:
            valence = +1.0
            surprise_gate = 1.5
        elif is_adverse_stall:
            valence = -1.0
            surprise_gate = float(np.clip(prediction_error / 0.25, 0.0, 2.0))
            
        # 4. Synaptic Weight Matrix Update
        dW = self.stdp_lr * surprise_gate * valence * self.E
        self.W = np.clip(self.W + dW, -1.5, 1.5)
        
        dw_norm = float(np.linalg.norm(dW))
        self.cumulative_dw += dw_norm
        self.last_dw = dW
        self.last_surprise_gate = float(surprise_gate)
        self.last_valence = float(valence)
        
        if dw_norm > 1e-5:
            if valence > 0:
                self.ltp_events += int(np.sum(dW > 0))
            else:
                self.ltd_events += int(np.sum(dW < 0))
                
        return dW, dw_norm



    def evaluate_sequence_rollouts(
        self,
        sensory,
        target_pos: Tuple[float, float] = (2.20, 0.00)
    ) -> Tuple[Tuple[str, str], float, Dict[str, float]]:
        """
        Evaluates candidate 2-segment action sequences under integrated Active Inference + STDP + HDC.
        """
        sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 5.0
        sensed_points = []
        for d_ray, ang in zip(sonar, self.sonar_angles):
            if d_ray < 3.2:
                pt_x = sensory.pos_x + d_ray * math.cos(sensory.yaw + ang)
                pt_y = sensory.pos_y + d_ray * math.sin(sensory.yaw + ang)
                sensed_points.append((pt_x, pt_y))
                
        pre_state = self.encode_presynaptic_state(sensory, target_coords=target_pos)
        stdp_q_values = self.predict_stdp_action_qualities(pre_state)
        
        best_seq = self.sequence_library[0]
        min_efe = float("inf")
        candidate_efes = {}
        
        r = self.wheel_radius
        b = self.track_width
        dt = self.dt
        k_steps = self.horizon_steps
        max_sim_retrieved = 0.0
        
        for a1, a2 in self.sequence_library:
            seq_name = f"{a1}->{a2}"
            seq = [self.candidate_actions[a1], self.candidate_actions[a2]]
            
            sim_x = float(sensory.pos_x)
            sim_y = float(sensory.pos_y)
            sim_yaw = float(sensory.yaw)
            
            risk = 0.0
            effort = 0.0
            memory_efe_bias = 0.0
            
            for act_data in seq:
                cmd = act_data["cmd"]
                curv = act_data["curv"]
                v_lin = act_data["v"]
                w_yaw = (cmd[1] - cmd[0]) * r / b
                effort += (curv ** 2) * 0.03
                
                for step in range(1, k_steps + 1):
                    sim_x += v_lin * math.cos(sim_yaw) * dt
                    sim_y += v_lin * math.sin(sim_yaw) * dt
                    sim_yaw += w_yaw * dt
                    
                    for px, py in sensed_points:
                        dx = px - sim_x
                        dy = py - sim_y
                        d_pt = math.sqrt(dx**2 + dy**2)
                        is_ahead = (dx * math.cos(sim_yaw) + dy * math.sin(sim_yaw)) > 0
                        if is_ahead:
                            if d_pt < 0.35:
                                risk += (0.35 - d_pt) * 100.0
                            if d_pt < 0.15:
                                risk += 1000.0
                            v_app = v_lin * (dx * math.cos(sim_yaw) + dy * math.sin(sim_yaw)) / (d_pt + 1e-4)
                            if v_app > 0.0 and d_pt < 1.0:
                                risk += (v_app / (d_pt + 0.1)**2) * 6.0
                        else:
                            if d_pt < 0.22:
                                risk += (0.22 - d_pt) * 120.0
                                
                    bd = min(4.8 - abs(sim_x), 4.8 - abs(sim_y))
                    if bd < 0.35:
                        risk += (0.35 - bd) * 100.0
                        
                    # Continuous HDC Episodic Memory Bias
                    if self.enable_hdc_memory and len(self.agent.memory.episodes) > 0:
                        self.memory_retrievals_this_episode += 1
                        for ep in self.agent.memory.episodes:
                            d_sq = (sim_x - ep.pos_x)**2 + (sim_y - ep.pos_y)**2
                            if d_sq < 0.64:
                                k_val = math.exp(-d_sq / (2.0 * 0.35**2))
                                memory_efe_bias += -ep.outcome_valence * k_val * 4.5
                                if k_val > max_sim_retrieved:
                                    max_sim_retrieved = k_val
            
            final_dist = math.sqrt((target_pos[0] - sim_x)**2 + (target_pos[1] - sim_y)**2)
            target_bearing = math.atan2(target_pos[1] - sim_y, target_pos[0] - sim_x)
            final_head_err = abs(math.atan2(math.sin(sim_yaw - target_bearing), math.cos(sim_yaw - target_bearing)))
            
            # STDP Action Quality Modulation (Subtract Q_stdp to favor learned quality)
            idx1 = self.action_to_idx[a1]
            idx2 = self.action_to_idx[a2]
            stdp_bias = self.stdp_lambda * (stdp_q_values[idx1] + stdp_q_values[idx2]) * 0.5
            
            dist_cost = final_dist * 80.0
            align_cost = final_head_err * 12.0
            vel_bonus = (seq[0]["v"] + seq[1]["v"]) * 30.0
            
            efe = dist_cost + align_cost + effort + risk + memory_efe_bias - stdp_bias - vel_bonus
            candidate_efes[seq_name] = float(efe)
            
            if efe < min_efe:
                min_efe = efe
                best_seq = (a1, a2)
                
        self.last_retrieval_similarity = float(max_sim_retrieved)
        return best_seq, min_efe, candidate_efes

    def step(self, hal, target_coords: Tuple[float, float] = (2.20, 0.00)) -> Dict[str, Any]:
        """
        Steps one 30 Hz perception-plasticity-actuation cycle.
        """
        sensory = self.agent.embodiment.read_proprioception(hal)
        pre_state = self.encode_presynaptic_state(sensory, target_coords=target_coords)
        
        # 1. Multi-Step Action Sequence Evaluation (EFE modulated by STDP + HDC)
        best_seq, best_efe, candidate_efes = self.evaluate_sequence_rollouts(sensory, target_pos=target_coords)
        best_a1 = best_seq[0]
        act_idx = self.action_to_idx[best_a1]
        act_cmd = self.candidate_actions[best_a1]["cmd"]
        
        # 2. Step embodied motor filter
        self.agent.embodiment.target_w_L = float(act_cmd[0])
        self.agent.embodiment.target_w_R = float(act_cmd[1])
        
        tb = math.atan2(target_coords[1] - sensory.pos_y, target_coords[0] - sensory.pos_x) - sensory.yaw
        tb = (tb + math.pi) % (2 * math.pi) - math.pi
        self.agent.embodiment.target_head_yaw = float(np.clip(tb, -1.2, 1.2))
        
        self.agent.embodiment.step_embodiment(hal)
        for _ in range(3):
            hal.step()
        self.agent.tick += 1
            
        # 3. Dynamic Generative Velocity Prediction & Stall Detection
        r = self.wheel_radius
        v_target = float((act_cmd[0] + act_cmd[1]) * 0.5 * r)
        self.v_expected += (self.dt / 0.12) * (v_target - self.v_expected)
        pred_error = abs(sensory.speed - self.v_expected)
        is_stall = (sensory.speed < 0.05 and v_target > 0.15 and self.agent.tick > 10)
        
        # 4. Check Food Absorption & Collision
        dist_food = math.sqrt((target_coords[0] - sensory.pos_x)**2 + (target_coords[1] - sensory.pos_y)**2)
        food_absorbed = (dist_food < 0.30)
        collision_occurred = sensory.has_body_collision
        
        # 5. Execute Three-Factor STDP Plasticity Update
        dW, dw_norm = self.step_stdp_plasticity(
            pre_features=pre_state,
            chosen_action_idx=act_idx,
            prediction_error=float(pred_error),
            collision_occurred=collision_occurred,
            is_stall=is_stall,
            food_absorbed=food_absorbed
        )

        
        # 6. HDC Episodic Memory Encoding (if enabled)
        if self.enable_hdc_memory:
            if food_absorbed:
                self.agent.memory.store_episode(
                    pos_x=float(sensory.pos_x), pos_y=float(sensory.pos_y),
                    active_need="SEEK_ENERGY", action=best_a1, outcome_valence=1.0,
                    hazard=False, pred_err=float(pred_error), tick=int(self.agent.tick)
                )
                self.memory_writes_this_episode += 1
            elif collision_occurred or (self.agent.tick > 20 and pred_error > 0.20 and sensory.speed < 0.05):
                self.agent.memory.store_episode(
                    pos_x=float(sensory.pos_x), pos_y=float(sensory.pos_y),
                    active_need="SEEK_ENERGY", action=best_a1, outcome_valence=-1.0,
                    hazard=True, pred_err=float(pred_error), tick=int(self.agent.tick)
                )
                self.memory_writes_this_episode += 1
                
        return {
            "sensory": sensory,
            "best_action": best_a1,
            "best_sequence": f"{best_seq[0]}->{best_seq[1]}",
            "best_efe": float(best_efe),
            "candidate_efes": candidate_efes,
            "prediction_error": float(pred_error),
            "v_expected": float(self.v_expected),
            "surprise_gate": float(self.last_surprise_gate),
            "outcome_valence": float(self.last_valence),
            "food_absorbed": food_absorbed,
            "collision_occurred": collision_occurred,

            "dist_food": float(dist_food),
            "stdp_dw_norm": float(dw_norm),
            "stdp_weight_norm": float(np.linalg.norm(self.W)),
            "stdp_mean_weight": float(np.mean(self.W)),
            "stdp_weight_var": float(np.var(self.W)),
            "stdp_q_values": self.predict_stdp_action_qualities(pre_state),
            "memory_writes": self.memory_writes_this_episode,
            "memory_retrievals": self.memory_retrievals_this_episode,
            "episodes_in_memory": len(self.agent.memory.episodes) if self.enable_hdc_memory else 0
        }

    def reset_for_episode(self, episode_num: int, seed: int, condition: str, preserve_synapses: bool = True, preserve_hdc: bool = True):
        """
        Resets controller state while preserving synaptic weights W across developmental episodes.
        """
        w_backup = np.copy(self.W) if preserve_synapses else np.copy(self.W_initial)
        mem_backup = None
        if self.enable_hdc_memory and preserve_hdc and len(self.agent.memory.episodes) > 0:
            mem_backup = {
                "episodes": list(self.agent.memory.episodes),
                "matrix": np.copy(self.agent.memory.hdc_memory_matrix)
            }
            
        self.agent.reset()
        self.W = w_backup
        self.v_expected = 0.0
        self.E[:] = 0.0
        self.A_pre[:] = 0.0
        self.A_post[:] = 0.0

        
        if mem_backup is not None:
            self.agent.memory.episodes = mem_backup["episodes"]
            self.agent.memory.hdc_memory_matrix = mem_backup["matrix"]
            
        self.agent.homeostasis.energy = 0.35
        self.memory_writes_this_episode = 0
        self.memory_retrievals_this_episode = 0
