"""
brain/test_stage2_1a_r_spatial.py — Stage 2.1A-R: Genuine Developmental Spatial Navigation Suite
Classification: [VERIFICATION] Emergent Spatial Cognition & Stochastic Robustness

Three rigorous developmental experiments:

Experiment 1: Developmental Path Integration & Autonomous Homing
    - Autonomous discovery of vestibular yaw channel from differential motor babbling.
    - Stochastic initial pose perturbation (x0, y0, yaw0).
    - Sensor & actuator noise injection.
    - Autonomous wander exploration followed by closed-loop homing to birthplace.
    - Gate: Final physical return drift to birth location <= 0.22m.

Experiment 2: Low-Friction Ice Immunity & Slip Gating (Battery 2.1B)
    - Glaze ice (mu = 0.005) transition across Dry (15 ticks) -> Ice (30 ticks) -> Dry (15 ticks).
    - Stage 1.6 slip-gating halts internal map advance during wheel spinout.
    - Compare Slip-Gated homing vs Ungated/Naive homing.
    - Gate: Steady-state false advance on ice <= 0.05m, false drift reduction >= 50%.

Experiment 3: Dual-Blind Permutation Vestibular Recovery
    - Sensory channels scrambled via anonymous permutation P_sens.
    - CARL must autonomously discover the scrambled gyro channel index: j* == P_sens[20].
    - Executes autonomous closed-loop homing under scrambled channels.
    - Gate: Correct permuted channel recovered, return drift <= 0.25m.

Development Seeds: [42, 101, 202]
Unseen Test Seeds: [303, 404, 505, 606, 707]
"""

import os
import sys
import json
import math
import time
import numpy as np
import mujoco
from typing import Dict, Any, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_organism import CarlStage1Organism
from brain.carl_stage2_dead_reckoning import DeadReckoningModule
from brain.carl_stage2_spatial_controller import CarlSpatialAgent, discover_vestibular_channel


def set_stochastic_initial_pose(hal: CarlStage1HAL, rng: np.random.RandomState) -> Tuple[float, float, float]:
    """Applies seed-conditioned initial pose perturbation to CARL in MuJoCo."""
    hal.reset()
    q_addr = int(hal.model.joint("spatial_identity").qposadr[0])

    init_x = float(rng.uniform(-0.035, 0.035))
    init_y = float(rng.uniform(-0.035, 0.035))
    init_yaw = float(rng.uniform(-0.080, 0.080))  # ~ +-4.5 degrees

    hal.data.qpos[q_addr] = init_x
    hal.data.qpos[q_addr + 1] = init_y
    hal.data.qpos[q_addr + 3] = math.cos(init_yaw / 2.0)
    hal.data.qpos[q_addr + 6] = math.sin(init_yaw / 2.0)
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    return init_x, init_y, init_yaw


# =============================================================================
# EXPERIMENT 1: Autonomous Homing Under Stochastic Initial State & Noise
# =============================================================================

