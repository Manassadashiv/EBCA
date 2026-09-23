"""
tests/test_stage3_1R_cann_causal_battery.py — Stage 3.1-R Frozen 2,114-Unit CANN Causal Coupling Battery
Classification: [STAGE 3.1-R REMEDIATION EXECUTION] Controlled Experimental Evaluation across 2,114 Units

Evaluates whether the 2,114-unit neuromorphic computational architecture:
- 64-neuron head-direction ring attractor (CANN)
- 1,024-neuron toroidal grid sheet attractor (CANN)
- 1,026-neuron recurrent liquid state machine reservoir (LSM)
causally contributes information to downstream continuous action selection and physical navigation
safety during sensory blackout / non-LOS conditions that is unrecoverable from immediate sensing alone.

Experimental Arms:
- ARM-A (Intact): Full 2,114-unit active integration with remediated spawn offset and inter-episode reset.
- ARM-C (Zeroed): Complete deprivation of all 2,114 units (0 active units).
- ARM-D (Full-Shuffled): Full-manifold permutation across all 2,114 units (HD ring, grid torus, reservoir).
- ARM-B (Frozen): Observational control only (static compass lock, excluded from certification).

Sample Size: 100 paired episodes per arm (5 unseen seeds x 4 challenge layouts x 5 trials).
Primary Endpoint: Hull Clearance Degradation of ARM-C vs ARM-A (Delta C_hull >= +0.05m, Wilcoxon p < 0.005).
"""

import sys
import os
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import scipy.stats as stats
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain

EVIDENCE_DIR = repo_root / "evidence" / "stage3_1R"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Pre-registered frozen protocol parameters
SEEDS = [3001, 3002, 3003, 3004, 3005]
LAYOUTS = [
    "layout_1_left_trap",
    "layout_2_right_trap",
    "layout_3_t_junction",
    "layout_4_corridor_slit",
]
TRIALS_PER_LAYOUT = 5

TASK_SPECS = {
    "layout_1_left_trap": {"max_ticks": 80, "blackout_range": (15, 40), "blackout_midpoint": 28},
    "layout_2_right_trap": {"max_ticks": 80, "blackout_range": (10, 30), "blackout_midpoint": 20},
    "layout_3_t_junction": {"max_ticks": 80, "blackout_range": (15, 35), "blackout_midpoint": 25},
    "layout_4_corridor_slit": {"max_ticks": 100, "blackout_range": (20, 40), "blackout_midpoint": 30},
}


def compute_cohens_d(group1: List[float], group2: List[float]) -> float:
    n1, n2 = len(group1), len(group2)
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_se = math.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / max(n1 + n2 - 2, 1)) + 1e-8
    return float((np.mean(group1) - np.mean(group2)) / pooled_se)


def generate_spawn_configs(seed: int) -> List[Dict[str, Any]]:
    """Generates 20 deterministic spawn configurations for the given seed (5 per layout)."""
    hal = CarlStage1HAL()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    rng = np.random.RandomState(seed)
    configs = []

    for layout_id in LAYOUTS:
        layout_configs = []
        attempts = 0
        while len(layout_configs) < TRIALS_PER_LAYOUT and attempts < 200:
            attempts += 1
            if layout_id == "layout_1_left_trap":
                x = float(rng.uniform(-3.05, -2.95))
                y = float(rng.uniform(-0.25, -0.15))
                yaw = float(-math.pi / 2.0 + rng.uniform(-0.04, 0.04))
            elif layout_id == "layout_2_right_trap":
                x = float(rng.uniform(-3.45, -3.35))
                y = float(rng.uniform(-0.68, -0.62))
                yaw = float(0.0 + rng.uniform(-0.03, 0.03))
            elif layout_id == "layout_3_t_junction":
                x = float(rng.uniform(-0.25, -0.15))
                y = float(rng.uniform(-2.55, -2.45))
                yaw = float(math.pi + rng.uniform(-0.04, 0.04))
            elif layout_id == "layout_4_corridor_slit":
                x = float(rng.uniform(-2.55, -2.45))
                y = float(rng.uniform(2.20, 2.30))
                yaw = float(0.0 + rng.uniform(-0.03, 0.03))
            else:
                raise ValueError(f"Unknown layout: {layout_id}")

            hal.reset()
            hal.data.qpos[qa:qa + 2] = [x, y]
            hal.data.qpos[qa + 3:qa + 7] = [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]
            hal.data.qvel[:] = 0.0
            mujoco.mj_forward(hal.model, hal.data)

            con = hal.get_carl_contact_info()
            if (con["carl_contacts"] - con["floor_contacts"]) > 0:
                continue

            layout_configs.append({
                "layout_id": layout_id,
                "pos": [x, y],
                "yaw": yaw,
                "seed": seed,
            })

        assert len(layout_configs) == TRIALS_PER_LAYOUT, f"Could not generate spawns for {layout_id}"
        configs.extend(layout_configs)

    return configs


