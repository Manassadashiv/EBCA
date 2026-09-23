# CARL STAGE 2.1B: BIOLOGICAL CONTINUOUS ATTRACTOR NEURAL NETWORKS (CANN)
## Architectural & Mathematical Specification for Head-Direction Ring & Toroidal Grid Cell Sheet
**Document Identifier:** `CARL-SPEC-STAGE2.1B-CANN-v1.0`  
**Classification:** Embodied Neuromorphic Cognitive Architecture  
**Target Embodiment:** CARL Differential-Drive Cybernetic Companion (`world/vessel_kinetic.xml`)  
**Status:** SPECIFICATION PHASE (DO NOT IMPLEMENT YET)  

---

## 1. Executive Summary & Epistemological Stance

In **Stage 2.1A-R**, we verified that CARL can autonomously discover its rotational vestibular channel without human labels, withstand stochastic initial poses and sensor noise, and navigate back to its birthplace using classical numerical dead reckoning with an average physical return drift of **$18.2\,\text{cm}$**.

However, as audited by the Independent Council, Stage 2.1A-R's spatial state $(x, y, \theta)$ was an **engineered mathematical scaffold**:
* Heading was a single scalar float updated via Euler integration ($\Delta \theta = \omega_z \Delta t$).
* Position was a pair of scalar coordinates updated via classical trigonometry ($\Delta x = \hat{v}_x \cos\theta \Delta t$).
* Steering was commanded via a classical Proportional (P) controller ($K_p = 1.6$).

### The Stage 2.1B Mission:
In **Stage 2.1B**, we replace the engineered scalar numbers with **Continuous Attractor Neural Networks (CANN)** inspired by mammalian and insect navigation circuits (Skaggs et al., 1995; Zhang, 1996; Moser & Moser, 2005; Burak & Fiete, 2009; Seelig & Jayaraman, 2015).

### Epistemological Rule: Hypotheses, Not Assumed Facts
We do **not** declare that a 64-neuron ring or $32 \times 32$ grid sheet is a settled biological fact. Rather, these are **explicit computational hypotheses** that must be rigorously benchmarked against the Stage 2.1A-R control group:
> **Core Hypothesis:** *A continuous attractor neural network with recurrent Mexican-hat connectivity and energy-minimizing dynamics acts as an active low-pass filter, filtering out high-frequency sensory noise and reducing homing drift compared to a classical numerical accumulator under identical stochastic conditions.*

---

## 2. Full Unified Brain Accounting: 2,114 Neurons

Stage 2.1B does **not** create a disconnected toy network. It integrates directly with CARL's existing Stage 1 nervous system, bringing the total brain to **2,114 neurons**:

```text
═══════════════════════════════════════════════════════════════════════════════════
                         CARL UNIFIED BRAIN ARCHITECTURE
                                (2,114 Neurons)
═══════════════════════════════════════════════════════════════════════════════════

                    Raw Multimodal Sensory Stream (25 Channels)
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
[STAGE 1 RESERVOIR]                                            [STAGE 1.6 ESTIMATOR]
   1,026 Neurons                                              Grounded Body Kinematics
Recurrent Echo State Network                                   Traction Loss Observer
Temporal Memory & Babbling                                         (Slip Ratio sigma)
        │                                                                 │
        │                                ┌────────────────────────────────┘
        │                                │
        │               ┌────────────────┴────────────────┐
        │               ▼                                 ▼
        │     Rotational Velocity wz              Translational Velocity v_hat_x
        │     (Discovered Ch 20)                 (Traction-Gated, sigma <= 0.35)
        │               │                                 │
        │               ▼                                 ▼
        │     [STAGE 2.1B HD RING]             [STAGE 2.1B GRID CELL SHEET]
        │          64 Neurons                         1,024 Neurons
        │     1D Attractor Ring                       2D Toroidal Sheet
        │     Heading Angle theta                     Position Phase (x, y)
        │               │                                 │
        └───────────────┼─────────────────────────────────┘
                        ▼
           Population Vector Decoders
                        ▼
         Internal Spatial Representation
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
[EXPERIMENTAL CANN]           [CONTROL GROUP BASELINE]
Stage 2.1B Neural State      Stage 2.1A-R Classical Math
  Target: < 18.2 cm drift       Baseline: 18.2 cm drift
```

