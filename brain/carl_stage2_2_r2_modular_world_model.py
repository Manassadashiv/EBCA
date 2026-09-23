"""
brain/carl_stage2_2_r2_modular_world_model.py — Module 3 & Integrated Modular World Model
Classification: [CORE SYSTEM] Modular Action-Conditioned Predictive World Model (Stage 2.2-R2)

Role:
Integrates the three causally isolated modules into the complete CARL-PredWorld-v2 system:
1. Module 1: Kinematic Body & Ego-Dynamics Predictor (M_body)
2. Module 2: Allocentric Spatial Occupancy Memory (M_env)
3. Module 3: Prospective Sensory Generator & Collision Oracle (M_sensor)

Also implements the three developmental control baselines:
- ARCH-2: No-Memory Control (ablates spatial memory substrate)
- ARCH-3: No-Body Control (ablates kinematic chassis forward model)
- ARCH-4: Parameter-Matched Monolithic GRU Control (reproduces Phase 1 for direct comparison)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, List

from brain.carl_stage2_2_r2_body_model import KinematicBodyModel
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory


class ProspectiveSensoryGenerator(nn.Module):
    """
    Module 3 (M_sensor): Prospective Sensory Generator & Collision Hazard Oracle.
    
    Inputs:
    - clearance_profile: 15-D prospective obstacle clearance queried from M_env at pose p_{t+H}
    - prospective_body: 9-D prospective chassis state emitted by M_body at tick t+H
    
    CRITICAL CAUSAL INVARIANT:
    Current sonar s_t is STRICTLY WITHHELD. Module 3 has no pathway to copy s_t into the future.
    """
    def __init__(
        self,
        sonar_dim: int = 15,
        proprio_dim: int = 9,
        hidden_dim: int = 128
    ):
        super().__init__()
        self.sonar_dim = sonar_dim
        self.proprio_dim = proprio_dim

        self.net = nn.Sequential(
            nn.Linear(sonar_dim + proprio_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU()
        )

        # Sonar prediction head
        self.head_sonar = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Linear(hidden_dim // 2, sonar_dim)
        )

        # Prospective collision hazard oracle head (predicts probability of collision in [0, 1])
        self.head_collision = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        clearance_profile: torch.Tensor,
        prospective_body: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Synthesizes predicted future sonars and prospective collision hazard.
        
        Args:
            clearance_profile: (batch, 15) prospective obstacle clearance
            prospective_body: (batch, 9) prospective proprioceptive state
            
        Returns:
            pred_sonar: (batch, 15) in meters [0.0, 5.0]
            pred_collision: (batch, 1) probability [0.0, 1.0]
        """
        x_in = torch.cat([clearance_profile, prospective_body], dim=-1)
        feat = self.net(x_in)

        delta_sonar = self.head_sonar(feat)
        # Bounded prospective sonar prediction centered around geometric ray clearance
        pred_sonar = torch.clamp(clearance_profile + delta_sonar, 0.0, 5.0)

        pred_collision = self.head_collision(feat)

        return pred_sonar, pred_collision


