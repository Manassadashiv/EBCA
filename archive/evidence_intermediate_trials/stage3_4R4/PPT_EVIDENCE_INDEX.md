# CARL Stage 3.4-R4 Presentation & Scientific Evidence Index

This index catalogs the authoritative diagnostic evidence, figures, demonstration videos, and telemetry artifacts produced for **Stage 3.4-R4** (Continuous Action Synthesis & Behavioral Discovery under Active Inference).

**Status:** `DIAGNOSTIC SCREENING COMPLETE — PRE-CERTIFICATION CHECKPOINT`  
**Date:** September 20, 2026  
**Artifact Directory:** [`evidence/stage3_4R4/`](file:///d:/ebca/evidence/stage3_4R4/)

---

## 1. High-Definition Demonstration Videos (720p, 30 FPS)

| Artifact | File | Resolution / FPS | Description |
| :--- | :--- | :--- | :--- |
| **Video 1** | [`videos/video1_r3_vs_r4_forensic.mp4`](file:///d:/ebca/evidence/stage3_4R4/videos/video1_r3_vs_r4_forensic.mp4) | 1280x720, 30 FPS | Synchronized side-by-side forensic replay of representative Config 0: Left shows R3 circular-approximation lateral wall strike at $y=-0.22\text{ m}$; Right shows R4 rectangular swept-hull feasibility + sonar heading fusion achieving clean, collision-free egress ($x \le -0.55\text{ m}$). |
| **Video 2** | [`videos/video2_cognitive_pov_demo.mp4`](file:///d:/ebca/evidence/stage3_4R4/videos/video2_cognitive_pov_demo.mp4) | 1280x720, 30 FPS | 8-Panel cognitive dashboard and body-eye POV demonstration during autonomous Active Inference escape under live telemetry ribbon. |

---

## 2. Publication-Quality Figures (>= 300 DPI)

| Figure | File | Type | Description |
| :--- | :--- | :--- | :--- |
| **Figure 1** | [`figures/fig1_trajectory_comparison.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig1_trajectory_comparison.png) | Vector / 300 DPI | Top-down physical vs estimated robot trajectories in Environment 1 (Turning Bay) comparing R3 failure vs R4 escape. |
| **Figure 2** | [`figures/fig2_rectangular_hull_swept_envelope.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig2_rectangular_hull_swept_envelope.png) | Heatmap / 300 DPI | 2D Clearance heatmap over lateral offset $y$ vs heading angle $\theta$ in 0.70 m corridor, showing safe rotation envelope ($|y| < 0.153\text{ m}$) and invariant boundary. |
| **Figure 3** | [`figures/fig3_heading_estimation.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig3_heading_estimation.png) | Time-Series / 300 DPI | Time-series of gyro integration, sonar wall orientation, and fused heading against evaluator ground truth, highlighting drift suppression. |
| **Figure 4** | [`figures/fig4_lateral_drift.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig4_lateral_drift.png) | Line Plot / 300 DPI | Centerline lateral offset over time comparing R3 unconstrained drift vs R4 bounded corridor tracking. |
| **Figure 5** | [`figures/fig5_mppi_candidate_fan.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig5_mppi_candidate_fan.png) | Trajectory Fan / 300 DPI | Receding-horizon candidate trajectory fan ($M=128, H=15$) showing accepted feasible vs rejected infeasible rollouts. |
| **Figure 6** | [`figures/fig6_efe_cost_landscape.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig6_efe_cost_landscape.png) | Scatter / 300 DPI | Expected Free Energy objective decomposition: $G_{\text{pragmatic}}$ vs $G_{\text{epistemic}}$ with rectangular hull feasibility mask. |
| **Figure 7** | [`figures/fig7_occupancy_frontier_heatmap.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig7_occupancy_frontier_heatmap.png) | Dual Heatmap / 300 DPI | Allocentric spatial memory: Channel 0 (Obstacle hits) and Channel 1 (Explored space with connected macro-frontier $f^*$). |
| **Figure 8** | [`figures/fig8_action_probability_mass.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig8_action_probability_mass.png) | Bar Plot / 300 DPI | MPPI candidate softmax probability mass distribution comparing dispersed R3 mass vs focused R4 reversal mass. |
| **Figure 9** | [`figures/fig9_collision_clearance_comparison.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig9_collision_clearance_comparison.png) | Bar / Boxplot / 300 DPI | Collision rate drop and physical hull clearance distribution across matched trials. |
| **Figure 10** | [`figures/fig10_arma_vs_armb.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig10_arma_vs_armb.png) | Grouped Bar / 300 DPI | ARM-A (Full Active Inference) vs ARM-B (Pragmatic-Only) matched outcome comparison ($\Delta = +30.0\%$). |
| **Figure 11** | [`figures/fig11_latency_distribution.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig11_latency_distribution.png) | Histogram & ECDF | Deliberation cycle latency distribution against Gate 4 pre-registered budgets ($20\text{ ms}$ mean, $45\text{ ms}$ p95). |
| **Figure 12** | [`figures/fig12_screening_scorecard.png`](file:///d:/ebca/evidence/stage3_4R4/figures/fig12_screening_scorecard.png) | Table / 300 DPI | Comprehensive 5-Gate diagnostic scorecard summarizing the 10-configuration screening results. |

---

## 3. Raw Machine-Readable Data & Telemetry

| Data File | Format | Description |
| :--- | :--- | :--- |
| [`r4_manifest.json`](file:///d:/ebca/evidence/stage3_4R4/r4_manifest.json) | JSON | SHA-256 baseline hashes and pre-flight configuration record. |
| [`r4_unit_test_results.json`](file:///d:/ebca/evidence/stage3_4R4/r4_unit_test_results.json) | JSON | Complete results from Phase 1 deterministic mathematical and geometric tests. |
| [`r4_ast_audit.json`](file:///d:/ebca/evidence/stage3_4R4/r4_ast_audit.json) | JSON | Gate 5 static AST decision-pipeline anti-cheat audit verification. |
| [`r4_single_episode_trace.json`](file:///d:/ebca/evidence/stage3_4R4/r4_single_episode_trace.json) | JSON | Complete control-cycle-by-cycle telemetry log for representative Config 0 (161 ticks). |
| [`r4_candidate_telemetry.json`](file:///d:/ebca/evidence/stage3_4R4/r4_candidate_telemetry.json) | JSON | Per-cycle candidate acceptance, rejection, entropy, and chosen actions. |
| [`r4_heading_fusion_telemetry.json`](file:///d:/ebca/evidence/stage3_4R4/r4_heading_fusion_telemetry.json) | JSON | Ground truth yaw, gyro heading, fused heading, error traces, and sonar confidence. |
| [`r4_clearance_telemetry.json`](file:///d:/ebca/evidence/stage3_4R4/r4_clearance_telemetry.json) | JSON | Lateral offsets, predicted clearances, and physical MuJoCo clearances. |
| [`r4_raw_trials.json`](file:///d:/ebca/evidence/stage3_4R4/r4_raw_trials.json) | JSON | Raw trial-by-trial logs for all 20 episodes of the 10-config matched screening battery. |
| [`r4_screening_scorecard.json`](file:///d:/ebca/evidence/stage3_4R4/r4_screening_scorecard.json) | JSON | Computed screening metrics: escape rates, collision rates, delta, McNemar test, and latencies. |
| [`r4_latency.json`](file:///d:/ebca/evidence/stage3_4R4/r4_latency.json) | JSON | Statistical latency breakdown (mean, median, p95, p99, max) across deliberation cycles. |
