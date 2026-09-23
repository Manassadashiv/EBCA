# CARL-DX CANDIDATE AGENCY ARCHITECTURES SPECIFICATION

This document outlines the three competing candidate architectures evaluated for CARL-DX:

### Architecture 1: Pure Homeostatic Active Inference (Baseline)
- Evaluates candidate actions using Expected Free Energy $G(a) = \mathcal{D}_{\text{KL}}(q(s' \mid a) \,\|\, p^*(s')) + \mathcal{H}(q(o' \mid s'))$.
- **Limitation**: Prone to freezing when physiological safety is satisfied, as standing still minimizes expected parameter divergence.

### Architecture 2: Dual-Drive (Homeostasis + Epistemic Curiosity)
- Adds epistemic novelty drive: $U(a) = -G(a) + w_{\text{cur}} \cdot \text{Var}(s' \mid a)$.
- **Limitation**: Agent sometimes seeks unpredictable regions (e.g. tight dead ends, high-friction wedges) because prediction variance is high, leading to physical entrapment.

### Architecture 3: Tri-Drive (Homeostasis + Curiosity + Controllability/Empowerment) [SELECTED]
- Evaluates actions by combining:
  1. Homeostatic viability constraint $\mathcal{U}_{\text{hom}}(a)$
  2. Epistemic curiosity / novelty bonus $\mathcal{U}_{\text{cur}}(a)$
  3. Controllability / Empowerment signal $\mathcal{E}(s')$
- Formally:
  $$\mathcal{U}_{\text{total}}(a) = w_{\text{hom}} \cdot \mathcal{U}_{\text{hom}}(a) + w_{\text{cur}} \cdot \mathcal{U}_{\text{cur}}(a) + w_{\text{emp}} \cdot \mathcal{E}(s')$$
- **Advantage**: Curiosity drives exploration into open unknown areas, but Empowerment vetoes actions leading into dead ends where future action entropy collapses!
