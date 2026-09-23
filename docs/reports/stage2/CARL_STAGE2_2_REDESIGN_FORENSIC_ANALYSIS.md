# CARL STAGE 2.2: REDESIGN FORENSIC ANALYSIS
## Scientific Post-Mortem of Failed World-Model Evaluation & Epistemic Decoupling
**Author:** Antigravity AI Research Orchestrator  
**Classification:** [FORENSIC POST-MORTEM & EPISTEMIC RESTRUCTURING]  
**Status:** **AUTHORITATIVE SCIENTIFIC ANALYSIS (NO RETROACTIVE SUCCESS CLAIMS)**  
**Milestone:** Stage 2.2 Post-Failure Diagnostic  
**Date:** September 5, 2026  
**Target Repository:** `d:/ebca`  

---

## 1. Executive Summary & Epistemic Context

The initial evaluation of CARL Stage 2.2 (Action-Conditioned Recurrent Sensory Forward Model) was executed against pre-registered gates and resulted in an unambiguous, formal **FAIL** (passing only 2 of 6 pre-registered batteries). A subsequent 4-condition spatial grounding benchmark was conducted to test whether adding Stage 2.1 spatial coordinates ($[x, y]$ toroidal grid phase) and head direction ($[\cos \theta, \sin \theta]$) directly to the network resolved the failure. That test revealed that spatial coordinates yielded **zero statistically significant improvement** ($p = 0.8167$, $d = -0.165$).

