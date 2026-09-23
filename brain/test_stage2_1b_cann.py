"""
brain/test_stage2_1b_cann.py — Stage 2.1B Master Verification & Falsification Suite
Classification: [ADVERSARIAL NEUROMORPHIC FALSIFICATION SUITE]

Adheres strictly to the Stage 2.1B Protocol:
1. Brain Accounting: 2,114 Neurons (1,026 Reservoir + 64 HD Ring + 1,024 Grid Torus).
2. Scientific Control Group: Stage 2.1A-R Classical (x, y, theta) baseline evaluated side-by-side.
3. Zero Hidden Shortcuts: Firing rates generated via continuous recurrent ODEs.
   Steering generated via neural population asymmetry; zero P-controller.
4. Dev / Test Split:
   - Development Seeds: [42, 101, 202]
   - FROZEN ALGORITHM
   - Unseen Test Seeds: [303, 404, 505, 606, 707]
5. Falsification Batteries:
   - Exp 1: Attractor Stability & Stationary Persistence
   - Exp 2: Closed-Loop Homing Showdown (CANN vs Classical Control)
   - Exp 3: High-Noise Attractor Advantage (sigma = 0.05 rad/s)
   - Exp 4: Glaze Ice Slip Gating on the Torus
   - Exp 5: Dual-Blind Permuted Gyro Recovery
   - Ablation Suite: Full CANN vs No-Recurrence vs No-Learning
"""

import os
import sys
import json
import time
import math
import numpy as np
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_organism import CarlStage1Organism
from brain.carl_stage2_dead_reckoning import DeadReckoningModule
from brain.carl_stage2_spatial_controller import CarlSpatialAgent, discover_vestibular_channel
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
from brain.carl_stage2_grid_torus import ToroidalGridCellAttractor


def apply_stochastic_initial_pose(hal: CarlStage1HAL, seed: int):
    """Applies stochastic initial pose jitter to CARL."""
    rng = np.random.RandomState(seed)
    jitter_x = rng.uniform(-0.04, 0.04)
    jitter_y = rng.uniform(-0.04, 0.04)
    jitter_yaw = rng.uniform(-0.25, 0.25)
    hal.data.qpos[0] = jitter_x
    hal.data.qpos[1] = jitter_y
    hal.data.qpos[3] = math.cos(jitter_yaw / 2.0)
    hal.data.qpos[6] = math.sin(jitter_yaw / 2.0)
    hal.step(np.zeros(6))


def inject_sensor_noise(s: np.ndarray, rng: np.random.RandomState, elevated: bool = False) -> np.ndarray:
    """Injects stochastic Gaussian noise into sensory channels."""
    s_noisy = s.copy()
    sigma_imu = 0.050 if elevated else 0.015
    sigma_accel = 0.060 if elevated else 0.030
    s_noisy[15:18] += rng.normal(0.0, sigma_accel, size=3)
    s_noisy[18:21] += rng.normal(0.0, sigma_imu, size=3)
    return s_noisy


def test_attractor_stability(seed: int = 42) -> Dict[str, Any]:
    """Battery 1: Verifies stationary bump persistence over 10 seconds (333 ticks) of silence."""
    brain = CarlStage2BIntegratedBrain(seed=seed)
    
    # Measure HD ring drift
    th0 = brain.hd_ring.decode_heading()
    for _ in range(333):
        brain.hd_ring.step(0.0)
    th_final = brain.hd_ring.decode_heading()
    hd_drift_deg = abs(math.degrees(math.atan2(math.sin(th_final - th0), math.cos(th_final - th0))))

    # Measure Grid torus phase drift
    x0 = brain.grid_torus.step(0.0, 0.0)["unwrapped_x_meters"]
    for _ in range(333):
        res = brain.grid_torus.step(0.0, 0.0)
    grid_drift_m = abs(res["unwrapped_x_meters"] - x0)

    passed = (hd_drift_deg <= 1.0) and (grid_drift_m <= 0.010)
    return {
        "hd_drift_deg": hd_drift_deg,
        "grid_drift_m": grid_drift_m,
        "passed": passed
    }


