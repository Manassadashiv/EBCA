# CARL Stage 2.2-R2: Adversarial Architectural Recovery Specification (v2.1 Hardened)
**Milestone:** Stage 2.2-R2 — Modular Action-Conditioned Predictive World Model  
**Classification:** [SCIENTIFIC DESIGN GATE] Pre-Implementation Adversarial Specification & Forensic Lock  
**Status:** **FROZEN & AUTHORIZED (v2.1 Pre-Implementation Checks Passed; Execution Active)**  
**Air-Gap Guarantee:** `PRIMARY_UNSEEN_TEST` (`seeds [303, 404, 505, 606, 707]`) **STRICTLY FORBIDDEN FROM EXISTING**  
**Development Baseline:** Multi-seed `DEV_TRAIN` (`[42, 101, 202]`, 24,000 steps) and `DEV_VAL` (`[210, 220, 230, 240]`, 8,000 steps)

---

## 1. Forensic Diagnosis of Phase 1 Failure & The Persistence Trap

Phase 1 evaluated 13 distinct configurations (Direct vs Residual targets across 6 representational states and matched capacity). All 13 candidate architectures decisively failed the Canonical Six Batteries on developmental validation data:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASE 1 FORENSIC SCORECARD SUMMARY                                │
├───────────────────────────────┬──────────────────────────┬──────────────────────┬───────────────┤
│ ARCHITECTURAL HYPOTHESIS      │ EMPIRICAL OBSERVATION    │ BENCHMARK CRITERION  │ STATUS        │
├───────────────────────────────┼──────────────────────────┼──────────────────────┼───────────────┤
│ 1. Residual target (Δs)       │ Action Zero Surge: -17.0%│ Surge >= +25.0%      │ FALSIFIED     │
│    restores motor causality   │ (Error actually dropped) │                      │               │
├───────────────────────────────┼──────────────────────────┼──────────────────────┼───────────────┤
│ 2. Average R² reflects true   │ High-Change Sonar R²:    │ High-Change R²       │ CHEAT EXPOSED │
│    predictive competence      │ Negative across all 13   │ >= 0.50              │               │
│                               │ (-0.0914 to -0.3226)     │                      │               │
├───────────────────────────────┼──────────────────────────┼──────────────────────┼───────────────┤
│ 3. HD + Grid coordinates      │ M5-E-RES R² = 0.1725 vs  │ Significant gain     │ DISPROVEN     │
│    improve forward prediction │ M2-B-RES R² = 0.2038     │ over sensors+actions │               │
├───────────────────────────────┼──────────────────────────┼──────────────────────┼───────────────┤
│ 4. Learned key-value memory   │ M6-F-RES R² = 0.1920 vs  │ Meaningful gain over │ CONFOUNDED    │
│    beats capacity baseline    │ M2-B-MATCHED R² = 0.1871 │ matched capacity     │               │
└───────────────────────────────┴──────────────────────────┴──────────────────────┴───────────────┘
```

### The Causal Failure Diagram of Monolithic Recurrent World Models

```text
[Monolithic Recurrent Forward Model Failure]

                 Sensory History S_t            Action u_t
                          │                         │
                          │                         │ (Double integration required:
                          │ (Direct autocorrelation │  u -> F -> a -> v -> x -> raycast)
                          │  gradients: Dominant)   │ (Gradients: Vanishingly Weak)
                          ▼                         ▼
                 ┌───────────────────────────────────────┐
                 │       Generic Recurrent Cell          │
                 │              (GRU / LSTM)             │
                 └──────────────────┬────────────────────┘
                                    │
                                    ▼
       BPTT Gradient Descent Follows Path of Least Resistance:
       - Mute the noisy, multi-step action bus (Weights -> 0)
       - Output persistent copy: ŝ_{t+1} ≈ s_t  (Direct Target)
       - Output zero delta:      Δŝ_t   ≈ 0     (Residual Target)
                                    │
                                    ▼
       - High overall R² on static flat floor (Room walls do not move)
       - Catastrophic collapse on dynamic changes (Negative R² on D_dynamic)
       - Complete action insensitivity (Zeroing u causes 0% error surge)
