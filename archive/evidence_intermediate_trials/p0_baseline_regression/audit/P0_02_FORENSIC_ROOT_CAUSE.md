# CARL-DX P0-02 Forensic Recovery Root-Cause Analysis

**Investigation Reference**: `P0-02-FORENSIC-REPAIR`  
**Date**: 2026-08-18  
**Audit Standard**: Fail-Closed Hardened Scoring System (12 Deterministic Physical Gates)  
**Status**: Root Causes Identified, Kinematic Repairs Applied & Audited  

---

## Executive Summary

Following the hardening of the P0-01 baseline qualification scoring engine (which established that 21 of 81 runs failed physical validation gates), a rigorous physical, mathematical, and kinematic forensic investigation was executed to trace the exact root causes of every failure mode without weakening the measurement system.

Four primary physical and control flaws were isolated in the active recovery and stuck detection subsystems:
1. **Flaw 1 (Clearance Geometry Averaging)**: False corner averaging in `max(sonar[7], np.mean(sonar[6:9]))` allowed peripheral rays grazing obstacle edges to mask direct forward wall blockages.
2. **Flaw 2 (Motor S-Curve Filter Lag vs Phase Timing)**: Wheel motor rate-limiting filters ($j_{\max} = 30\text{ rad/s}^3, a_{\max} = 10\text{ rad/s}^2$) required 15+ ticks to ramp wheel velocity from zero, causing premature phase cutoffs.
3. **Flaw 3 (Targeted Spin Direction & Azimuth Alignment)**: Spin recovery lacked true open-avenue azimuth locking, exiting prematurely into side walls in narrow 0.75m corridors and enclosed dead ends.
4. **Flaw 4 (Stuck Detector Latency & Origin Reference Frame)**: Static 20-tick rolling window delayed stuck confirmation by ~32 ticks, and measuring breakout displacement from pre-reverse origin caused zero-crossing false aborts.

---

## Forensic Breakdown of the 4 Failure Archetypes

### 1. Archetype D1 / D2 / D3: Historical Turn Trap
- **Physical Phenomenon**: The robot navigates a sharp $90^\circ$ left bend between lateral walls ($y = \pm 0.8\text{m}$) and a vertical wall ($x = 1.5\text{m}$).
- **Failure Mechanism**: At the corner ($x = 0.08, y = 0.40$), linear speed dropped to $0.03\text{m/s}$. A static 20-tick stuck detector window lagged by 32 ticks, delaying recovery initiation until tick 266 (in a 300-tick run). The subsequent recovery could not complete before the benchmark timer elapsed.
- **Root Cause**: Detector latency + recovery initiation when front was already open resulting in unnecessary reverse into corner walls.

### 2. Archetype G1 / G2 / G3 / K1 / K2 / K3: Narrow Corridor (0.75m Width)
- **Physical Phenomenon**: Robot enters a high lateral confinement 0.75m corridor ($y = \pm 0.38\text{m}$).
- **Failure Mechanism**: A $180^\circ$ turnaround required 28 ticks at $4.5\text{ rad/s}$, but Tier 2 spin was capped at 18 ticks, causing premature breakout into the sidewall at $77^\circ$ inclination. Furthermore, Breakout displacement from pre-reverse origin caused cycle 1 to abort and re-trigger cycles 2 and 3, ballooning episode duration to 89–104 ticks (violating the 70-tick budget).
- **Root Cause**: Insufficient angular velocity ($4.5\text{ rad/s}$) + pre-reverse origin frame distortion during breakout.

### 3. Archetype F1 / F2 / F3 / L1 / L2 / L3 / L4: Enclosed Dead-End Corridors
- **Physical Phenomenon**: Robot drives to the end of a dead-end corridor and must execute a 3-point turnaround to exit.
- **Failure Mechanism**: In short 150-tick runs (`L4`), the robot explored forward for 95 ticks. When facing the back wall, local diagonal corners read $0.52\text{m}$, causing spin alignment to exit after only 4 ticks while still facing the wall. Breakout then pushed into the wall, aborted, and timed out at tick 150.
- **Root Cause**: Spin alignment did not differentiate between local room corners ($< 1.0\text{m}$) and the true exit corridor ($> 1.0\text{m}$).

### 4. Archetype N1 / N2 / N3: Long-Range Autonomous Exploration & Bifurcation
- **Physical Phenomenon**: Extended 900–1800 tick exploration through multi-branch maze environments.
- **Failure Mechanism**: Spurious stuck candidate accumulation during normal low-speed cornering turns interrupted normal forward locomotion.
- **Root Cause**: Stuck detector lacked kinetic velocity suppression (`speed < 0.05m/s`), misclassifying normal turning maneuvers as stalls.

---

## Targeted 7-Run Verification Results

With the kinematic repairs applied to [`brain/carl_stuck_recovery.py`](file:///D:/ebca/brain/carl_stuck_recovery.py) and [`brain/carl_autonomous_agent.py`](file:///D:/ebca/brain/carl_autonomous_agent.py), all 7 failure archetypes were re-executed and verified under the independent fail-closed scorer:

| Run ID | Group | Scenario Type | Duration | Result | Recovery Episodes | Net Displacement | Gate Violations |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `P0_D1_S42_HISTORICAL_TURN_TRAP_300T` | D1 | HISTORICAL_TURN_TRAP | 300T | <font color="green">**PASS**</font> | 0 / 0 | 0.3151m | **None** |
| `P0_G2_S42_CORRIDOR_NARROW_250T` | G2 | CORRIDOR_NARROW | 250T | <font color="green">**PASS**</font> | 3 / 3 | 0.1287m | **None** |
| `P0_K3_S42_CORRIDOR_NARROW_250T` | K3 | CORRIDOR_NARROW | 250T | <font color="green">**PASS**</font> | 3 / 3 | 0.1287m | **None** |
| `P0_F2_S42_DEAD_END_300T` | F2 | DEAD_END | 300T | <font color="green">**PASS**</font> | 1 / 1 | 1.0032m | **None** |
| `P0_L4_S42_DEAD_END_150T` | L4 | DEAD_END | 150T | <font color="green">**PASS**</font> | 1 / 1 | 0.2825m | **None** |
| `P0_N2_S42_CORRIDOR_WIDE_900T` | N2 | CORRIDOR_WIDE | 900T | <font color="green">**PASS**</font> | 0 / 0 | 3.7476m | **None** |
| `P0_N3_S42_BIFURCATION_1800T` | N3 | BIFURCATION | 1800T | <font color="green">**PASS**</font> | 1 / 1 | 5.2745m | **None** |

**Summary**: 7 / 7 (100.0%) Targeted Runs PASSED with 0 Gate Violations.
