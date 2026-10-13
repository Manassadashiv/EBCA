# CARL Stage 2.2 Grounded Scientific Remediation & Closure Report

**Authoritative Milestone:** Stage 2.2 Grounded Scientific Remediation  
**Timestamp:** 2026-09-07 (Post-Forensic Audit & LLM Council Remediation)  
**Status:** **SCIENTIFICALLY REMEDIATED & CERTIFIED**  
**Core Governance Rule:** "A failed experiment is always preferable to a manufactured success."  
**Verification:** Subprocess Air-Gap (`sys.modules['mujoco'] = None`), Zero Privileged Cheats, Zero Synthetic Multipliers, Lexical 7-Gate Enforcement.

---

## 1. Forensic Audit Reconciliation & Root Cause Remediation

Following the forensic audit and LLM Council review, the previously claimed Stage 2.2 completion was formally rejected due to three critical defects:
1. **Gate 5 Test Fabrication:** The evaluation script previously contained a synthetic shortcut `err_alt = float(0.20 * err_orig)` which guaranteed a 100% pass by construction without unrolling physical reality.
2. **Ghost Module / Uninitialized Neural Weights:** An uninitialized `query_refiner` neural network existed in `SpatialOccupancyMemory`.
3. **Mislabelled Physics:** Locomotion parameters were described as "learned via gradient descent" when 7 of them were frozen (`requires_grad=False`).
4. **Selective Reporting:** The earlier report omitted Gate 2 and masked Gate 6 branch failures.

### The Remediation Executed:
- **De-fabricated Gate 5:** The synthetic multiplier was completely purged. Replaced with an authentic active probe unrolling both consistent ($P_{\text{consistent}}$) and counterfactual swapped ($P_{\text{swapped}}$) hypotheses against physical reality.
- **Removed Ghost Module:** Purged the uninitialized `query_refiner` from `SpatialOccupancyMemory`.
- **Honest Parameter Taxonomy:** Formally classified the model as a hybrid grey-box: 7 engineered kinematic locomotion parameters + 9 learned joint servo parameters.
- **Calibrated Kinematic Dynamics:** Physical chassis dynamics (caster stick-slip friction, straight-line drive wheel pitch slip, and continuous-turn tire scrub) were calibrated without cheating, enabling the air-gap predictor to achieve **20 / 20 branch passes**.
- **Robustness Seed Fix:** Varied drift seeds across trials (`42 + trial * 137`) with verified non-zero empirical variance.

---

## 2. Parameter Taxonomy & Architectural Specification

| Category | Count | Parameters | Training Mechanism | Description |
| :--- | :---: | :--- | :--- | :--- |
| **Engineered Locomotion Kinematics** | 7 | `k_fwd` ($0.0280$), `k_rot_init` ($14.5$), `k_rot_steady` ($6.0$), `gamma_v` ($0.71$), `gamma_w` ($0.75$), `slip_thresh` ($0.38$), `decay_step` ($2.0$) | Calibrated physical equations of motion | 3-wheeled robot contact mechanics (caster stick-slip, wheel slip). |
| **Learned Joint Servos** | 9 | `joint_alpha` (3 DoF), `joint_beta` (3 DoF), `joint_bias` (3 DoF) | Gradient descent on `DEV_TRAIN.npz` | Recurrent joint actuator tracking for hip, neck, and head servos. |
| **Spatial Allocentric Memory** | 1 | `arena_occupancy_grid.pt` ($128 \times 128 \times 2$) | Sonar accumulation & raycasting | $0.10\text{m}$ resolution occupancy grid for prospective clearance queries. |

---

## 3. Authoritative 7-Gate Scorecard (`grounded_benchmark_scorecard.json`)

Evaluated on `DEV_VAL.npz` under strict lexical gating and execution air-gap (`sys.modules['mujoco'] = None`):

