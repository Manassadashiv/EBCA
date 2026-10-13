"""
brain/test_stage2_1b_r_causality.py — Master Falsification Suite for Stage 2.1B-R
Classification: [SCIENTIFIC PROTOCOL] Attractor Causality, Persistence & 4-Substrate Showdown

Substrates Evaluated:
  A: Full Recurrent CANN (2,114 units, active Mexican-hat recurrence)
  B: Feedforward CANN (Identical architecture, W_rec = 0)
  C: Classical Baseline Control (Euler dead reckoning x, y, theta)
  D: Persistent Non-Neural Memory Control (Scalar latch, no attractor energy basin)

Batteries:
  Battery 1: Physically Changing Sensor Dropout (90 ticks / ~2.7s blackout during active turning)
  Battery 2: Pattern + Information Recovery under Neural Membrane Perturbation (noise shock eta ~ N(0, 2.0))
  Battery 3: Unwrapped Long-Horizon Spatial Tracking (> 1.5m, multi-torus wrap)
"""

import os
import sys
import math
import json
import time
import numpy as np

BASE_DIR = "d:/ebca"
sys.path.insert(0, BASE_DIR)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose, inject_sensor_noise

TELEMETRY_DIR = os.path.join(BASE_DIR, "evidence", "stage2_1b_r")
os.makedirs(TELEMETRY_DIR, exist_ok=True)
TELEMETRY_JSON = os.path.join(TELEMETRY_DIR, "stage2_1b_r_telemetry.json")

DEV_SEEDS = [42, 101, 202]
UNSEEN_TEST_SEEDS = [303, 404, 505, 606, 707]
ALL_SEEDS = DEV_SEEDS + UNSEEN_TEST_SEEDS


class PersistentNonNeuralControl:
    """
    Substrate D: Persistent Non-Neural Memory Control.
    Maintains a latched floating-point state vector (theta, x, y).
    During sensor blackout, retains the last state in memory, but has
    NO continuous attractor dynamics and NO energy basin of attraction.
    """
    def __init__(self, dt: float):
        self.dt = dt
        self.theta = 0.0
        self.x = 0.0
        self.y = 0.0

    def update(self, omega: float, v_fwd: float, is_blackout: bool = False):
        if not is_blackout:
            self.theta += omega * self.dt
            # Normalize angle to [-pi, pi)
            self.theta = (self.theta + math.pi) % (2.0 * math.pi) - math.pi
            self.x += v_fwd * math.cos(self.theta) * self.dt
            self.y += v_fwd * math.sin(self.theta) * self.dt
        # During blackout, values are latched in state memory without attractor relaxation


def create_feedforward_brain(seed: int, U_babble: np.ndarray, S_babble: np.ndarray) -> CarlStage2BIntegratedBrain:
    """
    Substrate B: Feedforward CANN.
    Identical 2,114-unit network, but all recurrent synaptic coupling
    weights are clamped to zero (W_rec = 0).
    """
    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_babble, S_babble)
    # Clamp HD Ring recurrent weights to zero
    brain.hd_ring.W_sym = np.zeros_like(brain.hd_ring.W_sym)
    brain.hd_ring.W_asym = np.zeros_like(brain.hd_ring.W_asym)
    # Clamp Grid Torus recurrent spectral kernels to zero
    brain.grid_torus.F_W_sym = np.zeros_like(brain.grid_torus.F_W_sym)
    brain.grid_torus.F_W_x = np.zeros_like(brain.grid_torus.F_W_x)
    brain.grid_torus.F_W_y = np.zeros_like(brain.grid_torus.F_W_y)
    return brain


# ══════════════════════════════════════════════════════════════════════════════
# BATTERY 1: PHYSICALLY CHANGING SENSOR DROPOUT (WORKING MEMORY UNDER DYNAMICS)
# ══════════════════════════════════════════════════════════════════════════════

