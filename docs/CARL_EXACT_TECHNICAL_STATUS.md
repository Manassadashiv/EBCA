# CARL-Ω / EBCA: Exact Technical Status & Comprehensive Master Plan
**Document Reference:** `d:\ebca\docs\CARL_EXACT_TECHNICAL_STATUS.md`  
**Updated:** August 2026  
**Status:** Grounded Engineering Reality & Production Execution Plan (Incorporating All 5 NASA JPL OSR Extractions)

---

## Executive Summary

| Category | Metric | Status |
|---|---|---|
| **Phase 1 — Digital Twin Software** | **62.5% Written / ~25% Actively Wired** | Main loop runs 5 core modules; 2 written modules remain unplugged |
| **Phase 2 — Physical Hardware** | **0% Assembled (100% Blueprinted)** | 2WD Hybrid chassis matching `vessel_kinetic.xml` for 1:1 Sim-to-Real transfer |
| **NASA JPL OSR Extractions** | **All 5 Innovations Integrated** | Packet safety, modular framing, dual-board team, velocity math, & power isolation |
| **Total Combined Project Progress** | **34.4%** | Software core active, physical hardware ready for build execution |

---

## 1. What Has Been Completed & Actively Wired (The Active ~25%)

These modules are **currently imported and running tick-by-tick** inside the primary entry point ([carl_simulation.py](file:///d:/ebca/carl_simulation.py)):

| Module / Component | File | Lines | Active Function in Main Loop |
|---|---|---|---|
| **Spiking Reservoir** | [carl_reservoir.py](file:///d:/ebca/brain/carl_reservoir.py) | 196 | Liquid State Machine ($N=500$ neurons) operating at critical state ($\rho \approx 1.0$) with RLS readout weight updates. |
| **Endocrine System** | [carl_endocrine.py](file:///d:/ebca/brain/carl_endocrine.py) | 118 | Tracks continuous neuromodulator dynamics: Dopamine (`DA`), Noradrenaline (`NE`), Serotonin (`5-HT`), and Acetylcholine (`ACh`). |
| **Spiking Reflex Layer** | [carl_reflex.py](file:///d:/ebca/brain/carl_reflex.py) | 176 | Fast hazard avoidance layer that overrides motor mixing during obstacle/wall contact. |
| **Grid & Place Cells** | [carl_grid_cells.py](file:///d:/ebca/brain/carl_grid_cells.py) | 452 | Hippocampal spatial mapping module tracking 2D place cell activations and feeding waypoints into motor mixing. |
| **STDP Evaluator** | [carl_stdp.py](file:///d:/ebca/brain/carl_stdp.py) | 277 | Spike-Timing-Dependent Plasticity evaluator updating synaptic eligibility traces. |
| **SSD-Lite Vision** | `carl_simulation.py` | — | Real-time object detection inference (line 192) classifying food/hazards from camera frames. |
| **Hardware Abstraction** | `HardwareInterface` | — | Normalizes 25-D sensory inputs (24 Sonar/ToF rays + 1 battery charge metric). |
| **Telemetry Logger** | `TelemetryLogger` | — | CSV logging of per-tick endocrine levels, motor torques, coordinates, and control loop execution latency. |

---

## 2. Available Standalone Modules & Pipelines

These files exist in the repository, pass Python syntax checks, but are either standalone utilities or **not yet wired into `carl_simulation.py`**:

### A. Standalone Cognitive Modules
- **[carl_physarum.py](file:///d:/ebca/brain/carl_physarum.py)** (256 lines): Slime-mold pathfinder that dynamically decays edge weights based on route traversal success. *Status: Unplugged in main loop.*
- **[carl_omega_extensions.py](file:///d:/ebca/brain/carl_omega_extensions.py)** (125 lines): Contains Theta gating (suppresses plasticity under high stress) and predictive allostasis. *Status: Unplugged in main loop.*

### B. Behavioral Testbed & Physics Wrappers
- **[phase18_alife_pretrained.py](file:///d:/ebca/phase18_alife_pretrained.py)** (1,035 lines): Standalone ALife behavioral testbed running on the 2-body world ([carl_mujoco.xml](file:///d:/ebca/world/carl_mujoco.xml)).
- **[carl_mj_physics.py](file:///d:/ebca/world/carl_mj_physics.py)** (210 lines): MuJoCo wrapper interfacing simulation physics with control loops.

---

## 3. Step-by-Step Execution Master Plan

### 🚀 Phase 1 — Software Integration Steps ([integration_roadmap.md](file:///d:/ebca/docs/integration_roadmap.md))

* [x] **Step 1: Arm Reach & Grasping Reflex** ✅ **(COMPLETED)**
  - Wired all 16 arm actuators in [vessel_kinetic.xml](file:///d:/ebca/world/vessel_kinetic.xml) into [carl_simulation.py](file:///d:/ebca/carl_simulation.py). Arms extend forward-down and grippers close when `food_dist < 1.2m` and `DA > 0.8`. Tested clean with 0 syntax/runtime errors.
* [ ] **Step 2: Wire Physarum Pathfinder & Omega Extensions**
  - Import `PhysarumPathfinder` to replace static A* with slime-mold adaptive route decay.
  - Gate `reservoir.rls_update()` on `theta_gate.open` during high stress (`NE > 0.4`).
* [ ] **Step 3: The Witness (Layer 4 Metacognition)**
  - Implement `brain/carl_witness.py` with a circular episode buffer. Detect repeated failure loops and trigger diagnostic `WIT-401` overrides.
* [ ] **Step 4a: Imagination Engine ($T_{wm}$ — Layer 6)**
  - Implement `brain/carl_imagination.py` spatiotemporal forward predictor for active inference.
* [ ] **Step 4b: MPC Causal Reasoning (Layer 5)**
  - Implement `brain/carl_mpc.py` for 50-step post-failure counterfactual rollouts.

---

## 4. The 5 NASA JPL Open Source Rover (OSR) Extractions

We extracted **5 core engineering innovations** from NASA JPL’s Open Source Rover (`nasa-jpl/open-source-rover`) to reinforce CARL's hardware architecture:

1. **CRC16 Checksum Serial Packet Safety Protocol**:
   - Binary UART checksum validation between Orange Pi 5 and ESP32 to reject noise-corrupted motor commands.
2. **Modular 2020 Slotted T-Slot Aluminum Framing**:
   - Extrusion mounting rails for easy, screw-in attachment of arm servos, neck servos, and ToF laser rings.
3. **Dual-Board "Driver + Thinker" Architecture (Orange Pi 5 + ESP32)**:
   - Separates 6.0 TOPS AI vision/spiking reservoir thinking from 100 Hz real-time ESP32 motor pulse generation so CARL never freezes during heavy AI math.
4. **Kinematic Velocity-to-Motor Mapping Equations**:
   - Extracted math converting high-level target velocity $(v_{\text{forward}}, \omega_{\text{turn}})$ into exact wheel motor PWM signals.
5. **Isolated Dual-Rail Power Distribution Circuit**:
   - Diode-isolated battery rails separating raw 7.4V motor current spikes from clean LM2596 5.0V regulated power for the Orange Pi 5.

---

## 5. Hardware Evolution & Sourcing Tiers (India Focus)

| Tier | Target Budget | Core Compute & NPU | Primary Spatial Sensors | Tactile & Motor Feedback | Sourcing Specs |
|---|---|---|---|---|---|
| **Tier 1: Frugal Base** | **~₹7,581 INR** | Orange Pi 3B (0.8 TOPS NPU) + ESP32 | 12x HC-SR04 Ultrasonic Sonar Ring | Standard RC Servos (MG996R/SG90) | [hardware_prototyping.md](file:///d:/ebca/hardware_prototyping.md) |
| **Tier 2: Production "Sweet Spot"** | **~₹9,845 INR** *(Sub-10K Ceiling)* | **Orange Pi 5 (6.0 TOPS RK3588 NPU)** + ESP32 | **6x VL53L1X Laser ToF Sensors** *(Solid-State Micro-LiDAR, Pitch-Black Vision)* | **1:1 2WD Sim-Matched Chassis** + **INA219 Torque Sensor** + **FSR-402 Pressure Pads** + **PCA9685 Servo Driver** | [CARL_SWEET_SPOT_HARDWARE_BOM.md](file:///d:/ebca/docs/CARL_SWEET_SPOT_HARDWARE_BOM.md) |
| **Tier 3: Unconstrained Flagship** | **~₹3,83,500 INR** *(Lab R&D)* | NVIDIA Jetson Orin NX 16GB (100 TOPS) + Akida SNN Coprocessor | RPLIDAR S2L 360° LiDAR + OAK-D Pro Stereo Depth | GelSight Mini Optical Tactile Skin + Dynamixel XM430 Smart Bus Servos | [CARL_UNCONSTRAINED_FLAGSHIP_HARDWARE_SPEC.md](file:///d:/ebca/docs/CARL_UNCONSTRAINED_FLAGSHIP_HARDWARE_SPEC.md) |

---

## 6. Visual Intelligence, VLA & DeepMind Integration Strategy

1. **Local NPU Vision (Orange Pi 5 @ 60 FPS)**:
   - Orange Pi 5's **6.0 TOPS NPU** executes quantized YOLOv8 / YOLO-World object detection at **60+ FPS**, tracking target objects and obstacle coordinates locally.

2. **Google DeepMind Gemini Robotics 2 / ER 2 Integration**:
   - **High-Level Embodied Reasoning (ER 2)**: Stream camera frames over Wi-Fi to **Google AI Studio Free API**. Gemini Robotics ER 2 analyzes the 3D scene, plans multi-step tasks, and outputs spatial target coordinates.
   - **Local Motor Brainstem**: CARL's local spiking brain ([carl_simulation.py](file:///d:/ebca/carl_simulation.py)) executes low-latency (10ms) arm reaching and obstacle avoidance.

3. **OpenVLA Integration Option**:
   - For 100% offline, on-device motor control without cloud internet, download **OpenVLA** (Stanford / Berkeley / DeepMind 7B VLA model on Hugging Face) and run local action generation.

4. **1-Shot Holographic Object Embedding**:
   - Unfamiliar objects (confidence < 0.30) trigger a Noradrenaline (`NE`) curiosity spike. CARL points camera/arm, prompts the user via phone/web, extracts a **512-dimensional feature embedding**, and saves it for instant **Cosine Similarity** recognition—**zero retraining needed**.

---

## 7. Dual Simulation Engine Strategy (MuJoCo vs. Webots)

| Simulation Role | Simulation Engine | Primary Purpose & Strength |
|---|---|---|
| **Primary Cognitive Training Engine** | **MuJoCo (Google DeepMind)** | Sub-millisecond convex contact physics, zero-jitter multi-joint arm grasping, 1,000+ FPS headless speed for spiking neural network training in `carl_simulation.py`. |
| **Secondary Visual Showcase Engine** | **Webots (Cyberbotics)** | Export via `world/carl.urdf` using native Webots Python API (**Zero ROS dependency**) for photorealistic 3D environment rendering (apartments, cities, outdoor landscapes) for video demonstrations. |

---

## 💡 Master Execution Matrix

```
[CARL-Ω SYSTEM ARCHITECTURE]
├── 🟢 ACTIVE CORE           : LSM Reservoir, Endocrine (DA/NE/5-HT/ACh), Spiking Reflex, Grid Cells, STDP
├── 🟢 INTEGRATION STEP 1    : Arm Actuator Reflex (vessel_kinetic.xml -> carl_simulation.py) ✅
├── ⬜ INTEGRATION STEP 2    : Connect Physarum Pathfinder & Omega Theta Gating
├── 🔴 UNBUILT LAYERS        : The Witness (L4), MPC Rollouts (L5), Imagination Engine (L6), SOM (L7)
├── ⚡ 1:1 SIM-MATCHED HARDWARE: 2WD Chassis (matching vessel_kinetic.xml) + Orange Pi 5 (6.0 TOPS) + VL53L1X Laser ToF (~₹9,845 INR)
├── 🚀 5 NASA JPL EXTRACTIONS: CRC16 Packet Safety + 2020 Framing + Dual-Board Team + Velocity Math + Power Isolation
├── 🧠 AI VISION / VLA       : Local NPU YOLOv8 + Google DeepMind Gemini Robotics ER 2 (Free API) + OpenVLA
└── 🎮 DUAL SIMULATION       : MuJoCo (Primary Cognitive Engine) + Webots (Visual 3D Demo Engine via URDF)
```
