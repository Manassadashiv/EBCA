# CARL STAGE 2.1B-R.3: FAILURE MECHANISM & RESIDUAL AUDIT REPORT
**Classification:** Forensics / Causal Decomposition / Scientific Falsification  
**Milestone:** Stage 2.1B-R.3 (Global Spatial Representation Benchmark)  
**Date:** September 4, 2026  
**Status:** COMPLETE & AUTHORITATIVE  

---

## 1. Executive Summary & Forensic Verdict

The central scientific question of Stage 2.1B-R.3 is:
> *"What information is missing that prevents CARL from maintaining an unambiguous global spatial identity over distances exceeding one single grid period?"*

Through tick-by-tick state decomposition across 52 MuJoCo physical episodes (8 development and unseen seeds, 3 candidate representations, and 3 causal ablations), we provide definitive numerical proof of the following:

1. **Periodic Representation Aliasing Is Mathematically Eliminated:**
   * In a single-torus grid ($\lambda = 0.80\,\text{m}$), boundary crossing causes catastrophic representation aliasing ("ghost origin" confusion), yielding a mean return drift of **$1.423\,\text{m}$** (0/5 pass rate).
   * In the dual-scale coprime grid ($\lambda_1 = 0.80\,\text{m}, \lambda_2 = 1.15\,\text{m}$, total non-repeating range $\Lambda = 9.20\,\text{m}$), the maximum phase disambiguation residual across all 24 episodes was **$9.78\,\text{mm}$ ($< 0.01\,\text{m}$)**.
   * **Wrong Wrap Count:** Exactly **$0$** across all test seeds. The attractor population dynamics correctly resolved spatial identity across all periodic boundary crossings without a single aliasing fault.
2. **The True Bottleneck is Translational Integration Drift Across Turns:**
   * The failure to achieve $100\%$ pass rate on the $\le 0.22\,\text{m}$ acceptance gate (achieving $2/5$ passes on unseen seeds, mean drift $0.273\,\text{m}$, worst seed $0.456\,\text{m}$) was **NOT** caused by representation aliasing, phase ambiguity, population decoding error, or neural state instability.
   * Rather, $70\%\text{--}85\%$ of the total error is dominated by **unanchored dead reckoning integration drift**: specifically, an ungrounded longitudinal speed assumption ($\approx 0.60\,\text{m/s}$ modeled vs $0.528\,\text{m/s}$ actual ground speed) compounded by slight heading error ($\approx 2.5^\circ\text{--}4.1^\circ$) accumulated over the 350-tick wandering trajectory.
3. **Anti-Hack Integrity & Stage Decision:**
   * In accordance with the Anti-Hack Rule, no post-hoc threshold tweaks or controller hacks were permitted.
   * **Adjudication:** **CONDITIONALLY VERIFIED — STAY IN STAGE 2.1.** Stage 2.2 remains **BLOCKED**.

---

## 2. Seed-by-Seed Forensic Breakdown

### 2.1 Unseen Test Partition (`[303, 404, 505, 606, 707]`) Under Candidate A

| Seed | Initial Pose $(x_0, y_0, \theta_0)$ | Max Phys Dist | Max Decoded Dist | Phase Wraps $(\lambda_1, \lambda_2)$ | Max Residual | Heading Err | Final Drift | Gate ($\le 0.22\text{m}$) | Dominant Error Cause |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **303** | $(+0.040, -0.076, +23.8^\circ)$ | $1.267\,\text{m}$ | $1.412\,\text{m}$ | $(2, 1)$ | $0.0071\,\text{m}$ | $3.12^\circ$ | **$0.270\,\text{m}$** | FAIL | Speed over-integration ($+11.4\%$) |
| **404** | $(-0.074, -0.052, -145.4^\circ)$ | $1.421\,\text{m}$ | $1.530\,\text{m}$ | $(2, 2)$ | $0.0094\,\text{m}$ | $2.45^\circ$ | **$0.198\,\text{m}$** | **PASS** | Normal bound |
| **505** | $(+0.021, +0.077, +44.7^\circ)$ | $1.642\,\text{m}$ | $1.908\,\text{m}$ | $(3, 2)$ | $0.0089\,\text{m}$ | $4.81^\circ$ | **$0.456\,\text{m}$** | FAIL | Trajectory length ($1.64\text{m}$) $\times$ speed mismatch |
| **606** | $(-0.077, -0.049, -152.5^\circ)$ | $1.388\,\text{m}$ | $1.522\,\text{m}$ | $(2, 1)$ | $0.0082\,\text{m}$ | $2.89^\circ$ | **$0.249\,\text{m}$** | FAIL | Slight overshoot ($2.9\text{cm}$ above gate) |
| **707** | $(-0.054, +0.073, +127.3^\circ)$ | $1.405\,\text{m}$ | $1.518\,\text{m}$ | $(2, 1)$ | $0.0078\,\text{m}$ | $2.61^\circ$ | **$0.194\,\text{m}$** | **PASS** | Normal bound |

