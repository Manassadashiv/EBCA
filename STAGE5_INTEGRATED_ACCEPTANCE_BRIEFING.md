# CARL-DX STAGE 5 INTEGRATED ACCEPTANCE & NEW CHAT HANDOFF BRIEFING

**Date:** October 19, 2026  
**Target Milestone:** Stage 5 Master Integrated Organism Acceptance Battery  
**Status:** Ready for Immediate Execution in Fresh Chat Session  

---

## 1. Context & Motivation

In our developmental audit, a critical distinction was identified between Stages 1–4 and Stage 5:
- **Stages 1, 2, 3, and 4** each concluded with a **Full-Organism Physical MuJoCo Acceptance Battery**:
  - *Stage 1:* Closed-loop HAL 6-channel babbling in MuJoCo (`tests/test_stage1_suite.py`).
  - *Stage 2:* 40-episode physical maze acceptance with all 5 organs active (`evidence/stage2_final/stage2_final_scorecard.json`).
  - *Stage 3:* 50-episode master physical acceptance in MuJoCo with `CarlAutonomousOrganismAgent` and all 7 organs active (`tests/run_stage3_7_complete_battery.py`).
  - *Stage 4:* 20-trial multi-lifespan warm-boot compounding in MuJoCo with sleep consolidation (`tests/run_stage4_4_complete_battery.py`).
- **Stage 5 (Phases 5.1–5.4)** tested its mathematical algorithms (introspective surprise, HDC causal attribution, permission gating, and Turrigiano homeostasis) in **isolated/synthetic test harnesses** (`MultiHazardEmbodiedEnvironment`), NOT yet as an integrated whole in the physical MuJoCo simulation!

---

## 2. Immediate Next Task: The Stage 5 Master Integrated MuJoCo Battery

Build and execute `tests/run_stage5_integrated_organism_battery.py`:
1. **Embodied Physical Environment:**
   - Use `CarlStage1HAL` with the canonical MuJoCo arena.
   - Inject **real physical hazards** inside the MuJoCo simulation:
     - Real surface friction drops ($\mu = 0.15$) for dynamic slip.
     - Real physical cul-de-sac dead-end walls.
     - Real visual occlusion (camera noise/blackout).
     - Conflicting motor habit priors (R-STDP misfire).
2. **Unified 8-Organ Organism:**
   - Instantiate `agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=...)`.
   - Verify that **all 8 developmental organs** are active simultaneously:
     1. Stage 1: Kinematic Slip & Wheel Velocity Observer
     2. Stage 2: 2,114-unit CANN Attractor Core (HD Ring + Grid Torus)
     3. Stage 3: Continuous MPPI Active Inference Deliberation Engine
     4. Stage 3.5: Endocrine Hormonal Kinetics (Noradrenaline & Cortisol)
     5. Stage 3.7: $64 \times 64$ Retinal VisionNet & Active Saccadic Head Gaze
     6. Stage 4.1: Three-Factor R-STDP Plasticity (Striatal Habit Bias)
     7. Stage 4.2: 2,048-D FHRR Holographic Episodic Memory (HDC)
     8. Stage 5: The Witness Metacognitive Monitoring, Causal Attribution, and Homeostatic Self-Modification
3. **Acceptance Criteria:**
   - $\ge 90\%$ physical escape rate across 20 physical trials (5 per hazard).
   - $0.0\%$ physical collisions.
   - 100% organ participation verified in every physical step.
   - Measurable online parameter adaptation and homeostatic recovery ($\tau_{\text{homeo}}$).
   - Zero simulator coordinate leaks (AST clean).

---

## 3. Key Files for the New Chat

- **Agent Implementation:** [`brain/carl_autonomous_agent.py`](file:///d:/ebca/brain/carl_autonomous_agent.py)
- **Metacognitive Organ:** [`brain/carl_witness.py`](file:///d:/ebca/brain/carl_witness.py)
- **Physical HAL:** [`brain/carl_stage1_hal.py`](file:///d:/ebca/brain/carl_stage1_hal.py)
- **Reference Physical Battery:** [`tests/run_stage3_7_complete_battery.py`](file:///d:/ebca/tests/run_stage3_7_complete_battery.py)
- **Persistence Engine:** [`brain/carl_gis.py`](file:///d:/ebca/brain/carl_gis.py)

---

## 4. Prompt to Paste in the New Chat

```text
Please read STAGE5_INTEGRATED_ACCEPTANCE_BRIEFING.md. We need to execute the Stage 5 Master Integrated Organism Acceptance Battery in physical MuJoCo (CarlStage1HAL + CarlAutonomousOrganismAgent with all 8 organs active under real physical hazards), bringing Stage 5 up to the same rigorous physical empirical standard as Stages 2, 3, and 4.
```
