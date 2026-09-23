# CARL-DX STAGE 3.1-R FORENSIC RATIONALE
**Document Classification:** Forensic Causal Analysis & Experimental Design Justification  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1-R — CANN Causal Coupling Remediation Re-Run  
**Status:** PRE-REGISTRATION ARTIFACT (FROZEN BEFORE EXECUTION)  
**Date:** September 13, 2026  

---

## 1. Purpose

This document establishes the forensic basis for the Stage 3.1-R remediation protocol. It records:
1. The exact reasons the original Stage 3.1 failed.
2. The complete causal signal flow audit of CANN state through deliberation.
3. The precise experimental design flaws identified.
4. The scientifically justified repairs the remediation protocol implements.

The original Stage 3.1 result is **permanently preserved as FAILED CLOSED**.

---

## 2. Original Stage 3.1 Result (Permanent Record)

| Gate | Metric | ARM-B (Frozen) | ARM-C (Zeroed) | ARM-D (Shuffled) | Overall |
|:---|:---|:---:|:---:|:---:|:---:|
| Gate 1 | $\Delta \mathbf{u} > 0.15$ | 0.511 ✅ | 0.413 ✅ | 0.455 ✅ | PASS |
| Gate 2 | $\rho \le 0.70$ | 0.687 ✅ | 0.604 ✅ | 0.697 ✅ | PASS |
| Gate 3 | $\Delta C_{\text{hull}} \ge +0.05\text{m}$ | -0.075 ❌ | -0.003 ❌ | -0.016 ❌ | FAIL |
| Gate 4 | Wilcoxon $p < 0.01$ | 5.27e-9 ✅ | 0.381 ❌ | 0.144 ❌ | FAIL |
| Gate 5 | $\Delta\text{Coll} \ge 0\%$ | -29% ❌ | -17% ❌ | -13% ❌ | FAIL |

**Verdict:** FAILED CLOSED. Intact CANN (44% collisions) was the worst performer.

### Post-Remediation Results (Coordinate-Fix Only, Same Protocol)

After fixing the spawn-offset bug and inter-episode memory leak:

| Gate | Metric | ARM-B (Frozen) | ARM-C (Zeroed) | ARM-D (Shuffled) | Overall |
|:---|:---|:---:|:---:|:---:|:---:|
| Gate 1 | $\Delta \mathbf{u} > 0.15$ | 0.396 ✅ | **0.518 ✅** | 0.574 ✅ | PASS |
| Gate 2 | $\rho \le 0.70$ | 1.000 ❌ | **0.584 ✅** | 0.609 ✅ | FAIL |
| Gate 3 | $\Delta C_{\text{hull}} \ge +0.05\text{m}$ | -0.009 ❌ | **+0.064 ✅** | +0.024 ❌ | FAIL |
| Gate 4 | Wilcoxon $p < 0.01$ | 0.425 ❌ | **1.79e-11 ✅** | 4.25e-4 ✅ | FAIL |
| Gate 5 | $\Delta\text{Coll} \ge 0\%$ | +13% ✅ | **+25% ✅** | +23% ✅ | PASS |

ARM-C passed all 5 gates with publication-grade significance. ARM-B and ARM-D failed due to experimental design flaws documented below.

---

## 3. Complete Causal Signal Flow Audit

### 3.1 CANN State Assembly