```

**Forensic Takeaway:** The failure was a fundamental structural flaw of end-to-end recurrent neural networks: when trained to minimize sensory mean squared error, backpropagation through time unconditionally suppresses motor-dependent geometric integration in favor of temporal persistence.

---

## 2. The Decoupled Causal Architecture (CARL-PredWorld-v2)

To physically and structurally forbid the persistence shortcut, the world model is decomposed into three distinct, causally isolated modules:

```text
                                ACTIONS u_t
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
                   │             MODULE 1:             │
                   │        Body / Ego-Dynamics        │
                   │           Predictor               │
                   │     (Kinematic Forward Model)     │
                   └─────────────────┬─────────────────┘
                                     │
                                     │ Predicted Ego-Motion:
                                     │ - Wheel speeds & gyro (v_t, ω_t)
                                     │ - Relative displacement (Δx_t, Δy_t, Δθ_t)
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
 PAST SONARS ─────>│             MODULE 2:             │
 PAST ACTIONS ────>│        Spatial Occupancy &        │
 PAST DISPL. ─────>│         Boundary Memory           │
                   │      (Internal Cognitive Map)     │
                   └─────────────────┬─────────────────┘
                                     │
                                     │ Retrieved Prospective Clearance Profile
                                     │ at pose p_{t+H} = p_t + Σ Δp
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
                   │             MODULE 3:             │
                   │    Prospective Sensory Generator  │
                   │         & Collision Oracle        │
                   └─────────────────┬─────────────────┘
                                     │
                                     ▼
                          PREDICTED OBSERVATIONS
                          - Dynamic Sonars ŝ_{t+H}
                          - IMU / Proprioception
                          - Prospective Collision Hazard ĉ_{t+H}
```

### Module 1: Body / Ego-Dynamics Predictor ($\mathcal{M}_{\text{body}}$)
- **Role:** Predicts how CARL's mechanical chassis responds to motor efference copy.
- **Input:** Proprioceptive state $s^{\text{body}}_t = [\text{wheel\_vel}, \text{gyro\_yaw}, \text{joint\_angles}]$, action command $u_t$.
- **Output:** Next body state $\hat{s}^{\text{body}}_{t+1}$ AND local kinematic displacement:
  $$\Delta \hat{\mathbf{p}}_t = [\Delta \hat{x}_t, \Delta \hat{y}_t, \Delta \hat{\theta}_t]$$
- **Causal Invariant (Physical Coasting Semantics):**
  $u_t = 0$ denotes **zero additional motor command**, NOT zero instantaneous velocity or zero displacement. If the chassis has non-zero velocity at $t$, setting $u_t = 0$ must predict physical deceleration governed by chassis momentum and rolling friction:
  $$u=0 \implies \text{torque} = 0 \implies \text{momentum} + \text{friction} \implies \text{deceleration} \implies \text{eventual halt}$$
  Module 1 must learn this dynamic physics. It is forbidden from hardcoding `if u==0: dp=0`.
- **Structural Barrier:** Module 1 receives **zero** external sensory information (no sonars, no arena maps, no simulator positions). It cannot predict obstacle clearance; it can only predict mechanical chassis displacement.

### Module 2: Spatial Occupancy & Boundary Memory ($\mathcal{M}_{\text{env}}$)
- **Role:** Maintains an allocentric spatial memory of obstacle endpoints discovered by CARL's own exploratory history relative to its subjective internal origin $(0, 0)$.
- **Update Rule:** Historical sonar readings are converted into obstacle endpoints using CARL's accumulated dead-reckoning trajectory:
  $$\mathbf{e}_{k, i} = \hat{\mathbf{p}}_k + s_{i, k} \begin{bmatrix} \cos(\hat{\theta}_k + \phi_i) \\ \sin(\hat{\theta}_k + \phi_i) \end{bmatrix}$$
  and accumulated into an internal 2D spatial grid $\mathbf{M}_{\text{env}} \in \mathbb{R}^{G \times G}$ ($0.10\,\text{m}$ resolution).
- **Query Interface:** Given prospective pose $\hat{\mathbf{p}}_{t+H} = \hat{\mathbf{p}}_t + \sum_{j=0}^{H-1} \Delta \hat{\mathbf{p}}_{t+j}$ emitted by Module 1, queries prospective obstacle clearance profile along ray angles $\phi_i \in [-120^\circ, +120^\circ]$.
- **Structural Barrier:** Coordinates are strictly spatial addresses into accumulated obstacle records. If an area is unvisited or the map is cleared, the query returns unmapped clearance ($\infty$). Coordinates have no intrinsic capacity to fabricate obstacle boundaries without historical sensor deposits.

### Module 3: Prospective Sensory Generator ($\mathcal{M}_{\text{sensor}}$)
- **Role:** Translates the retrieved prospective clearance profile and body state into predicted future sonar observations and prospective collision hazard.
- **Output:** Predicted future sonar vector $\hat{\mathbf{s}}_{t+H}$ and collision hazard probability $\hat{c}_{t+H} \in [0, 1]$.
- **Structural Barrier:** Current sonar $s_t$ is **strictly withheld** from Module 3. The module has no pathway to copy the current sensor state into the future. It must compute future sonars from the spatial query at the prospective pose.

---

## 3. The Reality Principle & The Six Hardened Pre-Implementation Protocols

### The Reality Principle (Non-Negotiable Foundational Axiom)
> **Internal self-consistency is NOT proof of world modeling. Physical reality is the sole judge.**  
> A model that manufactures large divergences between branches or under action zeroing is completely useless if those branches do not match the real physical consequences in the simulator.  
> **Every counterfactual capability must be judged by prediction accuracy against an independently executed physical counterfactual in MuJoCo, not merely by whether internal predictions differ.**

```text
                  PHYSICAL WORLD
                       │
               ┌───────┴────────┐
               │                │
          Mental model      Evaluator
         (Air-gapped)       (MuJoCo)
               │                │
               ▼                ▼
          prediction       real rollout
               │                │
               └───────┬────────┘
                       ▼
                    COMPARE
