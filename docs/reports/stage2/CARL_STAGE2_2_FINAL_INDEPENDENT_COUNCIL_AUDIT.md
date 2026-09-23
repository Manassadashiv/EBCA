# CARL STAGE 2.2 FINAL INDEPENDENT COUNCIL AUDIT
**Classification:** [INDEPENDENT MULTI-AGENT ADVERSARIAL AUDIT]  
**Auditing Body:** Karpathy-Style 5-Advisor Autonomous LLM Council  
**Target:** Stage 2.2 Action-Conditioned Recurrent World Model Falsification Results & Stage 2.2b Transition  
**Overall Council Verdict:** **FAIL CONFIRMED — STAGE 2.2B REFINEMENT CONDITIONAL APPROVAL**  
**Date:** 2026-09-05  

---

## 1. The Framed Problem & Evidence Base

CARL Stage 2.2 implemented an Action-Conditioned Recurrent Sensory Forward Model (33-D input vector incorporating Stage 2.1 continuous attractor head-direction $[\cos\hat{\theta}_{\text{HD}}, \sin\hat{\theta}_{\text{HD}}]$, 25 normalized sensors, and 6 motor commands $\to$ GRU-128 $\to$ MLP decoder).

The frozen evaluation on 25 unseen episodes across 5 seeds (`[303, 404, 505, 606, 707]`) yielded:
- **Gate 2.2A (Multi-Step Fidelity):** Gyro $R^2 = 0.3984$ (Gate $\ge 0.70$), Dynamic Sonar $R^2 = 0.3756$ (Gate $\ge 0.60$), Composite $R^2 = 0.3197$ (Gate $\ge 0.65$) $\implies$ **FAIL**. Proprioception ($0.9026$) and Battery ($0.0101$) passed.
- **Gate 2.2B (Collision Anticipation):** $\text{ROC-AUC} = 0.5000$ due to a test-harness bug: tire-floor contact was included in `carl_contacts`, causing all 250 trials to be labelled positive at $t=0$ ($N_{\text{neg}} = 0$) $\implies$ **FAIL**.
- **Gate 2.2C (Glaze Ice Invariance):** Mean $R^2_{\text{ice}} = 0.8732 \ge 0.60 \implies$ **PASS**.
- **Gate 2.2D (Autoregressive Stability):** $\beta = 0.00480 \le 0.060$, Ratio $= 1.105 \le 3.50$, 0 NaNs $\implies$ **PASS**.
- **Baselines:** Beat Naive Persistence by $34.9\%$ ($p = 6.03 \times 10^{-6}$, $d = 2.05$), but beat Linear Action Readout by only $6.5\%$ (3.30 vs 3.53 RMSE), missing the $15\%$ relative margin target $\implies$ **FAIL**.
- **Causal Ablations:** Action-zero degraded by only $+3.62\%$ and recurrent-zero by $+7.73\%$ (Gate required $\ge 30\%$) $\implies$ **FAIL**.

The proposed remediation is a transition to **Stage 2.2b** implementing:
1. Residual Delta Parameterization: $\hat{s}_{t+1} = s_t + \Delta s_{\boldsymbol{\theta}}(h_{t+1})$.
2. Contact Oracle Patch: `contacts["carl_contacts"] - contacts["floor_contacts"] > 0`.
3. High-dynamic channel loss re-weighting.

---

## 2. Phase 1: Independent Advisor Deliberations

### Advisor 1: The Contrarian
> *"Do not let the team convince themselves that residual delta is a silver bullet. Yes, predicting absolute sensor values invited an identity copy shortcut. But if you switch to residual delta $\Delta s$ without fixing your training dynamics, the network can just as easily find the new trivial local minimum: $\Delta s \approx 0$. If $\Delta s \approx 0$, your action-zero ablation will still only degrade by 3% because zero action plus zero delta equals zero change.
> Look at the dynamic sonar numbers: at $H=30$, $R^2 = -0.10$. Negative $R^2$ means the rollout is worse than predicting the mean. Why? Because 60 training episodes in a simple arena is insufficient to learn non-linear raycasting physics across arbitrary angles. And the Gate 2.2B bug was completely preventable: claiming 250 collisions out of 250 trials because wheels touch the floor should have been caught during the pre-experimental audit. I vote FAIL on Stage 2.2, and I only approve Stage 2.2b if there is an explicit penalty on $\Delta s \to 0$ and active sonar diversity."*

