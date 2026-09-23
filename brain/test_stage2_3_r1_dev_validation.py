"""
brain/test_stage2_3_r1_dev_validation.py — Development Validation for Stage 2.3-R1 Remediation
Classification: [DEV VALIDATION] Evaluates only on Development Seeds [42, 101, 202].
Held-out test seed 20260907 is strictly untouched.
"""

import sys
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
from scipy import stats

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.test_stage2_3_r1_runner import generate_layout_configs, run_single_trial, compute_cohens_d


def run_dev_validation(
    dev_seeds: List[int] = [42, 101, 202],
    trials_per_layout_per_seed: int = 15,
    max_ticks: int = 60
) -> Dict[str, Any]:
    print("=" * 70, flush=True)
    print(f"STAGE 2.3-R1 REMEDIATION: DEVELOPMENT VALIDATION (Seeds: {dev_seeds})", flush=True)
    print("=" * 70, flush=True)

    hal = CarlStage1HAL()
    layouts = [
        "layout_1_left_trap",
        "layout_2_right_trap",
        "layout_3_t_junction",
        "layout_4_corridor_slit"
    ]
    conditions = ["deliberative", "potential_field", "reflex"]

    all_spawn_configs = {lid: [] for lid in layouts}
    for s in dev_seeds:
        for lid in layouts:
            cfgs = generate_layout_configs(lid, n_trials=trials_per_layout_per_seed, seed=s)
            all_spawn_configs[lid].extend(cfgs)

    total_trials_per_cond = len(layouts) * len(dev_seeds) * trials_per_layout_per_seed
    print(f"Total trials per condition across dev seeds: {total_trials_per_cond}")

    condition_results = {}
    delib_alignments = []

    for cond in conditions:
        print(f"\n>>> Evaluating DEV Condition: [{cond.upper()}]...", flush=True)
        engine = CARLStage2_3R1DeliberationEngine(mode=cond)

        all_colls = []
        all_dists = []
        all_surv = []
        all_lats = []
        layout_metrics = {}

        for lid in layouts:
            spawns = all_spawn_configs[lid]
            trial_results = []
            for cfg in spawns:
                res = run_single_trial(
                    hal=hal,
                    engine=engine,
                    spawn_pos=cfg["pos"],
                    spawn_yaw=cfg["yaw"],
                    max_ticks=max_ticks
                )
                trial_results.append(res)
                if cond == "deliberative" and res["prediction_alignments"]:
                    delib_alignments.extend(res["prediction_alignments"])

            c_colls = [1.0 if r["collision"] else 0.0 for r in trial_results]
            c_dists = [r["distance_traversed"] for r in trial_results]
            c_surv_vals = [r["ticks_survived"] for r in trial_results]
            c_lats = [lat for r in trial_results for lat in r["latencies_ms"]]

            layout_metrics[lid] = {
                "collision_rate_percent": float(np.mean(c_colls) * 100.0),
                "mean_distance_m": float(np.mean(c_dists)),
                "mean_ticks_survived": float(np.mean(c_surv_vals))
            }
            all_colls.extend(c_colls)
            all_dists.extend(c_dists)
            all_surv.extend(c_surv_vals)
            all_lats.extend(c_lats)

            print(f"  [{lid:22s}] Collisions: {layout_metrics[lid]['collision_rate_percent']:.1f}% | "
                  f"Dist: {layout_metrics[lid]['mean_distance_m']:.2f}m | Ticks: {layout_metrics[lid]['mean_ticks_survived']:.1f}", flush=True)

        overall_coll_rate = float(np.mean(all_colls) * 100.0)
        overall_dist = float(np.mean(all_dists))
        overall_surv = float(np.mean(all_surv))
        p95_lat = float(np.percentile(all_lats, 95)) if all_lats else 0.0

        condition_results[cond] = {
            "total_trials": len(all_colls),
            "overall_collision_rate_percent": overall_coll_rate,
            "overall_mean_distance_m": overall_dist,
            "overall_mean_ticks_survived": overall_surv,
            "p95_latency_ms": p95_lat,
            "raw_collisions": all_colls,
            "raw_survivals": all_surv
        }
        print(f"  ==> TOTAL [{cond.upper()}]: Collisions: {overall_coll_rate:.1f}% | Latency p95: {p95_lat:.2f}ms", flush=True)

    # Compute key gate metrics
    delib_coll = condition_results["deliberative"]["overall_collision_rate_percent"]
    potfield_coll = condition_results["potential_field"]["overall_collision_rate_percent"]
    coll_red_vs_potfield = float((potfield_coll - delib_coll) / (potfield_coll + 1e-8) * 100.0)
    causal_align_pct = float(np.mean(delib_alignments) * 100.0) if delib_alignments else 0.0

    print("\n" + "=" * 70, flush=True)
    print("DEV VALIDATION GATES SCORECARD", flush=True)
    print("=" * 70, flush=True)
    print(f"1. Collision Reduction vs Potential Field: {coll_red_vs_potfield:.2f}% (Target: >= 25.0%) -> {'PASS' if coll_red_vs_potfield >= 25.0 else 'FAIL'}")
    print(f"2. Causal Prediction Alignment:            {causal_align_pct:.2f}% (Target: >= 85.0%) -> {'PASS' if causal_align_pct >= 85.0 else 'FAIL'}")
    print(f"3. Deliberative p95 Latency:               {condition_results['deliberative']['p95_latency_ms']:.2f}ms (Target: <= 50.0ms) -> {'PASS' if condition_results['deliberative']['p95_latency_ms'] <= 50.0 else 'FAIL'}")
    print("=" * 70, flush=True)

    dev_passed = (coll_red_vs_potfield >= 25.0) and (causal_align_pct >= 85.0) and (condition_results['deliberative']['p95_latency_ms'] <= 50.0)
    return {
        "dev_passed": dev_passed,
        "coll_red_vs_potfield": coll_red_vs_potfield,
        "causal_align_pct": causal_align_pct,
        "condition_results": condition_results
    }


if __name__ == "__main__":
    run_dev_validation()