```

---

### Strict Computational Isolation: Subprocess Air-Gap During Mental Rollout
During mental rollout, the mental world model process:
1. **Cannot import MuJoCo:** Subprocess execution sets `sys.modules['mujoco'] = None`, backed by static AST verification.
2. **Cannot access the environment object:** No `CarlStage1HAL`, `env`, or simulator handles exist within the process memory space.
3. **Cannot access internal simulator state:** Zero access to `qpos`, `qvel`, `qacc`, or collision buffers.
4. **Cannot access evaluator ground truth:** The evaluator runs separately *after* mental rollouts are completed and timestamped.

---

### The Pre-Implementation Protocols (v2.1 Operational Definitions)

#### Protocol 1: Ground-Truth Physical Branching Alignment & Continuous Action Sequences (Gate 6)
- **Vulnerability Blocked:** Prevents manufactured divergence (hallucinating arbitrary constant vectors) AND template memorization (hardcoding 4 discrete action labels).
- **Hardened Specification:**
  1. **Canonical Branches (Mandatory):** From state $\mathbf{S}_0$, physically execute in MuJoCo:
     - Branch A: Forward ($u = [0.8, 0.8]$) $\to s^*_{\text{fwd}}(t+10)$
     - Branch B: Hard Left ($u = [-0.7, 0.7]$) $\to s^*_{\text{left}}(t+10)$
     - Branch C: Hard Right ($u = [0.7, -0.7]$) $\to s^*_{\text{right}}(t+10)$
     - Branch D: Hard Reverse ($u = [-0.6, -0.6]$) $\to s^*_{\text{rev}}(t+10)$
  2. **Randomized Continuous Sequences ($K = 16$):** Generated from a frozen evaluator PRNG (`seed=20260905`) instantiated strictly **after** model freeze:
     - Random horizons $H \in [5, 15]$ steps.
     - Continuously sampled steering commands $u_L, u_R \in [-1.0, 1.0]$.
     - Transitions between steering and acceleration.
  3. **Execution Isolation & Non-Selectivity Invariant:**
     The evaluator freezes starting state $\mathbf{S}_0$ and all $4 + 16 = 20$ action sequences into a locked manifest (`frozen_branch_sequences.json`) **before** any model predictions or outcome inspection. Physical trajectories are generated independently in MuJoCo. The mental model runs purely internally in an air-gapped subprocess without seeing those trajectories. **No action sequence may be selected, removed, substituted, or rerun based on its outcome.**
  4. **Per-Branch Mandatory Pass Criteria (No Aggregate Cloaking):**
     - **Individual Branch Requirement:** Every single branch $k \in \{1, \dots, 20\}$ (all 4 canonical + all 16 randomized continuous branches) must INDIVIDUALLY pass:
       $$R^2(\hat{s}_k, s^*_k) \ge 0.50 \quad \text{and} \quad \text{RMSE}(\hat{s}_k, s^*_k) \le 1.20\,\text{m}$$
       *An aggregate average $R^2 \ge 0.50$ is INSUFFICIENT; 19 passing branches cannot hide 1 failing branch.*
     - **Confusion Matrix Diagonal Dominance:** Every predicted branch must match its own physical branch strictly closer than any competing physical branch by at least $0.30\,\text{m}$:
       $$\text{RMSE}(\hat{s}_k, s^*_k) \le \min_{j \ne k} \text{RMSE}(\hat{s}_k, s^*_j) - 0.30\,\text{m}$$
     - **Full Granular Reporting:** The benchmark scorecard must report granular per-branch metrics for all 20 branches alongside the summary distribution.

#### Protocol 2: Physical Counterfactual Intervention with Dynamic Coasting (Gate 3)
- **Vulnerability Blocked:** Eliminates the contradiction between action zeroing and physical momentum; prevents static mean prediction.
- **Hardened Specification ("Same State, Divergent Physics"):**
  1. From state $\mathbf{S}_0$, physically execute TWO independent rollouts in MuJoCo:
     - $\mathcal{T}_{\text{active}}$ under active motor sequence $u_{t:t+H}$.
     - $\mathcal{T}_{\text{zero}}$ under zero motor commands $u \equiv 0$, where the robot physically coasts under momentum, decelerates due to friction, and halts.
  2. **Evaluation Across Both Physical Realities:**
     - **Active Reality Test:** Feeding $u=0$ into the model when the physical robot moved actively must cause error to surge:
       $$\text{RMSE}(\hat{s}(u=0), s^*_{\text{active}}) \ge 1.25 \times \text{RMSE}(\hat{s}(u_{\text{active}}), s^*_{\text{active}})$$
     - **Coasting Reality Test:** When the physical robot coasted and halted, the model's $u=0$ prediction must accurately track deceleration and rest:
       $$R^2(\hat{s}(u=0), s^*_{\text{zero}}) \ge 0.60$$
     - **False Motion Rejection:** Predicting active motion when the physical robot coasted to a halt must fail:
       $$\text{RMSE}(\hat{s}(u_{\text{active}}), s^*_{\text{zero}}) \ge 1.25 \times \text{RMSE}(\hat{s}(u=0), s^*_{\text{zero}})$$

#### Protocol 3: Deterministic Gate 5 Pair Selection & Causal Alternate Reality Attraction
- **Vulnerability Blocked:** Eliminates statistical cherry-picking AND proves memory contains veridical geometry (attraction to swapped ground truth).
- **Deterministic Pair Selection Algorithm (Pre-Registered & Frozen):**
  1. Generate all candidate episode pairs $(\mathcal{E}_i, \mathcal{E}_j)$ from developmental validation data (`DEV_VAL`).
  2. Filter strictly by fixed physical tolerances:
     - Local sonar observation: $\|s^{(i)}(t_0) - s^{(j)}(t_0)\|_\infty \le 0.35\,\text{m}$.
     - Current proprioceptive body state: $\|s^{\text{body},(i)}(t_0) - s^{\text{body},(j)}(t_0)\|_\infty \le 0.10$.
     - Environmental memory divergence: mapped obstacle clearance along turn direction differs by $\ge 1.0\,\text{m}$ (wall within $1.5\,\text{m}$ in $\mathcal{E}_i$ vs open corridor $> 2.5\,\text{m}$ in $\mathcal{E}_j$).
  3. Compute deterministic similarity distance:
     $$d_{ij} = \|s^{(i)}(t_0) - s^{(j)}(t_0)\|_2 + \|s^{\text{body},(i)}(t_0) - s^{\text{body},(j)}(t_0)\|_2$$
  4. Rank candidate pairs in ascending order of $d_{ij}$ and select the first $N = 50$ pairs.
  5. Freeze the pair list into `frozen_tripartite_evaluation_pairs.json` **before** inspecting any prediction outcomes.
- **Directional Swap Verification (Alternate Reality Attraction):**
  Under turn command $u = [-0.7, 0.7]$, swapping memory maps ($\mathbf{M}_1 \leftrightarrow \mathbf{M}_2$) must satisfy:
  1. The prediction under swapped memory must move **toward the ground-truth trajectory of the alternate reality**:
     $$\text{RMSE}(\hat{s}(\mathcal{E}_1 \mid \mathbf{M}_2), s^{*,(2)}) < \text{RMSE}(\hat{s}(\mathcal{E}_1 \mid \mathbf{M}_2), s^{*,(1)}) \quad (\ge 85\% \text{ of pairs})$$
     $$\text{RMSE}(\hat{s}(\mathcal{E}_2 \mid \mathbf{M}_1), s^{*,(1)}) < \text{RMSE}(\hat{s}(\mathcal{E}_2 \mid \mathbf{M}_1), s^{*,(2)}) \quad (\ge 85\% \text{ of pairs})$$
  2. Statistical significance across all $N=50$ pairs: paired Wilcoxon signed-rank test $p < 0.01$.

#### Protocol 4: Mandatory Hard Falsification for Memory Destruction (Gate 4)
- Erasing or scrambling memory are **mandatory hard pass conditions**.
- If a model predicts future sonar with $R^2 \ge 0.60$ on normal trajectories, but erasing the occupancy grid causes $< 25\%$ error surge, the run is immediately stamped:
  $$\mathbf{FAIL} \quad (\text{Verdict: } \texttt{MEMORY\_INERT\_CHEAT})$$

#### Protocol 5: Strict Lexical Hierarchy (Body Can NEVER Compensate for World)
- Strict non-compensatory lexical hierarchy:
  $$\text{Milestone Outcome} = \text{Gate 1} \ \wedge \ \text{Gate 2} \ \wedge \ \text{Gate 3} \ \wedge \ \text{Gate 4} \ \wedge \ \text{Gate 5} \ \wedge \ \text{Gate 6} \ \wedge \ \text{Gate 7}$$
- Gate 1 (Body model fidelity) is a preliminary sanity check with **zero compensatory weight**. Environmental prediction gates must each pass independently.

#### Protocol 6: Genuinely Novel Environments for Final One-Shot Evaluation
- Seed novelty alone is insufficient. For the final post-lock unseen evaluation (`PRIMARY_UNSEEN_TEST`), the following are procedurally generated and frozen strictly **after** architecture, hyperparameters, and weights are locked:
  1. **Arena Geometry:** Novel multi-compartment topologies (L-shaped rooms, T-junctions, variable corridor widths $\in [1.2\,\text{m}, 3.5\,\text{m}]$).
  2. **Obstacle Layout:** Distinct obstacle counts, orientations, and geometries.
  3. **Spawn Poses:** Novel unvisited starting orientations and locations.
  4. **Surface Friction Distributions:** Variable friction patches $\mu \in [0.05, 1.2]$ (glaze ice, smooth tile, high traction).
  5. **Trajectory/Action RNG:** Independent action sequence generation.

---

## 4. Adversarial Pre-Mortem Matrix v2.1

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       ADVERSARIAL PRE-MORTEM MATRIX v2.1                                        │
├────────────────────┬─────────────────────────────┬───────────────────────────────┬──────────────────────────────┤
│ ATTACK VECTOR      │ HOW THE CHEAT WOULD OPERATE │ WHY PHASE 1 FELL FOR IT       │ HOW R2 STRUCTURALLY BLOCKS IT│
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 1. Manufactured    │ Outputs distinct constant   │ Gate 6 only tested pairwise   │ Requires R² >= 0.50 against  │
│    Branching       │ vectors for each branch to  │ divergence:                   │ true physical branch AND     │
│    Divergence      │ manufacture divergence.     │ ||s_A - s_B|| >= 0.80 m.      │ diagonal dominance (>=0.30m).│
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 2. Action Template │ Memorizes 4 fixed action    │ Only 4 discrete actions       │ Adds K=16 randomized         │
│    Memorization    │ vectors ([0.8,0.8], etc.)   │ were tested.                  │ continuous action sequences  │
│                    │ as lookup keys.             │                               │ with random durations.       │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 3. Action Zeroing  │ Defaults to global arena    │ Only evaluated u=0 on active  │ Requires u=0 prediction to   │
│    Spurious Shift  │ mean clearance, shifting    │ physical trajectory; did not  │ match physical coasting run  │
│                    │ error without understanding.│ test physical coasting run.   │ (R² >= 0.60) and fail active.│
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 4. Hidden-State    │ Uses memory vector as a     │ Scramble test was diagnostic; │ Tripartite test with swap:   │
│    Cache Cheat     │ high-capacity recurrent     │ did not control for identical │ must attract to alternate    │
│                    │ shortcut without geometry.  │ current sensor + body state.  │ physical reality (p < 0.01). │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 5. Statistical     │ Generates 1000 candidate    │ Pair selection protocol was   │ Deterministic algorithm      │
│    Cherry-Picking  │ pairs and selects best-     │ unspecified.                  │ pre-registers top N=50 pairs │
│                    │ looking pairs post-hoc.     │                               │ before outcome inspection.   │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 6. Inert           │ Coordinates treated as      │ No mandatory falsification    │ Gate 4 is a mandatory pass   │
│    Coordinates     │ generic regressors; ignores │ gate on memory destruction;   │ gate: Erased memory MUST     │
│    Bypass          │ actual obstacle grid cells. │ no swap intervention.         │ surge error >= +25%.         │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 7. Proprioceptive  │ Body model gets R² = 0.95,  │ Metrics were averaged into    │ Strict lexical hierarchy:    │
│    Masquerade      │ world gets R² = 0.10; claims│ a composite score, hiding     │ Body has 0% compensatory     │
│                    │ "0.80 average fidelity".    │ environmental failure.        │ weight for world gates.      │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 8. Persistence     │ Copies current sonar:       │ Evaluated on flat arena floor │ Module 3 has no sonar input; │
│    Free-Rider      │ s_{t+H} ≈ s_t or Δs ≈ 0.    │ where 80% of steps are static │ evaluated strictly on        │
│                    │                             │ (|Δs| < 0.15 m).              │ D_dynamic (|Δs| >= 0.15 m).  │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 9. Test Set        │ Architectural choices tuned │ Test seeds were accessible    │ Seeds [303,404,505,606,707]  │
│    Overfitting     │ on held-out test seeds.     │ during development.           │ STRICTLY FORBIDDEN from      │
│                    │                             │                               │ existing until Phase D lock. │
└────────────────────┴─────────────────────────────┴───────────────────────────────┴──────────────────────────────┘
```

