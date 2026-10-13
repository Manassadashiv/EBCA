"""
brain/test_stage2_1a_spatial.py — Stage 2.1A: Spatial Self-Localization Experiments
Classification: [VERIFICATION] Dead-Reckoning Integration with Slip Gating

Three experiments, strictly adhering to the Stage 2.1 developmental specification:

Experiment 1: Square Trajectory Drift (Closed Loop)
    CARL performs a closed square (4 legs of 0.5m with 90 deg right turns),
    guided entirely by its own internal dead-reckoning state (x, y, theta).
    Evaluates final physical return drift (<= 15% of path) and heading error (<= 12 deg).

Experiment 2: Low-Friction Slip Immunity (Battery 2.1B)
    CARL drives forward across 3 regimes: Dry (15 ticks) -> Glaze Ice (30 ticks) -> Dry Recovery (15 ticks).
    Compares Naive wheel integration (ungated) vs CARL Stage 2.1A Slip-Gated integration.
    Gate: False advance during ice phase must be <= 0.05m (<= 50% of naive).

Experiment 3: Sensor Permutation & Gyro Sensitivity
    Evaluates heading tracking accuracy under true gyro (channel 20) vs scrambled sensor (channel 0).
    Gate: Correct gyro Mean Absolute Heading Error <= 10 deg, wrong sensor MAE > 5x worse.

Seeds:
    Development seeds: [42, 101, 202]
    Test seeds (unseen): [303, 404, 505, 606, 707]
"""

import os
import sys
import json
import math
import time
import numpy as np
from typing import Dict, Any, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_organism import CarlStage1Organism
from brain.carl_stage2_dead_reckoning import DeadReckoningModule


# =============================================================================
# EXPERIMENT 1: Square Trajectory Drift (Guided by Internal State)
# =============================================================================

def run_experiment_1(seed: int = 42) -> Dict[str, Any]:
    """
    Experiment 1: Drive closed square guided by internal dead reckoning.
    Gate: Return drift <= 15.0% of total path, Heading error <= 12.0 deg.
    """
    hal = CarlStage1HAL(open_space=True)
    hal.reset()
    hal.set_floor_friction(3.0)
    dt = float(3 * hal.model.opt.timestep)

    org = CarlStage1Organism(hal=hal, seed=seed)
    org.discovered_topology = {"discovered_drive_channels": [0, 1]}
    org.run_session(60)
    org.learn_predictive_readout(reg_lambda=10.0)

    hal.reset()
    hal.set_floor_friction(3.0)
    dr = DeadReckoningModule(dt=dt)
    dr.slip_gate_enabled = True

    u_fwd = np.array([0.12, 0.12, 0.0, 0.0, 0.0, 0.0])
    u_turn = np.array([0.10, -0.10, 0.0, 0.0, 0.0, 0.0])

    gt_trajectory = []
    est_trajectory = []

    for leg in range(4):
        # 1. Forward until internal DR says 0.50m
        start_x, start_y = dr.x, dr.y
        for _ in range(120):
            s, diag = hal.step(u_fwd)
            kin = org.update_kinematic_state(u_fwd, s)
            dr.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[20]), slip_ratio=kin["slip_ratio"])
            gt_trajectory.append((diag["pos_x"], diag["pos_y"], diag["yaw"]))
            est_trajectory.append((dr.x, dr.y, dr.theta))

            dist = math.sqrt((dr.x - start_x)**2 + (dr.y - start_y)**2)
            if dist >= 0.50:
                break

        # 2. Turn right until internal DR says -90 deg (-pi/2)
        start_th = dr.theta
        for _ in range(80):
            s, diag = hal.step(u_turn)
            kin = org.update_kinematic_state(u_turn, s)
            dr.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[20]), slip_ratio=kin["slip_ratio"])
            gt_trajectory.append((diag["pos_x"], diag["pos_y"], diag["yaw"]))
            est_trajectory.append((dr.x, dr.y, dr.theta))

            dth = dr.theta - start_th
            dth = math.atan2(math.sin(dth), math.cos(dth))
            if dth <= -math.pi / 2.0:
                break

    diag = hal.get_diagnostics()
    gt_return_drift = math.sqrt(diag["pos_x"]**2 + diag["pos_y"]**2)
    est_return_drift = dr.get_distance_from_origin()
    total_path = dr.total_distance_integrated
    drift_pct = (gt_return_drift / max(total_path, 0.01)) * 100.0

    heading_err = abs(math.degrees(diag["yaw"]))
    heading_err = min(heading_err, 360.0 - heading_err)

    passed = bool(drift_pct <= 15.0 and heading_err <= 12.0)

    result = {
        "passed": passed,
        "total_ticks": dr.tick_count,
        "total_path_length_m": total_path,
        "gt_return_drift_m": gt_return_drift,
        "est_return_drift_m": est_return_drift,
        "est_drift_pct_of_path": drift_pct,
        "est_heading_error_deg": heading_err,
        "gate_drift_pct_limit": 15.0,
        "gate_heading_error_limit_deg": 12.0,
        "verdict": (
            f"PASS — Position drift {drift_pct:.1f}% (limit <=15%), heading error {heading_err:.1f} deg (limit <=12 deg)."
            if passed else
            f"FAIL — Position drift {drift_pct:.1f}% (limit <=15%), heading error {heading_err:.1f} deg (limit <=12 deg)."
        )
    }
    return result