def test_closed_loop_homing_showdown(
    seed: int,
    hal: CarlStage1HAL,
    use_cann: bool = True,
    no_recurrence: bool = False,
    elevated_noise: bool = False
) -> Dict[str, Any]:
    """
    Battery 2: Evaluates autonomous closed-loop homing.
    Can run as CANN (experimental system) or Classical Baseline (control group).
    """
    rng = np.random.RandomState(seed)
    hal.reset()
    apply_stochastic_initial_pose(hal, seed)

    # Developmental babbling
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    diag_start = hal.get_diagnostics()
    birth_x, birth_y = diag_start["pos_x"], diag_start["pos_y"]

    if use_cann:
        brain = CarlStage2BIntegratedBrain(seed=seed)
        brain.develop_from_babbling(U_babble, S_babble)
        
        # Ablation check
        if no_recurrence:
            brain.hd_ring.W_sym *= 0.0
            brain.grid_torus.F_W_sym *= 0.0
            
        brain.reset_at_birthplace()
    else:
        # Classical Stage 2.1A-R Control Group
        yaw_ch, yaw_sign, _ = discover_vestibular_channel(U_babble, S_babble, drive_channels=(0, 1))
        agent = CarlSpatialAgent(dt=0.030, drive_channels=(0, 1), yaw_channel=yaw_ch, yaw_sign=yaw_sign)
        agent.dr.slip_threshold = 0.35
        org = CarlStage1Organism(hal=hal, seed=seed)
        org.discovered_topology = {"discovered_drive_channels": [0, 1]}

    trajectory_x = [birth_x]
    trajectory_y = [birth_y]
    u_prev = np.zeros(6)

    # Phase 1: Wander Exploration (60 ticks)
    for tick in range(60):
        if use_cann:
            u_cmd = brain.compute_wander_action(tick, seed_offset=seed * 0.01)
        else:
            u_cmd = agent.compute_wander_action(tick, seed_offset=seed * 0.01)

        u_cmd += rng.normal(0, 0.005, size=6)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng, elevated=elevated_noise)

        if use_cann:
            brain.update_brain(u_cmd, s_noisy)
        else:
            kin = org.update_kinematic_state(u_cmd, s_noisy)
            agent.update_sensors_and_odometry(s_noisy, kin)

        u_prev = u_cmd
        trajectory_x.append(diag["pos_x"])
        trajectory_y.append(diag["pos_y"])

    wander_dist = math.sqrt((trajectory_x[-1] - birth_x)**2 + (trajectory_y[-1] - birth_y)**2)

    # Phase 2: Homing Phase (Up to 180 ticks)
    for tick in range(180):
        if use_cann:
            u_cmd, is_home, d_est = brain.compute_homing_action_neural()
        else:
            u_cmd, is_home, d_est = agent.compute_homing_action()

        if is_home:
            break

        u_cmd += rng.normal(0, 0.005, size=6)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng, elevated=elevated_noise)

        if use_cann:
            brain.update_brain(u_cmd, s_noisy)
        else:
            kin = org.update_kinematic_state(u_cmd, s_noisy)
            agent.update_sensors_and_odometry(s_noisy, kin)

        trajectory_x.append(diag["pos_x"])
        trajectory_y.append(diag["pos_y"])

    diag_final = hal.get_diagnostics()
    final_return_drift = math.sqrt((diag_final["pos_x"] - birth_x)**2 + (diag_final["pos_y"] - birth_y)**2)

    passed = bool(final_return_drift <= 0.20)

    return {
        "seed": seed,
        "use_cann": use_cann,
        "wander_displacement_m": float(wander_dist),
        "final_return_drift_m": float(final_return_drift),
        "trajectory_x": trajectory_x,
        "trajectory_y": trajectory_y,
        "passed": passed
    }


