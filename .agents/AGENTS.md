# CARL-DX Canonical Project Customizations & Invariants

## Persistent Long-Term Memory (Permanent Directive)

### The 5-Stage Master Developmental Architecture
Following the certified completion of Stage 2, all development follows this single, sequential, immutable roadmap:

1. **Stage 1 — Sensorimotor Grounding & Body Babbling ("Learn My Body"):**
   - 6-channel anonymous motor babbling & topology discovery (Stage 1.0).
   - 1-step linear forward momentum model (Stage 1.5).
   - Grounded kinematic slip & ice chatter estimation (Stage 1.6).
   - *Status*: **COMPLETED & CERTIFIED ✅**

2. **Stage 2 — Generative World & Self Modeling ("Learn My World"):**
   - Grounded spatial localization & path integration (Stage 2.1A-R certified).
   - Continuous Attractor Neural Networks (64-HD ring + 1,024-grid torus + 1,026 reservoir, 2,114 units) (Stage 2.1B / 2.1B-R certified).
   - Decoupled grounded world model ($R^2=0.97$) & allocentric raster occupancy memory (Stage 2.2 / 2.2-R2 certified).
   - Prospective continuous trajectory deliberation & rotational swept-cone veto (Stage 2.3-R1 certified).
   - Canonical organism integration (40/40 cleared, 0.00% collisions, p95 40.58 ms, 100% organs active, decision-pipeline AST clean).
   - **Certification Boundary:** Stage 2 certified the integrated sensorimotor, spatial-memory, predictive-deliberation substrate under its defined acceptance tests. **CANN causal coupling and non-LOS memory necessity remain explicitly unproven capabilities carried forward into Stage 3.**
   - *Status*: **COMPLETED & CERTIFIED (Scope-Bounded Substrate) ✅**

3. **Stage 3 — Continuous Action Synthesis & Behavioral Discovery ("Learn How to Behave"):**
   - **Stage 3.0 — Pre-Flight Integrity Lock & Code Hygiene Purge:** Purge dormant `geom_xpos` leak and `qpos` z-height in `carl_embodied_organism.py`, normalize floating base height, 100% clean AST decision-pipeline scan, lock SHA-256 baseline and tensor contracts.
   - **Stage 3.1 — CANN Causal Coupling (Stage 2 Repair Gate):** Wire CANN state into trajectory scoring, run pre-registered CANN Causal Battery (Intact vs Frozen vs Zeroed vs Shuffled; $\Delta \mathbf{u} > 0.15, p < 0.01$).
   - **Stage 3.2 — Counterfactual Trajectory Fidelity & Spatial Memory Necessity (Stage 2 Repair Gate):** Validate predicted rollouts against physical MuJoCo steps ($\le 0.08\text{m}$ error); force the core question (*Does spatial memory contribute information unrecoverable from sonar alone?*) across 5 non-LOS task families (blind corners, cul-de-sacs, backtracking, sonic symmetries, sensor blackouts; require $\Delta \text{Success} \ge 35\%, p < 0.001$).
   - **Stage 3.3 — Continuous Action Synthesis (MPPI):** Continuous trajectory optimization ($M=128, H=15, dt=0.03\text{s}$) over continuous wheel velocities $\mathbf{u} \in [-1.0, 1.0]^2$; evaluate candidates against learned world model and occupancy memory.
   - **Stage 3.4 — Autonomous Behavioral Discovery under Active Inference:** Expected Free Energy ($G = \text{Pragmatic} + \text{Epistemic}$); autonomous synthesis of composite maneuvers without handcoded rules. **(Stage 3.4-R3 200-episode frozen battery adjudicated: FAILED CLOSED ❌ on Gates 1, 2, 3, 4; Gate 5 100% AST clean; active milestone awaiting physical rotational hull clearance resolution)**.
   - **Stage 3.5 — Physical Perturbation & Environmental Adaptation:** Online adaptation to friction drops ($\mu=0.2$), torque loss, and wheel slip; dynamic exploration tuning via endocrine kinetics (Cortisol/NE).
   - **Stage 3.6 — Behavioral Synergy Formation & Physarum Routing:** Cluster recurring trajectories into reusable motor synergies via HDC memory; integrate Physarum plasmodial flow equations to prune dead-ends.
   - **Stage 3.7 — Multi-Modal Perception, Canonical Integration & Adversarial Acceptance:** Ingest offscreen RGB from `eye_cam` retina via `CarlVisionNet`; active head gaze scanning; full canonical organism integration in `carl_autonomous_agent.py`; 50-episode frozen acceptance suite (collision $\le 5\%$, p95 latency $\le 50\text{ ms}$, 100% organs active, decision-pipeline clean).
   - *Status*: **CURRENT ACTIVE STAGE ⏳ (Stage 3.0 Active)**

4. **Stage 4 — Autopoietic / Lifelong Memory & Persistence ("Remember & Develop"):**
   - Synaptic plasticity (R-STDP) + Holographic HDC long-term memory.
   - Persistent state compounding across lifespans via GIS-901.
   - *Status*: **FUTURE MILESTONE**

5. **Stage 5 — Metacognition & Permission-Gated Self-Modification ("Understand Myself & Improve"):**
   - Introspective failure analysis ("The Witness"), forms causal hypotheses, and proposes permission-gated self-improvements.
   - *Status*: **FINAL MATURITY**

---

## Architectural Invariants (Zero-Tolerance)

1. **No Roadmap Mutation Without Explicit User Approval:**
   - No agent may rename stages, add/remove stages, revive obsolete August 2026 roadmaps, reinterpret the current stage, or advance to a later stage without explicit written user approval.
2. **Current-Stage Gate (Task Declaration Protocol):**
   - Every task must declare: North Star, Current Stage (Stage 3), Current Subproblem (Stage 3.0 Pre-Flight), what it advances, and why it does not advance a later stage. Premature work on later stages triggers an immediate STOP.
3. **No Free-Ride Capability Inheritance:**
   - Stage 3 cannot inherit unproven capabilities simply because Stage 2's overall dashboard was green. Every capability must demonstrate downstream behavioral necessity.
4. **Exact Executable Timestep Rule:**
   - The recording/control loop must use the exact executable simulation/control timestep derived directly from model configuration (`model.opt.timestep * substeps`); never assume a hardcoded 0.0333 s.
5. **Unification Over Fragmentation:**
   - Every developmental capability is an organ being grown for the **ONE UNIFIED EMBODIED ORGANISM** ([`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py) / [`brain/carl_embodied_organism.py`](file:///d:/ebca/brain/carl_embodied_organism.py)) on the zero-copy memory bus. Never create disconnected, disposable prototype scripts.
6. **Decision-Pipeline Isolation Invariant:**
   - Zero simulator coordinates (`qpos`, `qvel`, `qacc`, `geom_xpos`, `mj_ray`) permitted inside the active cognitive decision loop. Hardware simulation remains cleanly isolated at the HAL and environment setup boundary.
7. **Strict Terminology:**
   - Use: **"2,114-unit neuromorphic computational architecture"**.
   - NEVER use: *"biological brain"*, *"machine consciousness"*, or *"emergent sentience"*.
   - Use: **"Sensorimotor grounding within recurrent topological inductive biases"**.
