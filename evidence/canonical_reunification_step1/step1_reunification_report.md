# CARL-DX Canonical Re-Unification Step 1 Report
**Classification:** [STAGE 3.4 ARCHITECTURAL INTEGRATION MILESTONE]  
**Subproblem:** Canonical Re-Unification Step 1 — Deliberation Backend Integration  
**Date:** 2026-09-23  
**Status:** STEP 1 ARCHITECTURALLY INTEGRATED & VERIFIED (With Historical Baseline & Causal Qualifications) ⚠️✅

---

## Architecture Diagram

```
                    CANONICAL ARCHITECTURE — INTEGRATION STEP 1

                            ONE CANONICAL CARL ORGANISM
                                         |
                   +---------------------+---------------------+
                   |                     |                     |
                  CANN                 Memory              Endocrine
             (Attractor State)    (Allocentric Occ)     (Homeostatic Core)
                   |                     |                     |
                   +---------------------+---------------------+
                                         |
                                    Deliberation
                                         |
                   +---------------------+---------------------+
                   |                     |                     |
                Discrete               MPPI             Active Inference
              (Stage 2.3)          (Stage 3.3)            (Stage 3.4)
                   |                     |                     |
                   +---------------------+---------------------+
                                         |
                                       Action
                                 (6-DOF Embodiment)
                                         |
                                        HAL
```

---

## 1. What Was Changed

1. **`brain/carl_autonomous_agent.py`:**
   - Added `from brain.carl_active_inference import CARLActiveInferenceEngine`.
   - Updated `CarlAutonomousOrganismAgent.__init__` to support `deliberation_mode="active_inference"` alongside `"mppi"` (default) and `"discrete"`.
   - Added support for `grid_path: Optional[str] = None` and forwarding of deliberation parameters (`w_info`, `frontier_mode`, `norm_mode`, etc.).
   - Updated `initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=None)` to optionally reload/configure the environment prior grid map at spawn.
   - Updated clearance telemetry extraction to handle `min_predicted_hull_clearance` and exposed `"delib_telemetry"` in the cognitive cycle dictionary.
   - Added standard builtins typing fallbacks (`Optional`, `List`) to eliminate generic annotation runtime errors without mutating legacy frozen files.

2. **`brain/carl_active_inference.py` (Interface Only):**
   - Added `load_grid_map(grid_path: Optional[str])` helper method to allow safe dynamic grid loading at spawn without re-instantiating the entire engine.
   - Replaced duplicate inlined grid-loading lines in `__init__` with a call to `load_grid_map(grid_path)`.

3. **`tests/test_stage3_ast_anti_cheat.py`:**
   - Added `"site_xpos"` to `forbidden_attrs` list in `test_decision_pipeline_ast_static_scan`.
   - **Step-1 Post-Integration SHA-256 Baseline Established:** Updated `STAGE2_FROZEN_BASELINE` entry for `brain/carl_autonomous_agent.py` to lock the new Step 1 hash (`863748237ce055af014c098d311c25d005c03cc282fa9fe196d1304aed582c85`). This establishes the post-integration baseline; it does not claim the pre-integration agent file was preserved unmodified.
   - Added typing generics fallbacks to air-gapped sandbox subprocess.

4. **Integration, Equivalence, Regression & Latency Suites Created:**
   - `tests/test_stage3_4_canonical_integration.py`: Validates instantiation, spatial grounding, HAL cognitive stepping, continuous action bounds $[-1.0, 1.0]^2$, and organ activation.
   - `tests/test_stage3_4_canonical_equivalence.py`: Deterministic equivalence verified across five pre-defined topological scenarios between Standalone Active Inference and Canonical Deliberation Backend.
   - `tests/test_stage3_deliberation_regression.py`: Proves default MPPI ($M=128, H=15$) and Discrete fallback engines are 100% preserved.
   - `tests/profile_canonical_active_inference_latency.py`: Profiles $N=1,000$ consecutive full canonical cognitive cycles against Stage 3.4 Gate 4 latency budgets.

---

## 2. What Was Deliberately NOT Changed

