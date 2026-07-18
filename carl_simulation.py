"""
carl_simulation.py — EBCA Full Autonomous Simulation Runner (Modular SoC Design)

Integrates modular cognitive files using clean imports.
Unifies memory with zero-copy S_unified architecture (Apple Silicon concept).

Diagnostic ID Tracking (PHY-001..004, LSM-211..212, END-201..205,
MEM-101..104, WIT-401, MPC-511, IMA-601, CON-701, GIS-901, HAL-911)
"""

import sys
import os
import math
import numpy as np
import time
import traceback
import csv
import mujoco
import mujoco.viewer
import torch
import torchvision
import functools
import torch.nn as nn
from torchvision.models.detection.ssdlite import SSDLiteClassificationHead

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Imports from modular brain package
from brain.carl_reservoir import LiquidStateReservoir
from brain.carl_endocrine import EndocrineSystem
from brain.carl_reflex import SpikingReflexLayer
from brain.carl_grid_cells import GridCellModule, PlaceCellLayer
from torchvision.models.detection.ssdlite import SSDLite320_MobileNet_V3_Large_Weights


def get_ssdlite_model():
    model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(
        weights=SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
    )
    in_channels = [layer[0][0].in_channels for layer in model.head.classification_head.module_list]
    num_anchors = model.anchor_generator.num_anchors_per_location()
    norm_layer = functools.partial(nn.BatchNorm2d, eps=0.001, momentum=0.03)
    model.head.classification_head = SSDLiteClassificationHead(
        in_channels=in_channels,
        num_anchors=num_anchors,
        num_classes=4,
        norm_layer=norm_layer
    )
    return model


# ──────────────────────────────────────────────────────────────────────────
# HARDWARE INTERFACE ABSTRACTION LAYER (HAL-911)
# ──────────────────────────────────────────────────────────────────────────

class HardwareInterface:
    """Abstract interface for decoupling cognitive brain from physical/virtual vessel."""
    def read_sensors(self) -> np.ndarray:
        """Returns 25-D vector mapping [Sonar (24), Battery (1)]"""
        raise NotImplementedError

    def write_motors(self, torque_left: float, torque_right: float, neck_target: float):
        """Applies control signals directly to physical/virtual servos"""
        raise NotImplementedError


