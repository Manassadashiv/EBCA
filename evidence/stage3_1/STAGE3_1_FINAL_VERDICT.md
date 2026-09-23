# CARL-DX STAGE 3.1 FINAL SCIENTIFIC VERDICT & CAUSAL ADJUDICATION
**Document Classification:** Pre-Registered Experimental Verdict (Fail-Closed Governance)  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1 — CANN Causal Coupling  
**Pre-Flight Status:** Stage 3.0 Certified ✅  
**Stage 3.1 Verdict:** **FAILED** ❌ (CANN causally connected but behaviorally non-essential under tested conditions)  
**Downstream Progression:** Stage 3.2 LOCKED 🔒 | Stage 3.3 (MPPI) LOCKED 🔒  
**Date:** September 13, 2026  

---

## 1. Formal Milestone Verdict

Under the frozen rules of CARL-DX canonical governance and the pre-registered protocols:

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                               STAGE 3.1 VERDICT: FAILED                              ║
║             CANN CAUSALLY CONNECTED BUT BEHAVIORALLY NON-ESSENTIAL                  ║
║                             UNDER TESTED CONDITIONS                                 ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

**Official Status:** **FAILED (FAIL-CLOSED)**.  
The 2,114-unit neuromorphic continuous attractor network (CANN) does **NOT** meet the certified standard of behavioral necessity.  
- Downstream Stage 3.2 (Counterfactual Trajectory Fidelity & Spatial Memory Necessity) remains **STRICTLY LOCKED**.
- Downstream Stage 3.3 (Continuous Action Synthesis via MPPI) remains **STRICTLY LOCKED**.
- No milestone progression is permitted.

---

## 2. Comprehensive Empirical Scorecard

Across two independent 400-episode batteries ($N = 800$ total controlled episodes evaluated across 10 random seeds, 4 maze environments, and 4 factorial intervention arms):

### Table 1: Revised Non-LOS Battery Results ($N = 400$ Episodes, Seeds 2001–2005)

| Metric | Required Threshold | ARM-A (Intact) | ARM-B (Frozen) | ARM-C (Zeroed) | ARM-D (Shuffled) | Gate Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Collision Rate (%)** | Baseline ($\Delta \ge 0\%$) | **44.0%** | **15.0%** (-29.0%) | **27.0%** (-17.0%) | **31.0%** (-13.0%) | **FAIL CLOSED** |
| **Mean Clearance ($C_{\text{hull}}$)** | Baseline | **0.078 m** | **0.153 m** | **0.080 m** | **0.094 m** | — |
| **Clearance Degradation ($\Delta C$)** | $\ge +0.050 \text{ m}$ | — | **-0.075 m** | **-0.003 m** | **-0.016 m** | **FAIL CLOSED** |
| **Wilcoxon Significance ($p$)** | $p < 0.0100$ | — | $5.27 \times 10^{-9}$ [PASS] | $0.381$ [FAIL] | $0.144$ [FAIL] | **FAIL CLOSED** |
| **Cohen's $d$ (Effect Size)** | Large ($d > 0.50$) | — | $-0.717$ | $-0.041$ | $-0.197$ | — |
| **Action Divergence ($\Delta \mathbf{u}$)** | $> 0.1500 \text{ m/s}$ | — | **0.511** [PASS] | **0.413** [PASS] | **0.455** [PASS] | **PASS** |
| **Spearman Rank Correlation ($\rho$)** | $\le 0.7000$ | — | **0.687** [PASS] | **0.604** [PASS] | **0.697** [PASS] | **PASS** |
| **Arm Overall Status** | All Gates Required | **BASELINE** | **FAIL CLOSED** | **FAIL CLOSED** | **FAIL CLOSED** | **FAILED** |

---

## 3. Independent Gate Adjudication

Each pre-registered gate is independently adjudicated:

### Gate 1: Continuous Action Divergence ($\Delta \mathbf{u} > 0.1500$) — [PASS ✅]
- Frozen: $\Delta \mathbf{u} = 0.511 \pm 0.170 > 0.150$ (PASS).
- Zeroed: $\Delta \mathbf{u} = 0.413 \pm 0.149 > 0.150$ (PASS).
- Shuffled: $\Delta \mathbf{u} = 0.455 \pm 0.154 > 0.150$ (PASS).
- **Verdict:** CANN state causally perturbs the selected continuous motor commands. Mathematical coupling is robust.

### Gate 2: Candidate Ranking Sensitivity (Spearman $\rho \le 0.7000$) — [PASS ✅]
- Frozen: $\rho = 0.687 \le 0.700$ (PASS).
- Zeroed: $\rho = 0.604 \le 0.700$ (PASS).
- Shuffled: $\rho = 0.697 \le 0.700$ (PASS).
- **Verdict:** CANN state reshuffles the prospective utility distribution over the continuous candidate fan.

