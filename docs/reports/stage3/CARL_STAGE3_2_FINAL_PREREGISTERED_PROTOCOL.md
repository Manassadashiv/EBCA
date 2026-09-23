# CARL-DX Stage 3.2 — Counterfactual Trajectory Fidelity & Spatial Memory Necessity
# FINAL PRE-REGISTERED EVALUATION PROTOCOL (FINAL REVISION 3)

```
========================================================================================
CARL-DX SCIENTIFIC PRE-REGISTRATION PROTOCOL: STAGE 3.2 (FINAL REVISION 3)
Status: FROZEN & PRE-REGISTERED (PRIOR TO BENCHMARK EXECUTION)
Date: 2026-09-13
North Star: 2,114-unit neuromorphic computational architecture for unscripted autonomous cognition
Current Stage: Stage 3 — Continuous Action Synthesis & Behavioral Discovery
Current Substage: Stage 3.2 — Counterfactual Trajectory Fidelity & Spatial Memory Necessity
Prerequisite Status: Stage 3.1-R CERTIFIED SUCCESSFUL
Subsequent Gate: Stage 3.3 Continuous MPPI remains STRICTLY LOCKED
Evaluation Architecture: Double-Blind Fail-Closed Sub-Gates (3.2A & 3.2B)
Methodology: Controller-State Causal Isolation + External Non-LOS World Pairing + Evaluator Firewall
========================================================================================
```

---

## 1. Executive Scientific Declaration & Task Protocol

### 1.1 Developmental Architecture Alignment
In accordance with the CARL-DX Master Developmental progression:
- **Stage 1 (Grounding & Babbling):** CERTIFIED ✅
- **Stage 2 (Generative World & Self-Model):** CERTIFIED (Scope-Bounded Substrate) ✅
- **Stage 3.0 (Pre-Flight Integrity & AST Clean Scan):** CERTIFIED ✅
- **Stage 3.1-R (CANN Causal Behavioral Coupling):** CERTIFIED ✅
- **Stage 3.2 (Counterfactual Trajectory Fidelity & Spatial Memory Necessity):** **CURRENT ACTIVE PRE-REGISTRATION (FINAL REV 3) ⏳**
- **Stage 3.3 (Continuous Action Synthesis via MPPI):** **STRICTLY LOCKED 🔒**

### 1.2 Core Scientific Question
> *"Does CARL's persistent allocentric spatial memory contain task-relevant causal information about distal and occluded environmental structure that cannot be reconstructed from its current local sensory observations and body state alone, and does its internal mental rollout model predict physical MuJoCo dynamics with sufficient metric fidelity to support continuous prospective deliberation?"*

### 1.3 Immutable Invariants
1. **Measurement Over Optimization:** The benchmark evaluates existing cognitive mechanisms. Zero tuning of neural parameters, deliberation heuristics, or cost functions to "pass" the benchmark is permitted.
2. **Double Fail-Closed Gate:** Stage 3.2 comprises TWO independent sub-gates:
   - **Sub-Gate 3.2A:** Counterfactual Trajectory Rollout Fidelity
   - **Sub-Gate 3.2B:** Spatial Memory Necessity under Non-Line-of-Sight Conditions
   *Both sub-gates must pass independently. If either sub-gate fails, Stage 3.2 fails closed, and Stage 3.3 MPPI remains locked.*
3. **Zero Simulator Coordinate Leaks:** Zero simulator ground truth (`qpos`, `qvel`, `qacc`, `geom_xpos`, `mj_ray`) is permitted inside the cognitive decision loop.
4. **Evaluator-Only Action Firewall:** Ground-truth optimal action sequences $\mathbf{u}^*$ exist strictly inside the external benchmark evaluation harness. Zero exposure of $\mathbf{u}^*$ to the cognitive architecture is permitted.

---

## 2. Methodological Distinction: A/B Task Pairing vs I/A Causal Ablation

To eliminate any ambiguity or overclaiming, the evaluation protocol formally defines two distinct pairing concepts that must never be conflated:

### 2.1 A/B Environment Pairs (External Task-Validity Comparison)
- **Purpose:** Used **ONLY** to establish observational equivalence at the critical decision point ($T_{\text{crit}}$).
- **Physical Reality:** Environment A and Environment B are **NOT** identical physical worlds. They differ in distal, non-line-of-sight geometry (e.g. Left corridor open in A, Right corridor open in B).
- **Equivalence Requirement:** At $T_{\text{crit}}$, their local observations must match within pre-registered tolerances ($\|\mathbf{s}_A - \mathbf{s}_B\|_2 \le 0.150\text{ m}$, $\|\mathbf{b}_A - \mathbf{b}_B\|_2 \le 0.050$), while requiring divergent ground-truth actions ($\|\mathbf{u}^*_A - \mathbf{u}^*_B\|_2 \ge 0.400$).
- **Role:** Guarantees that the task family poses a genuine non-LOS problem that cannot be solved by instantaneous sensing.

### 2.2 ARM-I vs ARM-A Causal Ablation (Primary Causal Intervention)
- **Purpose:** Evaluates whether persistent spatial memory $\mathbf{M}_{\text{env}}$ is necessary to solve the task.
- **Physical Reality:** Performed **WITHIN THE SAME PHYSICAL ENVIRONMENT** (within Environment A, or within Environment B).
- **State-Cloning Protocol:** At $T_{\text{crit}}$, the complete internal controller state is cloned:
  - Current 15-ray Sonar Readings: $\|\mathbf{s}_{\text{ARM-I}} - \mathbf{s}_{\text{ARM-A}}\|_2 = 0.0000\text{ m}$
  - Current Estimated Body State: $|v_{\text{hat, I}} - v_{\text{hat, A}}| = 0.0000$, $|\omega_{\text{hat, I}} - \omega_{\text{hat, A}}| = 0.0000$
  - Internal Dead-Reckoned Pose: $\|\hat{\mathbf{p}}_{\text{ARM-I}} - \hat{\mathbf{p}}_{\text{ARM-A}}\|_2 = 0.0000\text{ m}$
  - Internal Heading Estimate: $|\hat{\theta}_{\text{ARM-I}} - \hat{\theta}_{\text{ARM-A}}| = 0.0000\text{ rad}$
  - Recent Action History (10 ticks): $\|\mathbf{u}_{\text{hist, I}} - \mathbf{u}_{\text{hist, A}}\| = 0.0000$
  - CANN 2,114-Unit State: Identical firing rate vectors
  - Deliberation Parameters & Candidates: Identical $K=24$ candidate arcs, identical weights
  - Simulation Timestep: $dt = 0.030\text{ s}$ (exact match)
- **Sole Intervention Variable:**
  - `ARM-I`: Retains persistent spatial memory tensor $\mathbf{M}_{\text{env}} \in \mathbb{R}^{1 \times 2 \times 128 \times 128}$.
  - `ARM-A`: $\mathbf{M}_{\text{env}}$ is explicitly wiped to zero: $\mathbf{M}_{\text{env}} = \text{torch.zeros\_like}(\mathbf{M}_{\text{env}})$.
  - `ARM-S`: $\mathbf{M}_{\text{env}}$ undergoes $16 \times 16$ patch permutation (topology destroyed, histogram invariant).
  - `ARM-R` / `ARM-PF`: Scripted / potential-field memoryless baselines.

### 2.3 Core Methodological Summary
- **A/B is an external task-validity comparison** establishing observational ambiguity. External environments are NOT claimed to be identical.
- **I/A is the primary causal intervention** executed within the exact same physical world after controller cloning at $T_{\text{crit}}$.
- The two comparisons are cleanly decoupled and never conflated in the causal claim.

---

## 3. Sub-Gate 3.2A: Counterfactual Trajectory Rollout Fidelity Protocol

### 3.1 Objective
Validate that the internal kinematic forward model (`GroundedKinematicBodyModel` and `_mental_unroll_poses`) used during candidate deliberation accurately predicts physical MuJoCo rigid-body motion across CARL's complete action repertoire in open space.

