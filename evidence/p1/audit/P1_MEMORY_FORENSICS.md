# P1 Forensic Investigation: Episodic Memory Integrity & Write Provenance

```
========================================================================================
                      FORENSIC AUDIT: EPISODIC MEMORY INTEGRITY
========================================================================================
Document Path:       D:\ebca\evidence\p1\audit\P1_MEMORY_FORENSICS.md
Audit Date:          August 22, 2026
Audit Scope:         Verification of HDC memory writes, query density, Plot 5 flatness,
                     and the origin of the ">700 memory episodes" claim.
Status:              ROOT CAUSE IDENTIFIED & SCIENTIFICALLY PROVEN
========================================================================================
```

---

## 1. The Discrepancy

| Evidence Source | Observed Memory Value | Status |
| :--- | :--- | :--- |
| **525 Raw Telemetry CSVs** (`evidence/p1/telemetry/*.csv`) | `episodes_in_memory = 0` across all 525 files | **GROUND TRUTH** |
| **Plot 5** (`evidence/p1/plots/05_memory_usage.png`) | Flat curve at `0` episodes throughout | **MATCHES GROUND TRUTH** |
| **Rendered Videos** (`evidence/p1/videos/*.mp4`) | HUD text: `"Memory: 0 eps"` | **MATCHES GROUND TRUTH** |
| **Master MD Report / Receipt** | Claims `>700 autobiographical episodes` | **CROSS-CONTAMINATED CLAIM** |

---

## 2. Root Cause Analysis

### A. Code-Level Memory Trigger in P0/P1 Cognitive Engine
In `brain/carl_autonomous_agent.py` (lines 258–270), episodic memory writes are governed by:
```python
# 11. Store Autobiographical Episode on Collision or Food Absorption
if self.enable_memory:
  if collision_occurred:
    self.memory.store_episode(
        sensory.pos_x,
        sensory.pos_y,
        h_info["dominant_need"],
        best_action_name,
        -1.0,
        hazard=True,
        pred_err=pred_error,
        tick=self.tick,
    )
  elif food_absorbed:
    self.memory.store_episode(
        sensory.pos_x,
        sensory.pos_y,
        h_info["dominant_need"],
        best_action_name,
        +1.0,
        hazard=False,
        pred_err=pred_error,
        tick=self.tick,
    )
```
1. `collision_occurred` is derived strictly from `sensory.has_body_collision` (MuJoCo physical geom contact).
2. Because CARL's safety veto layer ([`brain/carl_endogenous_agency.py`](file:///d:/ebca/brain/carl_endogenous_agency.py)) successfully intervened whenever front clearance dropped below $0.35\text{ m}$, **the physical chassis never touched the obstacle barriers ($0\text{ collisions}$).**
3. Because `food_absorbed` was `False` due to the 300-tick timeout, **zero autobiographical episodes were written to the HDC memory matrix during the official 525-run campaign.**

### B. Origin of the ">700 Memory Episodes" Claim
1. During post-campaign exploratory shell debugging (`task-118`), an ad-hoc test script was executed with an experiment-side near-miss memory injection:
   ```python
   if sensory.min_obstacle_dist < 0.32 or t.veto_asserted:
     agent.agent.memory.store_episode(...)
   ```
2. That separate exploratory test accumulated 778 memory episodes in 5 runs.
3. When drafting the markdown report, the author inadvertently referenced data from that ad-hoc exploratory script instead of the official 525-run campaign dataset.

---

## 3. Scientific Implications & Ablation Finding

1. **Why `FULL_P1` and `NO_MEMORY` Performed Identically in the 525-Run Campaign**:
   Because 0 memory writes occurred in `FULL_P1` under the strict `collision_occurred == True` trigger, the memory matrix $M$ remained at zero throughout both conditions. This explains why `FULL_P1` and `NO_MEMORY` have identical mean final distances ($2.0815\text{ m}$) and action distributions in the 525-run campaign.
2. **Scientific Integrity Assessment**:
   The flat line in Plot 5 is **truthful and accurate** with respect to the official 525 raw CSV dataset.
   The claim of `>700 memory episodes` in `CARL_P1_MASTER_REPORT.md` is **formally retracted as a documentation cross-contamination**.
