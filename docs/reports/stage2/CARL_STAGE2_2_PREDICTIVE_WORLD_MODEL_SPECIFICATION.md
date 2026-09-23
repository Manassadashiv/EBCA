# CARL STAGE 2.2: PRE-EXPERIMENTAL SPECIFICATION
## RECURRENT MULTI-STEP SENSORY SYNTHESIS & EMBODIED FORWARD WORLD MODEL
**Author:** Antigravity AI Orchestrator  
**Classification:** [IMMUTABLE PRE-EXPERIMENTAL SPECIFICATION]  
**Status:** **LOCKED SPECIFICATION AWAITING USER APPROVAL (IMPLEMENTATION FROZEN)**  
**Milestone:** Stage 2.2 — Predictive World Modeling & Counterfactual Rollout  
**Date:** September 5, 2026  
**Target Module:** `brain/carl_stage2_2_world_model.py`  
**Target Organism Integration:** `brain/carl_stage2_integrated_brain.py` (Layer 6 Organ)  

---

## 1. Executive Directive & North Star Invariants

### 1.1 The Core Scientific Objective
The objective of Stage 2.2 is:
> **To determine whether CARL can learn, from embodied experience, an internal model that predicts the sensory consequences of its actions.**
> The objective is NOT to manufacture good prediction numbers through privileged state access, teacher forcing, or hand-coded physics.

### 1.2 North Star Principles
1. **One Canonical Unified Embodied Organism:**  
   CARL is a single, continuous developmental system. Stage 2.2 is an organ being developed for that organism, not a disconnected or competing parallel brain.
2. **Strict Stage Scoping:**  
   Stage 2.2 is strictly confined to **Predictive World & Self Modeling**.  
   No Stage 3 planning, MPPI, autonomous policy optimization, Place Cells, lifelong-memory architecture, or permission-gated self-modification may be introduced.
3. **No Fabricated Predictions:**  
   The forward model must run entirely in neural computational space without querying MuJoCo simulation internals (`mj_ray`, `data.qpos`, `data.qvel`, `data.contact`).
4. **Epistemic Honesty:**  
   Distinguish explicitly between the **ENGINEERED SUBSTRATE** and the **LEARNED CAPABILITY**. Do not call standard machine learning "emergence" or describe a GRU as proof of biological cognition, consciousness, sentience, or human-like intelligence.

---

## 2. Explicit Epistemic Classification: Engineered Substrate vs. Learned Capability

To prevent rhetoric inflation and maintain absolute scientific rigor, all components of Stage 2.2 are pre-classified:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        EPISTEMIC COMPONENT CLASSIFICATION                              │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ ENGINEERED SUBSTRATE                     │ LEARNED CAPABILITY                          │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • GRU Recurrent Architecture (d_h = 128) │ • Recurrent transition dynamics W_rec       │
│ • Sensory Decoder MLP & bounds clamps    │ • Observation synthesis mapping W_dec       │
│ • Multi-Horizon Weighted MSE Loss        │ • Action-to-gyro contingency discovery      │
│ • AdamW Optimizer & Cosine Decay         │ • Acoustic flow distance prediction         │
│ • Frozen Z-Score Normalization Pipeline  │ • Mechanical traction loss prediction       │
│ • Sensor Bus Topology (25-D vector)      │ • Temporal forward representation           │
│ • 4-Partition Dataset Infrastructure     │ • Counterfactual obstacle collision warning │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 3. Mathematical Architecture

### 3.1 State & Observation Spaces
- **Sensory Observation Vector $s_t \in \mathbb{R}^{25}$ (Anonymous Continuous Values):**
  - $s_{0:14}$: 15 Sonar ray range returns $[0.0, 5.0]\,\text{m}$ (exteroceptive field spanning $[-120^\circ, +120^\circ]$)
  - $s_{15:17}$: 3 IMU linear acceleration components $[ -50.0, +50.0]\,\text{m/s}^2$
  - $s_{18:20}$: 3 IMU angular velocity components (gyro) $[ -20.0, +20.0]\,\text{rad/s}$
  - $s_{21:23}$: 3 Joint proprioceptive positions (hip pitch, neck sweep, head pan) $[ -\pi, +\pi]\,\text{rad}$
  - $s_{24}$: 1 Battery level state $[0.0, 1.0]$
