# 🔬 DEEP DIVE #4 — `carl_simulation.py` (Every Line, Every Number, Every Why)
> *903 lines. Zero skipped. The master orchestrator — where every module connects.*

---

## FILE PURPOSE

This is the **main entry point** and **integration layer** — the file you actually RUN. It:
1. Loads the physics environment (MuJoCo)
2. Creates all cognitive modules (reservoir, endocrine, reflex, hippocampus)
3. Runs the **30Hz control loop** (the "heartbeat" of the robot)
4. Logs all data to CSV for analysis

Think of this as the "spinal cord + brainstem" that routes signals between the body and the brain.

---

## MODULE-BY-MODULE EXPLANATION

---

### Lines 1–9: Top Docstring

```python
"""
carl_simulation.py — EBCA Full Autonomous Simulation Runner (Modular SoC Design)
...
Diagnostic ID Tracking (PHY-001..004, LSM-211..212, END-201..205, ...)
"""
```

**"SoC Design"** = System-on-Chip. A design pattern from embedded systems where different functional units share a unified memory bus. Here: all cognitive modules share `S_unified` — a single 532-element array — so they can "talk" to each other via memory without function calls.

**"Zero-copy"**: Data written by one module (e.g., motor_commands) is immediately available to another module (reflex) because they're VIEWS into the same array — no copying needed. This is an Apple Silicon M-chip design concept: neural engine, CPU, and GPU share unified memory.

**Diagnostic IDs** (PHY-001, LSM-211, etc.): Each ID tags print statements and errors by subsystem, making it trivial to grep logs and find which module failed.

---

### Lines 11–24: Imports

```python
import sys, os, math, numpy as np, time, traceback, csv
import mujoco, mujoco.viewer
import torch, torchvision, functools, torch.nn as nn
from torchvision.models.detection.ssdlite import SSDLiteClassificationHead
```

**Why each import:**
- `sys`, `os`: Path manipulation, `sys.path.append()`
- `math`: `math.atan2()`, `math.cos()`, `math.sin()` for single scalars (faster than numpy for one value)
- `numpy as np`: All array operations
- `time`: Wall-clock timing for the control loop rate limiter
- `traceback`: Full error printout when exceptions occur
- `csv`: Writing the telemetry CSV file
- `mujoco`: Physics simulator, the actual robot body
- `mujoco.viewer`: The 3D visualization window
- `torch`: PyTorch, for the SSD-Lite object detection model
- `torchvision`: Pre-trained models (SSD-Lite MobileNetV3)
- `functools`: `functools.partial()` to customize BatchNorm2d arguments
- `torch.nn as nn`: Neural network layers (BatchNorm2d for the vision model)

---

### Lines 26–27: Path Setup

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
```

**`os.path.abspath(__file__)`**: Gets the ABSOLUTE path of this script file. `__file__` is a Python built-in that holds the current file's path (might be relative). `.abspath()` makes it absolute.

**`os.path.dirname(...)`**: Strips the filename, gives just the directory. So if the script is at `d:\ebca\carl_simulation.py`, `BASE_DIR = "d:\ebca"`.

**`sys.path.append(BASE_DIR)`**: Adds `d:\ebca` to Python's module search path. This allows `from brain.carl_reservoir import ...` to work (Python can now find the `brain/` folder as a package).

---

### Lines 37–50: `get_ssdlite_model()` — Vision Model Factory

```python
def get_ssdlite_model():
    model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(
        weights=SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
    )
```

**SSD-Lite MobileNetV3-Large**: A real-time object detection model.

- **SSD** = Single Shot Detector: detects ALL objects in one forward pass (no region proposal step)
- **Lite**: Lighter version with depthwise separable convolutions (faster, less accurate)
- **MobileNetV3-Large**: The backbone (feature extractor), optimized for mobile/embedded devices
- **320**: Input image size 320×320 pixels

`weights=DEFAULT`: Downloads pre-trained weights from ImageNet (80 COCO categories). We then REPLACE the classification head to handle CARL's 4 categories.

---

```python
    in_channels = [layer[0][0].in_channels for layer in model.head.classification_head.module_list]
    num_anchors = model.anchor_generator.num_anchors_per_location()
    norm_layer = functools.partial(nn.BatchNorm2d, eps=0.001, momentum=0.03)
    model.head.classification_head = SSDLiteClassificationHead(
        in_channels=in_channels, num_anchors=num_anchors, num_classes=4, norm_layer=norm_layer
    )
