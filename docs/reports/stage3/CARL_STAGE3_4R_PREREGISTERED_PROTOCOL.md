# CARL-DX STAGE 3.4-R PRE-REGISTERED PROTOCOL
**Authoritative Forensic Remediation & Causal Necessity Battery: Autonomous Behavioral Discovery under Active Inference**

```
========================================================================================
                               PROTOCOL CONTROL & METADATA
========================================================================================
Protocol ID:            CARL-STAGE3-4R-ACTIVE-INF-REMED-2026-09-14-v3
Milestone:              Stage 3.4-R — Continuous Active Inference Remediation & Necessity
Document Path:          D:\ebca\CARL_STAGE3_4R_PREREGISTERED_PROTOCOL.md
Historical Predecessor: CARL-STAGE3-4-ACTIVE-INF-PROTO-2026-09-14-v4 (FAILED CLOSED ❌)
Primary Scientific Q:   What computational mechanism is necessary to transform CARL's
                        emergent reversal/pivot behavior into reliable multi-step escape,
                        and is the combined epistemic objective causally necessary for that
                        transformation?
Episode Accounting:     200 Preregistered Certification Episodes (50 matched configs x 4 arms)
                        + 10 Non-Binding Pre-Flight Diagnostic Episodes
                        = 210 Physical Episodes Total (if both phases are executed).
Factorial Invariant:    Disentangle physical turning clearance from epistemic inference.
Adjudication Standard:  Fail-Closed Pre-Registration (Zero Compensatory Scoring)
Adjudication Engine:    Exact One-Sided McNemar Test (alpha = 0.001) + Contact Manifolds
========================================================================================
```

---

## 1. Epistemological Grounding & Permanent Baseline

### 1.1 Non-Negotiable Governance Invariants
1. **Stage 3.4 v4 Remains Permanently FAILED CLOSED ❌**: Stage 3.4 v4 is not reopened, rewritten, reinterpreted, or altered. Its 0.0% escape rate, 65.0% collision rate, scorecard, and raw trials remain immutable historical evidence.
2. **Stage 3.3 Remains Certified and Frozen ✅**: The Stage 3.3 continuous MPPI substrate is not modified or rewritten.
3. **Stage 3.5 Remains Strictly LOCKED 🔒**: No work on Stage 3.5 (Physical Perturbations & Adaptation) is permitted until Stage 3.4-R is certified.
4. **No Parameter Tuning Against Failed Benchmarks**: Algorithmic adjustments must be derived from fundamental mathematical principles and validated through pre-registered hypotheses, never post-hoc curve fitting.
5. **Strict Evaluator Firewall**: Evaluator telemetry ($v_{\text{wheel}}$, $\theta_{\text{world}}$) remains strictly quarantined outside the cognitive decision pipeline.
6. **No Scripted State Machines or Maneuver Macros**: Action synthesis must remain continuous trajectory optimization over continuous controls $\mathbf{u} \in [-1.0, 1.0]^2$.

---

## 2. Factorial Diagnostic Matrix: Disentangling Geometry from Inference

To prevent confounding a physical geometry change (turning bay) with an algorithmic remediation (frontier inference), Stage 3.4-R implements a strict factorial design:

```
===================================================================================================================
                                          FACTORIAL DIAGNOSTIC MATRIX
===================================================================================================================
Geometry Condition       | Cognitive Objective    | Role in Milestone      | Scientific Question Answered
-------------------------+------------------------+------------------------+---------------------------------------
A. Old Tight Cul-de-Sac  | Local EFE (Stage 3.4)  | Historical Baseline    | Did tight geometry cause 100% of
   (W = 0.70m)           | (w_info = 1.0)         | (Frozen Record ❌)     | lateral wall strikes? (YES, proven)
-------------------------+------------------------+------------------------+---------------------------------------
B. Turning Bay           | Local EFE (Stage 3.4)  | Pre-Flight Diagnostic  | Does physical clearance ALONE enable
   (W_bay = 1.30m)       | (w_info = 1.0)         | (N = 10 frozen trials) | full escape without frontier pull?
-------------------------+------------------------+------------------------+---------------------------------------
C. Turning Bay           | Frontier Active Inf    | Primary Certification  | Does frontier information potential
   (W_bay = 1.30m)       | (w_info = 1.0) [ARM-A] | Benchmark (N = 50)     | enable sustained multi-step escape?
-------------------------+------------------------+------------------------+---------------------------------------
D. Turning Bay           | Pragmatic-Only         | Primary Causal Control | Can the robot escape WITHOUT
   (W_bay = 1.30m)       | (w_info = 0.0) [ARM-B] | Benchmark (N = 50)     | epistemic information gain?
===================================================================================================================
```

