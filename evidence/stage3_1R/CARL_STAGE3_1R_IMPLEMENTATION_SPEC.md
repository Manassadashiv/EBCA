# CARL-DX STAGE 3.1-R IMPLEMENTATION SPECIFICATION
**Document Classification:** Technical Implementation Spec (Pre-Execution)  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1-R — CANN Causal Coupling Remediation  
**Status:** SPECIFICATION ONLY (No code changes authorized yet)  
**Date:** September 13, 2026  

---

## 1. Scope

This document specifies the exact code changes required to implement the Stage 3.1-R pre-registered protocol. **No changes are authorized until the user approves execution.**

### Files to Create
- `tests/test_stage3_1R_cann_causal_battery.py` — New battery script implementing 3-arm protocol

### Files NOT Modified
- `brain/carl_stage2_3_r1_deliberation.py` — Frozen baseline (SHA-256 locked)
- `brain/carl_stage2_integrated_brain.py` — Frozen baseline
- `brain/carl_stage2_hd_ring.py` — Frozen baseline
- `brain/carl_stage2_grid_torus.py` — Frozen baseline
- `brain/carl_stage1_reservoir.py` — Frozen baseline
- `brain/carl_embodied_organism.py` — Frozen baseline
- `brain/carl_autonomous_agent.py` — Frozen baseline
- `tests/test_stage3_1_cann_causal_battery.py` — Original battery (preserved permanently)

---

## 2. Test Script Architecture

```
tests/test_stage3_1R_cann_causal_battery.py
├── reset_cann_clean(brain)          # Identical to original (proven correct)
├── generate_spawn_configs(seed)     # Same task geometries, new seeds
├── build_cann_state_intact(...)     # ARM-A: remediated coordinate transform
├── build_cann_state_zeroed()        # ARM-C: complete deprivation
├── build_cann_state_full_shuffled(...)  # ARM-D: HD + Grid permuted
├── run_episode(...)                 # Core simulation loop with blackout
├── compute_blackout_midpoint_rho(...)   # Rank correlation at blackout center
├── run_stage3_1R_battery()          # Main orchestrator
└── if __name__ == "__main__":
```

---

## 3. Detailed Function Specifications

### 3.1 `reset_cann_clean(brain: CarlStage2BIntegratedBrain)`

Ensures complete, zero-leak reset across all 2,114 units:
1. Resets 1,026-unit reservoir activations and gain via `brain.reservoir.reset()`
2. Re-centers HD ring bump (64 units) to index 32 ($\theta = 0$)
3. Re-centers grid torus bump (1,024 units) to $(16, 16)$, clears wrap counters, resets birthplace phases.

```python
def reset_cann_clean(brain: CarlStage2BIntegratedBrain):
    brain.tick_count = 0
    # 1. Reset 1,026-neuron LSM Reservoir
    brain.reservoir.reset()

    # 2. Reset 64-neuron HD Ring Attractor
    brain.hd_ring.u[:] = 0.0
    brain.hd_ring.u[32] = 1.0
    brain.hd_ring.r = brain.hd_ring._activation(brain.hd_ring.u)
    brain.hd_ring._settle_initial_attractor(100)

    # 3. Reset 1,024-neuron Toroidal Grid Sheet Attractor
    brain.grid_torus.u[:] = 0.0
    brain.grid_torus.u[16, 16] = 2.0
    brain.grid_torus.r = brain.grid_torus._activation(brain.grid_torus.u)
    brain.grid_torus._settle_initial_attractor(50)
    brain.grid_torus.wrap_count_x = 0
    brain.grid_torus.wrap_count_y = 0
    brain.grid_torus.prev_phase_x = brain.grid_torus._readout_phase_x()
    brain.grid_torus.prev_phase_y = brain.grid_torus._readout_phase_y()

    brain.birth_grid_phase = np.array([
        brain.grid_torus.prev_phase_x,
        brain.grid_torus.prev_phase_y
    ], dtype=np.float64)
    brain.birth_hd_phase = brain.hd_ring.decode_heading()
    brain.ax_history.clear()
```

### 3.2 `build_cann_state_intact(...)`

ARM-A (Intact): Uses the remediated coordinate transform across the full 2,114-unit architecture.

```python
def build_cann_state_intact(
    cann: CarlStage2BIntegratedBrain,
    res: Dict,
    initial_heading: float,
    initial_x: float,
    initial_y: float,
    spawn_pos: List[float],
    spawn_yaw: float,
    k_shift: int
) -> Dict[str, Any]:
    hd_rel = float(res["hd_decoded_heading"]) - initial_heading
    hd_arena = math.atan2(math.sin(spawn_yaw + hd_rel), math.cos(spawn_yaw + hd_rel))

    dx_rel = float(res["grid_unwrapped_x"]) - initial_x
    dy_rel = float(res["grid_unwrapped_y"]) - initial_y
    dx_arena = dx_rel * math.cos(spawn_yaw) - dy_rel * math.sin(spawn_yaw)
    dy_arena = dx_rel * math.sin(spawn_yaw) + dy_rel * math.cos(spawn_yaw)

    r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)

    return {
        "hd_decoded_heading": hd_arena,
        "grid_unwrapped_x": float(spawn_pos[0] + dx_arena),
        "grid_unwrapped_y": float(spawn_pos[1] + dy_arena),
        "hd_rates": r_hd_shifted,
        "bump_amplitude": float(res["hd_bump_amplitude"]),
        "reservoir_norm": float(np.linalg.norm(cann.reservoir.x)),
        "total_units_active": 2114,
    }
```

