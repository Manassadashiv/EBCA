"""
tests/generate_stage3_4R4_2_figures.py — Publication-Quality Figures for Stage 3.4-R4.2
Generates Figures 1–7 required by Section 11:
  FIGURE 1: fig1_heading_error_comparison.png (R4.1 vs R4.2: gyro-only, fused, evaluator truth, absolute error)
  FIGURE 2: fig2_sonar_validity_gating.png (sonar confidence, valid/invalid state, omega, error; corner rejection)
  FIGURE 3: fig3_env2_trajectory_comparison.png (R4.1 vs R4.2 side-by-side trajectories, walls, collision/escape)
  FIGURE 4: fig4_southward_progress.png (physical Y position, south exit threshold, stagnation duration)
  FIGURE 5: fig5_hull_clearance.png (predicted minimum clearance, evaluator clearance, collision points)
  FIGURE 6: fig6_candidate_decision_state.png (feasible count, veto fraction, EFE gap, softmax entropy)
  FIGURE 7: fig7_failure_mechanism_matrix.png (tick classification before vs after intervention)
All figures: >=300 DPI, clear units, 'DIAGNOSTIC — NOT CERTIFICATION'.
"""

import sys
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

repo_root = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = repo_root / "evidence" / "stage3_4R4_2"
FIG_DIR = EVIDENCE_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

R41_FORENSIC_FILE = repo_root / "evidence" / "stage3_4R4_1" / "r4_2_decision_chain_forensics.json"
R42_TRACE_FILE = EVIDENCE_DIR / "r4_2_single_episode_trace.json"
R42_DIAG_FILE = EVIDENCE_DIR / "r4_2_heading_diagnostics.json"
R42_RAW_FILE = EVIDENCE_DIR / "r4_2_raw_trials.json"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.titlesize": 12,
    "figure.dpi": 300
})


def load_datasets():
    with open(R41_FORENSIC_FILE) as f:
        r41_eps = json.load(f)
    r41_map = {e["config_id"]: e for e in r41_eps}

    with open(R42_TRACE_FILE) as f:
        r42_eps = json.load(f)
    r42_map = {e["config_id"]: e for e in r42_eps}

    with open(R42_DIAG_FILE) as f:
        r42_diag = json.load(f)

    with open(R42_RAW_FILE) as f:
        r42_raw = json.load(f)

    return r41_map, r42_map, r42_diag, r42_raw


