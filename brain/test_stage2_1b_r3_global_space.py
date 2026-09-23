"""
brain/test_stage2_1b_r3_global_space.py — Stage 2.1B-R.3: Global Spatial Representation Benchmark
Classification: [SCIENTIFIC PROTOCOL] Multi-Scale Coprime Grid vs Winding Register vs Causal Controls

Rigorous evaluation of CARL's global spatial representation over distances > 1.25m
across developmental seeds [42, 101, 202] and unseen stochastic test seeds [303, 404, 505, 606, 707].

Constraints:
- Jitter applied strictly to spatial_identity at qposadr=22 (CARL's actual freejoint).
- Frozen efference model (k_eff = 4.0862).
- Zero privileged ground-truth state entering cognitive state.
- Saves raw telemetry for 10 figures and synchronized video.
"""

import os
import sys
import math
import time
import json
import hashlib
import numpy as np

BASE_DIR = "d:/ebca"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import ToroidalGridCellAttractor, MultiScaleGridToroid
from brain.test_stage2_1b_r2_efference import apply_carl_stochastic_initial_pose, inject_sensor_noise
from brain.test_stage2_1b_r1_aliasing_showdown import compute_steering_action

OUTPUT_DIR = os.path.join(BASE_DIR, "evidence", "stage2_1b_r3")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEV_SEEDS = [42, 101, 202]
UNSEEN_SEEDS = [303, 404, 505, 606, 707]
ALL_SEEDS = DEV_SEEDS + UNSEEN_SEEDS


def run_preflight_audit(hal: CarlStage1HAL) -> dict:
    """Preflight proving pairwise distinctness across all 8 seeds."""
    profiles = {}
    for s in ALL_SEEDS:
        hal.reset()
        jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, s)
        diag = hal.get_diagnostics()
        rng = np.random.RandomState(s)
        noise_acc = rng.normal(0.0, 0.02, size=3)
        noise_gyro = rng.normal(0.0, 0.015, size=3)

        profiles[str(s)] = {
            "seed": s,
            "partition": "DEV" if s in DEV_SEEDS else "UNSEEN",
            "pos_x": round(diag["pos_x"], 5),
            "pos_y": round(diag["pos_y"], 5),
            "yaw_deg": round(math.degrees(diag["yaw"]), 2),
            "accel_noise_sample": [round(float(v), 5) for v in noise_acc],
            "gyro_noise_sample": [round(float(v), 5) for v in noise_gyro],
            "hash": hashlib.sha256(f"{s}:{diag['pos_x']}:{diag['pos_y']}:{diag['yaw']}".encode()).hexdigest()[:16]
        }

    # Verify distinctness
    yaws = [p["yaw_deg"] for p in profiles.values()]
    distinct = len(set(yaws)) == len(yaws)
    return {
        "verified_distinct": distinct,
        "seed_count": len(profiles),
        "profiles": profiles
    }


