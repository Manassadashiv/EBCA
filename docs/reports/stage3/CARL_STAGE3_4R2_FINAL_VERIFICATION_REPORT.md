# CARL-DX STAGE 3.4-R2 FINAL SCIENTIFIC VERIFICATION REPORT
**Authoritative Forensic Remediation Report: Connected Macro-Frontier Representation & Dimensionless Active Inference**

```
========================================================================================
                                REPORT CONTROL & METADATA
========================================================================================
Milestone:              Stage 3.4-R2 — Frontier Representation & Normalization Remediation
Protocol ID:            CARL-STAGE3-4R2-ACTIVE-INF-REMED-2026-09-14-v1
Document Path:          D:\ebca\CARL_STAGE3_4R2_FINAL_VERIFICATION_REPORT.md
Scorecard Path:         D:\ebca\evidence\stage3_4R2\stage3_4R2_scorecard.json
Raw Trials Path:        D:\ebca\evidence\stage3_4R2\stage3_4R2_raw_trials.json
Pre-Flight Diagnostic:  D:\ebca\evidence\stage3_4R2\stage3_4R2_preflight_diagnostic.json
Total Workload:         210 Physical Episodes (10 Diagnostic + 200 Certification)
Certification Sample:   50 Matched Configurations x 4 Arms = 200 Physical Episodes
Evaluation Standard:    Fail-Closed Pre-Registration (Zero Compensatory Scoring)
Adjudication Engine:    Exact One-Sided McNemar Test (alpha = 0.001) + Contact Manifolds
Final Milestone Status: FAILED CLOSED ❌ (Permanent Scientific Record)
Active Stage Boundary:  Stage 3.5 Remains Strictly LOCKED 🔒
========================================================================================
```

---

## 1. Executive Summary & Forensic Adjudication