class CARLModularPredictiveWorldModel(nn.Module):
    """
    ARCH-1: Full Decoupled Modular Action-Conditioned Predictive World Model.
    Causally chains: Action -> Body Model -> Ego-Pose -> Spatial Memory Query -> Sensory Generator.
    """
    def __init__(
        self,
        sonar_dim: int = 15,
        proprio_dim: int = 9,
        action_dim: int = 6,
        hidden_dim: int = 128,
        grid_size: int = 128,
        resolution: float = 0.10
    ):
        super().__init__()
        self.sonar_dim = sonar_dim
        self.proprio_dim = proprio_dim
        self.action_dim = action_dim

        self.body_model = KinematicBodyModel(
            proprio_dim=proprio_dim,
            action_dim=action_dim,
            hidden_dim=hidden_dim
        )
        self.occupancy_memory = SpatialOccupancyMemory(
            grid_size=grid_size,
            resolution=resolution,
            max_range=5.0,
            num_sonar_rays=sonar_dim
        )
        self.sensory_generator = ProspectiveSensoryGenerator(
            sonar_dim=sonar_dim,
            proprio_dim=proprio_dim,
            hidden_dim=hidden_dim
        )

    def init_memory(self, batch_size: int, device: torch.device) -> torch.Tensor:
        """Initializes blank 2D occupancy grid anchored to internal origin (0, 0)."""
        return torch.zeros(batch_size, 2, self.occupancy_memory.grid_size, self.occupancy_memory.grid_size, device=device)

    def build_memory_from_history(
        self,
        sonars_history: torch.Tensor,
        actions_history: torch.Tensor,
        s_body_0: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Constructs internal occupancy grid from robot's own historical sensorimotor trajectory.
        
        Args:
            sonars_history: (batch, history_len, 15)
            actions_history: (batch, history_len, 6)
            s_body_0: (batch, 9) initial proprioception
            
        Returns:
            grid: (batch, 2, G, G) accumulated occupancy grid
            curr_pose: (batch, 3) current dead-reckoned pose [x, y, θ] at t_0
        """
        batch_size, hist_len, _ = actions_history.shape
        device = actions_history.device

        grid = self.init_memory(batch_size, device)
        _, _, poses_traj = self.body_model.unroll(s_body_0, actions_history)

        for t in range(hist_len):
            grid = self.occupancy_memory.accumulate_observations(
                grid,
                poses_traj[:, t, :],
                sonars_history[:, t, :]
            )

        curr_pose = poses_traj[:, -1, :]
        return grid, curr_pose

    def predict_rollout(
        self,
        grid: torch.Tensor,
        curr_pose: torch.Tensor,
        curr_s_body: torch.Tensor,
        future_actions: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Pure mental prospective rollout without external sensory peeking.
        
        Args:
            grid: (batch, 2, G, G) internal spatial cognitive map
            curr_pose: (batch, 3) current internal pose [x, y, θ]
            curr_s_body: (batch, 9) current body state
            future_actions: (batch, horizon, 6) prospective action plan
            
        Returns:
            Dict containing:
            - pred_sonars: (batch, horizon, 15)
            - pred_body: (batch, horizon, 9)
            - pred_collisions: (batch, horizon, 1)
            - prospective_poses: (batch, horizon, 3)
            - clearance_profiles: (batch, horizon, 15)
        """
        batch_size, horizon, _ = future_actions.shape
        device = future_actions.device

        # Step 1: Kinematic Body Rollout
        # Unroll displacement from current body state
        s_body_traj, delta_p_traj, rel_poses = self.body_model.unroll(curr_s_body, future_actions)

        # Shift relative poses by curr_pose in global allocentric frame
        prospective_poses_list = []
        for t in range(horizon):
            dx_rel = rel_poses[:, t, 0:1]
            dy_rel = rel_poses[:, t, 1:2]
            dtheta_rel = rel_poses[:, t, 2:3]

            theta_0 = curr_pose[:, 2:3]
            cos_0 = torch.cos(theta_0)
            sin_0 = torch.sin(theta_0)

            abs_x = curr_pose[:, 0:1] + dx_rel * cos_0 - dy_rel * sin_0
            abs_y = curr_pose[:, 1:2] + dx_rel * sin_0 + dy_rel * cos_0
            abs_theta = curr_pose[:, 2:3] + dtheta_rel

            prospective_poses_list.append(torch.cat([abs_x, abs_y, abs_theta], dim=-1).unsqueeze(1))

        prospective_poses = torch.cat(prospective_poses_list, dim=1)

        # Step 2: Query Prospective Clearance from Spatial Memory along trajectory
        pred_sonars_list = []
        pred_collisions_list = []
        clearance_list = []

        for t in range(horizon):
            pose_t = prospective_poses[:, t, :]
            body_t = s_body_traj[:, t, :]

            clearance_t = self.occupancy_memory.query_clearance(grid, pose_t)
            sonar_t, coll_t = self.sensory_generator(clearance_t, body_t)

            clearance_list.append(clearance_t.unsqueeze(1))
            pred_sonars_list.append(sonar_t.unsqueeze(1))
            pred_collisions_list.append(coll_t.unsqueeze(1))

        return {
            "pred_sonars": torch.cat(pred_sonars_list, dim=1),
            "pred_body": s_body_traj,
            "pred_collisions": torch.cat(pred_collisions_list, dim=1),
            "prospective_poses": prospective_poses,
            "clearance_profiles": torch.cat(clearance_list, dim=1)
        }


# =====================================================================
# DEVELOPMENTAL CONTROL ARCHITECTURES (ARCH-2, ARCH-3, ARCH-4)
# =====================================================================

class ARCH2NoMemoryControl(nn.Module):
    """
    ARCH-2 (No-Memory Control Baseline):
    Ablates the spatial occupancy memory. Retains Body Model (M_body) and Sensory Generator (M_sensor),
    but passes a blank/unmapped clearance profile (5.0m constant) to the generator.
    """
    def __init__(self, sonar_dim: int = 15, proprio_dim: int = 9, action_dim: int = 6, hidden_dim: int = 128):
        super().__init__()
        self.sonar_dim = sonar_dim
        self.body_model = KinematicBodyModel(proprio_dim, action_dim, hidden_dim)
        self.sensory_generator = ProspectiveSensoryGenerator(sonar_dim, proprio_dim, hidden_dim)

    def predict_rollout(self, grid: torch.Tensor, curr_pose: torch.Tensor, curr_s_body: torch.Tensor, future_actions: torch.Tensor) -> Dict[str, torch.Tensor]:
        batch_size, horizon, _ = future_actions.shape
        device = future_actions.device

        s_body_traj, _, _ = self.body_model.unroll(curr_s_body, future_actions)
        # Dummy unmapped clearance (5.0m everywhere)
        blank_clearance = torch.full((batch_size, self.sonar_dim), 5.0, device=device)

        pred_sonars_list = []
        pred_coll_list = []
        for t in range(horizon):
            sonar_t, coll_t = self.sensory_generator(blank_clearance, s_body_traj[:, t, :])
            pred_sonars_list.append(sonar_t.unsqueeze(1))
            pred_coll_list.append(coll_t.unsqueeze(1))

        return {
            "pred_sonars": torch.cat(pred_sonars_list, dim=1),
            "pred_body": s_body_traj,
            "pred_collisions": torch.cat(pred_coll_list, dim=1)
        }


class ARCH3NoBodyControl(nn.Module):
    """
    ARCH-3 (No-Body Control Baseline):
    Ablates the kinematic chassis model. Predicts displacement directly from action u_t via linear
    kinematics without tracking chassis momentum, deceleration, or body proprioception.
    """
    def __init__(self, sonar_dim: int = 15, proprio_dim: int = 9, action_dim: int = 6, hidden_dim: int = 128, grid_size: int = 128, resolution: float = 0.10):
        super().__init__()
        self.sonar_dim = sonar_dim
        self.proprio_dim = proprio_dim
        self.occupancy_memory = SpatialOccupancyMemory(grid_size, resolution, 5.0, sonar_dim)
        self.sensory_generator = ProspectiveSensoryGenerator(sonar_dim, proprio_dim, hidden_dim)
        self.k_trans = 1.1398
        self.track_width = 0.20
        self.dt = 0.030

    def predict_rollout(self, grid: torch.Tensor, curr_pose: torch.Tensor, curr_s_body: torch.Tensor, future_actions: torch.Tensor) -> Dict[str, torch.Tensor]:
        batch_size, horizon, _ = future_actions.shape
        device = future_actions.device

        # Naive instantaneous velocity without momentum / coasting
        pred_sonars_list = []
        pred_coll_list = []
        dummy_body = curr_s_body.clone()
        p = curr_pose.clone()

        for t in range(horizon):
            u = future_actions[:, t, :]
            u_L = u[:, 0:1]
            u_R = u[:, 1:2]
            # Zero coasting physics: if u=0, displacement is instantly 0
            dx_local = 0.5 * (u_L + u_R) * self.k_trans * self.dt
            dy_local = torch.zeros_like(dx_local)
            dtheta = (u_R - u_L) / self.track_width * self.dt

            theta = p[:, 2:3]
            new_x = p[:, 0:1] + dx_local * torch.cos(theta)
            new_y = p[:, 1:2] + dx_local * torch.sin(theta)
            new_theta = p[:, 2:3] + dtheta
            p = torch.cat([new_x, new_y, new_theta], dim=-1)

            clearance = self.occupancy_memory.query_clearance(grid, p)
            sonar_t, coll_t = self.sensory_generator(clearance, dummy_body)
            pred_sonars_list.append(sonar_t.unsqueeze(1))
            pred_coll_list.append(coll_t.unsqueeze(1))

        return {
            "pred_sonars": torch.cat(pred_sonars_list, dim=1),
            "pred_body": dummy_body.unsqueeze(1).repeat(1, horizon, 1),
            "pred_collisions": torch.cat(pred_coll_list, dim=1)
        }


class ARCH4MatchedMonolithicGRU(nn.Module):
    """
    ARCH-4 (Matched Monolithic GRU Baseline):
    Parameter-matched monolithic GRU that takes full state (s_t, u_t) directly to predict s_{t+1},
    reproducing the monolithic recurrent architecture of Phase 1.
    """
    def __init__(self, sonar_dim: int = 15, proprio_dim: int = 9, action_dim: int = 6, hidden_dim: int = 256):
        super().__init__()
        self.sonar_dim = sonar_dim
        self.proprio_dim = proprio_dim
        in_dim = sonar_dim + proprio_dim + action_dim

        self.gru = nn.GRU(in_dim, hidden_dim, batch_first=True)
        self.head_sonar = nn.Linear(hidden_dim, sonar_dim)
        self.head_body = nn.Linear(hidden_dim, proprio_dim)
        self.head_coll = nn.Sequential(nn.Linear(hidden_dim, 1), nn.Sigmoid())

    def predict_rollout(self, s_0: torch.Tensor, future_actions: torch.Tensor) -> Dict[str, torch.Tensor]:
        batch_size, horizon, _ = future_actions.shape
        pred_sonars = []
        pred_bodies = []
        pred_colls = []

        curr_s = s_0  # (batch, sonar_dim + proprio_dim)
        h = None

        for t in range(horizon):
            u_t = future_actions[:, t, :]
            x_in = torch.cat([curr_s, u_t], dim=-1).unsqueeze(1)
            out, h = self.gru(x_in, h)
            feat = out.squeeze(1)

            s_sonar = torch.clamp(curr_s[:, :self.sonar_dim] + self.head_sonar(feat), 0.0, 5.0)
            s_body = curr_s[:, self.sonar_dim:self.sonar_dim+self.proprio_dim] + self.head_body(feat)
            c_pred = self.head_coll(feat)

            pred_sonars.append(s_sonar.unsqueeze(1))
            pred_bodies.append(s_body.unsqueeze(1))
            pred_colls.append(c_pred.unsqueeze(1))

            curr_s = torch.cat([s_sonar, s_body], dim=-1)

        return {
            "pred_sonars": torch.cat(pred_sonars, dim=1),
            "pred_body": torch.cat(pred_bodies, dim=1),
            "pred_collisions": torch.cat(pred_colls, dim=1)
        }
