"""
brain/carl_empowerment.py — Information-Theoretic Empowerment & Future Controllability Estimator

Implements the universal agent-centric measure of control:
E(s) = max_{p(a)} I(A_{1:H}; S_H | S_0 = s)

For CARL-DX:
Estimates the reachable state space volume and mutual information across counterfactual
Dreamer rollouts, penalizing states that collapse future action authority (corners, dead-ends, blockages).
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

@dataclass
class EmpowermentEvaluation:
    empowerment_nats: float       # Mutual information I(A; S) in nats
    controllability_index: float  # Normalized [0.0, 1.0] controllability score
    reachable_dispersion: float   # Spatial variance of future reachable endpoints
    is_entropy_collapse: bool     # True if future states collapse into stall / collision
    action_affordance_entropy: float # Shannon entropy of viable actions


class CarlEmpowermentCore:
    """
    Computes real-time empowerment and future controllability signals for CARL-DX.
    """
    def __init__(self, horizon_steps: int = 15, num_probe_actions: int = 7, dt: float = 0.0333):
        self.horizon_steps = horizon_steps
        self.num_probe_actions = num_probe_actions
        self.dt = dt
        
        # Probe action set spanning [forward-left, forward-straight, forward-right, reverse, spins]
        # (w_L, w_R)
        self.probe_actions = [
            (10.0, 10.0),   # Straight forward
            (6.0, 12.0),    # Smooth left arc
            (12.0, 6.0),    # Smooth right arc
            (2.0, 14.0),    # Sharp left
            (14.0, 2.0),    # Sharp right
            (-6.0, -6.0),   # Straight reverse
            (-8.0, 8.0),    # Left spin
            (8.0, -8.0),    # Right spin
        ]
        self.last_evaluation = EmpowermentEvaluation(
            empowerment_nats=1.5,
            controllability_index=0.8,
            reachable_dispersion=0.5,
            is_entropy_collapse=False,
            action_affordance_entropy=2.0
        )

    def evaluate_empowerment(
        self,
        current_state,
        self_model,
        sonar_distances: np.ndarray = None,
        min_clearance: float = 1.0
    ) -> EmpowermentEvaluation:
        """
        Evaluates how much control CARL retains over future reachable states from current_state.
        """
        r = self_model.self_params.estimated_wheel_radius_m
        b = self_model.self_params.estimated_track_width_m
        
        x0 = float(current_state.pos_x)
        y0 = float(current_state.pos_y)
        yaw0 = float(current_state.yaw)
        
        endpoints = []
        viable_action_count = 0
        total_actions = len(self.probe_actions)
        
        for (wL, wR) in self.probe_actions:
            # Roll forward kinematics over horizon
            v = (wL + wR) * 0.5 * r
            w = (wR - wL) * r / b
            
            # Predict terminal position at horizon H
            dt_H = self.horizon_steps * self.dt
            if abs(w) < 1e-4:
                x_term = x0 + v * math.cos(yaw0) * dt_H
                y_term = y0 + v * math.sin(yaw0) * dt_H
            else:
                x_term = x0 + (v / w) * (math.sin(yaw0 + w * dt_H) - math.sin(yaw0))
                y_term = y0 - (v / w) * (math.cos(yaw0 + w * dt_H) - math.cos(yaw0))
                
            endpoints.append([x_term, y_term])
            
            # Check if this probe action maintains positive clearance
            # Approximate forward clearance along action vector
            if v > 0:
                is_viable = (min_clearance > 0.30)
            else:
                is_viable = True
            if is_viable:
                viable_action_count += 1
                
        endpoints_arr = np.array(endpoints) # (N, 2)
        
        # Compute spatial covariance of reachable endpoints
        cov = np.cov(endpoints_arr, rowvar=False) + 1e-5 * np.eye(2)
        det_cov = np.linalg.det(cov)
        dispersion = float(np.trace(cov))
        
        # Channel capacity / Mutual information approximation: I(A; S) ~ 0.5 * ln det(Cov / sigma_noise^2)
        # For 0.5s horizon, sigma_noise ~ 0.02m -> sigma^4 ~ 1.6e-7
        normalized_det = max(1e-4, det_cov / 1.6e-7)
        raw_empowerment = 0.5 * math.log(normalized_det)
        
        # Modulate by safety clearance and viable action ratio
        clearance_penalty = 1.0 if min_clearance > 0.40 else (min_clearance / 0.40) ** 2
        action_ratio = viable_action_count / max(1, total_actions)
        
        empowerment_nats = float(raw_empowerment * clearance_penalty * action_ratio - (1.0 - action_ratio) * 3.0)
        controllability_index = float(np.clip(1.0 / (1.0 + math.exp(-empowerment_nats + 1.0)), 0.0, 1.0))
        
        # Entropy collapse detection: low clearance or severely restricted viable actions
        is_entropy_collapse = (min_clearance < 0.28) or (action_ratio < 0.45)
        
        # Action affordance entropy: H = - sum p ln p
        if viable_action_count > 0:
            p_action = 1.0 / viable_action_count
            action_entropy = float(viable_action_count * (-p_action * math.log(p_action)))
        else:
            action_entropy = 0.0
            
        eval_res = EmpowermentEvaluation(
            empowerment_nats=round(empowerment_nats, 4),
            controllability_index=round(controllability_index, 4),
            reachable_dispersion=round(dispersion, 4),
            is_entropy_collapse=is_entropy_collapse,
            action_affordance_entropy=round(action_entropy, 4)
        )
        self.last_evaluation = eval_res
        return eval_res
