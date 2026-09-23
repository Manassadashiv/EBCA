# CARL-DX Stage 3.4 — Autonomous Behavioral Discovery under Active Inference
## Pre-Registered Benchmark Protocol & Scientific Governance Specification

```
========================================================================================
                          STAGE 3.4 PRE-REGISTERED PROTOCOL
========================================================================================
Protocol ID:            CARL-STAGE3-4-ACTIVE-INF-PROTO-2026-09-14-v4
Milestone:              Stage 3.4 — Autonomous Behavioral Discovery under Active Inference
Status:                 FROZEN PRIOR TO IMPLEMENTATION & BENCHMARKING ✅
Authority:              Lead Research Architect & Human Project Leadership
Pre-Registration Date:  September 14, 2026
Target System:          CARL-DX Embodied Organism (MuJoCo 3.3.4, vessel_kinetic.xml)
Governing Rule:         Zero threshold relaxation post-run. Strictly pre-registered gates.
Dependency:             Certified Stage 3.3 Continuous MPPI Substrate (Stage 3.4.0)
========================================================================================
```

---

## 1. Scientific Objective & Epistemological Taxonomy

### 1.1 The Four-Part Scientific Taxonomy
To prevent post-hoc rationalization, protocol contamination, and conflation of assumptions with empirical proof, all statements and components within Stage 3.4 are strictly classified into four distinct epistemological categories:

1. **[MATHEMATICAL DEFINITION]**: Axiomatic formulations, objective functions, probability distributions, observation models, and kinematics that define the computational substrate.
2. **[PRE-REGISTERED HYPOTHESIS]**: Mechanistic predictions formulated *ex ante* regarding how the mathematical optimization will behave under specific physical conditions, subject to falsification.
3. **[BENCHMARK MEASUREMENT]**: Empirical, quantitative observations directly recorded by automated test harnesses during trial execution (e.g., escape outcomes, latency, displacement, wheel velocities).
4. **[CERTIFICATION RESULT]**: Binary pass/fail adjudication of benchmark measurements against pre-registered acceptance thresholds in Section 6. The protocol *never* assumes that discovery will succeed prior to certification.

### 1.2 The Architectural Problem
In Stages 1 through 3.3, CARL acquired:
1. Sensorimotor grounding and unlabelled body babbling (Stage 1).
2. Continuous Attractor Neural Network (CANN) spatial heading and grid torus representations (Stage 2.1 / 3.1-R).
3. Grounded allocentric occupancy memory and body forward modeling (Stage 2.2-Grounded).
4. Continuous action synthesis via Model Predictive Path Integrals (MPPI, Stage 3.3).

However, all prospective trajectory scoring in Stage 3.3 was governed by **fixed heuristic objective weights** ($w_{\text{coll}}, w_{\text{margin}}, w_{\text{jerk}}, w_{\text{fwd}}, w_{\text{cann}}$). In non-convex environments—such as deep cul-de-sacs, dead-ends, or misleading obstacle pockets:
- A purely pragmatic forward agent drives into the trap, detects obstacle proximity, slows down, and stalls or bounces against the barrier.
- Classical robotics overcomes this through **handcoded state machines** (e.g., `if stuck: state = REVERSE; execute_reverse_primitive();`).
- In biological and autonomous cybernetic systems, composite maneuvers are not scripted rules. They are hypothesized to emerge naturally from **Expected Free Energy (EFE) minimization**, where actions are selected to simultaneously satisfy prior preferences (**pragmatic value**) and resolve environmental uncertainty (**epistemic value / information gain**).

### 1.3 Core Scientific Question
> **Can CARL autonomously discover and execute composite non-convex maneuvers (e.g., 3-point turns, reverse-pivot escapes, information-seeking corridor probing) purely through Expected Free Energy minimization over continuous MPPI trajectory rollouts, without handcoded maneuver rules, hardcoded state machines, or privileged simulator ground truth?**

---

## 2. Mathematical Formulation of Expected Free Energy

### 2.1 Expected Free Energy Definition [MATHEMATICAL DEFINITION]
Following active inference formulation (Friston et al.), the Expected Free Energy $G(\tau)$ for a prospective continuous trajectory rollout $\tau = (\mathbf{u}_0, \mathbf{u}_1, \dots, \mathbf{u}_{H-1})$ sampled over horizon $H=15$ ($dt=0.03\text{ s}$) is:

$$G(\tau) = G_{\text{pragmatic}}(\tau) + G_{\text{epistemic}}(\tau)$$

Where:
- $G_{\text{pragmatic}}(\tau)$ quantifies the risk or violation of prior organismic preferences (safety, target progress, effort).
- $G_{\text{epistemic}}(\tau)$ quantifies the expected information gain (salience / epistemic value) regarding the environment's occupancy state.

### 2.2 Pragmatic Value Formulation $G_{\text{pragmatic}}(\tau)$ [MATHEMATICAL DEFINITION]
The pragmatic term evaluates the expected divergence between predicted outcomes and desired prior preferences $P(\tilde{\mathbf{s}})$:

$$G_{\text{pragmatic}}(\tau) = w_{\text{coll}} J_{\text{coll}}(\tau) + w_{\text{margin}} J_{\text{margin}}(\tau) + w_{\text{jerk}} J_{\text{jerk}}(\tau) - w_{\text{cann}} J_{\text{cann}}(\tau) - w_{\text{fwd}} J_{\text{fwd}}(\tau)$$

Where:
1. **Collision Hazard $J_{\text{coll}}(\tau)$:** Trajectory points $\mathbf{p}_t$ evaluated against local allocentric occupancy memory $\mathcal{M}_{\text{occ}}$ via bilinear interpolation. If minimum clearance $< 0.12\text{ m}$, penalty $= +800.0$.
2. **Hull Safety Margin $J_{\text{margin}}(\tau)$:** Quadratic proximity cost when clearance $< 0.25\text{ m}$.
3. **Action Jerk Penalty $J_{\text{jerk}}(\tau)$:** Quadratic step-to-step delta penalty $\sum_{t=1}^{H-1} \|\mathbf{u}_t - \mathbf{u}_{t-1}\|^2$.
4. **CANN Heading Alignment $J_{\text{cann}}(\tau)$:** Alignment of endpoint heading $\theta_{H-1}$ with 64-unit Head-Direction ring population vector.
5. **Goal / Heading Progress $J_{\text{fwd}}(\tau)$:** Net displacement aligned with exploratory or global heading.

---

### 2.3 Bayesian Observation Model & Exact Information Gain Derivation [MATHEMATICAL DEFINITION]

#### Allocentric Spatial State
Let the allocentric spatial memory grid $\mathcal{M}_{\text{occ}}$ represent discrete spatial cells $c = (i, j)$. The true occupancy state of cell $c$ is a binary random variable:
$$C \in \{0, 1\}$$
where $C=1$ represents an occupied obstacle cell and $C=0$ represents a free traversable cell.

The organism maintains a probabilistic belief state parameterized by:
$$p_c = P(C = 1) \in [0, 1]$$
For unobserved, unexplored space, the belief state is initialized to the uninformative maximum-entropy prior:
$$p_{c, \text{prior}} = 0.50$$
The prior Shannon entropy of an unobserved cell is:
$$\mathcal{H}(p_c) = - p_c \log_2(p_c) - (1 - p_c) \log_2(1 - p_c)$$
$$\mathcal{H}(0.50) = - 0.5 \log_2(0.5) - 0.5 \log_2(0.5) = 1.0000\text{ bit}$$

#### Binary Sensor Likelihood Model
Along an anticipated sonar ray path traversing cell $c$, prospective sonar sensing yields a binary observation $Y \in \{0, 1\}$, where $Y=1$ denotes a reflective obstacle detection and $Y=0$ denotes a clear ray transmission.

The sensor observation likelihood is governed by pre-registered sensor reliability $\gamma$ and sensor noise / false-alarm rate $\epsilon$:
- **Sensor Reliability (True Positive / Hit Rate):** $P(Y = 1 \mid C = 1) = \gamma = 0.95$
- **Sensor Miss Rate (False Negative):** $P(Y = 0 \mid C = 1) = 1 - \gamma = \epsilon = 0.05$
- **True Negative Rate (Correct Rejection):** $P(Y = 0 \mid C = 0) = \gamma = 0.95$
- **False Alarm Rate (False Positive):** $P(Y = 1 \mid C = 0) = 1 - \gamma = \epsilon = 0.05$