def evaluate_trial(
    seed: int,
    candidate: str,
    hal: CarlStage1HAL,
    v_scale: float = 1.0,
    ablation: str = "none"
) -> dict:
    """
    Evaluates one full episode (developmental babbling -> wander -> homing)
    with detailed per-tick telemetry collection.
    """
    rng = np.random.RandomState(seed)
    hal.reset()
    jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, seed)

    # 1. Developmental Babbling (400 ticks)
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    brain.k_eff = 4.0862
    brain.use_motor_efference = True

    # Multi-Scale Grid or Single Torus
    if ablation == "no_multiscale":
        # Single torus only (0.80m scale)
        multi_grid = None
    else:
        multi_grid = MultiScaleGridToroid(seed=seed, dt=hal.dt, lambda1=0.80, lambda2=1.15)

    hal.reset()
    apply_carl_stochastic_initial_pose(hal, seed)
    brain.reset_at_birthplace()
    if multi_grid is not None:
        multi_grid.reset_at_birthplace()

    d0 = hal.get_diagnostics()
    bx, by, byaw = d0["pos_x"], d0["pos_y"], d0["yaw"]

    # Telemetry streams
    ticks = []
    traj_gt = []
    traj_dec = []
    head_gt = []
    head_dec = []
    phases_mod1 = []
    phases_mod2 = []
    homing_vectors = []
    disambig_residuals = []

    t_start = time.time()

    # 2. Wander Exploration (350 ticks)
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        u_noisy = u_cmd + rng.normal(0, 0.003, size=6)
        s, diag = hal.step(u_noisy)
        s_noisy = inject_sensor_noise(s, rng)

        if ablation == "shuffled_heading":
            s_noisy[brain.drive_channels] = np.roll(s_noisy[brain.drive_channels], 1)

        res_brain = brain.update_brain(u_noisy, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        # Translational velocity
        v_wheel = 0.048 * (float(u_noisy[0]) + float(u_noisy[1])) * 12.5 * v_scale
        v_grounded = v_wheel if not is_slipping else 0.0

        if ablation == "shuffled_spatial":
            current_heading += math.pi / 2.0  # Orthogonal velocity projection

        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)

        if candidate == "Candidate B":
            # Single Torus + Integer Winding Register
            dec_x = res_brain["grid_unwrapped_x"]
            dec_y = res_brain["grid_unwrapped_y"]
            p1_x = res_brain["grid_unwrapped_x"]
            p1_y = res_brain["grid_unwrapped_y"]
            p2_x, p2_y = 0.0, 0.0
            resid = 0.0
        elif ablation == "no_multiscale":
            dec_x = (math.atan2(math.sin(brain.grid_torus.prev_phase_x - brain.birth_grid_phase[0]),
                                math.cos(brain.grid_torus.prev_phase_x - brain.birth_grid_phase[0])) / (2.0 * math.pi)) * 0.80
            dec_y = (math.atan2(math.sin(brain.grid_torus.prev_phase_y - brain.birth_grid_phase[1]),
                                math.cos(brain.grid_torus.prev_phase_y - brain.birth_grid_phase[1])) / (2.0 * math.pi)) * 0.80
            p1_x = brain.grid_torus.prev_phase_x
            p1_y = brain.grid_torus.prev_phase_y
            p2_x, p2_y = 0.0, 0.0
            resid = 0.0
        else:
            multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)
            dec_x = multi_res["displacement_x_meters"]
            dec_y = multi_res["displacement_y_meters"]
            p1_x = multi_grid.mod1.prev_phase_x
            p1_y = multi_grid.mod1.prev_phase_y
            p2_x = multi_grid.mod2.prev_phase_x
            p2_y = multi_grid.mod2.prev_phase_y
            resid = multi_res["disambiguation_residual"]

        gt_x = diag["pos_x"] - bx
        gt_y = diag["pos_y"] - by

        ticks.append(tick)
        traj_gt.append((round(gt_x, 4), round(gt_y, 4)))
        traj_dec.append((round(dec_x, 4), round(dec_y, 4)))
        head_gt.append(round(diag["yaw"], 4))
        head_dec.append(round(current_heading, 4))
        phases_mod1.append((round(p1_x, 4), round(p1_y, 4)))
        phases_mod2.append((round(p2_x, 4), round(p2_y, 4)))
        disambig_residuals.append(round(resid, 5))

    wander_max_phys_dist = max([math.sqrt(gx**2 + gy**2) for gx, gy in traj_gt])

    # 3. Autonomous Homing Phase (up to 600 ticks)
    homing_ticks = 0
    stopped_cleanly = False

    for h_tick in range(600):
        dist_home = math.sqrt(dec_x**2 + dec_y**2)
        target_x = -dec_x
        target_y = -dec_y

        u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, target_x, target_y, dist_home)
        if is_home:
            stopped_cleanly = True
            break

        u_noisy = u_h + rng.normal(0, 0.003, size=6)
        s, diag = hal.step(u_noisy)
        s_noisy = inject_sensor_noise(s, rng)

        if ablation == "shuffled_heading":
            s_noisy[brain.drive_channels] = np.roll(s_noisy[brain.drive_channels], 1)

        res_brain = brain.update_brain(u_noisy, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        v_wheel = 0.048 * (float(u_noisy[0]) + float(u_noisy[1])) * 12.5 * v_scale
        v_grounded = v_wheel if not is_slipping else 0.0

        if ablation == "shuffled_spatial":
            current_heading += math.pi / 2.0

        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)

        if candidate == "Candidate B":
            dec_x = res_brain["grid_unwrapped_x"]
            dec_y = res_brain["grid_unwrapped_y"]
            p1_x = res_brain["grid_unwrapped_x"]
            p1_y = res_brain["grid_unwrapped_y"]
            p2_x, p2_y = 0.0, 0.0
            resid = 0.0
        elif ablation == "no_multiscale":
            dec_x = (math.atan2(math.sin(brain.grid_torus.prev_phase_x - brain.birth_grid_phase[0]),
                                math.cos(brain.grid_torus.prev_phase_x - brain.birth_grid_phase[0])) / (2.0 * math.pi)) * 0.80
            dec_y = (math.atan2(math.sin(brain.grid_torus.prev_phase_y - brain.birth_grid_phase[1]),
                                math.cos(brain.grid_torus.prev_phase_y - brain.birth_grid_phase[1])) / (2.0 * math.pi)) * 0.80
            p1_x = brain.grid_torus.prev_phase_x
            p1_y = brain.grid_torus.prev_phase_y
            p2_x, p2_y = 0.0, 0.0
            resid = 0.0
        else:
            multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)
            dec_x = multi_res["displacement_x_meters"]
            dec_y = multi_res["displacement_y_meters"]
            p1_x = multi_grid.mod1.prev_phase_x
            p1_y = multi_grid.mod1.prev_phase_y
            p2_x = multi_grid.mod2.prev_phase_x
            p2_y = multi_grid.mod2.prev_phase_y
            resid = multi_res["disambiguation_residual"]

        gt_x = diag["pos_x"] - bx
        gt_y = diag["pos_y"] - by

        ticks.append(350 + h_tick)
        traj_gt.append((round(gt_x, 4), round(gt_y, 4)))
        traj_dec.append((round(dec_x, 4), round(dec_y, 4)))
        head_gt.append(round(diag["yaw"], 4))
        head_dec.append(round(current_heading, 4))
        phases_mod1.append((round(p1_x, 4), round(p1_y, 4)))
        phases_mod2.append((round(p2_x, 4), round(p2_y, 4)))
        disambig_residuals.append(round(resid, 5))
        homing_ticks += 1

    final_diag = hal.get_diagnostics()
    final_drift_m = math.sqrt((final_diag["pos_x"] - bx)**2 + (final_diag["pos_y"] - by)**2)
    elapsed_ms = (time.time() - t_start) * 1000.0

    return {
        "seed": seed,
        "candidate": candidate,
        "ablation": ablation,
        "partition": "DEV" if seed in DEV_SEEDS else "UNSEEN",
        "initial_pose": {"x": round(bx, 4), "y": round(by, 4), "yaw_deg": round(math.degrees(byaw), 2)},
        "wander_max_phys_dist_m": round(wander_max_phys_dist, 3),
        "final_drift_m": round(final_drift_m, 3),
        "homing_ticks": homing_ticks,
        "stopped_cleanly": stopped_cleanly,
        "pass_gate": bool(final_drift_m <= 0.22),
        "max_disambig_residual_m": round(max(disambig_residuals), 5),
        "elapsed_ms": round(elapsed_ms, 1),
        "telemetry": {
            "ticks": ticks,
            "traj_gt": traj_gt,
            "traj_dec": traj_dec,
            "head_gt": head_gt,
            "head_dec": head_dec,
            "phases_mod1": phases_mod1,
            "phases_mod2": phases_mod2,
            "residuals": disambig_residuals
        }
    }


