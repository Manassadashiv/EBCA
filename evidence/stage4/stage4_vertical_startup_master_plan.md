# CARL-DX Stage 4 Vertical Startup Master Plan
## End-to-End Integrated Architecture, Failure Mode Effects Analysis (FMEA), and Vulnerability Pre-Emption Blueprint

**Document Version:** 1.0.0 (Pre-Registration Draft)  
**Date:** October 2026  
**North Star:** Autonomous Lifelong Emergence of an Embodied Neuromorphic Agent  
**Active Milestone:** Stage 4 — Autopoietic / Lifelong Memory & Persistence ("Remember & Develop")  
**Methodology:** Vertical Startup Approach (Full-Stack Vertical Slice Integration + Proactive FMEA Risk Mitigation)  
**Theoretical Backbone:** Integrated World Modeling Theory (IWMT; Safron 2020)  
**Target Substrate:** 2,114-Unit Neuromorphic Computational Architecture (`carl_autonomous_agent.py`)

---

## 1. What is the "Vertical Startup Approach"?

In complex systems engineering and autonomous robotics, development often fails due to **horizontal procrastination**—building layer 1 across the entire system, then layer 2, only to discover at the end that the layers do not integrate, interfaces clash, and latent numerical instabilities trigger cascading system failure.

The **Vertical Startup Approach** reverses this:
1. **Full-Stack Vertical Slice First:** We construct a complete, thin, end-to-end operational thread piercing **all four layers** simultaneously on a representative screening benchmark (5 matched corridors):
   $$\text{Physical HAL} \longrightarrow \text{Plasticity (4.1)} \longrightarrow \text{HDC Memory (4.2)} \longrightarrow \text{Sleep Replay (4.3)} \longrightarrow \text{GIS-901 Boot (4.4)}$$
2. **Proactive Failure Mode & Vulnerability Mitigation:** Every known theoretical and numerical failure mode (runaway weights, bundling saturation, replay hallucination, state desynchronization) is identified, modeled, and neutralized with software guardrails *before* full-scale horizontal evaluation.
3. **Fail-Closed Verification Gates:** Each vertical component must pass strict mathematical and latency bounds before the full 50-episode lifelong benchmark is unlocked.

```
====================================================================================================
                        HORIZONTAL VS. VERTICAL STARTUP ARCHITECTURE
====================================================================================================

  [ HORIZONTAL TRADITIONAL APPROACH - HIGH RISK ]
  Build ALL of Phase 4.1 for 50 mazes ---> Build ALL of Phase 4.2 ---> Discover Crash at Integration!

  [ CARL-DX VERTICAL STARTUP APPROACH - CERTIFIED ZERO RISK ]
  +------------------------------------------------------------------------------------------------+
  |  THIN VERTICAL SLICE (Screening Corridors 0-4):                                                |
  |  [Physical Robot] -> [R-STDP Update] -> [HDC Trace] -> [SWR Sleep Replay] -> [GIS-901 Reboot] |
  |  * Validate end-to-end dataflow, latency contracts, and FMEA guardrails immediately.           |
  +------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
  +------------------------------------------------------------------------------------------------+
  |  FULL HORIZONTAL SCALE-OUT:                                                                    |
  |  Deploy verified vertical engine across the complete 50-episode lifelong developmental battery.  |
  +------------------------------------------------------------------------------------------------+
====================================================================================================
```

---

## 2. Comprehensive Failure Modes & Effects Analysis (FMEA)

Based on our multi-database literature review (OpenAlex, Europe PMC, arXiv, bioRxiv), we identify **10 critical vulnerabilities and breakdown modes** across Stage 4, paired with mathematically enforced mitigations:

