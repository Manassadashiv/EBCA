# CARL-DX Stage 3.4-R4.1: Technical Diagnostic & Screening Evidence Pack
**Milestone:** Stage 3.4 — Autonomous Behavioral Discovery under Active Inference  
**Evaluation Scope:** Diagnostic Screening & Forensic Analysis (N=10 Matched Configurations)  
**Governance Stance:** Stage 3.4-R3 FAILED CLOSED (Permanent Record) | Stage 3.5 LOCKED | Stage 3.4 NOT CERTIFIED

---

## Slide 1: Stage 3.4 Current Challenge & Problem Definition
- **Title:** Stage 3.4 Autonomous Maneuver Discovery: The Structural Feasibility Problem
- **Bullet Points:**
  - Active Inference requires CARL to autonomously discover non-trivial reversing, pivoting, and corridor navigation without discrete state machines or heuristic escape macros.
  - While Environment 1 (Turning-Bay Cul-de-Sac) demonstrated emergent multi-point turns, Environment 2 (Asymmetric T-Junction) revealed severe geometric clearance constraints.
  - The core tension lies between prospective continuous action synthesis ($M=128, H=15$) and physical rectangular hull clearance in narrow ($0.65\text{ m}$) corridors.
  - Screening trials prior to R4.1 indicated real-time latency tails ($p95 = 86.67\text{ ms}$) exceeding the certified real-time budget ($p95 \le 45.0\text{ ms}$).
- **Figure Reference:** `figures/fig1_env2_trajectory_overlay.png`
- **Presentation Script (30–45s):**
  "Welcome. In Stage 3.4, CARL must discover composite navigation maneuvers under continuous Active Inference without handcoded macros or environment-specific branching. While open-space and turning-bay navigation showed promising emergent behavior, asymmetric junctions in narrow corridors introduced severe physical challenges: when rotating a rectangular chassis in tight quarters, clearance margins drop to centimeters. Today we examine R4.1's forensic diagnostic data, our generic heading fusion model, our offline hull validation, our latency resolution, and our 10-configuration screening results."
- **Takeaway Statement:**
  *Stage 3.4 demands that complex navigation maneuvers emerge strictly from continuous Expected Free Energy minimization without hardcoded escape controllers.*

---

## Slide 2: Retrospective: What Stage 3.4-R3 Proved and Preserved
- **Title:** Stage 3.4-R3 Audit: Definitive Fail-Closed Evidence
- **Bullet Points:**
  - Stage 3.4-R3 completed a full 200-episode frozen battery and failed closed on Gates 1, 2, 3, and 4, while achieving 100% clean AST verification on Gate 5.
  - R3 empirical evidence proved that physical hull geometry cannot be approximated as a point or circle: bumper corners swept into corridor boundaries during in-place turns.
  - Gyro integration accumulated heading drift over extended trajectories without absolute sensor anchoring.
  - All R3 historical telemetry and failure data remain sealed permanently in `evidence/stage3_4R3/` without mutation or deletion.
- **Figure Reference:** `figures/fig4_heading_fusion_comparison.png`
- **Presentation Script (30–45s):**
  "In accordance with our zero-tolerance governance rules, Stage 3.4-R3 is permanently preserved as a fail-closed milestone. R3 demonstrated that CARL's internal circular clearance model was physically inadequate: a 0.23 by 0.27 meter rectangular chassis rotating in a 0.70 meter corridor has corner sweep trajectories that circular approximations completely miss. Furthermore, unbounded gyro dead-reckoning drifted over 150-tick episodes. These lessons established the direct foundation for the R4 architectural improvements."
- **Takeaway Statement:**
  *Stage 3.4-R3 established that exact rectangular swept-hull feasibility and drift-free heading estimation are mandatory for narrow-corridor transit.*

---