### Component Breakdown:
1. **Stage 1 Reservoir (1,026 Neurons):** Recurrent Liquid State Machine maintaining continuous homeostatic plasticity, processing temporal sensorimotor sequences.
2. **Stage 2.1B Head-Direction (HD) Ring (64 Neurons):** 1D recurrent cyclic neural network representing angular orientation $\theta \in [-\pi, \pi)$.
3. **Stage 2.1B Toroidal Grid Sheet (1,024 Neurons):** $32 \times 32$ 2D recurrent neural sheet with periodic boundary conditions representing spatial position $(x, y)$.
4. **Stage 2.1A-R Control Baseline (0 Neurons):** Classical Euler dead-reckoning accumulator running in parallel to provide the scientific control group.

---

## 3. Mathematical Specification: 64-Neuron Head-Direction Ring Attractor

### 3.1 Neural Topology & Angular Preference
The ring consists of $N_{\text{HD}} = 64$ neurons. Each neuron $i \in \{0, \dots, N_{\text{HD}}-1\}$ has a preferred heading angle:
$$\theta_i = -\pi + \frac{2\pi \cdot i}{N_{\text{HD}}}$$
The angular spacing between adjacent neurons is:
$$\Delta \theta = \frac{2\pi}{64} \approx 0.09817\,\text{rad} \approx 5.625^\circ$$

### 3.2 Membrane Potential & Firing Rate Dynamics
Let $u_i(t)$ be the membrane potential (synaptic activation) of neuron $i$, and $r_i(t)$ be its firing rate.
The network evolves according to continuous-time leaky-integrator dynamics:
$$\tau_{\text{HD}} \frac{du_i}{dt} = -u_i(t) + \sum_{j=0}^{N_{\text{HD}}-1} W_{ij} r_j(t) + I_i^{\text{tonic}} + I_i^{\text{angular}}(t)$$

where:
* $\tau_{\text{HD}} = 0.010\,\text{s}$ (10 ms synaptic time constant).
* Firing rate $r_i(t)$ is computed via rectified linear activation with quadratic thresholding (promoting bump sparsity):
  $$r_i(t) = \left[\max(0, u_i(t))\right]^2$$
* $I_i^{\text{tonic}} = I_0$ is a uniform background excitability current maintaining spontaneous bump stability.

### 3.3 Recurrent Synaptic Weight Matrix (Mexican-Hat Connectivity)
Synaptic connections between neurons $i$ and $j$ depend purely on their angular distance along the ring:
$$\phi_{ij} = \text{atan2}(\sin(\theta_i - \theta_j), \cos(\theta_i - \theta_j))$$
The synaptic weight matrix $W_{ij}$ implements local excitation and global inhibition:
$$W_{ij} = J_{\text{ex}} \exp\left(-\frac{\phi_{ij}^2}{2 \sigma_{\text{HD}}^2}\right) - J_{\text{inh}}$$
* $\sigma_{\text{HD}} = \frac{\pi}{6} \approx 30^\circ$ (width of local excitatory footprint).
* $J_{\text{ex}} > 0$ (excitatory coupling strength).
* $J_{\text{inh}} > 0$ (global inhibitory coupling preventing runaway excitation).

