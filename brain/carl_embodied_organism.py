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
        
        # 4. Floating Base Pose (Fallback to zeros if unprivileged HAL is used)
        if hasattr(hal, "get_robot_pos"):
            x, y, yaw = hal.get_robot_pos()
        else:
            x, y, yaw = 0.0, 0.0, 0.0
        # Stage 3.0 Hygiene: Calibrated chassis rest height (0.05m); eliminate privileged qpos z read
        z = 0.05
        qbase_adr = model.joint('spatial_identity').qposadr[0]
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
        robot_body_names = {
            "drive_deck", "w_caster_front", "w_caster_rear", "wheel_L", "wheel_R",
            "torso", "neck_parallel_link", "head"
        }
        chassis_upper_geoms = {
            "chassis_bumper", "chassis_core", "chassis_shell", "sonar_hub",
            "torso_shell", "torso_collar", "chest_core_led", "neck_post",
            "head_dome", "head_visor", "eye_L", "eye_R", "ear_L", "ear_R"
        }
        
        for ci in range(data.ncon):
            c = data.contact[ci]
            g1_id = c.geom1
            g2_id = c.geom2
            g1 = model.geom(g1_id).name if g1_id >= 0 else ""
            g2 = model.geom(g2_id).name if g2_id >= 0 else ""
            b1 = model.body(model.geom_bodyid[g1_id]).name if g1_id >= 0 else ""
            b2 = model.body(model.geom_bodyid[g2_id]).name if g2_id >= 0 else ""
            
            is_r1 = b1 in robot_body_names
            is_r2 = b2 in robot_body_names
            
            # Skip robot internal self-contacts if any
            if is_r1 and is_r2:
                continue
                
            # If neither is robot, skip
            if not (is_r1 or is_r2):
                continue
                
            robot_g = g1 if is_r1 else g2
            other_g = g2 if is_r1 else g1
            robot_b = b1 if is_r1 else b2
            other_b = b2 if is_r1 else b1
            
            if other_g == "floor":
                if "tire_L" in robot_g:
                    wheel_contacts_L += 1
                elif "tire_R" in robot_g:
                    wheel_contacts_R += 1
                elif "caster" in robot_b:
                    caster_contacts += 1
                elif robot_g in chassis_upper_geoms:
                    chassis_floor_contacts += 1
            elif "wall" in other_g or "lwall" in other_g:
                robot_wall_contacts += 1
            elif any(obs in other_g for obs in ["hazard", "dynamic_hazard", "gcube", "gball"]) or "obj_" in other_b or "hazard" in other_b:
                robot_obstacle_contacts += 1
                
        has_body_collision = (robot_wall_contacts > 0 or robot_obstacle_contacts > 0 or chassis_floor_contacts > 0)
        
        # 6. Sonar Rangefinder (Use native C++ HAL rangefinder sensors)
        if hasattr(hal, "read_sensors"):
            raw_s = hal.read_sensors()
            sonar_rays = np.array(raw_s[:15], dtype=np.float32)
        else:
            sonar_rays = np.full(15, 5.0, dtype=np.float32)
            
        # 7. Active Optical Vision (Purged privileged simulator coordinate read; reserved for Stage 3.7 eye_cam)
        target_visible = False
        target_dist_val = None
        target_bearing_val = None
        
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