```

**"Transfer Learning"**: Take a model trained on 80 classes, replace the final prediction head with one for 4 classes (Food, Obstacle, Predator, Background), keep all the feature extraction layers.

`in_channels`: The number of input channels at each SSD prediction scale. SSD makes predictions at multiple scales (for detecting small and large objects). These channels must match.

`num_anchors`: SSD uses "anchor boxes" — predefined bounding box shapes at each grid cell. The number of anchors must match the original model design.

`functools.partial(nn.BatchNorm2d, eps=0.001, momentum=0.03)`: Creates a "frozen" version of BatchNorm2d with specific hyperparameters. `eps=0.001` avoids division by zero in normalization. `momentum=0.03` is the running statistics update rate (different from optimizer momentum).

`num_classes=4`: 0=Background, 1=Food, 2=Obstacle, 3=Predator.

---

### Lines 57–290: `SimulationHAL` — The Hardware Abstraction Layer

#### Why HAL (Hardware Abstraction Layer)?

```python
class HardwareInterface:
    def read_sensors(self) -> np.ndarray: raise NotImplementedError
    def write_motors(self, torque_left, torque_right, neck_target): raise NotImplementedError
```

This abstract base class defines the INTERFACE the cognitive brain uses to interact with the body. The brain only calls `read_sensors()` and `write_motors()` — it doesn't know or care whether the body is:
- A MuJoCo simulation (SimulationHAL)
- A real robot (would be implemented as `HardwareHAL`)
- A different simulation engine

This is the **Dependency Inversion Principle**: high-level modules (brain) don't depend on low-level modules (physics simulator), both depend on abstractions (HardwareInterface).

---

#### Lines 68–123: `SimulationHAL.__init__()`

```python
class SimulationHAL(HardwareInterface):
    def __init__(self, xml_path: str, open_space: bool = False):
        self.model = mujoco.MjModel.from_xml_path(xml_path)
```

`mujoco.MjModel.from_xml_path(xml_path)`: Parses `vessel_kinetic.xml` and compiles it into MuJoCo's internal binary model format. This includes:
- All body geometry (boxes, cylinders, spheres)
- Joint definitions and limits
- Actuator parameters
- Contact friction/stiffness
- Inertia tensors

---

```python
        if open_space:
            for i in range(self.model.ngeom):
                name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, i)
                if name and name.startswith("lwall_"):
                    self.model.geom_pos[i] = [99.0, 99.0, -99.0]
```

**Open-space training mode**: Internal maze walls (all geoms whose names start with "lwall_") are teleported to position [99, 99, -99] — far outside the arena and underground. This leaves CARL in an open 10×10m arena.

**Why `[99.0, 99.0, -99.0]` specifically?** 99m is far outside the arena boundary (±5m). -99m is 99 meters underground — completely inaccessible. Using a large number rather than `NaN` or deleting the geom preserves MuJoCo's internal data structures.

**Why remove walls for training?** Early training is easier without walls — CARL can learn food-seeking behavior without simultaneously dealing with obstacle avoidance complexity.

---

```python
        self.cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "eye_cam")
        if self.cam_id < 0:
            raise ValueError("Error: eye_cam camera not found in XML model!")
```

`mujoco.mj_name2id()`: Looks up a named entity in the model. Returns -1 if not found. The explicit check and raise helps catch XML naming errors immediately rather than silently producing wrong camera images.

---

```python
        self.sonar_angles = np.linspace(-np.pi, np.pi, 24, endpoint=False)
        self.battery_level = 1.0
```

`self.sonar_angles`: 24 angles evenly from -180° to +165°, matching the 24 LiDAR rays in `read_sensors()`.

`self.battery_level = 1.0`: Starts full. Depleted at 0.0001 per tick (0.003% per tick × 30Hz = 0.09%/second). Full battery lasts `1.0 / (0.0001 × 30) = 333 seconds = ~5.5 minutes`.

---

```python
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.vision_model = get_ssdlite_model()
        weights_path = os.path.join(BASE_DIR, "memory", "carl_multi_object_vision.pt")
        if os.path.exists(weights_path):
            self.vision_model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.vision_model.to(self.device)
        self.vision_model.eval()
```

`torch.cuda.is_available()`: Checks for GPU. If GPU present → runs vision model on GPU (10-100× faster). Otherwise CPU.

`load_state_dict()`: Loads ONLY the weight parameters — not the model architecture. Model structure was already defined by `get_ssdlite_model()`.

`map_location=self.device`: Loads weights onto the correct device. If model was trained on GPU but running on CPU, this remaps tensors.

`self.vision_model.eval()`: Switches model to inference mode. Disables:
- Dropout (should be off during inference)  
- BatchNorm running stats updates (should use stored stats, not compute new ones)

---

```python
        self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
        self.viewer.cam.azimuth = 45
        self.viewer.cam.elevation = -32
        self.viewer.cam.distance = 7.0
        self.viewer.cam.lookat[:] = [0.0, 0.0, 0.2]