This document performs an exhaustive, intellectually honest forensic post-mortem of the entire Stage 2.2 architecture, experimental design, datasets, and diagnostic conclusions. It explicitly distinguishes between:
1. What was empirically proven by data,
2. What was flawed in the diagnostic harness,
3. What was merely an unproven hypothesis, and
4. What structural gaps in the formulation must be addressed before any code is written.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             STAGE 2.2 FAILURE: THE EPISTEMIC REALITY                           │
├────────────────────────────────┬───────────────────────────────────────────────────────────────┤
│ EMPIRICAL FACT (OBSERVED)      │ The GRU decoder learned temporal persistence (s_{t+1} ≈ s_t).  │
│                                │ It ignored motor actions (+0.4% surge when zeroed).           │
│                                │ Dynamic sonar R² collapsed to negative by H=30.               │
│                                │ Appending (x, y, θ) coordinates produced no measurable gain.  │
├────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ ERRONEOUS INFERENCE (CORRECTED)│ "Therefore, residual prediction (Δs) will solve Stage 2.2."   │
│                                │ ➔ UNPROVEN HYPOTHESIS. Δs kills the identity copy shortcut,   │
│                                │   but cannot predict obstacles if coordinates lack map context.│
├────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ MISSING ARCHITECTURAL ELEMENT  │ (x, y) coordinates relative to an arbitrary spawn do NOT      │
│                                │ constitute an allocentric map of walls and obstacles.         │
│                                │ Environmental memory / structure was completely missing.      │
└────────────────────────────────┴───────────────────────────────────────────────────────────────┘
```

---

## 2. Forensic Breakdown of the Prior Experiment

### Part A: Which Parts of the Old Experiment Were Valid?

The prior experiment maintained several rigorous methodological invariants that must be preserved in all future iterations:

1. **Strict Anti-Cheat AST Static Analysis & Subprocess Poisoning:**
   - The test script `tests/test_stage2_2_anti_cheat_isolation.py` recursively scanned all reachable code from `rollout_mental_trajectory` and confirmed zero imports of `mujoco` and zero access to internal simulator pointers (`mj_ray`, `data.qpos`, `data.qvel`, `data.contact`).
   - The sandbox execution in a poisoned subprocess with `sys.modules['mujoco'] = None` proved that mental rollouts executed strictly on neural tensor state.
2. **Strict Dataset Partitioning & Cryptographic Immutability:**
   - The separation between training (`seeds [42, 101, 202]`) and unseen evaluation (`seeds [303, 404, 505, 606, 707]`) was preserved.
   - Datasets were partitioned and hashed before evaluation, guaranteeing that test trajectories were never exposed during model selection or gradient updates.
3. **Multi-Horizon Autoregressive Protocol ($H \in \{1, 5, 10, 15, 30\}$):**
   - Evaluating recursive closed-loop unrolling ($\hat{s}_{t+k} = f(\hat{s}_{t+k-1}, u_{t+k-1})$) correctly exposed long-horizon error accumulation and prevented teacher-forced inflation.
4. **Strong Body Model Baseline:**
   - The model accurately tracked internal wheel proprioception ($R^2 \approx 0.86\text{--}0.90$) and adapted to low-friction glaze ice ($\mu = 0.005$, $R^2_{\text{ice}} = 0.8732$). The body self-model substrate in Stage 1 and Stage 2.1 remains physically sound.

---

### Part B: Which Parts Were Diagnostically Broken?

Four distinct components of the experiment were diagnostically compromised:

1. **The Gate 2.2B Collision Oracle Defect (False Positives):**
   - In `brain/test_stage2_2_world_model_suite.py`, the physical collision ground truth checked `contacts["carl_contacts"] > 0` without subtracting `contacts["floor_contacts"]`.
   - Because CARL's wheels continuously touch the ground, all 250 evaluation trials were classified as "collided" at tick 0. This eliminated all negative examples ($N_{\text{neg}} = 0$), collapsing the ROC-AUC calculation to a degenerate $0.5000$. This was a software harness bug, not a neural failure.
2. **Sonar Saturation Camouflage:**
   - CARL's 15 sonars saturate at $5.0\,\text{m}$. In a $6\text{m} \times 6\text{m}$ arena, when CARL is in the central region, the majority of sonar beams return exactly $5.0\,\text{m}$.
   - Evaluating "All Sonars" gave an inflated $R^2 \approx 0.53$ simply because predicting $5.0\,\text{m}$ constantly scores well on saturated beams.
   - Only the dynamic return filter ($s < 4.5\,\text{m}$) revealed the collapse ($R^2 = 0.28$), but the training loss was still dominated by the saturated beams.
3. **Causal Decoupling from the Action Bus:**
   - The GRU received $x_t = [s_t; \mathbf{v}_{\text{HD}, t}; u_t] \in \mathbb{R}^{33}$.
   - Because $s_t$ changes slowly across $30\,\text{ms}$ ticks, the gradient of the MSE loss with respect to $s_t$ was orders of magnitude larger than the gradient with respect to $u_t$.
   - The optimizer quickly learned to route $s_t$ directly to the output via the recurrent state, virtually zeroing out the weights assigned to $u_t$. This resulted in the catastrophic $+0.4\%$ action-zero degradation (Figure 4).
4. **The Arbitrary Spawn / Relative Coordinate Confound:**
   - In `brain/carl_stage2_spatial_data_collector.py`, CARL was spawned at random coordinates $(x_0, y_0) \in [-2.0, 2.0]^2$.
   - However, the grid attractor `multi_grid.reset_at_birthplace()` always initialized displacement to $(0.0, 0.0)$ at spawn.
   - Thus, a coordinate of $(+1.0, +1.0)$ in one episode was in the room center, while in another episode it was centimeters from the boundary wall.
   - **Feeding this coordinate into the network gave it zero allocentric anchor to the physical walls of the arena!**

---

### Part C: Which Conclusions Are Actually Supported by Data?

The empirical data directly and indisputably supports the following:

1. **Direct-State Prediction Collapses to Temporal Persistence:**
   - When trained to output $\hat{s}_{t+1}$, recurrent neural networks optimize for identity pass-through. The model acts as a leaky integrator / buffer rather than a dynamic simulator.
2. **Causal Action Decoupling:**
   - Under direct MSE state loss, action conditioning fails ($+0.41\%$ degradation under $u=0$). The model is not an action-conditioned world model.
3. **Spatial Coordinates Alone Do Not Improve Direct-State Prediction:**
   - Feeding $[x, y, \cos\theta, \sin\theta]$ to the direct-state GRU resulted in an identical error profile ($3.3966$ vs $3.3989$, Wilcoxon $p = 0.8167$).

---

### Part D: Which Conclusions Were Only Hypotheses? (Critical Epistemic Correction)

The prior report made two unwarranted inferential leaps that must be formally corrected:

#### ❌ Unwarranted Leap 1: *"Residual prediction ($\Delta s$) will fix the world model."*
* **The Reality:** Predicting $\Delta s_t = s_{t+1} - s_t$ mathematically removes the trivial constant identity output ($\Delta s = 0$ carries zero predictive value for dynamic changes). **However, that does NOT mean the network will successfully predict sonar.** 
* Predicting $\Delta s_{\text{sonar}}$ when moving forward requires knowing whether an obstacle exists in front of the robot. If that spatial knowledge is missing, $\Delta s$ prediction will simply predict the average rate of approach or collapse to zero.
* **Status:** Residual delta prediction is an **experimental intervention to be tested**, not a proven solution.

#### ❌ Unwarranted Leap 2: *"Stage 2.1 spatial state contains the missing environmental information."*
* **The Reality:** Stage 2.1 provides dead-reckoned displacement relative to where the robot began integrating ($[x_{\text{rel}}, y_{\text{rel}}]$) and head direction ($\theta$).
* A coordinate pair $(x, y)$ contains **zero environmental information** about where walls, pillars, or obstacles are located, unless the model has learned a persistent mapping between coordinates and physical structures.
* Without landmark calibration or persistent spatial memory, $(x, y)$ is merely two abstract numbers.
* **Status:** The presence of predictive environmental information in Stage 2.1 is an **untested hypothesis that our benchmark showed is currently absent or inaccessible**.

---

### Part E: Systematic Taxonomy of Root Causes

The failure of Stage 2.2 is not attributable to a single defect, but to a multi-layer misalignment:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           MULTI-LAYER ROOT CAUSE TAXONOMY                                     │
├──────────────────────────┬─────────────────────────────────────────────────────────────────────┤
│ 1. TARGET FORMULATION    │ Predicting absolute state s_{t+1} allowed MSE loss to be dominated  │
│                          │ by the identity copy shortcut.                                      │
├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
│ 2. INPUT REPRESENTATION  │ Grid state was displacement from arbitrary spawn, lacking an        │
│                          │ allocentric anchor to arena boundaries or obstacles.               │
├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
│ 3. ENVIRONMENTAL MEMORY  │ The architecture lacked any mechanism to store, retrieve, or update │
│                          │ an internal map of where obstacles exist in the environment.        │
├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
│ 4. DATASET BIAS          │ Trajectories contained high fractions of saturated open-space       │
│                          │ sonars (5.0m) and smooth drift, starving collision gradients.       │
├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
│ 5. EVALUATION HARNESS    │ Collision oracle had a ground-contact defect; actions were not      │
│                          │ ablated with sign inversion or counterfactual branch testing.       │
└──────────────────────────┴─────────────────────────────────────────────────────────────────────┘
```

---

## 3. The Path Forward

To achieve genuine scientific validation, we must:
1. Freeze existing Stage 2.2 results as a definitive historical baseline.
2. Establish a new pre-experimental specification with strict hypothesis testing.
3. Design a diagnostic experiment that systematically separates:
   - Temporal persistence,
   - Body/self dynamics,
   - Action-conditioned dynamics,
   - Spatial grounding, and
   - Environmental structure/memory.
4. Test residual prediction ($\Delta s$) as an experimental hypothesis alongside direct-state prediction.
5. Require explicit disambiguation and counterfactual divergence tests before declaring success.
