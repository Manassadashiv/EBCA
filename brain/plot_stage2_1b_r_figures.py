"""
brain/plot_stage2_1b_r_figures.py — Publication Figures for Stage 2.1B-R
Classification: [VISUAL FORENSIC EVIDENCE] 4-Substrate Showdown & Attractor Causality

Generates:
  Figure 1: figure1_dropout_persistence.png (Working Memory Bump Retention & Heading Error)
  Figure 2: figure2_information_recovery.png (Attractor Basin Shock Relaxation & Info Conservation)
  Figure 3: figure3_unwrapped_long_horizon.png (Multi-Torus Unwrapped Tracking vs Ground Truth)
  Figure 4: figure4_causality_scorecard.png (Comprehensive 4-Substrate Matrix across 8 Seeds)
"""

import os
import sys
import json
import math
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = "d:/ebca"
TELEMETRY_DIR = os.path.join(BASE_DIR, "evidence", "stage2_1b_r")
TELEMETRY_JSON = os.path.join(TELEMETRY_DIR, "stage2_1b_r_telemetry.json")
ARTIFACT_DIR = r"C:\Users\MANAS\.gemini\antigravity-ide\brain\69694e15-b8b9-4584-a63c-480d3a7e2d8a"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300
})


def generate_all_figures():
    if not os.path.exists(TELEMETRY_JSON):
        print(f"[ERROR] Telemetry file not found: {TELEMETRY_JSON}")
        return

    with open(TELEMETRY_JSON, "r") as f:
        data = json.load(f)

    b1 = data["battery1_dropout"]
    b2 = data["battery2_perturbation"]
    b3 = data["battery3_long_horizon"]
    seeds = [int(s) for s in b1.keys()]

    # ══════════════════════════════════════════════════════════════════════════
    # FIGURE 1: SENSOR DROPOUT & WORKING MEMORY PERSISTENCE
    # ══════════════════════════════════════════════════════════════════════════
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 1A: Bump Retention Ratio (Full CANN vs FF Ablation)
    x = np.arange(len(seeds))
    w = 0.35
    ret_full = [b1[str(s)]["bump_retention_full"] for s in seeds]
    ret_ff = [b1[str(s)]["bump_retention_ff"] for s in seeds]

    axes[0].bar(x - w/2, ret_full, width=w, label="Full CANN (W_rec active)", color="#00e5ff", edgecolor="black")
    axes[0].bar(x + w/2, ret_ff, width=w, label="Feedforward CANN (W_rec = 0)", color="#ff5252", edgecolor="black")
    axes[0].axhline(0.85, color="#00e5ff", linestyle="--", alpha=0.7, label="Retention Threshold (0.85)")
    axes[0].axhline(0.15, color="#ff5252", linestyle="--", alpha=0.7, label="Collapse Threshold (0.15)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"S{s}" for s in seeds])
    axes[0].set_ylabel("Bump Amplitude Retention (R_post / R_pre)")
    axes[0].set_title("1A: Working Memory Bump Retention during 2.7s Blackout")
    axes[0].grid(True, linestyle=":", alpha=0.5)
    axes[0].legend(loc="lower right", fontsize=8)
    axes[0].set_ylim(-0.05, 1.15)

    # 1B: Heading Error across 4 Substrates
    err_full = [b1[str(s)]["err_full_deg"] for s in seeds]
    err_ff = [b1[str(s)]["err_ff_deg"] for s in seeds]
    err_class = [b1[str(s)]["err_classical_deg"] for s in seeds]
    err_d = [b1[str(s)]["err_d_deg"] for s in seeds]

    w4 = 0.20
    axes[1].bar(x - 1.5*w4, err_full, width=w4, label="Substrate A: Full CANN", color="#00e5ff")
    axes[1].bar(x - 0.5*w4, err_ff, width=w4, label="Substrate B: Feedforward", color="#ff5252")
    axes[1].bar(x + 0.5*w4, err_class, width=w4, label="Substrate C: Classical", color="#ffd600")
    axes[1].bar(x + 1.5*w4, err_d, width=w4, label="Substrate D: State Latch", color="#b388ff")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f"S{s}" for s in seeds])
    axes[1].set_ylabel("Post-Blackout Heading Error (deg)")
    axes[1].set_title("1B: Post-Blackout Heading Divergence under Dynamics")
    axes[1].grid(True, linestyle=":", alpha=0.5)
    axes[1].legend(loc="upper right", fontsize=8)

    fig.suptitle("CARL Stage 2.1B-R — Battery 1: Physically Changing Sensor Dropout Showdown", fontsize=13, fontweight="bold")
    plt.tight_layout()

    f1_path = os.path.join(TELEMETRY_DIR, "figure1_dropout_persistence.png")
    fig.savefig(f1_path)
    fig.savefig(os.path.join(ARTIFACT_DIR, "figure1_dropout_persistence.png"))
    plt.close(fig)
    print(f"[PLOT] Figure 1 saved: {f1_path}")

    # ══════════════════════════════════════════════════════════════════════════
    # FIGURE 2: NEURAL PERTURBATION & INFORMATION RECOVERY
    # ══════════════════════════════════════════════════════════════════════════
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 2A: Pattern Recovery vs Information Recovery
    pat_rec = [b2[str(s)]["pattern_recovery_full"] * 100 for s in seeds]
    info_err = [b2[str(s)]["d_theta_full_deg"] for s in seeds]

    axes[0].bar(x - w/2, pat_rec, width=w, label="Pattern Recovery (%)", color="#69f0ae", edgecolor="black")
    axes[0].axhline(80.0, color="#69f0ae", linestyle="--", label="Target Pattern Recovery (80%)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"S{s}" for s in seeds])
    axes[0].set_ylabel("Solitary Bump Amplitude Recovery (%)")
    axes[0].set_title("2A: Attractor Basin Pattern Recovery after Noise Shock eta ~ N(0, 2.0)")
    axes[0].grid(True, linestyle=":", alpha=0.5)
    axes[0].legend(loc="lower right", fontsize=8)
    axes[0].set_ylim(0, 110)

    # 2B: Information Recovery (Heading Error |theta_post - theta_pre|)
    axes[1].bar(x, info_err, width=0.4, label="Decoded Heading Deviation |theta_post - theta_pre|", color="#7c4dff", edgecolor="black")
    axes[1].axhline(15.0, color="#ff1744", linestyle="--", label="Information Loss Threshold (15.0 deg)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f"S{s}" for s in seeds])
    axes[1].set_ylabel("Heading Error Deviation (deg)")
    axes[1].set_title("2B: Decoded Information Conservation after Attractor Relaxation")
    axes[1].grid(True, linestyle=":", alpha=0.5)
    axes[1].legend(loc="upper right", fontsize=8)
    axes[1].set_ylim(0, 25)

    fig.suptitle("CARL Stage 2.1B-R — Battery 2: Attractor Basin Relaxation & Information Recovery", fontsize=13, fontweight="bold")
    plt.tight_layout()

    f2_path = os.path.join(TELEMETRY_DIR, "figure2_information_recovery.png")
    fig.savefig(f2_path)
    fig.savefig(os.path.join(ARTIFACT_DIR, "figure2_information_recovery.png"))
    plt.close(fig)
    print(f"[PLOT] Figure 2 saved: {f2_path}")

    # ══════════════════════════════════════════════════════════════════════════
    # FIGURE 3: UNWRAPPED LONG-HORIZON SPATIAL TRACKING
    # ══════════════════════════════════════════════════════════════════════════
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ate_full = [b3[str(s)]["ate_full_unwrapped_m"] * 100 for s in seeds]
    ate_class = [b3[str(s)]["ate_classical_m"] * 100 for s in seeds]
    max_dist = [b3[str(s)]["max_dist_from_origin"] for s in seeds]
    homing_drift = [b3[str(s)]["homing_drift_m"] * 100 for s in seeds]

    # 3A: Unwrapped ATE (Full CANN vs Classical)
    axes[0].bar(x - w/2, ate_full, width=w, label="Full CANN Unwrapped ATE", color="#00e5ff", edgecolor="black")
    axes[0].bar(x + w/2, ate_class, width=w, label="Classical Euler ATE", color="#ffd600", edgecolor="black")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"S{s}" for s in seeds])
    axes[0].set_ylabel("Average Trajectory Error (cm)")
    axes[0].set_title("3A: Unwrapped Trajectory Error over Multi-Torus Exploration")
    axes[0].grid(True, linestyle=":", alpha=0.5)
    axes[0].legend(loc="upper left", fontsize=8)

    # 3B: Autonomous Closed-Loop Homing Return
    axes[1].bar(x, homing_drift, width=0.45, label="Final Homing Return Drift", color="#00e676", edgecolor="black")
    axes[1].axhline(22.0, color="#ff1744", linestyle="--", label="Passing Bound (22.0 cm)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f"S{s}" for s in seeds])
    axes[1].set_ylabel("Origin Arrival Drift (cm)")
    axes[1].set_title("3B: Closed-Loop Return to Origin from Distant Boundary")
    axes[1].grid(True, linestyle=":", alpha=0.5)
    axes[1].legend(loc="upper left", fontsize=8)

    fig.suptitle("CARL Stage 2.1B-R — Battery 3: Unwrapped Multi-Torus Tracking & Autonomous Return", fontsize=13, fontweight="bold")
    plt.tight_layout()

    f3_path = os.path.join(TELEMETRY_DIR, "figure3_unwrapped_long_horizon.png")
    fig.savefig(f3_path)
    fig.savefig(os.path.join(ARTIFACT_DIR, "figure3_unwrapped_long_horizon.png"))
    plt.close(fig)
    print(f"[PLOT] Figure 3 saved: {f3_path}")

    # ══════════════════════════════════════════════════════════════════════════
    # FIGURE 4: COMPREHENSIVE 4-SUBSTRATE SCORECARD MATRIX
    # ══════════════════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")

    table_data = []
    headers = ["Seed", "Role", "B1: Working Memory", "B1: Full vs Class Err", "B2: Pattern Recov", "B2: Info Error", "B3: Unwrapped ATE", "B3: Homing Return"]

    for s in seeds:
        role = "DEV" if s in [42, 101, 202] else "UNSEEN"
        b1_res = "PASS" if b1[str(s)]["full_sustained"] and b1[str(s)]["ff_collapsed"] else "FAIL"
        b1_err = f"{b1[str(s)]['err_full_deg']:.1f}° vs {b1[str(s)]['err_classical_deg']:.1f}°"
        b2_pat = f"{b2[str(s)]['pattern_recovery_full']*100:.1f}%"
        b2_info = f"{b2[str(s)]['d_theta_full_deg']:.2f}°"
        b3_ate = f"{b3[str(s)]['ate_full_unwrapped_m']*100:.1f} cm"
        b3_hom = f"{b3[str(s)]['homing_drift_m']*100:.1f} cm [{'PASS' if b3[str(s)]['homing_pass'] else 'FAIL'}]"

        table_data.append([f"Seed {s}", role, b1_res, b1_err, b2_pat, b2_info, b3_ate, b3_hom])

    table = ax.table(cellText=table_data, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.15, 1.7)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#212121")
        elif "FAIL" in cell.get_text().get_text():
            cell.set_facecolor("#ffebee")
        elif "PASS" in cell.get_text().get_text():
            cell.set_facecolor("#e8f5e9")
        elif row % 2 == 1:
            cell.set_facecolor("#f5f5f5")

    ax.set_title("CARL Stage 2.1B-R — Master Multi-Seed Causality & Persistence Scorecard", fontsize=12, fontweight="bold", pad=20)
    plt.tight_layout()

    f4_path = os.path.join(TELEMETRY_DIR, "figure4_causality_scorecard.png")
    fig.savefig(f4_path)
    fig.savefig(os.path.join(ARTIFACT_DIR, "figure4_causality_scorecard.png"))
    plt.close(fig)
    print(f"[PLOT] Figure 4 saved: {f4_path}")


if __name__ == "__main__":
    generate_all_figures()
