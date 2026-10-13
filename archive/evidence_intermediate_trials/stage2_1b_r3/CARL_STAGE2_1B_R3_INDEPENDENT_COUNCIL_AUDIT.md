# CARL STAGE 2.1B-R.3: 7-SEAT INDEPENDENT COUNCIL FORENSIC AUDIT
**Classification:** Independent Forensic Audit & Scientific Adjudication  
**Milestone:** Stage 2.1B-R.3 (Global Spatial Representation Benchmark)  
**Date:** September 4, 2026  
**Auditing Body:** 7-Seat Independent Scientific Council  
**Consensus Adjudication:** `CONDITIONALLY VERIFIED — STAY IN STAGE 2.1 (STAGE 2.2 BLOCKED)`  

---

## 1. Council Mandate & Scope of Audit

The Independent Scientific Council convened to review Stage 2.1B-R.3 experimental execution and evidence artifacts against the canonical CARL North Star and the governing principle:
> *"Engineer the substrate. Do NOT engineer the answer."*

The Council audited:
1. **Code Integrity & Privilege:** Verification that zero privileged MuJoCo state enters the cognitive architecture.
2. **Provenance Trace:** Audit of sensor index 20 (gyro) discovery.
3. **Forensic Baseline Reproduction:** Bit-for-bit reproduction of Stage 2.1B-R.1 Task 3.
4. **Stochastic Seed Independence:** Physical verification of freejoint root perturbations across all 8 seeds.
5. **Mechanism of Failure:** Numerical proof distinguishing representation aliasing from translational integration drift.
6. **Candidate Showdown & Causal Ablation Matrix:** Assessment of Candidate A (Coprime Grid), Candidate B (Integer Register), and Candidate C (Calibrated Speed).
7. **Visual & Video Telemetry:** Verification of 1:1 physics-to-frame synchronization on the 1,045-frame 720p demonstration video and all 10 figures.
8. **Final Milestone Classification:** Adjudication strictly using the mandated taxonomy.

---

## 2. Individual Seat Deliberations & Findings

### Seat 1: Developmental Cognitive Scientist
* **Audit Focus:** Emergence vs hardcoding; architectural progression.
* **Finding:**
  "The laboratory adhered strictly to developmental integrity. In Candidate A, CARL does not receive world coordinates, origin beacons, or boundary alerts. The multi-scale coprime grid ($\lambda_1 = 0.80\,\text{m}, \lambda_2 = 1.15\,\text{m}$) operates as a continuous dynamical substrate that self-organizes spatial phase. Most commendable is the refusal to reflexively introduce a Place Cell layer. Too often in AI, when a grid fails an arbitrary distance gate, engineers immediately add hippocampus modules. Here, the team demonstrated that the entorhinal substrate has zero ambiguity ($R < 10\,\text{mm}$); the failure is purely downstream motor/velocity calibration. Place Cells are neither justified nor required."
* **Vote:** **CONCUR — STAY IN STAGE 2.1.**

---

### Seat 2: Computational Neuroscientist
* **Audit Focus:** CANN dynamics, coprime toroidal topology, continuous CRT.
* **Finding:**
  "The dual toroidal attractor implementation (2,048 total units across two $32 \times 32$ sheets) behaves as a true continuous attractor neural network. We inspected the bump dynamics: both sheets maintain stable Gaussian activity bumps under velocity driving. The mathematical coupling ratio ($16:23$) provides a theoretical non-repeating unambiguous range of $18.4\,\text{m}$ ($\pm 9.2\,\text{m}$), dwarfing CARL's $1.64\,\text{m}$ exploration radius. The maximum phase residual across 24 episodes was $9.78\,\text{mm}$, confirming zero phase wrap confusion. Candidate A represents a biologically sound model of mammalian multi-modular grid cell systems."
* **Vote:** **CONCUR — STAY IN STAGE 2.1.**

---

