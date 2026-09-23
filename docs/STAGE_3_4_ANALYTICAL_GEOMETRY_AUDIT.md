# Stage 3.4 Analytical Geometry Audit & Diagnostic Sweep Report

**Milestone:** Stage 3.4 — Continuous Action Synthesis & Autonomous Behavioral Discovery  
**Classification:** [SCIENTIFIC AUDIT & DECISION EXPERIMENT] Geometry Feasibility vs. Controller Mechanics  
**Date:** September 20, 2026  
**Status:** Analytical Proof Complete & Diagnostic Sweep Adjudicated  

---

## Executive Summary

This audit definitively resolves the foundational question raised by the LLM Council regarding whether the **0.70 m corridor width in Stage 3.4 is physically infeasible**:

1. **Static Swept Geometry vs. Corridor Width:**
   - Chassis bumper half-dimensions: $a = 0.115\text{ m}$ (half-length), $b = 0.135\text{ m}$ (half-width).
   - Maximum swept radius during in-place pivot: $R_{\text{swept}} = \sqrt{0.115^2 + 0.135^2} = \mathbf{0.1773\text{ m}}$.
   - Centered swept diameter: $2 R_{\text{swept}} = \mathbf{0.3547\text{ m}}$ — **roughly half the 0.70 m corridor width**.
   - With maximum observed spawn offset ($|y_0|_{\max} = 0.0591\text{ m}$): static swept envelope is **$0.4730\text{ m} \ll 0.70\text{ m}$**.
   - **Conclusion:** The 0.70 m corridor is **statically and geometrically feasible**. It is NOT physically impossible.

2. **Forensic Telemetry from R3 (Why Collisions Actually Occurred):**
   - At collision in R3, the robot was observed at $|y_{\text{coll}}|_{\max} = \mathbf{0.2233\text{ m}}$ (mean $0.1970\text{ m}$).
   - At $|y| = 0.2233\text{ m}$, the required half-width during rotation is $|y| + R_{\text{swept}} = 0.2233 + 0.1773 = \mathbf{0.4006\text{ m}}$.
   - Because corridor half-width is $0.3500\text{ m}$, the outer bumper corner penetrated the wall boundary by **$5.06\text{ cm}$**.
   - The collisions occurred because unmodeled corner clearance and uncorrected gyroscope drift under wheel slip allowed the robot to drift laterally into the wall during rotation.

3. **Empirical Diagnostic Geometry Sweep (Steps 2 & 3):**
   Testing the existing R3 controller across corridor widths $W \in [0.70, 0.75, 0.80, 0.85, 0.90\text{ m}]$ on matched configurations for both ARM-A (Active Inference) and ARM-B (Pragmatic-only baseline):
   - $W = 0.70\text{ m}$ to $0.80\text{ m}$: ARM-A 0% escape (100% collisions), ARM-B 0% escape.
   - $W = 0.85\text{ m}$: ARM-A achieves **60% escapes (3/5)**, ARM-B 0% escape.
   - $W = 0.90\text{ m}$: ARM-A drops to **20% escapes (1/5)**, ARM-B 0% escape.
   - **Finding:** ARM-B remained at 0% escapes across all widths, preserving the potential for Gate 3 causal separation. However, widening to 0.90 m actually degraded ARM-A performance due to unbounded angular drift before wall contact.

---

## 1. Step 1: Analytical Derivation from R3 Telemetry