### 3.4 Asymmetric Angular Velocity Injection
To shift the activity bump along the ring proportionally to physical turning:
CARL's discovered vestibular yaw signal $\hat{\omega}_z$ (from Stage 2.1A-R unsupervised babbling) is injected as an asymmetric, derivative-steering current (Zhang, 1996; Burak & Fiete, 2009):
$$I_i^{\text{angular}}(t) = \gamma_{\text{HD}} \cdot \hat{\omega}_z(t) \cdot \sin(\theta_i - \theta_{\text{bump}}(t))$$
where:
* $\hat{\omega}_z(t)$ is the physical yaw rate from discovered Gyro channel 20.
* $\theta_{\text{bump}}(t)$ is the instantaneous decoded center of the activity bump.
* $\gamma_{\text{HD}}$ is the angular calibration gain matching angular velocity to physical rotation speed.
* When $\hat{\omega}_z > 0$ (counter-clockwise turn), neurons ahead of the bump receive positive excitation while neurons behind receive inhibition, dragging the bump forward.

### 3.5 Population Vector Readout
The internal heading belief $\hat{\theta}_{\text{CANN}}$ is decoded from the population firing rate vector $\mathbf{r} = [r_0, \dots, r_{63}]$ via circular center of mass:
$$C = \sum_{i=0}^{N_{\text{HD}}-1} r_i \cos(\theta_i), \quad S = \sum_{i=0}^{N_{\text{HD}}-1} r_i \sin(\theta_i)$$
$$\hat{\theta}_{\text{CANN}} = \text{atan2}(S, C)$$
Bump amplitude (confidence metric):
$$A_{\text{bump}} = \sqrt{C^2 + S^2}$$
If $A_{\text{bump}} < A_{\text{min}}$, the network flags an attractor dispersion anomaly (loss of orientation).

---

## 4. Mathematical Specification: 1,024-Neuron Toroidal Grid Cell Sheet

### 4.1 Neural Sheet Topology ($32 \times 32$)
The grid cell sheet consists of $N_{\text{grid}} = 32 \times 32 = 1,024$ neurons arranged on a 2D Cartesian lattice:
$$\mathbf{p}_{i,j} = (x_i, y_j) \in [0, L) \times [0, L)$$
where $i, j \in \{0, \dots, 31\}$, and $L$ represents the spatial periodicity scale of the grid module ($L = 0.80\,\text{m}$).

### 4.2 Toroidal Boundary Conditions
To prevent edge effects and allow infinite navigation within a finite network, boundaries are topologically connected into a 2-torus $\mathbb{T}^2$:
$$d_x(x_i, x_k) = \min(|x_i - x_k|, L - |x_i - x_k|)$$
$$d_y(y_j, y_l) = \min(|y_j - y_l|, L - |y_j - y_l|)$$
$$D((i, j), (k, l)) = \sqrt{d_x(x_i, x_k)^2 + d_y(y_j, y_l)^2}$$

### 4.3 2D Membrane Dynamics
$$\tau_{\text{grid}} \frac{du_{ij}}{dt} = -u_{ij}(t) + \sum_{k=0}^{31} \sum_{l=0}^{31} W_{(ij),(kl)} r_{kl}(t) + I_{\text{tonic}} + I_{ij}^{\text{trans}}(t)$$
where:
* Firing rate $r_{ij}(t) = [\max(0, u_{ij}(t))]^2$.
* Synaptic connectivity kernel $W$ follows a 2D center-surround Mexican-hat profile:
  $$W(D) = J_{\text{ex}, 2D} \exp\left(-\frac{D^2}{2\sigma_{\text{grid}}^2}\right) - J_{\text{inh}, 2D}$$
  producing spontaneous formation of a localized 2D activity bump.

### 4.4 Slip-Gated Translational Velocity Injection
The 2D bump is shifted across the toroidal sheet by the grounded velocity vector from Stage 1.6:
$$\vec{v}_{\text{grounded}}(t) = \hat{v}_x(t) \cdot \begin{bmatrix} \cos(\hat{\theta}_{\text{CANN}}(t)) \\ \sin(\hat{\theta}_{\text{CANN}}(t)) \end{bmatrix}$$
where:
* $\hat{v}_x(t)$ is the Stage 1.6 forward speed, grounded by mechanical traction coupling.
* $\hat{\theta}_{\text{CANN}}(t)$ is the real-time heading decoded from the 64-neuron HD ring.
* **Traction Gating:** When $\sigma_t > 0.35$, $\hat{v}_x \to 0$, naturally freezing translational current injection $I_{ij}^{\text{trans}}$ and protecting the grid phase from wheel spinout on ice!

