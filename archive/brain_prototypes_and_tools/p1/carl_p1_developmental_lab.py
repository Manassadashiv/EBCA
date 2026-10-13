"""
brain/p1/carl_p1_developmental_lab.py — Phase 1 Developmental Laboratory Environment

Manages the physical MuJoCo simulation, developmental affordance configuration,
and perturbation schedule across repeated developmental episodes.
"""

import os
import math
import random
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import mujoco

from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer


class CarlP1DevelopmentalLab:
    """
    Physical laboratory environment executing controlled developmental experiments.
    """
    def __init__(self, xml_path: str = r"D:\ebca\world\vessel_kinetic.xml"):
        self.xml_path = xml_path
        self.hal = MuJoCoHardwareAbstractionLayer(xml_path)
        self.model = self.hal.model
        self.data = self.hal.data
        
        # Cache geom indices
        self.geom_names = {self.model.geom(i).name: i for i in range(self.model.ngeom)}
        self.body_names = {self.model.body(i).name: i for i in range(self.model.nbody)}
        
        # Resource Target Coordinates
        self.food_coords = (3.2, 0.0)

    def configure_environment(self, env_id: str, episode_num: int, seed: int):
        """
        Configures physical obstacle layout and affordance barriers based on environment ID and episode phase:
        - Phase 1 (Episodes 1-5): Baseline Experience (Central Route A Open)
        - Phase 2 (Episodes 6-10): Perturbed Environment (Central Route A Blocked)
        - Phase 3 (Episodes 11-15): Revisit / Generalization (Central Route A Re-opened)
        """
        np.random.seed(seed)
        random.seed(seed)
        
        # Reset all movable bodies to parking coordinates (10, 10)
        for b_name in ['obj_cube_0', 'obj_cube_1', 'obj_ball_0', 'hazard_cube']:
            if b_name in self.body_names:
                self.model.body_pos[self.body_names[b_name]] = [10.0, 10.0, 0.05]
                
        # Clear all internal corridor walls to default parking
        for g_name, g_id in self.geom_names.items():
            if g_name.startswith("lwall_"):
                self.model.geom_pos[g_id] = [10.0, 10.0, 0.25]
                
        # Set Food Resource Beacon Position
        if 'food' in self.geom_names:
            food_gid = self.geom_names['food']
            self.model.geom_pos[food_gid] = [self.food_coords[0], self.food_coords[1], 0.12]
            
        # Determine Perturbation State based on Episode Number
        is_perturbed = (6 <= episode_num <= 10)
        
        if env_id == "ENV_1_BIFURCATION_CANONICAL":
            # Outer corridor guiding walls
            if 'lwall_h_0_1' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_h_0_1']] = [1.5, 2.2, 0.25]
            if 'lwall_h_1_1' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_h_1_1']] = [1.5, -2.2, 0.25]
                
            # Lateral island walls defining Route A, Route B (North), and Route C (South)
            if 'lwall_v_2_0' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_v_2_0']] = [1.5, 1.1, 0.25]
            if 'lwall_v_2_2' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_v_2_2']] = [1.5, -1.1, 0.25]
                
            # Central Route A Barrier
            if is_perturbed:
                # Place blocking barrier in Route A at x=1.8, y=0.0
                if 'lwall_v_0_2' in self.geom_names:
                    self.model.geom_pos[self.geom_names['lwall_v_0_2']] = [1.8, 0.0, 0.25]
            else:
                # Open Route A: Park barrier away
                if 'lwall_v_0_2' in self.geom_names:
                    self.model.geom_pos[self.geom_names['lwall_v_0_2']] = [10.0, 10.0, 0.25]
                    
        elif env_id == "ENV_2_ASYMMETRIC_OFFSET":
            # Asymmetric lateral shift (+0.7m north shift)
            if 'lwall_h_0_1' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_h_0_1']] = [1.5, 2.5, 0.25]
            if 'lwall_h_1_1' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_h_1_1']] = [1.5, -1.8, 0.25]
                
            if 'lwall_v_2_0' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_v_2_0']] = [1.5, 1.8, 0.25]
            if 'lwall_v_2_2' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_v_2_2']] = [1.5, -0.6, 0.25]
                
            if is_perturbed:
                if 'lwall_v_0_2' in self.geom_names:
                    self.model.geom_pos[self.geom_names['lwall_v_0_2']] = [1.8, 0.5, 0.25]
            else:
                if 'lwall_v_0_2' in self.geom_names:
                    self.model.geom_pos[self.geom_names['lwall_v_0_2']] = [10.0, 10.0, 0.25]
                    
        elif env_id == "ENV_3_FRICTIONAL_TRANSITION":
            # Same geometry as ENV_1, but floor friction modulated
            if 'lwall_h_0_1' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_h_0_1']] = [1.5, 2.2, 0.25]
            if 'lwall_h_1_1' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_h_1_1']] = [1.5, -2.2, 0.25]
            if 'lwall_v_2_0' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_v_2_0']] = [1.5, 1.1, 0.25]
            if 'lwall_v_2_2' in self.geom_names:
                self.model.geom_pos[self.geom_names['lwall_v_2_2']] = [1.5, -1.1, 0.25]
                
            if is_perturbed:
                if 'lwall_v_0_2' in self.geom_names:
                    self.model.geom_pos[self.geom_names['lwall_v_0_2']] = [1.8, 0.0, 0.25]
            else:
                if 'lwall_v_0_2' in self.geom_names:
                    self.model.geom_pos[self.geom_names['lwall_v_0_2']] = [10.0, 10.0, 0.25]

    def reset_robot_pose(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0):
        """
        Resets CARL's chassis pose and zeros velocities.
        """
        self.hal.reset()
        deck_bid = self.model.body('drive_deck').id
        
        # Freejoint qpos: [x, y, z, qw, qx, qy, qz]
        jnt_adr = self.model.jnt_qposadr[self.model.body_jntadr[deck_bid]]
        qw = math.cos(yaw / 2.0)
        qz = math.sin(yaw / 2.0)
        
        self.data.qpos[jnt_adr:jnt_adr+7] = [x, y, 0.052, qw, 0.0, 0.0, qz]
        
        # Zero all velocities
        self.data.qvel[:] = 0.0
        self.data.qacc[:] = 0.0
        
        # Physics forward settle
        for _ in range(30):
            mujoco.mj_step(self.model, self.data)