### Gate 3: Behavioral Clearance Degradation ($\Delta C_{\text{hull}} \ge +0.0500 \text{ m}$) — [FAIL ❌]
- Frozen: $\Delta C_{\text{hull}} = -0.0752 \text{ m}$ (FAIL).
- Zeroed: $\Delta C_{\text{hull}} = -0.0029 \text{ m}$ (FAIL).
- Shuffled: $\Delta C_{\text{hull}} = -0.0162 \text{ m}$ (FAIL).
- **Verdict:** Removing the CANN did not degrade wall clearance by $5.0 \text{ cm}$. In all arms, clearance slightly or substantially increased.

### Gate 4: Statistical Significance ($p < 0.0100$) — [FAIL ❌]
- Zeroed (Primary Deprivation Arm): $p = 0.381 \ge 0.010$ (FAIL).
- Shuffled: $p = 0.144 \ge 0.010$ (FAIL).
- **Verdict:** No statistically significant clearance degradation under CANN deprivation.

### Gate 5: Safety Grounding & Collision Degradation ($\Delta \text{Coll} \ge 0.0\%$) — [FAIL ❌]
- Frozen: $-29.0\%$ collisions compared to Intact (FAIL).
- Zeroed: $-17.0\%$ collisions compared to Intact (FAIL).
- Shuffled: $-13.0\%$ collisions compared to Intact (FAIL).
- **Verdict:** Depriving or freezing the CANN reduced collisions. Intact CANN suffered 44.0% collisions, whereas Zeroed suffered 27.0% and Frozen suffered 15.0%.

---

## 4. Why Did the Ablation Outperform the Intact Organism?

A deep forensic inspection of the 800 trial trajectories reveals why the CANN ablation consistently achieved fewer collisions than the intact network:

1. **High-Frequency Escape Oscillations in Confined Spaces:**
   In narrow corridors ($0.60 - 0.80 \text{ m}$ wide), the physical chassis width is $0.27 \text{ m}$ (bumper width $0.23 \text{ m}$). When the intact CANN detects that an upcoming segment is occupied in the spatial memory raster, prospective deliberation attempts sharp composite turns (`hard_left_fast`, `reverse_straight`, `pivot`).
   Because the robot's wheels have physical inertia and slip dynamics, sharp pivots in narrow corridors cause the outer chassis bumper corners to swing into the lateral walls.
2. **Smooth Forward Momentum in Deprived Arms:**
   When CANN is zeroed (ARM-C), the deliberator lacks internal unroll offsets and falls back to simple forward tracking (`straight_full`, `straight_trim_R`). Without aggressive, ungrounded turning commands, the robot coasts smoothly down the centerline, avoiding side-wall clip collisions.
3. **Heading Clamping Advantage in Frozen Arm:**
   In ARM-B (Frozen), the head-direction attractor was clamped to the corridor orientation. This clamping acted as an artificial compass lock, preventing drift and keeping the robot centered, resulting in an ultra-low 15.0% collision rate.

---

## 5. Visual Evidence Summary
All 5 individual visual evidence artifacts have been generated on pure white backgrounds (`#ffffff`) and archived in `evidence/stage3_1/plots/`:
1. `plot1_action_divergence_delta_u.png`: Action divergence $\| \Delta \mathbf{u} \|$ across all ablation arms ($> 0.40 \text{ m/s}$).
2. `plot2_hull_clearance_comparison.png`: Mean clearance across all 4 arms showing failure of clearance degradation.
3. `plot3_collision_rates.png`: Collision rates showing Intact (44.0%) vs Frozen (15.0%), Zeroed (27.0%), Shuffled (31.0%).
4. `plot4_candidate_spearman_rho.png`: Spearman rank correlation showing $\rho \le 0.70$ decision modulation.
5. `plot5_stage3_1_adjudication_matrix.png`: Formal gate adjudication matrix documenting the Fail-Closed outcome.

---

## 6. Scientific Conclusion & Exact Next Step

### Scientific Conclusion
The experimental data conclusively demonstrates that while the 2,114-unit continuous attractor network is **causally wired to continuous action selection** ($\Delta \mathbf{u} \approx 0.41 - 0.51 \text{ m/s}$), it does **not provide behavioral necessity or survival advantage** under the current discrete candidate formulation ($K = 24$) in static mazes. In fact, attempting to enforce prospective unrolls through discrete trajectory branches in narrow corridors induces chassis swing collisions that pure reactive or clamped heading controllers avoid.

### Exact Next Step
Per canonical governance rules:
1. **Stage 3.1 is recorded as FAILED.**
2. **Do NOT advance to Stage 3.2.**
3. **Do NOT advance to Stage 3.3 (MPPI).**
4. Report the findings transparently to the user. Future work must decide whether:
   - (A) Re-architect CANN integration so that heading and grid state provide smooth guidance priors rather than triggering discrete chassis-swinging evasions;
   - (B) Evaluate CANN necessity strictly on open-arena foraging/homing tasks where turning space is unconstrained; or
   - (C) Formally defer continuous attractor coupling to Stage 3.4 (Active Inference) where continuous action synthesis replaces discrete branch selection.