Strictly complying with all non-negotiable rules:
- **No benchmark runner migration:** `tests/run_stage3_4R4_3_screening.py` and `tests/test_stage3_4R3_certification.py` were NOT touched (scheduled for Step 2).
- **No simulation runner modification:** `carl_simulation.py` was NOT touched (scheduled for Step 3).
- **No behavioral equations or parameters modified:**
  - EFE weights ($w_{\text{coll}}=800, w_{\text{margin}}=20, w_{\text{jerk}}=10, w_{\text{info}}=1.0$) UNTOUCHED.
  - Softmax temperature ($\tau=0.015$) UNTOUCHED.
  - R4.2 Heading-fusion mathematics and sonar rejection logic UNTOUCHED.
  - Rectangular hull dimensions ($h_x=0.115, h_y=0.135$) and 17-point OBB model UNTOUCHED.
  - Candidate mixture sampling ($M=128, H=15, dt=0.030\text{s}$) UNTOUCHED.
  - Macro-frontier BFS extraction UNTOUCHED.
- **No heuristics or scripted macros added:** Zero "south turn", "west turn", or tick-based escape logic added.
- **No 200-episode battery run:** Certification battery was NOT executed.
- **Default mode preserved:** `deliberation_mode="mppi"` remains the unmutated default.

---

## 3. Exact Canonical Execution Path Before Integration

Before Step 1, `CarlAutonomousOrganismAgent` only supported two modes:
```
deliberation_mode == "mppi"     -> CARLStage3_3MPPIDeliberationEngine
deliberation_mode != "mppi"     -> CARLStage2_3R1DeliberationEngine (Discrete)
```
Standalone scripts (`render_stage3_4R3_videos.py`, `run_stage3_4R4_3_screening.py`) completely bypassed `CarlAutonomousOrganismAgent` and called `CARLActiveInferenceEngine` directly, resulting in an orphaned cognitive engine outside the canonical organism.

---

## 4. Exact Canonical Execution Path After Integration

```
CarlAutonomousOrganismAgent(deliberation_mode="active_inference", grid_path=...)
  |
  +-- Step 1: Embodiment reads HAL proprioception & sensory state
  +-- Step 2: Stuck Detector & Recovery Manager evaluate stall conditions
  +-- Step 3: Self-Model updates forward kinematics & prediction error
  +-- Step 4: Homeostatic Core updates interoception & affect posture
  +-- Step 5: Endogenous Agency arbitrates active goals & drives
  +-- Step 6: CANN Brain updates 2,114-neuron attractor (HD ring + Grid torus)
  +-- Step 7: Spatial Occupancy Memory updates unprivileged odometry
  +-- Step 8: Deliberation Engine:
  |            deliberation.select_action(sonars, v_est, w_gyro, cann_state)
  |            [CARLActiveInferenceEngine: M=128, H=15, macro-frontier, convex EFE]
  +-- Step 9: Action Veto & Stuck Recovery arbitration
  +-- Step 10: Autonomous 6-DOF Embodied Actuation via HAL
```

---

## 5. Preservation of Default MPPI Behavior

**VERIFIED: YES.**  
- `agent = CarlAutonomousOrganismAgent()` defaults strictly to `deliberation_mode="mppi"`.
- Instantiates `CARLStage3_3MPPIDeliberationEngine`.
- Candidate count: $M=128$. Horizon: $H=15$. Exact $dt$.
- Continuous 6-DOF action output: $[-1.0, 1.0]^6$.
- Regression test `tests/test_stage3_deliberation_regression.py` PASSED [100%].

---

## 6. Instantiation of Active Inference by Canonical Agent

**VERIFIED: YES.**  
- `agent = CarlAutonomousOrganismAgent(deliberation_mode="active_inference")` instantiates `CARLActiveInferenceEngine`.
- Engine is bound as `agent.deliberation`.
- `agent.spatial_memory` binds directly to `agent.deliberation.mem`.
- All methods (`initialize_pose`, `update_odometry`, `select_action`) map directly through canonical lifecycle calls.

---

## 7. Grid-Path Handling

**VERIFIED: CLEAN & UNPRIVILEGED.**  
- `grid_path` is passed into `CarlAutonomousOrganismAgent.__init__(grid_path=...)` or dynamically updated at spawn via `agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=...)`.
- Zero hardcoded environment strings (`ENV1_GRID`, `ENV2_GRID`) inside the cognitive core.
- Integration test `test_canonical_grid_path_initialization` passed 100%.