def reset_cann_clean(brain: CarlStage2BIntegratedBrain):
    """
    Ensures complete, zero-leak reset of all 2,114 units:
    1. 1,026-neuron LSM reservoir: resets activations, gain, and step count.
    2. 64-neuron HD ring: re-centers bump to index 32 (theta = 0).
    3. 1,024-neuron grid torus: re-centers bump to (16, 16), clears wrap counters.
    """
    brain.tick_count = 0
    # 1. Reset 1,026-unit Reservoir
    brain.reservoir.reset()

    # 2. Reset 64-unit HD Ring
    brain.hd_ring.u[:] = 0.0
    brain.hd_ring.u[32] = 1.0
    brain.hd_ring.r = brain.hd_ring._activation(brain.hd_ring.u)
    brain.hd_ring._settle_initial_attractor(100)

    # 3. Reset 1,024-unit Grid Torus
    brain.grid_torus.u[:] = 0.0
    brain.grid_torus.u[16, 16] = 2.0
    brain.grid_torus.r = brain.grid_torus._activation(brain.grid_torus.u)
    brain.grid_torus._settle_initial_attractor(50)
    brain.grid_torus.wrap_count_x = 0
    brain.grid_torus.wrap_count_y = 0
    brain.grid_torus.prev_phase_x = brain.grid_torus._readout_phase_x()
    brain.grid_torus.prev_phase_y = brain.grid_torus._readout_phase_y()

    brain.birth_grid_phase = np.array([
        brain.grid_torus.prev_phase_x,
        brain.grid_torus.prev_phase_y
    ], dtype=np.float64)
    brain.birth_hd_phase = brain.hd_ring.decode_heading()
    brain.ax_history.clear()


def build_cann_state_intact(
    cann: CarlStage2BIntegratedBrain,
    res: Dict,
    initial_heading: float,
    initial_x: float,
    initial_y: float,
    spawn_pos: List[float],
    spawn_yaw: float,
    k_shift: int
) -> Dict[str, Any]:
    hd_rel = float(res["hd_decoded_heading"]) - initial_heading
    hd_arena = math.atan2(math.sin(spawn_yaw + hd_rel), math.cos(spawn_yaw + hd_rel))

    dx_rel = float(res["grid_unwrapped_x"]) - initial_x
    dy_rel = float(res["grid_unwrapped_y"]) - initial_y
    dx_arena = dx_rel * math.cos(spawn_yaw) - dy_rel * math.sin(spawn_yaw)
    dy_arena = dx_rel * math.sin(spawn_yaw) + dy_rel * math.cos(spawn_yaw)

    r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)

    return {
        "hd_decoded_heading": hd_arena,
        "grid_unwrapped_x": float(spawn_pos[0] + dx_arena),
        "grid_unwrapped_y": float(spawn_pos[1] + dy_arena),
        "hd_rates": r_hd_shifted,
        "bump_amplitude": float(res["hd_bump_amplitude"]),
        "reservoir_norm": float(np.linalg.norm(cann.reservoir.x)),
        "total_units_active": 2114,
    }


