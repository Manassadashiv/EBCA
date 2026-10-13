# CARL-DX — P0-01 FORENSIC DISCREPANCY INVESTIGATION
**Forensic Analysis of Runs D1 and G2: Active Recovery Termination & Scoring Engine Flaw**

```
===================================================================================================
                                   DISCREPANCY AUDIT METADATA
===================================================================================================
Investigation Date:       August 17, 2026
Target Runs Investigated: P0_D1_S42_HISTORICAL_TURN_TRAP_300T
                          P0_G2_S42_CORRIDOR_NARROW_250T
Canonical Specification:  D:\ebca\CARL_CONTROL_COGNITIVE_SPEC.md (Section 11: Stuck Recovery)
Scoring Engine Audited:   D:\ebca\tools\p0_independent_scorer.py
Evidence Sources:         Raw CSV Telemetry, Decoded MP4 Videos, Run Summaries
Final Verdict:            BASELINE VALIDATION CRITERIA FLAWED
===================================================================================================
```

---

## 1. QUESTION-BY-QUESTION FORENSIC FINDINGS

### QUESTION 1: Why did D1 (`P0_D1_S42_HISTORICAL_TURN_TRAP_300T`) receive PASS?

| Parameter | Quantitative Value | Evidence Source |
| :--- | :--- | :--- |
| **Final Recovery State** | `recovery_active = True`, `recovery_tier = 1`, `recovery_phase = "BREAKOUT"`, `stuck_state = "STUCK_IDLE"` | Telemetry CSV row 299 |
| **Recovery Start Tick** | Tick `278` ($t = 9.257\text{s}$) | Telemetry CSV row 278 |
| **Recovery End Tick** | `None` (Did not terminate before 300-tick run cutoff) | Full CSV inspection |
| **Displacement from Origin** | $\Delta p_{\text{rec}} = 0.1091\text{m}$ (Origin: $[0.0651, 0.3851]$, Final: $[-0.0245, 0.3228]$) | Derived Euclidean metric |
| **Front Clearance at Cutoff**| $d_{\text{front}} = 0.4284\text{m}$ | Telemetry CSV row 299 |
| **Exact Recovery Criteria** | $\Delta p \ge 0.35\text{m} \land d_{\text{front}} > 0.65\text{m}$ | `carl_stuck_recovery.py:L246-L255` |
| **Was Criteria Satisfied?** | **NO** ($\Delta p = 0.1091\text{m} < 0.35\text{m}$ and $d_{\text{front}} = 0.4284\text{m} < 0.65\text{m}$) | Forensic comparison |
| **Exact Code Path for PASS** | `tools/p0_independent_scorer.py:L139`: `is_pass = (len(failures_detected) == 0) and (total_coll == 0)` | Scorer source line 139 |

**Forensic Explanation**: 
At tick 278, CARL encountered a high-confinement corner and entered recovery. By tick 299 (22 ticks later), CARL had completed Reverse (1 tick), Spin (6 ticks), and was 15 ticks into Forward Breakout (moving forward at $0.2611\text{m/s}$). The physical breakout was actively occurring but had not yet reached the $0.35\text{m}$ displacement threshold when the benchmark arbitrarily reached its 300-tick duration. Because zero collisions occurred and no explicit failure detector fired during those 22 ticks, the scoring engine blindly assigned `is_pass = True`.

---

### QUESTION 2: Why did G2 (`P0_G2_S42_CORRIDOR_NARROW_250T`) receive PASS?

| Parameter | Quantitative Value | Evidence Source |
| :--- | :--- | :--- |
| **Final Recovery State** | `recovery_active = True`, `recovery_tier = 1`, `stuck_state = "STUCK_CANDIDATE"`, `speed = 0.0348 m/s` | Telemetry CSV row 249 |
| **Recovery Start Tick** | Tick `103` ($t = 3.430\text{s}$) | Telemetry CSV row 103 |
| **Recovery End Tick** | `None` (Persisted for 147 ticks until tick 249) | Full CSV inspection |
| **Displacement from Origin** | $\Delta p_{\text{rec}} = 0.1092\text{m}$ (Origin: $[-0.2401, -0.0046]$, Final: $[-0.3454, 0.0245]$) | Derived Euclidean metric |
| **Front Clearance at Cutoff**| $d_{\text{front}} = 0.3079\text{m}$ | Telemetry CSV row 249 |
| **Exact Recovery Criteria** | $\Delta p \ge 0.35\text{m} \land d_{\text{front}} > 0.65\text{m}$ | `carl_stuck_recovery.py:L246-L255` |
| **Was Criteria Satisfied?** | **NO** (Trapped in recovery loop for $58.8\%$ of run) | Forensic comparison |
| **Exact Code Path for PASS** | `tools/p0_independent_scorer.py:L139`: `is_pass = (len(failures_detected) == 0) and (total_coll == 0)` | Scorer source line 139 |

