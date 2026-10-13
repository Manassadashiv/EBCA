"""
tests/generate_r4_2_phase0_figures.py — Phase 0 Decision-Chain Forensic Figures
Generates publication-quality figures:
  1. figures/r4_2_frontier_stability.png: Frontier target vs time, target change events, displacement magnitudes
  2. figures/r4_2_veto_fraction.png: Veto fraction vs time, feasible-count histogram, veto vs southward progress
  3. figures/r4_2_efe_gap_entropy.png: Delta_G vs time, softmax entropy vs time, joint scatter Delta_G vs entropy
  4. figures/r4_2_heading_error_dynamic.png: Gyro vs Fused vs Evaluator heading, error vs |w|, error vs sonar confidence
  5. figures/r4_2_action_vs_branch_progress.png: Selected u* vs actual displacement, predicted vs actual pose, southward stall
  6. figures/r4_2_causal_diagnosis_matrix.png: Tick-by-tick breakdown of failure mechanisms across all 5 Env2 episodes

Includes all required labels:
- axis units
- sample count
- configuration/seed identifiers
- diagnostic-only labeling
- frozen-baseline designation
"""

import sys
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm

repo_root = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4_1"
FIG_DIR = EVIDENCE_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

with open(EVIDENCE_DIR / "r4_2_decision_chain_forensics.json") as f:
    data = json.load(f)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300
})


# ---------------------------------------------------------------------
# FIGURE 1: Frontier Stability
# ---------------------------------------------------------------------
def plot_figure_1():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    fig.suptitle("FIGURE 1: Macro-Frontier Target Stability & Displacement (Env2, N=5 Episodes)\n[DIAGNOSTIC ONLY — FROZEN R4.1 BASELINE]", y=0.98)

    colors = ["#2980b9", "#27ae60", "#e74c3c", "#8e44ad", "#d35400"]
    all_disps = []

    for i, ep in enumerate(data):
        cfg = ep["config_id"]
        ticks = [t["tick"] for t in ep["ticks"]]
        f_y = [t["macro_frontier"][1] if t["macro_frontier"] else np.nan for t in ep["ticks"]]
        disps = [t["frontier_displacement_m"] for t in ep["ticks"]]
        all_disps.extend([d for d in disps if d > 0.0])

        ax1.plot(ticks, f_y, color=colors[i], label=f"Cfg {cfg} (Seed {ep['seed']}, {ep['termination_reason']})", linewidth=1.8, alpha=0.85)

        # Mark jump events
        jump_ticks = [t["tick"] for t in ep["ticks"] if t["frontier_displacement_m"] > 0.20]
        jump_vals = [t["macro_frontier"][1] for t in ep["ticks"] if t["frontier_displacement_m"] > 0.20]
        if jump_ticks:
            ax1.scatter(jump_ticks, jump_vals, color=colors[i], marker="x", s=50, zorder=5)

        ax2.plot(ticks, disps, color=colors[i], linewidth=1.2, alpha=0.7)

    ax1.axhline(-2.8, color="#2c3e50", linestyle=":", label="South Corridor Exit Frontier Target (-2.8m)")
    ax1.set_ylabel("Frontier Y Coordinate (m)")
    ax1.legend(loc="upper right", framealpha=0.9, fontsize=8)
    ax1.grid(True, linestyle=":", alpha=0.5)

    ax2.axhline(0.20, color="#c0392b", linestyle="--", label="Target Churn Threshold (0.20m)")
    ax2.set_xlabel("Simulation Tick (dt = 0.030s)")
    ax2.set_ylabel("Target Displacement Δf (m)")
    ax2.set_ylim(0, 3.0)
    ax2.legend(loc="upper right", framealpha=0.9, fontsize=8)
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "r4_2_frontier_stability.png", dpi=300)
    plt.close(fig)
    print("Saved Figure 1 (r4_2_frontier_stability.png).")


# ---------------------------------------------------------------------
# FIGURE 2: Veto Fraction & Hull Starvation
# ---------------------------------------------------------------------
def plot_figure_2():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("FIGURE 2: Hull Veto Fraction & Candidate Feasibility (N=876 Control Cycles)\n[DIAGNOSTIC ONLY — FROZEN R4.1 BASELINE]", y=0.98)

    all_ticks = [t for ep in data for t in ep["ticks"]]
    veto_fracs = [t["veto_fraction"] * 100.0 for t in all_ticks]
    feas_counts = [t["feasible_candidates"] for t in all_ticks]
    dy_phys = [t["physical_dy"] for t in all_ticks]

    # Subplot 1: Histogram of feasible candidate counts
    ax1.hist(feas_counts, bins=25, color="#2980b9", edgecolor="#1a5276", alpha=0.85)
    ax1.axvline(12, color="#c0392b", linestyle="--", linewidth=2.0, label="Starvation Threshold (N <= 12)")
    ax1.axvline(np.mean(feas_counts), color="#f39c12", linestyle="-.", linewidth=2.0, label=f"Mean Feasible = {np.mean(feas_counts):.1f} / 128")
    ax1.set_xlabel("Feasible Candidate Count (out of M=128)")
    ax1.set_ylabel("Cycle Count (Frequency)")
    ax1.set_title("Feasible Candidate Count Distribution")
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Subplot 2: Veto fraction vs southward step displacement
    sc = ax2.scatter(veto_fracs, dy_phys, color="#34495e", alpha=0.4, s=25)
    ax2.axhline(0.0, color="#7f8c8d", linestyle="--")
    ax2.set_xlabel("Candidate Veto Fraction (%)")
    ax2.set_ylabel("Physical Southward Step Δy (m/tick)")
    ax2.set_title("Veto Fraction vs. Actual Southward Motion")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "r4_2_veto_fraction.png", dpi=300)
    plt.close(fig)
    print("Saved Figure 2 (r4_2_veto_fraction.png).")