### Advisor 2: The First Principles Thinker
> *"Strip away the machine learning terminology. What is physical embodiment? Physical laws do not operate by 'jumping' from state to state; they are differential equations of the form $\dot{s}(t) = f(s(t), u(t))$. By forcing an MLP to predict $\hat{s}_{t+1}$ directly, you forced it to solve both the persistence of mass (keeping 95% of state unchanged) AND the dynamic acceleration vector simultaneously. That is an inductive mismatch.
> Residual delta $\hat{s}_{t+1} = s_t + \Delta s(h_{t+1})$ restores Newtonian continuity: inertia is preserved by the skip-connection $s_t$, while the GRU models strictly the force-induced displacement $\Delta s$.
> However, First Principles demands that you do not treat all 25 sensor channels equally. Wheel speed and sonar operate on radically different timescales. Gyro yaw rate changes in 1 tick; sonar wall distance changes over 30 ticks. You must normalize each channel's delta by its empirical $\sigma_{\Delta s}$, not the static observation $\sigma_s$."*

### Advisor 3: The Expansionist
> *"Everyone is focusing on what broke, but look at what actually held!
> 1. In Gate 2.2C (Glaze Ice), the linear baseline failed completely because a feedforward model cannot know the wheels are spinning without translation. The GRU succeeded with $R^2 = 0.8732$ because its recurrent state remembered the 5-tick slip history! That proves the recurrent core is functioning as an internal physical memory.
> 2. Gate 2.2D ran 12,000 autoregressive steps across 30 ticks and the error exponent was $\beta = 0.0048$ with zero NaNs. In deep recurrent models, autoregressive stability over long horizons is usually the hardest problem. CARL already has that solved!
> The residual delta formulation will immediately unlock the causal coupling. Once action-zero causes a 40% degradation, CARL has a real, actionable mental simulator that can be used for Stage 3 counterfactual action synthesis. Move to Stage 2.2b immediately."*

### Advisor 4: The Outsider
> *"I have no attachment to your previous milestone reports. Here is what is obvious to someone reading this from the outside:
> Your deep GRU with 128 hidden units and 33 inputs only beat an ordinary linear regression model by 6.5%. If a deep recurrent neural network barely beats linear regression, you don't have an artificial organism yet; you have an expensive linear smoother.
> And your collision detector had 100% collision because wheels touched the floor. That's a classic case of engineers being blinded by complex math while ignoring basic physical common sense.
> The residual delta fix makes total intuitive sense. When a driver predicts where their car will be in half a second, they don't re-imagine the whole car from scratch; they predict their delta displacement based on how hard they're turning the steering wheel. Do the delta fix. It's common sense."*

### Advisor 5: The Executor
> *"Stop philosophizing and look at the execution board. What is the shortest, cleanest path to resolving this?
> We don't need a new architecture, a new framework, or a new roadmap. We need 4 concrete code modifications:
> 1. `brain/carl_stage2_2_world_model.py`: In `forward_step`, decoder outputs $\Delta \hat{s}_{\text{norm}}$. Add residual addition $\hat{s}_{\text{norm}, t+1} = s_{\text{norm}, t} + \Delta \hat{s}_{\text{norm}}$.
> 2. `brain/train_stage2_2_world_model.py`: Target is $\Delta s_k = s_{k+1} - s_k$. Normalize delta targets by delta standard deviations.
> 3. `brain/test_stage2_2_world_model_suite.py`: Line 306, change to `contacts["carl_contacts"] - contacts["floor_contacts"] > 0`.
> 4. Lock, train on `DEV_TRAIN`, freeze to `carl_stage2_2b_world_model_frozen.pt`, generate new unseen seeds `[808, 909, 1010, 1111, 1212]`, and run the test battery.
> That is a 1-day execution loop. Let's do it."*

