# CARL Stage 3: Autonomous Behavioral Discovery & Continuous Policy Synthesis
## Formal Scientific Specification (CARL-STAGE3-SPEC-2026-09-08)

---

### Executive Summary & Classification
* **Document Status:** `LOCKED ARCHITECTURAL SPECIFICATION`
* **Version:** `1.0.0-PROSPECTIVE`
* **Classification:** `Embodied Cognitive Architecture — Stage 3 Developmental Milestone`
* **Predecessor Milestones:**
  - Stage 1.0 — 1.6: Hal-911 Anonymous Sensorimotor Embodiment & Kinematic Verification (`CERTIFIED`)
  - Stage 2.1 — 2.2: Grounded Spatial Memory, CANN Attractor & Raster Occupancy (`CERTIFIED`)
  - Stage 2.3-R1: Prospective Deliberation & Collision Veto Engine (`CERTIFIED`)
* **Scientific Focus:** Continuous trajectory optimization (MPPI), Active Inference (Free Energy Principle), and Autonomous Behavioral Discovery under unlabelled, unprivileged physical constraints.

---

```
                                  STAGE 3: ACTIVE INFERENCE BEHAVIORAL LOOP
                                                     │
                                                     ▼
                                     1. PROSPECTIVE DRIVE / HOMEOSTASIS
                                      (Energy Balance, Novelty Seeking)
                                                     │
                                                     ▼
                                   2. CONTINUOUS TRAJECTORY OPTIMIZATION
                                       (MPPI over M=128 Latent Gaits)
                                                     │
                                                     ▼
                                      3. DUAL-WORLD MENTAL SIMULATION
                                       Module 1: Grounded Kinematics
                                       Module 2: Complete Occupancy Grid
                                                     │
                                                     ▼
                                      4. EXPECTED FREE ENERGY MINIMIZATION
                                     G(π) = Epistemic Value + Pragmatic Value
                                                     │
                                                     ▼
                                    5. MOTOR SYNERGY DISCOVERY & STORAGE
                                    (Online Clustering into Primitive Primitives)
                                                     │
                                                     ▼
                                      6. UNPRIVILEGED PHYSICAL EXECUTION
                                         (6-Channel Anonymous HAL-911)
                                                     ↺
```

---

## 1. Theoretical Framework: Active Inference & Expected Free Energy

Stage 3 transitions CARL from choosing among discrete candidate action branches ($K=24$ in Stage 2.3) to **synthesizing continuous motor trajectories from first principles** using the Free Energy Principle (Friston et al.).

### 1.1 Expected Free Energy (EFE) Formulation
For any candidate motor trajectory $\pi = [u_0, u_1, \dots, u_{H-1}]$, the Expected Free Energy $G(\pi)$ over lookahead horizon $H$ is defined as:

$$G(\pi) = \sum_{\tau=1}^H G_\tau(\pi)$$

$$G_\tau(\pi) = \underbrace{-\mathbb{E}_{Q(o_\tau, s_\tau|\pi)} [\ln P(o_\tau)]}_{\text{Pragmatic / Homeostatic Value}} - \underbrace{\mathbb{E}_{Q(s_\tau|\pi)} [D_{\text{KL}}(Q(o_\tau|s_\tau) \parallel P(o_\tau))]}_{\text{Epistemic / Exploration Value}}$$

Where:
1. **Pragmatic / Homeostatic Term:** Measures deviation from preferred sensory states:
   $$\ln P(o_\tau) = - w_{\text{coll}} \cdot \mathbb{I}(\text{clr}_\tau < r_{\text{safe}}) - w_{\text{batt}} \cdot \max(0, 0.20 - \text{batt}_\tau)^2 + w_{\text{fwd}} \cdot v_{\text{fwd}, \tau}$$
2. **Epistemic / Information Gain Term:** Measures reduction of spatial uncertainty in the internal environment model $M_{\text{env}}$:
   $$\mathcal{I}_{\text{epistemic}}(\pi) = \sum_{\tau=1}^H \sum_{i \in \text{FOV}(\tau)} \mathcal{H}(M_{\text{env}}(x_i)) - \mathcal{H}(M_{\text{env}}(x_i) | o_\tau)$$

