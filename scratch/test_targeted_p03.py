import os, sys, json, pandas as pd
sys.path.insert(0, '.')
from tools.p0_regression_runner import run_single_test
from tools.p0_independent_scorer import evaluate_run_telemetry

targeted_configs = [
    {'run_id': 'P0_G2_S42_CORRIDOR_NARROW_250T', 'scenario': 'CORRIDOR_NARROW', 'seed': 42, 'ticks': 250},
    {'run_id': 'P0_K3_S42_CORRIDOR_NARROW_250T', 'scenario': 'CORRIDOR_NARROW', 'seed': 42, 'ticks': 250},
    {'run_id': 'P0_D1_S42_HISTORICAL_TURN_TRAP_300T', 'scenario': 'HISTORICAL_TURN_TRAP', 'seed': 42, 'ticks': 300},
    {'run_id': 'P0_F2_S42_DEAD_END_300T', 'scenario': 'DEAD_END', 'seed': 42, 'ticks': 300},
    {'run_id': 'P0_L4_S42_DEAD_END_150T', 'scenario': 'DEAD_END', 'seed': 42, 'ticks': 150}
]

results = []
for cfg in targeted_configs:
    rid = cfg['run_id']
    print(f">>> Executing {rid}...")
    run_res = run_single_test(
        rid, 'TARGETED', cfg['scenario'], cfg['seed'], cfg['ticks'], record_video=True
    )
    score_res = evaluate_run_telemetry(run_res['csv_path'], run_res)
    status = score_res['pass_fail']
    disp = run_res['net_displacement_m']
    viols = score_res['gate_violations']
    results.append({
        'run_id': rid,
        'status': status,
        'disp': disp,
        'violations': viols
    })
    print(f"[{status}] {rid} -> Disp: {disp}m, Violations: {viols}")

print("\n=== TARGETED SCORECARD ===")
print(pd.DataFrame(results).to_string(index=False))

with open('evidence/p0_baseline_regression/audit/P0_03_TARGETED_RESULTS.json', 'w') as f:
    json.dump(results, f, indent=2)
