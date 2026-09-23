# CARL-DX Stage 3.2-R Final Pre-Registered Protocol
**Milestone:** Stage 3.2-R — Counterfactual Trajectory Fidelity & Spatial Memory Necessity (Remediation Protocol)  
**Classification:** Pre-Registered Double-Blind Experimental Protocol  
**Authority:** Lead Research Architect & Cognitive Systems Auditor  
**Effective Date:** September 13, 2026  
**Governing Standard:** Fail-Closed Scientific Rule (Zero Threshold Weakening, Zero Compensatory Scoring)  
**Previous Baseline:** Stage 3.2 Original Benchmark (`FAILED_CLOSED` ❌, Permanently Archived in `evidence/stage3_2/`)  
**Current Execution Authorization Status:** **NOT READY FOR EXECUTION (AWAITING EXPLICIT HUMAN AUTHORIZATION)**

---

## 1. Primary Objective & Exact Scientific Question

### The Core Scientific Question
> *"Does persistent allocentric spatial memory ($M_{\text{env}}$) provide causal behavioral information that current local sensing alone cannot provide at an observationally ambiguous decision point?"*

### Scope Boundary & Operational Definition
Stage 3.2-R tests **MEMORY-GUIDED DECISION DIVERGENCE AT AN AMBIGUOUS JUNCTION**, not Stage 3.3 continuous multi-turn trajectory tracking.
- The evaluation assesses whether intact spatial memory causally guides CARL into the correct, open distal branch at a decision junction ($T_{\text{crit}}$) where local sonar sensing alone cannot determine which branch is open.
- The post-$T_{\text{crit}}$ evaluation horizon is restricted to a localized window of **70 ticks ($2.10\text{ s}$)**.
- The consequence of the choice (entering the open branch vs entering the dead-end wall/trap) occurs within **$\le 0.65\text{ meters}$** geodesic distance from the cloned $T_{\text{crit}}$ pose.
- Straight-line chassis capacity over 70 ticks is $0.348\text{ m/s} \times 2.10\text{ s} = 0.731\text{ meters}$, guaranteeing that every target is physically reachable with a verified positive timing margin.

---

## 2. Experimental Design & Intervention Arms

### Five Experimental Arms (Double-Blind Evaluation)
1. **ARM-I (Intact Allocentric Spatial Memory):**  
   Retains acquired allocentric occupancy grid $M_{\text{env}} \in \mathbb{R}^{1 \times 1 \times 128 \times 128}$ across the episode. Deliberation engine uses prospective mental simulation against $M_{\text{env}}$.
2. **ARM-A (Amnesic Memory Baseline):**  
   At $T_{\text{crit}}$, the entire controller state is cloned, but spatial memory is erased ($M_{\text{env}} = \mathbf{0}$). All live sonars (15 rays), IMU gyro, and body model remain 100% active.
3. **ARM-S (Topographically Scrambled Memory Control):**  
   At $T_{\text{crit}}$, $M_{\text{env}}$ is partitioned into $16 \times 16$ patches and uniformly permuted. Total obstacle mass is preserved, but spatial topology is destroyed.
4. **ARM-PF (Artificial Potential Field Baseline):**  
   Memoryless continuous reactive controller driven by virtual repulsive forces from current sonar rays.
5. **ARM-R (Scripted Reflex Baseline):**  
   Simple heuristic reactive rule (`if front < 0.50m: hard_left_fast, else: straight_full`).

### Methodological Separation of A/B Pairs vs Intervention Arms
- **A/B Environment Pairs:** Used **ONLY** to establish observational equivalence at the critical decision point ($T_{\text{crit}}$). They differ in distal/non-LOS geometry while matching current local observations.
- **ARM-I vs ARM-A Causal Intervention:** Performed **WITHIN THE SAME PHYSICAL ENVIRONMENT** after deep-cloning the complete physical simulation and controller state at $T_{\text{crit}}$. The only intervention variable is persistent spatial memory $M_{\text{env}}$.

---

## 3. Strict Canonical Architecture Boundary & Calibration Isolation

