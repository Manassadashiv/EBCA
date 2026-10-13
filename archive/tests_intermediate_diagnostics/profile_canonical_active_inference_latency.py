"""
tests/profile_canonical_active_inference_latency.py — Stage 3.4 Canonical Latency Profile
Classification: [STAGE 3.4 ARCHITECTURAL INTEGRATION GATE 13]

Measures N=1000 consecutive closed-loop cycles of the canonical organism:
    CarlAutonomousOrganismAgent(deliberation_mode="active_inference")
under active HAL sensor ingestion, proprioception, interoception/homeostasis,
CANN attractor integration, spatial memory odometry, Active Inference receding-horizon
trajectory synthesis, action vetoing, and embodied actuation.

Evaluates against Stage 3.4 Gate 4:
- mean latency <= 20.0 ms
- p95 latency <= 45.0 ms
"""

import time
import json
import sys
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

EVIDENCE_DIR = REPO_ROOT / "evidence" / "canonical_reunification_step1"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def profile_canonical_latency(num_cycles: int = 1000, warmup_cycles: int = 15):
    print(f"Initializing CarlStage1HAL and CarlAutonomousOrganismAgent(deliberation_mode='active_inference')...")
    hal = CarlStage1HAL(headless=True)
    agent = CarlAutonomousOrganismAgent(
        dt=hal.dt,
        enable_memory=True,
        deliberation_mode="active_inference",
        grid_path=None,
        num_samples=128,
        horizon=15,
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    agent.initialize_spatial_grounding(0.0, 0.0, 0.0)

    print(f"Running {warmup_cycles} warmup cycles...")
    for _ in range(warmup_cycles):
        agent.step_cognitive_cycle(hal)

    print(f"Profiling {num_cycles} consecutive full canonical cognitive cycles...")
    latencies = []
    delib_latencies = []

    for i in range(num_cycles):
        t0 = time.perf_counter()
        res = agent.step_cognitive_cycle(hal)
        t_cycle_ms = (time.perf_counter() - t0) * 1000.0

        latencies.append(t_cycle_ms)
        delib_lat = res.get("delib_telemetry", {}).get("latency_ms", t_cycle_ms)
        delib_latencies.append(delib_lat)

        if (i + 1) % 200 == 0:
            cur_mean = np.mean(latencies)
            cur_p95 = np.percentile(latencies, 95)
            print(f"  Cycle {i+1}/{num_cycles}: running mean={cur_mean:.2f} ms, p95={cur_p95:.2f} ms")

    latencies_arr = np.array(latencies)
    delib_arr = np.array(delib_latencies)

    mean_lat = float(np.mean(latencies_arr))
    p50_lat = float(np.percentile(latencies_arr, 50))
    p95_lat = float(np.percentile(latencies_arr, 95))
    p99_lat = float(np.percentile(latencies_arr, 99))
    max_lat = float(np.max(latencies_arr))
    min_lat = float(np.min(latencies_arr))

    mean_delib = float(np.mean(delib_arr))
    p95_delib = float(np.percentile(delib_arr, 95))

    gate4_passed = bool(mean_lat <= 20.0 and p95_lat <= 45.0)

    results = {
        "benchmark": "Stage 3.4 Canonical Active Inference Cognitive Cycle Latency Profile",
        "num_cycles": num_cycles,
        "warmup_cycles": warmup_cycles,
        "canonical_full_cycle": {
            "mean_ms": round(mean_lat, 3),
            "p50_ms": round(p50_lat, 3),
            "p95_ms": round(p95_lat, 3),
            "p99_ms": round(p99_lat, 3),
            "max_ms": round(max_lat, 3),
            "min_ms": round(min_lat, 3)
        },
        "deliberation_only": {
            "mean_ms": round(mean_delib, 3),
            "p95_ms": round(p95_delib, 3)
        },
        "formal_gate_4_thresholds": {
            "mean_budget_ms": 20.0,
            "p95_budget_ms": 45.0,
            "gate4_passed": gate4_passed
        },
        "comparison_against_standalone_r4_2": {
            "r4_2_standalone_mean_ms": 1.76,
            "r4_2_standalone_p95_ms": 2.21,
            "canonical_organism_overhead_ms": round(mean_lat - mean_delib, 3)
        }
    }

    out_file = EVIDENCE_DIR / "latency_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"CANONICAL COGNITIVE CYCLE LATENCY RESULTS (N={num_cycles})")
    print("=" * 60)
    print(f"  Mean Latency: {mean_lat:.2f} ms (Budget <= 20.0 ms) -> {'PASS' if mean_lat <= 20.0 else 'FAIL'}")
    print(f"  p50  Latency: {p50_lat:.2f} ms")
    print(f"  p95  Latency: {p95_lat:.2f} ms (Budget <= 45.0 ms) -> {'PASS' if p95_lat <= 45.0 else 'FAIL'}")
    print(f"  p99  Latency: {p99_lat:.2f} ms")
    print(f"  Max  Latency: {max_lat:.2f} ms")
    print(f"  Deliberation Only Mean: {mean_delib:.2f} ms, p95: {p95_delib:.2f} ms")
    print(f"  Organism Overhead: {mean_lat - mean_delib:.2f} ms")
    print(f"  Formal Gate 4 Status: {'PASS' if gate4_passed else 'FAIL'}")
    print(f"  Artifact saved to: {out_file}")
    print("=" * 60)

    assert gate4_passed, f"Formal Gate 4 Latency Failure: mean={mean_lat:.2f}ms, p95={p95_lat:.2f}ms"


if __name__ == "__main__":
    profile_canonical_latency(num_cycles=1000)