| ID | Phase | Vulnerability / Failure Mode | Theoretical Root Cause | Catastrophic Consequence | Mathematical & Engineering Guardrail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | **4.1** | **Synaptic Runaway / Weight Explosion** | Positive Hebbian feedback loops in R-STDP without saturation limits (Song et al. 2000). | Weights blow up ($w \to \infty$), reservoir saturates, motor commands lock to $\pm 1.0$, robot spins out. | **Turrigiano Multiplicative Scaling:** Clamping $\|W\|_F \le W_{\max}$ and hard-bounding $w_{ij} \in [-1.0, 1.0]$ after every control tick. |
| **F-02** | **4.1** | **Attractor Manifold Disruption** | Weight updates leaking into CANN metric attractor weights (64-HD ring / 1,024-grid torus). | Internal spatial map loses metric gridness; agent becomes disoriented in darkness. | **Structural Plasticity Quarantine:** Zero plasticity in CANN recurrent weights. Plasticity is strictly confined to reservoir readouts and associative bridges. |
| **F-03** | **4.1** | **Silent / Atrophied Synapses** | Excessive LTD (depression) or negative prediction errors driving weights to zero. | Synapses permanently die; loss of exploratory plasticity (Turrigiano 2011). | **Floor Protection:** Minimum synaptic strength floor $\epsilon_{\text{floor}} = 0.01$ and stochastic spontaneous potentiation (noise injection). |
| **F-04** | **4.2** | **HDC Bundling Saturation (Noise Floor Collapse)** | Superposing too many vectors into one hypervector ($N > D / 10$) (Kanerva 2009). | Signal-to-noise ratio $\text{SNR} \propto \sqrt{D/N}$ drops below detection threshold; total recall failure. | **Segmented Episodic Clean-Up Dictionary:** Associative key-value store with maximum cluster capacity $K=128$; LRU eviction to long-term memory. |
| **F-05** | **4.2** | **Spurious Vector Hash Collision** | Two distinct corridor locations generating non-orthogonal hypervectors ($\cos(\mathbf{u}, \mathbf{v}) > 0.40$). | False episodic recall: agent thinks a novel dead-end is an open exit, causing wall collision. | **Cosine Distance Orthogonality Check:** Query similarity threshold $\theta_{\text{match}} = 0.72$; if $\cos < \theta$, declare "Novel Scene" rather than returning spurious match. |
| **F-06** | **4.3** | **Hallucinatory Sleep Replay** | Replaying corrupted or crashed trajectories during offline sleep without outcome filtering. | Reinforces erroneous wall-crashing actions into permanent long-term memory. | **Replay Sanity Gate:** Trajectories replayed during SWR must have verified clean termination, goal success, or high epistemic surprise without fatal contact. |
| **F-07** | **4.3** | **Retrograde Amnesia (Over-Pruning)** | Excessive synaptic downscaling in Synaptic Homeostasis (SHY) (Tononi & Cirelli 2014). | Erases previously mastered corridor routes; agent regresses to infant babbling. | **Engram Masking:** Synaptic weights with high usage count ($N_{\text{hits}} > 50$) are protected by an epigenetic lock from SHY pruning. |
| **F-08** | **4.4** | **Warm-Boot State Desynchronization** | Synaptic weights load correctly, but HDC memory dictionary or CANN phase fails to align. | Agent awakens with motor skills calibrated for an alien spatial coordinate frame; instant erratic motion. | **Unified Transactional Snapshot:** Zero-copy serialization of all modules into a single atomic binary container with atomic commit. |
| **F-09** | **4.4** | **Serialization Latency Spikes** | Checkpointing multi-megabyte tensor states on the active control loop. | Control loop exceeds the $30\text{ ms}$ real-time deadline, dropping physics simulation steps. | **Asynchronous Double-Buffered Serialization:** Background worker thread handles disk I/O; control bus copies pointers in $< 0.15\text{ ms}$. |
| **F-10** | **4.4** | **Markov Blanket Coordinate Leakage** | Leaking ground-truth simulator coordinates (`qpos`, `qvel`, `geom_xpos`) into state files. | Violates the zero-tolerance Anti-Cheat Invariant; invalidates empirical claims of autonomous life. | **Automated AST Anti-Cheat Gate:** Automated AST scanner rejects any checkpoint file containing raw simulator coordinates before commit. |

---

## 3. The 4-Phase Vertical Integration Plan

