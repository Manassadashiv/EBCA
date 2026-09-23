# CARL-DX — PHASE 1-R3 SCIENTIFIC EXPERIMENTAL PROTOCOL
## Memory-Causality & Experience-Dependent Route Choice in Embodied Active Inference

**Document Identifier**: `CARL-P1R3-PROTO-V1.0`  
**Date of Execution**: 2026-08-23T02:05:00Z  
**Primary Investigators**: Google DeepMind / Antigravity Autonomous Systems  
**Status**: APPROVED & ACTIVE  

---

## 1. Scientific Mission & Core Hypotheses

### Primary Research Question:
> *"Can prior experience causally change CARL's later route choice when the immediate sensory state at the decision point is identical?"*

### Hypotheses:
- **Null Hypothesis ($H_0$)**:  
  Episodic memory does not causally alter route selection at the decision bifurcation. When immediate sensory evidence is locally indistinguishable, `FULL_P1_R3` and `NO_MEMORY` exhibit statistically identical route-choice distributions:
  $$P(\text{Route A} \mid \text{FULL}, s_{\text{decision}}) = P(\text{Route A} \mid \text{NO\_MEM}, s_{\text{decision}})$$

- **Alternative Hypothesis ($H_1$)**:  
  After experiencing a route-specific adverse outcome (latent hazard / downstream barrier in Route A during Episode 1), `FULL_P1_R3` selectively alters its later route preference on Episode 2 **before the adverse outcome is locally observable by immediate sensors**, whereas `NO_MEMORY` repeats its baseline route choice distribution:
  $$P(\text{Route A} \mid \text{FULL}, \text{Ep 2}) < P(\text{Route A} \mid \text{NO\_MEM}, \text{Ep 2})$$

---

## 2. Decision Geometry & Strict Sensory Equivalence

### Y-Bifurcation Topology:
```text
                         TARGET FOOD
                            ★ (x=2.20, y=0.00)
                           / \
                          /   \
                         /     \
             Route A    /       \   Route B
             (North)   /  WALL   \  (South)
                      [X]         \
           (Occluded  /             \
            Hazard)  /               \
                    /                 \
                     \               /
                      \             /
                       \           /
                        \         /
                           CARL
                        (0.00, 0.00)
```

### Critical Invariance Specifications:
1. **Symmetric Bifurcation**:
   - Initial robot pose: $(x_0 = 0.00\text{ m}, y_0 = 0.00\text{ m}, \text{yaw}_0 = 0.00\text{ rad})$.
   - Central Divider: Placed along $y = 0.00$ separating North Corridor (Route A, $y > 0$) and South Corridor (Route B, $y < 0$).
   - Route A Entrance ($y \in [+0.35, +0.95\text{ m}]$) and Route B Entrance ($y \in [-0.95, -0.35\text{ m}]$) have identical path lengths to food beacon $(2.20, 0.00)$.
2. **Local Sensory Indistinguishability**:
   - At $(0.00, 0.00)$, sonar range measurements along left and right hemispheres are strictly symmetric:
     $$\|d_{\text{sonar}}(\text{Left}) - d_{\text{sonar}}(\text{Right})\|_{\infty} < 0.02\text{ m}$$
   - Visible local clearance, target bearing, and target distance are identical for both branches.
3. **Latent Downstream Hazard (Occluded)**:
   - In Route A, a solid barrier is located downstream at $(x = 1.40\text{ m}, y = +0.65\text{ m})$ behind an angular corridor occlusion.
   - At the bifurcation decision region ($x \le 0.40\text{ m}$), the hazard is completely occluded from direct line-of-sight sonar rays.
   - Consequently, `NO_MEMORY` cannot detect the blockage before committing into the branch.

---

## 3. Three-Episode Developmental Progression

| Episode | Phase Name | Route A (North) State | Route B (South) State | Scientific Purpose |
| :---: | :--- | :--- | :--- | :--- |
| **Ep 1** | **Experience** | Latent downstream barrier active at $(1.40, +0.65)$ | Completely open | First exposure: agent explores naturally; experiencing adverse outcome in A triggers generic episodic memory write. |
| **Ep 2** | **Recurrence** | Latent downstream barrier active at $(1.40, +0.65)$ | Completely open | **Primary Causal Test**: Identical initial sensory state at $(0.0, 0.0)$. Measure route choice **before** reaching $x = 0.50\text{ m}$ (prior to hazard line-of-sight). |
| **Ep 3** | **Context Extinction** | Barrier REMOVED (Route A fully clear) | Completely open | **Reversal / Flexibility Test**: Distinguishes context-dependent memory adaptation from permanent hardcoded avoidance. |

---

## 4. Matched-Control Design

- **Conditions**:
  1. `FULL_P1_R3`: Multi-step sequence rollout + HDC Autobiographical Episodic Memory enabled across sequential episodes.
  2. `NO_MEMORY`: Multi-step sequence rollout identical to FULL, but episodic memory disabled (reactive control).
  3. `P0_CONTROL`: Frozen P0 single-arc Active Inference baseline.
- **Seeds**: `42`, `101`, `2024`.
- **Pilot Size**: $3\text{ conditions} \times 3\text{ seeds} \times 3\text{ episodes} = 27\text{ physical episodes}$.

---

## 5. Mathematical Formulations & Causal Metrics

### Expected Free Energy with Memory Bias:
$$G(S) = G_{\text{kinematic}}(S) + \lambda_{\text{mem}} \cdot \text{MemoryBias}(S)$$
where:
$$G_{\text{kinematic}}(S) = w_d D(S) + w_\theta |\theta_{\text{err}}| + w_\kappa \kappa^2 + \text{TTC\_Risk}(S) - w_v v$$
$$\text{MemoryBias}(S) = \sum_{ep \in \mathcal{M}} \text{sim}(x_S, y_S, ep) \cdot (-\text{Valence}(ep))$$

### Primary Causal Metrics:
1. **Pre-Hazard Route Commitment ($x = 0.40\text{ m}$)**:
   $$\text{RouteChoice} = \begin{cases} \text{Route A (North)}, & y(x=0.40) > +0.15\text{ m} \\ \text{Route B (South)}, & y(x=0.40) < -0.15\text{ m} \end{cases}$$
2. **Pre-Hazard Lateral Trajectory Divergence**:
   $$\Delta y_{\text{pre}}(x=0.40) = y_{\text{FULL}}(0.40) - y_{\text{NO\_MEM}}(0.40)$$
3. **Route Choice Probability Shift**:
   $$\Delta P(\text{Route A}) = P(\text{Route A} \mid \text{FULL}, \text{Ep 2}) - P(\text{Route A} \mid \text{NO\_MEM}, \text{Ep 2})$$

---

## 6. Emergence Classification Standard

- **LEVEL 0 — ENGINEERED**: Hardcoded if/else rules, waypoints, or route labels detected in AST audit.
- **LEVEL 1 — TASK CAPABILITY**: Agent navigates both corridors but shows no experience-dependent choice shift.
- **LEVEL 2 — ADAPTATION CANDIDATE**: Behavior changes after Ep 1, but `FULL` and `NO_MEMORY` do not significantly diverge.
- **LEVEL 3 — MEMORY-CAUSAL BEHAVIOURAL CHANGE**: `FULL` dynamically switches to Route B before hazard observation on Ep 2, while `NO_MEMORY` does not ($\Delta P(\text{Route A}) \le -0.50$ across seeds).
- **LEVEL 4 — EMERGENTLY SUPPORTED**: Level 3 verified + Ep 3 extinction demonstrates flexible context updating with 0 behavior-specific rules.
