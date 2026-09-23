"""
brain/p1_r2/carl_p1r2_developmental_lab.py — Isolated Phase 1-R2 Physics & Environment Lab

Configures the 2-route bifurcation arena with physical solid reachability:
- Target food beacon at (1.80, 0.0).
- Central obstacle lwall_v_2_2 at (0.75, 0.0, 0.25) of half-size [0.05, 0.25, 0.25].
- Route 1 (North corridor): y in [+0.35, +1.50m].
- Route 2 (South corridor): y in [-1.50, -0.35m].
- Perturbation schedule:
  - Ep 1-2: Both routes open.
  - Ep 3: Route 2 (South) blocked by barrier lwall_v_0_2 at (0.75, -0.55), Route 1 (North) open.
  - Ep 4: Both routes open.
  - Ep 5: Route 2 (South) blocked again at (0.75, -0.55).
"""

import os
import math
import mujoco
import numpy as np
from typing import Dict, Any, Tuple, Optional

from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer


class CarlP1R2DevelopmentalLab:
    """
    MuJoCo Physics Simulation Harness for Phase 1-R2 Emergence Candidate Experiments.
    """
    def __init__(self, xml_path: str = "d:/ebca/world/vessel_kinetic.xml"):
        self.xml_path = os.path.abspath(xml_path)
        self.hal = MuJoCoHardwareAbstractionLayer(self.xml_path)
        self.model = self.hal.model
        self.data = self.hal.data
        
        self.geom_names = {self.model.geom(i).name: i for i in range(self.model.ngeom)}
        self.body_names = {self.model.body(i).name: i for i in range(self.model.nbody)}
        
        self.food_coords = (1.80, 0.0)
        
        # Offscreen renderer and tracking camera for HD 720p video
        self.renderer = mujoco.Renderer(self.model, height=720, width=1280)
        self.cam = mujoco.MjvCamera()
        self.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.cam.trackbodyid = self.model.body("drive_deck").id
        self.cam.distance = 2.80
        self.cam.elevation = -30.0
        self.cam.azimuth = 140.0
        
        self.park_unused_walls()
        self.set_food_position(1.80, 0.0)

    def park_unused_walls(self):
        """Parks decorative/unused walls far outside the active arena."""
        for g_name, g_id in self.geom_names.items():
            if g_name.startswith("lwall_"):
                self.model.geom_pos[g_id] = [10.0, 10.0, 0.25]
        if "hazard_cube" in self.body_names:
            self.model.body_pos[self.body_names["hazard_cube"]] = [10.0, 10.0, 0.15]
        mujoco.mj_forward(self.model, self.data)

    def set_food_position(self, x: float, y: float):
        """Sets the 3D position of the food resource beacon."""
        self.food_coords = (x, y)
        if "food" in self.geom_names:
            food_id = self.geom_names["food"]
            self.model.geom_pos[food_id] = [x, y, 0.12]
        mujoco.mj_forward(self.model, self.data)

    def configure_environment(self, episode_num: int):
        """
        Configures physical arena geometry based on episode structure:
        - Ep 1-2: Both routes open (Central obstacle at (0.75, 0.0))
        - Ep 3: South route blocked (Barrier at (0.75, -0.55), North Route open)
        - Ep 4: Both routes open (Barrier parked)
        - Ep 5: South route blocked (Barrier at (0.75, -0.55), North Route open)
        """
        self.park_unused_walls()
        self.set_food_position(1.80, 0.0)
        
        # 1. Central solid barrier separating North and South corridors (x=0.75, y=0.0, half-size 0.05x0.25x0.25)
        if "lwall_v_2_2" in self.geom_names:
            w_id = self.geom_names["lwall_v_2_2"]
            self.model.geom_size[w_id] = [0.05, 0.25, 0.25]
            self.model.geom_pos[w_id] = [0.75, 0.0, 0.25]
            
        # 2. Perturbation barrier blocking South Route on Episodes 3 and 5
        is_south_blocked = (episode_num in (3, 5))
        if is_south_blocked and "lwall_v_0_2" in self.geom_names:
            b_id = self.geom_names["lwall_v_0_2"]
            self.model.geom_size[b_id] = [0.05, 0.30, 0.25]
            self.model.geom_pos[b_id] = [0.75, -0.55, 0.25]
            
        mujoco.mj_forward(self.model, self.data)

    def reset_robot_pose(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0):
        """Resets CARL's chassis pose and zeros velocities."""
        self.hal.reset()
        deck_bid = self.model.body("drive_deck").id
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