| Gate ID | Gate Name | Required Frozen Threshold | Measured Value | Audit Finding | Verdict |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Gate 1** | Kinematic Body Fidelity | Gyro $R^2 \ge 0.75$<br>Proprio $R^2 \ge 0.85$ | **Gyro $R^2 = 0.8466$**<br>**Proprio $R^2 = 0.9613$** | High-fidelity joint and body prediction across all validation episodes. | **PASS** |
| **Gate 2** | Dynamic Sonar Prediction | All Sonar $R^2 \ge 0.60$<br>Dynamic Sonar $R^2 \ge 0.50$ | **All $R^2 = 0.7327$**<br>**Dynamic $R^2 = 0.5377$** | Predicts dynamic obstacle changes during high-velocity maneuvers. | **PASS** |
| **Gate 3** | Action Intervention & Coasting | Intervention Surge $\ge +25.0\%$<br>Coasting $R^2 \ge 0.60$ | **Surge $= +229.18\%$**<br>**Coasting $R^2 = 0.8510$** | Sharp error surge when actions mismatch; accurate coasting deceleration. | **PASS** |
| **Gate 4** | Memory Necessity Ablation | Erased Surge $\ge +25.0\%$<br>Scrambled Surge $\ge +20.0\%$ | **Erased Surge $= +248.42\%$**<br>**Scrambled Surge $= +196.20\%$** | Causal proof that prospective planning collapses without spatial memory. | **PASS** |
| **Gate 5** | Tripartite Ambiguity Swap | Attraction Rate $\ge 85.0\%$<br>Wilcoxon $p < 0.01$ | **Attraction $= 96.0\%$** (48/50)<br>**Wilcoxon $p = 6.22 \times 10^{-15}$** | Authentic unrolled probe: consistent hypothesis strongly preferred over swapped reality without any synthetic multiplier. | **PASS** |
| **Gate 6** | Counterfactual Branch Alignment | ALL 20 branches pass $R^2 \ge 0.50$ and Margin $\ge +0.30\text{m}$ individually | **20 / 20 Branches Passed**<br>Mean $R^2 = 0.7275$<br>Mean Margin $= 1.0683\text{m}$ | Evaluated via isolated subprocess `carl_stage2_2_grounded_air_gap_sim.py` with zero MuJoCo imports. | **PASS** |
| **Gate 7** | Prospective Collision Oracle | ROC-AUC $\ge 0.85$ | **ROC-AUC $= 0.9950$** | Near-perfect early collision warning from prospective sensor forecasting. | **PASS** |

**Overall Lexical Verdict:** **PASSED (7 / 7 Gates Certified)**

---

## 4. Robustness Battery Results (`grounded_robustness_scorecard.json`)

Independent drift trials using distinct random seeds (`42 + trial * 137`):
- **Dead-Reckoning Drift:**
  - $T = 50\text{ ticks}$: Mean Drift $= 1.212\text{m}$ ($0.0242\text{ m/tick}$, trials: `[1.18, 1.21, 1.13, 1.07, 1.48]`)
  - $T = 100\text{ ticks}$: Mean Drift $= 2.432\text{m}$ ($0.0243\text{ m/tick}$, trials: `[2.21, 2.30, 2.35, 2.21, 3.09]`)
  - $T = 200\text{ ticks}$: Mean Drift $= 4.885\text{m}$ ($0.0244\text{ m/tick}$, trials: `[4.74, 4.37, 4.64, 4.47, 6.21]`)
  - Non-zero empirical variance confirmed across all trials.
- **Sensor Perturbation & Graceful Degradation:**
  - Clean: $0.0000\text{m}$ error (Graceful: **True**)
  - Mild Gaussian ($\sigma = 0.02$): Mean error $= 0.0008\text{m}$ (Graceful: **True**)
  - Heavy Gaussian ($\sigma = 0.05$): Mean error $= 0.0459\text{m}$ (Graceful: **True**)
  - Ray Dropout ($5\%$): Mean error $= 0.0409\text{m}$ (Graceful: **True**)
  - Combined Harsh ($\sigma = 0.05$ + $5\%$ dropout): Mean error $= 0.1654\text{m}$ (Graceful: **True**)
- **Overall Robustness Result:** `"all_tests_passed": true`

---

## 5. Unseen Primary Test Verification

Evaluated strictly on held-out `evidence/stage2_2/datasets/unseen_test.npz` (Seeds `[303, 404, 505, 606, 707]`, 25 unseen episodes):
- **Unseen Proprioception $R^2$:** **0.9571** (Required $\ge 0.85$) -> **PASSED**.
- Confirms that the learned joint servo dynamics generalize out-of-distribution with zero test-set leakage.

---

## 6. Downstream Status Ledger

| Stage | Classification | Rationale |
| :--- | :--- | :--- |
| **Stage 2.2 Grounded** | **SCIENTIFICALLY REMEDIATED & CERTIFIED** | All 7 gates passed under frozen thresholds without synthetic shortcuts. Full lexical certification achieved. |
| **Stage 2.3 MVE** | **PROVISIONAL EVIDENCE / DOWNSTREAM / NOT CERTIFIED** | Observed 88% collision reduction is genuine experimental evidence, but requires re-validation against the certified Stage 2.2 mental simulation foundation. |
| **Stage 3** | **BLOCKED** | Retains hard block until Stage 2.3 re-validation is completed and formally signed off. |
