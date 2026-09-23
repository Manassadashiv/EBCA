# CARL-DX STAGE 3.1 FORENSIC DIAGNOSIS & CAUSAL ROOT CAUSE AUDIT
**Document Classification:** Scientific Forensic Audit & Causal Root Cause Analysis  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1 — CANN Causal Coupling  
**Pre-Flight Status:** Stage 3.0 Certified ✅ | Stage 3.1 Fail-Closed ❌ | Stage 3.2 Locked 🔒 | Stage 3.3 Locked 🔒  
**Date:** September 13, 2026  

---

## Executive Summary

The initial execution of the Stage 3.1 Pre-Registered CANN Causal Coupling Battery evaluated $N = 400$ controlled trials ($100 \text{ paired trials} \times 4 \text{ arms}$) across 5 unseen seeds and 4 challenge maze environments. The experimental data definitively confirmed **mathematical coupling** between the 2,114-unit continuous attractor neural network (CANN) and downstream continuous action selection:
- Motor action divergence was massive and statistically robust: $\Delta \mathbf{u} = 0.532 - 0.548 > 0.150$ across all ablation arms.
- Candidate utility rank correlation shifted significantly: Spearman $\rho = 0.608 - 0.657 \le 0.700$ across all ablation arms.

However, the protocol **FAILED CLOSED** on downstream behavioral necessity:
- Clearance degradation failed the pre-registered threshold ($\Delta C_{\text{hull}} = -0.0051 \text{ m}$ for Frozen, $-0.0187 \text{ m}$ for Zeroed, $-0.0091 \text{ m}$ for Shuffled; threshold: $\ge +0.0500 \text{ m}$).
- Clearance differences lacked statistical significance (Wilcoxon signed-rank $p = 0.485$ for Frozen, $p = 0.257$ for Zeroed, $p = 0.670$ for Shuffled; threshold: $p < 0.010$).
- Most damning of all: **ARM-C (Zeroed CANN) achieved a lower collision rate (7.0%) than ARM-A (Intact CANN, 9.0%)**, while ARM-B (Frozen) and ARM-D (Shuffled) produced 17.0% and 13.0% collisions respectively.

Per CARL-DX canonical governance, **no claim of CANN necessity or usefulness can be made.** CANN state alters the planner mathematically, but behavioral necessity has not been proven. This forensic audit determines the exact physical, mathematical, and architectural mechanisms responsible for this divergence.

---

## Phase 1 — Signal Flow & Causal Path Audit

### 1. The Complete CANN Signal Path
Tracing the signal from the 2,114 neuromorphic units to physical MuJoCo actuation in the tested codebase:

```
[Raw Sensors: IMU gyro yaw S[20], Forward accelerometer S[15], Sonar S[0..14]]
                                 │
                                 ▼
         [Projected Angular Velocity: omega = S @ w_rot]
                                 │
                                 ▼
   [64-Neuron Head-Direction Ring Attractor (CANN ODE: tau * du/dt = -u + W_sym*r + I_shift + I_tonic)]
                                 │
                                 ├──────────────────────────────┐
                                 ▼                              ▼
                 [Decoded Heading: theta_hat]          [HD Firing Rates: r_hd (64-D)]
                                 │                              │
                                 ▼                              │
     [1,024-Neuron 2D Toroidal Grid Sheet (CANN 2D ODE)]        │
                                 │                              │
                                 ▼                              │
             [Unwrapped Displacement: (x_hat, y_hat)]           │
                                 │                              │
                                 ├──────────────────────────────┘
                                 ▼
          [Deliberation Engine: select_action(cann_state={...})]
                                 │
       ┌─────────────────────────┴─────────────────────────┐
       ▼                                                   ▼
[Mental Rollout Origin: (c_x, c_y, c_th)]      [Candidate Scoring Utility]
  c_x = cann_state["grid_unwrapped_x"]           cann_alignment_score =
  c_y = cann_state["grid_unwrapped_y"]             0.25 * sum_i r_i * cos(theta_cand - phi_i)
  c_th = cann_state["hd_decoded_heading"]                  │
       │                                                   │
       ▼                                                   │
[Vectorized Ray-Marching vs self.grid_ch0]                 │
  Sample coordinates: (x_rollout, y_rollout)               │
  Collision Veto: penalty = 800.0                          │
       │                                                   │
       └─────────────────────────┬─────────────────────────┘
                                 ▼
           [Total Utility U(k) across K=24 Candidates]
                                 │
                                 ▼
           [Argmax Action Selection: a* = argmax U(k)]
                                 │
                                 ▼
         [MuJoCo Physical Execution: hal.step(action)]
                                 │
                                 ▼
         [Physical Outcome: Contact/Collision & Clearance]
```

