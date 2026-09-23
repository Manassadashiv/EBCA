# CARL STAGE 2.2: REVISED PRE-EXPERIMENTAL SPECIFICATION
## Action-Conditioned Predictive World Model & Environmental Grounding Protocol
**Author:** Antigravity AI Research Orchestrator  
**Classification:** [IMMUTABLE PRE-EXPERIMENTAL SPECIFICATION]  
**Status:** **PROPOSED REVISED SPECIFICATION (IMPLEMENTATION & TRAINING STRICTLY FROZEN)**  
**Milestone:** Stage 2.2-DIAG / Stage 2.2-R1  
**Date:** September 5, 2026  
**Target Repository:** `d:/ebca`  

---

## 1. Executive Directive & Research Questions

### 1.1 Core Scientific Objective
> **Determine what CARL actually needs in order to learn a genuine action-conditioned predictive world model.**

The model must answer the prospective sensorimotor question:
$$\text{“Given what I currently sense } s_t \text{, where I am } \mathbf{x}_t \text{, what my body is doing } \mathbf{b}_t \text{, and what action I choose } u_t \text{, what will I sense next } s_{t+1} \text{?”}$$

### 1.2 Five Orthogonal Dimensions to Distinguish
The experiment is designed to decouple and measure five distinct phenomena:
1. **Temporal Persistence / Copy Behavior:** Can the model predict anything beyond repeating recent observations?
2. **Body / Self Dynamics:** Can the model predict internal kinematics (wheel speeds, gyro, slip, battery)?
3. **Action-Conditioned Dynamics:** Do predictions actively diverge when actions change ($u_A$ vs $u_B$)?
4. **Spatial Grounding:** Does knowing heading and displacement relative to origin change environmental predictions?
5. **Environmental Structure / Memory:** Does the model possess a representation of where physical obstacles and boundaries exist in the world?

---

## 2. Non-Negotiable Methodological Invariants

1. **NO DATA LEAKAGE & ABSOLUTE PRIMARY-TEST ISOLATION:**
   - Strict tripartite partitioning: `DEV_TRAIN` (seeds `[42, 101, 202]`; $60\%$), `DEV_VAL` (seeds `[210, 220, 230, 240]`; $20\%$), `PRIMARY_UNSEEN_TEST` (seeds `[303, 404, 505, 606, 707]`; $20\%$).
   - **Absolute Primary-Test Isolation Rule:** `PRIMARY_UNSEEN_TEST` must not exist in accessible form during Phase 1. It must be generated only after the architecture, hyperparameters, metrics, preprocessing, and diagnostic conclusions are frozen (Phase 3).
   - Phase 1 diagnostic benchmarking across all 13 model configurations is strictly restricted to **`DEV_TRAIN` $\to$ `DEV_VAL` only**, with `DEV_VAL` spanning 4 independent environment seeds to prevent single-seed validation bias.
   - Normalization statistics ($\boldsymbol{\mu}, \boldsymbol{\sigma}$) must be computed **strictly on `DEV_TRAIN`** and frozen.
   - Zero exposure of unseen test data during training, hyperparameter tuning, model selection, or architecture search.
   - Unseen-test evaluation is strictly **one-shot and post-freeze** in Phase 3.
2. **NATURAL EMBODIED EXPERIENCE ONLY:**
   - Generate physical trajectories that naturally produce sufficient near-field sonar observations.
   - Sensor returns are never artificially clamped, scaled, or fabricated. All observations reflect unedited physics interactions in the environment.
3. **NO SIMULATOR LEAKAGE:**
   - Mental forward rollouts must execute entirely within neural computational space.
   - Absolute prohibition on importing `mujoco` or accessing internal simulator data structures (`mj_ray`, `data.qpos`, `data.qvel`, `data.contact`, collision trees, geom positions).
   - Enforced by automated static AST trace and poisoned-subprocess test sandbox (`sys.modules['mujoco'] = None`).
4. **NO HAND-CODED PHYSICS:**
   - Absolute prohibition on embedding geometric formulas ($x = v \cos\theta$), analytic raytracers, mathematical wall-distance equations, or hard-coded obstacle positions into the predictor.
   - All spatial relationships must be learned from sensorimotor experience and internal neural representations.
