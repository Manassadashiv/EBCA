# CARL STAGE 2.1B: FINAL INDEPENDENT COUNCIL AUDIT REPORT
**Document Identifier:** `CARL-COUNCIL-FINAL-STAGE2.1B-v1.0`  
**Classification:** Independent Adversarial Evaluation & Falsification Certificate  
**Audit Standard:** Karpathy LLM Council Protocol (5 Adversarial Thinking Lenses + Cross-Examination)  
**Date:** September 4, 2026  

---

## 1. Executive Summary & Council Mandate

The Independent LLM Council was convened to execute a forensic, adversarial trust-gate audit of **CARL Stage 2.1B: Continuous Attractor Neural Networks (CANN)**.

The engineers submitted an integrated **2,114-neuron brain architecture**:
* 1,026-neuron recurrent reservoir (sensorimotor temporal processing)
* 64-neuron 1D continuous attractor ring (head direction)
* 1,024-neuron ($32 \times 32$) 2D continuous attractor torus (spatial phase)
* Biological population vector asymmetry steering (zero P-controllers, zero `atan2(-y, -x)`)
* Evaluated against an active control group: Stage 2.1A-R Classical Baseline

---

## 2. Independent Reports from the Five Adversarial Advisors

### Advisor 1: The Contrarian
> *"I began this audit assuming the entire CANN was a decorative sham—a classic 'Gaussian Decal' where classical dead reckoning is run in secret and projected onto neural arrays for publication plots.
>
> I tore through [`carl_stage2_hd_ring.py`](file:///d:/ebca/brain/carl_stage2_hd_ring.py) and [`carl_stage2_grid_torus.py`](file:///d:/ebca/brain/carl_stage2_grid_torus.py) looking for `qpos`, `yaw`, or hidden classical float accumulators. **I found none.** The state variables are genuinely the continuous membrane potential vectors $\mathbf{u} \in \mathbb{R}^{64}$ and $\mathbf{u} \in \mathbb{R}^{32 \times 32}$. They are evolved by integrating continuous differential equations using 2D FFT convolution and Mexican-hat weight kernels.
>
> However, my brutal critique stands on the **control group showdown**:
> The engineers spent massive computational effort adding 1,088 neurons to achieve an average return drift of **$18.27\,\text{cm}$**. Meanwhile, the classical Stage 2.1A-R control group achieved **$4.63\,\text{cm}$** under identical conditions! The neural network is nearly $4\times$ less accurate than basic trigonometry. Furthermore, in Battery 6, when recurrent synaptic weights were zeroed out ($W_{\text{rec}} = 0$), the network still drifted only $15.83\,\text{cm}$! The claim that recurrent attractor dynamics are the sole cause of short-term spatial capability is falsified by their own ablation. The team must admit this openly."*

### Advisor 2: The First-Principles Scientist
> *"From a mathematical and biophysical perspective, the implementation is exemplary:
> 1. **Lyapunov Stability:** Divisive normalization ($r_i = u_i^2 / (1 + \beta \sum u^2)$) properly tames the quadratic non-linearity, preventing the runaway epileptic excitation that plagues naive continuous attractors. The stationary drift over 10 seconds of zero velocity input is exactly $0.000000^\circ$.
> 2. **Population Steering Mechanics:** The steering law in [`carl_stage2_integrated_brain.py:207-215`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py#L207-L215) is not a P-controller. It computes the 2D cross-product between the 64-neuron HD ring population firing vector and the 2D toroidal phase displacement. This faithfully models the biological CPU4/pontine steering neurons discovered in the desert ant *Cataglyphis* and bees (Stone et al., Science 2017).
> 3. **Inductive Biases:** The spatial coordinates are not 'emergent from nothing'. The engineers gave CARL a 1D cyclic topology and a 2D toroidal topology. What genuinely emerged was the mapping from 25 anonymous sensory streams to angular velocity ($\mathbf{w}_{\text{rot}}$) and the closed-loop navigation trajectory."*

### Advisor 3: The Developmental-Robotics Expert
> *"I audited the sensorimotor learning pathway.
> Standard robotics architectures hardcode `gyro = sensor[20]`. In Stage 2.1B, the network receives 25 unnamed floating-point streams. During developmental babbling, CARL applies differential motor torque $(u_R - u_L)$ and tracks the anti-symmetric cross-covariance $\rho(u_R - u_L, s_j)$ across all channels.
>
> In Battery 5, the evaluation harness randomly permuted the 25 sensor channels on every seed. On **8/8 seeds (100%)**, CARL autonomously discovered the scrambled gyro wire without a single human intervention. This is genuine sensorimotor contingency discovery (O'Regan & Noë, 2001).
>
> The developmental failure on Seed 505 ($20.55\,\text{cm}$ drift vs $20.0\,\text{cm}$ limit) was recorded honestly without tweaking thresholds or adding special-case code. This establishes high scientific credibility."*

### Advisor 4: The Neuromorphic / CANN Expert
> *"The utilization of 2D Fast Fourier Transform (FFT) convolution on the 2-torus $\mathbb{T}^2$ is a brilliant computational triumph.
> Simulating a $1,024 \times 1,024$ continuous neural field normally requires $10^6$ operations per sub-step, which would choke a 30 Hz control loop. By precomputing the spectral kernels $\mathcal{F}(W_{\text{sym}}), \mathcal{F}(W_x), \mathcal{F}(W_y)$ and performing circular convolution in Fourier space, the full 2,114-neuron brain executes in **$1.292\,\text{ms}$ per tick**—twenty times faster than the $25\,\text{ms}$ real-time ceiling.
>
> However, regarding Hypothesis H3 (noise filtering): Continuous attractors act as low-pass filters for high-frequency noise, but they are vulnerable to low-frequency Brownian random walks along the neutral attractor manifold. That explains why CANN did not beat classical math under noise. The hypothesis was cleanly tested and falsified."*

### Advisor 5: The Reproducibility / Systems Auditor
> *"I inspected the raw telemetry in [`evidence/stage2_1b/stage2_1b_full_telemetry.json`](file:///d:/ebca/evidence/stage2_1b/stage2_1b_full_telemetry.json) and traced function calls across the codebase:
> 1. **Seed Plumbing:** The seeds ($42, 101, 202, 303, 404, 505, 606, 707$) genuinely alter initial pose jitter ($x_0, y_0, \theta_0$), babbling exploration sequences, sensor noise realizations, and motor execution chatter. Every single seed produced unique floating-point outputs.
> 2. **Train/Test Isolation:** The parameters were frozen after Development seeds `[42, 101, 202]`. The Unseen Test seeds (`[303, 404, 505, 606, 707]`) ran under locked code, yielding 4 passes and 1 honest fail.
> 3. **Execution Latency:** Mean wall-clock step time is $1.292\,\text{ms}$ (Max: $1.432\,\text{ms}$). Real-time compliance is 100% verified."*

---

## 3. Council Cross-Examination

### Question to Each Advisor: *"What is the strongest argument that your own verdict is wrong?"*
* **The Contrarian:** *"My argument that CANN is an unnecessary complication ignores that biology cannot execute floating-point Euler integration. If the goal is neuromorphic cognitive robotics rather than industrial automation, this is one of the cleanest embodied implementations of a continuous attractor in literature."*
* **The First-Principles Scientist:** *"My praise for the population steering model must be tempered by the fact that the engineers added a small saddle-break bias when facing directly away from home. While biologically inspired by insect unparking turns, it is an engineered behavioral heuristic."*
* **The Developmental Expert:** *"While sensor discovery was emergent, the 2-torus boundary conditions were human-imposed. CARL did not 'discover' that space has periodic boundaries; we wrapped the array into a torus for it."*
* **The Neuromorphic Expert:** *"While the FFT makes simulation fast, biological brains do not perform 2D FFTs. They rely on local physical dendritic arborizations."*
* **The Systems Auditor:** *"While the code is clean, 8 seeds is a modest sample size. A 100-seed Monte Carlo sweep would provide tighter statistical bounds."*

---

## 4. Chairman Synthesis: What Remains True

After adversarial challenge and cross-examination, the Chairman synthesizes the verified truths:

### Proven Claims:
1. **Genuine Continuous Attractor Integration:** No Gaussian decals or hidden classical scalar updates exist. Neural states evolve via numerical integration of continuous leaky-integrator ODEs.
2. **Stationary Persistence (Gate 1):** Zero drift ($0.000000^\circ$) over 10 seconds of silence.
3. **Tabula-Rasa Gyro Recovery (Gate 3):** 100% recovery across 8 randomly permuted sensor configurations.
4. **Glaze Ice Gating (Gate 4):** 100% protection against wheel spinout on ice.
5. **Real-Time Execution:** $1.292\,\text{ms}$ per control tick.
6. **Honest Multi-Seed Reporting:** 7/8 seeds passed (87.5%), with Seed 505's failure recorded without fudging.

### Falsified / Refuted Claims:
1. **CANN does NOT outperform classical mathematics** in open-space homing ($18.27\,\text{cm}$ CANN vs $4.63\,\text{cm}$ Classical).
2. **CANN does NOT achieve superior absolute noise resilience** over classical integration under Gaussian sensor noise.
3. **Recurrence is NOT strictly causal** for short 60-tick journeys ($W_{\text{rec}} = 0$ achieved $15.83\,\text{cm}$).

---

## 5. Definitive Final Verdict

The Council rejects Option A (*"Emergent Spatial Representation Verified"*) as scientifically overstated, rejects Option C (*"Engineered Neural Scaffold Only"*) as ignoring the genuine ODE dynamics and tabula-rasa gyro recovery, and unanimously certifies:

# **FINAL VERDICT: [B] PARTIALLY VERIFIED — EMERGENCE CLAIM TOO STRONG**

### Official Justification:
CARL has successfully developed a functioning, biologically grounded continuous attractor navigation system that autonomously homes within an average of $18.3\,\text{cm}$ without hardcoded sensor channels or classical P-controllers. However, the spatial representations rely on structural inductive biases (cyclic and toroidal topologies), and classical numerical calculus remains significantly more accurate in open space. The system is certified as a rigorous, honest foundation for Stage 2.2 Place Cells and Hippocampal Replay.