### 3.2 Evaluated Action Repertoire (24 Profiles across 8 Families)
The test suite evaluates 24 continuous action profiles over horizon $H=10$ ($dt=0.030$ s, total horizon $T=0.30$ s):

| ID | Family | Profile Name | Motor Command $[u_L, u_R]$ | Kinematic Characterization |
| :--- | :--- | :--- | :--- | :--- |
| P01 | Straight | `straight_full` | $[0.80, 0.80]$ | High-speed forward translation |
| P02 | Straight | `straight_cruise` | $[0.60, 0.60]$ | Nominal cruise translation |
| P03 | Straight | `straight_trim_L` | $[0.75, 0.80]$ | Subtle left steering bias |
| P04 | Straight | `straight_trim_R` | $[0.80, 0.75]$ | Subtle right steering bias |
| P05 | Curved Left | `gentle_left` | $[0.65, 0.75]$ | Low curvature left sweep |
| P06 | Curved Left | `soft_left_mod` | $[0.40, 0.55]$ | Moderate curvature left |
| P07 | Curved Left | `soft_left_fast` | $[0.55, 0.80]$ | High-speed soft left |
| P08 | Curved Left | `med_left_mod` | $[0.25, 0.50]$ | Sharp curvature left |
| P09 | Curved Left | `med_left_fast` | $[0.35, 0.80]$ | Dynamic aggressive left |
| P10 | Curved Left | `hard_left_fast` | $[0.15, 0.80]$ | Maximum curvature forward turn |
| P11 | Curved Right | `gentle_right` | $[0.75, 0.65]$ | Low curvature right sweep |
| P12 | Curved Right | `soft_right_mod` | $[0.55, 0.40]$ | Moderate curvature right |
| P13 | Curved Right | `soft_right_fast` | $[0.80, 0.55]$ | High-speed soft right |
| P14 | Curved Right | `med_right_mod` | $[0.50, 0.25]$ | Sharp curvature right |
| P15 | Curved Right | `med_right_fast` | $[0.80, 0.35]$ | Dynamic aggressive right |
| P16 | Curved Right | `hard_right_fast`| $[0.80, 0.15]$ | Maximum curvature forward turn |
| P17 | In-Place Pivot | `pivot_left_hard` | $[-0.60, 0.60]$ | Fast zero-radius counter-clockwise spin |
| P18 | In-Place Pivot | `pivot_right_hard`| $[0.60, -0.60]$ | Fast zero-radius clockwise spin |
| P19 | In-Place Pivot | `pivot_left_mod` | $[-0.35, 0.35]$ | Controlled yaw realignment |
| P20 | Reverse | `reverse_straight`| $[-0.35, -0.35]$| Linear backward translation |
| P21 | Reverse-Hook | `reverse_hook_left` | $[-0.40, -0.15]$| Reverse escape hook to left |
| P22 | Reverse-Hook | `reverse_hook_right`| $[-0.15, -0.40]$| Reverse escape hook to right |
| P23 | Accel/Decel Ramp | `throttle_step` | Step $[0.2, 0.2] \to [0.8, 0.8]$ | Transient acceleration surge |
| P24 | Coasting / Decay | `inertial_coast` | Step $[0.8, 0.8] \to [0.0, 0.0]$ | Momentum decay ($\gamma_v=0.70, \gamma_w=0.75$) |

### 3.3 Test Environment & Execution Protocol
- **Environment:** Deterministic open-space arena with no obstacles within $3.0$ m radius.
- **Seeds:** 5 evaluation seeds (`[3001, 3002, 3003, 3004, 3005]`).
- **Total Trials:** $24 \text{ profiles} \times 5 \text{ seeds} = 120 \text{ rollouts}$.
- **Harness Isolation:** Simulator ground truth ($qpos, qvel$) is read strictly by the external evaluation harness. Zero simulator coordinates are passed to the mental unroll engine.

