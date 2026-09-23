# CARL Master Developmental Sequence & Architectural Invariants (Permanent Rule)

> [!IMPORTANT]
> **PERMANENT SYSTEM MEMORY & ANTI-DRIFT DIRECTIVE**:
> Following the pause of the legacy Phase 1 (P1-R1 through P1-R5) progression, CARL follows a strict, sequential, immutable **5-Stage Developmental Architecture**.
> Any agent working in this repository MUST strictly follow this progression and NEVER resurrect obsolete August 2026 slide decks, P0-P8 swarms, or 7-stage curricula.

---

## 1. The Canonical 5-Stage Sequence

| Stage | Name | Core Mandate | Status |
| :---: | :--- | :--- | :---: |
| **Stage 1** | **Sensorimotor Grounding & Body Babbling** | *"Learn My Body"*: Learns what its 6 anonymous actuators do; discovers sensory contingencies without human anatomical labels; grounds traction & slip estimation. | **COMPLETED & CERTIFIED ✅** |
| **Stage 2** | **Generative World & Self Modeling** | *"Learn My World"*: Builds internal spatial representation (heading $\theta$, spatial phase $x, y$) via continuous attractors; predicts future world states; establishes attractor persistence & causality. | **CURRENT ACTIVE STAGE ⏳** |
| **Stage 3** | **Continuous Action Synthesis & Behavioral Discovery** | *"Learn How to Behave"*: Stops relying on discrete action grids (12–14 primitives); discovers continuous, novel, agile trajectories (MPPI / continuous action optimization). | **QUEUED NEXT** |
| **Stage 4** | **Autopoietic / Lifelong Memory & Persistence** | *"Remember & Develop"*: Synaptic plasticity (R-STDP) + Holographic HDC long-term memory + persistent state compounding across lifespans via GIS-901. | **FUTURE MILESTONE** |
| **Stage 5** | **Metacognition & Permission-Gated Self-Modification** | *"Understand Myself & Improve"*: Introspective failure analysis ("The Witness"), forms causal hypotheses, and proposes permission-gated self-improvements. | **FINAL MATURITY** |

---

## 2. Invariant: No Roadmap Mutation Without Explicit User Approval

Any agent working on CARL is strictly forbidden from:
- Renaming the five stages,
- Inserting or removing a stage,
- Reviving an old historical roadmap (e.g. August 2026 P0–P8 or 7-stage emergence curriculum),
- Reinterpreting the definition of the current stage,
- Moving CARL to a later stage prematurely,

**UNLESS the user explicitly approves the change in writing.**

---

## 3. Invariant: Current-Stage Gate (Task Declaration Protocol)

Before initiating any substantial implementation, planning, or architectural change, the agent must declare:

```text
CARL North Star:      The 5-Stage Evolutionary Organism
Current Stage:        Stage 2 — Generative World & Self Modeling
Current Subproblem:   Stage 2.1B-R Attractor Causality & Persistence
What this task advances: [Explain exact current-stage deliverable]
Why it does not advance a later stage: [Explicit boundary check]
```

If an agent attempts to implement capabilities belonging to a subsequent stage (for example: *"Implementing place cells now"*, *"Adding MPPI trajectory optimizer now"*, or *"Wiring STDP memory now"*), the system must immediately trigger a **HARD STOP**:
> **"STOP — Stage 2.1B-R has not established the necessary current-stage capability. Advancing to later stages without clearing the active milestone is forbidden."**

---

## 4. Current Stage 2 Constraints & Next Actions

1. **Active Milestone is Stage 2.1B-R (Attractor Causality & Persistence):**
   - In the Stage 2.1B open-space benchmark, the 2,114-unit CANN ran at $1.29\,\text{ms}$ and passed 7/8 seeds ($18.3\,\text{cm}$ drift), but classical floating-point math achieved $4.6\,\text{cm}$, and short-horizon recurrence ablation ($W_{\text{rec}} = 0$) showed recurrence was not causally necessary over short 60-tick journeys. These are benchmark-specific empirical findings, not universal statements about CANNs.
   - **DO NOT JUMP TO STAGE 2.2 PLACE CELLS YET.**
   - Stage 2.1B-R must evaluate where the continuous attractor earns its keep over classical math and feedforward networks:
     * **Sensor Dropout / Blackout:** Working memory persistence during sensory blackout.
     * **Attractor Basin Relaxation:** Dynamic recovery from neural membrane state perturbation.
     * **Long-Horizon Drift Bounds:** Journeys where open-loop dead reckoning accumulates unbounded drift.
2. **Strict Terminology Invariant:**
   - Use: **"2,114-unit neuromorphic computational architecture"**.
   - NEVER call it: *"biological brain"*, *"machine sentience"*, or *"conscious emergence"*.
   - Use: **"Sensorimotor grounding within recurrent topological inductive biases"** (acknowledging that ring and toroidal topologies are human-designed structural inductive biases).
3. **The Unification Invariant:**
   - Every developmental capability is an organ being grown for the **ONE UNIFIED EMBODIED ORGANISM** (`carl_embodied_organism.py` / `carl_autonomous_agent.py`).
   - Do NOT create disposable, siloed prototype scripts that leave the architecture fragmented.
