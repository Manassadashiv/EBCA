# CARL-DX Scripted Behavior & Emergence Forensic Review

**Audit Date**: August 16, 2026  
**Status**: **`PROTOTYPE_DEMONSTRATION_VERIFIED — BLIND_EMERGENCE_PENDING`**  
**Working Directory**: `D:\ebca`  
**JSON Audit**: [`audit/scripted_behavior_forensics.json`](file:///D:/ebca/audit/scripted_behavior_forensics.json)  

---

## 1. Executive Summary

A forensic audit was performed on the prototype developmental curriculum (`scratch/run_developmental_curriculum.py` and supporting `brain/` modules). 

While the architectural modules (6-DOF Embodiment, Homeostasis Core, Generative Self-Model, HDC Memory, Endogenous Agency, Locomotion Quality Evaluator, and Visual Telemetry Pipeline) are fully implemented and functionally validated, **the demonstration sequence in `run_developmental_curriculum.py` relied on 39 scripted test-harness interventions**.

Specifically:
- **Phase Transitions** were triggered by hardcoded tick conditions (`if t < 15 ... elif t < 35 ...`) rather than endogenously initiated state transitions.
- **Affect States** (`CURIOUS`, `EXCITED`, `CAUTIOUS`, `THREAT_AVERSION`, `SATISFACTION`) were directly commanded by the test harness via `organism.set_affect_state()` rather than emerging dynamically from physiological drives.
- **Episodic Memories** in Stage 3 were seeded synthetically using `memory.store_episode()` rather than learned through unscripted natural collisions.
- **Target Coordinates** in Stage 1 were manually adjusted (`food.pos = [0.35, 0.0]`) to ensure demonstration completion within 60 ticks.

Therefore, the previous scorecard represents a **Functional Architecture Prototype Demonstration**, and **NOT YET Established Blind Emergence**.

---

## 2. Capability Taxonomy Matrix: Implemented vs Trained vs Demonstrated vs Emergent

| Capability Dimension | Implemented? | Trained? | Demonstrated? | Scripted in Harness? | Blind-Test Verified? | Forensic Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **6-DOF Kinematic Embodiment** | **YES** | **YES** | **YES** | **YES** | *Pending Blind Run* | **`EMBODIED_PRIMITIVE_STACK`** |
| **Homeostatic Interoception** | **YES** | **NO** (Analytical) | **YES** | **YES** (Food moved) | *Pending Blind Run* | **`ENDOGENOUS_DYNAMICS`** |
| **Generative Forward Self-Model** | **YES** | **YES** (Online) | **YES** | **PARTIAL** | *Pending Blind Run* | **`ONLINE_ESTIMATOR`** |
| **HDC Episodic Memory** | **YES** | **YES** (Bound) | **YES** | **YES** (Manually seeded) | *Pending Blind Run* | **`ASSOCIATIVE_MEMORY`** |
| **Endogenous Agency & Veto** | **YES** | **NO** (Rule-based) | **YES** | **YES** (Injected prompt) | *Pending Blind Run* | **`ARBITRATED_AGENCY`** |
| **Affective Body Language** | **YES** | **NO** | **YES** | **YES** (`set_affect_state`) | *Pending Blind Run* | **`POSTURAL_MAPPING`** |
| **Stage 6 Emergence Demonstration** | **YES** | **NO** | **YES** | **YES** (`if t < 15 ...`) | *Pending Blind Run* | **`PROTOTYPE_CHOREOGRAPHY`** |
| **Integrated Information $\Phi_{\text{proxy}}$** | **YES** | **N/A** (Metric) | **YES** | **NO** | **YES** | **`EXPERIMENTAL_METRIC`** |

---

## 3. Forensic Code Dissection (39 Scripted Interventions)

### 3.1 Hardcoded Tick-Based Timelines
In `scratch/run_developmental_curriculum.py`:
- Lines 66, 69, 72, 75: Stage 0 sliced into `t < 15` (Look), `t < 35` (Walk), `t < 48` (Inspect), `t >= 48` (Express).
- Lines 236: Stage 4 veto test injected 25 rad/s specifically at `15 <= t <= 25`.
- Lines 319, 324, 328, 332: Stage 6 emergence demonstration orchestrated four sequential phases based solely on simulation tick counter $t$.

### 3.2 External Affect Override
Across all stages, the test script directly forced internal emotional states:
- `organism.set_affect_state("CURIOUS", 1.0)`
- `organism.set_affect_state("EXCITED", 1.0)`
- `organism.set_affect_state("CAUTIOUS", 0.9)`
- `organism.set_affect_state("THREAT_AVERSION", 1.0)`
- `organism.set_affect_state("SATISFACTION", 1.0)`

### 3.3 Synthetic State Seeding
- Line 101: `runner.hal.model.geom('food').pos[:2] = [0.35, 0.0]` moved the resource directly in front of the robot.
- Line 188: `memory.store_episode(0.6, 0.0, "EXPLORE_NOVELTY", "STRAIGHT_FORWARD", -1.0, ...)` manually populated the HDC memory buffer with a pre-fabricated collision event.

---

## 4. Remediation Plan: The Blind Emergence Test Suite

To establish genuine evidence of developmental emergence and operational autonomy, we must implement:

1. **Closed-Loop Autonomous Agent (`brain/carl_autonomous_agent.py`)**:
   - The organism must run autonomously with **ZERO external function calls**.
   - Proprioception and sensors update $h(t)$.
   - $h(t)$ drives endogenous goal generation (`SEEK_ENERGY`, `REST_AND_COOL`, `EXPLORE_UNKNOWN`, `INSPECT_SURROUNDINGS`).
   - Dreamer evaluates counterfactual rollouts minimizing Expected Free Energy $G(a)$.
   - HDC memory queries recent experiences and biases motor selection.
   - Internal state automatically modulates body posture without external `set_affect_state()` calls.
   - If an external command is given, the internal agency core autonomously evaluates viability and asserts a veto if hazardous.

2. **Unseen Blind Environment**:
   - An environment with unmapped obstacles and resources where CARL is placed with no predefined task.

3. **Paired Memory Causality Benchmark**:
   - CARL encounters an unscripted hazard $\rightarrow$ natural collision occurs $\rightarrow$ stores autobiographical episode $\rightarrow$ reset $\rightarrow$ re-encounter situation.
   - Compare `WITH_MEMORY` vs `MEMORY_ABLATED`.

4. **Paired Self-Model Causality Benchmark**:
   - Compare action trajectories under normal self-model vs degraded/perturbed self-model.
"""