### 3.4 Pre-Registered Acceptance Thresholds (Sub-Gate 3.2A)
| Metric | Primary Acceptance Gate | Fail-Closed Condition |
| :--- | :--- | :--- |
| **Mean Terminal Position Error ($\bar{e}_{\text{term}}$)** | $\le 0.080\text{ m}$ ($8.0\text{ cm}$) | $> 0.080\text{ m}$ |
| **95th Percentile Terminal Error ($e_{\text{term}, p95}$)** | $\le 0.120\text{ m}$ ($12.0\text{ cm}$) | $> 0.120\text{ m}$ |
| **Mean Trajectory RMSE ($\overline{\text{RMSE}}_{xy}$)** | $\le 0.050\text{ m}$ ($5.0\text{ cm}$) | $> 0.050\text{ m}$ |
| **Mean Terminal Heading Error ($\bar{e}_{\theta}$)** | $\le 0.100\text{ rad}$ ($5.73^\circ$) | $> 0.100\text{ rad}$ |
| **Coasting Envelope Agreement ($R^2_v$)** | $\ge 0.80$ | $< 0.80$ |

---

## 4. Sub-Gate 3.2B: Spatial Memory Necessity Battery Protocol

### 4.1 Final Observational-Equivalence Definition & Firewall Specification
A task family qualifies for the final benchmark **only if** paired states $(A, B)$ satisfy exhaustive equivalence across ALL immediately available state variables:

```
+-----------------------------------------------------------------------------------------+
|                  EXHAUSTIVE OBSERVATIONAL EQUIVALENCE CRITERIA                          |
+-----------------------------------------------------------------------------------------+
| 1. Sonar Distance:        ||s_A - s_B||_2 <= 0.150 m  (max_i |s_A,i - s_B,i| <= 0.080 m)|
| 2. Body Velocity:         |v_A - v_B| + |w_A - w_B| <= 0.050                            |
| 3. Heading Alignment:     |atan2(sin(theta_A - theta_B), cos(theta_A - theta_B))| <= 0.02|
| 4. Internal Pose Match:   sqrt((x_hat_A - x_hat_B)^2 + (y_hat_A - y_hat_B)^2) <= 0.020 m|
| 5. Elapsed Ticks:         t_A = t_B = T_crit (exact match)                              |
| 6. Action History (10t):  (1/10) sum_{k=1}^10 ||u_{A, t-k} - u_{B, t-k}|| <= 0.010      |
| 7. Context / Labels:      Zero task IDs, environment names, or goal vectors exposed     |
| 8. Divergent Action:      ||u*_A - u*_B||_2 >= 0.400 (Evaluator Oracle Only)            |
+-----------------------------------------------------------------------------------------+
```

#### Ground-Truth Optimal Action Firewall Specification:
- $\mathbf{u}^*$ is an **EVALUATOR-ONLY ORACLE VARIABLE**.
- $\mathbf{u}^*$ is used EXCLUSIVELY by the offline evaluation harness to:
  1. Validate that paired task environments $(A, B)$ genuinely require divergent motor maneuvers ($\|\mathbf{u}^*_A - \mathbf{u}^*_B\| \ge 0.400$).
  2. Compute post-hoc scientific scoring.
- **Strict Prohibition Invariant:** $\mathbf{u}^*$ must NEVER enter:
  - Perception or sensory buffers
  - CANN attractor networks
  - Spatial occupancy memory $\mathbf{M}_{\text{env}}$
  - Deliberation candidate unrolls or scoring
  - Utility arbitration or action veto
  - Autonomous motor output
  - Controller state or training pipelines
- Verified by Audit 8 in the pre-execution audit manifest.

