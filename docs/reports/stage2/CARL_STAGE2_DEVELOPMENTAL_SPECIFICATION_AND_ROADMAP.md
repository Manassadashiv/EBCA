# CARL STAGE 2: DEVELOPMENTAL SPECIFICATION & INCREMENTAL ROADMAP
## PERSISTENT SPATIAL REPRESENTATION & EMBODIED PREDICTIVE CONTROL
**Author:** Antigravity AI Orchestrator  
**Status:** **APPROVED FOR DEVELOPMENT (INCREMENTAL GATING)**  
**Target Milestone:** Stage 2.1 — Persistent Spatial Representation & Path Integration  
**Date:** September 3, 2026  

---

## 1. Executive Directive & Architectural Principles

Per explicit user guidance and forensic council audit, Stage 2 will **NOT** attempt a monolithic multi-subsystem jump. We reject the trap of simultaneously implementing:
$$\text{MPPI} + \text{CANN} + \text{RSSM} + \text{EKF} + \text{everything at once}$$

Instead, Stage 2 is structured into **three strictly modular, sequential developmental slices**:

```text
STAGE 1.6 (CONDITIONALLY CLOSED)
"I can estimate whether my locomotion is physically working."
                       │
                       ▼
STAGE 2.1 (IMMEDIATE TARGET)
"I can build a persistent internal representation of where I am and my heading."
(Continuous-Attractor Ring/Torus Network + Grounded Path Integration)
                       │
                       ▼
STAGE 2.2 (SUBSEQUENT MILESTONE)
"I can predict multi-step consequences into the future."
(Recurrent Multi-Step Latent Forward Model / World Model)
                       │
                       ▼
STAGE 2.3 (COMPETENCE MILESTONE)
"I can synthesize optimal multi-step trajectories in latent space."
(Bounded Parallel Trajectory Rollouts / Local MPPI)
```

Each slice must be independently implemented, falsified against strict acceptance criteria, and cleared through the Independent Council before the next slice is attempted.

---

## 2. Stage 2.1 Technical Specification: Path Integration & Spatial Representation

### 2.1 The Biological & Computational Premise
In mammalian spatial navigation (Moser & Moser, 2005; Burak & Fiete, 2009), the brain does not calculate Euclidean coordinates through matrix multiplication. It maintains spatial orientation via **Continuous-Attractor Neural Networks (CANN)**:
1. **Head-Direction Ring Attractor (HD Ring):** A 1D cyclic neural sheet of $N_{\text{HD}} = 64$ neurons. Synaptic connectivity forms a "Mexican hat" topology (local excitation, global inhibition). An activity bump forms spontaneously and shifts around the ring in response to angular velocity inputs $\omega_z$.
2. **2D Toroidal Grid Cell Attractor:** A 2D recurrent neural sheet ($32 \times 32 = 1,024$ neurons) with periodic boundary conditions. Translational velocity signals $(v_x, v_y)$ shift the activity bump across the sheet, producing periodic triangular spatial firing fields.

### 2.2 Grounding with Stage 1.6 Signals
Unlike naive path integrators that integrate raw wheel velocity commands, CARL Stage 2.1 will integrate **grounded kinematic body-state estimates** from Stage 1.6:
- Commanded angular rate $\omega_{\text{wheel}}$ modified by rotational tracking concordance $\gamma_{\text{rot}}$:
  $$\hat{\omega}_z = \omega_{z, \text{obs}} \quad \text{when } |\omega_z| \le 6.0\,\text{rad/s}$$
- Forward translation velocity $\hat{v}_x$:
  $$\hat{v}_x = v_{\text{wheel}} \cdot \gamma_{\text{traction}}$$
- **Traction-Gated Dead Reckoning:** When slip is detected ($\sigma > 0.52$), the spatial integrator knows the wheels are spinning without translating and **suppresses dead-reckoning integration**, preventing catastrophic position drift on ice!

### 2.3 Mathematical Model of the HD Ring Attractor
For neuron $i \in \{0, \dots, N-1\}$ with preferred heading $\theta_i = \frac{2\pi i}{N}$:
$$\tau \frac{du_i}{dt} = -u_i + \sum_{j=0}^{N-1} W_{ij} r_j + I_i^{\text{angular}}$$
where firing rate $r_j = \max(0, u_j)$, synaptic weight $W_{ij} = J_0 + J_1 \cos(\theta_i - \theta_j)$, and asymmetric velocity modulation:
$$I_i^{\text{angular}} = \alpha \cdot \hat{\omega}_z \cdot \sin(\theta_i - \theta_{\text{bump}})$$
shifts the bump along the ring proportionally to physical turning rate.

---

## 3. Strict Falsification Gates for Stage 2.1

Before Stage 2.1 can be considered verified, it must pass three adversarial test batteries:

### Battery 2.1A: Closed-Loop Trajectory Drift Benchmark
- CARL drives a closed square trajectory (Forward $0.5\,\text{m} \to$ Turn $90^\circ \to$ Forward $0.5\,\text{m} \to$ Turn $90^\circ \to$ Forward $0.5\,\text{m} \to$ Turn $90^\circ \to$ Forward $0.5\,\text{m} \to$ Turn $90^\circ$).
- *Gate Criterion:* Final internal heading error $\Delta \theta \le 12.0^\circ$. Final estimated position drift $\le 15.0\%$ of total path length ($1.5\,\text{m} \implies \text{drift} \le 0.225\,\text{m}$).

### Battery 2.1B: Low-Friction Immunity (Slip Isolation)
- CARL drives on normal floor (10 ticks) $\to$ enters glaze ice ($\mu = 0.005$, 20 ticks) with spinning wheels $\to$ exits back to dry floor.
- *Gate Criterion:* Internal spatial coordinate must **NOT** advance during the ice phase by more than $0.05\,\text{m}$. Naive wheel integration will register $\Delta x \approx 0.45\,\text{m}$ of false movement; CARL's slip-gated integrator must reject this false advance.

### Battery 2.1C: Multi-Seed Stability ($N=5$ Seeds)
- Evaluated across seeds `[42, 101, 202, 303, 404]`.
- *Gate Criterion:* $5/5$ seeds must maintain stable bump formation with zero spontaneous dissolution or saturation.

---

## 4. Work Breakdown & Execution Plan

| Step | Milestone Task | Deliverable | Acceptance Condition |
|:---:|:---|:---|:---|
| **2.1.1** | HD Ring Attractor (`carl_stage2_hd_ring.py`) | 64-neuron Continuous Attractor | Stable solitary bump; shift rate linear with $\omega_z$ ($R^2 > 0.95$) |
| **2.1.2** | Slip-Gated Integrator (`carl_stage2_spatial.py`) | 2D Toroidal Grid Cell Sheet | Velocity integration gated by $\sigma \le 0.52$; ice immunity verified |
| **2.1.3** | Sonar Landmark Anchoring | Sensory Reset / Phase Alignment | Walls and obstacles prevent cumulative drift accumulation |
| **2.1.4** | Adversarial Verification Suite (`test_stage2_1_suite.py`) | Automated PyTest Batteries | 100% pass across all 3 gates (2.1A, 2.1B, 2.1C) |
| **2.1.5** | Forensic LLM Council Review | Independent Audit Artifact | Zero math discrepancies; all seeds verified; honest report |

---

## 5. Summary Invariant

We build Stage 2 on real foundations:
- **No premature hype.**
- **No unverified GPU benchmarks.**
- **No multi-subsystem sprawl.**
- **One grounded capability at a time.**
