# CARL-DX: Master Execution Plan & Developmental Progression (Updated)
**Document ID:** `CARL-PLAN-2026-STAGE5-POA-V2`  
**Candidate:** Manas Sadashiv (Roll: 22011P0310)  
**Affiliation:** JNTUH UCESTH, Department of Mechanical Engineering (IDP AMS)  
**Title:** DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS  
**Date Updated:** October 18, 2026  
**Hardware Baseline:** Lenovo IdeaPad Gaming 3 (Intel Core i5-13450HX 10C/16T, 16GB DDR5, RTX 3050 6GB Laptop, 512GB NVMe)

---

## Executive Overview: The Canonical Developmental Roadmap

This document serves as the single source of truth for CARL-DX's developmental progression, preserving our agreed Plan of Action (POA) across conversation compactions, defense preparation, and hardware execution.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Sensorimotor Grounding & Body Babbling                       [COMPLETED ✅]   │
│   └── 6-channel motor babbling, kinematic slip, traction estimation                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STAGE 2: Generative World & Self Modeling                             [COMPLETED ✅]   │
│   └── Grounded spatial memory, 2,114-unit CANN attractor, prospective deliberation   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STAGE 3: Continuous Action Synthesis & Behavioral Discovery           [COMPLETED ✅]   │
│   ├── 3.0: Pre-flight integrity & AST anti-cheat quarantine lock                       │
│   ├── 3.1 & 3.2: CANN causal coupling & spatial memory non-LOS necessity              │
│   ├── 3.3 & 3.4: Continuous MPPI under Active Inference (Epistemic + Pragmatic)        │
│   ├── 3.4.2: Smooth action synthesis, suspension stabilization & jerk penalty         │
│   ├── 3.5: Physical perturbation adaptation (friction drop μ=0.20, torque drag)       │
│   ├── 3.6: Physarum Hagen-Poiseuille routing & HDC motor synergy clustering           │
│   └── 3.7: Multi-modal vision (CarlVisionNet), head gaze, 50-episode frozen acceptance│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STAGE 4: Autopoietic / Lifelong Memory & Persistence                  [COMPLETED ✅]   │
│   ├── 4.1: Online Reward-Modulated STDP plasticity & Turrigiano homeostatic bounds    │
│   ├── 4.2: Holographic Vector Symbolic Memory Architecture (2,048-D FHRR episodic)    │
│   ├── 4.3: Memory consolidation, NREM SWR offline reverse replay & synaptic scaling   │
│   └── 4.4: Autopoietic lifelong persistence & WAL/GIS-901 state compounding (SHA-256) │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STAGE 5: Metacognition & Permission-Gated Self-Modification           [CURRENT ⏳]     │
│   ├── 5.1: "The Witness" introspective telemetry monitoring engine                     │
│   ├── 5.2: Abductive causal failure attribution via HDC trace lookup                   │
│   ├── 5.3: Permission-gated hyperparameter & habit plasticity self-adaptation         │
│   └── 5.4: Adversarial failure recovery certification suite (30–50 episodes)          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ M.TECH DISSERTATION & DEFENSE PACKAGE                                 [PRE-PLANNED 🔒] │
│   ├── Complete thesis chapter writeup, evidence dashboards (awesome_vis_*), p-values   │
│   └── Lightweight 30-fps headless video demo reel for examination committee           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ POST-STAGE 5 RESEARCH: 3D CLUTTER & MORPHOLOGICAL LITMUS TEST         [PLANNED 🔒]     │
│   ├── Phase A: Complex 3D cluttered / non-planar MuJoCo environment (post-Stage 5)    │
│   ├── Phase B: Foreign Embodiment Transfer (inject brain into unseen body + timer test)│
│   └── Phase C: Sim-to-Real Physical Hardware Prototype (₹2,150 BOM on ESP32 + HAL)     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Plan of Action (POA): Step-by-Step Execution

### Step 1: Stage 4 Baseline Freeze & Quarantine Lock
* **Status:** Complete verification.
* Ensure all Stage 4 test artifacts and evidence dashboards (`awesome_vis_*`, connectomes, SWR cascades) are archived.
* Confirm 100% clean AST anti-cheat quarantine across all 14 decision-pipeline files (zero `qpos`, `geom_xpos`, or `mj_ray` coordinate leaks).
* Commit and tag repository: `v4.4-certified`.

---

