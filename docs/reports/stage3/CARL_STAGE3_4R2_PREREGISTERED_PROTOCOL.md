# CARL-DX STAGE 3.4-R2 PRE-REGISTERED PROTOCOL
**Authoritative Forensic Remediation Battery: Frontier Representation & Dimensionless Active Inference**

```
========================================================================================
                                PROTOCOL CONTROL & METADATA
========================================================================================
Protocol ID:            CARL-STAGE3-4R2-ACTIVE-INF-REMED-2026-09-14-v1
Milestone:              Stage 3.4-R2 — Frontier Representation & Normalization Remediation
Document Path:          D:\ebca\CARL_STAGE3_4R2_PREREGISTERED_PROTOCOL.md
Historical Predecessors:Stage 3.4 v4 (FAILED CLOSED ❌, 0/40 escapes)
                        Stage 3.4-R v3 (FAILED CLOSED ❌, 0/50 escapes, McNemar p = 1.0)
Primary Scientific Q:   Does replacing the micro-local (3 cm) frontier shadow with a 
                        connected macro-frontier cluster and normalizing continuous 
                        cost terms resolve the corridor mouth free-energy well and 
                        demonstrate the causal necessity of epistemic active inference?
Episode Accounting:     200 Preregistered Certification Episodes (50 matched configs x 4 arms)
                        + 10 Non-Binding Pre-Flight Diagnostic Episodes
                        = 210 Physical Episodes Total (if both phases are executed).
Adjudication Standard:  Fail-Closed Pre-Registration (Zero Compensatory Scoring)
Adjudication Engine:    Exact One-Sided McNemar Test (alpha = 0.001) + Contact Manifolds
========================================================================================
```

---

## 1. Epistemological Grounding & Permanent Baseline

### 1.1 Non-Negotiable Governance Invariants
1. **Stage 3.4 and Stage 3.4-R Remain Permanently FAILED CLOSED ❌**: Their artifacts, scorecards, raw trials, and videos remain immutable historical evidence. They are not reopened, rewritten, reinterpreted, or altered.
2. **Stage 3.3 Substrate Remains Certified and Frozen ✅**: The Stage 3.3 continuous MPPI engine is not modified or rewritten.
3. **Stage 3.5 Remains Strictly LOCKED 🔒**: No work on Stage 3.5 (Physical Perturbations & Adaptation) is permitted until Stage 3.4-R2 is certified.
4. **Strict Evaluator Firewall**: Evaluator telemetry ($v_{\text{wheel}}$, $\theta_{\text{world}}$) remains quarantined outside the active cognitive decision pipeline.
5. **No Scripted State Machines or Maneuver Macros**: Action synthesis remains continuous trajectory optimization over continuous controls $\mathbf{u} \in [-1.0, 1.0]^2$.

---

## 2. Mathematical Formulation of Stage 3.4-R2 Active Inference `[MATHEMATICAL DEFINITION]`

### 2.1 Connected Macro-Frontier Extraction & Geodesic Field
Let the 2D spatial occupancy memory be a discrete grid $\mathcal{G} \subset \mathbb{R}^2$ with resolution $\delta = 0.10\text{ m}$:
- Channel 0: Obstacle hit density $O(i, j) \in [0, 10.0]$
- Channel 1: Observation / visibility mask $V(i, j) \in [0.0, 1.0]$

1. **Frontier Cell Set $\mathcal{F}$**:
   $$(i, j) \in \mathcal{F} \iff V(i, j) \ge 0.50 \wedge O(i, j) < 0.30 \wedge \exists (i', j') \in \mathcal{N}_8(i, j) \text{ s.t. } V(i', j') < 0.50 \wedge d_{\text{obs}}(i, j) \ge r_{\text{hull}}$$
2. **Connected Component Partitioning**:
   Partition $\mathcal{F}$ into 8-connected clusters $\{\mathcal{C}_k\}_{k=1}^K$ using connected-component labeling. Discard micro-noise clusters with $|\mathcal{C}_k| < 4$ cells.
