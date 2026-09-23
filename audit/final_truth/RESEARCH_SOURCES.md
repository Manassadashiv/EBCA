# CARL-DX SCIENTIFIC RESEARCH & EXTERNAL METHODOLOGY SOURCES

**Audit Standard**: NASA-Inspired Systems Engineering Rigor  
**Deliverable**: Formal Literature & Mathematical Grounding of CARL-DX Cognitive Architecture

---

## 1. Primary Theoretical Foundations

### 1. Active Inference & The Free Energy Principle
- **Source**: Friston, K. (2010). *The free-energy principle: a unified brain theory?* Nature Reviews Neuroscience, 11(2), 127-138.
- **Mathematical Idea**: Action selection minimizes Expected Free Energy (EFE), balancing pragmatic value (goal achievement) and epistemic value (information gain / uncertainty reduction):
  $$\mathcal{G}(\pi) = \sum_\tau \left( D_{\text{KL}}\left[ Q(o_\tau \mid \pi) \parallel P(o_\tau) \right] + \mathbb{E}_{Q(s_\tau \mid \pi)}\left[ H\left(P(o_\tau \mid s_\tau)\right) \right] \right)$$
- **Application in CARL**: Implemented in [`CarlGenerativeSelfModel.imagine_counterfactual_rollouts`](file:///D:/ebca/brain/carl_generative_self_model.py#L115) over 14 candidate arc trajectories.

### 2. Information-Theoretic Empowerment
- **Source**: Klyubin, A. S., Polani, D., & Nehaniv, C. L. (2005). *Empowerment: A universal agent-centric measure of control.* IEEE Congress on Evolutionary Computation.
- **Mathematical Idea**: Channel capacity between candidate action sequences and future reachable sensor states:
  $$\mathcal{E}(s) = \max_{p(a)} I(A; S' \mid s)$$
- **Application in CARL**: Evaluated in [`CarlEmpowermentCore.evaluate_empowerment`](file:///D:/ebca/brain/carl_empowerment.py#L45) to penalize dead-end corridor entrapment.

### 3. Hyperdimensional Computing (HDC) Associative Memory
- **Source**: Kanerva, P. (2009). *Hyperdimensional computing: An introduction to computing in distributed representation with high-dimensional random vectors.* Cognitive Computation, 1(2), 139-159.
- **Mathematical Idea**: High-dimensional binary/bipolar vectors combined using circular convolution (binding) and vector superposition (bundling) for noise-robust episodic recall:
  $$\mathbf{h}_{\text{episode}} = \mathbf{v}_{\text{pos}} \otimes \mathbf{v}_{\text{need}} \otimes \mathbf{v}_{\text{valence}}$$
- **Application in CARL**: Implemented in [`CarlEpisodicMemory`](file:///D:/ebca/brain/carl_episodic_memory.py#L30) with $D = 2048$ dimensions.

### 4. Tri-Drive Homeostatic Interoception
- **Source**: Sterling, P. (2012). *Allostasis: A predictive regulation of internal states.* Physiological Behavior, 106(1), 5-15.
- **Mathematical Idea**: Multi-compartment homeostatic decay and replenishing kinetics driving autonomous goal switching without hardcoded timers.
- **Application in CARL**: Implemented in [`CarlHomeostaticCore`](file:///D:/ebca/brain/carl_embodied_organism.py#L25) tracking energy, thermal load, and curiosity.