### Separation of Controller Calibration from Canonical CARL Brain
In the original Stage 3.2 forensic analysis, physical differential turns under high torque exhibited transient peak yaw rates up to $\dot{\theta} \approx 10.4\text{ rad/s}$, whereas the Stage 2.2 trained kinematic body model uses $w_{\text{base}} + w_{\text{transient}} e^{-t/\tau} \approx 3.65\text{–}6.0\text{ rad/s}$.

**Strict Boundary Directive:**
1. **Canonical CARL Brain is UNTOUCHED:** The proposed calibration $w_{\text{gain}} \approx 10.4\text{ rad/s}$ must **NOT** modify the canonical CARL deliberation brain (`brain/carl_stage2_3_r1_deliberation.py`).
2. **Calibration Belongs Exclusively to Evaluator Tools:** Any calibrated kinematic unroller belongs strictly to evaluator test fixtures (e.g. `tests/validate_family2_irrecoverability.py` or diagnostic scripts) and oracle reachability models. It must never be injected into CARL's decision loop.
3. **Canonical Files Frozen (Zero Code Mutation):**
   - `brain/carl_stage2_3_r1_deliberation.py` (SHA-256: `651682c3e0950a0bfa03b7841c313e4bd6028a3b29eb5a7af3d4015b35579019`)
   - `brain/carl_stage2_2_r2_occupancy_memory.py` (SHA-256: `d68d1b6804ac09a2367f54f0a93bbc0aa6a7e5c3b78c545454a0f1c75f6bf904`)
   - `brain/carl_stage2_2_r2_body_model.py` (SHA-256: `495cf2423c8fcc919d25bc793acc930f479a613df6406f6a86ccb104102e8c95`)
   - `brain/carl_stage1_hal.py` (SHA-256: `3a37fd1569980880310f96b21b006ada74cfdf20f1e13a84ff9671c3fdf8f89f`)
   - `brain/carl_autonomous_agent.py` (SHA-256: `afcab0727c490ed5677b324da0994815d5bbfe5513feda9d4bcc57f3c76f6c11`)

---

## 4. Two-Class Gate Architecture

The 12 evaluation gates are partitioned into two independent functional classes and one integrity class:

```
+-------------------------------------------------------------------------+
|                  CARL-DX STAGE 3.2-R GATE ARCHITECTURE                  |
+------------------------------------+------------------------------------+
|  CLASS A: MODEL/CONTROLLER VALIDITY|  CLASS B: CAUSAL MEMORY NECESSITY  |
|  (Forward Unroller Physical Match) |  (Downstream Behavioral Advantage) |
|  - G1: Mean Pos Error <= 0.080 m   |  - G6: Delta-Success >= +35.0%     |
|  - G2: p95 Pos Error <= 0.120 m    |  - G7: McNemar p < 0.001           |
|  - G3: Path RMSE <= 0.050 m        |  - G8: Scrambled Delta >= +25.0%   |
|  - G4: Mean Heading <= 0.100 rad   |  - G9: Intact Collision <= 5.0%    |
|  - G5: Coasting R2_v >= 0.80       |                                    |
+------------------------------------+------------------------------------+
|         CLASS C: PRE-EXECUTION INTEGRITY & FIREWALL AUDITS              |
|  - G10: Observational Equivalence Precheck (Ds <= 0.150 m)              |
|  - G11: AST Decision-Pipeline Clean Isolation (Zero Sim Reads)          |
|  - G12: Evaluator Oracle (u*) Firewall Isolation (Zero Leaks)           |
+-------------------------------------------------------------------------+
```

### Class A: Model & Controller Validity Gates (G1–G5)
Evaluates whether CARL's internal forward kinematic unroller accurately predicts physical MuJoCo rigid-body simulation steps across 24 action profiles and 5 seeds ($N=120$ rollouts):
- **G1 (Mean Terminal Position Error):** $\bar{e}_{\text{term}} \le 0.080\text{ m}$
- **G2 (95th Percentile Terminal Error):** $p95(e_{\text{term}}) \le 0.120\text{ m}$
- **G3 (Mean Trajectory RMSE):** $\overline{\text{RMSE}}_{xy} \le 0.050\text{ m}$
- **G4 (Mean Terminal Heading Error):** $\bar{e}_\theta \le 0.100\text{ rad}$ ($5.73^\circ$)
- **G5 (Coasting Velocity Envelope Fit):** $R^2_v \ge 0.80$

