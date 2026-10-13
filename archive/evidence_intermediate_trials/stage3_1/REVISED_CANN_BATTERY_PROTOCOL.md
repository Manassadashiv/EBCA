# CARL-DX STAGE 3.1 REVISED PRE-REGISTERED CANN CAUSAL BATTERY PROTOCOL
**Document Classification:** Pre-Registered Experimental Protocol (FROZEN BEFORE EXECUTION)  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1 — CANN Causal Coupling Remediation  
**Status:** FROZEN SPECIFICATION 🔒  
**Date:** September 13, 2026  

---

## 1. Research Question
Does the 2,114-unit neuromorphic continuous attractor neural network (CANN) contain genuinely useful, behaviorally indispensable spatial and directional information that downstream continuous action selection requires when instantaneous local exteroceptive sensations (sonar) are insufficient?

---

## 2. Null Hypothesis ($H_0$) and Alternative Hypothesis ($H_1$)
- **Null Hypothesis ($H_0$):** Removal or perturbation of the 2,114-unit CANN state (ARM-B Frozen, ARM-C Zeroed, ARM-D Shuffled) does not degrade downstream navigation performance (hull clearance, collision rate) compared to the uncorrupted network (ARM-A Intact) on non-LOS and sensory-ambiguous navigation tasks ($\Delta C_{\text{hull}} < 0.05 \text{ m}$ or $p \ge 0.01$).
- **Alternative Hypothesis ($H_1$):** Complete deprivation of the 2,114-unit CANN state (ARM-C Zeroed) significantly degrades navigation clearance by at least $0.05 \text{ m}$ ($p < 0.01$, Wilcoxon signed-rank test), causes an increase in collision rate, alters motor actions ($\Delta \mathbf{u} > 0.15$), and scrambles prospective candidate rankings ($\rho \le 0.70$).

---

## 3. Intervention Arms (4-Arm Controlled Factorial Design)
All arms are evaluated on identical initial physical states, seeds, and robot morphology:
1. **ARM-A (Intact):** Uncorrupted CANN integration. Synaptic ODEs step continuously from grounded proprioception and sensory projections.
2. **ARM-B (Frozen):** Attractor state is clamped to the initial spawn state for all $t > 0$ ($r(t) = r(0)$, $\hat{\theta}(t) = \hat{\theta}(0)$, $(\hat{x}, \hat{y}) = (0, 0)$).
3. **ARM-C (Zeroed — Primary Deprivation Control):** Complete deprivation of the attractor state ($r = \mathbf{0}$, $\hat{\theta} = 0$, $(\hat{x}, \hat{y}) = (0, 0)$, amplitude = $0$).
4. **ARM-D (Shuffled):** Attractor dynamics evolve normally, but the 64-neuron population is scrambled via a frozen deterministic permutation matrix $P_{\text{ep}}$ generated per episode seed.

---

## 4. Environment & Task Definitions (Non-LOS & Sensory Ambiguity)
To guarantee that **current local sensors are fundamentally insufficient to determine the correct action**, the revised battery evaluates four distinct tasks designed around non-line-of-sight navigation and sensory occlusions:

1. **Task 1: Sensor Blackout Corridor Traversal (`layout_1_left_trap`, 80 ticks):**
   - Sonar array experiences a sensory blackout (simulating acoustic absorption or occlusion) between ticks 15 and 40 (25 ticks = 0.75 s). All sonar rays read 5.0 m.
   - CARL must negotiate a sharp $90^\circ$ left corridor curve using CANN path integration and prospective ray-marching against internal spatial memory.
   - Deprived/Zeroed CANN lacks heading/displacement tracking during blackout and drifts into the outer wall.

2. **Task 2: Blind Corner Trap (`layout_2_right_trap`, 80 ticks):**
   - Robot approaches an acute right turn with a recessed trap. Sonar drops out for 20 ticks (ticks 10 to 30) during the entry transition.
   - Requires prospective unroll grounded in CANN displacement to brake and initiate turning before wall contact.

3. **Task 3: Symmetrical Sonic Bifurcation (`layout_3_t_junction`, 80 ticks):**
   - Approaching a T-junction where lateral clearances are sonically balanced ($d_{\text{left}} \approx d_{\text{right}}$).
   - One branch leads into a dead-end pocket; the opposite branch leads to the open arena.
   - Sonar drops out for 20 ticks (ticks 15 to 35). Only global attractor orientation correctly selects the open branch.

4. **Task 4: Long-Horizon Compass Corridor (`layout_4_corridor_slit`, 100 ticks):**
   - Extended multi-chicane traversal requiring continuous maintenance of the 64-neuron head-direction bump across consecutive opposite rotations with a 20-tick sonar dropout (ticks 20 to 40).

