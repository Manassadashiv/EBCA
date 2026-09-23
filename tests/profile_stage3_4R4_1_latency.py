"""
tests/profile_stage3_4R4_1_latency.py — Part 5 Comprehensive Latency Profiler
Instruments >= 1000 continuous planning cycles across separate stages:
- sensor_preprocessing
- occupancy_update
- frontier_extraction
- candidate_sampling
- trajectory_propagation
- hull_feasibility
- efe_cost_calculation
- softmax_action_synthesis
- telemetry_logging
- total_cycle_time

Computes mean, p50, p95, p99, max, std, top 10 slowest cycles, and per-stage timing contributions.
Saves to evidence/stage3_4R4_1/latency_profile.json.
"""

import sys
import time
import json
import math
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import torch
import torch.nn.functional as F

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_stage1_hal import CarlStage1HAL

OUT_DIR = repo_root / "evidence" / "stage3_4R4_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENV1_XML = repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"
ENV1_GRID = repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
ENV2_GRID = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"


def profile_latency(num_cycles: int = 1000) -> Dict[str, Any]:
    print(f"Profiling deliberation latency over {num_cycles} continuous cycles across environments...")
    
    stage_names = [
        "sensor_preprocessing",
        "occupancy_update",
        "frontier_extraction",
        "candidate_sampling",
        "trajectory_propagation",
        "hull_feasibility",
        "efe_cost_calculation",
        "softmax_action_synthesis",
        "telemetry_logging",
        "total_cycle_time"
    ]
    timings = {s: [] for s in stage_names}
    cycle_records = []

    # Two realistic scenarios: Env 1 (turning bay) and Env 2 (asymmetric T-junction)
    scenarios = [
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "spawn": [0.50, 0.00, 0.0]},
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "spawn": [0.00, 0.00, 0.0]},
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "spawn": [0.80, 0.00, 0.0]},
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "spawn": [0.60, 0.40, math.pi/2]},
    ]

    cycles_completed = 0
    ep = 0

    while cycles_completed < num_cycles:
        scen = scenarios[ep % len(scenarios)]
        ep += 1

        hal = CarlStage1HAL(xml_path=str(scen["xml"]))
        ctrl = CARLActiveInferenceEngine(grid_path=str(scen["grid"]))
        sx, sy, syaw = scen["spawn"]
        ctrl.initialize_pose(sx, sy, syaw)

        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
        import mujoco
        mujoco.mj_forward(hal.model, hal.data)

        # Run up to 60 steps per episode
        for step in range(60):
            if cycles_completed >= num_cycles:
                break

            curr_sensors = hal.read_sensors()

            # Profile true unified deliberation cycle
            u_star, telemetry = ctrl.select_action(curr_sensors)
            st = telemetry["stage_timings"]

            # Record in history
            for s in stage_names:
                timings[s].append(st[s])

            cycle_records.append({
                "cycle": cycles_completed,
                "total_ms": round(st["total_cycle_time"], 2),
                "frontier_ms": round(st["frontier_extraction"], 2),
                "hull_ms": round(st["hull_feasibility"], 2),
                "efe_ms": round(st["efe_cost_calculation"], 2),
                "sample_ms": round(st["candidate_sampling"], 2),
                "rollout_ms": round(st["trajectory_propagation"], 2),
            })

            cycles_completed += 1

            # Step environment
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(u_star[0])
            cmd_6d[1] = float(u_star[1])
            hal.step(cmd_6d)

    # Summary statistics
    total_arr = np.array(timings["total_cycle_time"])
    mean_lat = float(np.mean(total_arr))
    p50_lat = float(np.percentile(total_arr, 50))
    p95_lat = float(np.percentile(total_arr, 95))
    p99_lat = float(np.percentile(total_arr, 99))
    max_lat = float(np.max(total_arr))
    std_lat = float(np.std(total_arr))

    slowest_10 = sorted(cycle_records, key=lambda x: x["total_ms"], reverse=True)[:10]

    per_stage = {}
    for s in stage_names:
        s_arr = np.array(timings[s])
        per_stage[s] = {
            "mean_ms": round(float(np.mean(s_arr)), 3),
            "p50_ms": round(float(np.percentile(s_arr, 50)), 3),
            "p95_ms": round(float(np.percentile(s_arr, 95)), 3),
            "p99_ms": round(float(np.percentile(s_arr, 99)), 3),
            "max_ms": round(float(np.max(s_arr)), 3),
            "percent_of_total": round(float(np.mean(s_arr) / mean_lat * 100.0), 2)
        }

    report = {
        "num_cycles_profiled": cycles_completed,
        "mppi_candidates_M": ctrl.M,
        "horizon_H": ctrl.horizon,
        "total_cycle_statistics_ms": {
            "mean": round(mean_lat, 2),
            "p50": round(p50_lat, 2),
            "p95": round(p95_lat, 2),
            "p99": round(p99_lat, 2),
            "max": round(max_lat, 2),
            "std": round(std_lat, 2)
        },
        "target_comparison": {
            "mean_goal_ms": 20.0,
            "p95_goal_ms": 45.0,
            "mean_passed": mean_lat <= 20.0,
            "p95_passed": p95_lat <= 45.0,
            "status": "PASS" if (mean_lat <= 20.0 and p95_lat <= 45.0) else "FAIL"
        },
        "per_stage_breakdown": per_stage,
        "top_10_slowest_cycles": slowest_10
    }

    out_file = OUT_DIR / "latency_profile.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=== LATENCY PROFILING RESULTS (1000 CYCLES) ===")
    print(f"Mean: {report['total_cycle_statistics_ms']['mean']} ms (Target <= 20.0 ms)")
    print(f"p50:  {report['total_cycle_statistics_ms']['p50']} ms")
    print(f"p95:  {report['total_cycle_statistics_ms']['p95']} ms (Target <= 45.0 ms)")
    print(f"p99:  {report['total_cycle_statistics_ms']['p99']} ms")
    print(f"Max:  {report['total_cycle_statistics_ms']['max']} ms")
    print(f"Status: {report['target_comparison']['status']}")
    print(f"Saved profile to {out_file}\n")

    return report


if __name__ == "__main__":
    profile_latency(1000)