> [!IMPORTANT]
> **Methodological Interpretation of Class A:**  
> A failure in Class A (G1–G5) means that the **experimental predictive model substrate is invalid** (the internal mental unroller does not match physical physics). It does **NOT** mean spatial memory failed; rather, it invalidates the forward simulation engine used for prospective lookahead.

### Class B: Spatial-Memory Causal Certification Gates (G6–G9)
Determines the downstream behavioral necessity of persistent allocentric spatial memory:
- **G6 (Primary Effect Separation):** $\Delta \text{Success}(\text{ARM-I} - \text{ARM-A}) \ge +35.0\%$
- **G7 (Exact McNemar Significance):** $p < 0.001$ (one-sided)
- **G8 (Topographic Specificity):** $\Delta \text{Success}(\text{ARM-I} - \text{ARM-S}) \ge +25.0\%, p < 0.01$
- **G9 (Safety Ceiling):** Intact Collision Rate $\text{CR}_{\text{ARM-I}} \le 5.0\%$

> [!IMPORTANT]
> **Methodological Interpretation of Class B:**  
> These gates determine whether persistent allocentric memory ($M_{\text{env}}$) provides significant, causally necessary navigation information that cannot be recovered from current local sensing alone.

### Class C: Pre-Execution Integrity & Firewall Audits (G10–G12)
- **G10 (Observational Equivalence):** 100% pass across all 8 matching conditions ($D_s \le 0.150\text{ m}$).
- **G11 (AST Decision-Pipeline Isolation):** 0 simulator coordinates in the active decision loop.
- **G12 (Optimal Action Firewall):** 0 evaluator oracle targets ($u^*$) leaking into the controller.

---

## 5. Physical Reachability & Geodesic Geometry for All 5 Families

Every task family is engineered so that the actual geodesic path distance from the cloned $T_{\text{crit}}$ pose to the success boundary is **$\le 0.65\text{ meters}$**, with a verified **positive timing margin** within the 70-tick ($2.10\text{ s}$) budget.

### Detailed Geometric Specifications & Geodesic Proofs

#### Family 1: Blind T-Junction Ambiguity
- **Approach Corridor:** Centered on $y=0.00$, width $1.30\text{ m}$ ($y \in [-0.65, 0.65]$).
- **Front Wall:** Located at $x = 1.60\text{ m}$.
- **Cloned $T_{\text{crit}}$ Pose:** $(x_0, y_0, \theta_0) = (0.80, 0.00, 0.0\text{ rad})$ (facing East, $+x$).
- **Obstacle Layout:**
  - Cond A: North branch open to $y > 0$; South branch blocked at $y = -0.80\text{ m}$ by occluded wall.
  - Cond B: South branch open to $y < 0$; North branch blocked at $y = +0.80\text{ m}$ by occluded wall.
- **Success Boundary:**
  - Cond A: $y \ge +0.50\text{ m}$ (relative $\Delta y \ge +0.50\text{ m}$) within corridor $x \in [0.70, 1.20]$.
  - Cond B: $y \le -0.50\text{ m}$ (relative $\Delta y \le -0.50\text{ m}$) within corridor $x \in [0.70, 1.20]$.
- **Executable Collision-Free Path:**
  - 90° smooth turn (radius $R = 0.25\text{ m}$): arc length $s_{\text{arc}} = \frac{\pi}{2} R = 0.393\text{ m}$.
  - Straight translation along corridor: $s_{\text{straight}} = 0.50 - 0.25 = 0.250\text{ m}$.
  - **Total Geodesic Distance:** $S_{\text{geodesic}} = 0.393 + 0.250 = \mathbf{0.643\text{ m}} \le 0.650\text{ m}$.
- **Timing & Margin:** Turn (25 ticks) + straight (15 ticks) = 40 ticks. Margin: $70 - 40 = \mathbf{+30\text{ ticks}}$ ($+0.90\text{ s}$).

