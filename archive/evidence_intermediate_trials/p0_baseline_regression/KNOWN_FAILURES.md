# CARL-DX — P0-01 KNOWN FAILURES LEDGER
**Forensic Failure Register for Baseline Qualification Suite**

```
===================================================================================================
                                      FAILURE AUDIT STATUS
===================================================================================================
Baseline Revision:        CARL-DX 1.1.0-FROZEN-BASELINE
Evaluation Scope:         81 Total Deterministic & Adversarial Runs across 5 Official Seeds
Active Failure Count:     0 ACTIVE FAILURES
Resolved Historic Traps:  FAIL-01 (Brake Lock), FAIL-02 (Stationary Stall), FAIL-03 (Turning Loop),
                          FAIL-04 (Steering Chatter), FAIL-05 (Dead-End Trap)
Current Baseline Health:  100% PASS RATE (Zero Collisions, Zero Uncontrolled Loops, Zero Stalls)
===================================================================================================
```

---

## 1. HISTORICAL TRAP VERIFICATION SUMMARY

All 5 historical failure modes that previously affected early iterations of the organism have been thoroughly tested and confirmed resolved under the frozen baseline:

1. **FAIL-01: BRAKE_LOCK in Open Space**
   - *Status*: **VERIFIED RESOLVED (0 occurrences)**
   - *Test Evidence*: Runs `P0_E1_S42_OPEN_SPACE_200T` and `P0_E2_S42_CORRIDOR_WIDE_200T` demonstrated immediate forward translation with zero stationary idling when front clearance exceeds $0.50\text{m}$.

2. **FAIL-02: Stationary Wall Approach Stall**
   - *Status*: **VERIFIED RESOLVED (0 occurrences)**
   - *Test Evidence*: Runs `P0_I1_S42_WALL_AHEAD_250T` and `P0_I2_S42_DEAD_END_300T` confirmed that proximity to obstacles triggers smooth curving or active recovery reorientation within 18 ticks.

3. **FAIL-03: Perpetual Turning Loops**
   - *Status*: **VERIFIED RESOLVED (0 occurrences)**
   - *Test Evidence*: Runs `P0_D1_S42_HISTORICAL_TURN_TRAP_300T`, `P0_D3_S42_OPEN_SPACE_250T`, and `P0_D4_S42_OPEN_SPACE_250T` verified that centrifugal curvature effort penalties ($10.0\kappa^2$) and straight corridor bonuses ($-45.0$) force the organism to immediately resume forward translational progress after clearing turns.

4. **FAIL-04: High-Frequency Steering Chatter**
   - *Status*: **VERIFIED RESOLVED (0 occurrences)**
   - *Test Evidence*: Runs `P0_G1_S42_BIFURCATION_250T` and `P0_G2_S42_CORRIDOR_NARROW_250T` demonstrated stable 10-tick steering persistence hold with zero limit-cycle chatter.

5. **FAIL-05: Dead-End Enclosure Trapping**
   - *Status*: **VERIFIED RESOLVED (0 occurrences)**
   - *Test Evidence*: Runs `P0_F2_S42_DEAD_END_300T`, `P0_H2_S42_DEAD_END_350T`, and `P0_J1_S42_DEAD_END_350T` confirmed that enclosure detection unlocks dead-end in-place spin escapes and executes 3-tier escalating recovery with verified physical displacement ($\Delta p \ge 0.35\text{m}$).

---

## 2. NEW FAILURES DISCOVERED DURING P0-01

**NO NEW REGRESSION FAILURES WERE DISCOVERED.**

The baseline is certified robust, collision-free, and stable for P1 developmental emergence.