## Slide 3: Architectural Additions in Stage 3.4-R4
- **Title:** What Stage 3.4-R4 Introduced: Rectangular Feasibility & Odometry Fusion
- **Bullet Points:**
  - Replaced circular clearance circles with exact Oriented Bounding Box (OBB) geometric sweep evaluations.
  - Formulated continuous Biased-MPPI mixture sampling ($M=128, H=15$) directly over wheel velocities $\mathbf{u} \in [-1.0, 1.0]^2$.
  - Introduced prospective collision vetoing that penalizes infeasible trajectory candidates before action synthesis.
  - Conducted preliminary 10-configuration diagnostic screening showing initial escape capability in both environments.
- **Figure Reference:** `figures/fig2_mppi_candidate_fan.png`
- **Presentation Script (30–45s):**
  "R4 introduced two crucial architectural organs: first, an exact rectangular hull feasibility shield that evaluates 128 candidate trajectory rollouts over a 15-step horizon against allocentric occupancy memory; second, continuous MPPI action synthesis that respects physical actuator limits. Initial screening demonstrated that Environment 1 escape rates improved to 80% under ARM-A, and Environment 2 achieved its first documented autonomous escape."
- **Takeaway Statement:**
  *Stage 3.4-R4 introduced exact rectangular hull screening, enabling initial feasible trajectory selection in tight corridors.*

---

## Slide 4: Forensic Diagnosis: Action Synthesis & Branch Commitment Failure
- **Title:** Asymmetric Junction: Decision & Action Synthesis Deficit
- **Bullet Points:**
  - Env2 failure taxonomy establishes that **4 out of 5 ARM-A failures are Action/Decision Failures** (hesitation, limit-cycle oscillation, cautious timeout), while only 1 is a Geometric Failure (collision).
  - Telemetry reveals CARL accurately maps the south frontier $(0.4, -2.8\text{ m})$ with 2.7 m remaining and retains a large set of feasible candidates.
  - The core failure is **decision/action synthesis**: CARL does not reliably commit to the south branch, oscillating between straight centering and turning actions.
  - Geometric corner clipping is a secondary symptom when an off-center pose is held too long, not the primary cause of failure.
- **Figure Reference:** `figures/heatmap_d_env2_failure_taxonomy.png`
- **Presentation Script (30–45s):**
  "Why did Environment 2 remain unreliable? The diagnostic taxonomy reveals a critical truth: 4 out of 5 ARM-A failures are action and decision failures, not geometric impossibility. The internal world model correctly identifies the distant south escape frontier at (0.4, -2.8 m) and retains dozens of feasible candidates. Yet, the agent fails to commit: near-tied EFE costs and softmax dispersion cause the robot to oscillate between straight centering and turning, ultimately timing out or drifting into a boundary."
- **Takeaway Statement:**
  *Environment 2 failures are predominantly action synthesis and branch-commitment deficits (4/5 cases), not geometric impossibility.*

---

## Slide 5: The Rectangular Swept-Hull Feasibility Model
- **Title:** Exact Rectangular Hull Clearance: Offline Cross-Validation
- **Bullet Points:**
  - Evaluated 1,280 continuous candidate rollouts against actual MuJoCo contact ground truth across 10 diverse poses.
  - Confusion Matrix: True Positives = 17, False Positives (conservative safety vetoes) = 665, False Negatives = 0, True Negatives = 598.
  - **0 false negatives observed in the 1,280-rollout offline validation set** (sample FN rate: $0.00\%$).
  - **High False-Positive Veto Rate (52.65%):** The safety filter aggressively eliminates over half the action space, which may starve valid turning trajectories.
- **Figure Reference:** `figures/heatmap_a_hull_feasibility.png`
- **Presentation Script (30–45s):**
  "To validate our rectangular hull model, we evaluated 1,280 rollouts against ground-truth physics. Zero false negatives were observed in this validation sample, demonstrating strong safety filtering. However, the model exhibits a 52.65% false-positive veto rate. While this prevents collisions, aggressively eliminating over half of all candidate rollouts may actively starve the policy of viable turning actions in narrow corridors."
