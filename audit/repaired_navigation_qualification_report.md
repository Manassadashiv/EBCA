# CARL-DX Repaired Navigation Benchmark Qualification Report

**Execution Timestamp**: August 17, 2026  
**Evaluation Standard**: 10 Independent Physics & Behavioral Gates  
**Suite Status**: **`VERIFIED_WITH_FAILURES`**  
**Scorecard JSON**: [`audit/navigation_repair_v2/repaired_navigation_scorecard.json`](file:///D:/ebca/audit/navigation_repair_v2/repaired_navigation_scorecard.json)  

---

## 1. 10-Gate Acceptance Standard Summary

| Scenario ID | Min Clearance | Avoid Tick | Switches | Flips | Spins | Disp | Env Hash | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SCENARIO_A_WALL_DIRECTLY_AHEAD** | `0.20m` | `Tick 25` | `2` | `0` | `0` | `0.42m` | `a31cc061a7e5bf10` | **`FAIL`** |
| **SCENARIO_B_WALL_AT_45_DEG** | `0.42m` | `Tick 1` | `1` | `0` | `0` | `0.30m` | `bfd96b3bc9025e58` | **`FAIL`** |
| **SCENARIO_C_CORRIDOR_WITH_OPENING** | `0.15m` | `Tick 44` | `3` | `0` | `0` | `0.50m` | `561a735de6d58adb` | **`FAIL`** |
| **SCENARIO_D_DEAD_END_CORRIDOR** | `0.60m` | `Tick None` | `0` | `0` | `0` | `0.00m` | `8145a1612f67615e` | **`FAIL`** |
| **SCENARIO_E_BIFURCATION_OBSTACLE** | `0.12m` | `Tick None` | `2` | `0` | `0` | `0.64m` | `2dd0be9992360eef` | **`FAIL`** |
| **SCENARIO_F_MOVING_OBSTACLE** | `0.05m` | `Tick 40` | `4` | `1` | `0` | `0.87m` | `a096bcd176d6a645` | **`FAIL`** |
| **SCENARIO_G_NARROW_PASSAGE** | `0.18m` | `Tick 46` | `3` | `0` | `0` | `0.58m` | `3a24200d69766912` | **`FAIL`** |
| **SCENARIO_H_UNEXPECTED_DROP** | `0.10m` | `Tick None` | `1` | `0` | `0` | `0.64m` | `c17407b63520f1f3` | **`FAIL`** |

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
