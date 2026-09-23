# CARL-DX FORENSIC FAILURE ANALYSIS & ROOT-CAUSE RESOLUTION LOG

**Mission Standard**: NASA-Inspired Systems Engineering Rigor  
**Target Repository**: `D:\ebca`

---

## 1. Forensic Summary of Evaluated Failure Modes

| Failure Mode Category | Initial State / Symptom | Root Cause Discovered | Remediation Implemented | Verification State |
| :--- | :--- | :--- | :--- | :--- |
| **F1: Vertical Jumping Misclassification** | Speculative claims of jump affordance | Absence of vertical prismatic linear actuators or explosive vertical recoil mechanisms ($Mg = 14.4\text{N} \gg F_{\text{dyn}} < 0.8\text{N}$) | Formally classified as `JUMP_CAPABILITY = PHYSICALLY_UNSUPPORTED` in compliance with Section 9 & 25 | **RESOLVED & RIGOROUSLY DOCUMENTED** |
| **F2: Deadlock in Dead-Ends & Wedges** | Agent stalled or entered infinite in-place spin loops when trapped | Pure homeostatic or curiosity drives lack forward controllability signal | Integrated `CarlEmpowermentCore` measuring $I(A_{1:H}; S_H)$ to anticipate and veto entropy-collapsing states before entry | **RESOLVED & VERIFIED** |
| **F3: Stale Controller Bias Across Resets** | Steering bias or integrator windup persisted across soft resets | Memory/steering persistence variables remained in agent instance | Added explicit `reset()` lifecycle clearing `active_steering_bias` and S-curve filters on reset | **RESOLVED & VERIFIED** |
| **F4: Motor Parameter Prediction Divergence** | Wheel slip under reduced friction led to persistent kinematic prediction error | Generative self-model assumed static nominal friction ($\mu = 2.50$) | Added recursive online friction estimation updating $\hat{\mu}$ based on measured speed vs wheel angular velocity | **RESOLVED & VERIFIED** |
| **F5: Episodic Memory Action-Name Mismatch** | Query unbinding used discrete legacy action keys (`GENTLE_LEFT`) while Dreamer used continuous arc keys | Lexical mismatch prevented Dreamer from receiving associative hazard warnings | Expanded `basis_actions` to include all continuous curvature arc primitives | **RESOLVED & VERIFIED** |

---

## 2. Unresolved Limitations & Boundary Constraints
1. **Vertical Obstacle Traversal**: Because CARL-DX is a wheeled non-holonomic mobile base with an ultra-low center of mass ($z_{\text{CoM}} = 0.052\text{m}$), obstacles with step heights exceeding wheel radius ($r = 0.048\text{m}$) cannot be physically traversed and must be circumvented.
2. **Visual Camera Frame Rate**: Onboard camera rendering at $1920\times 1080$ consumes $\sim 15\text{ms}$ per frame on CPU; real-time cognitive cycles execute at $30\text{ Hz}$ using low-overhead 15-ray proximity scans paired with periodic camera attention saccades.
