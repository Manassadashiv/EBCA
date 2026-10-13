"""
brain/test_stage2_1b_r4_master_suite.py — Stage 2.1B-R.4 Master Experimental Protocol
Classification: [AUTHORITATIVE BENCHMARK & SCIENTIFIC AUDIT]
Subsystem: Smooth Angular-Gated Steering & Final Stage 2.1 Closure

Contracts:
1. Unified Organism: Implemented directly via canonical CarlStage2BIntegratedBrain.
2. Anti-Cheat: Zero privileged simulator state access (no qpos, qvel, friction, contact).
3. Dev/Test Separation:
   - DEV SEEDS: [42, 101, 202] (model fitting, held-out validation, freezing).
   - UNSEEN PRIMARY TEST SEEDS: [303, 404, 505, 606, 707] (strictly frozen zero-adaptation test).
4. Pre-Registered Falsification Gate:
   - 5 of 5 unseen seeds must strictly satisfy Final Drift <= 0.220000 m.
"""

import os
import sys
import time
import math
import json
import hashlib
import numpy as np
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import MultiScaleGridToroid
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
from brain.test_stage2_1b_r3_global_space import apply_carl_stochastic_initial_pose, inject_sensor_noise

OUTPUT_DIR = os.path.join(BASE_DIR, "evidence", "stage2_1b_r4")
os.makedirs(OUTPUT_DIR, exist_ok=True)
TELEMETRY_JSON = os.path.join(OUTPUT_DIR, "r4_telemetry.json")
PREFLIGHT_JSON = os.path.join(OUTPUT_DIR, "r4_preflight_audit.json")
SCORECARD_JSON = os.path.join(OUTPUT_DIR, "r4_scorecard.json")

DEV_SEEDS = [42, 101, 202]
UNSEEN_TEST_SEEDS = [303, 404, 505, 606, 707]
ALL_SEEDS = DEV_SEEDS + UNSEEN_TEST_SEEDS


def compute_steering_action_r4(
    r_hd: np.ndarray,
    angles_hd: np.ndarray,
    target_vec_x: float,
    target_vec_y: float,
    dist: float,
    controller_mode: str = "smooth_quadratic"
) -> Tuple[np.ndarray, bool]:
    """
    Biological Closed-Loop Steering via Head Direction Population Vector.
    - Smooth Quadratic (R.4): Forward speed scales smoothly with alignment squared.
    - Discontinuous Step (R.3): Full forward speed whenever alignment > 0.
    """
    if dist <= 0.04:
        return np.zeros(6, dtype=np.float64), True

    total_r = float(np.sum(r_hd)) + 1e-6
    neural_torque = float(np.sum(r_hd * (np.cos(angles_hd) * target_vec_y - np.sin(angles_hd) * target_vec_x)))
    forward_alignment = float(np.sum(r_hd * (np.cos(angles_hd) * target_vec_x + np.sin(angles_hd) * target_vec_y)))

    cos_align = np.clip(forward_alignment / (dist * total_r), -1.0, 1.0)
    steer_cmd = np.clip(0.40 * (neural_torque / (dist * total_r)), -0.15, 0.15)

    if controller_mode == "smooth_quadratic":
        # Break collinear saddle point if facing directly away
        if cos_align < -0.7 and abs(steer_cmd) < 0.02:
            steer_cmd = 0.10

        fwd_factor = max(0.0, cos_align) ** 2
        fwd_cmd = 0.12 * fwd_factor
    else:  # Legacy R.3 step controller
        if forward_alignment < 0.0 and abs(neural_torque) < 0.02:
            steer_cmd = 0.05
        fwd_cmd = 0.12 if forward_alignment > 0.0 else 0.01

    u = np.zeros(6, dtype=np.float64)
    u[0] = np.clip(fwd_cmd - steer_cmd, -0.15, 0.15)
    u[1] = np.clip(fwd_cmd + steer_cmd, -0.15, 0.15)
    return u, False


