"""
brain/carl_stage2_2_diagnostic_collector.py — Active-Contingency Sensorimotor & Spatial Data Harvester
Classification: [DATA ENGINE] Gated Active-Contingency Dataset Generator (Stage 2.2-DIAG)

Collects rich, dynamic exploratory trajectories specifically for Stage 2.2 Phase 1:
- DEV_TRAIN: 60 episodes (Seeds 42, 101, 202; 20 each = 24,000 timesteps)
- DEV_VAL:   20 episodes across 4 independent seeds (Seeds 210, 220, 230, 240; 5 each = 8,000 timesteps)
- PRIMARY_UNSEEN_TEST: PROHIBITED from being generated during Phase 1.

Methodological Invariants Enforced:
1. Zero Privileged GPS Leak: CARL's spatial state (HD ring and continuous grid attractor) strictly
   initializes to internal origin (0, 0) and heading theta_0 = 0. Zero access to MuJoCo qpos/qvel.
2. Natural Physical Trajectories: Explores 4 natural regimes (wall-following, obstacle approaches,
   high-yaw spins, burst-brake-reversals) to naturally produce rich near-field observations.
   Sensor returns are NEVER artificially edited, clamped, or synthesized.
3. Fixed Collision Oracle: Records obstacle contact events subtracting floor contacts.
4. Cryptographic Hashing: Saves SHA-256 hashes for all partitions prior to model training.
"""

import os
import sys
import math
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
from brain.carl_stage2_grid_torus import MultiScaleGridToroid


