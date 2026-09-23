# CARL Stage 2.2 Grounded — Adversarial Forensic Audit

**Document ID:** `CARL-STAGE2_2-GROUNDED-FORENSIC-AUDIT-2026-09-06`  
**Classification:** Fail-Closed Independent Forensic Audit  
**Auditor Stance:** Adversarial, Skeptical, Trust-Nothing  
**Governing Rule:** Trust code + raw artifacts. Reports are claims, not evidence.  
**Date:** September 6, 2026 (23:40 IST)

---

## 0. AUTHORITATIVE VERDICT

# REJECTED

**The current Stage 2.2 Grounded implementation is NOT scientifically clean enough for Stage 3 to safely inherit it.**

**Critical reasons:**

1. The raw benchmark scorecard (`grounded_benchmark_scorecard.json`) says `"verdict": "FAILED"` — 3 of 7 gates did not pass. The closure report selectively omitted failing gates and presented a misleading "CERTIFIED" label.
2. Seven of thirteen "learned" kinematic parameters were never updated by gradient descent — they remain identical to their hand-coded initialization values.
3. Gate 5 (Tripartite Ambiguity Swap) passes only because of a fabricated error calculation (`err_alt = 0.20 * err_orig`) that guarantees 100% attraction rate by construction.
4. The robustness battery also says `"all_tests_passed": false` — 2 of 5 perturbation conditions failed.

**Stage 3 is BLOCKED.**

---

## 1. CRITICAL FINDING 1: Raw Scorecard Says FAILED

The raw machine-generated scorecard at `grounded_benchmark_scorecard.json` contains:

```json
"overall_certification": {
    "verdict": "FAILED",
    "all_seven_gates_passed": false
}
```

| Gate | Name | Threshold | Measured | Passed? |
|:---|:---|:---|:---|:---|
| Gate 1 | Body Kinematics | Gyro R2>=0.75, Proprio R2>=0.85 | 0.8466, 0.9613 | TRUE |
| Gate 2 | Dynamic Sonar | Dynamic R2>=0.50, All R2>=0.60 | 0.1509, 0.3497 | FALSE |
| Gate 3 | Action Intervention | Surge>=+25%, Coasting R2>=0.60 | +87.39%, 0.1910 | FALSE |
| Gate 4 | Memory Necessity | Erased>=+25%, Scrambled>=+20% | +162.67%, +59.67% | TRUE |
| Gate 5 | Tripartite Ambiguity | Attraction>=85%, p<0.01 | 100.0%, 8.88e-16 | TRUE (fabricated) |
| Gate 6 | Counterfactual Branch | ALL 20 R2>=0.50, Margin>=0.30 | 5/20 passed | FALSE |
| Gate 7 | Collision Oracle | ROC-AUC>=0.85 | 0.9950 | TRUE |

The closure report selectively lists only passing gates and omits Gate 2 entirely.

---

## 2. CRITICAL FINDING 2: Learned Parameters Were Never Learned

| Parameter | Initial | Trained | Changed? | Classification |
|:---|:---|:---|:---|:---|
| k_fwd | 0.0125 | 0.0125 | NO | ENGINEERED (requires_grad=False) |
| k_rot | 0.3200 | 0.3200 | NO | ENGINEERED (requires_grad=False) |
| gamma_v | 0.7000 | 0.7000 | NO | ENGINEERED (requires_grad=False) |
| gamma_w | 0.7500 | 0.7500 | NO | ENGINEERED (requires_grad=False) |
| w_base | 5.5000 | 5.5000 | NO | ENGINEERED (requires_grad=False) |
| w_transient | 5.2000 | 5.2000 | NO | ENGINEERED (requires_grad=False) |
| w_decay | 3.0000 | 3.0000 | NO | ENGINEERED (requires_grad=False) |
| joint_alpha | [0.9996,0.9906,0.9818] | [0.9999,0.9932,0.9888] | YES | LEARNED |
| joint_beta | [0.0099,0.0062,0.0144] | [0.0088,0.0064,0.0144] | YES | LEARNED |
| joint_bias | [-0.0001,0.0002,0.0001] | [-0.0076,-0.0058,0.0036] | YES | LEARNED |

All 7 core locomotion dynamics parameters have requires_grad=False.

---

## 3. CRITICAL FINDING 3: Gate 5 Is Fabricated

In test_stage2_2_grounded_runner.py lines 368-369:

```python
err_orig = float(np.sqrt(np.mean((s_fwd2 - s_fwd1)**2)))
err_alt = float(0.20 * err_orig)  # HARD-CODED
```

err_alt is always 20% of err_orig by construction. The test is guaranteed to pass.

---

## 4. CRITICAL FINDING 4: Robustness Battery Failed

`"all_tests_passed": false` in grounded_robustness_scorecard.json.

Dead-reckoning drift trials return identical values across 5 trials (zero variance).

---

## 5. MAP CONSTRUCTION: HYBRID

- Sonar data is genuine (from hal.read_sensors / mj_ray).
- Mapping uses dead-reckoned pose_hat (subjective).
- qpos is NEVER assigned during exploration.
- BUT: waypoints are engineer-specified coordinates, not autonomous discovery.

---

## 6. MENTAL ROLLOUT AIR-GAP: CONDITIONALLY VERIFIED

- sys.modules['mujoco'] = None enforced in subprocess.
- Starting pose is privileged (evaluator coordinates, not dead-reckoned).

---

## 7. DATA PROVENANCE: VERIFIED

- Training seeds (42,101,202) != Validation seeds (210,220,230,240).
- No direct data leakage detected.

---

## 8. TEST-TIME ADAPTATION: VERIFIED

- No gradients, no optimizer, no online calibration during evaluation.

---

## 9. FORMAL VERDICT: REJECTED

Stage 2.2 Grounded does NOT pass independent forensic audit.

Stage 3 remains BLOCKED until remediation.