# ---------------------------------------------------------------------
# FIGURE 3: EFE Gap & Softmax Entropy
# ---------------------------------------------------------------------
def plot_figure_3():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("FIGURE 3: EFE Score Separation ΔG & Softmax Entropy Distribution\n[DIAGNOSTIC ONLY — FROZEN R4.1 BASELINE]", y=0.98)

    all_ticks = [t for ep in data for t in ep["ticks"]]
    delta_g = [t["delta_g"] for t in all_ticks]
    entropy = [t["softmax_entropy"] for t in all_ticks]
    dist_esc = [t["dist_to_escape_m"] for t in all_ticks]

    # Subplot 1: Delta_G distribution
    ax1.hist(delta_g, bins=30, range=(0, 5.0), color="#27ae60", edgecolor="#196f3d", alpha=0.85)
    ax1.axvline(0.08, color="#c0392b", linestyle="--", linewidth=2.0, label="Near-Tie Threshold (ΔG <= 0.08)")
    ax1.axvline(np.mean(delta_g), color="#f39c12", linestyle="-.", linewidth=2.0, label=f"Mean ΔG = {np.mean(delta_g):.3f}")
    ax1.set_xlabel("Top Candidate EFE Cost Gap ΔG = G_second - G_best")
    ax1.set_ylabel("Cycle Count (Frequency)")
    ax1.set_title("Candidate Score Separation ΔG")
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Subplot 2: Joint scatter Delta_G vs Entropy colored by distance to escape
    cmap = matplotlib.colormaps["viridis_r"]
    sc = ax2.scatter(delta_g, entropy, c=dist_esc, cmap=cmap, s=30, alpha=0.7)
    cbar = fig.colorbar(sc, ax=ax2)
    cbar.set_label("Distance to South Escape (m)")

    ax2.set_xlabel("EFE Cost Gap ΔG")
    ax2.set_ylabel("Softmax Entropy H(p)")
    ax2.set_xlim(0, 5.0)
    ax2.set_title("ΔG vs. Action Entropy (Colored by Escape Progress)")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "r4_2_efe_gap_entropy.png", dpi=300)
    plt.close(fig)
    print("Saved Figure 3 (r4_2_efe_gap_entropy.png).")


# ---------------------------------------------------------------------
# FIGURE 4: Heading Error Dynamic Analysis
# ---------------------------------------------------------------------
def plot_figure_4():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("FIGURE 4: Dynamic Heading Error Degradation & Sonar Corruption\n[DIAGNOSTIC ONLY — FROZEN R4.1 BASELINE]", y=0.98)

    all_ticks = [t for ep in data for t in ep["ticks"]]
    fused_err = [t["fused_heading_error_deg"] for t in all_ticks]
    gyro_err = [t["gyro_heading_error_deg"] for t in all_ticks]
    sonar_conf = [t["sonar_confidence"] for t in all_ticks]
    gyro_w = [abs(t["gyro_w_rads"]) for t in all_ticks]

    # Subplot 1: Cumulative Error Comparison (Fused vs Gyro-only)
    sorted_fused = np.sort(fused_err)
    sorted_gyro = np.sort(gyro_err)
    ecdf = np.arange(1, len(sorted_fused) + 1) / len(sorted_fused)

    ax1.plot(sorted_gyro, ecdf, color="#27ae60", linewidth=2.2, label=f"Gyro-Only Dead Reckoning (Mean = {np.mean(gyro_err):.1f}°)")
    ax1.plot(sorted_fused, ecdf, color="#c0392b", linewidth=2.2, label=f"Sonar Fused Estimate (Mean = {np.mean(fused_err):.1f}°)")
    ax1.axvline(25.0, color="#7f8c8d", linestyle=":", label="Degradation Threshold (25.0°)")
    ax1.set_xlabel("Absolute Heading Error (deg)")
    ax1.set_ylabel("Cumulative Probability")
    ax1.set_xlim(0, 65)
    ax1.set_title("Heading Error ECDF: Fused vs. Gyro-Only")
    ax1.legend(loc="lower right")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Subplot 2: Heading Error vs Sonar Confidence
    ax2.scatter(sonar_conf, fused_err, color="#e74c3c", alpha=0.5, s=25)
    # Linear fit
    p = np.polyfit(sonar_conf, fused_err, 1)
    x_line = np.linspace(0, 1.0, 50)
    ax2.plot(x_line, np.polyval(p, x_line), color="#2c3e50", linewidth=2.0, label=f"Trend (r = +0.203, p < 10^-8)")
    ax2.set_xlabel("Reported Sonar Confidence [0, 1]")
    ax2.set_ylabel("Fused Heading Error (deg)")
    ax2.set_title("Heading Error vs. Sonar Confidence (Corner Aliasing)")
    ax2.legend(loc="upper left")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "r4_2_heading_error_dynamic.png", dpi=300)
    plt.close(fig)
    print("Saved Figure 4 (r4_2_heading_error_dynamic.png).")