### 3.3 `build_cann_state_zeroed(...)`

ARM-C (Zeroed): Complete deprivation across all 2,114 units. Zeroes out reservoir activations, HD ring, and grid torus.

```python
def build_cann_state_zeroed(cann: CarlStage2BIntegratedBrain) -> Dict[str, Any]:
    # Deprive 1,026-unit reservoir
    cann.reservoir.x.fill(0.0)
    return {
        "hd_decoded_heading": 0.0,
        "grid_unwrapped_x": 0.0,
        "grid_unwrapped_y": 0.0,
        "hd_rates": np.zeros(64, dtype=np.float64),
        "bump_amplitude": 0.0,
        "reservoir_norm": 0.0,
        "total_units_active": 0,
    }
```

### 3.4 `build_cann_state_full_shuffled(...)` — Full 2,114-Unit Manifold Disruption

ARM-D (Full-Shuffled): Permutes the entire 2,114-unit manifold: HD ring (64), grid torus (1,024), and reservoir (1,026).

```python
def build_cann_state_full_shuffled(
    cann: CarlStage2BIntegratedBrain,
    res: Dict,
    P_hd: np.ndarray,           # (64,) permutation
    P_grid_flat: np.ndarray,    # (1024,) permutation
    P_res: np.ndarray,          # (1026,) permutation
    initial_hd_shuf: float,     # Shuffled heading at spawn
    initial_gx_shuf: float,     # Shuffled grid phase X at spawn
    initial_gy_shuf: float,     # Shuffled grid phase Y at spawn
    spawn_pos: List[float],
    spawn_yaw: float,
    k_shift: int
) -> Dict[str, Any]:
    # 1. Shuffle 1,026-unit Reservoir state vector (destroys spatiotemporal memory trajectories)
    cann.reservoir.x[:] = cann.reservoir.x[P_res]

    # 2. Shuffle 64-unit HD ring firing rates
    r_hd_shuffled = cann.hd_ring.r[P_hd]

    # Decode heading from shuffled rates
    angles_hd = np.linspace(-math.pi, math.pi, 64, endpoint=False)
    C_hd = float(np.sum(r_hd_shuffled * np.cos(angles_hd)))
    S_hd = float(np.sum(r_hd_shuffled * np.sin(angles_hd)))
    hd_shuf_decoded = math.atan2(S_hd, C_hd)

    # 3. Shuffle 1,024-unit grid torus firing rates
    r_grid_flat = cann.grid_torus.r.flatten()[P_grid_flat]
    r_grid_shuffled = r_grid_flat.reshape(32, 32)

    # Decode grid position from shuffled rates
    X, Y = np.meshgrid(np.arange(32), np.arange(32), indexing='ij')
    angle_x = 2.0 * math.pi * X / 32.0
    angle_y = 2.0 * math.pi * Y / 32.0
    Cx = float(np.sum(r_grid_shuffled * np.cos(angle_x)))
    Sx = float(np.sum(r_grid_shuffled * np.sin(angle_x)))
    Cy = float(np.sum(r_grid_shuffled * np.cos(angle_y)))
    Sy = float(np.sum(r_grid_shuffled * np.sin(angle_y)))
    gx_shuf = math.atan2(Sx, Cx) / (2.0 * math.pi) * 0.80
    gy_shuf = math.atan2(Sy, Cy) / (2.0 * math.pi) * 0.80

    # Relative displacement from shuffled initial state
    dgx = gx_shuf - initial_gx_shuf
    dgy = gy_shuf - initial_gy_shuf
    dx_arena = dgx * math.cos(spawn_yaw) - dgy * math.sin(spawn_yaw)
    dy_arena = dgx * math.sin(spawn_yaw) + dgy * math.cos(spawn_yaw)

    # Relative heading from shuffled initial state
    dhd = hd_shuf_decoded - initial_hd_shuf
    hd_arena = math.atan2(math.sin(spawn_yaw + dhd), math.cos(spawn_yaw + dhd))

    r_hd_shifted = np.roll(r_hd_shuffled, k_shift)
    bump_amp = float(math.sqrt(C_hd**2 + S_hd**2))

    return {
        "hd_decoded_heading": hd_arena,
        "grid_unwrapped_x": float(spawn_pos[0] + dx_arena),
        "grid_unwrapped_y": float(spawn_pos[1] + dy_arena),
        "hd_rates": r_hd_shifted,
        "bump_amplitude": bump_amp,
        "reservoir_norm": float(np.linalg.norm(cann.reservoir.x)),
        "total_units_active": 2114,
    }
```

