# CARL STAGE 2.1B-R.3: LEARNED TRANSLATIONAL SELF-MODEL SPECIFICATION
**Classification:** Pre-Experimental Architecture & Falsification Protocol  
**Subsystem:** Generative Spatial Self-Model / Translational Distance Grounding  
**Author:** CARL Autonomous Development Laboratory  
**Date:** September 4, 2026  
**Status:** LOCKED & PRE-REGISTERED PRIOR TO UNSEEN EVALUATION  

---

## 1. Executive Summary & North Star Alignment

```text
CARL CANONICAL DEVELOPMENTAL ROADMAP
│
├── Stage 1 — Sensorimotor Grounding & Body Babbling           [COMPLETE]
│
├── Stage 2 — Generative World & Self Modeling                [CURRENT — ACTIVE]
│     └── Stage 2.1: Spatial Self / World Representation      [CURRENT — INCOMPLETE]
│           ├── 2.1A: Classical Spatial Baseline              [COMPLETE]
│           ├── 2.1B: Continuous Attractor (CANN) Memory      [COMPLETE]
│           ├── 2.1B-R: Recurrent Attractor Causality         [COMPLETE]
│           ├── 2.1B-R.2: Stochastic Motor Efference Copy     [COMPLETE — 5/5 UNSEEN PASS]
│           └── 2.1B-R.3: Global Spatial Distance Grounding   [ACTIVE SPECIFICATION]
│                 ├── Multi-Scale Coprime Grid Substrate      [PROVEN UNAMBIGUOUS (< 10mm)]
│                 └── Learned Translational Self-Model        [TARGET CAPABILITY]
│
├── Stage 2.2 — Predictive Sensory Synthesis & Future Rollout   [BLOCKED PENDING 2.1 CLOSURE]
├── Stage 3 — Continuous Action Synthesis & Behavioral Discovery
├── Stage 4 — Autopoietic / Lifelong Memory & Persistence
└── Stage 5 — Metacognition & Permission-Gated Self-Modification
```

### The Scientific Core Question
> *"Can CARL learn from its own sensorimotor experience how its motor commands translate into actual translational motion, and can that learned self-model improve long-range spatial grounding?"*

Prior evaluations demonstrated that while multi-scale coprime continuous attractor networks completely eliminate periodic grid aliasing (residual $< 9.8\,\text{mm}$, zero wrong wraps), CARL achieved only a $2/5$ pass rate on the $\le 0.22\,\text{m}$ homing gate. Forensic investigation proved that $69.8\%$ of the residual error stems from an ungrounded, hardcoded velocity assumption ($v_{\text{model}} = 1.200 \cdot u_{\text{fwd}}$) that failed to account for physical caster drag, turning scrub, and motor load.

In strict adherence to the governing principle:
> **"Engineer the substrate. Do NOT engineer the answer."**

This specification locks the architecture, learning rules, held-out validation criteria, and control matrix for learning an embodied translational self-model from autonomous experience.

---

## 2. Forensic Audit of Previous Estimators

### 2.1 The Hardcoded Defect in Previous Code
Previous implementations contained the following hardcoded line:
```python
v_wheel = 0.048 * (float(u[0]) + float(u[1])) * 12.5
```
This formula injected two privileged physical constants:
1. `0.048`: Hardcoded wheel radius ($r_{\text{wheel}} = 0.048\,\text{m}$).
2. `12.5`: Hardcoded actuator velocity scaling ($0.5 \times 25.0\,\text{rad/s}$).

The resulting coefficient $1.200\,\text{m/s}$ per unit of forward motor command assumed ideal rolling on frictionless surfaces. On the physical MuJoCo floor with rolling resistance and front/rear spherical casters, the actual linear chassis speed is $0.119\,\text{m/s}$ at $u_{\text{fwd}} = 0.110$ ($k_{\text{phys}} \approx 1.088\,\text{m/s}$). The $+13.6\%$ velocity overestimation integrated over 350 wandering ticks into an overshoot of $0.18\text{--}0.32\,\text{m}$, causing premature homing termination.

### 2.2 Rejection of Post-Hoc Hacks
Testing manual scale factors (e.g. Candidate C: $0.88v$) was rejected as benchmark fitting. The scaling factor must emerge from autonomous sensorimotor experience, not human tuning.

---

## 3. Mathematical Architecture of the Translational Self-Model