### 4.2 Redesigned Five Non-LOS Task Families
1. **Family 1 — Blind-Corner Connectivity Ambiguity:** Symmetrical T-junction corridor ($1.2\text{ m}$ width). Both branches appear clear for $1.2\text{ m}$ under line-of-sight ($D_s \le 0.08\text{ m}$). One branch dead-ends around an occluded corner at $2.0\text{ m}$; the other is open.
2. **Family 2 — Irreversible Cul-de-Sac Funnel Trap (Redesigned):** Symmetrical Y-fork ($0.80\text{ m}$ throat, $D_s \le 0.05\text{ m}$). Branch 1 narrows to $0.32\text{ m}$ (chassis width $0.28\text{ m}$, turning diameter $0.44\text{ m}$), making turning around mechanically impossible without collision. Strict budget $T_{\text{budget}} = 100$ ticks ($3.0\text{ s}$). Reversal requires $> 160$ ticks. Entering Branch 1 guarantees episode failure, strictly isolating necessity from efficiency.
3. **Family 3 — Sonically Symmetric Locations with Divergent Action Requirements:** Matched cross-sections at distinct maze coordinates ($D_s \le 0.05\text{ m}$). North is open at $P_1 = (-1.5, 1.2)$; East is open at $P_2 = (1.5, -1.8)$. Memory is required to resolve pure perceptual aliasing.
4. **Family 4 — Occluded Dogleg Arterial vs Blind Detour (Redesigned):** Both Branch A (nominal heading) and Branch B (detour at $45^\circ$) extend straight for $1.8\text{ m}$ before entering orthogonal dogleg turns ($D_s \le 0.06\text{ m}$). Blockage is located $0.6\text{ m}$ beyond the dogleg ($2.4\text{ m}$ total distance), completely occluded from local sonar.
5. **Family 5 — Multi-Turn Sensory Blackout / Sonic Corridor Symmetry:** Narrow corridor sequence with alternating baffles where instantaneous sonar matches perpendicular wall profiles ($D_s \le 0.06\text{ m}$). Exit requires memory of prior turn topology.

---

## 5. ARM-S (Spatially Scrambled Memory) Forensic Audit

### 5.1 Permutation Mechanics
The $128 \times 128$ grid (cell size $0.10\text{ m}$, covering $12.8\text{ m} \times 12.8\text{ m}$) is partitioned into an $8 \times 8$ array of 64 non-overlapping patches, each of size $16 \times 16$ cells ($1.60\text{ m} \times 1.60\text{ m}$). A uniform random permutation $\pi \in \mathcal{S}_{64}$ is applied:
$$\text{Patch}_k \mapsto \text{Patch}_{\pi(k)}$$

### 5.2 Information Preserved vs Destroyed
- **What is PRESERVED (Control Invariants):**
  1. Total cell occupancy count ($N_{\text{wall}}$ invariant).
  2. Mean occupancy value and variance ($\mu_{\text{occ}}, \sigma^2_{\text{occ}}$ invariant).
  3. Total free-space carved volume vs deposited hit ratio.
  4. Local micro-texture within any single $1.6\text{ m} \times 1.6\text{ m}$ block.
- **What is DESTROYED (Topology Abolition):**
  1. Global metric coordinates: obstacle coordinates are displaced by up to $10.0\text{ m}$.
  2. Corridor continuity: walls crossing patch boundaries are sliced and relocated to disjoint regions.
  3. Spatial correspondence to dead-reckoned pose: prospective queries at $(\hat{x}, \hat{y})$ sample random patches.
- **Scientific Purpose:** Proves that ARM-I's advantage stems from **correct spatial topology**, not simply from having non-zero weights or obstacle densities in memory.

---

## 6. Final Statistical Test & Exact McNemar Compatibility Design

### 6.1 Paired Binary Decision Structure
For each of $N = 100$ matched pairs between ARM-I and ARM-A (cloned from identical state at $T_{\text{crit}}$):
$$Y_{\text{I}, i} \in \{0, 1\} \quad \text{and} \quad Y_{\text{A}, i} \in \{0, 1\}$$
where $1 = \text{Success}$ (reaches goal within $T_{\text{budget}}$ with 0 collisions) and $0 = \text{Failure}$ (collision or entrapment).

### 6.2 Contingency Table & Discordant Pairs
| | ARM-A Success ($Y_A=1$) | ARM-A Failure ($Y_A=0$) |
| :--- | :---: | :---: |
| **ARM-I Success ($Y_I=1$)** | $n_{11}$ | $n_{10}$ (Discordant, Intact wins) |
| **ARM-I Failure ($Y_I=0$)** | $n_{01}$ (Discordant, Amnesic wins) | $n_{00}$ |

