# CARL STAGE 2.1B: BRUTAL INDEPENDENT COUNCIL AUDIT PROMPT
**Document Identifier:** `CARL-COUNCIL-AUDIT-PROMPT-STAGE2.1B-v1.0`  
**Classification:** Adversarial Neuromorphic Verification & Falsification Protocol  
**Audit Standard:** Karpathy LLM Council Protocol (5 Independent Adversarial Thinking Lenses)  
**Target Milestone:** Stage 2.1B — Continuous Attractor Neural Networks (64-Neuron HD Ring + 1,024-Neuron Grid Torus)  

---

## 1. Context & Preamble for the Council

> **MANDATE FOR THE COUNCIL:**  
> You are convened to conduct a forensic, adversarial trust-gate audit of **CARL Stage 2.1B: Continuous Attractor Neural Networks (CANN)**.
>
> In Stage 2.1A-R, CARL established an honest, non-fudged baseline:
> * 7/8 seeds passed (87.5%), with 100% pass on autonomous homing ($18.2\,\text{cm}$ average drift) and 100% unsupervised vestibular discovery under sensor scrambling.
> * However, Stage 2.1A-R's internal spatial state was an **engineered classical scaffold** (scalar floats updated via Euler integration and steered by a P-controller).
>
> In Stage 2.1B, the engineers claim to have replaced this classical scaffold with a **2,114-neuron integrated brain**:
> 1. Stage 1 Reservoir: **1,026 neurons** (recurrent temporal dynamics).
> 2. Stage 2.1B HD Ring: **64 neurons** (1D continuous attractor representing heading $\theta$).
> 3. Stage 2.1B Grid Sheet: **1,024 neurons** (2D toroidal continuous attractor representing position phase $x, y$).
>
> Your role is **not** to congratulate the engineers. Your role is to aggressively search for cheats, cosmetic illusions, architectural bypasses, computational bottlenecks, and hidden failure modes.

---

## 2. Adversarial Audit Checklist: The Five Fatal Traps to Check

Before issuing any verdict, the Council must investigate the following five traps:

### TRAP 1: The "Gaussian Decal" Fraud (Fake Attractor Simulation)
* **The Scam:** Many robotics papers claim to simulate continuous attractor neural networks, but under the hood, they simply calculate classical dead reckoning ($\theta += \omega \cdot \Delta t$), and then set $r_i = \exp(-(\theta_i - \theta)^2 / 2\sigma^2)$ purely for visualization.
* **The Forensic Check:** Did the code actually integrate the recurrent differential equations:
  $$\tau \frac{du_i}{dt} = -u_i + \sum_j W_{ij} r_j + I_i$$
  using genuine synaptic weight matrices and numerical integration? Or is the neural activity a post-hoc cosmetic projection of classical math?
* **Action:** Trace the variable flow in `carl_stage2_hd_ring.py`. If $\theta_{\text{ground\_truth}}$ or $\theta_{\text{Euler}}$ is used to generate $r_i$, **INSTANTLY REJECT AND FAIL**.

### TRAP 2: The Control Group Showdown (Did CANN Actually Beat Classical Math?)
* **The Scam:** The engineers add 1,088 neurons, burn $10\times$ more CPU cycles, show a fancy spinning ring plot, and declare victory—even though the neural network navigates worse than the simple 3-variable math baseline.
* **The Forensic Check:** Compare Stage 2.1B's physical return drift directly against Stage 2.1A-R's $18.2\,\text{cm}$ baseline under identical seeds and noise.
* **Action:** If CANN return drift is worse than $0.25\,\text{m}$ or if noise resilience is inferior to classical dead reckoning, the CANN is an inefficient decoration.

### TRAP 3: Bump Dispersion & Runway Excitation (Attractor Stability)
* **The Scam:** Continuous attractor networks are notoriously delicate. If inhibitory gain $J_{\text{inh}}$ is too low, activity explodes into uniform epileptic firing. If $J_{\text{inh}}$ is too high, the bump vanishes into total silence.
* **The Forensic Check:** Did the engineers verify stationary bump stability? When the robot stops ($\omega_z = 0, v_x = 0$), does the bump remain pinned in place without vanishing or drifting spontaneously?
* **Action:** Check Gate 1 telemetry: stationary drift must be $\le 1.0^\circ$ over 10 seconds of silence.

### TRAP 4: Real-Time Latency & Computational Viability
* **The Scam:** Simulating a $1,024 \times 1,024$ recurrent synaptic matrix ($10^6$ connections) takes 200 ms per step on Python, completely breaking the 30 Hz ($30\,\text{ms}$) real-time MuJoCo physics loop.
* **The Forensic Check:** How is the 2D grid torus simulated? Is it vectorized using 2D FFT convolution, or does it lag the physics engine?
* **Action:** Measure step execution time. If tick duration exceeds $30\,\text{ms}$, the architecture is non-deployable in real-time embodied robotics.

