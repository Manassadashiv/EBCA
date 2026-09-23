# CARL-DX STAGE 3.1-R PRE-REGISTERED PROTOCOL
**Document Classification:** Pre-Registered Experimental Protocol (FROZEN BEFORE EXECUTION)  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1-R — CANN Causal Coupling Remediation  
**Status:** FROZEN SPECIFICATION 🔒 (Must not be modified after execution begins)  
**Prerequisite:** Stage 3.0 CERTIFIED ✅ | Stage 3.1 Original FAILED CLOSED ❌ (Permanent)  
**Date:** September 13, 2026  

---

## 1. Research Question

> **Does CARL's 2,114-unit neuromorphic computational architecture (64-neuron head-direction ring attractor + 1,024-neuron toroidal grid sheet attractor + 1,026-neuron recurrent liquid state reservoir) causally contribute information to downstream action selection and physical navigation behavior that is unrecoverable from instantaneous sonar sensing alone?**

The architecture consists of two tightly coupled functional substrates:
1. **Spatial-Directional Attractor Subsystem (1,088 units):** 64-neuron HD ring (continuous heading orientation) + 1,024-neuron toroidal grid sheet (2D spatial metric displacement).
2. **Spatiotemporal Dynamic Memory Subsystem (1,026 units):** 1,026-neuron Echo State Reservoir with continuous intrinsic homeostatic plasticity (non-linear recurrent sensory-motor history embedding).

The experiment must distinguish:
- **(A) Mere software influence / action divergence:** Neural state changes numbers in the candidate utility function.
- **(B) Genuine behavioral necessity:** Removing or scrambling the complete 2,114-unit architecture causes statistically significant degradation of physical navigation safety (hull clearance, collision rate) in environments where sonar alone is insufficient.

---

## 2. Hypotheses

- **Null Hypothesis ($H_0$):** Complete deprivation of the 2,114-unit neuromorphic architecture (ARM-C Zeroed, ARM-D Full-Shuffled) does not degrade downstream navigation performance compared to the uncorrupted network (ARM-A Intact) on non-line-of-sight navigation tasks with sensory blackout periods.

- **Alternative Hypothesis ($H_1$):** Complete deprivation across the 2,114-unit architecture significantly degrades hull clearance by at least $+0.05\text{ m}$ ($p < 0.005$, Bonferroni-corrected Wilcoxon signed-rank test), increases collision rate ($\Delta\text{Coll} \ge 0\%$), alters motor commands ($\Delta\mathbf{u} > 0.15$), and disrupts candidate ranking ($\rho \le 0.70$) during the active sensory-blackout decision window.

---

## 3. Intervention Arms (3-Arm Controlled Design across 2,114 Units)

### ARM-A: Intact (Experimental Condition — 2,114 Units Active)
Uncorrupted 2,114-unit neuromorphic integration:
- 1,026-neuron recurrent reservoir steps via continuous leaky integration with intrinsic plasticity.
- 64-neuron HD ring and 1,024-neuron grid torus step continuously from grounded proprioception.
- Spawn displacement zero-referenced (remediated coordinate transform).
- Inter-episode clean attractor and reservoir reset via `reset_cann_clean()`.

**State passed to deliberation:**
```python
cann_state = {
    "hd_decoded_heading": spawn_yaw + Δθ_hd,        # Arena-registered heading
    "grid_unwrapped_x": spawn_x + Δx_grid,           # Arena-registered X position
    "grid_unwrapped_y": spawn_y + Δy_grid,           # Arena-registered Y position
    "hd_rates": np.roll(hd_ring.r, k_shift),          # 64-D HD firing rates (arena-aligned)
    "bump_amplitude": hd_ring.bump_amplitude,
    "reservoir_norm": float(np.linalg.norm(reservoir.x)),
    "total_units_active": 2114,
}
```

