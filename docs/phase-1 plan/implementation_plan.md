# Implementation Plan - Rebuilding CARL (Step 1: Multi-Modal Sensorimotor Interface)

This plan details **Step 1: Multi-Modal Sensorimotor Interface**, connecting simulated perception (camera rendering and vision AI-based sensor fusion), exteroceptive signal routing to endocrine baselines, proprioceptive self-body filtering, vestibular neck lean dynamics, and precision weighting.

---

## 1. User Review Required

> [!IMPORTANT]
> - **Morphology Shift to Wall-E (Statically Stable)**: We have moved CARL's simulation from the unstable 2-wheeled balancer (`carl_mujoco.xml`) to the statically stable 4-wheeled Wall-E chassis (`vessel_kinetic.xml`). This model rests flat on two driven wheels and two passive caster wheels.
>   * *Benefit*: Eliminates the need to waste neural computation on basic upright Segway balancing.
> - **Visual AI instead of Heuristics**: We will NOT use color-tagging. We have implemented a simulated perception pipeline:
>   1. **Data Collection**: Captured 1,200 screenshots of objects inside the Wall-E world (`world/vessel_kinetic.xml`).
>   2. **Vision Model Training**: Trains a PyTorch CNN classifier and bounding box regressor on this custom dataset to output classifications based on shape, size, and geometry.
>   3. **Perception Inference**: Run this trained vision model on CARL's virtual camera stream (`eye_cam`) at 30 Hz.
> - **Proprioceptive Self-Body Filtering (Self vs. Environment)**:
>   1. **Physical Reality**: LiDAR rays will be cast normally and bounce off CARL's own moving arms and tires in the simulation.
>   2. **Kinematic Software Masking**: Software reads the active joint angles (neck, left/right arms) and uses **Forward Kinematics (FK)** to compute the 3D space occupied by CARL's own parts.
>   3. **Signal Gating**: Any LiDAR return that falls within these calculated self-body boundaries is filtered out, preventing self-reflections from triggering panic loops.
> - **Vestibular Neck Lean Dynamics**:
>   1. **Active Posture Balance**: While CARL cannot tip over on 4 wheels, he has a heavy head on a flexible parallel-link neck.
>   2. **Centrifugal Neck Tilt**: When steering right/left, the neck actuator (`neck_sweep`) will dynamically tilt inward (leaning into the turn) to keep the head-mounted camera stable.
>   3. **Linear Neck Lean**: Tilt the neck forward during acceleration and backward during braking to maintain camera leveling.
> - **Tactile Arm Retraction Reflex**:
>   1. If the arm collides with a wall or obstacle, bumper sites or joint limit torques trigger a priority retract signal.
>   2. Pulls the arm back to the body, clearing the LiDAR field-of-view and allowing normal scans to resume.
> - **Endocrine Kinetics Integration**: Updates neuromodulators (DA, NE, 5-HT, ACh) at 30 Hz using decay kinetics, modulated by exteroceptive event surges (e.g. wall proximity -> NE panic surge; food contact -> DA reward surge).
> - **Precision Weighting Loop**: Exteroceptive LiDAR inputs are scaled by $\pi_{\text{sensory}}$ calculated from the active neuromodulator states.

---

## 2. Proposed Changes

### Level 0: Physical Embodiment & Simulation Engine

#### [MODIFY] [carl_simulation.py](file:///D:/ebca/carl_simulation.py)
- **Initialize Offscreen Renderer:**
  - Instantiate `mujoco.Renderer` in `SimulationHAL` to render from `"eye_cam"` at 160x120.
- **Implement Kinematic Software Masking:**
  - Write a software filter inside `read_sensors()` that calculates body-bounding capsules using active joint positions.
  - Compare LiDAR ray depths against these capsules and mask out values matching the self-body coordinates.
- **Implement Vestibular Neck Lean Loop:**
  - Tilt the neck joint (`neck_sweep`) based on wheel acceleration and yaw rates to stabilize the camera.
- **Integrate Trained Vision Model:**
  - Load the trained PyTorch weights (`carl_vision.pt`) at boot.
  - Run inference at 30 Hz to predict target bounding boxes and labels (`[FOOD, OBSTACLE, PREDATOR, BACKGROUND]`).
- **Implement Perceptual Sensor Fusion & Self-Gating:**
  - Query the LiDAR ray distance $d$ corresponding to the calculated bounding box angle.
  - Output relative 3D pose vectors for targets into `S_unified`.
- **Integrate Endocrine Kinetics:**
  - Update neuromodulator baseline variables at 30 Hz.
  - Route exteroceptive event surges (e.g. $d_{\text{LiDAR}} < 0.25\text{ m} \implies$ NE surge $+0.4$; place transition $\implies$ ACh surge $+0.25$; food contact $\implies$ DA surge $+0.35$).
- **Implement Dynamic Precision Weighting:**
  - Multiply raw exteroceptive inputs by $\pi_{\text{sensory}}$ before feeding them to the SNN reflex network.

---

## 3. Verification & Validation Plan

### Automated Tests
- Run the dataset collector:
  `python D:\ebca\brain\collect_vision_dataset.py`
- Run the model trainer:
  `python D:\ebca\brain\train_vision.py`
- Run the integrated simulation runner:
  `python D:\ebca\carl_simulation.py`

### Manual Verification
- **Visual perception validation:** Confirm in the terminal outputs that CARL successfully detects when food, an obstacle, or a predator enters his camera FOV and classifies them correctly based on shape.
- **Self-recognition gating:** Move CARL's neck/arms to their limits and verify that the LiDAR ignores reflections off his own body.
- **Vestibular Lean check:** Steer CARL sharply and verify that his head leans dynamically into the turn to stabilize the camera feed.
- **Endocrine fluctuations:** Verify that printed neuromodulator values (`DA`, `NE`, `5HT`, `ACh`) fluctuate dynamically when the robot gets close to walls, cycles place cell coordinates, or eats food.