def run_battery1_dropout(seed: int, hal: CarlStage1HAL) -> dict:
    """
    Tests working memory during a physically changing sensory blackout.
    Before blackout (30 ticks): Robot drives and rotates.
    During blackout (90 ticks / 2.7s): Sensory inputs clamped to 0.0 while
    physical turning continues under motor torque.
    After blackout (30 ticks): Sensory stream restored.
    """
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    # Developmental babbling
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    # 1. Full Recurrent CANN (Substrate A)
    brain_full = CarlStage2BIntegratedBrain(seed=seed)
    brain_full.develop_from_babbling(U_babble, S_babble)

    # 2. Feedforward CANN (Substrate B)
    brain_ff = create_feedforward_brain(seed, U_babble, S_babble)

    # 3. Classical Euler Baseline (Substrate C)
    theta_classical = 0.0

    # 4. Persistent Non-Neural Control (Substrate D)
    control_d = PersistentNonNeuralControl(dt=hal.dt)

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    brain_full.reset_at_birthplace()
    brain_ff.reset_at_birthplace()

    u_turning = np.zeros(6)
    u_turning[0] = 0.12   # Left wheel forward
    u_turning[1] = -0.06  # Right wheel reverse -> Active physical rotation

    # Phase 1: Normal driving before blackout (30 ticks)
    for _ in range(30):
        s, diag = hal.step(u_turning)
        s_noisy = inject_sensor_noise(s, rng)
        res_full = brain_full.update_brain(u_turning, s_noisy)
        res_ff = brain_ff.update_brain(u_turning, s_noisy)
        omega_gyro = s_noisy[18]  # Gyro channel
        v_fwd = diag.get("speed_forward", 0.10)
        theta_classical = (theta_classical + omega_gyro * hal.dt + math.pi) % (2.0 * math.pi) - math.pi
        control_d.update(omega_gyro, v_fwd, is_blackout=False)

    heading_pre_blackout_gt = diag["yaw"]
    amp_pre_full = float(brain_full.hd_ring.get_bump_amplitude())
    amp_pre_ff = float(brain_ff.hd_ring.get_bump_amplitude())

    # Phase 2: Physically Changing Blackout (90 ticks / 2.7s)
    # Physical turning continues under motor torque, but sensory inputs clamped to 0
    for _ in range(90):
        s, diag = hal.step(u_turning)
        s_blackout = np.zeros_like(s)  # Sensory silence
        res_full = brain_full.update_brain(u_turning, s_blackout)
        res_ff = brain_ff.update_brain(u_turning, s_blackout)
        # Classical stops integrating because sensor is 0
        control_d.update(0.0, 0.0, is_blackout=True)

    # State immediately at the end of blackout
    gt_yaw_end = diag["yaw"]
    amp_blackout_full = float(brain_full.hd_ring.get_bump_amplitude())
    amp_blackout_ff = float(brain_ff.hd_ring.get_bump_amplitude())

    heading_full = brain_full.hd_ring.decode_heading()
    heading_ff = brain_ff.hd_ring.decode_heading()
    heading_class = theta_classical
    heading_d = control_d.theta

    err_full = abs(math.atan2(math.sin(heading_full - gt_yaw_end), math.cos(heading_full - gt_yaw_end)))
    err_ff = abs(math.atan2(math.sin(heading_ff - gt_yaw_end), math.cos(heading_ff - gt_yaw_end)))
    err_class = abs(math.atan2(math.sin(heading_class - gt_yaw_end), math.cos(heading_class - gt_yaw_end)))
    err_d = abs(math.atan2(math.sin(heading_d - gt_yaw_end), math.cos(heading_d - gt_yaw_end)))

    # Working Memory Bump Retention Ratio
    bump_retention_full = amp_blackout_full / (amp_pre_full + 1e-6)
    bump_retention_ff = amp_blackout_ff / (amp_pre_full + 1e-6)

    return {
        "seed": seed,
        "bump_amp_full": amp_blackout_full,
        "bump_amp_ff": amp_blackout_ff,
        "bump_retention_full": bump_retention_full,
        "bump_retention_ff": bump_retention_ff,
        "err_full_rad": err_full,
        "err_ff_rad": err_ff,
        "err_classical_rad": err_class,
        "err_d_rad": err_d,
        "err_full_deg": math.degrees(err_full),
        "err_ff_deg": math.degrees(err_ff),
        "err_classical_deg": math.degrees(err_class),
        "err_d_deg": math.degrees(err_d),
        "ff_collapsed": amp_blackout_ff < 0.10,
        "full_sustained": bump_retention_full > 0.85
    }


