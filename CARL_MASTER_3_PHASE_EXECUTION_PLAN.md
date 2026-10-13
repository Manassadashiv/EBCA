# CARL-DX: Master 3-Phase Execution Plan & Developmental Progression
**Document ID:** `CARL-PLAN-2026-PHASES-V1`  
**Candidate:** Manas Sadashiv (Roll: 22011P0310)  
**Affiliation:** JNTUH UCESTH, Department of Mechanical Engineering (IDP AMS)  
**Title:** DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS  
**Date Saved:** October 10, 2026  

---

## Executive Overview: The 3-Phase Architecture

This document preserves the official, sequential execution plan designed to take CARL from its active developmental roadblock through full cognitive closure, academic viva defense, and frugal physical hardware demonstration.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: The Immediate Fix for Stage 3.4 (Deadlock Resolution)        │
│   ├── Step 1: Eliminate Rear Blind Spot in HAL (-168° to +168°)   ✅   │
│   ├── Step 2: Upgrade to True Continuous Active Inference         ✅   │
│   └── Step 3: Run Frozen Stage 3.4 Certification Battery          ⏳   │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Complete the 5-Stage Master Dissertation Progression          │
│   ├── Step 4: Stages 3.5 to 3.7 (Friction, Physarum, Vision)      🔒   │
│   ├── Step 5: Stage 4 (Lifelong Memory via R-STDP & HDC)          🔒   │
│   └── Step 6: Stage 5 (Metacognition & "The Witness")             🔒   │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Physical Hardware Prototype Demonstration (Viva Defense)      │
│   └── Step 7: ESP32 Frugal Prototype (₹2,150 BOM & Sim-to-Real)   🔒   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: The Immediate Fix for Stage 3.4 (Resolving the Deadlock)

