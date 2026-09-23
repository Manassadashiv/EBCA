# CARL-DX Phase 1-R3: Memory-Causality Experimental Protocol

## 1. Scientific Objective & Hypotheses
The Phase 1-R3 campaign investigates whether stored autobiographical experience can causally alter CARL's subsequent route choice when encountering an otherwise locally identical sensory decision state ($H_1$), evaluated against a matched `NO_MEMORY` control ($H_0$).

- **$H_0$ (Null Hypothesis)**: Stored episodic memory does not alter route choice; both `FULL` and `NO_MEMORY` follow identical trajectory distributions at recurrence.
- **$H_1$ (Alternative Causal Hypothesis)**: After experiencing an adverse outcome in Route B on Episode 1, `FULL_P1_R3` retrieves the negative associative valence and switches to Route A on Episode 2 before the hazard is observable ($x \le 0.35\text{m}$), whereas `NO_MEMORY` repeats Route B.

---

## 2. Experimental Design & Structure

### Condition Matrix (Between-Agent Intervention):
1. **`FULL_P1_R3`**: Complete Active Inference + HDC Autobiographical Episodic Memory enabled ($N=2048$ hypervector space).
2. **`NO_MEMORY`**: Matched control sharing identical multi-step action sequence rollouts, kinematics, and physics, but with episodic memory disabled.

### Multi-Episode Protocol (Within-Agent Progression):
- **Episode 1 (Experience)**:
  - Start pose: $(x=0.00, y=0.00, \psi=0.00)$. Sensed sonar profile is symmetric ($\Delta d < 0.02\text{m}$).
  - Route B contains a latent downstream barrier at $(1.35, -0.55\text{m})$ occluded behind a corridor dogleg.
  - CARL interacts with the environment, encounters the hazard, and writes memory episodes with negative valence ($\text{Valence} = -1.0$).
- **Episode 2 (Recurrence)**:
  - Start pose: $(x=0.00, y=0.00, \psi=0.00)$. Same sensory clearance.
  - Evaluate route choice at $x = 0.35\text{m}$ (strictly before the hazard is in line-of-sight).
  - Measure route choice divergence $\Delta P(\text{Route A}) = P(\text{Route A} \mid \text{FULL}) - P(\text{Route A} \mid \text{NO\_MEM})$.
- **Episode 3 (Context Update / Extinction)**:
  - Start pose: $(x=0.00, y=0.00, \psi=0.00)$. Hazard removed in Route B.
  - Test whether `FULL_P1_R3` flexibly updates its exploration rather than exhibiting rigid avoidance.

### Pilot Size & Seeds:
- **Seed 42** (Primary Causal Verification Gate)
- **Seed 101**, **Seed 2024** (Multi-Seed Replication)
- Total: $2 \text{ conditions} \times 3 \text{ seeds} \times 3 \text{ episodes} = 18 \text{ physical simulation episodes}$.

---

## 3. Pre-Flight Sensor & Decision Matching Criteria
- At decision point ($x \le 0.35\text{m}$):
  - Max absolute sonar difference: $\|\Delta d_{\text{sonar}}\|_{\infty} \le 0.02\text{ m}$.
  - Mean absolute sonar difference: $\overline{|\Delta d_{\text{sonar}}|} \le 0.005\text{ m}$.
  - Initial pose match: $\Delta x = 0.000\text{ m}, \Delta y = 0.000\text{ m}, \Delta \psi = 0.0^\circ$.
  - True geometric wall clearance: $> 0.000\text{ m}$ (Zero wall penetration).
