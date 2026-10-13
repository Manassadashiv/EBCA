# Step 2 Report: Screening Runner Migration to Canonical Organism

**Milestone:** Canonical Re-Unification — Step 2  
**Date:** 2026-09-24  
**Workspace:** `d:\ebca`  
**Target Runner:** [`tests/run_stage3_4R4_3_screening.py`](file:///d:/ebca/tests/run_stage3_4R4_3_screening.py) (Screening Runner)  
**Organism Interface:** [`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py) (`CarlAutonomousOrganismAgent`)  
**Status:** **STEP 2 SCREENING RUNNER MIGRATION COMPLETE ✅ (Architectural Migration Only)**  
**Behavioral Certification Status:** **Stage 3.4 = UNCERTIFIED ❌ | Stage 3.5 = STRICTLY LOCKED 🔒**

---

## 1. Executive Summary & Audit Context

In accordance with the CARL-DX Master Developmental Architecture and the Step 2 Migration Protocol:
1. **Screening Runner Migration (Case A Scope Resolution):** [`tests/run_stage3_4R4_3_screening.py`](file:///d:/ebca/tests/run_stage3_4R4_3_screening.py) was updated to eliminate standalone engine calls (`CARLActiveInferenceEngine`) and instead instantiate and execute the **one unified canonical organism**:
   ```python
   agent = CarlAutonomousOrganismAgent(
       dt=hal.dt,
       enable_memory=True,
       deliberation_mode="active_inference",
       grid_path=grid_path,
       w_info=arm_w_info,
       frontier_mode="macro",
       norm_mode="dimensionless"
   )
   agent.initialize_spatial_grounding(sx, sy, syaw)
   ```
   *Scope Clarification:* Step 2 is strictly defined as the **Screening Runner Migration**. The 200-episode certification runner ([`tests/test_stage3_4R3_certification.py`](file:///d:/ebca/tests/test_stage3_4R3_certification.py)) was intentionally **not** migrated in Step 2; it remains preserved as an immutable historical record, and its migration is explicitly scheduled for the future Stage 3.4 behavioral resolution/re-certification phase.
2. **Canonical Cognitive Execution:** Each timestep runs through the complete organism cognitive cycle:
   ```python
   cog_result = agent.step_cognitive_cycle(hal)
   hal.step(cog_result["action_cmd"])
   ```
   Active Inference deliberation is invoked strictly through the canonical organism lifecycle, with full sensory ingestion, kinematic slip estimation, continuous attractor (CANN) tracking, and allocentric raster occupancy updates.
3. **Screening Battery Executed:** The 10-configuration screening battery (Configs 0–4 in Environment 1: Turning Bay, Configs 20–24 in Environment 2: Asymmetric T-Junction) was executed to completion under canonical control.
4. **Scope Boundaries Strictly Preserved:**
   - The 200-episode certification battery was **NOT** executed.
   - `carl_simulation.py` was **NOT** modified (reserved for Step 3).
   - EFE formulations, objective weights, candidate trajectories, and environment geometry were **NOT** altered.
   - **Architectural vs. Behavioral Distinction:** Step 2 is strictly an **architectural screening runner migration success**, NOT a Stage 3.4 behavioral success. Stage 3.4 remains **UNCERTIFIED**; Stage 3.5 remains **STRICTLY LOCKED**.

---

## 2. Migration Architecture: Before vs. After

| Attribute | Standalone Screening (Pre-Step 2) | Canonical Organism Screening (Step 2) |
| :--- | :--- | :--- |
| **Deliberation Class** | `CARLActiveInferenceEngine` directly | `CarlAutonomousOrganismAgent` (`deliberation_mode="active_inference"`) |
| **Step Invocation** | `ctrl.select_action(hal.get_sonar_readings(), ...)` | `cog_result = agent.step_cognitive_cycle(hal)` |
| **Physics Drive** | Direct wheel command injection | HAL actuation via `cog_result["action_cmd"]` |
| **Spatial Grounding** | Disconnected internal pose filter | Shared canonical path integrator + CANN tracking |
| **Occupancy Memory** | Standalone grid map instance | Canonical `AllocentricRasterOccupancyMemory` organ |
| **Cognitive Isolation** | Unverified in script | 100% verified AST-clean decision pipeline |

---

## 3. 10-Configuration Screening Results (Bit-for-Bit Traceable)

Execution was completed across 10 matched configurations using the exact physical MuJoCo simulation environment ($dt = 0.03\text{ s}$). The following tables and metrics are generated directly from [`evidence/canonical_reunification_step2/r4_3_screening_trials.json`](file:///d:/ebca/evidence/canonical_reunification_step2/r4_3_screening_trials.json) and [`evidence/canonical_reunification_step2/r4_3_screening_scorecard.json`](file:///d:/ebca/evidence/canonical_reunification_step2/r4_3_screening_scorecard.json).

### Individual Episode Diagnostics

| Config | Env | Seed | Outcome | Ticks | Final $(X, Y)$ | Mean Lat (ms) | p95 Lat (ms) | Mean $H_{err}$ | Veto Frac | Phases (Rev / Turn / Chan / Egress) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | Env 1 | 5001 | **TIMEOUT** | 220 | $(-0.3081, -0.0083)$ | 8.8 | 12.9 | 9.68° | 0.12 | ✅ / ✅ / ❌ / ✅ |
| **1** | Env 1 | 5001 | **ESCAPE** | 47 | $(0.6080, -0.1129)$ | 8.2 | 13.1 | 5.80° | 0.00 | ✅ / ✅ / ✅ / ✅ |
| **2** | Env 1 | 5001 | **ESCAPE** | 39 | $(0.4840, -0.1005)$ | 7.6 | 11.4 | 8.28° | 0.01 | ✅ / ✅ / ✅ / ✅ |
| **3** | Env 1 | 5001 | **ESCAPE** | 114 | $(0.0872, -0.1069)$ | 8.5 | 12.4 | 11.93° | 0.11 | ✅ / ✅ / ✅ / ✅ |
| **4** | Env 1 | 5002 | **ESCAPE** | 47 | $(0.6962, -0.1077)$ | 9.1 | 13.4 | 2.21° | 0.00 | ✅ / ✅ / ✅ / ❌ |
| **20** | Env 2 | 5001 | **TIMEOUT** | 220 | $(0.7606, -1.1073)$ | 9.7 | 16.1 | 13.10° | 0.16 | ✅ / ✅ / ✅ / ✅ |
| **21** | Env 2 | 5001 | **TIMEOUT** | 220 | $(0.9247, -1.1546)$ | 9.6 | 16.3 | 7.30° | 0.14 | ✅ / ✅ / ✅ / ✅ |
| **22** | Env 2 | 5001 | **TIMEOUT** | 220 | $(0.0577, 0.0995)$ | 8.8 | 14.4 | 7.82° | 0.19 | ✅ / ✅ / ❌ / ✅ |
| **23** | Env 2 | 5001 | **COLLISION** | 201 | $(1.0058, -0.6072)$ | 10.3 | 17.8 | 6.31° | 0.19 | ✅ / ✅ / ✅ / ✅ |
| **24** | Env 2 | 5001 | **TIMEOUT** | 220 | $(0.8521, -1.1444)$ | 8.6 | 13.3 | 10.62° | 0.17 | ✅ / ✅ / ✅ / ✅ |

### Aggregate Scorecard

| Metric | Target / Formal Gate | Screening Result | Adjudication |
| :--- | :--- | :--- | :--- |
| **Trials Completed** | 10 Screening Trials | 10 / 10 | Executed through canonical organism |
| **Overall Escapes** | $\ge 85\%$ (Formal Gate 1) | **4 / 10 (40.0%)** | **FAILED CLOSED ❌** |
| **Overall Collisions** | $\le 5\%$ (Formal Gate 2) | **1 / 10 (10.0%)** | **FAILED CLOSED ❌** |
| **Overall Timeouts** | Informational | **5 / 10 (50.0%)** | 1 in Env 1, 4 in Env 2 |
| **Env 1 Escapes** | Benchmark Diagnostic | 4 / 5 (80.0%) | 4/5 reached $y \le -0.10\text{ m}$ |
| **Env 1 Collisions** | $\le 5\%$ (Formal Gate 2) | 0 / 5 (0.0%) | Zero contact |
| **Env 2 Escapes ($y \le -1.20\text{ m}$)** | $\ge 85\%$ (Formal Gate 1) | **0 / 5 (0.0%)** | **FAILED CLOSED ❌ (Tick Cap)** |
| **Env 2 Channel Entries ($y < -0.50\text{ m}$)** | Diagnostic Progression | 4 / 5 (80.0%) | 4/5 penetrated narrow channel |
| **Env 2 Collisions** | $\le 5\%$ (Formal Gate 2) | 1 / 5 (20.0%) | 1 hull corner contact (Cfg 23) |
| **Mean Cognitive Latency** | $\le 20.0\text{ ms}$ (Formal Gate 4) | **8.93 ms** | **PASSED ✅ (55.4% margin)** |
| **p95 Cognitive Latency** | $\le 45.0\text{ ms}$ (Formal Gate 4) | **17.83 ms** | **PASSED ✅ (60.4% margin)** |

---

## 4. Behavioral Analysis & Visual Proofs

### Visual Plots Generated

The screening execution automatically generated publication-quality diagnostic plots in [`evidence/canonical_reunification_step2/plots/`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/):

1. **[`screening_trajectories_env1.png`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/screening_trajectories_env1.png):**
   - 2D trajectory traces in Environment 1 (Cul-de-sac Turning Bay).
   - Demonstrates that **4/5 configurations (Configs 1, 2, 3, 4) reached the registered Env-1 escape threshold** ($y \le -0.10\text{ m}$) in 39 to 114 ticks. (Note: Config 4 achieved the threshold crossing without registering $\ge 15$ ticks of sustained forward egress).
   - Config 0 completed reversal and reorientation but did not cross the registered Env-1 escape threshold; it stopped at $y=-0.0083\text{ m}$, 91.7 mm short of the $y=-0.10\text{ m}$ threshold at the 220-tick cutoff.
2. **[`screening_trajectories_env2.png`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/screening_trajectories_env2.png):**
   - 2D trajectory traces in Environment 2 (Asymmetric T-Junction).
   - Demonstrates that 4 out of 5 configurations (Configs 20, 21, 23, 24) successfully discovered and performed the multi-point turnaround and entered the narrow vertical channel ($y < -0.50\text{ m}$).
   - Configs 20, 21, and 24 traversed deeply down the channel to final positions $(0.7606, -1.1073)\text{ m}$, $(0.9247, -1.1546)\text{ m}$, and $(0.8521, -1.1444)\text{ m}$, stopping just short of the $-1.20\text{ m}$ goal line at the 220-tick cutoff.
   - Config 23 reached $(1.0058, -0.6072)\text{ m}$ before sustaining a single hull contact at tick 201 during tight channel navigation.
3. **[`screening_latency_and_heading_diagnostics.png`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/screening_latency_and_heading_diagnostics.png):**
   - **Latency (Left):** Every config exhibits mean cycle latency between 7.6 ms and 10.3 ms (overall mean 8.93 ms) and p95 latency between 11.4 ms and 17.8 ms (overall max 17.83 ms in Config 23), comfortably inside the real-time budgets (20.0 ms mean / 45.0 ms p95).
   - **Heading Tracking (Right):** Tracks heading error between internal fused CANN/odometry and unprivileged MuJoCo ground truth. Across all 10 trials, mean heading error ranges from **2.21° (Config 4) to 13.10° (Config 20)**, with an overall average of **8.31°** and peak p95 of **20.81°**.

---

## 5. Formal Adjudication & Integrity Affirmation

1. **Step 2 Screening Migration Verdict:** The migration of the screening runner (`tests/run_stage3_4R4_3_screening.py`) is **strictly an architectural integration success**. `tests/run_stage3_4R4_3_screening.py` now runs exclusively through `CarlAutonomousOrganismAgent` on the canonical zero-copy memory bus.
2. **Case A Scope Affirmation:** Step 2 is explicitly bounded to the screening runner. The 200-episode certification runner (`tests/test_stage3_4R3_certification.py`) was intentionally not touched; its migration is scheduled as a future task for the Stage 3.4 behavioral resolution/re-certification phase.
3. **Behavioral Gate Reality:**
   - Active Inference autonomously discovers multi-point turnaround and channel entry maneuvers (80% channel entry in Env 2) without handcoded rules.
   - However, **Stage 3.4 behavioral certification remains FAILED CLOSED ❌**:
     - Escape rate: 4/10 (40.0%) overall, 0/5 (0.0%) in Env 2 (Target: $\ge 85\%$).
     - Collision rate: 1/10 (10.0%) overall, 1/5 (20.0%) in Env 2 (Target: $\le 5\%$).
   - Full escape certification across asymmetric dead-ends remains unproven due to conservative forward egress speeds within the 220-tick budget and physical hull clearance limitations.
4. **Roadmap Invariant Lock:**
   - **Stage 3.4 Status:** **UNCERTIFIED ❌** (Formal certification gates 1 & 2 fail closed; the full 200-episode battery was **not** run).
   - **Stage 3.5 Status:** **STRICTLY LOCKED 🔒** (No development or unlocking of Stage 3.5 may proceed).

---

## 6. Artifact & Evidence Manifest

- **Screening Runner:** [`tests/run_stage3_4R4_3_screening.py`](file:///d:/ebca/tests/run_stage3_4R4_3_screening.py)
- **Trials Raw Data:** [`evidence/canonical_reunification_step2/r4_3_screening_trials.json`](file:///d:/ebca/evidence/canonical_reunification_step2/r4_3_screening_trials.json)
- **Scorecard Summary:** [`evidence/canonical_reunification_step2/r4_3_screening_scorecard.json`](file:///d:/ebca/evidence/canonical_reunification_step2/r4_3_screening_scorecard.json)
- **Env 1 Trajectory Plot:** [`evidence/canonical_reunification_step2/plots/screening_trajectories_env1.png`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/screening_trajectories_env1.png)
- **Env 2 Trajectory Plot:** [`evidence/canonical_reunification_step2/plots/screening_trajectories_env2.png`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/screening_trajectories_env2.png)
- **Latency & Heading Diagnostics:** [`evidence/canonical_reunification_step2/plots/screening_latency_and_heading_diagnostics.png`](file:///d:/ebca/evidence/canonical_reunification_step2/plots/screening_latency_and_heading_diagnostics.png)
