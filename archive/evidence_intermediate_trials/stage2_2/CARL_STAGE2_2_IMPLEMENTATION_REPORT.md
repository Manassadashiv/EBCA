# CARL STAGE 2.2 IMPLEMENTATION REPORT
**Classification:** [SCIENTIFIC BENCHMARK & FORENSIC ADVERSARIAL AUDIT]  
**Milestone:** Stage 2.2 Action-Conditioned Recurrent Sensory Forward Model  
**Overall Certification Verdict:** **FAIL (Honest Falsification Battery)**  
**Date:** 2026-09-05  

---

## 1. Executive Summary & Forensic Verdict

CARL Stage 2.2 transitions the organism from passive spatial representation (Stage 2.1 continuous attractor head-direction and spatial self-model) to **active generative sensory forward modeling**—the ability to simulate in neural tensor space the sensory consequences of its actions before executing them.

Under the pre-registered protocol, the action-conditioned recurrent world model was trained strictly on `DEV_TRAIN` (seeds `[42, 101, 202]`), selected on `DEV_VAL`, and **permanently frozen**. The primary unseen test set (`PRIMARY_UNSEEN_TEST`, seeds `[303, 404, 505, 606, 707]`) was generated **strictly post-freeze**, and evaluated without post-hoc threshold tuning or parameter modification.

### Master Falsification Scorecard

| Evaluation Gate | Pre-Registered Criterion | Empirical Result | Status |
| :--- | :--- | :--- | :---: |
| **Gate 2.2A: Gyro Yaw Rate ($H=10$)** | $R^2 \ge 0.70$ | $R^2 = 0.3984$ | **FAIL** |
| **Gate 2.2A: Sonar Dynamic ($s < 4.5\,\text{m}$)** | $R^2 \ge 0.60$ | $R^2 = 0.3756$ | **FAIL** |
| **Gate 2.2A: Proprioception ($H=10$)** | $R^2 \ge 0.80$ | $R^2 = 0.9026$ | **PASS** |
| **Gate 2.2A: Battery Drain ($H=10$)** | $\text{MAE} \le 0.05$ | $\text{MAE} = 0.0101$ | **PASS** |
| **Gate 2.2A: Composite Active 24-D** | $R^2 \ge 0.65$ | $R^2 = 0.3197$ | **FAIL** |
| **Gate 2.2B: Collision ROC-AUC** | $\text{ROC-AUC} \ge 0.88$ | $\text{ROC-AUC} = 0.5000$ | **FAIL** *(Oracle Defect)* |
| **Gate 2.2C: Glaze Ice Invariance ($\mu=0.005$)** | $R^2_{\text{ice}} \ge 0.60$ | $R^2_{\text{ice}} = 0.8732$ | **PASS** |
| **Gate 2.2D: Long-Horizon Stability ($H=30$)** | Slope $\beta \le 0.06$, Ratio $\le 3.5$ | $\beta = 0.00480$, Ratio $= 1.105$ | **PASS** |
| **Baseline vs Naive Persistence ($N=25$)** | $p < 0.01$, $d \ge 0.5$, $\Delta \text{RMSE} \ge 15\%$ | $p = 6.03 \times 10^{-6}$, $d = 2.05$, $-34.9\%$ | **PASS** |
| **Baseline vs Linear Readout ($N=25$)** | $p < 0.01$, $d \ge 0.5$, $\Delta \text{RMSE} \ge 15\%$ | $p = 0.00922$, $d = 0.63$, $-6.5\%$ | **FAIL** *(Relative $\Delta$)* |
| **Causal Ablation: Action Zero ($u=0$)** | Error Degradation $\ge 30.0\%$ | Degradation $= +3.62\%$ | **FAIL** |
| **Causal Ablation: Recurrent Zero ($h=0$)** | Error Degradation $\ge 30.0\%$ | Degradation $= +7.73\%$ | **FAIL** |
| **Causal Ablation: Action Permutation** | Error Degradation $\ge 30.0\%$ | Degradation $= +0.83\%$ | **FAIL** |
| **Causal Ablation: Channel Permutation** | Error Degradation $\ge 30.0\%$ | Degradation $= +22.49\%$ | **FAIL** |
| **OVERALL STAGE 2.2 VERDICT** | **All 6 Batteries Passing** | **2 Passed / 4 Failed** | **FAIL** |

---

## 2. Cryptographic Provenance & Call-Graph Air-Gap Audit