class SimulationHAL(HardwareInterface):
    """Concrete simulation implementation of the Hardware Abstraction Layer for Wall-E."""
    def __init__(self, xml_path: str, open_space: bool = False):
        try:
            self.model = mujoco.MjModel.from_xml_path(xml_path)
            # If open space training is enabled, move all internal walls out of the arena
            if open_space:
                for i in range(self.model.ngeom):
                    name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, i)
                    if name and name.startswith("lwall_"):
                        self.model.geom_pos[i] = [99.0, 99.0, -99.0]
                print("[HAL-911] Open space training enabled. All internal walls moved to safety.")
            self.data = mujoco.MjData(self.model)

            self.cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "eye_cam")
            if self.cam_id < 0:
                raise ValueError("Error: eye_cam camera not found in XML model!")
            self.robot_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "drive_deck")

            self.food_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "food")
            self.hazard_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "hazard_cube")

            self.cam_fov_h = 60.0
            self.img_width = 160
            self.img_height = 120

            self.sonar_angles = np.linspace(-np.pi, np.pi, 24, endpoint=False)
            self.battery_level = 1.0

            # Head pan joint address for camera-to-body frame transform
            self.head_pan_qposadr = int(self.model.joint("head_pan").qposadr[0])

            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.vision_model = get_ssdlite_model()
            weights_path = os.path.join(BASE_DIR, "memory", "carl_multi_object_vision.pt")
            if os.path.exists(weights_path):
                self.vision_model.load_state_dict(torch.load(weights_path, map_location=self.device))
                print(f"[VISION] Loaded trained multi-object SSD-Lite model on {self.device}")
            else:
                print(f"[VISION][WARNING] Trained weights not found at {weights_path}!")
            self.vision_model.to(self.device)
            self.vision_model.eval()

            self.offscreen_renderer = mujoco.Renderer(self.model, height=120, width=160)

            self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self.viewer.cam.azimuth = 45
            self.viewer.cam.elevation = -32
            self.viewer.cam.distance = 7.0
            self.viewer.cam.lookat[:] = [0.0, 0.0, 0.2]

            self.lidar_rays = []
        except Exception as e:
            print(f"[ERROR][HAL-911] Failed to initialize SimulationHAL: {e}")
            traceback.print_exc()
            raise

    def _is_self_body_geom(self, geom_id: int) -> bool:
        if geom_id < 0:
            return False
        try:
            body_id = self.model.geom_bodyid[geom_id]
            drive_deck_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "drive_deck")
            curr = body_id
            while curr > 0:
                if curr == drive_deck_id:
                    return True
                curr = self.model.body_parentid[curr]
            return False
        except Exception:
            return False

    def read_sensors(self) -> np.ndarray:
        """Cast 24 sonar rays starting from the robot outer boundary, excluding self geoms."""
        try:
            robot_x, robot_y, robot_yaw = self.get_robot_pos()
            pnt = np.array([robot_x, robot_y, 0.13], dtype=np.float64)  # 0.13m = scanner height
            yaw = robot_yaw

            geomid = np.array([-1], dtype=np.int32)
            offset = 0.16  # radius of robot to start ray outside chassis

            dists = []
            self.lidar_rays = []

            for a in self.sonar_angles:
                vec = np.array([math.cos(yaw+a), math.sin(yaw+a), 0], dtype=np.float64)
                pnt_ray = pnt + vec * offset
                dist = mujoco.mj_ray(self.model, self.data, pnt_ray, vec, None, 1, self.robot_body_id, geomid)

                if dist >= 0 and (self._is_self_body_geom(geomid[0]) or geomid[0] == self.food_geom_id):
                    dist = -1.0

                if dist < 0:
                    dist_val = 5.0
                    self.lidar_rays.append((pnt, pnt + vec * 5.0, False))
                else:
                    dist_val = dist + offset
                    if dist_val > 5.0:
                        dist_val = 5.0
                        self.lidar_rays.append((pnt, pnt + vec * 5.0, False))
                    else:
                        self.lidar_rays.append((pnt, pnt + vec * dist_val, True))
                
                dists.append(dist_val)

            self.battery_level = max(0.0, self.battery_level - 0.0001)

            sensor_vector = np.zeros(25)
            sensor_vector[0:24] = dists
            sensor_vector[24] = self.battery_level

            return sensor_vector
        except Exception as e:
            print(f"[ERROR][PHY-003] Failed to read sensors: {e}")
            raise

    def read_camera(self) -> dict:
        try:
            self.offscreen_renderer.update_scene(self.data, camera="eye_cam")
            img = self.offscreen_renderer.render()
            img_tensor = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1).to(self.device) / 255.0

            with torch.no_grad():
                predictions = self.vision_model([img_tensor])
                pred = predictions[0]

            boxes = pred["boxes"].cpu().numpy()
            labels = pred["labels"].cpu().numpy()
            scores = pred["scores"].cpu().numpy()
            valid_idx = np.where(scores >= 0.50)[0]

            return {
                "boxes": boxes[valid_idx],
                "labels": labels[valid_idx],
                "scores": scores[valid_idx]
            }
        except Exception as e:
            print(f"[ERROR][IMA-601] Live visual inference failed: {e}")
            return {"boxes": np.zeros((0, 4)), "labels": np.zeros(0), "scores": np.zeros(0)}

    def write_motors(self, speed_left: float, speed_right: float, neck_target: float):
        try:
            v_l = float(np.clip(speed_left, -20.0, 20.0))
            v_r = float(np.clip(speed_right, -20.0, 20.0))
            head_pan_pos = float(np.clip(neck_target, -1.4, 1.4))

            self.data.ctrl[0] = v_l
            self.data.ctrl[1] = v_r
            self.data.ctrl[4] = 0.0
            self.data.ctrl[5] = head_pan_pos

            self.data.ctrl[2:4] = 0.0
            self.data.ctrl[6:] = 0.0
        except Exception as e:
            print(f"[ERROR][PHY-001] Failed to apply motor outputs: {e}")
            raise

    def reset_robot(self):
        q_addr = int(self.model.joint("spatial_identity").qposadr[0])
        self.data.qpos[q_addr : q_addr+3] = [0.0, 0.0, 0.05]
        self.data.qpos[q_addr+3 : q_addr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qpos[q_addr+7:] = 0.0
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0
        self.battery_level = 1.0
        mujoco.mj_forward(self.model, self.data)

    def get_robot_pos(self) -> tuple:
        q_addr = int(self.model.joint("spatial_identity").qposadr[0])
        x = float(self.data.qpos[q_addr])
        y = float(self.data.qpos[q_addr + 1])
        qw = self.data.qpos[q_addr + 3]
        qz = self.data.qpos[q_addr + 6]
        yaw = 2.0 * math.atan2(qz, qw)
        return x, y, yaw

    def get_head_pan_angle(self) -> float:
        """Returns the current head pan joint angle in radians."""
        return float(self.data.qpos[self.head_pan_qposadr])

    def get_food_pos(self) -> np.ndarray:
        return self.model.geom_pos[self.food_geom_id].copy()

    def respawn_food(self):
        """Spawns food in validated open space with ray-tested wall clearance (>0.5m)."""
        best_pos = None
        max_clearance = -1.0

        for _ in range(50):
            cand_x = np.random.uniform(-3.8, 3.8)
            cand_y = np.random.uniform(-3.8, 3.8)
            pnt = np.array([cand_x, cand_y, 0.12], dtype=np.float64)

            # Test clearance in 8 radial directions
            geomid = np.array([-1], dtype=np.int32)
            min_wall_dist = 5.0
            for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
                vec = np.array([math.cos(angle), math.sin(angle), 0], dtype=np.float64)
                dist = mujoco.mj_ray(self.model, self.data, pnt, vec, None, 1, self.robot_body_id, geomid)
                if dist >= 0 and dist < min_wall_dist:
                    min_wall_dist = dist

            if min_wall_dist > 0.5:
                best_pos = [cand_x, cand_y, 0.12]
                break
            elif min_wall_dist > max_clearance:
                max_clearance = min_wall_dist
                best_pos = [cand_x, cand_y, 0.12]

        if best_pos is None:
            best_pos = [0.0, 0.0, 0.12]

        self.model.geom_pos[self.food_geom_id] = best_pos
        mujoco.mj_forward(self.model, self.data)
        print(f"[PHY-004] Food respawned at ({best_pos[0]:.2f}, {best_pos[1]:.2f}) with verified clearance.")

    def get_hazard_pos(self) -> np.ndarray:
        if self.hazard_body_id >= 0:
            return self.data.xpos[self.hazard_body_id].copy()
        return np.array([99, 99, 99])


# ──────────────────────────────────────────────────────────────────────────
# VISION → SONAR SENSOR FUSION (IMA-601)
# ──────────────────────────────────────────────────────────────────────────

class SensorFusion:
    CLASS_FOOD = 1
    CLASS_OBSTACLE = 2
    CLASS_PREDATOR = 3

    def __init__(self, img_width: int = 160, fov_deg: float = 60.0):
        self.img_width = img_width
        self.fov_rad = math.radians(fov_deg)

    def fuse(self, detections: dict, sonar_dists: np.ndarray,
             sonar_angles: np.ndarray, head_pan: float = 0.0) -> dict:
        """
        Fuse vision detections with sonar distances.
        head_pan: current head pan angle (radians) to transform camera-frame to body-frame.
        """
        food_vec = np.zeros(2)
        threat_vec = np.zeros(2)
        food_dist = float('inf')
        threat_dist = float('inf')
        food_angle = 0.0
        threat_angle = 0.0

        boxes = detections["boxes"]
        labels = detections["labels"]
        scores = detections["scores"]

        for i in range(len(labels)):
            lbl = int(labels[i])
            box = boxes[i]
            cx = (box[0] + box[2]) / 2.0

            # Angle relative to camera center (left is positive, right is negative)
            angle_cam = (0.5 - cx / self.img_width) * self.fov_rad
            # Transform to body frame by adding head pan angle
            angle_body = angle_cam + head_pan

            # Find matching sonar ray based on body-frame angle, accounting for wrap-around
            angle_diff = sonar_angles - angle_body
            angle_diff = (angle_diff + np.pi) % (2 * np.pi) - np.pi
            angle_diffs = np.abs(angle_diff)
            closest_ray_idx = np.argmin(angle_diffs)

            if lbl == self.CLASS_FOOD:
                # Estimate distance directly from camera bounding box height
                box_height = max(1.0, box[3] - box[1])
                # f = 138.56 (focal length for FOV=60 deg, width=160), H = 0.24m (diameter)
                # depth = (f * H) / box_height = 33.25 / box_height
                depth = 33.25 / box_height

                # Cross-Modal Sonar Gate (Zero Cheating):
                # Real food is sonar-transparent, so sonar rays pass through food and hit the wall BEHIND food (sonar_depth >= depth - 0.2m).
                # If sonar sees a wall strictly IN FRONT of vision target (sonar_depth < depth - 0.4m), vision is hallucinating food behind a wall -> discard.
                sonar_depth = sonar_dists[closest_ray_idx]
                if sonar_depth < (depth - 0.40):
                    # Wall is physically in front of vision target -> Discard ghost detection
                    continue
                
                if depth < food_dist:
                    food_dist = depth
                    # Use body-frame angle for the food vector
                    food_vec = np.array([depth * math.cos(angle_body), depth * math.sin(angle_body)])
                    food_angle = angle_body
            elif lbl in (self.CLASS_OBSTACLE, self.CLASS_PREDATOR):
                depth = min(sonar_dists[closest_ray_idx], 5.0)
                if depth < threat_dist:
                    threat_dist = depth
                    threat_vec = np.array([depth * math.cos(angle_body), depth * math.sin(angle_body)])
                    threat_angle = angle_body

        return {
            'food_vec': food_vec,
            'threat_vec': threat_vec,
            'food_dist': food_dist,
            'threat_dist': threat_dist,
            'food_angle': food_angle,
            'threat_angle': threat_angle,
        }


# ──────────────────────────────────────────────────────────────────────────
# TELEMETRY CSV LOGGER (WIT-401)
# ──────────────────────────────────────────────────────────────────────────

class TelemetryLogger:
    COLUMNS = [
        "tick", "wall_time_s", "x", "y", "yaw",
        "DA", "NE", "SHT", "ACh", "precision",
        "motor_L", "motor_R", "motor_neck",
        "reflex_L", "reflex_R",
        "reservoir_norm", "rls_updates",
        "food_dist", "min_sonar", "battery",
        "food_eaten_total", "surge_event",
        "cognitive_L", "cognitive_R", "cognitive_neck",
    ]

    def __init__(self, path: str, flush_interval: int = 30):
        self.path = path
        self.flush_interval = flush_interval
        self.buffer = []
        self.file = open(path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(self.COLUMNS)
        self.file.flush()
        print(f"[WIT-401] Telemetry logger opened: {path}")

    def log(self, row: dict):
        self.buffer.append([row.get(c, "") for c in self.COLUMNS])
        if len(self.buffer) >= self.flush_interval:
            self.flush()

    def flush(self):
        if self.buffer:
            self.writer.writerows(self.buffer)
            self.file.flush()
            self.buffer = []

    def close(self):
        self.flush()
        self.file.close()


# ──────────────────────────────────────────────────────────────────────────
# MAIN SIMULATION RUNNER — SOC MODULAR INTEGRATION
# ──────────────────────────────────────────────────────────────────────────

class CarlSimulationRunner:
    CPG_FORWARD_BIAS = 1.5
    CPG_NECK_AMPLITUDE = 0.7      # ±40 degrees — wide enough to scan corridors
    CPG_NECK_FREQUENCY = 0.04     # slightly slower sweep for stable vision frames
    FOOD_CONTACT_DIST = 0.50      # 50cm — realistic for a 22cm chassis to trigger eating

    def __init__(self, open_space: bool = False, debug: bool = False):
        self.debug = debug
        # 1. Allocate Unified Memory Space (S_unified)
        self.S_unified = np.zeros(532)
        self.sensor_state = self.S_unified[0:25]
        self.reservoir_state = self.S_unified[25:525]
        self.neuromodulators = self.S_unified[525:529]
        self.motor_commands = self.S_unified[529:532]

        self.dt = 0.033

        xml_path = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
        self.hal = SimulationHAL(xml_path, open_space=open_space)

        # 2. LSM Reservoir Brain (Layer 1)
        self.reservoir = LiquidStateReservoir(
            N=500, M=37, K=3,
            spectral_radius=1.0, sparsity=0.15,
            tau=0.1, sigma_in=0.1, seed=42
        )
        reservoir_path = os.path.join(BASE_DIR, "memory", "carl_reservoir.npz")
        self.reservoir.load(reservoir_path)

        # 3. Biological Endocrine Kinetics (Layer 2)
        self.endocrine = EndocrineSystem()

        # 4. Spiking Reflex Layer (Layer 2 parallel override)
        self.reflex_layer = SpikingReflexLayer(num_sensors=24, num_motor_neurons=2)

        # 5. Vision-Sonar Sensor Fusion (Layer 0 interface)
        self.sensor_fusion = SensorFusion(img_width=160, fov_deg=60.0)

        # 6. Hippocampal Spatial Representation (Layer 3) & Replay Navigator
        from brain.carl_grid_cells import HippocampalNavigator
        self.hippocampus = HippocampalNavigator()
        self.last_active_place_cell = -1

        # 7. Telemetry Logger
        telemetry_path = os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")
        self.telemetry = TelemetryLogger(telemetry_path, flush_interval=30)

        self.current_tick = 0
        self.last_rls_tick = 0
        self.food_eaten_total = 0
        self.start_wall_time = time.time()

        # Sync views into S_unified
        self.neuromodulators[0] = self.endocrine.DA
        self.neuromodulators[1] = self.endocrine.NE
        self.neuromodulators[2] = self.endocrine.SHT
        self.neuromodulators[3] = self.endocrine.ACh

        # Working Memory (Hippocampal Persistence)
        self.food_memory_pos = None
        self.food_memory_timer = 0

    def _build_sensory_input(self, raw_sonar: np.ndarray, fused: dict) -> np.ndarray:
        u = np.zeros(37)
        u[0:24] = 1.0 - np.clip(raw_sonar / 5.0, 0.0, 1.0)
        u[24:26] = np.clip(fused['food_vec'] / 5.0, -1.0, 1.0)
        u[26:28] = np.clip(fused['threat_vec'] / 5.0, -1.0, 1.0)
        u[28] = self.endocrine.DA / 3.0
        u[29] = self.endocrine.NE / 3.0
        u[30] = self.endocrine.SHT / 3.0
        u[31] = self.endocrine.ACh / 3.0
        u[32] = self.motor_commands[0] / 10.0
        u[33] = self.motor_commands[1] / 10.0
        u[34] = self.motor_commands[2] / 0.7
        u[35] = 0.0
        u[36] = self.sensor_state[24]
        return u

    def _compute_rls_target(self, y_cognitive: np.ndarray,
                            y_executed: np.ndarray) -> np.ndarray:
        reflex_dev = y_executed - y_cognitive
        reflex_dev[2] = 0.0
        return reflex_dev

    def step(self):
        try:
            # A. Read sensors & visual retina
            sensor_readings = self.hal.read_sensors()
            self.sensor_state[:] = sensor_readings
            raw_rays = sensor_readings[0:24]

            # Simulate 12-sonar physical array with 30-degree cone width and 1:2 software interpolation
            sonars = np.zeros(12)
            for i in range(12):
                center_idx = 2 * i
                left_idx = (center_idx - 1) % 24
                right_idx = (center_idx + 1) % 24
                sonars[i] = min(raw_rays[left_idx], raw_rays[center_idx], raw_rays[right_idx])

            raw_sonar = np.zeros(24)
            for i in range(12):
                raw_sonar[2 * i] = sonars[i]
                next_val = sonars[(i + 1) % 12]
                raw_sonar[2 * i + 1] = (sonars[i] + next_val) / 2.0

            detections = self.hal.read_camera()

            # B. Ground detections with sonar depth — body-frame corrected + cross-modal gate
            head_pan = self.hal.get_head_pan_angle()
            fused = self.sensor_fusion.fuse(
                detections, raw_sonar, self.hal.sonar_angles, head_pan=head_pan
            )
            if self.debug and len(detections["labels"]) > 0:
                print(f"  [DEBUG-SENSORS] head_pan: {head_pan:.3f} | fused: food_dist={fused['food_dist']:.2f}, food_angle={fused['food_angle']:.3f}")

            food_is_visible = fused['food_dist'] < 5.0 and np.linalg.norm(fused['food_vec']) > 0.05

            # Spatial Working Memory (Hippocampal Persistence):
            camera_saw_food = fused['food_dist'] < 5.0 and np.linalg.norm(fused['food_vec']) > 0.05
            if camera_saw_food:
                robot_x, robot_y, robot_yaw = self.hal.get_robot_pos()
                rel_x, rel_y = fused['food_vec']
                glob_x = robot_x + rel_x * math.cos(robot_yaw) - rel_y * math.sin(robot_yaw)
                glob_y = robot_y + rel_x * math.sin(robot_yaw) + rel_y * math.cos(robot_yaw)
                self.food_memory_pos = np.array([glob_x, glob_y])
                self.food_memory_timer = 90  # 3 seconds memory lock
            elif self.food_memory_timer > 0 and self.food_memory_pos is not None:
                self.food_memory_timer -= 1
                robot_x, robot_y, robot_yaw = self.hal.get_robot_pos()
                glob_x, glob_y = self.food_memory_pos
                dx = glob_x - robot_x
                dy = glob_y - robot_y
                rel_x = dx * math.cos(robot_yaw) + dy * math.sin(robot_yaw)
                rel_y = -dx * math.sin(robot_yaw) + dy * math.cos(robot_yaw)
                fused['food_vec'] = np.array([rel_x, rel_y])
                fused['food_dist'] = math.sqrt(dx**2 + dy**2)
                fused['food_angle'] = math.atan2(rel_y, rel_x)
                if self.food_memory_timer == 0:
                    self.food_memory_pos = None

            food_is_visible = fused['food_dist'] < 5.0 and np.linalg.norm(fused['food_vec']) > 0.05

            # Sensory Gating (Selective Attention): Clear sonar rays toward visible food
            if fused['food_dist'] < 1.0 and np.linalg.norm(fused['food_vec']) > 0.05:
                food_ray_idx = int(round((fused['food_angle'] - (-np.pi)) / (2*np.pi) * 24)) % 24
                for offset in range(-1, 2):
                    raw_sonar[(food_ray_idx + offset) % 24] = 5.0

            # C. Safeguards
            robot_x, robot_y, robot_yaw = self.hal.get_robot_pos()
            food_pos = self.hal.get_food_pos()
            food_dist_gt = math.sqrt((robot_x - food_pos[0])**2 + (robot_y - food_pos[1])**2)

            out_of_bounds = (abs(robot_x) > 4.9 or abs(robot_y) > 4.9)
            if out_of_bounds:
                print(f"[WARNING][HAL-911] Boundary breach. Teleporting to safety.")
                self.hal.reset_robot()
                self.endocrine.surge_ne(0.5)
                return

            if np.isnan(self.S_unified).any() or np.isinf(self.S_unified).any():
                self.S_unified[:] = np.nan_to_num(self.S_unified, nan=0.0, posinf=1.0, neginf=-1.0)

            # D. Hippocampal Update & Graph Construction
            v_fwd = (self.motor_commands[0] + self.motor_commands[1]) / 2.0 * 0.05
            vx = v_fwd * math.cos(robot_yaw)
            vy = v_fwd * math.sin(robot_yaw)

            hip_data = self.hippocampus.step(robot_x, robot_y, vx, vy, self.dt, learn=True)
            active_place_idx, _ = self.hippocampus.places.peak_cell()

            if self.last_active_place_cell >= 0:
                self.hippocampus.places.update_graph(
                    self.last_active_place_cell, active_place_idx, self.current_tick
                )
            self.last_active_place_cell = active_place_idx

            # Hippocampal Replay: Multi-sweep reward diffusion through the topological graph
            self.hippocampus.places.diffuse_rewards(gamma=0.9, decay=0.99995, n_sweeps=5)

            # Trigger neuromodulator surges
            min_sonar = np.min(raw_sonar)
            if min_sonar < 0.2:
                self.endocrine.surge_ne(0.5)
            elif min_sonar < 0.4:
                self.endocrine.surge_ne(0.2)

            # Food consumption check
            ate_food_this_tick = False
            if food_dist_gt < self.FOOD_CONTACT_DIST:
                ate_food_this_tick = True
                self.food_eaten_total += 1
                self.food_memory_pos = None
                self.food_memory_timer = 0
                self.endocrine.surge_da(0.7)
                self.endocrine.surge_sht(0.3)
                # Stamp strong, persistent reward in Hippocampal Replay Map
                self.hippocampus.places.stamp_reward(active_place_idx, amount=5.0)
                print(f"[END-201] CARL ate food! Total eaten: {self.food_eaten_total}")
                self.hal.respawn_food()
                # Full battery recharge — CARL must survive to the next food
                self.hal.battery_level = 1.0

            hazard_pos = self.hal.get_hazard_pos()
            hazard_dist = math.sqrt((robot_x - hazard_pos[0])**2 + (robot_y - hazard_pos[1])**2)
            if hazard_dist < 0.5:
                self.endocrine.surge_ne(0.3)

            if self.sensor_state[24] < 0.3:
                self.endocrine.surge_ne(0.05)

            self.endocrine.step(dt=self.dt)

            # Sync endocrine states to S_unified slice
            self.neuromodulators[0] = self.endocrine.DA
            self.neuromodulators[1] = self.endocrine.NE
            self.neuromodulators[2] = self.endocrine.SHT
            self.neuromodulators[3] = self.endocrine.ACh

            # E. Precision weighting & Reservoir step
            pi_sensory = self.endocrine.get_precision_weight()
            u_raw = self._build_sensory_input(raw_sonar, fused)
            u_weighted = pi_sensory * u_raw

            noise_scale = self.endocrine.get_exploration_noise_scale()
            y_cognitive = self.reservoir.step(u_weighted, noise_scale, self.dt)
            self.reservoir_state[:] = self.reservoir.x

            # F. Endocrine Behavioral Governor & Motor Mixing
            mode = self.endocrine.get_behavioral_mode(
                battery_level=self.hal.battery_level,
                food_visible=food_is_visible
            )

            # SNN Reflexes
            reservoir_bias = np.zeros(2)
            reflex_outputs = self.reflex_layer.step(
                sensor_dists=raw_sonar,
                reservoir_bias=reservoir_bias,
                da=self.endocrine.DA,
                food_dist=fused['food_dist']
            )

            nav_taxis = np.zeros(2)
            cpg_neck_amp = self.CPG_NECK_AMPLITUDE

            # Compute replay navigation vector (available in ALL modes)
            replay_nav = np.zeros(2)
            stats = self.hippocampus.places.get_graph_stats()
            max_nav = stats['max_nav_value']
            replay_blend = self.endocrine.get_replay_blend_weight(
                self.hal.battery_level, max_nav
            )

            if replay_blend > 0.01:
                replay_target = self.hippocampus.places.get_replay_target(active_place_idx)
                rtx, rty = None, None
                if replay_target is not None:
                    rtx, rty, r_val = replay_target
                else:
                    val_sum = np.sum(self.hippocampus.places.nav_values)
                    if val_sum > 0.001:
                        target_center = np.average(
                            self.hippocampus.places.centres, axis=0,
                            weights=self.hippocampus.places.nav_values
                        )
                        rtx, rty = target_center[0], target_center[1]

                if rtx is not None:
                    dx = rtx - robot_x
                    dy = rty - robot_y
                    target_angle = math.atan2(dy, dx) - robot_yaw
                    target_angle = (target_angle + math.pi) % (2 * math.pi) - math.pi
                    turn_drive = float(np.clip(target_angle * 3.5, -3.5, 3.5))
                    fwd_boost = float(max(0.2, 1.2 * (1.0 - abs(target_angle) / math.pi)))
                    replay_nav[0] = (fwd_boost - turn_drive) * replay_blend
                    replay_nav[1] = (fwd_boost + turn_drive) * replay_blend

            if mode == "EXPLOIT":
                # Lock-on appetitive taxis (strongest drive — direct food approach)
                hunger = 1.0 + 2.0 * (1.0 - self.hal.battery_level)
                satiation = 1.0 / max(0.5, self.endocrine.DA)
                motivation = hunger * satiation

                dist_scale = float(np.clip(fused['food_dist'] / 2.0, 0.3, 1.0))
                turn_drive = float(np.clip(fused['food_angle'] * 4.0 * dist_scale * motivation, -4.0, 4.0))
                fwd_boost = float(max(0.0, 1.5 * min(motivation, 2.0) * (1.0 - abs(fused['food_angle']) / 1.0)))
                nav_taxis[0] = fwd_boost - turn_drive
                nav_taxis[1] = fwd_boost + turn_drive
                # In EXPLOIT, replay nav is suppressed (food is visible, just go to it)

            elif mode == "SURVIVE":
                # Critical hunger: wide neck scan + full replay navigation
                cpg_neck_amp = 0.9
                nav_taxis = replay_nav  # replay dominates

            elif mode == "EXPLORE":
                # Blend novelty-seeking with replay gradient
                cpg_neck_amp = 0.8
                novelty_pos = self.hippocampus.places.get_novelty_target(active_place_idx, self.current_tick)
                novelty_taxis = np.zeros(2)
                if novelty_pos is not None:
                    dx = novelty_pos[0] - robot_x
                    dy = novelty_pos[1] - robot_y
                    target_angle = math.atan2(dy, dx) - robot_yaw
                    target_angle = (target_angle + math.pi) % (2 * math.pi) - math.pi
                    turn_drive = float(np.clip(target_angle * 1.8, -2.0, 2.0))
                    novelty_taxis[0] = 0.5 - turn_drive
                    novelty_taxis[1] = 0.5 + turn_drive

                # Blend: hunger drives replay weight, curiosity drives novelty
                # As hunger builds, replay navigation dominates over novelty
                nav_taxis = (1.0 - replay_blend) * novelty_taxis + replay_nav

            total_reflex = reflex_outputs + nav_taxis

            # H. Actuate Motors
            cpg_left = self.CPG_FORWARD_BIAS
            cpg_right = self.CPG_FORWARD_BIAS
            cpg_neck = cpg_neck_amp * math.sin(self.current_tick * self.CPG_NECK_FREQUENCY)

            u_left = cpg_left + y_cognitive[0] + total_reflex[0]
            u_right = cpg_right + y_cognitive[1] + total_reflex[1]
            u_neck = cpg_neck + y_cognitive[2]

            y_executed = np.array([u_left - cpg_left, u_right - cpg_right, u_neck - cpg_neck])

            self.motor_commands[0] = u_left
            self.motor_commands[1] = u_right
            self.motor_commands[2] = u_neck

            self.hal.write_motors(
                speed_left=u_left,
                speed_right=u_right,
                neck_target=u_neck
            )

            # I. RLS Online learning schedule
            has_reflex = np.linalg.norm(total_reflex) > 0.05
            has_surprise = (self.endocrine.NE > 0.15 or self.endocrine.DA > 1.05 or self.endocrine.ACh > 0.7)

            if has_reflex or has_surprise:
                time_since_rls = self.current_tick - self.last_rls_tick
                error_norm = np.linalg.norm(self.reservoir.last_prediction_error)

                if time_since_rls >= 6 or (error_norm > 0.25 and time_since_rls >= 3):
                    y_target = self._compute_rls_target(y_cognitive, y_executed)
                    self.reservoir.rls_update(y_target)
                    self.last_rls_tick = self.current_tick

            # J. Console Diagnostics
            if self.current_tick % 30 == 0:
                diag_stats = self.hippocampus.places.get_graph_stats()
                print(f"[TICK {self.current_tick:5d}] MODE:{mode:<7s} pos:({robot_x:.2f},{robot_y:.2f}) "
                      f"| {self.endocrine} "
                      f"| food:{food_dist_gt:.2f}m eaten:{self.food_eaten_total} "
                      f"| edges:{diag_stats['edges']} nav:{diag_stats['max_nav_value']:.2f} rblend:{replay_blend:.2f} beacons:{diag_stats['persistent_beacons']} "
                      f"| cog:[{y_cognitive[0]:.2f},{y_cognitive[1]:.2f}] "
                      f"| sonar_min:{min_sonar:.2f}")

            # K. Log Telemetry Row
            self.telemetry.log({
                "tick": self.current_tick,
                "wall_time_s": round(time.time() - self.start_wall_time, 3),
                "x": round(robot_x, 4),
                "y": round(robot_y, 4),
                "yaw": round(robot_yaw, 4),
                "DA": round(self.endocrine.DA, 4),
                "NE": round(self.endocrine.NE, 4),
                "SHT": round(self.endocrine.SHT, 4),
                "ACh": round(self.endocrine.ACh, 4),
                "precision": round(pi_sensory, 4),
                "motor_L": round(u_left, 4),
                "motor_R": round(u_right, 4),
                "motor_neck": round(u_neck, 4),
                "reflex_L": round(reflex_outputs[0], 4),
                "reflex_R": round(reflex_outputs[1], 4),
                "reservoir_norm": round(self.reservoir.get_state_norm(), 4),
                "rls_updates": self.reservoir.total_rls_updates,
                "food_dist": round(food_dist_gt, 4),
                "min_sonar": round(min_sonar, 4),
                "battery": round(self.sensor_state[24], 4),
                "food_eaten_total": self.food_eaten_total,
                "surge_event": self.endocrine.last_surge_event,
                "cognitive_L": round(y_cognitive[0], 4),
                "cognitive_R": round(y_cognitive[1], 4),
                "cognitive_neck": round(y_cognitive[2], 4),
            })
            self.endocrine.last_surge_event = ""

            self.current_tick += 1
        except Exception as e:
            print(f"[ERROR][HAL-911] Error inside control step loop: {e}")
            traceback.print_exc()
            raise


# ──────────────────────────────────────────────────────────────────────────
# SIMULATION MAIN LOOP
# ──────────────────────────────────────────────────────────────────────────

def run_simulation(open_space: bool = False):
    runner = CarlSimulationRunner(open_space=open_space)

    physics_ticks_per_control = 8
    control_period = 1.0 / 30.0

    print("\n" + "=" * 64)
    print("  EBCA AUTONOMOUS COGNITIVE LOOP — SOC MODULAR RUNNER")
    print("=" * 64)
    print(f"  Model:          world/vessel_kinetic.xml")
    print(f"  S_unified:      532 floats (zero-copy memory space)")
    print(f"  LSM Reservoir:  500 neurons (from brain.carl_reservoir)")
    print(f"  Endocrine:      DA/NE/5-HT/ACh (from brain.carl_endocrine)")
    print(f"  SNN Reflex:     Asymmetric differential steering (from brain.carl_reflex)")
    print(f"  Vision:         SSD-Lite multi-object retina")
    print(f"  Sonars:         12 ultrasonic (30° cone), interpolated to 24")
    print(f"  Telemetry:      telemetry_autonomous.csv")
    print("=" * 64)

    start_time = time.time()
    next_control_time = start_time
    step_durations = []

    def sync_viewer_rays():
        if runner.hal.viewer and runner.hal.viewer.is_running():
            runner.hal.viewer.user_scn.ngeom = 0
            for p1, p2, hit in runner.hal.lidar_rays:
                if runner.hal.viewer.user_scn.ngeom >= runner.hal.viewer.user_scn.maxgeom:
                    break
                color = np.array([1, 0, 0, 1]) if hit else np.array([0, 1, 0.5, 0.5])
                mujoco.mjv_initGeom(
                    runner.hal.viewer.user_scn.geoms[runner.hal.viewer.user_scn.ngeom],
                    mujoco.mjtGeom.mjGEOM_LINE, np.zeros(3),
                    np.zeros(3), np.zeros(9), color
                )
                mujoco.mjv_connector(
                    runner.hal.viewer.user_scn.geoms[runner.hal.viewer.user_scn.ngeom],
                    mujoco.mjtGeom.mjGEOM_LINE, 2,
                    np.array(p1), np.array(p2)
                )
                runner.hal.viewer.user_scn.ngeom += 1
            runner.hal.viewer.sync()

    try:
        while runner.hal.viewer.is_running():
            loop_start = time.time()

            if loop_start >= next_control_time:
                runner.step()

                for _ in range(physics_ticks_per_control):
                    mujoco.mj_step(runner.hal.model, runner.hal.data)

                sync_viewer_rays()

                duration_ms = (time.time() - loop_start) * 1000.0
                step_durations.append(duration_ms)
                if len(step_durations) >= 90:
                    avg_ms = sum(step_durations) / len(step_durations)
                    max_ms = max(step_durations)
                    print(f"[PROFILE] Control Loop: Avg {avg_ms:.1f} ms/tick, "
                          f"Max {max_ms:.1f} ms/tick (Budget: 33.3 ms)")
                    step_durations = []

                next_control_time += control_period
            else:
                time.sleep(0.001)
    except KeyboardInterrupt:
        print("\n[HAL-911] Shutdown requested.")
    finally:
        runner.reservoir.save(os.path.join(BASE_DIR, "memory", "carl_reservoir.npz"))
        runner.telemetry.close()
        print(f"[GIS-901] Session complete. Food eaten: {runner.food_eaten_total}. "
              f"RLS updates: {runner.reservoir.total_rls_updates}.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--open-space', action='store_true', help='Train in open space without internal maze walls')
    args = parser.parse_args()
    run_simulation(open_space=args.open_space)
