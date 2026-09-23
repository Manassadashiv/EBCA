# CARL STAGE 2.1B-R: ATTRACTOR CAUSALITY & PERSISTENCE SPECIFICATION
**Document Identifier:** `CARL-SPEC-STAGE2.1B-R-v1.0`  
**Classification:** Embodied Neuromorphic Cognitive Architecture  
**Target Milestone:** Stage 2 — Generative World & Self Modeling (Subproblem 2.1B-R)  
**Evaluation Standard:** Adversarial Karpathy LLM Council Protocol (4 Comparative Substrates)  
**Date:** September 4, 2026  

---

## 1. Executive Scientific Premise

### The Problem Defined in Stage 2.1B
In the Stage 2.1B open-space benchmark, the 2,114-unit continuous attractor network demonstrated genuine numerical ODE integration ($1.29\,\text{ms}$ step, 7/8 seeds passed), but:
1. **Classical floating-point calculus was nearly $4\times$ more accurate** in open space ($4.63\,\text{cm}$ vs $18.27\,\text{cm}$ drift).
2. **Short-horizon recurrence ablation ($W_{\text{rec}} = 0$) achieved $15.83\,\text{cm}$**, demonstrating that recurrent synaptic coupling was not causally necessary over short 60-tick journeys.
3. The hypothesis that CANN filters Gaussian sensor noise was falsified in absolute metric terms ($18.14\,\text{cm}$ vs $5.11\,\text{cm}$).

### The Core Question of Stage 2.1B-R
> **"Does recurrent continuous attractor dynamics provide a functional capability that is absent or substantially weaker in equivalent non-recurrent, persistent non-neural, and classical systems under identical information constraints?"**

We do not tune parameters to beat classical math at its own frictionless game. We evaluate four strictly isolated computational substrates under conditions where attractors are hypothesized to earn their keep.

---

## 2. The Four Comparative Substrates

| Substrate | Architecture | State Representation | Synaptic Recurrence | Persistence Mechanism |
| :--- | :--- | :--- | :---: | :--- |
| **A: Full CANN** | 2,114-unit integrated neuromorphic network | $\mathbf{u}_{\text{HD}} \in \mathbb{R}^{64}$, $\mathbf{u}_{\text{grid}} \in \mathbb{R}^{32 \times 32}$ | **ACTIVE** ($W_{\text{rec}}$ Mexican-hat) | Recurrent synaptic reverberation & continuous attractor manifold energy valley |
| **B: Feedforward CANN** | Identical 2,114-unit network | $\mathbf{u}_{\text{HD}} \in \mathbb{R}^{64}$, $\mathbf{u}_{\text{grid}} \in \mathbb{R}^{32 \times 32}$ | **DISABLED** ($W_{\text{rec}} = 0$) | Pure feedforward current integration; decays exponentially via passive leak $-\mathbf{u}/\tau$ |
| **C: Classical Control** | Classical dead-reckoning kinematics | Floating-point $(x, y, \theta) \in \mathbb{R}^3$ | N/A | Numerical Euler integration with P-controller |
| **D: Persistent Non-Neural** | Stateful scalar/vector latch | Latched vector $\mathbf{s}_{\text{latched}} \in \mathbb{R}^3$ | N/A | Retains previous state during blackout, but has **no attractor energy basin** and no pattern completion |

---

## 3. The Three Stress Batteries

### Battery 1: Physically Changing Sensor Dropout (Working Memory Under Dynamics)
* **Rationale:** A static blackout (robot holds still while sensors disappear) is trivially solved by keeping the last scalar value. To test true working memory, the physical state must continue changing while the sensory stream is blacked out.
* **Protocol:**
  1. *Phase 1 (Normal Drive, 30 ticks):* Robot drives and rotates under active wheel commands ($u_L = 0.12, u_R = -0.05$). All substrates track heading.
  2. *Phase 2 (Physically Changing Blackout, 90 ticks / $2.7\,\text{s}$):*
     - Gyro and forward velocity sensory signals injected into the brain are clamped to $0.0$.
     - Robot **continues physical rotation** under continuous motor commands.
  3. *Phase 3 (Sensory Resumption, 60 ticks):* Sensory inputs are restored.
* **Evaluation Metrics:**
  * Post-blackout decoded heading error: $|\hat{\theta}_{\text{decoded}} - \theta_{\text{ground\_truth}}|$ immediately upon sensory resumption.
  * Re-anchoring speed: ticks required to synchronize with true angular velocity.