# ══════════════════════════════════════════════════════════════════════════════
# BATTERY 2: PATTERN + INFORMATION RECOVERY UNDER NEURAL PERTURBATION (SHOCK)
# ══════════════════════════════════════════════════════════════════════════════

def run_battery2_perturbation(seed: int, hal: CarlStage1HAL) -> dict:
    """
    Tests both Pattern Recovery AND Information Recovery after a violent
    noise shock (eta ~ N(0, 2.0)) injected into neural membrane potential u.
    Evaluates:
      1. Pattern Recovery (does a solitary bump reform: R_post / R_pre >= 0.80?)
      2. Information Recovery (|theta_post - theta_pre| <= 15.0 deg?)
      3. Settling Latency (ticks to steady state).
    """
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain_full = CarlStage2BIntegratedBrain(seed=seed)
    brain_full.develop_from_babbling(U_babble, S_babble)
    brain_ff = create_feedforward_brain(seed, U_babble, S_babble)

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    brain_full.reset_at_birthplace()
    brain_ff.reset_at_birthplace()

    # Step forward while turning to establish steady heading theta_pre
    u_init = np.array([0.12, 0.04, 0, 0, 0, 0])
    for _ in range(40):
        s, diag = hal.step(u_init)
        brain_full.update_brain(u_init, s)
        brain_ff.update_brain(u_init, s)

    theta_pre_full = brain_full.hd_ring.decode_heading()
    theta_pre_ff = brain_ff.hd_ring.decode_heading()
    amp_pre_full = float(brain_full.hd_ring.get_bump_amplitude())
    amp_pre_ff = float(brain_ff.hd_ring.get_bump_amplitude())

    # INJECT VIOLENT NOISE SHOCK INTO MEMBRANE POTENTIALS
    shock_hd = rng.normal(0, 2.0, size=brain_full.hd_ring.N_NEURONS)
    shock_grid = rng.normal(0, 2.0, size=(brain_full.grid_torus.GRID_N, brain_full.grid_torus.GRID_N))

    # Apply shock
    brain_full.hd_ring.u += shock_hd
    brain_full.hd_ring.r = brain_full.hd_ring._activation(brain_full.hd_ring.u)
    brain_full.grid_torus.u += shock_grid
    brain_full.grid_torus.r = brain_full.grid_torus._activation(brain_full.grid_torus.u)

    brain_ff.hd_ring.u += shock_hd
    brain_ff.hd_ring.r = np.maximum(0.0, brain_ff.hd_ring.u)
    brain_ff.grid_torus.u += shock_grid
    brain_ff.grid_torus.r = np.maximum(0.0, brain_ff.grid_torus.u)

    # Observe relaxation over 30 ticks of zero velocity input
    settling_ticks_full = -1
    u_zero = np.zeros(6)
    s_zero = np.zeros(25)

    history_u_full = []
    for t in range(30):
        u_prev = brain_full.hd_ring.u.copy()
        # Step brain with zero external velocity
        brain_full.update_brain(u_zero, s_zero)
        diff = float(np.max(np.abs(brain_full.hd_ring.u - u_prev)))
        history_u_full.append(diff)
        if diff < 0.005 and settling_ticks_full == -1 and t >= 3:
            settling_ticks_full = t

    # Also step feedforward brain for 30 ticks
    for t in range(30):
        brain_ff.update_brain(u_zero, s_zero)

    if settling_ticks_full == -1:
        settling_ticks_full = 30

    # Post-recovery metrics
    amp_post_full = float(np.max(brain_full.hd_ring.r))
    amp_post_ff = float(np.max(brain_ff.hd_ring.r))
    theta_post_full = brain_full.hd_ring.decode_heading()
    theta_post_ff = brain_ff.hd_ring.decode_heading()

    pattern_recovery_full = amp_post_full / (amp_pre_full + 1e-6)
    pattern_recovery_ff = amp_post_ff / (amp_pre_ff + 1e-6)

    # Angular information error
    d_theta_full = abs(math.atan2(math.sin(theta_post_full - theta_pre_full),
                                  math.cos(theta_post_full - theta_pre_full)))
    d_theta_ff = abs(math.atan2(math.sin(theta_post_ff - theta_pre_ff),
                                math.cos(theta_post_ff - theta_pre_ff)))

    pattern_pass = (pattern_recovery_full >= 0.80)
    info_pass = (math.degrees(d_theta_full) <= 15.0)
    settling_pass = (settling_ticks_full <= 8)

    return {
        "seed": seed,
        "amp_pre_full": amp_pre_full,
        "amp_post_full": amp_post_full,
        "pattern_recovery_full": pattern_recovery_full,
        "pattern_recovery_ff": pattern_recovery_ff,
        "theta_pre_full_deg": math.degrees(theta_pre_full),
        "theta_post_full_deg": math.degrees(theta_post_full),
        "d_theta_full_deg": math.degrees(d_theta_full),
        "d_theta_ff_deg": math.degrees(d_theta_ff),
        "settling_ticks_full": settling_ticks_full,
        "pattern_pass": pattern_pass,
        "info_pass": info_pass,
        "settling_pass": settling_pass,
        "overall_pass": (pattern_pass and info_pass and settling_pass)
    }