---

## 2. Continuous Trajectory Optimization: Model Predictive Path Integral (MPPI)

Rather than evaluating fixed candidate arcs, Stage 3 introduces a vectorized GPU/CPU MPPI controller sampling $M=128$ continuous trajectory perturbations around a mean nominal control sequence $U = [u_0, \dots, u_{H-1}] \in \mathbb{R}^{H \times 6}$.

### 2.1 Trajectory Perturbation Sampling
At control cycle $t$, $M$ perturbation sequences are sampled from a multivariate Gaussian:
$$\delta u^{(m)} \sim \mathcal{N}(0, \Sigma_u), \quad m \in \{1, \dots, M\}$$
$$u^{(m)}_\tau = \text{clip}(U_\tau + \delta u^{(m)}_\tau, -1.0, 1.0)$$

Where control channels represent the unlabelled 6-D actuator vector:
- Channel 0: Left drive wheel angular velocity
- Channel 1: Right drive wheel angular velocity
- Channel 2: Head Pan / Yaw servo
- Channel 3: Neck Tilt / Pitch servo
- Channel 4: Torso / Hip Pitch servo
- Channel 5: Torso / Hip Roll servo

### 2.2 Forward Mental Rollout
Each candidate $m$ is prospective unrolled across horizon $H=15$ ticks ($450\,\text{ms}$) through CARL's calibrated internal models:
1. **Module 1 (Kinematic Body Model):** Computes body displacement and orientation:
   $$(x_{\tau+1}, y_{\tau+1}, \theta_{\tau+1}) = f_{\text{body}}(x_\tau, y_\tau, \theta_\tau, u^{(m)}_\tau)$$
2. **Module 2 (Occupancy Memory Grid):** Projects sensor rays into $M_{\text{env}}$ (`arena_occupancy_grid.pt`, 1,611 physical obstacle cells):
   $$\hat{s}_\tau^{(m)} = \text{RayCast}(M_{\text{env}}, x_\tau, y_\tau, \theta_\tau)$$

### 2.3 Trajectory Weighting & Optimal Policy Synthesis
The cost of each candidate trajectory is evaluated as $S(\tau^{(m)}) = -G(\pi^{(m)})$.
Normalized weights are computed via temperature-scaled softmax:
$$w_m = \frac{\exp\left(-\frac{1}{\lambda} [S(\tau^{(m)}) - \min_j S(\tau^{(j)})]\right)}{\sum_{k=1}^M \exp\left(-\frac{1}{\lambda} [S(\tau^{(k)}) - \min_j S(\tau^{(j)})]\right)}$$

The optimal action executed on HAL-911 is:
$$u^*_0 = U_0 + \sum_{m=1}^M w_m \delta u^{(m)}_0$$

Nominal sequence $U$ is shifted forward by 1 step for warm-starting the subsequent cycle ($U_\tau \leftarrow U_{\tau+1}$).

---

## 3. Motor Synergies & Autonomous Primitive Discovery

A key discovery in embodied motor control is that biological organisms do not plan raw muscle activations indefinitely; they discover and consolidate **motor synergies** (Bernstein, 1967).

### 3.1 Online Trajectory Clustering (Concept Genesis)
When an synthesized trajectory successfully resolves an impasse (e.g. escaping an asymmetric trap, negotiating a 0.9m slit, or overcoming traction loss), it is encoded into a compact low-dimensional synergy representation:
$$\mathbf{z}_{\text{synergy}} = \text{PCA}_{k=4}(\{u^*_0, \dots, u^*_{H-1}\})$$