---

## 5. Developmental Experiment Matrix (DEV Only)

Development is conducted strictly on `DEV_TRAIN` (`seeds [42, 101, 202]`) and `DEV_VAL` (`seeds [210, 220, 230, 240]`). `PRIMARY_UNSEEN_TEST` is strictly forbidden from existing.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               DEVELOPMENTAL EXPERIMENT MATRIX                                  │
├────────────────────┬──────────────────────────────────────────┬─────────────────────────────────┤
│ CONDITION ID       │ ARCHITECTURAL CONFIGURATION              │ SCIENTIFIC PURPOSE              │
├────────────────────┼──────────────────────────────────────────┼─────────────────────────────────┤
│ ARCH-1 (Modular)   │ Body Predictor + Spatial Map + Generator │ Full proposed causal model      │
├────────────────────┼──────────────────────────────────────────┼─────────────────────────────────┤
│ ARCH-2 (No-Memory) │ Body Predictor + Direct Generator        │ Ablates spatial memory substrate│
├────────────────────┼──────────────────────────────────────────┼─────────────────────────────────┤
│ ARCH-3 (No-Body)   │ Direct u -> Spatial Map + Generator      │ Ablates kinematic body model    │
├────────────────────┼──────────────────────────────────────────┼─────────────────────────────────┤
│ ARCH-4 (Matched)   │ Monolithic GRU (Matched Parameters)      │ Direct comparison to Phase 1    │
└────────────────────┴──────────────────────────────────────────┴─────────────────────────────────┘
```

---

## 6. The Seven Frozen Acceptance Gates (v2.1 Hardened)

The Stage 2.2 milestone can be declared **PASSED** if and only if **ARCH-1 passes all seven gates simultaneously**:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            FROZEN ACCEPTANCE GATES                                              │
├────────┬──────────────────────────────┬──────────────────────────────────────────┬──────────────────────────────┤
│ GATE   │ TEST DESCRIPTION             │ PRIMARY EVALUATION METRIC                │ MANDATORY PASS THRESHOLD     │
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 1 │ Body Kinematic Fidelity      │ H=10 Gyro Yaw Rate R²                    │ R² >= 0.75                   │
│        │ (Prerequisite Sanity Check;  │ H=10 Proprioception R²                   │ R² >= 0.85                   │
│        │ Zero Compensatory Power)     │ (Compensatory weight for world: 0.0)     │                              │
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 2 │ Dynamic Sonar Prediction     │ H=10 Sonar R² on D_dynamic (|Δs|>=0.15m) │ R² >= 0.50                   │
│        │ (Anti-Persistence Gate)      │ H=10 Sonar R² on D_all                   │ R² >= 0.60                   │
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 3 │ Physical Action Intervention │ Cross-comparison against independently   │ Surge(u=0 on active) >= +25% │
│        │ (Real Coasting Reality)      │ executed physical active vs coast rollouts│ R²(u=0 on coast) >= 0.60     │
│        │                              │ in MuJoCo physics simulator              │ Surge(active on coast) >= +25%│
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 4 │ Memory Necessity Ablation    │ Error surge under completely erased map  │ Erased: >= +25.0%            │
│        │ (Mandatory Pass Gate)        │ Error surge under spatially scrambled map│ Scrambled: >= +20.0%         │
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 5 │ Tripartite Ambiguity Test    │ N=50 pre-registered pairs; Directional   │ Swap Error(M1->alt reality)  │
│        │ (Same sensor, diff memory;   │ attraction to alternate ground-truth     │ < Error(M1->orig) for >=85%  │
│        │ Pre-registered pair list)    │ physical reality upon memory swap        │ of pairs; Wilcoxon p < 0.01  │
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 6 │ Counterfactual Physical      │ Prediction R² against 4 canonical + K=16 │ ALL 20 branches INDIVIDUALLY │
│        │ Branch Alignment             │ pre-frozen randomized physical rollouts; │ R²(k, s*_k) >= 0.50 (no avg  │
│        │ (Execution-Isolated)         │ Confusion matrix diagonal dominance      │ cloak); Margin >= +0.30 m    │
├────────┼──────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────┤
│ Gate 7 │ Prospective Hazard Oracle    │ ROC-AUC on contact-subtracted            │ ROC-AUC >= 0.85              │
│        │ Collision Anticipation       │ physical obstacle collisions             │                              │
└────────┴──────────────────────────────┴──────────────────────────────────────────┴──────────────────────────────┘
```

