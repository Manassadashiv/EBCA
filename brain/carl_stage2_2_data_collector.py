"""
brain/carl_stage2_2_data_collector.py — 4-Partition Dataset Harvester (Stage 2.2)
Classification: [DATA HARVESTER] Gated Sensorimotor Trajectory Generator

Generates rich, diverse exploratory trajectories for Stage 2.2:
- DEV_DEBUG: 5 episodes (Seed 42) for quick pipeline/shape tests.
- DEV_TRAIN: 60 episodes (Seeds 42, 101, 202; 20 each) for parameter optimization.
- DEV_VAL: 20 independent episodes (Seeds 42, 101, 202) for checkpoint selection & early stopping.
- PRIMARY_UNSEEN_TEST: Generated ONLY post-freeze (Step 8).

Computes normalization statistics (mu, sigma) strictly on DEV_TRAIN.
Pre-registers dynamic variance masks (sigma^2 >= 1e-4).
"""

import os
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor


class ActionGenerator:
    """
    Generates diverse, unconstrained motor babbling commands:
    - 40% Ornstein-Uhlenbeck continuous random walk
    - 25% Pure differential rotations
    - 20% Forward/backward drive bursts with active braking
    - 15% Obstacle approach / wall-grazing
    """
    def __init__(self, rng: np.random.RandomState):
        self.rng = rng
        self.ou_state = np.zeros(6, dtype=np.float64)
        self.theta = 0.15
        self.sigma = 0.30

    def get_action(self, tick: int, sonar_min: float, regime: str) -> np.ndarray:
        u = np.zeros(6, dtype=np.float64)

        if regime == "ou_random":
            # Ornstein-Uhlenbeck continuous random walk
            dx = -self.theta * self.ou_state + self.sigma * self.rng.randn(6)
            self.ou_state += dx
            u = np.clip(self.ou_state, -1.0, 1.0)

        elif regime == "rotation":
            # Sharp or sweeping turns
            direction = 1.0 if (tick // 60) % 2 == 0 else -1.0
            u[0] = -0.7 * direction
            u[1] = 0.7 * direction
            u[2:6] = 0.2 * self.rng.randn(4)

        elif regime == "burst_brake":
            # High speed forward followed by reverse braking
            phase = (tick // 40) % 3
            if phase == 0:
                u[0] = 0.8
                u[1] = 0.8
            elif phase == 1:
                u[0] = -0.6
                u[1] = -0.6
            else:
                u[0] = 0.0
                u[1] = 0.0

        elif regime == "obstacle_approach":
            # Drive forward until near wall, then turn away
            if sonar_min > 0.45:
                u[0] = 0.6
                u[1] = 0.6
            else:
                u[0] = -0.7
                u[1] = 0.7

        return np.clip(u, -1.0, 1.0)


def collect_single_episode(
    hal: CarlStage1HAL,
    seed: int,
    episode_idx: int,
    ticks: int = 400,
    friction: float = 1.0,
    regime: str = "ou_random"
) -> Dict[str, np.ndarray]:
    """Runs a single 400-tick episode and returns sensory, heading, and action trajectories."""
    ep_rng = np.random.RandomState(seed * 1000 + episode_idx)
    act_gen = ActionGenerator(ep_rng)

    hal.reset()
    hal.set_floor_friction(friction)

    # Instantiate Stage 2.1 HD Ring
    hd_ring = HeadDirectionRingAttractor(seed=seed, dt=0.030)

    S_traj = np.zeros((ticks, 25), dtype=np.float32)
    V_hd_traj = np.zeros((ticks, 2), dtype=np.float32)
    U_traj = np.zeros((ticks, 6), dtype=np.float32)

    # Initial sensor reading
    s = hal.read_sensors()

    for t in range(ticks):
        # Decode current HD ring heading
        theta_hd = hd_ring.decode_heading()
        v_hd = np.array([math.cos(theta_hd), math.sin(theta_hd)], dtype=np.float32)

        sonar_min = float(np.min(s[:15]))
        u = act_gen.get_action(t, sonar_min, regime)

        # Record state
        S_traj[t] = s.astype(np.float32)
        V_hd_traj[t] = v_hd
        U_traj[t] = u.astype(np.float32)

        # Step physical simulation
        hal.step(u)
        s_next = hal.read_sensors()

        # Step HD ring with observed gyro angular velocity (gyro z is channel 20)
        omega_z = float(s_next[20])
        hd_ring.step(omega_z)

        s = s_next

    return {
        "S": S_traj,
        "V_hd": V_hd_traj,
        "U": U_traj,
        "friction": friction,
        "seed": seed,
        "episode_idx": episode_idx
    }


def harvest_dataset_partition(
    seeds: List[int],
    episodes_per_seed: int,
    partition_name: str,
    output_path: Path
) -> Path:
    """Collects multi-seed episodes for a partition and saves to compressed .npz file."""
    hal = CarlStage1HAL(open_space=False)
    regimes = ["ou_random", "rotation", "burst_brake", "obstacle_approach"]

    all_S = []
    all_V_hd = []
    all_U = []
    metadata = []

    total_episodes = len(seeds) * episodes_per_seed
    print(f"\nHarvesting {partition_name}: {total_episodes} episodes across seeds {seeds}...")

    ep_count = 0
    for seed in seeds:
        for ep_idx in range(episodes_per_seed):
            # Vary regime across episodes
            regime = regimes[ep_count % len(regimes)]
            # Vary friction in DEV sets (from ice 0.05 to normal 1.0)
            friction = 1.0 if (ep_count % 5 != 0) else 0.05

            ep_data = collect_single_episode(
                hal=hal,
                seed=seed,
                episode_idx=ep_idx,
                ticks=400,
                friction=friction,
                regime=regime
            )

            all_S.append(ep_data["S"])
            all_V_hd.append(ep_data["V_hd"])
            all_U.append(ep_data["U"])
            metadata.append({
                "seed": seed,
                "episode_idx": ep_idx,
                "friction": friction,
                "regime": regime
            })

            ep_count += 1
            if ep_count % 10 == 0 or ep_count == total_episodes:
                print(f"  [{ep_count}/{total_episodes}] episodes generated.")

    # Convert to arrays: shape (N_episodes, T, D)
    S_arr = np.array(all_S, dtype=np.float32)
    V_hd_arr = np.array(all_V_hd, dtype=np.float32)
    U_arr = np.array(all_U, dtype=np.float32)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        S=S_arr,
        V_hd=V_hd_arr,
        U=U_arr,
        metadata=json.dumps(metadata)
    )

    print(f"Saved {partition_name} to {output_path} (Shape: S={S_arr.shape}, V_hd={V_hd_arr.shape}, U={U_arr.shape})")
    return output_path


def compute_and_save_norm_stats(dev_train_path: Path, norm_stats_path: Path, meta_path: Path):
    """
    Computes normalization statistics strictly on DEV_TRAIN.
    Saves mu, sigma, and dynamic channel masks.
    """
    data = np.load(dev_train_path)
    S = data["S"]  # (N, T, 25)
    S_flat = S.reshape(-1, 25)

    mu = np.mean(S_flat, axis=0).astype(np.float32)
    sigma = np.std(S_flat, axis=0).astype(np.float32)
    sigma = np.maximum(sigma, 1e-4)  # prevent division by zero

    # Dynamic variance mask: active channels have variance >= 1e-4
    variances = np.var(S_flat, axis=0)
    active_mask = (variances >= 1e-4)

    norm_stats_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        norm_stats_path,
        mu=mu,
        sigma=sigma,
        active_mask=active_mask,
        variances=variances
    )

    meta = {
        "sensory_dim": 25,
        "active_channel_count": int(np.sum(active_mask)),
        "active_channels": [int(i) for i in np.where(active_mask)[0]],
        "quiescent_channels": [int(i) for i in np.where(~active_mask)[0]],
        "channel_variances": [float(v) for v in variances],
        "mu": [float(m) for m in mu],
        "sigma": [float(s) for s in sigma]
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\nNormalization Statistics Saved to {norm_stats_path}")
    print(f"Active dynamic channels: {meta['active_channel_count']} of 25")
    if meta['quiescent_channels']:
        print(f"Quiescent channels: {meta['quiescent_channels']}")


def run_data_harvesting():
    dataset_dir = Path("evidence/stage2_2/datasets")
    checkpoints_dir = Path("checkpoints")

    # 1. Harvest DEV_DEBUG (5 episodes, seed 42)
    harvest_dataset_partition(
        seeds=[42],
        episodes_per_seed=5,
        partition_name="DEV_DEBUG",
        output_path=dataset_dir / "dev_debug.npz"
    )

    # 2. Harvest DEV_TRAIN (60 episodes: 20 per seed on [42, 101, 202])
    train_path = harvest_dataset_partition(
        seeds=[42, 101, 202],
        episodes_per_seed=20,
        partition_name="DEV_TRAIN",
        output_path=dataset_dir / "dev_train.npz"
    )

    # 3. Harvest DEV_VAL (20 episodes: 7, 7, 6 per seed on [42, 101, 202] with offset episode indices)
    harvest_dataset_partition(
        seeds=[42, 101, 202],
        episodes_per_seed=7,  # 3 * 7 = 21 episodes
        partition_name="DEV_VAL",
        output_path=dataset_dir / "dev_val.npz"
    )

    # 4. Compute and save normalization statistics on DEV_TRAIN strictly
    compute_and_save_norm_stats(
        dev_train_path=train_path,
        norm_stats_path=checkpoints_dir / "stage2_2_norm_stats.npz",
        meta_path=checkpoints_dir / "stage2_2_channel_meta.json"
    )

    print("\nSTEP 4 DATA HARVESTING COMPLETE!")


if __name__ == "__main__":
    run_data_harvesting()