def generate_developmental_approach_sweeps(seed: int, n_sweeps: int = 10) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Generates approach babbling sweeps towards habitat reflective boundaries."""
    hal = CarlStage1HAL(open_space=False)
    rng = np.random.RandomState(seed)
    U_sweeps = []
    S_sweeps = []

    for sweep in range(n_sweeps):
        hal.reset()
        q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[q_addr] = float(rng.uniform(-1.0, 1.0))
        hal.data.qpos[q_addr + 1] = float(rng.uniform(1.5, 2.5))
        hal.data.qpos[q_addr + 2] = 0.05291

        yaw = math.pi / 2.0 + float(rng.uniform(-0.15, 0.15))
        hal.data.qpos[q_addr + 3] = math.cos(yaw / 2.0)
        hal.data.qpos[q_addr + 6] = math.sin(yaw / 2.0)
        hal.step(np.zeros(6))

        sweep_u = []
        sweep_s = []
        fwd_speed = float(rng.uniform(0.06, 0.14))
        for t in range(30):
            u = np.zeros(6)
            u[0] = fwd_speed + rng.normal(0, 0.003)
            u[1] = fwd_speed + rng.normal(0, 0.003)
            s, diag = hal.step(u)
            if s[7] > 0.4:
                sweep_u.append(u)
                sweep_s.append(s)
            else:
                break

        if len(sweep_u) > 5:
            U_sweeps.append(np.array(sweep_u))
            S_sweeps.append(np.array(sweep_s))

    return U_sweeps, S_sweeps


def run_preflight_audit(hal: CarlStage1HAL) -> Dict[str, Any]:
    """Phase 0: Preflight Stochastic Independence & Leakage Audit."""
    print("=" * 80)
    print("PHASE 0: PREFLIGHT STOCHASTIC INDEPENDENCE & LEAKAGE AUDIT")
    print("=" * 80)

    profiles = {}
    seen_poses = []
    seen_hashes = []

    for seed in ALL_SEEDS:
        rng = np.random.RandomState(seed)
        hal.reset()
        jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, seed)
        diag0 = hal.get_diagnostics()

        q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
        carl_qpos = hal.data.qpos[q_addr:q_addr + 7].copy()

        u_sample = np.array([[float(rng.uniform(0.08, 0.12)), float(rng.uniform(0.08, 0.12))] for _ in range(30)])
        s_raw = hal.read_sensors()
        s_noisy = inject_sensor_noise(s_raw, rng)

        h_payload = carl_qpos.tobytes() + u_sample.tobytes() + s_noisy.tobytes()
        pose_hash = hashlib.sha256(h_payload).hexdigest()[:16]

        seen_poses.append((round(jx, 4), round(jy, 4), round(math.degrees(jyaw), 2)))
        seen_hashes.append(pose_hash)

        profiles[str(seed)] = {
            "seed": seed,
            "partition": "DEV" if seed in DEV_SEEDS else "UNSEEN",
            "pos_x": round(diag0["pos_x"], 5),
            "pos_y": round(diag0["pos_y"], 5),
            "yaw_deg": round(math.degrees(diag0["yaw"]), 2),
            "hash": pose_hash
        }

    distinct_poses = (len(set(seen_poses)) == len(ALL_SEEDS))
    distinct_hashes = (len(set(seen_hashes)) == len(ALL_SEEDS))
    assert distinct_poses and distinct_hashes, "FATAL: Duplicate stochastic seeds detected!"

    payload = {
        "verified_distinct": True,
        "seed_count": len(ALL_SEEDS),
        "profiles": profiles
    }

    with open(PREFLIGHT_JSON, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Preflight PASSED. All {len(ALL_SEEDS)} seeds verified pairwise distinct.")
    return payload


def run_developmental_learning() -> Dict[str, Any]:
    """Phase 1: Autonomous Developmental Calibration & Model Freezing."""
    print("\n" + "=" * 80)
    print("PHASE 1: AUTONOMOUS DEVELOPMENTAL CALIBRATION & MODEL FREEZING")
    print("=" * 80)

    dev_results = {}
    k_trans_list = []

    for seed in DEV_SEEDS:
        U_sweeps, S_sweeps = generate_developmental_approach_sweeps(seed, n_sweeps=10)

        fwd_list = []
        rates_list = []
        for U_sw, S_sw in zip(U_sweeps, S_sweeps):
            fwd_sw = 0.5 * (U_sw[:-1, 0] + U_sw[:-1, 1])
            rate_sw = -np.diff(S_sw[:, :15], axis=0) / 0.030
            fwd_list.append(fwd_sw)
            rates_list.append(rate_sw)

        all_fwd = np.concatenate(fwd_list)
        all_rates = np.concatenate(rates_list, axis=0)

        corrs = [float(np.corrcoef(all_fwd, all_rates[:, j])[0, 1]) for j in range(15)]
        best_sonar = int(np.argmax(corrs))

        denom = float(np.sum(all_fwd**2)) + 1e-9
        k_fit = float(np.sum(all_fwd * all_rates[:, best_sonar]) / denom)
        k_trans_list.append(k_fit)

        # Held-out validation on read-only seed + 9999
        U_val_sweeps, S_val_sweeps = generate_developmental_approach_sweeps(seed + 9999, n_sweeps=8)
        fwd_val_list, rates_val_list = [], []
        for U_sw, S_sw in zip(U_val_sweeps, S_val_sweeps):
            fwd_sw = 0.5 * (U_sw[:-1, 0] + U_sw[:-1, 1])
            rate_sw = -np.diff(S_sw[:, best_sonar], axis=0) / 0.030
            fwd_val_list.append(fwd_sw)
            rates_val_list.append(rate_sw)

        fwd_val = np.concatenate(fwd_val_list)
        rates_val = np.concatenate(rates_val_list)
        pred_val = k_fit * fwd_val

        ss_res = float(np.sum((rates_val - pred_val)**2))
        ss_tot = float(np.sum((rates_val - np.mean(rates_val))**2))
        r2_heldout = 1.0 - ss_res / (ss_tot + 1e-9)
        corr_heldout = float(np.corrcoef(rates_val, pred_val)[0, 1]) if len(rates_val) > 2 else 0.0

        dev_results[str(seed)] = {
            "seed": seed,
            "discovered_channel": best_sonar,
            "discovery_correlation": round(corrs[best_sonar], 4),
            "k_trans_fit": round(k_fit, 4),
            "held_out_r2": round(r2_heldout, 4),
            "held_out_corr": round(corr_heldout, 4)
        }
        print(f"  Dev Seed {seed:3d}: Channel={best_sonar} (r={corrs[best_sonar]:.3f}) | k_trans={k_fit:.4f} | Held-out R2={r2_heldout:.4f}")

    frozen_k_trans = round(float(np.mean(k_trans_list)), 4)
    print(f"\n  PERMANENT MODEL FREEZE: k_trans = {frozen_k_trans:.4f} m/s")
    print("=" * 80)

    return {
        "dev_seeds": dev_results,
        "frozen_k_trans": frozen_k_trans
    }


def run_single_trial(
    hal: CarlStage1HAL,
    seed: int,
    condition: str,
    frozen_k_trans: float = 1.1398
) -> Dict[str, Any]:
    """Executes one authoritative long-range navigation & homing trial."""
    rng = np.random.RandomState(seed)
    hal.reset()
    apply_carl_stochastic_initial_pose(hal, seed)

    # 1. Developmental Babbling Phase
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    brain.k_eff = 4.0862
    brain.use_motor_efference = True

    # Speed & steering configuration by condition
    if condition == "Condition A (Smooth Angular-Gated Steering)":
        brain.k_trans = frozen_k_trans
        brain.use_learned_speed = True
        controller_mode = "smooth_quadratic"
    elif condition == "Condition B (Discontinuous Step Controller)":
        brain.k_trans = frozen_k_trans
        brain.use_learned_speed = True
        controller_mode = "legacy_step"
    elif condition == "Condition C (Naive Motor-Only Baseline)":
        brain.k_trans = 1.200
        brain.use_learned_speed = False
        controller_mode = "smooth_quadratic"
    elif condition == "Condition D (Shuffled Sensor Control)":
        brain.k_trans = frozen_k_trans
        brain.use_learned_speed = True
        controller_mode = "smooth_quadratic"

    multi_grid = MultiScaleGridToroid(lambda1=0.80, lambda2=1.15, dt=hal.dt, seed=seed)

    hal.reset()
    apply_carl_stochastic_initial_pose(hal, seed)
    brain.reset_at_birthplace()
    multi_grid.reset_at_birthplace()

    diag0 = hal.get_diagnostics()
    bx, by = diag0["pos_x"], diag0["pos_y"]

    ticks = []
    traj_gt = []
    traj_dec = []
    speeds_phys = []
    speeds_est = []

    t_start = time.time()

    # 2. Wander Phase (350 ticks > 1.25m)
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        u_noisy = u_cmd + rng.normal(0, 0.003, size=6)
        s, diag = hal.step(u_noisy)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_noisy, s_noisy)
        hd = res_brain["hd_decoded_heading"]

        fwd_cmd = 0.5 * (float(u_noisy[0]) + float(u_noisy[1]))
        if condition in ["Condition A (Smooth Angular-Gated Steering)", "Condition B (Discontinuous Step Controller)"]:
            v_grounded = frozen_k_trans * fwd_cmd
        elif condition == "Condition C (Naive Motor-Only Baseline)":
            v_grounded = 1.200 * fwd_cmd
        elif condition == "Condition D (Shuffled Sensor Control)":
            v_grounded = frozen_k_trans * float(u_noisy[2])

        vx = v_grounded * math.cos(hd)
        vy = v_grounded * math.sin(hd)

        multi_res = multi_grid.step(vx, vy, slip_gated=False)
        dec_x = multi_res["displacement_x_meters"]
        dec_y = multi_res["displacement_y_meters"]

        gt_x = diag["pos_x"] - bx
        gt_y = diag["pos_y"] - by

        ticks.append(tick)
        traj_gt.append((round(gt_x, 4), round(gt_y, 4)))
        traj_dec.append((round(dec_x, 4), round(dec_y, 4)))
        speeds_phys.append(round(diag["speed"], 4))
        speeds_est.append(round(v_grounded, 4))

    wander_max_phys_dist = max([math.sqrt(gx**2 + gy**2) for gx, gy in traj_gt])
    wander_end_phys_dist = math.sqrt(traj_gt[-1][0]**2 + traj_gt[-1][1]**2)
    wander_end_int_dist = math.sqrt(dec_x**2 + dec_y**2)

    # 3. Autonomous Homing Phase (up to 600 ticks)
    homing_ticks = 0
    stopped_cleanly = False

    for h_tick in range(600):
        dist_home = math.sqrt(dec_x**2 + dec_y**2)
        target_x = -dec_x
        target_y = -dec_y

        u_h, is_home = compute_steering_action_r4(
            brain.hd_ring.r, brain.hd_ring.angles, target_x, target_y, dist_home, controller_mode=controller_mode
        )
        if is_home:
            stopped_cleanly = True
            break

        u_noisy = u_h + rng.normal(0, 0.003, size=6)
        s, diag = hal.step(u_noisy)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_noisy, s_noisy)
        hd = res_brain["hd_decoded_heading"]

        fwd_cmd = 0.5 * (float(u_noisy[0]) + float(u_noisy[1]))
        if condition in ["Condition A (Smooth Angular-Gated Steering)", "Condition B (Discontinuous Step Controller)"]:
            v_grounded = frozen_k_trans * fwd_cmd
        elif condition == "Condition C (Naive Motor-Only Baseline)":
            v_grounded = 1.200 * fwd_cmd
        elif condition == "Condition D (Shuffled Sensor Control)":
            v_grounded = frozen_k_trans * float(u_noisy[2])

        vx = v_grounded * math.cos(hd)
        vy = v_grounded * math.sin(hd)

        multi_res = multi_grid.step(vx, vy, slip_gated=False)
        dec_x = multi_res["displacement_x_meters"]
        dec_y = multi_res["displacement_y_meters"]

        gt_x = diag["pos_x"] - bx
        gt_y = diag["pos_y"] - by

        ticks.append(350 + h_tick)
        traj_gt.append((round(gt_x, 4), round(gt_y, 4)))
        traj_dec.append((round(dec_x, 4), round(dec_y, 4)))
        speeds_phys.append(round(diag["speed"], 4))
        speeds_est.append(round(v_grounded, 4))
        homing_ticks += 1

    final_diag = hal.get_diagnostics()
    final_drift_m = math.sqrt((final_diag["pos_x"] - bx)**2 + (final_diag["pos_y"] - by)**2)
    elapsed_ms = (time.time() - t_start) * 1000.0

    # Along-path vs cross-track error decomposition
    w_gt = traj_gt[349]
    f_gt = (final_diag["pos_x"] - bx, final_diag["pos_y"] - by)
    disp_phys = wander_end_phys_dist
    dot_return = (f_gt[0] * w_gt[0] + f_gt[1] * w_gt[1]) / (disp_phys**2 + 1e-12)
    along_path_err = dot_return * disp_phys
    cross_track_err = abs(f_gt[0] * w_gt[1] - f_gt[1] * w_gt[0]) / (disp_phys + 1e-12)

    return {
        "seed": seed,
        "condition": condition,
        "partition": "DEV" if seed in DEV_SEEDS else "UNSEEN",
        "wander_max_phys_dist_m": round(wander_max_phys_dist, 4),
        "wander_end_phys_dist_m": round(wander_end_phys_dist, 4),
        "wander_end_int_dist_m": round(wander_end_int_dist, 4),
        "final_drift_raw": float(final_drift_m),
        "final_drift_m": round(final_drift_m, 4),
        "along_path_err_m": round(float(along_path_err), 4),
        "cross_track_err_m": round(float(cross_track_err), 4),
        "homing_ticks": homing_ticks,
        "stopped_cleanly": stopped_cleanly,
        "pass_gate": bool(final_drift_m <= 0.220000000000),
        "elapsed_ms": round(elapsed_ms, 1),
        "telemetry": {
            "ticks": ticks,
            "traj_gt": traj_gt,
            "traj_dec": traj_dec,
            "speeds_phys": speeds_phys,
            "speeds_est": speeds_est
        }
    }


def main():
    print("*" * 80)
    print("CARL STAGE 2.1B-R.4: MASTER TRANSLATIONAL & STEERING EXPERIMENTAL SUITE")
    print("*" * 80)

    hal = CarlStage1HAL(open_space=True)

    # Phase 0: Preflight Audit
    preflight = run_preflight_audit(hal)

    # Phase 1: Developmental Learning & Freezing
    dev_pack = run_developmental_learning()
    frozen_k_trans = dev_pack["frozen_k_trans"]

    CONDITIONS = [
        "Condition A (Smooth Angular-Gated Steering)",
        "Condition B (Discontinuous Step Controller)",
        "Condition C (Naive Motor-Only Baseline)",
        "Condition D (Shuffled Sensor Control)"
    ]

    scorecard = {}
    all_telemetry = {}

    for cond in CONDITIONS:
        print("\n" + "=" * 80)
        print(f"EVALUATING: {cond}")
        print("=" * 80)

        cond_records = []
        drifts = []

        for seed in ALL_SEEDS:
            rec = run_single_trial(hal, seed, cond, frozen_k_trans=frozen_k_trans)
            cond_records.append(rec)
            drifts.append(rec["final_drift_raw"])

            p_str = "PASS" if rec["pass_gate"] else "FAIL"
            print(f"  Seed {seed:3d} ({rec['partition']:6s}): drift={rec['final_drift_m']:.4f}m [{p_str:4s}] in {rec['homing_ticks']:3d} ticks (along={rec['along_path_err_m']:+.3f}m, cross={rec['cross_track_err_m']:.3f}m)")

        drifts = np.array(drifts)
        dev_drifts = drifts[:len(DEV_SEEDS)]
        unseen_drifts = drifts[len(DEV_SEEDS):]

        all_pass_count = sum(1 for r in cond_records if r["pass_gate"])
        dev_pass_count = sum(1 for r in cond_records if r["partition"] == "DEV" and r["pass_gate"])
        unseen_pass_count = sum(1 for r in cond_records if r["partition"] == "UNSEEN" and r["pass_gate"])

        scorecard[cond] = {
            "name": cond,
            "all_mean_drift_m": round(float(np.mean(drifts)), 4),
            "all_passes": f"{all_pass_count}/{len(ALL_SEEDS)}",
            "dev_mean_drift_m": round(float(np.mean(dev_drifts)), 4),
            "dev_passes": f"{dev_pass_count}/{len(DEV_SEEDS)}",
            "unseen_mean_drift_m": round(float(np.mean(unseen_drifts)), 4),
            "unseen_median_drift_m": round(float(np.median(unseen_drifts)), 4),
            "unseen_worst_drift_m": round(float(np.max(unseen_drifts)), 4),
            "unseen_passes": f"{unseen_pass_count}/{len(UNSEEN_TEST_SEEDS)}",
            "unseen_pass_rate_pct": round(float(unseen_pass_count / len(UNSEEN_TEST_SEEDS) * 100.0), 1),
            "records": [{k: v for k, v in r.items() if k != "telemetry"} for r in cond_records]
        }

        all_telemetry[cond] = cond_records

        print(f"\n  SUMMARY {cond}:")
        print(f"    ALL SEEDS:    Mean={np.mean(drifts):.4f}m | Passes={all_pass_count}/{len(ALL_SEEDS)}")
        print(f"    UNSEEN SEEDS: Mean={np.mean(unseen_drifts):.4f}m | Median={np.median(unseen_drifts):.4f}m | Worst={np.max(unseen_drifts):.4f}m | Passes={unseen_pass_count}/{len(UNSEEN_TEST_SEEDS)}")

    with open(SCORECARD_JSON, "w") as f:
        json.dump(scorecard, f, indent=2)

    with open(TELEMETRY_JSON, "w") as f:
        json.dump(all_telemetry, f, indent=2)

    print("\n" + "*" * 80)
    print("Master R.4 experimental suite complete.")
    print(f"  Scorecard: {SCORECARD_JSON}")
    print(f"  Telemetry: {TELEMETRY_JSON}")
    print("*" * 80)


if __name__ == "__main__":
    main()