# =============================================================================
# EXPERIMENT 2: Low-Friction Slip Immunity (Battery 2.1B)
# =============================================================================

def run_experiment_2(seed: int = 42) -> Dict[str, Any]:
    """
    Experiment 2: Ice immunity comparison across Dry -> Ice -> Dry.
    Gate: False advance on ice (gated) <= 0.05m, reduction vs naive >= 50%.
    """
    hal = CarlStage1HAL(open_space=True)
    hal.reset()
    hal.set_floor_friction(3.0)
    dt = float(3 * hal.model.opt.timestep)

    org = CarlStage1Organism(hal=hal, seed=seed)
    org.discovered_topology = {"discovered_drive_channels": [0, 1]}
    org.run_session(60)
    org.learn_predictive_readout(reg_lambda=10.0)

    hal.reset()
    hal.set_floor_friction(3.0)
    dr_naive = DeadReckoningModule(dt=dt)
    dr_naive.slip_gate_enabled = False
    dr_gated = DeadReckoningModule(dt=dt)
    dr_gated.slip_gate_enabled = True

    u_fwd = np.array([0.15, 0.15, 0.0, 0.0, 0.0, 0.0])

    # Phase 1: Dry (15 ticks)
    for _ in range(15):
        s, diag = hal.step(u_fwd)
        kin = org.update_kinematic_state(u_fwd, s)
        dr_naive.update(v_hat_x=kin["v_wheel"], omega_z=float(s[20]), slip_ratio=0.0)
        dr_gated.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[20]), slip_ratio=kin["slip_ratio"])

    # Phase 2: Glaze Ice (mu = 0.005, 30 ticks)
    hal.set_floor_friction(0.005)
    ice_start_naive = dr_naive.x
    ice_start_gated = dr_gated.x
    ice_start_gt = hal.get_diagnostics()["pos_x"]

    for _ in range(30):
        s, diag = hal.step(u_fwd)
        kin = org.update_kinematic_state(u_fwd, s)
        dr_naive.update(v_hat_x=kin["v_wheel"], omega_z=float(s[20]), slip_ratio=0.0)
        dr_gated.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[20]), slip_ratio=kin["slip_ratio"])

    ice_adv_naive = abs(dr_naive.x - ice_start_naive)
    ice_adv_gated = abs(dr_gated.x - ice_start_gated)
    ice_adv_gt = abs(hal.get_diagnostics()["pos_x"] - ice_start_gt)

    # Phase 3: Dry Recovery (15 ticks)
    hal.set_floor_friction(3.0)
    for _ in range(15):
        s, diag = hal.step(u_fwd)
        kin = org.update_kinematic_state(u_fwd, s)
        dr_naive.update(v_hat_x=kin["v_wheel"], omega_z=float(s[20]), slip_ratio=0.0)
        dr_gated.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[20]), slip_ratio=kin["slip_ratio"])

    error_ratio = ice_adv_gated / max(ice_adv_naive, 1e-6)
    reduction_pct = (1.0 - error_ratio) * 100.0

    passed = bool(ice_adv_gated <= 0.05 and error_ratio <= 0.50)

    result = {
        "passed": passed,
        "ice_advance_gt_m": ice_adv_gt,
        "ice_advance_naive_m": ice_adv_naive,
        "ice_advance_gated_m": ice_adv_gated,
        "error_ratio_gated_over_naive": error_ratio,
        "false_drift_reduction_pct": reduction_pct,
        "ticks_gated_on_ice": dr_gated.total_ticks_gated,
        "gate_false_advance_limit_m": 0.05,
        "gate_error_ratio_limit": 0.50,
        "verdict": (
            f"PASS — Slip-gated false advance on ice is {ice_adv_gated:.4f}m (limit <=0.05m), "
            f"achieving {reduction_pct:.1f}% reduction vs naive ({ice_adv_naive:.4f}m)."
            if passed else
            f"FAIL — Slip-gated advance {ice_adv_gated:.4f}m (limit <=0.05m), ratio {error_ratio:.2f}."
        )
    }
    return result