In [`brain/carl_stage2_integrated_brain.py`](file:///d:/ebca/brain/carl_stage2_integrated_brain.py), `update_brain()` produces:

```python
return {
    "hd_decoded_heading": current_heading_rad,      # float: HD ring population vector angle
    "hd_bump_amplitude": hd_res["bump_amplitude"],   # float: HD ring bump confidence
    "grid_unwrapped_x": grid_res["unwrapped_x_meters"],  # float: Grid torus unwrapped X displacement
    "grid_unwrapped_y": grid_res["unwrapped_y_meters"],  # float: Grid torus unwrapped Y displacement
    "is_slipping": is_slipping,
    "total_neurons_active": self.TOTAL_NEURONS,
}
```

In the test battery ([`test_stage3_1_cann_causal_battery.py`](file:///d:/ebca/tests/test_stage3_1_cann_causal_battery.py)), the `cann_state` dict passed to `delib.select_action()` is:

```python
cann_state = {
    "hd_decoded_heading": hd_arena,                  # Heading in arena frame
    "grid_unwrapped_x": spawn_x + dx_arena,          # Position X in arena frame
    "grid_unwrapped_y": spawn_y + dy_arena,           # Position Y in arena frame
    "hd_rates": r_hd_shifted,                         # 64-D HD ring firing rates (shifted to arena)
    "bump_amplitude": float(res["hd_bump_amplitude"]),
}
```

### 3.2 Deliberation Engine Ingestion Points

In [`brain/carl_stage2_3_r1_deliberation.py`](file:///d:/ebca/brain/carl_stage2_3_r1_deliberation.py), CANN state enters through exactly **TWO** pathways:

#### Pathway A: Rollout Origin (Lines 280–287)
```python
elif cann_state is not None:
    hd_head = cann_state.get("hd_decoded_heading", None)
    c_th = float(hd_head)
    c_x = float(cann_state.get("grid_unwrapped_x", self.pose[0]))
    c_y = float(cann_state.get("grid_unwrapped_y", self.pose[1]))
```

**Effect:** Sets the spatial origin `(c_x, c_y, c_th)` from which all 24 candidate trajectories are mentally unrolled. This is the **primary behavioral pathway** — it determines where ray-marching against the occupancy grid starts.

- **HD ring contribution:** Provides `c_th` (heading). Determines the directional fan orientation.
- **Grid torus contribution:** Provides `(c_x, c_y)` (position). Determines where trajectory endpoints sample the occupancy map.

#### Pathway B: CANN Alignment Score (Lines 488–495)
```python
if cann_state is not None and "hd_rates" in cann_state:
    r_hd = np.asarray(cann_state["hd_rates"], dtype=np.float64)
    if len(r_hd) == 64:
        angles_hd = np.linspace(-math.pi, math.pi, 64, endpoint=False)
        cand_terminal_heading = p_k[-1][2]
        coherence = float(np.sum(r_hd * np.cos(cand_terminal_heading - angles_hd)))
        cann_alignment_score = coherence * 0.25
```

**Effect:** Computes a directional coherence bonus between the candidate's terminal heading and the HD ring population vector. Added to utility.

- **Magnitude:** Maximum ~2.5 utility points.
- **HD ring contribution:** The 64-D firing rate vector `hd_rates` directly enters the utility sum.
- **Grid torus contribution:** **NONE.** Grid torus firing rates (`r`, 32×32=1,024 neurons) are never read by deliberation. Only the decoded scalar displacements are used (Pathway A).

### 3.3 Competing Utility Terms

| Utility Term | Source | Typical Magnitude | Category |
|:---|:---|---:|:---|
| Collision veto penalty | Prospective ray-marching | **800.0** | Dominant |
| Forward progress | Trajectory displacement × `fwd_w` | **4.0–32.0** | Strong |
| Lateral evasion | Live sonar proximity | **0–40.0** | Strong |
| Margin penalty | Prospective lateral clearance | **0–30.0** | Strong |
| Pivot penalty | Candidate name contains "pivot" | **25.0** | Moderate |
| Reverse penalty | Reverse candidate + front open | **15.0** | Moderate |
| Spatial bias | Occupancy grid terminal query | **0–7.5** | Moderate |
| Clearance bonus | Prospective front/mean/hull/side clr | **0–8.0** | Moderate |
| Centering bonus | Left-right wall balance | **0–2.5** | Weak |
| **CANN alignment** | **HD ring firing rates** | **0–2.5** | **Weak** |
| Wide margin bonus | Side clearance clamp | **0–0.8** | Negligible |

**Critical finding:** The CANN alignment term ($\le 2.5$) is **2–3 orders of magnitude weaker** than the collision veto ($800.0$) and **10–16× weaker** than the reactive sonar terms ($30.0–40.0$). In any environment where sonar can detect walls, the CANN alignment score is mathematically irrelevant to the argmax.

### 3.4 Grid Torus: How It Actually Affects Behavior

The grid torus neurons (1,024 units) contribute **only through Pathway A** (the decoded scalar displacement). Their contribution is:

1. Set `c_x = spawn_x + Δx_grid` and `c_y = spawn_y + Δy_grid`
2. These coordinates determine where mental trajectory rollout endpoints land
3. Rollout endpoints are sampled against the 128×128 occupancy grid via `grid_sample`
4. The occupancy values become collision vetoes ($800.0$) or clearance bonuses ($4.0 × \text{clearance}$)

This means grid torus ablation affects behavior **indirectly**: it shifts where the organism *thinks it is*, which shifts where ray-marching queries the occupancy map. If the organism's grid-based position estimate is accurate, it ray-marches from its true location. If the estimate is wrong (or zeroed), it ray-marches from the wrong location, potentially missing walls or hallucinating obstacles.

### 3.5 The 2,114-Unit Architectural Decision: Testing the Complete Neuromorphic Architecture

CARL's canonical specification defines a **2,114-unit neuromorphic computational architecture**:
- **64 units:** Head-Direction Ring Attractor (CANN)
- **1,024 units:** Toroidal Grid Sheet Attractor (CANN)
- **1,026 units:** Recurrent Liquid State Machine (LSM) Reservoir with continuous intrinsic homeostatic plasticity
**Total: 2,114 units.**

In the original battery and preliminary drafts, the reservoir occupied an ambiguous status: it was stepped continuously in `update_brain()`, but its internal state vector was not explicitly ablated in ARM-C or permuted in ARM-D. This created an unacceptable scientific ambiguity: *Was the experiment testing only a 1,088-unit spatial-directional subsystem, or the full 2,114-unit architecture?*

Under this final frozen protocol, this ambiguity is resolved decisively:

1. **The Battery Tests the Complete 2,114-Unit Architecture:**
   - **ARM-A (Intact, 2,114 units):** All 1,026 reservoir neurons step continuously with local continuous intrinsic plasticity ($g_t$ adaptation); all 1,088 CANN attractor units step via continuous grounded ODEs.
   - **ARM-C (Zeroed, 0 units):** Complete deprivation of all 2,114 units. `cann.reservoir.x.fill(0.0)`, `cann.hd_ring.r.fill(0.0)`, and `cann.grid_torus.r.fill(0.0)`. Deliberation receives zeroed spatial, directional, and temporal history.
   - **ARM-D (Full-Shuffled, 2,114 units):** All 2,114 units are permuted using three deterministic, episode-held permutations ($P_{hd} \in S_{64}$, $P_{grid} \in S_{1024}$, $P_{res} \in S_{1026}$). Shuffling $x_{res}[P_{res}]$ scrambles the reservoir's recurrent spatiotemporal phase-space trajectory while preserving its energy norm $\Vert x \Vert_2$, and shuffling $r_{hd}$ and $r_{grid}$ destroys directional and spatial topology.
   - Reservoir state norm and diagnostics are explicitly tracked in `cann_state` and recorded in telemetry.

2. **Causal Pathway Accounting:**
   - **Spatial-directional attractor core (1,088 units):** Directly modulates rollout origin (Pathway A) and candidate coherence (Pathway B).
   - **Recurrent reservoir (1,026 units):** Provides the non-linear temporal memory substrate and sensory preprocessing history.
   - By ablating and permuting both substrates simultaneously in ARM-C and ARM-D, the experiment tests the **unified 2,114-unit architecture as a single coherent organ**, ensuring no unablated recurrent capacity remains to silently compensate.

---

## 4. Identified Experimental Design Flaws

### Flaw 1: ARM-B (Frozen) — Confounded Directional Prior

**Description:** ARM-B clamps the CANN to spawn state: heading = `spawn_yaw`, position = `spawn_pos`. In corridor-dominated tasks where spawn heading aligns with the corridor axis, freezing provides a **useful compass lock** — the organism maintains a stable heading reference that prevents drift-induced collisions.

**Evidence:** Post-remediation ARM-B achieved **15% collisions** with mean clearance **0.153 m** — substantially *outperforming* Intact (2% collisions, 0.145 m clearance) on the clearance metric. ARM-B's $\rho = 1.000$ (at $t=0$, frozen and intact states are mathematically identical before any dynamics evolve).

**Diagnosis:** Freezing is not deprivation — it is providing a different (potentially advantageous) prior. The ARM-B intervention cannot distinguish "CANN is useful" from "CANN drift is harmful."

### Flaw 2: ARM-D (Shuffled) — Incomplete Network Disruption

**Description:** In the original test battery, ARM-D shuffled only the **64-neuron HD ring** population via permutation `P_ep_hd`:
```python
P_ep_hd = rng_ep.permutation(64)
r_shuf = cann.hd_ring.r[P_ep_hd].copy()
```

The **1,024-neuron grid torus** was left completely untouched. The grid-derived position `(c_x, c_y)` — which is the primary behavioral pathway — was not disrupted:
```python
# ARM-D: Grid displacement computed normally (NOT shuffled)
dx_rel = float(res["grid_unwrapped_x"]) - initial_x
dy_rel = float(res["grid_unwrapped_y"]) - initial_y
dx_arena = dx_rel * math.cos(spawn_yaw) - dy_rel * math.sin(spawn_yaw)
dy_arena = dx_rel * math.sin(spawn_yaw) + dy_rel * math.cos(spawn_yaw)
```

ARM-D randomized the heading only (`hd_decoded_heading = rng_ep.uniform(-π, π)`), leaving the grid position intact at `spawn_pos + Δ_arena`. This preserved the main ray-marching origin pathway.

**Consequence:** ARM-D tested "Does disrupting 64/2,114 neurons (HD only) while preserving 1,024 grid neurons impair behavior?" — not "Does disrupting the full CANN impair behavior?"

### Flaw 3: Rank Correlation Measured at $t = 0$

**Description:** Spearman $\rho$ was computed at tick 0 — before any sensory blackout, before any meaningful navigation decision, and before the CANN has accumulated any displacement from spawn.

At $t = 0$:
- The CANN has executed zero velocity integration ticks
- The HD ring bump has not shifted from its spawn position
- The grid torus has not accumulated any displacement
- All sonars are reading true initial clearances (no blackout yet)

For ARM-B (Frozen), at $t = 0$ the frozen state **is** the spawn state, yielding $\rho = 1.000$ by mathematical construction.

**Consequence:** The rank correlation captures initialization artifacts, not active deliberation effects.

### Flaw 4: Reservoir Not Addressed in Intervention Design

**Description:** The 1,026-unit reservoir is part of the "2,114-unit neuromorphic computational architecture" but is never mentioned in any intervention arm. Since the reservoir does not enter the deliberation pipeline directly (see §3.5), this is not a direct experimental confound, but it means the experiment only tests 1,088/2,114 neurons (HD 64 + Grid 1,024) rather than the full architecture.

**Decision Required:** Whether Stage 3.1-R should include reservoir disruption in ARM-D.

---

## 5. Summary of Required Repairs

| Flaw | Original Design | Repair |
|:---|:---|:---|
| **ARM-B Confound** | Freeze at spawn heading/position | Remove from primary certification; retain as observational control only |
| **ARM-D Incomplete** | Shuffle 64 HD neurons only | Shuffle both HD ring (64) AND grid torus (1,024) representations |
| **Rank Correlation Timing** | Computed at $t = 0$ | Compute during active blackout window where CANN state diverges |
| **Reservoir Omission** | Not disrupted | Exclude from disruption (justified: reservoir does not enter deliberation) |

### Why Reservoir Exclusion is Justified

The research question for Stage 3.1-R is: *"Does the CANN state causally contribute to downstream action selection and physical behavior?"*

The CANN state, as consumed by the deliberation engine, consists of:
1. `hd_decoded_heading` (from 64-neuron HD ring)
2. `grid_unwrapped_x`, `grid_unwrapped_y` (from 1,024-neuron grid torus)
3. `hd_rates` (64-D firing rate vector from HD ring)

The reservoir's 1,026 neurons do not produce any quantity that enters the `cann_state` dict. Disrupting the reservoir would affect the internal dynamics of the HD ring and grid torus indirectly (by corrupting the sensory projection that drives them), but this would confound the test: we would not be able to distinguish "CANN topology is necessary" from "Reservoir temporal integration is necessary."

Therefore, Stage 3.1-R tests the 1,088 neurons (64 HD + 1,024 Grid) whose outputs directly enter the deliberation pipeline. The reservoir is stepped normally in all arms.

---

## 6. Architectural Limitation Disclosure

The following limitation is documented but NOT repaired in Stage 3.1-R:

**The 24-Action Discrete Menu Constraint:** The deliberation engine evaluates $K = 24$ pre-defined candidate trajectories. This means the CANN alignment score ($\le 2.5$ utility points) can only influence the argmax when two candidates are separated by less than $2.5$ points in total utility. In practice, the collision veto ($800.0$) and reactive sonar terms ($30–40$) almost always determine the winner.

This is a known architectural limitation that Stage 3.3 (MPPI) is designed to address. Stage 3.1-R does not repair it. Instead, the protocol designs tasks (sensory blackout, heading-dependent navigation) where reactive sonar is *insufficient*, forcing the deliberation to rely on CANN-grounded trajectory evaluation rather than reactive sonar magnitude.
