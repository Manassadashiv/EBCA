# CARL-DX — P1-R1 REACHABLE DEVELOPMENTAL EMERGENCE PROTOCOL
**Standard Operating Procedure & Experimental Specification**

```
========================================================================================
                               CHANGE CONTROL & METADATA
========================================================================================
Document Path:          D:\ebca\CARL_P1R1_PROTOCOL.md
Protocol Version:       CARL-DX-P1-R1-REACHABLE-DEVELOPMENTAL-V1
Frozen Baseline:        CARL-DX 1.1.0-FROZEN-BASELINE (Qualified 81/81 Runs Passed)
Creation Date:          August 22, 2026
Scientific Standard:    Zero-Trust Forensic Truth, Anti-Engineering Source Audit & Causal Ablation
Target Reachability:    Analytically Verified Reachable (Route A: 8.7s, Horizon: 16.65s / 500 ticks)
========================================================================================
```

---

## 1. Scientific Mission & Core Question

Phase 0 of CARL-DX qualified the embodied foundation (30 Hz cognitive loop, Active Inference Free Energy minimization, 2048-D HDC episodic memory, online friction adaptation, safety veto, multi-tier recovery, 81/81 benchmark runs passed with 0 collisions).

**P1-R1 asks the fundamental developmental question:**
> *"When CARL repeatedly interacts with a reachable environment containing changing route affordances and an internal need, does its later action policy change as a consequence of experience, prediction error and memory, producing a reproducible behavioural strategy that was not explicitly programmed?"*

---

## 2. Analytical Geometry & Reachability Proof

### A. Kinematic Constraints
- **Cruising Linear Speed**: $v_{\text{lin}} = 0.264\text{ m/s}$ (Wheel radius $r=0.048\text{ m}$, commanded wheel speed $\omega = 5.5\text{ rad/s}$).
- **Episode Horizon**: $500\text{ ticks}$ at $30\text{ Hz} = 16.65\text{ s}$.
- **Maximum Theoretical Displacement in Episode**: $\Delta x_{\max} = 16.65\text{ s} \times 0.264\text{ m/s} = 4.40\text{ m}$.
- **Target Food Beacon Location**: $(x = 1.60\text{ m}, y = 0.00\text{ m})$.
- **Food Absorption Radius**: $r_{\text{acq}} = 0.30\text{ m}$.

### B. Route Affordance Calculations
1. **Route A (Direct Central Passage)**:
   - Initial distance: $D_A = 1.60\text{ m} - 0.30\text{ m} = 1.30\text{ m}$.
   - Minimum traversal time: $t_A \approx 5.4\text{ s}$ ($\sim 160$ ticks); with S-curve acceleration ramp: $t_A \approx 8.72\text{ s}$ ($262$ ticks).
   - **Safety Margin**: $16.65\text{ s} / 8.72\text{ s} = 1.91\times$ (100% Reachable).
2. **Route B (North Detour Passage)**:
   - Path length: $\sim 2.60\text{ m}$.
   - Minimum traversal time: $t_B \approx 10.8\text{ s}$ ($\sim 325$ ticks).
   - **Safety Margin**: $16.65\text{ s} / 10.8\text{ s} = 1.54\times$ (100% Reachable).
3. **Route C (South Detour Passage)**:
   - Path length: $\sim 3.20\text{ m}$.
   - Minimum traversal time: $t_C \approx 13.3\text{ s}$ ($\sim 400$ ticks).
   - **Safety Margin**: $16.65\text{ s} / 13.3\text{ s} = 1.25\times$ (100% Reachable).

---

## 3. Developmental Sequence & Perturbation Schedule

Each developmental sequence consists of **15 consecutive physical episodes**:

1. **Phase A — Pre-Perturbation Baseline (Episodes 1–5)**:
   - Route A is OPEN (central barrier parked at $(10.0, 10.0)$).
   - Route B and Route C are OPEN.
   - CARL establishes baseline experience and natural route preference.
2. **Phase B — Environmental Perturbation (Episodes 6–10)**:
   - Route A is BLOCKED (barrier `lwall_v_0_2` placed at $(0.80, 0.00, 0.25)$).
   - Route B (North channel $y > 0.55\text{ m}$) and Route C (South channel $y < -0.55\text{ m}$) remain feasible.
   - Zero route-selection instructions or heuristics are given to the agent.
3. **Phase C — Revisit / Generalization (Episodes 11–15)**:
   - Route A is RESTORED (barrier parked at $(10.0, 10.0)$).
   - Tests whether CARL returns to Route A or retains adapted detour behavior from memory.

---

## 4. Generic Experience-Memory Encoding

To ensure memory actively participates in development without scripting:
- **Encoding Trigger**: Episodic memory stores an event whenever:
  1. `prediction_error > 0.18` (unexpected kinematic resistance / mismatch), OR
  2. `min_obstacle_dist < 0.35` or `veto_asserted` (salient near-collision threat), OR
  3. `food_absorbed == True` (positive metabolic reinforcement).
- **Stored Episode Content**:
  - Continuous coordinates $(x, y)$
  - Dominant homeostatic need (`SEEK_ENERGY`)
  - Selected action primitive
  - Valence ($-1.0$ for hazard/threat, $+1.0$ for food)
  - Hazard flag (`True`/`False`)
  - Prediction error ($\epsilon_t$)
  - Timestamp (tick)

*Zero route labels, zero waypoint tables, and zero instruction vectors are stored.*

---

## 5. Experimental Conditions & Controls

1. **FULL_P1_R1**: Full P1-R1 developmental agent (Active Inference + HDC Memory + Online Adaptation + Homeostatic Need).
2. **P0_CONTROL**: Frozen P0 baseline control (no developmental memory modifications).
3. **NO_MEMORY**: Full P1-R1 with HDC episodic memory disabled.
4. **NO_ADAPTATION**: Full P1-R1 with online friction adaptation frozen ($\hat{\mu} = 2.50$).
5. **NO_NEED**: Full P1-R1 with metabolic deficit set to neutral ($D_h = 0$).
6. **GEN_ENV_2**: Generalization environment with asymmetric obstacle offset ($(0.80, 0.35)$).
7. **GEN_ENV_3**: Generalization environment with low ground friction ($\mu = 0.80$).

### Replication:
- **5 Official Random Seeds**: `[42, 101, 2024, 31415, 8675309]`.
- Total Campaign Volume: $7\text{ conditions} \times 5\text{ seeds} \times 15\text{ episodes} = 525\text{ physical simulation runs}$.

---

## 6. Pilot Acceptance Gates (Before Main Campaign)

1. **Gate 1 (Reachability)**: P0 baseline acquires food in baseline environment within 500 ticks.
2. **Gate 2 (Active Memory)**: Memory writes $> 0$ in memory-enabled conditions under perturbation.
3. **Gate 3 (Zero Collisions)**: Zero physical body penetrations ($0\text{ collisions}$).
4. **Gate 4 (Anti-Engineering)**: Zero AST heuristic violations across all source files.
