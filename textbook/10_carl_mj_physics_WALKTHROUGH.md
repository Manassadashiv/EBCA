# Walkthrough: `world/carl_mj_physics.py`
### *MuJoCo Physics Engine Interface (210 Lines)*

This module wraps DeepMind’s MuJoCo physics engine (`mujoco`), managing XML model loading, physics stepping, sensor reading extractions, and rendering viewport hooks.

---

## 1. Structure & Model Loading

* **Lines 1–9:** Imports `mujoco`, `numpy`, and `os`. Sets up file paths using `BASE_DIR` absolute resolution.
* **Lines 10–25:** Defines class `CarlPhysics`. Holds `model` (`MjModel`), `data` (`MjData`), rendering handle, and sensor data arrays.
* **Lines 26–35:** `__init__(xml_filename="carl_mujoco.xml")`:
  * Resolves absolute XML path: `os.path.join(BASE_DIR, "world", xml_filename)` (or root fallback).
  * Loads model: `self.model = mujoco.MjModel.from_xml_path(xml_path)`.
  * Allocates simulation data buffer: `self.data = mujoco.MjData(self.model)`.

---

## 2. Sensor Extractions

* **Lines 36–55:** `get_qpos()` & `get_qvel()`: Extract generalized coordinate positions ($q_{pos}$) and velocities ($q_{vel}$).
* **Lines 56–78:** `get_sonar_distances()`: Reads distance readings from `data.sensordata` array. Replaces far/missing values with maximum range $10.0\text{m}$.
* **Lines 80–98:** `get_imu_data()`: Reads accelerometer (`accel`), gyroscope (`gyro`), and magnetometer/compass sensors from `data.sensordata`.
* **Lines 100–120:** `get_joint_positions()` & `get_joint_velocities()`: Extract wheel and arm joint angles and angular velocities.

---

## 3. Control Application & Physics Stepping

* **Lines 121–145:** `apply_control(ctrl_vector)`: Copies motor control array into `data.ctrl[:]`. Clamps values to actuator limits.
* **Lines 146–165:** `step(n_substeps=8)`: Runs `mujoco.mj_step(model, data)` `n_substeps` times (8 substeps at 240 Hz resolution inside the 30 Hz control cycle) for numerical physics stability.
* **Lines 166–190:** `reset()`: Resets simulation state to keyframe 0 (`mujoco.mj_resetData()`).
* **Lines 191–210:** `launch_viewer()`: Spawns interactive 3D OpenGL visualization window using `mujoco.viewer.launch_passive()`.