### Step 1: Eliminate the $120^\circ$ Rear Blind Spot
* **Target File:** [`brain/carl_stage1_hal.py`](file:///d:/ebca/brain/carl_stage1_hal.py)
* **Problem:** Distance rays were originally confined to $[-120^\circ, +120^\circ]$. When reversing or pivoting inside narrow $70\text{ cm}$ corridors, the robot was completely blind to rear obstacles.
* **Implementation:** Expanded the sonar ray array to 15 radial beams spanning $[-168^\circ, +168^\circ]$ at $0.14\text{ m}$ radial offset outside the chassis perimeter.
* **Status:** **COMPLETED & VERIFIED ✅**

---

### Step 2: Upgrade to True Continuous Active Inference (Kill the Canned Menu)
* **Target File:** [`brain/carl_active_inference.py`](file:///d:/ebca/brain/carl_active_inference.py)
* **Problem:** Brittle 128 canned action templates, discrete state latches (`_reverse_latched`, `_pivot_done`), and hardcoded Cartesian coordinates (`if c_x < 0.60`) violated the doctoral mandate of autopoietic emergence.
* **Implementation:**
  1. **Purged all heuristics:** Deleted all state latches, `if s_left < 0.85` checks, and coordinate cheats.
  2. **11-Point Chassis Hull Shield:** Evaluates the real rectangular bumper geometry ($23\text{ cm} \times 27\text{ cm}$) in $\mathcal{O}(1)$ time.
  3. **Continuous Harmonic Potential Field:** Evaluates electrostatic-like wall repulsion ($\mathcal{J}_{\text{rep}} \propto 1/d^2$) for natural hallway centering without conditional logic.
  4. **Geodesic Navigation Manifold:** Smooth gradient guidance ($\theta_{\text{des}} = -\operatorname{atan2}(\nabla \mathcal{D}_{\text{free}})$) computed via dynamic programming on allocentric occupancy memory.
  5. **Continuous Velocity Grid ($M=128, H=15$):** Uniform sampling over the 2D velocity manifold ($u_{\text{fwd}} \in [-0.65, 0.75], u_{\text{diff}} \in [-0.90, 0.90]$) blended via softmax path-integral weighting.
  6. **Static Geometry Caching:** Cached the traversable manifold, dropping mean cycle latency to **4.99 ms** (p95: **5.63 ms**).
* **Audit:** Passed 7/7 automated tests in [`tests/test_stage3_ast_anti_cheat.py`](file:///d:/ebca/tests/test_stage3_ast_anti_cheat.py) in **21.03 s** (100% clean AST anti-cheat quarantine).
* **Status:** **COMPLETED & VERIFIED ✅**

---

### Step 3: Run the Frozen Stage 3.4 Certification Battery
* **Target Files:** [`tests/test_stage3_4R4_screening.py`](file:///d:/ebca/tests/test_stage3_4R4_screening.py), [`tests/test_stage3_4R3_certification.py`](file:///d:/ebca/tests/test_stage3_4R3_certification.py)
* **Objective:** Execute the multi-environment benchmark across all 50 matched configurations $\times$ 4 arms (Cul-de-sac turning bays, asymmetric T-junctions, and narrow non-line-of-sight challenge mazes).
* **Certification Gates:**
  * **Gate 1:** Escape Rate $\ge 80.0\%$, Collision Rate $\le 10.0\%$.
  * **Gate 2:** Complete Emergent Maneuver Verification (Phase 1 reversal $\to$ Phase 2 re-orientation $\to$ Phase 3 corridor entry $\to$ Phase 4 egress).
  * **Gate 3:** Epistemic Causal Necessity (ARM-A vs ARM-B separation, McNemar $p < 0.001$).
  * **Gate 4:** Real-Time Cycle Latency: Mean $\le 20.0\text{ ms}$, p95 $\le 45.0\text{ ms}$ (Already achieving **4.99 ms** mean / **5.63 ms** p95).
  * **Gate 5:** 100% AST Decision Pipeline Isolation (Zero simulator coordinates).
* **Status:** **UP NEXT (Current Active Milestone) ⏳**

---

## Phase 2: Complete the 5-Stage Master Dissertation Progression

Once Stage 3.4 is certified and locked, development progresses through the remaining developmental milestones on the unified zero-copy agent bus:

### Step 4: Environmental Adaptation & Canonical Integration (Stages 3.5 – 3.7)
* **Stage 3.5 — Physical Perturbation & Adaptation:**
  * Wire [`brain/carl_adaptation.py`](file:///d:/ebca/brain/carl_adaptation.py) and [`brain/carl_endocrine.py`](file:///d:/ebca/brain/carl_endocrine.py).
  * Test sudden friction collapse ($\mu = 0.20$, ice/oil patches) and motor torque loss.
  * Morphological slip estimation dynamically scales motor gains, while stress hormone kinetics (Noradrenaline / Cortisol) modulate MPPI temperature $\lambda$ to broaden exploratory candidate spread during high uncertainty.
* **Stage 3.6 — Behavioral Synergy Formation & Physarum Flow Routing:**
  * Wire [`brain/carl_physarum.py`](file:///d:/ebca/brain/carl_physarum.py) and [`brain/carl_hdc.py`](file:///d:/ebca/brain/carl_hdc.py).
  * Slime mold plasmodial flux equations adapt tube network conductivity $D$, causing dead ends to decay and funneling candidate generation toward proven global corridors.
  * Cluster successful trajectory maneuvers into 10,000-D hypervector motor synergies for instantaneous recall.
* **Stage 3.7 — Multi-Modal Vision & Full Canonical Reunification:**
  * Ingest offscreen RGB retinal feed from `eye_cam` via `CarlVisionNet`.
  * Active neck pan/tilt gaze scanning.
  * Unify all cognitive organs into the canonical organism ([`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py)) and execute the final 50-episode adversarial acceptance suite.
* **Status:** **LOCKED 🔒**

---

### Step 5: Stage 4 — Autopoietic / Lifelong Memory & Persistence
* **Target Files:** [`brain/carl_stdp.py`](file:///d:/ebca/brain/carl_stdp.py), [`brain/carl_hdc.py`](file:///d:/ebca/brain/carl_hdc.py)
* **Capabilities:**
  * **Online R-STDP Plasticity:** Reward-modulated Spike-Timing-Dependent Plasticity converts recurring Active Inference policies into fast reflex habits without catastrophic forgetting.
  * **Holographic Episodic Memory:** Multi-modal state binding across high-dimensional space ($[P \otimes S \otimes E]$).
  * **GIS-901 State Compounding:** Compounding spatial knowledge and topological graphs across multiple simulated lifespans.
* **Status:** **FUTURE MILESTONE 🔒**

---

### Step 6: Stage 5 — Metacognition ("The Witness")
* **Target File:** [`brain/carl_witness.py`](file:///d:/ebca/brain/carl_witness.py)
* **Capabilities:**
  * **Introspective Failure Analysis:** An introspective metacognitive cortex monitors prediction error surges and candidate veto rates.
  * **Abductive Causal Attribution:** Diagnoses failure causes (distinguishing sensor lag, friction loss, or clearance misjudgment).
  * **Introspective Monologue:** Generates transparent, human-readable failure attribution explanations (the centerpiece for your viva defense presentation).
  * **Permission-Gated Self-Improvement:** Proposes formal parameter updates to the human user with mathematical proof before execution.
* **Status:** **FINAL MATURITY 🔒**

---

## Phase 3: Physical Hardware Prototype Demonstration (Viva Defense)

### Step 7: Build the ₹2,150 Frugal Physical Hardware Prototype
* **Specification File:** [`docs/CARL_STUDENT_FRUGAL_HARDWARE_BOM.md`](file:///d:/ebca/docs/CARL_STUDENT_FRUGAL_HARDWARE_BOM.md)
* **Hardware Architecture:**
  * Microcontroller: ESP32 Dual-Core (Wi-Fi/Bluetooth PNS peripheral bridge).
  * Sensors: Array of VL53L0X / VL53L1X Time-of-Flight distance sensors + MPU6050 6-DoF IMU.
  * Actuators: N20 Micro Metal Gearmotors driven by DRV8833 H-Bridge.
  * Chassis: 3D printed / laser-cut acrylic differential-drive chassis matching digital twin dimensions ($23\text{ cm} \times 27\text{ cm}$).
* **Software Bridge (Sim-to-Real):**
  * Micro-ROS / UDP socket interface streaming unprivileged sensor readings over Wi-Fi to the laptop workstation running CARL's Active Inference brain at 30 Hz.
  * Return stream transmits continuous wheel velocity PWM commands back to the ESP32.
* **Viva Presentation Value:** Proves that the digital twin developed in JNTUH's Mechanical Engineering department is not just a simulation exercise, but a deployed physical robotic architecture.
* **Status:** **READY FOR HARDWARE SOURCING & ASSEMBLY 🔒**

---

## Master Checklist & Progress Tracker

| Milestone | Sub-Step | Deliverable | Status |
|---|---|---|:---:|
| **Phase 1** | **Step 1** | Eliminate Rear Blind Spot (15 rays, $[-168^\circ, +168^\circ]$) | **DONE ✅** |
| **Phase 1** | **Step 2** | Pure Continuous Active Inference & AST Anti-Cheat Pass | **DONE ✅** |
| **Phase 1** | **Step 3** | Run Frozen Stage 3.4 Multi-Environment Certification Battery | **CURRENT ⏳** |
| **Phase 2** | **Step 4** | Stages 3.5 – 3.7 (Friction Adaptation, Physarum, Vision) | **NEXT 🔒** |
| **Phase 2** | **Step 5** | Stage 4 (Lifelong Synaptic Memory via R-STDP & HDC) | **PLANNED 🔒** |
| **Phase 2** | **Step 6** | Stage 5 (Metacognitive "Witness" & Monologue) | **PLANNED 🔒** |
| **Phase 3** | **Step 7** | Physical Frugal Hardware Demonstration (₹2,150 Prototype) | **PLANNED 🔒** |

---

*This document serves as the permanent, immutable engineering record for CARL-DX developmental progression. It must be preserved across conversation compaction and used to guide all subsequent sprints.*