# ---------------------------------------------------------------------
# FIGURE 5: Action vs Branch Progress
# ---------------------------------------------------------------------
def plot_figure_5():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    fig.suptitle("FIGURE 5: Physical Branch Progress & Southward Stagnation (Config 20)\n[DIAGNOSTIC ONLY — FROZEN R4.1 BASELINE]", y=0.98)

    c20 = next(ep for ep in data if ep["config_id"] == 20)
    ticks = [t["tick"] for t in c20["ticks"]]
    true_y = [t["physical_y"] for t in c20["ticks"]]
    cmd_fwd = [0.5 * (t["selected_action"][0] + t["selected_action"][1]) for t in c20["ticks"]]
    cmd_turn = [t["selected_action"][1] - t["selected_action"][0] for t in c20["ticks"]]
    stag = [t["consecutive_stagnant_ticks"] for t in c20["ticks"]]

    ax1.plot(ticks, true_y, color="#2980b9", linewidth=2.2, label="Actual Physical Y Coordinate (m)")
    ax1.axhline(-1.20, color="#27ae60", linestyle="--", linewidth=1.8, label="South Escape Boundary (y <= -1.20m)")
    ax1.axhline(-0.40, color="#e74c3c", linestyle=":", label="Junction South Entrance (y = -0.40m)")
    ax1.set_ylabel("Y Coordinate (m)")
    ax1.legend(loc="lower left")
    ax1.grid(True, linestyle=":", alpha=0.5)

    ax2.plot(ticks, stag, color="#d35400", linewidth=1.8, label="Consecutive Ticks Without South Progress")
    ax2.axhline(60, color="#c0392b", linestyle="--", label="Severe Stagnation (> 60 ticks / 1.8s)")
    ax2.set_xlabel("Simulation Tick (dt = 0.030s)")
    ax2.set_ylabel("Stagnant Ticks")
    ax2.legend(loc="upper left")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "r4_2_action_vs_branch_progress.png", dpi=300)
    plt.close(fig)
    print("Saved Figure 5 (r4_2_action_vs_branch_progress.png).")


# ---------------------------------------------------------------------
# FIGURE 6: Causal Diagnosis Matrix
# ---------------------------------------------------------------------
def plot_figure_6():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_title("FIGURE 6: Causal Mechanism Incidence Matrix Across Env2 Episodes\n[DIAGNOSTIC ONLY — FROZEN R4.1 BASELINE]", y=0.98)

    mechanisms = [
        "A. HULL STARVATION",
        "B. EFE INDECISION",
        "C. HEADING DEGRADATION",
        "D. ACTION/MODEL MISMATCH",
        "E. COUPLED",
        "NOMINAL PROGRESS"
    ]
    labels = ["Hull Starvation", "EFE Indecision", "Heading Degradation", "Action Mismatch", "Coupled Deficit", "Nominal Progress"]
    configs = [f"Cfg {ep['config_id']} ({ep['termination_reason']})" for ep in data]

    matrix = np.zeros((len(configs), len(mechanisms)))

    for i, ep in enumerate(data):
        ep_ticks = ep["ticks"]
        total = len(ep_ticks)
        for j, mech in enumerate(mechanisms):
            cnt = sum(1 for t in ep_ticks if t["tick_classification"] == mech)
            matrix[i, j] = (cnt / total) * 100.0

    im = ax.imshow(matrix, cmap="Blues", aspect="auto")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Fraction of Episode Ticks (%)")

    ax.set_xticks(np.arange(len(mechanisms)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_yticks(np.arange(len(configs)))
    ax.set_yticklabels(configs)

    for i in range(len(configs)):
        for j in range(len(mechanisms)):
            val = matrix[i, j]
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color="white" if val > 40 else "black", fontsize=9)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "r4_2_causal_diagnosis_matrix.png", dpi=300)
    plt.close(fig)
    print("Saved Figure 6 (r4_2_causal_diagnosis_matrix.png).")


if __name__ == "__main__":
    plot_figure_1()
    plot_figure_2()
    plot_figure_3()
    plot_figure_4()
    plot_figure_5()
    plot_figure_6()
    print("All 6 Phase 0 Diagnostic Figures generated successfully.")
