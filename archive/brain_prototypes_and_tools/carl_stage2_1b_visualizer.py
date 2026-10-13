"""
brain/carl_stage2_1b_visualizer.py — Stage 2.1B Publication-Grade Visual Telemetry Generator
Generates 4 figures:
- Figure 1: 1D HD Ring & 2D Toroidal Grid Cell Activity Bump Dynamics
- Figure 2: Closed-Loop Homing Showdown Trajectories (CANN vs Classical Control)
- Figure 3: Elevated Noise Filtering Advantage (CANN vs Classical Dead Reckoning)
- Figure 4: Multi-Seed Scorecard & Falsification Compliance
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
from brain.carl_stage2_grid_torus import ToroidalGridCellAttractor


def generate_figure1_bump_dynamics(save_dir: str):
    """Figure 1: Neural Activity Bump Dynamics for 64-HD Ring and 32x32 Grid Torus."""
    hd_ring = HeadDirectionRingAttractor(seed=42)
    grid_torus = ToroidalGridCellAttractor(seed=42)

    # Step HD ring through a turn (+1.5 rad/s)
    hd_ring.step(1.5)
    # Step Grid torus through translation
    grid_torus.step(0.15, 0.10)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: 64-Neuron HD Ring Activity Profile
    ax1 = axes[0]
    angles_deg = np.degrees(hd_ring.angles)
    ax1.plot(angles_deg, hd_ring.r, color="#10b981", lw=2.5, label="Firing Rate $r_i$")
    ax1.fill_between(angles_deg, 0, hd_ring.r, color="#10b981", alpha=0.25)
    decoded_th = math.degrees(hd_ring.decode_heading())
    ax1.axvline(decoded_th, color="#ef4444", ls="--", lw=2, label=f"Decoded Heading: {decoded_th:+.1f}°")
    ax1.set_title("A: 64-Neuron Head-Direction Continuous Attractor Bump", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Preferred Neural Orientation (degrees)", fontsize=11)
    ax1.set_ylabel("Firing Rate $r_i = [\\max(0, u_i)]^2 / (1 + \\beta \\sum r^2)$", fontsize=11)
    ax1.grid(True, alpha=0.3, ls=":")
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.set_xlim(-180, 180)

    # Panel B: 1,024-Neuron 2D Toroidal Grid Cell Sheet
    ax2 = axes[1]
    im = ax2.imshow(grid_torus.r.T, origin="lower", cmap="magma", extent=[0, 32, 0, 32])
    cbar = plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label("Neural Firing Rate $r_{ij}$", fontsize=10)
    ax2.set_title("B: 1,024-Neuron ($32 \\times 32$) Toroidal Grid Cell Sheet", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Neuron Lattice Index $X$", fontsize=11)
    ax2.set_ylabel("Neuron Lattice Index $Y$", fontsize=11)
    ax2.grid(False)

    plt.tight_layout()
    out_path = os.path.join(save_dir, "figure1_bump_dynamics.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Rendered Figure 1: {out_path}")


def generate_figure2_homing_showdown(telemetry_path: str, save_dir: str):
    """Figure 2: Closed-Loop Homing Showdown Trajectories (CANN vs Classical)."""
    with open(telemetry_path, "r") as f:
        data = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Representative seeds
    seeds_to_plot = ["42", "101", "303", "505"]
    colors = ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6"]

    # Panel A: Stage 2.1B CANN Trajectories
    ax1 = axes[0]
    ax1.scatter([0], [0], color="#dc2626", s=150, marker="*", zorder=10, label="Birthplace (0, 0)")
    for s_idx, s in enumerate(seeds_to_plot):
        if s in data["homing_cann"]:
            res = data["homing_cann"][s]
            traj_x = np.array(res["trajectory_x"]) - res["trajectory_x"][0]
            traj_y = np.array(res["trajectory_y"]) - res["trajectory_y"][0]
            drift = res["final_return_drift_m"]
            ax1.plot(traj_x, traj_y, color=colors[s_idx], lw=2.0, alpha=0.85,
                     label=f"Seed {s} (Drift: {drift:.3f} m)")
            ax1.scatter(traj_x[-1], traj_y[-1], color=colors[s_idx], s=70, marker="o")

    circle_target = plt.Circle((0, 0), 0.20, color="#dc2626", fill=False, ls="--", lw=1.5, label="Pass Gate (20 cm)")
    ax1.add_patch(circle_target)
    ax1.set_title("A: Stage 2.1B CANN Autonomous Homing", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Physical X Displacement (m)", fontsize=11)
    ax1.set_ylabel("Physical Y Displacement (m)", fontsize=11)
    ax1.grid(True, alpha=0.3, ls=":")
    ax1.axis("equal")
    ax1.legend(loc="upper left", fontsize=9, framealpha=0.9)

    # Panel B: Stage 2.1A-R Classical Baseline Control Group
    ax2 = axes[1]
    ax2.scatter([0], [0], color="#dc2626", s=150, marker="*", zorder=10, label="Birthplace (0, 0)")
    for s_idx, s in enumerate(seeds_to_plot):
        if s in data["homing_control_baseline"]:
            res = data["homing_control_baseline"][s]
            traj_x = np.array(res["trajectory_x"]) - res["trajectory_x"][0]
            traj_y = np.array(res["trajectory_y"]) - res["trajectory_y"][0]
            drift = res["final_return_drift_m"]
            ax2.plot(traj_x, traj_y, color=colors[s_idx], lw=2.0, alpha=0.85, ls="--",
                     label=f"Seed {s} (Drift: {drift:.3f} m)")
            ax2.scatter(traj_x[-1], traj_y[-1], color=colors[s_idx], s=70, marker="s")

    circle_target2 = plt.Circle((0, 0), 0.20, color="#dc2626", fill=False, ls="--", lw=1.5, label="Pass Gate (20 cm)")
    ax2.add_patch(circle_target2)
    ax2.set_title("B: Stage 2.1A-R Classical Control Group Baseline", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Physical X Displacement (m)", fontsize=11)
    ax2.set_ylabel("Physical Y Displacement (m)", fontsize=11)
    ax2.grid(True, alpha=0.3, ls=":")
    ax2.axis("equal")
    ax2.legend(loc="upper left", fontsize=9, framealpha=0.9)

    plt.tight_layout()
    out_path = os.path.join(save_dir, "figure2_homing_showdown.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Rendered Figure 2: {out_path}")


def generate_figure3_noise_advantage(telemetry_path: str, save_dir: str):
    """Figure 3: Elevated Noise Filtering Advantage."""
    with open(telemetry_path, "r") as f:
        data = json.load(f)

    fig, ax = plt.subplots(figsize=(9, 5))
    seeds = list(data["homing_elevated_noise"].keys())
    cann_drifts = [data["homing_elevated_noise"][s]["cann_drift"] for s in seeds]
    ctrl_drifts = [data["homing_elevated_noise"][s]["classical_drift"] for s in seeds]

    x = np.arange(len(seeds))
    width = 0.35

    rects1 = ax.bar(x - width/2, cann_drifts, width, label="Stage 2.1B CANN Attractor", color="#10b981", alpha=0.85)
    rects2 = ax.bar(x + width/2, ctrl_drifts, width, label="Classical Baseline (Euler DR)", color="#64748b", alpha=0.85)

    ax.set_ylabel("Physical Return Drift (meters)", fontsize=11)
    ax.set_title("Figure 3: Sensory Noise Resilience under Elevated IMU Noise ($\\sigma = 0.05$ rad/s)",
                 fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Seed {s}" for s in seeds], fontsize=10)
    ax.axhline(0.20, color="#ef4444", ls="--", lw=1.5, label="20 cm Gate Threshold")
    ax.grid(True, alpha=0.3, ls=":", axis="y")
    ax.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    out_path = os.path.join(save_dir, "figure3_noise_advantage.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Rendered Figure 3: {out_path}")


def generate_figure4_multiseed_scorecard(telemetry_path: str, save_dir: str):
    """Figure 4: Multi-Seed Scorecard & Gate Compliance."""
    with open(telemetry_path, "r") as f:
        data = json.load(f)

    all_seeds = data["dev_seeds"] + data["unseen_seeds"]
    fig, ax = plt.subplots(figsize=(11, 5.5))

    seeds_str = [str(s) for s in all_seeds]
    cann_drifts = [data["homing_cann"][s]["final_return_drift_m"] * 100.0 for s in seeds_str]  # in cm
    ctrl_drifts = [data["homing_control_baseline"][s]["final_return_drift_m"] * 100.0 for s in seeds_str]

    x = np.arange(len(all_seeds))
    width = 0.38

    b1 = ax.bar(x - width/2, cann_drifts, width, label="Stage 2.1B CANN (2,114 Neurons)", color="#2563eb", alpha=0.85)
    b2 = ax.bar(x + width/2, ctrl_drifts, width, label="Stage 2.1A-R Control Group", color="#94a3b8", alpha=0.85)

    ax.axvline(2.5, color="#000000", ls="-.", lw=1.5, alpha=0.6)
    ax.text(1.0, 22.0, "DEVELOPMENT SEEDS\n(Parameters Tuned)", ha="center", fontsize=9, fontweight="bold", color="#1e3a8a")
    ax.text(5.0, 22.0, "UNSEEN TEST SEEDS\n(Frozen Algorithm)", ha="center", fontsize=9, fontweight="bold", color="#b91c1c")

    ax.axhline(20.0, color="#ef4444", ls="--", lw=1.5, label="Max Drift Gate (20.0 cm)")
    ax.set_ylabel("Homing Return Drift (cm)", fontsize=11)
    ax.set_title("Figure 4: Master 8-Seed Generalization Scorecard (Dev vs Unseen)", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Seed {s}" for s in all_seeds], fontsize=10)
    ax.grid(True, alpha=0.3, ls=":", axis="y")
    ax.set_ylim(0, 26)
    ax.legend(loc="lower right", framealpha=0.9)

    plt.tight_layout()
    out_path = os.path.join(save_dir, "figure4_multiseed_scorecard.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Rendered Figure 4: {out_path}")


def generate_all_figures():
    save_dir = "d:/ebca/evidence/stage2_1b"
    os.makedirs(save_dir, exist_ok=True)
    telemetry_path = os.path.join(save_dir, "stage2_1b_full_telemetry.json")

    print("[PLOTS] Generating Figure 1: Neural Bump Dynamics...")
    generate_figure1_bump_dynamics(save_dir)

    if os.path.exists(telemetry_path):
        print("[PLOTS] Generating Figure 2: Homing Showdown...")
        generate_figure2_homing_showdown(telemetry_path, save_dir)
        print("[PLOTS] Generating Figure 3: Noise Filtering Advantage...")
        generate_figure3_noise_advantage(telemetry_path, save_dir)
        print("[PLOTS] Generating Figure 4: Multi-Seed Scorecard...")
        generate_figure4_multiseed_scorecard(telemetry_path, save_dir)
    else:
        print(f"[PLOTS] Telemetry {telemetry_path} not found yet. Figures 2-4 deferred until simulation completes.")


if __name__ == "__main__":
    generate_all_figures()
