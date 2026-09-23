# CARL Stage 2.3-R1: Full Closed-Loop Action Deliberation Specification

**Document Identifier:** `CARL-STAGE2_3_R1-SPEC-2026-09-07`  
**Milestone:** Stage 2.3-R1 Full Action Deliberation  
**Standard:** Zero-Trust Falsification, Unprivileged Internal Localization, Multi-Environment Evaluation  
**Status:** **LOCKED TECHNICAL SPECIFICATION**  

---

## 1. Scientific Motivation & Scope Demarcation

Stage 2.3-MVE demonstrated that internal prospective simulation causally prevents collisions in an asymmetric trap. However, MVE relied on three simplifying constraints:
1. Only 3 discrete pre-scripted action choices (`fwd`, `left`, `right`).
2. A single spatial trap configuration.
3. Ground-truth pose injection from simulator `qpos`.

**Stage 2.3-R1 removes all three simplifications.** It evaluates whether an embodied agent can:
- Generate a diverse, continuous candidate action space ($K = 24$ arcs).
- Navigate purely via internal dead-reckoned localization without reading simulator coordinates.
- Generalize across 4 structurally distinct spatial hazard layouts.
- Maintain high causal prediction fidelity (Predict $\to$ Act $\to$ Compare) in real-time ($\le 50\,\text{ms}$).

---

## 2. Mathematical Formalism

### 2.1 Continuous Action Space Parameterization ($K = 24$ Arcs)
At each decision tick $t$, the candidate generator synthesizes $K = 24$ distinct motor action sequences $U^{(k)} \in \mathbb{R}^{H \times 6}$ over horizon $H = 10$ ($300\,\text{ms}$ at $\Delta t = 0.030\,\text{s}$):

$$\mathcal{U}_{\text{cand}} = \{ U^{(1)}, U^{(2)}, \dots, U^{(24)} \}$$

The candidate fan spans five distinct behavioral classes:
1. **Curvature Fan (14 arcs):** Forward drive with differential wheel speeds:
   $$u_L = v_{\text{nom}} - \frac{b}{2} \omega_k, \quad u_R = v_{\text{nom}} + \frac{b}{2} \omega_k$$
   where $v_{\text{nom}} \in \{0.4, 0.7\}$, $\omega_k \in \{-1.2, -0.8, -0.5, -0.2, +0.2, +0.5, +0.8, +1.2\}$.
2. **High-Speed Forward & Trims (4 arcs):** Straight and slight-bias arcs ($u = [0.8, 0.8]$, $[0.8, 0.75]$, $[0.75, 0.8]$, $[0.6, 0.6]$).
3. **In-Place Pivots (3 arcs):** Pure rotational maneuvers without forward displacement:
   - Hard Left Pivot: $u = [-0.6, 0.6]$
   - Hard Right Pivot: $u = [0.6, -0.6]$
   - Moderate Left Pivot: $u = [-0.35, 0.35]$
4. **Reverse Escape Maneuvers (3 arcs):** Backward curving trajectories for stuck recovery:
   - Reverse Left: $u = [-0.4, -0.15]$
   - Reverse Right: $u = [-0.15, -0.4]$
   - Straight Reverse: $u = [-0.35, -0.35]$

### 2.2 Unprivileged Internal Dead-Reckoning Localization
The agent is supplied its initial spawn coordinates $S_0 = (x_0, y_0, \theta_0)$ at $t = 0$. Thereafter, simulator state `hal.data.qpos` is **STRICTLY FORBIDDEN** from reaching the decision policy.

At each step $t$, the internal pose estimate $\hat{\mathbf{p}}_t = (\hat{x}_t, \hat{y}_t, \hat{\theta}_t)^T$ updates via the grounded kinematic self-model:
$$\hat{\theta}_{t+1} = \hat{\theta}_t + \omega_{z, \text{gyro}} \cdot \Delta t$$
$$\hat{v}_{t+1} = \frac{r}{2} (\dot{\phi}_R + \dot{\phi}_L) \cdot \gamma_{\text{traction}}$$
$$\hat{x}_{t+1} = \hat{x}_t + \hat{v}_{t+1} \cos(\hat{\theta}_{t+1}) \Delta t$$
$$\hat{y}_{t+1} = \hat{y}_t + \hat{v}_{t+1} \sin(\hat{\theta}_{t+1}) \Delta t$$