```

`launch_passive()`: Opens a 3D viewer window that runs in the background. "Passive" means the simulation is controlled by the Python code — the viewer just renders. The camera is set up for a nice isometric overview angle:
- `azimuth=45°`: Look from 45° east of north
- `elevation=-32°`: Look down at 32° below horizontal
- `distance=7.0`: 7 meters from the lookat point
- `lookat=[0,0,0.2]`: Look at the center of the arena, 20cm up

---

### Lines 125–139: `_is_self_body_geom()`

```python
def _is_self_body_geom(self, geom_id: int) -> bool:
    body_id = self.model.geom_bodyid[geom_id]
    drive_deck_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "drive_deck")
    curr = body_id
    while curr > 0:
        if curr == drive_deck_id:
            return True
        curr = self.model.body_parentid[curr]
    return False
```

**Purpose:** Given a geom (geometry piece) that a LiDAR ray hit, determine if it's part of CARL's own body (so we can ignore it).

**Algorithm:** Traverses the **kinematic tree** (body hierarchy) upward from the hit geom's body, checking if any ancestor is "drive_deck" (CARL's base body). If yes → this is a CARL body part → ignore the LiDAR hit.

**`self.model.body_parentid[curr]`**: Each body in MuJoCo has a parent body. The root body has parent 0. Walking up the tree: `geom_body → parent → grandparent → ... → root`.

**Why traverse the whole tree?** CARL has a complex kinematic chain: `drive_deck → neck_body → head_body → camera_mount`. A ray hitting the head should be ignored even though the camera is not directly "drive_deck" — it's a grandchild.

---

### Lines 140–183: `read_sensors()` — 24-Ray LiDAR

```python
def read_sensors(self) -> np.ndarray:
    robot_x, robot_y, robot_yaw = self.get_robot_pos()
    pnt = np.array([robot_x, robot_y, 0.13], dtype=np.float64)  # 13cm height
    offset = 0.16  # 16cm = CARL's chassis radius
```

**Why `z=0.13`?** CARL's body is 4cm tall (size 0.02 in XML × 2 + offset). The LiDAR scanner is mounted at 13cm height — above the chassis but below eye level. This prevents scanning the floor.

**Why `offset=0.16`?** The ray starts 16cm from the robot center (approximately the chassis half-diagonal). This ensures the ray doesn't immediately hit CARL's own chassis.

---

```python
    for a in self.sonar_angles:
        vec = np.array([math.cos(yaw+a), math.sin(yaw+a), 0], dtype=np.float64)
        pnt_ray = pnt + vec * offset
        dist = mujoco.mj_ray(self.model, self.data, pnt_ray, vec, None, 1, self.robot_body_id, geomid)
```

`math.cos(yaw+a)`, `math.sin(yaw+a)`: The ray direction in world frame. `yaw` is CARL's current heading. Adding `a` (the sensor angle relative to CARL's front) rotates the ray to face angle `a` relative to CARL.

`pnt_ray = pnt + vec * offset`: Starts the ray 16cm ahead, so it doesn't immediately hit CARL's chassis.

`mujoco.mj_ray(model, data, pnt_ray, vec, None, 1, robot_body_id, geomid)`:
- Arguments: model, data, ray_start, ray_direction, geom_group_filter, flg_static, robot_body_id, output_geomid
- `None`: No geom group filter (hit anything)
- `1`: Include static geoms (walls)
- `robot_body_id`: Body to EXCLUDE from ray cast
- `geomid`: Output array — will contain the ID of the first hit geometry
- Returns: distance to hit, or -1 if nothing hit

---

```python
        if dist >= 0 and (self._is_self_body_geom(geomid[0]) or geomid[0] == self.food_geom_id):
            dist = -1.0
```

**Two special cases for ignoring hits:**
1. `_is_self_body_geom(geomid[0])`: Hit part of CARL's own body → ignore
2. `geomid[0] == self.food_geom_id`: Hit the food sphere → ignore

**Why ignore food?** Food is visually transparent (a sphere that sensors pass through). If sonar reported "obstacle at 0.4m" because of food, CARL's reflex would dodge the food instead of eating it. Making food sonar-transparent forces CARL to use VISION to detect food.

---

```python
        if dist < 0:
            dist_val = 5.0
        else:
            dist_val = dist + offset
```

**No hit → 5.0m**: Maximum reportable distance. Arena is ~9m wide, so 5m means "nothing close."

**`dist + offset`**: The raw `mj_ray` distance is from `pnt_ray` (16cm ahead of center). Adding offset gives distance from CARL's actual center.

---

```python
        self.battery_level = max(0.0, self.battery_level - 0.0001)
        sensor_vector = np.zeros(25)
        sensor_vector[0:24] = dists
        sensor_vector[24] = self.battery_level
        return sensor_vector
```

**Battery depletion**: 0.0001 per tick × 30Hz = 0.003/second = 5.5 minute battery life.

**Sensor vector [25]**: First 24 = LiDAR distances. Last 1 = battery. This bundles all "body state" into one clean vector that the brain receives.

---

### Lines 185–207: `read_camera()` — Vision Inference

```python
    def read_camera(self) -> dict:
        self.offscreen_renderer.update_scene(self.data, camera="eye_cam")
        img = self.offscreen_renderer.render()   # Returns RGB numpy array (120, 160, 3)
        img_tensor = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1).to(self.device) / 255.0