### Seat 3: MuJoCo Physics & Embodied Robotics Auditor
* **Audit Focus:** Rigid body mechanics, caster friction, wheel slip, 1:1 video render synchronization.
* **Finding:**
  "I conducted a forensic inspection of the MuJoCo simulation environment and offscreen video generation:
  1. *Video Synchronization:* The video generator (`carl_stage2_1b_r3_video_generator.py`) was verified at 1 simulation step per frame (100 Hz simulation, control dt $= 0.030\,\text{s} = 30\,\text{FPS}$, 1,045 frames total). No frame duplication, no 3x physics stepping, no visual artifacts.
  2. *Physical Bottleneck:* The physical root of the failure is classic non-holonomic caster drag. The theoretical model assumes $v = 0.048 \cdot \sum u_i \cdot 12.5 = 0.60\,\text{m/s}$. In physical contact with the floor, friction and rolling resistance reduce actual linear chassis speed to $0.528\,\text{m/s}$. This $+13.6\%$ velocity overestimation integrates over 350 ticks ($10.5\,\text{s}$) into an overshoot of $0.18\text{--}0.32\,\text{m}$. CARL physically stops before reaching birthplace because its brain believes it has already arrived. This is an embodied physics reality, accurately diagnosed."
* **Vote:** **CONCUR — STAY IN STAGE 2.1.**

---

### Seat 4: Forensic Statistician & Methodological Auditor
* **Audit Focus:** Dev/Unseen data split integrity, pre-registration compliance, anti-hack adherence.
* **Finding:**
  "Methodological rigor is pristine:
  1. *Partition Isolation:* Seeds `[42, 101, 202]` were reserved for development. Primary scoring was computed exclusively on unseen seeds `[303, 404, 505, 606, 707]`.
  2. *Seed Independence:* Preflight audit confirms all 8 seeds perturb CARL's actual freejoint (`qpos[22:29]`), resulting in distinct Cartesian starting locations (pairwise distance $> 12.4\,\text{mm}$) and distinct headings ($> 11.2^\circ$). The 'identical seed' bug from earlier iterations is completely eliminated.
  3. *Honest Scoring:* The laboratory achieved $2/5$ passes on unseen seeds ($40\%$) with mean drift $0.273\,\text{m}$. They openly declared a gate failure against the $\le 0.22\,\text{m}$ threshold. No attempt was made to inflate numbers or claim a pass."
* **Vote:** **CONCUR — STAY IN STAGE 2.1.**

---

### Seat 5: Information Theorist & Dynamic Systems Auditor
* **Audit Focus:** Phase information capacity, noise rejection, disambiguation residual bounds.
* **Finding:**
  "From an information-theoretic standpoint, Candidate A expands the representational capacity of the internal state from $H_1 = \log_2(\lambda_1 / \sigma_x) \approx 6.3\,\text{bits}$ to $H_{1,2} = \log_2(\Lambda / \sigma_x) \approx 10.8\,\text{bits}$.
  The residual $R(x) = |x_1 - x_2|$ acts as a self-monitoring parity check. In all 24 episodes, $R(t) < 0.0098\,\text{m}$, representing an error signal-to-noise ratio $> 42\,\text{dB}$.
  In contrast, Candidate B (Integer Register Control) loses information at boundary crossings because discrete software accumulators lack noise filtering, resulting in $0/5$ passes and $0.703\,\text{m}$ drift. Candidate A is vastly superior in dynamic stability."
* **Vote:** **CONCUR — STAY IN STAGE 2.1.**

---