### 3.2 Dynamic Motor Repertoire
Discovered synergies are cataloged in `brain/carl_motor_synergies.py`:
- `synergy_corridor_cruise`: Coupled differential trim with balanced flank clearances.
- `synergy_flank_escape`: Forward-bias curvature avoiding tail-swing chassis collision.
- `synergy_hook_reverse`: High-curvature backward maneuver clearing convex dead-ends.
- `synergy_traction_limp`: Asymmetric duty-cycle locomotion maintaining linear trajectory under drive-wheel failure.

---

## 4. Experimental Validation Batteries

Stage 3 certification requires empirical validation across three challenging experimental batteries executed strictly on unprivileged physical embodiments:

### Battery 3A: U-Shaped Trap Obstacle Circumvention
* **Setup:** CARL is initialized facing into a 3-sided convex cul-de-sac ($1.5\,\text{m} \times 1.5\,\text{m}$).
* **Failure Mode of Baselines:** Potential field and reactive agents suffer limit-cycle trap lock or oscillate against the back wall.
* **Success Criterion:** CARL must autonomously discover and synthesize a multi-step reverse-turn-navigate escape trajectory within $\le 45$ ticks ($1.35\,\text{s}$) with $0\%$ collision rate across $N=50$ episodes.

### Battery 3B: Friction-Slip Surface Transition Adaptation
* **Setup:** Floor friction coefficient dynamically drops mid-run from $\mu=1.0$ (concrete) to $\mu=0.05$ (polished ice).
* **Failure Mode of Baselines:** Open-loop and fixed-gain controllers spin out or overshoot into walls due to unmodeled wheel slip.
* **Success Criterion:** Upon sensing odometry-gyro prediction error residuals $\Delta v > 0.10\,\text{m/s}$, CARL adapts its MPPI covariance and discovers a reduced-acceleration smooth gait, maintaining directional tracking within $\pm 0.15\,\text{m}$ cross-track error.

### Battery 3C: Asymmetric Actuator Impairment (Limping Gait Discovery)
* **Setup:** At $t=1.0\,\text{s}$, HAL channel 0 (Left Wheel) torque is halved ($k_{\text{gain}} \leftarrow 0.50$).
* **Failure Mode of Baselines:** Symmetric forward commands cause severe clockwise circular drift ($r < 0.5\,\text{m}$).
* **Success Criterion:** CARL detects heading deviation and discovers an asymmetric differential synergy ($u_L = 1.0, u_R = 0.50$), restoring straight-line navigation along the corridor.

---

## 5. Pre-Registered Acceptance Criteria for Stage 3 Gate Closure

To earn formal Stage 3 Certification, the implementation must meet all 7 locked criteria:

| Metric | Pre-Registered Standard | Verification Method |
| :--- | :--- | :--- |
| **MPPI Trajectory Latency** | $p95 \le 35.0\,\text{ms}$ (30 Hz control loop) | Microsecond timer per control step |
| **Battery 3A Trap Escape Rate** | $\ge 90.0\%$ escape within 60 ticks | Automated test suite ($N=50$) |
| **Battery 3B Ice Slip Stability** | $\le 10.0\%$ slip-induced spin-outs | Yaw variance under $\mu=0.05$ test |
| **Battery 3C Impairment Recovery** | $\le 0.20\,\text{m}$ cross-track heading drift | Corridor center tracking test |
| **Active Inference Epistemic Gain** | $\ge 40.0\%$ faster map entropy reduction | Shannon entropy of $M_{\text{env}}$ over time |
| **Statistical Significance** | $p < 0.001$ vs. Fixed Arc Deliberator | 2-sample independent $t$-test |
| **Zero Coordinate Injection** | Strict $0.0\%$ simulator pose leakage | Memory audit & HAL boundary check |

---

## 6. Architectural Boundary & Prohibitions

1. **No Oracle Privileged Pose Injection:**
   All localization must proceed via unprivileged internal dead reckoning (IMU gyro + wheel odometry).
2. **No Pre-Scripted Maneuvers:**
   All behaviors in Batteries 3A, 3B, and 3C must be discovered on-the-fly via MPPI sampling and EFE minimization.
3. **No External Network Dependencies:**
   All forward simulation and optimization must run locally on device within real-time compute limits.
