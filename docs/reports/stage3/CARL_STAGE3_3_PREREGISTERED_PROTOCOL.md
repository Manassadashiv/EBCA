# CARL-DX Stage 3.3 — Continuous Action Synthesis (MPPI)
## Pre-Registered Benchmark Protocol & Governance Specification

```
========================================================================================
                          STAGE 3.3 PRE-REGISTERED PROTOCOL
========================================================================================
Protocol ID:            CARL-STAGE3-3-MPPI-PROTO-2026-09-13
Milestone:              Stage 3.3 — Continuous Action Synthesis (MPPI)
Status:                 FROZEN PRIOR TO BENCHMARK EXECUTION ✅
Authority:              Lead Research Architect & Human Project Leadership
Pre-Registration Date:  September 13, 2026
Target System:          CARL-DX Embodied Organism (MuJoCo 3.3.4, vessel_kinetic.xml)
Governing Rule:         Zero threshold relaxation post-run. Pre-registered comparative gates.
========================================================================================
```

---

## 1. Scientific Objective & Developmental Context

### 1.1 The Architectural Problem
Stage 3.2-R demonstrated that CARL's spatial memory causally affects action selection at ambiguous junctions ($\|\Delta \mathbf{u}\| = 0.466\text{ m/s}$ under observationally equivalent local sonars). However, the organism failed the behavioral navigation criterion because its motor controller was constrained to a discrete menu of static primitives (constant curvature arcs / discrete commands). The organism possessed the cognitive intention to turn, but lacked continuous control authority to smoothly steer through tortuous non-LOS corridors.

### 1.2 The Stage 3.3 Solution: Model Predictive Path Integral Control
Stage 3.3 constructs the continuous motor execution substrate ("the hands") by replacing discrete candidate menus with **continuous Model Predictive Path Integral (MPPI) control**:
- Sample size: $M = 128$ candidate trajectories
- Lookahead horizon: $H = 15$ steps ($0.50\text{ s}$ lookahead at $dt \approx 0.0333\text{ s}$)
- Action space: Continuous wheel velocity commands $\mathbf{u} = [u_L, u_R]^T \in [-1.0, 1.0]^2$
- Multi-objective trajectory cost: Evaluates candidates against learned grounded body dynamics, spatial occupancy memory, CANN directional attractor heading, and lateral clearances.
- Real-time constraint: Total cognitive cycle computation $\le 45.0\text{ ms}$ (within the $50.0\text{ ms}$ biological clock tick).

### 1.3 Governance Boundaries
1. **Permanent Ledger Integrity:** Stage 3.2-R remains permanently recorded as `FAILED CLOSED / DIAGNOSTIC RESULT ❌`. Stage 3.3 is a distinct capability build, not a retroactive fix or quiet rerun of Stage 3.2.
2. **Comparative Gate Design:** Following human directive, Gate 3 evaluates MPPI comparatively against the frozen Stage 2 discrete controller rather than imposing an artificial, brittle $0.0\%$ zero-defect requirement on a newly synthesized continuous controller.

---

## 2. Mathematical Formulation & Tensor Contracts

### 2.1 Forward Kinematic Rollout
For each candidate trajectory $m \in \{1, \dots, M\}$ across steps $t \in \{0, \dots, H-1\}$:

$$\mathbf{u}_{m, t} = \text{clamp}(\bar{\mathbf{u}}_t + \delta \mathbf{u}_{m, t}, \; -1.0, \; 1.0)$$

Where $\bar{\mathbf{U}} \in \mathbb{R}^{H \times 2}$ is the warm-started nominal control sequence, and $\delta \mathbf{u} \sim \mathcal{N}(\mathbf{0}, \mathbf{\Sigma}_u)$ with diagonal exploration covariance $\mathbf{\Sigma}_u = \text{diag}(\sigma_L^2, \sigma_R^2)$.

Forward rollout uses certified grounded body dynamics:
$$\begin{aligned}
u_{\text{fwd}} &= \frac{1}{2}(u_L + u_R), \quad u_{\text{diff}} = u_R - u_L \\
v_{t+1} &= \alpha_v v_t + (1 - \alpha_v) (u_{\text{fwd}} \cdot k_{\text{fwd}} / dt) \\
\omega_{t+1} &= \alpha_\omega \omega_t + (1 - \alpha_\omega) (u_{\text{diff}} \cdot k_{\text{rot}}) \\
x_{t+1} &= x_t + v_{t+1} \cos(\theta_t) dt \\
y_{t+1} &= y_t + v_{t+1} \sin(\theta_t) dt \\
\theta_{t+1} &= \theta_t + \omega_{t+1} dt
\end{aligned}$$

### 2.2 Multi-Objective Trajectory Cost $S(\mathbf{U}_m)$
Each prospective trajectory $m$ is assigned a scalar cost $S_m$:

$$S_m = w_{\text{coll}} J_{\text{coll}}(m) + w_{\text{margin}} J_{\text{margin}}(m) + w_{\text{jerk}} J_{\text{jerk}}(m) - w_{\text{fwd}} J_{\text{fwd}}(m) - w_{\text{cann}} J_{\text{cann}}(m) - w_{\text{center}} J_{\text{center}}(m)$$