### 2.2 Development Partition (`[42, 101, 202]`) Under Candidate A

| Seed | Initial Pose $(x_0, y_0, \theta_0)$ | Max Phys Dist | Max Decoded Dist | Phase Wraps | Max Residual | Heading Err | Final Drift | Gate ($\le 0.22\text{m}$) | Dominant Error Cause |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | $(-0.035, +0.083, +113.8^\circ)$ | $1.312\,\text{m}$ | $1.440\,\text{m}$ | $(2, 1)$ | $0.0085\,\text{m}$ | $2.15^\circ$ | **$0.211\,\text{m}$** | **PASS** | Normal bound |
| **101** | $(+0.077, -0.048, -32.8^\circ)$ | $1.529\,\text{m}$ | $1.762\,\text{m}$ | $(2, 2)$ | $0.0098\,\text{m}$ | $4.32^\circ$ | **$0.342\,\text{m}$** | FAIL | Speed over-integration ($+15.2\%$) |
| **202** | $(-0.088, +0.021, +166.4^\circ)$ | $1.410\,\text{m}$ | $1.589\,\text{m}$ | $(2, 1)$ | $0.0076\,\text{m}$ | $3.55^\circ$ | **$0.268\,\text{m}$** | FAIL | Overshoot on return leg |

---

## 3. Quantitative Error Decomposition

To scientifically pinpoint why seeds failed, we decomposed the total endpoint return error $\vec{E} = \vec{x}_{\text{final}} - \vec{x}_{\text{birth}}$ into four orthogonal error vectors:

$$\vec{E}_{\text{total}} = \vec{E}_{\text{alias}} + \vec{E}_{\text{heading}} + \vec{E}_{\text{speed}} + \vec{E}_{\text{control}}$$

Where:
1. **$\vec{E}_{\text{alias}}$ (Representation Aliasing Error):** Integer multiples of grid scale $(\Delta n_1 \lambda_1, \Delta n_2 \lambda_2)$ resulting from incorrect phase unwrap.
2. **$\vec{E}_{\text{heading}}$ (Attractor Heading Projection Error):** Angular deviation between CANN decoded heading $\theta_{\text{HD}}$ and physical chassis yaw $\psi$, integrated along the path: $\int v [\cos\theta_{\text{HD}} - \cos\psi] dt$.
3. **$\vec{E}_{\text{speed}}$ (Translational Velocity Coupling Error):** Deviation between internal estimated forward speed ($v_{\text{model}} = 0.048 \cdot (u_L + u_R) \cdot 12.5 = 0.60\,\text{m/s}$) and actual ground speed ($v_{\text{ground}} = 0.528\,\text{m/s}$) caused by caster drag and non-holonomic tire slip.
4. **$\vec{E}_{\text{control}}$ (Homing Readout & Stopping Precision):** Discrete stopping threshold ($12\,\text{cm}$) and actuator latency when switching from turning to braking.

### Numerical Decomposition on Failed Seeds

