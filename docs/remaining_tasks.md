# Detailed Roadmap: Unimplemented & Unintegrated Features (CARL-Ω)

This document provides a highly detailed breakdown of the remaining tasks required to complete Phase 1 (The Digital Twin) and Phase 2 (The Physical Prototype). You can use this directly in your project proposal to outline your future scope of work.

---

## Part 1: Phase 1 (Digital Twin) Integration Tasks

While many individual files and math formulations have been written as standalone prototypes in the `GENESIS/carl_scout` directory, they are currently disconnected from the main active simulation loop (`carl_simulation.py`). The following integration steps are required:

### 1. Primate Body & Kinematics Integration (Layer 0)
* **Chassis XML Migration**: Switch the active Mujoco world file from the basic 4-wheeled model (`vessel_kinetic.xml`) to the 28-DOF primate scout model (`carl_primate_scout.xml`).
* **Bilateral Inverse Kinematics (IK) Mapping**: Wire the Damped-Least-Squares IK controller into the active step loop, translating 3D coordinates into joint angles for the 5-joint arms.
* **Closed-Loop Touch Grasping**: Program the finger actuators (thumb, index, middle) to trigger clasping forces *only* when local touch sensors register physical collision with target blocks.
* **Posture-Expression Motor Mapping**: Hook up the emotional posture system (`carl_expression.py`). Map raw dopamine, norepinephrine, cortisol, and serotonin levels to head/neck tilt angles and arm positions to express Joy, Sadness, Fear, Curiosity, Excitement, Calm, and Surprise.

### 2. High-Dimensional Memory (Layer 1)
* **Vector Symbolic Architecture (VSA) Wiring**: Connect the 40,000-dimensional bipolar hypervector engine.
* **Decoupled Register Lanes**: Bind and bundle sensory/emotional vectors into three separate, active registers: `M_spatial`, `M_affective`, and `M_procedural`.
* **Sleep Consolidation Protocol**: Wire NREM-1, NREM-3, and REM cycles. Program weight decay ($\lambda = 0.95$) to dim background noise and salience amplification ($\gamma = 2.0$) to reinforce survival-critical events.

### 3. Cognitive Stack Wiring (Layers 4–7)
* **Layer 4 — The Witness (Metacognition)**: Integrate the circular episode buffer (storing coordinates, NE levels, actions, and outcomes). Write the pattern counter to detect repeated failure states and inject targeted torque penalties to prevent CARL from repeating his own errors.
* **Layer 5 — Causal Reasoning (Question Generator)**: Connect the post-death counterfactual simulator. After a failure, the agent must run 3 alternative forward simulations using estimated dynamics, choose the best outcome, and scale RLS learning weights on that trajectory.
* **Layer 6 — The Imagination Engine (Active Inference)**: Wire the spatiotemporal predictor RNN. Establish the predictive coding loop where CARL's internal prediction ($T_{wm}$) serves as his primary reality, and physical sonars/cameras are used only as error-correcting inputs.
* **Layer 7 — Concept Genesis**: Implement unsupervised Self-Organizing Maps (SOM) to cluster continuous sensor arrays into internal abstract concepts (e.g. mapping high tilt rate + low battery to a single conceptual "vulnerability" state).

### 4. Social & Multi-Body Mechanics
* **Collective Long-Term Memory (LTM)**: Write the memory synchronization bridge to share weights between dual sibling bodies.
* **Social Emotional Contagion**: Code the Norepinephrine (NE) spike that propagates when a sibling body experiences failure, simulating grief/mourning.

---

## Part 2: Phase 2 (Physical Hardware) Translation Tasks

Once the digital twin is fully integrated and training successfully, Phase 2 covers the transition to physical hardware:

### 1. The Sim-to-Real Bridge
* **Domain Randomization**: Inject randomized physical parameters during simulation training:
  * Lateral floor friction: $\text{Uniform}(0.4, 1.2)$
  * Head/Torso link mass variations
  * Input sensor Gaussian noise
  * Motor step delays: 1 to 3 frames
* **HAL Porting**: Map the generalized `HardwareInterface` calls from MuJoCo APIs to real-world GPIO, PWM, and I2C micro-controller serial outputs.

### 2. Physical Construction & Assembly
* **Chassis Fabrication**: Assemble the 4-wheeled physical chassis, expressive servo-controlled neck, and bilateral reach limbs.
* **Sensor Array Integration**: Calibrate the physical 12-sonar ultrasonic array, IMU, and head-mounted visual camera.
* **Online Embedded Learning**: Port the RLS matrix updates and the LSM reservoir weights onto the onboard CPU/microcontroller, optimizing execution to fit the real-time 30 Hz control cycle.