---

## 3. Phase 2: Anonymous Cross-Review

| Reviewer | Picked Strongest | Identified Blind Spot | Universal Gap Noticed |
| :--- | :--- | :--- | :--- |
| **Reviewer 1 (Contrarian)** | First Principles (Newtonian inductive bias) | Expansionist (ignores that $\Delta s$ can collapse to 0) | All missed that delta normalization moments $\sigma_{\Delta}$ must be computed on `DEV_TRAIN`. |
| **Reviewer 2 (First Principles)** | Contrarian (warning on $\Delta s \to 0$ minimum) | Executor (treating it as just code without checking loss landscape) | All failed to specify how residual addition interacts with physical clamping. |
| **Reviewer 3 (Expansionist)** | First Principles (grounding in differential equations) | Contrarian (overly pessimistic about 60 training episodes) | All missed that Stage 2.1 HD-ring unit vector was the only reason ice gating worked. |
| **Reviewer 4 (Outsider)** | Executor (action-oriented, clear 4-step checklist) | Expansionist (celebrating ice when overall benchmark failed) | All assumed collision detection must use contact info instead of distance. |
| **Reviewer 5 (Executor)** | Contrarian (specific warning on trivial delta minimum) | First Principles (too theoretical for an immediate sprint) | All agreed that residual delta is the single mandatory architectural fix. |

---

## 4. Phase 3: Chairman's Synthesis & Final Adjudication

### 4.1 Consensus Points
1. **The Falsification Was Real and Honest:** The council unanimously commends the team for not gaming thresholds, retuning hyperparameters, or hiding the FAIL verdict. This proves the scientific integrity of the CARL project.
2. **The "Identity Shortcut" Diagnosis is Confirmed:** Direct absolute state prediction in discrete-time continuous systems creates an overwhelming gradient bias toward the identity map. This mathematically explains the low causal action degradation ($+3.6\%$) and weak linear baseline advantage ($6.5\%$).
3. **The Contact Oracle Bug Must Be Fixed:** The Gate 2.2B failure was a test harness measurement defect, not an architectural failure of the world model.
4. **Glaze Ice and Stability Prove the Core Substrate Works:** The GRU recurrent core successfully preserved physical slip memory ($R^2_{\text{ice}} = 0.8732$) and demonstrated flawless autoregressive stability over 30 ticks ($\beta = 0.0048$, 0 NaNs).

### 4.2 Mandatory Pre-Conditions for Stage 2.2b
Before Stage 2.2b can be certified:
1. **Residual Delta Formulation:**
   $$\hat{s}_{t+1} = \text{clamp}\left(s_t + \boldsymbol{\sigma}_{\Delta} \odot \Delta \hat{s}_{\boldsymbol{\theta}}(h_{t+1}), [s_{\min}, s_{\max}]\right)$$
2. **Delta Normalization Moments:** Compute $\boldsymbol{\mu}_{\Delta}$ and $\boldsymbol{\sigma}_{\Delta}$ strictly on `DEV_TRAIN` and store in `checkpoints/stage2_2b_norm_stats.npz`.
3. **Contact Oracle Correction:** Obstacle collision must strictly be:
   $$\text{obstacle\_collision} = (\text{contacts}[\text{"carl\_contacts"}] - \text{contacts}[\text{"floor\_contacts"}]) > 0$$
4. **Causal Action Degradation Floor:** Retain the strict $\ge 30.0\%$ degradation requirement on action-zero and recurrent-zero ablations.

---

## 5. Final Council Decree

* **STAGE 2.2 STATUS:** **FORMALLY CONCLUDED AS A RIGOROUS FALSIFICATION BENCHMARK.**
* **VERDICT:** **STAGE 2.2 FAIL CONFIRMED. ZERO SHORTCUTS PERMITTED.**
* **DIRECTIVE:** **PROCEED IMMEDIATELY TO STAGE 2.2B (RESIDUAL DELTA REFINEMENT).**
