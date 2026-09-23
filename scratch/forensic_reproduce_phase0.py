"""
scratch/forensic_reproduce_phase0.py — Forensic Reproduction of Stage 2.1B-R.1 Task 3
Reproduces Candidate A, Candidate B, and Legacy Control on all 8 seeds:
Seeds: [42, 101, 202, 303, 404, 505, 606, 707]
Captures:
- Initial physical pose
- Initial neural state
- Trajectory length
- Maximum physical displacement
- Maximum decoded displacement
- Phase wraps
- Heading error
- Position error
- Final physical position
- Final internal position
- Final homing command
- Final distance to true birthplace
- Failure phase breakdown (exploration vs update vs homing vs stopping)
"""

import os
import sys
import math
import time
import json
import numpy as np

BASE_DIR = "d:/ebca"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_grid_torus import ToroidalGridCellAttractor, MultiScaleGridToroid
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose, inject_sensor_noise
from brain.test_stage2_1b_r1_aliasing_showdown import compute_steering_action

ALL_SEEDS = [42, 101, 202, 303, 404, 505, 606, 707]
DEV_SEEDS = [42, 101, 202]
UNSEEN_SEEDS = [303, 404, 505, 606, 707]

def run_seed_audit(seed: int, hal: CarlStage1HAL):
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    # Developmental babbling
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    brain.k_eff = 4.0862
    brain.use_motor_efference = True

    multi_grid = MultiScaleGridToroid(seed=seed, dt=hal.dt, lambda1=0.80, lambda2=1.15)

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    brain.reset_at_birthplace()
    multi_grid.reset_at_birthplace()

    diag0 = hal.get_diagnostics()
    birth_x = diag0["pos_x"]
    birth_y = diag0["pos_y"]
    birth_yaw = diag0["yaw"]

    init_neural_hd = float(brain.hd_ring.r.sum())
    init_neural_mod1 = float(multi_grid.mod1.r.sum())
    init_neural_mod2 = float(multi_grid.mod2.r.sum())

    traj_phys = []
    traj_dec = []
    heading_errors = []
    pos_errors = []
    max_phys_dist = 0.0
    max_dec_dist = 0.0

    total_path_length = 0.0
    prev_x, prev_y = birth_x, birth_y

    t0 = time.time()

    # 1. Wander Phase (350 ticks)
    for tick in range(350):
        u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng)

        res_brain = brain.update_brain(u_cmd, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        v_wheel = 0.048 * (float(u_cmd[0]) + float(u_cmd[1])) * 12.5
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)
        multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)

        cur_x, cur_y = diag["pos_x"], diag["pos_y"]
        step_dist = math.sqrt((cur_x - prev_x)**2 + (cur_y - prev_y)**2)
        total_path_length += step_dist
        prev_x, prev_y = cur_x, cur_y

        gt_x = cur_x - birth_x
        gt_y = cur_y - birth_y
        phys_dist = math.sqrt(gt_x**2 + gt_y**2)
        if phys_dist > max_phys_dist:
            max_phys_dist = phys_dist

        dec_x = multi_res["displacement_x_meters"]
        dec_y = multi_res["displacement_y_meters"]
        dec_dist = math.sqrt(dec_x**2 + dec_y**2)
        if dec_dist > max_dec_dist:
            max_dec_dist = dec_dist

        traj_phys.append((gt_x, gt_y))
        traj_dec.append((dec_x, dec_y))

        # Heading error
        gt_yaw = diag["yaw"]
        h_err = abs(math.atan2(math.sin(current_heading - gt_yaw), math.cos(current_heading - gt_yaw)))
        heading_errors.append(h_err)

        # Position error during wander
        p_err = math.sqrt((dec_x - gt_x)**2 + (dec_y - gt_y)**2)
        pos_errors.append(p_err)

    wander_end_phys_dist = phys_dist
    wander_end_pos_err = p_err

    # 2. Homing Return Phase (up to 600 ticks)
    homing_ticks = 0
    stopped_cleanly = False
    last_u_h = np.zeros(6)

    for h_tick in range(600):
        disp_x = multi_res["displacement_x_meters"]
        disp_y = multi_res["displacement_y_meters"]
        dist_home = math.sqrt(disp_x**2 + disp_y**2)

        target_x = -disp_x
        target_y = -disp_y

        u_h, is_home = compute_steering_action(brain.hd_ring.r, brain.hd_ring.angles, target_x, target_y, dist_home)
        last_u_h = u_h.copy()

        if is_home:
            stopped_cleanly = True
            break

        s, diag = hal.step(u_h)
        s_noisy = inject_sensor_noise(s, rng)
        res_brain = brain.update_brain(u_h, s_noisy)
        current_heading = res_brain["hd_decoded_heading"]
        is_slipping = res_brain["is_slipping"]

        v_wheel = 0.048 * (float(u_h[0]) + float(u_h[1])) * 12.5
        v_grounded = v_wheel if not is_slipping else 0.0
        vx = v_grounded * math.cos(current_heading)
        vy = v_grounded * math.sin(current_heading)
        multi_res = multi_grid.step(vx, vy, slip_gated=is_slipping)
        homing_ticks += 1

        cur_x, cur_y = diag["pos_x"], diag["pos_y"]
        step_dist = math.sqrt((cur_x - prev_x)**2 + (cur_y - prev_y)**2)
        total_path_length += step_dist
        prev_x, prev_y = cur_x, cur_y

        gt_x = cur_x - birth_x
        gt_y = cur_y - birth_y
        dec_x = multi_res["displacement_x_meters"]
        dec_y = multi_res["displacement_y_meters"]

        traj_phys.append((gt_x, gt_y))
        traj_dec.append((dec_x, dec_y))

        gt_yaw = diag["yaw"]
        h_err = abs(math.atan2(math.sin(current_heading - gt_yaw), math.cos(current_heading - gt_yaw)))
        heading_errors.append(h_err)
        pos_errors.append(math.sqrt((dec_x - gt_x)**2 + (dec_y - gt_y)**2))

    final_diag = hal.get_diagnostics()
    final_drift_m = math.sqrt((final_diag["pos_x"] - birth_x)**2 + (final_diag["pos_y"] - birth_y)**2)
    final_dec_x = multi_res["displacement_x_meters"]
    final_dec_y = multi_res["displacement_y_meters"]
    final_internal_dist = math.sqrt(final_dec_x**2 + final_dec_y**2)

    # Determine failure phase if drift > 0.22m
    if final_drift_m <= 0.22:
        failure_phase = "NONE (PASSED)"
    else:
        # Check where the discrepancy originated
        if wander_end_pos_err > 0.20:
            failure_phase = "EXPLORATION / INTEGRATION"
        elif not stopped_cleanly:
            failure_phase = "HOMING / TIMEOUT"
        elif final_internal_dist > 0.10:
            failure_phase = "STOPPING / CONVERGENCE"
        else:
            failure_phase = "REPRESENTATION ALIASING / RESIDUAL DRIFT"

    elapsed = time.time() - t0

    return {
        "seed": seed,
        "partition": "DEV" if seed in DEV_SEEDS else "UNSEEN",
        "initial_physical_pose": {
            "x": round(birth_x, 4),
            "y": round(birth_y, 4),
            "yaw_deg": round(math.degrees(birth_yaw), 2)
        },
        "initial_neural_sum": {
            "hd_r": round(init_neural_hd, 4),
            "mod1_r": round(init_neural_mod1, 4),
            "mod2_r": round(init_neural_mod2, 4)
        },
        "total_trajectory_length_m": round(total_path_length, 3),
        "max_physical_disp_m": round(max_phys_dist, 3),
        "max_decoded_disp_m": round(max_dec_dist, 3),
        "mod1_wraps": {"x": multi_grid.mod1.wrap_count_x, "y": multi_grid.mod1.wrap_count_y},
        "mod2_wraps": {"x": multi_grid.mod2.wrap_count_x, "y": multi_grid.mod2.wrap_count_y},
        "mean_heading_error_deg": round(math.degrees(np.mean(heading_errors)), 2),
        "max_heading_error_deg": round(math.degrees(np.max(heading_errors)), 2),
        "wander_end_pos_err_m": round(wander_end_pos_err, 3),
        "final_pos_error_m": round(pos_errors[-1], 3),
        "final_physical_pos": {"x": round(final_diag["pos_x"] - birth_x, 4), "y": round(final_diag["pos_y"] - birth_y, 4)},
        "final_internal_pos": {"x": round(final_dec_x, 4), "y": round(final_dec_y, 4)},
        "final_homing_cmd": [round(float(c), 4) for c in last_u_h[:2]],
        "final_distance_to_birthplace_m": round(final_drift_m, 3),
        "homing_ticks": homing_ticks,
        "stopped_cleanly": stopped_cleanly,
        "failure_phase": failure_phase,
        "pass_gate": bool(final_drift_m <= 0.22),
        "runtime_s": round(elapsed, 1)
    }

