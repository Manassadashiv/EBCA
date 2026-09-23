#!/usr/bin/env python3
r"""
Generate Independent Single-Panel Plots for CARL-DX Presentation Surgery.
Strict Rule: ZERO composite / multi-panel dashboards.
Every generated PNG contains exactly ONE independent plot with its own axes, labels, and title.
"""

import sys
import os
import json
import math
import time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(r"D:\ebca")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
OUTPUT_DIR = REPO_ROOT / "evidence" / "independent_single_plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.titlesize": 18,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "axes.facecolor": "white"
})


def generate_stage3_2_single_plots():
    print("Generating Stage 3.2 independent single plots...")
    from tests.generate_stage3_2R_evidence import load_benchmark_data
    matched_pairs, scorecard, fidelity_data = load_benchmark_data()

    # 1. Terminal Error by Profile (Single Plot)
    rollouts = fidelity_data["rollouts"]
    profile_pids = sorted(list(set(r["pid"] for r in rollouts)))
    names = []
    mean_errors = []
    rmse_xys = []
    for pid in profile_pids:
        pid_rollouts = [r for r in rollouts if r["pid"] == pid]
        pname = pid_rollouts[0]["pname"]
        names.append(f"{pid}\n{pname[:8]}")
        mean_errors.append(np.mean([r["e_term"] for r in pid_rollouts]))
        rmse_xys.append(np.mean([r["rmse_xy"] for r in pid_rollouts]))

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    bars = ax.bar(range(len(names)), mean_errors, color="#1f77b4", edgecolor="black", alpha=0.85, width=0.55)
    ax.axhline(0.080, color="crimson", linestyle="--", linewidth=2.0, label="G1 Acceptance Threshold (≤ 0.080 m)")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=11)
    ax.set_ylabel("Terminal Position Error (m)", fontweight="bold", fontsize=13)
    ax.set_title("Mean Terminal Position Error by Kinematic Profile (Class A)", fontweight="bold", fontsize=15, pad=12)
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(0, 0.12)
    out1 = OUTPUT_DIR / "fig_stage3_2_terminal_error.png"
    plt.savefig(out1, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out1}")

    # 2. Path RMSE by Profile (Single Plot)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    bars = ax.bar(range(len(names)), rmse_xys, color="#2ca02c", edgecolor="black", alpha=0.85, width=0.55)
    ax.axhline(0.050, color="crimson", linestyle="--", linewidth=2.0, label="G3 Acceptance Threshold (≤ 0.050 m)")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=11)
    ax.set_ylabel("Path RMSE (m)", fontweight="bold", fontsize=13)
    ax.set_title("Path Tracking Root Mean Square Error (RMSE) by Profile", fontweight="bold", fontsize=15, pad=12)
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(0, 0.07)
    out2 = OUTPUT_DIR / "fig_stage3_2_path_rmse.png"
    plt.savefig(out2, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out2}")

    # 3. Success Rates Across Experimental Arms (Single Plot)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    arms = ["ARM-I\n(Intact)", "ARM-A\n(Amnesic)", "ARM-S\n(Scrambled)", "ARM-PF\n(Pot. Field)", "ARM-R\n(Reflex)"]
    arm_keys = ["ARM-I", "ARM-A", "ARM-S", "ARM-PF", "ARM-R"]
    succ_rates = [float(scorecard["success_rates"][k].split("%")[0]) for k in arm_keys]
    colors = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e"]
    bars = ax.bar(arms, succ_rates, color=colors, width=0.50, edgecolor="black", linewidth=1.2)
    ax.set_ylabel("Autonomous Success Rate (%)", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_title("Task Family Success Rate Across Experimental Arms (N = 100 Matched Pairs)", fontsize=15, fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 2.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=12, fontweight="bold")
    out3 = OUTPUT_DIR / "fig_stage3_2_success_by_arm.png"
    plt.savefig(out3, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out3}")

    # 4. Action Divergence Distribution ||u_I - u_A|| (Single Plot)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    delta_us = [p["delta_u_I_A"] for p in matched_pairs]
    ax.hist(delta_us, bins=16, color="#386cb0", edgecolor="black", alpha=0.85, rwidth=0.85)
    mean_du = np.mean(delta_us)
    ax.axvline(mean_du, color="red", linestyle="-", linewidth=2.5, label=f"Mean ||Δu|| = {mean_du:.3f} m/s")
    ax.axvline(0.250, color="darkorange", linestyle="--", linewidth=2.0, label="Substantial Divergence (0.250 m/s)")
    ax.set_xlabel("Action Divergence ||u_Intact - u_Amnesic|| (m/s)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Matched Pair Count", fontsize=13, fontweight="bold")
    ax.set_title("Decision Divergence at T_crit Under Identical Local Sonar Sensors", fontsize=15, fontweight="bold", pad=12)
    ax.grid(axis="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=12)
    out4 = OUTPUT_DIR / "fig_stage3_2_action_divergence_hist.png"
    plt.savefig(out4, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out4}")


def generate_stage3_3_single_plots():
    print("Generating Stage 3.3 independent single plots...")
    from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
    
    # 1. Action Continuity & Step Delta Distribution (Single Plot)
    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    mppi.initialize_pose(0.0, 0.0, 0.0)
    actions = []
    deltas = []
    u_prev = np.array([0.5, 0.5])
    for step in range(120):
        d_front = 1.5 + 0.8 * math.sin(step * 0.1)
        d_left = 0.8 + 0.4 * math.cos(step * 0.15)
        d_right = 0.8 - 0.4 * math.cos(step * 0.15)
        sensors = np.array([
            d_right, d_right, d_right, d_right, d_right, d_right,
            d_front, d_front, d_front,
            d_left, d_left, d_left, d_left, d_left, d_left
        ], dtype=np.float32)
        u_star, tel = mppi.select_action(sensors, curr_v=0.15, curr_w=0.0)
        actions.append(u_star)
        deltas.append(np.linalg.norm(u_star - u_prev))
        u_prev = u_star

    deltas = np.array(deltas)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.hist(deltas, bins=20, color="#1f77b4", edgecolor="black", alpha=0.85, density=True)
    mean_d = float(np.mean(deltas))
    ax.axvline(mean_d, color="#d62728", linestyle="--", linewidth=2.2, label=f"Mean Step Delta = {mean_d:.4f} (Req ≤ 0.35)")
    ax.axvline(0.35, color="red", linestyle=":", linewidth=2.0, label="G1 Smoothness Ceiling (0.35)")
    ax.set_xlabel("Action Difference ||Δu*||_2", fontweight="bold", fontsize=13)
    ax.set_ylabel("Probability Density", fontweight="bold", fontsize=13)
    ax.set_title("MPPI Step-to-Step Action Continuity Distribution (Zero Chatter)", fontweight="bold", fontsize=15, pad=12)
    ax.legend(loc="upper right", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)
    out1 = OUTPUT_DIR / "fig_stage3_3_action_continuity.png"
    plt.savefig(out1, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out1}")

    # 2. Cycle Latency Distribution (Single Plot)
    cann_state = {
        "hd_decoded_heading": 0.25,
        "grid_unwrapped_x": 0.0,
        "grid_unwrapped_y": 0.0,
        "hd_rates": np.random.uniform(0.0, 1.0, 64).astype(np.float32)
    }
    latencies = []
    rng = np.random.RandomState(42)
    for _ in range(200):
        sensors = rng.uniform(0.2, 3.0, 15).astype(np.float32)
        v = float(rng.uniform(0.0, 0.3))
        w = float(rng.uniform(-0.5, 0.5))
        t0 = time.perf_counter()
        mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_state)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

    latencies = np.array(latencies)
    mean_l = float(np.mean(latencies))
    p95_l = float(np.percentile(latencies, 95))

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.hist(latencies, bins=25, color="#2ca02c", edgecolor="black", alpha=0.85, density=True)
    ax.axvline(mean_l, color="blue", linestyle="--", linewidth=2.0, label=f"Mean Latency ({mean_l:.2f} ms)")
    ax.axvline(p95_l, color="purple", linestyle="--", linewidth=2.0, label=f"p95 Latency ({p95_l:.2f} ms)")
    ax.axvline(45.0, color="crimson", linestyle=":", linewidth=2.0, label="Budget Ceiling (45.0 ms)")
    ax.set_xlabel("Deliberation Latency (ms)", fontweight="bold", fontsize=13)
    ax.set_ylabel("Probability Density", fontweight="bold", fontsize=13)
    ax.set_title("Vectorized MPPI Cognitive Cycle Latency Distribution (M=128, H=15)", fontweight="bold", fontsize=15, pad=12)
    ax.legend(loc="upper right", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)
    out2 = OUTPUT_DIR / "fig_stage3_3_cycle_latency.png"
    plt.savefig(out2, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out2}")

    # 3. Obstacle Negotiation: Mean Hull Clearance (Single Plot)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    controllers = ["Discrete Baseline\n(Stage 2 Frozen)", "Continuous MPPI\n(Stage 3.3 Engine)"]
    clearances = [0.1464, 0.1737]
    bars = ax.bar(controllers, clearances, color=["#7f7f7f", "#1f77b4"], width=0.45, edgecolor="black", alpha=0.85)
    ax.set_ylabel("Mean Minimum Hull Clearance (m)", fontweight="bold", fontsize=13)
    ax.set_title("Physical Hull Margin in Tortuous Obstacle Mazes", fontweight="bold", fontsize=15, pad=12)
    ax.set_ylim(0, 0.24)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.005, f"{h:.4f} m", ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.text(0.5, 0.20, "+18.7% Clearance Gain (ΔC_hull = +0.0273 m)", ha="center", va="center",
            fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0fdf4", edgecolor="#16a34a", lw=1.5))
    out3 = OUTPUT_DIR / "fig_stage3_3_hull_clearance.png"
    plt.savefig(out3, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out3}")


def generate_stage3_4_single_plots():
    print("Generating Stage 3.4 independent single plots...")
    from tests.generate_stage3_4R4_2_figures import load_datasets
    r41_map, r42_map, r42_diag, r42_raw = load_datasets()

    # 1. Heading Error Comparison: R4.1 vs R4.2 (Config 22 - Single Plot)
    cfg_id = 22
    ep41 = r41_map.get(cfg_id)
    ep42 = r42_map.get(cfg_id)
    if ep41 and ep42:
        t41 = [t["tick"] * 0.03 for t in ep41["ticks"]]
        err41 = [t["fused_heading_error_deg"] for t in ep41["ticks"]]
        t42 = [t["tick"] * 0.03 for t in ep42["ticks"]]
        err42 = [t["r42_error_deg"] for t in ep42["ticks"]]

        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
        ax.plot(t41, err41, color="#dc2626", linewidth=2.2, alpha=0.9, label="R4.1 Baseline (Ungated Sonar Heading Error, Peak 61.0°)")
        ax.plot(t42, err42, color="#16a34a", linewidth=2.2, label="R4.2 Gated (Sonar Validity Gating Error, Peak 24.3°)")
        ax.axhline(15.0, color="#6b7280", linestyle="--", linewidth=1.8, label="Feasibility Tolerance Target (15.0°)")
        ax.set_xlabel("Time in Episode (seconds)", fontweight="bold", fontsize=13)
        ax.set_ylabel("Absolute Heading Error (degrees)", fontweight="bold", fontsize=13)
        ax.set_title("Dynamic Heading Estimation Error — R4.1 Baseline vs R4.2 Gated (Config 22)", fontweight="bold", fontsize=15, pad=12)
        ax.legend(loc="upper right", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_ylim(0, 70)
        out1 = OUTPUT_DIR / "fig_stage3_4_heading_error_config22.png"
        plt.savefig(out1, bbox_inches="tight")
        plt.close()
        print(f"Saved: {out1}")

    # 2. Heading Error Reduction Summary Across All Configs (Single Plot)
    configs = [20, 21, 22, 23, 24]
    err_r41 = [16.7, 48.8, 61.0, 44.7, 49.8]
    err_r42 = [7.1, 27.2, 24.3, 28.9, 20.3]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    x = np.arange(len(configs))
    width = 0.35
    b1 = ax.bar(x - width/2, err_r41, width, label="R4.1 Ungated Baseline", color="#ef4444", edgecolor="black")
    b2 = ax.bar(x + width/2, err_r42, width, label="R4.2 Corner Gating Remediated", color="#22c55e", edgecolor="black")
    ax.set_xlabel("Test Maze Configuration", fontweight="bold", fontsize=13)
    ax.set_ylabel("Peak Heading Error (degrees)", fontweight="bold", fontsize=13)
    ax.set_title("Peak Heading Error Reduction Across Asymmetric T-Junction Configs", fontweight="bold", fontsize=15, pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Config {c}" for c in configs], fontsize=11)
    ax.legend(loc="upper right", fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(0, 70)
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}°", ha="center", va="bottom", fontsize=11, fontweight="bold")
    out2 = OUTPUT_DIR / "fig_stage3_4_heading_reduction_summary.png"
    plt.savefig(out2, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out2}")


if __name__ == "__main__":
    generate_stage3_2_single_plots()
    generate_stage3_3_single_plots()
    generate_stage3_4_single_plots()
    print("\nAll independent single plots generated successfully in:", OUTPUT_DIR)

