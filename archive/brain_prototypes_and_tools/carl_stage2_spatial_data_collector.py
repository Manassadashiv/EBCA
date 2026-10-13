"""
brain/carl_stage2_spatial_data_collector.py — Synchronized Sensorimotor & Spatial Data Harvester
Classification: [DATA HARVESTER] Synchronized S, V_hd, G_grid, U Trajectory Generator

Collects synchronized trajectories combining:
- Sensory observations S_t in R^25 (15 sonars, 3 accel, 3 gyro, 3 proprio, 1 batt)
- Head Direction Ring Attractor vector V_hd_t = [cos(theta_HD), sin(theta_HD)] in R^2
- Multi-Scale Coprime Toroidal Grid Attractor state G_grid_t = [disp_x, disp_y] in R^2
- Motor actions U_t in [-1, 1]^6

Used for the 4-Condition Forensic Spatial Grounding Architecture Benchmark:
- Condition A: S + U (31 dims)
- Condition B: S + V_hd + U (33 dims)
- Condition C: S + G_grid + U (33 dims)
- Condition D: S + V_hd + G_grid + U (35 dims)
"""

import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
from brain.carl_stage2_grid_torus import MultiScaleGridToroid


class ActionGenerator:
    def __init__(self, rng: np.random.RandomState):
        self.rng = rng
        self.ou_state = np.zeros(6, dtype=np.float64)
        self.theta = 0.15
        self.sigma = 0.30

    def get_action(self, tick: int, sonar_min: float, regime: str) -> np.ndarray:
        u = np.zeros(6, dtype=np.float64)
        if regime == "ou_random":
            dx = -self.theta * self.ou_state + self.sigma * self.rng.randn(6)
            self.ou_state += dx
            u = np.clip(self.ou_state, -1.0, 1.0)
        elif regime == "rotation":
            direction = 1.0 if (tick // 60) % 2 == 0 else -1.0
            u[0] = -0.7 * direction
            u[1] = 0.7 * direction
            u[2:6] = 0.2 * self.rng.randn(4)
        elif regime == "burst_brake":
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
            if sonar_min > 0.45:
                u[0] = 0.6
                u[1] = 0.6
            else:
                u[0] = -0.7
                u[1] = 0.7
        return np.clip(u, -1.0, 1.0)


def collect_single_spatial_episode(
    hal: CarlStage1HAL,
    seed: int,
    episode_idx: int,
    ticks: int = 400,
    friction: float = 1.0,
    regime: str = "ou_random",
    k_trans: float = 1.1398
) -> Dict[str, np.ndarray]:
    ep_rng = np.random.RandomState(seed * 1000 + episode_idx)
    act_gen = ActionGenerator(ep_rng)

    hal.reset()
    hal.set_floor_friction(friction)

    # Varied initial pose across inner room
    x0 = ep_rng.uniform(-2.0, 2.0)
    y0 = ep_rng.uniform(-2.0, 2.0)
    yaw0 = ep_rng.uniform(-math.pi, math.pi)

    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa: qa + 2] = [x0, y0]
    hal.data.qpos[qa + 3: qa + 7] = [math.cos(yaw0 / 2.0), 0.0, 0.0, math.sin(yaw0 / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    hd_ring = HeadDirectionRingAttractor(seed=seed, dt=0.030)
    multi_grid = MultiScaleGridToroid(lambda1=0.80, lambda2=1.15, dt=0.030, seed=seed)
    multi_grid.reset_at_birthplace()

    S_traj = np.zeros((ticks, 25), dtype=np.float32)
    V_hd_traj = np.zeros((ticks, 2), dtype=np.float32)
    G_grid_traj = np.zeros((ticks, 2), dtype=np.float32)
    U_traj = np.zeros((ticks, 6), dtype=np.float32)

    s = hal.read_sensors()

    for t in range(ticks):
        theta_hd = hd_ring.decode_heading()
        v_hd = np.array([math.cos(theta_hd), math.sin(theta_hd)], dtype=np.float32)

        sonar_min = float(np.min(s[:15]))
        u = act_gen.get_action(t, sonar_min, regime)

        # Update Grid Continuous Attractor via translational dead-reckoning
        fwd_cmd = 0.5 * (float(u[0]) + float(u[1]))
        v_est = k_trans * fwd_cmd
        vx = v_est * math.cos(theta_hd)
        vy = v_est * math.sin(theta_hd)
        grid_res = multi_grid.step(vx, vy, slip_gated=False)
        g_grid = np.array([grid_res["displacement_x_meters"], grid_res["displacement_y_meters"]], dtype=np.float32)

        # Record
        S_traj[t] = s.astype(np.float32)
        V_hd_traj[t] = v_hd
        G_grid_traj[t] = g_grid
        U_traj[t] = u.astype(np.float32)

        # Step physics
        hal.step(u)
        s_next = hal.read_sensors()

        # Step HD ring with observed gyro yaw rate
        hd_ring.step(float(s_next[20]))
        s = s_next

    return {
        "S": S_traj,
        "V_hd": V_hd_traj,
        "G_grid": G_grid_traj,
        "U": U_traj,
        "friction": friction,
        "seed": seed,
        "episode_idx": episode_idx
    }


def harvest_spatial_partition(
    seeds: List[int],
    episodes_per_seed: int,
    partition_name: str,
    output_path: Path
) -> Path:
    hal = CarlStage1HAL(open_space=False)
    regimes = ["ou_random", "rotation", "burst_brake", "obstacle_approach"]

    all_S, all_V_hd, all_G_grid, all_U, metadata = [], [], [], [], []
    total_episodes = len(seeds) * episodes_per_seed
    print(f"\nHarvesting {partition_name}: {total_episodes} episodes across seeds {seeds}...")

    ep_count = 0
    for seed in seeds:
        for ep_idx in range(episodes_per_seed):
            regime = regimes[ep_count % len(regimes)]
            friction = 1.0 if (ep_count % 5 != 0) else 0.05

            ep_data = collect_single_spatial_episode(
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
            metadata.append({
                "seed": seed,
                "episode_idx": ep_idx,
                "friction": friction,
                "regime": regime
            })

            ep_count += 1
            if ep_count % 10 == 0 or ep_count == total_episodes:
                print(f"  [{ep_count}/{total_episodes}] spatial episodes harvested.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        S=np.array(all_S, dtype=np.float32),
        V_hd=np.array(all_V_hd, dtype=np.float32),
        G_grid=np.array(all_G_grid, dtype=np.float32),
        U=np.array(all_U, dtype=np.float32),
        metadata=np.array(metadata, dtype=object)
    )
    print(f"Partition saved to {output_path} (Shape: {len(all_S)} x 400 x 25)")
    return output_path


if __name__ == "__main__":
    datasets_dir = Path("evidence/stage2_2/datasets")
    # Harvest DEV_TRAIN (60 episodes)
    harvest_spatial_partition(
        seeds=[42, 101, 202],
        episodes_per_seed=20,
        partition_name="SPATIAL_DEV_TRAIN",
        output_path=datasets_dir / "spatial_dev_train.npz"
    )
    # Harvest UNSEEN_TEST (25 episodes)
    harvest_spatial_partition(
        seeds=[303, 404, 505, 606, 707],
        episodes_per_seed=5,
        partition_name="SPATIAL_UNSEEN_TEST",
        output_path=datasets_dir / "spatial_unseen_test.npz"
    )