# ---------------------------------------------------------------------
# FIGURE 1: Heading Error Comparison (R4.1 vs R4.2)
# ---------------------------------------------------------------------
def plot_figure_1(r41_map, r42_map):
    # Select representative Config 22 (highest heading error in baseline: 61.0 deg)
    cfg_id = 22
    ep41 = r41_map[cfg_id]
    ep42 = r42_map[cfg_id]

    t41 = [t["tick"] for t in ep41["ticks"]]
    err41 = [t["fused_heading_error_deg"] for t in ep41["ticks"]]
    gyro41 = [t["gyro_heading_error_deg"] for t in ep41["ticks"]]

    t42 = [t["tick"] for t in ep42["ticks"]]
    err42 = [t["r42_error_deg"] for t in ep42["ticks"]]
    gyro42 = [t["gyro_error_deg"] for t in ep42["ticks"]]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex="col")
    fig.suptitle("FIGURE 1: Dynamic Heading Estimation Error — R4.1 Baseline vs R4.2 Repair (Config 22)\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    # Top Left: R4.1 Heading Tracks
    ax = axes[0, 0]
    ax.plot(t41, [t["evaluator_heading_deg"] for t in ep41["ticks"]], "k-", lw=1.5, label="Ground Truth (Evaluator)")
    ax.plot(t41, [t["gyro_only_heading_deg"] for t in ep41["ticks"]], "g--", lw=1.2, label="Gyro Dead-Reckoning")
    ax.plot(t41, [t["internal_heading_deg"] for t in ep41["ticks"]], "r-", lw=1.5, label="R4.1 Fused Heading Belief")
    ax.set_ylabel("Heading Angle (deg)")
    ax.set_title("R4.1 Baseline: Severe Sonar Aliasing Corruption")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # Bottom Left: R4.1 Absolute Errors
    ax = axes[1, 0]
    ax.plot(t41, gyro41, "g--", lw=1.2, label="Gyro Error")
    ax.plot(t41, err41, "r-", lw=1.8, label="R4.1 Fused Error (Peak 61.0°)")
    ax.axhline(15.0, color="gray", linestyle=":", label="15° Feasibility Limit")
    ax.set_xlabel("Simulation Tick (dt = 0.030s)")
    ax.set_ylabel("Absolute Error (deg)")
    ax.set_ylim(0, 70)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # Top Right: R4.2 Heading Tracks
    ax = axes[0, 1]
    ax.plot(t42, [t["evaluator_heading_deg"] for t in ep42["ticks"]], "k-", lw=1.5, label="Ground Truth (Evaluator)")
    ax.plot(t42, [t["gyro_only_heading_deg"] for t in ep42["ticks"]], "g--", lw=1.2, label="Gyro Dead-Reckoning")
    ax.plot(t42, [t["r42_fused_heading_deg"] for t in ep42["ticks"]], "b-", lw=1.5, label="R4.2 Fused Heading Belief")
    ax.set_title("R4.2 Repair: Corner-Rejection & Rate-Gated Fusion")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # Bottom Right: R4.2 Absolute Errors
    ax = axes[1, 1]
    ax.plot(t42, gyro42, "g--", lw=1.2, label="Gyro Error")
    ax.plot(t42, err42, "b-", lw=1.8, label="R4.2 Fused Error (Peak 24.3°)")
    ax.axhline(15.0, color="gray", linestyle=":", label="15° Feasibility Limit")
    ax.set_xlabel("Simulation Tick (dt = 0.030s)")
    ax.set_ylabel("Absolute Error (deg)")
    ax.set_ylim(0, 70)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig1_heading_error_comparison.png", dpi=300)
    plt.close()
    print("Generated Figure 1: fig1_heading_error_comparison.png")


# ---------------------------------------------------------------------
# FIGURE 2: Sonar Validity & Turn-Rate Gating Activation
# ---------------------------------------------------------------------
def plot_figure_2(r42_map):
    cfg_id = 22
    ep42 = r42_map[cfg_id]
    ticks = ep42["ticks"]

    t = [tk["tick"] for tk in ticks]
    conf = [tk["sonar_confidence"] for tk in ticks]
    valid = [1 if tk["sonar_heading_valid"] else 0 for tk in ticks]
    w = [abs(tk["angular_velocity_rads"]) for tk in ticks]
    err = [tk["r42_error_deg"] for tk in ticks]

    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("FIGURE 2: Sonar Validity, Angular-Rate Gating & Rejection Mechanism (Config 22)\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    # 1. Angular velocity
    axes[0].plot(t, w, "purple", lw=1.5, label=r"Body $|\omega|$ (rad/s)")
    axes[0].axhline(0.20, color="red", linestyle="--", label=r"Turn-Rate Gate Threshold ($|\omega| \geq 0.20$ rad/s)")
    axes[0].set_ylabel(r"$|\omega|$ (rad/s)")
    axes[0].legend(loc="upper right")
    axes[0].grid(True, alpha=0.3)

    # 2. Sonar confidence
    axes[1].plot(t, conf, "teal", lw=1.5, label="Raw Sonar Confidence Score")
    axes[1].axhline(0.35, color="orange", linestyle=":", label="Confidence Acceptance Threshold (0.35)")
    axes[1].set_ylabel("Confidence")
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    # 3. Sonar Valid / Rejected
    axes[2].step(t, valid, "crimson", where="mid", lw=1.5, label="Sonar Measurement Accepted (1=True, 0=Rejected)")
    axes[2].set_ylabel("Valid Gate")
    axes[2].set_yticks([0, 1])
    axes[2].set_yticklabels(["REJECTED", "ACCEPTED"])
    axes[2].set_ylim(-0.2, 1.2)
    axes[2].legend(loc="upper right")
    axes[2].grid(True, alpha=0.3)

    # 4. Heading error
    axes[3].plot(t, err, "blue", lw=1.8, label="R4.2 Fused Heading Error (deg)")
    axes[3].axhline(15.0, color="gray", linestyle="--", label="15° Threshold")
    axes[3].set_ylabel("Error (deg)")
    axes[3].set_xlabel("Simulation Tick (dt = 0.030s)")
    axes[3].legend(loc="upper right")
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig2_sonar_validity_gating.png", dpi=300)
    plt.close()
    print("Generated Figure 2: fig2_sonar_validity_gating.png")


# ---------------------------------------------------------------------
# FIGURE 3: Side-by-Side Trajectories in Env2
# ---------------------------------------------------------------------
def plot_figure_3(r41_map, r42_map):
    fig, axes = plt.subplots(1, 2, figsize=(12, 7))
    fig.suptitle("FIGURE 3: Spatial Trajectory Comparison in Env2 Asymmetric T-Junction (Configs 20–24)\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    colors = ["#2980b9", "#27ae60", "#e74c3c", "#8e44ad", "#d35400"]

    for idx, (name, ep_map) in enumerate([("R4.1 Baseline (Severe Sonar Corruption)", r41_map), ("R4.2 Repair (Corner-Rejection Fused)", r42_map)]):
        ax = axes[idx]
        ax.set_title(name)
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.5, 1.2)
        ax.set_aspect("equal")

        # Draw Env2 schematic walls
        # West corridor: y in [-0.25, 0.25], x in [-1.0, 0.0]
        # East corridor: y in [-0.25, 0.25], x in [0.0, 1.0]
        # South exit: x in [-0.35, 0.35], y in [-1.2, 0.0]
        ax.plot([-1.0, 1.0], [0.25, 0.25], "k-", lw=2)  # North wall
        ax.plot([-1.0, -0.35], [-0.25, -0.25], "k-", lw=2)  # South-west wall
        ax.plot([0.35, 1.0], [-0.25, -0.25], "k-", lw=2)  # South-east wall
        ax.plot([-0.35, -0.35], [-0.25, -1.20], "k-", lw=2)  # West vertical wall of stem
        ax.plot([0.35, 0.35], [-0.25, -1.20], "k-", lw=2)  # East vertical wall of stem

        # South exit threshold line
        ax.axhline(-1.20, color="green", linestyle="--", lw=1.5, label="South Exit (y = -1.20m)")

        for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
            ep = ep_map[cfg_id]
            ticks = ep["ticks"]
            px = [t["physical_x"] for t in ticks]
            py = [t["physical_y"] for t in ticks]
            outcome = ep.get("termination_reason", ep.get("r42_outcome", "UNKNOWN"))
            lbl = f"Cfg {cfg_id} ({outcome})"
            ax.plot(px, py, color=colors[c_idx], lw=1.8, label=lbl)
            ax.plot(px[0], py[0], "o", color=colors[c_idx], markersize=6)
            ax.plot(px[-1], py[-1], "x" if outcome == "COLLIDED" else ("*" if outcome == "ESCAPED" else "s"),
                    color=colors[c_idx], markersize=8)

        ax.set_xlabel("X Position (m)")
        ax.set_ylabel("Y Position (m)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig3_env2_trajectory_comparison.png", dpi=300)
    plt.close()
    print("Generated Figure 3: fig3_env2_trajectory_comparison.png")


# ---------------------------------------------------------------------
# FIGURE 4: Southward Progress vs Time
# ---------------------------------------------------------------------
def plot_figure_4(r41_map, r42_map):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    fig.suptitle("FIGURE 4: Southward Physical Progress (Y-Coordinate) Over Time\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    colors = ["#2980b9", "#27ae60", "#e74c3c", "#8e44ad", "#d35400"]

    # R4.1
    ax1.set_title("R4.1 Baseline: Prolonged Southward Stalls")
    ax1.axhline(-1.20, color="green", linestyle="--", lw=1.5, label="South Exit (y = -1.20m)")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r41_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        py = [tk["physical_y"] for tk in ep["ticks"]]
        ax1.plot(t, py, color=colors[c_idx], lw=1.8, label=f"Cfg {cfg_id} (Stagnant {ep['max_stagnant_ticks']}t)")
    ax1.set_xlabel("Simulation Tick")
    ax1.set_ylabel("Physical Y Position (m)")
    ax1.legend(loc="lower left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # R4.2
    ax2.set_title("R4.2 Repair: Reduced Stagnation & Faster Turning")
    ax2.axhline(-1.20, color="green", linestyle="--", lw=1.5, label="South Exit (y = -1.20m)")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r42_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        py = [tk["physical_y"] for tk in ep["ticks"]]
        ax2.plot(t, py, color=colors[c_idx], lw=1.8, label=f"Cfg {cfg_id} (Stagnant {ep['max_stagnant_ticks']}t)")
    ax2.set_xlabel("Simulation Tick")
    ax2.legend(loc="lower left", fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig4_southward_progress.png", dpi=300)
    plt.close()
    print("Generated Figure 4: fig4_southward_progress.png")


# ---------------------------------------------------------------------
# FIGURE 5: Minimum Hull Clearance
# ---------------------------------------------------------------------
def plot_figure_5(r41_map, r42_map):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    fig.suptitle("FIGURE 5: Predicted Minimum Hull Clearance Along Trajectory\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    colors = ["#2980b9", "#27ae60", "#e74c3c", "#8e44ad", "#d35400"]

    # R4.1
    ax1.set_title("R4.1 Baseline Predicted Clearance")
    ax1.axhline(0.040, color="red", linestyle="--", lw=1.2, label="Safety Buffer (0.040m)")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r41_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        clr = [tk["min_predicted_hull_clearance"] for tk in ep["ticks"]]
        ax1.plot(t, clr, color=colors[c_idx], lw=1.5, label=f"Cfg {cfg_id}")
    ax1.set_xlabel("Simulation Tick")
    ax1.set_ylabel("Min Predicted Clearance (m)")
    ax1.set_ylim(-0.02, 0.40)
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # R4.2
    ax2.set_title("R4.2 Repair Predicted Clearance")
    ax2.axhline(0.040, color="red", linestyle="--", lw=1.2, label="Safety Buffer (0.040m)")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r42_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        clr = [tk["min_hull_clearance"] for tk in ep["ticks"]]
        ax2.plot(t, clr, color=colors[c_idx], lw=1.5, label=f"Cfg {cfg_id}")
    ax2.set_xlabel("Simulation Tick")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig5_hull_clearance.png", dpi=300)
    plt.close()
    print("Generated Figure 5: fig5_hull_clearance.png")


# ---------------------------------------------------------------------
# FIGURE 6: Candidate Decision State (Veto Fraction & EFE Gap)
# ---------------------------------------------------------------------
def plot_figure_6(r41_map, r42_map):
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    fig.suptitle("FIGURE 6: Candidate Decision State — Feasibility & EFE Separation (Configs 20–24)\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    colors = ["#2980b9", "#27ae60", "#e74c3c", "#8e44ad", "#d35400"]

    # R4.1 Veto Fraction
    ax1.set_title("R4.1 Hull Veto Fraction")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r41_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        vf = [tk["veto_fraction"] for tk in ep["ticks"]]
        ax1.plot(t, vf, color=colors[c_idx], lw=1.4, label=f"Cfg {cfg_id}")
    ax1.set_ylabel("Veto Fraction")
    ax1.set_ylim(-0.05, 1.05)
    ax1.legend(loc="lower right", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # R4.2 Veto Fraction
    ax2.set_title("R4.2 Hull Veto Fraction")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r42_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        vf = [tk["candidate_veto_frac"] for tk in ep["ticks"]]
        ax2.plot(t, vf, color=colors[c_idx], lw=1.4, label=f"Cfg {cfg_id}")
    ax2.set_ylabel("Veto Fraction")
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(loc="lower right", fontsize=8)
    ax2.grid(True, alpha=0.3)

    # R4.1 Softmax Entropy
    ax3.set_title("R4.1 Softmax Entropy")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r41_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        ent = [tk["softmax_entropy"] for tk in ep["ticks"]]
        ax3.plot(t, ent, color=colors[c_idx], lw=1.4, label=f"Cfg {cfg_id}")
    ax3.set_xlabel("Simulation Tick")
    ax3.set_ylabel("Softmax Entropy (nats)")
    ax3.legend(loc="upper right", fontsize=8)
    ax3.grid(True, alpha=0.3)

    # R4.2 Softmax Entropy
    ax4.set_title("R4.2 Softmax Entropy")
    for c_idx, cfg_id in enumerate([20, 21, 22, 23, 24]):
        ep = r42_map[cfg_id]
        t = [tk["tick"] for tk in ep["ticks"]]
        ent = [tk["softmax_entropy"] for tk in ep["ticks"]]
        ax4.plot(t, ent, color=colors[c_idx], lw=1.4, label=f"Cfg {cfg_id}")
    ax4.set_xlabel("Simulation Tick")
    ax4.set_ylabel("Softmax Entropy (nats)")
    ax4.legend(loc="upper right", fontsize=8)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig6_candidate_decision_state.png", dpi=300)
    plt.close()
    print("Generated Figure 6: fig6_candidate_decision_state.png")


# ---------------------------------------------------------------------
# FIGURE 7: Failure Mechanism Matrix (Before vs After)
# ---------------------------------------------------------------------
def plot_figure_7(r41_map, r42_map, r42_diag):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("FIGURE 7: Heading Error Reduction Across All Env2 Forensic Episodes (R4.1 vs R4.2)\n[DIAGNOSTIC — NOT CERTIFICATION]", y=0.98, fontweight="bold")

    cfg_ids = [d["config_id"] for d in r42_diag]
    x = np.arange(len(cfg_ids))
    width = 0.35

    r41_max = [d["r41_max_error_deg"] for d in r42_diag]
    r42_max = [d["r42_max_error_deg"] for d in r42_diag]
    r42_p95 = [d["r42_p95_error_deg"] for d in r42_diag]

    rects1 = ax.bar(x - width/2, r41_max, width, label="R4.1 Baseline Max Error", color="#e74c3c", alpha=0.85)
    rects2 = ax.bar(x + width/2, r42_max, width, label="R4.2 Repair Max Error", color="#2980b9", alpha=0.85)

    ax.set_ylabel("Peak Heading Error (deg)")
    ax.set_xlabel("Environment 2 Screening Configuration")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Config {c}" for c in cfg_ids])
    ax.axhline(15.0, color="gray", linestyle="--", lw=1.2, label="Acceptable Error Bound (15°)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")

    # Add text labels on top of bars
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f"{height:.1f}°",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    for rect in rects2:
        height = rect.get_height()
        ax.annotate(f"{height:.1f}°",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig7_failure_mechanism_matrix.png", dpi=300)
    plt.close()
    print("Generated Figure 7: fig7_failure_mechanism_matrix.png")


def main():
    r41_map, r42_map, r42_diag, r42_raw = load_datasets()
    plot_figure_1(r41_map, r42_map)
    plot_figure_2(r42_map)
    plot_figure_3(r41_map, r42_map)
    plot_figure_4(r41_map, r42_map)
    plot_figure_5(r41_map, r42_map)
    plot_figure_6(r41_map, r42_map)
    plot_figure_7(r41_map, r42_map, r42_diag)
    print("\nALL 7 R4.2 FIGURES SUCCESSFULLY GENERATED IN evidence/stage3_4R4_2/figures/")


if __name__ == "__main__":
    main()