Where:
1. **Collision Hazard $J_{\text{coll}}(m)$:** Query allocentric occupancy memory $\mathcal{M}_{\text{occ}}$ along the trajectory via vectorized bilinear interpolation. If minimum hull clearance $< 0.12\text{ m}$, assert collision veto penalty ($+800.0$).
2. **CANN Directional Coherence $J_{\text{cann}}(m)$:** Population vector alignment with 64-unit Head-Direction ring:
   $$J_{\text{cann}}(m) = \sum_{i=1}^{64} r_i^{\text{HD}} \cos(\theta_{m, H-1} - \phi_i)$$
3. **Forward Progress $J_{\text{fwd}}(m)$:** Net displacement along ego-heading frame.
4. **Corridor Centering $J_{\text{center}}(m)$:** Penalty for asymmetric proximity to flanking walls.
5. **Action Smoothness $J_{\text{jerk}}(m)$:** Quadratic rate-of-change penalty:
   $$J_{\text{jerk}}(m) = \sum_{t=1}^{H-1} \|\mathbf{u}_{m, t} - \mathbf{u}_{m, t-1}\|^2$$

### 2.3 Path Integral Softmax Weighting
The optimal action $\mathbf{u}^*$ is computed via exponential softmax weighting with temperature parameter $\lambda$:

$$\beta = \min_{m} S_m$$

$$w_m = \frac{\exp\left( -\frac{1}{\lambda}(S_m - \beta) \right)}{\sum_{j=1}^M \exp\left( -\frac{1}{\lambda}(S_j - \beta) \right)}$$

$$\mathbf{u}^* = \sum_{m=1}^M w_m \mathbf{u}_{m, 0}$$

The nominal trajectory is updated via warm-starting:
$$\bar{\mathbf{u}}_t \leftarrow \sum_{m=1}^M w_m \mathbf{u}_{m, t+1} \quad (0 \le t < H-1), \quad \bar{\mathbf{u}}_{H-1} \leftarrow \bar{\mathbf{u}}_{H-2}$$

---

## 3. Pre-Registered Capability Acceptance Gates

Stage 3.3 certification requires all 5 gates to pass independently under automated testing.

| Gate | Name | Pre-Registered Metric | Acceptance Threshold | Mandatory Failure Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 1** | **Action Space Continuity & Smoothness** | Step-to-step action delta $\|\Delta \mathbf{u}^*\|_2$ and control range | Strictly bounded in $[-1.0, 1.0]^2$; mean $\|\Delta \mathbf{u}^*\| \le 0.35$; 0% NaN / Inf | Bang-bang oscillation (frequency $> 0.4 \times f_{\text{Nyquist}}$) or out-of-bounds commands |
| **Gate 2** | **Real-Time Cognitive Cycle Latency** | Execution latency over $N \ge 100$ cycles ($M=128, H=15$) | **p95 latency $\le 45.0\text{ ms}$**; mean latency $\le 20.0\text{ ms}$ | p95 latency $> 45.0\text{ ms}$ (violates 50 ms simulation clock budget) |
| **Gate 3** | **Comparative Obstacle Negotiation** | Collision rate and hull clearance vs discrete baseline in tortuous corridors | **$\ge 50.0\%$ relative collision reduction vs discrete baseline**; **Collision rate $\le 10.0\%$**; **$\Delta C_{\text{hull}} > 0$** | Collision rate $> 10.0\%$ or no improvement over discrete baseline |
| **Gate 4** | **CANN & Memory Multi-Objective Coupling** | Action divergence under CANN heading perturbation ($\pm 90^\circ$) | **$\|\Delta \mathbf{u}^*\| \ge 0.15\text{ m/s}$ ($p < 0.01$)** | Action insensitive to internal cognitive representations ($\|\Delta \mathbf{u}^*\| < 0.15$) |
| **Gate 5** | **Decision-Pipeline AST Anti-Cheat** | Static AST scan across all decision pipeline files | **100% clean (0 imports of `mujoco`, 0 privileged reads)** | Any static reference to `qpos`, `qvel`, `geom_xpos`, `mj_ray`, or `mujoco` |

---

## 4. Execution Protocol & Verification Artifacts

1. **Architecture Integrity:** `brain/carl_mppi_deliberation.py` must be added to `COGNITIVE_DECISION_PIPELINE_FILES` in `tests/test_stage3_ast_anti_cheat.py`.
2. **Canonical Organism Integration:** `brain/carl_autonomous_agent.py` must support and execute the MPPI deliberation engine.
3. **Artifact Generation:**
   - Detailed JSON scorecard: `evidence/stage3_3/stage3_3_scorecard.json`.
   - Comprehensive verification report: `CARL_STAGE3_3_FINAL_VERIFICATION_REPORT.md`.
   - Publication-quality evidence figures displaying action distributions, latency histograms, and comparative trajectories.
