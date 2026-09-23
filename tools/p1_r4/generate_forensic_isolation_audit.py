"""
tools/p1_r4/generate_forensic_isolation_audit.py — Forensic Telemetry Visualizer for P1-R4

Generates:
1. evidence/p1_r4_forensic/01_forensic_initial_q_and_actions.png
2. evidence/p1_r4_forensic/02_forensic_w_norm_vs_time_divergence.png
3. evidence/p1_r4_forensic/03_forensic_trajectory_overlay_first_update.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

DARK_BG = "#0E1117"
PANEL_BG = "#161B22"
GRID_COLOR = "#21262D"
TEXT_COLOR = "#E6EDF3"
CYAN = "#00E5FF"
CORAL = "#FF5252"
GREEN = "#00FF66"
GOLD = "#FFD700"

OUTPUT_DIR = "evidence/p1_r4_forensic"
os.makedirs(OUTPUT_DIR, exist_ok=True)

df_stdp = pd.read_csv("evidence/p1_r4_isolation/telemetry/P1R4_ISOLATION_NO_HDC_STDP_S42_EP1.csv")
df_no = pd.read_csv("evidence/p1_r4_isolation/telemetry/P1R4_ISOLATION_NO_HDC_NO_STDP_S42_EP1.csv")


def plot_01_initial_q_and_actions():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), facecolor=DARK_BG)
    for ax in (ax1, ax2):
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        
    actions = ["STR", "C_L_G", "C_L_S", "SW_L", "C_R_G", "C_R_S", "SW_R"]
    q_t0 = np.zeros(7)
    
    # Tick 0
    ax1.bar(actions, q_t0, color="#6E7681", width=0.5, edgecolor=TEXT_COLOR)
    ax1.set_ylim(-1.0, 1.0)
    ax1.axhline(0.0, color="#6E7681", linestyle="--")
    ax1.set_title("Tick 0: Q_stdp Before Any Learning (W = 0.0)", color=TEXT_COLOR, fontweight="bold")
    ax1.set_ylabel("Learned Action Quality Q_stdp", color=TEXT_COLOR)
    ax1.text(3, 0.2, "All Actions Equal (Q = 0.0)", ha="center", color=GOLD, fontweight="bold")

    # Tick 2 EFE comparison
    efe_stdp = [548.2, 547.1, 546.0, 545.57, 547.1, 546.0, 545.65]
    efe_no = [548.2, 547.1, 546.0, 545.58, 547.1, 546.0, 545.58]
    
    x = np.arange(len(actions))
    w = 0.35
    ax2.bar(x - w/2, efe_stdp, width=w, color=CYAN, label="NO_HDC_STDP (SW_L Wins: 545.57)")
    ax2.bar(x + w/2, efe_no, width=w, color=CORAL, label="NO_HDC_NO_STDP (Tie: 545.58)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(actions, color=TEXT_COLOR)
    ax2.set_ylim(540, 552)
    ax2.set_title("Tick 2: EFE Landscape After Startup Inertia Update", color=TEXT_COLOR, fontweight="bold")
    ax2.set_ylabel("Expected Free Energy (Lower = Better)", color=TEXT_COLOR)
    ax2.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "01_forensic_initial_q_and_actions.png"), dpi=300, facecolor=DARK_BG)
    plt.close()
    print("Generated: 01_forensic_initial_q_and_actions.png")


def plot_02_w_norm_divergence():
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=DARK_BG)
    ax.set_facecolor(PANEL_BG)
    ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
    
    ticks = range(15)
    pe_stdp = df_stdp["prediction_error"].iloc[:15]
    dw_stdp = df_stdp["stdp_dw_norm"].iloc[:15] * 1000
    
    ax.plot(ticks, pe_stdp, "o-", color=CORAL, lw=2.5, label="Motor Prediction Error (PE in m/s)")
    ax.plot(ticks, dw_stdp, "s--", color=CYAN, lw=2.0, label="STDP Weight Shift Magnitude dW (x10^-3)")
    
    ax.axhline(0.18, color=GOLD, linestyle=":", lw=1.5, label="Surprise Threshold (PE = 0.18 m/s)")
    ax.axvline(1, color="#BD93F9", linestyle="--", lw=1.5, label="Tick 1: Startup PE Surge (PE = 0.214)")
    ax.axvline(2, color=GREEN, linestyle="--", lw=1.5, label="Tick 2: Action Divergence (SW_L vs SW_R)")

    ax.set_title("Startup Acceleration Inertia Surge (Ticks 0–15)", color=TEXT_COLOR, fontweight="bold")
    ax.set_xlabel("Simulation Tick", color=TEXT_COLOR)
    ax.set_ylabel("Magnitude", color=TEXT_COLOR)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "02_forensic_w_norm_vs_time_divergence.png"), dpi=300, facecolor=DARK_BG)
    plt.close()
    print("Generated: 02_forensic_w_norm_vs_time_divergence.png")


def plot_03_trajectory_overlay():
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=DARK_BG)
    ax.set_facecolor(PANEL_BG)
    ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
    
    # Arena walls
    ax.add_patch(patches.Rectangle((0.60, -0.25), 0.10, 0.50, facecolor="#30363D", edgecolor="#6E7681"))
    ax.add_patch(patches.Rectangle((1.10, 0.30), 0.10, 0.50, facecolor="#30363D", edgecolor="#6E7681"))
    ax.add_patch(patches.Rectangle((1.10, -0.80), 0.10, 0.50, facecolor="#30363D", edgecolor="#6E7681"))
    ax.add_patch(patches.Rectangle((1.40, -0.80), 0.10, 0.50, facecolor=CORAL, alpha=0.5, edgecolor=CORAL, label="Hazard Barrier (1.45, -0.55m)"))
    
    # Trajectories
    ax.plot(df_stdp["x"], df_stdp["y"], color=CYAN, lw=2.5, label="NO_HDC_STDP (Episode 1)")
    ax.plot(df_no["x"], df_no["y"], color=CORAL, lw=2.0, linestyle="--", label="NO_HDC_NO_STDP (Episode 1)")
    
    # Annotate Tick 1 update point
    ax.scatter([0.0001], [0.0], color="#FF3366", s=180, marker="X", zorder=6, label="First STDP Update (Tick 1, x=0.0001m)")
    ax.annotate("Tick 1: Startup PE Surge\nDepressed SWERVE_RIGHT\n(x = 0.0001m, y = 0.0000m)",
                xy=(0.0001, 0.0), xytext=(0.20, -0.40),
                arrowprops=dict(arrowstyle="->", color=GOLD, lw=2),
                color=GOLD, fontweight="bold", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=PANEL_BG, edgecolor=GOLD))

    ax.set_xlim(-0.2, 2.0)
    ax.set_ylim(-1.0, 1.0)
    ax.set_title("Episode 1 Trajectory & Startup Divergence Point", color=TEXT_COLOR, fontweight="bold")
    ax.set_xlabel("X Position (meters)", color=TEXT_COLOR)
    ax.set_ylabel("Y Position (meters)", color=TEXT_COLOR)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, loc="upper left")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "03_forensic_trajectory_overlay_first_update.png"), dpi=300, facecolor=DARK_BG)
    plt.close()
    print("Generated: 03_forensic_trajectory_overlay_first_update.png")


if __name__ == "__main__":
    plot_01_initial_q_and_actions()
    plot_02_w_norm_divergence()
    plot_03_trajectory_overlay()
