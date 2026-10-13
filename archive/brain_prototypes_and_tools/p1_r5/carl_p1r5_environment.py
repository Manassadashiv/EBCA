"""
brain/p1_r5/carl_p1r5_environment.py — Embodied MuJoCo Physics Environment for P1-R5 Causal Validation
"""

import os
import math
import mujoco
import numpy as np
from typing import Tuple, Dict, Any, Optional

from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer


class CarlP1R5Environment:
    """
    MuJoCo Physics Simulation Harness for Phase 1-R5 STDP Plasticity Experiments.
    """

    def __init__(self, xml_path: str = "d:/ebca/world/vessel_kinetic.xml"):
        self.xml_path = os.path.abspath(xml_path)
        self.hal = MuJoCoHardwareAbstractionLayer(self.xml_path)
        self.model = self.hal.model
        self.data = self.hal.data

        self.geom_names = {self.model.geom(i).name: i for i in range(self.model.ngeom)}
        self.body_names = {self.model.body(i).name: i for i in range(self.model.nbody)}

        self.food_coords = (2.20, 0.00)
        self.dt = 0.0333

        # Tracking Camera
        self.renderer = mujoco.Renderer(self.model, height=720, width=1280)
        self.cam = mujoco.MjvCamera()
        self.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.cam.trackbodyid = self.model.body("drive_deck").id
        self.cam.distance = 2.60
        self.cam.elevation = -30.0
        self.cam.azimuth = 140.0

        self.park_unused_walls()
        self.set_food_position(2.20, 0.00)

    def park_unused_walls(self):
        """Parks decorative/unused walls far outside the active arena without mutual overlap."""
        for idx, (g_name, g_id) in enumerate(self.geom_names.items()):
            if g_name.startswith("lwall_"):
                self.model.geom_pos[g_id] = [30.0 + idx * 2.0, 30.0, 0.25]
        if "hazard_cube" in self.body_names:
            self.model.body_pos[self.body_names["hazard_cube"]] = [60.0, 60.0, 0.15]
        mujoco.mj_forward(self.model, self.data)

    def set_food_position(self, x: float, y: float):
        """Sets the 3D position of the food resource beacon."""
        self.food_coords = (x, y)
        if "food" in self.geom_names:
            food_id = self.geom_names["food"]
            self.model.geom_pos[food_id] = [x, y, 0.12]
        mujoco.mj_forward(self.model, self.data)

    def configure_environment(self, episode_num: int, reversal: bool = False):
        """
        Configures physical arena geometry based on STDP developmental progression:
        - Ep 1 (Experience): Route B barrier at (1.45, -0.55), Route A open.
        - Ep 2 (Recurrence): Route B barrier at (1.45, -0.55), Route A open.
        - Ep 3 (Reversal): If reversal=True, barrier moves to Route A (1.45, +0.55) to test synaptic adaptation.
        """
        self.park_unused_walls()
        self.set_food_position(2.20, 0.00)

        # 1. Symmetric entrance divider at (0.65, 0.00, 0.25)
        if "lwall_v_2_2" in self.geom_names:
            w_id = self.geom_names["lwall_v_2_2"]
            self.model.geom_size[w_id] = [0.05, 0.25, 0.25]
            self.model.geom_pos[w_id] = [0.65, 0.00, 0.25]

        # 2. Symmetric outer guide walls at y = +-0.85, x = 0.65
        if "lwall_h_0_1" in self.geom_names:
            ng_id = self.geom_names["lwall_h_0_1"]
            self.model.geom_size[ng_id] = [0.45, 0.05, 0.25]
            self.model.geom_pos[ng_id] = [0.65, 0.85, 0.25]

        if "lwall_h_1_1" in self.geom_names:
            sg_id = self.geom_names["lwall_h_1_1"]
            self.model.geom_size[sg_id] = [0.45, 0.05, 0.25]
            self.model.geom_pos[sg_id] = [0.65, -0.85, 0.25]

        # 3. Symmetric dogleg baffles at x = 1.15, y = +-0.55
        if "lwall_v_3_1" in self.geom_names:
            nb_id = self.geom_names["lwall_v_3_1"]
            self.model.geom_size[nb_id] = [0.05, 0.25, 0.25]
            self.model.geom_pos[nb_id] = [1.15, 0.55, 0.25]

        if "lwall_v_2_0" in self.geom_names:
            sb_id = self.geom_names["lwall_v_2_0"]
            self.model.geom_size[sb_id] = [0.05, 0.25, 0.25]
            self.model.geom_pos[sb_id] = [1.15, -0.55, 0.25]

        # 4. Latent Hazard Barrier Placement
        if reversal and episode_num >= 6:
            if "lwall_v_0_2" in self.geom_names:
                hz_id = self.geom_names["lwall_v_0_2"]
                self.model.geom_size[hz_id] = [0.05, 0.25, 0.25]
                self.model.geom_pos[hz_id] = [1.45, 0.55, 0.25]
        else:
            if "lwall_v_0_2" in self.geom_names:
                hz_id = self.geom_names["lwall_v_0_2"]
                self.model.geom_size[hz_id] = [0.05, 0.25, 0.25]
                self.model.geom_pos[hz_id] = [1.45, -0.55, 0.25]

        mujoco.mj_forward(self.model, self.data)

    def reset_robot_pose(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0, settle_ticks: int = 10):
        """Resets CARL's chassis pose, zeros velocities, and performs physical settling."""
        self.hal.reset()
        deck_bid = self.model.body("drive_deck").id
        jnt_adr = self.model.jnt_qposadr[self.model.body_jntadr[deck_bid]]
        qw = math.cos(yaw / 2.0)
        qz = math.sin(yaw / 2.0)

        self.data.qpos[jnt_adr + 0] = x
        self.data.qpos[jnt_adr + 1] = y
        self.data.qpos[jnt_adr + 2] = 0.052
        self.data.qpos[jnt_adr + 3] = qw
        self.data.qpos[jnt_adr + 4] = 0.0
        self.data.qpos[jnt_adr + 5] = 0.0
        self.data.qpos[jnt_adr + 6] = qz

        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0
        mujoco.mj_forward(self.model, self.data)

        # Zero-torque gravity settling
        for _ in range(settle_ticks):
            self.hal.step()

        self.data.qvel[0] = 0.0
        self.data.qvel[1] = 0.0
        mujoco.mj_forward(self.model, self.data)

    def render_frame(self) -> np.ndarray:
        self.renderer.update_scene(self.data, camera=self.cam)
        return self.renderer.render()