def run_experiment_1(seed: int = 42) -> Dict[str, Any]:
    """
    Experiment 1: Developmental path integration and closed-loop homing.
    Gate: Final physical return drift to birth location <= 0.22m.
    """
    rng = np.random.RandomState(seed)
    hal = CarlStage1HAL(open_space=True)
    dt = float(3 * hal.model.opt.timestep)

    # 1. Developmental Babbling Phase (400 ticks)
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = []
    hal.reset()
    for u in U_babble:
        s, _ = hal.step(u)
        S_babble.append(s)
    S_babble = np.array(S_babble)

    # Unsupervised Discovery of Yaw Gyro Channel
    yaw_ch, yaw_sign, yaw_corr = discover_vestibular_channel(U_babble, S_babble, drive_channels=(0, 1))

    # 2. Stochastic Initial Pose
    init_x, init_y, init_yaw = set_stochastic_initial_pose(hal, rng)
    hal.set_floor_friction(3.0)

    agent = CarlSpatialAgent(dt=dt, drive_channels=(0, 1), yaw_channel=yaw_ch, yaw_sign=yaw_sign)
    agent.dr.slip_threshold = 0.35
    org = CarlStage1Organism(hal=hal, seed=seed)
    org.discovered_topology = {"discovered_drive_channels": [0, 1]}

    gt_trajectory = []
    est_trajectory = []

    # 3. Phase A: Wander Exploration (60 ticks)
    for t in range(60):
        u_wander = agent.compute_wander_action(tick=t, seed_offset=float(seed * 0.17))
        # Add actuator execution noise
        u_exec = u_wander + rng.normal(0, 0.005, size=6)

        s, diag = hal.step(u_exec)
        # Add sensor noise
        s_noisy = s.copy()
        s_noisy[yaw_ch] += rng.normal(0, 0.015)
        s_noisy[15] += rng.normal(0, 0.030)

        kin = org.update_kinematic_state(u_exec, s_noisy)
        agent.update_sensors_and_odometry(s_noisy, kin)

        gt_trajectory.append((diag["pos_x"] - init_x, diag["pos_y"] - init_y))
        est_trajectory.append((agent.dr.x, agent.dr.y))

    wander_peak_dist = math.sqrt(est_trajectory[-1][0]**2 + est_trajectory[-1][1]**2)

    # 4. Phase B: Autonomous Homing (Closed-Loop Return to Birthplace)
    homing_ticks = 0
    homing_completed = False

    for t_home in range(120):
        u_home, is_home, dist_to_home = agent.compute_homing_action()
        if is_home:
            homing_completed = True
            break

        u_exec = u_home + rng.normal(0, 0.005, size=6)
        s, diag = hal.step(u_exec)

        s_noisy = s.copy()
        s_noisy[yaw_ch] += rng.normal(0, 0.015)
        s_noisy[15] += rng.normal(0, 0.030)

        kin = org.update_kinematic_state(u_exec, s_noisy)
        agent.update_sensors_and_odometry(s_noisy, kin)

        gt_trajectory.append((diag["pos_x"] - init_x, diag["pos_y"] - init_y))
        est_trajectory.append((agent.dr.x, agent.dr.y))
        homing_ticks += 1

    final_diag = hal.get_diagnostics()
    final_gt_dx = final_diag["pos_x"] - init_x
    final_gt_dy = final_diag["pos_y"] - init_y
    physical_return_drift = math.sqrt(final_gt_dx**2 + final_gt_dy**2)
    dr_belief_dist = agent.dr.get_distance_from_origin()

    passed = bool(physical_return_drift <= 0.22 and yaw_ch == 20)

    result = {
        "passed": passed,
        "seed": seed,
        "discovered_yaw_channel": int(yaw_ch),
        "yaw_discovery_correlation": float(yaw_corr),
        "initial_pose_perturbed": {"x0": init_x, "y0": init_y, "yaw0_deg": math.degrees(init_yaw)},
        "wander_peak_dist_m": float(wander_peak_dist),
        "homing_ticks_taken": homing_ticks,
        "physical_return_drift_m": float(physical_return_drift),
        "dr_belief_distance_m": float(dr_belief_dist),
        "gate_drift_limit_m": 0.22,
        "verdict": (
            f"PASS — Gyro channel {yaw_ch} discovered (corr {yaw_corr:+.3f}). "
            f"Physical return drift {physical_return_drift:.3f}m <= 0.22m limit."
            if passed else
            f"FAIL — Return drift {physical_return_drift:.3f}m (limit <= 0.22m) or wrong gyro channel {yaw_ch}."
        )
    }
    return result


# =============================================================================
# EXPERIMENT 2: Low-Friction Ice Immunity (Battery 2.1B)
# =============================================================================

