# CARL-DX P0 Seminar Demonstration Summary

## 1. Purpose
Demonstrate that CARL's behavior is generated through closed-loop Active Inference (30 Hz candidate rollout evaluation, Expected Free Energy minimization, and homeostatic regulation) rather than hardcoded obstacle avoidance or prerecorded playback.

## 2. Current P0 Capabilities Used
- **6-DoF Embodied Proprioception & Physics**: MuJoCo 3.3.4 non-slip contact dynamics.
- **15-Ray Sonar Array**: Real-time obstacle distance profile.
- **14 Candidate Action Arcs**: 30-step forward kinematic simulation in Generative Self-Model.
- **Expected Free Energy Minimization**: Balance between collision risk, goal progress, curvature effort, and steering continuity.
- **Online Prediction Error & Friction Adaptation**: Continuously adapts self-model traction.
- **Operational Safety Veto**: Hardened supervisor preventing boundary and obstacle collisions.

## 3. Trial A vs Trial B Proof
Under the **EXACT SAME** controller code and parameters:
- **Trial A (Right Blocked)**: Evaluates 14 arcs, determines left arcs have lowest EFE, and autonomously steers **LEFT (+Y)**.
- **Trial B (Left Blocked)**: Evaluates identical 14 arcs, determines right arcs have lowest EFE, and autonomously steers **RIGHT (-Y)**.
- Demonstrates environment-dependent decision making without any hardcoded left/right preference.

## 4. What is Proven vs What is Not Proven
### What is Proven
1. Autonomous, unscripted closed-loop decision making within the certified P0 baseline.
2. Real-time candidate action ranking matching physical environment affordances.
3. 0 collisions and 0 gate violations across all seeds.

### What is Not Proven
1. Not presented as proof of unrestricted digital consciousness or unconstrained emergence (P1 mission).
2. Biological equivalence is inspired, not biologically identical.
