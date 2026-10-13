# CARL-DX Stage 4 Master Plan of Action
## Grounded in the Integrated World Modeling Theory (IWMT) Framework

**Document Version:** 1.0.0 (Pre-Registration Draft)  
**Date:** October 2026  
**North Star:** Autonomous Lifelong Emergence of an Embodied Neuromorphic Agent  
**Active Milestone:** Stage 4 — Autopoietic / Lifelong Memory & Persistence ("Remember & Develop")  
**Theoretical Backbone:** Integrated World Modeling Theory (IWMT; Safron 2020)  
**Target Substrate:** 2,114-Unit Neuromorphic Computational Architecture (`carl_autonomous_agent.py`)

---

## 1. Executive Framing: IWMT as the Architectural Blueprint

The **Integrated World Modeling Theory (IWMT)** states that conscious agency arises when an embodied agent constructs and maintains a **spatially, temporally, and evaluatively unified generative model of itself and its environment**.

Stages 2 and 3 established the **real-time spatial and predictive core** of CARL's world model. **Stage 4 provides the missing temporal depth**: transforming a real-time reactive model into an enduring, autopoietic entity with memories, sleep-driven consolidation, and lifelong persistence.

```
========================================================================================
             CARL-DX STAGE 4 LIFELONG INTEGRATED WORLD MODELING PIPELINE
========================================================================================

                 [ Real-Time Sensory Stream: Retinal RGB + Sonar + Proprioception ]
                                                |
                                                v
            +-------------------------------------------------------+
            |  CANN Metric Manifold + World Model (Stages 2 & 3)    |
            |  - 64-HD Head Direction Ring                          |
            |  - 1,024-Grid Torus Metric Position                   |
            |  - 1,026 Neuromorphic Reservoir                       |
            +-------------------------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
     [ Phase 4.1: Online Plasticity ]              [ Phase 4.2: Episodic Memory ]
     IWMT: Adaptive Synaptic Updating              IWMT: High-Dimensional Scene Binding
     - Local eligibility traces (tau=1.5s)         - 2,048-D Holographic Hypervectors (HDC)
     - Expected Free Energy RPE gating             - Quasi-orthogonal binding: Pose (X) Vision
     - Turrigiano homeostatic scaling              - Associative clean-up dictionary
                 |                                             |
                 +----------------------+----------------------+
                                        |
                                        v
                       [ Phase 4.3: Sleep & Offline Replay ]
                       IWMT: Two-Stage Consolidation (CLS + SHY)
                       - High-speed Sharp-Wave Ripple (SWR) Replay (10x-20x)
                       - Reverse replay: Terminal goal/collision -> origin
                       - Synaptic Homeostasis (SHY): alpha=0.98 downscaling & pruning
                                        |
                                        v
                    [ Phase 4.4: Autopoietic Persistence Engine ]
                    IWMT: Lifelong Compounding Identity (GIS-901)
                    - Continuous cryptographic serialization (SHA-256)
                    - Epigenetic compounding across lifespans/reboots
                    - Zero-loss warm boots with 0 exploration penalty
========================================================================================
```

---

## 2. Phase-by-Phase Plan of Action

### Phase 4.1: Adaptive Synaptic Plasticity & Three-Factor Gating (R-STDP)
* **IWMT Function:** The world model's predictive priors must adapt dynamically when the organism encounters friction drops, motor fatigue, or new corridor topologies without destroying previously calibrated metric manifolds.
* **Core Mechanisms to Wire:**
  1. **Three-Factor Synaptic Plasticity:** Presynaptic spike $\times$ Postsynaptic state $\times$ Neuromodulatory gating.
  2. **Dopaminergic Gating via Free Energy:** The neuromodulatory signal is derived directly from the Active Inference Expected Free Energy prediction error:
     $$M(t) = \mathcal{R}_{\text{pragmatic}} + \mathcal{R}_{\text{epistemic}} - \bar{\mathcal{R}}$$
  3. **Local Eligibility Traces:** Eligibility tags $e_{ij}$ decay with time constant $\tau = 1.5\text{ s}$ to bridge the distal credit assignment gap.
  4. **Turrigiano Homeostatic Scaling:** Multiplicative normalization ensures total synaptic Frobenius norm per neuron does not exceed $W_{\max}$, preventing epileptic runaway.
* **Pre-Registered Acceptance Gate 4.1:**
  * Post-plasticity escape latency in altered friction corridors must improve by $\ge 25.0\%$ compared to static frozen weights.
  * CANN attractor energy divergence must remain $< 10^{-4}$ (metric manifolds remain intact).
  * 100% zero access to ground-truth coordinates (`qpos`, `qvel`, `geom_xpos`).

---

### Phase 4.2: Holographic Hyperdimensional Computing (HDC) Episodic Memory
* **IWMT Function:** The world model must bind multimodal scene snapshots into a coherent, non-destructive episodic memory representation immune to catastrophic forgetting.
* **Core Mechanisms to Wire:**
  1. **High-Dimensional Hypervectors ($\mathbf{H}_t \in \{-1, +1\}^{2048}$):**
     Representing spatial position, heading, visual features, and motor synergies via quasi-orthogonal vector symbolic architectures (VSA).
  2. **Lossless Multimodal Binding:**
     $$\mathbf{H}_t = (\mathbf{B}_{\text{pos}} \otimes \mathbf{P}_{\text{CANN}}) \oplus (\mathbf{B}_{\text{heading}} \otimes \mathbf{P}_{\text{HD}}) \oplus (\mathbf{B}_{\text{vision}} \otimes \mathbf{V}_{\text{retina}}) \oplus (\mathbf{B}_{\text{action}} \otimes \mathbf{U}_{\text{motor}})$$
  3. **Associative Clean-Up Memory:** Fast cosine-similarity associative dictionary enabling instant sub-millisecond pattern completion given partial or noisy sensory cues.
