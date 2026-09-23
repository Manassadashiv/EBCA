# CARL STAGE 2.2: IMPLEMENTATION PLAN
## ACTION-CONDITIONED RECURRENT SENSORY SYNTHESIS & EMBODIED FORWARD WORLD MODEL
**Author:** Antigravity AI Orchestrator  
**Classification:** [IMMUTABLE PRE-EXPERIMENTAL IMPLEMENTATION PLAN]  
**Status:** **FROZEN AWAITING USER APPROVAL (ZERO IMPLEMENTATION COMMENCED)**  
**Milestone:** Stage 2.2 — Predictive World Modeling & Counterfactual Rollout  
**Date:** September 5, 2026  
**Governing Specification:** [`CARL_STAGE2_2_PREDICTIVE_WORLD_MODEL_SPECIFICATION.md`](file:///d:/ebca/CARL_STAGE2_2_PREDICTIVE_WORLD_MODEL_SPECIFICATION.md)  
**Governing Forensic Audit:** [`CARL_STAGE2_2_PREIMPLEMENTATION_FORENSIC_AUDIT.md`](file:///d:/ebca/CARL_STAGE2_2_PREIMPLEMENTATION_FORENSIC_AUDIT.md)  

---

## 1. Execution Order & Gated Protocol

Implementation follows a strict, non-negotiable **10-step sequential workflow**. No step may proceed until the preceding step is verified:

```text
STEP 1:  Forensic Consistency Pass & Spec Lock           [COMPLETE]
   │
   ▼
STEP 2:  Lock Implementation Plan & Artifacts             [CURRENT STEP]
   │
   ▼
STEP 3:  Anti-Cheat & Full Call-Graph Isolation Harness   [tests/test_stage2_2_anti_cheat_isolation.py]
   │
   ▼
STEP 4:  4-Partition Dataset Harvester (DEV Partitions)   [brain/carl_stage2_2_data_collector.py]
   │
   ▼
STEP 5:  Action-Conditioned Recurrent Model & Baselines   [brain/carl_stage2_2_world_model.py]
   │
   ▼
STEP 6:  Training Pipeline & Checkpoint Selection on VAL  [brain/train_stage2_2_world_model.py]
   │
   ▼
STEP 7:  Hard Model Freeze & Checkpoint Hash Assertion    [checkpoints/carl_stage2_2_world_model_frozen.pt]
   │
   ▼
STEP 8:  Generate & Hash PRIMARY_UNSEEN_TEST Dataset      [evidence/stage2_2/datasets/]
   │
   ▼
STEP 9:  Master Adversarial Evaluation (Strictly Once)    [brain/test_stage2_2_world_model_suite.py]
   │
   ▼
STEP 10: Publication Figures, Video & Final Council Audit [evidence/stage2_2/ & Audit Report]
```

---

## 2. Detailed Step-by-Step Work Breakdown

### Step 3: Anti-Cheat & Full Call-Graph Isolation Harness
- **File:** `tests/test_stage2_2_anti_cheat_isolation.py`
- **Objective:** Programmatically prove that mental rollouts have zero connection to MuJoCo simulator internals.
- **Verification Logic:**
  1. **Full Call-Graph AST Inspection:** Recursively traces all local project modules reachable from the rollout function. Asserts 0 occurrences of `import mujoco`, `from mujoco import ...`, `CarlStage1HAL`, `mj_ray`, `data.qpos`, `data.qvel`, `data.contact`.
  2. **Subprocess MuJoCo Poisoning Sandbox:** Executes `rollout_mental_trajectory` in a clean Python subprocess where `sys.modules['mujoco'] = None`. If MuJoCo is accessed or required, the test triggers an immediate **HARD FAIL**.

### Step 4: 4-Partition Dataset Harvester (DEV Partitions First)
- **File:** `brain/carl_stage2_2_data_collector.py`
- **Objective:** Collect rich, diverse sensorimotor trajectories across isolated partitions.
- **Specifications:**
  - `DEV_DEBUG`: 5 short episodes (Seed 42) for quick pipeline testing and shape checks.
  - `DEV_TRAIN`: 60 episodes (Seeds 42, 101, 202; 20 each) with unconstrained motor babbling.
  - `DEV_VAL`: 20 independent episodes (Seeds 42, 101, 202) with novel action sequences for checkpoint selection.
  - `PRIMARY_UNSEEN_TEST`: **DO NOT GENERATE YET.** Generated and hashed only at Step 8 post-freeze.
  - Calculates normalization statistics $(\boldsymbol{\mu}_{\text{dev}}, \boldsymbol{\sigma}_{\text{dev}})$ strictly on `DEV_TRAIN` and saves to `checkpoints/stage2_2_norm_stats.npz`.
  - Computes channel variance masks ($\sigma_j^2 \ge 10^{-4}$) to pre-register active vs quiescent channels.

### Step 5: Action-Conditioned Recurrent World Model & Baselines
- **File:** `brain/carl_stage2_2_world_model.py`
- **Objective:** Implement the core forward transition and observation synthesis engine.
- **Key Modules:**
  1. `CarlStage2WorldModel(nn.Module)`:
     - Input: 25 normalized sensors $\tilde{s}_t$ + 2-D HD heading $[\cos\hat{\theta}_{\text{HD}}, \sin\hat{\theta}_{\text{HD}}]$ + 6 motor actions $u_t = 33\,\text{dims}$.
     - Recurrent core: GRU ($d_{\text{in}} = 33, d_h = 128$).
     - Sensory decoder: MLP ($128 \to 128 \to 25$ with SiLU non-linearities and physical bounding clamps).
     - `rollout_mental_trajectory(h_0, u_sequence, H)`: Pure autoregressive rollout feeding $\hat{s}_{t+k} \to \tilde{s}_k$ with internal gyro heading updating and zero teacher forcing.
  2. `NaivePersistencePredictor`: $\hat{s}_{t+k} = s_t$.
  3. `LinearActionPredictor`: Ridge regression baseline $\hat{s}_{t+k} = \mathbf{W}_s s_t + \mathbf{W}_u u_{t+k-1} + \mathbf{b}$.
  4. Integration mount: Connects cleanly to `CarlStage2BIntegratedBrain` as Layer 6.

### Step 6: Training Pipeline & Checkpoint Selection on DEV_VAL
- **File:** `brain/train_stage2_2_world_model.py`
- **Objective:** Self-supervised optimization with early stopping on `DEV_VAL`.
- **Protocol:**
  - Multi-horizon autoregressive sequence loss ($H=1$ to $H=10$) with scheduled sampling.
  - Modality-weighted normalized MSE loss.
  - Early stopping strictly on `DEV_VAL` autoregressive loss ($H=10$) with patience of 15 epochs.
  - Saves best checkpoint to `checkpoints/carl_stage2_2_world_model_frozen.pt`.
  - Emits `checkpoints/stage2_2_training_receipt.json` containing epoch loss curves and SHA-256 checkpoint hash.

### Step 7: Hard Model Freeze & Parameter Hash Invariant Check
- **Verification:**
  - Parameters set to `requires_grad = False`.
  - Optimizer deleted from memory.
  - All online learning and adaptation hooks disabled.
  - Pre-evaluation test verifies that parameter SHA-256 hash is invariant before and after test evaluation.

### Step 8: Generate & Hash PRIMARY_UNSEEN_TEST Dataset
- **Protocol:**
  - Generate 25 episodes across Seeds `[303, 404, 505, 606, 707]` (5 episodes per seed).
  - Compute and record SHA-256 hash in `evidence/stage2_2/datasets/unseen_test_manifest.json`.
  - Automated anti-contamination assertion verifies test data was never present in training cache.

### Step 9: Master Adversarial Verification Suite
- **File:** `brain/test_stage2_2_world_model_suite.py`
- **Objective:** Official frozen evaluation on `PRIMARY_UNSEEN_TEST` executed **strictly once**.
- **Batteries Evaluated:**
  1. **Gate 2.2A:** Multi-Step Prediction Fidelity ($H \in [1, 5, 10, 15, 30]$): $R^2 \ge 0.70$ (gyro), $R^2 \ge 0.60$ (sonar dynamic returns $< 4.5\,\text{m}$), $R^2 \ge 0.80$ (proprio), Active 24-D Mean $R^2 \ge 0.65$. Bounded channels evaluated via MAE/RMSE.
  2. **Gate 2.2B:** Counterfactual Collision Anticipation: ROC-AUC $\ge 0.88$, PR-AUC $\ge 0.85$ across 250 randomized obstacle trials (heading offsets up to $\pm 60^\circ$ for oblique angles).
  3. **Gate 2.2C:** Traction / Friction Grounding Invariance: $R^2_{\text{ice}} \ge 0.60$ evaluated on a 25-tick rollout conditioned on a 5-tick observed slip window without receiving friction labels.
  4. **Gate 2.2D:** Long-Horizon Autoregressive Stability ($H=30$): Zero NaNs/Infs, zero range violations, fitted log-linear error growth slope $\beta \le 0.06$.
  5. **Baseline Comparison:** Paired Wilcoxon signed-rank test ($N=25$ episodes) requiring $p < 0.01$, Cohen's $d \ge 0.50$, and relative RMSE reduction $\ge 15.0\%$.
  6. **Causal Ablation Matrix:** Evaluates Action-Zeroed, Recurrent-Zeroed, Action-Shuffled, and Channel-Scrambled controls ($> 30.0\%$ degradation required).
- **Output:** Raw telemetry saved to `evidence/stage2_2/stage2_2_scorecard.json` and `stage2_2_telemetry.json`.

### Step 10: Publication Visualizations, Video & Council Audit
- **Files:** `brain/carl_stage2_2_visualizer.py`, `evidence/stage2_2/`
- **Deliverables:**
  - Figures 1 through 10 (PDF and PNG, 300 DPI).
  - Dual split-screen demonstration video `evidence/stage2_2/carl_stage2_2_world_model_demonstration.mp4` (720p 30 FPS).
  - Final Forensic Audit: `CARL_STAGE2_2_FINAL_FORENSIC_AUDIT.md`.

---

## 3. Pre-Implementation Verification & Stop Rules

- **Zero Tolerance for Leakage:** If any test-time adaptation, simulator query, or data partition leak is discovered during implementation, coding must stop immediately and be documented.
- **Immutable Test Scores:** Primary unseen seeds `[303, 404, 505, 606, 707]` must be run exactly once post-freeze. If any gate fails, the failure must be recorded without re-tuning.
- **Current Execution State:** **FROZEN.** No training, data collection, or test execution will begin until the user explicitly reviews and approves this plan.
