# CARL STAGE 2.2: DIAGNOSTIC EXPERIMENT MATRIX
## 6-Condition x 2-Formulation Controlled Falsification Protocol (Locked Specification)
**Author:** Antigravity AI Research Orchestrator  
**Classification:** [EXPERIMENTAL PROTOCOL & DECISION LOGIC MATRIX]  
**Status:** **PRE-REGISTERED SPECIFICATION MATRIX (NO EXECUTION UNTIL APPROVED)**  
**Milestone:** Stage 2.2-DIAG Diagnostic Framework  
**Date:** September 5, 2026  
**Target Repository:** `d:/ebca`  

---

## 1. The Multi-Dimensional Diagnostic Space

To rigorously isolate why the prior Stage 2.2 model failed, this diagnostic matrix evaluates the full factorial product across **Input Representation**, **Prediction Target Formulation**, **Evaluation Horizons**, and the **Canonical Six Batteries**, while enforcing the user pre-experimental corrections:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   DIAGNOSTIC MATRIX DIMENSIONS                                  │
├────────────────────────────┬────────────────────────────────────────────────────────────────────┤
│ 1. INPUT REPRESENTATIONS   │ 6 Conditions: A (Sensory), B (+Action), C (+HD),                   │
│                            │               D (+Grid), E (+HD+Grid), F (+Environmental Memory)   │
│                            │ + 1 Capacity Control: B-MATCHED (Matched capacity to Cond F)       │
├────────────────────────────┼────────────────────────────────────────────────────────────────────┤
│ 2. TARGET FORMULATIONS     │ 2 Types: Direct State (ŝ_{t+1}) vs Residual Delta (s_t + Δŝ_t)     │
├────────────────────────────┼────────────────────────────────────────────────────────────────────┤
│ 3. EVALUATION PARTITIONS   │ 2 Subsets: All Timesteps (D_all) vs High-Change (D_dynamic)        │
├────────────────────────────┼────────────────────────────────────────────────────────────────────┤
│ 4. PREDICTION HORIZONS     │ 5 Horizons: H = 1 (30ms), 5 (150ms), 10 (300ms), 15, 30 (900ms)    │
├────────────────────────────┼────────────────────────────────────────────────────────────────────┤
│ 5. CANONICAL SIX BATTERIES │ 1: Predictive Fidelity, 2: Action Causality, 3: Spatial Causality, │
│                            │ 4: Spatial Disambiguation, 5: Counterfactual Branching,            │
│                            │ 6: Collision Anticipation                                          │
└────────────────────────────┴────────────────────────────────────────────────────────────────────┘
```

---

## 2. Invariants & Anti-Confound Guarantees

### Invariant 1: Zero Privileged GPS Leak
- CARL's spatial state (dead reckoning and continuous attractor grid phase) must initialize strictly at origin $(0, 0)$ with heading $\theta_0 = 0$ at the start of every episode.
- Spatial state is updated **exclusively** through allowed sensory/motor integration (wheel velocity proprioception, gyro yaw rate, accelerometer).
- The model, memory, and evaluator **never** access MuJoCo `qpos`, `qvel`, true arena boundaries, geometry, or obstacle locations.

### Invariant 2: Strict Provenance of Environmental Memory (Condition F)
- Information available to Condition F's memory module consists **strictly** of:
  $$\text{Input to Memory} = \{S_{1:t}, U_{1:t-1}, [\hat{x}_t, \hat{y}_t, \hat{\theta}_t]\}$$
- Prohibited data sources: MuJoCo model, arena obstacle coordinates, true trajectory coordinates, or evaluator contact state. Memory is learned entirely end-to-end via attention over past experience.

### Invariant 3: Parameter-Count Confound Control
- Standard model conditions (M1-A through M5-E) are bounded to a matched parameter budget: $\approx 90\text{K} \pm 5\%$ parameters.
- Condition F requires additional memory query/key/value parameters ($\approx 140\text{K}$ parameters).
- To prevent attributing pure network capacity gains to memory, an explicit capacity control model **`M2-B-MATCHED`** ($\approx 140\text{K}$ parameters, widened hidden layers, no memory) is included. Condition F is considered an architectural success only if it outperforms both `M5-E-RES` and `M2-B-MATCHED`.

### Invariant 4: High-Change Transition Evaluation ($\mathcal{D}_{\text{dynamic}}$)
- Residual models ($\Delta s$) can achieve deceptively low RMSE by predicting $\Delta s \approx 0$ during static or straight-line intervals.
- Therefore, all metrics are computed and reported separately on:
  1. $\mathcal{D}_{\text{all}}$: All evaluation timesteps.
  2. $\mathcal{D}_{\text{dynamic}}$: High-change transition subset ($|\Delta s_{\text{sonar}}| \ge 0.15\,\text{m}$, $|\Delta \omega| \ge 1.0\,\text{rad/s}$, or $|\Delta v| \ge 0.1\,\text{m/s}$).
- Passing requires dynamic sonar $R^2 \ge 0.60$ specifically on $\mathcal{D}_{\text{dynamic}}$.

### Invariant 5: Natural Embodied Experience Only
- Trajectories are physically generated to naturally produce sufficient near-field sonar observations in the $[0.3, 3.5]\,\text{m}$ range.
- Sensor returns are **never** artificially clamped, scaled, or fabricated. All observations reflect unedited physics interactions in the environment.

### Invariant 6: Absolute Primary-Test Isolation
- `PRIMARY_UNSEEN_TEST` must not exist in accessible form during Phase 1. It must be generated only after the architecture, hyperparameters, metrics, preprocessing, and diagnostic conclusions are frozen (Phase 3).
- Phase 1 diagnostic benchmarking across all 13 model configurations is strictly restricted to **`DEV_TRAIN` $\to$ `DEV_VAL` only**.

### Invariant 7: Multi-Seed Validation Hardening (DEV_VAL)
- To eliminate single-seed bias during architectural discovery, `DEV_VAL` comprises 20 episodes drawn across 4 independent development seeds `[210, 220, 230, 240]` (5 episodes/seed = 8,000 timesteps).
- This ensures that diagnostic rankings and the selection of winning representations reflect general physical principles rather than quirks of a single validation environment.
- Unseen test seeds `[303, 404, 505, 606, 707]` remain completely ungenerated and untouched during Phase 1.

---

## 3. Comprehensive Model Condition Matrix (13 Configurations)

All models are trained strictly on `DEV_TRAIN` (seeds `[42, 101, 202]`; 25 epochs, AdamW, batch size 32, BPTT 30) and evaluated strictly on `DEV_VAL` (seeds `[210, 220, 230, 240]`):

| Model ID | Input Features | Target Output | Input Dims | Parameters | Core Scientific Hypothesis Tested |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **M1-A-DIR** | Sensory History $S_{t-k:t}$ | Direct $\hat{s}_{t+1}$ | $25 \times (k+1)$ | $\approx 88\text{K}$ | Baseline: Can sensory history alone predict future without actions? |
| **M1-A-RES** | Sensory History $S_{t-k:t}$ | Residual $\Delta \hat{s}_t$ | $25 \times (k+1)$ | $\approx 88\text{K}$ | Does residual formulation prevent static persistence without actions? |
| **M2-B-DIR** | $S + U$ | Direct $\hat{s}_{t+1}$ | $31 \times (k+1)$ | $\approx 90\text{K}$ | Old Stage 2.2: Does adding actions improve direct prediction? (Prior: FAILED) |
| **M2-B-RES** | $S + U$ | Residual $\Delta \hat{s}_t$ | $31 \times (k+1)$ | $\approx 90\text{K}$ | **Core Test 1:** Does residual prediction restore causal action dependence? |
| **M2-B-MATCHED** | $S + U$ (widened hidden) | Residual $\Delta \hat{s}_t$ | $31 \times (k+1)$ | $\approx 140\text{K}$ | **Capacity Control:** Matches Condition F parameters without memory. |
| **M3-C-DIR** | $S + U + \mathbf{v}_{\text{HD}}$ | Direct $\hat{s}_{t+1}$ | $33 \times (k+1)$ | $\approx 91\text{K}$ | Does head direction alone improve direct prediction? |
| **M3-C-RES** | $S + U + \mathbf{v}_{\text{HD}}$ | Residual $\Delta \hat{s}_t$ | $33 \times (k+1)$ | $\approx 91\text{K}$ | Does head direction improve residual yaw/sonar prediction? |
| **M4-D-DIR** | $S + U + \mathbf{G}_{\text{grid}}$ | Direct $\hat{s}_{t+1}$ | $33 \times (k+1)$ | $\approx 91\text{K}$ | Does spatial displacement alone improve direct prediction? |
| **M4-D-RES** | $S + U + \mathbf{G}_{\text{grid}}$ | Residual $\Delta \hat{s}_t$ | $33 \times (k+1)$ | $\approx 91\text{K}$ | Does spatial displacement improve residual prediction? |
| **M5-E-DIR** | $S + U + \mathbf{v}_{\text{HD}} + \mathbf{G}_{\text{grid}}$ | Direct $\hat{s}_{t+1}$ | $35 \times (k+1)$ | $\approx 92\text{K}$ | Prior Benchmark (Cond D): Full self-pose direct prediction (Prior: FAILED) |
| **M5-E-RES** | $S + U + \mathbf{v}_{\text{HD}} + \mathbf{G}_{\text{grid}}$ | Residual $\Delta \hat{s}_t$ | $35 \times (k+1)$ | $\approx 92\text{K}$ | **Core Test 2:** Can self-pose predict sonar when identity shortcut is removed? |
| **M6-F-DIR** | $S + U + \text{Pose} + \mathbf{M}_{\text{env}}$ | Direct $\hat{s}_{t+1}$ | $35 + d_{\text{mem}}$ | $\approx 140\text{K}$ | Does environmental memory help direct-state prediction? |
| **M6-F-RES** | $S + U + \text{Pose} + \mathbf{M}_{\text{env}}$ | Residual $\Delta \hat{s}_t$ | $35 + d_{\text{mem}}$ | $\approx 140\text{K}$ | **Core Test 3:** Full grounded world model (Residual + Pose + Memory) |

---

## 4. The Canonical Six Batteries (Strict Final Definition)

All model configurations are evaluated against exactly six pre-registered diagnostic batteries:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                CANONICAL SIX BATTERY DEFINITIONS                                │
├────────────────────────────────┬──────────────────────────────────────┬────────────────────────┤
│ BATTERY                        │ TEST PROTOCOL                        │ PASS CRITERION         │
├────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Battery 1: Predictive Fidelity │ Multi-horizon autoregressive rollout │ H=10 Sonar R² >= 0.60   │
│                                │ on D_all and D_dynamic               │ specifically on        │
│                                │                                      │ D_dynamic partition    │
├────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Battery 2: Action Causality    │ Zero actions (u=0), Permute actions, │ Zero: ΔE >= +25%       │
│                                │ and Invert action sign (u -> -u)     │ Perm: ΔE >= +20%       │
│                                │                                      │ Invert: ΔE >= +30%     │
├────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Battery 3: Spatial Causality   │ Scramble CANN spatial coordinates    │ Sonar error surge      │
│                                │ while keeping sensors & actions real │ ΔE >= +20%             │
├────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Battery 4: Spatial             │ Two distinct arena locations with    │ Divergence at H=10     │
│            Disambiguation      │ matching forward sonar within tol    │ ||ŝ_loc1 - ŝ_loc2||    │
│                                │ (front diff <= 0.35m, dist >= 1.2m)  │ >= 1.0 m               │
├────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Battery 5: Counterfactual      │ Branching rollouts from identical    │ Trajectory divergence  │
│            Branching           │ initial state under 3 motor sequences│ >= 1.0 m               │
│                                │ (Straight, Left Spin, Reverse)       │ normalized distance    │
├────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Battery 6: Collision           │ Predict upcoming contact event       │ Hazard detection       │
│            Anticipation        │ across horizons H in [1, 10] steps   │ ROC-AUC >= 0.85        │
│                                │ using contact-subtracted oracle      │ (Floor contacts excl.) │
└────────────────────────────────┴──────────────────────────────────────┴────────────────────────┘
```

