# CARL STAGE 2.2: PRE-IMPLEMENTATION FORENSIC AUDIT
## COMPREHENSIVE VULNERABILITY, LEAKAGE, AND ARCHITECTURAL INTEGRITY AUDIT
**Author:** Antigravity AI Orchestrator  
**Classification:** [PRE-EXPERIMENTAL AUDIT] Immutable Verification Baseline  
**Date:** September 5, 2026  
**Governing Mandate:** Stage 2.2 Learned Generative World & Self Modeling  
**Target Milestone:** Transition from Persistent Spatial Representation (2.1) to Learned Forward World Modeling (2.2)  

---

## 1. Executive Directive & Audit Context

Per executive instruction, all development, training, and execution on Stage 2.2 is frozen until this forensic audit and all associated specification artifacts are completed, reviewed, and locked.

The objective of Stage 2.2 is:
> **To determine whether CARL can learn, from embodied experience, an internal model that predicts the consequences of its actions.**
> The objective is NOT to manufacture artificially favorable prediction numbers.

CARL remains **ONE canonical unified embodied organism**. Stage 2.2 is an organ being developed for that organism, not a second independent brain. No Stage 3 planning (MPPI, policy optimization, behavioral discovery) or lifelong self-modification may be introduced prematurely.

This audit evaluates the preliminary draft specification (`CARL_STAGE2_2_PREDICTIVE_WORLD_MODEL_SPECIFICATION.md`), the draft implementation plan (`implementation_plan.md`), the legacy prototype (`brain/carl_world_model.py`), and the active Stage 2.1B codebase (`carl_stage2_integrated_brain.py`, `carl_stage1_hal.py`).

---