#### Marginal Observation Likelihood
For an unobserved cell with prior $p_c = 0.50$, the marginal probability of observing $Y$ is:
$$P(Y = 1) = P(Y = 1 \mid C = 1) P(C = 1) + P(Y = 1 \mid C = 0) P(C = 0) = (0.95)(0.50) + (0.05)(0.50) = 0.5000$$
$$P(Y = 0) = P(Y = 0 \mid C = 1) P(C = 1) + P(Y = 0 \mid C = 0) P(C = 0) = (0.05)(0.50) + (0.95)(0.50) = 0.5000$$

#### Posterior Probability Update (Bayes' Rule)
Upon receiving observation $Y=1$ (obstacle detection):
$$p_{c \mid Y=1} = P(C = 1 \mid Y = 1) = \frac{P(Y = 1 \mid C = 1) P(C = 1)}{P(Y = 1)} = \frac{0.95 \times 0.50}{0.5000} = 0.9500$$

Upon receiving observation $Y=0$ (free space):
$$p_{c \mid Y=0} = P(C = 1 \mid Y = 0) = \frac{P(Y = 0 \mid C = 1) P(C = 1)}{P(Y = 0)} = \frac{0.05 \times 0.50}{0.5000} = 0.0500$$

#### Posterior Entropy Calculation
The Shannon entropy of the posterior distribution following an observation is:
$$\mathcal{H}(p_{c \mid Y=1}) = \mathcal{H}(0.95) = - 0.95 \log_2(0.95) - 0.05 \log_2(0.05)$$
Using exact logarithmic expansion:
$$\log_2(0.95) = \frac{\ln(0.95)}{\ln(2)} \approx -0.0740006\text{ bit}$$
$$\log_2(0.05) = \frac{\ln(0.05)}{\ln(2)} \approx -4.3219281\text{ bit}$$
$$\mathcal{H}(0.95) = - (0.95)(-0.0740006) - (0.05)(-4.3219281) = 0.0703006 + 0.2160964 = 0.2863970\text{ bit} \approx 0.2864\text{ bit}$$

By symmetry of the binary entropy function $\mathcal{H}(p) = \mathcal{H}(1-p)$:
$$\mathcal{H}(p_{c \mid Y=0}) = \mathcal{H}(0.05) = 0.2863970\text{ bit} \approx 0.2864\text{ bit}$$

#### Expected Posterior Entropy
The expected posterior entropy across possible observations is:
$$\mathbb{E}_{Y}[\mathcal{H}(p_{c \mid Y})] = P(Y = 1) \mathcal{H}(p_{c \mid Y=1}) + P(Y = 0) \mathcal{H}(p_{c \mid Y=0})$$
$$\mathbb{E}_{Y}[\mathcal{H}(p_{c \mid Y})] = (0.5000)(0.286397) + (0.5000)(0.286397) = 0.286397\text{ bit} \approx 0.2864\text{ bit}$$

#### Exact Derivation of Unexplored Cell Information Gain ($0.714\text{ bit}$)
The expected information gain (mutual information / entropy reduction) for an unexplored cell ($p_c = 0.50$) is therefore analytically derived as:
$$\Delta \mathcal{H}_c = \mathcal{H}(p_c) - \mathbb{E}_{Y}[\mathcal{H}(p_{c \mid Y})] = 1.0000\text{ bit} - 0.286397\text{ bit} = \mathbf{0.713603\text{ bit} \approx 0.714\text{ bit}}$$

- **Explored / Scanned Cells:** When a cell is already characterized as known-free ($p_c \le 0.05$) or known-occupied ($p_c \ge 0.95$), prior entropy is $\mathcal{H}(p_c) \le 0.2864\text{ bit}$. An additional observation produces negligible entropy reduction: $\Delta \mathcal{H}_c \approx 0.0\text{ bit}$.
- **Unexplored Cells:** An unobserved boundary cell ($p_c = 0.50$) produces the maximum information gain of $\mathbf{0.714\text{ bit}}$.

#### Prospective Trajectory Information Gain
The total epistemic utility for trajectory $\tau$ over prospective sensor ray paths $\Omega(\mathbf{p}_t, \theta_t)$ discounted by radial distance is:
$$G_{\text{epistemic}}(\tau) = - w_{\text{info}} \sum_{t=1}^H \sum_{c \in \Omega(\mathbf{p}_t, \theta_t)} \Delta \mathcal{H}_c \cdot \exp\left(-\frac{\|\mathbf{r}_c - \mathbf{p}_t\|_2}{\sigma_r}\right)$$
where $\sigma_r = 1.0\text{ m}$ geometrically discounts distant sensory projections.