### 2.1 Frozen Pre-Flight Diagnostic Specification (N = 10 Trials)
- **Environment**: `cul_de_sac_turning_bay.xml`.
- **Controller**: Stage 3.4 Local EFE ($w_{\text{info}} = 1.0$, $\lambda_{\text{frontier}} = 0.0$).
- **Frozen Configurations**: Exactly 10 matched spawn states from Environment 1:
  - Seed 5001: Configs 0, 1
  - Seed 5002: Configs 4, 5
  - Seed 5003: Configs 8, 9
  - Seed 5004: Configs 12, 13
  - Seed 5005: Configs 16, 17
- **Strict Governance Rule on Pre-Flight Diagnostic**:
  > **The pre-flight diagnostic is strictly exploratory and non-binding on certification parameters.** Its sole scientific purpose is to record whether turning clearance alone permits complete escape under local EFE. Diagnostic outcomes SHALL NOT alter, relax, rebalance, or re-tune the certification acceptance gates, objective weights, geometry, or sample allocations of the Stage 3.4-R battery.

---

## 3. Mathematical Formulation of Frontier Active Inference `[MATHEMATICAL DEFINITION]`

### 3.1 Total Expected Free Energy
Candidate trajectories $\tau = (\mathbf{x}_{0:H}, \mathbf{u}_{0:H-1})$ are evaluated by minimizing:
$$G(\tau) = G_{\text{pragmatic}}(\tau) + w_{\text{info}} \cdot G_{\text{epistemic}}(\tau)$$

Where $G_{\text{pragmatic}}(\tau)$ is identical to Stage 3.3/3.4:
$$G_{\text{pragmatic}}(\tau) = w_{\text{coll}} \sum_{t=1}^H \mathbb{I}[d_t \le r_{\text{hull}}] + w_{\text{margin}} \sum_{t=1}^H \max(0, d_{\text{margin}} - d_t)^2 + w_{\text{jerk}} \sum_{t=1}^{H-1} \|\mathbf{u}_t - \mathbf{u}_{t-1}\|^2 - w_{\text{fwd}} \sum_{t=0}^{H-1} \bar{v}_t + J_{\text{steer}}$$

### 3.2 Epistemic Information Gain & Frontier Potential
The epistemic term combines local ray Shannon entropy reduction with allocentric frontier progress:
$$G_{\text{epistemic}}(\tau) = - \left( \Delta \mathcal{H}_{\text{local}}(\tau) + \Phi_{\text{frontier}}(\tau) \right)$$

#### Exact Mathematical Specification of $\Phi_{\text{frontier}}(\tau)$
Let the 2D spatial occupancy memory be a discrete grid $\mathcal{G} \subset \mathbb{R}^2$ with resolution $\delta = 0.10\text{ m}$:
- Channel 0: Obstacle hit density $O(i, j) \in [0, 10.0]$
- Channel 1: Observation / visibility mask $V(i, j) \in [0.0, 1.0]$

1. **Free Explored Cell Condition**:
   A cell $(i, j)$ is free and explored if:
   $$V(i, j) \ge 0.50 \quad \text{and} \quad O(i, j) < 0.30$$

2. **Unexplored Cell Condition**:
   A cell $(i, j)$ is unexplored if:
   $$V(i, j) < 0.50$$

3. **Frontier Cell Set $\mathcal{F}$**:
   A cell $(i, j)$ is an element of the frontier set $\mathcal{F}$ if and only if:
   $$(i, j) \text{ is a Free Explored Cell} \quad \wedge \quad \exists (i', j') \in \mathcal{N}_8(i, j) \text{ s.t. } V(i', j') < 0.50 \quad \wedge \quad d_{\text{obs}}(i, j) \ge r_{\text{hull}}$$
   Where $\mathcal{N}_8(i, j)$ is the 8-connected Moore neighborhood, and $d_{\text{obs}}(i, j) \ge 0.17\text{ m}$ ensures safe hull clearance.