Total matched pairs: $N = n_{11} + n_{10} + n_{01} + n_{00} = 100$.
Total discordant pairs: $n_d = n_{10} + n_{01}$.
Marginal difference in success rates:
$$\Delta \text{Success}_{\text{I} - \text{A}} = \frac{n_{10} - n_{01}}{N}$$

### 6.3 Exact Statistical Test (Exact McNemar Test)
Conditioned on discordant pairs $n_d = n_{10} + n_{01}$:
- **Null Hypothesis:** $H_0: P(Y_{\text{I}} = 1, Y_{\text{A}} = 0) \le P(Y_{\text{I}} = 0, Y_{\text{A}} = 1) \iff p_{\text{discordant}} \le 0.50$
- **Alternative Hypothesis:** $H_1: P(Y_{\text{I}} = 1, Y_{\text{A}} = 0) > P(Y_{\text{I}} = 0, Y_{\text{A}} = 1) \iff p_{\text{discordant}} > 0.50$
- **Exact One-Sided $p$-value:**
  $$p = \sum_{k=n_{10}}^{n_d} \binom{n_d}{k} 0.5^{n_d}$$
- **Pre-Registered Significance Level:**
  $$\alpha = 0.001 \quad (\text{one-sided})$$

### 6.4 Exact McNemar Compatibility Bound across Discordant Allocations
The pre-registered primary effect threshold is:
$$\Delta \text{Success}_{\text{I} - \text{A}} \ge 0.350 \implies n_{10} - n_{01} \ge 35$$

We evaluate the exact binomial $p$-value across the entire space of compatible discordant allocations on $N=100$:
- **Case 1: Minimum Discordant Count ($n_d = 35$, $n_{10} = 35, n_{01} = 0$):**
  $$p = 0.5^{35} = 2.91 \times 10^{-11} \ll 0.001$$
- **Case 2: Moderate Discordant Count ($n_d = 55$, $n_{10} = 45, n_{01} = 10$):**
  $$p = \sum_{k=45}^{55} \binom{55}{k} 0.5^{55} = 6.22 \times 10^{-7} \ll 0.001$$
- **Case 3: High Discordant Count ($n_d = 75$, $n_{10} = 55, n_{01} = 20$):**
  $$p = \sum_{k=55}^{75} \binom{75}{k} 0.5^{75} = 2.41 \times 10^{-5} < 0.001$$
- **Case 4: Extreme Discordant Count ($n_d = 95$, $n_{10} = 65, n_{01} = 30$):**
  $$p = \sum_{k=65}^{95} \binom{95}{k} 0.5^{95} = 0.00015 < 0.001$$
- **Case 5: Absolute Worst-Case Discordant Allocation ($n_d = 99$, $n_{10} = 67, n_{01} = 32$):**
  $$p = \sum_{k=67}^{99} \binom{99}{k} 0.5^{99} = 0.00030 < 0.001$$

**Exact McNemar Compatibility Bound:**
For $N=100$, any observed paired outcome configuration satisfying $\Delta \text{Success} \ge 0.350$ has an exact one-sided McNemar $p$-value below $\alpha = 0.001$ under the pre-registered discordant-pair definition (the worst-case allocation on $N=100$ is $n_d=99, n_{10}=67, n_{01}=32$, yielding $p = 0.00030 < 0.001$).
*(Note: This represents an exact compatibility bound over the discrete paired sample space satisfying the effect threshold, rather than a prospective statistical power calculation).*

---

## 7. Pre-Execution Integrity Audits (10-Point Manifest)

Before running the final 500-episode battery, the test suite executes the automated 10-point audit suite:

1. **Audit 1 (AST Anti-Cheat Scan):** Static AST scan of all decision-pipeline modules verifying zero simulator coordinates (`qpos`, `qvel`, `qacc`, `geom_xpos`, `mj_ray`).
2. **Audit 2 (State-Cloning Fidelity):** Verification that at decision tick $T_{\text{crit}}$, sensor readings, body states, odometry, and CANN activations between ARM-I and ARM-A have zero divergence ($\|\Delta \mathbf{s}\| = 0.0000$, $\|\Delta \mathbf{b}\| = 0.0000$).
3. **Audit 3 (Arm Equivalence):** Structural verification that ARM-I and ARM-A instantiate identical classes, identical model weights, and identical candidate action fans.
4. **Audit 4 (Observational-Equivalence Automated Precheck):** Verification that all 5 task families satisfy $\|\mathbf{s}_A - \mathbf{s}_B\| \le 0.150\text{ m}$ and $\|\mathbf{b}_A - \mathbf{b}_B\| \le 0.050$.
5. **Audit 5 (Seed Determinism):** Verification of exact bitwise determinism across duplicate executions of seeds `[3001-3005]`.
6. **Audit 6 (Simulator Coordinate Isolation):** Confirmation that MuJoCo execution occurs strictly behind the HAL interface; zero simulator coordinates passed to candidate scoring.
7. **Audit 7 (Actuation Interface Invariant):** Verification that all 5 experimental arms produce standard 6-channel motor control vectors in $[-1.0, 1.0]^6$.
8. **Audit 8 (Ground-Truth Optimal Action Firewall):** Static AST and runtime inspection verifying that $\mathbf{u}^*$ is never accessed, imported, or referenced by perception, CANN, memory, deliberation, or action selection.
9. **Audit 9 (Amnesic Arm Invariant):** Verification that ARM-A retains active 15-ray live sonars, IMU, and dead-reckoning; only $\mathbf{M}_{\text{env}}$ is zeroed.
10. **Audit 10 (Cryptographic SHA-256 Manifest):** Locking SHA-256 hashes of all protocol documents, model checkpoints, test scripts, and arena XMLs before launch.

---

## 8. Final Pre-Registered Acceptance Matrix (Unchanged Thresholds)

All original Stage 3.2 thresholds are strictly preserved:

| Gate | Sub-Gate | Metric | Acceptance Threshold | Fail-Closed Condition |
| :---: | :---: | :--- | :--- | :--- |
| **G1** | **3.2A** | **Mean Terminal Position Error ($\bar{e}_{\text{term}}$)** | $\le 0.080\text{ m}$ ($8.0\text{ cm}$) | $> 0.080\text{ m}$ |
| **G2** | **3.2A** | **95th Percentile Terminal Error ($e_{\text{term}, p95}$)** | $\le 0.120\text{ m}$ ($12.0\text{ cm}$) | $> 0.120\text{ m}$ |
| **G3** | **3.2A** | **Mean Trajectory RMSE ($\overline{\text{RMSE}}_{xy}$)** | $\le 0.050\text{ m}$ ($5.0\text{ cm}$) | $> 0.050\text{ m}$ |
| **G4** | **3.2A** | **Mean Terminal Heading Error ($\bar{e}_{\theta}$)** | $\le 0.100\text{ rad}$ ($5.73^\circ$) | $> 0.100\text{ rad}$ |
| **G5** | **3.2A** | **Coasting Momentum Envelope ($R^2_v$)** | $\ge 0.80$ | $< 0.80$ |
| **G6** | **3.2B** | **Primary Effect Separation ($\Delta \text{Success}_{\text{I} - \text{A}}$)** | $\ge 35.0\%$ ($0.350$) | $< 35.0\%$ |
| **G7** | **3.2B** | **Exact McNemar Significance ($p$-value)** | $p < 0.001$ (one-sided) | $p \ge 0.001$ |
| **G8** | **3.2B** | **Topology Control Separation ($\Delta \text{Success}_{\text{I} - \text{S}}$)** | $\ge 25.0\%$ ($0.250$), $p < 0.01$ | $< 25.0\%$ or $p \ge 0.01$ |
| **G9** | **3.2B** | **Intact Collision Rate ($\text{CR}_{\text{ARM-I}}$)** | $\le 5.0\%$ | $> 5.0\%$ |
| **G10**| **Audit** | **Observational Equivalence Integrity** | $100\%$ tasks pass ($D_s \le 0.150\text{ m}$) | Any task fails |
| **G11**| **Audit** | **AST Decision-Pipeline Anti-Cheat** | $0$ simulator coordinate leaks | $\ge 1$ leak detected |
| **G12**| **Audit** | **Optimal Action Firewall Integrity** | $0$ leaks of $\mathbf{u}^*$ to decision pipeline | Any leak detected |

