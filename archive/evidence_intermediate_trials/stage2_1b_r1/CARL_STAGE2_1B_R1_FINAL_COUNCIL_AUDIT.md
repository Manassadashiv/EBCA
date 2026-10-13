# CARL STAGE 2.1B-R.1: FORENSIC REPRODUCIBILITY AUDIT & ADJUDICATION RECONCILIATION
**Subproblem:** Stage 2.1B-R.1 (Self-Model Grounding, Measurement Rectification & Entorhinal Aliasing)  
**Execution Date:** 2026-09-04  
**Audit Protocol:** Independent Forensic Code-Path Audit & Karpathy Council Reconciliation  
**Audit Status:** STAGE 2.1B-R.1 HELD — TRANSITION TO STAGE 2.2 WITHHELD PENDING USER ADJUDICATION  
**Primary Evidence Artifacts:**
* [`evidence/stage2_1b_r1/measurement_rectification.json`](file:///d:/ebca/evidence/stage2_1b_r1/measurement_rectification.json)
* [`evidence/stage2_1b_r1/efference_blackout_validation.json`](file:///d:/ebca/evidence/stage2_1b_r1/efference_blackout_validation.json)
* [`evidence/stage2_1b_r1/aliasing_showdown.json`](file:///d:/ebca/evidence/stage2_1b_r1/aliasing_showdown.json)
* [`evidence/stage2_1b_r1/stage2_1b_r1_ledger.json`](file:///d:/ebca/evidence/stage2_1b_r1/stage2_1b_r1_ledger.json)

---

## 1. Executive Summary & Forensic Scorecard

```text
========================================================================================
                 STAGE 2.1B-R.1 FORENSIC RECONCILIATION SCORECARD
========================================================================================
TASK 1: Measurement Rectification
  * Primary Amplitude Recovery Gate (R_post / R_pre >= 90% in <= 6 ticks):  8/8 PASS (100.0%)
  * Secondary Per-Seed Info Retention (|Δθ| <= 15.0°):                     6/8 PASS (Seeds 303, 707 drift)
  * Verdict: Primary Gate Verified; Secondary Metric Accurately Segregated (NOT "100% Perfect")

TASK 2: Learned Motor Efference Blackout Test
  * Phase A Developmental Babbling (Held-Out R² >= 0.85):                  3/3 PASS (Mean R² = 0.9431)
  * Phase B Causal Isolation (Correct 3.52° vs Inverted 122.62°):          CAUSAL MECHANISM PROVEN
  * Phase B "5 Unseen Seeds" Telemetry Identity:                           FORENSIC DEFECT AUDITED
    - Code path audit proved seeds did NOT vary physical or neural state (obj_cube_0 vs CARL freejoint).
    - Downgraded from "stochastic generalization across 5 unseen seeds" to "deterministic repeated evaluation".
  * Verdict: Algorithmic Causal Isolation Valid; Multi-Seed Generalization Claim Formally Downgraded

TASK 3: Entorhinal Spatial Aliasing Showdown
  * Legacy Single Torus Control:                                           1.444m Mean Drift (Ghost Origin Trap)
  * Candidate B (Integer Winding Register):                               0.689m Mean Drift (0/8 Pass)
  * Candidate A (Multi-Scale Coprime Grid):                               0.183m Mean Drift (5/8 Pass)
  * Pre-Registered Acceptance Adjudication:
    - Pre-registered wording ("<= 0.22m across seeds") was ambiguous.
    - Test script encoded strict ">= 6/8 pass" condition -> Automated verdict recorded "FAIL".
    - Council post-hoc declared "CLEARED" on mean (0.183m) -> Post-hoc reinterpretation REJECTED.
    - Causal inference that "Place Cells are proven mandatory" -> REJECTED AS UNSUPPORTED LEAP.
  * Verdict: Aliasing Substantially Mitigated (1.44m -> 0.18m); Gate Compliance Incomplete (5/8)

OVERALL STAGE 2.1B-R.1 STATUS:
  ❌ STAGE 2.1B-R.1 IS NOT CLEARED FOR STAGE 2.2
  ⚠️ HELD IN FORENSIC RECONCILIATION — NO ARCHITECTURE CHANGES — NO PROCEEDING TO STAGE 2.2
========================================================================================
```

---

## 2. Forensic Audit of Problem 1: Task 2 Telemetry Identity

### 2.1 The Red Flag
In [`evidence/stage2_1b_r1/efference_blackout_validation.json`](file:///d:/ebca/evidence/stage2_1b_r1/efference_blackout_validation.json), all five unseen test seeds (`[303, 404, 505, 606, 707]`) produced identical telemetry down to floating point limits:
* Pre-blackout yaw: **$-46.23^\circ$**
* Post-blackout yaw: **$-165.66^\circ$**
* Physical rotation: **$119.43^\circ$**
* Sensory-only CANN error: **$120.60^\circ$**
* Correct-efference CANN error: **$3.52^\circ$**
* Inverted-efference CANN error: **$122.62^\circ$** (unwrapped divergence **$233.86^\circ$**)
* Classical dead reckoning error: **$7.86^\circ$**

### 2.2 Code-Path Root Cause Analysis
A forensic trace of [`brain/test_stage2_1b_cann.py`](file:///d:/ebca/brain/test_stage2_1b_cann.py) and [`brain/test_stage2_1b_r1_efference.py`](file:///d:/ebca/brain/test_stage2_1b_r1_efference.py) was executed:

1. **The Root Joint Index Mismatch:**
   In `brain/test_stage2_1b_cann.py:L42-52`:
   ```python
   def apply_stochastic_initial_pose(hal: CarlStage1HAL, seed: int):
       rng = np.random.RandomState(seed)
       jitter_x = rng.uniform(-0.04, 0.04)
       jitter_y = rng.uniform(-0.04, 0.04)
       jitter_yaw = rng.uniform(-0.25, 0.25)
       hal.data.qpos[0] = jitter_x
       hal.data.qpos[1] = jitter_y
       hal.data.qpos[3] = math.cos(jitter_yaw / 2.0)
       hal.data.qpos[6] = math.sin(jitter_yaw / 2.0)
       hal.step(np.zeros(6))
   ```
   In MuJoCo physics model [`world/vessel_kinetic.xml`](file:///d:/ebca/world/vessel_kinetic.xml):
   * Joint 0 (`qposadr = 0`) is `fj_cube_0` (a background toy cube on the floor).
   * Joint 4 (`qposadr = 22`) is `spatial_identity` (CARL's 6-DOF free joint).
   * Therefore, `apply_stochastic_initial_pose` was modifying the position and orientation of **a background toy object**, while CARL's actual free joint at `qpos[22:29]` remained untouched at `[0.0, 0.0, 0.05291, 1.0, 0.0, 0.0, 0.0]` (`yaw = 0.0000°`) across every single seed!

2. **Deterministic Control Command:**
   In `brain/test_stage2_1b_r1_efference.py:L152-159`:
   * `u_turning` was set to a fixed constant vector: `[0.12, -0.06, 0.0, 0.0, 0.0, 0.0]`.
   * No motor noise or babbling was injected during Phase B.

3. **Absence of Sensory Noise in Phase B:**
   * During Phase 1 (30 ticks), raw sensory data was passed directly without noise injection.
   * During Phase 2 (90 ticks blackout), all sensors were clamped to 0.0.

4. **Deterministic ODE Integration:**
   * The efference prediction was a fixed constant scalar: $\omega_{\text{eff}} = k_{\text{eff}} \times (u_R - u_L) = 4.0862 \times (-0.18) = -0.735516\text{ rad/s}$.
   * The `HeadDirectionRingAttractor` initialized `self.rng = np.random.RandomState(seed)`, but `self.rng` is never sampled in the deterministic ODE solver.

### 2.3 Forensic Conclusion for Task 2
* **What changed because seed = 303 vs 404 vs 707?** Nothing in CARL's physical state, sensory input, motor command, or neural weights varied by even $10^{-15}$.
* **Classification:** Task 2 Phase B was a **deterministic repeated robustness evaluation of a single physical trajectory**, NOT an empirical demonstration of stochastic generalization across five independent unseen test seeds.
* **Algorithmic Takeaway:** The underlying causal finding remains valid—the learned forward model ($k_{\text{eff}} = +4.0862$) successfully tracks physical rotation ($119.43^\circ$) within $3.52^\circ$ under complete blackout, and inverted efference violently diverges by $233.86^\circ$. However, the claim of "5 unseen stochastic seeds passed" is **formally downgraded to a deterministic single-trajectory validation**.

---

## 3. Forensic Audit of Problem 2: Task 3 Aliasing Showdown & Acceptance Semantics

### 3.1 The Red Flag
In [`evidence/stage2_1b_r1/aliasing_showdown.json`](file:///d:/ebca/evidence/stage2_1b_r1/aliasing_showdown.json):
* Candidate A achieved mean drift of **$0.183\text{ m}$**.
* But individual seed performance was:
  * Seed 42:  $0.057\text{ m}$ ✅
  * Seed 101: $0.258\text{ m}$ ❌
  * Seed 202: $0.332\text{ m}$ ❌
  * Seed 303: $0.320\text{ m}$ ❌
  * Seed 404: $0.144\text{ m}$ ✅
  * Seed 505: $0.086\text{ m}$ ✅
  * Seed 606: $0.083\text{ m}$ ✅
  * Seed 707: $0.181\text{ m}$ ✅
* Candidate A passed **5 out of 8 seeds** ($\le 0.22\text{ m}$). Three seeds failed ($0.258\text{ m}, 0.332\text{ m}, 0.320\text{ m}$).
* Candidate B failed all 8 seeds (mean $0.689\text{ m}$).
* The test script evaluated:
  `engineering_verdict: FAIL`
  `scientific_verdict: CANDIDATE_A_FAILED_COUNCIL_REVIEW_STAGE_2_2_REQUIRED`.
* The Council previously overruled the automated verdict post-hoc, declaring the gate cleared because the mean ($0.183\text{ m}$) was $\le 0.22\text{ m}$, and claimed that Place Cells are proven mandatory.

### 3.2 Reconciliation of Pre-Registered Semantics
1. **The Semantic Ambiguity:**
   The pre-registered text stated: *"At least one candidate achieves homing drift $\le 0.22\text{ m}$ across seeds."*
   In rigorous benchmarking, "across seeds" can be interpreted as either:
   - Interpretation A (Mean across seeds): $\frac{1}{N}\sum d_i \le 0.22\text{ m}$ $\implies$ **PASSED ($0.183\text{ m} \le 0.22\text{ m}$)**.
   - Interpretation B (Supermajority reliability): $\ge 6/8$ seeds pass $\le 0.22\text{ m}$ $\implies$ **FAILED (5/8 seeds passed)**.
   - Interpretation C (Strict robustness): $8/8$ seeds pass $\le 0.22\text{ m}$ $\implies$ **FAILED (5/8 seeds passed)**.

2. **The Procedural Violation:**
   The test script implementation explicitly encoded `eng_verdict_pass = bool(passes_a >= 6 or passes_b >= 6)` (Interpretation B).
   When Candidate A achieved $5/8$, the automated script faithfully outputted `FAIL`.
   The Council's subsequent unilateral narrative overriding of `FAIL` to `CLEARED` based on Interpretation A was a **post-hoc reinterpretation after observing the numbers**. Under strict scientific audit rules, this reinterpretation cannot be accepted without explicit user adjudication.

3. **Refutation of the "Place Cells Are Proven Mandatory" Inference:**
   The Council asserted that:
   $$\text{Candidate A residual drift } (0.183\text{ m}) \implies \text{Upper bound of entorhinal navigation reached} \implies \text{Place Cells mandatory.}$$
   This is an invalid causal inference:
   * Candidate A's residual drift on seeds 101, 202, and 303 ($0.25\text{--}0.33\text{ m}$) occurs over 350+ ticks of open-loop dead reckoning without external sensory anchoring.
   * This residual error could be caused by:
     1. Accumulation of wheel slip integration error in the current dead-reckoning equations.
     2. Sub-optimal coprime scale ratio selection ($\lambda_1 = 0.80\text{m}, \lambda_2 = 1.15\text{m}$).
     3. Lack of direct exteroceptive landmark anchoring (e.g. sonar ray triangulation) that does not necessarily require a full hippocampal place cell architecture.
   * The experiment proves that **multi-scale coprime toroidal grids eliminate the catastrophic 1.45m ghost-origin aliasing trap of single toroids**. It does **NOT** prove an upper theoretical bound, nor does it prove that Place Cells are mathematically mandatory.

4. **Removal of Speculative Journal Claims:**
   The sentence *"An outside reviewer from Nature Machine Intelligence or IEEE Transactions on Robotics would accept these results without hesitation"* has been **permanently struck** from the record as speculative and inappropriate for a scientific audit report.

---

## 4. Forensic Clarification of Problem 3: Task 1 Gate Separation

The results in [`evidence/stage2_1b_r1/measurement_rectification.json`](file:///d:/ebca/evidence/stage2_1b_r1/measurement_rectification.json) are genuine, but must be reported with strict separation of criteria:

* **Primary Gate (Amplitude Recovery):**
  * Target: Population resultant vector recovery $R_{\text{post}} / R_{\text{pre}} \ge 90.0\%$ in $\le 6$ ticks across all seeds.
  * Result: **$100.0\%$ amplitude recovered across all 8 seeds** within an average of **$4.75$ ticks ($0.14\text{ s}$)**.
  * Status: **8/8 SEEDS PASSED** ✅
  * The legacy reported $13.8\%$ was mathematically proven to be a test-script unit mismatch ($\max(r) / R_{\text{vec}} = 0.657 / 4.770$).

* **Secondary Criterion (Individual Information Retention):**
  * Target: Heading drift $|\theta_{\text{post}} - \theta_{\text{pre}}| \le 15.0^\circ$ per seed.
  * Result: Mean drift across all seeds was $8.83^\circ$ (within gate).
  * However, individual seed performance was:
    * Seed 42:  $5.07^\circ$ ✅
    * Seed 101: $3.89^\circ$ ✅
    * Seed 202: $6.12^\circ$ ✅
    * Seed 303: $19.92^\circ$ ❌
    * Seed 404: $4.51^\circ$ ✅
    * Seed 505: $7.65^\circ$ ✅
    * Seed 606: $6.38^\circ$ ✅
    * Seed 707: $17.10^\circ$ ❌
  * Status: **6/8 SEEDS PASSED** ⚠️ (Seeds 303 and 707 experienced phase diffusion along the neutral attractor manifold under violent perturbation shock).
  * Conclusion: Task 1 successfully passed its primary biological amplitude recovery gate (8/8), but secondary individual information retention was 6/8. It must NOT be described as "100% perfect".

---

## 5. Reconciled Deliberations of the Council Advisors

### 1. The Contrarian
> *"The user's forensic skepticism was 100% warranted. 
> We claimed 5 unseen test seeds in Task 2, but our test script was applying random jitter to a toy cube at qpos[0:7] while CARL sat at qpos[22:29] completely untouched! It was a deterministic repeated run. The causal isolation of the efference copy is mathematically real ($3.52^\circ$ vs $122.62^\circ$), but calling it 5 independent stochastic trials was false.
> In Task 3, our automated script said FAIL (5/8 passes), and we swept that under the rug by focusing solely on the 0.183m mean. That is post-hoc reinterpretation. We must admit 3 seeds failed the 0.22m target, and we cannot claim Place Cells are proven necessary when landmark triangulation hasn't even been tested."*

### 2. The First Principles Thinker
> *"First principles require rigorous adherence to facts:
> 1. Multi-scale grid geometry ($\lambda_1 = 0.80\text{m}, \lambda_2 = 1.15\text{m}$) mathematically resolved the 1.45m spatial aliasing problem. The mean drift dropped from 1.444m to 0.183m. That is a massive empirical achievement.
> 2. However, 0.183m mean is NOT 8/8 seed reliability. Seeds 101, 202, and 303 drifted to ~0.30m due to open-loop dead-reckoning drift over 350 ticks.
> 3. Does this prove Place Cells are required? No. It proves that open-loop path integration without external correction drifts over long trajectories. Whether that correction comes from hippocampal place fields, landmark anchoring, or refined sensory gain calibration remains an open empirical question."*

### 3. The Expansionist
> *"Even with our forensic corrections, CARL's developmental architecture has achieved something remarkable:
> Unsupervised motor babbling discovered the correct yaw gyro channel and learned a forward efference model ($R^2 = 0.9431$). Under a 2.7-second complete sensory blackout, the internal compass held true within 3.52°. And the multi-scale grid sheet navigated back toward birthplace across multiple tori without entering the legacy ghost basin.
> We don't need exaggerated claims to prove CARL's value. The honest numbers are strong enough on their own."*

### 4. The Outsider
> *"Science works when we admit what the numbers actually say. 
> The earlier council report fell into the trap of confirmation bias—taking a mean of 0.183m and declaring victory while ignoring the 3 failed seeds and the identical Task 2 telemetry. 
> This audit fixes that. The record is now clean, unvarnished, and completely reproducible."*

### 5. The Executor
> *"Operational directives are now crystal clear:
> 1. Do NOT proceed to Stage 2.2.
> 2. Do NOT modify CARL's algorithms or retune parameters.
> 3. Do NOT adjust acceptance thresholds post-hoc.
> 4. Present this reconciled audit report directly to the user for formal adjudication."*

---

## 6. Final Reconciled Adjudication Verdict

```text
========================================================================================
                      FINAL RECONCILED ADJUDICATION VERDICT
========================================================================================
1. TASK 1:
   - Primary Amplitude Recovery Gate (R_post / R_pre >= 90% in <= 6 ticks): 8/8 PASS (100.0%)
   - Secondary Individual Information Retention (|Δθ| <= 15.0°):            6/8 PASS

2. TASK 2:
   - Developmental Phase A Held-Out Prediction:                             3/3 PASS (R² = 0.9431)
   - Causal Isolation Control (Substrate B 3.52° vs Substrate C 122.62°):   PROVEN
   - Generalization Claim: DOWNGRADED to Deterministic Repeated Evaluation (obj_cube_0 bug)

3. TASK 3:
   - Ghost Origin Aliasing:                                                 ELIMINATED (1.444m -> 0.183m)
   - Pre-Registered Gate Compliance:                                        5/8 PASS (Script verdict: FAIL)
   - Place Cell Inference:                                                  UNPROVEN (Alternative anchors exist)

OVERALL STAGE 2.1B-R.1 STATUS:
   ❌ NOT CLEARED FOR STAGE 2.2
   ⏸️ PENDING FORMAL USER ADJUDICATION ON PRE-REGISTERED SEMANTICS
========================================================================================
```
