# Stage 2.1B: Genuine Emergent Spatial Intelligence (Continuous Attractor Neural Networks)
## Master Implementation Plan & Anti-Cheat Architecture Audit

**Target Milestone:** Stage 2.1B — Continuous Attractor Neural Networks (CANN)  
**Total Brain Accounting:** 2,114 Neurons (1,026 Stage 1 Reservoir + 64 HD Ring + 1,024 Toroidal Grid Sheet)  
**Control Group:** Stage 2.1A-R Classical $(x, y, \theta)$ Dead Reckoning ($18.2\,\text{cm}$ return drift baseline)  

---

## 1. User Review Required & Critical Architectural Invariants

> [!IMPORTANT]
> **NO FORBIDDEN SHORTCUTS ALLOWED:**
> 1. **Zero Hardcoded Channels:** The network receives 25 anonymous sensory streams. Rotation and translation are inferred via learned generic projections ($\mathbf{w}_{\text{rot}}, \mathbf{w}_{\text{fwd}} \in \mathbb{R}^{25}$) developed through unsupervised babbling.
> 2. **Zero Classical Hidden Variables:** Neural states are the continuous membrane potential vectors $\mathbf{u}_{\text{HD}} \in \mathbb{R}^{64}$ and $\mathbf{u}_{\text{grid}} \in \mathbb{R}^{32 \times 32}$. There is NO hidden `theta += omega*dt` or `x += v*cos(theta)*dt`. Firing rates are generated exclusively by integrating the recurrent ODE:
>    $$\tau \frac{d\mathbf{u}}{dt} = -\mathbf{u} + W_{\text{rec}} \mathbf{r} + \mathbf{I}_{\text{ext}} + \mathbf{I}_{\text{tonic}}$$
> 3. **Zero Classical P-Controller / Zero `atan2(-y, -x)`:** Steering during homing is generated directly from neural population vector overlap between current HD ring firing and the stored home memory vector, NOT a hand-coded P-controller.
> 4. **Strict Train/Test Split:** Dev seeds `[42, 101, 202]` $\to$ Freeze algorithm $\to$ Unseen test seeds `[303, 404, 505, 606, 707]`.
> 5. **Scientific Control Group:** Stage 2.1A-R runs in parallel under identical stochastic seeds and noise as a separate baseline. The CANN system does NOT consume any variable from the classical baseline.

---

## 2. Architecture & Information Flow

```text
═══════════════════════════════════════════════════════════════════════════════════════
                    STAGE 2.1B INFORMATION FLOW & NEURAL DYNAMICS
═══════════════════════════════════════════════════════════════════════════════════════

                       Anonymous Sensory Stream (25 Channels)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [Stage 1 Reservoir (1,026)]                     [Developmental Discovery]
     Recurrent Liquid State Machine                  Cross-Covariance Learning
     Temporal Dynamics & Context                                 │
                 │                                ┌──────────────┴──────────────┐
                 │                                ▼                             ▼
                 │                      Rotational Projection         Forward Projection
                 │                         w_rot in R^25                 w_fwd in R^25
                 │                                │                             │
                 │                                ▼                             ▼
                 │                      Learned Angular Current       Learned Forward Speed
                 │                             I_angular                   v_trans
                 │                                │                             │
                 │                                ▼                             ▼
                 │                     [64-Neuron HD Ring CANN]    [1,024-Neuron Grid Torus]
                 │                     Recurrent ODE: tau du/dt    2D FFT Recurrent ODE
                 │                     Continuous 1D Attractor     Continuous 2D Attractor
                 │                                │                             │
                 │                                └──────────────┬──────────────┘
                 │                                               ▼
                 │                               [Neural Population Readout]
                 │                               Circular & Fourier Phase Decoders
                 │                                               │
                 │                                               ▼
                 │                              [Neural Action Steering Head]
                 │                              Population Asymmetry Motor Drive
                 │                              (NO P-Controller, NO atan2)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                               Motor Commands (u in R^6)
```

---

## 3. Proposed Changes & New Modules

