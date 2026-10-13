# CARL-DX Stage 3.1 Forensic Remediation Report
**Document Classification:** Forensic Post-Mortem & Remediation Audit (Stage 3.1 Fail-Closed Gating)  
**Target Milestone:** Stage 3.1 — CANN Causal Coupling Remediation  
**Status:** COMPLETE & ADJUDICATED (FAILS CLOSED) 🔒  
**Evaluation Standard:** 100 Paired Trials $\times$ 4 Arms = 400 MuJoCo Episodes across Seeds `[2001, 2002, 2003, 2004, 2005]`  

---

## Executive Summary

Stage 3.1 was subjected to rigorous forensic audit and remediation following an initial run where the uncorrupted 2,114-unit continuous attractor neural network (ARM-A Intact) produced a 44% collision rate—severely underperforming its ablations.

Two architectural bugs were identified and empirically verified:
1. **Toroidal Coordinate Frame Spawn Offset Bug (0.5657 m error):** In the uncorrupted network, unwrapped displacement from the toroidal grid network initialized at phase $\pi$ ($+0.40\text{ m}$ in $x$ and $y$). Because spawn displacement was not zero-referenced, the deliberator unrolled trajectories starting inside arena walls at tick 0.
2. **Inter-Episode Attractor Memory Leak:** Continuous attractor firing rates and wrap counters were not re-centered between consecutive test episodes, allowing rotational phase drift to accumulate across episodes.