- **Takeaway Statement:**
  *The hull shield observed 0 false negatives in 1,280 rollouts, but a 52.65% false-positive veto rate heavily restricts the available action space.*

---

## Slide 6: Generic Sonar + Gyro Heading Fusion
- **Title:** Unbiased Heading Estimation via Generic Sonar Wall Extraction
- **Bullet Points:**
  - Replaced all environment-specific cardinal heading heuristics with generic relative line estimation from raw 15-channel sonar returns.
  - Passed 9 out of 9 deterministic unit tests: horizontal walls, vertical walls, 35-degree rotated walls, partial visibility, noisy returns, single-wall tracking, outlier rejection, 180-degree wraparound, and sonar-blackout fallback.
  - Dedicated validation reduced error to $\le 6.1^\circ$; however, **episode-level behavioral robustness remains under active evaluation**.
  - During complex behavioral transit (e.g. Config 20), maximum heading error reached $29.5^\circ$, demonstrating that dynamic multi-surface environments require further filtering.
- **Figure Reference:** `figures/fig4_heading_fusion_comparison.png`
- **Presentation Script (30–45s):**
  "A critical requirement of R4.1 was purging all environment-specific heading assumptions. The new generic heading estimator passed all 9 deterministic bench tests, achieving 6.1-degree error under idealized conditions. However, in actual behavioral episodes like Config 20, dynamic maneuvers produced peak heading errors up to 29.5 degrees. Thus, heading fusion is architecturally generic, but its dynamic behavioral robustness is not yet proven."
- **Takeaway Statement:**
  *Generic heading fusion eliminates cardinal snapping and passes unit tests, but dynamic behavioral episodes still experience heading error up to 29.5°.*

---

## Slide 7: Continuous Action Synthesis via MPPI Feasibility Filtering
- **Title:** Prospective Trajectory Deliberation & Expected Free Energy
- **Bullet Points:**
  - Deliberation samples $M=128$ continuous trajectories propagated over horizon $H=15$ ($dt = 0.030\text{ s}$).
  - Expected Free Energy balances pragmatic cost (safety margin, smoothness, lateral centering) and epistemic value (macro-frontier information gain).
  - Feasibility filtering masks out all candidates whose swept rectangular envelope penetrates mapped occupancy or live sonar points.
  - Optimal action $\mathbf{u}^*$ is computed via numerically stabilized softmax weighting with temperature $\tau = 0.002$.
- **Figure Reference:** `figures/fig3_efe_decomposition.png`
- **Presentation Script (30–45s):**
  "Here we observe the inner workings of CARL's deliberation cycle. At each tick, 128 candidate trajectory rollouts are propagated. Candidates that violate the rectangular hull clearance envelope receive an immediate feasibility veto. For all surviving candidates, Expected Free Energy evaluates pragmatic penalties alongside epistemic exploration incentives. Softmax weighting synthesizes a continuous action vector without discrete mode switches."
- **Takeaway Statement:**
  *Continuous MPPI synthesizes safe control actions by evaluating epistemic value exclusively over geometrically feasible trajectories.*

---

## Slide 8: Forensic Case Study: Config 21 Autonomous Escape
- **Title:** Environment 2 Forensic Case Study: Config 21 Autonomous Egress
- **Bullet Points:**
  - Spawn pose: $x = 0.537\text{ m}, y = 0.038\text{ m}, \theta = +2.4^\circ$ inside the approach corridor.
  - Navigation trace: CARL advances into the T-junction, detects the south macro-frontier via allocentric geodesic propagation ($3.2\text{ m}$ reach), initiates a coordinated turn, and aligns with the south corridor centerline ($x = 0.825\text{ m}$).
  - Total ticks executed: 188 ticks ($5.64\text{ s}$ simulation time); achieved exit threshold ($y \le -1.20\text{ m}$) at tick 188.
  - Zero simulator coordinate leakage: decision pipeline verified 100% AST compliant; odometry derived solely from unprivileged sensors.
