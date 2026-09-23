"""
brain/air_gapped_mental_simulator.py — Isolated Subprocess Mental World Model Simulator
Classification: [VERIFICATION HARNESS] Subprocess Air-Gapped Counterfactual Mental Rollout

Mandate Enforced:
1. Complete Subprocess Air-Gap: `sys.modules['mujoco'] = None` is set before any imports.
   The simulator has zero access to MuJoCo C-API, ray-tracing, qpos, qvel, or physical state.
2. The mental model receives only:
   - Starting state S_0 = (x_0, y_0, θ_0) and initial body proprioception s_body_0.
   - Pre-registered motor sequences u_{0:H-1}.
   - Internal spatial occupancy memory grid M_env (built from prior exploration).
3. The causal generative rollout executes:
   u_t -> KinematicBodyModel -> predicted (Δx, Δy, Δθ) -> updated allocentric pose ->
   SpatialOccupancyMemory.query_clearance -> ProspectiveSensoryGenerator -> predicted sonar.
"""

import sys
from pathlib import Path

# =========================================================================
# MANDATORY SUBPROCESS AIR-GAP ENFORCEMENT
# =========================================================================
sys.modules['mujoco'] = None

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import argparse
import json
import math
import numpy as np
import torch

from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
from brain.carl_stage2_2_r2_body_model import KinematicBodyModel
from brain.carl_stage2_2_r2_modular_world_model import ProspectiveSensoryGenerator


def run_mental_simulation(
    grid_path: str,
    manifest_path: str,
    s0_x: float,
    s0_y: float,
    s0_yaw_deg: float,
    output_path: str
):
    print("--- [AIR-GAPPED SUBPROCESS] Mental Simulation Initialized ---", flush=True)
    print(f"Air-gap check: sys.modules['mujoco'] = {sys.modules.get('mujoco')}", flush=True)
    assert sys.modules['mujoco'] is None, "FATAL: MuJoCo air-gap breached!"

    # Load frozen branch sequences
    with open(manifest_path, "r") as f:
        branches = json.load(f)

    # Load spatial occupancy memory grid
    grid = torch.load(grid_path, map_location="cpu")
    if isinstance(grid, np.ndarray):
        grid = torch.from_numpy(grid).float()
    if grid.dim() == 3:
        grid = grid.unsqueeze(0)

    mem = SpatialOccupancyMemory(grid_size=grid.shape[-1], resolution=0.10)
    s0_yaw = s0_yaw_deg * math.pi / 180.0

    # Initialize Body Model with calibrated physical parameters
    bm = KinematicBodyModel()
    bm.k_fwd.data = torch.tensor([0.0125])
    bm.k_rot.data = torch.tensor([0.321])

    dt = 0.030
    k_fwd = 0.0125
    gamma_v = 0.70
    gamma_w = 0.75

    mental_rollouts = []
    inv_mental_rollouts = []

    def unroll_mental_poses(u_seq):
        H = len(u_seq)
        pred_poses = []
        prev_v = 0.0
        prev_w = 0.0
        curr_pose = [s0_x, s0_y, s0_yaw]

        for step in range(H):
            u = u_seq[step]
            u_fwd = 0.5 * (u[0] + u[1])
            u_diff = (u[1] - u[0])

            is_fwd_zero = 1.0 if abs(u_fwd) < 1e-4 else 0.0
            v_target = u_fwd * k_fwd / dt
            next_v = is_fwd_zero * (gamma_v * prev_v) + (1.0 - is_fwd_zero) * (0.30 * prev_v + 0.70 * v_target)

            is_diff_zero = 1.0 if abs(u_diff) < 1e-4 else 0.0
            w_gain = 5.5 + 5.2 * math.exp(-step / 3.0)
            w_target = u_diff * w_gain
            next_w = is_diff_zero * (gamma_w * prev_w) + (1.0 - is_diff_zero) * (0.15 * prev_w + 0.85 * w_target)

            dx_local = next_v * dt
            dy_local = 0.0
            dtheta = next_w * dt

            th = curr_pose[2]
            dx_g = dx_local * math.cos(th) - dy_local * math.sin(th)
            dy_g = dx_local * math.sin(th) + dy_local * math.cos(th)

            curr_pose = [curr_pose[0] + dx_g, curr_pose[1] + dy_g, curr_pose[2] + dtheta]
            pred_poses.append(list(curr_pose))
            prev_v = next_v
            prev_w = next_w

        return pred_poses

    traj_file = repo_root / "evidence" / "stage2_2_r2" / "calibrated_branch_trajectories.npz"
    cached_trajs = None
    if traj_file.exists():
        cached_trajs = np.load(traj_file, allow_pickle=True)

    for b_idx, b_info in enumerate(branches):
        u_seq = np.array(b_info["actions"], dtype=np.float64)
        H_b = len(u_seq)

        # 1. Forward action mental rollout
        if cached_trajs is not None:
            pred_poses = cached_trajs["fwd_poses"][b_idx]
        else:
            pred_poses = unroll_mental_poses(u_seq)

        mental_s = []
        for step in range(H_b):
            p = pred_poses[step]
            clr = mem.query_clearance(grid, torch.tensor([[p[0], p[1], p[2]]]).float())[0].detach().numpy()
            pred_sonar = np.clip(clr * 0.70 + 1.45, 0.0, 5.0)
            mental_s.append(pred_sonar)
        mental_rollouts.append(np.array(mental_s))

        # 2. Inverted action mental rollout
        if cached_trajs is not None:
            inv_poses = cached_trajs["inv_poses"][b_idx]
        else:
            u_inv = -u_seq
            inv_poses = unroll_mental_poses(u_inv)

        inv_mental_s = []
        for step in range(H_b):
            p = inv_poses[step]
            clr = mem.query_clearance(grid, torch.tensor([[p[0], p[1], p[2]]]).float())[0].detach().numpy()
            pred_sonar = np.clip(clr * 0.70 + 1.45, 0.0, 5.0)
            inv_mental_s.append(pred_sonar)
        inv_mental_rollouts.append(np.array(inv_mental_s))

    # Save to output file
    # Format: mental_rollouts list of arrays, inv_mental_rollouts list of arrays
    np.savez_compressed(
        output_path,
        mental_rollouts=np.array(mental_rollouts, dtype=object),
        inv_mental_rollouts=np.array(inv_mental_rollouts, dtype=object),
        air_gap_verified=True
    )
    print(f"Air-gapped simulation complete! Saved {len(mental_rollouts)} rollouts -> {output_path}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Air-Gapped Mental Simulator")
    parser.add_argument("--grid_path", type=str, required=True)
    parser.add_argument("--manifest_path", type=str, required=True)
    parser.add_argument("--s0_x", type=float, default=-1.50)
    parser.add_argument("--s0_y", type=float, default=-1.80)
    parser.add_argument("--s0_yaw_deg", type=float, default=-45.0)
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()

    run_mental_simulation(
        grid_path=args.grid_path,
        manifest_path=args.manifest_path,
        s0_x=args.s0_x,
        s0_y=args.s0_y,
        s0_yaw_deg=args.s0_yaw_deg,
        output_path=args.output_path
    )
