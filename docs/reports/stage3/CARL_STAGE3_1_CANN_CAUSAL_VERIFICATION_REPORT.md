# CARL-DX STAGE 3.1 — CANN CAUSAL COUPLING VERIFICATION REPORT
**Author:** Antigravity AI Engine (Autonomous Pair Programmer)  
**Date:** September 12, 2026  
**Status:** **EVALUATION COMPLETE — FAIL-CLOSED GATE ENFORCED ⚠️**  
**Target Architecture:** 2,114-Unit Neuromorphic Continuous Attractor Network (64 HD + 1,024 Grid + 1,026 Reservoir)  
**Evaluation Protocol:** Pre-Registered 4-Arm Controlled Battery (`CARL_STAGE3_CANN_CAUSAL_BATTERY.md`, v1.1)

---

## 1. Executive Summary & Forensic Verdict

Stage 3.1 was executed to answer the fundamental question:
> *"Does the 2,114-unit neuromorphic continuous attractor network causally modulate downstream continuous action selection, and does corrupting or depriving this internal representation cause statistically significant and behaviorally indispensable degradation?"*

### Key Findings
1. **Causal Data Path & Action Modulation Certified (PASS ✅):**
   - After wiring the CANN's 64-HD population vector $\mathbf{r}_{\text{HD}}$, decoded heading $\hat{\theta}_{\text{CANN}}$, and grid phase into `deliberation.select_action()`, the deliberator actively responds to internal attractor states.
   - Downstream action command divergence under all three ablation conditions massively exceeded the pre-registered passing threshold ($\Delta \mathbf{u} > 0.15$):
     - **ARM-B (Frozen):** $\Delta \mathbf{u} = 0.5336 \pm 0.2029$ (**PASS**)
     - **ARM-C (Zeroed):** $\Delta \mathbf{u} = 0.5319 \pm 0.1290$ (**PASS**)
     - **ARM-D (Shuffled):** $\Delta \mathbf{u} = 0.5481 \pm 0.1551$ (**PASS**)
   - Candidate trajectory rank correlation dropped below the pre-registered ceiling ($\rho \le 0.70$), proving that CANN ablation actively re-ranks candidate action branches:
     - **ARM-B (Frozen):** $\rho = 0.6566$ (**PASS**)
     - **ARM-C (Zeroed):** $\rho = 0.6081$ (**PASS**)
     - **ARM-D (Shuffled):** $\rho = 0.6240$ (**PASS**)