3. **Discrete Free-Space Geodesic Wavefront**:
   Compute the discrete BFS wavefront distance field $D_{\text{free}}(x, y)$ from current robot position $\mathbf{x}_0$ over traversable grid cells ($O < 0.85$).
4. **Macro-Frontier Selection Rule**:
   $$k^* = \arg\max_k \left[ \frac{|\mathcal{C}_k|}{D_{\text{free}}(\mathcal{C}_k) + \epsilon_{\text{dist}}} \right]$$
   Where $\epsilon_{\text{dist}} = 0.50\text{ m}$. Select target coordinate $\mathbf{f}^* \in \mathcal{C}_{k^*}$ as the medial frontier cell with maximum obstacle clearance.
   > **Epistemic Proxy Qualification**: The selection rule provides a macro-scale, reachable proxy for epistemic value by favoring large frontier regions at low free-space geodesic cost. It does not mathematically prove maximum expected information gain.

### 2.2 Dimensionless Expected Free Energy Formulation
Candidate rollouts $\tau = (\mathbf{x}_{0:H}, \mathbf{u}_{0:H-1})$ sampled via MPPI ($M=128, H=15, \Delta t=0.030\text{ s}$) are evaluated under a dimensionless formulation:

1. **Collision Hard Inadmissibility Constraint**:
   $$G(\tau) = \infty \quad \text{if } \exists t \in \{1, \dots, H\} \text{ s.t. } d_t \le r_{\text{hull}}$$
2. **Dimensionless Continuous Cost Terms ($\tau \in \mathcal{T}_{\text{free}}$)**:
   - **Normalized Terminal Geodesic Progress**:
     $$\bar{\Phi}_{\text{frontier}}(\tau) = \frac{D_{\text{free}}(\mathbf{x}_0) - D_{\text{free}}(\mathbf{x}_H)}{D_{\max}} \in [-1.0, 1.0]$$
     where $D_{\max} = v_{\max} H \Delta t = 0.30 \times 15 \times 0.030 = 0.135\text{ m}$.
     > **Technical Approximation Qualification**: The terminal potential is an approximate geodesic value function derived from the discrete free-space wavefront field; bilinear interpolation is used solely to obtain a differentiable/continuous terminal score for sampled trajectories. It is not treated as an exact continuous geodesic solution.
   - **Normalized Margin Penalty**:
     $$\bar{J}_{\text{margin}}(\tau) = \frac{1}{H} \sum_{t=1}^H \left( \frac{\max(0, d_{\text{margin}} - d_t)}{d_{\text{margin}}} \right)^2 \in [0, 1.0]$$
   - **Normalized Jerk Penalty**:
     $$\bar{J}_{\text{jerk}}(\tau) = \frac{1}{(H-1) \Delta u_{\max}^2} \sum_{t=1}^{H-1} \|\mathbf{u}_t - \mathbf{u}_{t-1}\|^2 \in [0, 1.0]$$
     where $\Delta u_{\max} = 2.0$.
   - **Normalized Sonar Flank Steer Centering**:
     $$\bar{J}_{\text{steer}}(\tau) = \left( \frac{\Delta u_0 - \Delta u_{\text{target}}}{2.0} \right)^2 \in [0, 1.0]$$

3. **Total Free Energy**:
   $$G(\tau) = \alpha_{\text{margin}} \bar{J}_{\text{margin}}(\tau) + \alpha_{\text{jerk}} \bar{J}_{\text{jerk}}(\tau) + \alpha_{\text{steer}} \bar{J}_{\text{steer}}(\tau) - w_{\text{info}} \alpha_{\text{epistemic}} \bar{\Phi}_{\text{frontier}}(\tau)$$
   With fixed pre-registered weights:
   $$\alpha_{\text{margin}} = 0.35, \quad \alpha_{\text{epistemic}} = 0.40, \quad \alpha_{\text{jerk}} = 0.15, \quad \alpha_{\text{steer}} = 0.10$$

---

## 3. Pre-Registered Hypotheses `[PRE-REGISTERED HYPOTHESIS]`