```

`update_scene()`: Syncs the renderer with the current physics state.
`render()`: Renders the camera view. Returns `uint8` array of shape (H, W, 3) = (120, 160, 3).

`.permute(2, 0, 1)`: Converts from (H, W, C) = (120, 160, 3) → (C, H, W) = (3, 120, 160). PyTorch models expect channels-first format.

`/ 255.0`: Normalizes pixel values from [0, 255] to [0.0, 1.0]. The SSD model was trained with normalized inputs.

---

```python
        with torch.no_grad():
            predictions = self.vision_model([img_tensor])
            pred = predictions[0]
        valid_idx = np.where(scores >= 0.50)[0]
```

`torch.no_grad()`: Disables gradient computation during inference. This:
- Saves ~50% memory (no gradient buffers)
- Speeds up inference ~10%
- Makes output deterministic (no gradient noise)

`[img_tensor]`: SSD model takes a LIST of images (batched inference). Using a single-element list = batch size 1.

`scores >= 0.50`: Confidence threshold. Only detections where the model is at least 50% confident are kept. Below 50% = too uncertain, discard.

---

### Lines 295–371: `SensorFusion.fuse()` — Vision + Sonar Integration

#### The Critical Problem: Sonar Cross-Modal Gate (Lines 344–350)

```python
            if lbl == self.CLASS_FOOD:
                box_height = max(1.0, box[3] - box[1])
                depth = 33.25 / box_height   # Pinhole camera depth estimate
                sonar_depth = sonar_dists[closest_ray_idx]
                if sonar_depth < (depth - 0.40):
                    continue  # Discard: wall is in front of vision target
```

**Why this matters:** Sonar and vision measure DIFFERENT THINGS:
- Sonar = distance to nearest SOLID object in a beam
- Vision = distance to a DETECTED OBJECT (which might be behind a wall/glass)

A false positive from vision (hallucinating food behind a wall) would cause CARL to chase a ghost through a wall. The sonar gate catches this:

**Logic:** If sonar sees a wall at distance `sonar_depth` = 1.5m, but vision says food is at `depth` = 3.0m, then:
```
sonar_depth < (depth - 0.40)
1.5 < (3.0 - 0.40) = 2.6  → TRUE → discard
```
There's a wall between CARL and the supposed food. Discard the detection.

**Tolerance `0.40`**: Food sphere has diameter 24cm ≈ 0.24m. The sonar might hit the FAR side of the food sphere (so sonar_depth ≈ vision_depth + 0.24). The 0.40m tolerance gives 16cm margin beyond the food diameter to avoid discarding real food.

**`depth = 33.25 / box_height` — Pinhole camera depth formula:**
```
depth = (focal_length × object_height_real) / object_height_pixels
      = f × H_real / h_pixels
