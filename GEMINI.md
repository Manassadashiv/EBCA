# CARL-DX Canonical Project Rules & Master Developmental Progression

## The 5-Stage Developmental Architecture (Permanent Reference)
Following the certified completion of Stage 2, all development strictly follows this sequential, immutable roadmap:

* **Stage 1 — Sensorimotor Grounding & Body Babbling ("Learn My Body"):** **COMPLETED & CERTIFIED ✅** (6-channel anonymous motor babbling, linear forward momentum, kinematic slip & traction estimation).
* **Stage 2 — Generative World & Self Modeling ("Learn My World"):** **COMPLETED & CERTIFIED (Scope-Bounded Substrate) ✅** (Stage 2 certified the integrated sensorimotor, spatial-memory, predictive-deliberation substrate under its defined acceptance tests: 40/40 challenge mazes cleared, 0.00% collisions, p95 40.58 ms, 100% organ activation, clean AST decision-pipeline isolation. **CANN causal coupling and non-LOS memory necessity remain explicitly unproven capabilities carried forward into Stage 3**).
* **Stage 3 — Continuous Action Synthesis & Behavioral Discovery ("Learn How to Behave"):** **CURRENT ACTIVE MILESTONE ⏳**
  * **Stage 3.0 — Pre-Flight Integrity Lock & Code Hygiene Purge:** Purge dormant `geom_xpos` leak and `qpos` z-height read in `carl_embodied_organism.py`, normalize floating base height, verify 100% clean AST anti-cheat scan in the decision pipeline, lock SHA-256 baselines and tensor contracts.
  * **Stage 3.1 — CANN Causal Coupling (Stage 2 Repair Gate):** Wire CANN state into trajectory scoring, execute pre-registered CANN Causal Ablation Battery (Intact vs Frozen vs Zeroed vs Shuffled; require $\Delta \mathbf{u} > 0.15, p < 0.01$).
  * **Stage 3.2 — Counterfactual Trajectory Fidelity & Spatial Memory Necessity (Stage 2 Repair Gate):** Validate predicted rollouts against physical MuJoCo steps ($\le 0.08\text{ m}$ error); force the core question (*Does spatial memory contribute information unrecoverable from sonar alone?*) across 5 non-LOS task families (blind corners, cul-de-sacs, backtracking, sonic symmetries, sensor blackouts; require $\Delta \text{Success} \ge 35\%, p < 0.001$).
  * **Stage 3.3 — Continuous Action Synthesis (MPPI):** Continuous trajectory optimization ($M=128, H=15, dt=0.03\text{s}$) over continuous wheel velocities $\mathbf{u} \in [-1.0, 1.0]^2$; evaluate candidates against learned world model and occupancy memory.
  * **Stage 3.4 — Autonomous Behavioral Discovery under Active Inference:** Expected Free Energy minimization ($G = \text{Pragmatic} + \text{Epistemic}$); autonomous discovery of composite maneuvers without handcoded rules. **(Stage 3.4-R3 200-episode frozen battery adjudicated: FAILED CLOSED ❌ on Gates 1, 2, 3, 4; Gate 5 100% AST clean; active milestone awaiting physical rotational hull clearance resolution)**.
  * **Stage 3.5 — Physical Perturbation & Environmental Adaptation:** Online adaptation to friction drops ($\mu=0.2$), torque loss, and wheel slip; dynamic exploration tuning via endocrine kinetics (Cortisol/NE).
  * **Stage 3.6 — Behavioral Synergy Formation & Physarum Routing:** Cluster recurring trajectories into reusable motor synergies via HDC memory; integrate Physarum plasmodial flow equations to prune dead-ends.
  * **Stage 3.7 — Multi-Modal Perception, Canonical Integration & Adversarial Acceptance:** Ingest offscreen RGB from `eye_cam` retina via `CarlVisionNet`; active head gaze scanning; full canonical organism integration in `carl_autonomous_agent.py`; 50-episode frozen acceptance suite (collision $\le 5\%$, p95 latency $\le 50\text{ ms}$, 100% organs active, decision-pipeline clean).
* **Stage 4 — Autopoietic / Lifelong Memory & Persistence ("Remember & Develop"):** FUTURE MILESTONE (Online R-STDP synaptic plasticity, Holographic HDC long-term memory, GIS-901 state compounding across lifespans).
* **Stage 5 — Metacognition & Permission-Gated Self-Modification ("Understand Myself & Improve"):** FINAL MATURITY ("The Witness" introspective failure-pattern analysis, causal attribution, permission-gated self-improvement).

---

## Architectural Invariants (Zero-Tolerance)

1. **No Roadmap Mutation Without Explicit User Approval:** No agent may rename stages, delete stages, invent milestones, or jump ahead.
2. **Current-Stage Gate:** Always declare alignment: North Star, Current Stage (Stage 3), Current Subproblem (Stage 3.0 Pre-Flight). Jumping ahead triggers an immediate STOP.
3. **No Free-Ride Capability Inheritance:** Stage 3 cannot inherit unproven capabilities simply because Stage 2's overall dashboard was green. Every capability must demonstrate downstream behavioral necessity.
4. **Exact Executable Timestep Rule:** Derive `dt` directly from simulation configuration (`model.opt.timestep * substeps`); never assume a hardcoded 0.0333 s.
5. **Unification Over Fragmentation:** All capabilities are organs grown for the **ONE UNIFIED CANONICAL ORGANISM** ([`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py) / [`brain/carl_embodied_organism.py`](file:///d:/ebca/brain/carl_embodied_organism.py)) on the zero-copy agent bus. Never create disconnected benchmark-only scripts.
6. **Fail-Closed Acceptance & Pre-Registration:** Thresholds, sample counts, and statistical tests must be pre-registered BEFORE evaluation. No compensatory scoring; no threshold relaxing.
7. **Decision-Pipeline Isolation Invariant:** Zero simulator coordinates (`qpos`, `qvel`, `qacc`, `geom_xpos`, `mj_ray`) permitted inside the active cognitive decision loop. Spawn pose is initialized once. Hardware emulation remains cleanly quarantined at the HAL/environment boundary.
8. **Strict Terminology:** Use **"2,114-unit neuromorphic computational architecture"** (never "biological brain", "machine consciousness", or "emergent sentience").
