# CARL STAGE 2.1B-R.4: SMOOTH ANGULAR-GATED STEERING & HOMING CLOSURE
**Classification:** Pre-Experimental Architecture & Falsification Protocol  
**Subsystem:** Generative Spatial Self-Model / Closed-Loop Homing Action Selection  
**Author:** CARL Autonomous Development Laboratory  
**Date:** September 5, 2026  
**Status:** LOCKED & PRE-REGISTERED PRIOR TO AUTHORITATIVE RUN  

---

## 1. Executive Summary & Problem Formulation

In Stage 2.1B-R.3, CARL demonstrated robust spatial representation via dual-scale coprime continuous attractor networks (residual $< 10\,\text{mm}$, zero periodic aliasing) and learned forward translational grounding ($0.273\,\text{m} \to 0.207\,\text{m}$ mean unseen drift). However, individual evaluation revealed:
* Unseen pass rate: **2 of 5 passes (40%)**
* Seed 505: $0.220190\,\text{m}$ (failed gate by $+0.19\,\text{mm}$)
* Seed 303: $0.239396\,\text{m}$ (failed gate by $+1.94\,\text{cm}$)
* Seed 606: $0.262618\,\text{m}$ (failed gate by $+4.26\,\text{cm}$)

### Forensic Root Cause
Detailed kinematic and telemetry decomposition revealed:
1. **Longitudinal Stopping Accuracy:** Along the 1D projection of the return path, CARL stopped within **$\le 3.7\,\text{cm}$** of the origin line across all seeds (with four seeds stopping within $0.28\text{--}7.6\,\text{mm}$).
2. **Dominant Lateral Cross-Track Drift:** Over $90\%$ of final Euclidean drift was lateral offset ($10\text{--}26\,\text{cm}$) perpendicular to the return line.
3. **Controller Defect:** The legacy steering controller `compute_steering_action` commanded full forward cruise ($u_{\text{fwd}} = 0.12$) whenever `forward_alignment > 0` (any angle within $\pm 90^\circ$ of home). When turning $180^\circ$ to return home, the robot drove forward at maximum speed while perpendicular to its goal, generating a wide 150-tick lateral arc.

---

## 2. Mathematical Architecture: Smooth Angular-Gated Steering

To eliminate the lateral arcing wander without introducing hardcoded switches or threshold cliffs, we formulate **Smooth Angular-Gated Steering** via the continuous population vector of the Head Direction Ring Attractor:

### 2.1 Normalized Alignment Projection
Let $r_i$ and $\theta_i$ be the firing rates and preferred angles of the 64 neurons in the continuous attractor ring, and $\vec{d}_{\text{target}} = (-x_{\text{int}}, -y_{\text{int}})$ be the internal home vector.
The total population firing mass is:
$$R_{\text{total}} = \sum_{i=1}^{64} r_i$$

The normalized forward alignment cosine is:
$$\cos(\Delta \theta) = \frac{1}{\|\vec{d}_{\text{target}}\| \cdot R_{\text{total}}} \sum_{i=1}^{64} r_i \left(\cos\theta_i \cdot d_{\text{target}, x} + \sin\theta_i \cdot d_{\text{target}, y}\right)$$

### 2.2 Quadratic Velocity Modulation
The forward cruise command $u_{\text{fwd}}$ is smoothly modulated by the square of positive alignment:
$$u_{\text{fwd}} = u_{\text{max}} \cdot \left[\max\left(0, \cos(\Delta \theta)\right)\right]^2$$
where $u_{\text{max}} = 0.12$.

* **When facing away ($\Delta \theta \ge 90^\circ$):** $\cos(\Delta \theta) \le 0 \implies u_{\text{fwd}} = 0.0$. The robot executes a pure in-place rotational turn.
* **When angled ($\Delta \theta = 45^\circ$):** $\cos(45^\circ) = 0.707 \implies u_{\text{fwd}} = 0.12 \times 0.50 = 0.06$.
* **When aligned ($\Delta \theta \to 0^\circ$):** $\cos(0^\circ) = 1.0 \implies u_{\text{fwd}} = 0.12$. Full forward commute.

### 2.3 Steering Torque
Differential steering torque is driven by the population cross-product:
$$\tau_{\text{steer}} = \frac{1}{\|\vec{d}_{\text{target}}\| \cdot R_{\text{total}}} \sum_{i=1}^{64} r_i \left(\cos\theta_i \cdot d_{\text{target}, y} - \sin\theta_i \cdot d_{\text{target}, x}\right)$$
$$u_{\text{steer}} = \text{clip}\left(k_{\text{steer}} \cdot \tau_{\text{steer}}, -0.15, 0.15\right)$$

Wheel commands:
$$u_{\text{left}} = \text{clip}\left(u_{\text{fwd}} - u_{\text{steer}}, -0.15, 0.15\right)$$
$$u_{\text{right}} = \text{clip}\left(u_{\text{fwd}} + u_{\text{steer}}, -0.15, 0.15\right)$$

---

## 3. Mandatory 4-Condition Control Matrix

The experiment must be conducted across all 8 seeds (3 DEV + 5 UNSEEN) across 4 controlled conditions:

1. **Condition A (Smooth Angular-Gated Steering + Learned Translational Model):**
   Full R.4 substrate with quadratic forward modulation and frozen $k_{\text{trans}} = 1.1398\,\text{m/s}$.
2. **Condition B (Discontinuous Step Controller):**
   Legacy R.3 controller where $u_{\text{fwd}} = 0.12$ whenever $\cos(\Delta \theta) > 0$.
3. **Condition C (Naive Speed Baseline):**
   Smooth gating with naive motor constant $v = 1.200 \cdot u_{\text{fwd}}$.
4. **Condition D (Shuffled Sensor Control):**
   Negative control with sensory projections randomly permuted.

---

## 4. Pre-Registered Falsification & Gate Criteria

1. **Individual Gate:** Every single unseen seed (`[303, 404, 505, 606, 707]`) must achieve:
   $$\text{Final Drift} \le 0.220000\,\text{m}$$
   Pass rate requirement: **$5 / 5$ unseen passes ($100.0\%$)**.
2. **Ensemble Mean Gate:** Unseen ensemble mean drift must satisfy:
   $$\bar{D}_{\text{unseen}} \le 0.180\,\text{m}$$
3. **Causal Attribution:** Condition D must fail catastrophically ($> 1.0\,\text{m}$ drift), proving causal dependency on the spatial substrate.
4. **Zero Simulator Leakage:** Cognitive substrate receives only $s_t \in \mathbb{R}^{25}$ and $u_t \in [-1, 1]^6$.
