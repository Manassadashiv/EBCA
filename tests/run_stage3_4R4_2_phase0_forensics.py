"""
tests/run_stage3_4R4_2_phase0_forensics.py — Stage 3.4-R4.2 Phase 0 Decision-Chain Forensic Decomposition
Executes tick-by-tick telemetry logging on Env2 screening episodes (Configs 20, 21, 22, 23, 24)
under the frozen R4.1 baseline (ARM-A, w_info=1.0, M=128, H=15, dt=0.030s).
ZERO behavioral modifications. ZERO parameter tuning.

Records for every tick:
1. selected macro-frontier (x_f, y_f)
2. frontier target change from previous tick (delta_f)
3. total candidate count (M=128)
4. feasible candidate count
5. rejected candidate count
6. veto fraction
7. top-K feasible candidates
8. G_best
9. G_second
10. Delta_G = G_second - G_best
11. softmax probabilities
12. softmax entropy
13. effective candidate count (N_eff = 1 / sum(p^2))
14. selected action u*
15. predicted terminal pose of u*
16. predicted minimum hull clearance
17. internal heading
18. evaluator-only heading
19. instantaneous heading error
20. actual physical displacement dx, dy
21. branch-progress metric (distance toward south exit y <= -1.20m)
22. time spent without southward progress

Saves:
  evidence/stage3_4R4_1/r4_2_decision_chain_forensics.json
"""

import sys
import math
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
import torch.nn.functional as F
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_stage1_hal import CarlStage1HAL
from tests.diagnose_env2_failures import build_50_matched_configurations

EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4_1"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

ENV2_XML = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"
ENV2_GRID = repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"

SCREENING_ENV2_CONFIG_IDS = [20, 21, 22, 23, 24]
MAX_TICKS = 220