- **Figure Reference:** `figures/fig5_lateral_offset_hull_clearance.png`
- **Presentation Script (30–45s):**
  "Let us examine the successful escape of Config 21 in Environment 2. Spawning in the approach corridor, CARL drives forward into the junction. Using our newly extended 32-iteration geodesic field, the internal world model discovers the deep south open branch. MPPI synthesizes an arc that clears the west corner wall, centers the chassis at x = 0.825 meters, and drives cleanly down to the escape boundary at tick 188 with zero collisions."
- **Takeaway Statement:**
  *Config 21 demonstrates that autonomous negotiation of the asymmetric T-junction is geometrically and computationally feasible under Active Inference.*

---

## Slide 9: Deliberation Latency: Profiling & Optimization Results
- **Title:** Latency Tail Elimination: From 86.7 ms to 8.67 ms p95
- **Bullet Points:**
  - Diagnostic profiling revealed the primary bottleneck: pure-Python deque breadth-first search during macro-frontier geodesic updates on cache misses ($25\text{–}50\text{ ms}$).
  - Replaced with in-place NumPy slice raster geodesic propagation (`_compute_geodesic_field`), running in under $0.95\text{ ms}$ for a $3.2\text{ m}$ wavefront.
  - Continuous 1,000-cycle profiling results:
    - **Mean latency: $4.14\text{ ms}$** (Budget $\le 20.0\text{ ms}$ — **PASS**)
    - **p50 latency: $2.96\text{ ms}$**
    - **p95 latency: $8.67\text{ ms}$** (Budget $\le 45.0\text{ ms}$ — **PASS**)
    - **p99 latency: $10.39\text{ ms}$**, Max: $16.02\text{ ms}$.
- **Figure Reference:** `figures/fig7_latency_ecdf.png`
- **Presentation Script (30–45s):**
  "Deliberation cycle latency was one of our primary screening failure modes. Through fine-grained stage instrumentation across 1,000 cycles, we pinpointed the exact bottleneck: Python BFS queue allocations during frontier distance field updates. By replacing this with vectorized NumPy slice raster propagation, the geodesic update dropped from 35 milliseconds to under 1 millisecond. Our p95 latency is now 8.67 milliseconds, well below the 45-millisecond certification ceiling."
- **Takeaway Statement:**
  *Vectorized geodesic propagation reduced p95 deliberation latency by 90%, easily satisfying the real-time certification budget.*

---

## Slide 10: 10-Configuration Matched Screening Battery
- **Title:** R4.1 Diagnostic Screening Results: ARM-A vs ARM-B
- **Bullet Points:**
  - Evaluated 10 matched configurations (Configs 0–4 in Env 1; Configs 20–24 in Env 2) across both arms ($N=20$ episodes).
  - **ARM-A (Full Active Inference):** Escapes = 2/10 (20.0%), Collisions = 3/10 (30.0%), Timeouts = 5/10 (50.0%).
  - **ARM-B (Pragmatic Only):** Escapes = 0/10 (0.0%), Collisions = 4/10 (40.0%), Timeouts = 6/10 (60.0%).
  - Action Divergence: $0.855$ mean Euclidean difference between arms on common steps, confirming strong epistemic drive engagement.
  - In Environment 2, ARM-A achieved an autonomous escape (Config 21), whereas ARM-B achieved 0 escapes and higher collision frequency.
- **Figure Reference:** `figures/fig8_screening_arma_vs_armb.png`
- **Presentation Script (30–45s):**
  "Our matched 10-configuration screening battery tested ARM-A with Active Inference against ARM-B without epistemic value. ARM-A achieved a +20 percentage point escape advantage over ARM-B, with ARM-B scoring zero escapes. Furthermore, mean action divergence between the two arms was 0.855, demonstrating that epistemic frontier seeking significantly alters trajectory selection. However, with an overall 20% escape rate, these results represent screening progress, not certification."