2. **Downstream Clearance Superiority in Short Mazes NOT Established (FAIL-CLOSED ⚠️):**
   - While corrupting the CANN altered action choices, it did **not** produce a statistically significant degradation in physical hull clearance ($\Delta C_{\text{hull}} \ge 0.05\,\text{m}, p < 0.01$):
     - **ARM-B (Frozen):** $\Delta C_{\text{hull}} = -0.0051\,\text{m}$ ($p = 0.485$, Cohen's $d = -0.047$)
     - **ARM-C (Zeroed):** $\Delta C_{\text{hull}} = -0.0187\,\text{m}$ ($p = 0.257$, Cohen's $d = -0.179$)
     - **ARM-D (Shuffled):** $\Delta C_{\text{hull}} = -0.0091\,\text{m}$ ($p = 0.670$, Cohen's $d = -0.085$)
   - Collision rates showed vulnerability under frozen attractor bias (ARM-B: $17.0\%$ vs Intact: $9.0\%$) and topological scrambling (ARM-D: $13.0\%$), but Zeroed CANN (ARM-C) achieved $7.0\%$ collisions.

### Formal Stage 3.1 Verdict
Under the immutable **Fail-Closed Governance Policy**, because Metric 2 ($\Delta C_{\text{hull}} \ge 0.05\,\text{m}$, $p < 0.01$) did not clear the pre-registered threshold across the 400-episode suite, **STAGE 3.1 FAILS CLOSED**. 

No compensatory scoring is permitted. The exact scientific root cause is analyzed below.

---

## 2. Quantitative Scorecard & Statistical Tests

Evaluation executed across $N = 100$ paired trials per arm (5 unseen test seeds $\times$ 4 certified challenge layouts $\times$ 5 trials = 400 total episodes):

| Condition ID | Treatment Description | Collision Rate (%) | Mean Hull Clearance (m) | Action Divergence $\Delta \mathbf{u}$ | Spearman $\rho$ vs Intact | Wilcoxon $p$-value | Gate Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ARM-A (Intact)** | Uncorrupted CANN ODE | **9.0%** | **0.128 ± 0.105** | Baseline (0.000) | 1.000 | N/A | **Baseline Ref** |
| **ARM-B (Frozen)** | Clamped at spawn heading | 17.0% (+8.0%) | 0.134 ± 0.113 | **0.534 ± 0.203** | **0.657** | $p = 0.485$ | **FAIL CLOSED** |
| **ARM-C (Zeroed)** | Neural blackout ($\mathbf{r} = \mathbf{0}$) | 7.0% (-2.0%) | 0.147 ± 0.103 | **0.532 ± 0.129** | **0.608** | $p = 0.257$ | **FAIL CLOSED** |
| **ARM-D (Shuffled)**| Deterministic perm $\mathbf{P}_{\text{ep}}$ | 13.0% (+4.0%) | 0.138 ± 0.108 | **0.548 ± 0.155** | **0.624** | $p = 0.670$ | **FAIL CLOSED** |

### Detailed Metric Compliance Table

| Gate ID | Metric Name | Protocol Threshold | ARM-B (Frozen) | ARM-C (Zeroed) | ARM-D (Shuffled) | Compliant? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Gate 1** | Motor Divergence $\Delta \mathbf{u}$ | $> 0.150$ | $0.534$ | $0.532$ | $0.548$ | **YES (3.5× threshold)** |
| **Gate 2** | Candidate Re-Ranking $\rho$ | $\le 0.700$ | $0.657$ | $0.608$ | $0.624$ | **YES (Modulates ranking)** |
| **Gate 3** | Clearance Degradation $\Delta C_{\text{hull}}$ | $\ge 0.050\,\text{m}$ | $-0.005\,\text{m}$ | $-0.019\,\text{m}$ | $-0.009\,\text{m}$ | **NO (Below threshold)** |
| **Gate 4** | Clearance Significance $p$ | $< 0.010$ | $p = 0.485$ | $p = 0.257$ | $p = 0.670$ | **NO (Non-significant)** |

---

## 3. Forensic Scientific Analysis: Why Did Clearance Not Degrade?

This empirical result reveals the exact mechanics of navigation in short, reactive mazes:

### The Dominance of Immediate Sonar Swept-Cones
In 60-tick challenge layouts (`layout_1_left_trap`, `layout_2_right_trap`, `layout_3_t_junction`, `layout_4_corridor_slit`), the robot is almost constantly within line-of-sight of arena walls ($< 0.40\,\text{m}$).
1. In `deliberation.select_action()`, the collision veto (`min_hull_clr < 0.10` or `min_cone_clr < 0.16`) imposes an $800.0$ penalty on any candidate arc that physically intersects a detected surface.
2. Immediate sonar proximity active lateral evasion provides up to $40.0$ utility units of repulsive steering away from flanking walls.
3. Therefore, even when the CANN orientation representation is zeroed (ARM-C), the robot's reactive rangefinder potential field and swept-cone veto prevent physical chassis contact. 
4. In fact, under Zeroed CANN (ARM-C), the robot has no internal directional preference, so it strictly adheres to reactive rangefinder clearance, yielding a $7.0\%$ collision rate.
5. Under Frozen CANN (ARM-B) and Scrambled CANN (ARM-D), erroneous attractor population vectors actively push the robot to turn into walls (increasing collisions to $17.0\%$ and $13.0\%$). However, because reactive sonar vetoes blunt the worst impacts, the net mean clearance across all surviving steps remains statistically indistinguishable ($\Delta C_{\text{hull}} \approx 0$).

### Core Conclusion
**In short, reactive line-of-sight environments, an internal head-direction attractor network is not physically indispensable for obstacle clearance; immediate sonar rangefinders suffice.**
The CANN only becomes indispensable when tasks require **integrating orientation across non-line-of-sight trajectories where immediate sonar provides ambiguous or misleading local cues** (the exact finding that prompted the Stage 3.2 tightening).

---

## 4. Visual Evidence Package

All plots generated with pure white backgrounds (`#ffffff`) and dark slate typography (`#0f172a`):

1. **Figure 1 — Downstream Action Choice Divergence ($\Delta \mathbf{u}$):**
   `evidence/stage3_1_cann/plots/plot1_cann_action_divergence.png`
   Demonstrates that corrupting or zeroing the CANN causes massive motor divergence ($\Delta \mathbf{u} > 0.53$).

2. **Figure 2 — Minimum Hull Clearance Degradation ($\Delta C_{\text{hull}}$):**
   `evidence/stage3_1_cann/plots/plot2_cann_hull_clearance.png`
   Honest visual reporting of clearance across arms, showing absence of clearance drop.

3. **Figure 3 — Autonomous Collision Rates ($P_{\text{coll}}$):**
   `evidence/stage3_1_cann/plots/plot3_cann_collision_rates.png`
   Shows collision increases in ARM-B ($17\%$) and ARM-D ($13\%$) vs Intact ($9\%$).

4. **Figure 4 — Candidate Trajectory Rank Correlation (Spearman's $\rho$):**
   `evidence/stage3_1_cann/plots/plot4_cann_rank_correlation.png`
   Confirms significant modulation of candidate trajectory utility rankings ($\rho \approx 0.61 - 0.65$).

5. **Figure 5 — 64-Neuron Head-Direction Attractor Polar Profiles:**
   `evidence/stage3_1_cann/plots/plot5_cann_bump_profiles.png`
   Circular firing rate distribution of the continuous attractor across Intact, Frozen, Zeroed, and Shuffled states.

---

## 5. Next Steps & Remediation Pathway

Per canonical rules:
1. **Stage 3.3 (MPPI) Remains Strictly Blocked.**
2. **Current State:** Stage 3.1 is formally classified as **FAILS CLOSED** on Metric 2 ($\Delta C_{\text{hull}}$).
3. **Remediation Plan:**
   - The causal link between CANN and Deliberation is structurally established and verified ($\Delta \mathbf{u} > 0.53$).
   - To demonstrate clearance necessity, CANN heading must be evaluated on tasks where line-of-sight sensing is deceived (e.g., asymmetric long-horizon corridors where dead-reckoned orientation must override ambiguous immediate sonar).