To eliminate simulation leakage, the system enforced two immutable constraints before any evaluation:

1. **Static AST Analysis & Subprocess Poisoning (`tests/test_stage2_2_anti_cheat_isolation.py`):**
   - Recursive AST analysis proved 0 occurrences of `mujoco`, `CarlStage1HAL`, `mj_ray`, `data.qpos`, `data.qvel`, or `data.contact`.
   - In an isolated subprocess where `sys.modules['mujoco'] = None`, the model successfully performed a 30-step forward mental rollout from raw tensor priors without error.
2. **Cryptographic Checkpoint Locking:**
   - **Frozen Model Weights:** `checkpoints/carl_stage2_2_world_model_frozen.pt`  
     `SHA-256: 47f8556c3485e8263c1f41ddee007563c499c3f09020816f03845c9a5275ec14`
   - **Primary Unseen Test Dataset:** `evidence/stage2_2/datasets/unseen_test.npz`  
     `SHA-256: 0952ca999991a0e44202df50e5ede07b48db14ada3347f63b794330e192c26b0`
   - **Normalization Statistics:** `checkpoints/stage2_2_norm_stats.npz`  
     `SHA-256: 0b435ff2008e70a316b1aa103aa2fc49d115e8d6f51be0e6f21baad390757d42`
   - Test dataset SHA-256 is absent from all training manifests and was generated strictly post-freeze.

---

## 3. Detailed Battery Results

### 3.1 Gate 2.2A: Multi-Step Prediction Fidelity

Evaluated across $N=25$ unseen episodes (Seeds 303, 404, 505, 606, 707) at horizons $H \in \{1, 5, 10, 15, 30\}$ ($30\,\text{ms}$ to $900\,\text{ms}$):

```
Horizon H= 1 ( 30ms) | Gyro R2: 0.3959 | Sonar Dyn R2: 0.6808 | Proprio R2: 0.9666 | Comp R2: 0.2588
Horizon H= 5 (150ms) | Gyro R2: 0.4142 | Sonar Dyn R2: 0.5348 | Proprio R2: 0.9366 | Comp R2: 0.3299
Horizon H=10 (300ms) | Gyro R2: 0.3984 | Sonar Dyn R2: 0.3756 | Proprio R2: 0.9026 | Comp R2: 0.3197
Horizon H=15 (450ms) | Gyro R2: 0.3648 | Sonar Dyn R2: 0.2451 | Proprio R2: 0.8458 | Comp R2: 0.3006
Horizon H=30 (900ms) | Gyro R2: 0.2925 | Sonar Dyn R2:-0.1048 | Proprio R2: 0.6304 | Comp R2: 0.2427
```

- **Proprioception ($R^2 = 0.903$):** Outstanding fidelity. Wheel speeds and joint angles track accurately.
- **Battery ($R^2 = 0.999$, $\text{MAE} = 0.010$):** Perfectly tracks monotonic depletion.
- **Gyro ($R^2 = 0.398$) & Dynamic Sonar ($R^2 = 0.376$):** Failed pre-registered targets ($0.70$ and $0.60$). At $H=1$, dynamic sonar hits $R^2 = 0.681$, but decays across autoregressive rollout.

### 3.2 Gate 2.2B: Counterfactual Collision Anticipation (250 Trials)

- **Empirical Metric:** $\text{ROC-AUC} = 0.5000$, $\text{Recall} = 0.0480$, $\text{Precision} = 1.0000$, $\text{FPR} = 0.0000$.
- **Forensic Diagnosis of Test-Harness Defect:**
  In `brain/test_stage2_2_world_model_suite.py` line 306:
  ```python
  contacts = hal.get_carl_contact_info()
  if contacts["carl_contacts"] > 0:
      collided = True
  ```
  `CarlStage1HAL.get_carl_contact_info()` counts external contacts, which includes tire-floor contact (`floor_contacts`). Because the robot's wheels touch the ground every step, MuJoCo registered $250 / 250$ trials as "in contact" at $t=0$. With 0 true negatives in the physical label vector, ROC-AUC is mathematically degenerate ($0.5000$).

### 3.3 Gate 2.2C: Traction Grounding Invariance (Glaze Ice $\mu=0.005$)

- **Empirical Metric:** Mean Sonar $R^2_{\text{ice}} = 0.8732$ (Passed $\ge 0.60$ threshold across all 5 seeds).
- **Physical Meaning:** When conditioned on the 5-tick slip observation history, the world model correctly decouples wheel actuation from forward translation, predicting stationary wall distances despite active wheel drive commands.

