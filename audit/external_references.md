# CARL-DX EXTERNAL SCIENTIFIC & TECHNICAL REFERENCES AUDIT

**Mission Standard**: NASA-Inspired Systems Engineering Rigor  
**Audit Purpose**: Complete provenance of theoretical principles, algorithms, and models integrated into CARL-DX.

---

## 1. Primary Academic & Literature References

### 1. Information-Theoretic Empowerment
- **Citation**: Klyubin, A. S., Polani, D., & Nehaniv, C. L. (2005). *Empowerment: A universal agent-centric measure of control.* IEEE Congress on Evolutionary Computation, 1, 128-135.
- **Concept Adapted**: Channel capacity between candidate action sequences and future reachable states $I(A_{1:H}; S_H)$.
- **Role in CARL-DX**: Implemented in [`brain/carl_empowerment.py`](file:///D:/ebca/brain/carl_empowerment.py) (`CarlEmpowermentCore`) to anticipate and veto dead-end entropy collapse.

### 2. Active Inference & Expected Free Energy
- **Citation**: Friston, K., Rigoli, F., Ognibene, D., Mathys, C., Fitzgerald, T., & Pezzulo, G. (2015). *Active inference and epistemic value.* Cognitive Neuroscience, 6(4), 187-214.
- **Concept Adapted**: Action selection minimizing Expected Free Energy $G(a) = \text{Risk} + \text{Cost} - \text{Epistemic Information Gain}$.
- **Role in CARL-DX**: Implemented in [`brain/carl_generative_self_model.py`](file:///D:/ebca/brain/carl_generative_self_model.py).

### 3. Hyperdimensional Computing (HDC) Associative Memory
- **Citation**: Kanerva, P. (2009). *Hyperdimensional computing: An introduction to computing in distributed representation with high-dimensional random vectors.* Cognitive Computation, 1(2), 139-159.
- **Concept Adapted**: Vector symbolic architectures with multiplicative binding and superposition bundle encoding.
- **Role in CARL-DX**: Implemented in [`brain/carl_episodic_memory.py`](file:///D:/ebca/brain/carl_episodic_memory.py) using 2048-dimensional holographic vectors.

### 4. Robot Body Schema & Sensorimotor Self-Modeling
- **Citation**: Hoffmann, M., Marques, H. G., Hernandez-Arieta, A., Sumioka, H., Lungarella, M., & Pfeifer, R. (2010). *Body schema in robotics: a review.* IEEE Transactions on Autonomous Mental Development, 2(4), 304-324.
- **Concept Adapted**: Recursive estimation of mass, inertia, and ground traction parameters from proprioceptive mismatch.
- **Role in CARL-DX**: Online parameter tracking in [`brain/carl_generative_self_model.py`](file:///D:/ebca/brain/carl_generative_self_model.py).

### 5. Multi-Timescale Cognitive Architecture
- **Citation**: Pezzulo, G., Rigoli, F., & Friston, K. (2018). *Hierarchical Active Inference: A Theory of Motivated Control.* Trends in Cognitive Sciences, 22(4), 294-306.
- **Concept Adapted**: Separation of high-frequency low-latency sensorimotor reflexes ($30\text{ Hz}$) from medium-frequency goal arbitration ($3\text{ Hz}$) and offline memory consolidation.
- **Role in CARL-DX**: Hierarchical loop separation in [`brain/carl_autonomous_agent.py`](file:///D:/ebca/brain/carl_autonomous_agent.py).