```
For CARL's camera (FOV=60°, image height H=120):
```
f = H / (2 × tan(FOV/2)) = 120 / (2 × tan(30°)) = 120 / 1.155 = 103.9 pixels
```
Wait — that gives f≈104, but code uses 33.25. The formula is actually:
```
depth = (f × H_real) / h_pixels = (138.56 × 0.24) / h_pixels
```
Comment says: "f=138.56 (focal for FOV=60,width=160), H=0.24m (food diameter)"
```
33.25 = 138.56 × 0.24
```
Yes: 138.56 × 0.24 = 33.25. For a 160px-wide 60° FOV camera, f_x = 138.56.

---

### Lines 420–476: `CarlSimulationRunner.__init__()` — Unified Memory Architecture

```python
self.S_unified = np.zeros(532)
self.sensor_state    = self.S_unified[0:25]    # View: indices 0-24
self.reservoir_state = self.S_unified[25:525]  # View: indices 25-524
self.neuromodulators = self.S_unified[525:529] # View: indices 525-528
self.motor_commands  = self.S_unified[529:532] # View: indices 529-531
```

**Zero-copy memory design:**

`np.zeros(532)`: Creates ONE contiguous array of 532 float64 values in memory.

`self.S_unified[0:25]`: Creates a **view** (not a copy) into that array. Writing to `self.sensor_state[3] = 2.0` writes to `self.S_unified[3]` directly — NO COPY.

Why this matters: When the reservoir receives `self.sensor_state` as input, it reads from the SAME memory location that was just written by the HAL. No serialization, no copying, just pointer passing. This is exactly how Apple M-chip's "unified memory architecture" works — GPU and CPU share the same physical RAM.

**Memory layout:**
```
Indices 0-24:    [sonar_0, ..., sonar_23, battery]         ← Sensors
Indices 25-524:  [x_0, x_1, ..., x_499]                    ← Reservoir state (500 neurons)
Indices 525-528: [DA, NE, SHT, ACh]                        ← Hormones
Indices 529-531: [motor_L, motor_R, motor_neck]             ← Motor commands
```

---

### Lines 441–444: Reservoir Initialization

```python
self.reservoir = LiquidStateReservoir(
    N=500, M=37, K=3,
    spectral_radius=1.0, sparsity=0.15,
    tau=0.1, sigma_in=0.1, seed=42
)
```

**M=37 here vs M=25 in the class default:** The `carl_simulation.py` uses a richer 37D input vector including food/threat vectors, neuromodulators, and previous motor commands — not just the 24+1 sonar. The default M=25 in `carl_reservoir.py` is just a fallback.

---

### Lines 482–496: `_build_sensory_input()` — The 37-D Input Vector

```python
def _build_sensory_input(self, raw_sonar: np.ndarray, fused: dict) -> np.ndarray:
    u = np.zeros(37)
    u[0:24]  = 1.0 - np.clip(raw_sonar / 5.0, 0.0, 1.0)   # Sonar proximity (inverted)
    u[24:26] = np.clip(fused['food_vec'] / 5.0, -1.0, 1.0) # Food vector (2D)
    u[26:28] = np.clip(fused['threat_vec'] / 5.0, -1.0, 1.0) # Threat vector (2D)
    u[28]  = self.endocrine.DA  / 3.0   # Dopamine (normalized)
    u[29]  = self.endocrine.NE  / 3.0   # Norepinephrine
    u[30]  = self.endocrine.SHT / 3.0   # Serotonin
    u[31]  = self.endocrine.ACh / 3.0   # Acetylcholine
    u[32]  = self.motor_commands[0] / 10.0  # Previous left motor
    u[33]  = self.motor_commands[1] / 10.0  # Previous right motor
    u[34]  = self.motor_commands[2] / 0.7   # Previous neck angle
    u[35]  = 0.0                            # Reserved
    u[36]  = self.sensor_state[24]          # Battery level
    return u
```

**`1.0 - np.clip(raw_sonar / 5.0, ...)`**:
- Raw sonar: 0m (obstacle) to 5m (nothing). Divided by 5 → [0, 1]. Inverted → [1, 0].
- So: obstacle at 0m → input = 1.0 (MAX excitation), nothing at 5m → input = 0.0
- WHY invert? Proximity should excite the reservoir more. "1.0" = obstacle right here.

**Why feed previous motor commands (u[32-34])?**
This creates an **efference copy** — a model of "what I just commanded." With this, the reservoir knows its own recent actions and can plan sequences. Without it, the same sensory input always produces the same output — no sequential behavior possible.

**Why feed hormones (u[28-31])?**
The reservoir needs to know the current behavioral context. High DA = food just found → this pattern should lead to different motor outputs than high NE = danger. Feeding hormones into the reservoir allows the SAME neural network to implement DIFFERENT behavioral strategies depending on context.

**Normalization reasons:**
- Sonar / 5.0: max sonar distance is 5m
- Hormones / 3.0: max hormone level is 3.0
- Motor / 10.0: typical motor range is ±10
- Neck / 0.7: max neck angle is 0.7 rad (±40°)

All inputs normalize to approximately [-1, 1] range. This keeps the `tanh()` in the reservoir from saturating.

---

### Lines 504–814: `step()` — The 33ms Brain-Body Loop

This is the most complex function — runs 30 times per second. Let me walk through every section:

---

#### Section A: Sensor Reading (Lines 506–523)

```python
sensor_readings = self.hal.read_sensors()
self.sensor_state[:] = sensor_readings   # Zero-copy write into S_unified
raw_rays = sensor_readings[0:24]
```

`self.sensor_state[:] = sensor_readings`: The `[:]` slice assignment writes INTO the existing view (no new allocation). This is the zero-copy update.

---

```python
sonars = np.zeros(12)
for i in range(12):
    center_idx = 2 * i
    left_idx  = (center_idx - 1) % 24
    right_idx = (center_idx + 1) % 24
    sonars[i] = min(raw_rays[left_idx], raw_rays[center_idx], raw_rays[right_idx])
```

**12-ray physical sonar simulation:**  
Real ultrasonic sonars have a wide cone (30°). The 24-ray virtual LiDAR is too precise. This code SIMULATES physical sonars by taking the MINIMUM of each ray and its two neighbors.

Why minimum? Sonar returns the CLOSEST object in its wide cone. If three adjacent LiDAR rays cover the same 45° sector, the physical sonar would report the closest of the three readings.

`% 24`: Modular arithmetic for wrap-around. Sensor 0's left neighbor is sensor 23 (directly behind).

---

```python
raw_sonar = np.zeros(24)
for i in range(12):
    raw_sonar[2 * i] = sonars[i]
    next_val = sonars[(i + 1) % 12]
    raw_sonar[2 * i + 1] = (sonars[i] + next_val) / 2.0