### ARM-C: Zeroed (Primary Deprivation Control — 0 Units Active)
Complete deprivation of all 2,114 units across the architecture:
- 1,026-neuron reservoir state $x \in \mathbb{R}^{1026}$ zeroed (`brain.reservoir.x.fill(0.0)`).
- 64-neuron HD ring rates $r$ and bump amplitude set to 0.
- 1,024-neuron grid torus rates $r$ and unwrapped coordinates set to 0.
- Decoded scalars set to 0.0. The deliberation engine receives zeroed spatial, directional, and recurrent temporal state, relying strictly on live rangefinders and dead-reckoning.

**State passed to deliberation:**
```python
cann_state = {
    "hd_decoded_heading": 0.0,
    "grid_unwrapped_x": 0.0,
    "grid_unwrapped_y": 0.0,
    "hd_rates": np.zeros(64),
    "bump_amplitude": 0.0,
    "reservoir_norm": 0.0,
    "total_units_active": 0,
}
```

**Rationale:** ARM-C is the definitive deprivation control: it eliminates all internal representations across the full 2,114-unit architecture without injecting synthetic substitute biases.

### ARM-D: Full-Shuffled (Disrupted-Topology Control — 2,114 Units Permuted)
Disrupts the entire 2,114-unit manifold via three independent, pre-registered deterministic permutation matrices held fixed across each episode:
- $P_{hd} \in S_{64}$: Permutes the 64-neuron HD ring firing rates.
- $P_{grid} \in S_{1024}$: Permutes the 1,024-neuron grid sheet firing rates.
- $P_{res} \in S_{1026}$: Permutes the 1,026-neuron reservoir state vector.

The continuous ODEs and leaky dynamics evolve normally, but topological and temporal correspondence is completely destroyed.

**Disruption specification:**
```python
# Pre-registered per-episode permutations (deterministic from episode seed)
rng_ep = np.random.RandomState(ep_seed)
P_hd = rng_ep.permutation(64)                    # HD ring permutation
P_grid_flat = rng_ep.permutation(1024)            # Grid torus permutation (flattened)
P_res = rng_ep.permutation(1026)                  # Reservoir state permutation

# Apply permutations to neural arrays
r_hd_shuffled = cann.hd_ring.r[P_hd]
r_grid_flat = cann.grid_torus.r.flatten()[P_grid_flat]
r_grid_shuffled = r_grid_flat.reshape(32, 32)
cann.reservoir.x[:] = cann.reservoir.x[P_res]
```

**Derived quantities from shuffled arrays:**
```python
# Shuffled HD heading: population vector decode on permuted rates
angles_hd = np.linspace(-np.pi, np.pi, 64, endpoint=False)
C_shuf = float(np.sum(r_hd_shuffled * np.cos(angles_hd)))
S_shuf = float(np.sum(r_hd_shuffled * np.sin(angles_hd)))
hd_shuffled_heading = math.atan2(S_shuf, C_shuf)

# Shuffled grid displacement: population vector decode on permuted 2D rates
X, Y = np.meshgrid(np.arange(32), np.arange(32), indexing='ij')
angle_x = 2.0 * np.pi * X / 32.0
angle_y = 2.0 * np.pi * Y / 32.0
Cx = float(np.sum(r_grid_shuffled * np.cos(angle_x)))
Sx = float(np.sum(r_grid_shuffled * np.sin(angle_x)))
Cy = float(np.sum(r_grid_shuffled * np.cos(angle_y)))
Sy = float(np.sum(r_grid_shuffled * np.sin(angle_y)))
grid_shuf_phase_x = math.atan2(Sx, Cx)
grid_shuf_phase_y = math.atan2(Sy, Cy)
grid_shuf_x = grid_shuf_phase_x / (2 * np.pi) * 0.80
grid_shuf_y = grid_shuf_phase_y / (2 * np.pi) * 0.80
```