```
====================================================================================================
                        STAGE 4 VERTICAL INTEGRATION PIPELINE
====================================================================================================

      [ STEP 1: PRE-FLIGHT INTEGRITY LOCK & CONTRACT INITIALIZATION ]
      - Confirm 'stage-3-certified' git baseline.
      - Establish zero-copy tensor schemas for STDP, HDC, SWR, and GIS.
      - Install FMEA mathematical guardrails (Turrigiano clamp, Engram lock).
                                        |
                                        v
      [ STEP 2: VERTICAL SLICE SCREENING (Configs 0-4) ]
      - Run end-to-end 5-config screening loop:
        * 100 control ticks per config.
        * Online R-STDP weight update with eligibility traces.
        * Real-time 2,048-D HDC episodic encoding.
        * Inter-episode 10x offline SWR reverse replay.
        * GIS-901 state save -> Simulated Crash -> Warm Boot.
      - Verify: 0 collisions, latency < 25 ms, 100% state restoration.
                                        |
                                        v
      [ STEP 3: PHASE-BY-PHASE FORMAL CERTIFICATION ]
      - Phase 4.1 Certification: Plasticity stability battery (100 episodes).
      - Phase 4.2 Certification: HDC anti-forgetting battery (500 episodes).
      - Phase 4.3 Certification: Sleep consolidation causal ablation battery.
      - Phase 4.4 Certification: Lifelong persistence & reboot compounding.
                                        |
                                        v
      [ STEP 4: 50-EPISODE LIFELONG ACCEPTANCE BATTERY ]
      - Execute 50-episode adversarial lifelong battery.
      - Verify 0% collisions, 100% escapes, zero memory decay across reboots.
====================================================================================================
```

---

## 4. Phase-by-Phase Technical Specifications & Mathematical Contracts

### Phase 4.1: Adaptive Synaptic Plasticity Engine (`carl_stdp.py`)
* **Mathematical Contract:**
  1. **Eligibility Trace Update:**
     $$\mathbf{e}_{ij}(t + \Delta t) = \mathbf{e}_{ij}(t) \cdot \exp\left(-\frac{\Delta t}{\tau_e}\right) + \mathbf{x}_j(t) \cdot \mathbf{y}_i(t)$$
     where $\tau_e = 1.50\text{ s}$ and $\Delta t = \text{executable simulation timestep}$.
  2. **Three-Factor Gating:**
     $$\Delta W_{ij} = \eta \cdot \mathbf{e}_{ij}(t) \cdot \left(\mathcal{R}_{\text{EFE}}(t) - \bar{\mathcal{R}}\right)$$
     where $\mathcal{R}_{\text{EFE}} = -\Delta G$ (reduction in Expected Free Energy).
  3. **Turrigiano Homeostatic Normalization:**
     $$W_i \longleftarrow W_i \cdot \left[1 + \gamma \cdot (a^* - \bar{a}_i)\right], \quad \text{clamped to } \|W_i\|_2 \le W_{\max}$$
* **FMEA Guardrails:** Active clamping $W_{ij} \in [-1.0, 1.0]$; CANN weights cryptographically immutable (`requires_grad = False`, frozen mask).

---

### Phase 4.2: Holographic Hyperdimensional Memory (`carl_hdc.py`)
* **Mathematical Contract:**
  1. **Hypervector Dimension:** $D = 2,048$, bipolar $\mathbf{v} \in \{-1, +1\}^D$.
  2. **Quasi-Orthogonal Multimodal Binding:**
     $$\mathbf{H}_t = \text{sign}\left( (\mathbf{B}_{\text{spatial}} \otimes \mathbf{P}_{\text{CANN}}) + (\mathbf{B}_{\text{heading}} \otimes \mathbf{P}_{\text{HD}}) + (\mathbf{B}_{\text{vision}} \otimes \mathbf{V}_{\text{retina}}) + (\mathbf{B}_{\text{action}} \otimes \mathbf{U}_{\text{motor}}) \right)$$
  3. **Associative Clean-Up Query:**
     $$\hat{\mathbf{U}} = \operatorname{argmax}_{\mathbf{U}_k \in \mathcal{D}} \left( \frac{\mathbf{H}_{\text{query}} \cdot \mathbf{H}_k}{\|\mathbf{H}_{\text{query}}\| \|\mathbf{H}_k\|} \right), \quad \text{valid if } \cos > 0.72$$
* **FMEA Guardrails:** Clean-up dictionary segmented into spatial Voronoi buckets; maximum cluster size 128 to prevent bundling saturation.

---

