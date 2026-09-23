# CARL-DX STAGE 3.0 — PRE-FLIGHT IMPLEMENTATION PLAN
**Version:** 1.0 (Master Implementation Directive)  
**Date:** September 12, 2026  
**Status:** **STAGE 3.0 COMPLETED & CERTIFIED ✅ | AWAITING STAGE 3.1 APPROVAL ⏳**  
**Target Repository:** `d:/ebca`  

---

## 1. Overview & Objective

Before opening Stage 3.1 (CANN Causal Coupling) or implementing Stage 3.3 (Continuous MPPI), Stage 3.0 must establish an impenetrable architectural and forensic baseline.

This plan details the four mandatory pre-flight integrity locks:
* **3.0-A:** Privileged State Audit & Code Hygiene (AST scan + runtime validation + leak purge).
* **3.0-B:** CANN Participation Audit & Data Path Tracing.
* **3.0-C:** Spatial Memory Participation Audit & Data Path Tracing.
* **3.0-D:** Organism Unity & Single-Controller Quarantine Check.

---

## 2. Work Breakdown Structure

### Phase 3.0-A: Privileged State Audit & Code Hygiene Purge

#### 1. Code Hygiene Remediation
* **Target:** [`brain/carl_embodied_organism.py:238-255`](file:///d:/ebca/brain/carl_embodied_organism.py#L238-L255).
* **Defect:** `food_pos = data.geom_xpos[food_geom.id][:2]` reads simulator ground-truth coordinates.
* **Remediation Action:**
  1. Remove simulator `data.geom_xpos` lookup completely.
  2. Implement an unprivileged exteroceptive optical cone check using the front sonar cluster (`raw_s[6:9]`) or pass external sensory food alerts through the anonymous sensory bus.
  3. Replace `data.qpos[qbase_adr + 2]` with calibrated chassis rest height `0.05m`.

#### 2. AST Static Decision-Pipeline Isolation Verification
* **Target:** Develop and execute `tests/test_stage3_ast_anti_cheat.py`.
* **Verification Scope:** Scan all active cognitive and decision modules (`carl_autonomous_agent.py`, `carl_stage2_3_r1_deliberation.py`, `carl_stage2_2_r2_occupancy_memory.py`, `carl_stage2_integrated_brain.py`, `carl_stage2_hd_ring.py`, `carl_stage2_grid_torus.py`).
* **Boundary Principle:** Hardware simulation in `carl_stage1_hal.py` and arena environment fixtures in `test_*.py` legitimately interface with MuJoCo C-APIs; the scanner verifies that **zero privileged simulator state bleeds into the decision-making loop**.
* **Forbidden AST Patterns inside Decision Pipeline:**
  * Any access to `data.qpos`, `data.qvel`, `data.qacc`, or `data.geom_xpos`.
  * Any call to `mujoco.mj_ray` or `mujoco.mj_step`.
  * Any import of `mujoco` inside planning or deliberation classes.
* **Passing Gate:** 100% clean AST parse across all active cognitive decision-making nodes.

---

### Phase 3.0-B: CANN Participation Audit & Causal Interventions

#### 1. Current State Identification
* **Code Reference:** [`brain/carl_autonomous_agent.py:265-273`](file:///d:/ebca/brain/carl_autonomous_agent.py#L265-L273).
* **Finding:** `brain_res = self.cann_brain.update_brain(...)` runs every tick, but `brain_res` is passed only to cycle telemetry (`telemetry["attractor_state"]`). It is NOT passed into `self.deliberation.select_action(...)`.
* **Diagnosis:** The CANN is **architecturally present** but **causally disconnected** from action selection.

#### 2. Pre-Flight Interface Wiring for Stage 3.1
* Add an explicit `cann_state` parameter to `select_action()`:
  ```python
  def select_action(self, curr_sensors, curr_v, curr_w, cann_state=None):
  ```
* Define the 4 pre-flight test conditions:
  1. `INTACT`: Standard uncorrupted 2,114-unit attractor state.
  2. `FROZEN`: Attractor firing rates frozen at tick 0 values.
  3. `ZEROED`: Attractor firing rates zeroed out.
  4. `SHUFFLED`: Attractor firing rates randomly permuted across unit indices.

---

### Phase 3.0-C: Spatial Memory Participation Audit

#### 1. Current State Identification
* **Code Reference:** [`brain/carl_stage2_3_r1_deliberation.py:380-406`](file:///d:/ebca/brain/carl_stage2_3_r1_deliberation.py#L380-L406).
* **Finding:** The static occupancy grid (`self.grid_ch0`) is queried to compute `grid_bias_scores`, which modifies candidate branch utility by `+ spatial_bias`.
* **Diagnosis:** Spatial memory is **computationally and mathematically active** in the utility calculation, but provides no statistical advantage in 60-tick line-of-sight obstacle mazes.

#### 2. Pre-Flight Protocol for Stage 3.2
* Create dedicated non-line-of-sight test layouts where sonar alone is topologically insufficient (e.g., blind hairpin corners, deep cul-de-sacs, and symmetric corridors).
* Standardize the 4 memory control conditions:
  1. `INTACT_MEMORY`: True allocentric occupancy grid.
  2. `ERASED_MEMORY` (Amnesic): Zero-filled occupancy grid.
  3. `SCRAMBLED_MEMORY`: Spatially permuted grid cells.
  4. `CROSS_EPISODE_MISMATCH`: Grid loaded from a different maze geometry.

---

### Phase 3.0-D: Organism Unity Check

#### 1. Single Controller Enforcement
* Formally verify that no secondary "shadow" controllers or evaluation-only shortcuts are called in any Stage 3 benchmark.
* Audit test runners to ensure that `agent = CarlAutonomousOrganismAgent()` is the sole instantiated decision maker.

---

## 3. Pre-Flight Checklist & Gate Verification Criteria

| Gate ID | Check Item | Verification Command | Mandatory Passing Criteria |
| :--- | :--- | :--- | :--- |
| **GATE-3.0-A1** | Code Hygiene Purge | Code inspection of `carl_embodied_organism.py` | Zero instances of `data.geom_xpos` |
| **GATE-3.0-A2** | Static AST Isolation | `python tests/test_stage3_ast_anti_cheat.py` | 100% Clean (Zero privileged reads) |
| **GATE-3.0-B1** | CANN Interface Contract | Inspection of `carl_autonomous_agent.py` | `brain_res` wired into trajectory evaluation |
| **GATE-3.0-C1** | Spatial Memory Interface | Verification of memory query tensor | Occupancy queried & logged per candidate |
| **GATE-3.0-D1** | Single Organism Unity | Import graph scan of test runners | 100% execution through `CarlAutonomousOrganismAgent` |

---

## 4. Required Stop Point

Upon completing tasks 3.0-A through 3.0-D, all work halts. No MPPI implementation or Stage 3.1 benchmarking will occur until this pre-flight plan and its specifications receive explicit human sign-off.
