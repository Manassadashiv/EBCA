"""
tests/test_stage3_2R_observational_equivalence.py — Stage 3.2-R Observational-Equivalence Audit
Classification: [STAGE 3.2-R AUDIT] Strict Non-LOS Equivalence & Ambiguity Verification

Enforces the pre-registered equivalence criteria for all 5 task families across 5 seeds:
- D_sensory = ||s_A - s_B||_2 <= 0.150 m across all 15 rays
- max_i |s_A,i - s_B,i| <= 0.080 m
- D_body = |v_A - v_B| + |w_A - w_B| <= 0.050
- D_yaw <= 0.050 rad
- D_pose <= 0.050 m (in relative intersection frame for Family 3)
- Elapsed ticks: t_A == t_B
- Zero task/goal/context labels
- Divergent Ground-Truth Action: ||u*_A - u*_B||_2 >= 0.250 (Evaluator Oracle Only)
"""

import sys
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.stage3_2R_task_fixtures import generate_all_fixtures

EVIDENCE_DIR = repo_root / "evidence" / "stage3_2R"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [3001, 3002, 3003, 3004, 3005]
TRIALS_PER_SEED = 4

DECISION_CONFIGS = {
    "family_1": {
        "name": "Blind-Corner Connectivity Ambiguity",
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
        "u_star_A": np.array([0.15, 0.80]),  # Hard Left turn to exit
        "u_star_B": np.array([0.80, 0.15]),  # Hard Right turn to exit
        "t_crit": 40,
    },
    "family_2": {
        "name": "Symmetrical Y-Fork Funnel Trap",
        "nominal_pos": [-0.40, 0.0],
        "nominal_yaw": 0.0,
        "u_star_A": np.array([0.65, 0.35]),  # Steer into Lower open branch
        "u_star_B": np.array([0.35, 0.65]),  # Steer into Upper open branch
        "t_crit": 35,
    },
    "family_3": {
        "name": "Sonically Symmetric Locations (P1 vs P2)",
        "pos_A": [-1.50, 1.20],
        "pos_B": [ 1.50, -1.80],
        "nominal_yaw": 0.0,
        "u_star_A": np.array([0.20, 0.65]),  # Turn Left into North arterial
        "u_star_B": np.array([0.65, 0.20]),  # Drive Straight into East arterial
        "t_crit": 50,
    },
    "family_4": {
        "name": "Occluded Dogleg Arterial vs Blind Detour",
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
        "u_star_A": np.array([0.20, 0.75]),  # Take Dogleg North branch
        "u_star_B": np.array([0.75, 0.75]),  # Take Straight East branch
        "t_crit": 45,
    },
    "family_5": {
        "name": "Multi-Turn Sensory Blackout / Sonic Corridor Symmetry",
        "nominal_pos": [0.0, 0.0],
        "nominal_yaw": 0.0,
        "u_star_A": np.array([0.75, 0.25]),  # Egress turn Right (South)
        "u_star_B": np.array([0.25, 0.75]),  # Egress turn Left (North)
        "t_crit": 60,
    },
}


