# CARL-DX — P0-01 SCORER HARDENING & BASELINE RE-QUALIFICATION REPORT
**Forensic Audit, Hardened Validation Gate Implementation & Baseline Re-Scoring Results**

```
===================================================================================================
                                      SCORER HARDENING SUMMARY
===================================================================================================
Audit Date:               August 17, 2026
Audited Module:           D:\ebca\tools\p0_independent_scorer.py
Unit Test Suite:          D:\ebca\tools\tests\test_p0_independent_scorer.py (12 / 12 Tests Passed)
Total Runs Re-Scored:     81 Raw Evidence Runs (Zero CARL Source Code Changes)
Old Scorer Verdict:       81 / 81 PASS (100.0%) [FLAWED PERMISSIVE LOGIC]
Hardened Scorer Verdict:  60 / 81 PASS (74.07%) | 21 / 81 FAIL (25.93%)
Run D1 Verdict:           FAIL (Terminated in mid-breakout @ tick 299)
Run G2 Verdict:           FAIL (Trapped in 147-tick recovery loop in narrow corridor)
Overall P0 Baseline Gate: LOCKED (Real Locomotion / Recovery Deficiencies Identified)
Overall P1 Emergence Gate:LOCKED (Progression Prohibited Until P0 Deficiencies Are Addressed)
===================================================================================================
```

---

## 1. OLD SCORING LOGIC & WHY IT WAS FLAWED

### Old Scoring Logic
In the previous implementation of `tools/p0_independent_scorer.py`, the pass/fail determination was computed on line 139 as:
```python
is_pass = (len(failures_detected) == 0) and (total_coll == 0)
```

### Forensic Flaws in Old Logic
1. **Conflating "No Detector Fired" with "Task Success"**: If an unscripted run entered a stuck state and initiated recovery, but the recovery was still in progress when the simulation timer ran out, no explicit failure detector fired. The scorer treated silence from the failure detectors as proof of successful navigation.
2. **Ignoring End-of-Run Active Recovery**: Runs terminating with `recovery_active == True`, `action_name == "RECOVERY_FORWARD_BREAKOUT"` (e.g., Run D1), or `action_name == "RECOVERY_REVERSE_CURVE_RIGHT"` (e.g., Run G2) were awarded `PASS` despite being in an uncompleted emergency state.
3. **Masking Continuous Recovery Loops**: The old limit-cycle and stall detectors explicitly ignored ticks where `recovery_active == 1` (`if not any(sub_rec)`). Consequently, in narrow corridors where the physical clearance threshold ($d_{\text{front}} > 0.65\text{m}$) was physically impossible to reach, CARL cycled continuously through recovery tiers for 147 consecutive ticks ($58.8\%$ of the run) without triggering any failure flag.

---

## 2. HARDENED SCORING ARCHITECTURE & GATES

The new independent scoring engine implements strict, fail-closed physical qualification gates:

### A. Universal Gates (All Runs)
- **`G_VALID`**: Telemetry CSV exists, headers match schema, tick count matches duration.
- **`G_NAN_INF`**: Zero NaN / Inf in positions, velocities, motor commands, energy, heat, prediction error.
- **`G_COMMAND_BOUNDS`**: Wheel actuator commands strictly capped: $|\omega_L|, |\omega_R| \le 12.0\text{ rad/s}$.
- **`G_NO_COLLISION`**: Multi-body contact collisions strictly zero (`total_collisions == 0`).
- **`G_NO_BRAKE_LOCK`**: Zero uncaused idling ($>15$ ticks in open space without thermal/safety cause).
- **`G_NO_STALL`**: Zero stationary stalls ($v_{\text{fwd, cmd}} > 0.08\text{m/s}, \Delta p < 0.02\text{m}$ for 20 ticks outside recovery).
- **`G_NO_SPIN_LOOP`**: Zero open-space spin loops ($|\Delta\psi| > 4\pi, \Delta p < 0.30\text{m}$).
- **`G_NO_STEERING_CHATTER`**: Zero rapid curvature flips ($>6$ flips in 12 ticks).
- **`G_NO_VELOCITY_LIMIT_CYCLE`**: Zero rapid velocity reversals ($>4$ flips in 15 ticks outside recovery).
- **`G_RESET_NEUTRAL`**: In post-reset runs, initial differential command must be neutral ($|\omega_L - \omega_R| \le 0.10$).

### B. Recovery & End-of-Run Gates
- **`G_END_RECOVERY_INACTIVE`**: Organism MUST terminate in `recovery_active == False`. Any run ending during active recovery is an automatic FAIL.
- **`G_END_STUCK_NEUTRAL`**: Organism MUST terminate in `stuck_state == "STUCK_IDLE"` (rejects `STUCK_CANDIDATE` or `STUCK_CONFIRMED`).
- **`G_END_ACTION_NORMAL`**: Final action primitive must NOT be a recovery primitive (`not action_name.startswith("RECOVERY_")`).
- **`G_RECOVERY_COMPLETED`**: Total recovery episodes started must equal total recovery episodes successfully exited.
- **`G_RECOVERY_DURATION_BOUNDED`**: Continuous time spent in a single recovery attempt must not exceed `MAX_RECOVERY_EPISODE_TICKS = 70` ticks ($2.33\text{s}$). Exceeding 70 ticks triggers `EXCESSIVE_RECOVERY_DURATION`.
- **`G_NORMAL_POLICY_RETURNED`**: Following recovery completion, the organism must operate under normal autonomous policy control for $\ge 5$ consecutive ticks before run end.

