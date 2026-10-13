"""
brain/carl_stage1_hal.py — Anonymous 6-Channel Hardware Abstraction Layer (HAL-911)
Classification: [ARCHITECTURAL INVARIANT] Anonymous Embodiment Interface

Exposes CARL's physical MuJoCo embodiment via strictly anonymous vector slices:
- Sensory vector: s ∈ R^25 (15 sonar rays, 3 IMU accel, 3 IMU gyro, 3 joint proprio, 1 battery)
- Motor command vector: u ∈ [-1.0, 1.0]^6 (6 continuous actuator channels)

No semantic labels ("left wheel", "torso", "neck") are provided to the cognitive core.
Supports runtime channel permutation to verify cognitive permutation invariance.
"""

import os
import math
import numpy as np
from typing import Tuple, Dict, Any, Optional
import mujoco


class CarlStage1HAL:
    """
    Hardware Abstraction Layer decoupling CARL's developmental brain from MuJoCo physics.
    Provides unlabelled continuous vector interfaces for true developmental grounding.
    """
    # [NUMERICAL / PHYSICAL CONSTANT] Channel dimensions
    SENSORY_DIM: int = 25
    ACTUATOR_DIM: int = 6

    def __init__(self, xml_path: Optional[str] = None, open_space: bool = False, headless: bool = True):
        """
        Initializes MuJoCo physics engine and HAL interfaces.
        """
        if xml_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            xml_path = os.path.join(base_dir, "world", "vessel_kinetic.xml")

        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"[HAL-911] MuJoCo model file not found: {xml_path}")

        self.xml_path = xml_path
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.n_substeps: int = 3
        # Exact control loop timestep derived directly from model configuration (e.g. 0.01s * 3 = 0.03s)
        self.dt: float = float(self.model.opt.timestep * self.n_substeps)
        self.DT: float = self.dt
        
        if open_space:
            # Relocate all obstacles and maze corridors to prevent collisions during open-space navigation
            for i in range(self.model.ngeom):
                name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, i)
                if name and (name.startswith("lwall_") or name in ["dynamic_hazard", "food", "laser_dot"]):
                    self.model.geom_pos[i] = [99.0, 99.0, -99.0]
            for i in range(self.model.nbody):
                name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, i)
                if name and name in ["hazard_cube", "obj_cube_0", "obj_cube_1", "obj_ball_0", "laser_target"]:
                    self.model.body_pos[i] = [99.0, 99.0, -99.0]

        self.data = mujoco.MjData(self.model)

        # Internal physical mapping array (C-API indices -> HAL channel)
        # HAL channel 0: Left wheel motor velocity
        # HAL channel 1: Right wheel motor velocity
        # HAL channel 2: Head Pan (yaw) position servo
        # HAL channel 3: Neck Tilt (pitch) position servo
        # HAL channel 4: Torso/Hip Pitch hinge servo
        # HAL channel 5: Torso/Hip Roll hinge servo
        self._permutation = np.arange(self.ACTUATOR_DIM, dtype=int)
        self._sensor_permutation = np.arange(self.SENSORY_DIM, dtype=int)
        
        # Omnidirectional Optical ToF: 15 laser distance rays spanning full 360-deg ring [-168 deg, +168 deg]
        # Step: 24.0 deg (Ray 7 = 0.0 deg forward, Rays 0 & 14 = +/-168 deg rear bumper coverage)
        self._sonar_angles = np.deg2rad(np.linspace(-168.0, 168.0, 15, endpoint=True))
        
        # Identify all bodies and geoms belonging strictly to CARL's kinematic tree
        root_body_id = self.model.body("drive_deck").id
        self.carl_body_ids = set()
        for b_id in range(self.model.nbody):
            curr = b_id
            while curr > 0:
                if curr == root_body_id:
                    self.carl_body_ids.add(b_id)
                    break
                curr = self.model.body_parentid[curr]

        self.carl_geom_ids = {
            g_id for g_id in range(self.model.ngeom)
            if self.model.geom_bodyid[g_id] in self.carl_body_ids
        }
        self.floor_geom_id = self.model.geom("floor").id
        try:
            self.bumper_geom_id = self.model.geom("chassis_bumper").id
        except Exception:
            self.bumper_geom_id = -1
        self.tire_geom_ids = {
            self.model.geom("tire_L").id,
            self.model.geom("tire_R").id
        }

        # Battery state
        self._battery_level: float = 1.0
        self._battery_drain_rate: float = 0.0001  # per tick

        # Offscreen camera renderer cache
        self._renderer: Optional[mujoco.Renderer] = None

        # Internal tracking
        self.tick_count: int = 0
        self.reset()

    def reset(self, qpos: Optional[np.ndarray] = None, qvel: Optional[np.ndarray] = None):
        """Resets physical simulation to ground-settled equilibrium state."""
        mujoco.mj_resetData(self.model, self.data)

        # Set freejoints to valid unit quaternions
        for j in range(self.model.njnt):
            if self.model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
                qa = self.model.jnt_qposadr[j]
                self.data.qpos[qa + 3: qa + 7] = [1.0, 0.0, 0.0, 0.0]

        # Robot resting height on casters
        q_addr = int(self.model.joint("spatial_identity").qposadr[0])
        self.data.qpos[q_addr: q_addr + 3] = [0.0, 0.0, 0.05291]
        self.data.qpos[q_addr + 3: q_addr + 7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qpos[q_addr + 7:] = 0.0
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0

        if qpos is not None:
            self.data.qpos[:len(qpos)] = qpos
        if qvel is not None:
            self.data.qvel[:len(qvel)] = qvel

        self._battery_level = 1.0
        self.tick_count = 0
        mujoco.mj_forward(self.model, self.data)

    def set_channel_permutation(self, perm: np.ndarray):
        """
        [VALIDATION CRITERION] Shuffles actuator channel routing to verify
        that cognitive discovery is invariant to physical wiring order.
        """
        assert len(perm) == self.ACTUATOR_DIM, "Permutation must match actuator dimension"
        assert set(perm) == set(range(self.ACTUATOR_DIM)), "Permutation must be a valid permutation of 0..5"
        self._permutation = np.array(perm, dtype=int)

    def read_sensors(self) -> np.ndarray:
        """
        Reads 25-D unlabelled sensory vector:
        - [0:15]   = 15 Sonar ray distances [0.0, 5.0] meters
        - [15:18]  = 3 IMU linear acceleration (m/s^2)
        - [18:21]  = 3 IMU angular velocities (rad/s)
        - [21:24]  = 3 Joint proprioceptive positions (rad)
        - [24:25]  = 1 Battery state [0.0, 1.0]
        """
        s = np.zeros(self.SENSORY_DIM, dtype=np.float64)

        # 1. Cast 15 Sonar Rays (Radial offset outside chassis ring R=0.14m)
        q_addr = int(self.model.joint("spatial_identity").qposadr[0])
        x_pos = float(self.data.qpos[q_addr])
        y_pos = float(self.data.qpos[q_addr + 1])
        z_pos = float(self.data.qpos[q_addr + 2]) + 0.10  # sensor hub height
        qw = self.data.qpos[q_addr + 3]
        qz = self.data.qpos[q_addr + 6]
        yaw = 2.0 * math.atan2(qz, qw)

        geomid = np.array([-1], dtype=np.int32)
        R_hull = 0.14  # radial offset outside chassis boundary

        for idx, angle in enumerate(self._sonar_angles):
            ray_yaw = yaw + angle
            vec = np.array([math.cos(ray_yaw), math.sin(ray_yaw), 0.0], dtype=np.float64)
            pnt = np.array([x_pos + R_hull * math.cos(ray_yaw), y_pos + R_hull * math.sin(ray_yaw), z_pos], dtype=np.float64)
            dist = mujoco.mj_ray(self.model, self.data, pnt, vec, None, 1, -1, geomid)
            if dist < 0 or dist > 5.0:
                dist = 5.0
            s[idx] = dist

        # 2. IMU Linear Acceleration (Body frame with gravitational bias)
        v_addr = int(self.model.joint("spatial_identity").dofadr[0])
        accel_raw = self.data.qacc[v_addr: v_addr + 3] if hasattr(self.data, 'qacc') else np.zeros(3)
        s[15:18] = np.clip(accel_raw, -50.0, 50.0)

        # 3. IMU Angular Velocities (Gyro)
        gyro_raw = self.data.qvel[v_addr + 3: v_addr + 6]
        s[18:21] = np.clip(gyro_raw, -20.0, 20.0)

        # 4. Joint Proprioception (Hip pitch, neck tilt, head pan)
        j_hip = float(self.data.qpos[self.model.joint("hip_pitch").qposadr[0]])
        j_neck = float(self.data.qpos[self.model.joint("neck_sweep").qposadr[0]])
        j_head = float(self.data.qpos[self.model.joint("head_pan").qposadr[0]])
        s[21] = j_hip
        s[22] = j_neck
        s[23] = j_head

        # 5. Battery State
        self._battery_level = max(0.0, self._battery_level - self._battery_drain_rate)
        s[24] = self._battery_level

        # Apply sensor permutation (anonymous channel routing)
        return s[self._sensor_permutation]

    def set_sensor_permutation(self, permutation: np.ndarray):
        """Sets the anonymous sensor routing permutation P_sens."""
        assert len(permutation) == self.SENSORY_DIM, f"Sensor permutation must have length {self.SENSORY_DIM}"
        self._sensor_permutation = np.array(permutation, dtype=int)

    def set_permutation(self, permutation: np.ndarray):
        """Sets the anonymous actuator routing permutation P_act."""
        assert len(permutation) == self.ACTUATOR_DIM, f"Actuator permutation must have length {self.ACTUATOR_DIM}"
        self._permutation = np.array(permutation, dtype=int)

    def set_floor_friction(self, friction: float):
        """Sets floor and tire friction coefficients for in-situ slip / traction loss experiments."""
        self.model.geom_friction[self.floor_geom_id, 0] = friction
        for t_id in self.tire_geom_ids:
            self.model.geom_friction[t_id, 0] = friction

    def get_carl_contact_info(self) -> Dict[str, int]:
        """
        Counts contacts strictly involving geoms belonging to CARL's kinematic tree.
        Excludes background toy/obstacle collisions and internal self-collisions.
        """
        ext_contacts = 0
        floor_contacts = 0
        tire_floor_contacts = 0
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            in1 = c.geom1 in self.carl_geom_ids
            in2 = c.geom2 in self.carl_geom_ids
            # External contact: exactly one geom is CARL
            if (in1 and not in2) or (in2 and not in1):
                ext_contacts += 1
                other = c.geom2 if in1 else c.geom1
                if other == self.floor_geom_id:
                    floor_contacts += 1
                    carl_geom = c.geom1 if in1 else c.geom2
                    if carl_geom in self.tire_geom_ids:
                        tire_floor_contacts += 1
        return {
            "carl_contacts": ext_contacts,
            "floor_contacts": floor_contacts,
            "tire_floor_contacts": tire_floor_contacts,
        }

    def get_carl_impact_info(self) -> Dict[str, Any]:
        """
        Distinguishes damaging structural collisions (Fn > 15.0 N or penetration < -5mm)
        from compliant tangential cuticular boundary sliding (tactile thigmotaxis).
        Grounding: Jayaram & Full (PNAS 2016) & Phase 0 Invariant 2.
        """
        damaging_impacts = 0
        grazing_contacts = 0
        max_normal_force = 0.0
        c_force = np.zeros(6, dtype=np.float64)
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            in1 = c.geom1 in self.carl_geom_ids
            in2 = c.geom2 in self.carl_geom_ids
            if (in1 and not in2) or (in2 and not in1):
                other = c.geom2 if in1 else c.geom1
                if other != self.floor_geom_id:
                    mujoco.mj_contactForce(self.model, self.data, i, c_force)
                    fn = float(abs(c_force[0]))
                    if fn > max_normal_force:
                        max_normal_force = fn
                    carl_g = c.geom1 if in1 else c.geom2
                    is_bumper = (carl_g == self.bumper_geom_id)
                    if (is_bumper or fn <= 15.0) and c.dist >= -0.004:
                        grazing_contacts += 1
                    else:
                        damaging_impacts += 1
        return {
            "damaging_impacts": damaging_impacts,
            "grazing_contacts": grazing_contacts,
            "max_normal_force": max_normal_force,
        }

    def write_actuators(self, u: np.ndarray) -> np.ndarray:
        """
        Applies continuous 6-D command vector u ∈ [-1.0, 1.0]^6 to physical actuators.
        Returns the clipped executed command vector.
        """
        assert len(u) == self.ACTUATOR_DIM, f"Command must be {self.ACTUATOR_DIM}-D"
        u_clamped = np.clip(u, -1.0, 1.0)
        
        # Apply internal permutation (HAL routing)
        u_routed = u_clamped[self._permutation]

        # Physical Control Scalings:
        # Wheel velocity actuators (ctrl 0, 1): scaled to max ±25.0 rad/s
        self.data.ctrl[0] = float(u_routed[0] * 25.0)  # Left Wheel
        self.data.ctrl[1] = float(u_routed[1] * 25.0)  # Right Wheel
        
        # Servo position actuators (ctrl 2..5): scaled to physical joint ranges
        self.data.ctrl[2] = float(u_routed[4] * 0.45)   # Hip/Torso Pitch (range ±0.45 rad)
        self.data.ctrl[3] = float(u_routed[5] * 0.30)   # Hip/Torso Roll (range ±0.30 rad)
        self.data.ctrl[4] = float(u_routed[3] * 0.50)   # Neck Tilt/Pitch (range ±0.50 rad)
        self.data.ctrl[5] = float(u_routed[2] * 1.20)   # Head Pan/Yaw (range ±1.20 rad)

        return u_clamped

    def step(self, u: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Advances physical simulation by 1 control timestep (30 Hz = 3 substeps of dt=0.01s).
        Returns: (s_next, diagnostics_dict)
        """
        u_executed = self.write_actuators(u)

        # Step MuJoCo physics (3 substeps of 0.01s = 0.03s per control tick)
        for _ in range(3):
            mujoco.mj_step(self.model, self.data)

        self.tick_count += 1
        s_next = self.read_sensors()
        diag = self.get_diagnostics()
        diag["u_executed"] = u_executed

        return s_next, diag

    def read_camera(self, camera_name: str = "eye_cam", width: int = 64, height: int = 64) -> np.ndarray:
        """
        Unprivileged offscreen retinal ingestion from CARL's physical eye_cam.
        Returns uint8 RGB array of shape (height, width, 3).
        """
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.model, height=height, width=width)
        self._renderer.update_scene(self.data, camera=camera_name)
        return self._renderer.render()

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns ground-truth physical state diagnostics for validation audits."""
        q_addr = int(self.model.joint("spatial_identity").qposadr[0])
        v_addr = int(self.model.joint("spatial_identity").dofadr[0])

        x = float(self.data.qpos[q_addr])
        y = float(self.data.qpos[q_addr + 1])
        z = float(self.data.qpos[q_addr + 2])

        qw = float(self.data.qpos[q_addr + 3])
        qx = float(self.data.qpos[q_addr + 4])
        qy = float(self.data.qpos[q_addr + 5])
        qz = float(self.data.qpos[q_addr + 6])

        # Euler angles from quaternion
        sinr_cosp = 2.0 * (qw * qx + qy * qz)
        cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (qw * qy - qz * qx)
        pitch = math.asin(np.clip(sinp, -1.0, 1.0))

        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        vx = float(self.data.qvel[v_addr])
        vy = float(self.data.qvel[v_addr + 1])
        vz = float(self.data.qvel[v_addr + 2])
        speed = math.sqrt(vx * vx + vy * vy)

        contact_info = self.get_carl_contact_info()
        has_traction = contact_info["tire_floor_contacts"] > 0

        return {
            "tick": self.tick_count,
            "pos_x": x,
            "pos_y": y,
            "pos_z": z,
            "roll": roll,
            "pitch": pitch,
            "yaw": yaw,
            "speed": speed,
            "ncon": self.data.ncon,
            "carl_contacts": contact_info["carl_contacts"],
            "floor_contacts": contact_info["floor_contacts"],
            "tire_floor_contacts": contact_info["tire_floor_contacts"],
            "has_ground_traction": has_traction,
            "battery": self._battery_level,
        }