### Secondary Diagnostics (Separately Reported)
The following tests are recorded as informative engineering diagnostics but do not override the Canonical Six Batteries:
1. **IAAFT Surrogate Test:** Phase-randomized null distribution to confirm non-linearity of predictive gains ($p < 0.01$).
2. **Sensor Noise Robustness:** Sensitivity to $\pm 10\%$ Gaussian sensor noise injection.
3. **Capacity Scaling Curve:** Parameter efficiency comparisons across $[50\text{K}, 90\text{K}, 140\text{K}]$.

---

## 5. Architectural Decision Trees & Falsification Logic

The matrix outcomes dictate the definitive scientific path forward via a strict decision tree:

```text
                                [M2-B-RES vs M2-B-DIR]
                      Does Residual Δs restore Action Sensitivity?
                                      │
                      ┌───────────────┴───────────────┐
                      ▼ YES                           ▼ NO
             [Action Bus Coupled]            [Identity Shortcut Persists]
             Residual hypothesis             Residual formulation fails;
             partially supported             investigate loss weighting
                      │
                      ▼
           [M5-E-RES vs M2-B-RES]
  Does Stage 2.1 Spatial State (HD+Grid)
   significantly improve Sonar R²?
                      │
      ┌───────────────┴───────────────┐
      ▼ YES                           ▼ NO
 [Spatial Grounding Proven]     [Spatial Information Insufficient]
 Stage 2.1 contains necessary   Stage 2.1 coordinates lack map context;
 environmental structure        dead-reckoned pose alone cannot predict obstacles
      │                               │
      ▼                               ▼
 [Proceed to STAGE 2.2-R1]      [Evaluate M6-F-RES vs M2-B-MATCHED]
 Lock minimal architecture      Does learned environmental memory outperform
 using Stage 2.1 Pose           both M5-E-RES and matched-capacity baseline?
                                              │
                              ┌───────────────┴───────────────┐
                              ▼ YES                           ▼ NO
                      [Memory Required]               [STAGE 2.2 FORMAL FAIL]
                      Architecture must               CARL cannot learn predictive
                      include explicit learned        world model from current sensory
                      environmental memory            apparatus without architectural
                      substrate                       expansion
```

