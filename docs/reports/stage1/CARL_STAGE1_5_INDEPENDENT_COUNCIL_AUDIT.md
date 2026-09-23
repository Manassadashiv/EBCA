# CARL STAGE 1.5 — INDEPENDENT COUNCIL FORENSIC AUDIT
**Date of Audit:** September 3, 2026  
**Auditor:** Antigravity Independent Evaluation Tribunal & The LLM Council  
**Classification:** [FINAL TRUST GATE] Stage 1.5 Adversarial Falsification Audit  
**Adversarial Standard:** Absolute verification of executable source code, raw results, and runtime information flow. Zero tolerance for promotional language, simulated consensus, or harness intelligence.

---

## 1. Executive Verdict

**OVERALL AUDIT VERDICT: B. SUBSTANTIALLY VERIFIED WITH CRITICAL LIMITATIONS**

The Stage 1.5 forensic repair successfully eliminated the catastrophic structural frauds of Stage 1.0 (privileged `qpos` steering, external sklearn predictor models, global arena contact contamination, and inverted airborne traction logic). 

However, deep code-level tracing reveals **three critical new limitations and ungrounded shortcuts** in the current Stage 1.5 implementation:

1. **The Test 6 Action Selection Illusion:** In `CarlStage1Organism.synthesize_action()`, line 223 contains an early return: `if self.sensory_target_channel is None: return candidates[1]`. Because Test 6 never called `set_sensory_goal()`, `sensory_target_channel` was `None`. Consequently, CARL's predictive forward model was **never queried during action selection in Test 6**. CARL did not "optimize sensory clearance"; it executed an open-loop constant pulse (`candidates[1] = [0.15, 0.15]`) on its discovered drive channels.
2. **The Traction Discrepancy False-Alarm Defect:** In `CarlStage1Organism.detect_traction_discrepancy()`, instantaneous prediction error is measured as the 25-D Euclidean vector norm $\|s_t - \hat{s}_t\|_2$, but the developmental baseline was saved as the element-wise scalar RMSE. Because vector norm scales as $\sqrt{25} \approx 5\times$ scalar RMSE, the slip detector triggers **16 out of 30 ticks on dry, high-friction ground ($\mu = 3.0$)**. Test 7's reported 14 slip detections on ice were not unique to ice; the detector was already misfiring on dry concrete.
3. **Counterfactual Prediction is a 1-Step Linear Jacobian:** `evaluate_counterfactuals()` performs no temporal rollout, planning, or recurrent reservoir integration. It evaluates $\hat{s}(u) = s_t + W_{\text{pred}} [s_t, u] + b_{\text{pred}}$, which simplifies to $\Delta \hat{s} = W_u (u_A - u_B)$. This is a static first-order linear transfer matrix, not multi-step counterfactual cognitive reasoning.

---

## 2. What CARL Definitely Does

Based on verified runtime execution and immutable code inspection:
- **Autonomous Babbling & Reservoir Driving:** CARL generates bounded motor commands ($|u_i| \le 0.15$) via Ornstein-Uhlenbeck diffusion and drives a 1026-neuron Liquid State Machine reservoir with unified memory layout (`S_unified[1061]`).
- **Data Collection for Discovery:** CARL autonomously logs 25-D sensory feedback and 6-D executed motor actions into `telemetry_history`.
- **Bilateral Locomotion Channel Identification:** CARL's sensory-motor correlation structure allows the discovery engine to unambiguously identify the two differential drive wheels under dual-blind actuator and sensor scrambling ($P_{\text{act}}$ and $P_{\text{sens}}$).
- **Internal 1-Step Predictive Modeling:** CARL fits and stores an internal linear readout ($W_{\text{pred}} \in \mathbb{R}^{25 \times 31}$) that predicts 1-step sensory velocity $\Delta s$ from $[s_t, u_t]$, achieving a **26.57% error reduction over persistence** on held-out developmental data.
- **Directional Gyro Prediction:** CARL's internal weights correctly predict that differential drive pulses rotate the robot in the opposite yaw direction from straight cruise (gyro cosine similarity = **+0.904**).

---

## 3. What the Harness Definitely Does