**State passed to deliberation:**
```python
cann_state = {
    "hd_decoded_heading": spawn_yaw + hd_shuffled_heading - initial_hd_shuffled,
    "grid_unwrapped_x": spawn_x + (grid_shuf_x - initial_grid_shuf_x) * cos(spawn_yaw)
                                 - (grid_shuf_y - initial_grid_shuf_y) * sin(spawn_yaw),
    "grid_unwrapped_y": spawn_y + (grid_shuf_x - initial_grid_shuf_x) * sin(spawn_yaw)
                                 + (grid_shuf_y - initial_grid_shuf_y) * cos(spawn_yaw),
    "hd_rates": np.roll(r_hd_shuffled, k_shift),
    "bump_amplitude": float(np.sqrt(C_shuf**2 + S_shuf**2)),
    "reservoir_norm": float(np.linalg.norm(cann.reservoir.x)),
    "total_units_active": 2114,
}
```

**Rationale:** ARM-D preserves unit activation norms, metabolic activity, and marginal distributions while destroying internal topological and temporal order across all 2,114 units.

### Why ARM-B (Frozen) Is Removed from Primary Certification

ARM-B (freeze at spawn state) is excluded from the primary certification criterion because:
1. Freezing heading at spawn orientation provides an artificial compass lock that is structurally confounded with corridor alignment.
2. At $t = 0$, frozen state is mathematically identical to intact state, yielding $\rho = 1.000$ by construction.
3. Freezing is not deprivation — it is providing a different (potentially advantageous) static prior.

ARM-B may be retained as an **observational control** for post-hoc analysis, but its results **do not** contribute to the Stage 3.1-R pass/fail verdict.

---

## 4. Task Environments

All tasks are designed so that **instantaneous sonar is fundamentally insufficient** to determine the correct action during a critical decision window. Each task includes a sensory blackout period where all 15 sonar rays return $5.0\text{ m}$ (maximum range).

### Task 1: Sensor Blackout Corridor Curve (`layout_1_left_trap`)
- **Episode length:** 80 ticks (2.4 s)
- **Geometry:** Sharp $90°$ left corridor curve, corridor width $0.60\text{ m}$
- **Blackout window:** Ticks 15–40 (25 ticks, 0.75 s)
- **CANN utility:** During blackout, the CANN heading and position are the only available orientation/displacement references. The organism must maintain path integration through the curve using CANN dead-reckoning, pre-turn into the curve using prospective unrolls grounded in CANN position.
- **Spawn:** $x \in [-3.05, -2.95]$, $y \in [-0.25, -0.15]$, $\theta \approx -\pi/2$ ($\pm 0.04$ rad)

### Task 2: Blind Corner Trap (`layout_2_right_trap`)
- **Episode length:** 80 ticks (2.4 s)
- **Geometry:** Acute right turn with recessed trap, corridor width $0.60\text{ m}$
- **Blackout window:** Ticks 10–30 (20 ticks, 0.60 s)
- **CANN utility:** Requires prospective braking grounded in CANN displacement. Without CANN, the organism cannot anticipate the wall during blackout.
- **Spawn:** $x \in [-3.45, -3.35]$, $y \in [-0.68, -0.62]$, $\theta \approx 0.0$ ($\pm 0.03$ rad)

### Task 3: Symmetric Sonic Bifurcation (`layout_3_t_junction`)
- **Episode length:** 80 ticks (2.4 s)
- **Geometry:** T-junction where lateral clearances are balanced ($d_L \approx d_R$). One branch leads to dead-end, other to open corridor.
- **Blackout window:** Ticks 15–35 (20 ticks, 0.60 s)
- **CANN utility:** Only global heading/grid state can disambiguate the correct branch during blackout when sonar sees identical clearances.
- **Spawn:** $x \in [-0.25, -0.15]$, $y \in [-2.55, -2.45]$, $\theta \approx \pi$ ($\pm 0.04$ rad)

### Task 4: Long-Horizon Compass Corridor (`layout_4_corridor_slit`)
- **Episode length:** 100 ticks (3.0 s)
- **Geometry:** Multi-chicane extended traversal requiring continuous heading maintenance
- **Blackout window:** Ticks 20–40 (20 ticks, 0.60 s)
- **CANN utility:** Persistent heading retention across consecutive opposite rotations during blackout. Without CANN, accumulated heading drift causes wall clips on exit from blackout.
- **Spawn:** $x \in [-2.55, -2.45]$, $y \in [2.20, 2.30]$, $\theta \approx 0.0$ ($\pm 0.03$ rad)