---

### 2.4 Pre-Registered Mechanistic Hypotheses [PRE-REGISTERED HYPOTHESIS]

To strictly separate theoretical predictions from empirical results, the mechanistic interactions between EFE, sensor geometry, and kinematics are pre-registered as falsifiable hypotheses:

#### Hypothesis H1: Reverse-Aperture Expansion & Exit Re-Orientation
It is hypothesized that when CARL is trapped at a dead-end boundary:
1. Forward candidate trajectories produce minimal information gain ($\mathcal{I} \approx 0$) because the 15 forward sonar rays are occluded against known-occupied barrier cells at short range ($d < 0.15\text{ m}$), while incurring extreme pragmatic collision penalties ($J_{\text{coll}} \gg 0$).
2. Pure forward-rotation candidates in narrow corridors ($W \le 0.70\text{ m}$) cause the chassis outer perimeter ($R_{\text{hull}} = 0.14\text{ m}$) to violate hull margins against side walls.
3. Candidate trajectories featuring reverse-curvature actions ($\mathbf{u} = [v_x, \omega]$ with $v_x < 0, \omega \ne 0$) simultaneously achieve:
   - Physical stand-off expansion from the dead-end wall, reducing collision penalty.
   - Rotation of the forward-facing sonar arc toward previously unobserved exit corridors and lateral junctions, which contain high-entropy cells ($p_c \approx 0.50, \Delta \mathcal{H}_c \approx 0.714\text{ bit}$).
4. *Prediction:* Under full EFE scoring ($w_{\text{info}} = 1.0$), reverse-pivot trajectory candidates will obtain systematically lower total free energy $G(\tau)$ than forward or stationary candidates, resulting in the autonomous selection of reverse-pivot maneuvers without heuristic state transitions.

#### Hypothesis H2: Pragmatic-Only Failure Mode (Ablation Prediction)
It is hypothesized that under the pragmatic-only condition ($w_{\text{info}} = 0.0$, ARM-B):
1. Without the epistemic reward of unobserved space, candidate trajectories directed into the dead-end wall will decelerate to zero forward velocity due to collision avoidance.
2. Because reversing into previously traversed space yields zero forward progress and provides no pragmatic incentive to turn, the agent will enter an equilibrium stall or limit cycle near the barrier.
3. *Prediction:* ARM-B will fail to escape the non-convex cul-de-sac in $\ge 70\%$ of trials, producing a statistically significant performance deficit relative to ARM-A ($\Delta \text{Escape} \ge 35.0\%, p < 0.001$).

---

## 3. Controller-State Description & Anti-Cheat Architecture

### 3.1 Formal Deliberation Mapping & Legitimate Controller State [MATHEMATICAL DEFINITION]
Action selection in Stage 3.4 is **not** a purely stateless instantaneous function, nor is it a prohibited state machine. It is a receding-horizon optimization over continuous internal controller state.

The continuous cognitive decision mapping is formally defined as:
$$f_{\text{delib}}: (\mathbf{s}_t, \mathcal{M}_{\text{occ}}, \mathbf{r}_{\text{CANN}}, \bar{\mathbf{U}}_{t-1}) \mapsto (\mathbf{u}_t^*, \bar{\mathbf{U}}_t)$$

Where:
1. **$\mathbf{s}_t \in \mathbb{R}^{17}$:** Sanitized sensory state (15 sonar distances, wheel odometry speed $v_{\text{odom}}$, gyroscope yaw rate $\omega_{\text{gyro}}$).
2. **$\mathcal{M}_{\text{occ}} \in \mathbb{R}^{N_x \times N_y}$:** Allocentric occupancy memory grid maintaining evidence-accumulated cell beliefs $p_c \in [0, 1]$.
3. **$\mathbf{r}_{\text{CANN}} \in \mathbb{R}^{2114}$:** Neuromorphic Continuous Attractor Neural Network state (64-HD ring + 1,024-grid torus + 1,026 reservoir).
4. **$\bar{\mathbf{U}}_{t-1} \in \mathbb{R}^{H \times 2}$:** **Internal MPPI Nominal Control Trajectory** from the preceding timestep.