### C. Task Completion Gates
- **`G_TASK_COMPLETION`**: Open-space runs must achieve $\ge 0.50\text{m}$ net displacement (for runs $\ge 150$ ticks) or $\ge 0.10\text{m}$ (for startup 30 ticks).

---

## 3. UNIT TEST SUITE VALIDATION

The hardened scorer was independently validated across 12 synthetic unit tests in [`tools/tests/test_p0_independent_scorer.py`](file:///D:/ebca/tools/tests/test_p0_independent_scorer.py):

| Test Case | Scenario Description | Expected | Result |
| :--- | :--- | :---: | :---: |
| **TEST 1** | No collision + normal finish | `PASS` | **PASS** |
| **TEST 2** | No collision + active recovery at run end | `FAIL` | **PASS (Detected `TERMINATED_IN_ACTIVE_RECOVERY`)** |
| **TEST 3** | No collision + recovery duration $>70$ ticks | `FAIL` | **PASS (Detected `EXCESSIVE_RECOVERY_DURATION`)** |
| **TEST 4** | No collision + recovery success + normal return | `PASS` | **PASS** |
| **TEST 5** | Body contact collision occurred | `FAIL` | **PASS (Detected `BODY_COLLISION_BREACH`)** |
| **TEST 6** | Missing telemetry CSV file | `FAIL` | **PASS (Detected `MISSING_TELEMETRY_CSV`)** |
| **TEST 7** | Actuator command exceeds $+/-12.0\text{ rad/s}$ | `FAIL` | **PASS (Detected `INVALID_ACTUATOR_COMMAND`)** |
| **TEST 8** | NaN in floating base position | `FAIL` | **PASS (Detected `NAN_STATE`)** |
| **TEST 9** | Inf in forward linear velocity | `FAIL` | **PASS (Detected `INF_STATE`)** |
| **TEST 10** | Unresolved stuck state (`STUCK_CONFIRMED`) at end | `FAIL` | **PASS (Detected `UNRESOLVED_STUCK_STATE_AT_END`)** |
| **TEST 11** | Simulation timer cutoff during active recovery | `FAIL` | **PASS (Detected `INCOMPLETE_RECOVERY_EPISODE`)** |
| **TEST 12** | Stationary drift in open space ($\Delta p < 0.50\text{m}$) | `FAIL` | **PASS (Detected `INSUFFICIENT_TASK_DISPLACEMENT`)** |

---

## 4. RAW EVIDENCE RE-SCORING COMPARISON

Re-scoring the 81 existing raw telemetry runs produced the following difference ledger:

```
===================================================================================================
                                  RE-SCORING VERDICT TOTALS
===================================================================================================
Total Raw Runs Evaluated:        81
Old Scorer Verdict:              81 PASS / 0 FAIL  (100.0% Pass Rate)
Hardened Scorer Verdict:         60 PASS / 21 FAIL (74.07% Pass Rate)
Newly Identified Failures:       21 Runs
===================================================================================================
```

### Complete Inventory of Newly Failed Runs (21 Runs)

| Run ID | Group | Scenario | Seed | Specific Gate Violations | Failure Analysis |
| :--- | :---: | :--- | :---: | :--- | :--- |
| `P0_D1_S42_HISTORICAL_TURN_TRAP_300T` | **D1** | `HISTORICAL_TURN_TRAP` | 42 | `INCOMPLETE_RECOVERY_EPISODE`, `TERMINATED_IN_ACTIVE_RECOVERY`, `TERMINATED_WITH_RECOVERY_ACTION` | Cutoff at 300 ticks while in mid-breakout ($\Delta p = 0.109\text{m} < 0.35\text{m}$). |
| `P0_F2_S42_DEAD_END_300T` | **F2** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Dead-end recovery took $>70$ ticks to escape enclosure. |
| `P0_G2_S42_CORRIDOR_NARROW_250T` | **G2** | `CORRIDOR_NARROW` | 42 | `EXCESSIVE_RECOVERY_DURATION`, `INCOMPLETE_RECOVERY_EPISODE`, `TERMINATED_IN_ACTIVE_RECOVERY`, `TERMINATED_WITH_RECOVERY_ACTION`, `UNRESOLVED_STUCK_STATE_AT_END` | Continuous 147-tick recovery oscillation in $0.75\text{m}$ corridor. Clearance threshold unreachable. |
| `P0_H2_S42_DEAD_END_350T` | **H2** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Recovery duration exceeded 70 ticks during multi-tier escape. |
| `P0_I2_S42_DEAD_END_300T` | **I2** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Recovery duration exceeded 70 ticks in dead-end corner. |
| `P0_J1_S42_DEAD_END_350T` | **J1** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Reverse curve recovery cycle exceeded 70 ticks. |
| `P0_J2_S42_DEAD_END_350T` | **J2** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Targeted spin recovery cycle exceeded 70 ticks. |
| `P0_J3_S42_DEAD_END_350T` | **J3** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Breakout acceleration cycle exceeded 70 ticks. |
| `P0_K3_S42_CORRIDOR_NARROW_250T` | **K3** | `CORRIDOR_NARROW` | 42 | `EXCESSIVE_RECOVERY_DURATION`, `INCOMPLETE_RECOVERY_EPISODE`, `TERMINATED_IN_ACTIVE_RECOVERY`, `TERMINATED_WITH_RECOVERY_ACTION`, `UNRESOLVED_STUCK_STATE_AT_END` | Narrow corridor trapped recovery oscillation (duplicate of G2). |
| `P0_K5_S42_DEAD_END_300T` | **K5** | `DEAD_END` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Dead-end trap recovery exceeded 70 ticks. |
| `P0_L4_S42_DEAD_END_150T` | **L4** | `DEAD_END` | 42 | `INCOMPLETE_RECOVERY_EPISODE`, `TERMINATED_IN_ACTIVE_RECOVERY`, `TERMINATED_WITH_RECOVERY_ACTION`, `UNRESOLVED_STUCK_STATE_AT_END` | 150-tick run terminated prematurely while recovery was active. |
| `P0_N2_S42_CORRIDOR_WIDE_900T` | **N2** | `CORRIDOR_WIDE` | 42 | `EXCESSIVE_RECOVERY_DURATION` | Long corridor recovery attempt exceeded 70 ticks. |
| `P0_N2_S101_CORRIDOR_WIDE_900T` | **N2** | `CORRIDOR_WIDE` | 101 | `EXCESSIVE_RECOVERY_DURATION` | Long corridor recovery attempt exceeded 70 ticks. |
| `P0_N2_S2024_CORRIDOR_WIDE_900T` | **N2** | `CORRIDOR_WIDE` | 2024 | `EXCESSIVE_RECOVERY_DURATION` | Long corridor recovery attempt exceeded 70 ticks. |
| `P0_N2_S31415_CORRIDOR_WIDE_900T` | **N2** | `CORRIDOR_WIDE` | 31415 | `EXCESSIVE_RECOVERY_DURATION` | Long corridor recovery attempt exceeded 70 ticks. |
| `P0_N2_S8675309_CORRIDOR_WIDE_900T` | **N2** | `CORRIDOR_WIDE` | 8675309 | `EXCESSIVE_RECOVERY_DURATION` | Long corridor recovery attempt exceeded 70 ticks. |
| `P0_N3_S42_BIFURCATION_1800T` | **N3** | `BIFURCATION` | 42 | `EXCESSIVE_RECOVERY_DURATION` | 60s stress run recovery episode exceeded 70 ticks. |
| `P0_N3_S101_BIFURCATION_1800T` | **N3** | `BIFURCATION` | 101 | `EXCESSIVE_RECOVERY_DURATION` | 60s stress run recovery episode exceeded 70 ticks. |
| `P0_N3_S2024_BIFURCATION_1800T` | **N3** | `BIFURCATION` | 2024 | `EXCESSIVE_RECOVERY_DURATION` | 60s stress run recovery episode exceeded 70 ticks. |
| `P0_N3_S31415_BIFURCATION_1800T` | **N3** | `BIFURCATION` | 31415 | `EXCESSIVE_RECOVERY_DURATION` | 60s stress run recovery episode exceeded 70 ticks. |
| `P0_N3_S8675309_BIFURCATION_1800T` | **N3** | `BIFURCATION` | 8675309 | `EXCESSIVE_RECOVERY_DURATION` | 60s stress run recovery episode exceeded 70 ticks. |

---

## 5. FORENSIC SANITY CHECK FOR D1 AND G2

- **Run D1 (`P0_D1_S42_HISTORICAL_TURN_TRAP_300T`)**: Confirmed **`FAIL`** under hardened scorer due to `INCOMPLETE_RECOVERY_EPISODE` and `TERMINATED_IN_ACTIVE_RECOVERY`.
- **Run G2 (`P0_G2_S42_CORRIDOR_NARROW_250T`)**: Confirmed **`FAIL`** under hardened scorer due to `EXCESSIVE_RECOVERY_DURATION` (147 ticks in recovery) and `UNRESOLVED_STUCK_STATE_AT_END`.

---

## 6. SCIENTIFIC & GOVERNANCE STATUS

1. **CARL Source Code Status**: **100% UNTOUCHED**. Zero changes were made to `brain/`, `world/`, or robot control algorithms.
2. **Measurement System Status**: **CORRECTED & HARDENED**. The scoring engine now reliably detects genuine locomotion and recovery traps.
3. **P0 Baseline Status**: **`LOCKED`**. Real physical failure modes exist in CARL's recovery logic under narrow corridors ($0.75\text{m}$) and dead ends.
4. **P1 Emergence Status**: **`LOCKED`**. Progression to Stage 1 active inference emergence remains blocked until P0 recovery deficiencies are repaired.
