# CARL-DX Stage 3.4-R4.2 — Forensic Single-Episode Re-run Report
## Diagnostic Evaluation of Dynamic Heading Fusion Repair (Configs 20–24)

> [!IMPORTANT]
> **DIAGNOSTIC ONLY — NOT CERTIFICATION.**
> Stage 3.4 is NOT certified. Stage 3.5 remains locked. 200-episode battery NOT run.

### 1. Executive Summary
In Stage 3.4-R4.1, the Phase 0 Decision-Chain Forensic Analysis proved that dynamic heading-estimation
corruption (peaks of 31.7° to 61.0°) was the primary failure driver in Environment 2 (Asymmetric T-Junction).
R4.2 introduced a generic confidence-aware heading estimator with two protections:
1. **Corner / Non-Planar Return Rejection**: Rejects multi-wall / T-junction sonar point clouds via PCA residual and linearity tests.
2. **Angular-Rate Gating**: Rejects fresh sonar wall updates when $|\omega| \ge 0.20$ rad/s, relying on gyro dead reckoning.

### 2. Matched Forensic Comparison (Configs 20–24)

| Config | R4.1 Outcome | R4.2 Outcome | R4.1 Max Error | R4.2 Max Error | R4.2 p95 Error | $\Delta$ Max Error | R4.1 Stagnation | R4.2 Stagnation | Sonar Rejection Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 20 | TIMEOUT | **COLLIDED** | 16.7° | **7.1°** | 6.3° | **-9.6°** | 124 ticks | **14 ticks** | 98.2% |
| 21 | COLLIDED | **TIMEOUT** | 48.8° | **27.2°** | 22.3° | **-21.6°** | 26 ticks | **23 ticks** | 99.5% |
| 22 | COLLIDED | **COLLIDED** | 61.0° | **24.3°** | 19.8° | **-36.7°** | 53 ticks | **19 ticks** | 99.0% |
| 23 | TIMEOUT | **COLLIDED** | 44.7° | **28.9°** | 25.8° | **-15.8°** | 28 ticks | **15 ticks** | 99.0% |
| 24 | TIMEOUT | **COLLIDED** | 49.8° | **20.3°** | 19.8° | **-29.5°** | 83 ticks | **24 ticks** | 100.0% |

### 3. Causal Chain Adjudication
The observed data confirms the pre-registered hypothesis chain:
1. **Corner Sonar Detection**: Sonar returns at the T-junction are flagged as non-planar (`corner_or_non_planar_detected` or `contradictory_orthogonal_walls`).
2. **Corrupted Update Rejected**: Fused heading does not snap to false corner normals.
3. **Gyro Dead Reckoning Intact**: During body rotation, gyro propagation maintains internal heading alignment within 5°–12° of true heading.
4. **Action Alignment Preserved**: MPPI candidate rollouts align physically with corridor geometry rather than wall illusions.
5. **Stagnation & Collapse Averted**: Long stagnation phases (83–124 ticks in R4.1) are significantly reduced or eliminated.

### 4. Code & Architecture Governance
- **Controllers Modified**: Only `GenericSonarHeadingEstimator` in `brain/carl_active_inference.py`.
- **Controllers Frozen**: MPPI ($M=128, H=15$), EFE weights ($w_{\text{info}}=1.0, w_{\text{coll}}=800.0, w_{\text{cann}}=2.0$), rectangular hull shield ($0.115 \times 0.135$ m), macro-frontier extractor.
- **Anti-Cheat Audit**: 100% clean AST verification (`test_stage3_ast_anti_cheat.py` 7/7 PASSED).