- **Coordinates Permutations:** The test harness generates the secret permutations $P_{\text{act}} = [3, 0, 5, 1, 4, 2]$ and $P_{\text{sens}}$, and routes them through the HAL.
- **Computes Surrogate Significance:** `CarlSensorimotorDiscoveryEngine` generates IAAFT phase-randomized surrogate time-series, computes mutual information matrices, and runs the bilateral pairing algorithm. This code resides outside `CarlStage1Organism`.
- **Evaluates Ground Truth:** The harness clones MuJoCo simulator state vectors ($qpos, qvel$) in Test 5 to evaluate physical ground truth, and queries `hal.data.qpos` after Test 6 to measure physical displacement.
- **Sets Physical Regimes:** The harness manually changes MuJoCo body positions (90° roll for sideways, $z=0.60\text{ m}$ for airborne) and surface friction ($\mu = 0.005$ for ice).

---

## 4. What the Simulator Definitely Does

- **Solves Rigid-Body Dynamics:** MuJoCo solves Newton-Euler equations, contact impulses, friction cones, and constraint satisfaction at 30 Hz (substep $dt = 0.0111\text{ s}$).
- **Enforces Kinematic Limits:** Wheel rotation, caster castor swivel, chassis pitch, and tilt dynamics are entirely computed by MuJoCo's C-bindings.
- **Decouples Traction Physically:** When friction drops or the chassis tilts, MuJoCo physically decouples wheel spin from chassis translation. CARL does not simulate this physics; MuJoCo does.

---

## 5. Information-Flow Diagram

```
[MuJoCo 3.12.0 Physics Engine]
         │
         │ (qpos, qvel, qacc, geom contacts)
         ▼
[CarlStage1HAL]
         │
         ├── Filter: Extract 20 CARL geoms -> carl_contacts, floor_contacts
         ├── Sensor permutation: s_raw -> s_permuted (25-D)
         ▼
[Sensation Acquisition: s_t in R^25]
         │
         ├───▶ [S_unified Buffer: S[0:25]]
         │
         ▼
[CarlStage1Organism Runtime]
         │
         ├── Step 1: Compute Prediction Error e_t = s_t - s_hat_t
         │
         ├── Step 2: Action Synthesis (synthesize_action)
         │      │
         │      ├── [AUDIT FINDING]: sensory_target_channel is None!
         │      │     └── Returns candidates[1] = [0.15, 0.15] (Constant cruise)
         │      │     └── (Predictive candidate evaluation is bypassed!)
         │      │
         │      └── Safety Clamping: u_executed = clip(u_proposed, -0.15, 0.15)
         │
         ├── Step 3: Write u_executed -> S_unified[1055:1061]
         ├── Step 4: Step 1026-N Reservoir -> S_unified[25:1051]
         │
         ├── Step 5: Compute 1-step prediction for next tick:
         │      └── s_hat_{t+1} = s_t + W_pred @ [s_t, u_executed] + b_pred
         │
         └── Step 6: Dispatch u_executed to HAL
                     │
                     ▼
             [Actuator Permutation: u_permuted = u[P_act]]
                     │
                     ▼
             [MuJoCo ctrl[0:6] Actuation]
```

---

## 6. Council Advisor Reports

### The Contrarian
> *"I went straight for the jugular in `brain/carl_stage1_organism.py` and found the smoking gun:
> 
> Look at line 223 of `synthesize_action()`:
> ```python
> if self.sensory_target_channel is None:
>     return candidates[1]
> ```
> Now look at Test 6 in `brain/carl_stage1_adversarial_suite.py`. It initializes `org_full`, sets `control_mode = 'goal_seeking'`, and calls `org_full.step()`. It **never calls `set_sensory_goal()`**.
> 
> That means `self.sensory_target_channel` is `None` for the entire 200 ticks of the benchmark! Lines 226–244, where the forward model is supposed to score candidate motor commands, **never executed**. CARL was simply driving forward on cruise control because `candidates[1]` happens to be `[0.15, 0.15]`.
> 
> Furthermore, in Test 7, the slip detector triggered 16 times on dry concrete because someone compared a 25-D vector Euclidean norm against a 1-D scalar RMSE. The claim that CARL 'discovered when it was slipping and adapted' is ungrounded. CARL's slip detector was screaming that it was slipping before the ice was even added."*

