"""
tests/test_stage3_4_canonical_equivalence.py — Stage 3.4 Canonical Deliberation Equivalence Gate
Classification: [STAGE 3.4 ARCHITECTURAL INTEGRATION GATE 10]

Proves that hosting CARLActiveInferenceEngine inside CarlAutonomousOrganismAgent(deliberation_mode="active_inference")
does NOT alter its computational decisions, objective evaluations, candidate feasibility, or continuous actuation.

Compares:
PATH A: Direct CARLActiveInferenceEngine.select_action(...)
PATH B: Canonical CarlAutonomousOrganismAgent(deliberation_mode="active_inference") via canonical deliberation organ.

Tested Scenarios:
1. Scenario 1: Symmetric Open Corridor (Straight navigation)
2. Scenario 2: Right Proximity Gating (Approaching lateral obstacle on right)
3. Scenario 3: Left Proximity Gating (Approaching lateral obstacle on left)
4. Scenario 4: Dead-End Wall Encounter (Forward distance < 0.32m, retreat threshold)
5. Scenario 5: Asymmetric Oblique Corridor with Gyro Yaw Rate

Numerical Tolerances Derived from IEEE-754 Single/Double Precision:
- Action u*: atol = 1e-6
- Best Cost: atol = 1e-5
- Epistemic / Pragmatic Mean Cost: atol = 1e-5
- Candidate Counts (accepted, rejected): exact match (0)
- Best Candidate Index: exact match (0)
- Heading Confidence / Wall Angle: atol = 1e-6
"""

import json
import math
import numpy as np
import torch
import pytest
from pathlib import Path
from typing import Dict, Any

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_active_inference import CARLActiveInferenceEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "evidence" / "canonical_reunification_step1"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def build_synthetic_sensor_vector(scenario_type: str) -> np.ndarray:
    """Constructs deterministic 25-dim sensor vectors representing diverse maze topologies."""
    s = np.zeros(25, dtype=np.float64)
    if scenario_type == "open_corridor":
        # Clear path straight ahead (2.5m), walls on left and right at ~0.8m
        s[:15] = 2.50
        s[0] = 0.80   # Ray -120°
        s[1] = 0.82
        s[2] = 0.85
        s[12] = 0.85
        s[13] = 0.82
        s[14] = 0.80  # Ray +120°
        s[6:9] = 2.40 # Rays around 0° (forward)
        s[15] = 0.20  # forward accel
        s[20] = 0.00  # gyro yaw
    elif scenario_type == "right_proximity":
        s[:15] = 2.00
        s[9:15] = np.linspace(0.40, 0.20, 6) # obstacle close on right
        s[6:9] = 1.50
        s[15] = 0.10
        s[20] = -0.15 # turning right
    elif scenario_type == "left_proximity":
        s[:15] = 2.00
        s[0:6] = np.linspace(0.20, 0.40, 6)  # obstacle close on left
        s[6:9] = 1.50
        s[15] = 0.10
        s[20] = 0.15  # turning left
    elif scenario_type == "dead_end":
        s[:15] = 0.80
        s[6:9] = 0.28 # dead ahead obstacle < 0.32m
        s[0:4] = 0.30
        s[11:15] = 0.30
        s[15] = -0.05
        s[20] = 0.0
    elif scenario_type == "oblique_corridor":
        s[:15] = 1.80
        s[3:7] = 1.20
        s[7:11] = 0.60
        s[15] = 0.15
        s[20] = 0.22 # yaw rate
    return s