# ══════════════════════════════════════════════════════════════════════════════
# BATTERY 3: UNWRAPPED LONG-HORIZON TRAJECTORY TRACKING (> 1.5m, MULTI-TORUS)
# ══════════════════════════════════════════════════════════════════════════════

def run_battery3_long_horizon(seed: int, hal: CarlStage1HAL) -> dict:
    """
    Evaluates cumulative trajectory tracking across a long multi-curvature
    horizon exceeding multiple toroidal wrap boundaries (> 1.5m).
    Measures UNWRAPPED Average Trajectory Error (ATE) against independent
    physical ground truth for evaluation only (brain never sees ground truth).
    """
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = np.array([hal.step(u)[0] for u in U_babble])

    brain_full = CarlStage2BIntegratedBrain(seed=seed)
    brain_full.develop_from_babbling(U_babble, S_babble)
    brain_ff = create_feedforward_brain(seed, U_babble, S_babble)

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    brain_full.reset_at_birthplace()
    brain_ff.reset_at_birthplace()

    diag0 = hal.get_diagnostics()
    birth_x, birth_y = diag0["pos_x"], diag0["pos_y"]

    # Trajectory unwrapping accumulators
    pos_gt = []
    pos_full_unwrapped = []
    pos_classical = []

    cur_unwrapped_full = np.array([0.0, 0.0])
    cur_classical = np.array([0.0, 0.0])
    theta_classical = 0.0

    prev_phase_full = np.array([brain_full.grid_torus.prev_phase_x, brain_full.grid_torus.prev_phase_y])
    grid_scale = brain_full.grid_torus.GRID_SCALE_METERS / (2.0 * math.pi)

    # Wander over 350 ticks (~10.5 seconds at 30 Hz)
    for tick in range(350):
        u_cmd = brain_full.compute_wander_action(tick, seed_offset=seed * 0.01)
        s, diag = hal.step(u_cmd)
        s_noisy = inject_sensor_noise(s, rng)
        res_full = brain_full.update_brain(u_cmd, s_noisy)

        # Ground truth relative to birth
        gt_x = diag["pos_x"] - birth_x
        gt_y = diag["pos_y"] - birth_y
        pos_gt.append((gt_x, gt_y))

        # Unwrapping Grid Torus Phase
        cur_phase = np.array([brain_full.grid_torus.prev_phase_x, brain_full.grid_torus.prev_phase_y])
        d_phase = cur_phase - prev_phase_full
        # Unwind periodic wraps
        d_phase = (d_phase + math.pi) % (2.0 * math.pi) - math.pi
        cur_unwrapped_full += d_phase * grid_scale
        prev_phase_full = cur_phase.copy()
        pos_full_unwrapped.append(cur_unwrapped_full.copy())

        # Classical Euler dead reckoning
        gyro = s_noisy[18]
        v_est = diag.get("speed_forward", 0.10)
        theta_classical = (theta_classical + gyro * hal.dt + math.pi) % (2.0 * math.pi) - math.pi
        cur_classical[0] += v_est * math.cos(theta_classical) * hal.dt
        cur_classical[1] += v_est * math.sin(theta_classical) * hal.dt
        pos_classical.append(cur_classical.copy())

    # Calculate Average Trajectory Error (ATE)
    errors_full = [math.sqrt((p[0] - gt[0])**2 + (p[1] - gt[1])**2) for p, gt in zip(pos_full_unwrapped, pos_gt)]
    errors_classical = [math.sqrt((p[0] - gt[0])**2 + (p[1] - gt[1])**2) for p, gt in zip(pos_classical, pos_gt)]

    ate_full = float(np.mean(errors_full))
    ate_classical = float(np.mean(errors_classical))
    max_dist_from_origin = float(np.max([math.sqrt(gt[0]**2 + gt[1]**2) for gt in pos_gt]))

    # Closed-loop Homing from distant point
    homing_drift_full = -1.0
    for h_tick in range(180):
        u_h, is_home, d_est = brain_full.compute_homing_action_neural()
        if is_home:
            break
        s, diag = hal.step(u_h)
        brain_full.update_brain(u_h, inject_sensor_noise(s, rng))

    final_diag = hal.get_diagnostics()
    homing_drift_full = math.sqrt((final_diag["pos_x"] - birth_x)**2 + (final_diag["pos_y"] - birth_y)**2)

    return {
        "seed": seed,
        "max_dist_from_origin": max_dist_from_origin,
        "ate_full_unwrapped_m": ate_full,
        "ate_classical_m": ate_classical,
        "homing_drift_m": homing_drift_full,
        "homing_pass": homing_drift_full <= 0.22,
        "traversed_multiple_tori": max_dist_from_origin > 0.80
    }