### TRAP 5: Multi-Seed Independence & Unseen Generalization
* **The Scam:** Developers secretly tune synaptic weights $J_{\text{ex}}, J_{\text{inh}}, \gamma$ on the test seeds to ensure 100% pass rates.
* **The Forensic Check:** Verify that synaptic parameters were frozen after Development Seeds `[42, 101, 202]`, and evaluated blindly on Unseen Test Seeds `[303, 404, 505, 606, 707]`.
* **Action:** Verify that metrics vary across seeds to full floating-point precision and that any failure is reported honestly without code edits.

---

## 3. Council Prompt Template (The 5 Adversarial Lenses)

When evaluating the Stage 2.1B implementation, dispatch the following instructions to the five sub-agents:

```text
═══════════════════════════════════════════════════════════════════════════════════
COUNCIL SUB-AGENT PROMPT: STAGE 2.1B CONTINUOUS ATTRACTOR NEURAL AUDIT
═══════════════════════════════════════════════════════════════════════════════════

You are [Advisor Name] on the Independent Karpathy LLM Council.
Audit the target files:
- d:/ebca/brain/carl_stage2_hd_ring.py
- d:/ebca/brain/carl_stage2_grid_torus.py
- d:/ebca/brain/carl_stage2_integrated_brain.py
- d:/ebca/brain/test_stage2_1b_cann.py
- d:/ebca/evidence/stage2_1b/carl_stage2_1b_development_results.json
- d:/ebca/evidence/stage2_1b/carl_stage2_1b_test_results.json

Evaluate the following specific mandate according to your thinking style:

1. THE CONTRARIAN:
   - Search aggressively for cheats. Is the 64-neuron ring genuinely running recurrent ODEs, or is it a Gaussian decal?
   - Did the 1,088 CANN neurons actually beat or match the 18.2 cm classical dead-reckoning baseline, or did it perform worse?
   - Are the test seed metrics genuinely stochastic, or did someone execute deterministic replays?
   - Did any seed fail? If so, did the authors record it honestly, or did they tune thresholds to make it green?

2. THE FIRST-PRINCIPLES THINKER:
   - Audit the physics and mathematics. Is the continuous attractor mathematically well-formed?
   - Are the Mexican-hat connectivity kernels translationally invariant?
   - How is heading decoded? Is it a true population vector sum across firing rates, or does it cheat by reading simulator Euler angles?
   - How does velocity injection shift the bump? Is the asymmetric injection current proportional to discovered physical gyro rates?

3. THE EXPANSIONIST:
   - Does this biological neuromorphic architecture open new computational horizons that classical dead reckoning cannot achieve?
   - Does the self-sustaining energy well of the attractor demonstrate superior noise rejection under elevated Gaussian sensor noise?
   - How cleanly does the 1,024-neuron grid torus connect to downstream Stage 2.2 Place Cells and Stage 2.3 Topological Cognitive Maps?

4. THE OUTSIDER:
   - Strip away the academic jargon (CANN, toroidal manifolds, Mexican-hat topologies).
   - Tell me simply: Did the robot leave home, wander, turn around, and return to its starting spot using this neural network?
   - Does watching the video demonstrate a real activity bump sliding along the neural ring in sync with the physical robot's turns?
   - Is this useful cognitive robotics or academic over-engineering?

5. THE EXECUTOR:
   - Audit the execution plumbing and latency.
   - Does the 1,088-neuron simulation run in real-time (< 30 ms per control step) without stuttering MuJoCo?
   - Are the video and plot artifacts verified, uncorrupted, and accurately linked?
   - Verify that all development seeds [42, 101, 202] were frozen before running test seeds [303, 404, 505, 606, 707].
```

---

## 4. Mandatory Falsification Standards for Stage 2.1B Closure

The Council is strictly prohibited from granting clearance unless the following empirical criteria are verified in the raw receipts:

| Test Battery | Target Dimension | Falsification Limit |
| :--- | :--- | :--- |
| **Battery 2.1B-1** | Autonomous Closed-Loop Homing | Physical return drift $\le 0.20\,\text{m}$ across $\ge 7/8$ seeds |
| **Battery 2.1B-2** | Attractor Noise Filtering | $\ge 15\%$ reduction in heading drift vs Euler under $\sigma_{\text{sensor}} = 0.05\,\text{rad/s}$ |
| **Battery 2.1B-3** | Glaze Ice Slip Gating | Toroidal grid displacement during 30 ticks on ice $\le 0.05\,\text{m}$ equivalent |
| **Battery 2.1B-4** | Stationary Bump Stability | Spontaneous drift $\le 1.0^\circ$ over 10 seconds of zero velocity input |
| **Latency Gate** | Real-Time Embodied Execution | Total brain computation $\le 25.0\,\text{ms}$ per 30 Hz control tick |

---

## 5. Chairman Synthesis & Final Verdict Format

When all 5 sub-agents submit their independent reports, the Chairman will issue:
1. **The Consensus Matrix:** Where the 5 lenses unanimously agree.
2. **The Battlegrounds:** Where the Contrarian and Expansionist clash.
3. **The Line-by-Line Code Audit Findings:** Concrete line numbers verifying genuine ODE integration vs Gaussian decals.
4. **The Final Binary Decision:** **[CLEARED FOR STAGE 2.2]** or **[REJECTED — RETURN TO DEVELOPMENT]**.