#### Warm-Start Nominal Control as Legitimate Controller State
At each control tick $t$, MPPI shifts the previous optimal nominal trajectory by one timestep:
$$\bar{\mathbf{u}}_\tau \leftarrow \bar{\mathbf{u}}_{\tau+1} \quad \text{for } \tau = 0, \dots, H-2, \quad \bar{\mathbf{u}}_{H-1} \leftarrow \bar{\mathbf{u}}_{H-2}$$
This nominal sequence $\bar{\mathbf{U}}_t$ serves as the mean around which $M=128$ candidate perturbations are sampled:
$$\mathbf{U}^{(m)} = \bar{\mathbf{U}}_t + \mathcal{E}^{(m)}, \quad \mathcal{E}^{(m)} \sim \mathcal{N}(\mathbf{0}, \mathbf{\Sigma}_u)$$
The warm-start sequence $\bar{\mathbf{U}}_t$ provides inter-step kinematic continuity and temporal coherence across 30 Hz cycles. It is a **legitimate continuous internal controller state** of the model predictive optimization process.

### 3.2 Distinction Between Controller State and Prohibited State Machines
To maintain scientific integrity, the distinction between permissible controller state and prohibited heuristic state machines is explicitly codified:

| Dimension | Legitimate Controller State (PERMITTED ✅) | Prohibited Maneuver State Machine (FORBIDDEN ❌) |
| :--- | :--- | :--- |
| **Mathematical Nature** | Continuous mathematical tensors ($\bar{\mathbf{U}} \in \mathbb{R}^{H \times 2}$, $\mathcal{M}_{\text{occ}}$, $\mathbf{r}_{\text{CANN}}$) | Discrete symbolic variables (`state = 'REVERSING'`, `phase = 2`, `mode = 'ESCAPE'`) |
| **Control Logic** | Soft path-integral weighted averaging over $M=128$ candidates: $\mathbf{u}_t^* = \sum_m w_m \mathbf{u}_{0}^{(m)}$ | Hard conditional branching: `if state == 'REVERSING': return u_reverse` |
| **Transition Trigger** | Dynamic minimization of continuous Expected Free Energy $G(\tau)$ | Heuristic threshold triggers: `if speed < 0.05: switch_state()` |
| **Timing Mechanism** | Receding horizon rollout evaluation ($H=15 \times 0.03\text{ s}$) | Integer tick counters: `reversal_ticks_remaining -= 1` |
| **Emergence** | Maneuvers emerge smoothly from path-integral trajectory sampling | Maneuvers are pre-programmed procedural macros (`execute_3_point_turn()`) |

### 3.3 Strictly Prohibited Structures (Violations Trigger Immediate `FAIL CLOSED`):
1. **Zero Programmatic State-Machine Variables:** No `state`, `phase`, `subtask`, `mode`, or equivalent discrete execution tracking variables in the cognitive decision pipeline.
2. **Zero Stuck / Velocity Threshold Triggers:** Zero conditional clauses that monitor speed, stall duration, or collision contacts to trigger behavioral changes (e.g., `if speed < 0.02: reverse()`).
3. **Zero Hardcoded Maneuver Sequences:** Zero scripted macro routines (e.g., `3_point_turn()`, `pivot_180()`, `back_up()`).
4. **Zero Environment-Specific Branching:** Zero conditional branches checking layout type, maze name, or obstacle coordinates (e.g., `if "cul_de_sac" in env_name:`).
5. **Zero Simulator Hooks / Privileged Overrides:** Zero direct manipulation of MuJoCo velocities, positions, or solver states to force an escape.

