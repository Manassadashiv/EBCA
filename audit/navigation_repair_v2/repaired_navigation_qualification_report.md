# CARL-DX Repaired Navigation Benchmark Qualification Report

**Execution Timestamp**: August 17, 2026  
**Evaluation Standard**: 10 Independent Physics & Behavioral Gates  
**Suite Status**: **`VERIFIED_WITH_FAILURES`**  
**Scorecard JSON**: [`audit/navigation_repair_v2/repaired_navigation_scorecard.json`](file:///D:/ebca/audit/navigation_repair_v2/repaired_navigation_scorecard.json)  

---

## 1. 10-Gate Acceptance Standard Summary

| Scenario ID | Min Clearance | Avoid Tick | Switches | Flips | Spins | Disp | Env Hash | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SCENARIO_A_WALL_DIRECTLY_AHEAD** | `0.17m` | `Tick 63` | `3` | `0` | `0` | `1.07m` | `c9968ffc0f912749` | **`FAIL`** |
| **SCENARIO_B_WALL_AT_45_DEG** | `0.16m` | `Tick 66` | `3` | `0` | `0` | `0.99m` | `db8f6ef612f34aae` | **`FAIL`** |
| **SCENARIO_C_CORRIDOR_WITH_OPENING** | `0.18m` | `Tick 52` | `5` | `0` | `2` | `1.07m` | `0364c8a507c5da2c` | **`FAIL`** |
| **SCENARIO_D_DEAD_END_CORRIDOR** | `0.60m` | `Tick None` | `2` | `0` | `0` | `0.77m` | `373246c7bc055edc` | **`FAIL`** |
| **SCENARIO_E_BIFURCATION_OBSTACLE** | `0.08m` | `Tick 60` | `3` | `0` | `0` | `1.03m` | `76edc325225c3760` | **`FAIL`** |
| **SCENARIO_F_MOVING_OBSTACLE** | `0.44m` | `Tick 48` | `4` | `0` | `0` | `1.23m` | `2adab07204fdbd7d` | **`PASS`** |
| **SCENARIO_G_NARROW_PASSAGE** | `0.45m` | `Tick 67` | `2` | `0` | `0` | `1.41m` | `897b5d772852598a` | **`PASS`** |
| **SCENARIO_H_UNEXPECTED_DROP** | `0.12m` | `Tick 52` | `4` | `0` | `1` | `1.24m` | `0048d545da095c5a` | **`FAIL`** |

---

## 2. Visual Evidence Package (720p HD MP4 with HUD + Diagnostics)

- [Scenario A Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_a_wall_directly_ahead.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_a_wall_directly_ahead_diagnostics.png)
- [Scenario B Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_b_wall_at_45_deg.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_b_wall_at_45_deg_diagnostics.png)
- [Scenario C Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_c_corridor_with_opening.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_c_corridor_with_opening_diagnostics.png)
- [Scenario D Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_d_dead_end_corridor.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_d_dead_end_corridor_diagnostics.png)
- [Scenario E Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_e_bifurcation_obstacle.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_e_bifurcation_obstacle_diagnostics.png)
- [Scenario F Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_f_moving_obstacle.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_f_moving_obstacle_diagnostics.png)
- [Scenario G Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_g_narrow_passage.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_g_narrow_passage_diagnostics.png)
- [Scenario H Video](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_h_unexpected_drop.mp4) | [Diagnostics Plot](file:///D:/ebca/evidence/navigation_repair_v2/benchmarks/scenario_h_unexpected_drop_diagnostics.png)