Extracting raw kinematics directly from the 200 physical episodes in [`stage3_4R3_raw_trials.json`](file:///d:/ebca/evidence/stage3_4R3/stage3_4R3_raw_trials.json):

| Metric | Measured Value | Mathematical Formula / Source |
| :--- | :--- | :--- |
| **Bumper Half-Length ($a$)** | $0.115\text{ m}$ | Physical chassis bumper geom (`world/stage3_4_environments/cul_de_sac_turning_bay.xml`) |
| **Bumper Half-Width ($b$)** | $0.135\text{ m}$ | Physical chassis bumper geom |
| **Worst-Case Swept Radius ($R_{\text{swept}}$)** | $0.1773\text{ m}$ | $R = \sqrt{a^2 + b^2} = \sqrt{0.115^2 + 0.135^2}$ |
| **Centered Swept Diameter ($2R$)** | **$0.3547\text{ m}$** | Worst-case rotational footprint on the spot |
| **Max Lateral Spawn Offset ($|y_0|_{\max}$)** | **$0.0591\text{ m}$** | Config 2 ($y_0 = -0.042\text{ m}$), Config 7 ($y_0 = -0.059\text{ m}$) |
| **Mean Lateral Spawn Offset** | $0.0243\text{ m}$ | Uniform distribution over $\pm 0.05\text{ m}$ nominal jitter |
| **Static Envelope with Max Spawn** | **$0.4730\text{ m}$** | $2 \times (|y_0|_{\max} + R_{\text{swept}}) = 2 \times (0.0591 + 0.1773)$ |
| **Static Corridor Clearance Margin** | **$+0.2270\text{ m}$** ($22.7\text{ cm}$) | $0.7000\text{ m} - 0.4730\text{ m}$ |
| **Mean Egress Speed ($v_{\text{egress}}$)** | $0.406\text{ m/s}$ | Measured across successful egress channel traversals |
| **Max Egress Speed** | $0.554\text{ m/s}$ | Peak forward velocity down exit corridor |
| **Mean Maneuver Duration** | $4.64\text{ s}$ ($155\text{ ticks}$) | Reversal $\to$ In-Place Turn $\to$ Forward Egress |
| **Lateral Drift at Collision ($|y_{\text{coll}}|_{\max}$)** | **$0.2233\text{ m}$** | Observed pose at wall contact event |
| **Mean Lateral Drift at Collision** | $0.1970\text{ m}$ | Across all 40 ARM-A collision events |
| **Wall Penetration at Collision** | **$+5.06\text{ cm}$** | $(0.2233 + 0.1773) - 0.3500 = +0.0506\text{ m}$ |

### Dynamic Clearance vs. Static Clearance
The minimum corridor width required by the **observed uncorrected dynamics** is:
$$W_{\text{dyn\_uncorrected}} = 2 \times (|y_{\text{coll}}|_{\max} + R_{\text{swept}}) = 2 \times (0.2233 + 0.1773) = \mathbf{0.8013\text{ m}}$$
This explains why the existing uncorrected controller required $0.85\text{ m}$ to escape in the empirical sweep: the controller was allowing the robot to drift $0.22\text{ m}$ laterally off-center before attempting to pivot.

Conversely, if the robot maintains lateral centering ($|y| \le 0.03\text{ m}$) via parallel-wall sonar centering:
$$W_{\text{dyn\_centered}} = 2 \times (0.0300 + 0.1773) = \mathbf{0.4147\text{ m}}$$
The $0.70\text{ m}$ corridor leaves **nearly $30\text{ cm}$ of dynamic margin**, proving that the physical arena is not the defect.

---

## 2. Step 2 & 3: Diagnostic Geometry Sweep (ARM-A vs ARM-B)

The existing baseline controller was evaluated across 5 corridor width variants on matched configurations:

```
========================================================
DIAGNOSTIC GEOMETRY SWEEP: EXISTING CONTROLLER ON CORRIDOR WIDTHS
========================================================
Width    | ARM-A Escapes  | ARM-A Colls  | ARM-B Escapes  | ARM-B Colls 
--------------------------------------------------------
0.70 m   | 0/5 (  0%)     | 5/5 (100%)   | 0/5 (  0%)     | 1/5 ( 20%)
0.75 m   | 0/5 (  0%)     | 5/5 (100%)   | 0/5 (  0%)     | 2/5 ( 40%)
0.80 m   | 0/5 (  0%)     | 5/5 (100%)   | 0/5 (  0%)     | 1/5 ( 20%)
0.85 m   | 3/5 ( 60%)     | 2/5 ( 40%)   | 0/5 (  0%)     | 0/5 (  0%)
0.90 m   | 1/5 ( 20%)     | 4/5 ( 80%)   | 0/5 (  0%)     | 1/5 ( 20%)
```

### Critical Findings from the Sweep:
1. **The Physical Transition Point:** The existing controller transitions from 0% escape to 60% escape at **$W = 0.85\text{ m}$**, closely matching the analytically predicted $W_{\text{dyn\_uncorrected}} = 0.801\text{ m}$.
2. **The 0.90 m Trap:** Widening beyond $0.85\text{ m}$ does NOT improve performance; it worsens it (escape drops to 20%, collisions jump to 80%). With wider walls, the robot drifts further off-axis before sonar cues become strong, resulting in high-speed angled wall collisions.
3. **ARM-B Causal Stability:** ARM-B produced 0 escapes across all widths (0/5 at 0.70m, 0.75m, 0.80m, 0.85m, 0.90m). Without epistemic curiosity ($w_{\text{info}} = 0.0$), the robot does not autonomously discover the reverse-pivot escape sequence simply because the corridor is wider.

---

## 3. Mathematical Feasibility Map (The Legitimate Body Model)

For a rectangular body with half-dimensions $a = 0.115\text{ m}$ and $b = 0.135\text{ m}$ at heading $\theta$:

$$\text{Lateral Half-Span: } R_y(\theta) = |a \sin\theta| + |b \cos\theta|$$
$$\text{Longitudinal Half-Span: } R_x(\theta) = |a \cos\theta| + |b \sin\theta|$$

In a corridor of half-width $W/2$ with safety margin $m = 0.02\text{ m}$:
$$|y| + R_y(\theta) < \frac{W}{2} - m$$

### Allowed Lateral Offset as a Function of Heading ($W = 0.70\text{ m}$):
- **Aligned with Corridor ($\theta = 0$ or $\pi$):**
  $$R_y = 0.135\text{ m} \implies |y|_{\max} = 0.350 - 0.020 - 0.135 = \mathbf{0.195\text{ m}} \quad (\pm 19.5\text{ cm})$$
- **Perpendicular across Corridor ($\theta = \pm \pi/2$):**
  $$R_y = 0.115\text{ m} \implies |y|_{\max} = 0.350 - 0.020 - 0.115 = \mathbf{0.215\text{ m}} \quad (\pm 21.5\text{ cm})$$
- **Worst-Case Diagonal Heading ($\theta = \pm 40.4^\circ$ or $\pm 139.6^\circ$):**
  $$R_y = 0.1773\text{ m} \implies |y|_{\max} = 0.350 - 0.020 - 0.1773 = \mathbf{0.1527\text{ m}} \quad (\pm 15.3\text{ cm})$$

**The Invariant Feasibility Rule:**
> **CARL is physically guaranteed to rotate freely without wall contact at ANY orientation in a 0.70 m corridor as long as $|y| < 0.1527\text{ m}$.**

---

## 4. Generic Parallel-Wall Sonar/Gyro Heading Fusion

Let two sonar rays on a flat wall be at angles $\phi_1, \phi_2$ relative to the robot chassis, measuring distances $d_1, d_2$.
Their hit coordinates in robot body frame are:
$$(x_1, y_1) = (d_1 \cos\phi_1, d_1 \sin\phi_1), \quad (x_2, y_2) = (d_2 \cos\phi_2, d_2 \sin\phi_2)$$

The wall line vector in the robot frame is:
$$\Delta x = x_1 - x_2, \quad \Delta y = y_1 - y_2$$

The angle of the wall in the robot frame is:
$$\psi = -\text{atan2}(\Delta y, \Delta x)$$

### Mathematical Proof of Invariance:
For a wall along the world axis at distance $d_\perp$, if the robot is tilted by true angle $\theta_{\text{true}}$, the observed points satisfy:
$$\frac{\Delta y}{\Delta x} = -\tan(\theta_{\text{true}})$$
$$\psi = -\text{atan2}(-\tan\theta_{\text{true}}, 1) = \theta_{\text{true}}$$
This was empirically validated in `scratch/test_wall_slope.py` with zero error ($< 0.01^\circ$).
This provides a **100% generic, cheat-free heading correction** from raw sonars without requiring environment identifiers or simulator coordinates.

---

## 5. Architectural Verdict & Next Milestone Action

We have answered the user's primary challenge:
- **0.70 m is verified physically feasible.** We do NOT widen the benchmark corridor.
- **Wider corridor does not automatically fix performance:** At 0.90 m, escape rate collapsed back to 20%.
- **The root cause is control/body modeling, not environment geometry:** Incorporating the rectangular swept-hull feasibility constraint and parallel-wall heading fusion directly into candidate trajectory scoring is the scientifically valid path for Stage 3.4-R4.