def build_cann_state_zeroed(cann: CarlStage2BIntegratedBrain) -> Dict[str, Any]:
    cann.reservoir.x.fill(0.0)
    return {
        "hd_decoded_heading": 0.0,
        "grid_unwrapped_x": 0.0,
        "grid_unwrapped_y": 0.0,
        "hd_rates": np.zeros(64, dtype=np.float64),
        "bump_amplitude": 0.0,
        "reservoir_norm": 0.0,
        "total_units_active": 0,
    }


def build_cann_state_full_shuffled(
    cann: CarlStage2BIntegratedBrain,
    res: Dict,
    P_hd: np.ndarray,
    P_grid_flat: np.ndarray,
    P_res: np.ndarray,
    initial_hd_shuf: float,
    initial_gx_shuf: float,
    initial_gy_shuf: float,
    spawn_pos: List[float],
    spawn_yaw: float,
    k_shift: int
) -> Dict[str, Any]:
    # 1. Scramble 1,026-unit reservoir state
    cann.reservoir.x[:] = cann.reservoir.x[P_res]

    # 2. Scramble 64-unit HD ring firing rates
    r_hd_shuffled = cann.hd_ring.r[P_hd]
    angles_hd = np.linspace(-math.pi, math.pi, 64, endpoint=False)
    C_hd = float(np.sum(r_hd_shuffled * np.cos(angles_hd)))
    S_hd = float(np.sum(r_hd_shuffled * np.sin(angles_hd)))
    hd_shuf_decoded = math.atan2(S_hd, C_hd)

    # 3. Scramble 1,024-unit grid torus firing rates
    r_grid_flat = cann.grid_torus.r.flatten()[P_grid_flat]
    r_grid_shuffled = r_grid_flat.reshape(32, 32)
    X, Y = np.meshgrid(np.arange(32), np.arange(32), indexing='ij')
    angle_x = 2.0 * math.pi * X / 32.0
    angle_y = 2.0 * math.pi * Y / 32.0
    Cx = float(np.sum(r_grid_shuffled * np.cos(angle_x)))
    Sx = float(np.sum(r_grid_shuffled * np.sin(angle_x)))
    Cy = float(np.sum(r_grid_shuffled * np.cos(angle_y)))
    Sy = float(np.sum(r_grid_shuffled * np.sin(angle_y)))
    gx_shuf = math.atan2(Sx, Cx) / (2.0 * math.pi) * 0.80
    gy_shuf = math.atan2(Sy, Cy) / (2.0 * math.pi) * 0.80

    dgx = gx_shuf - initial_gx_shuf
    dgy = gy_shuf - initial_gy_shuf
    dx_arena = dgx * math.cos(spawn_yaw) - dgy * math.sin(spawn_yaw)
    dy_arena = dgx * math.sin(spawn_yaw) + dgy * math.cos(spawn_yaw)

    dhd = hd_shuf_decoded - initial_hd_shuf
    hd_arena = math.atan2(math.sin(spawn_yaw + dhd), math.cos(spawn_yaw + dhd))

    r_hd_shifted = np.roll(r_hd_shuffled, k_shift)
    bump_amp = float(math.sqrt(C_hd**2 + S_hd**2))

    return {
        "hd_decoded_heading": hd_arena,
        "grid_unwrapped_x": float(spawn_pos[0] + dx_arena),
        "grid_unwrapped_y": float(spawn_pos[1] + dy_arena),
        "hd_rates": r_hd_shifted,
        "bump_amplitude": bump_amp,
        "reservoir_norm": float(np.linalg.norm(cann.reservoir.x)),
        "total_units_active": 2114,
    }