### The First-Principles Scientist
> *"From a physical and mathematical perspective, we must distinguish three layers of claims:
> 
> 1. **Topological Discovery (Test 3):** Mathematically sound. Two differential drive wheels act symmetrically on a single rigid body's rotational degree of freedom. Under arbitrary permutations $\pi$ on actuators and $\sigma$ on sensors, the bilateral mutual information invariant $\max_j \min(MI(u_a, s_j), MI(u_b, s_j))$ uniquely recovers the drive pair without human semantic priors.
> 2. **Predictive Forward Model (Test 4):** Valid but modest. An error reduction of 26.57% over persistence on developmental babbling and 16.97% on out-of-distribution 2.0 Hz multi-sine proves that a linear mapping $\Delta s \approx W [s, u]$ captures first-order rigid-body inertia. However, an $R^2$ of 0.0615 indicates that over 93% of sensory variance is unexplained by the linear model. Calling this a 'world model' overstates a linear autoregressive filter.
> 3. **Counterfactual Reasoning (Test 5):** Mathematically, `evaluate_counterfactuals()` evaluates $\hat{s}(u_A) - \hat{s}(u_B) = W_u (u_A - u_B)$. This is literally the linear directional derivative $\nabla_u s \cdot \Delta u$. That the gyro subspace aligns with physical reality ($+0.904$ cosine similarity) proves the Jacobian has the correct sign, but it does not represent multi-step cognitive branching."*

### The Developmental Robotics Expert
> *"In developmental robotics (Oudeyer, Lungarella, Pfeifer), motor babbling serves to build an internal body schema. CARL genuinely achieves the first half of this paradigm:
> 
> - It begins with anonymous, uncalibrated wires.
> - It babbles within a safe physical ceiling ($|u| \le 0.15$).
> - It identifies the kinematic distinction between locomotion actuators (whole-body angular coupling) and articulation servos (sparse localized joint proprioception).
> - It eliminates causally inert channels (Visor LED) via isolated interventions ($3.32 \times 10^{-6}\text{ m/s}^2$).
> 
> Where the developmental claim fails is **closed-loop intentionality**. A developmental organism uses its learned forward model to minimize free energy or prediction error. Because Test 6 defaulted to constant cruise without engaging `predict_next_observation()` in the action loop, CARL has not demonstrated goal-directed intentionality. It has demonstrated sensory-motor calibration followed by hardcoded forward execution."*

### The Outsider / Null-Hypothesis Reviewer
> *"My job is to find the simplest, dumbest explanation that explains all the positive test numbers without invoking any machine intelligence:
> 
> - **Why did Test 1 pass?** Because MuJoCo physics works. When a robot is in the air, wheels turn and it doesn't move forward. That proves the simulator is working, not that CARL knows it is airborne.
> - **Why did Test 3 pass?** Because the wheels vibrate the gyro harder than the neck servos do. Finding the two strongest actuators connected to the gyro is a straightforward 2-column matrix search.
> - **Why did Test 6 pass ($4.29\times$ over random walk)?** Because CARL sent `[+0.15, +0.15]` every tick for 200 ticks, moving forward in a straight line, while the random baseline was jittering back and forth around zero. Any robot that drives straight beats a random walk.
> - **Why did Test 7 detect slip?** Because the threshold was miscalibrated so badly that the detector triggers on almost every step regardless of whether there is ice or not.
> 
> The null hypothesis easily explains Test 1, Test 6, and Test 7. Only Test 3 (permutation invariance) and Test 4 (linear prediction over persistence) withstand the null hypothesis."*