---

## 5. Sample Size & Power
- **Seeds:** 5 unseen pseudorandom seeds: `[2001, 2002, 2003, 2004, 2005]`.
- **Layouts:** 4 distinct task environments.
- **Trials per Layout:** 5 paired trials per layout.
- **Total Trials per Arm:** $5 \times 4 \times 5 = 100$ paired trials.
- **Total Benchmark Episodes:** $100 \text{ trials} \times 4 \text{ arms} = 400 \text{ episodes}$.
- **Statistical Power:** $N = 100$ paired observations provides $> 95\%$ power to detect an effect size of Cohen's $d \ge 0.40$ at $\alpha = 0.01$ (two-tailed Wilcoxon signed-rank test).

---

## 6. Primary and Secondary Metrics

### Primary Metric (Downstream Behavioral Necessity)
1. **Hull Clearance Degradation ($\Delta C_{\text{hull}}$):**
   $$\Delta C_{\text{hull}} = \bar{C}_{\text{Intact}} - \bar{C}_{\text{Ablated}}$$
   where $C$ is the minimum hull clearance recorded across the episode.
   - **Threshold:** $\Delta C_{\text{hull}} \ge +0.0500 \text{ m}$ ($5.0 \text{ cm}$).
2. **Statistical Significance ($p$-value):**
   Two-tailed Wilcoxon signed-rank test on paired trial clearances:
   - **Threshold:** $p < 0.0100$.

### Secondary Metrics (Mechanistic and Safety Coupling)
3. **Continuous Action Divergence ($\Delta \mathbf{u}$):**
   $$\Delta \mathbf{u} = \frac{1}{T} \sum_{t=1}^T \| \mathbf{u}_{\text{Intact}}(t) - \mathbf{u}_{\text{Ablated}}(t) \|_2$$
   - **Threshold:** Mean $\Delta \mathbf{u} > 0.1500$.
4. **Candidate Utility Rank Correlation (Spearman $\rho$):**
   Mean Spearman rank correlation between candidate utility profiles at trial start ($t = 0$):
   - **Threshold:** $\bar{\rho} \le 0.7000$.
5. **Collision Rate Increase ($\Delta \text{Coll}$):**
   $$\Delta \text{Coll} = \text{CollRate}_{\text{Ablated}} - \text{CollRate}_{\text{Intact}}$$
   - **Requirement:** $\Delta \text{Coll} \ge 0.0\%$ (Ablated arm must not outperform Intact).

---

## 7. Statistical Test Protocol
1. Paired comparisons between ARM-A (Intact) and each ablation arm (ARM-B, ARM-C, ARM-D).
2. Two-tailed Wilcoxon signed-rank test on paired clearance vectors: $(\mathbf{c}_{\text{Intact}} - \mathbf{c}_{\text{Ablated}})$.
3. Cohen's $d$ effect size calculation using pooled sample variance:
   $$d = \frac{\bar{C}_{\text{Intact}} - \bar{C}_{\text{Ablated}}}{s_{\text{pooled}}}$$
4. McNemar's exact test on paired binary collision outcomes.

---

## 8. Exact Pass/Fail Thresholds & Adjudication Matrix

| Gate | Metric | Condition | Required Value | Criticality |
|:---|:---|:---:|:---:|:---:|
| **Gate 1** | Action Divergence | $\Delta \mathbf{u}$ | $> 0.1500$ | Mechanistic Gating |
| **Gate 2** | Candidate Rank Shift | Spearman $\rho$ | $\le 0.7000$ | Decision Gating |
| **Gate 3** | Clearance Degradation | $\Delta C_{\text{hull}}$ | $\ge +0.0500 \text{ m}$ | **Behavioral Necessity** |
| **Gate 4** | Clearance Significance | Wilcoxon $p$ | $< 0.0100$ | **Statistical Rigor** |
| **Gate 5** | Collision Degradation | $\Delta \text{Coll}$ | $\ge 0.0\%$ | **Safety Grounding** |

---

## 9. Fail-Closed Governance Rule
1. **Zero Compromise:** If ARM-C (Zeroed) fails any of Gates 1–5, the test FAILS CLOSED.
2. **No Claim of Necessity Without Behavioral Proof:** Mathematical action divergence alone ($\Delta \mathbf{u} > 0.15$) cannot be used to declare Stage 3.1 passed.
3. **No Downstream Unlocking:** Stages 3.2 and 3.3 remain strictly locked regardless of the outcome.
4. **AST Anti-Cheat Invariant:** Zero simulator coordinate reads (`qpos`, `qvel`, `geom_xpos`, `mj_ray`) permitted in the active cognitive decision loop.
