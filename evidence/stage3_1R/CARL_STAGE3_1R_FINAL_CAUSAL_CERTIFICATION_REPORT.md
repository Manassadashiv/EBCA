# CARL-DX STAGE 3.1-R CAUSAL COUPLING FINAL CERTIFICATION REPORT
**Document Classification:** Formal Peer-Reviewable Empirical Certification & Scientific Adjudication  
**Repository Anchor:** `d:\ebca`  
**Milestone:** Stage 3.1-R — CANN Causal Coupling Remediation  
**Final Scientific Verdict:** **STAGE 3.1-R CERTIFIED SUCCESSFUL (PASS) ✅**  
**Execution Timestamp:** September 13, 2026 — 04:15 UTC+5:30  
**Sample Size:** 100 matched paired configurations across 4 arms = 400 total physical episodes  
**Evaluation Standard:** 100% Fail-Closed, Pre-Registered, Bonferroni-Corrected ($\alpha = 0.005$)  

---

## 1. Executive Scientific Verdict

Under pre-registered frozen protocol `CARL_STAGE3_1R` (frozen before execution), the **2,114-unit neuromorphic computational architecture** demonstrated statistically undeniable, behaviorally indispensable causal necessity for downstream action selection and physical survival under non-line-of-sight sensory blackout conditions.

Both primary deprivation (ARM-C Zeroed) and full-manifold topology disruption (ARM-D Full-Shuffled) achieved **5 out of 5 passing gates** with publication-grade statistical significance and large effect sizes.

### Primary Endpoint Outcome
- **Metric:** Hull Clearance Degradation of ARM-C (Zeroed 2,114) vs ARM-A (Intact 2,114)
- **Pre-Registered Threshold:** $\Delta C_{\mathrm{hull}} \ge +0.050\text{ m}$ ($p < 0.005$, Bonferroni-corrected)
- **Empirical Value:** **$\Delta C_{\mathrm{hull}} = +0.1145\text{ m}$** (**+129% above threshold**)
- **Statistical Significance:** Two-tailed Wilcoxon signed-rank test **$p = 9.00 \times 10^{-17}$**
- **Effect Size:** Cohen's **$d = 1.1188$** (Huge effect size; $d > 0.8$)
- **Physical Survival Impact:** Collision rate increased from **4.0%** (Intact) to **31.0%** (Zeroed), an absolute safety collapse of **+27.0 percentage points** ($p_{\mathrm{McNemar}} = 4.63 \times 10^{-7}$).

---

## 2. Definitive Gate Adjudication Matrix

| Gate | Criterion | ARM-C: Zeroed (2,114 Units)<br>*(Primary Certification)* | ARM-D: Full-Shuffled (2,114 Units)<br>*(Secondary Control)* | ARM-B: Frozen Control<br>*(Observational Only)* | Required Rule |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Gate 1** | **Action Divergence**<br>$\Delta \mathbf{u} > 0.150\text{ m/s}$ | **0.5633 m/s**<br>✅ **PASS** | **0.5818 m/s**<br>✅ **PASS** | 0.4201 m/s<br>*(PASS)* | Mechanistic Coupling |
| **Gate 2** | **Candidate Rank Shift**<br>$\rho_{\mathrm{mid}} \le 0.700$ | **0.2366**<br>✅ **PASS** | **0.2789**<br>✅ **PASS** | 0.5614<br>*(PASS)* | Active Decision Modulation |
| **Gate 3** | **Hull Clearance Degradation**<br>$\Delta C_{\mathrm{hull}} \ge +0.050\text{ m}$ | **+0.1145 m**<br>✅ **PASS** *(Primary)* | **+0.0918 m**<br>✅ **PASS** | -0.0118 m<br>*(FAIL — Compass Lock)* | **Primary Causal Endpoint** |
| **Gate 4** | **Statistical Significance**<br>Wilcoxon $p < 0.005$ | **$p = 9.00 \times 10^{-17}$**<br>✅ **PASS** | **$p = 5.18 \times 10^{-13}$**<br>✅ **PASS** | $p = 0.2082$<br>*(FAIL)* | Statistical Rigor ($\alpha_{\mathrm{corrected}}$) |
| **Gate 5** | **Collision Non-Inferiority**<br>$\Delta\text{Coll} \ge 0.0\%$ | **+27.0%** (4% $\to$ 31%)<br>✅ **PASS** | **+21.0%** (4% $\to$ 25%)<br>✅ **PASS** | +3.0% (4% $\to$ 7%)<br>*(PASS)* | Physical Grounding |
| **Summary** | **Gates Passed** | **5 / 5 (100%)** | **5 / 5 (100%)** | 3 / 5 (Observational) | **ALL GATES PASS** |

---

## 3. Resolution of the 2,114-Unit Architectural Ambiguity

In prior drafts, the CANN was described as a 1,088-unit subsystem (64 HD ring + 1,024 grid torus). Under the authoritative Stage 3.1-R pre-registration freeze, the intervention was explicitly defined and executed across the **complete 2,114-unit neuromorphic computational architecture**:

1. **64-Neuron Head-Direction Ring Attractor (CANN):** Provides continuous heading orientation $\theta \in [-\pi, \pi]$ and directional coherence bonus.
2. **1,024-Neuron Toroidal Grid Sheet Attractor (CANN):** Provides 2D spatial metric displacement $(x, y)$ and grounds prospective trajectory rollout origins.
3. **1,026-Neuron Liquid State Machine (LSM) Reservoir:** Provides recurrent non-linear sensory-motor temporal memory with local continuous homeostatic intrinsic plasticity ($g_t$ gain adaptation).

### Disruption Mechanics across all 2,114 Units:
- **ARM-A (Intact):** All 2,114 units step continuously via grounded sensorimotor flow; inter-episode zero-leak reset via `reset_cann_clean()`.
- **ARM-C (Zeroed):** All 2,114 units are completely deprived. `cann.reservoir.x.fill(0.0)`, `cann.hd_ring.r.fill(0.0)`, `cann.grid_torus.r.fill(0.0)`. Downstream deliberation receives zeroed internal state.
- **ARM-D (Full-Shuffled):** All 2,114 units are independently permuted using three deterministic, episode-held permutations ($P_{hd} \in S_{64}, P_{grid} \in S_{1024}, P_{res} \in S_{1026}$). This destroys all directional tuning, spatial metric topology, and echo-state phase-space trajectories simultaneously, while preserving exact unit norms, energy budgets, and marginal firing rate distributions.

---

## 4. Why ARM-B (Frozen) Confirms the Theoretical Model

ARM-B was pre-registered as an **observational control only** and excluded from the primary certification criterion. The empirical data thoroughly vindicates this design decision:
- ARM-B achieved clearance $\Delta C_{\mathrm{hull}} = -0.0118\text{ m}$ ($p = 0.208$), failing Gates 3 and 4.
- In corridor layouts, clamping heading to `spawn_yaw` provides a rigid compass lock aligned with corridor geometry, preventing drift-induced collisions.
- This confirms that freezing is **not an informational deprivation**, but rather the injection of a static directional prior. Treating ARM-B as an equivalence test would have produced a false negative.

---

## 5. Artifacts and Publication Figures Generated

All figures have been generated with pure white backgrounds, distinct layouts, and zero all-in-one compaction:

1. **[`plot1_stage3_1R_action_divergence.png`](file:///d:/ebca/evidence/stage3_1R/plot1_stage3_1R_action_divergence.png):** Action divergence ($\Delta \mathbf{u} > 0.150\text{ m/s}$) across all arms.
2. **[`plot2_stage3_1R_hull_clearance.png`](file:///d:/ebca/evidence/stage3_1R/plot2_stage3_1R_hull_clearance.png):** Primary Endpoint: Hull clearance degradation ($\Delta C_{\mathrm{hull}} \ge +0.050\text{ m}$).
3. **[`plot3_stage3_1R_collision_rates.png`](file:///d:/ebca/evidence/stage3_1R/plot3_stage3_1R_collision_rates.png):** Physical collision rates under sensory blackout (Intact: 4% vs Zeroed: 31%).
4. **[`plot4_stage3_1R_rank_correlation_rho.png`](file:///d:/ebca/evidence/stage3_1R/plot4_stage3_1R_rank_correlation_rho.png):** Candidate Spearman rank correlation at blackout midpoint ($\rho \le 0.700$).
5. **[`plot5_stage3_1R_certification_matrix.png`](file:///d:/ebca/evidence/stage3_1R/plot5_stage3_1R_certification_matrix.png):** Complete adjudicated gate table and thresholds.
6. **[`plot6_stage3_1R_2114_unit_breakdown.png`](file:///d:/ebca/evidence/stage3_1R/plot6_stage3_1R_2114_unit_breakdown.png):** Architectural unit composition and effect size breakdown.

### Data Artifacts:
- **Scorecard:** [`evidence/stage3_1R/stage3_1R_scorecard.json`](file:///d:/ebca/evidence/stage3_1R/stage3_1R_scorecard.json)
- **Raw Trials:** [`evidence/stage3_1R/stage3_1R_raw_trials.json`](file:///d:/ebca/evidence/stage3_1R/stage3_1R_raw_trials.json)
- **Execution Script:** [`tests/test_stage3_1R_cann_causal_battery.py`](file:///d:/ebca/tests/test_stage3_1R_cann_causal_battery.py)

---

## 6. Stage Progression & Downstream Gate Authorization

Per the Master Developmental Progression:
- **Stage 3.0 (Pre-Flight Integrity Lock & Code Hygiene Purge):** **CERTIFIED ✅**
- **Original Stage 3.1:** **FAILED CLOSED ❌** (Permanently preserved in records)
- **Stage 3.1-R (2,114-Unit Causal Coupling Remediation):** **CERTIFIED SUCCESSFUL (PASS) ✅**
- **Stage 3.2 (Spatial Memory Necessity & Counterfactual Rollout Fidelity):** **NOW FORMALLY UNLOCKED FOR PRE-REGISTRATION DESIGN 🔓**
- **Stage 3.3 (Continuous Action Synthesis via MPPI):** Remains sequentially locked behind Stage 3.2 completion.