---

## 9. Diagnostic Dead-Reckoning Drift Protocol

- **Measurement:** Tracking $\Delta r_{\text{drift}}(t) = \sqrt{(x_t - \hat{x}_t)^2 + (y_t - \hat{y}_t)^2}$ across $T \in [0, 600]$ ticks.
- **Reporting:** Mean cumulative drift $\bar{\Delta} r_{\text{drift}}$ and drift rate (m/s).
- **Explicit Isolation:** **Diagnostic only.** Does not constitute an independent pass/fail certification gate.

---

## 10. Deliverables Manifest & Files to Be Created

Upon human approval to proceed, the following files will be created or updated:

| File Path | Action | Description |
| :--- | :---: | :--- |
| [`CARL_STAGE3_2_FINAL_PREREGISTERED_PROTOCOL.md`](file:///d:/ebca/CARL_STAGE3_2_FINAL_PREREGISTERED_PROTOCOL.md) | **CREATED** | Authoritative frozen protocol document (Revision 3) |
| [`implementation_plan.md`](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/70ce1824-88d3-4886-8215-ae84fa5df454/implementation_plan.md) | **UPDATED** | Pre-registration implementation plan artifact |
| `tests/test_stage3_2_integrity_audit.py` | **TO CREATE** | 10-point pre-execution audit suite (AST, seeds, memory dataflow, u* firewall) |
| `tests/test_stage3_2_observational_equivalence.py` | **TO CREATE** | Automated anti-fake-task precheck for the 5 task families |
| `tests/test_stage3_2A_trajectory_fidelity.py` | **TO CREATE** | Sub-Gate 3.2A kinematic rollout benchmark ($N=120$) |
| `tests/test_stage3_2B_memory_necessity_battery.py` | **TO CREATE** | Sub-Gate 3.2B 500-episode paired ablation evaluation runner |
| `tests/generate_stage3_2_plots.py` | **TO CREATE** | Publication-grade evidence plotting script |
| `evidence/stage3_2/` | **TO CREATE** | Raw JSON trial data, SHA-256 manifests, and generated figures |
| `CARL_STAGE3_2_FINAL_VERIFICATION_REPORT.md` | **TO CREATE** | Final formal verification and certification report |

---

## 11. Exact Fail-Closed & Stop Conditions

Execution immediately stops and fails closed under ANY of the following conditions:

```
[FAIL-CLOSED TRIGGER 1] Sub-Gate 3.2A Failure:
- Mean terminal position error > 0.080 m
- 95th percentile terminal position error > 0.120 m
- Mean trajectory RMSE > 0.050 m
- Mean terminal heading error > 0.100 rad
- Coasting velocity prediction R² < 0.80

[FAIL-CLOSED TRIGGER 2] Sub-Gate 3.2B Failure:
- Primary necessity effect ΔSuccess (ARM-I - ARM-A) < 35.0%
- Exact McNemar test p-value >= 0.001
- Topology control effect ΔSuccess (ARM-I - ARM-S) < 25.0% or p >= 0.01
- ARM-I collision rate > 5.0%

[FAIL-CLOSED TRIGGER 3] Scientific Integrity Violation:
- State cloning failure (pre-decision state divergence between ARM-I and ARM-A > 0.000)
- Any task family fails observational-equivalence precheck (Ds > 0.150 m)
- Any simulator coordinate leak detected in the AST scan
- Any u* oracle leakage detected into the cognitive pipeline
- Post-hoc adjustment of thresholds, seeds, or sample counts
- Oracle map injected into ARM-I without sensorimotor grounding
```

If any failure condition occurs, Stage 3.2 is certified as **FAILED CLOSED**. Stage 3.3 Continuous MPPI remains **LOCKED**.

---
*PROTOCOL END (FINAL REVISION 3) — AWAITING EXPLICIT HUMAN APPROVAL TO PROCEED TO BENCHMARK CODING AND AUDIT EXECUTION.*