- **Internal Spatial Self-Model Heading Vector $\mathbf{v}_{\text{HD}} \in \mathbb{R}^2$ (From Stage 2.1 HD Ring):**
  - $[\cos\hat{\theta}_{\text{HD}}, \sin\hat{\theta}_{\text{HD}}]$: 2D directional unit vector decoded from the 64-neuron Head-Direction Ring Attractor. Directly grounds the world model in Stage 2.1's spatial self-model without leaking privileged Cartesian coordinates.
- **Motor Efference Command Vector $u_t \in [-1.0, 1.0]^6$:**
  - $u_{0:1}$: Differential wheel drive commands $(u_{\text{left}}, u_{\text{right}})$
  - $u_{2:5}$: Auxiliary robotic actuators (joints, head pan, neck sweep)
- **Total Composite World Model Input Vector $x_t \in \mathbb{R}^{33}$:**
  $$x_t = [\tilde{s}_t; \mathbf{v}_{\text{HD}, t}; u_t] \in \mathbb{R}^{25 + 2 + 6 = 33}$$
- **Internal Recurrent Belief State $h_t \in \mathbb{R}^{d_h}$:**
  - Latent temporal memory encoding history of sensorimotor contingencies ($d_h = 128$).

### 3.2 Action-Conditioned Forward Dynamics & Observation Decoder
The forward model consists of two parameter sets $\boldsymbol{\theta} = \{\mathbf{W}_{\text{enc}}, \mathbf{W}_{\text{rec}}, \mathbf{W}_{\text{dec}}\}$:

1. **Recurrent Belief State Transition:**
   $$h_{t+1} = \text{GRU}_{\boldsymbol{\theta}}(h_t, x_t) = \text{GRU}_{\boldsymbol{\theta}}(h_t, [\tilde{s}_t; \mathbf{v}_{\text{HD}, t}; u_t])$$
   where $\tilde{s}_t = (s_t - \boldsymbol{\mu}_{\text{dev}}) \oslash \boldsymbol{\sigma}_{\text{dev}}$ is the normalized observation vector standardized using frozen `DEV_TRAIN` statistics.
2. **Sensory Synthesis Decoder:**
   $$\hat{s}_{t+1} = \boldsymbol{\mu}_{\text{dev}} + \boldsymbol{\sigma}_{\text{dev}} \odot g_{\boldsymbol{\theta}}(h_{t+1})$$
   where $g_{\boldsymbol{\theta}}$ is a multi-layer perceptron with linear output for continuous dynamics, followed by clamping to physical channel bounds $[s_{\min}, s_{\max}]$.

### 3.3 Autoregressive Multi-Step Rollout Formulation (Mental Simulation)
To simulate $H$ steps into the future given candidate motor sequence $u_{t:t+H-1}$:
$$\begin{aligned}
\tilde{h}_0 &= h_t, \quad \tilde{s}_0 = s_t, \quad \tilde{\mathbf{v}}_0 = \mathbf{v}_{\text{HD}, t} \\
\text{For } k &= 0, 1, \dots, H-1: \\
\tilde{x}_k &= [\text{Norm}(\tilde{s}_k); \tilde{\mathbf{v}}_k; u_{t+k}] \in \mathbb{R}^{33} \\
\tilde{h}_{k+1} &= \text{GRU}_{\boldsymbol{\theta}}(\tilde{h}_k, \tilde{x}_k) \\
\hat{s}_{t+k+1} &= \text{Denorm}(g_{\boldsymbol{\theta}}(\tilde{h}_{k+1})) \\
\tilde{s}_{k+1} &= \hat{s}_{t+k+1} \quad \text{\textbf{(STRICT AUTOREGRESSIVE FEEDBACK, ZERO TEACHER FORCING)}} \\
\tilde{\mathbf{v}}_{k+1} &= \text{UpdateHeadingStep}(\tilde{\mathbf{v}}_k, \hat{s}_{t+k+1, 18:20}) \quad \text{\textbf{(INTERNAL GYRO INTEGRATION)}}
\end{aligned}$$