### Component 1: 64-Neuron Head-Direction Ring Attractor (`brain/carl_stage2_hd_ring.py`)
- **[NEW]** [`carl_stage2_hd_ring.py`](file:///d:/ebca/brain/carl_stage2_hd_ring.py):
  - 64 cyclic neurons with preferred angles $\theta_i = -\pi + \frac{2\pi i}{64}$.
  - Leaky-integrator ODE solver with synaptic time constant $\tau = 10\,\text{ms}$.
  - Recurrent Mexican-hat weight matrix $W_{ij} = J_{\text{ex}} \exp(-\phi_{ij}^2 / 2\sigma^2) - J_{\text{inh}}$.
  - Asymmetric velocity modulation:
    $$W_{ij}^{\text{shift}}(\omega) = \gamma \cdot \omega \cdot \sin(\theta_i - \theta_j)$$
    drags the continuous neural activity bump along the ring proportionally to physical turning.
  - Spontaneous bump formation under resting tonic drive $I_0$.
  - Population vector readout $\hat{\theta}_{\text{CANN}} = \text{atan2}(\sum r_i \sin\theta_i, \sum r_i \cos\theta_i)$ used solely for external observation/scoring.

### Component 2: 1,024-Neuron Toroidal Grid Cell Attractor (`brain/carl_stage2_grid_torus.py`)
- **[NEW]** [`carl_stage2_grid_torus.py`](file:///d:/ebca/brain/carl_stage2_grid_torus.py):
  - $32 \times 32 = 1,024$ neurons arranged on a 2-torus with periodic boundary conditions.
  - 2D Mexican-hat recurrent connectivity kernel precomputed in frequency domain $\mathcal{F}(W)$.
  - Ultra-fast 2D FFT convolution integration ($\le 0.5\,\text{ms}$ per tick) solving the genuine continuous attractor ODE without latency.
  - Directional velocity modulation dragging the 2D activity bump across the torus driven by grounded forward velocity and current HD ring population heading.
  - Traction gating: suppresses velocity injection when slip is detected ($\sigma > 0.35$).

### Component 3: Unified 2,114-Neuron Embodied Brain (`brain/carl_stage2_integrated_brain.py`)
- **[NEW]** [`carl_stage2_integrated_brain.py`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py):
  - Combines:
    1. Stage 1 Reservoir (1,026 units)
    2. Stage 2.1B HD Ring (64 units)
    3. Stage 2.1B Grid Torus (1,024 units)
  - Unsupervised Developmental Babbling: learns sensory projections $\mathbf{w}_{\text{rot}}, \mathbf{w}_{\text{fwd}}$ from motor babbling contingencies. Zero hardcoded channels.
  - Neural Population Steering: converts the internal spatial displacement into differential wheel motor commands through neural population asymmetry, completely eliminating classical P-controllers.

### Component 4: Falsification Suite & Control Group Showdown (`brain/test_stage2_1b_cann.py`)
- **[NEW]** [`test_stage2_1b_cann.py`](file:///d:/ebca/brain/test_stage2_1b_cann.py):
  - **Experiment 1: Attractor Stability & Bump Persistence:** Verifies spontaneous bump formation and $< 1.0^\circ$ drift over 10s of zero input.
  - **Experiment 2: Closed-Loop Homing Showdown (CANN vs Classical Control):** Tests both under identical stochastic initial poses and noise across Dev seeds (`[42, 101, 202]`) and Unseen Test seeds (`[303, 404, 505, 606, 707]`).
  - **Experiment 3: Noise Filtering Benchmark:** Compares heading drift under elevated sensor noise ($\sigma = 0.05\,\text{rad/s}$).
  - **Experiment 4: Glaze Ice Slip Gating on the Torus:** Tests grid bump displacement on $\mu = 0.005$ glaze ice.
  - **Experiment 5: Dual-Blind Permuted Gyro Recovery:** Tests tabula-rasa recovery under randomly scrambled sensor channels.
  - **Ablation Suite:** Evaluates CANN with recurrence removed ($W_{\text{rec}} = 0$) and with learning removed to verify causal contribution of attractor dynamics.

### Component 5: Visual Telemetry & Video Demonstration
- **[NEW]** [`carl_stage2_1b_visualizer.py`](file:///d:/ebca/brain/carl_stage2_1b_visualizer.py): Generates 4 publication-grade analytical figures (ring bump dynamics, grid torus heatmap, CANN vs Classical trajectory comparison, and multi-seed scorecard).
- **[NEW]** [`carl_stage2_1b_video_generator.py`](file:///d:/ebca/brain/carl_stage2_1b_video_generator.py): Renders continuous 720p 30 FPS demonstration video with live 3D tracking, neural ring raster display, 2D grid torus heatmap overlay, and HUD.

---

## 4. Verification & Falsification Plan

### Automated Tests:
1. `pytest` or standalone verification of ODE numerical stability (checking no NaN, no explosion, stable Lyapunov energy).
2. Development Seeds evaluation: `python -m brain.test_stage2_1b_cann --mode dev` (`[42, 101, 202]`).
3. Freeze code and parameter locks.
4. Unseen Test Seeds evaluation: `python -m brain.test_stage2_1b_cann --mode test` (`[303, 404, 505, 606, 707]`).
5. Ablation testing: `python -m brain.test_stage2_1b_cann --mode ablations`.
6. Wall-clock latency benchmark: ensuring total brain tick $\le 25.0\,\text{ms}$.
7. Real Independent LLM Council Audit: dispatching the 5 adversarial advisors.

---

## 5. Anti-Cheat Verification Matrix

| Check | Requirement | Compliance Strategy |
| :--- | :--- | :--- |
| **Gyro Tap** | NO `sensor[20]` | Cross-covariance projection $\mathbf{w}_{\text{rot}} \in \mathbb{R}^{25}$ learned via babbling |
| **Angle Integration** | NO `theta += omega*dt` | 64-neuron ODE $\tau \dot{u} = -u + Wr + I$ integrates activity directly |
| **Position Integration** | NO `x += v*cos(theta)*dt` | 1,024-neuron 2D toroidal FFT ODE shifts bump across sheet |
| **Gaussian Decal** | NO Gaussian synthesized from float | Bump emerges spontaneously from Mexican-hat attractor dynamics |
| **Steering Law** | NO `steer = Kp * heading_err` | Population vector asymmetry directly drives wheel motor differential |
| **Home Vector** | NO `atan2(-y, -x)` | Population activity compared against birthplace neural memory pattern |
| **Test Seeds** | Frozen before test evaluation | Dev seeds `[42, 101, 202]`, Unseen test seeds `[303, 404, 505, 606, 707]` |