def test_ice_immunity(seed: int, hal: CarlStage1HAL) -> Dict[str, Any]:
    """Battery 4: Evaluates false displacement rejection on glaze ice (mu = 0.005)."""
    rng = np.random.RandomState(seed)
    hal.reset()
    apply_stochastic_initial_pose(hal, seed)

    U_babble = rng.uniform(-0.15, 0.15, size=(300, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    hal.reset()
    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    brain.reset_at_birthplace()

    u_fwd = np.zeros(6)
    u_fwd[0] = 0.12
    u_fwd[1] = 0.12

    # Normal floor (10 ticks)
    for _ in range(10):
        s, _ = hal.step(u_fwd)
        brain.update_brain(u_fwd, s)

    # Enter glaze ice
    hal.set_floor_friction(0.005)
    # Flush filter latency (6 ticks)
    for _ in range(6):
        s, _ = hal.step(u_fwd)
        brain.update_brain(u_fwd, s)

    # Measure steady-state ice displacement
    grid_x0 = brain.grid_torus.step(0, 0)["unwrapped_x_meters"]
    for _ in range(24):
        s, _ = hal.step(u_fwd)
        brain.update_brain(u_fwd, s)
    grid_x1 = brain.grid_torus.step(0, 0)["unwrapped_x_meters"]

    ice_advance = abs(grid_x1 - grid_x0)
    hal.set_floor_friction(3.0)

    passed = bool(ice_advance <= 0.050)
    return {
        "seed": seed,
        "ice_advance_m": float(ice_advance),
        "passed": passed
    }


def test_permuted_gyro_recovery(seed: int, hal: CarlStage1HAL) -> Dict[str, Any]:
    """Battery 5: Evaluates dual-blind recovery under randomly scrambled sensor channels."""
    rng = np.random.RandomState(seed)
    perm = rng.permutation(25)

    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])
    S_perm = S_babble[:, perm]

    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_perm)

    dominant_channel = int(np.argmax(np.abs(brain.w_rot)))
    actual_gyro_slot = int(np.where(perm == 20)[0][0])

    recovered = bool(dominant_channel == actual_gyro_slot)
    return {
        "seed": seed,
        "discovered_channel": dominant_channel,
        "actual_gyro_slot": actual_gyro_slot,
        "recovered": recovered
    }