---

## 5. Sample Size & Statistical Power

| Parameter | Value |
|:---|:---|
| Seeds | 5 unseen pseudorandom: `[3001, 3002, 3003, 3004, 3005]` |
| Layouts | 4 task environments |
| Trials per layout per seed | 5 |
| Total trials per arm | $5 \times 4 \times 5 = 100$ |
| Arms | 3 (Intact, Zeroed, Full-Shuffled) |
| **Total benchmark episodes** | **300** |
| Statistical power | $N = 100$ paired observations, $> 95\%$ power to detect $d \ge 0.40$ at $\alpha = 0.01$ |

**Note:** Seeds `[3001–3005]` are **different** from the original battery seeds `[2001–2005]`. This prevents any data re-use.

---

## 6. Primary and Secondary Metrics

### Primary Endpoint (Behavioral Necessity — Stage 3.1-R Certification Criterion)

**Hull Clearance Degradation of ARM-C (Zeroed) vs ARM-A (Intact):**
$$\Delta C_{\text{hull}} = \bar{C}_{\text{Intact}} - \bar{C}_{\text{Zeroed}}$$

This is the **single primary endpoint** that determines Stage 3.1-R certification.

**Justification:** ARM-C (Zeroed) is the cleanest deprivation control. If removing all CANN state degrades clearance by a meaningful physical amount ($\ge 0.05\text{ m} = 5\text{ cm}$) with statistical significance ($p < 0.01$), then the CANN provides behaviorally necessary information.

### Secondary Metrics (Support, Do Not Substitute)

| Metric | Formula | Threshold | Purpose |
|:---|:---|:---:|:---|
| Action Divergence $\Delta\mathbf{u}$ | $\frac{1}{T}\sum_t \|\mathbf{u}_A(t) - \mathbf{u}_X(t)\|_2$ | $> 0.15$ | Mechanistic coupling proof |
| Candidate Rank Shift $\rho$ | Spearman correlation at blackout mid-tick | $\le 0.70$ | Decision modulation proof |
| Collision Rate Increase $\Delta\text{Coll}$ | $\text{Coll}_X - \text{Coll}_A$ | $\ge 0\%$ | Safety direction proof |
| Cohen's $d$ | $(\bar{C}_A - \bar{C}_X) / s_{\text{pooled}}$ | $\ge 0.40$ | Effect size (informational) |

### Rank Correlation Timing Fix

Spearman $\rho$ is computed at the **blackout midpoint tick** (not $t = 0$):
- Layout 1: tick 28 (midpoint of blackout 15–40)
- Layout 2: tick 20 (midpoint of blackout 10–30)
- Layout 3: tick 25 (midpoint of blackout 15–35)
- Layout 4: tick 30 (midpoint of blackout 20–40)

At the blackout midpoint, intact CANN has accumulated meaningful heading/displacement state while ablated arms have diverged. This captures the causal effect during active deliberation.

---

## 7. Statistical Test Protocol

1. **Primary Test:** Two-tailed Wilcoxon signed-rank test on 100 paired clearance differences: $(\mathbf{c}_{\text{Intact}} - \mathbf{c}_{\text{Zeroed}})$.
2. **Secondary Tests:**
   - Wilcoxon signed-rank on ARM-D (Full-Shuffled) paired clearances
   - McNemar's exact test on paired binary collision outcomes
3. **Multiple Comparison Correction:** Bonferroni correction across 2 primary comparisons (ARM-C, ARM-D): $\alpha_{\text{adjusted}} = 0.01 / 2 = 0.005$.
4. **Effect Size:** Cohen's $d$ using pooled sample variance.
5. **No Jitter:** Do not add synthetic jitter to paired differences. If all differences are exactly zero (tied ranks), report $p = 1.0$.