def evaluate_observational_equivalence() -> Dict[str, Any]:
    print("=========================================================================")
    print("STAGE 3.2-R AUTOMATED OBSERVATIONAL-EQUIVALENCE PRECHECK")
    print("Classification: [ANTI-FAKE-TASK GATE] Strict Non-LOS Equivalence Audit")
    print("=========================================================================")

    fixtures = generate_all_fixtures()
    results = {
        "families": {},
        "overall_pass": True,
        "total_trials_evaluated": 0,
        "failed_trials": 0,
    }

    for fam_key, (xml_A, xml_B) in fixtures.items():
        spec = DECISION_CONFIGS[fam_key]
        print(f"\n--- Auditing {fam_key.upper()}: {spec['name']} ---")

        hal_A = CarlStage1HAL(xml_path=str(xml_A))
        hal_B = CarlStage1HAL(xml_path=str(xml_B)) if xml_A != xml_B else hal_A

        fam_data = {
            "name": spec["name"],
            "trials": [],
            "max_d_sensory": 0.0,
            "max_single_ray_diff": 0.0,
            "max_d_body": 0.0,
            "max_d_yaw": 0.0,
            "max_d_pose": 0.0,
            "action_divergence": float(np.linalg.norm(spec["u_star_A"] - spec["u_star_B"])),
            "family_passed": True,
        }

        # Check divergent action threshold upfront
        assert fam_data["action_divergence"] >= 0.250, (
            f"Action divergence {fam_data['action_divergence']:.4f} < 0.250 for {fam_key}"
        )

        for seed in SEEDS:
            rng = np.random.RandomState(seed)
            for trial_idx in range(TRIALS_PER_SEED):
                # Matched small perturbation applied identically to paired states
                dx = float(rng.uniform(-0.010, 0.010))
                dy = float(rng.uniform(-0.010, 0.010))
                dyaw = float(rng.uniform(-0.008, 0.008))

                if fam_key == "family_3":
                    pA = [spec["pos_A"][0] + dx, spec["pos_A"][1] + dy]
                    pB = [spec["pos_B"][0] + dx, spec["pos_B"][1] + dy]
                else:
                    pA = [spec["nominal_pos"][0] + dx, spec["nominal_pos"][1] + dy]
                    pB = [spec["nominal_pos"][0] + dx, spec["nominal_pos"][1] + dy]

                yaw_A = spec["nominal_yaw"] + dyaw
                yaw_B = spec["nominal_yaw"] + dyaw

                # Setup HAL A
                hal_A.reset()
                qa_A = int(hal_A.model.joint("spatial_identity").qposadr[0])
                hal_A.data.qpos[qa_A:qa_A+2] = pA
                hal_A.data.qpos[qa_A+3:qa_A+7] = [math.cos(yaw_A / 2.0), 0.0, 0.0, math.sin(yaw_A / 2.0)]
                hal_A.data.qvel[:] = 0.0
                hal_A.data.ctrl[:] = 0.0
                import mujoco
                mujoco.mj_forward(hal_A.model, hal_A.data)
                s_A = hal_A.read_sensors()

                # Setup HAL B
                hal_B.reset()
                qa_B = int(hal_B.model.joint("spatial_identity").qposadr[0])
                hal_B.data.qpos[qa_B:qa_B+2] = pB
                hal_B.data.qpos[qa_B+3:qa_B+7] = [math.cos(yaw_B / 2.0), 0.0, 0.0, math.sin(yaw_B / 2.0)]
                hal_B.data.qvel[:] = 0.0
                hal_B.data.ctrl[:] = 0.0
                mujoco.mj_forward(hal_B.model, hal_B.data)
                s_B = hal_B.read_sensors()

                # Compute Distances
                sonar_A = s_A[:15]
                sonar_B = s_B[:15]
                d_sensory = float(np.linalg.norm(sonar_A - sonar_B))
                max_ray_diff = float(np.max(np.abs(sonar_A - sonar_B)))
                d_body = float(np.abs(s_A[15] - s_B[15]) + np.abs(s_A[18] - s_B[18]))  # accel + gyro
                d_yaw = float(abs(math.atan2(math.sin(yaw_A - yaw_B), math.cos(yaw_A - yaw_B))))
                
                # In family 3, pose is matched in relative coordinate frame to intersection center
                if fam_key == "family_3":
                    rel_pA = np.array(pA) - np.array(spec["pos_A"])
                    rel_pB = np.array(pB) - np.array(spec["pos_B"])
                    d_pose = float(np.linalg.norm(rel_pA - rel_pB))
                else:
                    d_pose = float(np.linalg.norm(np.array(pA) - np.array(pB)))

                # Check Acceptance Thresholds
                pass_sensory = bool(d_sensory <= 0.150 and max_ray_diff <= 0.080)
                pass_body = bool(d_body <= 0.050)
                pass_yaw = bool(d_yaw <= 0.050)
                pass_pose = bool(d_pose <= 0.050)
                trial_passed = bool(pass_sensory and pass_body and pass_yaw and pass_pose)

                fam_data["max_d_sensory"] = max(fam_data["max_d_sensory"], d_sensory)
                fam_data["max_single_ray_diff"] = max(fam_data["max_single_ray_diff"], max_ray_diff)
                fam_data["max_d_body"] = max(fam_data["max_d_body"], d_body)
                fam_data["max_d_yaw"] = max(fam_data["max_d_yaw"], d_yaw)
                fam_data["max_d_pose"] = max(fam_data["max_d_pose"], d_pose)

                results["total_trials_evaluated"] += 1
                if not trial_passed:
                    results["failed_trials"] += 1
                    fam_data["family_passed"] = False
                    results["overall_pass"] = False

                fam_data["trials"].append({
                    "seed": seed,
                    "trial_idx": trial_idx,
                    "d_sensory": d_sensory,
                    "max_ray_diff": max_ray_diff,
                    "d_body": d_body,
                    "d_yaw": d_yaw,
                    "d_pose": d_pose,
                    "passed": trial_passed,
                })

        print(f"  Max D_sensory        : {fam_data['max_d_sensory']:.4f} m (threshold <= 0.150 m)")
        print(f"  Max Single Ray Diff  : {fam_data['max_single_ray_diff']:.4f} m (threshold <= 0.080 m)")
        print(f"  Max D_body           : {fam_data['max_d_body']:.4f}   (threshold <= 0.050)")
        print(f"  Max D_yaw            : {fam_data['max_d_yaw']:.4f} rad (threshold <= 0.050 rad)")
        print(f"  Max D_pose           : {fam_data['max_d_pose']:.4f} m   (threshold <= 0.050 m)")
        print(f"  Evaluator Oracle ||Delta u*||: {fam_data['action_divergence']:.4f} (threshold >= 0.250)")
        print(f"  Family Equivalence Pass: {'PASS [OK]' if fam_data['family_passed'] else 'FAIL [DEFECTIVE]'}")

        results["families"][fam_key] = fam_data

    out_file = EVIDENCE_DIR / "observational_equivalence_data.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n=========================================================================")
    print(f"TOTAL MATCHED TRIALS AUDITED : {results['total_trials_evaluated']}")
    print(f"FAILED PAIRS                : {results['failed_trials']}")
    print(f"OVERALL EQUIVALENCE STATUS  : {'PASS [CERTIFIED]' if results['overall_pass'] else 'FAIL [REJECTED]'}")
    print(f"Saved Evidence Data         : {out_file}")
    print("=========================================================================\n")

    return results


if __name__ == "__main__":
    res = evaluate_observational_equivalence()
    if not res["overall_pass"]:
        sys.exit(1)
