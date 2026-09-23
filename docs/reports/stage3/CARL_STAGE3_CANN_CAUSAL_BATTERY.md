# CARL-DX STAGE 3.1 — CANN CAUSAL COUPLING BATTERY PROTOCOL
**Version:** 1.0 (Pre-Registered Scientific Protocol)  
**Date:** September 12, 2026  
**Status:** **PRE-REGISTERED SPECIFICATION (FROZEN PRIOR TO EVALUATION)**  
**Target Architecture:** 2,114-Unit Neuromorphic Continuous Attractor (64 HD + 1,024 Grid + 1,026 Reservoir)  

---

## 1. Scientific Research Question

> *"Does the 2,114-unit neuromorphic continuous attractor network provide information that the CARL autonomous planner genuinely utilizes to synthesize actions, and does corrupting or removing this neural representation cause statistically and behaviorally measurable degradation?"*

### The Core Null Hypothesis
* **$H_0$ (Causal Inefficacy / Decorative Passenger):** Downstream action selection, trajectory clearance, and collision avoidance under the intact CANN do not differ significantly from ablations where CANN firing rates are zeroed, frozen, or shuffled.
  $$\mu(\text{Score}_{\text{Intact}}) = \mu(\text{Score}_{\text{Ablation}})$$
* **$H_1$ (Causal Coupling):** Intact CANN internal states provide indispensable orientation and metric spatial coordinate signals, such that removing or scrambling them causes statistically significant degradation ($p < 0.01$, Cohen's $d \ge 0.50$).
  $$\mu(\text{Score}_{\text{Intact}}) > \mu(\text{Score}_{\text{Ablation}})$$

---

## 1.1 Architectural Wiring Prerequisite (Fail-Closed Gate)

Prior to running the causal ablation battery, the cognitive architecture must be verified to ingest CANN state directly into the deliberation candidate trajectory evaluation pipeline:
```text
CANN state (HD Ring + Grid Torus)
       ↓
Trajectory / Candidate Action Evaluation (deliberation.select_action)
       ↓
Selected Motor Action u*
```
Testing ablations on a CANN whose output is routed solely to telemetry is scientifically invalid ($H_0$ would be accepted vacuously). Therefore:
1. Candidate trajectories projected against the allocentric occupancy grid are grounded using the continuous attractor's internal head direction $\hat{\theta}_{\text{CANN}}$ and metric displacement $(\hat{x}_{\text{CANN}}, \hat{y}_{\text{CANN}})$.
2. Candidate heading trajectories are scored against the 64-neuron HD attractor population vector:
   $$S_{\text{CANN}}(k) = \sum_{i=1}^{64} r_{\text{HD}, i} \cos(\theta_i - \theta_{k, H})$$
   where $\theta_i = \frac{2\pi i}{64} - \pi$, directly modulating candidate action utility.

---

## 2. Experimental Intervention Arms

The battery evaluates four strictly isolated computational conditions on the exact same physical robot and environments:

| Condition ID | Treatment | Implementation Mechanism | Expected Information Disruption |
| :--- | :--- | :--- | :--- |
| **ARM-A (Intact)** | Uncorrupted CANN | Standard ODE integration of HD ring, grid torus, and reservoir | Baseline ground truth |
| **ARM-B (Frozen)** | Static Attractor | Firing rates $\mathbf{r}$ clamped to initial spawn orientation/position for all $t > 0$ | Directional & translational velocity tracking halted |
| **ARM-C (Zeroed)** | Complete Blackout | Firing rate vectors set to $\mathbf{r} = \mathbf{0}$ | Total deprivation of internal neural coordinate frame |
| **ARM-D (Shuffled)**| Topological Scramble| Fixed deterministic permutation matrix $\mathbf{P}_{\text{ep}}$ per episode seed, held constant across all ticks | Spatial/topological correspondence destroyed; rate distribution & energy preserved without high-frequency white noise artifacts |

### Methodological Rigor on ARM-D (Frozen Permutation Schedule)
Randomly permuting the firing vector at every tick introduces high-frequency white noise perturbations at every timestep, which conflates "controller vulnerability to random sensor noise" with "causal necessity of the learned topological representation."
To isolate topological necessity, ARM-D uses a **pre-registered deterministic permutation schedule**:
$$\mathbf{r}_t^{\text{Shuffled}} = \mathbf{P}_{\text{ep}} \mathbf{r}_t^{\text{Intact}}$$
where $\mathbf{P}_{\text{ep}}$ is a fixed permutation matrix generated once per episode from the episode seed. This holds the total vector norm, unit firing rate distribution, and energy completely invariant, while permanently scrambling spatial adjacency and destroying the topological attractor manifold for the duration of the trial.

---

## 3. Pre-Registered Quantitative Metrics

Every trial records tick-by-tick telemetry across a standardized 100-episode test suite (5 unseen seeds $\times$ 4 environments $\times$ 5 trials):

### 3.1 Metric 1: Downstream Action Choice Divergence ($\Delta \mathbf{u}$)
Measures how much the selected motor command deviates when the CANN is ablated:
$$\Delta \mathbf{u}_{\text{ablation}} = \frac{1}{T} \sum_{t=1}^T \|\mathbf{u}_t^{\text{Intact}} - \mathbf{u}_t^{\text{Ablation}}\|_2$$
* **Passing Criterion:** $\Delta \mathbf{u}_{\text{ablation}} > 0.15$ (Proves the planner actively responds to the CANN state).

### 3.2 Metric 2: Trajectory Hull Clearance Degradation ($\Delta C_{\text{hull}}$)
Measures the loss of physical safety margin:
$$\Delta C_{\text{hull}} = \bar{C}_{\text{hull}}(\text{Intact}) - \bar{C}_{\text{hull}}(\text{Ablation})$$
* **Passing Criterion:** $\Delta C_{\text{hull}} \ge 0.05\text{ m}$ ($p < 0.01$).

### 3.3 Metric 3: Collision Rate Difference ($\Delta P_{\text{coll}}$)
$$\Delta P_{\text{coll}} = P_{\text{coll}}(\text{Ablation}) - P_{\text{coll}}(\text{Intact})$$
* **Passing Criterion:** In environments requiring heading coherence, $P_{\text{coll}}(\text{Ablation}) > P_{\text{coll}}(\text{Intact})$ with statistical significance ($p < 0.01$).

### 3.4 Metric 4: Counterfactual Trajectory Agreement
Measures rank correlation (Spearman's $\rho$) between candidate trajectory rankings under Intact vs Ablated CANN states.
* **Passing Criterion:** $\rho(\text{Intact}, \text{Ablated}) \le 0.70$ (Proves the CANN modulates candidate rankings).

---

## 4. Pre-Registered Statistical Power & Protocol

* **Sample Size:** $N = 100$ paired episodes per condition ($4 \times 100 = 400$ total evaluation episodes).
* **Test Partitions:**
  * **Seeds:** Unseen test seeds `[1001, 1002, 1003, 1004, 1005]`.
  * **Environments:** 4 certified challenge layouts (Left Trap, Right Trap, T-Junction, Corridor Slit).
* **Statistical Tests:**
  * Two-tailed Wilcoxon signed-rank test for paired continuous metrics ($\Delta \mathbf{u}$, $\Delta C_{\text{hull}}$).
  * McNemar's test for paired collision/success outcomes.
* **Significance Ceiling:** $\alpha = 0.01$ (with Bonferroni correction for multi-arm comparison: $\alpha_{\text{adjusted}} = 0.0033$).
* **Effect Size Threshold:** Minimum Cohen's $d \ge 0.50$ (medium-to-large effect size).

---

## 5. Mandatory Fail-Closed Policy

If the intact CANN does **not** demonstrate statistically significant superiority over ARM-B, ARM-C, and ARM-D ($p \ge 0.01$ or Cohen's $d < 0.50$):
1. **STAGE 3.1 FAILS CLOSED.**
2. The CANN is declared a *decorative passenger* in the tested configuration.
3. No progress to Stage 3.2 or Stage 3.3 is permitted until the architecture is remediated to enforce true causal coupling.