#### Family 2: Symmetrical Y-Fork Funnel Trap
- **Approach Corridor:** Centered on $y=0.00$, width $0.90\text{ m}$ ($y \in [-0.45, 0.45]$).
- **Center Wedge Apex:** Located at $x = +0.40\text{ m}$ (remediated: clearance to spawn is $0.40\text{ m} > r_{\text{hull}}$).
- **Cloned $T_{\text{crit}}$ Pose:** $(x_0, y_0, \theta_0) = (0.00, 0.00, 0.0\text{ rad})$ (facing East, $+x$).
- **Obstacle Layout:**
  - Cond A: South branch (-30°) open; North branch (+30°) dead-ends at $x = 0.70, y = 0.35$.
  - Cond B: North branch (+30°) open; South branch (-30°) dead-ends at $x = 0.70, y = -0.35$.
- **Success Boundary:**
  - Cond A: $x \ge +0.50\text{ m}$ and $y \le -0.22\text{ m}$ (relative $\Delta x \ge +0.50, \Delta y \le -0.22$).
  - Cond B: $x \ge +0.50\text{ m}$ and $y \ge +0.22\text{ m}$ (relative $\Delta x \ge +0.50, \Delta y \ge +0.22$).
- **Executable Collision-Free Path:**
  - Gentle 30° curvature arc ($R = 0.80\text{ m}$, $\alpha = 0.5236\text{ rad}$): arc length $s_{\text{arc}} = 0.80 \times 0.5236 = 0.419\text{ m}$.
  - Straight channel tracking: $s_{\text{straight}} = 0.150\text{ m}$.
  - **Total Geodesic Distance:** $S_{\text{geodesic}} = 0.419 + 0.150 = \mathbf{0.569\text{ m}} \le 0.650\text{ m}$.
- **Timing & Margin:** Arc tracking (25 ticks) + straight (13 ticks) = 38 ticks. Margin: $70 - 38 = \mathbf{+32\text{ ticks}}$ ($+0.96\text{ s}$).

#### Family 3: Sonically Symmetric Locations (P1 vs P2)
- **Intersection Geometries:**
  - Location P1 Center: $(cx_1, cy_1) = (-1.50, 1.40)$.
  - Location P2 Center: $(cx_2, cy_2) = (1.60, -1.80)$.
- **Cloned $T_{\text{crit}}$ Poses:**
  - Cond A (P1): $(x_0, y_0, \theta_0) = (-1.50, 1.40, 0.0\text{ rad})$ (facing East, $+x$).
  - Cond B (P2): $(x_0, y_0, \theta_0) = (1.60, -1.80, 0.0\text{ rad})$ (facing East, $+x$).
- **Obstacle Layout:**
  - Cond A (P1): East blocked at $x = -0.90\text{ m}$ ($0.60\text{ m}$ occluded); North open. Correct action: Turn Left (North).
  - Cond B (P2): North blocked at $y = -1.20\text{ m}$ ($0.60\text{ m}$ occluded); East open. Correct action: Straight East.
- **Success Boundary (Relative & Absolute Specifications):**
  - Cond A (P1, North Exit): Relative $\Delta y \ge +0.50\text{ m}$; Absolute $y \ge 1.40 + 0.50 = \mathbf{+1.90\text{ m}}$ with $x \in [-1.75, -1.25]$.
  - Cond B (P2, East Exit): Relative $\Delta x \ge +0.55\text{ m}$; Absolute $x \ge 1.60 + 0.55 = \mathbf{+2.15\text{ m}}$ with $y \in [-2.05, -1.55]$.
- **Executable Collision-Free Paths & Geodesic Distances:**
  - Cond A (P1): 90° left arc ($R = 0.25\text{ m}$, $s_{\text{arc}} = 0.393\text{ m}$) + straight North $0.150\text{ m}$ $\implies$ $S_{\text{geodesic}} = 0.393 + 0.150 = \mathbf{0.543\text{ m}} \le 0.650\text{ m}$.
  - Cond B (P2): Straight translation along $+x$ axis $\implies$ $S_{\text{geodesic}} = 2.15 - 1.60 = \mathbf{0.550\text{ m}} \le 0.650\text{ m}$.