---

## 8. Pass/Fail Adjudication Rules

### Certification PASS (Stage 3.1-R CERTIFIED)

**ALL** of the following must hold for **ARM-C (Zeroed)**:
1. $\Delta C_{\text{hull}} \ge +0.050\text{ m}$ (Primary Endpoint)
2. Wilcoxon $p < 0.005$ (Bonferroni-corrected)
3. $\Delta\mathbf{u} > 0.150$
4. $\rho \le 0.700$ (at blackout midpoint)
5. $\Delta\text{Coll} \ge 0.0\%$

**AND** at least **3 of 5** gates must hold for **ARM-D (Full-Shuffled)**:
1. $\Delta C_{\text{hull}} \ge +0.050\text{ m}$
2. Wilcoxon $p < 0.005$ (Bonferroni-corrected)
3. $\Delta\mathbf{u} > 0.150$
4. $\rho \le 0.700$ (at blackout midpoint)
5. $\Delta\text{Coll} \ge 0.0\%$

### Partial / Inconclusive

ARM-C passes all 5 gates, but ARM-D fails to pass 3 of 5 gates.

**Interpretation:** CANN provides necessary information under complete deprivation, but the topology-preserving disruption does not reliably degrade behavior. This may indicate that the grid/HD scalar readout pathway (Pathway A) is the primary behavioral channel, while the population vector alignment (Pathway B) is negligible.

**Action:** Stage 3.1-R is recorded as INCONCLUSIVE. A focused follow-up addressing the specific failing ARM-D gates may be designed.

### FAIL CLOSED

ARM-C fails any of the 5 gates.

**Interpretation:** The CANN does not provide behaviorally necessary information even under complete deprivation during sensory blackout. The reactive deliberation system with unprivileged dead-reckoning (`self.pose`) and occupancy memory is sufficient.

**Action:** Stage 3.1-R is recorded as FAILED. Stage 3.2 and 3.3 remain LOCKED. A fundamental architectural review is required.

---

## 9. Exclusion and Stopping Rules

### Episode Exclusion
- Episodes where physical spawn results in immediate wall contact ($t = 0$ collision) are excluded and replaced by the next valid spawn configuration from the seed sequence.
- Maximum 200 spawn attempts per layout per seed.

### Early Stopping
- **No early stopping for favorable results.** All 300 episodes must complete regardless of interim statistics.
- **Emergency stop** only if $> 5$ consecutive MuJoCo simulation crashes occur (hardware/software failure, not experimental failure).

---

## 10. Forensic Traceability Requirements

For each episode, the following must be recorded in `stage3_1R_raw_trials.json`:

1. **Spawn configuration:** `(x, y, yaw, seed, layout_id, trial_idx)`
2. **Per-tick CANN state:** `{hd_heading, grid_x, grid_y, bump_amplitude}` (ARM-A only, for telemetry)
3. **Per-tick action commands:** `(u_L, u_R)` for ARM-A, ARM-C, ARM-D
4. **Per-tick candidate utilities:** Full 24-entry utility dict at blackout midpoint tick
5. **Per-tick selected branch name**
6. **Per-tick minimum hull clearance** (from physical sonar, not blackout-masked)
7. **Collision flag and collision tick**
8. **Blackout window boundaries**
9. **Permutation matrices** `P_hd`, `P_grid_flat` for ARM-D (or their seeds)

---

## 11. What This Protocol Does NOT Do

1. ❌ Does not claim Stage 3.1 has passed (original result is permanently preserved as FAILED)
2. ❌ Does not modify frozen baseline code (`brain/carl_stage2_*`, SHA-256 locked)
3. ❌ Does not change acceptance thresholds (except adding Bonferroni correction, which is *stricter*)
4. ❌ Does not implement MPPI, Stage 3.2, or any later milestone
5. ❌ Does not add homeostatic motivation or new architectural capabilities
6. ❌ Does not modify the CARL developmental roadmap
7. ❌ Does not re-use seeds from the original battery