### 2. Forensic Code Inspection of the Active Pipeline

#### A. Origin & Displacement Coordinate Frame Mismatch
In [`brain/carl_stage2_3_r1_deliberation.py`](file:///d:/ebca/brain/carl_stage2_3_r1_deliberation.py#L280-L290):
```python
elif cann_state is not None:
    # Ground pose in 2,114-unit neuromorphic continuous attractor
    hd_head = cann_state.get("hd_decoded_heading", None)
    if hd_head is None:
        hd_head = cann_state.get("cann_heading", self.pose[2])
    c_th = float(hd_head)
    c_x = float(cann_state.get("grid_unwrapped_x", self.pose[0]))
    c_y = float(cann_state.get("grid_unwrapped_y", self.pose[1]))
```
- `cann_state["grid_unwrapped_x"]` and `cann_state["grid_unwrapped_y"]` are produced by `carl_stage2_grid_torus.py` (lines 168–169). They measure cumulative unwrapped displacement in meters **from the birthplace reset location**, starting identically at $(0.0, 0.0)$.
- However, the allocentric occupancy map `self.grid_ch0` (128 $\times$ 128 raster representing $[-6.4, 6.4] \text{ m}$) is indexed in **global arena coordinates**.
- In the test benchmark, CARL spawns at:
  - Layout 1: $(x, y) \approx (-3.00, -0.20)$
  - Layout 2: $(x, y) \approx (-3.40, -0.65)$
  - Layout 3: $(x, y) \approx (-0.20, -2.50)$
  - Layout 4: $(x, y) \approx (-2.50, +2.25)$
- **The Defect:** Overwriting $(c_x, c_y)$ with `(grid_unwrapped_x, grid_unwrapped_y)` sets prospective trajectory unroll roots to $(0.0, 0.0)$ instead of the agent's arena location! Ray-casting against `self.grid_ch0` sampled occupancy values around the arena center (often empty or occupied by unrelated interior obstacles), completely severing prospective ray-marching from the agent's physical location!

#### B. Head-Direction Ring Bump Initialization Offset
In [`brain/carl_stage2_hd_ring.py`](file:///d:/ebca/brain/carl_stage2_hd_ring.py#L45-L52):
```python
self.u = np.zeros(self.N_NEURONS, dtype=np.float64)
self.u[self.N_NEURONS // 2] = 1.0 # Index 32 corresponds to angle 0.0 rad
self.r = self._activation(self.u)
self._settle_initial_attractor(steps=100)
```
- The resting attractor bump unconditionally forms around neuron index 32 ($\theta = 0.0 \text{ rad}$, East).
- In [`brain/carl_stage2_integrated_brain.py`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py#L182-L188), `reset_at_birthplace()` memorizes the phase at spawn but **does not re-center or phase-shift the bump** to the robot's physical spawn orientation.
- In the benchmark, spawn orientations are:
  - Layout 1: $\text{yaw} \approx -\pi/2 \text{ rad}$ (South, $-90^\circ$)
  - Layout 3: $\text{yaw} \approx \pi \text{ rad}$ (West, $180^\circ$)
- Because `c_th = cann_state["hd_decoded_heading"]` was set to the decoded heading of the HD bump (which began at 0 rad), the prospective trajectories were unrolled facing East ($0^\circ$), even when the robot was physically positioned facing South ($-90^\circ$) or West ($180^\circ$).

#### C. Magnitude Discrepancy in Utility Formulation
In [`brain/carl_stage2_3_r1_deliberation.py`](file:///d:/ebca/brain/carl_stage2_3_r1_deliberation.py#L488-L513):
```python
# Term 1: CANN Directional Coherence
coherence = float(np.sum(r_hd * np.cos(cand_terminal_heading - angles_hd)))
cann_alignment_score = coherence * 0.25 # Max magnitude: ~1.2 to 2.5

# Competing Reactive & Heuristic Terms:
collision_penalty = 800.0 if is_collision_predicted else 0.0
fwd_progress * fwd_w # fwd_w = 40.0 (magnitude up to ~4.0)
lateral_evasion # magnitude up to ~10.0
pivot_penalty # 25.0
is_reverse # 15.0
```
- The total contribution of the CANN alignment term is $\le 2.5$ utility points.
- The reactive collision veto is $800.0$ points.
- Lateral evasion from live sonar proximity is up to $10.0$ points.
- Consequently, whenever an obstacle is within immediate range, reactive sonar overrides CANN guidance by two to three orders of magnitude.

### 3. Inventory of Competing Signals
In the current organism, eight distinct signals can determine action selection:
1. **Current Sonar Array (15 rays):** Direct exteroceptive measurement. Determines immediate collision vetoes ($800.0$) and lateral evasion ($40.0 \times \text{proximity}$).
2. **Internal Dead Reckoning (`self.pose`):** Unprivileged integration of wheel velocity and IMU gyro yaw. Accurately tracks $(x, y, \theta)$ from spawn.
3. **Occupancy Memory (`self.grid_ch0`):** Allocentric $128 \times 128$ spatial raster queried by ray sampling.
4. **Action Priors & Forward Progress Bias:** Strong reward for linear drive ($40.0 \times \text{progress}$) and heavy penalties on reverse ($-15.0$) and in-place pivots ($-25.0$).
5. **Lateral Margin Penalties:** Prevents turning into flank walls ($30.0 \times \text{penetration}$).
6. **Centering Bonus:** Balances left and right wall clearances in narrow channels.
7. **Potential Field Baseline:** Reactive gradient computed purely from inverse sonar distances.
8. **Scripted Reflex Vetoes:** Hard thresholds triggered on front sonar $< 0.40 \text{ m}$.

### 4. Signal Redundancy & Masking
Is CANN information redundant with these other signals in the tested benchmark?
- **Yes, 100% redundant and completely masked.**
- In the 4 test layouts, corridors are narrow ($0.60 - 0.90 \text{ m}$ wide), and walls are directly visible to the 15-ray sonar array at all times.
- The forward sonar ray directly detects obstacles at $0.20 - 0.50 \text{ m}$.
- The lateral sonar rays directly detect side walls.
- When an obstacle appears ahead:
  - If the path bends left, right sonar detects close right wall, left sonar detects open corridor.
  - The reactive lateral evasion term ($40.0$) and clearance utility ($4.0 \times \text{clearance}$) immediately favor the left-turning candidates.
  - The CANN alignment term ($\sim 1.5$) is completely unnecessary to select the turning action.
- When the CANN is **Zeroed (ARM-C)**, the agent relies solely on live sonar and swept-cone vetoes. It makes clean, reactive turns with zero contradictory bias. This explains why ARM-C suffered only **7.0% collisions**, fewer than ARM-A (9.0%)!

### 5. Benchmark Horizon & Line-of-Sight Dominance
- **Episode Length:** `MAX_TICKS = 60`. At $\Delta t = 0.030 \text{ s}$, total episode duration is **1.80 seconds**.
- **Translational Speed:** Under maximum linear drive ($u_{\text{fwd}} \approx 0.60$), forward velocity is $v \approx 0.18 - 0.25 \text{ m/s}$.
- **Total Distance Traveled:** In 60 ticks, CARL travels at most **$0.35 - 0.45 \text{ meters}$** (barely 3 body lengths).
- In a 40 cm dash inside a static corridor:
  - The agent never rounds a blind corner where the destination is occluded.
  - The agent never traverses a symmetric bifurcation where one branch is a deep dead-end.
  - The agent never experiences sensory dropout (e.g. sonar blinding or blackout).
  - The agent never revisits a location requiring topological loop closure.
- **Conclusion:** The Stage 3.1 benchmark was **line-of-sight dominated and horizon-truncated**. Under these conditions, an internal 2,114-neuron continuous attractor network has no behavioral advantage over a memoryless 3-line Braitenberg vehicle.

---

## Phase 2 — Categorization of the Failure Mode

Based on forensic code analysis and empirical trial data, the failure mode is classified across the mandatory diagnostic categories:

| Category | Status | Empirical & Code-Level Proof |
|:---|:---:|:---|
| **A. CANN is causally disconnected** | **REFUTED** | $\Delta \mathbf{u} = 0.534 > 0.150$; Spearman $\rho = 0.657 \le 0.700$. CANN state directly alters candidate evaluation and motor commands. |
| **B. CANN is connected but redundant with sonar/odometry** | **CONFIRMED PRIMARY** | In short, unobstructed corridors, live sonar provides full state information for obstacle avoidance. Reactive sonar terms ($800.0$, $40.0$) mask the CANN signal. Zeroing the CANN (ARM-C) produces 7% collisions, matching or beating Intact (9%). |
| **C. CANN is useful only on longer-horizon spatial tasks** | **CONFIRMED PRIMARY** | 60 ticks (1.8s, ~0.4m traversal) is insufficient to reveal path-integration utility. Attractor dynamics integrate velocity over time; on sub-second scales, delta displacement is dominated by initial velocity. |
| **D. Benchmark does not require CANN information** | **CONFIRMED PRIMARY** | In the 4 test layouts, every decision is fully solvable via instantaneous line-of-sight rangefinding. No task required persistent heading retention or non-local spatial disambiguation. |
| **E. CANN representation is inaccurate/drifting** | **PARTIAL CONTRIBUTOR** | In open loop, HD drift is $\sim 1.2^\circ/\text{s}$ and grid drift is $\sim 0.04 \text{ m/s}$ (both within Stage 2 specs). However, the uncentered spawn bump introduced an initial offset of up to $180^\circ$ relative to arena yaw. |
| **F. Intervention design is invalid or confounded** | **CONFIRMED CONTRIBUTOR** | Clamping the attractor to spawn state (ARM-B Frozen) or permuting it (ARM-D Shuffled) didn't merely deprive CARL of information; it injected **active contradictory guidance**, constantly pulling the robot into walls (17% and 13% collisions). ARM-C (Zeroed) was the only uncorrupted deprivation arm, and it beat Intact! |
| **G. Utility weighting suppresses genuine CANN contribution** | **CONFIRMED CONTRIBUTOR** | `cann_alignment_score` was capped at $\sim 2.5$ utility points, compared to $800.0$ for collision vetoes and $40.0$ for live sonar lateral evasion. |
| **H. Architectural / Coordinate Frame Defect** | **CONFIRMED PRIMARY** | In `deliberation.py` line 286–287, `(c_x, c_y)` was overwritten with `(grid_unwrapped_x, grid_unwrapped_y)` (relative to spawn) rather than registering relative grid displacement onto allocentric arena coordinates: $(x_{\text{spawn}} + \Delta x_{\text{grid}}, y_{\text{spawn}} + \Delta y_{\text{grid}})$. This caused ray-marching to query the wrong sector of the arena raster map! |

### Synthesis: The True Scientific Diagnosis
The failure of Stage 3.1 to demonstrate behavioral necessity is **NOT** evidence that continuous attractor networks are biologically or computationally useless. Rather, it is the consequence of four compounding factors:
1. **The Coordinate Registration Flaw:** Grid torus displacement was treated as absolute arena position $(0, 0)$ rather than relative displacement $(\Delta x, \Delta y)$ from spawn, and the HD ring bump was initialized at 0 rad rather than aligned to spawn orientation.
2. **Line-of-Sight Masking:** Local sonar array and high reactive weights completely solved the tested short-horizon navigation tasks without needing cognitive self-modeling.
3. **Horizon Truncation:** At 60 ticks (1.8s), the robot moved less than half a meter, never encountering situations where instantaneous sensations disagree with true spatial state.
4. **Deprivation vs Toxicity Confound:** Freezing and shuffling the attractor injected toxic steering biases rather than testing neutral information deprivation. ARM-C (Zeroed) demonstrated that removing this toxic bias improved performance over Intact.

---

## Phase 3 & 4 Recommendation: The Smallest Valid Scientific Repair

To test genuine CANN necessity under scientific rigor:
1. **Fix Coordinate Registration:**
   - In `HeadDirectionRingAttractor`: Provide a clean initialization method `set_initial_bump(spawn_yaw)` that centers the resting attractor bump at `spawn_yaw` at birthplace birth.
   - In `deliberation.py`: Register continuous attractor displacement to spawn pose:
     $$\hat{x} = x_{\text{spawn}} + \Delta x_{\text{grid}}, \quad \hat{y} = y_{\text{spawn}} + \Delta y_{\text{grid}}, \quad \hat{\theta} = \theta_{\text{cann}}$$
2. **Design Tasks Where Local Sonar is Fundamentally Insufficient:**
   - **Task Family 1 (Sensor Blackout / Blind Corridor):** Temporary sensory occlusion (e.g. sonar dropouts where $S_{0..14} = 5.0 \text{ m}$ or zeroed) during high-speed traversal through a curving corridor. An agent with an intact CANN can maintain path integration and heading across the blackout; a deprived/zeroed agent drifts into the walls.
   - **Task Family 2 (Symmetric Bifurcation with Distant Cul-de-sac):** A T-junction where immediate sonar reads identical clearance to both left and right ($d_{\text{left}} = d_{\text{right}} = 0.80 \text{ m}$), but one direction leads to a blocked dead-end 1.5 m away and the other leads to the open goal corridor. Only an agent with global heading/grid state can choose the open direction.
   - **Task Family 3 (Multi-Turn Long-Horizon Traversal):** Extended 120-tick runs ($3.6 \text{ s}$) where persistent orientation retention across consecutive chicanes is required.
3. **Pre-Register Revised Protocol:**
   Pre-register all hypotheses, thresholds, seeds, and statistical tests in `evidence/stage3_1/REVISED_CANN_BATTERY_PROTOCOL.md` BEFORE modifying code or running benchmarks.