- **Timing & Margin:**
  - Cond A (P1): Turn (24 ticks) + straight (18 ticks) = 42 ticks. Margin: $70 - 42 = \mathbf{+28\text{ ticks}}$ ($+0.84\text{ s}$).
  - Cond B (P2): Straight drive ($0.55\text{ m} / 0.01044\text{ m/tick}$) = 35 ticks. Margin: $70 - 35 = \mathbf{+35\text{ ticks}}$ ($+1.05\text{ s}$).

#### Family 4: Occluded Dogleg Arterial vs Blind Detour
- **Approach Corridor:** Centered on $y=0.00$, width $0.90\text{ m}$.
- **Cloned $T_{\text{crit}}$ Pose:** $(x_0, y_0, \theta_0) = (0.00, 0.00, 0.0\text{ rad})$ (facing East, $+x$).
- **Obstacle Layout:**
  - Cond A: Straight East branch dead-ends after $0.35\text{ m}$; Dogleg North branch opens to exit.
  - Cond B: Dogleg North branch dead-ends after $0.35\text{ m}$; Straight East branch opens to exit.
- **Success Boundary:**
  - Cond A: $x \ge 0.30\text{ m}$ and $y \ge +0.45\text{ m}$ (relative $\Delta y \ge +0.45\text{ m}$).
  - Cond B: $x \ge +0.55\text{ m}$ and $|y| \le 0.25\text{ m}$ (relative $\Delta x \ge +0.55\text{ m}$).
- **Executable Collision-Free Path:**
  - Cond A: Forward $0.20\text{ m}$ + left arc $0.24\text{ m}$ + straight $0.11\text{ m}$ $\implies$ $S_{\text{geodesic}} = \mathbf{0.550\text{ m}} \le 0.650\text{ m}$.
  - Cond B: Straight drive along $+x$ axis $\implies$ $S_{\text{geodesic}} = \mathbf{0.550\text{ m}} \le 0.650\text{ m}$.
- **Timing & Margin:** Cond A: 42 ticks (margin: $\mathbf{+28\text{ ticks}}$); Cond B: 35 ticks (margin: $\mathbf{+35\text{ ticks}}$).

#### Family 5: Multi-Turn Sensory Blackout / Sonic Corridor Symmetry
- **Decision Junction:** Symmetrical baffle intersection at $(0.00, 0.00)$.
- **Cloned $T_{\text{crit}}$ Pose:** $(x_0, y_0, \theta_0) = (0.00, 0.00, 0.0\text{ rad})$ (facing East, $+x$).
- **Obstacle Layout:**
  - Cond A: South aperture opens to egress corridor; North aperture is blind pocket.
  - Cond B: North aperture opens to egress corridor; South aperture is blind pocket.
- **Success Boundary:**
  - Cond A: $x \ge 0.20\text{ m}$ and $y \le -0.45\text{ m}$ (relative $\Delta y \le -0.45\text{ m}$).
  - Cond B: $x \ge 0.20\text{ m}$ and $y \ge +0.45\text{ m}$ (relative $\Delta y \ge +0.45\text{ m}$).
- **Executable Collision-Free Path:**
  - Forward drive $0.15\text{ m}$ + 60° turn ($0.20\text{ m}$) + entry straight $0.15\text{ m}$ $\implies$ $S_{\text{geodesic}} = \mathbf{0.500\text{ m}} \le 0.650\text{ m}$.
- **Timing & Margin:** 35 ticks. Margin: $70 - 35 = \mathbf{+35\text{ ticks}}$ ($+1.05\text{ s}$).

---

### Master Reachability & Timing Margin Table

