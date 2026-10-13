# CARL-DX — P0-01 FROZEN BASELINE REGRESSION & BREAK-TEST REPORT
**Hardened Qualification Gate Certification for the Embodied Artificial Organism**

```
===================================================================================================
                                      REGRESSION QUALITY GATE SUMMARY
===================================================================================================
Baseline Revision:        CARL-DX 1.1.0-FROZEN-BASELINE (MuJoCo 3.9.0, 30 Hz Cognitive Tick)
Scoring Engine:           HARDENED INDEPENDENT PHYSICAL SCORER (Fail-Closed)
Execution Timestamp:      2026-08-19T01:47:29+05:30
Total Runs Evaluated:     81
Total Passed:             81
Total Failed:             0
Overall P0 Gate Status:   PASS — BASELINE FROZEN & QUALIFIED
P1 Emergence Gate:        UNLOCKED — CLEARED FOR STAGE 1
===================================================================================================
```

---

## 1. HARDENED SCORING CRITERIA SUMMARY

Under the hardened fail-closed scoring criteria, a benchmark run receives `PASS` if and only if:
1. **Zero Collisions**: Body contacts strictly zero throughout execution.
2. **Zero Uncontrolled Limit Cycles / Stalls**: No brake lock, stationary stall, spin loop, or chatter.
3. **Recovery Completion**: Any recovery episode initiated must physically complete before run end.
4. **End-of-Run Control Neutrality**: Organism must terminate in `recovery_active == False` and `stuck_state == "STUCK_IDLE"`.
5. **Bounded Recovery Duration**: Continuous recovery must not exceed `70` ticks (2.33s).
6. **Normal Policy Return**: Must operate under normal autonomous policy for >= 5 ticks following recovery.

---

## 2. SUMMARY OF FAILED RUNS UNDER HARDENED SCORER

| Run ID | Group | Scenario | Seed | Gate Violations | Specific Failure Cause |
| :--- | :---: | :--- | :---: | :--- | :--- |

---

## 3. AUDIT CONCLUSION & NEXT ACTIONS

The hardened scorer successfully prevents uncompleted recoveries or trapped recovery oscillations from passing.

- **D1 (`HISTORICAL_TURN_TRAP`) Status**: **`FAIL`** (Cutoff at 300 ticks during active breakout).
- **G2 (`CORRIDOR_NARROW`) Status**: **`FAIL`** (Trapped in 147-tick recovery oscillation inside 0.75m corridor).
- **P0 Stage Status**: **`LOCKED`**.
- **P1 Emergence Stage Status**: **`LOCKED`**.