### The Systems / Reproducibility Auditor
> *"I traced every variable, buffer, and hash:
> 1. **Code Hygiene & Memory:** The UMA buffer contract (`S_unified[1061]`) is clean and strictly enforced via numpy slice assertions. There are no memory leaks or NaN instabilities.
> 2. **No Privileged State in Control:** I verified that `qpos` and `qvel` are completely absent from `CarlStage1Organism.step()`. The organism receives only `s_t \in \mathbb{R}^{25}` from `hal.read_sensors()`.
> 3. **Determinism:** The test suite is 100% reproducible. From seed 42, all numbers in `carl_stage1_5_results.json` match executable output to 6 decimal places.
> 4. **Runtime Ownership Breakdown:**
>    - Permutation discovery: HARNESS / ENGINE
>    - Model training ($W_{\text{pred}}$): CARL
>    - 1-step prediction: CARL
>    - Candidate evaluation during Test 6: BYPASSED (HARNESS / DEFAULT)
>    - Slip detection: CARL (BUT MATHEMATICALLY DEFECTIVE)"*

---

## 7. Chairman Cross-Examination

**Question 1 to The Contrarian:**  
*Is the bilateral pairing criterion in Test 3 a disguised semantic cheat?*  
**Contrarian Response:** *"No. The code does not check sensor indices. It computes an IAAFT null across all $6 \times 25$ pairs and finds the pair of actuators maximizing shared MI to an anonymous column. That is a legitimate structural property of a 2-wheel chassis. It's real, but it only works for differential drive."*

**Question 2 to The First-Principles Scientist:**  
*Can a 1-step linear model with $R^2 = 0.0615$ be considered a valid basis for active inference?*  
**First-Principles Response:** *"Only in a very crude sense. A linear model predicting velocities from $[s, u]$ captures the dominant sign of inertia ($\Delta \dot{\theta} \propto u_R - u_L$). It is sufficient to know that driving wheels moves the body forward and differential pulses turn it. But it cannot predict non-linear slip or multi-body bouncing. It is an inertia estimator, not a full generative world model."*

**Question 3 to The Outsider:**  
*Does CARL's 0.688 m displacement in Test 6 prove embodied competence?*  
**Outsider Response:** *"It proves that CARL correctly mapped its motors to its drive wheels and applied positive torque. If it had chosen the head servos, it would have moved 0.0004 m. So discovering which wires are wheels and powering them forward is real competence. But calling it 'autonomous predictive goal synthesis' is false because the predictive scoring loop was bypassed."*

---

## 8. Test-by-Test Adversarial Scorecard

| Test Battery | Intended Claim | CARL's Real Role | Harness Role | Simulator Role | Privileged State? | Actual Proven Result | Verdict | Confidence |
|---|---|---|---|---|---|---|---|---|
| **Test 1: Abnormal States** | Body-state grounded traction awareness | Passive sensor ingestion | Positions body; logs metrics | Simulates contact & free-wheeling | None to CARL; Evaluator uses `qpos` | MuJoCo contact physics correctly isolated (0 airborne contacts). CARL does not cognitive process this state. | **PASS (Physics Verified; Agent Passive)** | 100% |
| **Test 2: Causal Interventions** | Causal isolation of inert channels | Passive sensor ingestion | Pulses isolated actuators $do(u_i = c)$ | Propagates forces | None | LED actuator proven to have $3.32 \times 10^{-6}\text{ m/s}^2$ mechanical influence. Causal physics verified. | **PASS (Physical Causality Verified)** | 100% |
| **Test 3: Dual-Blind Permutation** | Tabula-rasa discovery under scrambled I/O | Provides babbling telemetry | Scrambles arrays; executes pairing algorithm | Executes scrambled inputs | None | Recovers scrambled drive wires `[0, 3]` without sensor labels via bilateral synergy invariant. | **PASS (Autonomous Discovery Verified)** | 100% |
| **Test 4: Predictive Model** | Generalizable internal forward model | Trains & stores $W_{\text{pred}}$ from telemetry | Generates test trajectories | Simulates ground truth | None | Linear readout achieves 26.57% held-out error reduction and 16.97% OOD reduction over persistence. Low $R^2$ (0.0615). | **PASS (Weak Linear Model Verified)** | 95% |
| **Test 5: Counterfactuals** | Mental branching without sim rollout | Computes $\hat{s}_A, \hat{s}_B, \hat{s}_C$ via $W_{\text{pred}}$ | Clones sim state to establish ground truth | Simulates physical branches | None to CARL | 1-step linear action sensitivity aligns with physical gyro divergence (CosSim = +0.904). 1-step Jacobian, not cognitive branching. | **PASS (Linear Sensitivity Verified)** | 90% |
| **Test 6: Autonomous Competence** | Closed-loop predictive action synthesis | Executes `synthesize_action()` | Sets up baselines; logs displacement | Simulates motion | None | Moves 0.688 m vs 0.160 m random walk. Predictive scoring was bypassed due to `sensory_target_channel is None`. Constant cruise executed. | **PARTIAL (Locomotion Verified; Predictive Optimization Falsified)** | 95% |
| **Test 7: Traction Loss** | Autonomous slip detection and adaptation | Runs slip check; scales torque | Drops floor friction to $\mu = 0.005$ | Simulates friction loss | None | Prediction error spikes by 1.52x on ice. However, slip detector misfires 53% on dry floor due to norm-vs-RMSE mismatch. | **PARTIAL (Error Spike Real; Slip Detector Broken)** | 95% |

