"""
brain/carl_stage1_6_visualizer.py - High-Resolution Visual Analytics for CARL Stage 1.6
Generates publication-grade, dark-mode analytical charts for:
1. Figure 1: 7-Point Friction Gradient Sweep & Slip Monotonicity
2. Figure 2: 6 Physical Regimes Traction Discrepancy & Detection Rates
3. Figure 3: Dynamic Friction Transition (DRY -> ICE -> RECOVERY) Full Time-Series
4. Figure 4: Multi-Seed Stability & Edge-Case Forensic Breakdown
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import MultipleLocator

# Apply sleek cybernetic dark-mode styling
plt.rcParams.update({
    "figure.facecolor": "#0a0f1d",
    "axes.facecolor": "#0f172a",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#f8fafc",
    "axes.titlecolor": "#f8fafc",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "grid.color": "#1e293b",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 11,
})

BASE_DIR = "d:/ebca"
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence", "stage1_6")
PLOTS_DIR = os.path.join(EVIDENCE_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

RESULTS_PATH = os.path.join(EVIDENCE_DIR, "carl_stage1_6_results.json")


def load_results():
    with open(RESULTS_PATH, "r", encoding="utf-8") as fp:
        return json.load(fp)


def plot_figure1_friction_gradient(data):
    """Figure 1: 7-Point Friction Gradient Sweep & Slip Monotonicity"""
    fric_data = data["friction_gradient"]
    mus = [float(k) for k in fric_data.keys()]
    slip_ratios = [fric_data[k]["mean_slip_ratio"] for k in fric_data.keys()]
    v_hats = [fric_data[k]["mean_v_hat_x"] for k in fric_data.keys()]
    det_rates = [fric_data[k]["detection_rate"] * 100 for k in fric_data.keys()]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), facecolor="#0a0f1d")

    # Left Panel: Slip Ratio vs Floor Friction
    ax1.set_title("CARL STAGE 1.6: Slip Ratio vs Floor Friction (μ)", fontsize=14, fontweight="bold", pad=15)
    ax1.axhspan(0.0, 0.52, color="#10b981", alpha=0.12, label="Nominal Grip Zone (Slip ≤ 0.52)")
    ax1.axhspan(0.52, 1.0, color="#ef4444", alpha=0.12, label="Slip Discrepancy Zone (Slip > 0.52)")
    ax1.axhline(0.52, color="#f59e0b", linestyle="--", linewidth=1.8, label="Detection Threshold (σ = 0.52)")

    # Plot curve
    ax1.plot(mus, slip_ratios, color="#00e5ff", marker="o", markersize=9, linewidth=2.5, label="Measured Slip Ratio σ")
    for mu, slip in zip(mus, slip_ratios):
        ax1.annotate(f"σ={slip:.3f}", (mu, slip), textcoords="offset points", xytext=(0, 12),
                     ha="center", fontsize=9, fontweight="bold", color="#ffffff",
                     bbox=dict(boxstyle="round,pad=0.2", facecolor="#1e293b", edgecolor="#00e5ff", alpha=0.8))

    ax1.set_xscale("log")
    ax1.set_xlabel("Surface Friction Coefficient μ (log scale)", fontsize=12, labelpad=10)
    ax1.set_ylabel("Longitudinal Slip Ratio σ = 1 - γ", fontsize=12, labelpad=10)
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True)
    ax1.legend(loc="upper right", framealpha=0.8, facecolor="#0f172a", edgecolor="#334155")

    # Right Panel: Estimated Velocity vs Commanded Speed
    ax2.set_title("Chassis Velocity vs Surface Grip", fontsize=14, fontweight="bold", pad=15)
    bar_pos = np.arange(len(mus))
    width = 0.35

    ax2.bar(bar_pos - width/2, [0.15]*len(mus), width=width, label="Commanded Wheel Speed (0.15 m/s)", color="#38bdf8", alpha=0.7)
    ax2.bar(bar_pos + width/2, v_hats, width=width, label="Estimated Chassis Speed v̂_x", color="#10b981", alpha=0.85)

    ax2.set_xticks(bar_pos)
    ax2.set_xticklabels([f"μ={m}" for m in mus], rotation=25)
    ax2.set_xlabel("Friction Coefficient μ", fontsize=12, labelpad=10)
    ax2.set_ylabel("Speed (m/s)", fontsize=12, labelpad=10)
    ax2.set_ylim(0, 0.20)
    ax2.grid(True)
    ax2.legend(loc="upper right", framealpha=0.8, facecolor="#0f172a", edgecolor="#334155")

    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure1_friction_gradient_sweep.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"[PLOT] Generated: {out_path}")


def plot_figure2_physical_regimes(data):
    """Figure 2: 6 Physical Regimes Traction Discrepancy & Detection Rates"""
    regimes = data["physical_regimes"]
    names = list(regimes.keys())
    slip_ratios = [regimes[k]["mean_slip_ratio"] for k in names]
    det_rates = [regimes[k]["detection_rate"] * 100 for k in names]

    fig, ax1 = plt.subplots(figsize=(14, 7), facecolor="#0a0f1d")
    ax1.set_title("CARL STAGE 1.6: Traction Discrepancy Across 6 Physical Regimes", fontsize=15, fontweight="bold", pad=15)

    x = np.arange(len(names))
    width = 0.38

    # Bars for slip ratio
    bars1 = ax1.bar(x - width/2, slip_ratios, width, label="Slip Ratio σ (0=Grip, 1=Free Spin)", color="#00e5ff", alpha=0.85, edgecolor="#38bdf8")
    ax1.set_ylabel("Mean Slip Ratio σ", fontsize=12, color="#00e5ff", labelpad=10)
    ax1.set_ylim(0, 1.15)
    ax1.axhline(0.52, color="#f59e0b", linestyle="--", linewidth=1.5, label="Slip Alarm Threshold (0.52)")

    # Secondary axis for detection rate %
    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, det_rates, width, label="True Detection Rate %", color="#a855f7", alpha=0.85, edgecolor="#c084fc")
    ax2.set_ylabel("Detection / Flag Rate (%)", fontsize=12, color="#c084fc", labelpad=10)
    ax2.set_ylim(0, 115)
    ax2.axhline(10.0, color="#ef4444", linestyle=":", linewidth=1.5, label="Max Acceptable Dry FP (10%)")

    ax1.set_xticks(x)
    ax1.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=11, fontweight="bold")
    ax1.grid(True)

    # Annotate values
    for b in bars1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2, h + 0.02, f"{h:.2f}", ha="center", va="bottom", color="#00e5ff", fontsize=10, fontweight="bold")
    for b in bars2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2, h + 2, f"{h:.1f}%", ha="center", va="bottom", color="#c084fc", fontsize=10, fontweight="bold")

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.85, facecolor="#0f172a", edgecolor="#334155")

    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure2_physical_regimes_comparison.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"[PLOT] Generated: {out_path}")


def plot_figure3_dynamic_timeseries():
    """Figure 3: Dynamic Friction Transition Full Time-Series (DRY -> ICE -> RECOVERY)"""
    import sys
    sys.path.insert(0, BASE_DIR)
    from brain.carl_stage1_hal import CarlStage1HAL
    from brain.carl_stage1_organism import CarlStage1Organism

    hal = CarlStage1HAL(open_space=True)
    hal.reset()
    hal.set_floor_friction(3.0)
    org = CarlStage1Organism(hal=hal, seed=42)
    org.discovered_topology = {'discovered_drive_channels': [0, 1]}
    org.run_session(60)
    org.learn_predictive_readout(reg_lambda=10.0)

    hal.reset()
    hal.set_floor_friction(3.0)
    org.control_mode = "goal_seeking"
    org.set_sensory_goal(channel=7, mode="maximize")

    ticks = []
    mus = []
    v_wheels = []
    v_hats = []
    slips = []
    detections = []
    chatter = []
    u_scales = []

    # Phase 1: DRY (25 ticks)
    for t in range(25):
        rec = org.step()
        det = org.detect_traction_discrepancy(slip_threshold=0.52)
        ticks.append(t)
        mus.append(3.0)
        v_wheels.append(rec["v_wheel"])
        v_hats.append(rec["v_hat_x"])
        slips.append(rec["slip_ratio"])
        detections.append(1.0 if det else 0.0)
        chatter.append(float(np.std(org.ax_history)) if len(org.ax_history) > 1 else 0.0)
        u_scales.append(0.4 if det else 1.0)

    # Phase 2: ICE (35 ticks)
    hal.set_floor_friction(0.005)
    for t in range(25, 60):
        rec = org.step()
        det = org.detect_traction_discrepancy(slip_threshold=0.52)
        ticks.append(t)
        mus.append(0.005)
        v_wheels.append(rec["v_wheel"])
        v_hats.append(rec["v_hat_x"])
        slips.append(rec["slip_ratio"])
        detections.append(1.0 if det else 0.0)
        chatter.append(float(np.std(org.ax_history)) if len(org.ax_history) > 1 else 0.0)
        u_scales.append(0.4 if det else 1.0)

    # Phase 3: RECOVERY (25 ticks)
    hal.set_floor_friction(3.0)
    for t in range(60, 85):
        rec = org.step()
        det = org.detect_traction_discrepancy(slip_threshold=0.52)
        ticks.append(t)
        mus.append(3.0)
        v_wheels.append(rec["v_wheel"])
        v_hats.append(rec["v_hat_x"])
        slips.append(rec["slip_ratio"])
        detections.append(1.0 if det else 0.0)
        chatter.append(float(np.std(org.ax_history)) if len(org.ax_history) > 1 else 0.0)
        u_scales.append(0.4 if det else 1.0)

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(16, 12), facecolor="#0a0f1d", sharex=True)

    # Top Panel: Surface Friction Phase
    ax1.set_title("CARL STAGE 1.6: Dynamic Friction Transition Telemetry (DRY -> ICE -> RECOVERY)", fontsize=15, fontweight="bold", pad=15)
    ax1.axvspan(0, 25, color="#10b981", alpha=0.15, label="Phase 1: DRY RUBBER (μ = 3.0)")
    ax1.axvspan(25, 60, color="#00e5ff", alpha=0.15, label="Phase 2: CONTINUOUS ICE (μ = 0.005)")
    ax1.axvspan(60, 85, color="#10b981", alpha=0.15, label="Phase 3: RECOVERY (μ = 3.0)")
    ax1.plot(ticks, mus, color="#38bdf8", linewidth=2.0)
    ax1.set_ylabel("Floor μ", fontsize=11)
    ax1.set_yscale("log")
    ax1.legend(loc="upper right", framealpha=0.85, facecolor="#0f172a", edgecolor="#334155")
    ax1.grid(True)

    # Second Panel: Speeds
    ax2.axvspan(0, 25, color="#10b981", alpha=0.08)
    ax2.axvspan(25, 60, color="#00e5ff", alpha=0.08)
    ax2.axvspan(60, 85, color="#10b981", alpha=0.08)
    ax2.plot(ticks, v_wheels, color="#fbbf24", linewidth=2.0, label="Commanded Wheel Speed v_wheel")
    ax2.plot(ticks, v_hats, color="#10b981", linewidth=2.5, label="Estimated Chassis Speed v̂_x")
    ax2.set_ylabel("Speed (m/s)", fontsize=11)
    ax2.legend(loc="upper right", framealpha=0.85, facecolor="#0f172a", edgecolor="#334155")
    ax2.grid(True)

    # Third Panel: Accelerometer Chatter
    ax3.axvspan(0, 25, color="#10b981", alpha=0.08)
    ax3.axvspan(25, 60, color="#00e5ff", alpha=0.08)
    ax3.axvspan(60, 85, color="#10b981", alpha=0.08)
    ax3.plot(ticks, chatter, color="#ec4899", linewidth=2.0, label="Longitudinal Chatter σ_ax (m/s²)")
    ax3.axhline(1.1, color="#f43f5e", linestyle="--", linewidth=1.5, label="Grip Chatter Nominal Scale (1.1 m/s²)")
    ax3.set_ylabel("Vibration σ_ax", fontsize=11)
    ax3.legend(loc="upper right", framealpha=0.85, facecolor="#0f172a", edgecolor="#334155")
    ax3.grid(True)

    # Bottom Panel: Slip Ratio & Mitigation Trigger
    ax4.axvspan(0, 25, color="#10b981", alpha=0.08)
    ax4.axvspan(25, 60, color="#00e5ff", alpha=0.08)
    ax4.axvspan(60, 85, color="#10b981", alpha=0.08)
    ax4.plot(ticks, slips, color="#00e5ff", linewidth=2.5, label="Longitudinal Slip Ratio σ")
    ax4.axhline(0.52, color="#f59e0b", linestyle="--", linewidth=1.8, label="Slip Threshold (0.52)")

    # Scatter detection triggers
    det_x = [t for t, d in zip(ticks, detections) if d > 0.5]
    det_y = [slips[t] for t in det_x]
    ax4.scatter(det_x, det_y, color="#ef4444", s=50, zorder=5, label="Slip Detected (0.4x Torque Scaling Active)")

    ax4.set_xlabel("Simulation Tick (30 Hz | Δt = 33.3 ms)", fontsize=12, labelpad=10)
    ax4.set_ylabel("Slip Ratio σ", fontsize=11)
    ax4.set_ylim(-0.05, 1.05)
    ax4.legend(loc="upper right", framealpha=0.85, facecolor="#0f172a", edgecolor="#334155")
    ax4.grid(True)

    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure3_dynamic_transition_timeseries.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"[PLOT] Generated: {out_path}")


def plot_figure4_multiseed_audit(data):
    """Figure 4: Multi-Seed Stability & Edge-Case Forensic Breakdown"""
    multiseed = data["multiseed_stability"]
    details = multiseed["seed_details"]
    seeds = [d["seed"] for d in details]
    dry_fps = [d["dry_fp_rate"] * 100 for d in details]
    ice_dets = [d["ice_detection_rate"] * 100 for d in details]
    rec_rates = [d["recovery_rate"] * 100 for d in details]
    verdicts = [d["verified"] for d in details]

    fig, ax = plt.subplots(figsize=(15, 7), facecolor="#0a0f1d")
    ax.set_title("CARL STAGE 1.6: Multi-Seed Forensic Audit (N=5 Seeds)", fontsize=15, fontweight="bold", pad=15)

    x = np.arange(len(seeds))
    width = 0.26

    b1 = ax.bar(x - width, dry_fps, width, label="Dry Floor False Positive Rate (%)", color="#f43f5e", alpha=0.85)
    b2 = ax.bar(x, ice_dets, width, label="Ice Detection Rate (%)", color="#00e5ff", alpha=0.85)
    b3 = ax.bar(x + width, rec_rates, width, label="Recovery False Flags (%)", color="#a855f7", alpha=0.85)

    # Threshold guidelines
    ax.axhline(10.0, color="#f43f5e", linestyle="--", linewidth=1.5, label="Max Acceptable Dry FP (10%)")
    ax.axhline(70.0, color="#00e5ff", linestyle="--", linewidth=1.5, label="Min Acceptable Ice Det (70%)")

    ax.set_xticks(x)
    labels = []
    for s, v in zip(seeds, verdicts):
        status_txt = "PASS" if v else "FAIL"
        color_tag = "#10b981" if v else "#ef4444"
        labels.append(f"Seed {s}\n[{status_txt}]")
    ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax.set_ylabel("Rate (%)", fontsize=12, labelpad=10)
    ax.set_ylim(0, 115)
    ax.grid(True)

    # Annotate percentages
    for b in b1:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 1.5, f"{h:.1f}%", ha="center", va="bottom", color="#f43f5e", fontsize=9, fontweight="bold")
    for b in b2:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 1.5, f"{h:.1f}%", ha="center", va="bottom", color="#00e5ff", fontsize=9, fontweight="bold")
    for b in b3:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 1.5, f"{h:.1f}%", ha="center", va="bottom", color="#a855f7", fontsize=9, fontweight="bold")

    # Add callout annotations for Seed 202 and 303
    ax.annotate("SEED 202 FAIL:\nIn-place spinout on ice saturated\ngyro (20 rad/s) & centrifugal accel,\ndeceiving chatter proxy.",
                xy=(2, 14.3), xytext=(1.5, 55),
                arrowprops=dict(facecolor="#ef4444", shrink=0.05, width=1.5, headwidth=6),
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e293b", edgecolor="#ef4444", alpha=0.9),
                fontsize=9, color="#f8fafc")

    ax.annotate("SEED 303 FAIL:\nSteering oscillation caused\nrotational chassis inertia lag,\ntriggering 20% dry false alarms.",
                xy=(3 - width, 20.0), xytext=(2.7, 85),
                arrowprops=dict(facecolor="#f43f5e", shrink=0.05, width=1.5, headwidth=6),
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e293b", edgecolor="#f43f5e", alpha=0.9),
                fontsize=9, color="#f8fafc")

    ax.legend(loc="upper right", framealpha=0.85, facecolor="#0f172a", edgecolor="#334155")

    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, "figure4_multiseed_forensic_breakdown.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"[PLOT] Generated: {out_path}")


if __name__ == "__main__":
    print("=" * 80)
    print("CARL STAGE 1.6: GENERATING PUBLICATION-GRADE VISUAL ANALYTICS")
    print("=" * 80)
    data = load_results()
    plot_figure1_friction_gradient(data)
    plot_figure2_physical_regimes(data)
    plot_figure3_dynamic_timeseries()
    plot_figure4_multiseed_audit(data)
    print("\n[COMPLETE] All 4 publication-grade figures successfully generated.")
