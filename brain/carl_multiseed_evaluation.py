"""
brain/carl_multiseed_evaluation.py — 3-Seed Multi-Run Statistical Robustness Benchmark for CARL-DX

Runs all 10 scenarios across Seeds [42, 101, 2024] (30 runs total).
Outputs summary matrix and verifies 100% pass rate.
"""

import os
import sys
import json
REPO_ROOT = r"D:\ebca"
AUDIT_DIR = os.path.join(REPO_ROOT, "audit", "overnight_20260817")
os.makedirs(AUDIT_DIR, exist_ok=True)
sys.path.insert(0, REPO_ROOT)

from brain.carl_overnight_master_suite import run_overnight_scenario

def run_multiseed_benchmark():
    scenarios = [
        ("SCENARIO_1_OPEN_SPACE_LOCOMOTION", "Scenario 1: Open Space Locomotion"),
        ("SCENARIO_2_HEAD_ON_WALL", "Scenario 2: Wall Directly Ahead"),
        ("SCENARIO_3_ANGLED_45_WALL", "Scenario 3: 45° Angled Wall"),
        ("SCENARIO_4_CORRIDOR_WITH_OPENING", "Scenario 4: Corridor with Lateral Opening"),
        ("SCENARIO_5_DEAD_END_ENCLOSURE", "Scenario 5: Dead-End U-Enclosure"),
        ("SCENARIO_6_NARROW_PASSAGE", "Scenario 6: Narrow Passage Centering"),
        ("SCENARIO_7_DYNAMIC_CROSSING_HAZARD", "Scenario 7: Dynamic Crossing Hazard"),
        ("SCENARIO_8_UNEXPECTED_DROP_HAZARD", "Scenario 8: Sudden Unexpected Drop Hazard"),
        ("SCENARIO_9_ADVERSARIAL_RANDOM_CLUTTER", "Scenario 9: Adversarial Random Clutter Field"),
        ("SCENARIO_10_CORNER_WEDGE_TRAP", "Scenario 10: Corner Wedge Trap (Stuck & Recovery)")
    ]
    
    seeds = [42, 101, 2024]
    multiseed_records = []
    
    total_runs = len(scenarios) * len(seeds)
    passed_runs = 0
    
    print("\n" + "="*95)
    print(f"      CARL-DX 30-RUN MULTI-SEED STATISTICAL BENCHMARK ({len(scenarios)} Scenarios x {len(seeds)} Seeds)")
    print("="*95 + "\n")
    
    for sc_id, sc_title in scenarios:
        for seed in seeds:
            res = run_overnight_scenario(sc_id, sc_title, max_ticks=100, seed=seed)
            multiseed_records.append(res)
            if res["overall_verdict"] == "PASS":
                passed_runs += 1
                
    multiseed_summary_path = os.path.join(AUDIT_DIR, "multiseed_30run_summary.json")
    with open(multiseed_summary_path, "w") as f:
        json.dump(multiseed_records, f, indent=2)
        
    print("\n" + "="*95)
    print(f"  MULTI-SEED SUMMARY: {passed_runs}/{total_runs} RUNS PASSED ({passed_runs/total_runs*100:.1f}%)")
    print(f"  Summary saved to: {multiseed_summary_path}")
    print("="*95 + "\n")
    
    return multiseed_records

if __name__ == "__main__":
    run_multiseed_benchmark()
