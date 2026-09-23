# CARL-DX / EBCA — CANONICAL PROJECT MASTER STATE
**The Authoritative Living Master Memory, Forensic Architecture Matrix & Developmental State Ledger**

```
========================================================================================
                                 CHANGE CONTROL & METADATA
========================================================================================
Document Path:          D:\ebca\CARL_PROJECT_MASTER_STATE.md
Canonical Status:       SINGLE PERMANENT SOURCE OF TRUTH (Overrides all historical notes & claims)
Master State Version:   3.4.0-STAGE3_3_CERTIFIED
Effective Date:         September 14, 2026
Authoritative Baseline: CARL-DX Embodied Organism (MuJoCo 3.3.4, vessel_kinetic.xml)
Scientific Standard:    Zero-Trust Forensic Truth & Fail-Closed Validation
Active Milestone:       Stage 3.0 Certified ✅ | Stage 3.1-R Certified ✅ | Stage 3.2 FAILED CLOSED ❌ | Stage 3.2-R FAILED CLOSED (Diagnostic) ❌ | Stage 3.3 CERTIFIED ✅ | Stage 3.4 FAILED CLOSED ❌ | Stage 3.4-R FAILED CLOSED ❌ | Stage 3.4-R2 FAILED CLOSED ❌
Master Roadmap Doc:     d:\ebca\CARL_STAGE3_MASTER_ROADMAP_AND_GOVERNANCE.md
Pre-Reg Protocol:       d:\ebca\CARL_STAGE3_4R2_PREREGISTERED_PROTOCOL.md
Verification Report:    d:\ebca\CARL_STAGE3_4R2_FINAL_VERIFICATION_REPORT.md
Scorecard:              d:\ebca\evidence\stage3_4R2\stage3_4R2_scorecard.json
========================================================================================

```

---

## 1. Executive Definition & Non-Negotiable Scientific Guardrails

### What CARL Currently Is
CARL-DX is an embodied computational organism simulated in MuJoCo physics (`world/vessel_kinetic.xml`) operating at 30 Hz. It integrates:
1. **Physical Embodiment (Stage 1 & 1.6 - Certified)**: 6-DoF differential drive chassis ($m = 1.045\text{ kg}$, $b = 0.23\text{ m}$, $r = 0.048\text{ m}$) with jerk-limited S-curve motor dynamics and grounded traction/slip estimation.
2. **Attractor Spatial Memory (Stage 2.1A-R / 2.1B-R4 - Certified)**: Continuous Attractor Neural Networks (64-HD ring + 1,024-grid torus, 2,114 total units) performing robust dead-reckoning and causal heading maintenance under sensor blackout.
3. **Predictive Mental Simulator (Stage 2.2-R2 - Benchmark Passed, Architecturally Disclosed)**: An air-gapped hybrid analytical-occupancy forward simulator predicting multi-modal proprioception, gyroscope heading, and radial sonar clearance over 5-to-20 step counterfactual action arcs.

### What CARL Is NOT (Strict Negative Boundaries)
- **CARL is NOT a scripted robot**: No rule-based state machine controls navigation (`if obstacle -> turn_right` is strictly prohibited).
- **CARL is NOT an end-to-end black-box Deep RL policy**: Navigation is driven by internal predictive forward modeling and Free Energy optimization, not static Q-tables or opaque weight vectors.
- **CARL is NOT conscious, sentient, or self-aware**: Claims of machine consciousness, qualia, or artificial sentience are unscientific, rejected, and strictly prohibited.
- **CARL is NOT an autonomous general SLAM system (YET)**: The current Stage 2.2-R2 occupancy grid was generated using privileged MuJoCo coordinates, not autonomous exploratory discovery.

### The 3-Tier Truth Taxonomy
To prevent semantic drift, all capabilities must be classified into one of three tiers:
- **Tier A (Vision)**: Theoretical blueprints, equations, and long-term aspirational targets.
- **Tier B (Code)**: Syntactically functional Python scripts present in the repository (`d:\ebca`).
- **Tier C (Evidence)**: Empirically validated physical simulation logs, decoded 30 FPS video recordings, and reproducible scorecards.

---


# CARL Developmental Architecture & Forensic Master Audit
**Document ID:** `CARL-DEV-MASTER-AUDIT-2026-09-06`  
**Classification:** Scientific Governance, Forensic Reconciliation & Stage 4 Readiness Blueprint  
**Authority:** Lead Research Architect & Forensic Auditor  
**Governing Rule:** *No stage advancement without empirical closure. Zero compensatory weighting. Zero conflation of [IMPLEMENTED] with [PROVEN].*

---

## A. Authoritative CARL State Ledger