### 3.1 Sensorimotor Representation
CARL receives an unlabelled 25-D sensory vector $s_t \in \mathbb{R}^{25}$ and 6-D actuator command $u_t \in [-1, 1]^6$:
* Forward motor synergy: $u_{\text{fwd}}(t) = \frac{1}{2} (u_{\text{drive}, 0}(t) + u_{\text{drive}, 1}(t))$
* Differential motor synergy: $\Delta u(t) = u_{\text{drive}, 1}(t) - u_{\text{drive}, 0}(t)$
* Sensed angular velocity: $\omega_{\text{gyro}}(t) = s_t \cdot w_{\text{rot}}$ (via discovered gyro channel 20)

### 3.2 Translational Efference Model
The forward translational velocity is formulated as a learned self-model:
$$\hat{v}(t) = \max\left(0.0, k_{\text{trans}} \cdot u_{\text{fwd}}(t) \cdot \left(1.0 - \beta_{\text{drag}} \cdot \frac{|\Delta u(t)|}{u_{\text{fwd}}(t) + \epsilon}\right)\right)$$

Where:
* $k_{\text{trans}}$ is the developmental translational efference gain (grounding linear motor power into translational velocity).
* $\beta_{\text{drag}}$ is the learned lateral turning scrub coefficient (accounting for caster drag during differential steering).

### 3.3 Autonomous Developmental Learning Protocol
During developmental babbling on development seeds `[42, 101, 202]`:
1. CARL executes exploratory motor babbling sweeps $u_t$ and records sensory responses $s_t$.
2. **Channel Discovery:** CARL discovers the frontal range-rate channel by computing correlation with forward motor synergy:
   $$j^* = \arg\max_j \rho(u_{\text{fwd}}, -\dot{s}_j)$$
3. **Efference Calibration:** On valid approach intervals, CARL estimates $k_{\text{trans}}$ via least-squares regression:
   $$k_{\text{trans}} = \frac{\sum_t u_{\text{fwd}, t} \cdot (-\dot{s}_{j^*, t})}{\sum_t u_{\text{fwd}, t}^2}$$
4. **Permanent Freezing:** The learned parameters $(k_{\text{trans}}, \beta_{\text{drag}})$ are permanently frozen before evaluating unseen test seeds.

---

## 4. Strict Anti-Cheating & Data Separation Contracts

1. **Zero Privileged State:** Cognitive classes contain zero references to `qpos`, `qvel`, `cvel`, `xpos`, `contact`, `friction`, or simulator diagnostics.
2. **Separation of LAB vs CARL:**
   * CARL receives ONLY $s_t$ and $u_t$.
   * MuJoCo ground truth is used ONLY by external laboratory scoring scripts.
3. **Strict Partitioning:**
   * Development Seeds: `[42, 101, 202]` (model fitting, held-out validation, freezing).
   * Unseen Primary Test Seeds: `[303, 404, 505, 606, 707]` (strictly frozen evaluation).
4. **Zero Test-Time Adaptation:** No recalibration, learning rate updates, or seed-specific branches are allowed during unseen evaluation.

---

## 5. Mandatory Experimental Controls

| Condition | Architecture & Logic | Purpose |
| :--- | :--- | :--- |
| **A. Full Learned Translational Self-Model** | $k_{\text{trans}}$ learned via autonomous developmental experience | Experimental treatment |
| **B. Naive Motor-Only Baseline** | Commanded wheel scaling without empirical grounding ($1.200 \cdot u_{\text{fwd}}$) | Controls for uncalibrated motor integration |
| **C. Previous Stage 1.6 Estimator** | Grounded kinematic slip estimator using $ax_{\text{std}}$ and sonar | Replicates historical baseline |
| **D. Shuffled / Destroyed Sensor Control** | Permuted sensor channels and inverted motor contingencies | Establishes causal specificity |
| **E. Frozen Unseen Test** | Unseen seeds `[303, 404, 505, 606, 707]` evaluated under frozen model | Proof of out-of-distribution generalization |

---

## 6. Pre-Registered Acceptance Gate

* **Primary Metric:** Final homing drift $\le 0.22\,\text{m}$ across all 5 unseen test seeds.
* **Generalization Gate:** Unseen pass rate must be reported honestly. No mean-masking of catastrophic failures.
* **Stop / Go Ruling:** Advance to Stage 2.2 ONLY if the frozen learned model satisfies the gate across unseen seeds. If any seed fails, remain in Stage 2.1.
