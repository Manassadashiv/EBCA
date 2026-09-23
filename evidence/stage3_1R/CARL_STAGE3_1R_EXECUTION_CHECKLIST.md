# CARL-DX STAGE 3.1-R EXECUTION CHECKLIST
**Document Classification:** Execution Sequencing & Verification Checklist  
**Repository Anchor:** `d:\ebca`  
**Target Milestone:** Stage 3.1-R — CANN Causal Coupling Remediation  
**Status:** PRE-EXECUTION (Awaiting user authorization)  
**Date:** September 13, 2026  

---

## Pre-Execution Gates (MUST ALL PASS BEFORE RUNNING)

- [ ] **G-PRE-1:** User has explicitly authorized Stage 3.1-R execution
- [ ] **G-PRE-2:** All 5 deliverables reviewed by user:
  - [ ] `CARL_STAGE3_1R_PREREGISTERED_PROTOCOL.md`
  - [ ] `CARL_STAGE3_1R_FORENSIC_RATIONALE.md`
  - [ ] `CARL_STAGE3_1R_IMPLEMENTATION_SPEC.md`
  - [ ] `CARL_STAGE3_1R_ACCEPTANCE_MATRIX.json`
  - [ ] `CARL_STAGE3_1R_EXECUTION_CHECKLIST.md` (this document)
- [ ] **G-PRE-3:** Original Stage 3.1 result permanently recorded as FAILED CLOSED in `CARL_PROJECT_MASTER_STATE.md`
- [ ] **G-PRE-4:** No open questions or governance amendments pending

---

## Phase 1: Environment Verification

- [ ] **1.1:** Verify Python environment has required packages (`numpy`, `scipy`, `torch`, `mujoco`)
- [ ] **1.2:** Verify `world/vessel_kinetic.xml` exists and loads without error
- [ ] **1.3:** Verify `evidence/stage2_2_grounded/arena_occupancy_grid.pt` exists
- [ ] **1.4:** Verify `checkpoints/stage2_2_grounded/grounded_body_model.pt` exists
- [ ] **1.5:** Run SHA-256 hash verification on all 8 frozen decision pipeline files:
  - `brain/carl_stage2_3_r1_deliberation.py`
  - `brain/carl_stage2_integrated_brain.py`
  - `brain/carl_stage2_hd_ring.py`
  - `brain/carl_stage2_grid_torus.py`
  - `brain/carl_stage1_reservoir.py`
  - `brain/carl_embodied_organism.py`
  - `brain/carl_autonomous_agent.py`
  - `brain/carl_stage1_hal.py`

---

## Phase 2: Test Script Implementation

- [ ] **2.1:** Create `tests/test_stage3_1R_cann_causal_battery.py` per implementation spec
- [ ] **2.2:** Verify `reset_cann_clean()` resets all 2,114 units (reservoir, HD ring, grid torus)
- [ ] **2.3:** Verify `build_cann_state_intact()` implements remediated coordinate transform across all 2,114 units
- [ ] **2.4:** Verify `build_cann_state_zeroed()` deprives all 2,114 units (reservoir.x.fill(0), zeroed rates/scalars)
- [ ] **2.5:** Verify `build_cann_state_full_shuffled()` permutes ALL 2,114 units: HD ring (64), grid torus (1,024), and reservoir (1,026)
- [ ] **2.6:** Verify blackout midpoint tick computation matches protocol (Layout 1: 28, Layout 2: 20, Layout 3: 25, Layout 4: 30)
- [ ] **2.7:** Verify Spearman $\rho$ computed at blackout midpoint, not $t = 0$
- [ ] **2.8:** Verify seeds are `[3001, 3002, 3003, 3004, 3005]` (NOT original `[2001–2005]`)
- [ ] **2.9:** Verify Bonferroni correction applied ($\alpha = 0.005$)
- [ ] **2.10:** Verify no synthetic jitter added to Wilcoxon test
- [ ] **2.11:** Run a single pilot trial (seed 3001, layout 1 only) to verify script executes without error