Under explicit user authorization and strictly governed by the frozen pre-registered protocol [`CARL_STAGE3_4R2_PREREGISTERED_PROTOCOL.md`](file:///d:/ebca/CARL_STAGE3_4R2_PREREGISTERED_PROTOCOL.md), Stage 3.4-R2 executed the complete 210-episode physical evaluation:
1. **Pre-Flight Diagnostic Phase (10 Frozen Non-Binding Trials)**: Evaluated ARM-A on Environment 1 (1.30m Turning Bay) recording an escape rate of 0.0% (0/10), collision rate of 10.0% (1/10), stall rate of 90.0% (9/10), and mean cognitive latency of 6.10 ms.
2. **Authoritative Certification Phase (200 Physical Episodes)**: Evaluated 50 matched configurations across 4 strictly invariant experimental arms under fixed pre-registered seeds `[5001, 5002, 5003, 5004, 5005]`.

### The 5 Pre-Registered Acceptance Gates

| Gate ID | Gate Name | Pre-Registered Requirement | Empirical Measurement | Verdict |
| :--- | :--- | :--- | :--- | :---: |
| **Gate 1** | **Autonomous Task Completion & Collision Ceiling** | ARM-A Only ($N=50$ configs):<br>$\text{Escape} \ge 80.0\%$ (40/50)<br>$\text{Collision} \le 10.0\%$ (5/50) | $\text{Escape Rate} = 0.0\%$ (0/50)<br>$\text{Collision Rate} = 28.0\%$ (14/50)<br>$\text{Stalls / Timeouts} = 72.0\%$ (36/50) | **FAIL ❌** |
| **Gate 2** | **Complete Emergent Maneuver Verification** | ARM-A Only ($N=50$ configs):<br>$\ge 75.0\%$ (38/50) complete composite sequence:<br>Reversal $\to$ Pivot $\to$ Corridor $\to$ Egress | $\text{Complete Sequence Rate} = 0.0\%$ (0/50)<br>(Reversals & pivots occurred, but stalled before corridor entry) | **FAIL ❌** |
| **Gate 3** | **Epistemic-Objective Causal Necessity** | Environment 2 ($N=30$ pairs):<br>$\Delta\text{Escape} \ge 40.0\%$ AND $p < 0.001$<br>Pooled ($N=50$ pairs):<br>$\Delta\text{Escape} \ge 35.0\%$ AND $p < 0.001$ | Env 2: $\Delta = 0.0\%$, exact McNemar $p = 1.0$<br>($b=0, c=0$)<br>Pooled: $\Delta = 0.0\%$, exact McNemar $p = 1.0$<br>($b=0, c=0$) | **FAIL ❌** |
| **Gate 4** | **Real-Time Cognitive Cycle Latency Budget** | $\text{Mean Latency} \le 20.0\text{ ms}$<br>$\text{p95 Latency} \le 45.0\text{ ms}$<br>($N \ge 1,000$ cycles across arms) | $\text{Mean Latency} = 3.76\text{ ms}$<br>$\text{p95 Latency} = 10.20\text{ ms}$<br>($N = 38,693$ cycles evaluated) | **PASS ✅** |
| **Gate 5** | **Decision-Pipeline AST Anti-Cheat Audit** | 100% clean static and dynamic scan<br>Zero simulator coordinates in pipeline | 7/7 AST unit scans passed cleanly<br>Dynamic poisoned MuJoCo test clean<br>No-script audit 100% compliant | **PASS ✅** |

**Final Milestone Adjudication: FAILED CLOSED ❌.**  
Under fail-closed zero-tolerance governance, because Gates 1, 2, and 3 failed their pre-registered acceptance thresholds, Stage 3.4-R2 fails closed. Stage 3.4 v4, Stage 3.4-R, and Stage 3.4-R2 remain permanent, immutable historical records. **Stage 3.5 remains strictly LOCKED 🔒.**

---

## 2. Four-Arm Comparative Performance Breakdown (N = 200 Certification Episodes)

The 200 physical certification episodes were evaluated across 50 matched initial configurations under fixed pre-registered seeds `[5001, 5002, 5003, 5004, 5005]`:

```
===================================================================================================================
                                      ARM PERFORMANCE SUMMARY (N = 200 EPISODES)
===================================================================================================================
Arm ID   | Experimental Arm Description      | Pooled Escape | Pooled Coll | Env 1 Escape | Env 2 Escape | Mean Latency
---------+-----------------------------------+---------------+-------------+--------------+--------------+--------------
ARM-A    | Full Remediated Active Inference  |   0/50 (0.0%) | 14/50 (28%) |   0/20 (0.0%)|   0/30 (0.0%)|   3.76 ms
ARM-B    | Pragmatic-Only Baseline           |   0/50 (0.0%) | 13/50 (26%) |   0/20 (0.0%)|   0/30 (0.0%)|   1.48 ms
ARM-C    | Ablation 1: Micro-Local 3cm Shadow|   0/50 (0.0%) | 24/50 (48%) |   0/20 (0.0%)|   0/30 (0.0%)|   1.46 ms
ARM-D    | Ablation 2: Unnormalized Scale    |   0/50 (0.0%) | 10/50 (20%) |   0/20 (0.0%)|   0/30 (0.0%)|   5.82 ms
===================================================================================================================
```

### Ablation Findings
1. **Macro-Frontier vs Micro-Local Shadow (ARM-A vs ARM-C)**:
   - In ARM-C (micro-local 3 cm frontier shadow), the collision rate was **48.0% (24/50)**, nearly double that of ARM-A (**28.0%**). The 3 cm local frontier pulled the chassis directly against immediate obstacle perimeters, causing severe wall scraping.
   - The macro-frontier with BFS distance field in ARM-A and ARM-D successfully kept the robot further from walls during turning maneuvers.
2. **Dimensionless Normalization vs Unnormalized Scale (ARM-A vs ARM-D)**:
   - In ARM-D (unnormalized scale $\lambda=8.0$), collision rate was lower (20.0%), and robot heading rotated up to 179°–180° in almost all trials.
   - However, neither ARM-A nor ARM-D achieved autonomous egress down the corridor (0.0% escape).

---

## 3. Forensic Analysis: Why Did Stage 3.4-R2 Fail Closed?

A rigorous post-mortem of the raw trial telemetry ([`evidence/stage3_4R2/stage3_4R2_raw_trials.json`](file:///d:/ebca/evidence/stage3_4R2/stage3_4R2_raw_trials.json)) reveals the exact physical and mathematical mechanism of the failure:

### 1. The Kinematic Disentanglement Was Successful
- In Stage 3.4 (tight $0.70\text{ m}$ corridor), the robot physically collided with lateral walls in 65% of trials during attempted turns.
- In Stage 3.4-R2 with the $1.30\text{ m}$ turning bay, ARM-A achieved an average maximum yaw rotation of **$135.26^\circ$** (with many trials reaching $176^\circ - 180^\circ$) and sustained reversals averaging **$9.54$ consecutive ticks** ($v < -0.05\text{ m/s}$).
- The robot autonomously backed into the turning bay, pivoted to face the corridor, and aligned its heading with the egress axis.

### 2. The Corridor Mouth Free-Energy Saddle Point
Once aligned to face the corridor (x ≈ 0.50 m in Environment 1):
- The corridor width is $W = 0.70\text{ m}$, and CARL's chassis diameter is $0.34\text{ m}$.
- Inside the turning bay ($W = 1.30\text{ m}$), the lateral wall distance is $\sim 0.48\text{ m}$, well above $d_{\text{margin}} = 0.35\text{ m}$, yielding $\bar{J}_{\text{margin}} \approx 0$.
- However, entering the narrow corridor requires driving into a channel where lateral clearance drops to $(0.70 - 0.34)/2 = 0.18\text{ m} < d_{\text{margin}}$.
- Even with dimensionless normalization, entering the corridor incurs an unavoidable, persistent margin penalty across all $H=15$ steps of the rollout:
  $$\bar{J}_{\text{margin}}(\tau) \approx \left(\frac{0.35 - 0.18}{0.35}\right)^2 \approx 0.235$$
  Multiplied by $\alpha_{\text{margin}} = 0.35$, this adds $+0.082$ to the candidate free energy.
- Meanwhile, the normalized geodesic frontier progress over $H=15$ steps ($0.135\text{ m}$) contributes at most:
  $$-w_{\text{info}} \alpha_{\text{epistemic}} \bar{\Phi}_{\text{frontier}} \approx -0.40 \times \frac{0.135}{0.135} = -0.40 \text{ (in the best unconstrained rollout)}$$
- But any rollout entering the channel also experiences sonar flank steering discrepancies and heading sensitivity. The MPPI optimizer finds that remaining stationary or oscillating in the safe, open turning bay has lower Expected Free Energy than committing forward into the narrow, high-margin-penalty corridor.
- Consequently, the robot finished at $x = 0.474\text{ m}$ on average in Environment 1—right at the threshold of the turning bay—and timed out after 220 ticks.

### 3. Causal Equivalence with ARM-B
Because neither ARM-A nor ARM-B committed to the narrow channel, both arms produced identical escape rates of $0.0\%$, resulting in $\Delta = 0.0\%$ and exact McNemar $p = 1.0$. Epistemic objective necessity could not be demonstrated.

---

## 4. Evidence Artifacts Verification

All required evidence artifacts have been generated, frozen, and verified:

1. **Scorecard**: [`evidence/stage3_4R2/stage3_4R2_scorecard.json`](file:///d:/ebca/evidence/stage3_4R2/stage3_4R2_scorecard.json)
2. **Raw Trial Telemetry**: [`evidence/stage3_4R2/stage3_4R2_raw_trials.json`](file:///d:/ebca/evidence/stage3_4R2/stage3_4R2_raw_trials.json)
3. **Pre-Flight Diagnostic**: [`evidence/stage3_4R2/stage3_4R2_preflight_diagnostic.json`](file:///d:/ebca/evidence/stage3_4R2/stage3_4R2_preflight_diagnostic.json)
4. **Publication Figures**:
   - `fig1_ablation_comparison.png` (4-Arm comparison across Env 1 & Env 2)
   - `fig2_macro_frontier_trajectories.png` (Trajectory traces in both environments)
   - `fig3_geodesic_potential_and_heatmaps.png` (Occupancy mask, BFS geodesic field & centerline gradient)
   - `fig4_collision_clearance_and_mppi_fan.png` (Hull clearance profiles & M=128 MPPI trajectory fan)
   - `fig5_stage3_4R2_formal_certification_matrix.png` (Authoritative 5-Gate scorecard matrix)
5. **Demonstration Videos**:
   - `video_turning_bay_escape_r2.mp4` (Side-by-side POV camera & cognitive telemetry dashboard)
   - `video_tjunction_epistemic_showdown_r2.mp4` (Synchronized side-by-side comparison)

---

## 5. Master Governance Adjudication & Lock

```
========================================================================================
                              PERMANENT GOVERNANCE STATUS
========================================================================================
Stage 3.0: Pre-Flight Integrity Lock              — CERTIFIED ✅
Stage 3.1: CANN Causal Coupling (Stage 3.1-R)     — CERTIFIED ✅
Stage 3.2: Spatial Memory Necessity (Stage 3.2-R) — CERTIFIED ✅
Stage 3.3: Continuous Action Synthesis (MPPI)     — CERTIFIED ✅
Stage 3.4: Autonomous Behavioral Discovery (EFE)  — FAILED CLOSED ❌ (Aug 2026)
Stage 3.4-R: Active Inference Remediation         — FAILED CLOSED ❌ (Sept 2026)
Stage 3.4-R2: Macro-Frontier Remediation          — FAILED CLOSED ❌ (Sept 2026)
Stage 3.5: Physical Perturbation & Adaptation     — STRICTLY LOCKED 🔒
========================================================================================
```

Stage 3.4-R2 is adjudicated **FAILED CLOSED ❌**. Stage 3.5 remains strictly locked. All artifacts are committed to the permanent project record.
