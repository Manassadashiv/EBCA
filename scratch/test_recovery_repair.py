"""
scratch/test_recovery_repair.py — Prototype & Validate Minimal Recovery Repair
Tests targeted failed runs under improved recovery geometry & exit conditions.
"""

import sys
import os
import numpy as np

REPO_ROOT = r"D:\ebca"
sys.path.insert(0, REPO_ROOT)

from tools.p0_regression_runner import run_single_test
from tools.p0_independent_scorer import evaluate_run_telemetry

def test_targeted_runs():
    targeted = [
        ("P0_D1_S42_HISTORICAL_TURN_TRAP_300T", "D1", "HISTORICAL_TURN_TRAP", 42, 300, True),
        ("P0_G2_S42_CORRIDOR_NARROW_250T", "G2", "CORRIDOR_NARROW", 42, 250, True),
        ("P0_K3_S42_CORRIDOR_NARROW_250T", "K3", "CORRIDOR_NARROW", 42, 250, True),
        ("P0_F2_S42_DEAD_END_300T", "F2", "DEAD_END", 42, 300, True),
        ("P0_L4_S42_DEAD_END_150T", "L4", "DEAD_END", 42, 150, True),
        ("P0_N2_S42_CORRIDOR_WIDE_900T", "N2", "CORRIDOR_WIDE", 42, 900, True),
        ("P0_N3_S42_BIFURCATION_1800T", "N3", "BIFURCATION", 42, 1800, True)
    ]
    
    print("=================================================================")
    print("   RUNNING TARGETED RECOVERY REGRESSION TESTS")
    print("=================================================================")
    
    results = []
    for run_id, grp, scen, seed, dur, rec_vid in targeted:
        print(f"\nExecuting: {run_id} ({dur} ticks)...")
        run_meta = run_single_test(run_id, grp, scen, seed, dur, record_video=rec_vid)
        csv_p = f"D:/ebca/evidence/p0_baseline_regression/telemetry/{run_id}.csv"
        score = evaluate_run_telemetry(csv_p, {
            "run_id": run_id, "test_group": grp, "scenario_type": scen, "seed": seed
        })
        print(f"  >>> RESULT: {score['pass_fail']} | Violations: {score['gate_violations']}")
        print(f"      Rec Episodes: {score['recovery_episodes_completed']} / {score['recovery_episodes_started']} | Rec Active at End: {score['is_recovery_active_at_end']} | Net Disp: {score['net_displacement_m']}m")
        results.append(score)
        
    print("\n=================================================================")
    print(f"Targeted Results: {sum(1 for r in results if r['pass_fail'] == 'PASS')} / {len(results)} PASSED")
    print("=================================================================")

if __name__ == "__main__":
    test_targeted_runs()
