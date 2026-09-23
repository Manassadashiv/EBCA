"""
brain/p1_r1/carl_p1r1_developmental_lab.py — P1-R1 Developmental Physics Laboratory

Manages MuJoCo physics simulation, dynamic obstacle perturbation schedules,
camera rendering (720p 30 FPS), and reproducible environment configurations.
"""

from typing import Dict, Any, Tuple, Optional
import os
import math
import numpy as np
import mujoco

from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer


class CarlP1R1DevelopmentalLab:
    """
    P1-R1 Developmental Laboratory Environment.
    """
    def __init__(self, xml_path: str = "world/vessel_kinetic.xml", dt: float = 0.0333):
        self.xml_path = xml_path
        self.dt = dt
        self.hal = MuJoCoHardwareAbstractionLayer(xml_path)
        self.model = self.hal.model
        self.data = self.hal.data
        
        # Build geom index map
        self.geom_names = {self.model.geom(i).name: i for i in range(self.model.ngeom)}
        
        # Default food coordinates
        self.food_coords = (1.60, 0.0)
        
        # Setup offscreen renderer and tracking camera for HD 720p video
        self.renderer = mujoco.Renderer(self.model, height=720, width=1280)
        self.cam = mujoco.MjvCamera()
        self.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.cam.trackbodyid = self.model.body('drive_deck').id
        self.cam.distance = 2.80
        self.cam.elevation = -30.0
        self.cam.azimuth = 140.0
        
        # Initialize default arena layout (park unused walls)
        self.park_unused_walls()
        self.set_food_position(1.60, 0.0)

    def park_unused_walls(self):
        """Parks decorative/unused walls far outside the active arena."""
        for g_name, g_id in self.geom_names.items():
            if g_name.startswith("lwall_"):
                self.model.geom_pos[g_id] = [10.0, 10.0, 0.25]

    def set_food_position(self, x: float, y: float):
        """Sets the 3D position of the food resource beacon."""
        self.food_coords = (x, y)
        if "food" in self.geom_names:
            food_id = self.geom_names["food"]
            self.model.geom_pos[food_id] = [x, y, 0.12]

    def configure_environment(self, env_id: str, episode_num: int):
        """
        Configures physical arena geometry based on environment ID and episode phase:
        - Phase A (Ep 1-5): Baseline Open (Barrier parked at 10.0, 10.0)
        - Phase B (Ep 6-10): Perturbation (Barrier placed to block Route A)
        - Phase C (Ep 11-15): Revisit Open (Barrier parked at 10.0, 10.0)
        """
        self.park_unused_walls()
        self.set_food_position(1.60, 0.0)
        
        is_perturbed = (6 <= episode_num <= 10)
        
        # Default floor friction
        if "floor" in self.geom_names:
            self.model.geom_friction[self.geom_names["floor"]][0] = 1.0
            
        barrier_id = self.geom_names.get("lwall_v_0_2")
        
        if env_id == "ENV_1_BIFURCATION_CANONICAL":
            if is_perturbed and barrier_id is not None:
                self.model.geom_pos[barrier_id] = [0.80, 0.0, 0.25]
                
        elif env_id == "ENV_2_ASYMMETRIC_OFFSET":
            if is_perturbed and barrier_id is not None:
                self.model.geom_pos[barrier_id] = [0.80, 0.35, 0.25]
                
        elif env_id == "ENV_3_FRICTIONAL_TRANSITION":
            if is_perturbed:
                if barrier_id is not None:
                    self.model.geom_pos[barrier_id] = [0.80, 0.0, 0.25]
                if "floor" in self.geom_names:
                    self.model.geom_friction[self.geom_names["floor"]][0] = 0.80

    def reset_robot_pose(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0):
        """Resets CARL's chassis pose and zeros velocities."""
        self.hal.reset()
        deck_bid = self.model.body('drive_deck').id
        jnt_adr = self.model.jnt_qposadr[self.model.body_jntadr[deck_bid]]
        qw = math.cos(yaw / 2.0)
        qz = math.sin(yaw / 2.0)
        self.data.qpos[jnt_adr:jnt_adr+7] = [x, y, 0.052, qw, 0.0, 0.0, qz]
        self.data.qvel[:] = 0.0
        self.data.qacc[:] = 0.0
        for _ in range(30):
            mujoco.mj_step(self.model, self.data)

    def render_frame(self) -> np.ndarray:
        """Renders an RGB 1280x720 frame from the third-person tracking camera."""
        self.renderer.update_scene(self.data, camera=self.cam)
        return self.renderer.render()
