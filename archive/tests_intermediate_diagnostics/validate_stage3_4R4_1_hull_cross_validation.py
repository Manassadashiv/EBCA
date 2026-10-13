"""
tests/validate_stage3_4R4_1_hull_cross_validation.py — Part 4 Rectangular Hull Offline Cross-Validation
Compares predicted rectangular hull feasibility against actual MuJoCo collision ground truth across
candidate rollouts.
Saves confusion matrix (TP, FP, FN, TN) to evidence/stage3_4R4_1/hull_cross_validation.json.
"""

import sys
import math
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

OUT_DIR = repo_root / "evidence" / "stage3_4R4_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENV1_XML = repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"
ENV1_GRID = repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
ENV2_GRID = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"


def cross_validate_hull():
    print("Running Part 4 Rectangular Hull Cross-Validation...")
    test_states = [
        # Env 1: Centered in corridor
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "pos": [0.50, 0.00], "yaw": 0.0},
        # Env 1: Near south wall (y = -0.18, 3.5cm wall clearance)
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "pos": [0.50, -0.18], "yaw": 0.0},
        # Env 1: Near north wall (y = +0.18, 3.5cm wall clearance)
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "pos": [0.50, 0.18], "yaw": 0.0},
        # Env 1: In turning bay (x = 0.60, y = 0.40)
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "pos": [0.60, 0.40], "yaw": math.pi/2},
        # Env 1: Approaching dead end cap (x = 1.00, y = 0.0, 8.5cm front clearance)
        {"env": 1, "xml": ENV1_XML, "grid": ENV1_GRID, "pos": [1.00, 0.00], "yaw": 0.0},
        # Env 2: In approach corridor (x = 0.0, y = 0.0)
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "pos": [0.00, 0.00], "yaw": 0.0},
        # Env 2: At T-junction approaching front wall (x = 0.80, y = 0.0)
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "pos": [0.80, 0.00], "yaw": 0.0},
        # Env 2: In south branch centered (x = 0.825, y = -0.70)
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "pos": [0.825, -0.70], "yaw": -math.pi/2},
        # Env 2: In south branch near east wall (x = 0.95, y = -0.70)
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "pos": [0.95, -0.70], "yaw": -math.pi/2},
        # Env 2: In south branch near west wall (x = 0.70, y = -0.70)
        {"env": 2, "xml": ENV2_XML, "grid": ENV2_GRID, "pos": [0.70, -0.70], "yaw": -math.pi/2},
    ]

    tp, fp, fn, tn = 0, 0, 0, 0
    total_candidates = 0
    corridor_entering_total = 0
    corridor_entering_accepted = 0
    min_predicted_clearances = []
    min_actual_clearances = []

    for s_idx, state in enumerate(test_states):
        hal = CarlStage1HAL(xml_path=str(state["xml"]))
        ctrl = CARLActiveInferenceEngine(grid_path=str(state["grid"]))
        sx, sy = state["pos"]
        syaw = state["yaw"]
        ctrl.initialize_pose(sx, sy, syaw)

        # Populate static map or sensor reading
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        sensors = hal.read_sensors()
        ctrl.update_occupancy_memory(sensors)

        # Sample M=128 candidates
        u_batch = ctrl._sample_trajectories()
        px, py, pth = ctrl._vectorized_rollout(sx, sy, syaw, 0.0, 0.0, u_batch)

        # Evaluate EFE to get predicted collision mask & clearances
        costs, dbg = ctrl._evaluate_expected_free_energy(px, py, pth, u_batch, sx, sy, syaw, sensors, None)
        cand_coll_mask = dbg["collision_mask"]
        cand_min_dists = dbg["min_dists"]

        for m in range(ctrl.M):
            total_candidates += 1
            cand_u = u_batch[m].numpy() # (H, 2)

            # Step clone physics along candidate actions
            hal.reset()
            hal.data.qpos[qa:qa+2] = [sx, sy]
            hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
            mujoco.mj_forward(hal.model, hal.data)

            actual_collision = False
            min_contact_dist = 10.0
            for t in range(ctrl.horizon):
                cmd_6d = np.zeros(6, dtype=np.float64)
                cmd_6d[0] = float(cand_u[t, 0])
                cmd_6d[1] = float(cand_u[t, 1])
                hal.step(cmd_6d)
                c_info = hal.get_carl_contact_info()
                if (c_info["carl_contacts"] - c_info["floor_contacts"]) > 0:
                    actual_collision = True
                    min_contact_dist = 0.0
                    break

            predicted_rejected = bool(cand_coll_mask[m])
            pred_clearance = float(cand_min_dists[m]) if cand_min_dists is not None else 0.0
            min_predicted_clearances.append(pred_clearance)
            min_actual_clearances.append(min_contact_dist)

            # Track corridor-entering candidates (forward progress in corridor)
            if state["pos"][0] == 0.0 and state["env"] == 2:
                corridor_entering_total += 1
                if not predicted_rejected:
                    corridor_entering_accepted += 1

            if predicted_rejected and actual_collision:
                tp += 1
            elif predicted_rejected and not actual_collision:
                fp += 1  # Conservative safety veto (safe margin preservation)
            elif not predicted_rejected and actual_collision:
                fn += 1  # Missed collision (safety critical defect)
            else:
                tn += 1

        print(f"  State {s_idx+1}/{len(test_states)} tested ({state['pos']}, yaw={round(math.degrees(syaw))}deg).")

    fp_rate = fp / max(1, (fp + tn))
    fn_rate = fn / max(1, (fn + tp))
    accuracy = (tp + tn) / max(1, total_candidates)

    validation_result = {
        "total_candidate_rollouts_evaluated": total_candidates,
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives_conservative_vetoes": fp,
            "false_negatives_missed_collisions": fn,
            "true_negatives_safe_accepted": tn,
        },
        "accuracy_pct": round(accuracy * 100.0, 2),
        "false_positive_veto_rate_pct": round(fp_rate * 100.0, 2),
        "false_negative_rate_pct": round(fn_rate * 100.0, 2),
        "corridor_entering_candidates": {
            "total_evaluated": corridor_entering_total,
            "accepted": corridor_entering_accepted,
            "acceptance_rate_pct": round(corridor_entering_accepted / max(1, corridor_entering_total) * 100.0, 2),
        },
        "clearance_metrics": {
            "min_predicted_clearance_m": round(float(np.min(min_predicted_clearances)), 4),
            "mean_predicted_clearance_m": round(float(np.mean(min_predicted_clearances)), 4),
        },
        "safety_audit": "PASS" if fn_rate < 0.02 else "FAIL",
    }

    out_file = OUT_DIR / "hull_cross_validation.json"
    with open(out_file, "w") as f:
        json.dump(validation_result, f, indent=2)

    print("\n=== HULL CROSS-VALIDATION RESULTS ===")
    print(f"Total Rollouts: {total_candidates}")
    print(f"TP: {tp} | FP (Conservative Vetoes): {fp} | FN (Missed): {fn} | TN: {tn}")
    print(f"Accuracy: {validation_result['accuracy_pct']}%")
    print(f"False-Negative Rate: {validation_result['false_negative_rate_pct']}% (Target: < 2.0%)")
    print(f"Saved to {out_file}")
    return validation_result


if __name__ == "__main__":
    cross_validate_hull()