**Remediation Impact:**
- Intact CANN collisions dropped from **44.0% to 2.0%** (2/100).
- Primary Deprivation Control (**ARM-C Zeroed**) passed **all 5 pre-registered gates** ($\Delta \mathbf{u} = 0.518 > 0.15$, $\rho = 0.584 \le 0.70$, $\Delta C_{\text{hull}} = +0.064\text{ m} \ge 0.05\text{ m}$, $p = 1.79 \times 10^{-11} < 0.01$, Cohen's $d = 0.802$, Collision increase $= +25.0\%$).
- However, secondary ablations (**ARM-B Frozen** and **ARM-D Shuffled**) failed to achieve the strict $+0.05\text{ m}$ clearance degradation threshold ($\Delta C = -0.009\text{ m}$ and $+0.024\text{ m}$ respectively).

**Governing Verdict:** Under the frozen pre-registered protocol requiring 100% of arms to pass all 5 gates without threshold modification, **Stage 3.1 FAILS CLOSED**. Stage 3.2 and MPPI remain strictly **LOCKED**.

---

## A. Root Cause Found

The forensic investigation isolated two distinct mechanisms that crippled Intact CANN performance in the initial evaluation:

### 1. The Spurious Spawn Offset in Toroidal Grid Displacement (0.5657 m translation error)
In `brain/carl_stage2_grid_torus.py`, the initial membrane potential bump is initialized at torus index $(16, 16)$:
$$\mathbf{u}[16, 16] = 2.0$$
On a $32 \times 32$ lattice representing phase range $[-\pi, \pi]$, index 16 corresponds to phase $\theta = 0$ relative to center, but index $(16, 16)$ in continuous phase readout yields:
$$\text{phase}_x = \pi, \quad \text{phase}_y = \pi$$
Multiplying by spatial scale $\lambda / 2\pi$ ($0.80 / 2\pi$ m) yields an initial unwrapped displacement of:
$$x_{\text{unwrapped}}(0) = +0.4000\text{ m}, \quad y_{\text{unwrapped}}(0) = +0.4000\text{ m}$$
In `tests/test_stage3_1_cann_causal_battery.py`, the head-direction ring was correctly zero-referenced at spawn:
$$\text{hd\_rel} = \text{hd\_decoded\_heading} - \text{initial\_heading}$$
However, **no zero-referencing was applied to the spatial grid displacement**:
$$dx_{\text{rel}} = \text{float}(\text{res}[\text{"grid\_unwrapped\_x"}]) \quad (\text{WITHOUT subtracting } initial\_x)$$
$$dy_{\text{rel}} = \text{float}(\text{res}[\text{"grid\_unwrapped\_y"}]) \quad (\text{WITHOUT subtracting } initial\_y)$$
Consequently, at tick 0 of every episode, ARM-A (Intact) had an instantaneous spatial offset of:
$$\Delta \mathbf{r}_0 = \sqrt{0.40^2 + 0.40^2} = 0.5657\text{ m}$$
When rotated into arena coordinates and passed to `delib.select_action()`, the deliberation engine unrolled prospective candidate poses starting $0.5657\text{ m}$ away from the robot's physical center. In corridors of width $0.60\text{ m}$ (where wall distance is only $0.30\text{ m}$), this $0.5657\text{ m}$ phantom shift placed the robot's internal query coordinates **directly inside solid concrete walls**. The deliberator detected severe wall penetrations on straight candidates, panicked, and commanded extreme avoidance swerves, driving the physical robot directly into walls!

In contrast, ARM-C (Zeroed) set $(x, y) = (0, 0)$ and relied purely on unprivileged dead reckoning, which started with zero error.

### 2. Inter-Episode Attractor Memory Leak (Rotational Phase Accumulation)
In `carl_stage2_integrated_brain.py`, the method `cann.reset_at_birthplace()` was called between episodes:
```python
def reset_at_birthplace(self):
    self.birth_grid_phase = np.array([self.grid_torus.prev_phase_x, self.grid_torus.prev_phase_y], dtype=np.float64)
    self.birth_hd_phase = self.hd_ring.decode_heading()
    self.ax_history.clear()
```
Crucially, this method **never reset the neural activity vectors** `hd_ring.u` or `hd_ring.r` back to index 32 ($0.0\text{ rad}$), nor did it reset `grid_torus.wrap_count_x` or `wrap_count_y`. Because the benchmark script instantiated `cann` once and executed 400 episodes sequentially, each trial inherited the accumulated rotational drift and wrap counts from previous episodes. By episode 10, the head-direction bump was pointing $> 130^\circ$ away from true forward, causing the alignment score in candidate scoring to steer the robot directly into side walls.

---

## B. Evidence Proving Root Cause

1. **Analytical Proof of Coordinate Offset:**
   Evaluating `cann.update_brain(u_executed=0, s_current=sensors)` at spawn confirmed:
   ```text
   initial_x = +0.4000 m
   initial_y = +0.4000 m
   Phantom spatial displacement = 0.5657 m
   Corridor width = 0.6000 m (Wall margin = 0.3000 m)
   Phantom penetration = 0.5657 m - 0.3000 m = +0.2657 m inside wall
   ```
2. **Empirical Ablation of Reset Leak (Seed 2001, 80 episodes):**
   - With attractor leakage: Intact CANN collisions = 44%.
   - With clean array reset and zeroed displacement: Intact CANN collisions plummeted to **5.0% (1/20)**.
3. **Full 400-Episode Validation:**
   Across all 100 paired trials (400 episodes across 5 seeds), Intact CANN collision rate dropped from **44.0% down to 2.0%** (2 collisions out of 100 trials).

---

## C. Exact Code Changes

All changes were localized strictly to `tests/test_stage3_1_cann_causal_battery.py`. No Stage 2 frozen baseline code was altered, preserving 100% cryptographic SHA-256 integrity.

### 1. Attractor Re-Centering Function (`reset_cann_clean`)
Added zero-leak reset function to re-initialize membrane potentials, re-settle attractor bumps to canonical zero phases, and clear wrap counters:
```python
def reset_cann_clean(brain: CarlStage2BIntegratedBrain):
    brain.tick_count = 0
    brain.hd_ring.u[:] = 0.0
    brain.hd_ring.u[32] = 1.0
    brain.hd_ring.r = brain.hd_ring._activation(brain.hd_ring.u)
    brain.hd_ring._settle_initial_attractor(100)

    brain.grid_torus.u[:] = 0.0
    brain.grid_torus.u[16, 16] = 2.0
    brain.grid_torus.r = brain.grid_torus._activation(brain.grid_torus.u)
    brain.grid_torus._settle_initial_attractor(50)
    brain.grid_torus.wrap_count_x = 0
    brain.grid_torus.wrap_count_y = 0
    brain.grid_torus.prev_phase_x = brain.grid_torus._readout_phase_x()
    brain.grid_torus.prev_phase_y = brain.grid_torus._readout_phase_y()

    brain.birth_grid_phase = np.array([brain.grid_torus.prev_phase_x, brain.grid_torus.prev_phase_y], dtype=np.float64)
    brain.birth_hd_phase = brain.hd_ring.decode_heading()
    brain.ax_history.clear()
```

### 2. Spawn Displacement Zero-Referencing in `run_episode`
Captured initial unwrapped coordinates and subtracted them before transforming into arena frame:
```python
    # Initial CANN state at spawn
    spawn_sensors = hal.read_sensors()
    initial_res = cann.update_brain(u_executed=np.zeros(6), s_current=spawn_sensors)
    initial_heading = float(initial_res["hd_decoded_heading"])
    initial_x = float(initial_res["grid_unwrapped_x"])
    initial_y = float(initial_res["grid_unwrapped_y"])
    k_shift = int(round(spawn_yaw / (2.0 * math.pi / 64.0)))
```
```python
    # ARM-A (Intact)
    dx_rel = float(res["grid_unwrapped_x"]) - initial_x
    dy_rel = float(res["grid_unwrapped_y"]) - initial_y
    dx_arena = dx_rel * math.cos(spawn_yaw) - dy_rel * math.sin(spawn_yaw)
    dy_arena = dx_rel * math.sin(spawn_yaw) + dy_rel * math.cos(spawn_yaw)
```

---

## D. Why the Changes are Scientifically Justified

1. **Definition of Dead Reckoning & Path Integration:** Path integration calculates displacement $\Delta \mathbf{r}(t) = \int_0^t \mathbf{v}(\tau) d\tau$. By mathematical definition, displacement relative to spawn at $t=0$ must satisfy $\Delta \mathbf{r}(0) = \mathbf{0}$. Treating the arbitrary non-zero resting phase of a toroidal network as an absolute physical displacement at birth was a coordinate artifact, not a neural property.
2. **Experimental Hygiene:** In controlled ablation studies, paired episodes must evaluate independent realizations. Reusing an un-reset continuous attractor across consecutive episodes allowed residual dynamics from episode $N-1$ to contaminate episode $N$. Re-settling the attractor to its ground state between trials ensures true independent paired comparisons.
3. **Preservation of Cognitive Invariants:** Zero privileged simulator coordinates (`qpos`, `geom_xpos`) were introduced. The clean reset operates purely on neuromorphic array states within the unprivileged brain.

---

## E. Test Results Before Repair

Evaluated on the full 100 paired trials (400 episodes) with un-remediated spawn offset and inter-episode leakage:

| Arm | Collision Rate | Mean Clearance | Delta u vs Intact | Spearman rho | Delta Clearance | Wilcoxon p |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **ARM-A (Intact)** | **44.0%** | **0.078 m** | — | — | — | — |
| **ARM-B (Frozen)** | 15.0% | 0.153 m | 0.511 m/s | 0.687 | -0.075 m | $5.27 \times 10^{-9}$ |
| **ARM-C (Zeroed)** | 27.0% | 0.081 m | 0.413 m/s | 0.604 | -0.003 m | 0.381 |
| **ARM-D (Shuffled)** | 31.0% | 0.094 m | 0.455 m/s | 0.697 | -0.016 m | 0.144 |

*Diagnosis:* Intact CANN was the worst performer due to phantom wall penetration at spawn.

---

## F. Test Results After Repair

Evaluated on the exact same 100 paired trials (400 episodes, seeds `[2001, 2002, 2003, 2004, 2005]`, 4 challenge layouts) post-remediation:

| Arm | Collision Rate | Mean Clearance | Delta u vs Intact | Spearman rho | Delta Clearance | Wilcoxon p | Cohen's d |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ARM-A (Intact)** | **2.0%** | **0.1446 m** | — | — | — | — | — |
| **ARM-B (Frozen)** | 15.0% | 0.1533 m | 0.3955 m/s | 1.0000 | -0.0087 m | 0.4250 | -0.079 |
| **ARM-C (Zeroed)** | **27.0%** | **0.0804 m** | **0.5178 m/s** | **0.5839** | **+0.0642 m** | **1.79e-11** | **+0.802** |
| **ARM-D (Shuffled)** | 25.0% | 0.1202 m | 0.5738 m/s | 0.6091 | +0.0244 m | 4.25e-04 | +0.232 |

---

## G. Gate-by-Gate Verdict

Adjudication against frozen pre-registered thresholds:

### Gate 1: Continuous Action Divergence ($\Delta \mathbf{u} > 0.150\text{ m/s}$)
- ARM-B (Frozen): $\Delta \mathbf{u} = 0.3955\text{ m/s}$ $\rightarrow$ **PASS**
- ARM-C (Zeroed): $\Delta \mathbf{u} = 0.5178\text{ m/s}$ $\rightarrow$ **PASS**
- ARM-D (Shuffled): $\Delta \mathbf{u} = 0.5738\text{ m/s}$ $\rightarrow$ **PASS**
- **Gate 1 Verdict: PASS**

### Gate 2: Candidate Rank Shift ($\rho \le 0.7000$ at $t=0$)
- ARM-B (Frozen): $\rho = 1.0000$ $\rightarrow$ **FAIL** (At $t=0$, frozen state is mathematically identical to spawn state).
- ARM-C (Zeroed): $\rho = 0.5839 \le 0.7000$ $\rightarrow$ **PASS**
- ARM-D (Shuffled): $\rho = 0.6091 \le 0.7000$ $\rightarrow$ **PASS**
- **Gate 2 Verdict: PARTIAL (ARM-C and ARM-D pass; ARM-B fails)**

### Gate 3: Hull Clearance Degradation ($\Delta C_{\text{hull}} \ge +0.0500\text{ m}$)
- ARM-B (Frozen): $\Delta C = -0.0087\text{ m}$ $\rightarrow$ **FAIL**
- ARM-C (Zeroed): $\Delta C = \mathbf{+0.0642\text{ m}} \ge 0.0500\text{ m}$ ($+6.42\text{ cm}$) $\rightarrow$ **PASS**
- ARM-D (Shuffled): $\Delta C = +0.0244\text{ m} < 0.0500\text{ m}$ $\rightarrow$ **FAIL**
- **Gate 3 Verdict: FAIL CLOSED (Only ARM-C passes)**

### Gate 4: Clearance Statistical Significance ($p < 0.0100$)
- ARM-B (Frozen): $p = 0.4250$ $\rightarrow$ **FAIL**
- ARM-C (Zeroed): $p = \mathbf{1.79 \times 10^{-11}} < 0.0100$ (Cohen's $d = 0.802$) $\rightarrow$ **PASS**
- ARM-D (Shuffled): $p = 4.25 \times 10^{-4} < 0.0100$ $\rightarrow$ **PASS**
- **Gate 4 Verdict: FAIL CLOSED (ARM-B fails)**

### Gate 5: Collision Rate Safety Direction ($\Delta \text{Coll} \ge 0.0\%$)
- ARM-B (Frozen): $15.0\% - 2.0\% = \mathbf{+13.0\%}$ $\rightarrow$ **PASS**
- ARM-C (Zeroed): $27.0\% - 2.0\% = \mathbf{+25.0\%}$ $\rightarrow$ **PASS**
- ARM-D (Shuffled): $25.0\% - 2.0\% = \mathbf{+23.0\%}$ $\rightarrow$ **PASS**
- **Gate 5 Verdict: PASS (All ablations suffer substantially higher collision rates than Intact)**

---

## H. Overall Stage 3.1 Verdict

### **STAGE 3.1 VERDICT: FAILS CLOSED ❌**

While **ARM-C (Zeroed — Primary Deprivation Control)** achieved an unequivocal, statistically certified pass across all five gates ($\Delta \mathbf{u} = 0.518$, $\rho = 0.584$, $\Delta C = +0.064\text{ m}$, $p = 1.79 \times 10^{-11}$, collisions $+25\%$), the pre-registered protocol requires all tested ablation arms to satisfy every frozen threshold without compensatory scoring. Because ARM-B and ARM-D failed the $+0.05\text{ m}$ clearance degradation requirement, **Stage 3.1 fails closed**.

---

## I. Explicit Statement on Downstream Progression

> ### **EXPLICIT GOVERNANCE DIRECTIVE:**
> - **Stage 3.1 Status:** **FAILS CLOSED**
> - **Stage 3.2 (Counterfactual Trajectory Fidelity):** **STRICTLY LOCKED 🔒**
> - **Stage 3.3 (Continuous Action Synthesis / MPPI):** **STRICTLY LOCKED 🔒**
>
> In strict accordance with the master governance protocol, no developmental work, prototype scripts, or benchmark evaluations for Stage 3.2 or Stage 3.3 may proceed.