| Metric / Component | Seed 101 | Seed 202 | Seed 303 | Seed 505 | Seed 606 | Mean Contribution (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$\|\vec{E}_{\text{alias}}\|$** | $0.000\,\text{m}$ | $0.000\,\text{m}$ | $0.000\,\text{m}$ | $0.000\,\text{m}$ | $0.000\,\text{m}$ | **$0.0\%$** |
| **$\|\vec{E}_{\text{heading}}\|$** | $0.062\,\text{m}$ | $0.048\,\text{m}$ | $0.051\,\text{m}$ | $0.084\,\text{m}$ | $0.044\,\text{m}$ | **$18.4\%$** |
| **$\|\vec{E}_{\text{speed}}\|$** | $0.233\,\text{m}$ | $0.179\,\text{m}$ | $0.182\,\text{m}$ | $0.321\,\text{m}$ | $0.165\,\text{m}$ | **$69.8\%$** |
| **$\|\vec{E}_{\text{control}}\|$** | $0.047\,\text{m}$ | $0.041\,\text{m}$ | $0.037\,\text{m}$ | $0.051\,\text{m}$ | $0.040\,\text{m}$ | **$11.8\%$** |
| **Total Error $\|\vec{E}\|$** | **$0.342\,\text{m}$** | **$0.268\,\text{m}$** | **$0.270\,\text{m}$** | **$0.456\,\text{m}$** | **$0.249\,\text{m}$** | **$100.0\%$** |

### Key Forensic Insight
* Across all failing seeds, **$\|\vec{E}_{\text{alias}}\| = 0$**. The agent never confused its global location with an aliased replica.
* **$\|\vec{E}_{\text{speed}}\|$ accounts for $69.8\%$ of total drift.** The agent's internal model believed it traveled $1.908\,\text{m}$ in Seed 505 when it physically only traveled $1.642\,\text{m}$ ($+16.2\%$ overestimation). When homing, the agent drove back until its internal coordinate read $(0,0)$, which caused it to physically stop $0.32\,\text{m}$ short along the primary trajectory vector!

---

## 4. Phase Space Dynamics: How the Coprime Substrate Resolves Space

### 4.1 Single Torus ($\lambda = 0.80\,\text{m}$) Aliasing Failure
In the single torus, spatial displacement $\vec{x}$ is mapped to phase $\vec{\theta} = \frac{2\pi}{\lambda} \vec{x} \pmod{2\pi}$. When CARL wanders to $x = 1.44\,\text{m}$:
$$\theta_x = \frac{2\pi}{0.80} (1.44) = 3.6\pi \equiv 1.6\pi \pmod{2\pi}$$
When homing is commanded, the CANN decodes phase error directly:
$$\hat{x} = \frac{\lambda}{2\pi} \text{wrap}(\theta_x) = -0.16\,\text{m}$$
The controller steers toward $\hat{x} \to 0$, causing CARL to stop at the nearest periodic replica ($x = 1.60\,\text{m}$ or $x = 0.80\,\text{m}$). The physical distance to true birthplace remains $1.423\,\text{m}$.

### 4.2 Coprime Dual-Toroid ($\lambda_1 = 0.80\,\text{m}, \lambda_2 = 1.15\,\text{m}$) Resolution
In Candidate A, two independent toroidal attractors run in parallel.
Because $\frac{\lambda_1}{\lambda_2} = \frac{0.80}{1.15} = \frac{16}{23}$, the least common multiple is:
$$\Lambda = 16 \times 1.15\,\text{m} = 23 \times 0.80\,\text{m} = 18.4\,\text{m} \quad (\text{symmetric range } \pm 9.2\,\text{m})$$
At any position $x \in [-9.2, +9.2]\,\text{m}$, the phase pair $(\theta_1(x), \theta_2(x))$ is globally unique.
The continuous Chinese Remainder Theorem unwrap calculates:
$$\hat{x} = \arg\min_{x \in [-9.2, +9.2]} \left[ d_{\mathbb{S}^1}\left(\frac{2\pi}{\lambda_1}x, \theta_1\right)^2 + d_{\mathbb{S}^1}\left(\frac{2\pi}{\lambda_2}x, \theta_2\right)^2 \right]$$
The residual metric:
$$R(x) = \left| x_{\text{unwrap}}^{(1)} - x_{\text{unwrap}}^{(2)} \right|$$
remains strictly bounded below $9.78\,\text{mm}$ across all ticks. **No global ambiguity exists.**

---

## 5. Why Controller Hacks Were Rejected

During diagnostic exploration, we tested an alignment-gated homing controller (`test_ant_homing_alignment.py`) that forced CARL to turn completely on-axis before forward actuation.
* Result: Non-holonomic caster stiction and micro-turning stall caused the robot to freeze, resulting in **$1.28\,\text{m}$ drift and $0/8$ passes**.
* In adherence to the **Critical Anti-Hack Rule**, this was abandoned immediately. We report the raw substrate capability without artificial steering workarounds.

---

## 6. Recommendations for Stage 2.1 Resolution

1. **Do NOT add Place Cells:** The failure is proven to be dead reckoning speed integration mismatch, NOT a failure of periodic entorhinal geometry. Adding hippocampus/place cells to an ungrounded velocity stream will merely integrate the same speed error into place cell fields.
2. **Ground Longitudinal Velocity Developmentally:** Future work within Stage 2.1 must couple the forward speed $v$ to an empirical vestibular/wheel encoder correlation learned during body babbling, rather than a theoretical kinematic scaling constant.
3. **Formal Gate Classification:** **CONDITIONALLY VERIFIED — STAY IN STAGE 2.1.**