1. **$H_1$ (Egress Monotonicity)**: Conditional on the selected macro-frontier lying downstream along the egress corridor, geodesic terminal value is expected to increase monotonically with forward progress toward that frontier.
2. **$H_2$ (Epistemic Causal Necessity)**: ARM-A vs ARM-B will produce $\Delta\text{Escape} \ge 35.0\%$ with exact one-sided McNemar $p < 0.001$.
3. **$H_3$ (Macro-Frontier Representation Necessity)**: ARM-A vs ARM-C will produce $\Delta\text{Escape} \ge 30.0\%$ with $p < 0.001$, confirming that the macro-cluster representation is necessary compared to the 3 cm local frontier shadow.
4. **$H_4$ (Dimensionless Normalization Necessity)**: ARM-A vs ARM-D will produce $\Delta\text{Escape} \ge 30.0\%$ with $p < 0.001$, confirming that dimensionless normalization is necessary to overcome corridor mouth margin resistance.

---

## 4. Test Environments & Sample Allocation (N = 50 Configurations, 200 Episodes)

### 4.1 Environments
1. **Environment 1: Cul-de-Sac with Rotational Turning Bay (`cul_de_sac_turning_bay.xml`)**:
   - Corridor length $1.80\text{ m}$, width $0.70\text{ m}$, turning bay width $W_{\text{bay}} = 1.30\text{ m}$.
   - Configurations 0–19 (4 matched spawn variations $\times 5$ seeds: `5001, 5002, 5003, 5004, 5005`).
2. **Environment 2: Asymmetric Epistemic T-Junction (`asymmetric_t_junction.xml`)**:
   - East branch is dead end ($1.20\text{ m}$ deep); West branch opens into wide arena ($3.0\text{ m} \times 3.0\text{ m}$).
   - Configurations 20–49 (6 matched spawn variations $\times 5$ seeds: `5001, 5002, 5003, 5004, 5005`).

### 4.2 Four Experimental Arms
```
===================================================================================================================
                                          EXPERIMENTAL ARMS SPECIFICATION
===================================================================================================================
Arm ID   | Name                              | w_info | Frontier Representation | Objective Formulation | Horizon
---------+-----------------------------------+--------+-------------------------+-----------------------+----------
ARM-A    | Full Remediated Active Inference  |  1.0   | Macro-Cluster Geodesic  | Dimensionless Norm    | H = 15
ARM-B    | Pragmatic-Only Baseline           |  0.0   | None (w_info = 0.0)     | Dimensionless Norm    | H = 15
ARM-C    | Ablation: Micro-Local Frontier    |  1.0   | Stage 3.4-R (3cm Shadow)| Dimensionless Norm    | H = 15
ARM-D    | Ablation: Unnormalized Scale      |  1.0   | Macro-Cluster Geodesic  | Stage 3.4-R (Lambda=8)| H = 15
===================================================================================================================
```

#### Authoritative Physical Episode Accounting
- **Pre-Flight Diagnostic Phase**: 10 non-binding physical episodes (ARM-A on Turning Bay).
- **Authoritative Certification Phase**: 50 matched configurations $\times 4$ arms = **200 physical certification episodes**.
- **Total Physical Workload**: **210 physical episodes total**.

---

## 5. Pre-Registered Acceptance Gates

```
===================================================================================================================
                                      STAGE 3.4-R2 CERTIFICATION GATES
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

---

## 6. Required Evidence Artifacts

1. **Scorecard & Telemetry**:
   - `evidence/stage3_4R2/stage3_4R2_scorecard.json`
   - `evidence/stage3_4R2/stage3_4R2_raw_trials.json`
2. **Figures (`evidence/stage3_4R2/figures/`)**:
   - `fig1_ablation_comparison.png`
   - `fig2_macro_frontier_trajectories.png`
   - `fig3_geodesic_potential_dynamics.png`
   - `fig4_comparative_escape_rates.png`
   - `fig5_stage3_4R2_certification_matrix.png`
3. **Videos (`evidence/stage3_4R2/videos/`)**:
   - `video_turning_bay_escape_r2.mp4`
   - `video_tjunction_epistemic_showdown_r2.mp4`