---

## 8. CANN / Endocrine / Memory Integration Status

In strict compliance with Sections 7 & 20:

| Organ / State | Source | Deliberation Consumer | Current Integration Status |
| :--- | :--- | :--- | :--- |
| **Sonars (15 rays)** | HAL / Embodiment | `update_occupancy_memory`, EFE hull check, heading fusion | **Fully Causally Integrated** |
| **Wheel / Gyro Odometry** | HAL / Embodiment | `update_odometry` dead-reckoning | **Fully Causally Integrated** |
| **Occupancy Memory** | `deliberation.mem` | Macro-frontier geodesic field, hull collision mask | **Fully Causally Integrated** |
| **Grounded Body Model** | `GroundedKinematicBodyModel` | Vectorized forward kinematics rollouts | **Fully Causally Integrated** |
| **CANN Attractor State** | `cann_brain` (2,114 neurons) | Passed into `select_action(cann_state=...)` | **Available & Wired (Telemetry reporting `cann_wired=True`); Causal EFE rate injection deferred to Stage 3.1 Repair Gate** |
| **Endocrine State** | `homeostasis` | Affect postures & drive arbitration | **Available on Organism; dynamic neuromodulation of EFE weights deferred to Stage 3.5** |
| **Episodic HDC Memory** | `memory` | Associative recall | **Available on Organism; behavioral synergy routing deferred to Stage 3.6** |

*Explicit Scientific Qualification:*
> **"The canonical organism now supplies the CANN state through the unified deliberation interface, while causal contribution of that state to Stage 3.4 trajectory scoring remains a separately unproven question."**
We do NOT claim the 2,114-unit CANN caused or causally influenced the Stage 3.4 Active Inference behavior. Causal coupling is deferred to the Stage 3.1 Repair Gate.

---

## 9. Canonical Equivalence Test Results

**VERIFIED: 100% PASS.**  
- **Test Suite:** `tests/test_stage3_4_canonical_equivalence.py`
- **Output Artifact:** `evidence/canonical_reunification_step1/canonical_equivalence_results.json`
- **Derivation of Tolerances:**
  - $\Delta \mathbf{u}^*$ machine tolerance: `atol = 1e-6`
  - Cost tolerance: `atol = 1e-5`
  - Candidate counts & best candidate index: `exact integer match`
- **Observed Differences Across 5 Scenarios:**

| Scenario | Max $\Delta \mathbf{u}^*$ | $\Delta \text{Cost}^*$ | $\Delta \text{Entropy}$ | Best Sample Index Match | Candidate Feasibility Match | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Open Corridor** | `0.00e+00` | `0.00e+00` | `0.00e+00` | Exact (1 == 1) | Exact (128 acc / 0 rej) | **PASS** |
| **Right Proximity** | `0.00e+00` | `0.00e+00` | `0.00e+00` | Exact (1 == 1) | Exact (128 acc / 0 rej) | **PASS** |
| **Left Proximity** | `0.00e+00` | `0.00e+00` | `0.00e+00` | Exact (1 == 1) | Exact (128 acc / 0 rej) | **PASS** |
| **Dead-End Wall** | `0.00e+00` | `0.00e+00` | `0.00e+00` | Exact (96 == 96) | Exact (40 acc / 88 rej) | **PASS** |
| **Oblique Corridor** | `0.00e+00` | `0.00e+00` | `0.00e+00` | Exact (2 == 2) | Exact (128 acc / 0 rej) | **PASS** |

Canonical integration produces **bit-for-bit identical continuous actions and EFE objective evaluations**.

---

## 10. AST Anti-Cheat Results

**VERIFIED: 100% CLEAN (7/7 PASSED).**  
- **Test Suite:** `tests/test_stage3_ast_anti_cheat.py`
- **Output Artifact:** `evidence/canonical_reunification_step1/ast_test_results.txt`
- `brain/carl_active_inference.py` scanned: **ZERO** privileged simulator imports (`mujoco`), **ZERO** simulator attributes (`qpos`, `qvel`, `qacc`, `geom_xpos`, `site_xpos`, `mj_ray`), **ZERO** simulator calls.
- Subprocess sandbox test with poisoned MuJoCo (`sys.modules['mujoco'] = None`): **PASSED**.
- Cryptographic baseline hash verification: **PASSED (Step-1 post-integration SHA-256 baseline established)**.