### Step 2: Stage 5 — Metacognition & Permission-Gated Self-Modification
* **Target File:** [`brain/carl_witness.py`](file:///d:/ebca/brain/carl_witness.py) (integrated into [`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py))
* **Core Principle:** Isolated, clean developmental environment to prevent physics engine artifacts from confounding cognitive failure diagnosis.
* **Architecture:**
  1. **Sub-Phase 5.1 ("The Witness" Telemetry Monitoring):**
     * Introspectively monitors internal signals: prediction error divergence, Free Energy variance, motor stall, CANN drift, endocrine stress hormones (Noradrenaline/Cortisol).
     * Strictly bounded to unprivileged HAL telemetry (zero simulator cheats).
  2. **Sub-Phase 5.2 (Abductive Causal Attribution):**
     * When uncertainty spikes or progress stalls, query 2,048-D HDC episodic memory.
     * Differentiate: Sensor occlusion vs. wheel slip/traction loss vs. topological dead end vs. actuator saturation.
     * Formulate structured human-readable introspective diagnoses (the star deliverable for the viva defense).
  3. **Sub-Phase 5.3 (Permission-Gated Self-Modification):**
     * Synthesize bounded parameter modulations: MPPI exploration temperature, obstacle repulsion weight, R-STDP habit plasticity rates.
     * Enforce mathematical safety invariants (clamped bounds; no runaway feedback loops).
  4. **Sub-Phase 5.4 (Stage 5 Certification Battery):**
     * 30–50 randomized adversarial traps (cul-de-sacs with sudden friction drops, blind occlusions, symmetric dead ends).
     * Pass criteria: Significant reduction in time-to-recovery vs. ablation ($p < 0.001$), 0 collisions, 100% clean AST quarantine.

---

### Step 3: M.Tech Dissertation Submission & Defense Asset Packaging
* **Target:** JNTUH UCESTH Mechanical Engineering (IDP AMS) Defense Committee.
* **Framing Strategy:**
  * Emphasize **first-principles neuromorphic engineering** (37,500+ lines of native mathematics, not canned black-box ROS/YOLO).
  * Highlight **edge-compute feasibility**: Complete 10-organ cognitive cycle executes in $< 25\text{ ms}$ on consumer hardware.
  * Showcase **empirical rigor**: Pre-registered ablation batteries, McNemar / Wilcoxon tests with $p < 10^{-12}$, and AST anti-cheat quarantine.
* **Assets:**
  * Compile thesis chapters from generated markdown evidence files.
  * Presentation slides with embedded high-resolution graphics (`awesome_vis_4_*`).
  * Headless-rendered 30-fps video runs demonstrating autonomous navigation, slip recovery, and sleep consolidation.

---

### Step 4: Post-Stage 5 Research & Morphological Transfer Test
* **Rationale for Timing:** Introducing complex 3D environments *only after* Stage 5 is fully certified prevents confounding cognitive failure attribution with mesh collision bugs.

#### Phase A: Heavy 3D Cluttered Environment
* Introduce 3D non-planar terrain (slopes, ramps, rough ground) and dynamic clutter obstacles in MuJoCo.
* Validate that CARL's virtual suspension, pitch stabilization, and Active Inference MPPI scale seamlessly to 3D dynamics.

#### Phase B: The Foreign Embodiment Transfer Experiment (The Litmus Test)
* **The Hypothesis:** If CARL-DX is a true developmental cognitive architecture and not an overfitted maze solver, the cognitive core should autonomously adapt to a foreign robot body without manual code changes.
* **Protocol:**
  1. Inject checkpointed brain into an unseen morphology (e.g., 4-wheel skid steer, asymmetric wheel diameters, or altered center-of-mass).
  2. Start the clock ($T$).
  3. CARL initiates Stage 1 body babbling to re-discover motor-sensory kinematics.
  4. Measure time-to-adaptation, stability recovery, and maze navigation success vs. a tabula rasa baseline.
* **Academic Significance:** Proves true morphological adaptability; publishable in international developmental robotics conferences (e.g., IEEE ICDL / ALIFE).

#### Phase C: Sim-to-Real Physical Hardware Prototype
* **Specification File:** [`docs/CARL_STUDENT_FRUGAL_HARDWARE_BOM.md`](file:///d:/ebca/docs/CARL_STUDENT_FRUGAL_HARDWARE_BOM.md)
* **Budget:** ₹2,150 frugal bill of materials (ESP32 dual-core, VL53L0X ToF array, MPU6050 IMU, DRV8833, N20 metal gearmotors).
* **Bridge:** UDP/Wi-Fi unprivileged HAL bridge streaming real sensor data to laptop workstation and returning PWM wheel commands at 30 Hz.

---

## Computational Invariants & Laptop Health Protocol

* **Machine:** Lenovo IdeaPad Gaming 3 (i5-13450HX, 16GB RAM, RTX 3050 6GB Laptop).
* **Headless Simulation Mandate:** All benchmark certification runs and training cycles must run in headless mode (`render=False`). MuJoCo math executes in pure C/Python at $10\times$–$20\times$ real-time speed.
* **Thread Throttling:** Limit concurrent CPU worker threads to 8–10 out of the 16 available threads. This guarantees your laptop never freezes, thermals stay cool, and daily workflow/browser remain completely responsive.
* **Memory Ceiling:** Memory footprint for the entire 2,114-unit network, HDC hypervectors, and MPPI rollout buffer is strictly clamped to $< 1.5\text{ GB}$ RAM.

---

*This document is the official execution charter for Stage 5 through final viva defense and physical embodiment.*