class DecisionChainObserver:
    """
    Observes baseline execution without modifying any behavioral logic or controller parameters.
    Hooks _evaluate_expected_free_energy to capture exact EFE cost distributions, candidate
    separation, and softmax entropy.
    """
    def __init__(self, controller: CARLActiveInferenceEngine):
        self.ctrl = controller
        self.last_efe_costs = None
        self.last_efe_debug = None

        orig_eval = self.ctrl._evaluate_expected_free_energy
        def wrapped_eval(*args, **kwargs):
            g_total, efe_debug = orig_eval(*args, **kwargs)
            self.last_efe_costs = g_total.detach().clone()
            self.last_efe_debug = efe_debug
            return g_total, efe_debug

        self.ctrl._evaluate_expected_free_energy = wrapped_eval

    def observe_and_step(
        self,
        curr_sensors: np.ndarray,
        curr_v: float,
        curr_w: float
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        # Call unmodified baseline select_action
        u_star, telem = self.ctrl.select_action(curr_sensors, curr_v=curr_v, curr_w=curr_w)

        efe_costs = self.last_efe_costs
        efe_debug = self.last_efe_debug

        M = self.ctrl.M
        collision_mask = efe_debug["collision_mask"]
        feasible_mask = ~collision_mask
        n_feasible = int(np.sum(feasible_mask))
        n_rejected = int(np.sum(collision_mask))
        veto_fraction = float(n_rejected / M)

        efe_np = efe_costs.cpu().numpy()
        feasible_costs = efe_np[feasible_mask]

        if len(feasible_costs) >= 2:
            sorted_feas = np.sort(feasible_costs)
            g_best = float(sorted_feas[0])
            g_second = float(sorted_feas[1])
            delta_g = float(g_second - g_best)
            top5_costs = [float(x) for x in sorted_feas[:5]]
        elif len(feasible_costs) == 1:
            g_best = float(feasible_costs[0])
            g_second = float(feasible_costs[0])
            delta_g = 0.0
            top5_costs = [g_best]
        else:
            sorted_all = np.sort(efe_np)
            g_best = float(sorted_all[0])
            g_second = float(sorted_all[1])
            delta_g = float(g_second - g_best)
            top5_costs = [float(x) for x in sorted_all[:5]]

        # Softmax probabilities over all candidates under baseline temperature
        min_cost = float(torch.min(efe_costs).item())
        scaled_costs = efe_np - min_cost
        weights = np.exp(-scaled_costs / self.ctrl.temperature)
        probs = weights / (np.sum(weights) + 1e-12)

        entropy = float(-np.sum(probs * np.log(probs + 1e-12)))
        n_eff = float(1.0 / (np.sum(probs ** 2) + 1e-8))

        macro_res = self.ctrl._cached_macro_frontier

        # Compute predicted terminal pose from warm-started action sequence
        pred_x, pred_y, pred_th = self.ctrl.pose
        dt = self.ctrl.dt
        for h in range(self.ctrl.horizon):
            ul = float(self.ctrl.nominal_u[h, 0])
            ur = float(self.ctrl.nominal_u[h, 1])
            v = 0.5 * (ul + ur) * 0.35
            w = (ur - ul) * 0.35 / 0.230
            pred_th += w * dt
            pred_x += v * math.cos(pred_th) * dt
            pred_y += v * math.sin(pred_th) * dt
        predicted_term_pose = [round(pred_x, 4), round(pred_y, 4), round(pred_th, 4)]

        forensic_data = {
            "macro_frontier": [round(float(macro_res[0]), 3), round(float(macro_res[1]), 3)] if macro_res else None,
            "total_candidates": M,
            "feasible_candidates": n_feasible,
            "rejected_candidates": n_rejected,
            "veto_fraction": round(veto_fraction, 4),
            "g_best": round(g_best, 4),
            "g_second": round(g_second, 4),
            "delta_g": round(delta_g, 4),
            "top5_feasible_costs": [round(c, 4) for c in top5_costs],
            "softmax_entropy": round(entropy, 4),
            "effective_candidates_neff": round(n_eff, 2),
            "selected_action": [round(float(u_star[0]), 4), round(float(u_star[1]), 4)],
            "predicted_term_pose": predicted_term_pose,
            "min_predicted_hull_clearance": float(telem.get("min_predicted_hull_clearance", 0.0)),
            "sonar_heading_confidence": float(telem.get("sonar_heading_confidence", 0.0)),
        }

        return u_star, forensic_data


def run_phase0_decomposition():
    print("=======================================================================")
    print("  CARL-DX STAGE 3.4-R4.2 PHASE 0: DECISION-CHAIN FORENSICS")
    print("=======================================================================")

    all_configs = build_50_matched_configurations()
    env2_configs = [c for c in all_configs if c["config_id"] in SCREENING_ENV2_CONFIG_IDS]

    dataset = []

    for cfg in env2_configs:
        cfg_id = cfg["config_id"]
        seed = cfg["seed"]
        np.random.seed(seed)
        torch.manual_seed(seed)

        hal = CarlStage1HAL(xml_path=str(ENV2_XML))
        ctrl = CARLActiveInferenceEngine(
            grid_path=str(ENV2_GRID),
            w_info=1.0,
            frontier_mode="macro",
            norm_mode="dimensionless",
        )
        observer = DecisionChainObserver(ctrl)

        sx, sy = cfg["spawn_pos"]
        syaw = cfg["spawn_yaw"]
        ctrl.initialize_pose(sx, sy, syaw)

        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)

        # Evaluator-only dead reckoning tracker for gyro alone
        gyro_only_yaw = syaw

        v_est = 0.0
        collided = False
        escaped = False

        prev_frontier = None
        frontier_changes = 0
        frontier_displacements = []
        consecutive_stagnant_ticks = 0
        max_stagnant_ticks = 0
        best_south_y = sy

        episode_ticks = []
        prev_true_x, prev_true_y = sx, sy

        for tick in range(MAX_TICKS):
            curr_sensors = hal.read_sensors()
            gyro_w = float(curr_sensors[20])

            # Update odometry in controller
            ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_w, dt=0.030)
            gyro_only_yaw += gyro_w * 0.030

            # Ground truth from evaluator firewall
            qa = int(hal.model.joint("spatial_identity").qposadr[0])
            true_x = float(hal.data.qpos[qa])
            true_y = float(hal.data.qpos[qa+1])
            q_rot = hal.data.qpos[qa+3:qa+7]
            true_yaw = math.atan2(2.0 * (q_rot[0]*q_rot[3] + q_rot[1]*q_rot[2]),
                                  1.0 - 2.0 * (q_rot[2]**2 + q_rot[3]**2))

            # Step Action Selection
            u_star, f_meta = observer.observe_and_step(curr_sensors, curr_v=v_est, curr_w=gyro_w)

            # Physical step
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = float(u_star[0])
            cmd_6d[1] = float(u_star[1])
            hal.step(cmd_6d)

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

            # Check contacts
            c_info = hal.get_carl_contact_info()
            if (c_info["carl_contacts"] - c_info["floor_contacts"]) > 0:
                collided = True

            # Check escape
            if true_y <= -1.20:
                escaped = True

            # Displacements & branch progress
            dx = true_x - prev_true_x
            dy = true_y - prev_true_y
            prev_true_x, prev_true_y = true_x, true_y

            # Southward branch progress: distance remaining to y <= -1.20m
            dist_to_escape = max(0.0, true_y - (-1.20))
            if true_y < best_south_y - 0.005:  # Progressed south by at least 5mm
                best_south_y = true_y
                consecutive_stagnant_ticks = 0
            else:
                consecutive_stagnant_ticks += 1
                if consecutive_stagnant_ticks > max_stagnant_ticks:
                    max_stagnant_ticks = consecutive_stagnant_ticks

            # Frontier Stability calculation
            curr_f = f_meta["macro_frontier"]
            f_disp = 0.0
            if prev_frontier is not None and curr_f is not None:
                f_disp = math.hypot(curr_f[0] - prev_frontier[0], curr_f[1] - prev_frontier[1])
                if f_disp > 0.20:  # Displacement > 20cm considered a change event
                    frontier_changes += 1
                    frontier_displacements.append(f_disp)
            prev_frontier = curr_f

            # Heading Errors
            est_yaw = ctrl.pose[2]
            fused_err_deg = math.degrees(abs(math.atan2(math.sin(est_yaw - true_yaw), math.cos(est_yaw - true_yaw))))
            gyro_err_deg = math.degrees(abs(math.atan2(math.sin(gyro_only_yaw - true_yaw), math.cos(gyro_only_yaw - true_yaw))))

            # Numerical Causal Classification for this tick
            # Criteria:
            # A: Hull starvation (feasible <= 12 or veto >= 0.90)
            # B: EFE indecision (feasible >= 32, delta_g <= 0.08, entropy >= 2.0)
            # C: Heading degradation (heading_err >= 25.0 deg)
            # D: Model/Action mismatch (pred dy < -0.02 but physical dy >= 0.0)
            # E: Coupled (more than one of above active)
            crit_a = bool(f_meta["feasible_candidates"] <= 12 or f_meta["veto_fraction"] >= 0.90)
            crit_b = bool(f_meta["feasible_candidates"] >= 32 and f_meta["delta_g"] <= 0.08 and f_meta["softmax_entropy"] >= 2.0)
            crit_c = bool(fused_err_deg >= 25.0)
            pred_dy = f_meta["predicted_term_pose"][1] - true_y
            crit_d = bool(pred_dy < -0.02 and dy >= 0.0 and f_meta["feasible_candidates"] >= 32 and not crit_c)

            active_crits = sum([crit_a, crit_b, crit_c, crit_d])
            if active_crits > 1:
                tick_class = "E. COUPLED"
            elif crit_a:
                tick_class = "A. HULL STARVATION"
            elif crit_b:
                tick_class = "B. EFE INDECISION"
            elif crit_c:
                tick_class = "C. HEADING DEGRADATION"
            elif crit_d:
                tick_class = "D. ACTION/MODEL MISMATCH"
            else:
                tick_class = "NOMINAL PROGRESS"

            tick_rec = {
                "tick": tick,
                "macro_frontier": curr_f,
                "frontier_displacement_m": round(f_disp, 4),
                "total_candidates": f_meta["total_candidates"],
                "feasible_candidates": f_meta["feasible_candidates"],
                "rejected_candidates": f_meta["rejected_candidates"],
                "veto_fraction": f_meta["veto_fraction"],
                "g_best": f_meta["g_best"],
                "g_second": f_meta["g_second"],
                "delta_g": f_meta["delta_g"],
                "top5_feasible_costs": f_meta["top5_feasible_costs"],
                "softmax_entropy": f_meta["softmax_entropy"],
                "effective_candidates_neff": f_meta["effective_candidates_neff"],
                "selected_action": f_meta["selected_action"],
                "predicted_terminal_pose": f_meta["predicted_term_pose"],
                "min_predicted_hull_clearance": round(f_meta["min_predicted_hull_clearance"], 4),
                "internal_heading_deg": round(math.degrees(est_yaw), 2),
                "evaluator_heading_deg": round(math.degrees(true_yaw), 2),
                "gyro_only_heading_deg": round(math.degrees(gyro_only_yaw), 2),
                "fused_heading_error_deg": round(fused_err_deg, 2),
                "gyro_heading_error_deg": round(gyro_err_deg, 2),
                "gyro_w_rads": round(gyro_w, 4),
                "sonar_confidence": round(f_meta["sonar_heading_confidence"], 3),
                "physical_x": round(true_x, 4),
                "physical_y": round(true_y, 4),
                "physical_dx": round(dx, 4),
                "physical_dy": round(dy, 4),
                "dist_to_escape_m": round(dist_to_escape, 4),
                "consecutive_stagnant_ticks": consecutive_stagnant_ticks,
                "tick_classification": tick_class,
            }
            episode_ticks.append(tick_rec)

            if collided or escaped:
                break

        term_reason = "ESCAPED" if escaped else ("COLLIDED" if collided else "TIMEOUT")

        # Episode level summary
        ep_summary = {
            "config_id": cfg_id,
            "seed": seed,
            "env_id": 2,
            "arm": "ARM-A",
            "termination_reason": term_reason,
            "ticks_executed": len(episode_ticks),
            "frontier_changes_count": frontier_changes,
            "fraction_ticks_with_frontier_change": round(frontier_changes / max(1, len(episode_ticks)), 4),
            "mean_frontier_displacement_m": round(float(np.mean(frontier_displacements)), 4) if frontier_displacements else 0.0,
            "max_frontier_displacement_m": round(float(np.max(frontier_displacements)), 4) if frontier_displacements else 0.0,
            "mean_veto_fraction": round(float(np.mean([t["veto_fraction"] for t in episode_ticks])), 4),
            "mean_feasible_count": round(float(np.mean([t["feasible_candidates"] for t in episode_ticks])), 2),
            "mean_delta_g": round(float(np.mean([t["delta_g"] for t in episode_ticks])), 4),
            "mean_softmax_entropy": round(float(np.mean([t["softmax_entropy"] for t in episode_ticks])), 4),
            "mean_neff": round(float(np.mean([t["effective_candidates_neff"] for t in episode_ticks])), 2),
            "mean_fused_heading_error_deg": round(float(np.mean([t["fused_heading_error_deg"] for t in episode_ticks])), 2),
            "p95_fused_heading_error_deg": round(float(np.percentile([t["fused_heading_error_deg"] for t in episode_ticks], 95)), 2),
            "max_fused_heading_error_deg": round(float(np.max([t["fused_heading_error_deg"] for t in episode_ticks])), 2),
            "mean_gyro_heading_error_deg": round(float(np.mean([t["gyro_heading_error_deg"] for t in episode_ticks])), 2),
            "max_stagnant_ticks": max_stagnant_ticks,
            "final_pose": [episode_ticks[-1]["physical_x"], episode_ticks[-1]["physical_y"]],
            "ticks": episode_ticks
        }
        dataset.append(ep_summary)
        print(f"Config {cfg_id}: Outcome = {term_reason} | Ticks = {len(episode_ticks)} | Frontier Changes = {frontier_changes} | Mean Veto = {ep_summary['mean_veto_fraction']:.1%} | Mean dG = {ep_summary['mean_delta_g']:.3f} | Max HErr = {ep_summary['max_fused_heading_error_deg']:.1f} deg | Stagnant Ticks = {max_stagnant_ticks}")

    out_json = EVIDENCE_DIR / "r4_2_decision_chain_forensics.json"
    with open(out_json, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"\nSaved Forensic Decomposition Data to {out_json}")
    return dataset


if __name__ == "__main__":
    run_phase0_decomposition()