---

## 9. CARL Ownership Matrix

| Capability | CARL | Harness | Simulator | Direct Code Evidence | Verdict |
|---|---|---|---|---|---|
| **1. Actuator Discovery** | 20% | 80% | 0% | Telemetry collected by CARL; surrogate test in `CarlSensorimotorDiscoveryEngine` | **SHARED** |
| **2. Sensor Discovery** | 20% | 80% | 0% | Sensation from CARL; max-shared MI search in `discovery.py` | **SHARED** |
| **3. Body-State Estimation** | 100% | 0% | 0% | Reservoir $x_{t+1}$ and unified memory buffer `S_unified` in `organism.py` | **CARL** |
| **4. Prediction** | 100% | 0% | 0% | $W_{\text{pred}}, b_{\text{pred}}$ trained and queried in `organism.py` | **CARL** |
| **5. Prediction-Error Computation** | 100% | 0% | 0% | `e_t = s_t - s_hat_t` computed onboard in `organism.step()` | **CARL** |
| **6. Counterfactual Prediction** | 100% | 0% | 0% | `organism.evaluate_counterfactuals()` evaluates without sim steps | **CARL (1-Step Linear)** |
| **7. Candidate-Action Evaluation** | 0% | 100% | 0% | Bypassed in Test 6 (`if sensory_target_channel is None: return candidates[1]`) | **HARNESS DEFAULT** |
| **8. Action Selection** | 40% | 60% | 0% | Selects candidate 1 based on discovered topology, but optimization loop uncalled | **SHARED** |
| **9. Traction-Loss Detection** | 100% | 0% | 0% | `detect_traction_discrepancy()` in `organism.py` (has dimensional bug) | **CARL (Defective)** |
| **10. Adaptation** | 100% | 0% | 0% | Torque scaling `candidates = [c * 0.4 ...]` in `organism.py` | **CARL** |
| **11. Goal-Directed Behavior** | 10% | 90% | 0% | Test 6 ran open-loop cruise; no goal-reaching feedback loop in CARL | **HARNESS-DEPENDENT** |

---

## 10. Hidden Leakage Findings

1. **Test 6 Early-Return Shortcut:** Line 223 of `carl_stage1_organism.py` short-circuited the candidate evaluation loop because `sensory_target_channel` was `None`. No runtime error occurred, but the predictive model was excluded from the action-selection loop.
2. **Test 7 Dimension Bug:** In `learn_predictive_readout()`, `self.baseline_prediction_error_norm` was assigned scalar element-wise RMSE ($1.003$). In `step()`, `self.last_prediction_error_norm` was computed as the 25-D vector Euclidean norm ($\approx 5.8 - 7.5$). The $2.0\times$ threshold was constantly exceeded on dry ground.
3. **Restored Hardware Coupling in Test 6:** When Test 3 finished, HAL restored the identity permutation, but Test 6 initially received the scrambled channel indices `[0, 3]`. This was patched to `[0, 1]`, but revealed that the test runner was manually bridging the hardware state between tests.

---

## 11. Statistical Validity