### 3.4 Gate 2.2D: Long-Horizon Autoregressive Stability ($H=30$)

- **Empirical Metric:** Fitted slope $\beta = 0.00480$ (Passed $\le 0.060$ threshold).
- **Ratio $\text{RMSE}_{30} / \text{RMSE}_1$:** $1.105$ (Passed $\le 3.50$ threshold).
- Zero numerical overflow, zero NaNs, zero physical boundary violations across 12,000 autoregressive steps.

### 3.5 Baselines and Causal Ablations

- **vs Persistence Baseline:** $34.90\%$ error reduction ($p = 6.03 \times 10^{-6}$, Cohen's $d = 2.05$). Clear rejection of static persistence.
- **vs Linear Action Baseline:** $6.50\%$ error reduction ($p = 0.00922$, Cohen's $d = 0.630$). Statistically significant superiority, but missed the aggressive $15\%$ relative margin pre-registered.
- **Causal Ablations:** Action-zero degradation was only $+3.62\%$ and recurrent-zero degradation was $+7.73\%$, failing the $\ge 30\%$ gate.

---

## 4. Root-Cause Forensic Autopsy

Why did the world model pass stability, ice invariance, and proprioception, but fail the causal ablation and gyro/sonar dynamic gates?

### The "Absolute State Copy" Minimum in Direct Autoregressive Models
In continuous-time physical systems ($dt = 30\,\text{ms}$), state $s_{t+1}$ is very close to $s_t$. When trained to output the absolute normalized vector $\hat{s}_{t+1}$ directly:
$$\hat{s}_{t+1} = \text{Decoder}(\text{GRU}([s_t; \mathbf{v}_t; u_t]))$$
the gradient path overwhelmingly favors learning an **identity pass-through** ($\hat{s}_{t+1} \approx s_t$).
Because the model relies heavily on copying $s_t$:
1. When actions are zeroed ($u_t = 0$), the copied state is still close to true state, so error only rises $+3.62\%$.
2. When recurrent state is zeroed ($h_t = 0$), the instantaneous sensory feedforward component still passes through, so error only rises $+7.73\%$.
3. When predicting high-frequency dynamic signals like gyro yaw rate during sudden steering transitions, the identity bias introduces a phase lag, limiting $R^2$ to $\sim 0.40$.

**The Canonical Architectural Fix (Pre-Registered for Next Stage / Refinement):**
Formulate the decoder as a **residual delta generator**:
$$\hat{s}_{t+1} = s_t + \Delta s_{\boldsymbol{\theta}}(h_{t+1})$$
This forces the GRU and decoder to model strictly the *change* caused by motor action and inertia, making action inputs causally essential ($\ge 50\%$ degradation when $u=0$).

---

## 5. Visual Evidence & Artifacts

All publication figures have been rendered at 300 DPI and mirrored to the artifact directory:

- [Figure 1: Physical vs Predicted Sensory Trajectory](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure1_physical_vs_predicted_trajectory.png)
- [Figure 2: Prediction Error Growth vs Horizon H=1..30](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure2_error_growth_vs_horizon.png)
- [Figure 3: Multi-Horizon Fidelity Degradation across Modalities](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure3_multi_horizon_degradation.png)
- [Figure 4: Counterfactual Collision Anticipation Benchmark](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure4_collision_anticipation.png)
- [Figure 5: Glaze Ice Grounding Invariance across Seeds](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure5_glaze_ice_invariance.png)
- [Figure 6: Long-Horizon Autoregressive Multi-Sensor Rollout](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure6_autoregressive_rollout.png)
- [Figure 7: Mandatory Baseline Comparison on Unseen Episodes](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure7_baseline_comparison.png)
- [Figure 8: Causal Ablation Degradation Matrix](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure8_ablation_comparison.png)
- [Figure 9: Cross-Seed Generalization Consistency](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure9_per_seed_generalization.png)
- [Figure 10: Stage 2.2 Master Scientific Dashboard](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure10_master_dashboard.png)

### Video Demonstration
- [carl_stage2_2_world_model_demonstration.mp4](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/carl_stage2_2_world_model_demonstration.mp4) (720p 30 FPS, Dual Split-Screen: MuJoCo Physical Reality vs Pure Neural Imagination).
