# CARL STAGE 2.1B: VISUAL EVIDENCE & DEMONSTRATION PACKAGE
## Continuous Attractor Neural Networks (CANN) & Neuromorphic Spatial Navigation
**Target Milestone:** Stage 2.1B — 2,114-Neuron Integrated Brain  
**Classification:** Visual & Physical Evidence Package  
**Artifact Directory Mirror:** `C:\Users\MANAS\.gemini\antigravity-ide\brain\69694e15-b8b9-4584-a63c-480d3a7e2d8a`  
**Date:** September 4, 2026  

---

## 1. Master Demonstration Video (720p 30 FPS, 42.5 Seconds)

> [!NOTE]
> The demonstration video is a comprehensive **42.5-second (1,275 frames @ 30 FPS)** continuous cinematic sequence featuring close-up 3D MuJoCo tracking (`cam.distance = 1.60`, `cam.elevation = -28.0`), full studio lighting, minimal title card (1.5s), and over 39 seconds of active robot movement across four distinct physical phases.

![CARL Stage 2.1B Continuous Attractor Navigation Video Demonstration](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/carl_stage2_1b_cann_demonstration.mp4)

* **Physical File:** [`d:/ebca/evidence/stage2_1b/carl_stage2_1b_cann_demonstration.mp4`](file:///d:/ebca/evidence/stage2_1b/carl_stage2_1b_cann_demonstration.mp4)
* **Artifact Mirror:** [`carl_stage2_1b_cann_demonstration.mp4`](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/carl_stage2_1b_cann_demonstration.mp4)
* **Resolution:** $1280 \times 720$ @ 30 FPS | **Duration:** 42.5 seconds (1,275 frames) | **Size:** 34.83 MB

### Video Snapshots Across the Four Execution Phases

````carousel
![Phase 1: Tabula-Rasa Motor Babbling](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/snapshot_1_babbling.png)
<!-- slide -->
![Phase 2: Long Autonomous Wander Exploration](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/snapshot_2_wander.png)
<!-- slide -->
![Phase 3: Closed-Loop Homing via Population Steering](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/snapshot_3_homing.png)
<!-- slide -->
![Phase 4: Low-Friction Glaze Ice Slip Gating](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/snapshot_4_ice_slip.png)
````

---

## 2. Publication-Grade Analytical Figures

### Figure 1: Continuous Attractor Activity Bump Dynamics
![Figure 1: Neural Activity Bump Dynamics](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure1_bump_dynamics.png)

* **Panel A:** The 64-neuron head-direction ring forms a sparse, localized activity bump via divisive normalization ($r_i = [\max(0, u_i)]^2 / (1 + \beta \sum u^2)$). Decoded heading tracks physical turning with $0.000000^\circ$ stationary drift over 10 seconds of silence.
* **Panel B:** The 1,024-neuron ($32 \times 32$) toroidal grid sheet forms a localized 2D activity bump whose spatial phase continuously shifts across the torus driven by grounded forward velocity.

---

### Figure 2: Closed-Loop Homing Showdown Trajectories (CANN vs Classical Control)
![Figure 2: Homing Showdown Trajectories](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure2_homing_showdown.png)

* **Panel A (Stage 2.1B CANN):** Autonomous closed-loop return trajectories using neuromorphic population vector cross-product steering across representative seeds. Mean physical return drift is **$18.27\,\text{cm}$**.
* **Panel B (Stage 2.1A-R Classical Baseline Control Group):** Classical dead reckoning with Proportional (P) control achieving **$4.63\,\text{cm}$** drift under identical conditions.

---

### Figure 3: Elevated Noise Filtering Benchmark
![Figure 3: Elevated Sensor Noise Benchmark](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure3_noise_advantage.png)

* Compares return drift under elevated sensor noise ($\sigma = 0.05\,\text{rad/s}$, $3.3\times$ nominal).
* The CANN maintains high internal stability ($0.1827\,\text{m} \to 0.1814\,\text{m}$), but classical floating-point math remains physically tighter ($0.0511\,\text{m}$).

---

### Figure 4: Master 8-Seed Generalization Scorecard (Dev vs Unseen Test Split)
![Figure 4: Multi-Seed Scorecard](C:/Users/MANAS/.gemini/antigravity-ide/brain/69694e15-b8b9-4584-a63c-480d3a7e2d8a/figure4_multiseed_scorecard.png)

* **Development Seeds (`[42, 101, 202]`):** 3/3 passed (100%).
* **ALGORITHM STRICTLY FROZEN.**
* **Unseen Test Seeds (`[303, 404, 505, 606, 707]`):** 4/5 passed (80%).
  * Seed 505 drift was $20.55\,\text{cm}$ ($5.5\,\text{mm}$ over the $20.0\,\text{cm}$ threshold) and is honestly recorded as a failure.
* **Overall Pass Rate:** **7/8 Seeds Passed (87.5%)**.

---

## 3. Evidence Index & File Provenance

* **Master Raw Telemetry JSON:** [`d:/ebca/evidence/stage2_1b/stage2_1b_full_telemetry.json`](file:///d:/ebca/evidence/stage2_1b/stage2_1b_full_telemetry.json)
* **Final Council Audit Certificate:** [`d:/ebca/CARL_STAGE2_1B_FINAL_INDEPENDENT_COUNCIL_AUDIT.md`](file:///d:/ebca/CARL_STAGE2_1B_FINAL_INDEPENDENT_COUNCIL_AUDIT.md)
* **Master Implementation Report:** [`d:/ebca/CARL_STAGE2_1B_IMPLEMENTATION_REPORT.md`](file:///d:/ebca/CARL_STAGE2_1B_IMPLEMENTATION_REPORT.md)
* **Core Neural Modules:**
  * [`carl_stage2_hd_ring.py`](file:///d:/ebca/brain/carl_stage2_hd_ring.py) (64-neuron 1D CANN)
  * [`carl_stage2_grid_torus.py`](file:///d:/ebca/brain/carl_stage2_grid_torus.py) (1,024-neuron 2D CANN)
  * [`carl_stage2_integrated_brain.py`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py) (2,114-neuron unified architecture)