# =============================================================================
# EXPERIMENT 3: Sensor Permutation & Gyro Sensitivity
# =============================================================================

def run_experiment_3(seed: int = 42) -> Dict[str, Any]:
    """
    Experiment 3: Heading MAE under correct gyro (ch 20) vs wrong sensor (ch 0).
    Gate: Correct MAE <= 10.0 deg, Degradation factor >= 5.0x.
    """
    hal = CarlStage1HAL(open_space=True)
    hal.reset()
    hal.set_floor_friction(3.0)
    dt = float(3 * hal.model.opt.timestep)

    org = CarlStage1Organism(hal=hal, seed=seed)
    org.discovered_topology = {"discovered_drive_channels": [0, 1]}
    org.run_session(60)
    org.learn_predictive_readout(reg_lambda=10.0)

    hal.reset()
    hal.set_floor_friction(3.0)
    dr_correct = DeadReckoningModule(dt=dt)
    dr_wrong = DeadReckoningModule(dt=dt)

    actions = [
        (np.array([0.12, 0.12, 0.0, 0.0, 0.0, 0.0]), 20),
        (np.array([0.10, -0.10, 0.0, 0.0, 0.0, 0.0]), 15),
        (np.array([0.12, 0.12, 0.0, 0.0, 0.0, 0.0]), 20),
        (np.array([-0.10, 0.10, 0.0, 0.0, 0.0, 0.0]), 25),
    ]

    th_c, th_w = [], []

    for u_cmd, steps in actions:
        for _ in range(steps):
            s, diag = hal.step(u_cmd)
            kin = org.update_kinematic_state(u_cmd, s)
            gt_yaw = diag["yaw"]

            dr_correct.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[20]), slip_ratio=kin["slip_ratio"])
            dr_wrong.update(v_hat_x=kin["v_hat_x"], omega_z=float(s[0]), slip_ratio=kin["slip_ratio"])

            err_c = abs(math.atan2(math.sin(dr_correct.theta - gt_yaw), math.cos(dr_correct.theta - gt_yaw)))
            err_w = abs(math.atan2(math.sin(dr_wrong.theta - gt_yaw), math.cos(dr_wrong.theta - gt_yaw)))

            th_c.append(math.degrees(err_c))
            th_w.append(math.degrees(err_w))

    mae_c = float(np.mean(th_c))
    mae_w = float(np.mean(th_w))
    degradation = float(mae_w / max(mae_c, 1e-4))

    passed = bool(mae_c <= 10.0 and degradation >= 5.0)

    result = {
        "passed": passed,
        "correct_gyro_channel": 20,
        "wrong_sensor_channel": 0,
        "correct_mae_deg": mae_c,
        "wrong_mae_deg": mae_w,
        "degradation_factor": degradation,
        "gate_correct_mae_limit_deg": 10.0,
        "gate_degradation_factor_min": 5.0,
        "verdict": (
            f"PASS — Correct gyro MAE is {mae_c:.2f} deg (limit <=10 deg), "
            f"scrambled sensor degrades {degradation:.1f}x to {mae_w:.2f} deg."
            if passed else
            f"FAIL — Correct MAE {mae_c:.2f} deg, Degradation {degradation:.1f}x."
        )
    }
    return result