**Key properties of this function:**
1. All 2,114 units across HD ring (64), grid torus (1,024), and reservoir (1,026) are independently permuted
2. Permutation matrices are deterministic per episode seed (reproducible)
3. Unit norms, energy budgets, and marginal rate distributions are mathematically preserved while internal spatiotemporal and directional topology is completely destroyed
4. Spawn-relative displacement is computed from shuffled readouts (zero-referenced)

### 3.5 Blackout Midpoint Rank Correlation

```python
def compute_blackout_midpoint_rho(
    utils_intact_at_mid: Dict[str, float],
    utils_ablated_at_mid: Dict[str, float]
) -> float:
    """Spearman rank correlation at blackout midpoint tick."""
    keys = sorted(utils_intact_at_mid.keys())
    vals_A = [utils_intact_at_mid[k] for k in keys]
    vals_X = [utils_ablated_at_mid[k] for k in keys]
    rho, _ = stats.spearmanr(vals_A, vals_X)
    return float(rho)
```

### 3.6 Episode Loop Modifications

The `run_episode()` function must:

1. Record candidate utilities at the blackout midpoint tick (not $t = 0$)
2. Pass blackout-masked sonar to deliberation during blackout window
3. Continue stepping the CANN even during ARM-C/ARM-D (the CANN's internal dynamics are irrelevant for zeroed arms, but for ARM-D the dynamics evolve normally — only the readout is shuffled)
4. Record per-tick minimum hull clearance from *physical* sonar (not blackout-masked)

---

## 4. Output Artifacts

### 4.1 Scorecard (`evidence/stage3_1R/stage3_1R_scorecard.json`)
```json
{
  "protocol_version": "3.1-R",
  "n_trials": 100,
  "n_arms": 3,
  "total_episodes": 300,
  "seeds": [3001, 3002, 3003, 3004, 3005],
  "arms": {
    "ARM-A_Intact": { "collision_rate_pct": ..., "mean_clearance": ..., "std_clearance": ... },
    "ARM-C_Zeroed": { ... },
    "ARM-D_FullShuffled": { ... }
  },
  "comparisons": {
    "ARM-C_Zeroed": {
      "delta_u": ..., "delta_clearance": ..., "wilcoxon_p": ...,
      "bonferroni_p": ..., "cohens_d": ..., "spearman_rho_blackout_mid": ...,
      "collision_increase_pct": ..., "gate_checks": { ... }, "gate_passed": ...
    },
    "ARM-D_FullShuffled": { ... }
  },
  "primary_endpoint_passed": ...,
  "overall_stage3_1R_verdict": "PASS" | "INCONCLUSIVE" | "FAIL_CLOSED"
}
```

### 4.2 Raw Trial Data (`evidence/stage3_1R/stage3_1R_raw_trials.json`)

Full per-trial records including spawn configs, per-tick actions, clearances, candidate utilities at blackout midpoint, collision flags, and permutation seeds.

### 4.3 Evidence Plots (`evidence/stage3_1R/plots/`)
- `plot1_action_divergence.png` — $\Delta\mathbf{u}$ bar chart (ARM-C, ARM-D)
- `plot2_hull_clearance.png` — Mean clearance comparison (3 arms)
- `plot3_collision_rates.png` — Collision rate comparison (3 arms)
- `plot4_spearman_rho_blackout.png` — Spearman $\rho$ at blackout midpoint
- `plot5_adjudication_matrix.png` — Formal gate pass/fail matrix

---

## 5. Validation Checks (Post-Execution)

Before reporting results, the following validation checks must pass:

1. **Episode Count:** Exactly 300 episodes completed (100 per arm)
2. **Seed Verification:** All episodes used seeds from `[3001, 3002, 3003, 3004, 3005]`
3. **Blackout Verification:** During blackout ticks, sonar array was set to `5.0` for deliberation input
4. **Physical Clearance:** Min hull clearances were measured from physical (non-masked) sonar
5. **Permutation Determinism:** ARM-D permutations are reproducible from `ep_seed`
6. **No Baseline Modification:** SHA-256 hashes of all 8 frozen decision pipeline files match Stage 3.0 baselines
7. **No Threshold Modification:** All acceptance thresholds match this pre-registered document exactly

---

## 6. Relationship to Original Battery

| Aspect | Original Stage 3.1 | Stage 3.1-R |
|:---|:---|:---|
| Status | FAILED CLOSED (permanent) | PENDING (awaiting execution approval) |
| Seeds | `[2001, 2002, 2003, 2004, 2005]` | `[3001, 3002, 3003, 3004, 3005]` |
| Arms | 4 (A, B, C, D) | 3 (A, C, D) |
| ARM-B (Frozen) | Included in certification | Excluded from certification |
| ARM-D shuffling | HD ring only (64 neurons) | HD ring (64) + Grid torus (1,024) |
| Rank correlation | $t = 0$ | Blackout midpoint tick |
| Multiple comparison | None | Bonferroni ($\alpha = 0.005$) |
| Spawn-offset bug | Present in initial run, fixed in remediation | Fixed |
| Inter-episode leak | Present in initial run, fixed in remediation | Fixed |
| Script file | `test_stage3_1_cann_causal_battery.py` | `test_stage3_1R_cann_causal_battery.py` |