---

## Phase 3: Execution

- [ ] **3.1:** Execute full 300-episode battery: `python tests/test_stage3_1R_cann_causal_battery.py`
- [ ] **3.2:** Verify 300 episodes completed (100 per arm × 3 arms)
- [ ] **3.3:** Verify all 100 trial configs generated (5 seeds × 4 layouts × 5 trials)
- [ ] **3.4:** Record wall-clock execution time
- [ ] **3.5:** Save scorecard to `evidence/stage3_1R/stage3_1R_scorecard.json`
- [ ] **3.6:** Save raw trial data to `evidence/stage3_1R/stage3_1R_raw_trials.json`

---

## Phase 4: Post-Execution Validation

- [ ] **4.1:** Verify episode count: exactly 300 in raw data
- [ ] **4.2:** Verify seed set: all episodes used seeds from `{3001, 3002, 3003, 3004, 3005}`
- [ ] **4.3:** Verify blackout implementation: sonar arrays read 5.0 during blackout ticks
- [ ] **4.4:** Verify physical clearance: min hull clearances measured from physical (unmasked) sonar
- [ ] **4.5:** Verify ARM-D permutation determinism: re-derive permutations from saved seeds and confirm match
- [ ] **4.6:** Re-run SHA-256 hash verification: confirm no frozen files were modified during execution
- [ ] **4.7:** Verify no threshold was modified from pre-registered values

---

## Phase 5: Adjudication

- [ ] **5.1:** Compute primary endpoint: $\Delta C_{\text{hull}}$ (ARM-C vs ARM-A)
- [ ] **5.2:** Compute Bonferroni-corrected Wilcoxon $p$-values
- [ ] **5.3:** Compute Cohen's $d$ effect sizes
- [ ] **5.4:** Evaluate all 5 gates for ARM-C
- [ ] **5.5:** Evaluate all 5 gates for ARM-D
- [ ] **5.6:** Apply pass/fail rules from acceptance matrix:
  - If ARM-C passes all 5 AND ARM-D passes ≥ 3: **PASS**
  - If ARM-C passes all 5 but ARM-D passes < 3: **INCONCLUSIVE**
  - If ARM-C fails any gate: **FAIL CLOSED**
- [ ] **5.7:** Record verdict in scorecard JSON
- [ ] **5.8:** Generate 5 evidence plots (white background, publication-ready)

---

## Phase 6: Documentation

- [ ] **6.1:** Write `evidence/stage3_1R/CARL_STAGE3_1R_VERDICT.md` documenting:
  - Exact scientific verdict
  - Gate-by-gate adjudication with numerical values
  - Comparison to original Stage 3.1 results
  - Any anomalies or unexpected findings
- [ ] **6.2:** Update `CARL_PROJECT_MASTER_STATE.md` ledger with Stage 3.1-R result
- [ ] **6.3:** If PASS: Update master state to show Stage 3.2 as UNLOCKED (pending pre-registration)
- [ ] **6.4:** If FAIL: Document failure mechanism and recommended next action

---

## Mandatory Stop Points

| Condition | Action |
|:---|:---|
| Any pre-execution gate fails | STOP. Resolve before proceeding. |
| SHA-256 verification fails during execution | STOP. Abort run. Investigate. |
| > 5 consecutive MuJoCo crashes | STOP. Hardware/software failure. |
| Seed mismatch detected | STOP. Discard results. |
| Threshold mismatch detected | STOP. Discard results. |

---

## What This Checklist Does NOT Authorize

- ❌ Implementing MPPI (Stage 3.3)
- ❌ Running Stage 3.2 tests
- ❌ Modifying frozen cognitive baseline code
- ❌ Relaxing acceptance thresholds
- ❌ Changing the CARL developmental roadmap
- ❌ Declaring Stage 3.1 original as anything other than FAILED CLOSED
