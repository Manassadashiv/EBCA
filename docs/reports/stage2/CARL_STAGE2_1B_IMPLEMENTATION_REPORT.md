# CARL STAGE 2.1B: MASTER IMPLEMENTATION & EMPIRICAL FALSIFICATION REPORT
**Document Identifier:** `CARL-REPORT-STAGE2.1B-v1.0`  
**Classification:** Embodied Neuromorphic Cognitive Architecture  
**Target Embodiment:** CARL Differential-Drive Cybernetic Companion (`world/vessel_kinetic.xml`)  
**Evaluation Standard:** Adversarial Karpathy LLM Council Protocol  
**Date:** September 4, 2026  

---

## 1. Executive Summary: What Was Proven vs What Was Falsified

In Stage 2.1B, we replaced the engineered classical dead-reckoning equations and classical P-controller of Stage 2.1A-R with an integrated **2,114-neuron biological brain**:
1. **Stage 1 Recurrent Reservoir:** 1,026 neurons (sensorimotor temporal dynamics & contingency discovery).
2. **Stage 2.1B Head-Direction (HD) Ring Attractor:** 64 neurons (1D continuous attractor tracking heading $\theta$).
3. **Stage 2.1B Toroidal Grid Cell Sheet:** 1,024 neurons ($32 \times 32$ continuous attractor tracking 2D spatial phase $x, y$).
4. **Neuromorphic Population Vector Steering:** Directional torque generated from population cross-products ($\tau = \sum r_i (\hat{\mathbf{e}}_i \times \Delta \vec{\phi})$), completely eliminating classical P-controllers (`steer = Kp * heading_error`) and `atan2(-y, -x)`.
5. **Control Group:** Stage 2.1A-R classical $(x, y, \theta)$ baseline evaluated concurrently under identical stochastic noise realizations.

### The Honest Empirical Findings (Dev vs Unseen Test Split):
* **Autonomous Closed-Loop Homing:** **7/8 Seeds Passed (87.5%)** with an average physical return drift of **$18.27\,\text{cm}$**.
  * Development Seeds (`[42, 101, 202]`): 3/3 passed ($16.8\,\text{cm}, 17.4\,\text{cm}, 18.0\,\text{cm}$).
  * Unseen Test Seeds (`[303, 404, 505, 606, 707]`): 4/5 passed ($18.1\,\text{cm}, 18.5\,\text{cm}, \mathbf{20.5\,\text{cm} \text{ [FAIL]}}, 19.0\,\text{cm}, 17.7\,\text{cm}$).
  * Seed 505 exceeded the $20.0\,\text{cm}$ threshold by $5.5\,\text{mm}$ and is recorded honestly as a failure.
* **Attractor Stationary Stability (Gate 1):** **$0.000000^\circ$ drift** over 10 seconds (333 ticks) of silence.
* **Dual-Blind Permuted Gyro Recovery (Gate 3):** **8/8 Seeds (100%)** discovered the randomly scrambled gyro channel purely through cross-covariance without human labels.
* **Glaze Ice Slip Gating on the Torus (Gate 4):** **8/8 Seeds (100%)** suppressed false displacement on glaze ice ($\mu = 0.005$).
* **Real-Time Latency Gate:** **$1.292\,\text{ms}$** per 30 Hz control tick (Target $\le 25.0\,\text{ms}$).

### The Three Critical Scientific Falsifications:
1. **Hypothesis H5 Falsified (CANN vs Classical Math):** The classical floating-point control baseline achieved a mean drift of **$4.63\,\text{cm}$**, vastly outperforming the 2,114-neuron CANN ($18.27\,\text{cm}$). A biological continuous attractor network does **not** outperform human trigonometry and calculus in simple open-space navigation.
2. **Hypothesis H3 Falsified (Absolute Noise Resilience):** Under elevated sensor noise ($\sigma = 0.05\,\text{rad/s}$), the CANN drifted $18.14\,\text{cm}$, whereas classical dead reckoning drifted $5.11\,\text{cm}$. The CANN exhibited high internal immunity to noise (only 1% variation), but its absolute physical precision was lower than exact floating-point odometry.
3. **Hypothesis H6 Falsified (Ablation Causality on Short Journeys):** Setting recurrent weights to zero ($W_{\text{rec}} = 0$) during a short 60-tick journey yielded a return drift of $15.83\,\text{cm}$ (comparable to full CANN $16.84\,\text{cm}$). On short timescales, transient feedforward integration carries significant spatial information; recurrent attractor dynamics are only causal for long-term stationary persistence ($> 10\,\text{seconds}$).

---

## 2. Full Master Telemetry Scorecard