4. **Frontier Information Potential**:
   Let $\mathbf{f}^* \in \mathcal{F}$ be the nearest valid frontier coordinate to the current robot position $\mathbf{x}_0$:
   $$\mathbf{f}^* = \arg\min_{\mathbf{f} \in \mathcal{F}} \|\mathbf{x}_0 - \mathbf{f}\|_2$$
   For candidate rollout $\tau$ with terminal position $\mathbf{x}_H$:
   $$\Delta d_{\text{frontier}}(\tau) = \|\mathbf{x}_0 - \mathbf{f}^*\|_2 - \|\mathbf{x}_H - \mathbf{f}^*\|_2$$
   $$\Phi_{\text{frontier}}(\tau) = \lambda_{\text{frontier}} \cdot \Delta d_{\text{frontier}}(\tau)$$
   Where:
   - $\lambda_{\text{frontier}} = 8.0$ (fixed, pre-registered scaling weight).
   - If $\mathcal{F} = \emptyset$ (arena fully explored), $\Phi_{\text{frontier}}(\tau) = 0.0$.
   - **Strict Invariance**: When $w_{\text{info}} = 0.0$ (ARM-B), $G_{\text{epistemic}} \equiv 0.0$ and $\Phi_{\text{frontier}} \equiv 0.0$.

---

## 4. Test Environments & Sample Allocation (N = 50 Configurations, 200 Episodes)

The benchmark executes across two standardized test environments with strict sample balance:

### 4.1 Environment Allocation (20 + 30 Matched Configurations = 50 Total)
1. **Environment 1: Cul-de-Sac with Rotational Turning Bay (`cul_de_sac_turning_bay.xml`)**:
   - Corridor length $1.80\text{ m}$, width $0.70\text{ m}$.
   - Dead-end expands into a rectangular turning bay of width $W_{\text{bay}} = 1.30\text{ m}$ ($2.7 \times$ chassis length) for $x \in [0.35, 0.85]$.
   - Preserves exact $1.10\text{ m}$ escape depth while eliminating unphysical lateral wall strikes during $180^\circ$ turns.
   - **Sample Allocation**: Configurations 0–19 (4 matched spawn variations $\times 5$ seeds: `5001, 5002, 5003, 5004, 5005`).

2. **Environment 2: Asymmetric Epistemic T-Junction (`asymmetric_t_junction.xml`)**:
   - Robot approaches T-junction from a corridor facing North.
   - East branch is a dead-end pocket ($1.20\text{ m}$ deep); West branch opens into a wide arena ($3.0\text{ m} \times 3.0\text{ m}$).
   - Sonars at spawn and junction are locally symmetrical, isolating epistemic necessity from collision avoidance.
   - **Sample Allocation**: Configurations 20–49 (6 matched spawn variations $\times 5$ seeds: `5001, 5002, 5003, 5004, 5005`).
   - **Statistical Feasibility**: With $N=30$, an effect size of $\Delta = 40\%$ (12 net discordant pairs) makes an exact one-sided McNemar $p < 0.001$ mathematically attainable (e.g. at $b=12, c=0$, $p = 2^{-12} = 0.000244 < 0.001$), whereas it was mathematically impossible at $N=20$ ($2^{-8} = 0.0039 > 0.001$).

### 4.2 Four Experimental Arms & Episode Accounting
```
===================================================================================================================
                                         EXPERIMENTAL ARMS SPECIFICATION
===================================================================================================================
Arm ID   | Name                                | w_info | Memory Substrate   | Planning Dynamics
---------+-------------------------------------+--------+--------------------+-------------------------------------
ARM-A    | Full Active Inference + Frontier EFE|  1.0   | Allocentric 2-Ch   | Continuous MPPI (M=128, H=15)
ARM-B    | Pragmatic-Only Baseline             |  0.0   | Allocentric 2-Ch   | Continuous MPPI (Strictly Matched)
ARM-C    | Amnesic Active Inference (No Memory)|  1.0   | Erased Each Tick   | Continuous MPPI (Instantaneous)
ARM-D    | Frozen Stage 2 Discrete Baseline    |  N/A   | Allocentric Raster | Discrete 7-Primitive Tree
===================================================================================================================
```