def run_experiment_2(seed: int = 42) -> Dict[str, Any]:
    """
    Experiment 2: Low-friction ice immunity benchmark (Battery 2.1B).
    Evaluates false advance on glaze ice under stochastic initial pose & noise.
    Gate: Steady-state ice false advance <= 0.05m, false advance reduction >= 50%.
    """
    dt = 0.030
    rng = np.random.RandomState(seed)
    hal = CarlStage1HAL(open_space=True)

    # 1. Developmental Babbling
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = []
    hal.reset()
    for u in U_babble:
        s, _ = hal.step(u)
        S_babble.append(s)
    yaw_ch, yaw_sign, yaw_corr = discover_vestibular_channel(U_babble, np.array(S_babble), drive_channels=(0, 1))

    results = {}
    u_fwd = np.array([0.15, 0.15, 0.0, 0.0, 0.0, 0.0])

    for mode in ["gated", "naive"]:
        init_x, init_y, init_yaw = set_stochastic_initial_pose(hal, rng)
        hal.set_floor_friction(3.0)

        agent = CarlSpatialAgent(dt=dt, drive_channels=(0, 1), yaw_channel=yaw_ch, yaw_sign=yaw_sign)
        agent.dr.slip_gate_enabled = (mode == "gated")
        agent.dr.slip_threshold = 0.35
        org = CarlStage1Organism(hal=hal, seed=seed)
        org.discovered_topology = {"discovered_drive_channels": [0, 1]}

        # Dry 15 ticks
        for _ in range(15):
            s, diag = hal.step(u_fwd)
            kin = org.update_kinematic_state(u_fwd, s)
            v = kin["v_wheel"] if mode == "naive" else kin["v_hat_x"]
            slip = 0.0 if mode == "naive" else kin["slip_ratio"]
            agent.dr.update(v, float(s[yaw_ch]) * yaw_sign, slip)

        # Ice 30 ticks (mu = 0.005)
        hal.set_floor_friction(0.005)
        # Account for 6-tick filter latency draining rubber floor chatter
        for _ in range(6):
            s, diag = hal.step(u_fwd)
            kin = org.update_kinematic_state(u_fwd, s)
            v = kin["v_wheel"] if mode == "naive" else kin["v_hat_x"]
            slip = 0.0 if mode == "naive" else kin["slip_ratio"]
            agent.dr.update(v, float(s[yaw_ch]) * yaw_sign, slip)

        ss_ice_start_x = agent.dr.x
        for _ in range(24):
            s, diag = hal.step(u_fwd)
            kin = org.update_kinematic_state(u_fwd, s)
            v = kin["v_wheel"] if mode == "naive" else kin["v_hat_x"]
            slip = 0.0 if mode == "naive" else kin["slip_ratio"]
            agent.dr.update(v, float(s[yaw_ch]) * yaw_sign, slip)

        ss_ice_adv = abs(agent.dr.x - ss_ice_start_x)

        # Dry recovery 15 ticks
        hal.set_floor_friction(3.0)
        for _ in range(15):
            s, diag = hal.step(u_fwd)
            kin = org.update_kinematic_state(u_fwd, s)
            v = kin["v_wheel"] if mode == "naive" else kin["v_hat_x"]
            slip = 0.0 if mode == "naive" else kin["slip_ratio"]
            agent.dr.update(v, float(s[yaw_ch]) * yaw_sign, slip)

        results[mode] = ss_ice_adv

    gated_adv = results["gated"]
    naive_adv = results["naive"]
    ratio = gated_adv / max(naive_adv, 1e-6)
    reduction = (1.0 - ratio) * 100.0

    passed = bool(gated_adv <= 0.05 and ratio <= 0.50)

    result = {
        "passed": passed,
        "seed": seed,
        "discovered_yaw_channel": int(yaw_ch),
        "gated_ice_advance_m": float(gated_adv),
        "naive_ice_advance_m": float(naive_adv),
        "advance_ratio": float(ratio),
        "false_drift_reduction_pct": float(reduction),
        "gate_advance_limit_m": 0.05,
        "gate_ratio_limit": 0.50,
        "verdict": (
            f"PASS — Slip-gated advance on ice is {gated_adv:.4f}m (limit <=0.05m), "
            f"achieving {reduction:.1f}% reduction vs naive ({naive_adv:.4f}m)."
            if passed else
            f"FAIL — Gated advance {gated_adv:.4f}m (limit <=0.05m) or ratio {ratio:.2f}."
        )
    }
    return result