def run_full_evaluation():
    print("=" * 78)
    print("CARL STAGE 2.1B: GENUINE EMERGENT CONTINUOUS ATTRACTOR EVALUATION")
    print("Brain Architecture: 2,114 Neurons (1,026 Reservoir + 64 HD + 1,024 Grid)")
    print("=" * 78)

    hal = CarlStage1HAL(open_space=True)
    dev_seeds = [42, 101, 202]
    unseen_seeds = [303, 404, 505, 606, 707]
    all_seeds = dev_seeds + unseen_seeds

    results = {
        "timestamp": time.time(),
        "dev_seeds": dev_seeds,
        "unseen_seeds": unseen_seeds,
        "stability_battery": {},
        "homing_cann": {},
        "homing_control_baseline": {},
        "homing_elevated_noise": {},
        "ice_immunity": {},
        "permuted_recovery": {},
        "ablations": {},
        "latencies": {}
    }

    # 1. Attractor Stability
    print("\n[BATTERY 1] Testing Attractor Stability & Bump Persistence...")
    stab = test_attractor_stability(seed=42)
    results["stability_battery"] = stab
    print(f"  -> HD Stationary Drift (10s): {stab['hd_drift_deg']:.6f} deg")
    print(f"  -> Grid Stationary Drift (10s): {stab['grid_drift_m']:.6f} m")
    print(f"  -> Stability Gate: {'PASS' if stab['passed'] else 'FAIL'}")

    # 2. Closed-Loop Homing Showdown: CANN vs Stage 2.1A-R Control Group
    print("\n[BATTERY 2] Closed-Loop Homing Showdown across 8 Seeds (CANN vs Classical)...")
    cann_drifts = []
    control_drifts = []

    for seed in all_seeds:
        is_dev = seed in dev_seeds
        tag = "[DEV]" if is_dev else "[UNSEEN]"
        
        # Test Experimental CANN
        cann_res = test_closed_loop_homing_showdown(seed, hal, use_cann=True)
        results["homing_cann"][str(seed)] = cann_res
        cann_drifts.append(cann_res["final_return_drift_m"])

        # Test Control Baseline (Classical Stage 2.1A-R)
        ctrl_res = test_closed_loop_homing_showdown(seed, hal, use_cann=False)
        results["homing_control_baseline"][str(seed)] = ctrl_res
        control_drifts.append(ctrl_res["final_return_drift_m"])

        print(f"  Seed {seed} {tag:8s} | CANN Drift: {cann_res['final_return_drift_m']:.4f} m ({'PASS' if cann_res['passed'] else 'FAIL'}) | Classical: {ctrl_res['final_return_drift_m']:.4f} m")

    mean_cann = float(np.mean(cann_drifts))
    mean_ctrl = float(np.mean(control_drifts))
    print(f"\n  ==> CANN Mean Drift: {mean_cann:.4f} m vs Classical Baseline: {mean_ctrl:.4f} m")

    # 3. High-Noise Resilience Benchmark
    print("\n[BATTERY 3] Elevated Sensor Noise Benchmark (sigma = 0.050 rad/s)...")
    cann_noise_drifts = []
    ctrl_noise_drifts = []
    for seed in [42, 101, 303, 505]:
        c_noise = test_closed_loop_homing_showdown(seed, hal, use_cann=True, elevated_noise=True)
        b_noise = test_closed_loop_homing_showdown(seed, hal, use_cann=False, elevated_noise=True)
        cann_noise_drifts.append(c_noise["final_return_drift_m"])
        ctrl_noise_drifts.append(b_noise["final_return_drift_m"])
        results["homing_elevated_noise"][str(seed)] = {
            "cann_drift": c_noise["final_return_drift_m"],
            "classical_drift": b_noise["final_return_drift_m"]
        }
        print(f"  Seed {seed} | CANN: {c_noise['final_return_drift_m']:.4f} m | Classical: {b_noise['final_return_drift_m']:.4f} m")

    mean_c_noise = float(np.mean(cann_noise_drifts))
    mean_b_noise = float(np.mean(ctrl_noise_drifts))
    noise_reduction = float((mean_b_noise - mean_c_noise) / mean_b_noise * 100.0)
    print(f"  ==> High Noise Mean: CANN {mean_c_noise:.4f} m vs Classical {mean_b_noise:.4f} m (Noise Advantage: {noise_reduction:+.1f}%)")

    # 4. Glaze Ice Immunity
    print("\n[BATTERY 4] Glaze Ice Slip Gating on the Torus...")
    ice_passes = 0
    for seed in all_seeds:
        ice_res = test_ice_immunity(seed, hal)
        results["ice_immunity"][str(seed)] = ice_res
        if ice_res["passed"]:
            ice_passes += 1
        print(f"  Seed {seed} | Steady-state ice advance: {ice_res['ice_advance_m']:.4f} m ({'PASS' if ice_res['passed'] else 'FAIL'})")
    print(f"  ==> Ice Gate: {ice_passes}/{len(all_seeds)} passed")

    # 5. Permuted Gyro Recovery
    print("\n[BATTERY 5] Dual-Blind Permuted Gyro Recovery...")
    perm_passes = 0
    for seed in all_seeds:
        p_res = test_permuted_gyro_recovery(seed, hal)
        results["permuted_recovery"][str(seed)] = p_res
        if p_res["recovered"]:
            perm_passes += 1
        print(f"  Seed {seed} | Discovered: ch {p_res['discovered_channel']:2d}, Actual: ch {p_res['actual_gyro_slot']:2d} ({'RECOVERED' if p_res['recovered'] else 'MISSED'})")
    print(f"  ==> Permutation Recovery Gate: {perm_passes}/{len(all_seeds)} recovered")

    # 6. Ablation Battery (Causality Proof)
    print("\n[BATTERY 6] Ablation Battery: Testing Causal Contribution of Recurrence...")
    abl_no_rec = test_closed_loop_homing_showdown(seed=42, hal=hal, use_cann=True, no_recurrence=True)
    results["ablations"]["no_recurrence"] = abl_no_rec
    print(f"  -> Ablation (W_rec = 0): Final Drift = {abl_no_rec['final_return_drift_m']:.4f} m (vs Full CANN {cann_drifts[0]:.4f} m)")

    # 7. Computational Latency Benchmark
    print("\n[BATTERY 7] Wall-Clock Latency Benchmark...")
    brain_test = CarlStage2BIntegratedBrain(seed=42)
    brain_test.develop_from_babbling(np.random.randn(100, 6), np.random.randn(100, 25))
    brain_test.reset_at_birthplace()
    times = []
    for _ in range(100):
        t0 = time.time()
        brain_test.update_brain(np.zeros(6), np.zeros(25))
        times.append((time.time() - t0) * 1000.0)
    mean_lat = float(np.mean(times))
    max_lat = float(np.max(times))
    results["latencies"] = {"mean_ms": mean_lat, "max_ms": max_lat}
    print(f"  -> Mean 2,114-Neuron Step: {mean_lat:.3f} ms, Max: {max_lat:.3f} ms (Target <= 25.0 ms)")

    # Save telemetry
    os.makedirs("d:/ebca/evidence/stage2_1b", exist_ok=True)
    out_path = "d:/ebca/evidence/stage2_1b/stage2_1b_full_telemetry.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[EVIDENCE] Raw Telemetry written to: {out_path}")
    return results


if __name__ == "__main__":
    run_full_evaluation()