The velocity-induced directional current:
$$I_{ij}^{\text{trans}}(t) = \beta \cdot \left(\vec{v}_{\text{grounded}}(t) \cdot \hat{\mathbf{e}}_{ij}\right)$$
drags the 2D bump along the sheet in the exact physical travel direction.

### 4.5 2D Phase Readout
The continuous 2D spatial phase $(x_{\text{grid}}, y_{\text{grid}})$ is decoded via 2D Fourier phase extraction across the toroidal population, yielding the periodic internal coordinates.

---

## 5. Formal Scientific Falsification Gates for Stage 2.1B

To prevent Stage 2.1B from being certified as a "success" without empirical proof, it must satisfy **five strict falsification gates**:

### Gate 1: Autonomous Bump Formation & Stationary Stability
* With zero velocity input ($\omega_z = 0, v_x = 0$), the 64-neuron ring and 1,024-neuron grid sheet must spontaneously form a single, localized, stable activity bump within 50 ms.
* The bump must remain stationary for $> 10\,\text{seconds}$ without drifting by more than $\pm 1.0^\circ$ (testing against spurious numerical drift).

### Gate 2: Linear Angular Velocity Tracking Concordance
* Across angular velocity sweeps $\omega_z \in [-3.0, +3.0]\,\text{rad/s}$, the shift rate of the neural bump must maintain linear correlation $R^2 \ge 0.95$ with physical yaw rate.
* Mean decoded heading error under dynamic S-curves must satisfy $\text{MAE} \le 8.0^\circ$.

### Gate 3: Classical Control Benchmark (The 18.2 cm Showdown)
* Run identical closed-loop homing across the 3 development seeds (`[42, 101, 202]`) and 5 unseen test seeds (`[303, 404, 505, 606, 707]`).
* **Hypothesis Test:** The 2,114-neuron integrated brain must achieve physical return drift **comparable to or better than** the Stage 2.1A-R classical baseline ($18.2\,\text{cm}$):
  $$\text{Drift}_{\text{CANN}} \le 0.20\,\text{m} \quad (\text{across } \ge 7/8 \text{ seeds})$$

### Gate 4: Noise Filtering Resilience (The Attractor Advantage)
* Inject elevated sensor noise ($\sigma_{\text{sensor}} = 0.05\,\text{rad/s}$, $3.3\times$ higher than nominal).
* Under high noise, classical Euler integration will linearly accumulate Brownian drift.
* **Criterion:** The CANN bump's recurrent energy well must demonstrate superior noise suppression, achieving $\ge 15\%$ lower heading drift than classical numerical dead reckoning.

### Gate 5: Low-Friction Ice Immunity on the Torus
* Cross glaze ice ($\mu = 0.005$) for 30 ticks during homing.
* Grid cell bump displacement during steady-state ice must remain $\le 0.05\,\text{m}$ equivalent phase shift.

---

## 6. Execution Manifest
1. **Implementation Files:**
   * `brain/carl_stage2_hd_ring.py` (64-neuron 1D CANN ring)
   * `brain/carl_stage2_grid_torus.py` (1,024-neuron 2D CANN torus)
   * `brain/carl_stage2_integrated_brain.py` (Unified 2,114-neuron architecture)
   * `brain/test_stage2_1b_cann.py` (Master falsification suite)
2. **Visual Telemetry:**
   * Live neural activity raster plots (64-neuron ring bump animation).
   * 2D toroidal activity heatmap ($32 \times 32$).
   * Classical vs CANN trajectory comparison plots.
   * 720p 30 FPS demonstration video.