---

## 7. Mathematical & Procedural Proof of Non-Gameability

1. **Why Physical Coasting Semantics are Preserved:**  
   Module 1 does not use a static cutoff. When $u=0$, it predicts physical deceleration: forward displacement $\Delta \hat{\mathbf{p}}$ continues with decaying magnitude until speed reaches zero. Gate 3 requires matching true physical coasting ($R^2 \ge 0.60$), making hardcoded zeroing fail immediately.
2. **Why Gate 5 Cannot Be Cherry-Picked:**  
   Candidate pairs are generated, filtered, ranked by distance $d_{ij}$, and the top $N=50$ pairs are frozen into a manifest before calculating model metrics. No human or automated selection of "best-looking" pairs is possible.
3. **Why Template Memorization Fails Gate 6:**  
   The evaluator executes $K=16$ randomly sampled continuous action sequences with random durations and steering asymmetries generated from a frozen RNG after model freeze. A model with memorized canonical actions will fail on the random sequences ($R^2 < 0.50$).
4. **Why Swapped Memory Proves Geometric Reality:**  
   A generic memory buffer causes indiscriminate error increase when swapped. In Gate 5, the model must show directional attraction: its swapped prediction must be closer to the *alternate physical reality* than to the original physical reality for $\ge 85\%$ of frozen pairs ($p < 0.01$).
5. **Why Subprocess Air-Gap Eliminates All Sensor Leaks:**  
   The mental rollout executes in a sandboxed Python process where `sys.modules['mujoco'] = None`. The model cannot call `mj_ray`, touch `qpos`, or peek at simulator geometry.