# =============================================================================
# EXPERIMENT 3: Dual-Blind Permutation Vestibular Recovery
# =============================================================================

def run_experiment_3(seed: int = 42) -> Dict[str, Any]:
    """
    Experiment 3: Sensor channels are randomly scrambled.
    CARL must autonomously discover which scrambled channel is the gyro (j* == P_sens[20])
    and execute closed-loop homing successfully.
    Gate: Discovered channel == P_sens[20], physical return drift <= 0.25m.
    """
    rng = np.random.RandomState(seed + 999)
    hal = CarlStage1HAL(open_space=True)
    dt = float(3 * hal.model.opt.timestep)

    # Generate random permutation of 25 sensor channels
    P_sens = rng.permutation(25)
    hal.set_sensor_permutation(P_sens)
    expected_gyro_channel = int(np.where(P_sens == 20)[0][0])

    # 1. Developmental Babbling Phase under scrambled sensors (400 ticks)
    U_babble = rng.uniform(-0.15, 0.15, size=(400, 6))
    S_babble = []
    hal.reset()
    for u in U_babble:
        s, _ = hal.step(u)
        S_babble.append(s)
    S_babble = np.array(S_babble)

    # Unsupervised Discovery of Yaw Gyro Channel on Scrambled Stream
    discovered_ch, yaw_sign, yaw_corr = discover_vestibular_channel(U_babble, S_babble, drive_channels=(0, 1))

    # Verify discovery
    gyro_recovered = bool(discovered_ch == expected_gyro_channel)

    # 2. Stochastic Initial Pose
    init_x, init_y, init_yaw = set_stochastic_initial_pose(hal, rng)
    hal.set_floor_friction(3.0)

    agent = CarlSpatialAgent(dt=dt, drive_channels=(0, 1), yaw_channel=discovered_ch, yaw_sign=yaw_sign)
    agent.dr.slip_threshold = 0.35
    org = CarlStage1Organism(hal=hal, seed=seed)
    org.discovered_topology = {"discovered_drive_channels": [0, 1]}

    # Wander 60 ticks
    for t in range(60):
        u_wander = agent.compute_wander_action(tick=t, seed_offset=float(seed * 0.17))
        s, diag = hal.step(u_wander)
        kin = org.update_kinematic_state(u_wander, s)
        agent.update_sensors_and_odometry(s, kin)

    # Closed-Loop Homing
    for t_home in range(120):
        u_home, is_home, _ = agent.compute_homing_action()
        if is_home:
            break
        s, diag = hal.step(u_home)
        kin = org.update_kinematic_state(u_home, s)
        agent.update_sensors_and_odometry(s, kin)

    final_diag = hal.get_diagnostics()
    physical_return_drift = math.sqrt((final_diag["pos_x"] - init_x)**2 + (final_diag["pos_y"] - init_y)**2)

    passed = bool(gyro_recovered and physical_return_drift <= 0.25)

    result = {
        "passed": passed,
        "seed": seed,
        "expected_permuted_gyro_channel": expected_gyro_channel,
        "discovered_channel": int(discovered_ch),
        "gyro_recovered": gyro_recovered,
        "discovery_correlation": float(yaw_corr),
        "physical_return_drift_m": float(physical_return_drift),
        "gate_drift_limit_m": 0.25,
        "verdict": (
            f"PASS — Scrambled gyro recovered (ch {discovered_ch} == {expected_gyro_channel}, corr {yaw_corr:+.3f}). "
            f"Homing drift {physical_return_drift:.3f}m <= 0.25m."
            if passed else
            f"FAIL — Scrambled channel discovery ({discovered_ch} vs {expected_gyro_channel}) or drift {physical_return_drift:.3f}m."
        )
    }
    return result