### Phase 4.3: Sleep & Offline Replay Engine (`carl_rem_sleep.py`)
* **Mathematical Contract:**
  1. **Sharp-Wave Ripple (SWR) Compressed Replay:** Replays episodic buffer at $15\times$ speed ($\Delta t_{\text{sleep}} = \Delta t / 15$).
  2. **Reverse Temporal Playback:** Trajectory $T = (s_0, s_1, \dots, s_K)$ is replayed in reverse: $s_K \to s_{K-1} \to \dots \to s_0$, backpropagating terminal value tags to early decision nodes.
  3. **Synaptic Homeostasis (SHY) Downscaling:**
     $$W_{ij} \longleftarrow W_{ij} \cdot \alpha_{\text{down}}, \quad \alpha_{\text{down}} = 0.98$$
     $$\text{if } |W_{ij}| < \epsilon_{\text{prune}} \ (10^{-3}) \text{ and } N_{\text{hits}}(ij) < 10 \implies W_{ij} = 0$$
* **FMEA Guardrails:** Trajectories with collision flags are vetoed from replay; engram lock protects critical motor skills from synaptic pruning.

---

### Phase 4.4: Autopoietic Lifelong Persistence Engine (`carl_gis.py`)
* **Mathematical Contract:**
  1. **Cryptographic State Checkpointing:**
     $$\mathcal{S}_{\text{organism}} = \left\{ W_{\text{STDP}}, \mathcal{D}_{\text{HDC}}, \Theta_{\text{WorldModel}}, \mathbf{E}_{\text{endocrine}}, \text{Age}_{\text{cycles}} \right\}$$
     Serializes to zero-copy memory-mapped binary (`carl_state.bin`) with SHA-256 integrity hash (`carl_state.sha256`).
  2. **Atomic Transactional Rollback (WAL):** Write-Ahead Logging guarantees that a crash during disk write rolls back to the prior valid checkpoint with zero data corruption.
  3. **Lifelong Compounding Warm Boot:**
     Upon reboot, the state is verified via SHA-256 and mapped directly into memory in $< 15\text{ ms}$, resuming continuous developmental adaptation.
* **FMEA Guardrails:** AST scanner enforces zero `qpos`/`qvel` simulator coordinate leakage into serialized dictionaries.

---

## 5. Pre-Registered Acceptance Gates for Stage 4

Before any capability is declared certified, it must satisfy its pre-registered quantitative acceptance gate:

| Gate | Target Subsystem | Pre-Registered Metric & Pass Threshold | Statistical Requirement |
| :--- | :--- | :--- | :--- |
| **Gate 4.0** | Vertical Screening | End-to-end vertical execution on Configs 0–4: 5/5 escapes, 0 collisions, cycle latency $< 25\text{ ms}$, warm boot verified. | $100\%$ pass on screening set |
| **Gate 4.1** | Plasticity Stability | Adaptation latency improvement $\ge 25.0\%$ under friction changes; CANN energy divergence $< 10^{-4}$; $\|W\|_F \le W_{\max}$ over 100 episodes. | $p < 0.01$ (Student's t-test) |
| **Gate 4.2** | HDC Anti-Forgetting | $\ge 90.0\%$ associative recall accuracy under $50\%$ cue noise across 500 stored episodes; $< 5.0\%$ degradation on early episodes. | $N = 500$ episodes |
| **Gate 4.3** | Sleep Necessity | Sleep-consolidated agent outperforms wake-only agent by $\ge 20.0\%$ escape success across novel maze configurations. | $p < 0.001$ (Mann-Whitney U) |
| **Gate 4.4** | Autopoietic Reboot | $100.0\%$ SHA-256 match on warm reboot; $0$ re-exploration penalty on previously mastered mazes; serialization latency $< 20\text{ ms}$. | Deterministic zero-loss |
| **AST Gate** | Anti-Cheat Quarantine | $100\%$ clean AST scan across all Stage 4 files (zero simulator coordinates permitted in cognitive loops). | 0 violations |

---

## 6. Actionable Next Steps

1. **Review and Lock Plan:** Confirm alignment with this Vertical Startup Plan.
2. **Implement Vertical Slice Screening Battery:** Build `tests/test_stage4_vertical_screening.py` connecting the vertical dataflow across Configs 0–4.
3. **Execute and Validate:** Verify all FMEA guardrails in action before horizontally expanding to the full 50-episode certification.