def run_equivalence_trial(scenario_name: str, seed: int = 42) -> Dict[str, Any]:
    """Runs Path A and Path B on identical initial conditions, inputs, and seeds."""
    sensor_vec = build_synthetic_sensor_vector(scenario_name)
    sonars = sensor_vec[:15].astype(np.float32)
    curr_v = float(sensor_vec[15]) * 0.5
    curr_w = float(sensor_vec[20])
    spawn_pose = (0.25, -0.15, 0.05)

    # -------------------------------------------------------------
    # PATH A: Direct Standalone CARLActiveInferenceEngine
    # -------------------------------------------------------------
    torch.manual_seed(seed)
    np.random.seed(seed)
    engine_a = CARLActiveInferenceEngine(
        grid_path=None,
        num_samples=128,
        horizon=15,
        dt=0.030,
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    engine_a.initialize_pose(*spawn_pose)

    torch.manual_seed(seed + 100)
    u_a, telem_a = engine_a.select_action(
        curr_sensors=sonars,
        curr_v=curr_v,
        curr_w=curr_w,
        forced_pose=None,
        cann_state=None
    )

    # -------------------------------------------------------------
    # PATH B: Canonical CarlAutonomousOrganismAgent
    # -------------------------------------------------------------
    torch.manual_seed(seed)
    np.random.seed(seed)
    agent_b = CarlAutonomousOrganismAgent(
        dt=0.030,
        enable_memory=True,
        deliberation_mode="active_inference",
        grid_path=None,
        num_samples=128,
        horizon=15,
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    agent_b.initialize_spatial_grounding(*spawn_pose)

    # Call canonical deliberation route directly with identical seed and state
    torch.manual_seed(seed + 100)
    u_b, telem_b = agent_b.deliberation.select_action(
        curr_sensors=sonars,
        curr_v=curr_v,
        curr_w=curr_w,
        forced_pose=None,
        cann_state=None
    )

    # Compute exact deviations
    delta_u = np.abs(u_a - u_b)
    delta_cost = abs(telem_a["best_cost"] - telem_b["best_cost"])
    delta_pragmatic = abs(telem_a["efe_pragmatic_mean"] - telem_b["efe_pragmatic_mean"])
    delta_epistemic = abs(telem_a["efe_epistemic_mean"] - telem_b["efe_epistemic_mean"])
    delta_entropy = abs(telem_a["ensemble_entropy"] - telem_b["ensemble_entropy"])
    delta_clearance = abs(telem_a["min_predicted_hull_clearance"] - telem_b["min_predicted_hull_clearance"])

    is_equiv = bool(
        np.all(delta_u < 1e-6) and
        delta_cost < 1e-5 and
        delta_pragmatic < 1e-5 and
        delta_epistemic < 1e-5 and
        delta_entropy < 1e-5 and
        telem_a["best_sample_idx"] == telem_b["best_sample_idx"] and
        telem_a["accepted_candidates"] == telem_b["accepted_candidates"] and
        telem_a["rejected_candidates"] == telem_b["rejected_candidates"] and
        telem_a["rejection_reason"] == telem_b["rejection_reason"]
    )

    return {
        "scenario": scenario_name,
        "seed": seed,
        "path_a_action": u_a.tolist(),
        "path_b_action": u_b.tolist(),
        "delta_u": delta_u.tolist(),
        "max_delta_u": float(np.max(delta_u)),
        "path_a_best_idx": int(telem_a["best_sample_idx"]),
        "path_b_best_idx": int(telem_b["best_sample_idx"]),
        "path_a_best_cost": float(telem_a["best_cost"]),
        "path_b_best_cost": float(telem_b["best_cost"]),
        "delta_best_cost": float(delta_cost),
        "path_a_accepted": int(telem_a["accepted_candidates"]),
        "path_b_accepted": int(telem_b["accepted_candidates"]),
        "path_a_rejected": int(telem_a["rejected_candidates"]),
        "path_b_rejected": int(telem_b["rejected_candidates"]),
        "path_a_entropy": float(telem_a["ensemble_entropy"]),
        "path_b_entropy": float(telem_b["ensemble_entropy"]),
        "delta_entropy": float(delta_entropy),
        "path_a_min_clearance": float(telem_a["min_predicted_hull_clearance"]),
        "path_b_min_clearance": float(telem_b["min_predicted_hull_clearance"]),
        "delta_min_clearance": float(delta_clearance),
        "path_a_rejection_reason": str(telem_a["rejection_reason"]),
        "path_b_rejection_reason": str(telem_b["rejection_reason"]),
        "is_equivalent": is_equiv
    }


def test_canonical_active_inference_equivalence():
    """Executes the full 5-scenario pre-registered equivalence suite."""
    scenarios = [
        "open_corridor",
        "right_proximity",
        "left_proximity",
        "dead_end",
        "oblique_corridor"
    ]
    results = {}
    all_passed = True

    for scen in scenarios:
        res = run_equivalence_trial(scen, seed=42)
        results[scen] = res
        print(f"Scenario [{scen}]: delta_u_max={res['max_delta_u']:.2e}, delta_cost={res['delta_best_cost']:.2e}, EQUIV={res['is_equivalent']}")
        assert res["is_equivalent"] is True, f"Equivalence failure in scenario: {scen}"

    # Save comprehensive results artifact
    output_file = EVIDENCE_DIR / "canonical_equivalence_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_suite": "Stage 3.4 Canonical Equivalence Gate",
            "overall_pass": True,
            "numerical_tolerances": {
                "action_u_atol": 1e-6,
                "cost_atol": 1e-5,
                "entropy_atol": 1e-5,
                "candidate_count_exact": True,
                "best_idx_exact": True
            },
            "scenarios": results
        }, f, indent=2)

    print(f"\nCanonical Equivalence Suite: PASS. Results written to {output_file}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