- **Takeaway Statement:**
  *Diagnostic screening confirms that epistemic drive produces substantial behavioral differentiation (+20% escape delta), though overall reliability remains below certification thresholds.*

---

## Slide 11: Current R4.1 Status & Scientific Synthesis
- **Title:** Stage 3.4-R4.1 Status: Validated Substrates & Decision Deficits
- **Bullet Points:**
  - **Subsystems Validated in Diagnostic Experiments:**
    - Deliberation latency: Mean $4.14\text{ ms}$, p95 $8.67\text{ ms}$ (Compliant with real-time budget).
    - Hull feasibility model: 0 false negatives observed across 1,280 rollouts.
    - Generic heading fusion: 9/9 deterministic unit tests passed; zero environment branching.
    - AST decision-pipeline isolation: 100% clean, zero simulator coordinates.
  - **Primary Unresolved Deficits:**
    - Action indecision & branch commitment: CARL fails to commit to the south branch despite feasible options, leading to 50% timeouts.
    - Aggressive hull veto rate ($52.65\%$ FP) potentially starving turning trajectories.
    - Episode-level heading error reaches $29.5^\circ$ during behavioral turns.
- **Figure Reference:** `figures/heatmap_b_efe_landscape.png`
- **Presentation Script (30–45s):**
  "To summarize our current status: R4.1 has validated our core computational and geometric foundations in diagnostic tests. Deliberation latency is completely resolved, the hull model observed zero false negatives, and heading fusion is architecturally generic. However, our primary obstacle is an action synthesis deficit: CARL hesitates and oscillates at the junction despite having valid frontiers. Until action commitment and candidate veto starvation are resolved, certification is impossible."
- **Takeaway Statement:**
  *Computational and geometric substrates are validated in diagnostic tests, but action synthesis indecision and high veto rates prevent certification.*

---

## Slide 12: Roadmap Governance: Focus Areas for Stage 3.4-R4.2
- **Title:** What Stage 3.4-R4.2 Must Target Before Certification
- **Bullet Points:**
  - **Do NOT launch the 200-episode certification battery:** Current screening reliability (20%) is far below the $\ge 70\%$ Gate 1 threshold.
  - **Investigate Coupled Triad in R4.2 (No Hardcoded Damping):**
    - **1. Frontier Stability:** Quantify target churn ($f_t, f_{t-1}, f_{t-2}$) to determine if the macro-frontier is flickering between branches.
    - **2. Action Commitment:** Measure EFE candidate score separation ($\Delta G = G_2 - G_1$) and softmax entropy to resolve junction indecision.
    - **3. Conservative Hull Veto Audit:** Evaluate whether the $52.65\%$ false-positive veto rate is starving turning maneuvers.
  - **Governance Invariant:** Stage 3.5 remains strictly LOCKED until Stage 3.4 passes all five frozen gates in a single unbroken execution.
- **Figure Reference:** `figures/heatmap_c_occupancy_frontier.png`
- **Presentation Script (30–45s):**
  "In accordance with our pre-registered governance rules, we fail closed and do not authorize the 200-episode certification battery. R4.2 will not resort to arbitrary speed dampening. Instead, it will probe the coupled chain of frontier stability, EFE score separation, and candidate veto starvation. We will diagnose exactly why CARL hesitates at the junction before touching weights. Stage 3.5 remains locked, maintaining strict scientific integrity."
- **Takeaway Statement:**
  *Stage 3.4 certification is withheld; R4.2 will probe frontier stability, EFE candidate score gaps, and hull veto starvation before attempting certification.*

---
*Evidence pack compiled on September 20, 2026. All raw telemetry, scorecards, and high-resolution figures are preserved in `evidence/stage3_4R4_1/`.*