def run_episode(
    hal: CarlStage1HAL,
    delib: CARLStage2_3R1DeliberationEngine,
    cann: CarlStage2BIntegratedBrain,
    arm: str,
    spawn_pos: List[float],
    spawn_yaw: float,
    layout_id: str,
    ep_seed: int
) -> Dict[str, Any]:
    spec = TASK_SPECS[layout_id]
    max_ticks = spec["max_ticks"]
    blackout_start, blackout_end = spec["blackout_range"]
    blackout_midpoint = spec["blackout_midpoint"]

    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.reset()
    hal.data.qpos[qa:qa + 2] = spawn_pos
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    delib.initialize_pose(spawn_pos[0], spawn_pos[1], spawn_yaw)
    reset_cann_clean(cann)

    # Pre-generate frozen permutations for ARM-D across all 2,114 units
    rng_ep = np.random.RandomState(ep_seed)
    P_ep_hd = rng_ep.permutation(64)
    P_ep_grid_flat = rng_ep.permutation(1024)
    P_ep_res = rng_ep.permutation(1026)

    # Initial CANN state at spawn
    spawn_sensors = hal.read_sensors()
    initial_res = cann.update_brain(u_executed=np.zeros(6), s_current=spawn_sensors)
    initial_heading = float(initial_res["hd_decoded_heading"])
    initial_x = float(initial_res["grid_unwrapped_x"])
    initial_y = float(initial_res["grid_unwrapped_y"])
    k_shift = int(round(spawn_yaw / (2.0 * math.pi / 64.0)))

    # Compute initial shuffled references for ARM-D zero-referencing
    r_hd_init_shuf = cann.hd_ring.r[P_ep_hd]
    angles_hd = np.linspace(-math.pi, math.pi, 64, endpoint=False)
    initial_hd_shuf = math.atan2(
        float(np.sum(r_hd_init_shuf * np.sin(angles_hd))),
        float(np.sum(r_hd_init_shuf * np.cos(angles_hd)))
    )

    r_grid_init_flat = cann.grid_torus.r.flatten()[P_ep_grid_flat].reshape(32, 32)
    X, Y = np.meshgrid(np.arange(32), np.arange(32), indexing='ij')
    angle_x = 2.0 * math.pi * X / 32.0
    angle_y = 2.0 * math.pi * Y / 32.0
    initial_gx_shuf = math.atan2(
        float(np.sum(r_grid_init_flat * np.sin(angle_x))),
        float(np.sum(r_grid_init_flat * np.cos(angle_x)))
    ) / (2.0 * math.pi) * 0.80
    initial_gy_shuf = math.atan2(
        float(np.sum(r_grid_init_flat * np.sin(angle_y))),
        float(np.sum(r_grid_init_flat * np.cos(angle_y)))
    ) / (2.0 * math.pi) * 0.80

    v_est = 0.0
    last_action = np.zeros(6, dtype=np.float64)
    collision = False
    collision_tick = max_ticks
    actions = []
    min_hull_clearances = []
    utilities_at_midpoint = None

    for t in range(max_ticks):
        sensors = hal.read_sensors()
        sonars = sensors[:15].copy()

        # Ground truth clearance for scoring
        min_sonar = float(np.min(sensors[:15]))
        min_hull_clearances.append(min_sonar)

        # Sensory Blackout: simulate temporary sensory occlusion (sonar reads 5.0m max range)
        is_blackout = (blackout_start <= t <= blackout_end)
        if is_blackout:
            sonars[:] = 5.0

        gyro_yaw = float(sensors[20]) if len(sensors) > 20 else 0.0

        # Grounded kinematic forward speed integration
        u_fwd = float(0.5 * (last_action[0] + last_action[1]))
        v_target = u_fwd * (delib.k_fwd / 0.030)
        v_est = 0.70 * v_est + 0.30 * v_target

        # Update unprivileged dead reckoning
        delib.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

        # Build CANN state according to intervention Arm
        if arm == "ARM-A_Intact":
            res = cann.update_brain(u_executed=last_action, s_current=sensors)
            cann_state = build_cann_state_intact(
                cann, res, initial_heading, initial_x, initial_y, spawn_pos, spawn_yaw, k_shift
            )
        elif arm == "ARM-B_Frozen":
            # Observational control: static compass lock
            r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
            cann_state = {
                "hd_decoded_heading": spawn_yaw,
                "grid_unwrapped_x": float(spawn_pos[0]),
                "grid_unwrapped_y": float(spawn_pos[1]),
                "hd_rates": r_hd_shifted,
                "bump_amplitude": 1.0,
                "reservoir_norm": float(np.linalg.norm(cann.reservoir.x)),
                "total_units_active": 2114,
            }
        elif arm == "ARM-C_Zeroed":
            cann_state = build_cann_state_zeroed(cann)
        elif arm == "ARM-D_FullShuffled":
            res = cann.update_brain(u_executed=last_action, s_current=sensors)
            cann_state = build_cann_state_full_shuffled(
                cann, res, P_ep_hd, P_ep_grid_flat, P_ep_res,
                initial_hd_shuf, initial_gx_shuf, initial_gy_shuf,
                spawn_pos, spawn_yaw, k_shift
            )
        else:
            raise ValueError(f"Unknown arm: {arm}")

        # Deliberation action selection
        delib_action, delib_telemetry = delib.select_action(
            curr_sensors=sonars,
            curr_v=v_est,
            curr_w=gyro_yaw,
            forced_pose=None,
            cann_state=cann_state
        )

        # Capture candidate utilities at blackout midpoint for rank correlation analysis
        if t == blackout_midpoint:
            utilities_at_midpoint = delib_telemetry.get("all_utilities", {}).copy()

        action_6d = np.zeros(6, dtype=np.float64)
        action_6d[0] = delib_action[0]
        action_6d[1] = delib_action[1]

        actions.append([float(action_6d[0]), float(action_6d[1])])

        # Step physical environment
        hal.step(action_6d)
        last_action = action_6d.copy()

        # Physical contact evaluation
        con = hal.get_carl_contact_info()
        carl_contacts = con["carl_contacts"] - con["floor_contacts"]
        if carl_contacts > 0 and not collision:
            collision = True
            collision_tick = t

    mean_clearance = float(np.mean(min_hull_clearances))
    min_clearance = float(np.min(min_hull_clearances))

    return {
        "arm": arm,
        "layout_id": layout_id,
        "ep_seed": ep_seed,
        "collision": collision,
        "collision_tick": collision_tick,
        "mean_clearance": mean_clearance,
        "min_clearance": min_clearance,
        "actions": actions,
        "utilities_at_midpoint": utilities_at_midpoint,
    }


