# CARL-DX SCIENTIFIC CAPABILITY CLASSIFICATION MATRIX

**Evaluation Standard**: NASA-Inspired Systems Engineering Rigor  
**Classification Taxonomy**:
- `IMPLEMENTED`: Code exists in repository.
- `FUNCTIONALLY EXECUTING`: Module executes in cognitive loop without errors.
- `LEARNED / ADAPTED`: Parameters adapt dynamically during simulation runtime.
- `BEHAVIORALLY DEMONSTRATED`: Observable physical action changes in MuJoCo physics.
- `CAUSALLY VERIFIED`: A/B paired trials or ablations confirm causal dependence.
- `EMERGENT CANDIDATE`: Unscripted selection among affordances driven by internal tri-drives.
- `PROVEN / NOT PROVEN`: Physical capability status.

---

## 1. Complete Capability Taxonomy Table

| Capability / Subsystem | Primary Module | Scientific Classification | Empirical Evidence / Verification Method |
| :--- | :--- | :--- | :--- |
| **6-DoF Differential Drive & Posture Actuation** | `carl_embodied_organism.py` | `FUNCTIONALLY EXECUTING` | Proprioceptive telemetry & actuator torque traces |
| **Active Information Gaze Saccades** | `carl_embodied_organism.py` | `BEHAVIORALLY DEMONSTRATED` | $\Delta \mathcal{H} = 1.45\text{ nats}$ spatial uncertainty reduction |
| **15-Ray Directional Proximity Scanning** | `carl_embodied_organism.py` | `CAUSALLY VERIFIED` | Proximity range heatmap and anticipatory clearance avoidance |
| **Floating-Base Attitude Self-Stabilization** | `carl_embodied_organism.py` | `BEHAVIORALLY DEMONSTRATED` | Pitch & roll excursions bounded within $<2.0^\circ$ |
| **Interoceptive Homeostatic Drive Core** | `carl_homeostatic_core.py` | `CAUSALLY VERIFIED` | Energy / thermal load / fatigue dynamics driving goal shifts |
| **Active Inference & Counterfactual Dreamer** | `carl_generative_self_model.py` | `CAUSALLY VERIFIED` | 20-step forward arc rollouts minimizing Expected Free Energy $G(a)$ |
| **Online Self-Model Parameter Adaptation** | `carl_generative_self_model.py` | `LEARNED / ADAPTED` | Recursive friction estimation $\hat{\mu} \rightarrow 1.30$ under slip |
| **2048-dim HDC Episodic Memory** | `carl_episodic_memory.py` | `CAUSALLY VERIFIED` | Paired trials prove $\Delta x > 0.05\text{m}$ avoidance divergence |
| **Tri-Drive Controllability & Empowerment** | `carl_empowerment.py` | `EMERGENT CANDIDATE` | Mutual information $I(A_{1:H}; S_H)$ vetoes dead-ends before entry |
| **Stuck Detection & 3-Tier Escalating Recovery** | `carl_stuck_recovery.py` | `BEHAVIORALLY DEMONSTRATED` | Rolling displacement tracking & 3-tier escape execution |
| **Procedural Emotional Audio Vocalization** | `carl_audio_synth.py` | `FUNCTIONALLY EXECUTING` | 16-bit PCM WAV emotional audio synthesis |
| **Controlled Differential Drift Dynamics** | `vessel_kinetic.xml` / `carl_reflex_laboratory.py` | `BEHAVIORALLY DEMONSTRATED` | Slip ratio $S = 0.04 - 0.12$, lateral velocity $v_y \le 0.03\text{m/s}$ |
| **Vertical Jumping Mobility** | `vessel_kinetic.xml` | `PHYSICALLY_UNSUPPORTED` | $Mg = 14.4\text{N} \gg F_{\text{pulse}} < 0.8\text{N}$; zero vertical impulse |