def main():
    print("=" * 80)
    print("PHASE 0: FORENSIC REPRODUCTION OF STAGE 2.1B-R.1 TASK 3")
    print("=" * 80)
    hal = CarlStage1HAL(open_space=True)

    records = []
    for s in ALL_SEEDS:
        print(f"Executing Seed {s:3d} ({'DEV' if s in DEV_SEEDS else 'UNSEEN'})...", end="", flush=True)
        rec = run_seed_audit(s, hal)
        records.append(rec)
        status = "PASS" if rec["pass_gate"] else "FAIL"
        print(f" -> Drift: {rec['final_distance_to_birthplace_m']:.3f}m [{status}] ({rec['runtime_s']}s)")

    mean_drift = float(np.mean([r["final_distance_to_birthplace_m"] for r in records]))
    passes = sum(1 for r in records if r["pass_gate"])

    print("\n" + "=" * 80)
    print(f"REPRODUCTION RESULT: Mean Drift = {mean_drift:.3f}m | Passes = {passes}/8")
    print("=" * 80)

    out_file = os.path.join(BASE_DIR, "scratch", "phase0_reproduction_records.json")
    with open(out_file, "w") as f:
        json.dump({
            "mean_drift_m": round(mean_drift, 3),
            "passes": f"{passes}/8",
            "matches_previous_report": bool(passes == 5 and abs(mean_drift - 0.183) < 0.005),
            "records": records
        }, f, indent=2)
    print(f"Saved records to {out_file}")

if __name__ == "__main__":
    main()