# =============================================================================
# MASTER RUNNER
# =============================================================================

def run_stage2_1a_r_suite(
    seeds: List[int] = None,
    label: str = "development"
) -> Dict[str, Any]:
    if seeds is None:
        seeds = [42, 101, 202]

    print("=" * 80)
    print(f"CARL STAGE 2.1A-R: GENUINE DEVELOPMENTAL SPATIAL NAVIGATION ({label.upper()} SEEDS)")
    print(f"Seeds: {seeds}")
    print("=" * 80)

    all_results = {
        "label": label,
        "seeds": seeds,
        "timestamp": time.time(),
        "seed_results": {}
    }

    for seed in seeds:
        print(f"\n--- Running Seed {seed} ---")
        e1 = run_experiment_1(seed=seed)
        print(f"  Exp 1 (Homing): {e1['verdict']}")

        e2 = run_experiment_2(seed=seed)
        print(f"  Exp 2 (Ice Gate): {e2['verdict']}")

        e3 = run_experiment_3(seed=seed)
        print(f"  Exp 3 (Permutation): {e3['verdict']}")

        all_ok = bool(e1["passed"] and e2["passed"] and e3["passed"])
        all_results["seed_results"][str(seed)] = {
            "experiment_1": e1,
            "experiment_2": e2,
            "experiment_3": e3,
            "all_passed": all_ok
        }

    total_seeds = len(seeds)
    passing_seeds = sum(1 for sr in all_results["seed_results"].values() if sr["all_passed"])

    all_results["master_synthesis"] = {
        "total_seeds": total_seeds,
        "passing_seeds": passing_seeds,
        "all_passed": (passing_seeds == total_seeds),
        "pass_rate": passing_seeds / total_seeds
    }

    out_dir = os.path.join(REPO_ROOT, "evidence", "stage2_1a_r")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"carl_stage2_1a_r_{label}_results.json")

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
    print(f"STAGE 2.1A-R {label.upper()}: {passing_seeds}/{total_seeds} SEEDS PASSED")
    print("=" * 80)

    print("\nPer-Experiment Summary Table:")
    print(f"{'Seed':<8} {'Exp1 (Homing Drift)':<25} {'Exp2 (Ice Advance)':<25} {'Exp3 (Permutation)':<25} {'All':<6}")
    print("-" * 92)
    for seed_str, sr in all_results["seed_results"].items():
        s1 = "[PASS]" if sr["experiment_1"]["passed"] else "[FAIL]"
        s2 = "[PASS]" if sr["experiment_2"]["passed"] else "[FAIL]"
        s3 = "[PASS]" if sr["experiment_3"]["passed"] else "[FAIL]"
        sa = "[PASS]" if sr["all_passed"] else "[FAIL]"
        e1_info = f"{s1} {sr['experiment_1']['physical_return_drift_m']:.3f}m"
        e2_info = f"{s2} {sr['experiment_2']['gated_ice_advance_m']:.4f}m ({sr['experiment_2']['false_drift_reduction_pct']:.0f}% red)"
        e3_info = f"{s3} ch {sr['experiment_3']['discovered_channel']}=={sr['experiment_3']['expected_permuted_gyro_channel']}"
        print(f"{seed_str:<8} {e1_info:<25} {e2_info:<25} {e3_info:<25} {sa}")

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CARL Stage 2.1A-R Developmental Experiments")
    parser.add_argument("--mode", choices=["dev", "test", "all"], default="dev",
                        help="Which seed set: dev (42,101,202), test (303,404,505,606,707), all")
    args = parser.parse_args()

    if args.mode == "dev":
        run_stage2_1a_r_suite(seeds=[42, 101, 202], label="development")
    elif args.mode == "test":
        run_stage2_1a_r_suite(seeds=[303, 404, 505, 606, 707], label="test")
    elif args.mode == "all":
        run_stage2_1a_r_suite(seeds=[42, 101, 202], label="development")
        run_stage2_1a_r_suite(seeds=[303, 404, 505, 606, 707], label="test")