### 3.4 Automated AST Anti-Cheat Enforcement
The test harness [`tests/test_stage3_4_no_script_audit.py`](file:///d:/ebca/tests/test_stage3_4_no_script_audit.py) will parse the abstract syntax tree (AST) of [`brain/carl_active_inference.py`](file:///d:/ebca/brain/carl_active_inference.py) to guarantee:
- Exactly 0 occurrences of discrete state-variable assignments.
- Exactly 0 conditional statements evaluating low-velocity thresholds to initiate reversals.
- Continuous decision mapping operating strictly on sanitized sensory observations, occupancy memory, CANN state, and MPPI nominal trajectory tensors.

---

## 4. Matched-Arm Invariance Specification

To rigorously prove that composite maneuver discovery is causally driven by epistemic active inference, ARM-A and ARM-B must be strictly identical across all parameters except $w_{\text{info}}$:

| Parameter / Subsystem | ARM-A (Full Active Inference) | ARM-B (Pragmatic-Only Baseline) | Status |
| :--- | :---: | :---: | :---: |
| **Epistemic Info Weight $w_{\text{info}}$** | **$1.0$** | **$0.0$** | **ONLY EXPERIMENTAL VARIABLE** |
| **Pragmatic Collision Weight $w_{\text{coll}}$** | $800.0$ | $800.0$ | Identical Invariant |
| **Pragmatic Margin Weight $w_{\text{margin}}$** | $20.0$ | $20.0$ | Identical Invariant |
| **Pragmatic Jerk Weight $w_{\text{jerk}}$** | $10.0$ | $10.0$ | Identical Invariant |
| **CANN Alignment Weight $w_{\text{cann}}$** | $2.0$ | $2.0$ | Identical Invariant |
| **Forward Progress Weight $w_{\text{fwd}}$** | $5.0$ | $5.0$ | Identical Invariant |
| **MPPI Candidate Samples $M$** | $128$ | $128$ | Identical Invariant |
| **MPPI Horizon Steps $H$** | $15$ ($0.45\text{ s}$) | $15$ ($0.45\text{ s}$) | Identical Invariant |
| **MPPI Temperature $\lambda$** | $0.05$ | $0.05$ | Identical Invariant |
| **Sampling Covariance $\mathbf{\Sigma}_u$** | $\text{diag}(0.25, 0.25)$ | $\text{diag}(0.25, 0.25)$ | Identical Invariant |
| **Evaluation Timestep $dt$** | $0.030\text{ s}$ | $0.030\text{ s}$ | Identical Invariant |
| **Initial Pose & Velocity** | Exact Cloned State | Exact Cloned State | Identical Invariant |
| **Pre-Registered Evaluation Seeds** | `4001, 4002, 4003, 4004, 4005` | `4001, 4002, 4003, 4004, 4005` | Identical Invariant |
| **Physical Fixture Environments** | Identical XMLs | Identical XMLs | Identical Invariant |

---

## 5. Architectural Isolation Invariant & Evaluator Telemetry Firewall

In strict adherence to Rule 7 (*Zero Simulator Coordinates in Decision Pipeline*):
1. The cognitive active inference engine [`brain/carl_active_inference.py`](file:///d:/ebca/brain/carl_active_inference.py) must import **ONLY**:
   - `numpy`, `math`, `typing`, `pathlib`
   - Certified cognitive modules: `brain/carl_stage2_2_r2_occupancy_memory.py`, `brain/carl_mppi_deliberation.py`
2. **STRICTLY FORBIDDEN IMPORTS:**
   - Zero imports of `mujoco`
   - Zero imports of `brain.carl_stage1_hal` (HAL is quarantined strictly to test harnesses in `tests/`)
   - Zero access to simulator coordinates: `qpos`, `qvel`, `qacc`, `geom_xpos`, `mj_ray`, or simulator object IDs.
3. The cognitive module receives strictly sanitized inputs:
   - `sonars`: 15-channel numpy array ($s \in \mathbb{R}^{15}$)
   - `curr_v`: scalar forward speed estimate from wheel odometry
   - `curr_w`: scalar yaw rate from gyroscope sensor ($s[20]$)
4. **Gate 2 Evaluator Telemetry Firewall:**
   - Wheel velocities ($v_{\text{wheel}}$) and chassis orientation/heading ($\theta_{\text{world}}$) used to adjudicate emergent reversal and pivot behavior in Gate 2 are strictly **evaluator-only telemetry** recorded externally by the benchmark test harness.
   - Evaluator telemetry must **NEVER** be passed into the cognitive decision pipeline.
   - The cognitive controller continues receiving strictly the pre-registered sanitized inputs (`sonars`, `curr_v`, `curr_w`), allocentric memory $\mathcal{M}_{\text{occ}}$, CANN activity $\mathbf{r}_{\text{CANN}}$, and internal MPPI nominal control trajectory $\bar{\mathbf{U}}$.
   - Evaluator telemetry may be used solely for offline, post-run quantitative measurement and verification of Gate 2.

---

## 6. Pre-Registered Acceptance Gates

Stage 3.4 certification requires passing all 5 gates simultaneously under automated evaluation using fixed pre-registered seeds (`4001, 4002, 4003, 4004, 4005`) with zero manual intervention:

| Gate | Name | Pre-Registered Metric | Acceptance Threshold | Mandatory Failure Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 1** | **Autonomous Cul-de-Sac Escape Rate** | Successful exit from $1.8\text{ m}$ non-convex U-trap without collision or supervisor override across $N=40$ fixed-seed trials | **Escape Rate $\ge 80.0\%$ (32/40)** | Escape rate $< 80.0\%$ OR collision rate $> 10.0\%$ |
| **Gate 2** | **Emergent Maneuver Verification** | Spontaneous reversal ($v_{\text{wheel}} < -0.05\text{ m/s}$ for $\ge 10$ ticks) followed by orientation rotation ($|\Delta \theta| \ge 90^\circ$) without handcoded state transitions (evaluated via external telemetry firewall) | **$\ge 75.0\%$ of dead-end trials** exhibit authentic composite reversal-pivot | Any hardcoded state-machine trigger or maneuver conditional detected in audit |
| **Gate 3** | **Information-Gain Causal Necessity** | Paired ablation: Full Active Inference (ARM-A, $w_{\text{info}}=1.0$) vs Pragmatic-Only (ARM-B, $w_{\text{info}}=0.0$) across 40 matched seeds | **$\Delta \text{Escape} \ge 35.0\%$** AND exact one-sided McNemar **$p < 0.001$** | **$\Delta \text{Escape} < 35.0\%$ OR exact McNemar $p \ge 0.001$** |
| **Gate 4** | **Real-Time Cognitive Cycle Latency** | Deliberation latency over $N \ge 1,000$ active cycles ($M=128, H=15$) | **p95 latency $\le 45.0\text{ ms}$**; mean latency $\le 20.0\text{ ms}$ | **p95 latency $> 45.0\text{ ms}$ OR mean latency $> 20.0\text{ ms}$** |
| **Gate 5** | **Decision-Pipeline AST Anti-Cheat** | Static AST inspection across all Stage 3.4 active inference and deliberation files | **100% clean (0 simulator reads, 0 HAL imports)** | Any import of `mujoco`, `carl_stage1_hal`, or simulator state inside decision code |

### Gate 2 Evaluator Telemetry Firewall Specification
> [!IMPORTANT]
> **Firewall Separation of Evaluator Telemetry:**
> The physical wheel velocities ($v_{\text{wheel}} < -0.05\text{ m/s}$) and chassis heading changes ($|\Delta \theta| \ge 90^\circ$) used to adjudicate emergent reversal and pivot maneuvers are **evaluator-only telemetry** recorded externally by the benchmark test harness.
> - Evaluator telemetry must **NEVER** be passed into the cognitive decision pipeline or active inference engine.
> - The cognitive controller continues receiving strictly the pre-registered sanitized inputs (`sonars`, `curr_v`, `curr_w`), allocentric memory $\mathcal{M}_{\text{occ}}$, CANN activity $\mathbf{r}_{\text{CANN}}$, and internal MPPI nominal control trajectory $\bar{\mathbf{U}}$.
> - Evaluator telemetry is restricted exclusively to offline, post-run adjudication of Gate 2 compliance.

### Critical Statistical Independence Specification for Gate 3
> [!IMPORTANT]
> **Independence of Effect Size and $p$-Value Thresholds on $N=40$ Matched Pairs:**
> Passing the effect size threshold $\Delta \text{Escape} \ge 35.0\%$ does **NOT** mathematically guarantee passing the significance threshold $p < 0.001$. Both are independent mandatory gates.
>
> In an exact one-sided McNemar test over $N=40$ matched pairs, $\Delta \text{Escape} = \frac{n_{10} - n_{01}}{40} \ge 0.35$ requires a net discordant difference $n_{10} - n_{01} \ge 14$.
> However, the exact one-sided binomial $p$-value depends on the total number of discordant pairs $n_{\text{disc}} = n_{10} + n_{01}$:
> - If $n_{10} = 17$ and $n_{01} = 3$, then $n_{10} - n_{01} = 14$ ($\Delta \text{Escape} = 35.0\%$). But with $n_{\text{disc}} = 20$, the exact one-sided $p$-value is:
>   $$p = \sum_{k=17}^{20} \binom{20}{k} 0.5^{20} = \frac{1140 + 190 + 20 + 1}{1,048,576} = \frac{1,351}{1,048,576} \approx \mathbf{0.001288 \ge 0.001000} \implies \text{\textbf{FAIL CLOSED}}$$
> - If $n_{10} = 15$ and $n_{01} = 1$, then $n_{10} - n_{01} = 14$ ($\Delta \text{Escape} = 35.0\%$), and $n_{\text{disc}} = 16$:
>   $$p = \sum_{k=15}^{16} \binom{16}{k} 0.5^{16} = \frac{16 + 1}{65,536} = \frac{17}{65,536} \approx \mathbf{0.000259 < 0.001000} \implies \text{\textbf{PASS}}$$
> 
> Therefore, Gate 3 enforces **both** $\Delta \text{Escape} \ge 35.0\%$ AND $p < 0.001$. Any run where $p \ge 0.001$ triggers an immediate mandatory `FAIL CLOSED`.

---

## 7. Required Visual Evidence & Artifact Manifest

All generated evidence must be saved in `evidence/stage3_4/` prior to any certification claim. Specifications are strictly neutral and do not presuppose successful behavioral emergence:

1. **Publication-Grade Figures (`evidence/stage3_4/figures/`):**
   - `fig1_expected_free_energy_landscape.png`: Heatmap showing candidate trajectory costs decomposed into pragmatic vs epistemic components.
   - `fig2_cul_de_sac_trajectories.png`: Overlaid 2D physical paths recording trial trajectories and empirically observed behavioral outcomes (escape, stall, collision) across experimental arms.
   - `fig3_entropy_reduction_dynamics.png`: Time-series plot of map entropy $\mathcal{H}_{\text{map}}(t)$ during exploration and escape attempts.
   - `fig4_comparative_escape_rates.png`: Bar chart comparing ARM-A, ARM-B, ARM-C, and ARM-D escape and collision rates.
   - `fig5_stage3_4_formal_certification_matrix.png`: Formal 5-gate scorecard table.
2. **Synchronized Video Demonstrations (`evidence/stage3_4/videos/`):**
   - `video_cul_de_sac_behavioral_trial.mp4`: 720p 30 FPS side-by-side video recording robot POV, allocentric occupancy grid entropy evolution, MPPI trajectory fan, and the neutrally reported observed behavioral outcome (escape, stall, collision, or other measured dynamics).
   - `video_pragmatic_vs_active_showdown.mp4`: Side-by-side comparative recording of ARM-A (Full Active Inference) and ARM-B (Pragmatic-Only Baseline) under identical initial conditions, documenting whatever behavioral outcomes are empirically observed (escape, stall, collision, or other measured behavior) without presupposing success.
3. **Machine-Readable Scorecards (`evidence/stage3_4/`):**
   - `stage3_4_scorecard.json`: Full machine-readable gate outcomes, contingency tables, latencies, and $p$-values.
   - `stage3_4_raw_trials.json`: Tick-by-tick trajectory coordinates, motor actions, and EFE component logs for all 160 episodes.

---

## 8. Epistemological Adjudication Boundaries

To guarantee complete scientific rigor across all reporting:
- **[MATHEMATICAL DEFINITION]**: Equations (Section 2) are verified for numerical and dimensional correctness prior to execution.
- **[PRE-REGISTERED HYPOTHESIS]**: Predictions (Section 2.4) remain hypotheses until empirically tested; they are never treated as established facts in the protocol.
- **[BENCHMARK MEASUREMENT]**: The automated test harness records empirical outcomes without bias, manual intervention, or runtime parameter modification.
- **[CERTIFICATION RESULT]**: Certification is granted if and only if all 5 acceptance thresholds in Section 6 are satisfied. If any metric violates its threshold, Stage 3.4 will be declared `FAILED CLOSED` with remediation required.

```
========================================================================================
                      END OF STAGE 3.4 PRE-REGISTERED PROTOCOL
========================================================================================
```