#### Authoritative Physical Episode Accounting
- **Pre-Flight Diagnostic Phase**: 10 non-binding physical episodes (Turning Bay + Stage 3.4 Local EFE).
- **Authoritative Certification Phase**: 50 matched configurations $\times 4$ arms = **200 physical certification episodes**.
- **Total Physical Execution Workload**: **210 physical episodes total** across both phases.
- The certification sample size remains strictly fixed at 200 episodes.

---

## 5. Pre-Registered Acceptance Gates

```
===================================================================================================================
                                      STAGE 3.4-R CERTIFICATION GATES
===================================================================================================================
Gate ID  | Description                         | Acceptance Threshold              | Mandatory Failure Condition
---------+-------------------------------------+-----------------------------------+-------------------------------
Gate 1   | Autonomous Task Completion Rate     | ARM-A Only (N = 50 configs):      | ARM-A Escape < 80.0% OR
         | & Physical Collision Ceiling        | Escape Rate >= 80.0% (40/50)      | ARM-A Collision Rate > 10.0%
         |                                     | AND Collision Rate <= 10.0% (5/50)|
---------+-------------------------------------+-----------------------------------+-------------------------------
Gate 2   | Complete Emergent Maneuver          | ARM-A Only (N = 50 configs):      | ARM-A Emergence Rate < 75.0%
         | Verification (External Firewall)    | >= 75.0% (38/50) complete         | OR scripted state machine detected
         |                                     | composite sequence:               | 
         |                                     | Reversal (v < -0.05m/s >= 10 tk)  | 
         |                                     | -> Pivot (|Delta th| >= 90 deg)   | 
         |                                     | -> Egress (v > +0.05m/s >= 15 tk) | 
---------+-------------------------------------+-----------------------------------+-------------------------------
Gate 3   | Epistemic-Objective Causal          | Environment 2 (N = 30 pairs):     | Env 2 Delta < 40.0% OR
         | Necessity                           | Delta >= 40.0% (>= 12 net pairs)  | Env 2 McNemar p >= 0.001 OR
         | (Environment-Separated McNemar)     | AND Env 2 exact McNemar p < 0.001 | Pooled McNemar p >= 0.001
         |                                     | AND Pooled (N = 50 pairs):        | 
         |                                     | Delta >= 35.0% AND p < 0.001      | 
---------+-------------------------------------+-----------------------------------+-------------------------------
Gate 4   | Real-Time Cognitive Cycle Latency   | Mean Latency <= 20.0 ms           | Mean Latency > 20.0 ms OR
         | (N >= 1,000 cycles across arms)     | AND p95 Latency <= 45.0 ms        | p95 Latency > 45.0 ms
---------+-------------------------------------+-----------------------------------+-------------------------------
Gate 5   | Decision-Pipeline AST Anti-Cheat    | 100% Clean Static & Dynamic Audit | Any simulator coordinate read
         | & No-Script Quarantine              | (0 sim coordinates, 0 macros)     | or scripted macro in pipeline
===================================================================================================================
```

### Operational Criteria for Gate 2 (Complete Emergent Sequence)
Evaluated strictly on **ARM-A** by the external evaluator harness without passing telemetry to the controller:
1. **Phase 1 (Reversal)**: Physical wheel speed $v_{\text{wheel}} < -0.05\text{ m/s}$ sustained for $\ge 10$ consecutive simulation ticks.
2. **Phase 2 (Orientation Inversion)**: Absolute heading rotation $|\Delta \theta| \ge 90^\circ$ relative to initial spawn heading.
3. **Phase 3 (Corridor Egress)**: Re-entry into the egress channel ($x \le 0.35\text{ m}$ in Env 1, or turn into open West branch in Env 2).
4. **Phase 4 (Sustained Forward Egress)**: Forward physical wheel speed $v_{\text{wheel}} \ge +0.05\text{ m/s}$ sustained for $\ge 15$ consecutive ticks toward the exit without physical collision.