def main():
    print("=" * 80)
    print("CARL STAGE 2.1B-R.3: GLOBAL SPATIAL REPRESENTATION MASTER PROTOCOL")
    print("=" * 80)

    hal = CarlStage1HAL(open_space=True)

    # 1. Preflight Seed Independence Audit
    print("\n[PHASE 2 PREFLIGHT] Verifying physical pose independence across 8 seeds...")
    preflight = run_preflight_audit(hal)
    with open(os.path.join(OUTPUT_DIR, "preflight_seed_independence.json"), "w") as f:
        json.dump(preflight, f, indent=2)
    print(f"  Preflight Verified: {preflight['verified_distinct']} (8/8 pairwise distinct poses)")

    # 2. Minimum-Complexity Showdown (Candidate A vs B vs C)
    print("\n[PHASE 4 SHOWDOWN] Evaluating Candidates across DEV and UNSEEN partitions...")
    candidates = [
        ("Candidate A (Multi-Scale Coprime Grid)", "Candidate A", 1.0, "none"),
        ("Candidate B (Integer Winding Register Control)", "Candidate B", 1.0, "none"),
        ("Candidate C (Calibrated Grounded Translation)", "Candidate C", 0.880, "none"),
    ]

    showdown_records = {}
    full_telemetry = {}

    for name, cand_type, v_sc, abl in candidates:
        print(f"\n--- {name} ---")
        cand_results = []
        for s in ALL_SEEDS:
            role = "DEV" if s in DEV_SEEDS else "UNSEEN"
            res = evaluate_trial(s, cand_type, hal, v_scale=v_sc, ablation=abl)
            # Store full telemetry separately to keep ledger compact
            key = f"{cand_type}_{s}"
            full_telemetry[key] = res["telemetry"]
            # Exclude raw timeseries from summary record
            record_summary = {k: v for k, v in res.items() if k != "telemetry"}
            cand_results.append(record_summary)
            status = "PASS" if res["pass_gate"] else "FAIL"
            print(f"  Seed {s:3d} [{role}]: Drift = {res['final_drift_m']:.3f}m | Max Wander = {res['wander_max_phys_dist_m']:.2f}m [{status}] ({res['elapsed_ms']:.0f}ms)")

        drifts = [r["final_drift_m"] for r in cand_results]
        unseen_drifts = [r["final_drift_m"] for r in cand_results if r["partition"] == "UNSEEN"]
        dev_drifts = [r["final_drift_m"] for r in cand_results if r["partition"] == "DEV"]
        passes = sum(1 for r in cand_results if r["pass_gate"])
        unseen_passes = sum(1 for r in cand_results if r["pass_gate"] and r["partition"] == "UNSEEN")

        showdown_records[cand_type] = {
            "name": name,
            "all_seeds_mean_drift_m": round(float(np.mean(drifts)), 3),
            "all_seeds_passes": f"{passes}/8",
            "unseen_mean_drift_m": round(float(np.mean(unseen_drifts)), 3),
            "unseen_median_drift_m": round(float(np.median(unseen_drifts)), 3),
            "unseen_worst_drift_m": round(float(np.max(unseen_drifts)), 3),
            "unseen_passes": f"{unseen_passes}/5",
            "dev_mean_drift_m": round(float(np.mean(dev_drifts)), 3),
            "records": cand_results
        }
        print(f"  -> All: Mean={np.mean(drifts):.3f}m, Passes={passes}/8 | UNSEEN: Mean={np.mean(unseen_drifts):.3f}m, Passes={unseen_passes}/5")

    with open(os.path.join(OUTPUT_DIR, "candidate_showdown.json"), "w") as f:
        json.dump(showdown_records, f, indent=2)

    # 3. Causal Ablation Matrix (Phase 5)
    print("\n[PHASE 5 ABLATIONS] Evaluating Causal Ablation Matrix on Candidate A...")
    ablations = [
        ("Full Representation", "none"),
        ("No Multi-Scale (Single Torus 0.80m)", "no_multiscale"),
        ("Shuffled Spatial Coupling", "shuffled_spatial"),
        ("Shuffled Heading Coupling", "shuffled_heading")
    ]

    ablation_records = {}
    for abl_name, abl_type in ablations:
        print(f"\n--- Ablation: {abl_name} ---")
        abl_results = []
        for s in UNSEEN_SEEDS:
            res = evaluate_trial(s, "Candidate A", hal, v_scale=1.0, ablation=abl_type)
            record_summary = {k: v for k, v in res.items() if k != "telemetry"}
            abl_results.append(record_summary)
            status = "PASS" if res["pass_gate"] else "FAIL"
            print(f"  Unseen Seed {s:3d}: Drift = {res['final_drift_m']:.3f}m [{status}]")

        drifts = [r["final_drift_m"] for r in abl_results]
        ablation_records[abl_type] = {
            "name": abl_name,
            "mean_drift_m": round(float(np.mean(drifts)), 3),
            "median_drift_m": round(float(np.median(drifts)), 3),
            "worst_drift_m": round(float(np.max(drifts)), 3),
            "passes": f"{sum(1 for r in abl_results if r['pass_gate'])}/5",
            "records": abl_results
        }

    with open(os.path.join(OUTPUT_DIR, "causal_ablations.json"), "w") as f:
        json.dump(ablation_records, f, indent=2)

    # 4. Save Full Telemetry
    print("\nSaving full high-resolution telemetry...")
    with open(os.path.join(OUTPUT_DIR, "global_spatial_telemetry.json"), "w") as f:
        json.dump(full_telemetry, f)
    print(f"  Saved {len(full_telemetry)} full episode trajectories to {OUTPUT_DIR}/global_spatial_telemetry.json")

    print("\n" + "=" * 80)
    print("STAGE 2.1B-R.3 BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