### 2.3 Prospective Clearance Evaluation & Utility
Each candidate trajectory $k \in \{1 \dots K\}$ is unrolled in imagination over $H = 10$ steps:
$$\{\hat{\mathbf{p}}_{t+1}^{(k)}, \dots, \hat{\mathbf{p}}_{t+H}^{(k)}\} = \text{MentalUnroll}(\hat{\mathbf{p}}_t, U^{(k)})$$

Clearances are queried from the allocentric occupancy grid:
$$C^{(k)} = \text{SpatialOccupancyMemory.query\_clearance}(\mathcal{M}_{\text{arena}}, \hat{\mathbf{p}}_{1:H}^{(k)})$$

The prospective utility $\mathcal{J}(k)$ balances safety, corridor clearance, forward progression, and control effort:
$$\mathcal{J}(k) = w_{\text{front}} \cdot \min C_{H, 6:9}^{(k)} + w_{\text{mean}} \cdot \bar{C}_H^{(k)} + w_{\text{fwd}} \cdot \Delta d_{\text{fwd}}^{(k)} - w_{\text{coll}} \cdot \mathbb{I}\Big[\min C_{1:H, 6:9}^{(k)} < d_{\text{safe}}\Big] - w_{\text{rev}} \cdot \mathbb{I}[v_k < 0]$$

Parameters: $w_{\text{front}} = 4.0$, $w_{\text{mean}} = 2.0$, $w_{\text{fwd}} = 2.5$, $w_{\text{coll}} = 800.0$, $d_{\text{safe}} = 0.22\,\text{m}$, $w_{\text{rev}} = 15.0$.

---

## 3. The 4 Spatial Hazard Environments

| Layout | Environment Name | Arena Geometry & Trap Mechanism | Why Reflex Fails |
| :--- | :--- | :--- | :--- |
| **Layout 1** | **Asymmetric Left Trap** | Facing South toward `lwall_h_2_0` ($y = -0.90$) with East wall `lwall_v_2_0` ($x = -2.70$) | Naive left-turn reflex steers directly into the East wall. |
| **Layout 2** | **Asymmetric Right Trap** | Facing South toward `lwall_h_1_0` ($y = -0.90$) with West wall `lwall_v_0_0` ($x = -4.50$) | Mirror trap: turning right collides with West wall. Proves deliberator has no hardcoded turning bias. |
| **Layout 3** | **T-Junction Dead-End** | Facing West into flat vertical divider (`lwall_v_1_0` at $x = -3.60$), North and South corridors open | Forward drive collides; both Left and Right are valid evasions. |
| **Layout 4** | **Narrow Choke Passage** | Approaching narrow slit between horizontal dividers ($y \in [-0.15, +0.15]$) | Requires smooth centering; aggressive turns clip the slit corners. |

---

## 4. The 5 Experimental Conditions

1. **`deliberative` (Ours)**: $K = 24$ continuous candidate unrolls, bilinear spatial memory clearance queries, unprivileged internal dead reckoning.
2. **`reflex`**: Scripted reactive baseline ("If front sonar $< 0.50\,\text{m}$, turn left").
3. **`amnesic`**: Deliberation engine running with erased spatial memory ($\mathcal{M}_{\text{env}} = \mathbf{0}$).
4. **`random`**: Stochastic selection among the $K = 24$ continuous action candidates.
5. **`potential_field`**: Classical continuous reactive baseline computing repulsive force vectors from instantaneous sonar rays without lookahead.

---

## 5. Quantitative Acceptance Criteria

| ID | Criterion | Pre-Registered Threshold | Purpose |
| :--- | :--- | :---: | :--- |
| **CRIT-1** | Collision Reduction vs Reflex | **$\ge 60.0\%$** | Demonstrates clear superiority over reactive baseline across diverse traps. |
| **CRIT-2** | Collision Reduction vs Random | **$\ge 60.0\%$** | Demonstrates non-stochastic, directed avoidance. |
| **CRIT-3** | Collision Reduction vs Potential Field | **$\ge 25.0\%$** | Proves prospective lookahead outperforms memoryless continuous vector steering. |
| **CRIT-4** | Causal Prediction Alignment | **$\ge 85.0\%$** | Physical clearance at $t+1$ within $\pm 0.25\,\text{m}$ of predicted clearance. |
| **CRIT-5** | Real-Time Latency Budget | **p95 $\le 50.0\,\text{ms}$** | Real-time robotics viability on 16-thread CPU. |
| **CRIT-6** | Statistical Significance | **$p < 0.01$, $d \ge 0.80$** | Independent two-sample $t$-test on survival duration vs all controls. |
| **CRIT-7** | Zero Pose Injections | **100% compliant** | `hal.data.qpos` never passed to decision policy during active trials. |