* **Hypotheses:**
  * *Substrate B (Feedforward):* Membrane potential decays to zero ($\mathbf{u} \to 0$); heading bump vanishes.
  * *Substrate D (Persistent Non-Neural):* Retains the frozen pre-blackout heading, but has no dynamical mechanism to integrate expected inertia or re-anchor.
  * *Substrate A (Full CANN):* Attractor state preserves phase continuity and re-anchors smoothly upon input resumption.

---

### Battery 2: Pattern & Information Recovery Under Neural Membrane Perturbation
* **Rationale:** Measuring "bump reformation" alone is insufficient; a network could reset to an arbitrary default bump at $0^\circ$ and claim "stability". The attractor must restore both the **spatial pattern** and the **original informational content**.
* **Protocol:**
  1. Record pre-shock steady heading $\theta_{\text{pre}}$ and bump amplitude $R_{\text{pre}}$.
  2. At tick $t_0$, inject a violent disruptive noise shock:
     $$\mathbf{u}_{\text{shock}} = \mathbf{u} + \boldsymbol{\eta}, \quad \boldsymbol{\eta} \sim \mathcal{N}(0, 2.0)$$
     corrupting the continuous attractor manifold into a jagged multi-peaked distribution.
  3. Observe recovery over 30 ticks of zero velocity input ($\omega_z = 0$).
* **Evaluation Metrics:**
  * **Pattern Recovery:** Does a solitary bump reform ($R_{\text{post}} / R_{\text{pre}} \ge 0.80$ with unimodal circular variance $\le 0.35$)?
  * **Information Recovery:** Does the recovered bump preserve the pre-shock heading:
    $$\Delta \theta_{\text{info}} = |\hat{\theta}_{\text{post}} - \theta_{\text{pre}}| \le 15.0^\circ$$
    *(If $\Delta \theta_{\text{info}} > 15.0^\circ$, it is scored as a FAILURE, even if a beautiful bump exists!)*
  * **Settling Latency:** Number of ticks until $\frac{d\|\mathbf{u}\|}{dt} < 10^{-3}$.

---

### Battery 3: Unwrapped Long-Horizon Spatial Tracking ($> 1.5\,\text{m}$)
* **Rationale:** A toroidal network is mathematically bounded on $[-\pi, \pi)$ by design. Measuring wrapped phase distance on the torus does not prove spatial accuracy. We must evaluate **unwrapped trajectory tracking** against independent physical ground truth over paths extending beyond multiple toroidal wrap boundaries.
* **Protocol:**
  * Continuous multi-curvature exploration over 300 to 500 ticks.
  * Distance from origin reaches $1.5\,\text{m}$ to $2.0\,\text{m}$ (crossing the $0.80\,\text{m}$ torus wrap boundary twice).
* **Evaluation Metrics:**
  * Cumulative unwrapped trajectory error:
    $$\text{ATE} = \frac{1}{T} \sum_{t=1}^T \|\hat{\mathbf{p}}_{\text{unwrapped}}(t) - \mathbf{p}_{\text{gt}}(t)\|$$
  * Closed-loop homing return accuracy from the distant perimeter back to origin star.

---

## 4. Acceptance & Falsification Criteria

The Council will evaluate the experimental evidence under a strict battery-specific rubric:

| Battery | Hypothesized Recurrent Attractor Capability | Pass Threshold | Falsification Condition |
| :--- | :--- | :--- | :--- |
| **Battery 1 (Dropout)** | Recurrent reverberation sustains heading representation during blackout | Full CANN post-dropout error $< 30^\circ$, FF ablation collapses ($R < 0.1$) | CANN drift $\ge$ Persistent Non-Neural control |
| **Battery 2 (Shock)** | Mexican-hat recurrence recovers solitary bump AND original heading | Pattern recovery $\ge 80\%$, Information recovery $\le 15^\circ$, settling $\le 6$ ticks | Information recovery $> 15^\circ$ or bump fails to reform |
| **Battery 3 (Long Horizon)** | Toroidal grid sheet maintains bounded unwrapped trajectory tracking | Unwrapped ATE $\le 0.25\,\text{m}$ across multi-torus traversal | Unwrapped ATE exceeds classical Euler accumulation |

---

## 5. Summary Invariant
If the full recurrent CANN fails to demonstrate a significant advantage on any battery, **we report the failure honestly**. The acceptance criterion is genuine scientific discovery, not benchmark victory.
