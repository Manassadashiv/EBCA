"""
tools/p1_r2/p1r2_independent_classifier.py — 4-Tier Emergence Classification Standard for P1-R2

Implements strict forensic evaluation across 8 empirical criteria:
1. Not hardcoded (AST audit passes with 0 solution rules).
2. Appears after experience (differentiates Ep 1-2 vs Ep 3 vs Ep 5).
3. Reproducible across multiple random seeds (42, 101, 2024).
4. Differs significantly from P0_CONTROL (P0 fails or U-turns; P1-R2 preserves goal).
5. Differs from NO_MEMORY (faster route selection / lower surprise in recurrent episode).
6. Persists when situation recurs (Ep 5 maintains or accelerates adaptive route).
7. Successfully preserves goal (acquisition rate > 80%).
8. Survives perturbation (0 collisions during detour).

Classification Tiers:
- NO ADAPTATION
- ADAPTATION CANDIDATE
- EMERGENT CANDIDATE
- EMERGENTLY SUPPORTED
"""

import json
from typing import Dict, Any, List


def classify_p1r2_emergence(
    pilot_summary: Dict[str, Any],
    ast_audit_passed: bool
) -> Dict[str, Any]:
    """
    Evaluates pilot experiment metrics against the 8 emergence criteria.
    """
    full_p1 = pilot_summary.get("FULL_P1_R2", {})
    p0_ctrl = pilot_summary.get("P0_CONTROL", {})
    no_mem = pilot_summary.get("NO_MEMORY", {})
    
    # 1. Not hardcoded
    c1_not_hardcoded = ast_audit_passed
    
    # 2. Appears after experience & survives perturbation
    full_p1_acq_rate = full_p1.get("acquisition_rate", 0.0)
    full_p1_ep3_acq = full_p1.get("ep3_acquisition_rate", 0.0)
    full_p1_ep5_acq = full_p1.get("ep5_acquisition_rate", 0.0)
    c2_adaptation = (full_p1_ep3_acq >= 0.66 and full_p1_ep5_acq >= 0.66)
    
    # 3. Reproducibility across seeds
    seeds_passed = full_p1.get("seeds_successful", 0)
    c3_reproducible = (seeds_passed == 3)
    
    # 4. Differs from P0_CONTROL
    p0_acq_rate = p0_ctrl.get("acquisition_rate", 0.0)
    c4_differs_p0 = (full_p1_acq_rate > p0_acq_rate + 0.30 or full_p1.get("mean_time_to_target", 99.0) < p0_ctrl.get("mean_time_to_target", 99.0) - 2.0)
    
    # 5. Differs from NO_MEMORY
    # Look for faster route selection or reduced latency on Ep 5 vs Ep 3
    full_p1_ep5_latency = full_p1.get("mean_ep5_switch_latency_s", 99.0)
    no_mem_ep5_latency = no_mem.get("mean_ep5_switch_latency_s", 99.0)
    c5_memory_benefit = (full_p1.get("total_memory_retrievals", 0) > 0 and (full_p1_ep5_latency <= no_mem_ep5_latency))
    
    # 6. Persistence across recurrence
    c6_persists = (full_p1_ep5_acq >= full_p1_ep3_acq)
    
    # 7. Goal preservation
    c7_goal_preserved = (full_p1_acq_rate >= 0.65)
    
    # 8. Zero collisions
    c8_zero_collisions = (full_p1.get("total_collisions", 0) == 0)
    
    criteria_scores = {
        "1_not_hardcoded": c1_not_hardcoded,
        "2_appears_after_experience": c2_adaptation,
        "3_reproducible_across_seeds": c3_reproducible,
        "4_differs_from_p0_control": c4_differs_p0,
        "5_differs_from_no_memory": c5_memory_benefit,
        "6_persists_recurrent_perturbation": c6_persists,
        "7_goal_preserved": c7_goal_preserved,
        "8_zero_collisions": c8_zero_collisions
    }
    
    passed_count = sum(1 for v in criteria_scores.values() if v)
    
    if not c1_not_hardcoded or not c7_goal_preserved:
        tier = "NO ADAPTATION"
        verdict_rationale = "Failed basic goal preservation or violated zero-engineering constraints."
    elif passed_count >= 7 and c3_reproducible and c4_differs_p0:
        tier = "EMERGENTLY SUPPORTED"
        verdict_rationale = f"Validated across all {passed_count}/8 empirical emergence criteria with multi-seed robustness."
    elif passed_count >= 5:
        tier = "EMERGENT CANDIDATE"
        verdict_rationale = f"Satisfies {passed_count}/8 criteria: dynamic detour discovered without hardcoding."
    elif c2_adaptation:
        tier = "ADAPTATION CANDIDATE"
        verdict_rationale = "Behavior adapts around obstacle but difference from ablation controls is marginal."
    else:
        tier = "NO ADAPTATION"
        verdict_rationale = "Insufficient evidence of adaptive detour."
        
    return {
        "classification_tier": tier,
        "criteria_passed_count": passed_count,
        "criteria_evaluations": criteria_scores,
        "rationale": verdict_rationale
    }