### Operational Criteria for Gate 3 (Epistemic-Objective Causal Necessity & Statistical Independence)
Effect size and statistical significance are independent mandatory criteria; satisfying the effect-size threshold does not guarantee $p < 0.001$. Both criteria must be satisfied by the observed paired outcomes.

- **Scope of Causal Attribution**:
  ARM-A evaluates the combined epistemic navigation objective $G_{\text{epistemic}} = -(\Delta \mathcal{H}_{\text{local}} + \Phi_{\text{frontier}})$, where $\Delta \mathcal{H}_{\text{local}}$ is local expected information gain and $\Phi_{\text{frontier}}$ is allocentric frontier progress potential. Therefore, Gate 3 tests the causal necessity of the **COMBINED pre-registered epistemic objective**, not Bayesian local information gain in isolation. Success establishes the necessity of the combined epistemic objective (information gain + frontier attraction) over the pragmatic-only baseline (ARM-B).

- **Independent Dual-Criteria Invariant**:
  A given $\Delta\text{Escape}$ does NOT mathematically imply $p < 0.001$. 
  - *Counterexample 1 (Env 2, $N=30$)*: An outcome of $b=21, c=9$ gives $\Delta = (21-9)/30 = 40.0\%$, but exact one-sided McNemar $p = \sum_{k=21}^{30} \binom{30}{k} 0.5^{30} \approx 0.0214 \not< 0.001$. Gate 3 FAILS.
  - *Counterexample 2 (Pooled, $N=50$)*: An outcome of $b=34, c=16$ gives $\Delta = (34-16)/50 = 36.0\% \ge 35.0\%$, but exact one-sided McNemar $p = \sum_{k=34}^{50} \binom{50}{k} 0.5^{50} \approx 0.00767 \not< 0.001$. Gate 3 FAILS.
  - Therefore, both the effect size ($\Delta \ge 40\%$ in Env 2, $\Delta \ge 35\%$ pooled) AND the exact significance ($p < 0.001$) are independent mandatory hurdles. Neither compensates for the other.

- **Environment 2 Acceptance Requirements ($N = 30$ matched configurations)**:
  - ARM-A vs ARM-B paired discordance: $\Delta\text{Escape} = \frac{b - c}{30} \ge 40.0\%$ ($\ge 12$ net pairs).
  - Exact one-sided McNemar test: $p < 0.001$.
- **Environment 1 Analysis ($N = 20$ matched configurations)**:
  - Multi-step emergence evaluated in turning bay; reported alongside Environment 2.
- **Pooled Across All $N = 50$ Pairs**:
  - $\Delta\text{Escape} = \text{Escape}(\text{ARM-A}) - \text{Escape}(\text{ARM-B}) \ge 35.0\%$ ($\ge 18$ net pairs).
  - Exact one-sided McNemar test: $p < 0.001$.

---

## 6. Required Evidence Artifacts

1. **Machine-Readable Telemetry**:
   - `evidence/stage3_4R/stage3_4R_scorecard.json` (Includes pooled, Env 1, and Env 2 metrics).
   - `evidence/stage3_4R/stage3_4R_raw_trials.json` (Full 200-episode telemetry, actions, trajectories).
2. **Publication Figures (`evidence/stage3_4R/figures/`)**:
   - `fig1_factorial_diagnostic_comparison.png`: Factorial comparison separating geometry effect from frontier inference.
   - `fig2_turning_bay_and_tjunction_trajectories.png`: 4-panel trajectory plots across Env 1 and Env 2.
   - `fig3_frontier_entropy_dynamics.png`: Sustained entropy reduction and frontier potential time-series.
   - `fig4_comparative_escape_rates.png`: Comparative bar plot with environment breakdown and 95% Wilson intervals.
   - `fig5_stage3_4R_formal_certification_matrix.png`: Rigorous 5-Gate certification status matrix.
3. **High-Resolution Demonstration Videos (`evidence/stage3_4R/videos/`)**:
   - `video_turning_bay_escape.mp4`: 720p side-by-side composite (MuJoCo tracking POV + real-time telemetry dashboard).
   - `video_tjunction_epistemic_showdown.mp4`: Synchronized 720p comparison of ARM-A choosing open arena vs ARM-B entering dead end.