# =============================================================================
# MASTER RUNNER
# =============================================================================

def run_stage2_1a_experiments(
    seeds: List[int] = None,
    label: str = "development",
) -> Dict[str, Any]:
    """Runs all 3 experiments across specified seeds and logs formatted results."""
    if seeds is None:
        seeds = [42, 101, 202]

    print("=" * 80)
    print(f"CARL STAGE 2.1A: SPATIAL SELF-LOCALIZATION EXPERIMENTS ({label.upper()} SEEDS)")
    print(f"Seeds: {seeds}")
    print("=" * 80)

    all_results = {
        "label": label,
        "seeds": seeds,
        "timestamp": time.time(),
        "seed_results": {},
    }

    for seed in seeds:
        print(f"\n--- Running Seed {seed} ---")
        e1 = run_experiment_1(seed=seed)
        print(f"  Exp 1 (Square): {e1['verdict']}")

        e2 = run_experiment_2(seed=seed)
        print(f"  Exp 2 (Ice Gate): {e2['verdict']}")

        e3 = run_experiment_3(seed=seed)
        print(f"  Exp 3 (Permutation): {e3['verdict']}")

        all_ok = bool(e1["passed"] and e2["passed"] and e3["passed"])
        all_results["seed_results"][str(seed)] = {
            "experiment_1": e1,
            "experiment_2": e2,
            "experiment_3": e3,
            "all_passed": all_ok,
        }

    total_seeds = len(seeds)
    passing_seeds = sum(1 for sr in all_results["seed_results"].values() if sr["all_passed"])

    all_results["master_synthesis"] = {
        "total_seeds": total_seeds,
        "passing_seeds": passing_seeds,
        "all_passed": (passing_seeds == total_seeds),
        "pass_rate": passing_seeds / total_seeds,
    }

    out_dir = os.path.join(REPO_ROOT, "evidence", "stage2_1a")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"carl_stage2_1a_{label}_results.json")

    def to_serializable(obj):
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return str(obj)

    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(all_results, fp, indent=2, default=to_serializable)

    print(f"\n[RECEIPT] Telemetry saved to: {out_path}")
    print("=" * 80)
    print(f"STAGE 2.1A {label.upper()}: {passing_seeds}/{total_seeds} SEEDS PASSED")
    print("=" * 80)

    print("\nPer-Experiment Summary Table:")
    print(f"{'Seed':<8} {'Exp1 (Square)':<24} {'Exp2 (Ice Gate)':<24} {'Exp3 (Permutation)':<24} {'All':<6}")
    print("-" * 88)
    for seed_str, sr in all_results["seed_results"].items():
        s1 = "[PASS]" if sr["experiment_1"]["passed"] else "[FAIL]"
        s2 = "[PASS]" if sr["experiment_2"]["passed"] else "[FAIL]"
        s3 = "[PASS]" if sr["experiment_3"]["passed"] else "[FAIL]"
        sa = "[PASS]" if sr["all_passed"] else "[FAIL]"
        e1_info = f"{s1} {sr['experiment_1']['est_drift_pct_of_path']:.1f}% drift"
        e2_info = f"{s2} {sr['experiment_2']['ice_advance_gated_m']:.3f}m"
        e3_info = f"{s3} {sr['experiment_3']['degradation_factor']:.1f}x"
        print(f"{seed_str:<8} {e1_info:<24} {e2_info:<24} {e3_info:<24} {sa}")

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CARL Stage 2.1A Spatial Experiments")
    parser.add_argument("--mode", choices=["dev", "test", "all"], default="dev",
                        help="Which seed set to run: dev (42,101,202), test (303,404,505,606,707), all")
    args = parser.parse_args()

    if args.mode == "dev":
        run_stage2_1a_experiments(seeds=[42, 101, 202], label="development")
    elif args.mode == "test":
        run_stage2_1a_experiments(seeds=[303, 404, 505, 606, 707], label="test")
    elif args.mode == "all":
        run_stage2_1a_experiments(seeds=[42, 101, 202], label="development")
        run_stage2_1a_experiments(seeds=[303, 404, 505, 606, 707], label="test")
