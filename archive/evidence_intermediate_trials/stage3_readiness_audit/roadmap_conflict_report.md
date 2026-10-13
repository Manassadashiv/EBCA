# Roadmap Consistency Audit: Governance & Documentation Conflicts

**Audit Date:** 2026-09-24  
**Workspace:** `d:\ebca`  
**Standard:** Canonical 5-Stage Developmental Architecture ([`GEMINI.md`](file:///d:/ebca/GEMINI.md) & [`.agents/AGENTS.md`](file:///d:/ebca/.agents/AGENTS.md))  
**Auditor:** Antigravity Agentic Audit Subsystem  
**Status:** **DIAGNOSTIC REPORT ONLY — ZERO FILES MUTATED**

---

## 1. The Canonical Reference Standard

Per the immutable project rules in [`GEMINI.md`](file:///d:/ebca/GEMINI.md) and [`.agents/AGENTS.md`](file:///d:/ebca/.agents/AGENTS.md), the only authoritative roadmap definition is:

* **Stage 1 — Sensorimotor Grounding & Body Babbling:** **CERTIFIED ✅**
* **Stage 2 — Generative World & Self Modeling:** **CERTIFIED (Scope-Bounded Substrate) ✅**
* **Stage 3 — Continuous Action Synthesis & Behavioral Discovery:** **ACTIVE MILESTONE ⏳**
  * Stage 3.0 — Pre-Flight Integrity Lock & Code Hygiene Purge (**Certified ✅**)
  * Stage 3.1 — CANN Causal Coupling (**Certified ✅**)
  * Stage 3.2 — Counterfactual Trajectory Fidelity & Spatial Memory Necessity (**Certified ✅**)
  * Stage 3.3 — Continuous Action Synthesis (MPPI) (**Certified ✅**)
  * Stage 3.4 — Autonomous Behavioral Discovery under Active Inference (**Active; Re-unification Steps 1 & 2 Complete; Behavioral Gate Failed Closed ❌**)
  * **Stage 3.5 — Physical Perturbation & Environmental Adaptation** (Friction drops $\mu=0.2$, torque loss, wheel slip; dynamic exploration via endocrine Cortisol/NE)
  * **Stage 3.6 — Behavioral Synergy Formation & Physarum Routing** (HDC motor synergy clustering; Physarum plasmodial flow equations to prune dead-ends)
  * **Stage 3.7 — Multi-Modal Perception, Canonical Integration & Adversarial Acceptance** (Ingest offscreen RGB from `eye_cam` retina via `CarlVisionNet`; active head gaze scanning; full canonical organism integration; 50-episode frozen acceptance suite)
* **Stage 4 — Autopoietic / Lifelong Memory & Persistence:** FUTURE MILESTONE
* **Stage 5 — Metacognition & Permission-Gated Self-Modification:** FINAL MATURITY

---

## 2. Identified Roadmap Conflicts Across the Workspace

### Conflict 1: The 9-Phase $P0 \to P8$ Legacy Roadmap
* **Conflicting File:** [`docs/architecture/CARL_SLIDE_19_ROADMAP_NOTES.md`](file:///d:/ebca/docs/architecture/CARL_SLIDE_19_ROADMAP_NOTES.md) (and corresponding slides in older decks).
* **Conflicting Definition:**
  * Defines an 8-phase progression: $P0$ (Embodied Foundation), $P1$ (Individual Emergence: LSM, STDP, 4-factor endocrine), $P2$ (Sensory & Spatial: Vision, Grid/Place cells), $P3$ (Adaptive Routing: Physarum), $P4$ (Social), $P5$ (Swarm), $P6$ (Metacognition), $P7$ (Morphological Co-Evolution), $P8$ (Sim-to-Real).
* **The Conflict:**
  * Places **Endocrine kinetics in Phase P1** (whereas canonical places it in **Stage 3.5**).
  * Places **Grid/Place cells in Phase P2** (whereas grid cells were certified as part of the 2,114-unit CANN substrate in **Stage 2.1B**).
  * Places **Vision in Phase P2** (whereas canonical places optical vision in **Stage 3.7**).
  * Places **Physarum in Phase P3** (whereas canonical places it in **Stage 3.6**).
* **Impact:** Any reader or slide viewer comparing Slide 19 notes with the canonical architecture will see contradictory numbering and misplaced milestones.

---

### Conflict 2: Legacy "Stage 1.4 Endocrine" References
* **Conflicting Files:** [`scratch/dump_slides.txt`](file:///d:/ebca/scratch/dump_slides.txt) (line 3: *"Endocrine System & Neuromodulatory Dynamics (Stage 1.4 & Stage 3.5)"*).
* **The Conflict:**
  * In early exploratory drafts, endocrine dynamics were attempted during Stage 1 as "Stage 1.4".
  * In the formal Stage 1 certification, Stage 1 was strictly bounded to anonymous motor babbling (Stage 1.0), linear momentum (Stage 1.5), and kinematic slip estimation (Stage 1.6). Endocrine modulation was formally deferred to **Stage 3.5**.
* **Impact:** Confuses reviewers about whether endocrine modulation is a Stage 1 foundation or a Stage 3.5 perturbation adaptation organ.

---

### Conflict 3: The Legacy Monolithic `carl_simulation.py` Runner
* **Conflicting File:** [`carl_simulation.py`](file:///d:/ebca/carl_simulation.py) (lines 43–50, 520–540, 1030–1070).
* **The Conflict:**
  * `carl_simulation.py` instantiates modules from almost every stage simultaneously:
    - `WorldModelImaginationEngine` (Stage 2)
    - `ConceptGenesisEngine` (Stage 5 concept formation)
    - `WitnessConsciousnessStream` (Stage 5 metacognition)
    - `REMSleepConsolidationEngine` (Stage 4 sleep consolidation)
    - `EpigeneticEvolutionEngine` (Legacy Phase P7)
    - `MorphologicalAdaptationEngine` (Legacy P0/P1 stub)
    - `ExpressiveVisorEngine` (Cosmetic UI)
    - `SSDLite` object detection (Legacy external vision)
  * It bypasses the canonical organism ([`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py)), directly reads simulator coordinates (`hal.data.qvel`), and executes `adaptation.step_adaptation()` while completely discarding the return values.
* **Impact:** `carl_simulation.py` reflects an outdated, monolithic prototype paradigm that directly contradicts the developmental gating rule: *"No free-ride capability inheritance; capabilities must demonstrate downstream necessity in sequential stages."*

---

### Conflict 4: Legacy Phase 1 Diagnostic Reports & Scripts
* **Conflicting Files:** [`evidence/p1_r1/`](file:///d:/ebca/evidence/p1_r1), [`evidence/p1_r2/`](file:///d:/ebca/evidence/p1_r2), [`docs/reports/phase1_audits/CARL_P1_MASTER_REPORT.json`](file:///d:/ebca/docs/reports/phase1_audits/CARL_P1_MASTER_REPORT.json).
* **The Conflict:**
  * These historical folders document Phase 1 runs under the older $P0 \to P8$ nomenclature from early 2026.
* **Impact:** Historical records; they do not impact the current active code but contribute to confusion if referenced without noting their legacy status.

---

## 3. Summary of Roadmap Integrity

The active governance documents ([`GEMINI.md`](file:///d:/ebca/GEMINI.md), [`.agents/AGENTS.md`](file:///d:/ebca/.agents/AGENTS.md), and [`docs/reports/stage3/CARL_STAGE3_MASTER_ROADMAP_AND_GOVERNANCE.md`](file:///d:/ebca/docs/reports/stage3/CARL_STAGE3_MASTER_ROADMAP_AND_GOVERNANCE.md)) are **100% consistent** regarding the definitions of Stages 3.5, 3.6, and 3.7:
- **Stage 3.5 = Physical Perturbation & Environmental Adaptation**
- **Stage 3.6 = Behavioral Synergy Formation & Physarum Routing**
- **Stage 3.7 = Multi-Modal Perception, Canonical Integration & Adversarial Acceptance**

All conflicts exist exclusively in historical slide reference notes ([`CARL_SLIDE_19_ROADMAP_NOTES.md`](file:///d:/ebca/docs/architecture/CARL_SLIDE_19_ROADMAP_NOTES.md)), legacy monolithic test harnesses ([`carl_simulation.py`](file:///d:/ebca/carl_simulation.py)), and archived early-2026 audit logs. Per user instructions, **no files have been modified or overwritten**.