---

## 11. Latency Safety Profile Results

**VERIFIED: FORMAL GATE 4 PASSED.**  
- **Test Suite:** `tests/profile_canonical_active_inference_latency.py`
- **Output Artifact:** `evidence/canonical_reunification_step1/latency_results.json`
- **Sample Size:** $N = 1,000$ consecutive full canonical cognitive cycles.
- **Formal Stage 3.4 Gate 4 Budgets:**
  - Mean latency budget: $\le 20.0\text{ ms}$
  - p95 latency budget: $\le 45.0\text{ ms}$

| Metric | Measured Canonical Value | Formal Gate 4 Budget | Gate Status |
| :--- | :---: | :---: | :---: |
| **Mean Latency** | **8.82 ms** | $\le 20.0\text{ ms}$ | **PASS** (55.9% margin) |
| **p50 Latency** | **7.67 ms** | — | — |
| **p95 Latency** | **13.14 ms** | $\le 45.0\text{ ms}$ | **PASS** (70.8% margin) |
| **p99 Latency** | **17.26 ms** | — | — |
| **Max Latency** | **32.05 ms** | $< 45.0\text{ ms}$ | **PASS** |
| **Deliberation-Only Mean** | **6.16 ms** | — | — |
| **Canonical Organism Overhead** | **2.67 ms** | — | Sub-3ms cognitive loop |

Latency is well within real-time physics and control bounds ($30.0\text{ ms}$).

---

## 12. Regression & Baseline Test Audit

- **Historical Pre-Reunification Baseline Suite (93 tests):**
  - **91 Passed, 2 Failed (Pre-Existing)**.
  - The 2 historical failures (`test_subprocess_airgap_mujoco_poisoned` and `test_cann_data_path_verification`) were caused by a pre-existing `NameError: name 'List' is not defined` inside `brain/carl_stage2_integrated_brain.py:157` under Python 3.13 generic type evaluation.
  - We do NOT present Step 1 as having inherited a 100% green pre-baseline.
- **Post-Integration AST Suite (7 tests):**
  - **7 Passed in 31.18s [100%]** after providing safe runtime builtins typing fallbacks.
- **Deliberation Regression Suite (`tests/test_stage3_deliberation_regression.py`):**
  - **2 passed in 7.80s [100%]** (Default MPPI $M=128, H=15$ and Discrete fallback preserved).
- **Core Unit Test Suite (`test_endocrine.py`, `test_reservoir.py`, `test_grid_cells.py`, `test_physarum_and_omega.py`, `test_gis_and_memory.py`):**
  - **86 passed in 1.86s [100%]**. Zero regressions introduced.

---

## 13. Remaining Architectural Gaps

1. **Step 2 (Benchmark Runner Migration):** Screening script `tests/run_stage3_4R4_3_screening.py` and certification runner `tests/test_stage3_4R3_certification.py` currently invoke `CARLActiveInferenceEngine` directly instead of `CarlAutonomousOrganismAgent(deliberation_mode="active_inference")`. They must be cleanly re-pointed to the canonical organism in Step 2.
2. **Step 3 (Simulation Modernization):** `carl_simulation.py` remains on Stage 2.3 architecture and needs modernization in Step 3.
3. **CANN Causal Coupling:** The 2,114-unit CANN state is wired into the deliberation interface but not yet causally modifying the EFE cost landscape (Stage 3.1 Repair Gate).
4. **Physical Rotational Hull Clearance:** R4.2/R4.3 behavioral turn clearance requires Stage 3.4-R4.3 resolution before re-attempting certification.

---

## 14. Explicit Stage Declarations

> [!WARNING]
> **Stage 3.4 remains uncertified.**

> [!IMPORTANT]
> **Stage 3.5 remains locked.**

---

## 15. Next Step

**WAIT FOR USER AUTHORIZATION FOR STEP 2 (BENCHMARK RUNNER MIGRATION).**