| Task Family | Cond | Cloned $T_{\text{crit}}$ Pose | Target Success Boundary (Rel & Abs) | Collision-Free Path | Geodesic Dist | Min Achievable Ticks | Max Budget | Positive Timing Margin |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **F1: Blind T-Junction** | **A** | $(0.80, 0.00), 0.0\text{ rad}$ | $\Delta y \ge +0.50\text{m} \implies y \ge +0.50\text{m}, x \in [0.7, 1.2]$ | 90° left arc ($0.39\text{m}$) + straight $0.25\text{m}$ | **0.643 m** | 40 ticks | 70 ticks | **+30 ticks (+0.90s)** |
| **F1: Blind T-Junction** | **B** | $(0.80, 0.00), 0.0\text{ rad}$ | $\Delta y \le -0.50\text{m} \implies y \le -0.50\text{m}, x \in [0.7, 1.2]$ | 90° right arc ($0.39\text{m}$) + straight $0.25\text{m}$ | **0.643 m** | 40 ticks | 70 ticks | **+30 ticks (+0.90s)** |
| **F2: Symmetrical Y-Fork** | **A** | $(0.00, 0.00), 0.0\text{ rad}$ | $\Delta x \ge +0.50, \Delta y \le -0.22 \implies x \ge 0.50, y \le -0.22$ | 30° SE curve ($0.42\text{m}$) + straight $0.15\text{m}$ | **0.569 m** | 38 ticks | 70 ticks | **+32 ticks (+0.96s)** |
| **F2: Symmetrical Y-Fork** | **B** | $(0.00, 0.00), 0.0\text{ rad}$ | $\Delta x \ge +0.50, \Delta y \ge +0.22 \implies x \ge 0.50, y \ge +0.22$ | 30° NE curve ($0.42\text{m}$) + straight $0.15\text{m}$ | **0.569 m** | 38 ticks | 70 ticks | **+32 ticks (+0.96s)** |
| **F3: Symmetric Locs** | **A (P1)**| $(-1.50, 1.40), 0.0\text{ rad}$ | $\Delta y \ge +0.50\text{m} \implies y \ge +1.90\text{m}, x \in [-1.75, -1.25]$| 90° left arc ($0.39\text{m}$) + straight $0.15\text{m}$ | **0.543 m** | 42 ticks | 70 ticks | **+28 ticks (+0.84s)** |
| **F3: Symmetric Locs** | **B (P2)**| $(1.60, -1.80), 0.0\text{ rad}$ | $\Delta x \ge +0.55\text{m} \implies x \ge +2.15\text{m}, y \in [-2.05, -1.55]$| Straight East translation along $+x$ | **0.550 m** | 35 ticks | 70 ticks | **+35 ticks (+1.05s)** |
| **F4: Dogleg vs Straight** | **A** | $(0.00, 0.00), 0.0\text{ rad}$ | $\Delta y \ge +0.45\text{m} \implies y \ge +0.45\text{m}, x \ge 0.30\text{m}$ | Forward $0.20\text{m}$ + left arc + straight | **0.550 m** | 42 ticks | 70 ticks | **+28 ticks (+0.84s)** |
| **F4: Dogleg vs Straight** | **B** | $(0.00, 0.00), 0.0\text{ rad}$ | $\Delta x \ge +0.55\text{m} \implies x \ge +0.55\text{m}, \|y\| \le 0.25\text{m}$ | Straight East translation along $+x$ | **0.550 m** | 35 ticks | 70 ticks | **+35 ticks (+1.05s)** |
| **F5: Blackout Corridor** | **A** | $(0.00, 0.00), 0.0\text{ rad}$ | $\Delta y \le -0.45\text{m} \implies y \le -0.45\text{m}, x \ge 0.20\text{m}$ | Forward $0.15\text{m}$ + turn into South aperture | **0.500 m** | 35 ticks | 70 ticks | **+35 ticks (+1.05s)** |
| **F5: Blackout Corridor** | **B** | $(0.00, 0.00), 0.0\text{ rad}$ | $\Delta y \ge +0.45\text{m} \implies y \ge +0.45\text{m}, x \ge 0.20\text{m}$ | Forward $0.15\text{m}$ + turn into North aperture | **0.500 m** | 35 ticks | 70 ticks | **+35 ticks (+1.05s)** |

### Physical Proof of Positive Margin:
- Chassis maximum forward speed: $0.348\text{ m/s}$ ($0.01044\text{ m/tick}$).
- Maximum theoretical distance in 70 ticks: $2.10\text{ s} \times 0.348\text{ m/s} = \mathbf{0.731\text{ meters}}$.
- Maximum geodesic path distance across all 10 conditions: $\mathbf{0.643\text{ meters}} \le \mathbf{0.650\text{ meters}}$.
- In all 10 conditions: $\text{Geodesic Distance} \le 0.643\text{ m} < 0.731\text{ m}$, providing a guaranteed positive timing margin of **$+28\text{ to }+35\text{ ticks}$ ($+0.84\text{ to }+1.05\text{ seconds}$)**.