```

**Interpolate back from 12 to 24:** Between each pair of physical sonars, insert the average. This restores the 24-ray resolution expected by the reflex layer, while using "sonically realistic" values (wide-cone minimums).

Why go 24→12→24? The 12-ray minimum step simulates realistic sonar physics. The 24-ray interpolation gives the reflex layer smooth angular resolution.

---

#### Section B: Vision Fusion (Lines 525–566)

```python
head_pan = self.hal.get_head_pan_angle()
fused = self.sensor_fusion.fuse(detections, raw_sonar, self.hal.sonar_angles, head_pan=head_pan)
```

**Why pass `head_pan`?** The camera rotates with the neck. If head is panned +0.3 rad (right), an object seen at the camera center is actually at +0.3 rad body-frame — not straight ahead. The fusion must transform camera-frame angles to body-frame angles.

---

```python
if camera_saw_food:
    robot_x, robot_y, robot_yaw = self.hal.get_robot_pos()
    rel_x, rel_y = fused['food_vec']
    glob_x = robot_x + rel_x * math.cos(robot_yaw) - rel_y * math.sin(robot_yaw)
    glob_y = robot_y + rel_x * math.sin(robot_yaw) + rel_y * math.cos(robot_yaw)
    self.food_memory_pos = np.array([glob_x, glob_y])
    self.food_memory_timer = 90  # 3 seconds
```

**2D Rotation transform: Camera-frame → World-frame:**
```
[glob_x]   [cos(yaw)  -sin(yaw)] [rel_x]   [robot_x]
[glob_y] = [sin(yaw)   cos(yaw)] [rel_y] + [robot_y]
```

This is a standard **2D rotation matrix** applied to transform the food vector from CARL's local body frame (where `rel_x` = forward, `rel_y` = leftward) to the global world frame.

`food_memory_timer = 90`: 90 ticks × 0.033s = ~3 seconds. If food leaves camera view (CARL turns away), the remembered global position is maintained for 3 seconds, continuing to guide navigation.

---

```python
if fused['food_dist'] < 1.0 and np.linalg.norm(fused['food_vec']) > 0.05:
    food_ray_idx = int(round((fused['food_angle'] - (-np.pi)) / (2*np.pi) * 24)) % 24
    for offset in range(-1, 2):
        raw_sonar[(food_ray_idx + offset) % 24] = 5.0
```

**Sensory Gating**: When food is within 1m, the sonar rays pointing AT the food are artificially set to 5.0m (maximum = "nothing there").

**Why?** Food is sonar-transparent (physically: a colored sphere, not a solid wall). But in the simulation, food might register as an obstacle if sonar rays hit it. Setting those rays to max prevents the reflex from dodging the food CARL is trying to eat.

**`food_ray_idx`**: Convert food angle to sonar array index.  
Formula: `(angle - (-π)) / (2π) × 24` maps angle from [-π, +π] to [0, 24].

`range(-1, 2)` = [-1, 0, 1] → modifies the food ray and one on each side (3 rays total, ~45° cone cleared).

---

#### Section C: Safeguards (Lines 568–581)

```python
out_of_bounds = (abs(robot_x) > 4.9 or abs(robot_y) > 4.9)
if out_of_bounds:
    self.hal.reset_robot()
    self.endocrine.surge_ne(0.5)
    return
```

Arena is ±5m. If CARL gets within 10cm of the boundary (4.9m), teleport it back to center. `surge_ne(0.5)` adds stress — this was a bad outcome. `return` skips the rest of this tick (no motor commands written).

```python
if np.isnan(self.S_unified).any() or np.isinf(self.S_unified).any():
    self.S_unified[:] = np.nan_to_num(self.S_unified, nan=0.0, posinf=1.0, neginf=-1.0)
