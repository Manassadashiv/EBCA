# Causal Verification & Behavioral Measurement Rules

1. **Geometric Boundary Invariant**:
   - Behavioral state transitions (routes, chambers, detours) MUST require sustained geometric occupancy beyond a defined clearance threshold ($|y| \ge y_{\text{threshold}}$).
   - Zero-crossing sign tests (e.g. `py > 0.00`) on uncommitted centerline paths are strictly forbidden as evidence of behavioral choice.

2. **Transient vs Hazard Attribution**:
   - Always log both `first_any_update_tick` and `first_hazard_attributable_update_tick`.
   - Never attribute early wheel-slip or acceleration prediction errors to downstream experimental obstacles.

3. **Ledger-Driven Reporting Invariant**:
   - Master markdown and JSON report metrics must be computed directly by automated auditor scripts reading raw ledger CSVs with zero manual value overrides.
