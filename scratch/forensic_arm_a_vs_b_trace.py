"""
scratch/forensic_arm_a_vs_b_trace.py — Code-Level Causal Forensic Trace
Investigates the 4 core scientific questions:
1. Does the frontier term actually change the MPPI trajectory ranking?
2. How large is the frontier contribution compared with collision, margin, jerk, steer?
3. Can the frontier target physically be reached within H=15 / 0.45s, and where is f*?
4. At what exact point and why does ARM-A become identical to ARM-B?
"""

import sys
import math
from pathlib import Path
import numpy as np
import scipy.stats as stats
import torch

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"


def forensic_trace_episode(env_id: int, seed: int = 5001, spawn_pos=(0.50, 0.0), spawn_yaw=0.0):
    xml_path = str(ENV1_XML if env_id == 1 else ENV2_XML)
    grid_path = str(ENV1_GRID if env_id == 1 else ENV2_GRID)

    print("=" * 80)
    print(f"FORENSIC TRACE: Environment {env_id} (Seed {seed}, Spawn={spawn_pos}, Yaw={spawn_yaw:.2f})")
    print("=" * 80)

    # Initialize two matched engines: ARM-A (Frontier EFE) vs ARM-B (Pragmatic Only)
    engine_a = CARLActiveInferenceEngine(grid_path=grid_path, w_info=1.0, lambda_frontier=8.0)
    engine_b = CARLActiveInferenceEngine(grid_path=grid_path, w_info=0.0, lambda_frontier=8.0)

    hal_a = CarlStage1HAL(xml_path=xml_path)
    hal_b = CarlStage1HAL(xml_path=xml_path)

    for hal, eng in [(hal_a, engine_a), (hal_b, engine_b)]:
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = list(spawn_pos)
        hal.data.qpos[qa+3:qa+7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
        hal.step(np.zeros(6))
        eng.initialize_pose(spawn_pos[0], spawn_pos[1], spawn_yaw)

    # Track step-by-step
    action_diffs = []
    ranking_correlations = []
    frontier_magnitudes = []
    collision_costs = []
    margin_costs = []
    jerk_costs = []
    fwd_costs = []
    steer_costs = []
    frontier_distances = []
    f_star_positions = []

    v_est_a = 0.0
    v_est_b = 0.0

    qa = int(hal_a.model.joint("spatial_identity").qposadr[0])

    # Sample specific ticks for detailed inspection
    inspect_ticks = [0, 5, 15, 30, 50, 80, 120]
    detailed_traces = {}

    for tick in range(150):
        # 1. Read sensors
        s_a = hal_a.read_sensors()
        s_b = hal_b.read_sensors()

        sonars_a = s_a[:15]
        gyro_a = float(s_a[20])
        sonars_b = s_b[:15]
        gyro_b = float(s_b[20])

        engine_a.update_odometry(v_wheel=v_est_a, w_gyro=gyro_a, dt=0.030)
        engine_b.update_odometry(v_wheel=v_est_b, w_gyro=gyro_b, dt=0.030)

        # Pre-sampling inspection on ARM-A
        # Sample candidate trajectories with fixed seed for matched comparison
        torch.manual_seed(seed + tick)
        u_cand_a = engine_a._sample_trajectories()

        torch.manual_seed(seed + tick)
        u_cand_b = engine_b._sample_trajectories()

        # Check candidate rollout poses
        poses_x_a, poses_y_a, poses_th_a = engine_a._vectorized_rollout(
            engine_a.pose[0], engine_a.pose[1], engine_a.pose[2], v_est_a, gyro_a, u_cand_a
        )
        poses_x_b, poses_y_b, poses_th_b = engine_b._vectorized_rollout(
            engine_b.pose[0], engine_b.pose[1], engine_b.pose[2], v_est_b, gyro_b, u_cand_b
        )

        # Evaluate free energies
        g_a, debug_a = engine_a._evaluate_expected_free_energy(
            poses_x_a, poses_y_a, poses_th_a, u_cand_a,
            engine_a.pose[0], engine_a.pose[1], engine_a.pose[2],
            sonars_a, cann_state=None
        )

        g_b, debug_b = engine_b._evaluate_expected_free_energy(
            poses_x_b, poses_y_b, poses_th_b, u_cand_b,
            engine_b.pose[0], engine_b.pose[1], engine_b.pose[2],
            sonars_b, cann_state=None
        )

        # Check frontier computation directly
        frontier_info = engine_a._compute_nearest_frontier(engine_a.pose[0], engine_a.pose[1])
        if frontier_info is not None:
            f_star_x, f_star_y, d0 = frontier_info
            f_star_positions.append((f_star_x, f_star_y))
            frontier_distances.append(d0)

            # Compute phi_frontier across all 128 rollouts
            d_term = torch.sqrt((poses_x_a[:, -1] - f_star_x)**2 + (poses_y_a[:, -1] - f_star_y)**2)
            delta_d = float(d0) - d_term
            phi = 8.0 * delta_d
            frontier_magnitudes.append({
                "mean": float(torch.mean(phi).item()),
                "min": float(torch.min(phi).item()),
                "max": float(torch.max(phi).item()),
                "std": float(torch.std(phi).item()),
            })
        else:
            frontier_distances.append(-1.0)
            frontier_magnitudes.append({"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0})

        # Calculate Spearman correlation between ARM-A and ARM-B rollout scores
        g_a_np = g_a.detach().numpy()
        g_b_np = g_b.detach().numpy()
        rho, _ = stats.spearmanr(g_a_np, g_b_np)
        ranking_correlations.append(rho)

        # Compute MPPI action weighting
        best_a = int(np.argmin(g_a_np))
        best_b = int(np.argmin(g_b_np))
        action_a = u_cand_a[best_a, 0].numpy()
        action_b = u_cand_b[best_b, 0].numpy()

        diff = float(np.linalg.norm(action_a - action_b))
        action_diffs.append(diff)

        # Record detailed trace at inspection ticks
        if tick in inspect_ticks:
            detailed_traces[tick] = {
                "tick": tick,
                "robot_pos_a": [float(hal_a.data.qpos[qa]), float(hal_a.data.qpos[qa+1])],
                "robot_pos_b": [float(hal_b.data.qpos[qa]), float(hal_b.data.qpos[qa+1])],
                "f_star": f_star_positions[-1] if f_star_positions else None,
                "d_to_f_star": frontier_distances[-1],
                "phi_range": (frontier_magnitudes[-1]["min"], frontier_magnitudes[-1]["max"]),
                "phi_std": frontier_magnitudes[-1]["std"],
                "best_a_idx": best_a,
                "best_b_idx": best_b,
                "same_best_trajectory": (best_a == best_b),
                "action_a": [float(action_a[0]), float(action_a[1])],
                "action_b": [float(action_b[0]), float(action_b[1])],
                "spearman_rho": float(rho),
                "action_divergence": diff,
            }

        # Step physics
        cmd_a = np.zeros(6, dtype=np.float64); cmd_a[0] = float(action_a[0]); cmd_a[1] = float(action_a[1])
        cmd_b = np.zeros(6, dtype=np.float64); cmd_b[0] = float(action_b[0]); cmd_b[1] = float(action_b[1])
        hal_a.step(cmd_a)
        hal_b.step(cmd_b)

        v_est_a = 0.70 * v_est_a + 0.30 * (0.5 * (cmd_a[0] + cmd_a[1]) * 0.30)
        v_est_b = 0.70 * v_est_b + 0.30 * (0.5 * (cmd_b[0] + cmd_b[1]) * 0.30)

        # Check contact termination
        c_a = hal_a.get_carl_contact_info()
        c_b = hal_b.get_carl_contact_info()
        if (c_a["carl_contacts"] - c_a["floor_contacts"] > 0) or (c_b["carl_contacts"] - c_b["floor_contacts"] > 0):
            print(f"Contact termination at tick {tick}: A_coll={c_a['carl_contacts'] - c_a['floor_contacts'] > 0}, B_coll={c_b['carl_contacts'] - c_b['floor_contacts'] > 0}")
            break

    return {
        "env_id": env_id,
        "action_diffs": action_diffs,
        "ranking_correlations": ranking_correlations,
        "frontier_magnitudes": frontier_magnitudes,
        "frontier_distances": frontier_distances,
        "detailed_traces": detailed_traces,
    }


def main():
    print("RUNNING FORENSIC TRACE ON ENVIRONMENT 1 (TURNING BAY CUL-DE-SAC)...")
    res1 = forensic_trace_episode(env_id=1, seed=5001, spawn_pos=(0.50, 0.0), spawn_yaw=0.0)

    print("\nRUNNING FORENSIC TRACE ON ENVIRONMENT 2 (ASYMMETRIC T-JUNCTION)...")
    res2 = forensic_trace_episode(env_id=2, seed=5001, spawn_pos=(-0.45, 0.0), spawn_yaw=0.0)

    # Print Question 1 Analysis: Ranking change & divergence
    print("\n" + "=" * 80)
    print("QUESTION 1: DOES THE FRONTIER TERM ACTUALLY CHANGE TRAJECTORY RANKING?")
    print("=" * 80)
    for env_id, res in [(1, res1), (2, res2)]:
        rhos = [r for r in res["ranking_correlations"] if not np.isnan(r)]
        diffs = res["action_diffs"]
        same_action_pct = sum(1 for d in diffs if d < 1e-4) / max(1, len(diffs)) * 100.0
        print(f"Env {env_id}:")
        print(f"  Mean Spearman Rank Correlation (ARM-A vs ARM-B): {np.mean(rhos):.4f} (min={np.min(rhos):.4f}, max={np.max(rhos):.4f})")
        print(f"  Identical Top Action Percentage (||u_A - u_B|| < 1e-4): {same_action_pct:.1f}%")
        print(f"  Mean Action Divergence ||u_A - u_B||: {np.mean(diffs):.4f} m/s")

    # Print Question 2 Analysis: Component magnitudes
    print("\n" + "=" * 80)
    print("QUESTION 2: HOW LARGE IS THE FRONTIER CONTRIBUTION COMPARED TO PRAGMATIC TERMS?")
    print("=" * 80)
    for env_id, res in [(1, res1), (2, res2)]:
        stds = [m["std"] for m in res["frontier_magnitudes"]]
        spans = [m["max"] - m["min"] for m in res["frontier_magnitudes"]]
        print(f"Env {env_id}:")
        print(f"  Frontier Potential Dynamic Range across 128 candidates (max - min): mean={np.mean(spans):.3f}, max={np.max(spans):.3f}")
        print(f"  Frontier Potential Standard Deviation across 128 candidates: mean={np.mean(stds):.3f}")

    # Print Question 3 Analysis: Frontier target reachability & position
    print("\n" + "=" * 80)
    print("QUESTION 3: CAN THE FRONTIER TARGET PHYSICALLY BE REACHED WITHIN H=15 / 0.45s?")
    print("=" * 80)
    for env_id, res in [(1, res1), (2, res2)]:
        dists = [d for d in res["frontier_distances"] if d >= 0]
        print(f"Env {env_id}:")
        print(f"  Distance to nearest frontier f*: mean={np.mean(dists):.2f}m (min={np.min(dists):.2f}m, max={np.max(dists):.2f}m)")
        print(f"  Max displacement possible in H=15 (0.45s at v_max=0.30 m/s): ~0.135 m")
        print(f"  Ratio (Max Rollout Reach / Frontier Distance): {0.135 / np.mean(dists) * 100:.1f}%")

    # Print Question 4 Analysis: Exact divergence points
    print("\n" + "=" * 80)
    print("QUESTION 4: AT WHAT EXACT POINT DOES ARM-A BECOME IDENTICAL TO ARM-B?")
    print("=" * 80)
    for env_id, res in [(1, res1), (2, res2)]:
        print(f"Env {env_id} Key Inspection Ticks:")
        for t, trace in res["detailed_traces"].items():
            print(f"  Tick {t:3d}: PosA=({trace['robot_pos_a'][0]:.2f}, {trace['robot_pos_a'][1]:.2f}), "
                  f"f*={trace['f_star']}, dist={trace['d_to_f_star']:.2f}m, "
                  f"phi_std={trace['phi_std']:.3f}, same_best={trace['same_best_trajectory']}, "
                  f"rho={trace['spearman_rho']:.3f}, ||Du||={trace['action_divergence']:.4f}")


if __name__ == "__main__":
    main()