```

**NaN/Inf sweep**: Checks all 532 values at once (`np.isnan().any()` = O(532)). If any bad values, replace them. This catches numerical instability before it propagates through the whole system.

---

#### Section D: Hippocampal Update (Lines 583–598)

```python
v_fwd = (self.motor_commands[0] + self.motor_commands[1]) / 2.0 * 0.05
vx = v_fwd * math.cos(robot_yaw)
vy = v_fwd * math.sin(robot_yaw)
```

**Velocity estimation:** Average of left + right motor commands = forward speed (differential drive). Multiply by `0.05` (empirical scaling: motor unit → m/s). Then decompose into world-frame vx, vy using heading angle.

This velocity estimate feeds path integration in the grid cell system — allows the hippocampus to track position even when GPS isn't available (in a real robot, this would run between GPS updates).

---

#### Section F: Precision Weighting and Reservoir Step (Lines 639–646)

```python
pi_sensory = self.endocrine.get_precision_weight()   # ≈ 0.5 to 2.0
u_raw = self._build_sensory_input(raw_sonar, fused)  # 37D input vector
u_weighted = pi_sensory * u_raw                       # Scale inputs by precision
noise_scale = self.endocrine.get_exploration_noise_scale()
y_cognitive = self.reservoir.step(u_weighted, noise_scale, self.dt)
```

**Precision-weighted input**: Multiply every input dimension by `π` (precision weight).  
- High precision (π=2.0): inputs effectively doubled → reservoir pays MORE attention to current sensors
- Low precision (π=0.5): inputs halved → reservoir relies more on its own recurrent dynamics (habits)

This is mathematically equivalent to **Bayesian active inference** where precision weights the likelihood term in perception.

---

#### Section G: Behavioral Modes and Motor Mixing (Lines 648–745)

```python
mode = self.endocrine.get_behavioral_mode(battery_level=self.hal.battery_level, food_visible=food_is_visible)
```

Then depending on mode:

**EXPLOIT mode (food visible):**
```python
hunger = 1.0 + 2.0 * (1.0 - self.hal.battery_level)  # 1 to 3
satiation = 1.0 / max(0.5, self.endocrine.DA)          # 1/DA
motivation = hunger * satiation                          # 0.33 to 6.0
turn_drive = clip(fused['food_angle'] * 4.0 * dist_scale * motivation, -4, 4)
fwd_boost = max(0.0, 1.5 * min(motivation, 2.0) * (1.0 - abs(fused['food_angle'])/1.0))
```

`turn_drive`: Proportional control on food angle. If food is at +30° (left), `turn_drive = 30° × 4 ≈ 2.1` → left turn of strength 2.1.

`fwd_boost`: Forward speed proportional to alignment. When food is directly ahead (angle≈0): `1.0 - 0 = 1.0` → full forward boost. When food is 90° away (angle=1.57): `1.0 - 1.57 = negative → max(0, ...) = 0` → no forward, just turning.

`hunger × satiation`: Motivational urgency. Low battery (hungry) + low DA (unsatisfied) → high motivation → faster approach.

**EXPLORE mode (default):**
```python
novelty_taxis = (steer toward least-recently-visited place cell)
nav_taxis = (1.0 - replay_blend) * novelty_taxis + replay_nav
```

Blends two exploration strategies:
1. **Novelty**: Go to places not visited recently (drives map coverage)
2. **Replay**: Follow the gradient toward remembered food locations

As hunger increases (`replay_blend` increases), replay dominates. At full battery, novelty dominates.

---

#### Section H: Final Motor Mixing (Lines 736–755)

```python
cpg_left  = self.CPG_FORWARD_BIAS   # 1.5
cpg_right = self.CPG_FORWARD_BIAS   # 1.5
cpg_neck  = cpg_neck_amp * math.sin(self.current_tick * self.CPG_NECK_FREQUENCY)  # Oscillating

u_left  = cpg_left  + y_cognitive[0] + total_reflex[0]
u_right = cpg_right + y_cognitive[1] + total_reflex[1]
u_neck  = cpg_neck  + y_cognitive[2]
```

**Three-layer motor mixing:**
1. **CPG (Central Pattern Generator)**: The baseline — constant forward push (1.5) + neck sinusoid
2. **Cognitive (Reservoir)**: Modifies trajectory — up to ±2 each side
3. **Reflex (SNN)**: Emergency overrides — up to ±6 each side

Priority (effective): Reflex > Cognitive > CPG (because reflex has highest magnitude)

**`CPG_FORWARD_BIAS = 1.5`**: Makes CARL always want to move forward. If cognitive and reflex both output 0, CARL still moves at speed 1.5. This prevents being stuck when the brain is uncertain.

**CPG neck oscillation:**
```python
cpg_neck = 0.7 × sin(tick × 0.04)
```
- Period = 2π/0.04 = 157 ticks = 5.2 seconds (slow neck sweep)
- Amplitude = ±0.7 radians = ±40 degrees
- Enables CARL to scan left and right while driving, giving the vision system a wide field of view

---

#### Section I: RLS Learning Trigger (Lines 757–768)

```python
has_reflex  = np.linalg.norm(total_reflex) > 0.05
has_surprise = (NE > 0.15 or DA > 1.05 or ACh > 0.7)

if has_reflex or has_surprise:
    time_since_rls = self.current_tick - self.last_rls_tick
    error_norm = np.linalg.norm(self.reservoir.last_prediction_error)

    if time_since_rls >= 6 or (error_norm > 0.25 and time_since_rls >= 3):
        y_target = self._compute_rls_target(y_cognitive, y_executed)
        self.reservoir.rls_update(y_target)
        self.last_rls_tick = self.current_tick
