# CARL-DX Phase 1-R5: Final Bounded Verification & Exit Gate Report

**Date**: August 26, 2026  
**Final Decision**: **`PARTIAL PASS — SYNAPTIC PLASTICITY VERIFIED, BEHAVIOURAL CAUSALITY NOT DEMONSTRATED`**  
**Milestone Status**: **`FROZEN`**

---

## 1. Executive Summary

A clean, bounded repair and validation cycle was executed to address the measurement and reporting defects identified during the forensic audit of Phase 1-R5. 

Using **strict geometric corridor boundaries** ($\text{North: } y > +0.25\text{m}, \text{ South: } y < -0.25\text{m}, \text{ Center: } |y| \le 0.25\text{m}$), 96 physical simulation episodes were evaluated across 4 matched conditions (`STDP_ACTIVE`, `NO_STDP`, `SHUFFLED_STDP`, `STDP_ABLATION`) and 3 seeds (42, 101, 2024).

### Key Scientific Findings:
1. **Synaptic Plasticity Verified**: Three-Factor STDP is functionally active and changes synaptic matrix $W$ ($\|W\| = 0.0010$, 224 LTD events across 8 episodes).
2. **Sub-Threshold Behavioural Effect**: Isolated STDP updates produce an EFE shift of $\Delta \text{EFE}_{\text{stdp}} \approx 0.05\text{ units}$, which is sub-threshold to overcome baseline Active Inference kinematic preferences.
3. **Geometric Outcome**: All 4 conditions follow the exact same centerline trajectory (`CENTER_UNCOMMITTED`, 100%).
4. **Previous Artifact Resolved**: The earlier reported "100% vs 0% Detour Switch" was caused by a simplistic sign test (`py > 0.00`) operating on straight centerline motion ($y \approx 0.000003\text{m}$).

---

## 2. Causal Criteria Evaluation (C1–C10)

| Criterion | Description | Status |
| :--- | :--- | :---: |
| **C1. Initial Baseline** | Zero pre-existing STDP weight bias ($\|W\| = 0.0$ at $t=0$) | **PASS** |
| **C2. Geometric Validity** | Route classified by physical corridor occupancy ($|y| > 0.25\text{m}$) | **PASS** |
| **C3. Hazard Event** | Hazard interaction timestamped with physical stall/contact | **PASS** |
| **C4. Learning Attribution** | Attributable STDP updates separated from transients | **PASS** |
| **C5. Temporal Precedence** | Experience $\to$ STDP update $\to$ persistent state change | **PASS** |
| **C6. Physical Policy Effect** | Learned state causes measurable physical trajectory divergence | **FAIL** |
| **C7. Counterfactual Control** | `NO_STDP` differs in physical route from `STDP_ACTIVE` | **FAIL** |
| **C8. Temporal-Structure Control** | `SHUFFLED_STDP` breaks route adaptation | **FAIL** |
| **C9. Ablation** | `STDP_ABLATION` abolishes route adaptation | **FAIL** |
| **C10. Replication** | Evaluated consistently across Seeds 42, 101, 2024 | **PASS** |

---

## 3. Milestone Freeze Declaration

**P1-04 / P1-R5 is officially FROZEN.**  
No further iterations, parameter fishing, or scope expansions will be performed on this milestone. The project is ready to proceed to the next planned Phase-1 milestone (integrating spatio-temporal reservoir dynamics / LSM to bridge synaptic plasticity with macro-scale behavioural policy shifts).