5. **NO TEST-TIME ADAPTATION:**
   - No Recursive Least Squares (RLS), no online gradient steps, no running batch-norm updates, no seed-specific calibration, and no post-hoc rescaling at evaluation time.
6. **NO THRESHOLD MOVING:**
   - Pre-registered gates, metric thresholds, and failure criteria are frozen in this document.
   - A failure is reported as a FAIL. Thresholds are never lowered to manufacture a pass.
7. **NO CHERRY-PICKING:**
   - Every episode and every seed in the unseen test set must be reported with unrounded raw values.
   - No discarding difficult trajectories, collision events, or edge cases.
8. **NO CLAIMS OF "EMERGENCE":**
   - Distinguish strictly between engineered network topology and learned parameters.
   - No claims of biological cognition, consciousness, sentience, or human-level intelligence.
9. **ZERO PRIVILEGED GPS / SIMULATOR-POSITION LEAK:**
   - CARL's spatial state ($\mathbf{v}_{\text{HD}}$, $\mathbf{G}_{\text{grid}}$) must ONLY be initialized from information available to CARL through its allowed sensory/motor history.
   - Absolute prohibition on initializing internal spatial state from simulator coordinates, `qpos`, geom positions, obstacle locations, or evaluator state.
   - Spatial integration begins at internal origin $(0, 0)$ at the birth of the trajectory. Any allocentric relationship to walls must be learned purely from sensorimotor observations.

---

## 3. The 6-Condition Diagnostic Experiment

To rigorously establish which information sources actually drive predictive accuracy, six distinct models will be trained on identical data and evaluated under identical conditions:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           THE 6-CONDITION ARCHITECTURAL TAXONOMY                                │
├───────────┬───────────────────────────────────────────────────┬──────────────┬──────────────────┤
│ CONDITION │ INPUT BUS REPRESENTATION                          │ INPUT DIMS   │ INFORMATION TYPE │
├───────────┼───────────────────────────────────────────────────┼──────────────┼──────────────────┤
│ Cond A    │ Sensory History S_{t-k:t}                         │ 25 * (k+1)   │ Sensory Only     │
│ Cond B    │ Sensory History + Actions U_{t-k:t}               │ 31 * (k+1)   │ + Motor Intent   │
│ Cond C    │ S + U + Stage 2.1 HD Ring v_HD                    │ 33 * (k+1)   │ + Heading Self   │
│ Cond D    │ S + U + Stage 2.1 Grid Torus G_grid               │ 33 * (k+1)   │ + Displacement   │
│ Cond E    │ S + U + HD Ring v_HD + Grid Torus G_grid          │ 35 * (k+1)   │ + Full Self-Pose │
│ Cond F    │ S + U + v_HD + G_grid + Learned Environmental Mem │ 35 + d_mem   │ + World Memory   │
└───────────┴───────────────────────────────────────────────────┴──────────────┴──────────────────┘
```

### 3.1 Strict Definition & Provenance of Condition F (Learned Environmental Memory)
"Environmental memory" in Condition F is strictly defined as an internal neural representation updated over time:
$$\mathbf{M}_t = \text{MemoryUpdate}(\mathbf{M}_{t-1}, s_t, u_t, \mathbf{v}_{\text{HD}, t}, \mathbf{G}_{\text{grid}, t})$$
- **Allowed Information Sources (Strict Provenance):**
  1. Past sensory history ($s_{0:t}$)
  2. Past actions ($u_{0:t}$)
  3. Internal self-model dead-reckoning state ($\mathbf{v}_{\text{HD}, t}, \mathbf{G}_{\text{grid}, t}$)
- **Strictly Prohibited:**
  - True simulator coordinates ($x, y$ from MuJoCo `qpos`)
  - Ground-truth arena maps or obstacle coordinates
  - Simulator collision geometry or raycasters
- Condition F represents an explicit learned spatial-attentive recurrent memory (e.g. key-value spatial memory where key = internal pose phase, value = sensory return) trained strictly end-to-end from sensorimotor experience.

### 3.2 Parameter-Count Confound Control & Matched Capacity
To ensure that performance differences between Condition F and simpler conditions are not caused by parameter-capacity scaling:
1. **Target Parameter Budget:** All base models are calibrated to $\approx 90\text{K} \pm 5\%$ trainable parameters by adjusting the recurrent hidden dimension $d_h$ (e.g. Condition B with $d_h = 128$ vs Condition F with $d_h = 104$ plus memory query/key projections).
2. **Matched-Capacity Control Model (`M2-B-MATCHED`):** A high-capacity sensory+action baseline (Condition B) with the exact parameter count of Condition F will be evaluated in parallel. Condition F is only considered superior if it statistically outperforms `M2-B-MATCHED`.

---

## 4. Target Formulation: The Residual Prediction ($\Delta s$) Hypothesis Test

To formally resolve the identity shortcut, we do not assume $\Delta s$ solves everything. A model can easily learn $\Delta s \approx 0$ if the dataset is dominated by slow or static drift. We establish a controlled 2x2 factorial comparison:

```
                          ┌───────────────────────┬───────────────────────┐
                          │   DIRECT PREDICTION   │   RESIDUAL PREDICTION │
                          │     ŝ_{t+1}           │     s_t + Δŝ_t        │
