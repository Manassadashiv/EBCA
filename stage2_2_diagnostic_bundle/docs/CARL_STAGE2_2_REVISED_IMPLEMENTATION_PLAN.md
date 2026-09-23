# CARL STAGE 2.2: REVISED IMPLEMENTATION PLAN
## Phased Diagnostic & Architectural Recovery Protocol (Loophole-Free Locked Specification)
**Author:** Antigravity AI Research Orchestrator  
**Classification:** [TECHNICAL IMPLEMENTATION ROADMAP]  
**Status:** **PRE-IMPLEMENTATION FREEZE (AWAITING USER AUTHORIZATION TO EXECUTE PHASE 1)**  
**Milestone:** Stage 2.2 Redesign Execution  
**Date:** September 5, 2026  
**Target Repository:** `d:/ebca`  

---

## 1. Executive Summary & Epistemic Commitments

Following the forensic post-mortem of Stage 2.2, this implementation plan operationalizes the 6-Condition $\times$ 2-Formulation diagnostic matrix to isolate the true scientific cause of predictive failure. All pre-experimental corrections and isolation guarantees have been strictly integrated:

1. **Zero Privileged GPS Leak Invariant:** Internal spatial states begin strictly at $(0, 0)$ and heading $\theta_0 = 0$ at trajectory birth. CARL is never given MuJoCo `qpos`, true coordinates, or arena boundary equations.
2. **Strict Provenance for Condition F (Environmental Memory):** Inputs to memory consist strictly of past sensory history $S_{1:t}$, past actions $U_{1:t-1}$, and internal dead-reckoned spatial state $[\hat{x}_t, \hat{y}_t, \hat{\theta}_t]$. Never simulator maps, obstacle geometry, or true trajectories.
3. **Parameter-Count Confound Control:** Standard architectures are bounded at $\approx 90\text{K} \pm 5\%$ parameters, and an explicit capacity control model (`M2-B-MATCHED`, $\approx 140\text{K}$ parameters) matches Condition F to separate memory structure from network capacity.
4. **High-Change Evaluation ($\mathcal{D}_{\text{dynamic}}$):** To prevent models from exploiting the $\Delta s \approx 0$ static cheat, all metrics are evaluated and reported separately on high-change transitions ($|\Delta s_{\text{sonar}}| \ge 0.15\,\text{m}$, $|\Delta \omega| \ge 1.0\,\text{rad/s}$, or $|\Delta v| \ge 0.1\,\text{m/s}$).
5. **Absolute Primary-Test Isolation Rule:** `PRIMARY_UNSEEN_TEST` must not exist in accessible form during Phase 1. It must be generated only after the architecture, hyperparameters, metrics, preprocessing, and diagnostic conclusions are frozen (Phase 3). Phase 1 diagnostic training and benchmarking across all 13 configurations is strictly **`DEV_TRAIN` $\to$ `DEV_VAL` only**.
6. **Natural Embodied Experience Only:** Physical trajectories are generated that naturally produce sufficient near-field sonar observations. Sensor readings are never artificially clamped, edited, or fabricated.
7. **Canonical Six Batteries Locked:** Evaluation adheres strictly to the canonical six-battery definition:
   - **Battery 1:** Predictive Fidelity (Multi-Horizon & High-Change $\mathcal{D}_{\text{dynamic}}$)
   - **Battery 2:** Action Causality (Action Zero, Permute, Sign-Invert)
   - **Battery 3:** Spatial Causality (Spatial Phase Scrambling)
   - **Battery 4:** Spatial Disambiguation (Identical Local Observations $\to$ Distinct Arenic Contexts)
   - **Battery 5:** Counterfactual Branching (Branch Divergence under Divergent Motor Commands)
   - **Battery 6:** Collision Anticipation (Floor-Contact Corrected Hazard Detection ROC-AUC)

---

## 2. Three-Phase Developmental Phasing Strategy

To prevent premature commitments to large architectures or speculative fixes, Stage 2.2 development is split into three strictly sequential phases:

```text
  ┌───────────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 1: STAGE 2.2-DIAG (Diagnostic Isolation & Dataset Redesign)                 │
  │ • Harvest DEV_TRAIN and DEV_VAL only (PRIMARY_UNSEEN_TEST does not exist on disk) │
  │ • Extract high-change partition D_dynamic (|Δs| >= 0.15m) on DEV data             │
  │ • Train 13 model configurations strictly DEV_TRAIN -> DEV_VAL                     │
  │ • Benchmark direct-state vs residual-delta on DEV_VAL (D_all and D_dynamic)       │
  │ • Execute the Canonical Six Batteries on DEV_VAL only                             │
  │ ➔ OBJECTIVE: Prove what representation & formulation genuinely predict futures    │
  └─────────────────────────────────────────┬─────────────────────────────────────────┘
                                            ▼
  ┌───────────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 2: STAGE 2.2-R1 (Minimal Architecture Lock)                                 │
  │ • Select winning representation based on Phase 1 falsification logic              │
  │ • Freeze architecture, hyperparameters, metrics, and preprocessing                │
  │ • Run independent council audit on architectural lock                             │
  └─────────────────────────────────────────┬─────────────────────────────────────────┘
                                            ▼
  ┌───────────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 3: STAGE 2.2-R2 (Authoritative Training & One-Shot Evaluation)              │
  │ • Train frozen model on DEV_TRAIN                                                 │
  │ • Generate PRIMARY_UNSEEN_TEST (Seeds 303, 404, 505, 606, 707) POST-FREEZE ONLY   │
  │ • Run Canonical Six Batteries strictly one-shot on unseen test set                │
  │ • Publish scorecard, 300 DPI figures, and video package                          │
  └───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Dataset Redesign & Saturation Audit Protocol

### 3.1 Confound Identification in Prior Dataset
In the previous dataset (`spatial_dev_train.npz` and `spatial_unseen_test.npz`):
1. **High Saturated Fraction:** When CARL wandered in open space, $> 65\%$ of sonar readings were pinned at maximum range $5.0\,\text{m}$.
2. **Stationary / Low-Delta Fraction:** In straight-line driving at steady state, sensory readings changed by $< 1.5\%$ per $30\,\text{ms}$ tick, allowing models to cheat via static persistence ($\Delta s \approx 0$).
3. **Absence of Near-Field Interactions:** Trajectories lacked sustained wall-following, tight cornering, and rapid motor reversals.

### 3.2 Revised Data Harvesting Protocol (`brain/carl_stage2_2_diagnostic_collector.py`)
The new data generation engine guarantees rich dynamic variance through embodied interaction without leaking privileged world coordinates:
- **Zero Privileged GPS Leak Invariant:** At the start of every episode, CARL's internal dead reckoning and CANN grid phase are initialized strictly to origin $(0, 0)$ with heading $\theta_0 = 0$. The simulator's true world position `qpos[0:2]` is **NEVER** provided to CARL's neural network, memory, or spatial integrator. Allocentric map coordinates can only be discovered via sensory-spatial integration over time.
- **Natural Behavioral Regimes (Near-Field Sonar Observation Guarantees):**
  - **Regime 1: Wall Following & Perpendicular Approach:** Generate physical trajectories that naturally produce sufficient near-field sonar observations in the $[0.3, 3.5]\,\text{m}$ range.
  - **Regime 2: High-Angular Turns & Spin Maneuvers:** Generate physical rotational maneuvers that naturally produce high gyro yaw rates $[-15, +15]\,\text{rad/s}$ and dynamic sweep sonar changes.
  - **Regime 3: Burst-Brake-Reverse Sequences:** Generate natural acceleration/deceleration sequences that exercise rapid positive and negative wheel proprioception.
  - **Regime 4: Friction Transitions:** Traverse glaze ice patches ($\mu = 0.005$) to dry arena ($\mu = 1.0$) under natural slip.
- **Strict Prohibition on Synthetic Sensor Modification:** Under no circumstances are sensor returns artificially clamped, synthetic values injected, or noise/range artificially modified. All observations are strictly natural, unedited physical interactions from the MuJoCo simulation environment.
- **Stratified Partitioning & Absolute Unseen Test Isolation:**
  - `DEV_TRAIN`: 60 episodes across seeds `[42, 101, 202]` (400 ticks/ep = 24,000 timesteps).
  - `DEV_VAL`: 20 episodes across 4 independent development seeds `[210, 220, 230, 240]` (5 episodes/seed, 400 ticks/ep = 8,000 timesteps), ensuring multi-environment validation independence.
  - **Absolute Primary-Test Isolation Rule:** `PRIMARY_UNSEEN_TEST` must not exist in accessible form during Phase 1. It must be generated only after the architecture, hyperparameters, metrics, preprocessing, and diagnostic conclusions are frozen (Phase 3). During Phase 1 (`STAGE 2.2-DIAG`), the data collector will generate and store **only** `DEV_TRAIN` and `DEV_VAL`. Unseen test seeds `[303, 404, 505, 606, 707]` will not be run, inspected, or sampled, and no unseen test dataset will exist on disk.
- **High-Change Partition Extraction ($\mathcal{D}_{\text{dynamic}}$):**
  - `DEV_VAL` will be partitioned into $\mathcal{D}_{\text{all}}$ and $\mathcal{D}_{\text{dynamic}}$, where $\mathcal{D}_{\text{dynamic}}$ selects timesteps satisfying:
    $$\frac{1}{15}\sum_{i=1}^{15} |s_{t+1}^i - s_t^i| \ge 0.15\,\text{m} \quad \lor \quad |\omega_{t+1} - \omega_t| \ge 1.0\,\text{rad/s} \quad \lor \quad |v_{t+1} - v_t| \ge 0.10\,\text{m/s}$$
- **Preregistered Hash Freeze:** Record SHA-256 hashes of `DEV_TRAIN.npz` and `DEV_VAL.npz` prior to training.

---

## 4. Software Architecture & Implementation Components

### 4.1 Component Directory Structure
```text
d:/ebca/
├── brain/
│   ├── carl_stage2_2_diagnostic_collector.py   # Rich contingency dataset harvester (DEV only)
│   ├── carl_stage2_2_world_model_suite.py      # Abstract modular forward model suite (13 models)
│   ├── carl_stage2_2_memory_module.py          # Learned spatial-attentive memory (Cond F)
│   ├── test_stage2_2_diagnostic_runner.py      # Canonical Six Battery benchmark engine (DEV_VAL)
│   └── carl_stage2_2_diagnostic_visualizer.py  # Publication figure generator (300 DPI)
├── tests/
│   ├── test_stage2_2_anti_cheat_isolation.py   # AST static analysis & sandbox test
│   └── test_stage2_2_fixed_oracle.py           # Ground-contact subtracted collision test
└── evidence/stage2_2_diag/                     # Output directory for scorecards & plots
```

### 4.2 Modular Forward Model Design (`carl_stage2_2_world_model_suite.py`)
All models inherit from an abstract base class with standardized interfaces for direct and residual prediction:
```python
class BasePredictiveWorldModel(nn.Module):
    def forward(self, x_t: torch.Tensor, h_t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Direct-state prediction: returns (s_next_pred, h_next)"""
        raise NotImplementedError

    def predict_delta(self, x_t: torch.Tensor, h_t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Residual-delta prediction: returns (delta_s_pred, h_next)"""
        raise NotImplementedError
```

### 4.3 Model Registry & Parameter Capacity Bounds (13 Models)

| Model ID | Input Representation | Prediction Target | Parameter Budget | Purpose |
| :--- | :--- | :--- | :---: | :--- |
| **M1-A-DIR** | Sensory History $S_{t-k:t}$ (25D) | Direct $\hat{s}_{t+1}$ | $88\text{K} \pm 2\text{K}$ | Sensory-only baseline |
| **M1-A-RES** | Sensory History $S_{t-k:t}$ (25D) | Residual $\Delta \hat{s}_t$ | $88\text{K} \pm 2\text{K}$ | Sensory-only residual baseline |
| **M2-B-DIR** | $S + U$ (31D) | Direct $\hat{s}_{t+1}$ | $90\text{K} \pm 2\text{K}$ | Old Stage 2.2 replication (Prior: FAILED) |
| **M2-B-RES** | $S + U$ (31D) | Residual $\Delta \hat{s}_t$ | $90\text{K} \pm 2\text{K}$ | **Core Test 1:** Does residual restore action causality? |
| **M2-B-MATCHED** | $S + U$ (31D, widened hidden) | Residual $\Delta \hat{s}_t$ | $140\text{K} \pm 5\text{K}$ | **Capacity Control:** Matches Condition F parameter count |
| **M3-C-DIR** | $S + U + \mathbf{v}_{\text{HD}}$ (33D) | Direct $\hat{s}_{t+1}$ | $91\text{K} \pm 2\text{K}$ | Direct HD pose baseline |
| **M3-C-RES** | $S + U + \mathbf{v}_{\text{HD}}$ (33D) | Residual $\Delta \hat{s}_t$ | $91\text{K} \pm 2\text{K}$ | Residual HD pose evaluation |
| **M4-D-DIR** | $S + U + \mathbf{G}_{\text{grid}}$ (33D) | Direct $\hat{s}_{t+1}$ | $91\text{K} \pm 2\text{K}$ | Direct grid translation baseline |
| **M4-D-RES** | $S + U + \mathbf{G}_{\text{grid}}$ (33D) | Residual $\Delta \hat{s}_t$ | $91\text{K} \pm 2\text{K}$ | Residual grid translation evaluation |
| **M5-E-DIR** | $S + U + \mathbf{v}_{\text{HD}} + \mathbf{G}_{\text{grid}}$ (35D) | Direct $\hat{s}_{t+1}$ | $92\text{K} \pm 2\text{K}$ | Full pose direct baseline (Prior: FAILED) |
| **M5-E-RES** | $S + U + \mathbf{v}_{\text{HD}} + \mathbf{G}_{\text{grid}}$ (35D) | Residual $\Delta \hat{s}_t$ | $92\text{K} \pm 2\text{K}$ | **Core Test 2:** Full pose with residual formulation |
| **M6-F-DIR** | $S + U + \text{Pose} + \mathbf{M}_{\text{env}}$ | Direct $\hat{s}_{t+1}$ | $140\text{K} \pm 5\text{K}$ | Direct model with learned environmental memory |
| **M6-F-RES** | $S + U + \text{Pose} + \mathbf{M}_{\text{env}}$ | Residual $\Delta \hat{s}_t$ | $140\text{K} \pm 5\text{K}$ | **Core Test 3:** Grounded world model + learned memory |

### 4.4 Condition F: Learned Environmental Memory Provenance & Architecture
To ensure scientific validity, Condition F's memory is constructed strictly as follows:
- **Strict Data Provenance:**
  ```text
  past sensory history S_{1:t}
          +
  past actions U_{1:t-1}
          +
  dead-reckoned pose [x_hat_t, y_hat_t, theta_hat_t] (from origin 0,0)
          ↓
  learned key-value spatial memory M in R^{K x d_m}
  ```
- **Prohibited Data Sources:** MuJoCo `model`, `data`, `geom_xpos`, true obstacle locations, `qpos`, `qvel`, `mj_ray`, or evaluator state. Zero privileged geometry is accessible.
- **Memory Addressing Mechanism:**
  - Memory buffer $\mathbf{M} \in \mathbb{R}^{K \times d_m}$ ($K=64$ slots, $d_m=64$).
  - Write head: $k_{\text{write}} = W_k [\hat{x}_t, \hat{y}_t, \hat{\theta}_t]$, $v_{\text{write}} = W_v [S_t, U_t]$. Soft-address write into least-used or spatially nearest slot.
  - Read head: $q_{\text{read}} = W_q [\hat{x}_t, \hat{y}_t, \hat{\theta}_t]$. Attention weights $\alpha_i = \text{softmax}(q \cdot k_i / \sqrt{d_m})$. Retrieved context $c_t = \sum_i \alpha_i v_i \in \mathbb{R}^{64}$.
  - The retrieved context $c_t$ is concatenated to the forward model's hidden representation.

---

## 5. Phase 1 Diagnostic Verification & Execution Protocol

### Step 1: Pre-Execution Harness Verification
1. Run AST Static Analysis (`tests/test_stage2_2_anti_cheat_isolation.py`):
   - Scans all files in `brain/` to verify zero imports of `mujoco` or access to `qpos`/`qvel`.
2. Run Ground-Contact Subtracted Collision Oracle Test (`tests/test_stage2_2_fixed_oracle.py`):
   - Verifies that normal floor rolling produces strictly zero collision flags.
   - Verifies that wall/pillar impacts produce true positive collision flags.

### Step 2: Diagnostic Dataset Generation & Saturation Audit (DEV Partitions Only)
1. Run `brain/carl_stage2_2_diagnostic_collector.py` to harvest `DEV_TRAIN` (seeds 42, 101, 202; 60 episodes) and `DEV_VAL` (seeds 210, 220, 230, 240; 20 episodes across 4 seeds). `PRIMARY_UNSEEN_TEST` is not generated.
2. Generate and verify dataset saturation report on `DEV_VAL`:
   - Saturated sonar fraction ($s = 5.0\,\text{m}$): Must be $\le 30\%$ (down from $>65\%$).
   - High-change transition fraction ($|\Delta s| \ge 0.15\,\text{m}$): Must be $\ge 25\%$.
   - Non-zero action fraction: $100\%$.
3. Extract $\mathcal{D}_{\text{dynamic}}$ from `DEV_VAL` and verify SHA-256 hashes of `DEV_TRAIN.npz` and `DEV_VAL.npz`.

### Step 3: Diagnostic Benchmark Execution (Strictly DEV_TRAIN $\to$ DEV_VAL)
1. Train all 13 models on `DEV_TRAIN` for 25 epochs using identical training hyperparameters (AdamW, lr=$1\times 10^{-3}$, cosine decay, batch size 32, BPTT length 30).
2. Evaluate all 13 models on `DEV_VAL` across the **Canonical Six Batteries**:
   - **Battery 1 (Predictive Fidelity):** Multi-horizon $R^2$ ($H \in \{1, 5, 10, 15, 30\}$) reported on both $\mathcal{D}_{\text{all}}$ and $\mathcal{D}_{\text{dynamic}}$.
   - **Battery 2 (Action Causality):** Action Zeroing ($\Delta \mathcal{E}_{u=0} \ge +25\%$), Action Permutation ($\ge +20\%$), Action Sign Inversion ($\ge +30\%$).
   - **Battery 3 (Spatial Causality):** Spatial phase scrambling ($\ge +20\%$ error surge on sonar).
   - **Battery 4 (Spatial Disambiguation):** Divergence between identical local sonars in distinct arenic contexts ($\|\hat{s}_{\text{loc1}} - \hat{s}_{\text{loc2}}\|_2 \ge 1.5\,\text{m}$).
   - **Battery 5 (Counterfactual Branching):** Divergence across 3 candidate action sequences from identical state ($\ge 1.0\,\text{m}$).
   - **Battery 6 (Collision Anticipation):** Prediction of upcoming contact event at $H \in [1, 10]$ steps ($\text{ROC-AUC} \ge 0.85$).
3. Compare `M6-F-RES` against `M2-B-MATCHED` to explicitly test whether memory benefits exceed parameter-capacity benefits.
4. Output comprehensive scorecard `evidence/stage2_2_diag/diagnostic_scorecard.json` and publication figures.

### Step 4: Stop Condition & Human Review Gate
- **STOP.** Under no circumstances will Phase 2 or 3 be executed, nor will unseen test data (`seeds [303, 404, 505, 606, 707]`) exist or be touched.
- Present raw, unrounded diagnostic findings and decision-tree outcomes to the user for explicit review and architectural authorization.
