# Stage 3 Deadline Feasibility Matrix & Risk Assessment

**Audit Target:** Feasibility of Stage 3.5, 3.6, and 3.7 before submission deadline (Next Wednesday)  
**Date:** 2026-09-24  
**Workspace:** `d:\ebca`  
**Time Horizon:** 6 calendar days remaining  
**Compliance Standard:** Fail-Closed Pre-Registered Acceptance  

---

## 1. Test Coverage & Empirical Grounding Matrix

| Stage | Capability | Existing Tests | Current Test Status | Missing Critical Tests | Feasible in < 1 Day? |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **3.5** | **Endocrine Kinetics** | [`tests/test_endocrine.py`](file:///d:/ebca/tests/test_endocrine.py) (211 lines) | **PASS ✅ (Unit only)** | Closed-loop integration with MPPI/Active Inference; behavioral modulation of exploration noise. | **YES (< 4 hrs)** |
| **3.5** | **Friction Drops ($\mu=0.2$) & Torque Loss** | [`tests/test_stage1_suite.py`](file:///d:/ebca/tests/test_stage1_suite.py) (slip ratio observer only) | **PASS ✅ (Observer only)** | Closed-loop torque compensation test; $\mu=0.20$ ice recovery test suite; torque drop injection benchmark. | **YES (approx. 1 day)** |
| **3.5** | **Morphological Adaptation** | None | **NO TESTS ❌** | Any functional unit test or validation suite for `carl_adaptation.py`. | **NO (stub code)** |
| **3.6** | **HDC Motor Synergy Formation** | None (only discrete place-cell binding in [`tests/test_gis_and_memory.py`](file:///d:/ebca/tests/test_gis_and_memory.py)) | **NO TESTS ❌** | Trajectory hypervector encoding; continuous action clustering; synergy recall and candidate seeding test. | **NO (> 3 days)** |
| **3.6** | **Physarum Maze Routing** | [`tests/test_physarum_and_omega.py`](file:///d:/ebca/tests/test_physarum_and_omega.py) (lines 25–45) | **PASS ✅ (10x10 synthetic grid)** | 25x25 real-time latency benchmark; coupling to continuous trajectory sampling; dead-end pruning benchmark. | **POSSIBLY (1–2 days)** |
| **3.7** | **Optical Vision (CarlVisionNet)** | [`brain/verify_vision_predictions.py`](file:///d:/ebca/brain/verify_vision_predictions.py) | **FAIL ❌ (`NameError: BASE_DIR`)** | Real-time offscreen rendering test; bounding box unprojection to raster occupancy; active gaze tracking test. | **NO (> 3 days)** |
| **3.7** | **Active Gaze & Eye Camera Ingestion** | None (AST anti-cheat scan confirms isolation only) | **NO TESTS ❌** | Unprivileged 30 Hz eye camera ingestion; head servo tracking; multi-modal sensor fusion battery. | **NO (> 3 days)** |
| **3.7** | **50-Episode Adversarial Suite** | None for Stage 3.7 | **NO TESTS ❌** | Pre-registered 50-episode frozen benchmark combining vision, Physarum, and adaptation. | **NO (unwritten)** |

---

## 2. Integration Risk Classification

### Stage 3.5: Physical Perturbation & Environmental Adaptation
* **Endocrine Kinetics (`carl_endocrine.py`):** **LOW RISK**
  * *Code Evidence:* The mathematical core in [`brain/carl_endocrine.py`](file:///d:/ebca/brain/carl_endocrine.py) is self-contained with no heavy dependencies beyond `numpy`. It already exposes `get_precision_weight()` and `get_exploration_noise_scale()`. Connecting it to scale candidate perturbation noise in `CarlAutonomousOrganismAgent` is direct and clean.
* **Friction Drops & Slip Recovery:** **MEDIUM RISK**
  * *Code Evidence:* `CarlStage1HAL` already supports `hal.set_friction(mu)`. `CarlAutonomousOrganismAgent` already computes `self.slip_ratio` at line 295. Implementing a closed-loop gain scheduler that scales motor commands upon slip detection is straightforward, but designing a reproducible perturbation benchmark battery requires 1 full day of calibration.
* **Overall Stage 3.5 Risk:** **MEDIUM**

---

### Stage 3.6: Behavioral Synergy Formation & Physarum Routing
* **Physarum Routing (`carl_physarum.py`):** **HIGH RISK**
  * *Code Evidence:* [`brain/carl_physarum.py`](file:///d:/ebca/brain/carl_physarum.py) requires solving an $N=625$ sparse Poisson system (`scipy.sparse.linalg.spsolve`). In initial timing tests, `spsolve` consumes 5–15 ms per call. Adding this into the 30 Hz control loop threatens the **Gate 4 latency budget ($\le 20.0\text{ ms}$ mean / $\le 45.0\text{ ms}$ p95)**. Furthermore, bridging a discrete 25x25 pressure field into continuous action rollouts requires non-trivial algorithmic glue.
* **HDC Motor Synergy Formation (`carl_hdc.py`):** **CRITICAL RISK**
  * *Code Evidence:* [`brain/carl_hdc.py`](file:///d:/ebca/brain/carl_hdc.py) contains vector algebra for *discrete places* (`place_idx`), but contains **zero code for trajectory clustering, motor primitive compression, or continuous action recall**. Building a clustering pipeline that transforms continuous candidate trajectories into reusable motor synergies from scratch cannot be completed and certified in 6 days.
* **Overall Stage 3.6 Risk:** **HIGH / CRITICAL**

---

### Stage 3.7: Multi-Modal Perception & Final Acceptance
* **CarlVisionNet & Eye Camera Integration:** **CRITICAL RISK**
  * *Code Evidence:* `CarlStage1HAL` does not currently instantiate an offscreen `mujoco.Renderer` in its 30 Hz control loop. MuJoCo offscreen rendering at $160 \times 120$ takes 20–35 ms on CPU/OpenGL per frame. Running `CarlVisionNet` CNN forward passes on top of physics step and rendering would immediately blow through the 20 ms cognitive cycle budget. Furthermore, `CarlVisionNet` was trained on synthetic colored primitives, not the textured turning bay / T-junction mazes.
* **Active Head Gaze & 50-Episode Acceptance Suite:** **CRITICAL RISK**
  * *Code Evidence:* Gaze pan/tilt servoing is unwritten. A 50-episode frozen adversarial acceptance battery with multi-modal perception does not exist.
* **Overall Stage 3.7 Risk:** **CRITICAL**

---

## 3. Deadline Feasibility Evaluation (Next Wednesday)

| Milestone | Realistic to Integrate & Demonstrate Before Wednesday? | Feasibility Verdict | Key Blocking Reason |
| :--- | :---: | :---: | :--- |
| **Stage 3.5** (Perturbation & Endocrine) | **YES** | **FEASIBLE ✅** | Endocrine kinetics and slip observer already exist; can be integrated into the organism in 1–2 days and tested on friction drop ($\mu=0.2$) scenarios. |
| **Stage 3.6** (Physarum & HDC Synergies) | **POSSIBLY (Demonstration Only)** | **PARTIAL / AT RISK ⚠️** | Physarum routing can be demonstrated as an allocentric planning visualizer or heuristic prior; true HDC motor synergy clustering is unwritten and cannot be certified. |
| **Stage 3.7** (Multi-Modal Vision & Full Acceptance) | **NO** | **INFEASIBLE ❌** | Offscreen camera rendering latency violates the 20 ms real-time budget; CarlVisionNet lacks grounded maze training; multi-modal occupancy fusion cannot be engineered and certified in 6 days without compromising integrity. |

> [!IMPORTANT]
> **Scientific Integrity Rule:** Under CARL-DX fail-closed governance, **"Demonstration" is not "Certification"**. We can demonstrate Stage 3.5 adaptation and a standalone Stage 3.6 Physarum visualizer, but we CANNOT claim formal Stage 3.6 or Stage 3.7 certification by Wednesday.

---

## 4. Minimum Viable Stage-3 Submission Scope (MV-S3)

To ensure the project submitted next Wednesday is scientifically unassailable, robust, and 100% bug-free:

### 1. MUST FINISH (Core Submission Guarantee — Days 1–3)
1. **Canonical Re-Unification Step 3:** Complete [`carl_simulation.py`](file:///d:/ebca/carl_simulation.py) CLI unification with `--deliberation {mppi, active_inference}`.
2. **Stage 3.4 Physical Clearance Resolution:** Fix rotational swept-cone clearance / tick budget in Environment 2 so the autonomous multi-point turning behavior reaches escape certification.
3. **Stage 3.5 Endocrine & Friction Adaptation:** Wire `EndocrineSystem` (stress kinetics NE/Cortisol modulating exploration noise) and closed-loop slip compensation ($\mu=0.20$ ice floor recovery) into `CarlAutonomousOrganismAgent`.

### 2. SHOULD FINISH (High-Impact Secondary Goal — Days 3–4)
1. **Stage 3.6 Physarum Prior Integration:** Wire `PhysarumMaze` as an offline/background heuristic goal prior to bias global exploration toward open channels.
2. **Diagnostic Video Generation:** Render clean 30 fps tracking videos of CARL adapting to friction drops and performing autonomous dead-end reversals.

### 3. DEMONSTRATE ONLY (Present as Architectural Prototype — Day 5)
1. **HDC Vector Algebra:** Demonstrate 10,000-D hypervector binding and associative recall in a standalone interactive notebook/script.
2. **Eye Camera Retina Feed:** Demonstrate an offscreen visual snapshot from `eye_cam` rendered via `carl_visual_telemetry_pipeline.py`.

### 4. FUTURE WORK (Document Transparently in Defense Deck & Blueprint)
1. **Full Online HDC Motor Synergy Clustering:** Formally defer continuous trajectory clustering to post-submission developmental milestones.
2. **Multi-Modal Active Head Gaze VisionNet Ingestion (Stage 3.7):** Explicitly document as the next milestone, citing the 20 ms real-time compute budget and offscreen rendering latency constraints.
3. **Stage 4 (Autopoietic Lifelong Synaptic Memory) & Stage 5 (Metacognition):** Preserved in the formal Master Architecture roadmap.