def run_stage3_1R_battery() -> Dict[str, Any]:
    print("=" * 70)
    print("CARL STAGE 3.1-R — FROZEN 2,114-UNIT CANN CAUSAL COUPLING BATTERY")
    print("=" * 70)
    start_time = time.time()

    hal = CarlStage1HAL()
    delib = CARLStage2_3R1DeliberationEngine()

    # Load developmental brain weights
    brain = CarlStage2BIntegratedBrain(seed=42, dt=0.030)
    brain.develop_from_babbling(
        U_history=np.zeros((100, 6)),
        S_history=np.zeros((100, 25))
    )
    # Load learned parameters
    brain.w_rot = np.zeros(25, dtype=np.float64)
    brain.w_rot[20] = 1.0  # Gyro yaw rate channel
    brain.k_eff = 1.0
    brain.use_motor_efference = True
    brain.k_trans = 1.088
    brain.use_learned_speed = True

    # Generate all 100 paired spawn configs
    print("[1/3] Generating 100 deterministic spawn configurations (5 seeds x 4 layouts x 5 trials)...")
    all_configs = []
    for seed in SEEDS:
        configs = generate_spawn_configs(seed)
        all_configs.extend(configs)
    assert len(all_configs) == 100, f"Expected 100 configs, got {len(all_configs)}"
    print(f"      Verified: 100 matched configurations generated successfully.")

    # Execution Arms: ARM-A (Intact), ARM-C (Zeroed), ARM-D (Full-Shuffled), plus ARM-B (Observational)
    ARMS = ["ARM-A_Intact", "ARM-C_Zeroed", "ARM-D_FullShuffled", "ARM-B_Frozen"]
    raw_results = {arm: [] for arm in ARMS}

    total_episodes = len(ARMS) * len(all_configs)
    ep_count = 0
    print(f"[2/3] Executing {total_episodes} episodes across {len(ARMS)} arms...")

    for i, cfg in enumerate(all_configs):
        spawn_pos = cfg["pos"]
        spawn_yaw = cfg["yaw"]
        layout_id = cfg["layout_id"]
        ep_seed = cfg["seed"] * 100 + i

        for arm in ARMS:
            res = run_episode(
                hal=hal,
                delib=delib,
                cann=brain,
                arm=arm,
                spawn_pos=spawn_pos,
                spawn_yaw=spawn_yaw,
                layout_id=layout_id,
                ep_seed=ep_seed
            )
            raw_results[arm].append(res)
            ep_count += 1
            if ep_count % 40 == 0:
                print(f"      Completed {ep_count}/{total_episodes} episodes ({ep_count / total_episodes * 100:.1f}%)...")

    wall_time = time.time() - start_time
    print(f"      Execution finished in {wall_time:.1f}s.")

    # [3/3] Statistical Analysis & Gating
    print("[3/3] Computing Pre-Registered Gating Metrics & Statistical Tests...")
    N = len(all_configs)

    intact_runs = raw_results["ARM-A_Intact"]
    intact_clearances = [r["mean_clearance"] for r in intact_runs]
    intact_collisions = sum(1 for r in intact_runs if r["collision"])
    intact_coll_rate = intact_collisions / N

    arm_evals = {}
    for arm in ["ARM-C_Zeroed", "ARM-D_FullShuffled", "ARM-B_Frozen"]:
        abl_runs = raw_results[arm]
        abl_clearances = [r["mean_clearance"] for r in abl_runs]
        abl_collisions = sum(1 for r in abl_runs if r["collision"])
        abl_coll_rate = abl_collisions / N

        # Gate 1: Continuous Action Divergence Delta u
        delta_u_vals = []
        for r_int, r_abl in zip(intact_runs, abl_runs):
            u_int = np.array(r_int["actions"])
            u_abl = np.array(r_abl["actions"])
            min_len = min(len(u_int), len(u_abl))
            diff = np.linalg.norm(u_int[:min_len] - u_abl[:min_len], axis=1)
            delta_u_vals.append(float(np.mean(diff)))
        mean_delta_u = float(np.mean(delta_u_vals))
        g1_pass = bool(mean_delta_u > 0.150)

        # Gate 2: Candidate Rank Shift at Blackout Midpoint (Spearman rho <= 0.70)
        rhos = []
        for r_int, r_abl in zip(intact_runs, abl_runs):
            u_dict_int = r_int.get("utilities_at_midpoint")
            u_dict_abl = r_abl.get("utilities_at_midpoint")
            if u_dict_int and u_dict_abl:
                common_cands = [k for k in u_dict_int if k in u_dict_abl]
                if len(common_cands) >= 5:
                    vals_int = [u_dict_int[k] for k in common_cands]
                    vals_abl = [u_dict_abl[k] for k in common_cands]
                    if np.std(vals_int) > 1e-6 and np.std(vals_abl) > 1e-6:
                        rho, _ = stats.spearmanr(vals_int, vals_abl)
                        if not np.isnan(rho):
                            rhos.append(float(rho))
        mean_rho = float(np.mean(rhos)) if len(rhos) > 0 else 1.0
        g2_pass = bool(mean_rho <= 0.700)

        # Gate 3: Hull Clearance Degradation Delta C_hull >= +0.05m
        # Delta C_hull = mean(C_Intact) - mean(C_Ablated)
        diff_clearance = np.array(intact_clearances) - np.array(abl_clearances)
        delta_c_hull = float(np.mean(diff_clearance))
        g3_pass = bool(delta_c_hull >= 0.050)

        # Gate 4: Clearance Statistical Significance (Wilcoxon p < 0.005, Bonferroni-corrected)
        # Fail-closed: if all differences are zero, p=1.0; no synthetic jitter added
        non_zero_diffs = diff_clearance[np.abs(diff_clearance) > 1e-9]
        if len(non_zero_diffs) > 10:
            # Two-sided Wilcoxon signed-rank test
            _, w_p_raw = stats.wilcoxon(diff_clearance, alternative='two-sided')
            # Bonferroni correction: k=2 primary comparisons (ARM-C and ARM-D)
            # Threshold alpha_corrected = 0.005
            g4_pass = bool(w_p_raw < 0.005)
        else:
            w_p_raw = 1.0
            g4_pass = False

        # Effect size: Cohen's d
        cohens_d = compute_cohens_d(intact_clearances, abl_clearances)

        # Gate 5: Collision Rate Safety Direction (Delta Coll >= 0%)
        # Ablated collision rate should be greater than or equal to intact (intact should not be worse)
        delta_coll = float(abl_coll_rate - intact_coll_rate)
        g5_pass = bool(delta_coll >= -1e-6)

        # McNemar exact test on paired binary collisions
        n_01 = sum(1 for r_int, r_abl in zip(intact_runs, abl_runs) if (not r_int["collision"]) and r_abl["collision"])
        n_10 = sum(1 for r_int, r_abl in zip(intact_runs, abl_runs) if r_int["collision"] and (not r_abl["collision"]))
        # Exact binomial test for McNemar
        mcnemar_total = n_01 + n_10
        if mcnemar_total > 0:
            mcnemar_p = float(stats.binomtest(n_01, mcnemar_total, 0.5).pvalue)
        else:
            mcnemar_p = 1.0

        gates_passed = sum([g1_pass, g2_pass, g3_pass, g4_pass, g5_pass])

        arm_evals[arm] = {
            "g1_delta_u": {"value": mean_delta_u, "threshold": "> 0.150", "pass": g1_pass},
            "g2_spearman_rho_midpoint": {"value": mean_rho, "threshold": "<= 0.700", "pass": g2_pass, "samples": len(rhos)},
            "g3_delta_c_hull": {"value": delta_c_hull, "threshold": ">= +0.050m", "pass": g3_pass},
            "g4_wilcoxon_p": {"value": float(w_p_raw), "alpha_corrected": 0.005, "pass": g4_pass},
            "g5_delta_coll": {"value": delta_coll, "intact_coll": intact_coll_rate, "abl_coll": abl_coll_rate, "pass": g5_pass},
            "cohens_d": cohens_d,
            "mcnemar_p": mcnemar_p,
            "gates_passed_count": gates_passed,
            "all_gates_pass": (gates_passed == 5),
        }

    # Pass/Fail Decision Logic per Pre-Registered Acceptance Matrix:
    # PASS: ARM-C passes ALL 5 gates, and ARM-D passes AT LEAST 3 of 5 gates
    # INCONCLUSIVE: ARM-C passes ALL 5 gates, but ARM-D passes < 3 gates
    # FAIL_CLOSED: ARM-C fails ANY gate
    arm_c = arm_evals["ARM-C_Zeroed"]
    arm_d = arm_evals["ARM-D_FullShuffled"]

    arm_c_all_pass = arm_c["all_gates_pass"]
    arm_d_gate_count = arm_d["gates_passed_count"]

    if arm_c_all_pass and arm_d_gate_count >= 3:
        overall_verdict = "PASS"
        verdict_summary = "Stage 3.1-R CERTIFIED: 2,114-unit neuromorphic computational architecture demonstrated causal necessity."
    elif arm_c_all_pass and arm_d_gate_count < 3:
        overall_verdict = "INCONCLUSIVE"
        verdict_summary = "Stage 3.1-R INCONCLUSIVE: ARM-C deprivation passed all 5 gates, but ARM-D topology disruption passed fewer than 3 gates."
    else:
        overall_verdict = "FAIL_CLOSED"
        verdict_summary = "Stage 3.1-R FAILED CLOSED: Primary deprivation control ARM-C failed one or more mandatory gates."

    print("-" * 70)
    print(f"VERDICT: {overall_verdict}")
    print(f"SUMMARY: {verdict_summary}")
    print("-" * 70)
    for arm, ev in arm_evals.items():
        role = "(PRIMARY CERTIFICATION)" if arm == "ARM-C_Zeroed" else "(SECONDARY)" if arm == "ARM-D_FullShuffled" else "(OBSERVATIONAL ONLY)"
        print(f"\n{arm} {role}:")
        print(f"  G1 (Delta u > 0.150):           {ev['g1_delta_u']['value']:.4f} -> {'PASS' if ev['g1_delta_u']['pass'] else 'FAIL'}")
        print(f"  G2 (rho_mid <= 0.700):          {ev['g2_spearman_rho_midpoint']['value']:.4f} -> {'PASS' if ev['g2_spearman_rho_midpoint']['pass'] else 'FAIL'}")
        print(f"  G3 (Delta C_hull >= +0.050m):   {ev['g3_delta_c_hull']['value']:+.4f} m -> {'PASS' if ev['g3_delta_c_hull']['pass'] else 'FAIL'} [PRIMARY ENDPOINT]")
        print(f"  G4 (Wilcoxon p < 0.005):        {ev['g4_wilcoxon_p']['value']:.2e} -> {'PASS' if ev['g4_wilcoxon_p']['pass'] else 'FAIL'}")
        print(f"  G5 (Delta Coll >= 0%):          {ev['g5_delta_coll']['value']:+.1%} (Intact: {intact_coll_rate:.1%}, Abl: {ev['g5_delta_coll']['abl_coll']:.1%}) -> {'PASS' if ev['g5_delta_coll']['pass'] else 'FAIL'}")
        print(f"  Effect Size (Cohen's d):        {ev['cohens_d']:.4f}")
        print(f"  Gates Passed:                   {ev['gates_passed_count']}/5")

    # Save Scorecard and Raw Telemetry
    scorecard = {
        "milestone": "Stage 3.1-R",
        "date": "2026-09-13",
        "verdict": overall_verdict,
        "verdict_summary": verdict_summary,
        "total_architecture_units": 2114,
        "architecture_breakdown": {
            "head_direction_ring": 64,
            "toroidal_grid_sheet": 1024,
            "cann_subsystem": 1088,
            "liquid_state_reservoir": 1026,
            "total_units": 2114
        },
        "sample_size_per_arm": N,
        "seeds": SEEDS,
        "layouts": LAYOUTS,
        "wall_time_seconds": wall_time,
        "intact_baseline": {
            "mean_clearance": float(np.mean(intact_clearances)),
            "collision_rate": intact_coll_rate,
            "total_collisions": intact_collisions,
        },
        "arms_evaluation": arm_evals,
    }

    scorecard_path = EVIDENCE_DIR / "stage3_1R_scorecard.json"
    with open(scorecard_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)
    print(f"\nScorecard saved to: {scorecard_path}")

    # Save slim raw trial data for auditing
    slim_raw = {}
    for arm, runs in raw_results.items():
        slim_raw[arm] = [{
            "layout_id": r["layout_id"],
            "ep_seed": r["ep_seed"],
            "collision": r["collision"],
            "collision_tick": r["collision_tick"],
            "mean_clearance": r["mean_clearance"],
            "min_clearance": r["min_clearance"],
        } for r in runs]

    raw_path = EVIDENCE_DIR / "stage3_1R_raw_trials.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(slim_raw, f, indent=2)
    print(f"Raw trials saved to: {raw_path}")

    # Generate publication-grade white background figures
    try:
        from tests.generate_stage3_1R_plots import generate_plots
        print("\nGenerating separate white-background publication plots...")
        generate_plots()
    except Exception as e:
        print(f"Warning: plot generation encountered error: {e}")

    return scorecard


if __name__ == "__main__":
    run_stage3_1R_battery()