- **Permutation Significance:** The replacement of Gaussian tail extrapolation with exact non-parametric empirical bounds $p = (1 + k)/(N + 1)$ is statistically valid. For $N = 50$ surrogates, zero exceedance establishes $p \le 0.0196$.
- **Correction Limitations:** With $m = 150$ pairwise tests, Bonferroni correction requires $\alpha / 150 \approx 0.00033$, which cannot be achieved without $N \ge 3000$ surrogates. The current discovery engine uses effect-size ranking ($z \ge 3.0$) and zero exceedances rather than strict FWER Bonferroni. This is acceptable for exploratory discovery, but **claims of Bonferroni-corrected significance at N=50 are statistically invalid**.

---

## 12. Baseline Validity

- **Random Walk Baseline:** The continuous random walk ($u \sim \mathcal{U}(-0.15, 0.15)$ each tick) is a legitimate, fair baseline. It moved $0.160\text{ m}$. Full CARL moved $0.688\text{ m}$ ($4.29\times$ margin). This margin is physically meaningful and statistically robust.
- **Zero-Action & Shuffled Baselines:** Zero-action moved $0.00048\text{ m}$ ($1,433\times$ ratio) and shuffled topology moved $0.00042\text{ m}$ ($1,638\times$ ratio). These large numbers are strawman ratios and must NOT be cited as intelligence multipliers.

---

## 13. Reproducibility

- **Git Commit:** `ef054099d4dc455ec9358d10c933fa2d8ecde64d`
- **File Integrity:** All source files (`carl_stage1_hal.py`, `carl_stage1_discovery.py`, `carl_stage1_organism.py`, `carl_stage1_adversarial_suite.py`) verified against recorded SHA-256 hashes.
- **Runtime:** `pytest tests/test_stage1_gate5_suite.py -v` executes 7/7 tests in **28.08 seconds** on Python 3.11 / MuJoCo 3.12.0 / PyTorch 2.6.0+cu124.

---

## 14. Remaining Uncertainties

1. **Non-Linear Dynamics:** How well will the linear predictive readout hold up when CARL interacts with obstacles, walls, or uneven terrain?
2. **True Closed-Loop Action Synthesis:** When `sensory_target_channel` is actively set (e.g., maximizing rangefinder distance or minimizing gyro yaw), does CARL navigate obstacles autonomously, or does the linear predictor fail to avoid collisions?
3. **Multi-Step Rollout:** Can the 1026-N reservoir state be harnessed to predict beyond 1 tick, or is CARL forever limited to instantaneous velocity extrapolation?

---

## 15. Required Repairs (For Stage 2 Pre-Requisites)

1. **Fix Slip Detector Normalization:** In `carl_stage1_organism.py`, set `self.baseline_prediction_error_norm` to the **mean Euclidean norm** of prediction errors over developmental babbling, or normalize `last_prediction_error_norm` by $\sqrt{25}$.
2. **Implement Explicit Sensory Objective in Benchmark:** Test 6 must explicitly call `org.set_sensory_goal(channel=15, mode="maximize")` (or forward distance sensor) so that `synthesize_action()` actively executes lines 226–244 and chooses actions via internal predictive scoring.
3. **Integrate Discovery Engine into Organism:** Move `infer_body_topology()` from the standalone discovery engine directly into `CarlStage1Organism` so the agent discovers its body internally rather than being audited by an external harness script.

---

## 16. Minimum Experiment to Close Remaining Gaps

**The 60-Second Closed-Loop Validation Experiment:**
1. Instantiate `CarlStage1Organism`.
2. Babble for 300 ticks to fit $W_{\text{pred}}$.
3. Normalize baseline error: `baseline = mean([norm(e_i)])`.
4. Place an obstacle in front of CARL.
5. Set sensory goal: `org.set_sensory_goal(channel=sonar_front, mode="maximize")`.
6. Run 100 ticks. Verify that `predict_next_observation(u=cand)` selects steering commands that turn away from the obstacle using only internal predictions.

---

## 17. Final One-Sentence Verdict

> **CARL Stage 1.5 has genuinely achieved tabula-rasa kinematic discovery, physically grounded causal isolation, and an internal 1-step linear inertia model, but its claimed "autonomous closed-loop action synthesis" and "traction-loss adaptation" were masked by an uncalled optimization branch and a vector-norm baseline mismatch.**

---
<!-- AUDIT_COMPLETE -->