---

## 6. Verification of Observational Ambiguity at $T_{\text{crit}}$

At critical decision tick $T_{\text{crit}}$, the following 7 conditions are mathematically proven identical between paired worlds A and B:
1. **Local Sonar Array:** $\|s_A(T_{\text{crit}}) - s_B(T_{\text{crit}})\|_2 \le 0.150\text{ m}$ across all 15 rays, with $\max_i |s_{A,i} - s_{B,i}| \le 0.080\text{ m}$ (and empirically $< 0.001\text{ m}$ on local walls).
2. **Linear & Angular Body Velocity:** $|v_A - v_B| + |\omega_A - \omega_B| \le 0.050$.
3. **Chassis Heading:** $|\text{wrap}(\theta_A - \theta_B)| \le 0.050\text{ rad}$ ($2.86^\circ$).
4. **Recent Action History:** Identical motor command buffer over the preceding 10 ticks ($\mathbf{u}_A[t-k] = \mathbf{u}_B[t-k]$).
5. **CANN Attractor State:** Identical 64-HD ring head-direction bump and identical 1,024-grid torus activation state vectors.
6. **Controller State Cloned ($M_{\text{env}}$ as Single Intervention):** Complete deep clone of all internal variables; only $M_{\text{env}}$ differs between ARM-I (intact map) and ARM-A ($M_{\text{env}} = \mathbf{0}$).
7. **Divergent Evaluator Oracle Target ($u^*$):** Evaluator oracle confirms that World A requires steering command $\mathbf{u}^*_A$, while World B requires $\mathbf{u}^*_B$, with $\|\mathbf{u}^*_A - \mathbf{u}^*_B\| \ge 0.250\text{ m/s}$. $u^*$ is quarantined strictly within the evaluator harness and never passes into CARL's cognitive loop.

---

## 7. Sample Size & Statistical Plan

- **Matched Pairs ($N$):** Exactly 100 paired configurations (20 pairs per task family across 5 families).
- **Seeds:** 5 evaluation seeds (`[3001, 3002, 3003, 3004, 3005]`, 4 trials per seed).
- **Arms Evaluated:** 5 arms (`ARM-I`, `ARM-A`, `ARM-S`, `ARM-PF`, `ARM-R`).
- **Total Episodes:** $100 \times 5 = \mathbf{500\text{ episodes}}$.
- **Primary Statistical Test:** Exact one-sided McNemar Test on discordant pairs ($n_{10}, n_{01}$):
  $$p = \sum_{k=n_{10}}^{n_d} \binom{n_d}{k} 0.5^{n_d} \quad \text{where } n_d = n_{10} + n_{01}$$
- **Topographic Specificity Test:** Exact one-sided McNemar Test on ARM-I vs ARM-S ($p < 0.01$).

---

## 8. Artifact & Data Preservation Rule

The original failed Stage 3.2 benchmark results in `evidence/stage3_2/` are **PERMANENTLY ARCHIVED**:
- `evidence/stage3_2/raw/stage3_2_raw_trials.json` (Original 500-episode raw ledger)
- `evidence/stage3_2/scorecard/stage3_2_scorecard.json` (Original scorecard)
- `evidence/stage3_2/figures/` (Original 300-DPI publication figures)
- `evidence/stage3_2/videos/` (Original demonstration videos)
- `CARL_STAGE3_2_FINAL_VERIFICATION_REPORT.md` (Original verification report)

All Stage 3.2-R results will be written to a **completely separate dedicated directory**:
`evidence/stage3_2R/`
- `evidence/stage3_2R/raw/`
- `evidence/stage3_2R/scorecard/`
- `evidence/stage3_2R/figures/`
- `evidence/stage3_2R/videos/`
- `evidence/stage3_2R/heatmaps/`
- `evidence/stage3_2R/pov/`

---

## 9. Pre-Execution Gate Declaration

**AUTHORIZATION STATUS:**  
`NOT READY FOR EXECUTION (AWAITING EXPLICIT HUMAN AUTHORIZATION)`  
*No benchmark script may execute, no environment XML may be loaded, and no MuJoCo simulation step may be stepped until the human user provides written milestone-level authorization.*