Raw Evidence File: [`evidence/stage2_1b/stage2_1b_full_telemetry.json`](file:///d:/ebca/evidence/stage2_1b/stage2_1b_full_telemetry.json)

| Seed | Status | CANN Return Drift (m) | Gate (20 cm) | Classical Baseline (m) | Ice Advance (m) | Scrambled Gyro Recovery |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | **DEV** | **$0.1684\,\text{m}$** | **PASS** | $0.0160\,\text{m}$ | $0.0009\,\text{m}$ | Ch 15 $\to$ Ch 15 (100%) |
| **101** | **DEV** | **$0.1742\,\text{m}$** | **PASS** | $0.0507\,\text{m}$ | $0.0248\,\text{m}$ | Ch 15 $\to$ Ch 15 (100%) |
| **202** | **DEV** | **$0.1802\,\text{m}$** | **PASS** | $0.0565\,\text{m}$ | $0.0248\,\text{m}$ | Ch 12 $\to$ Ch 12 (100%) |
| **303** | **UNSEEN** | **$0.1815\,\text{m}$** | **PASS** | $0.0452\,\text{m}$ | $0.0248\,\text{m}$ | Ch 9 $\to$ Ch 9 (100%) |
| **404** | **UNSEEN** | **$0.1849\,\text{m}$** | **PASS** | $0.0534\,\text{m}$ | $0.0248\,\text{m}$ | Ch 21 $\to$ Ch 21 (100%) |
| **505** | **UNSEEN** | **$0.2055\,\text{m}$** | **FAIL** | $0.0371\,\text{m}$ | $0.0248\,\text{m}$ | Ch 8 $\to$ Ch 8 (100%) |
| **606** | **UNSEEN** | **$0.1903\,\text{m}$** | **PASS** | $0.0511\,\text{m}$ | $0.0248\,\text{m}$ | Ch 19 $\to$ Ch 19 (100%) |
| **707** | **UNSEEN** | **$0.1768\,\text{m}$** | **PASS** | $0.0607\,\text{m}$ | $0.0248\,\text{m}$ | Ch 12 $\to$ Ch 12 (100%) |
| **MEAN** | **OVERALL** | **$0.1827\,\text{m}$ ($18.3\,\text{cm}$)** | **7/8 (87.5%)** | **$0.0463\,\text{m}$ ($4.6\,\text{cm}$)** | **$0.0218\,\text{m}$** | **8/8 (100%)** |

---

## 3. Code Anti-Cheat Audit (Line-by-Line Inspection)

To satisfy the Council's mandate, we verify that zero forbidden shortcuts exist in the code paths:

1. **Zero Hardcoded Channels:**
   - In [`carl_stage2_integrated_brain.py:53-75`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py#L53-L75), `w_rot` and `w_fwd` are initialized to zero vectors.
   - During `develop_from_babbling`, `w_rot` is learned purely via anti-symmetric cross-covariance $\rho(u_R - u_L, s_j)$ across all 25 anonymous channels.
   - Channel 20 is never mentioned in the code.
2. **Zero Classical Hidden Coordinates:**
   - In [`carl_stage2_hd_ring.py:90-115`](file:///d:/ebca/brain/carl_stage2_hd_ring.py#L90-L115), heading is stored exclusively in membrane potential vector $\mathbf{u} \in \mathbb{R}^{64}$, evolved via continuous leaky integration $\tau \dot{u} = -u + Wr + I_{\text{shift}}$. Firing rates are computed via divisive normalization.
   - There is no `theta += omega * dt`.
   - In [`carl_stage2_grid_torus.py:120-155`](file:///d:/ebca/brain/carl_stage2_grid_torus.py#L120-L155), spatial position is stored exclusively in the 2D periodic firing pattern of $32 \times 32$ units on a 2-torus, evolved via 2D Fast Fourier Transform convolution.
   - There is no `x += v * cos(theta) * dt`.
3. **Zero Classical P-Controllers or `atan2(-y, -x)`:**
   - In [`carl_stage2_integrated_brain.py:195-220`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py#L195-L220), steering is computed via population cross-product:
     $$\tau_{\text{neural}} = \sum_{i=0}^{63} r_i (\cos\theta_i \Delta \phi_y - \sin\theta_i \Delta \phi_x)$$
     $$\text{steer\_cmd} = \text{clip}\left(0.40 \cdot \frac{\tau_{\text{neural}}}{\text{dist}_{\text{grid}} + 10^{-3}}, -0.10, 0.10\right)$$
   - The motor commands emerge directly from the overlap between the active HD bump and the 2D grid phase displacement.