---

## 4. Strict Causality, Anti-Cheat, & Call-Graph Verification

### 4.1 Permitted Information at Prediction Time $t$
The predictive model may access ONLY:
- Past and current sensory observations: $\{s_\tau\}_{\tau \le t}$
- Past and current executed motor actions: $\{u_\tau\}_{\tau \le t}$
- Internal recurrent state of the organism at time $t$: $h_t$
- Proposed future action sequence for the rollout: $\{u_{t+k}\}_{k=0}^{H-1}$

### 4.2 Absolute Prohibitions at Prediction Time $t$ (Hard Violations)
The predictive model and rollout engine must **NEVER** access:
- MuJoCo internal state variables (`data.qpos`, `data.qvel`, `data.qacc`)
- MuJoCo collision or contact structures (`data.contact`, `data.ncon`)
- Simulator geometric coordinates or obstacle bounding boxes
- MuJoCo raycasting engines (`mujoco.mj_ray`)
- Future simulator ground-truth states ($s_{t+k}$ for $k \ge 1$)
- Future environment variables or ground-truth friction coefficients $\mu$
- Privileged Cartesian positions $(x, y, z)$ or global headings $\theta_{\text{world}}$

### 4.3 Two-Tier Anti-Cheat Call-Graph Verification
1. **Full Call-Graph AST Static Analysis (`tests/test_stage2_2_anti_cheat_isolation.py`):**
   Recursively traces all imported project modules reachable from the mental rollout function. Asserts zero occurrences of `mujoco`, `CarlStage1HAL`, `data.qpos`, `data.qvel`, `data.contact`, and `mj_ray`.
2. **Subprocess MuJoCo Poisoning Sandbox:**
   Executes the mental forward rollout in an isolated Python subprocess where `sys.modules['mujoco'] = None`. If the forward rollout requires MuJoCo to execute or fails to run without it, it triggers an immediate **HARD FAIL**.

---

## 5. Four-Partition Data Architecture & Randomization Locking

