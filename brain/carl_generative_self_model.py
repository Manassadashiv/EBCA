"""
brain/carl_generative_self_model.py — Generative Self-World Model, Active Inference & Counterfactual Imagination

1. Generative Forward Model: Predicts future sensory consequences P(s_{t+1} | s_t, a_t)
2. Online Self-Model: Estimates body mass, wheel radius, ground traction, and actuator latency
3. Active Inference & Expected Free Energy: G(a) = Predicted Risk + Homeostatic Deviation - Epistemic Information Gain
4. Counterfactual Imagination: Rolls out internal simulations (Dreamer Engine) of candidate actions before execution
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

@dataclass
class SelfModelParameters:
    estimated_mass_kg: float = 0.95        # Body mass estimate
    estimated_wheel_radius_m: float = 0.048 # Wheel radius estimate
    estimated_track_width_m: float = 0.230 # Differential wheelbase estimate
    estimated_friction_coeff: float = 2.50 # Ground traction estimate
    estimated_actuator_latency_s: float = 0.033 # Response delay estimate
    confidence: float = 0.85               # Self-model parameter confidence [0.0, 1.0]


class CarlGenerativeSelfModel:
    """
    Generative Self-World Model executing Active Inference and Counterfactual Rollouts.
    """
    def __init__(self, dt: float = 0.0333):
        self.dt = dt
        self.self_params = SelfModelParameters()
        
        # Recurrent hidden state for temporal context
        self.hidden_dim = 32
        self.hidden_state = np.zeros(self.hidden_dim)
        
        # Forward transition weights (linearized generative approximation)
        self.W_trans = np.random.randn(self.hidden_dim, self.hidden_dim) * 0.05
        self.W_act = np.random.randn(self.hidden_dim, 2) * 0.05
        self.W_obs = np.random.randn(6, self.hidden_dim) * 0.05
        
        # Last predicted observation
        self.last_prediction = np.zeros(6) # [pos_x, pos_y, yaw, speed, w_L, w_R]
        self.prediction_error = 0.0
        self.prediction_error_history = []

    def predict_next_state(self, current_sensory_state, action_cmds: np.ndarray) -> np.ndarray:
        """
        Predicts sensory observation at t+1 using generative kinematics + self-model.
        """
        x = current_sensory_state.pos_x
        y = current_sensory_state.pos_y
        yaw = current_sensory_state.yaw
        wL_curr = current_sensory_state.wheel_w_L
        wR_curr = current_sensory_state.wheel_w_R
        uL, uR = float(action_cmds[0]), float(action_cmds[1])
        
        r = self.self_params.estimated_wheel_radius_m
        b = self.self_params.estimated_track_width_m
        
        # S-curve rate-limited velocity prediction
        max_accel = 10.0
        pred_wL = wL_curr + np.clip(uL - wL_curr, -max_accel * self.dt, max_accel * self.dt)
        pred_wR = wR_curr + np.clip(uR - wR_curr, -max_accel * self.dt, max_accel * self.dt)
        
        # Forward differential kinematics prediction with traction attenuation
        traction = float(np.clip(self.self_params.estimated_friction_coeff / 2.50, 0.20, 1.0))
        v_pred = (pred_wL + pred_wR) * 0.5 * r * traction
        w_yaw_pred = (pred_wR - pred_wL) * r / b * traction
        
        pred_x = x + v_pred * math.cos(yaw) * self.dt
        pred_y = y + v_pred * math.sin(yaw) * self.dt
        pred_yaw = yaw + w_yaw_pred * self.dt
        
        self.last_prediction = np.array([pred_x, pred_y, pred_yaw, v_pred, pred_wL, pred_wR])
        return self.last_prediction

    def update_with_observation(self, current_sensory_state) -> float:
        """
        Computes sensory prediction error epsilon_t and updates online self-model parameters.
        """
        err_v = abs(current_sensory_state.speed - self.last_prediction[3])
        err_p = math.sqrt((current_sensory_state.pos_x - self.last_prediction[0])**2 + (current_sensory_state.pos_y - self.last_prediction[1])**2)
        
        err = float(err_v + 5.0 * err_p)
        self.prediction_error = err
        self.prediction_error_history.append(self.prediction_error)
        
        # Online Self-Model Parameter Adaptation (Friction estimation under wheel slip)
        if current_sensory_state.speed > 0.05:
            avg_w = (abs(current_sensory_state.wheel_w_L) + abs(current_sensory_state.wheel_w_R)) * 0.5
            meas_r = current_sensory_state.speed / max(0.01, avg_w)
            slip_ratio = min(1.0, meas_r / self.self_params.estimated_wheel_radius_m)
            target_mu = float(np.clip(0.40 + 2.10 * slip_ratio, 0.40, 2.50))
            self.self_params.estimated_friction_coeff = float(0.92 * self.self_params.estimated_friction_coeff + 0.08 * target_mu)
                
        return self.prediction_error

    def imagine_counterfactual_rollouts(
        self,
        current_state,
        homeostatic_core,
        target_pos: Optional[np.ndarray] = None,
        last_action_name: str = "STRAIGHT_FORWARD",
        active_steering_bias: float = 0.0,
        horizon_steps: int = 20
    ) -> Dict[str, Any]:
        """
        Counterfactual Imagination (Dreamer Engine):
        Evaluates candidate continuous curvature trajectories inside the internal forward kinematic model.
        Simulates multi-step spatial clearance along curved kinematic arcs and selects the policy
        minimizing Expected Free Energy G(a) with strong action persistence and smooth forward progression.
        """
        # Continuous curvature candidate actions with positive forward velocity
        candidate_actions = {
            "STRAIGHT_FORWARD": {"cmd": np.array([5.5, 5.5]), "curv": 0.0, "v": 0.275},
            "CURVE_LEFT_SLIGHT": {"cmd": np.array([4.6, 5.8]), "curv": +0.5, "v": 0.26},
            "CURVE_LEFT_MODERATE": {"cmd": np.array([3.6, 6.0]), "curv": +1.2, "v": 0.24},
            "CURVE_LEFT_STRONG": {"cmd": np.array([2.8, 6.8]), "curv": +2.2, "v": 0.24},
            "CURVE_LEFT_TIGHT": {"cmd": np.array([1.2, 6.2]), "curv": +3.5, "v": 0.185},
            "CURVE_RIGHT_SLIGHT": {"cmd": np.array([5.8, 4.6]), "curv": -0.5, "v": 0.26},
            "CURVE_RIGHT_MODERATE": {"cmd": np.array([6.0, 3.6]), "curv": -1.2, "v": 0.24},
            "CURVE_RIGHT_STRONG": {"cmd": np.array([6.8, 2.8]), "curv": -2.2, "v": 0.24},
            "CURVE_RIGHT_TIGHT": {"cmd": np.array([6.2, 1.2]), "curv": -3.5, "v": 0.185},
            "SLOW_CREEP_FORWARD": {"cmd": np.array([2.2, 2.2]), "curv": 0.0, "v": 0.11},
            "EMERGENCY_REVERSE": {"cmd": np.array([-2.5, -2.5]), "curv": 0.0, "v": -0.125},
            "EMERGENCY_SPIN_LEFT": {"cmd": np.array([-4.0, 4.0]), "curv": +8.0, "v": 0.0},
            "EMERGENCY_SPIN_RIGHT": {"cmd": np.array([4.0, -4.0]), "curv": -8.0, "v": 0.0},
            "BRAKE_REST": {"cmd": np.array([0.0, 0.0]), "curv": 0.0, "v": 0.0}
        }
        
        evaluations = {}
        r = self.self_params.estimated_wheel_radius_m
        b = self.self_params.estimated_track_width_m
        mu_hat = self.self_params.estimated_friction_coeff
        
        # Sonar distance profile (15 rays from -120 deg (Right) to +120 deg (Left))
        sonar_rays = current_state.sonar_distances if current_state.sonar_distances is not None else np.ones(15) * 5.0
        n_rays = len(sonar_rays)
        if n_rays == 15:
            min_front_clearance = float(np.min(sonar_rays[6:9])) # Frontal cone (-16 deg to +16 deg)
            front_direct_clear = float(sonar_rays[7])
            right_clearance = float(np.mean(sonar_rays[0:6]))
            left_clearance = float(np.mean(sonar_rays[9:15]))
        else:
            mid = n_rays // 2
            min_front_clearance = float(np.min(sonar_rays[max(0, mid-1):min(n_rays, mid+2)]))
            front_direct_clear = float(sonar_rays[mid])
            right_clearance = float(np.mean(sonar_rays[:mid]))
            left_clearance = float(np.mean(sonar_rays[mid:]))
        
        # HARD SPIN ELIGIBILITY GATE:
        # In-place spin is permitted ONLY if direct front path is blocked AND both sides are constrained (genuine dead end)
        is_dead_end_trapped = (front_direct_clear < 0.75 and min_front_clearance < 0.70 and left_clearance < 1.40 and right_clearance < 1.40)
        
        # Previous action curvature for smoothness
        last_info = candidate_actions.get(last_action_name, {"curv": 0.0, "v": 0.25})
        last_curv = last_info["curv"]
        
        # Sensed Sonar Points Projected into 2D World Coordinates
        sonar_angles = np.linspace(-math.pi * 0.666, math.pi * 0.666, 15)
        sensed_points = []
        for d_ray, ang in zip(sonar_rays, sonar_angles):
            if d_ray < 3.5:
                pt_x = current_state.pos_x + d_ray * math.cos(current_state.yaw + ang)
                pt_y = current_state.pos_y + d_ray * math.sin(current_state.yaw + ang)
                sensed_points.append((pt_x, pt_y))

        for name, act_data in candidate_actions.items():
            act = act_data["cmd"]
            curv = act_data["curv"]
            v_lin = act_data["v"]
            uL, uR = float(act[0]), float(act[1])
            w_yaw = (uR - uL) * r / b
            
            sim_x = current_state.pos_x
            sim_y = current_state.pos_y
            sim_yaw = current_state.yaw
            
            sim_traj = [(sim_x, sim_y)]
            cumulative_collision_risk = 0.0
            min_arc_clearance = 5.0
            
            dist_0_25s = 5.0
            dist_0_50s = 5.0
            dist_1_00s = 5.0
            
            # 1. Multi-Step Forward Kinematic Arc Simulation (30 steps = 1.0s)
            for step in range(1, horizon_steps + 1):
                sim_x += v_lin * math.cos(sim_yaw) * self.dt
                sim_y += v_lin * math.sin(sim_yaw) * self.dt
                sim_yaw += w_yaw * self.dt
                sim_traj.append((sim_x, sim_y))
                
                # Sensed 2D Obstacle Proximity & Time-To-Collision Risk
                for px, py in sensed_points:
                    dx = px - sim_x
                    dy = py - sim_y
                    d_pt = math.sqrt(dx**2 + dy**2)
                    min_arc_clearance = min(min_arc_clearance, d_pt)
                    
                    is_ahead = (dx * math.cos(sim_yaw) + dy * math.sin(sim_yaw)) > 0
                    if is_ahead:
                        if d_pt < 0.35 and v_lin > 0.0:
                            cumulative_collision_risk += (0.35 - d_pt) * 80.0
                        if d_pt < 0.12 and v_lin > 0.0:
                            cumulative_collision_risk += 800.0
                        v_app = v_lin * (dx * math.cos(sim_yaw) + dy * math.sin(sim_yaw)) / (d_pt + 1e-4)
                        if v_app > 0.0 and d_pt < 1.0:
                            cumulative_collision_risk += (v_app / (d_pt + 0.1)**2) * 5.0
                    else:
                        if d_pt < 0.20:
                            cumulative_collision_risk += (0.20 - d_pt) * 100.0
                
                if step == int(0.25 / self.dt):
                    dist_0_25s = min_arc_clearance
                elif step == int(0.50 / self.dt):
                    dist_0_50s = min_arc_clearance
                elif step == horizon_steps:
                    dist_1_00s = min_arc_clearance
                    
                # Arena Boundary Proximity Penalty (Maintains >=0.35m clearance to arena boundary walls at +/- 5.0m)
                bound_dist = min(4.80 - abs(sim_x), 4.80 - abs(sim_y))
                if bound_dist < 0.55:
                    cumulative_collision_risk += (0.55 - bound_dist) * 80.0
                if bound_dist < 0.30:
                    cumulative_collision_risk += 500.0
                    
            # 2. Hard Spin & Reverse Penalties: Prohibited during normal navigation unless trapped in dead end
            spin_penalty = 0.0
            if "SPIN" in name:
                if not is_dead_end_trapped:
                    spin_penalty = 1200.0
                else:
                    spin_penalty = 0.0
                    
            reverse_penalty = 0.0
            if "REVERSE" in name:
                if not is_dead_end_trapped:
                    reverse_penalty = 1000.0
                else:
                    reverse_penalty = 0.0
                    
            # Idling penalty: Standing still when open space is available is penalized
            idling_penalty = 0.0
            if name == "BRAKE_REST":
                if front_direct_clear > 0.35 or not is_dead_end_trapped:
                    idling_penalty = 600.0
                else:
                    idling_penalty = 100.0
                
            # 3. Action Smoothness & Steering Continuity Cost
            # Penalizes sharp curvature derivatives without preventing returning to straight
            curvature_change_penalty = 2.0 * (abs(curv - last_curv) ** 1.2)
            action_persistence_penalty = 1.0 if name != last_action_name else 0.0
            
            # Curvature effort / energy cost (centrifugal drag when turning unnecessarily in open space)
            curvature_effort_cost = 0.0
            if min_front_clearance > 0.85:
                # When front is open, high curvature turning is physically inefficient and penalized
                curvature_effort_cost = 10.0 * (curv ** 2)
            elif min_front_clearance > 0.55:
                curvature_effort_cost = 3.0 * (curv ** 2)
                
            # Steering Directional Bias (Maintains chosen avoidance direction without flickering)
            steering_bias_bonus = 0.0
            if active_steering_bias > 0.1 and curv > 0:
                steering_bias_bonus = 4.0 * active_steering_bias
            elif active_steering_bias < -0.1 and curv < 0:
                steering_bias_bonus = 4.0 * abs(active_steering_bias)
                
            # 4. Straight Progression and Corridor Centering Bonus
            straight_bonus = 0.0
            if name == "STRAIGHT_FORWARD" and min_front_clearance > 0.65:
                straight_bonus = 45.0
            elif "SLIGHT" in name and min_front_clearance > 0.65:
                straight_bonus = 18.0
                
            corridor_centering_bonus = 0.0
            if left_clearance < 0.75 and right_clearance < 0.75:
                lateral_imbalance = abs(left_clearance - right_clearance)
                if name == "STRAIGHT_FORWARD":
                    corridor_centering_bonus = 40.0 * (1.0 - min(1.0, lateral_imbalance * 2.0))
                elif abs(curv) > 0.3:
                    curvature_change_penalty += 30.0
                    
            # 5. Forward Velocity and Progress Reward
            # Strong intrinsic drive to maintain forward translation
            forward_velocity_bonus = 25.0 * max(0.0, v_lin)
            
            # Open Space / Clearance Bonus along candidate arc (capped to avoid runaway side-turning)
            open_space_bonus = 8.0 * min(2.0, max(0.0, min_arc_clearance - 0.5))
            
            # Target Goal Progress
            if target_pos is not None:
                init_dist = np.linalg.norm(target_pos - np.array([current_state.pos_x, current_state.pos_y]))
                final_dist = np.linalg.norm(target_pos - np.array([sim_x, sim_y]))
                goal_progress_reward = (init_dist - final_dist) * 6.0
            else:
                goal_progress_reward = open_space_bonus * 0.5
                
            # Slip penalty under low ground friction
            slip_risk = 0.0
            if (abs(uL) + abs(uR)) > 8.0 and mu_hat < 1.0:
                slip_risk = (1.0 - mu_hat) * 15.0
                
            energy_cost = (abs(uL) + abs(uR)) * 0.005 * self.dt
            
            # 6. Expected Free Energy G(a)
            G = (
                (cumulative_collision_risk * 3.5)
                + spin_penalty
                + reverse_penalty
                + idling_penalty
                + curvature_change_penalty
                + curvature_effort_cost
                + action_persistence_penalty
                + energy_cost
                + slip_risk
                - forward_velocity_bonus
                - goal_progress_reward
                - steering_bias_bonus
                - corridor_centering_bonus
                - straight_bonus
            )
            
            coll_prob = 1.0 / (1.0 + math.exp(min(10.0, (dist_0_50s - 0.35) * 8.0)))
            
            evaluations[name] = {
                "action": act,
                "expected_free_energy": float(G),
                "predicted_trajectory": sim_traj,
                "predicted_progress_m": float(goal_progress_reward),
                "predicted_risk": float(cumulative_collision_risk),
                "predicted_slip_risk": float(slip_risk),
                "curvature": float(curv),
                "pred_dist_0_25s": float(round(dist_0_25s, 3)),
                "pred_dist_0_50s": float(round(dist_0_50s, 3)),
                "pred_dist_1_00s": float(round(dist_1_00s, 3)),
                "collision_probability": float(round(coll_prob, 3)),
                "spin_eligible": is_dead_end_trapped
            }
            
        best_candidate = min(evaluations, key=lambda k: evaluations[k]["expected_free_energy"])
        
        return {
            "best_action_name": best_candidate,
            "best_action_cmd": evaluations[best_candidate]["action"],
            "best_expected_free_energy": evaluations[best_candidate]["expected_free_energy"],
            "candidates": evaluations,
            "spin_eligible": is_dead_end_trapped
        }