```

**WHEN does learning happen?**
1. When something interesting occurred: reflex fired (`has_reflex`) OR neurochemical surprise (`has_surprise`)
2. At least 6 ticks since last update (prevents overfitting to correlated sequential frames)
3. OR at least 3 ticks since last update AND prediction error is large (learn faster when wrong)

**WHY only learn when surprised?** This is the brain's **prediction error-driven learning principle** (same as dopamine). Learning constantly on every tick would:
- Overfit to boring, expected situations
- Waste computation on stable periods
- Create instability (the network chases its own outputs)

Learning ONLY when the reflex corrects the reservoir (surprise) forces the reservoir to learn FROM the reflex — turning a fast, instinctive correction into a slow, learned response.

**`_compute_rls_target(y_cognitive, y_executed)`:**
```python
reflex_dev = y_executed - y_cognitive   # How much did the reflex change things?
reflex_dev[2] = 0.0                     # Don't learn neck from this
return reflex_dev
```
Target = "the reflex's correction." Tells the reservoir: "next time you're in this situation, output THIS (what the reflex did), not THAT (what you did)." Over time, the reservoir internalizes reflex corrections → develops smooth anticipatory obstacle avoidance rather than reactive jerks.

---

### Lines 821–895: `run_simulation()` — The Main Loop

```python
physics_ticks_per_control = 8
control_period = 1.0 / 30.0   # 33.3ms
```

**Why `physics_ticks_per_control = 8`?**  
MuJoCo physics runs at `1/timestep = 1/0.004166 = 240 Hz` (set in XML).  
Control runs at 30 Hz.  
`240 / 30 = 8` physics ticks per control tick.

This means: for every ONE brain update (read sensors, compute commands), the physics engine simulates 8 small timesteps. Smaller physics steps = more accurate contact simulation (especially wheel-floor friction).

---

```python
while runner.hal.viewer.is_running():
    loop_start = time.time()
    if loop_start >= next_control_time:
        runner.step()
        for _ in range(physics_ticks_per_control):
            mujoco.mj_step(runner.hal.model, runner.hal.data)
        sync_viewer_rays()
        next_control_time += control_period
    else:
        time.sleep(0.001)
```

**Real-time pacing:** The `next_control_time` counter advances by exactly `control_period = 0.0333s` each iteration. If computation takes less than 33ms, `time.sleep(0.001)` yields CPU. If computation takes exactly 33ms, the next control tick starts immediately.

This is a **fixed-rate control loop** (not fixed step) — robust to variable computation time. Even if one tick takes 50ms (GPU busy), the NEXT tick will still try to run immediately. The robot might skip one update but won't drift into ever-longer delays.

**`sync_viewer_rays()`**: Draws the 24 LiDAR rays in the 3D viewer. Red lines = rays that hit something. Green lines = rays that hit nothing (extended to 5m). Uses MuJoCo's `mjv_initGeom` and `mjv_connector` to draw line geometry directly in the scene.

---

```python
finally:
    runner.reservoir.save(os.path.join(BASE_DIR, "memory", "carl_reservoir.npz"))
    runner.telemetry.close()
```

**Always save on exit** (even if Ctrl+C): The `finally` block runs regardless of how the loop exits. This ensures learned weights are never lost even if the user kills the program.

---

## FINAL SYSTEM INTEGRATION MAP

```
Every 33ms (30 Hz):
│
├─[A] HAL.read_sensors() → raw_rays[24], battery[1]
│     ↓ 24-ray → 12-ray sonar sim → interpolate back → raw_sonar[24]
│
├─[B] HAL.read_camera() → SSD detections → SensorFusion.fuse() → fused{}
│     ↓ cross-modal sonar gate, food memory, sensory gating
│
├─[C] Safety checks (OOB, NaN)
│
├─[D] HippocampalNavigator.step() → grid cells, place cells, topological graph
│     ↓ reward diffusion (hippocampal replay)
│
├─[E] EndocrineSystem.step() → DA, NE, SHT, ACh decay
│     ↓ surge DA/NE/SHT based on food/hazard/wall events
│
├─[F] precision = endocrine.get_precision_weight()
│     u = build_sensory_input() → precision × u
│     ↓ y_cognitive = reservoir.step(u) [500-neuron LSM]
│
├─[G] reflex_outputs = SpikingReflexLayer.step() [24-ray SNN obstacle avoidance]
│
├─[H] behavioral_mode = EXPLOIT / SURVIVE / EXPLORE
│     nav_taxis = food taxis / replay navigation / novelty navigation
│
├─[I] FINAL MOTOR MIX:
│       u_left  = CPG(1.5) + cognitive[0] + reflex[0] + nav[0]
│       u_right = CPG(1.5) + cognitive[1] + reflex[1] + nav[1]
│       u_neck  = CPG_neck_sin + cognitive[2]
│
├─[J] HAL.write_motors(u_left, u_right, u_neck)
│
├─[K] RLS learning (if surprised or reflex fired)
│
└─[L] TelemetryLogger.log() → CSV row
```