class ActiveContingencyActionGenerator:
    """
    Generates purposeful, active-contingency motor sequences that naturally exercise
    the full dynamic range of sensors and actuators:
    - Regime 1: Wall Following & Perpendicular Approach (sonars in 0.3 - 3.5 m)
    - Regime 2: High-Angular Turns & Spin Maneuvers (yaw rate in [-15, +15] rad/s)
    - Regime 3: Burst-Brake-Reverse Sequences (rapid proprioceptive accelerations)
    - Regime 4: Friction Transitions (normal floor to low-friction glaze ice)
    """
    def __init__(self, rng: np.random.RandomState):
        self.rng = rng
        self.ou_state = np.zeros(6, dtype=np.float64)
        self.theta = 0.15
        self.sigma = 0.35

    def get_action(self, tick: int, sonar_min: float, front_sonar: float, regime: str) -> np.ndarray:
        u = np.zeros(6, dtype=np.float64)

        if regime == "wall_follow":
            # Cruise along arena perimeter maintaining distance ~0.6 - 1.2m
            # Sonar channels 0-3: left; 4-10: front; 11-14: right
            # If too close, turn gently away; if opening ahead, continue
            if front_sonar < 0.80:
                # Turn away from obstacle ahead
                u[0] = -0.7
                u[1] = 0.7
            elif sonar_min < 0.50:
                # Steer slightly outward
                u[0] = 0.7
                u[1] = 0.4
            else:
                # Drive forward with minor steering bias toward boundary
                u[0] = 0.6
                u[1] = 0.65
            # Add subtle head pan to track boundary
            u[2] = 0.4 * math.sin(tick * 0.1)

        elif regime == "perpendicular_approach":
            # Drive straight toward wall, slam brakes, rotate 90-180 degrees, burst away
            phase = (tick // 50) % 3
            if phase == 0:
                # Forward charge
                u[0] = 0.85
                u[1] = 0.85
                if front_sonar < 0.50:
                    # Emergency spin if wall is hit early
                    u[0] = -0.8
                    u[1] = 0.8
            elif phase == 1:
                # Sharp brake & hard reverse
                u[0] = -0.75
                u[1] = -0.75
            else:
                # Hard pivot spin
                turn_dir = 1.0 if (tick // 150) % 2 == 0 else -1.0
                u[0] = -0.8 * turn_dir
                u[1] = 0.8 * turn_dir

        elif regime == "high_spin":
            # Rapid alternating angular spins to force high gyro yaw rates and dynamic sweeps
            cycle = (tick // 30) % 4
            if cycle == 0:
                u[0] = -0.9
                u[1] = 0.9
            elif cycle == 1:
                u[0] = 0.8
                u[1] = 0.8
            elif cycle == 2:
                u[0] = 0.9
                u[1] = -0.9
            else:
                u[0] = -0.6
                u[1] = -0.6
            u[2] = 0.7 * math.sin(tick * 0.2)  # Active head pan
            u[3] = 0.3 * math.cos(tick * 0.1)  # Active neck tilt

        elif regime == "burst_brake_reverse":
            # Exercises longitudinal acceleration, wheel encoders, accelerometer forward/back
            step = (tick // 25) % 4
            if step == 0:
                u[0] = 1.0
                u[1] = 1.0  # Max forward burst
            elif step == 1:
                u[0] = 0.0
                u[1] = 0.0  # Dead stop / coast
            elif step == 2:
                u[0] = -0.9
                u[1] = -0.9  # Hard reverse drive
            else:
                u[0] = 0.5
                u[1] = -0.5  # Reorient spin

        elif regime == "friction_transition":
            # Exploratory locomotion across surface friction boundaries
            dx = -self.theta * self.ou_state + self.sigma * self.rng.randn(6)
            self.ou_state += dx
            u = np.clip(self.ou_state, -1.0, 1.0)
            # Ensure non-trivial forward/turn component
            u[0] = 0.6 * np.sign(u[0]) if abs(u[0]) < 0.2 else u[0]
            u[1] = 0.6 * np.sign(u[1]) if abs(u[1]) < 0.2 else u[1]

        return np.clip(u, -1.0, 1.0)


def collect_single_diagnostic_episode(
    hal: CarlStage1HAL,
    seed: int,
    episode_idx: int,
    ticks: int = 400,
    friction: float = 1.0,
    regime: str = "wall_follow",
    k_trans: float = 1.1398
) -> Dict[str, np.ndarray]:
    """
    Runs a single 400-tick physical episode with synchronized sensory, internal pose,
    and action streams under zero simulator leakage.
    """
    ep_rng = np.random.RandomState(seed * 1000 + episode_idx)
    act_gen = ActiveContingencyActionGenerator(ep_rng)

    hal.reset()
    hal.set_floor_friction(friction)

    # Varied initial spawn inside arena boundary (bounds: +/-2.5m)
    x0 = float(ep_rng.uniform(-2.2, 2.2))
    y0 = float(ep_rng.uniform(-2.2, 2.2))
    yaw0 = float(ep_rng.uniform(-math.pi, math.pi))

    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa: qa + 2] = [x0, y0]
    hal.data.qpos[qa + 3: qa + 7] = [math.cos(yaw0 / 2.0), 0.0, 0.0, math.sin(yaw0 / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    # Invariant 1: CARL's internal dead reckoning & CANN start strictly at internal (0, 0, 0)
    hd_ring = HeadDirectionRingAttractor(seed=seed, dt=0.030)
    multi_grid = MultiScaleGridToroid(lambda1=0.80, lambda2=1.15, dt=0.030, seed=seed)
    multi_grid.reset_at_birthplace()

    S_traj = np.zeros((ticks, 25), dtype=np.float32)
    V_hd_traj = np.zeros((ticks, 2), dtype=np.float32)
    G_grid_traj = np.zeros((ticks, 2), dtype=np.float32)
    U_traj = np.zeros((ticks, 6), dtype=np.float32)
    Collision_traj = np.zeros(ticks, dtype=np.int32)

    s = hal.read_sensors()

    for t in range(ticks):
        # Decode current internal heading & spatial displacement
        theta_hd = hd_ring.decode_heading()
        v_hd = np.array([math.cos(theta_hd), math.sin(theta_hd)], dtype=np.float32)

        sonar_min = float(np.min(s[:15]))
        front_sonar = float(np.min(s[6:9]))  # Center front sonars
        u = act_gen.get_action(t, sonar_min, front_sonar, regime)

        # Update Grid Continuous Attractor via subjective dead-reckoning (Zero GPS leak)
        fwd_cmd = 0.5 * (float(u[0]) + float(u[1]))
        v_est = k_trans * fwd_cmd
        vx = v_est * math.cos(theta_hd)
        vy = v_est * math.sin(theta_hd)
        grid_res = multi_grid.step(vx, vy, slip_gated=False)
        g_grid = np.array([grid_res["displacement_x_meters"], grid_res["displacement_y_meters"]], dtype=np.float32)

        # Check genuine obstacle contacts (subtracted floor contacts)
        contact_info = hal.get_carl_contact_info()
        obs_contacts = max(0, contact_info["carl_contacts"] - contact_info["floor_contacts"])
        is_collision = 1 if obs_contacts > 0 else 0

        # Record trajectory state
        S_traj[t] = s.astype(np.float32)
        V_hd_traj[t] = v_hd
        G_grid_traj[t] = g_grid
        U_traj[t] = u.astype(np.float32)
        Collision_traj[t] = is_collision

        # Step physical simulation
        hal.step(u)
        s_next = hal.read_sensors()

        # Step internal HD ring with observed gyro yaw rate (channel 20)
        hd_ring.step(float(s_next[20]))
        s = s_next

    return {
        "S": S_traj,
        "V_hd": V_hd_traj,
        "G_grid": G_grid_traj,
        "U": U_traj,
        "collision": Collision_traj,
        "friction": friction,
        "seed": seed,
        "episode_idx": episode_idx,
        "regime": regime
    }


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def harvest_diagnostic_datasets(
    output_dir: Path
) -> Dict[str, Path]:
    """
    Harvests DEV_TRAIN and DEV_VAL datasets enforcing all locked invariants.
    Explicitly refuses to generate PRIMARY_UNSEEN_TEST.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    hal = CarlStage1HAL(open_space=False)

    regimes = [
        "wall_follow",
        "perpendicular_approach",
        "high_spin",
        "burst_brake_reverse",
        "friction_transition"
    ]

    partitions_spec = {
        "DEV_TRAIN": {
            "seeds": [42, 101, 202],
            "episodes_per_seed": 20,
            "filename": "DEV_TRAIN.npz"
        },
        "DEV_VAL": {
            "seeds": [210, 220, 230, 240],
            "episodes_per_seed": 5,
            "filename": "DEV_VAL.npz"
        }
    }

    generated_paths = {}

    for part_name, spec in partitions_spec.items():
        seeds = spec["seeds"]
        ep_per_seed = spec["episodes_per_seed"]
        out_file = output_dir / spec["filename"]

        all_S = []
        all_V_hd = []
        all_G_grid = []
        all_U = []
        all_Col = []
        meta_list = []

        total_ep = len(seeds) * ep_per_seed
        print(f"\n========================================================")
        print(f" Harvesting {part_name}: {total_ep} episodes across seeds {seeds}")
        print(f"========================================================")

        ep_counter = 0
        for seed in seeds:
            for ep_idx in range(ep_per_seed):
                regime = regimes[ep_counter % len(regimes)]
                # Friction: 80% dry arena (1.0), 20% ice patches (0.05)
                friction = 1.0 if (ep_counter % 5 != 0) else 0.05

                ep_data = collect_single_diagnostic_episode(
                    hal=hal,
                    seed=seed,
                    episode_idx=ep_idx,
                    ticks=400,
                    friction=friction,
                    regime=regime
                )

                all_S.append(ep_data["S"])
                all_V_hd.append(ep_data["V_hd"])
                all_G_grid.append(ep_data["G_grid"])
                all_U.append(ep_data["U"])
                all_Col.append(ep_data["collision"])
                meta_list.append({
                    "seed": seed,
                    "episode_idx": ep_idx,
                    "regime": regime,
                    "friction": friction
                })

                ep_counter += 1
                if ep_counter % 5 == 0 or ep_counter == total_ep:
                    print(f"  [{ep_counter}/{total_ep}] episodes harvested ({regime}, friction={friction})")

        # Save compressed arrays: (N, T, D)
        np.savez_compressed(
            out_file,
            S=np.array(all_S, dtype=np.float32),
            V_hd=np.array(all_V_hd, dtype=np.float32),
            G_grid=np.array(all_G_grid, dtype=np.float32),
            U=np.array(all_U, dtype=np.float32),
            collision=np.array(all_Col, dtype=np.int32),
            seeds=np.array(seeds, dtype=np.int32)
        )
        generated_paths[part_name] = out_file
        print(f"  --> Saved {part_name} to {out_file} ({out_file.stat().st_size / 1024 / 1024:.2f} MB)")

    return generated_paths


def audit_dataset_saturation(npz_path: Path) -> Dict[str, float]:
    """
    Computes rigorous variance, saturation, and high-change transition metrics:
    - Sonar Saturation Fraction: percentage of sonar returns pinned at 5.0m
    - High-Change Transition Fraction: transitions satisfying |delta s| >= 0.15m or high gyro/accel
    - Collision Fraction: percentage of timesteps involving obstacle contact
    """
    data = np.load(npz_path)
    S = data["S"]  # (N, T, 25)
    U = data["U"]  # (N, T, 6)
    Col = data["collision"]  # (N, T)

    N, T, D = S.shape
    total_timesteps = N * T

    sonars = S[:, :, :15]
    sat_mask = (sonars >= 4.95)
    sat_fraction = float(np.mean(sat_mask))

    # Delta sonars between consecutive steps
    delta_s = np.abs(S[:, 1:, :15] - S[:, :-1, :15])
    mean_abs_delta_s = float(np.mean(delta_s))

    # Gyro yaw rate delta
    delta_omega = np.abs(S[:, 1:, 20] - S[:, :-1, 20])
    
    # Wheel velocity delta (channel 21, 22)
    delta_wheel = np.abs(S[:, 1:, 21] - S[:, :-1, 21])

    # High-change transitions: |delta s_mean| >= 0.15 OR delta_omega >= 1.0 OR delta_wheel >= 0.1
    high_change_mask = (
        (np.mean(delta_s, axis=-1) >= 0.15) |
        (delta_omega >= 1.0) |
        (delta_wheel >= 0.10)
    )
    high_change_fraction = float(np.mean(high_change_mask))
    collision_fraction = float(np.mean(Col))

    metrics = {
        "total_episodes": N,
        "total_timesteps": total_timesteps,
        "sonar_saturation_fraction": sat_fraction,
        "active_sonar_fraction": 1.0 - sat_fraction,
        "mean_abs_sonar_delta_m": mean_abs_delta_s,
        "high_change_transition_fraction": high_change_fraction,
        "collision_timestep_fraction": collision_fraction
    }
    return metrics


if __name__ == "__main__":
    out_dir = Path("evidence/stage2_2_diag/datasets")
    paths = harvest_diagnostic_datasets(out_dir)

    print("\n--- Auditing Harvested Dataset Saturation ---")
    audit_report = {}
    hashes_report = {}

    for part_name, path in paths.items():
        sha = compute_file_sha256(path)
        metrics = audit_dataset_saturation(path)
        audit_report[part_name] = metrics
        hashes_report[part_name] = {
            "path": str(path),
            "sha256": sha,
            "metrics": metrics
        }
        print(f"\n[{part_name}] SHA-256: {sha}")
        print(f"  Sonar Saturation: {metrics['sonar_saturation_fraction']*100:.2f}% (Requirement: <= 30%)")
        print(f"  Active Sonar Fraction: {metrics['active_sonar_fraction']*100:.2f}%")
        print(f"  High-Change Fraction (D_dynamic): {metrics['high_change_transition_fraction']*100:.2f}% (Requirement: >= 25%)")
        print(f"  Collision Timestep Fraction: {metrics['collision_timestep_fraction']*100:.2f}%")

    # Save cryptographic hashes manifest
    hash_manifest_path = Path("evidence/stage2_2_diag/dataset_hashes.json")
    with open(hash_manifest_path, "w") as f:
        json.dump(hashes_report, f, indent=2)
    print(f"\nCryptographic dataset hash manifest saved to {hash_manifest_path}")
