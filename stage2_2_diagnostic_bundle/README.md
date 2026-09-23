# Stage 2.2 Phase 1 Diagnostic Run Bundle (`STAGE 2.2-DIAG`)

**Package Root:** `d:/ebca/stage2_2_diagnostic_bundle/`  
**Milestone:** Stage 2.2 — Action-Conditioned Predictive World Model Redesign  
**Phase:** Phase 1 (Diagnostic Falsification Benchmark on Developmental Data)  
**Status:** **EMPIRICALLY COMPLETED — ALL 13 ARCHITECTURES FALSIFIED**  
**Air-Gap Guarantee:** `PRIMARY_UNSEEN_TEST` (Seeds `[303, 404, 505, 606, 707]`) strictly ungenerated and untouched.

---

## Directory Structure & Contents

### `docs/` — Specifications, Plans, Forensic Analysis, and Diagnostic Report
1. [`CARL_STAGE2_2_DIAGNOSTIC_REPORT.md`](docs/CARL_STAGE2_2_DIAGNOSTIC_REPORT.md): The definitive Phase 1 empirical report containing complete 13-model tables, hypothesis evaluations, root-cause synthesis, and Phase 2 recommendations.
2. [`CARL_STAGE2_2_REVISED_PREEXPERIMENTAL_SPECIFICATION.md`](docs/CARL_STAGE2_2_REVISED_PREEXPERIMENTAL_SPECIFICATION.md): Pre-experimental specification with all 8 locked invariants, capacity bounds, and pre-registered Battery 4 tolerance.
3. [`CARL_STAGE2_2_DIAGNOSTIC_MATRIX.md`](docs/CARL_STAGE2_2_DIAGNOSTIC_MATRIX.md): The 6-representation x 2-target x 6-battery test matrix.
4. [`CARL_STAGE2_2_REVISED_IMPLEMENTATION_PLAN.md`](docs/CARL_STAGE2_2_REVISED_IMPLEMENTATION_PLAN.md): The approved Phase 1 engineering plan.
5. [`CARL_STAGE2_2_REDESIGN_FORENSIC_ANALYSIS.md`](docs/CARL_STAGE2_2_REDESIGN_FORENSIC_ANALYSIS.md): Initial post-mortem identifying identity copying and action decoupling in Stage 2.2.

### `figures/` — 300 DPI Publication Quality Dashboards
1. [`diag_fig1_predictive_fidelity.png`](figures/diag_fig1_predictive_fidelity.png): Multi-horizon sonar R² across all timesteps (D_all) vs high-change transitions (D_dynamic).
2. [`diag_fig2_action_causality.png`](figures/diag_fig2_action_causality.png): Action zeroing, permutation, and sign inversion error surges across all 13 models.
3. [`diag_fig3_capacity_and_memory.png`](figures/diag_fig3_capacity_and_memory.png): Capacity-matched isolation of Condition F (M6-F-RES) vs M2-B-MATCHED vs M5-E-RES.
4. [`diag_fig4_master_dashboard.png`](figures/diag_fig4_master_dashboard.png): 6-panel executive dashboard summarizing fidelity, causality, disambiguation, branching, collision ROC-AUC, and parameter scaling.

### `data/` — Datasets, Checksums & Complete Scorecards
1. [`diagnostic_scorecard.json`](data/diagnostic_scorecard.json): Machine-readable JSON scorecard with exact metrics for all 13 models across the Canonical Six Batteries.
2. [`dataset_hashes.json`](data/dataset_hashes.json): Cryptographic SHA-256 digests and saturation audits of developmental partitions.
3. [`DEV_TRAIN.npz`](data/DEV_TRAIN.npz): 60 physical episodes (24,000 timesteps) across seeds [42, 101, 202] under 5 behavioral regimes.
4. [`DEV_VAL.npz`](data/DEV_VAL.npz): 20 physical episodes (8,000 timesteps) across 4 independent seeds [210, 220, 230, 240].

### `code/` — Reproducible Source Code & Isolation Tests
1. [`carl_stage2_2_diagnostic_collector.py`](code/carl_stage2_2_diagnostic_collector.py): Active-contingency physical data harvester.
2. [`carl_stage2_2_world_model_suite.py`](code/carl_stage2_2_world_model_suite.py): Clean, calibrated PyTorch definitions for all 13 models.
3. [`carl_stage2_2_memory_module.py`](code/carl_stage2_2_memory_module.py): Learned spatial environmental key-value memory module.
4. [`test_stage2_2_diagnostic_runner.py`](code/test_stage2_2_diagnostic_runner.py): Benchmark harness executing training and the Canonical Six Batteries.
5. [`carl_stage2_2_diagnostic_visualizer.py`](code/carl_stage2_2_diagnostic_visualizer.py): Script generating the 300 DPI publication figures.
6. [`test_stage2_2_fixed_oracle.py`](code/test_stage2_2_fixed_oracle.py): Unit test proving contact-subtracted collision oracle correctness.
7. [`test_stage2_2_anti_cheat_isolation.py`](code/test_stage2_2_anti_cheat_isolation.py): Static AST scanner and sandbox ensuring zero simulator leaks.