---

## 6. Pre-Registration & Test Freeze Commitments

1. **What is Frozen and Absolute Primary-Test Isolation:**
   - The 13 configurations, metrics, intervention formulas, and thresholds defined in this matrix are frozen.
   - **PRIMARY_UNSEEN_TEST must not exist in accessible form during Phase 1. It must be generated only after the architecture, hyperparameters, metrics, preprocessing, and diagnostic conclusions are frozen (Phase 3).**
   - Phase 1 diagnostic benchmarking across all 13 model configurations is strictly restricted to **`DEV_TRAIN` $\to$ `DEV_VAL` only**.
   - Unseen test seeds `[303, 404, 505, 606, 707]` will not be run, inspected, or sampled, and no unseen dataset will exist on disk during Phase 1.
2. **What Constitutes a Milestone Pass:**
   - A model passes Stage 2.2 if and only if it passes all six canonical batteries on the frozen unseen test set in Phase 3.
3. **What Constitutes a Milestone Fail:**
   - If no model passes all six canonical batteries, Stage 2.2 is officially certified as **FAILED**, and the exact empirical bottlenecks will be published without retroactive adjustment.
4. **What Must NOT Be Changed:**
   - No lowering thresholds post-hoc.
   - No introducing privileged simulator state or GPS coordinates.
   - No hand-coding geometric formulas or wall equations.
   - No test-time online adaptation.