* **Pre-Registered Acceptance Gate 4.2:**
  * Storing 500 navigational episodes must achieve $\ge 90.0\%$ associative recall accuracy under $50\%$ input sensory noise.
  * Catastrophic forgetting test: Recall accuracy on the first 50 episodes must degrade by $< 5.0\%$ after learning 450 subsequent episodes.

---

### Phase 4.3: Memory Consolidation, Offline Replay & Sleep Dynamics
* **IWMT Function:** The world model must periodically disengage from active wakefulness to consolidate fragile episodic memories into durable topological schemas and reset synaptic noise.
* **Core Mechanisms to Wire:**
  1. **Complementary Learning Systems (CLS) Architecture:**
     Separating fast online episodic buffer from slow offline schema integration.
  2. **Sharp-Wave Ripple (SWR) High-Speed Replay:**
     Episodes stored in the HDC buffer are replayed at 10×–20× speed during simulated rest.
  3. **Reverse Replay Value Propagation:**
     Trajectories ending in goal achievement or collision are replayed in reverse order, backpropagating value to origin states without a forward simulator.
  4. **Synaptic Homeostasis Hypothesis (SHY) Downscaling:**
     Global multiplicative downscaling factor ($\alpha = 0.98$) applied to background weights, pruning connections where $|w_{ij}| < \epsilon$ to restore dynamic range.
* **Pre-Registered Acceptance Gate 4.3:**
  * Interleaving offline sleep cycles between novel maze exposures must yield a statistically significant $\ge 20.0\%$ improvement in retention over wake-only baselines ($p < 0.001$).
  * SHY pruning must eliminate $\ge 15.0\%$ of weak/noisy synapses without reducing maze navigation success.

---

### Phase 4.4: Autopoietic Lifelong Persistence Engine (GIS-901)
* **IWMT Function:** The world model must maintain organismic identity continuity across system shutdowns, reboots, and multi-day deployments, compounding experience across lifespans.
* **Core Mechanisms to Wire:**
  1. **GIS-901 Cryptographic State Serialization:**
     Zero-copy serialization of 2,114-unit synaptic matrices, HDC episodic clean-up dictionaries, world-model transition weights, and endocrine baselines.
  2. **Epigenetic Compounding:**
     Warm boots resume from the consolidated checkpoint with SHA-256 verification, preserving developmental age and acquired skills.
  3. **Markov Blanket Boundary Invariant:**
     The agent boundary remains self-enclosing; external environment variables are never saved into the cognitive state.
* **Pre-Registered Acceptance Gate 4.4:**
  * Following a hard system reboot (warm boot from disk), CARL must restore 100.0% state identity (SHA-256 verified).
  * 0 re-exploration penalty: CARL must navigate previously mastered challenge mazes on reboot with 0 collisions and zero degradation.

---

## 3. Sequential Execution Roadmap

```
Step 1: Formal Pre-Registration Approval
        Review this plan, lock criteria, verify git tag 'stage-3-certified'.
                                 |
                                 v
Step 2: Phase 4.1 Execution (R-STDP & Plasticity)
        Wire three-factor learning into carl_stdp.py on canonical bus.
        Execute 100-episode plasticity stability battery.
                                 |
                                 v
Step 3: Phase 4.2 Execution (HDC Episodic Memory)
        Integrate 2,048-D VSA binder into carl_hdc.py on canonical bus.
        Execute 500-episode anti-forgetting battery.
                                 |
                                 v
Step 4: Phase 4.3 Execution (Sleep Replay & Consolidation)
        Implement SWR reverse replay & SHY pruning in carl_rem_sleep.py.
        Execute wake-vs-sleep causal ablation battery.
                                 |
                                 v
Step 5: Phase 4.4 Execution (GIS-901 Lifelong Persistence)
        Integrate autopoietic serialization in carl_gis.py.
        Execute cold/warm boot persistence and compounding battery.
                                 |
                                 v
Step 6: Stage 4 Capstone Certification & Dashboard
        Comprehensive 50-episode lifelong acceptance suite.
```

---

## 4. Immutable Project Invariants for Stage 4

1. **No Roadmap Mutation:** Strictly advance Phase 4.1 first; never skip ahead to Stage 5.
2. **Unification Over Fragmentation:** All four phases are organs wired into the **ONE UNIFIED CANONICAL ORGANISM** (`carl_autonomous_agent.py`) on the zero-copy bus. No standalone benchmark scripts.
3. **Decision-Pipeline Isolation Invariant:** Zero simulator coordinates (`qpos`, `qvel`, `qacc`, `geom_xpos`) inside cognitive loops. Verified by automated AST scan before certification.
4. **Strict Terminology:** "2,114-unit neuromorphic computational architecture" with "sensorimotor grounding within recurrent topological inductive biases".