**Forensic Explanation**:
In G2 (Narrow Corridor of width $0.75\text{m}$), CARL entered recovery at tick 103 and cycled through 9 recovery phase transitions (Reverse $\to$ Spin $\to$ Breakout $\to$ Reverse $\dots$). Because the corridor is physically only $0.75\text{m}$ wide (with robot width $0.24\text{m}$), clearance could never exceed $0.38\text{m}$, making the required $0.65\text{m}$ clearance threshold physically unreachable. The scoring engine assigned PASS because:
1. `total_coll == 0` (No contact was breached).
2. The limit-cycle and stall detectors explicitly ignored ticks where `recovery_active == 1` (`if not any(sub_rec)`).
3. The scorer contained **zero checks requiring recovery to terminate before the end of the run**.

---

### QUESTION 3: Is "No Failure Detector Trigger" Treated as Success?

**YES.** In `tools/p0_independent_scorer.py`, line 139:
```python
is_pass = (len(failures_detected) == 0) and (total_coll == 0)
```
The scoring system treats the simple absence of a triggered failure detector as full certification of PASS / SUCCESS.

---

### QUESTION 4: Audit of the Implemented Scoring Logic

| Evaluation Criterion | Required by P0 Spec? | Checked by Scorer? | Implementation Location |
| :--- | :---: | :---: | :--- |
| **A. Absence of Catastrophic Failure** | YES | **YES** | `p0_independent_scorer.py:L40-L130` |
| **B. Successful Task / Traverse Completion** | YES | **NO** | Not implemented |
| **C. Successful Recovery Prior to Run End** | YES | **NO** | Not implemented |
| **D. Minimum Net Displacement Threshold** | YES | **NO** | Logged only, not gated in `is_pass` |
| **E. Normal Post-Recovery Autonomous State** | YES | **NO** | Not implemented |

---

### QUESTION 5: Quantitative Comparison Table (D1 vs G2)

| Forensic Metric | D1 (`HISTORICAL_TURN_TRAP_300T`) | G2 (`CORRIDOR_NARROW_250T`) |
| :--- | :---: | :---: |
| **Total Time in Recovery** | 22 ticks ($0.73\text{s}$ / $7.3\%$) | **147 ticks ($4.90\text{s}$ / $58.8\%$)** |
| **Number of Recovery Actions** | 22 | 147 |
| **Recovery Phase Transitions** | 2 | **9** |
| **Minimum Clearance** | $0.3483\text{m}$ | $0.2126\text{m}$ |
| **Maximum Clearance During Recovery** | $0.4284\text{m}$ | $0.3785\text{m}$ |
| **Physical Displacement During Recovery** | $0.1091\text{m}$ | $0.1092\text{m}$ |
| **Total Net Displacement (Full Run)** | $0.3237\text{m}$ | $0.3465\text{m}$ |
| **Final State** | `recovery_active = True` | `recovery_active = True` |
| **Final Action** | `RECOVERY_FORWARD_BREAKOUT` | `RECOVERY_REVERSE_CURVE_RIGHT` |
| **Returned to Normal Policy Control?** | **NO (Cutoff in mid-breakout)** | **NO (Stuck in persistent recovery loop)** |

---

### QUESTION 6: Specification Compliance Comparison

- **P0 Specification Axiom**: *"Recovery success requires physical outcome, not merely timer expiration or command issuance."*
- **Discrepancy**: While the active source code in `carl_stuck_recovery.py` strictly enforces $\Delta p \ge 0.35\text{m} \land d_{\text{front}} > 0.65\text{m}$, the **independent scoring engine allowed runs to PASS simply because the benchmark timer ran out while recovery was still active**.

---

### QUESTION 7: Classification of the Discrepancy

- **Finding**: A benchmark can currently receive PASS even though CARL is still in an active recovery state at the end of the run.
- **Classification**: **`P0-01 BENCHMARK VALIDATION BUG (SCORING CRITERIA FLAW)`**.

---

### QUESTION 8: MP4 Video Cross-Verification

Decoded frame inspections of the uploaded videos confirm:
1. `P0_D1_S42_HISTORICAL_TURN_TRAP_300T.mp4` @ Frame 299:
   - HUD: `Action: RECOVERY_FORWARD_BREAKOUT`, `Speed: 0.26 m/s`, `Recovery: True (T1)`.
   - Visual: Robot is actively driving forward away from obstacle but run ends prematurely.
2. `P0_G2_S42_CORRIDOR_NARROW_250T.mp4` @ Frame 249:
   - HUD: `Action: RECOVERY_REVERSE_CURVE_RIGHT`, `Speed: 0.03 m/s`, `Recovery: True (T1)`.
   - Visual: Robot is oscillating back and forth in a $0.75\text{m}$ narrow corridor unable to achieve $>0.65\text{m}$ front clearance.

---

## 2. FINAL VERDICT & NEXT-STEP GOVERNANCE

```
===================================================================================================
                                      OFFICIAL AUDIT VERDICT
===================================================================================================
VERDICT: BASELINE VALIDATION CRITERIA FLAWED

REASON:
The scoring script `tools/p0_independent_scorer.py` defined PASS purely as the absence of detected
failures without verifying that:
1. `recovery_active == False` at run termination.
2. The organism successfully returned to normal autonomous policy control.
3. The benchmark duration is sufficient for active recovery cycles to conclude physically.

STATUS: P1 EMERGENCE STAGE REMAINS LOCKED UNTIL BENCHMARK SCORING IS HARDENED.
===================================================================================================
```