## 2. Forensic Itemized Vulnerability Matrix (Dimensions A through M)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               FORENSIC AUDIT SUMMARY MATRIX                                      │
├────┬───────────────────────────────────┬──────────────┬───────────────────────────────────────────┤
│ ID │ Vulnerability Domain              │ Risk Level   │ Primary Remediation Required              │
├────┼───────────────────────────────────┼──────────────┼───────────────────────────────────────────┤
│ A  │ True Statistical Unit             │ CRITICAL     │ Pre-register episode-level paired units   │
│ B  │ Dataset Partition Separation      │ CRITICAL     │ 4 explicit partitions: DEBUG/TRAIN/VAL/TEST│
│ C  │ Randomization Provenance          │ HIGH         │ Hierarchical seed tracking & dataset hash │
│ D  │ Cross-Partition Contamination     │ CRITICAL     │ Separate artifacts + automated assertions │
│ E  │ Post-Selection Hard Freeze        │ CRITICAL     │ Parameter hash invariant before & after   │
│ F  │ Rollout Call-Graph Isolation      │ FATAL        │ AST full-graph trace + subprocess sandbox │
│ G  │ Epistemic Claim Inflation         │ MODERATE     │ Explicit Engineered vs Learned taxonomy   │
│ H  │ Baseline Significance Rigor       │ HIGH         │ Wilcoxon paired test + effect size gate   │
│ I  │ Ablation Distributional Shifts    │ HIGH         │ Isolated ceteris-paribus counterfactuals  │
│ J  │ Collision Ground-Truth Leakage    │ FATAL        │ Pure counterfactuals + sensor threshold   │
│ K  │ Outcome Ambiguity & Stop Rules    │ HIGH         │ Exact PASS / FAIL / INVALID definitions   │
│ L  │ Visualization Deception           │ MODERATE     │ Strict plotting rules: no selective axes  │
│ M  │ Premature Execution               │ CRITICAL     │ 10-step strict sequential order locked    │
└────┴───────────────────────────────────┴──────────────┴───────────────────────────────────────────┘
```

---

### A. True Statistical Unit & Hypothesis Testing

#### 1. Vulnerability Identified
Reporting only an aggregate mean across 5 seeds creates a statistical $N=5$. With $N=5$, non-parametric paired tests (such as the Wilcoxon signed-rank test) have a minimum possible two-tailed $p$-value of $2 \times (1/2)^5 = 0.0625$, making it mathematically impossible to achieve $p < 0.05$ or $p < 0.01$! Conversely, pooling individual time-steps ($N = 25 \times 400 = 10,000$) inflates degrees of freedom through severe temporal autocorrelation, producing artificially tiny $p$-values.

#### 2. Mandatory Correction
- **Primary Statistical Unit:** The independent unit for all statistical tests is pre-registered as the **independent evaluation episode** ($N = 25$ episodes across 5 seeds, 5 episodes per seed).
- For baseline comparisons (Proposed World Model vs Persistence vs Linear Readout):
  - Comparisons must be performed as **paired differences on identical episode trajectories**:
    $$\Delta \text{RMSE}_e = \text{RMSE}_e(\text{Baseline}) - \text{RMSE}_e(\text{World Model})$$
  - Statistical test: Two-tailed Wilcoxon signed-rank test on paired episode errors ($N=25$).
  - Required reporting: Sample size $N$, test statistic $W$, exact unrounded $p$-value, and effect size (rank-biserial correlation $r$ and Cohen's $d$).
  - Invariant: A statistically significant $p$-value ($p < 0.01$) is invalid if the practical effect size is negligible (mandating Cohen's $d \ge 0.50$ and relative RMSE reduction $\ge 15.0\%$).

---

### B. Separation of Development Debugging from Primary Test

#### 1. Vulnerability Identified
If engineers use the test partition or a mixed validation set to debug scripts, trace shapes, or tune hyperparameters, test data is leaked into the developer's feedback loop.

#### 2. Mandatory Correction
Establish **4 explicitly isolated partitions**:
1. `DEV_DEBUG`: 5 short episodes (Seed 42) strictly for pipeline testing, shape validation, and smoke tests.
2. `DEV_TRAIN`: 60 episodes (Seeds 42, 101, 202; 20 each) strictly for parameter gradient backpropagation.
3. `DEV_VAL`: 20 independent episodes (Seeds 42, 101, 202) strictly for early stopping and hyperparameter selection.
4. `PRIMARY_UNSEEN_TEST`: 25 episodes (Seeds 303, 404, 505, 606, 707; 5 each) strictly evaluated **once post-freeze**.
- `PRIMARY_UNSEEN_TEST` is generated and cryptographically hashed (SHA-256) ONLY after implementation, hyperparameters, metrics, and evaluation scripts are frozen.

---

### C. Hierarchical Randomization & Provenance Tracking

#### 1. Vulnerability Identified
Random variation in obstacle placement, initial robot orientation, or motor babbling sequences can prevent exact reproducibility if RNG states are not hierarchically tracked.

#### 2. Mandatory Correction
Every experimental trajectory must record:
- Master RNG seed
- Per-episode seed: $S_{\text{ep}} = \text{hash}(\text{master\_seed}, \text{partition}, \text{episode\_idx})$
- Environment geometry seed (obstacle layout)
- Action sequence generator seed
- Floor friction seed
- SHA-256 hash of the complete dataset file

A rerun with the identical frozen configuration must reproduce the exact bit-for-bit sensory trajectory and numerical score.

---

### D. Separation of Training, Validation, and Test Artifacts

#### 1. Vulnerability Identified
Shared python modules or global state dictionaries can accidentally allow test data to update normalization statistics or leak running moments.

#### 2. Mandatory Correction
- **Normalization Statistics:** Computed strictly on `DEV_TRAIN`. Saved to `checkpoints/stage2_2_norm_stats.npz`.
- **Checkpoint Selection:** Selected strictly on `DEV_VAL` autoregressive loss ($H=10$).
- **Hyperparameter Tuning:** Conducted strictly on `DEV_TRAIN` + `DEV_VAL`.
- **Automated Anti-Contamination Assertions:** Automated assertions in the test harness verify that:
  - The test dataset path is not in the training data loader.
  - Normalization tensors match the SHA-256 hash of `checkpoints/stage2_2_norm_stats.npz`.
  - Zero test-seed indices appear in the training ledger.

---

### E. Hard Freeze After Checkpoint Selection

#### 1. Vulnerability Identified
In many machine learning frameworks, calling `model(x)` in `eval()` mode can still mutate internal buffers if `track_running_stats=True` or if online adaptation hooks exist.

#### 2. Mandatory Correction
- Once the final checkpoint is saved to `checkpoints/carl_stage2_2_world_model_frozen.pt`:
  - PyTorch parameters are set to `requires_grad = False`.
  - Optimizer is completely deleted from memory.
  - All adaptation methods (`update_model`, RLS, Kalman) are detached.
  - Evaluation wrapper computes `hash_before = sha256(model.parameters())` before evaluating an unseen seed and `hash_after = sha256(model.parameters())` immediately after.
  - An automated assertion enforces: `assert hash_before == hash_after`.

---

### F. Strengthened Anti-Cheat Call-Graph Isolation

#### 1. Vulnerability Identified
AST-checking only `carl_stage2_2_world_model.py` leaves a loophole: helper functions in other modules (e.g. `carl_stage1_hal.py`, `carl_stage2_spatial_controller.py`) could be imported and invoked during rollout.

#### 2. Mandatory Correction
1. **Full Call-Graph AST Inspection:** The static analyzer `tests/test_stage2_2_anti_cheat_isolation.py` must recursively inspect all imported local project modules reachable from the rollout function. It must verify that:
   - Zero functions in the rollout path import `mujoco`.
   - Zero variables access `data.qpos`, `data.qvel`, `data.contact`, or `mj_ray`.
2. **Subprocess MuJoCo-Banned Execution:** The test harness must execute the mental forward rollout in an isolated Python subprocess where `mujoco` is actively poisoned:
   ```python
   sys.modules["mujoco"] = None  # Any import of mujoco raises ImportError
   ```
   If the mental rollout attempts to call MuJoCo or fails to run without MuJoCo present, it triggers a **HARD FAIL**.

---

### G. Epistemic Classification: Engineered vs Learned

#### 1. Vulnerability Identified
Describing standard GRU sequence prediction with inflated cognitive terminology ("emergent consciousness", "biological thought", "sentient agency") is unscientific and erodes credibility.

#### 2. Mandatory Correction
Explicitly categorize all aspects of Stage 2.2:
- **ENGINEERED SUBSTRATE:**
  - Recurrent neural network topology (GRU) and decoder MLP.
  - Loss formulation (multi-horizon weighted MSE) and AdamW optimizer.
  - Sensor input normalization and bounding clamps.
  - Training schedule and curriculum.
- **LEARNED CAPABILITY:**
  - Internal forward transition weights $\mathbf{W}_{\text{rec}}$.
  - Sensory synthesis mapping $\mathbf{W}_{\text{dec}}$.
  - Temporal forward contingency representations.
- Prohibited Terminology: "biological brain", "conscious", "sentient", "human-like".

---

### H. Rigorous Baseline Verification

#### 1. Vulnerability Identified
Showing that a model beats a trivial baseline by an infinitesimally small margin (e.g. $0.1\%$ error reduction) can be statistically significant with large $N$ while being practically useless.

#### 2. Mandatory Correction
- Baseline A (Naive Persistence: $\hat{s}_{t+k} = s_t$) and Baseline B (Linear Action Predictor) must be evaluated on the **exact same 25 unseen test episodes**.
- The Recurrent World Model must satisfy **BOTH**:
  1. Statistical significance: $p < 0.01$ (Wilcoxon signed-rank test).
  2. Substantive effect size: Cohen's $d \ge 0.50$ AND relative RMSE reduction $\ge 15.0\%$ vs Baseline A and Baseline B.

---

### I. Scientifically Precise Causal Ablations

#### 1. Vulnerability Identified
If an ablation modifies input scales or introduces out-of-distribution noise, the model might fail due to numerical shock rather than causal loss of information.

#### 2. Mandatory Correction
All ablations must be evaluated on the identical 25 unseen test episodes, preserving all other variables:
1. **Ablation 1 (Action-Zero):** Same initial observation $s_t$, same internal state $h_t$, candidate future actions set to $u_{t:t+H-1} = \mathbf{0}$. (Tests reliance on motor efference).
2. **Ablation 2 (Recurrent-Zero):** Same initial observation $s_t$, candidate future actions $u$, initial belief state clamped to $h_t = \mathbf{0}$. (Tests temporal memory).
3. **Ablation 3 (Action-Shuffle):** Candidate actions permuted using a fixed deterministic seed permutation: $\tilde{u}_{t+k} = u_{t+\pi(k)}$. (Tests sequential action causality).
4. **Ablation 4 (Channel-Shuffle):** Input observations permuted with a fixed spatial permutation matrix: $\tilde{s} = \mathbf{P}_{\text{perm}} s$. (Tests sensory topology).
- Degradation metric: Report exact percentage change in RMSE relative to the intact model on the identical episodes:
  $$\Delta \text{Degradation} = \frac{\text{RMSE}_{\text{ablation}} - \text{RMSE}_{\text{intact}}}{\text{RMSE}_{\text{intact}}} \times 100\%$$
- Required threshold: $> 30.0\%$ degradation for each active ablation.

---

### J. Purely Counterfactual Collision Anticipation

#### 1. Vulnerability Identified
If collision ground truth is derived from simulator geometry during prediction, or if obstacle positions are leaked to the model, collision prediction is trivially engineered.

#### 2. Mandatory Correction
- At prediction time $t$, the model receives ONLY $(s_{\le t}, u_{\le t}, h_t)$ and candidate action sequences $u_{t:t+H-1}^{(A)}$ (collide) vs $u_{t:t+H-1}^{(B)}$ (evade).
- The model synthesizes predicted sensory trajectories: $\hat{s}_{t+1:t+H}$.
- Collision prediction is computed via a fixed pre-registered sensory rule:
  $$\hat{C} = \mathbb{I}\left( \min_{k \le 15} \hat{s}_{\text{front}, k} \le 0.15\,\text{m} \right)$$
- The evaluator steps the physical simulator in an independent run to obtain physical ground truth ($N_{\text{contact}} > 0$).
- ROC-AUC and PR-AUC are computed strictly after predictions are locked.

---

### K. Operational Definitions of Success, Failure, and Invalid Runs

#### 1. Vulnerability Identified
Ambiguity between an infrastructure crash (e.g. out-of-memory, file permission, missing asset) and a scientific failure can lead to discarding unfavorable runs.

#### 2. Mandatory Correction
Define the three possible outcomes unambiguously:
- **PASS:** All pre-registered numerical criteria met across 5/5 unseen test seeds without a single gate failure.
- **FAIL:** The simulation completed successfully, code functioned as intended, but numerical criteria failed (e.g. $R^2 < 0.65$, ROC-AUC $< 0.88$, or stability slope $\beta > 0.06$).
- **UNDECIDABLE / INVALID RUN:** An infrastructure defect (unhandled exception, NaN in simulator physics, missing disk file) interrupted execution before completing the pre-registered protocol.
  - Protocol for Invalid Runs: An invalid run on DEV data must be repaired before testing unseen data. If an invalid run occurs during the official `PRIMARY_UNSEEN_TEST`, the entire test run is invalidated, the root cause documented, and a newly pre-registered unseen test battery generated. Zero selective re-running of individual test seeds.

---

### L. Deception-Free Visualizations

#### 1. Vulnerability Identified
Cherry-picking single successful episodes, truncating error axes, or smoothing time-series can make failing models appear competent.

#### 2. Mandatory Correction
All 10 figures must adhere to immutable presentation rules:
1. Every plot must explicitly display: Ground Truth, Prediction, Residual Error, Time/Horizon, Seed ID, and Partition Name.
2. Zero selective axis clipping (all bounds must include $[0, 5\,\text{m}]$ for sonars, $[-20, 20\,\text{rad/s}]$ for gyros).
3. The Master Dashboard (Figure 10) must show results for **every individual unseen seed** (no averaging away failures).
4. The demonstration video must display:
   - First: CARL's imagined forward rollout generated in tensor space.
   - Second: The physical trajectory executed in MuJoCo, overlaid with absolute visual distinction.

---

### M. Strict Sequential Execution Order

```text
STAGE 1: Forensic Consistency Check (THIS AUDIT)                <-- COMPLETE
   │
   ▼
STAGE 2: Lock Corrected Specification & Implementation Plan    <-- IMMEDIATE
   │
   ▼
STAGE 3: Development Validation on DEV_DEBUG / TRAIN / VAL      <-- NEXT PHASE
   │
   ▼
STAGE 4: Hard Freeze of Code, Checkpoint & Norm Statistics      <-- CRITICAL GATE
   │
   ▼
STAGE 5: Generate & Hash PRIMARY_UNSEEN_TEST                     <-- AIR-GAPPED
   │
   ▼
STAGE 6: Execute Official Primary Unseen Evaluation Exactly Once <-- STRICT ONCE
   │
   ▼
STAGE 7: Generate Raw Telemetry, 10 Figures & Video Package      <-- EVIDENCE
   │
   ▼
STAGE 8: Multi-Role Independent Forensic Audit Report            <-- VERDICT
```

---

## 3. Final Pre-Execution Sign-Off

This audit has closed all identified statistical, architectural, and experimental loopholes. 
Implementation remains **STRICTLY FROZEN** until the corrected specification and implementation plan are locked.