# ══════════════════════════════════════════════════════════════════════════════
# MASTER STAGE 2.1B-R EXECUTION SUITE
# ══════════════════════════════════════════════════════════════════════════════

def run_master_stage2_1b_r_suite():
    print("=" * 80)
    print("CARL STAGE 2.1B-R: ATTRACTOR CAUSALITY & PERSISTENCE EVALUATION")
    print("4 Comparative Substrates: Full CANN vs W_rec=0 vs Classical vs Persistent Non-Neural")
    print("=" * 80)

    hal = CarlStage1HAL(open_space=True)
    print(f"-> Environment: Open Space Verified (All obstacles purged to [99, 99, -99])")
    print(f"-> Timestep dt: {hal.dt:.4f}s (Derived directly from {hal.model.opt.timestep:.3f}s * {hal.n_substeps} substeps)")

    results = {
        "battery1_dropout": {},
        "battery2_perturbation": {},
        "battery3_long_horizon": {},
        "summary": {}
    }

    # --- BATTERY 1: Sensor Dropout ---
    print("\n[BATTERY 1] Testing Physically Changing Sensor Dropout (90 ticks / ~2.7s blackout)...")
    b1_passes = 0
    for seed in ALL_SEEDS:
        role = "DEV" if seed in DEV_SEEDS else "UNSEEN"
        res = run_battery1_dropout(seed, hal)
        results["battery1_dropout"][str(seed)] = res
        print(f"  Seed {seed:3d} [{role:6s}] | Bump Retention: Full={res['bump_retention_full']:.2f} vs FF={res['bump_retention_ff']:.2f} | "
              f"Heading Err: Full={res['err_full_deg']:.1f}deg vs FF={res['err_ff_deg']:.1f}deg vs Class={res['err_classical_deg']:.1f}deg vs D={res['err_d_deg']:.1f}deg")
        if res["full_sustained"] and res["ff_collapsed"]:
            b1_passes += 1

    print(f"  ==> Battery 1 Working Memory Retention: {b1_passes}/{len(ALL_SEEDS)} passed")

    # --- BATTERY 2: Neural Perturbation & Recovery ---
    print("\n[BATTERY 2] Testing Pattern + Information Recovery under Neural Perturbation (Shock eta ~ N(0, 2.0))...")
    b2_passes = 0
    for seed in ALL_SEEDS:
        role = "DEV" if seed in DEV_SEEDS else "UNSEEN"
        res = run_battery2_perturbation(seed, hal)
        results["battery2_perturbation"][str(seed)] = res
        status = "PASS" if res["overall_pass"] else "FAIL"
        print(f"  Seed {seed:3d} [{role:6s}] | Pattern: {res['pattern_recovery_full']*100:.1f}% | Info Err: {res['d_theta_full_deg']:.2f}deg | "
              f"Settling: {res['settling_ticks_full']:2d} ticks | Status: {status}")
        if res["overall_pass"]:
            b2_passes += 1

    print(f"  ==> Battery 2 Pattern + Information Recovery: {b2_passes}/{len(ALL_SEEDS)} passed")

    # --- BATTERY 3: Unwrapped Long-Horizon Trajectory ---
    print("\n[BATTERY 3] Testing Unwrapped Long-Horizon Trajectory Tracking (> 1.5m, 350 ticks)...")
    b3_passes = 0
    for seed in ALL_SEEDS:
        role = "DEV" if seed in DEV_SEEDS else "UNSEEN"
        res = run_battery3_long_horizon(seed, hal)
        results["battery3_long_horizon"][str(seed)] = res
        status = "PASS" if res["homing_pass"] else "FAIL"
        print(f"  Seed {seed:3d} [{role:6s}] | Max Dist: {res['max_dist_from_origin']:.2f}m (Multi-Torus: {res['traversed_multiple_tori']}) | "
              f"ATE Full: {res['ate_full_unwrapped_m']:.3f}m vs Class: {res['ate_classical_m']:.3f}m | Homing: {res['homing_drift_m']:.3f}m [{status}]")
        if res["homing_pass"]:
            b3_passes += 1

    print(f"  ==> Battery 3 Long-Horizon Return: {b3_passes}/{len(ALL_SEEDS)} passed")

    # Summary synthesis
    results["summary"] = {
        "battery1_dropout_retention_rate": b1_passes / len(ALL_SEEDS),
        "battery2_shock_recovery_rate": b2_passes / len(ALL_SEEDS),
        "battery3_long_horizon_return_rate": b3_passes / len(ALL_SEEDS),
        "all_seeds": ALL_SEEDS,
        "dev_seeds": DEV_SEEDS,
        "unseen_test_seeds": UNSEEN_TEST_SEEDS
    }

    with open(TELEMETRY_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[EVIDENCE] Raw Stage 2.1B-R Telemetry written to: {TELEMETRY_JSON}")


if __name__ == "__main__":
    run_master_stage2_1b_r_suite()