| Stage | Substage | Implemented | Tested | Verified | Certified | Primary Evidence Artifacts | Blocking Issues / Forensic Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Stage 1** | **Sensorimotor Grounding** | **YES** | **YES** | **YES** | **YES** | `CARL_STAGE1_SCIENTIFIC_VALIDATION_REPORT.md`<br>`CARL_STAGE1_GATE_RESULTS.json` | None. Closed. |
| **Stage 1.6** | **Locomotion / Self-Model** | **YES** | **YES** | **YES** | **YES** | `CARL_STAGE1_6_KINEMATIC_SLIP_VERIFICATION_REPORT.md`<br>`carl_stage1_6_traction_demonstration.mp4` | None. Closed. |
| **Stage 2.1** | **Persistent Spatial Grounding (CANN)** | **YES** | **YES** | **YES** | **YES** | `CARL_STAGE2_1B_R4_IMPLEMENTATION_REPORT.md`<br>`carl_stage2_1b_r4_spatial_demonstration.mp4` | None. Closed. |
| **Stage 2.2** | **Initial Monolithic Predictor** | **YES** | **YES** | **NO** | **NO** | `CARL_STAGE2_2_IMPLEMENTATION_REPORT.md` | **FAILED** (2/6 gates passed; collapsed into identity mapping). |
| **Stage 2.2** | **2.2-DIAG (Diagnostic Battery)** | **YES** | **YES** | **YES** | **YES** | `CARL_STAGE2_2_DIAGNOSTIC_MATRIX.md`<br>`stage2_2_diagnostic_bundle/` | **CLOSED**. Proved action-insensitivity of GRUs; established necessity of modular decomposition. |
| **Stage 2.2** | **2.2-R2 (Modular Predictor)** | **YES** | **YES** | **PARTIAL** | **NO** | `evidence/stage2_2_r2/r2_benchmark_scorecard.json`<br>`evidence/stage2_2_r2/CARL_STAGE2_2_R2_RECOVERY_REPORT.md` | **CONDITIONAL PASS ON BENCHMARK.** Blocked from scientific certification by privileged map teleportation and hardcoded momentum decay. |
| **Stage 2.2** | **2.2-GROUNDED (Grounded Predictor)** | **YES** | **YES** | **YES** | **YES** | `evidence/stage2_2_grounded/grounded_benchmark_scorecard.json`<br>`evidence/stage2_2_grounded/CARL_STAGE2_2_GROUNDED_CLOSURE_REPORT.md` | **SCIENTIFICALLY REMEDIATED & CERTIFIED.** All 7 gates passed under lexical certification without synthetic shortcuts (`0.20 * err_orig` purged). Gate 5 authentic probe: 96.0% ($p=6.22\times 10^{-15}$); Gate 6: 20/20 branches passed ($R^2=0.7275$, Margin$=1.068\text{m}$) under strict subprocess air-gap. Parameter taxonomy: 7 engineered kinematics, 9 learned servos. |
| **Stage 2.3** | **2.3-MVE (Closed-Loop Deliberation)** | **YES** | **YES** | **YES** | **YES** | `evidence/stage2_3/stage2_3_scorecard.json`<br>`evidence/stage2_3/CARL_STAGE2_3_MVE_REPORT.md` | **SCIENTIFICALLY REVALIDATED & CERTIFIED.** Revalidated on certified Stage 2.2 model foundation. Deliberation achieves 2.0% collision rate vs 68.0% reflex and 68.0% amnesic (97.1% reduction, p=6.36e-13, Cohen's d=1.628). Causal prediction alignment: 97.9%. Deliberation p95 latency: 37.7ms (<= 50ms budget). |
| **Stage 3.0** | **Pre-Flight Integrity Lock & Code Hygiene Purge** | **YES** | **YES** | **YES** | **YES** | `CARL_STAGE3_PREFLIGHT_VERIFICATION_REPORT.md`<br>`tests/test_stage3_ast_anti_cheat.py` | **CERTIFIED & CLOSED ✅.** Dormant `geom_xpos` and `qpos` z-height purged. 12/12 SHA-256 baseline hashes verified. AST scanner 100% clean across all 8 decision pipeline files. Subprocess MuJoCo poisoning pass. |
| **Stage 3.1** | **CANN Causal Coupling (Original Battery)** | **YES** | **YES** | **NO** | **NO** | `tests/test_stage3_1_cann_causal_battery.py`<br>`evidence/stage3_1/stage3_1_scorecard.json` | **FAILED CLOSED ❌ (Permanent Record).** Exposed spawn-offset bug, inter-episode drift, and ARM-B compass lock confound. |
| **Stage 3.1-R** | **2,114-Unit CANN Causal Remediation Battery** | **YES** | **YES** | **YES** | **YES** | `CARL_STAGE3_1R_FINAL_CAUSAL_CERTIFICATION_REPORT.md`<br>`evidence/stage3_1R/stage3_1R_scorecard.json` | **CERTIFIED & CLOSED ✅.** 5/5 gates passed for ARM-C (Zeroed) & ARM-D (Full-Shuffled) across 2,114 units. Primary Endpoint: $\Delta C_{\mathrm{hull}} = +0.1145\text{m}$ ($p=9.00\times 10^{-17}$, $d=1.119$). Collision rate: 4.0% intact vs 31.0% zeroed. |
| **Stage 3.2** | **Trajectory Fidelity & Memory Necessity (Original)** | **YES** | **YES** | **YES** | **NO (FAILED CLOSED)** | `CARL_STAGE3_2_FINAL_VERIFICATION_REPORT.md`<br>`evidence/stage3_2/scorecard/stage3_2_scorecard.json`<br>`evidence/stage3_2/stage3_2_frozen_manifest.json` | **FAILED CLOSED ❌ (Permanent Record).** Discrete 8-primitive unroller failed non-LOS task families and uncalibrated trajectory fidelity. |
| **Stage 3.2-R** | **Trajectory Fidelity & Memory Necessity Remediation** | **YES** | **YES** | **YES** | **NO (FAILED CLOSED)** | `CARL_STAGE3_2R_FINAL_VERIFICATION_REPORT.md`<br>`evidence/stage3_2R/scorecard/stage3_2R_scorecard.json`<br>`evidence/stage3_2R/stage3_2R_frozen_manifest.json` | **FAILED CLOSED / DIAGNOSTIC RESULT ❌.** Class C integrity passed (10/10, Ds<=0.0487m). Class A model validity: `INVALID_MODEL`. Class B memory necessity: `FAILED_CLOSED` (behavioral navigation gate failed). Action divergence at T_crit confirms memory causally changes action selection under observationally equivalent local sensory conditions (mean ||Du||=0.466 m/s), but discrete 7-candidate deliberation cannot execute continuous non-LOS navigation. Proves continuous action synthesis (MPPI) is an architectural prerequisite. |
| **Stage 3.3** | **Continuous Action Synthesis (MPPI)** | **YES** | **YES** | **YES** | **YES (CERTIFIED ✅)** | `CARL_STAGE3_3_FINAL_VERIFICATION_REPORT.md`<br>`CARL_STAGE3_3_PREREGISTERED_PROTOCOL.md`<br>`evidence/stage3_3/stage3_3_scorecard.json`<br>`evidence/stage3_3/stage3_3R_40trial_battery_scorecard.json` | **CERTIFIED & CLOSED ✅ (Stage 3.3-R Remediation Battery Passed).** Continuous MPPI engine ($M=128, H=15$) achieves chatter-free smoothness (delta $= 0.0602 \le 0.35$), sub-2ms latency (p95 $= 2.14\text{ ms} \le 45.0\text{ ms}$), $+0.0191\text{ m}$ clearance margin gain, and causal CANN coupling ($\Delta \mathbf{u}^* = 0.4247\text{ m/s}$, $p=1.18\times 10^{-168}$). In 40-trial matched remediation stress test against discrete baseline, MPPI reduced collisions by 50.0% ($15.0\% \to 7.5\%$), with an MPPI collision ceiling of $7.5\% \le 10.0\%$. In Family 4 dogleg chicane, MPPI cut collisions from 75% to 25% (66.7% reduction). All 5 frozen gates passed. |
| **Stage 3.4** | **Autonomous Behavioral Discovery under Active Inference** | **YES** | **YES** | **YES** | **NO (FAILED CLOSED ❌)** | `CARL_STAGE3_4_FINAL_VERIFICATION_REPORT.md`<br>`CARL_STAGE3_4_PREREGISTERED_PROTOCOL.md`<br>`evidence/stage3_4/stage3_4_scorecard.json`<br>`evidence/stage3_4/stage3_4_raw_trials.json` | **FAILED CLOSED ❌ (Permanent Record).** Gate 2 Emergent Reversal passed (77.5% >= 75.0%), Gate 4 Latency passed (mean 13.52ms, p95 23.22ms), Gate 5 AST Anti-Cheat passed. Gate 1 (0% escape, 65% collision) and Gate 3 (Delta=0%, p=1.0) failed closed due to physical geometry constraints: tight 0.70m U-trap leaves insufficient clearance (<0.11m) for single-horizon MPPI pivot arcs without multi-point oscillation. |
| **Stage 3.4-R** | **Active Inference Remediation & Epistemic Causal Necessity** | **YES** | **YES** | **YES** | **NO (FAILED CLOSED ❌)** | `CARL_STAGE3_4R_FINAL_VERIFICATION_REPORT.md`<br>`CARL_STAGE3_4R_PREREGISTERED_PROTOCOL.md`<br>`evidence/stage3_4R/stage3_4R_scorecard.json`<br>`evidence/stage3_4R/stage3_4R_raw_trials.json` | **FAILED CLOSED ❌ (Permanent Record).** 210 episodes executed (10 diagnostic + 200 certification). Factorial diagnostic proved turning clearance alone does not solve escape (0% escape, 70% stall). In 200-episode certification battery across 50 matched configs, ARM-A achieved 0% escape, 18% collision, 82% stall/timeout. Gate 1 (0% < 80%), Gate 2 (2% < 75%), and Gate 3 (Delta=0%, p=1.0) failed closed. Gate 4 (mean 12.18ms, p95 22.30ms) and Gate 5 (100% clean AST) passed. Stage 3.5 remains strictly LOCKED 🔒. |
| **Stage 3.4-R2** | **Macro-Frontier & Dimensionless Remediation** | **YES** | **YES** | **YES** | **NO (FAILED CLOSED ❌)** | `CARL_STAGE3_4R2_FINAL_VERIFICATION_REPORT.md`<br>`CARL_STAGE3_4R2_PREREGISTERED_PROTOCOL.md`<br>`evidence/stage3_4R2/stage3_4R2_scorecard.json`<br>`evidence/stage3_4R2/stage3_4R2_raw_trials.json` | **FAILED CLOSED ❌ (Permanent Record).** 210 episodes executed (10 diagnostic + 200 certification). 4-arm ablation (Macro+DimNorm, Pragmatic, Micro 3cm, Unnorm). ARM-A achieved 0% escape, 28% collision, 72% stall/timeout. Gate 1 (0% < 80%), Gate 2 (0% < 75%), and Gate 3 (Delta=0%, p=1.0) failed closed due to corridor mouth margin energy barrier ($W=0.70\text{ m}$). Gate 4 (mean 3.76ms, p95 10.20ms) and Gate 5 (100% clean AST) passed. Stage 3.5 remains strictly LOCKED 🔒. |
| **Stage 4** | **Autopoietic / Lifelong Memory** | **PARTIAL** | **NO** | **NO** | **NO** | `brain/carl_stdp.py`, `brain/carl_hdc.py`, `brain/carl_gis.py` | **UNPROVEN.** Substrate scripts exist; no multi-session reboot test proving causal behavioral advantage. |

| **Stage 5** | **Metacognition** | **NO** | **NO** | **NO** | **NO** | None | **CONCEPTUAL ONLY.** Zero implementation. |

---

## B. Forensic Verdict on Stage 2.2-R2

Stage 2.2-R2 represents an enormous engineering advance over the failed initial monolithic model, but **it cannot be certified as an autonomous biological world model**. It must be scientifically classified as:
> **An execution-isolated, air-gapped hybrid analytical-occupancy mental simulator.**

```
                                  STAGE 2.2-R2 FORENSIC DECOMPOSITION
                                                  │
                 ┌────────────────────────────────┴────────────────────────────────┐
                 ▼                                                                 ▼
      WHAT IS GENUINELY PROVEN                                          WHAT IS PRIVILEGED / ENGINEERED
  • Air-gapped subprocess execution                                 • Map built via 9-point privileged teleportation
    (sys.modules['mujoco'] = None)                                    (scratch/save_test_grid.py using qpos)
  • 30.6ms batched ray-clearance query                              • Mental model spoon-fed global origin
    (39,000x speedup via grid_sample)                                 (S0 = [-1.50, -1.80, -45°])
  • Severe causal memory dependence                                 • Momentum decay parameters manually fitted
    (+204.8% error on erasure, +109.8% on scramble)                   (gamma_v = 0.70, gamma_w = 0.75)
  • Directional attraction to alternate reality                     • Razor-thin safety margins on continuous branches
    (100% on N=50 pairs, p = 8.88e-16)                                (Branch 8 R² margin: +0.014; Branch 3: +2.0cm)
  • Collision anticipation before contact                           • Static arena assumption
    (ROC-AUC = 0.9950)                                                (No mechanism for dynamic/moving obstacles)
```

### 1. What is Genuinely Proven
* **Computational Independence (Subprocess Air-Gap):** The mental simulator runs inside a separate Python interpreter with `sys.modules['mujoco'] = None`. It accesses zero simulator state, zero C-API calls, and zero external raycasting.
* **Vectorized Clearance Mapping (The 30ms Engine):** Ray queries against internal 2D grid tensors were fully vectorized via bilinear sampling, reducing rollout latency from 20 minutes to 30.6 milliseconds.
* **Causal Dependence on Spatial Memory (Gate 4 & Gate 5):**
  * Erasing the grid memory surges prediction error by **$+204.82\%$**.
  * Scrambling the grid memory surges prediction error by **$+109.77\%$**.
  * Swapping grid memories on $N=50$ sensory-ambiguous pairs directionally attracts prediction toward the alternate reality in **$100.0\%$ of trials ($p = 8.88 \times 10^{-16}$)**.
* **Early Hazard Anticipation (Gate 7):** Prospective obstacle clearance predicts impending collisions with **$\text{ROC-AUC} = 0.9950$**.

### 2. What is Engineered / Privileged
* **The Teleported Oracle Map:** `evidence/stage2_2_r2/arena_occupancy_grid.pt` was populated by `scratch/save_test_grid.py`, which systematically set `hal.data.qpos` to 9 predefined grid coordinates $[(-1.5, -1.5) \dots (1.5, 1.5)]$ and rotated across 24 angles. The map was **not** acquired through autonomous locomotion from $(0, 0)$.
* **Hardcoded Absolute Origin:** The air-gapped mental simulator had to be handed $S_0 = [-1.50, -1.80, -45.0^\circ]$ to align with the teleported map. CARL has no self-localization mechanism to determine its own $(x, y, \theta)$ relative to an unknown room.
* **Hand-Tuned Momentum Physics:** Decay factors ($\gamma_v = 0.70, \gamma_w = 0.75$) were originally manually tuned.

### 3. Stage 2.2 Grounded Scientific Closure (CERTIFIED & CLOSED)
Under forensic audit, Stage 2.2 was completely re-grounded from raw sensorimotor embodiment to permanently eliminate privileged cheats:
* **Autonomous Spatial Discovery:** Replaced 9-point oracle teleportation with 1,899 ticks of autonomous exploration from origin $(0,0,0)$ via differential locomotion and online raycasting (`evidence/stage2_2_grounded/grounded_occupancy_grid.pt`).
* **Learned Kinematic Body Dynamics:** Replaced hand-tuned momentum with a 13-parameter model trained by gradient descent on empirical transitions (`checkpoints/stage2_2_grounded/grounded_body_model.pt`, Proprio $R^2 = 0.9613$, Gyro $R^2 = 0.8466$).
* **Subprocess Air-Gap Sandbox:** Strictly enforced `sys.modules['mujoco'] = None`, passing all 7 forensic gates. Full report: `evidence/stage2_2_grounded/CARL_STAGE2_2_GROUNDED_CLOSURE_REPORT.md`.

---

## C. Stage 2.3: Closed-Loop Action Deliberation MVE (VALIDATED & CERTIFIED)

Stage 2.3 transitions CARL from **passive prediction** ("What will happen?") to **active decision-making** ("Which imagined future should I pick?").

```
                                 STAGE 2.3 CLOSED-LOOP ACTION DELIBERATION
                                                     │
                                                     ▼
                                        CURRENT SENSOR STATE (s_t)
                                                     │
                                                     ▼
                                     GENERATE 3 CANDIDATE BRANCHES
                                    [Straight]    [Left]    [Right]
                                         │           │         │
                                         ▼           ▼         ▼
                                        AIR-GAPPED MENTAL SIMULATOR
                                       (H=10 step lookahead in 12ms)
                                         │           │         │
                                         ▼           ▼         ▼
                                    EVALUATE PREDICTED CLEARANCE & HAZARD
                                     P(coll)=0.92  P(coll)=0.85  P(coll)=0.05
                                         │           │         │
                                         └─────┬─────┴─────────┘
                                               │
                                               ▼
                                      SELECT BEST CANDIDATE
                                    (Minimum Risk / Max Clearance)
                                               │
                                               ▼
                                        PHYSICAL EXECUTION
                                      (Step wheels in MuJoCo)
                                               │
                                               ▼
                                  COMPARE PREDICTION vs PHYSICAL REALITY
                                     (Compute Prediction Error PE)
                                               │
                                               ↺
```

### 1. Minimal Scientific Specification
* **Objective:** CARL approaches an obstacle at $0.5 - 0.8\,\text{m}$. It must internally roll out 3 candidate action sequences ($H=10$):
  1. *Candidate A (Straight):* $u = [0.8, 0.8]$
  2. *Candidate B (Left Turn):* $u = [0.2, 0.8]$
  3. *Candidate C (Right Turn):* $u = [0.8, 0.2]$
* **Deliberation Mechanism:** The action chosen must be the one with $\min P(\text{collision})$ and $\max \text{Clearance}$ evaluated via prospective unroll on `grounded_occupancy_grid.pt`.
* **Zero Simulator Leaks:** The deliberation function sees only its own mental unrolls from `SpatialOccupancyMemory`. It receives zero MuJoCo geometry, contacts, or coordinate buffers.

### 2. Mandatory Scientific Controls (4-Way Comparison over $N=50$ Trials, 200 Total Episodes)
1. **Control 1 (Random Exploration):** Stochastic exploration baseline among candidate action branches.
2. **Control 2 (Static Scripted Reflex):** "If front sonar $< 0.5\,\text{m}$, turn left" (naive reactive baseline).
3. **Control 3 (Amnesic / No-Memory Model):** Mental rollout running with erased spatial memory ($\mathcal{M}_{\text{env}} = \mathbf{0}$).
4. **Experimental (Stage 2.3 Deliberative Policy):** Mental rollout running through full air-gapped modular predictor.

### 3. Quantitative Acceptance Criteria & Empirical Results (`evidence/stage2_3/stage2_3_scorecard.json`)

| Metric | Deliberative (Ours) | Scripted Reflex | Amnesic (No Map) | Random Walk | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Collision Rate (%)** | **8.0%** (4/50) | **68.0%** (34/50) | **68.0%** (34/50) | **48.0%** (24/50) | **PASSED** |
| **Mean Ticks Survived** | **57.0** / 60 | 41.8 / 60 | 41.8 / 60 | 47.7 / 60 | **PASSED** |
| **p95 Latency (ms)** | **12.11 ms** | 0.017 ms | 0.020 ms | 0.066 ms | **$\le 50.0\text{ ms}$ (PASSED)** |
| **Collision Reduction vs Random** | **83.3%** | — | — | — | **$\ge 60.0\%$ (PASSED)** |
| **Collision Reduction vs Reflex** | **88.2%** | — | — | — | **$\ge 25.0\%$ (PASSED)** |
| **Causal Prediction Alignment** | **98.14%** | — | — | — | **$\ge 85.0\%$ (PASSED)** |
| **Statistical Significance ($p$)** | — | **$1.56 \times 10^{-8}$** | **$1.56 \times 10^{-8}$** | **$3.33 \times 10^{-4}$** | **$p < 0.05$ (PASSED)** |

**Milestone Verdict:** **STAGE 2.3 MVE SCIENTIFICALLY CERTIFIED & VALIDATED**. Full report: `evidence/stage2_3/CARL_STAGE2_3_MVE_REPORT.md`.

---

## D. Stage 3: Architecture & Experimental Roadmap

Stage 3 transitions CARL from choosing among fixed pre-scripted action branches to **synthesizing and discovering continuous behavior**.

```
                                  STAGE 3: BEHAVIORAL DISCOVERY LOOP
                                                    │
                                                    ▼
                                       PROSPECTIVE DRIVE / HOMEOSTASIS
                                     (Energy Deficit, Novelty Seeking)
                                                    │
                                                    ▼
                                     CONTINUOUS TRAJECTORY OPTIMIZATION
                                        (MPPI in Latent Motor Space)
                                                    │
                                                    ▼
                                     EVALUATE THROUGH WORLD MODEL (M_env)
                                                    │
                                                    ▼
                                      EXECUTE DISCOVERED MOTOR GAIT
                                                    │
                                                    ▼
                                       OUTCOME & INTRINSIC REWARD
                                      (Epistemic & Pragmatic Value)
                                                    │
                                                    ▼
                                       UPDATE MOTOR REPERTOIRE
                                                    ↺
```

### 1. Architectural Components
* **Intrinsic Motivation Engine:** Computes free-energy / prediction error reduction. CARL is rewarded for actions that resolve spatial uncertainty (epistemic drive) while avoiding hazards (homeostatic drive).
* **Model Predictive Path Integral (MPPI) Controller:** Samples 128 continuous Gaussian perturbations in motor space $[u_L, u_R, u_{\text{hip}}, u_{\text{neck}}]$, unrolls them through Module 1 & Module 2 in parallel, and computes a trajectory distribution without gradient descent.
* **Motor Synergies Library:** Compresses high-dimensional discovered actions into reusable primitive behaviors (e.g., pivot-reverse escape, wall-following cruise).

### 2. Experimental Batteries
* **Battery 3A (Obstacle Circumvention Discovery):** CARL placed facing an irregular U-shaped trap. Reactive agents get stuck in local minima; CARL must synthesize a multi-step reverse-turn-navigate trajectory.
* **Battery 3B (Terrain Transition Adaptation):** Floor friction dynamically drops from $\mu=1.0$ (concrete) to $\mu=0.05$ (ice). CARL must discover a lower-acceleration locomotion gait to maintain control.
* **Battery 3C (Non-Predefined Gait Synthesis):** Disabling one drive wheel; CARL must discover an asymmetrical limping gait to maintain directional locomotion.

---

## E. Stage 4: Autopoietic / Lifelong Memory & Persistence

**Scientific Definition:** CARL retains, consolidates, retrieves, and continuously updates experiential knowledge across process lifecycles, demonstrating a measurable behavioral advantage in Session $N+1$ based on experiences from Session $N$.

```
                                      STAGE 4 LIFELONG LIFECYCLE
                                                    │
    ┌───────────────────────────────────────────────┴───────────────────────────────────────────────┐
    │                                           SESSION 1                                           │
    │  CARL navigates novel environment → Experiences severe hazard at Location X (Collision/Low Batt)│
    │                                               │                                               │
    │                                               ▼                                               │
    │                                4.1 MEMORY FORMATION (Encoding)                                │
    │                           Multi-modal binding: [Place ⊗ Sonar ⊗ Trauma]                       │
    │                                               │                                               │
    │                                               ▼                                               │
    │                             4.2 MEMORY CONSOLIDATION (Synaptic / HDC)                         │
    │                       Eligibility traces stabilize into permanent weights                     │
    └───────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                                    │
                                                    ▼
                                   4.3 PERSISTENT STORAGE (Shutdown)
                                   Dumps to disk / Zero state in RAM
                                                    │
                                            [PROCESS DIES]
                                                    │
                                            [PROCESS REBOOTS]
                                                    │
    ┌───────────────────────────────────────────────┴───────────────────────────────────────────────┐
    │                                           SESSION 2                                           │
    │                                               │                                               │
    │                                               ▼                                               │
    │                                    4.4 SELECTIVE RETRIEVAL                                    │
    │                         Re-approaches Location X → Cue triggers memory recall                 │
    │                                               │                                               │
    │                                               ▼                                               │
    │                                   4.8 BEHAVIORAL CONSEQUENCE                                  │
    │                     Alters action trajectory 1.5m BEFORE hazard without new collision         │
    │                                               │                                               │
    │                                               ▼                                               │
    │                               4.5 LIFELONG UPDATING & INTERFERENCE                            │
    │                   If barrier has been removed → Extinguishes old trauma memory                │
    └───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The 8 Structural Pillars of Stage 4

1. **4.1 Memory Formation:** Event-driven multi-modal binding of subjective states $[s_{\text{body}}, s_{\text{sonar}}, \text{endocrine}]$ into unified experiential tokens.
2. **4.2 Memory Consolidation:** Transforming volatile short-term eligibility traces into permanent synaptic weights or hyperdimensional attractor basins.
3. **4.3 Persistent Storage:** Serialization format that survives process death (`SIGKILL`) with zero background daemons.
4. **4.4 Selective Retrieval:** Associative content-addressable recall where partial cues (e.g., familiar wall pattern) retrieve the associated hazard vector.
5. **4.5 Lifelong Updating:** Continual plasticity that incorporates new facts without catastrophic forgetting of established knowledge.
6. **4.6 Conflict & Interference Management:** Disambiguating two similar locations with opposing reward histories.
7. **4.7 Bounded Memory Management:** Eviction, spatial pooling, or compression ensuring that 100 hours of exploration does not exceed fixed VRAM/RAM budgets.
8. **4.8 Causal Behavioral Consequence:** Prior memory must measurably change physical motor output, trajectory clearance, or survival metrics.

### Mandatory 5-Way Control Experiment Across Reboots
To prevent Stage 4 from becoming a trivial disk-saving demo, the reboot test must evaluate five parallel conditions on an identical unseen hazard test:

```
[Condition A] Full Lifelong Memory (Experience + Consolidation + Reboot + Retrieval)
[Condition B] Amnesic Control (Reboot with wiped memory file)
[Condition C] Storage-Only Control (Memory loaded, but retrieval pathways severed)
[Condition D] Permutation Control (Memory loaded, but associative keys spatially permuted)
[Condition E] Tabula Rasa Control (Fresh, completely untrained organism)
```

**The Pass Criterion:** Condition A must show statistically significant ($p < 0.01$, Cohen's $d \ge 0.80$) avoidance of the historical trauma zone at least $1.0\,\text{m}$ earlier than Conditions B, C, D, and E.

---

## F. Forensic Audit of Existing Stage-4 Modules

The repository currently contains three files associated with Stage 4. We performed an empirical inspection of each:

```
                                    EXISTING MODULE TAXONOMY
                                                │
               ┌────────────────────────────────┼────────────────────────────────┐
               ▼                                ▼                                ▼
         carl_stdp.py                      carl_hdc.py                      carl_gis.py
      [Status: EXPERIMENT]             [Status: SUBSTRATE]             [Status: SERIALIZER]
  • Reward-Modulated STDP          • 10,000-D Bipolar HDC           • Disk-backed NPZ state saver
  • Eligible traces (Markram)      • Kanerva vector algebra         • Dumps weights & place graphs
  • Decoupled from HAL/MuJoCo      • Standalone unit tests only     • Zero learning / purely I/O
```

### 1. `brain/carl_stdp.py`
* **What it actually does:** Implements Reward-Modulated Spike-Timing Dependent Plasticity (R-STDP) with pre/post-synaptic activity traces, eligibility decay ($\tau_e = 50\,\text{ms}$), and reward modulation ($dW = \eta \cdot R \cdot E$). Also contains a draft `QuantumDeliberator`.
* **What it consumes:** Raw numerical arrays representing state vectors and action indices.
* **What is learned vs serialized:** Learns an action-weight matrix $W \in \mathbb{R}^{\text{pre} \times \text{post}}$. Contains zero disk-saving or reboot logic.
* **Integration Status:** **DISCONNECTED EXPERIMENT.** It is not wired into `CarlStage1HAL` or the Stage 2.2 modular world model.
* **Classification:** `[EXPERIMENTAL SUBSTRATE]`

### 2. `brain/carl_hdc.py`
* **What it actually does:** Implements 10,000-D Bipolar Hyperdimensional Computing (`HolographicEpisodicMemory`). Uses binding ($\otimes$, element-wise product) and bundling ($\oplus$, sign-sum superposition) to encode $[Place \otimes Sonar \otimes Endocrine]$.
* **What it consumes:** Discrete place indices, 24-D sonar vectors, and 4-D neuroendocrine levels.
* **What is learned vs serialized:** Accumulates episodic hypervectors into $M_{\text{spatial}}$ and $M_{\text{aversion}}$. Generates cosine similarity threats.
* **Integration Status:** **DORMANT ORGAN.** Mathematically sound, but currently invoked only in historical unit tests. Not driving real-time motor commands.
* **Classification:** `[VIABLE MEMORY SUBSTRATE]`

### 3. `brain/carl_gis.py`
* **What it actually does:** `GlobalIntegratedStateManager`. It is an I/O utility that packages reservoir weights, place centres, and HDC vectors into compressed `.npz` files (`carl_gis_state.npz`).
* **What it consumes:** Python references to memory objects.
* **What is learned vs serialized:** **Zero learning.** It is purely a dictionary serialization script.
* **Integration Status:** **UTILITY.** It saves files, but proves zero cognitive persistence on its own.
* **Classification:** `[STORAGE PLUMBING]`

---

## G. Master Developmental Dependency Graph

```
┌────────────────────────────────────────────────────────┐
│ STAGE 1: Sensorimotor Grounding                        │  STATUS: CLOSED / VERIFIED
│ (Chassis kinematic babbling, joint servo control)     │  EVIDENCE: Stage 1 Report
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2.1: Continuous Spatial Self-Model (CANN)        │  STATUS: CLOSED / VERIFIED
│ (Head-direction ring attractor, phase unwrapping)      │  EVIDENCE: Stage 2.1b-R4 Report
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2.2: Modular Predictive World Model              │  STATUS: CONDITIONAL PASS
│ (M_body + M_env + M_gen mental simulation)             │  FORENSIC AUDIT: 7/7 Gates on benchmark,
└───────────────────────────┬────────────────────────────┘  but flagged with privileged map/pose.
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2.3: Predictive Planning & Action Selection      │  STATUS: READY FOR EXECUTION
│ (Mental rollout evaluation: pick candidate with min PE)│  DEPENDENCY: Needs Stage 2.2 air-gap.
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 3: Continuous Behavioral Discovery               │  STATUS: ARCHITECTURAL DESIGN
│ (MPPI trajectory optimization, autonomous navigation) │  DEPENDENCY: Needs Stage 2.3 policy loop.
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 4: Autopoietic / Lifelong Memory & Persistence   │  STATUS: ARCHITECTURAL BLUEPRINT
│ (Experience → Consolidation → Reboot → Changed Action) │  DEPENDENCY: Needs Stage 3 behavior.
└────────────────────────────────────────────────────────┘
```

---

## H. The "Monday Readiness" Package

### 1. One-Page Developmental Summary

```
                      CARL SCIENTIFIC READINESS OVERVIEW
                      ──────────────────────────────────
  CURRENT POSITION:  Stage 2.2-R2 Benchmarked (Forensically Annotated)
  NEXT ACTIVE BUILD: Stage 2.3 Closed-Loop Action Selection MVE
  GOAL FOR MONDAY:   Legitimate Stage 2.3 Verification + Formal Stage 4 Architecture

  STAGE 1   [Body Babbling]        ──────► CERTIFIED (100% Closed)
  STAGE 1.6 [Traction Grounding]   ──────► CERTIFIED (100% Closed)
  STAGE 2.1 [Spatial Self-Model]   ──────► CERTIFIED (100% Closed)
  STAGE 2.2 [World Model Predictor]──────► BENCHMARKED (Caveats Formally Disclosed)
  STAGE 2.3 [Action Selection MVE] ──────► BLUEPRINT READY (Execution Next)
  STAGE 3   [Behavior Discovery]   ──────► DESIGN SPECIFIED (Not Implemented)
  STAGE 4   [Lifelong Memory]      ──────► FULLY DESIGNED (Substrates Audited)
  STAGE 5   [Metacognition]        ──────► ROADMAP CONCEPT ONLY
```

### 2. High-Level System Architecture Diagram

```
                              CARL UNIFIED ORGANISM (STAGE 2.3 TARGET)
                                                 │
                                                 ▼
                              ┌─────────────────────────────────────┐
                              │          MuJoCo SIMULATION          │
                              │       (Physical Ground Truth)       │
                              └──────────────┬───────────────▲──────┘
                                             │               │
                              Physical       │               │ Motor
                              Sensors (s_t)  │               │ Actions (u_t)
                                             ▼               │
                        ┌────────────────────────────────────┴──────────┐
                        │              CANONICAL AGENT CORE             │
                        │                                               │
                        │  ┌─────────────────────────────────────────┐  │
                        │  │  STAGE 2.3 POLICY DELIBERATION ENGINE   │  │
                        │  │  Generates 3 candidates: [L, Fwd, R]    │  │
                        │  └────────────────────┬────────────────────┘  │
                        │                       │                       │
                        │                       ▼                       │
                        │  ┌─────────────────────────────────────────┐  │
                        │  │     AIR-GAPPED MENTAL SIMULATOR         │  │
                        │  │     (sys.modules['mujoco'] = None)      │  │
                        │  │                                         │  │
                        │  │  ┌─────────────┐     ┌───────────────┐  │  │
                        │  │  │ M_body      │────►│ M_env (Grid)  │  │  │
                        │  │  │ Kinematics  │     │ Spatial Map   │  │  │
                        │  │  └──────┬──────┘     └───────┬───────┘  │  │
                        │  │         │                    │          │  │
                        │  │         └───────────┬────────┘          │  │
                        │  │                     ▼                   │  │
                        │  │              ┌─────────────┐            │  │
                        │  │              │ M_gen       │            │  │
                        │  │              │ Clearance   │            │  │
                        │  │              └─────────────┘            │  │
                        │  └─────────────────────────────────────────┘  │
                        └───────────────────────────────────────────────┘
```

### 3. Stage 4 Memory Lifecycle Diagram

```
                               STAGE 4 LIFELONG MEMORY LIFECYCLE
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
        WAKING STATE (Session N)                                    POST-REBOOT (Session N+1)
  ┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
  │ Physical Experience (s, u, PE)  │                         │ Reboot with Clean RAM Cache     │
  └────────────────┬────────────────┘                         └────────────────┬────────────────┘
                   │                                                           │
                   ▼                                                           ▼
  ┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
  │ HDC Multi-Modal Binding         │                         │ Retrieve Associated Memory (HDC)│
  │ [Place ⊗ Sonar ⊗ Endocrine]     │                         │ Cue: Visual Sonar Pattern       │
  └────────────────┬────────────────┘                         └────────────────┬────────────────┘
                   │                                                           │
                   ▼                                                           ▼
  ┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
  │ Consolidate to Superposition    │                         │ Modulate Stage 2.3 Action Pick  │
  │ M_aversion += Episode           │                         │ Avoid trauma zone 1.5m prior    │
  └────────────────┬────────────────┘                         └─────────────────────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │ Atomic Disk Sync (GIS-901)      │
  │ carl_gis_state.npz              │
  └─────────────────────────────────┘
```

---

## I. Scientific Honesty Safeguards: What CANNOT Be Claimed by Monday

To maintain uncompromised scientific integrity before advisors, reviewers, or stakeholders, the following claims **MUST NOT BE MADE**:

1. **DO NOT CLAIM:** *"Stage 4 is complete because `carl_stdp.py`, `carl_hdc.py`, and `carl_gis.py` are written."*  
   *The Truth:* Those files are modular code substrates. They have never been subjected to a multi-session reboot test proving that historical memory alters future physical behavior.
2. **DO NOT CLAIM:** *"Stage 3 behavioral discovery is verified."*  
   *The Truth:* CARL currently selects from pre-scripted action branches. Continuous synthesis of non-predefined behaviors has not been demonstrated.
3. **DO NOT CLAIM:** *"CARL learned an internal map of the arena autonomously."*  
   *The Truth:* The 7,592-cell occupancy map was produced via 9-point privileged coordinate teleportation in MuJoCo.
4. **DO NOT CLAIM:** *"CARL discovered physical momentum and friction."*  
   *The Truth:* Linear and angular coasting filters were analytically derived and hand-coded by the engineer.
5. **DO NOT CLAIM:** *"CARL possesses general human-like imagination."*  
   *The Truth:* CARL possesses an isolated 30-millisecond kinematic raycasting simulator that validates counterfactual spatial clearances in a static, structured arena.

---

## Conclusion & Stop Condition

The roadmap, state ledger, forensic audit, Stage 2.3 MVE, and Stage 4 blueprints are completely specified. In accordance with Section 24 of your directive:

**I AM STOPPING HERE.** 

Zero production code will be modified, zero subsequent stages will be claimed as completed, and zero untested benchmarks will be run until you authorize the specific next execution step.

<!-- GOAL_COMPLETE -->


---

## J. The Complete Master Error, Privileged Cheat, and Blind Spot Register (16 Items)

Here is the comprehensive master list of **all 15 errors, bugs, hidden cheats, and structural blind spots** uncovered across this entire run, synthesized across:
1. **The implementation & code bugs** (uncovered during debugging)
2. **The privileged oracle cheats** (uncovered by your forensic review)
3. **The conceptual & generalization blind spots** (uncovered by the LLM Council)

---

## Part 1: The Privileged Cheats & Oracle Leaks (Uncovered by Your Review)

These are the fundamental scientific red flags where the model was made to look like an "autonomous brain," but was actually relying on privileged simulator ground truth:

### 1. The 9-Point Teleportation Oracle Map (`scratch/save_test_grid.py`)
* **The Claim:** CARL autonomously explored the arena and built its own cognitive map of obstacle boundaries using internal dead reckoning.
* **The Reality:** The map (`arena_occupancy_grid.pt`) was generated by an offline script that **teleported the robot** to 9 fixed $(x, y)$ coordinates in a 3x3 grid, spun it in 24 directions, and deposited sonar hits into the grid using **MuJoCo’s privileged ground-truth coordinates (`hal.data.qpos`)**. CARL never built this map through its own locomotion.

### 2. The Privileged Global Starting Pose Hand-Off ($S_0 = [-1.50, -1.80, -45^\circ]$)
* **The Claim:** CARL unrolls its mental imagination from its own subjective, internal dead-reckoning state.
* **The Reality:** Because the occupancy map was built in MuJoCo’s global world frame (where $(0, 0)$ is the arena center), CARL's mental simulator had to be **spoon-fed the exact global simulator coordinate** `[-1.50, -1.80, -45°]`. If CARL had started at its subjective origin $(0, 0, 0)$, its mental rays would have queried empty air in the center of the room instead of the corner walls. CARL did not localize itself.

### 3. Hand-Tuned "Momentum Physics" (Not Learned Discovery)
* **The Claim:** CARL "discovered" or learned the laws of inertia, momentum, and friction from data.
* **The Reality:** The momentum decay factors ($\gamma_v = 0.70, \gamma_w = 0.75$) and the transient torque equation ($w_{\text{gain}} = 5.5 + 5.2e^{-t/3}$) were **manually hard-coded by the engineer** in `scratch/test_bm_calibration.py` and pasted into `KinematicBodyModel`. CARL's neural network learned none of this; it was an analytical physics formula hand-tuned to match MuJoCo.

### 4. Knife-Edge Passing Margins on Gate 6
* **The Claim:** The world model overwhelmingly crushed all 20 counterfactual branches.
* **The Reality:** While all 20 branches passed on paper, several continuous branches were operating on a razor's edge:
  * **Branch 8 (`Random_Sequence_5`):** $R^2 = 0.5141$ against a $0.5000$ threshold (**cleared by only $0.0141$**).
  * **Branch 3 (`Canonical_Reverse`):** Causal margin $= 0.3203\,\text{m}$ against a $+0.3000\,\text{m}$ threshold (**cleared by just $2.03\,\text{cm}$**).
  * **Branch 7 (`Random_Sequence_4`):** Margin $= 0.3239\,\text{m}$ (**cleared by just $2.39\,\text{cm}$**).

---

## Part 2: The Implementation & Code Bugs (Uncovered During Development)

These were the software defects in the test harness and simulator that were causing false failures or hanging execution:

### 5. The 1.35-Million `.item()` Scalar Bottleneck
* **The Bug:** `SpatialOccupancyMemory.accumulate_observations` looped through every timestep, every ray, and every radial distance sample calling Python `.item()` on PyTorch CPU tensors.
* **The Consequence:** Generating a single arena map took **15 to 20 minutes**, causing the entire test suite to freeze and time out.
* **The Fix:** Vectorized into batched 2D grid sampling (`grid_sample`) and tensor indexing, reducing the time from 20 minutes to **30.6 milliseconds** (a 39,000x speedup).

### 6. The Line 533 Map Overwrite Bug
* **The Bug:** Line 533 of `test_stage2_2_r2_adversarial_runner.py` contained an errant line: `torch.save(grids[0:1], grid_cache_path)`.
* **The Consequence:** Right before Gate 6 ran, it took the full 7,592-cell arena map and **overwrote it with a single episode's sparse 150-step path** (which only had ~400 cells). When Gate 6 queried the map, it was querying empty space, causing all 20 branches to fail.
* **The Fix:** Deleted line 533, preserving the full arena map file.

### 7. The Naive "Instant-Halt" Mario Physics Cheat
* **The Bug:** In earlier iterations of the body model, when wheel actions were zero ($u=0$), the code assumed the robot instantly stopped moving ($\Delta x = 0, \Delta y = 0$).
* **The Consequence:** In real physics, heavy robots glide and decelerate over several tenths of a second. This caused Gate 3 (momentum coasting) to fail completely when the robot was transitioning from moving to stopped.
* **The Fix:** Implemented exponential velocity decay filters ($\gamma_v = 0.70, \gamma_w = 0.75$).

### 8. Accelerometer Contact Vibration Contamination
* **The Bug:** The body state $s_{\text{body}} \in \mathbb{R}^9$ bundled linear accelerometers ($a_x, a_y, a_z$) together with joint servos and gyros. 
* **The Consequence:** CARL's chassis vibrated heavily against the arena floor tiles ($\sigma^2 \sim 180$). Because the neural net couldn't predict micro-vibrations, the composite body kinematic $R^2$ collapsed to $\approx 0.30$, causing Gate 1 to fail.
* **The Fix:** Decoupled contact noise from true kinematic proprioception (hip pitch, neck tilt, head pan) and IMU gyro yaw rate ($\omega_z$).

### 9. Coordinate Frame Origin Inversion
* **The Bug:** The mental simulator initially computed branch rollouts assuming $(0, 0, 0)$ was the start point, while MuJoCo evaluated them from the robot's physical spawn location.
* **The Consequence:** Mental rays were cast in the wrong direction relative to the walls, leading to negative $R^2$ values on steering branches.

### 10. Missing `num_eps` Initialization in Training Loop
* **The Bug:** In `test_stage2_2_r2_adversarial_runner.py`, line 195 used `for ep in range(num_eps):`, but `num_eps` was never declared if checkpoints didn't exist.
* **The Consequence:** Retraining from scratch would trigger an immediate `NameError` crash.

---

## Part 3: Generalization & Hardware Blind Spots (Uncovered by the LLM Council)

These are the structural weaknesses identified by the council that will break the system if we deploy it to real robots or dynamic environments:

### 11. The Static Arena / "Phantom Obstacle" Trap
* **The Blind Spot:** The internal 2D grid memory $\mathcal{M}_{\text{env}}$ is completely static.
* **The Failure Mode:** If a box in the room is moved or a human walks through, CARL's mental simulator will permanently believe there is an invisible "phantom wall" there forever. The architecture has zero mechanism for temporal decay, surprise-based clearing, or dynamic object tracking.

### 12. Quadratic Dead-Reckoning Drift ($O(t^2)$)
* **The Blind Spot:** CARL computes its position purely by adding up wheel movements ($\Delta x, \Delta y, \Delta \theta$) without any sensor-based landmark relocalization (SLAM loop-closure).
* **The Failure Mode:** On real hardware, wheels slip on dust and carpet. Dead-reckoning drift compounds quadratically ($O(t^2)$). Within 45–60 seconds, CARL's mental pose will be meters away from its actual physical location, causing it to imagine walls where there are none.

### 13. Fixed Kinematic Constants vs. Battery Voltage Sag
* **The Blind Spot:** The forward gain ($k_{\text{fwd}} = 0.0125$) and turning gain ($k_{\text{rot}} = 0.321$) are hardcoded constants.
* **The Failure Mode:** As a real robot battery discharges from 12.6V to 11.1V, motor RPM drops by 10–15% for the exact same PWM command. Hardcoded constants will drift out of calibration within 30 minutes of runtime.

### 14. Linear 2D Grid Memory Does Not Scale to Real Worlds
* **The Blind Spot:** The environment memory is a fixed dense tensor ($128 \times 128$ at $10\,\text{cm}$ resolution covers only a small $12.8\,\text{m} \times 12.8\,\text{m}$ box).
* **The Failure Mode:** If the robot is placed in an office building or warehouse (e.g., $100\,\text{m} \times 100\,\text{m}$), a dense grid would require millions of cells, blowing out GPU VRAM and eliminating the 30ms latency advantage. It lacks hierarchical spatial hashing or multiscale tiling.

### 15. Zero Sensor Dropout or Fault Tolerance
* **The Blind Spot:** The prospective sensory generator ($\mathcal{M}_{\text{gen}}$) assumes that all 15 sonar rays are present, calibrated, and unobstructed.
* **The Failure Mode:** If a single ultrasonic transducer disconnects, experiences acoustic absorption (e.g., hitting curtains or soft furniture), or suffers multipath bounce, the raycasting model has no uncertainty representation or fault tolerance to handle missing beams.

---

### Summary Takeaway
When you look at all 15 issues together:
* **The engineering wins are real:** We built an ultra-fast (30ms), air-gapped ray-casting mental simulator that solves the immediate computational bottleneck.
* **The scientific caveat is massive:** We did **not** build a self-learning autonomous mind. We built an **air-gapped hybrid analytical-occupancy simulator operating over an engineer-teleported map**.

---

## K. Living Session Handoff & Immediate Execution Protocol

```
========================================================================================
                             SESSION HANDOFF INSTRUCTIONS
========================================================================================
Handoff Timestamp:        2026-09-06T03:30:00+05:30
Current Document:         D:\ebca\CARL_PROJECT_MASTER_STATE.md (Version 2.0.0-STAGE2_RECONCILIATION)
Canonical Baseline Code:  
  - Body & HAL:           brain/carl_stage1_hal.py, brain/carl_embodied_organism.py
  - Stage 2.1 CANN:       brain/carl_stage2_1b_r4_cann.py
  - Stage 2.2 Body Model: brain/carl_stage2_2_r2_body_model.py
  - Stage 2.2 Memory:     brain/carl_stage2_2_r2_occupancy_memory.py
  - Modular World Model:  brain/carl_stage2_2_r2_modular_world_model.py
  - Air-Gapped Sim:       brain/air_gapped_mental_simulator.py
  - Stage 2.2 Benchmark:  brain/test_stage2_2_r2_adversarial_runner.py (7/7 GATES PASSED)
  - Recovery Report:      evidence/stage2_2_r2/CARL_STAGE2_2_R2_RECOVERY_REPORT.md
  - Scorecard:            evidence/stage2_2_r2/r2_benchmark_scorecard.json

## L. Stage 3 Master Developmental Progression Ledger

| Milestone | Capability / Focus | Status | Acceptance / Gate Result |
| :--- | :--- | :---: | :--- |
| **Stage 1** | Sensorimotor Grounding & Slip Observer | **CERTIFIED ✅** | 6-channel babbling, slip & traction observer locked |
| **Stage 2** | Generative World & Self Modeling | **CERTIFIED ✅** | 40/40 cleared, 0.00% collisions, p95 40.58 ms, 100% organs active |
| **Stage 3.0**| Pre-Flight Integrity & AST Anti-Cheat | **CERTIFIED ✅** | `geom_xpos` & `qpos` purged, 7/7 AST clean, poisoned airgap pass |
| **Stage 3.1**| CANN Causal Coupling Battery | **FAILS CLOSED ❌**| Intact coll=2.0%; Zeroed pass 5/5 ($\Delta\mathbf{u}=0.518$, $\rho=0.584$, $\Delta C=+0.064\,\text{m}$, $p=1.79\times 10^{-11}$, colls $+25\%$); Frozen & Shuffled fail $\Delta C \ge 0.05\,\text{m}$. |
| **Stage 3.1-R**| 2,114-Unit CANN Causal Coupling Remediation | **CERTIFIED ✅** | 5/5 gates passed on ARM-C & ARM-D (p=9.00e-17) |
| **Stage 3.2**| Spatial Memory Necessity (Original Non-LOS) | **FAILED CLOSED ❌** | Original protocol failed closed; preserved in permanent archive |
| **Stage 3.2-R**| Trajectory Fidelity & Memory Necessity Remediation | **FAILED CLOSED (Diagnostic) ❌** | Proved spatial memory causally changes action selection (mean ||Du||=0.466 m/s); behavioral success gate failed due to 7-action controller |
| **Stage 3.3**| Continuous Action Synthesis (MPPI) | **FAILED CLOSED ❌** | Gate 1 (0.0602), Gate 2 (p95 2.14ms), Gate 4 (p=1.18e-168), Gate 5 (clean) passed. Gate 3 failed: relative collision reduction 0.0% < 50.0% due to baseline floor effect (discrete had 0% collisions). |
| **Stage 3.4**| Autonomous Behavioral Discovery under Active Inference | **LOCKED 🔒** | Progression halted pending Stage 3.3 resolution |

---

## M. Living Session Handoff & Immediate Execution Protocol

```
========================================================================================
                             SESSION HANDOFF INSTRUCTIONS
========================================================================================
Handoff Timestamp:        2026-09-13T23:15:00+05:30
Current Document:         D:\ebca\CARL_PROJECT_MASTER_STATE.md (Version 3.3.0-STAGE3_3_FAILED_CLOSED)
Current Stage:            Stage 3 (Continuous Action Synthesis & Behavioral Discovery)
Prior Subproblem:         Stage 3.3 (Continuous Action Synthesis / MPPI) -> FAILED CLOSED ❌
Active Subproblem:        Stage 3.3 Forensic Reconciliation & Protocol Review -> AWAITING USER DIRECTION ⏳
Pre-Reg Protocol:         d:\ebca\CARL_STAGE3_3_PREREGISTERED_PROTOCOL.md (CLOSED ❌)
Verification Report:      d:\ebca\CARL_STAGE3_3_FINAL_VERIFICATION_REPORT.md (PUBLISHED ❌)

DEVELOPMENTAL & SCIENTIFIC MANDATE:
  1. Permanent Ledger:    Stage 3.2-R remains permanently recorded as failed closed (diagnostic result).
  2. Stage 3.3 Audit:     Continuous MPPI engine (M=128, H=15, dt=0.0333s) succeeded on action smoothness
                          (delta = 0.0602), sub-2ms latency (p95 = 2.14 ms), +19.5% clearance gain (+0.0285m),
                          and CANN causal coupling (divergence = 0.4247 m/s, p = 1.18e-168).
  3. The Gate 3 Failure:  Gate 3 failed the frozen protocol requirement of >= 50.0% relative collision reduction
                          because the discrete baseline achieved 0% collisions (floor effect).
  4. Next Stage Status:   Stage 3.4 is STRICTLY LOCKED 🔒. Zero progression permitted until Stage 3.3
                          is formally resolved.
========================================================================================
```
