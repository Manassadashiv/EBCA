# CARL-DX FINAL ARCHITECTURE TRUTH TABLE & MECHANISM DECONSTRUCTION

**Mission Standard**: NASA-Inspired Systems Engineering Rigor  
**Purpose**: Absolute deconstruction of all mechanisms in CARL-DX, explicitly separating engineered heuristics from adaptive and emergent processes.

---

## 1. Complete Mechanism Truth Table

| Subsystem / Feature | Mechanism Type | Code Location | What is Explicitly Engineered (Heuristic / Rule) | What is Dynamically Learned / Adapted | Proven Status | Most Likely Alternative Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Locomotion Kinematics** | Differential Drive S-Curve Filter | `carl_embodied_organism.py:80-140` | Wheel radius ($r=0.048$), track width ($b=0.230$), S-curve acceleration limit ($10.0\text{ rad/s}^2$) | None (Fixed kinematics) | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Standard industrial differential drive controller |
| **Active Gaze Saccades** | Uncertainty-Weighted Scan | `carl_autonomous_agent.py:210-225` | Periodic sweep $\sin(0.10 t)$ in open space, sinusoidal scan $\sin(0.25 t)$ near obstacles, bearing tracking when target visible | Dynamic target bearing tracking | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Heuristic head sweep schedule with target tracking |
| **Endogenous Goal Generation** | Drive-Threshold Priority Arbitration | `carl_endogenous_agency.py:60-140` | Fixed thresholds: `energy < 0.50` -> VIABILITY, `thermal > 0.70` -> REST, `curiosity > 0.40` -> EXPLORE | Priority arbitration weights | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Classical homeostatic state machine / utility agent |
| **Directional Action Selection** | Active Inference & Counterfactual Dreamer | `carl_generative_self_model.py:115-320` | 14 discrete curvature candidate arcs, fixed reward weights ($+25$ velocity, $+40$ corridor centering, $+18$ straight, $-100$ idling) | Counterfactual rollout evaluation across local geometry | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | 20-step Model Predictive Path Integral (MPPI) / Arc Rollout |
| **Operational Action Veto** | Geometric Clearance & Boundary Guard | `carl_endogenous_agency.py:145-235` | Dead-end veto (`front < 1.10 & left < 1.40 & right < 1.40`), obstacle veto (`front < 0.55 & min_dist < 0.40`), boundary veto (`abs(pos) > 2.35`) | Dynamic clearance checks | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Safety filter / Control Barrier Function |
| **Directional Hysteresis Hold** | Steering Persistence Filter | `carl_endogenous_agency.py:40-58` | 6 to 10 tick steering hold ($0.2-0.33\text{s}$) upon initiating curve | None | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Schmitt trigger / low-pass filter preventing chatter |
| **Online Parameter Estimation** | Recursive Slip Adaptation | `carl_generative_self_model.py:95-102` | Update rule multiplying $\hat{\mu} \times 0.98$ on slip ratio mismatch | Ground friction coefficient $\hat{\mu} \in [0.1, 2.5]$ | `ADAPTATION_DEMONSTRATED` | Recursive least squares / parameter estimator |
| **Episodic Memory Biasing** | 2048-dim HDC Associative Recall | `carl_episodic_memory.py:60-140` | Quantized $50\times 50$ grid, $+25$ Free Energy penalty on recalled hazard | Episodic storage of $(x, y, \text{need}, \text{action}, \text{valence})$ | `CAUSALLY_VERIFIED` | Associative vector memory biasing planner cost |
| **Tri-Drive Empowerment** | Reachable State Dispersion Capacity | `carl_empowerment.py:30-95` | 8-probe kinematic rollout covariance $\det(\text{Cov})$, clearance scaling | Mutual information $I(A_{1:H}; S_H)$ estimation | `EMERGENT_CANDIDATE` | Information-theoretic controllability estimation |
| **Stuck Detection & Escalation** | Rolling Window Stall Monitor | `carl_stuck_recovery.py:25-180` | 20-tick displacement window threshold ($\Delta x < 0.02\text{m}$), 3-tier state machine (Reverse $\rightarrow$ Spin $\rightarrow$ Breakout) | Real-time command vs physical translation tracking | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Classical fault detection and recovery protocol |
| **Vertical Jumping** | Physical Impulse Limit | `world/vessel_kinetic.xml` | Wheels and hips have no vertical linear authority; $Mg = 14.4\text{N} \gg F_{\text{dyn}} < 0.8\text{N}$ | None | `PHYSICALLY_UNSUPPORTED` | Physical law: rigid wheeled robot without vertical pistons cannot jump |
| **Affect & Audio Expression** | State-Mapped Audio Synthesizer | `carl_audio_synth.py:90-110` | 5 pre-computed procedural WAV waveforms mapped to neuro-endocrine levels | None | `ENGINEERED_BEHAVIOUR_DEMONSTRATED` | Rule-based procedural audio triggering |