┌─────────────────────────┼───────────────────────┼───────────────────────┤
│ Without Spatial/Memory  │ Direct-Sensory        │ Residual-Sensory      │
│ (Cond B: S + U)         │ (Old Stage 2.2)       │ (Kills copy shortcut) │
├─────────────────────────┼───────────────────────┼───────────────────────┤
│ With Spatial/Memory     │ Direct-Spatial        │ Residual-Spatial      │
│ (Cond E / Cond F)       │ (Prior Benchmark)     │ (True Hypothesis Test)│
└─────────────────────────┴───────────────────────┴───────────────────────┘
```

### 4.1 Mathematical Formulations
1. **Direct-State Predictor:**
   $$\hat{s}_{t+1} = f_\theta(h_t, x_t)$$
   Loss: $\mathcal{L}_{\text{direct}} = \|\hat{s}_{t+1} - s_{t+1}\|^2_{\mathbf{W}}$
2. **Residual-State Predictor (Euler Delta):**
   $$\Delta \hat{s}_t = g_\theta(h_t, x_t)$$
   $$\hat{s}_{t+1} = s_t + \Delta \hat{s}_t$$
   Loss: $\mathcal{L}_{\text{residual}} = \|\Delta \hat{s}_t - (s_{t+1} - s_t)\|^2_{\mathbf{W}}$

---

## 5. The Canonical Six Pre-Registered Test Batteries

To prevent diagnostic ambiguity, the final evaluation consists of **exactly six pre-registered batteries** on the frozen unseen test partition ($N=25$ episodes across seeds `[303, 404, 505, 606, 707]`):

### Battery 1 — Predictive Fidelity ($H=10$, $300\,\text{ms}$)
- **Gate 1A (Dynamic Sonar $s < 4.5\,\text{m}$):** $R^2 \ge 0.60$.
- **Gate 1B (High-Change Transition Sonar $\mathcal{D}_{\text{dynamic}}$):** $R^2 \ge 0.50$, evaluated strictly on transitions with $|\Delta s_{\text{sonar}}| \ge 0.15\,\text{m}$ (prevents $\Delta s \approx 0$ static cheat).
- **Gate 1C (Gyroscope Yaw Rate):** $R^2 \ge 0.70$.
- **Gate 1D (Proprioception - Wheels & Joints):** $R^2 \ge 0.85$.
- **Gate 1E (Normalized Composite Sensory RMSE):** $\text{RMSE} \le 2.00$.

### Battery 2 — Action Causality
A genuine forward model must degrade significantly when its motor causes are corrupted:
- **Gate 2A (Action Zeroing $u = 0$):** Error surge $\Delta \mathcal{E} \ge +25.0\%$.
- **Gate 2B (Action Temporal Permutation):** Error surge $\Delta \mathcal{E} \ge +20.0\%$.
- **Gate 2C (Action Sign Inversion $u \to -u$):** Error surge $\Delta \mathcal{E} \ge +25.0\%$.

### Battery 3 — Spatial Causality
- **Gate 3A (Spatial Coordinate Scrambling):** Randomizing $[x, y]$ inputs to Condition E/F must degrade dynamic sonar prediction by $\ge 20.0\%$.
- **Gate 3B (Heading Scrambling):** Permuting $\mathbf{v}_{\text{HD}}$ must degrade gyro and directional sonar prediction by $\ge 20.0\%$.

### Battery 4 — Spatial Disambiguation ("Same Sensory State, Different World Context")
- **Protocol & Pre-Registered Tolerance:** Identify naturally occurring trajectory state pairs in the validation set where immediate forward local sensory observations match within pre-registered tolerance ($\max_{k \in [4, 10]} |s_{1, k} - s_{2, k}| \le 0.35\,\text{m}$ or $\text{MAE}_{\text{all}} \le 0.40\,\text{m}$), while internal spatial positions are widely separated ($\|\mathbf{g}_1 - \mathbf{g}_2\|_2 \ge 1.20\,\text{m}$).
- **Action Injected:** Hard Right Turn ($u = [0.6, -0.6]$) for 10 ticks.
- **Gate 4:** The model must predict diverging sonar profiles corresponding to the differing spatial contexts ($\|\hat{s}_{\text{loc1}} - \hat{s}_{\text{loc2}}\|_2 \ge 1.0\,\text{m}$).

### Battery 5 — Counterfactual Action Branching
- Given identical starting state at $t_0$, unroll 3 candidate action sequences for 15 ticks purely neurally (Zero MuJoCo queries):
  - Branch A: Forward ($u = [0.7, 0.7]$)
  - Branch B: Left Spin ($u = [-0.7, 0.7]$)
  - Branch C: Reverse ($u = [-0.6, -0.6]$)
- **Gate 5:** Neural predictions must diverge pairwise by $\text{MAE} \ge 0.80\,\text{m}$ across sonar beams by tick 10, matching independently measured physical branch outcomes.

### Battery 6 — Collision Anticipation (Fixed Ground-Contact Oracle)
- **Fixed Oracle Ground Truth:**
  $$\text{Collision Event } \iff (\text{carl\_contacts} - \text{floor\_contacts}) > 0$$
- Predict collision within 10 ticks from neural rollout:
  $$\hat{c} = \max_{k \in [1, 10]} \mathbb{I}(\min(\hat{s}_{t+k, 0:14}) < 0.25\,\text{m})$$
- **Gate 6:** $\text{ROC-AUC} \ge 0.85$ across balanced physical trials.

### Secondary Non-Gated Diagnostics (Reported for Scientific Completeness)
- Glaze ice friction invariance ($\mu = 0.005$, target $R^2 \ge 0.60$).
- Battery drain tracking ($\text{MAE} \le 0.05$).
- Multi-horizon error growth slope $\beta$ ($H=1..30$, target $\beta \le 0.060$).

---

## 6. Explicit Pass/Fail Criteria & Falsification Table

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FORMAL FALSIFICATION MATRIX                                   │
├────────────────────────────────────────────────────┬────────────────────┬───────────────────────┤
│ EMPIRICAL OBSERVATION                              │ CONCLUSION         │ ARCHITECTURAL VERDICT │
├────────────────────────────────────────────────────┼────────────────────┼───────────────────────┤
│ Cond B action-zero surge < 10% under residual Δs   │ Hypothesis Falsified│ Residual formulation  │
│                                                    │                    │ fails to couple motor │
├────────────────────────────────────────────────────┼────────────────────┼───────────────────────┤
│ High-change sonar R² (Gate 1B) collapses < 0.20    │ Trivial Cheat      │ Residual model learned│
│                                                    │ Detected           │ Δs ≈ 0 persistence    │
├────────────────────────────────────────────────────┼────────────────────┼───────────────────────┤
│ Cond E (HD+Grid) sonar R² < 0.40 at H=10           │ Hypothesis Proven  │ Stage 2.1 coordinates │
│                                                    │                    │ lack obstacle geometry│
├────────────────────────────────────────────────────┼────────────────────┼───────────────────────┤
│ Cond F equals M2-B-MATCHED (no statistical gain)   │ Capacity Confound  │ Environmental memory  │
│                                                    │                    │ provides no gain      │
├────────────────────────────────────────────────────┼────────────────────┼───────────────────────┤
│ Cond F passes all 6 batteries & beats matched B    │ World Model Proven │ Memory substrate is   │
│                                                    │                    │ necessary & sufficient│
└────────────────────────────────────────────────────┴────────────────────┴───────────────────────┘
```

### Overall Milestone Approval Rule:
Stage 2.2 can be declared **PASSED** if and only if **one of the candidate architectures passes ALL 6 Batteries simultaneously** on the frozen unseen test partition. If no condition passes all 6, Stage 2.2 remains **FAILED**.
