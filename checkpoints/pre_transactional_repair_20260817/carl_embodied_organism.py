"""
brain/carl_embodied_organism.py — Complete Embodied Sensorimotor, Instrument & Expressive Engine

Treats the entire physical embodiment as CARL's active body:
1. Actuator Inventory & Control: 6 active DOF (left wheel, right wheel, hip pitch, hip roll, neck sweep, head pan)
2. Proprioception: Reads joint positions, velocities, actuator torques, tire contact forces, floating-base IMU
3. Active Sensing & Attention: Directs head pan/tilt, retina camera, and sonar rays to minimize perceptual uncertainty
4. Coordinated Motor Primitives: Walk, Turn, Look, Inspect, Search, Approach, Avoid, Swirl-Away, Recover, Express
5. Functional Affect & Expressiveness: Maps internal computational states (Curious, Excited, Caution, Satisfaction, Aversion, Social Attention)
   to coordinated, physically stable head/torso body language and simulated audio output.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List

@dataclass
class EmbodiedSensoryState:
    # Proprioception
    wheel_w_L: float = 0.0
    wheel_w_R: float = 0.0
    hip_pitch: float = 0.0
    hip_roll: float = 0.0
    neck_pitch: float = 0.0
    head_yaw: float = 0.0
    
    # Actuator Torques
    tau_wheel_L: float = 0.0
    tau_wheel_R: float = 0.0
    tau_hip_pitch: float = 0.0
    tau_hip_roll: float = 0.0
    tau_neck: float = 0.0
    tau_head: float = 0.0
    
    # Ground & Contact Classification
    wheel_contacts_L: int = 0
    wheel_contacts_R: int = 0
    caster_contacts: int = 0
    robot_wall_contacts: int = 0
    robot_obstacle_contacts: int = 0
    chassis_floor_contacts: int = 0
    has_body_collision: bool = False
    ncon: int = 0
    
    # IMU / Floating Base
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    speed: float = 0.0
    
    # Range / Sonar / Active Vision
    sonar_distances: np.ndarray = None
    min_obstacle_dist: float = 10.0
    target_visible: bool = False
    target_bearing: Optional[float] = None
    target_dist: Optional[float] = None
    
    # Active Attention & Uncertainty
    visual_uncertainty: float = 0.0
    spatial_entropy: float = 0.0


class CarlEmbodiedOrganism:
    """
    Unified Embodied Controller managing all 6 actuators, active sensing, proprioception, and body language.
    """
    def __init__(self, dt: float = 0.0333):
        self.dt = dt
        
        # Actuator targets (6 DOF)
        self.target_w_L = 0.0
        self.target_w_R = 0.0
        self.target_hip_pitch = 0.0
        self.target_hip_roll = 0.0
        self.target_neck_pitch = 0.0
        self.target_head_yaw = 0.0
        
        # Smoothed actual motor commands (S-curve filtered)
        self.cmd_w_L = 0.0
        self.cmd_w_R = 0.0
        self.accel_w_L = 0.0
        self.accel_w_R = 0.0
        
        # Head joint filters
        self.cmd_hip_pitch = 0.0
        self.cmd_hip_roll = 0.0
        self.cmd_neck_pitch = 0.0
        self.cmd_head_yaw = 0.0
        
        # Audio / Tone State
        self.current_audio_frequency_hz = 0.0
        self.current_audio_pattern = "SILENT"
        
        # Active Attention State
        self.gaze_target_yaw = 0.0
        self.gaze_target_pitch = 0.0
        self.scan_phase = 0.0
        
        # Expressive Body State
        self.affect_state = "NEUTRAL"
        self.expressive_intensity = 0.0
        
        # Physical Design Limits
        self.max_w = 12.0          # rad/s wheel speed
        self.max_accel = 10.0      # rad/s^2 wheel accel
        self.max_jerk = 30.0       # rad/s^3 wheel jerk
        self.limit_hip_pitch = (-0.15, 0.15)
        self.limit_hip_roll = (-0.06, 0.06)
        self.limit_neck_pitch = (-0.6, 0.7)
        self.limit_head_yaw = (-1.4, 1.4)

    def read_proprioception(self, hal) -> EmbodiedSensoryState:
        """
        Reads complete physical state from MuJoCo simulator sensors and joints.
        """
        model = hal.model
        data = hal.data
        
        # 1. Wheels
        wL_adr = model.joint('w_left').dofadr[0]
        wR_adr = model.joint('w_right').dofadr[0]
        wL = float(data.qvel[wL_adr])
        wR = float(data.qvel[wR_adr])
        
        # 2. Torso / Neck / Head
        hp_adr = model.joint('hip_pitch').qposadr[0]
        hr_adr = model.joint('hip_roll').qposadr[0]
        nk_adr = model.joint('neck_sweep').qposadr[0]
        hd_adr = model.joint('head_pan').qposadr[0]
        
        q_hp = float(data.qpos[hp_adr])
        q_hr = float(data.qpos[hr_adr])
        q_nk = float(data.qpos[nk_adr])
        q_hd = float(data.qpos[hd_adr])
        
        # 3. Torques
        tau_wL = float(data.actuator_force[0])
        tau_wR = float(data.actuator_force[1])
        tau_hp = float(data.actuator_force[2]) if len(data.actuator_force) > 2 else 0.0
        tau_hr = float(data.actuator_force[3]) if len(data.actuator_force) > 3 else 0.0
        tau_nk = float(data.actuator_force[4]) if len(data.actuator_force) > 4 else 0.0
        tau_hd = float(data.actuator_force[5]) if len(data.actuator_force) > 5 else 0.0
        
        # 4. Floating Base IMU
        x, y, yaw = hal.get_robot_pos()
        qbase_adr = model.joint('spatial_identity').qposadr[0]
        z = float(data.qpos[qbase_adr + 2])
        qw = float(data.qpos[qbase_adr + 3])
        qx = float(data.qpos[qbase_adr + 4])
        qy = float(data.qpos[qbase_adr + 5])
        qz = float(data.qpos[qbase_adr + 6])
        
        roll = math.atan2(2 * (qw * qx + qy * qz), 1 - 2 * (qx**2 + qy**2))
        pitch = math.asin(np.clip(2 * (qw * qy - qz * qx), -1.0, 1.0))
        
        cvel_x = float(data.cvel[model.body('drive_deck').id][3])
        cvel_y = float(data.cvel[model.body('drive_deck').id][4])
        speed = math.sqrt(cvel_x**2 + cvel_y**2)
        
        # 5. Precise Physical Contact & Collision Classification
        wheel_contacts_L = 0
        wheel_contacts_R = 0
        caster_contacts = 0
        robot_wall_contacts = 0
        robot_obstacle_contacts = 0
        chassis_floor_contacts = 0
        
        robot_geom_names = {
            "chassis_core", "chassis_shell", "sonar_hub", "torso_shell", "torso_collar",
            "chest_core_led", "neck_post", "head_shell", "visor_mat", "ear_L", "ear_R",
            "eye_retina_L", "eye_retina_R"
        }
        
        for ci in range(data.ncon):
            c = data.contact[ci]
            g1 = model.geom(c.geom1).name if c.geom1 >= 0 else ""
            g2 = model.geom(c.geom2).name if c.geom2 >= 0 else ""
            
            # Left wheel with floor
            if ("tire_L" in (g1, g2)) and ("floor" in (g1, g2)):
                wheel_contacts_L += 1
            # Right wheel with floor
            elif ("tire_R" in (g1, g2)) and ("floor" in (g1, g2)):
                wheel_contacts_R += 1
            # Casters with floor
            elif ("floor" in (g1, g2)) and (g1 == "" or g2 == "" or "caster" in g1 or "caster" in g2):
                caster_contacts += 1
            # Robot chassis / upper body with floor
            elif any(rg in (g1, g2) for rg in robot_geom_names) and ("floor" in (g1, g2)):
                chassis_floor_contacts += 1
            # Robot body/wheels with walls
            elif ("wall" in g1 or "wall" in g2) and (any(rg in (g1, g2) for rg in robot_geom_names) or "tire" in g1 or "tire" in g2):
                robot_wall_contacts += 1
            # Robot body/wheels with dynamic obstacles / props
            elif any(obs in (g1, g2) for obs in ["hazard", "dynamic_hazard", "gcube", "gball"]) and (any(rg in (g1, g2) for rg in robot_geom_names) or "tire" in g1 or "tire" in g2):
                robot_obstacle_contacts += 1
                
        has_body_collision = (robot_wall_contacts > 0 or robot_obstacle_contacts > 0 or chassis_floor_contacts > 0)
        
        # 6. Sonar Rangefinder (15-ray high-density directional scan with 0 deg center ray)
        sonar_rays = []
        angles = np.linspace(-math.pi * 0.666, math.pi * 0.666, 15)
        for ang in angles:
            ray_yaw = yaw + ang
            ray_dir = np.array([math.cos(ray_yaw), math.sin(ray_yaw)])
            ray_dist = 5.0
            
            # Check intersection against boundary walls
            # North wall (y = 5.0), South wall (y = -5.0), East wall (x = 5.0), West wall (x = -5.0)
            if ray_dir[0] > 1e-4:
                ray_dist = min(ray_dist, (2.60 - x) / ray_dir[0])
            elif ray_dir[0] < -1e-4:
                ray_dist = min(ray_dist, (-2.60 - x) / ray_dir[0])
                
            if ray_dir[1] > 1e-4:
                ray_dist = min(ray_dist, (2.60 - y) / ray_dir[1])
            elif ray_dir[1] < -1e-4:
                ray_dist = min(ray_dist, (-2.60 - y) / ray_dir[1])
                
            # Check intersection against internal obstacle geoms and props using exact AABB box slab method
            for i in range(model.ngeom):
                gname = model.geom(i).name
                if ("wall" in gname or "hazard" in gname or "gcube" in gname or "gball" in gname) and "wg_" not in gname and gname != "floor":
                    gpos = data.geom_xpos[i][:2]
                    gsize = model.geom_size[i][:2]
                    
                    # If geom is hidden at (99, 99), ignore
                    if abs(gpos[0]) > 10.0 or abs(gpos[1]) > 10.0:
                        continue
                        
                    # 2D Box Slab Intersection
                    gx_min, gx_max = gpos[0] - gsize[0], gpos[0] + gsize[0]
                    gy_min, gy_max = gpos[1] - gsize[1], gpos[1] + gsize[1]
                    
                    dx = ray_dir[0] if abs(ray_dir[0]) > 1e-5 else (1e-5 if ray_dir[0] >= 0 else -1e-5)
                    dy = ray_dir[1] if abs(ray_dir[1]) > 1e-5 else (1e-5 if ray_dir[1] >= 0 else -1e-5)
                    
                    tx1 = (gx_min - x) / dx
                    tx2 = (gx_max - x) / dx
                    t_min_x = min(tx1, tx2)
                    t_max_x = max(tx1, tx2)
                    
                    ty1 = (gy_min - y) / dy
                    ty2 = (gy_max - y) / dy
                    t_min_y = min(ty1, ty2)
                    t_max_y = max(ty1, ty2)
                    
                    t_enter = max(t_min_x, t_min_y)
                    t_exit = min(t_max_x, t_max_y)
                    
                    if t_exit >= t_enter and t_exit > 0.0:
                        hit_d = t_enter if t_enter > 0.0 else 0.02
                        ray_dist = min(ray_dist, max(0.02, hit_d))
                            
            sonar_rays.append(float(np.clip(ray_dist, 0.05, 5.0)))
            
        sonar_rays = np.array(sonar_rays)
        
        # 7. Active Optical Vision (FOV Cone +/- 45 deg, Max Range 3.5m)
        target_visible = False
        target_dist_val = None
        target_bearing_val = None
        
        if 'food' in [model.geom(i).name for i in range(model.ngeom)]:
            food_pos = data.geom_xpos[model.geom('food').id][:2]
            dx = food_pos[0] - x
            dy = food_pos[1] - y
            tdist = math.sqrt(dx**2 + dy**2)
            tangle = math.atan2(dy, dx)
            # Head-centered bearing
            gaze_yaw = yaw + q_hd
            heading_err = (tangle - gaze_yaw + math.pi) % (2 * math.pi) - math.pi
            
            # Visible only if inside optical cone and within sight range
            if abs(heading_err) <= math.radians(45.0) and tdist <= 3.5:
                target_visible = True
                target_dist_val = float(tdist)
                target_bearing_val = float(heading_err)
        
        return EmbodiedSensoryState(
            wheel_w_L=wL, wheel_w_R=wR,
            hip_pitch=q_hp, hip_roll=q_hr, neck_pitch=q_nk, head_yaw=q_hd,
            tau_wheel_L=tau_wL, tau_wheel_R=tau_wR,
            tau_hip_pitch=tau_hp, tau_hip_roll=tau_hr, tau_neck=tau_nk, tau_head=tau_hd,
            wheel_contacts_L=wheel_contacts_L, wheel_contacts_R=wheel_contacts_R,
            caster_contacts=caster_contacts, robot_wall_contacts=robot_wall_contacts,
            robot_obstacle_contacts=robot_obstacle_contacts, chassis_floor_contacts=chassis_floor_contacts,
            has_body_collision=has_body_collision,
            ncon=data.ncon,
            pos_x=x, pos_y=y, pos_z=z, yaw=yaw, roll=roll, pitch=pitch, speed=speed,
            sonar_distances=sonar_rays,
            min_obstacle_dist=float(np.min(sonar_rays)),
            target_visible=target_visible,
            target_bearing=target_bearing_val,
            target_dist=target_dist_val
        )

    def set_affect_state(self, affect: str, intensity: float = 1.0):
        """
        Sets the functional affect state for body language expression.
        Supported states: NEUTRAL, CURIOUS, EXCITED, CAUTIOUS, THREAT_AVERSION, SATISFACTION, SOCIAL_ATTENTION
        """
        self.affect_state = affect
        self.expressive_intensity = np.clip(intensity, 0.0, 1.0)

    def execute_motor_primitive(self, primitive: str, params: Dict[str, Any] = None):
        """
        Executes a coordinated multi-actuator motor primitive.
        """
        p = params if params is not None else {}
        speed = p.get("speed", 6.0)
        steer = p.get("steer", 0.0)
        
        if primitive == "WALK":
            self.target_w_L = speed - steer
            self.target_w_R = speed + steer
            self.target_hip_pitch = 0.02 # Slight forward lean for natural locomotion
            self.target_hip_roll = 0.0
            self.target_neck_pitch = 0.0
            self.target_head_yaw = 0.0
            
        elif primitive == "TURN":
            yaw_rate = p.get("yaw_rate", 4.0)
            self.target_w_L = -yaw_rate
            self.target_w_R = yaw_rate
            self.target_head_yaw = np.clip(-yaw_rate * 0.15, -0.6, 0.6) # Anticipatory gaze in turn direction
            
        elif primitive == "LOOK":
            target_yaw = p.get("yaw", 0.0)
            target_pitch = p.get("pitch", 0.0)
            self.target_w_L = 0.0
            self.target_w_R = 0.0
            self.target_head_yaw = np.clip(target_yaw, self.limit_head_yaw[0], self.limit_head_yaw[1])
            self.target_neck_pitch = np.clip(target_pitch, self.limit_neck_pitch[0], self.limit_neck_pitch[1])
            
        elif primitive == "INSPECT":
            # Slow approach + targeted head sweep + range scan
            self.target_w_L = 1.5
            self.target_w_R = 1.5
            self.scan_phase += self.dt * 2.5
            self.target_head_yaw = 0.4 * math.sin(self.scan_phase)
            self.target_neck_pitch = 0.2 + 0.1 * math.cos(self.scan_phase)
            
        elif primitive == "SEARCH":
            # Slow rotation + wide head pan scan
            self.scan_phase += self.dt * 3.0
            self.target_w_L = -2.0
            self.target_w_R = 2.0
            self.target_head_yaw = 0.8 * math.sin(self.scan_phase)
            self.target_neck_pitch = 0.15 * math.cos(self.scan_phase * 0.5)
            
        elif primitive == "AVOID":
            # Steer away from obstacle
            avoid_dir = p.get("dir", 1.0)
            self.target_w_L = -3.0 * avoid_dir
            self.target_w_R = 3.0 * avoid_dir
            self.target_head_yaw = 0.5 * avoid_dir
            self.target_hip_pitch = -0.04 # Slight back lean
            
        elif primitive == "SWIRL_AWAY":
            # Rapid controlled turn-away from threat + backward acceleration
            self.target_w_L = -5.0
            self.target_w_R = 5.0
            self.target_hip_pitch = -0.06
            self.target_head_yaw = -0.7
            self.current_audio_pattern = "ALARM_CHIRP"
            self.current_audio_frequency_hz = 880.0
            
        elif primitive == "RECOVER":
            # Stabilize chassis to level, zero wheel torque, neutral head posture
            self.target_w_L = 0.0
            self.target_w_R = 0.0
            self.target_hip_pitch = 0.0
            self.target_hip_roll = 0.0
            self.target_neck_pitch = 0.0
            self.target_head_yaw = 0.0
            
        elif primitive == "EXPRESS":
            self._apply_affect_expression()

    def _apply_affect_expression(self):
        """
        Translates internal affect state into coordinated physical head/body posture.
        """
        I = self.expressive_intensity
        self.scan_phase += self.dt * 4.0
        
        if self.affect_state == "CURIOUS":
            # Head tilt (hip_roll + head_yaw) + subtle inquisitive pitch
            self.target_hip_roll = 0.03 * I
            self.target_head_yaw = 0.35 * math.sin(self.scan_phase * 0.5) * I
            self.target_neck_pitch = (0.20 + 0.08 * math.sin(self.scan_phase)) * I
            self.current_audio_pattern = "INQUISITIVE_WARBLE"
            self.current_audio_frequency_hz = 520.0 + 120.0 * math.sin(self.scan_phase)
            
        elif self.affect_state == "EXCITED":
            # Rapid rhythmic head bob + cheerful high-tone chirps + small celebratory spin
            self.target_neck_pitch = 0.15 * math.sin(self.scan_phase * 2.0) * I
            self.target_head_yaw = 0.25 * math.cos(self.scan_phase * 1.5) * I
            self.target_w_L = 3.0 * math.sin(self.scan_phase) * I
            self.target_w_R = -3.0 * math.sin(self.scan_phase) * I
            self.current_audio_pattern = "EXCITED_TRILL"
            self.current_audio_frequency_hz = 1040.0 + 300.0 * math.sin(self.scan_phase * 2.0)
            
        elif self.affect_state == "CAUTIOUS":
            # Low, careful posture, slow head scan, low hum
            self.target_neck_pitch = -0.15 * I
            self.target_hip_pitch = -0.03 * I
            self.target_head_yaw = 0.5 * math.sin(self.scan_phase * 0.4) * I
            self.current_audio_pattern = "CAUTION_DRONE"
            self.current_audio_frequency_hz = 220.0
            
        elif self.affect_state == "THREAT_AVERSION":
            # Quick retraction posture, head tilted away from threat
            self.target_hip_pitch = -0.08 * I
            self.target_head_yaw = -0.70 * I
            self.target_neck_pitch = 0.30 * I
            self.current_audio_pattern = "WARNING_PULSE"
            self.current_audio_frequency_hz = 780.0
            
        elif self.affect_state == "SATISFACTION":
            # Smooth gentle nod + harmonious chime
            self.target_neck_pitch = 0.12 * math.cos(self.scan_phase) * I
            self.target_hip_roll = 0.0
            self.target_head_yaw = 0.0
            self.current_audio_pattern = "CHIME_HARMONY"
            self.current_audio_frequency_hz = 659.25 # E5 tone
            
        elif self.affect_state == "SOCIAL_ATTENTION":
            # Gaze directed forward-upward at user/companion + soft trill
            self.target_neck_pitch = 0.35 * I
            self.target_head_yaw = 0.0
            self.target_hip_pitch = 0.02 * I
            self.current_audio_pattern = "GREETING_PURR"
            self.current_audio_frequency_hz = 440.0

    def step_embodiment(self, hal) -> Dict[str, Any]:
        """
        Integrates S-curve filter for wheels and position servos for upper body,
        then commands the MuJoCo HAL interface.
        """
        # 1. S-Curve Motor Rate Limiting for Wheels
        max_delta_a = self.max_jerk * self.dt
        
        # Left Wheel
        des_a_L = (self.target_w_L - self.cmd_w_L) / self.dt
        des_a_L = np.clip(des_a_L, -self.max_accel, self.max_accel)
        delta_a_L = np.clip(des_a_L - self.accel_w_L, -max_delta_a, max_delta_a)
        self.accel_w_L = np.clip(self.accel_w_L + delta_a_L, -self.max_accel, self.max_accel)
        self.cmd_w_L = np.clip(self.cmd_w_L + self.accel_w_L * self.dt, -self.max_w, self.max_w)
        
        # Right Wheel
        des_a_R = (self.target_w_R - self.cmd_w_R) / self.dt
        des_a_R = np.clip(des_a_R, -self.max_accel, self.max_accel)
        delta_a_R = np.clip(des_a_R - self.accel_w_R, -max_delta_a, max_delta_a)
        self.accel_w_R = np.clip(self.accel_w_R + delta_a_R, -self.max_accel, self.max_accel)
        self.cmd_w_R = np.clip(self.cmd_w_R + self.accel_w_R * self.dt, -self.max_w, self.max_w)
        
        # 2. Position Servos for Upper Body Joints (Exponential smoothing)
        alpha_servo = 0.25
        self.cmd_hip_pitch += alpha_servo * (self.target_hip_pitch - self.cmd_hip_pitch)
        self.cmd_hip_roll += alpha_servo * (self.target_hip_roll - self.cmd_hip_roll)
        self.cmd_neck_pitch += alpha_servo * (self.target_neck_pitch - self.cmd_neck_pitch)
        self.cmd_head_yaw += alpha_servo * (self.target_head_yaw - self.cmd_head_yaw)
        
        # Clip to hardware joint limits
        self.cmd_hip_pitch = float(np.clip(self.cmd_hip_pitch, self.limit_hip_pitch[0], self.limit_hip_pitch[1]))
        self.cmd_hip_roll = float(np.clip(self.cmd_hip_roll, self.limit_hip_roll[0], self.limit_hip_roll[1]))
        self.cmd_neck_pitch = float(np.clip(self.cmd_neck_pitch, self.limit_neck_pitch[0], self.limit_neck_pitch[1]))
        self.cmd_head_yaw = float(np.clip(self.cmd_head_yaw, self.limit_head_yaw[0], self.limit_head_yaw[1]))
        
        # 3. Write Commands to MuJoCo HAL
        # Write wheel velocities
        hal.data.ctrl[0] = self.cmd_w_L
        hal.data.ctrl[1] = self.cmd_w_R
        
        # Write position actuators if present in model
        if len(hal.data.ctrl) >= 6:
            hal.data.ctrl[2] = self.cmd_hip_pitch
            hal.data.ctrl[3] = self.cmd_hip_roll
            hal.data.ctrl[4] = self.cmd_neck_pitch
            hal.data.ctrl[5] = self.cmd_head_yaw
            
        return {
            "cmd_w_L": self.cmd_w_L,
            "cmd_w_R": self.cmd_w_R,
            "cmd_hip_pitch": self.cmd_hip_pitch,
            "cmd_hip_roll": self.cmd_hip_roll,
            "cmd_neck_pitch": self.cmd_neck_pitch,
            "cmd_head_yaw": self.cmd_head_yaw,
            "affect_state": self.affect_state,
            "audio_pattern": self.current_audio_pattern,
            "audio_freq_hz": self.current_audio_frequency_hz
        }