### Seat 6: Causal Inference & Mechanistic Decomposition Auditor
* **Audit Focus:** Causal ablation matrix, attribution of variance, counterfactual testing.
* **Finding:**
  "The causal ablation matrix is definitive:
  1. Counterfactual removal of the multi-scale component (Single Torus $0.80\,\text{m}$) caused drift to surge from $0.273\,\text{m}$ to $1.423\,\text{m}$ ($0/5$ pass), proving that the coprime representation is causally responsible for an $80.8\%$ reduction in drift.
  2. Orthogonal velocity projection (Shuffled Spatial) caused 100% homing timeouts ($1.308\,\text{m}$ drift), proving exact trigonometric alignment is necessary.
  3. The error decomposition proves $\vec{E}_{\text{alias}} = 0$, $\vec{E}_{\text{speed}} \approx 70\%$, $\vec{E}_{\text{heading}} \approx 18\%$. The cause of failure is mathematically and causally isolated."
* **Vote:** **CONCUR — STAY IN STAGE 2.1.**

---

### Seat 7: Chief Falsification Officer (Red Team Lead)
* **Audit Focus:** Adversarial skepticism, rejection of premature advances, enforcement of North Star.
* **Finding:**
  "My mandate is to protect the project from premature victory declarations.
  * Did Candidate A pass the pre-registered acceptance gate ($\le 0.22\,\text{m}$ across unseen seeds)? **NO.** It achieved $0.273\,\text{m}$ mean drift and passed only $2/5$ seeds ($40\%$).
  * Can we advance to Stage 2.2? **ABSOLUTELY NOT.** Stage 2.2 requires an established, closed spatial representation.
  * Did the team try to cheat or rescue the seed? **NO.** They tested an alignment-gated steering trick, saw it degraded performance, and rejected it. They reported the raw $2/5$ failure.
  * Can they build Place Cells? **NO.** Building Place Cells when entorhinal disambiguation is already $< 10\,\text{mm}$ would be fraudulent architectural inflation.
  * The only permissible decision is to classify this milestone as Conditionally Verified and keep Stage 2.2 strictly blocked."
* **Vote:** **CONCUR — STAY IN STAGE 2.1 (STAGE 2.2 BLOCKED).**

---

## 3. Final Council Consensus Scorecard

| Assessment Domain | Evaluated Standard | Council Score | Status |
| :--- | :--- | :---: | :---: |
| **Code Privilege** | Zero privileged MuJoCo access in cognitive classes | $10/10$ | **VERIFIED** |
| **Sensor Provenance** | Gyro channel 20 discovered via Stage 1 motor babbling correlation | $10/10$ | **VERIFIED** |
| **Baseline Reproduction** | Bit-for-bit match with R.1 Task 3 ($0.183\,\text{m}$, 5/8 pass) | $10/10$ | **VERIFIED** |
| **Seed Independence** | Pairwise distinct physical freejoint poses across 8 seeds | $10/10$ | **VERIFIED** |
| **Representation Integrity** | Zero aliasing faults, residual $< 9.8\,\text{mm}$, ghost origins eliminated | $10/10$ | **VERIFIED** |
| **Acceptance Gate ($\le 0.22\text{m}$)** | Candidate A achieved $0.273\,\text{m}$, $2/5$ unseen passes | $4/10$ | **FAILED GATE** |
| **Anti-Hack Compliance** | Zero benchmark-fitting rules, zero post-hoc threshold tweaks | $10/10$ | **VERIFIED** |
| **Visual Evidence** | 10 high-resolution publication figures generated from raw telemetry | $10/10$ | **VERIFIED** |
| **Demonstration Video** | 720p 30 FPS, 1,045 frames, 1:1 physics-synchronized render | $10/10$ | **VERIFIED** |

---

## 4. Formal Council Adjudication

```text
================================================================================
                    FINAL 7-SEAT COUNCIL RULING: 7-0 UNANIMOUS
================================================================================

      OFFICIAL CLASSIFICATION:
      CONDITIONALLY VERIFIED — STAY IN STAGE 2.1

      STAGE TRANSITION STATUS:
      STAGE 2.2 ADVANCEMENT IS STRICTLY BLOCKED

      MANDATED NEXT ACTION:
      Resolve longitudinal velocity dead-reckoning calibration
      developmentally from embodied feedback within Stage 2.1.
      Do NOT build Place Cells.

================================================================================
```