### 5.1 The Four Explicit Partitions

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FOUR ISOLATED DATA PARTITIONS                             │
├──────────────────────┬──────────────────────┬────────────┬─────────────────────────────┤
│ Partition Name       │ Seeds                │ Episodes   │ Permitted Usage             │
├──────────────────────┼──────────────────────┼────────────┼─────────────────────────────┤
│ DEV_DEBUG            │ 42                   │ 5 episodes │ Pipeline test, smoke tests  │
│ DEV_TRAIN            │ [42, 101, 202]       │ 60 episodes│ Parameter updates (SGD)     │
│ DEV_VAL              │ [42, 101, 202] (nov) │ 20 episodes│ Checkpoint & hyperparam sel │
│ PRIMARY_UNSEEN_TEST  │ [303, 404, 505, 606, │ 25 episodes│ Official frozen evaluation  │
│                      │  707]                │ (5 / seed) │ (strictly once post-freeze) │
└──────────────────────┴──────────────────────┴────────────┴─────────────────────────────┘
```

### 5.2 Partition Invariants & Anti-Contamination Assertions
1. **Normalization Invariant:** Normalization statistics $(\boldsymbol{\mu}_{\text{dev}}, \boldsymbol{\sigma}_{\text{dev}})$ are computed strictly on `DEV_TRAIN` and saved to `checkpoints/stage2_2_norm_stats.npz`. `PRIMARY_UNSEEN_TEST` data must never participate in computing scaling moments.
2. **Checkpoint Selection:** Checkpoint selection is performed strictly on `DEV_VAL` autoregressive loss ($H=10$).
3. **Late Generation & Cryptographic Hashing:** `PRIMARY_UNSEEN_TEST` is generated and hashed with SHA-256 ONLY after model training, hyperparameters, and evaluation scripts are locked.
4. **Automated Assertion:** Automated test assertions verify that the SHA-256 hash of `PRIMARY_UNSEEN_TEST` does not appear in any training loader log.

### 5.3 Hierarchical Randomization Locking
Every generated episode records:
- Master RNG seed
- Episode seed: $S_{\text{ep}} = \text{hash}(\text{master\_seed}, \text{partition}, \text{ep\_idx})$
- Environment geometry seed (obstacle layout)
- Action sequence generator seed
- Floor friction seed
- SHA-256 hash of the complete dataset file

A rerun with the identical configuration reproduces the exact bit-for-bit sensory trajectory.

---

## 6. Training Protocol & Hard Model Freeze

### 6.1 Training Hyperparameters & Schedule
- **Architecture:** 1-layer GRU ($d_{\text{in}} = 33, d_h = 128$) + MLP Decoder ($128 \to 128 \to 25$ with SiLU).
  - Input: 25 normalized sensors $\tilde{s}_t$ + 2-D Stage 2.1 HD ring heading vector $[\cos\hat{\theta}_{\text{HD}}, \sin\hat{\theta}_{\text{HD}}]$ + 6 motor actions $u_t = 33\,\text{dims}$.
- **Optimization:** AdamW ($\text{lr} = 1 \times 10^{-3}$, weight decay $= 1 \times 10^{-4}$, gradient clipping norm $= 1.0$).
- **Loss Formulation:** Multi-horizon autoregressive sequence loss:
  $$\mathcal{L}(\boldsymbol{\theta}) = \frac{1}{B} \sum_{b=1}^B \sum_{k=1}^H \sum_{j=0}^{24} w_j \left( \frac{\hat{s}_{b, k, j} - s_{b, k, j}}{\sigma_{\text{dev}, j}} \right)^2$$
  where $w_{\text{sonar}} = 1.0, w_{\text{gyro}} = 2.0, w_{\text{accel}} = 1.0, w_{\text{proprio}} = 1.0, w_{\text{batt}} = 0.1$.
- **Stopping Rule:** Early stopping triggered when `DEV_VAL` autoregressive loss ($H=10$) fails to improve for 15 consecutive epochs.

### 6.2 Hard Freeze Post-Checkpoint Selection
Immediately after saving `checkpoints/carl_stage2_2_world_model_frozen.pt`:
- Parameters $\boldsymbol{\theta}$ are permanently frozen (`requires_grad = False`).
- The optimizer is completely deleted.
- All online learning and adaptation hooks (`update_model`, RLS) are disabled.
- **Model Hash Assertion:** The test harness computes $\text{hash}_{\text{before}} = \text{SHA256}(\boldsymbol{\theta})$ before evaluating each unseen seed and $\text{hash}_{\text{after}} = \text{SHA256}(\boldsymbol{\theta})$ immediately after.
  $$\text{assert } \text{hash}_{\text{before}} == \text{hash}_{\text{after}}$$

---

## 7. True Statistical Units & Pre-Registered Falsification Gates

### 7.1 Pre-Registered Statistical Unit
- **Independent Statistical Unit:** The **individual evaluation episode** ($N = 25$ episodes across the 5 unseen seeds, 5 episodes per seed).
- **Reporting Requirement:** Metrics must be reported per episode, per seed, and aggregated across episodes.

### 7.2 Gate 2.2A: Multi-Step Held-Out Prediction Fidelity ($H \in \{1, 5, 10, 15, 30\}$)
- **Active Channels** (DEV variance $\sigma_j^2 \ge 10^{-4}$): Evaluated via $R^2$, MAE, RMSE.
- **Quiescent Channels** ($\sigma_j^2 < 10^{-4}$, e.g. Battery $s_{24}$): Evaluated via MAE and RMSE only (excluded from $R^2$ averaging to prevent division by near-zero variance).
- **Sonar Dynamic Return Filter:** To prevent the "empty room / 5m saturation trap" (where guessing constant 5.0m in open space inflates $R^2$), sonar performance must be reported both overall and specifically on **active/dynamic returns ($s_{\text{true}} < 4.5\,\text{m}$)**.
- **Pre-Registered Passing Thresholds at $H = 10$ ticks (0.30 s):**
  - IMU Angular Velocity Gyro ($s_{18:20}$): Mean $R^2 \ge 0.70$ (worst seed $\ge 0.55$).
  - Sonar Dynamic Returns ($s_{0:14}, s < 4.5\,\text{m}$): Mean $R^2 \ge 0.60$ (worst seed $\ge 0.45$).
  - Proprioceptive Joint Angles ($s_{21:23}$): Mean $R^2 \ge 0.80$ (worst seed $\ge 0.70$).
  - Active 24-D Composite Mean $R^2 \ge 0.65$ across all 25 unseen episodes.

### 7.3 Gate 2.2B: Counterfactual Collision Anticipation
- **Task:** 50 randomized obstacle trials per unseen seed (250 total trials). Robot placed at $d_0 \in [0.25, 0.65]\,\text{m}$ facing obstacle with heading offset $\Delta \psi \in [-60^\circ, +60^\circ]$ (including oblique/glancing angles).
- **Counterfactual Action Proposal A (Collide):** $u_{\text{fwd}} = +0.6, u_{\text{turn}} = 0.0$ for 20 ticks.
- **Counterfactual Action Proposal B (Evade):** $u_{\text{fwd}} = 0.0, u_{\text{turn}} = +0.7$ for 20 ticks.
- **Ground Truth:** Physical contact ($N_{\text{contact}} > 0$) OR minimum clearance $\le 0.02\,\text{m}$ in physical evaluation.
- **Predictive Classifier:** Purely sensory: $\hat{C} = \mathbb{I}\left( \min_{k \le 15} \hat{s}_{\text{front}, k} \le 0.15\,\text{m} \right)$.
- **Passing Thresholds:**
  - ROC-AUC $\ge 0.88$ across 250 pooled unseen trials.
  - PR-AUC $\ge 0.85$.
  - False Positive Rate $\le 0.15$ at $90\%$ True Positive Recall.

### 7.4 Gate 2.2C: Friction / Traction Grounding Invariance
- **Protocol:** The robot drives forward on floor entering glaze ice ($\mu = 0.005$).
- **5-Tick Observed Slip History Window:** The rollout is evaluated *after* a mandatory 5-tick physical observation window ($150\,\text{ms}$) where wheels spin, IMU acceleration chatter drops, and acoustic flow halts. This ensures the model observes slip before being asked to predict its future consequences (closing the "psychic ice" loophole).
- **Mental Rollout:** Given this 5-tick history, the model performs a 25-tick autoregressive rollout under continuing forward drive ($u_{\text{fwd}} = +0.5$).
- **Requirement:** Model receives zero friction labels or ice flags. It must predict zero forward sonar range closure on ice conditioned on the observed slip dynamics.
- **Passing Threshold:** $R^2_{\text{ice}} \ge 0.60$ on sonar channels across unseen seeds.
- **Passing Threshold:** $R^2_{\text{ice}} \ge 0.60$ on sonar channels across unseen seeds.

### 7.5 Gate 2.2D: Long-Horizon Autoregressive Stability ($H = 30$ ticks / 0.90 s)
- **Numerical Integrity:** Exactly 0 NaNs/Infs, exactly 0 physical range violations.
- **Error Growth Model:** Fit log-linear model $\ln(\text{RMSE}_k) = \alpha + \beta \cdot k$ for $k \in \{1, \dots, 30\}$.
- **Passing Thresholds:**
  - Fitted slope $\beta \le 0.06$ (doubling time $> 11.5$ ticks).
  - Maximum horizon RMSE ratio: $\text{RMSE}_{30} \le 3.5 \cdot \text{RMSE}_1$.

---

## 8. Mandatory Baselines & Causal Ablation Controls

### 8.1 Baseline Comparison Protocol
All models evaluated on the **exact same 25 unseen test episodes**:
1. **Baseline A (Naive Persistence Predictor):** $\hat{s}_{t+k} = s_t$.
2. **Baseline B (Linear Action Readout):** Ridge regression $\hat{s}_{t+k} = \mathbf{W}_s s_t + \mathbf{W}_u u_{t+k-1} + \mathbf{b}$.
3. **Learned Recurrent World Model:** Proposed GRU architecture.
- **Statistical Significance Requirement:**
  - Paired Wilcoxon signed-rank test on episode errors ($N=25$): $p < 0.01$.
  - Substantive Effect Size: Cohen's $d \ge 0.50$ AND relative RMSE reduction $\ge 15.0\%$ vs both baselines.

### 8.2 Causal Ablation Battery (Ceteris Paribus)
Evaluated on the identical 25 unseen test episodes:
1. **Ablation 1 (Action-Zero):** Same $s_t, h_t$, candidate future actions $u_{t:t+H-1} = \mathbf{0}$.
2. **Ablation 2 (Recurrent-Zero):** Same $s_t, u_{t:t+H-1}$, initial hidden state clamped to $h_t = \mathbf{0}$.
3. **Ablation 3 (Action-Shuffle):** Candidate actions permuted with deterministic seed permutation: $\tilde{u}_{t+k} = u_{t+\pi(k)}$.
4. **Ablation 4 (Channel-Shuffle):** Input observations permuted with deterministic spatial permutation: $\tilde{s} = \mathbf{P}_{\text{perm}} s$.
- **Acceptance Threshold:** Each active ablation must produce $> 30.0\%$ degradation in RMSE relative to the intact model on identical episodes.

---

## 9. Operational Definitions of Outcomes & Stop Rules

### 9.1 The Three Mutually Exclusive Outcomes
1. **PASS:** All pre-registered numerical criteria met across 5/5 unseen test seeds without a single gate failure.
2. **FAIL:** Code executed correctly to completion, but one or more numerical thresholds failed (e.g. $R^2 < 0.65$ or ROC-AUC $< 0.88$).
3. **UNDECIDABLE / INVALID RUN:** An infrastructure or software defect (unhandled exception, file I/O error, simulator physics crash) interrupted execution before completing the protocol.
   - **Protocol for Invalid Runs:** Invalid runs on DEV data must be repaired before touching test data. If an invalid run occurs during `PRIMARY_UNSEEN_TEST`, the entire test battery is invalidated, root cause documented, and a new pre-registered evaluation created. Zero selective re-runs of individual seeds.

### 9.2 Pre-Registered Stop Rule
If any unseen test seed fails:
1. **DO NOT** modify the model architecture to fit that seed.
2. **DO NOT** tune thresholds or change hyperparameters.
3. **DO NOT** discard difficult seeds or redefine evaluation metrics.
4. **RECORD FAILURE:** Document the exact failure mechanism in `CARL_STAGE2_2_FINAL_FORENSIC_AUDIT.md`.

---

## 10. Visualization Rules & Publication Deliverables

### 10.1 Presentation Invariants
All 10 figures must explicitly show:
- Ground Truth, Model Prediction, Residual Error, Time/Horizon, Seed ID, and Partition Name.
- Zero selective axis clipping, zero destructive smoothing, zero cherry-picking.
- Figure 10 (Master Dashboard) must show every individual unseen seed.

### 10.2 Deliverable Package
- **Figures 1–10:** High-resolution PDF/PNG in `evidence/stage2_2/`.
- **Demonstration Video:** `evidence/stage2_2/carl_stage2_2_world_model_demonstration.mp4` (720p 30 FPS). Dual split-screen displaying CARL's mental forward rollout generated first in tensor space, followed by physical trajectory execution for comparison.
- **Raw Telemetry:** `evidence/stage2_2/stage2_2_telemetry.json` with unrounded floating-point metrics and SHA-256 hashes.

---

## 11. Strict 10-Step Sequential Execution Order

```text
STEP 1:  Forensic Consistency Check & Spec Lock (THIS SPECIFICATION)
STEP 2:  Lock Implementation Plan & Artifacts
STEP 3:  Anti-Cheat & AST Isolation Harness Implementation
STEP 4:  Data Harvester: Generate DEV_DEBUG, DEV_TRAIN, and DEV_VAL
STEP 5:  Model & Baselines Implementation in Neural Space
STEP 6:  Training Pipeline & Checkpoint Selection on DEV_VAL
STEP 7:  Hard Model Freeze & Checkpoint Hash Assertion
STEP 8:  Generate & Hash PRIMARY_UNSEEN_TEST Dataset
STEP 9:  Execute Official Primary Unseen Evaluation Exactly Once
STEP 10: Generate Figures, Video, Telemetry, and Final Council Audit
```

---

## 12. Final Pre-Execution Sign-Off

Implementation remains **STRICTLY FROZEN** until user review and approval.
