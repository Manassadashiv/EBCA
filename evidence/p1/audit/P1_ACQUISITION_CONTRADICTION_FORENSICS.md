# P1 Forensic Investigation: Acquisition Contradiction Root-Cause Analysis

```
========================================================================================
                      FORENSIC AUDIT: ACQUISITION CONTRADICTION
========================================================================================
Document Path:       D:\ebca\evidence\p1\audit\P1_ACQUISITION_CONTRADICTION_FORENSICS.md
Audit Date:          August 22, 2026
Audit Scope:         Discrepancy between Raw CSV Telemetry (0.0%), Master JSON (0.0%),
                     and Master Markdown Report / Execution Receipt (66.7% / 350 runs).
Status:              ROOT CAUSE IDENTIFIED & EMPIRICALLY RECONCILED
========================================================================================
```

---

## 1. The Contradiction

A direct contradiction was detected between the primary empirical artifacts and the narrative documentation:

| Artifact | Reported Acquisitions | Reported Failures | Success Rate | Status |
| :--- | :--- | :--- | :--- | :--- |
| **525 Raw Telemetry CSVs** (`evidence/p1/telemetry/*.csv`) | **0** | **525** | **0.00%** | **AUTHORITATIVE (GROUND TRUTH)** |
| **Master Report JSON** (`CARL_P1_MASTER_REPORT.json`) | **0** | **525** | **0.00%** | **MATCHES GROUND TRUTH** |
| **Plot 6** (`evidence/p1/plots/06_target_distance.png`) | **0** (Min dist = 2.04m) | **525** | **0.00%** | **MATCHES GROUND TRUTH** |
| **6 Rendered Videos** (`evidence/p1/videos/*.mp4`) | **0** (All end at timeout) | 6 | **0.00%** | **MATCHES GROUND TRUTH** |
| **Master MD Report** (`CARL_P1_MASTER_REPORT.md`) | 350 | 175 | 66.7% | **DOCUMENTATION ERROR (HALLUCINATION)** |
| **Execution Receipt** (`P1_EXECUTION_RECEIPT.txt`) | 350 | 175 | 66.7% | **DOCUMENTATION ERROR (HALLUCINATION)** |

---

## 2. Root Cause Analysis

### A. Physical Mechanics Root Cause
1. **Target Distance**: The resource food beacon was positioned at $(x = 3.20\text{ m}, y = 0.00\text{ m})$ in `carl_p1_developmental_lab.py`.
2. **Episode Timeout**: The maximum duration per episode was fixed at `MAX_TICKS_PER_EPISODE = 300` ticks ($10.0\text{ s}$ at $30\text{ Hz}$).
3. **Kinematic Velocity Ceiling**: CARL's maximum cruising speed is $v_{\max} = 0.275\text{ m/s}$.
4. **Physical Upper Bound**: Even traveling in a perfect straight line with zero turns or decelerations, the maximum theoretical displacement in $10.0\text{ s}$ is:
   $$\Delta x_{\max} = 10.0\text{ s} \times 0.275\text{ m/s} = 2.75\text{ m}$$
5. **Acquisition Threshold**: Acquisition requires Euclidean distance $d < 0.30\text{ m}$. At $x = 2.75\text{ m}$, the remaining distance to $(3.20, 0.0)$ is $3.20 - 2.75 = 0.45\text{ m} > 0.30\text{ m}$.
6. **Empirical Outcome**: CARL advanced to $x \approx 1.16\text{ m}$ to $2.13\text{ m}$ during open baseline episodes before the 300-tick timer expired. Consequently, **every single one of the 525 episodes timed out before reaching the 0.30m acquisition sphere.**

### B. Documentation / Serialization Root Cause
1. `p1_experiment_runner.py` executed the 525 physical episodes, logged the raw CSV files, and serialized the machine-readable summary `CARL_P1_MASTER_REPORT.json` which accurately recorded:
   ```json
   "successful_episodes": 0,
   "failed_episodes": 525,
   "overall_success_rate": 0.0,
   "final_status": "NO_QUALIFYING_EMERGENT_BEHAVIOR"
   ```
2. When the human-readable markdown files (`CARL_P1_MASTER_REPORT.md` and `P1_EXECUTION_RECEIPT.txt`) were subsequently drafted, the narrative assumed that because CARL had traveled straight along Route A without collisions during Baseline (Episodes 1–5, 35 runs $\times$ 5 seeds = 175) and Revisit (Episodes 11–15, 35 runs $\times$ 5 seeds = 175), those 350 episodes represented "100% success".
3. The report author wrote `350 / 525 = 66.7%` in the markdown text without verifying that `target_acquired` in the raw CSVs was `False`.

---

## 3. Forensic Reconciliation Verdict

1. **The Raw Dataset is Untouched and Internally Consistent**: All 525 CSV files, the 6 rendered MP4 videos, all 10 matplotlib plots, and the machine-readable `CARL_P1_MASTER_REPORT.json` agree 100.0% that **0/525 runs achieved physical food absorption within 300 ticks.**
2. **The Documentation Contradiction is Categorized as**:
   > **TYPE B / C: DATASET VALID WITH DOCUMENTATION & ANALYSIS ERRORS**
3. **Corrected Official Acquisition Metric**:
   - Total Valid Episodes: **525**
   - Successful Physical Acquisitions: **0**
   - Timed-Out Episodes: **525 (100.0%)**
   - True Empirical Acquisition Rate: **0.00%**
