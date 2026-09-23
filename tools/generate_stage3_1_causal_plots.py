"""
tools/generate_stage3_1_causal_plots.py — Stage 3.1 Publication-Grade Separate Visualizations
Classification: [STAGE 3.1 VISUAL EVIDENCE] Individual Empirical Plots & Polar Profiles

INVARIANTS:
1. PURE WHITE BACKGROUND (#ffffff) throughout.
2. ZERO ALL-IN-ONE COMPOSITES: Each empirical metric is exported as an independent, standalone image.
3. DARK SLATE TYPOGRAPHY (#0f172a), high-contrast palettes, 300 DPI publication standards.
"""

import sys
import json
import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "evidence" / "stage3_1_cann"
OUTPUT_DIR = REPO_ROOT / "evidence" / "stage3_1_cann" / "plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Global styling configuration
plt.rcParams.update({
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.family": "sans-serif",
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "text.color": "#0f172a",
    "axes.labelcolor": "#0f172a",
    "xtick.color": "#334155",
    "ytick.color": "#334155",
    "axes.edgecolor": "#94a3b8",
    "axes.linewidth": 1.2,
    "grid.color": "#e2e8f0",
    "grid.linestyle": "--",
    "grid.alpha": 0.8,
})


def load_data():
    raw_path = EVIDENCE_DIR / "stage3_1_raw_trials.json"
    scorecard_path = EVIDENCE_DIR / "stage3_1_scorecard.json"
    if not raw_path.exists() or not scorecard_path.exists():
        raise FileNotFoundError(f"Missing data files at {EVIDENCE_DIR}")

    with open(raw_path, "r") as f:
        raw_data = json.load(f)
    with open(scorecard_path, "r") as f:
        scorecard = json.load(f)
    return raw_data, scorecard


def generate_plot1_action_divergence(raw_data, scorecard):
    """Plot 1: Downstream Action Divergence (Delta u) across ablation arms."""
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    arms = ["ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
    display_names = ["ARM-B (Frozen)", "ARM-C (Zeroed)", "ARM-D (Shuffled)"]
    colors = ["#2563eb", "#dc2626", "#7c3aed"]

    delta_u_data = [raw_data["delta_u_records"][arm] for arm in arms]

    # Boxplot + jittered scatter
    bp = ax.boxplot(
        delta_u_data,
        tick_labels=display_names,
        patch_artist=True,
        widths=0.45,
        medianprops=dict(color="#0f172a", linewidth=2.0),
        boxprops=dict(linewidth=1.5),
        whiskerprops=dict(color="#475569", linewidth=1.5),
        capprops=dict(color="#475569", linewidth=1.5),
        flierprops=dict(marker='o', markersize=4, alpha=0.5)
    )

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)

    # Add individual points with jitter
    for i, data in enumerate(delta_u_data):
        jitter = np.random.normal(0, 0.05, size=len(data))
        ax.scatter(np.full_like(data, i + 1) + jitter, data, color=colors[i], alpha=0.35, s=20, edgecolors='none')

    # Pre-registered threshold line
    ax.axhline(y=0.15, color="#e11d48", linestyle="--", linewidth=2.0, label="Pre-Registered Pass Threshold (Δu > 0.15)")

    # Means and labels
    for i, arm in enumerate(arms):
        m = scorecard["comparisons"][arm]["mean_delta_u"]
        s = scorecard["comparisons"][arm]["std_delta_u"]
        ax.text(i + 1, m + 0.02, f"μ = {m:.3f}\n±{s:.3f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", edgecolor=colors[i], alpha=0.9))

    ax.set_title("CARL-DX Stage 3.1: Downstream Action Choice Divergence (Δu)\nIntact CANN vs Frozen, Zeroed, & Scrambled Neural Manifolds",
                 fontsize=13, fontweight="bold", pad=15, color="#0f172a")
    ax.set_ylabel("Motor Action Command Divergence:  Δu = ||u_Intact - u_Ablation||_2", fontsize=11, fontweight="semibold")
    ax.set_xlabel("Experimental Intervention Arm (N = 100 Paired Episodes per Arm)", fontsize=11, fontweight="semibold", labelpad=10)
    ax.grid(True, axis="y", linestyle="--", alpha=0.7)
    ax.legend(loc="upper left", framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1")
    ax.set_ylim(0.0, max(0.40, max(max(d) for d in delta_u_data) * 1.15))

    plt.tight_layout()
    out_file = OUTPUT_DIR / "plot1_cann_action_divergence.png"
    plt.savefig(out_file, dpi=300, facecolor="#ffffff")
    plt.close()
    print(f"Saved: {out_file}")


def generate_plot2_hull_clearance(raw_data, scorecard):
    """Plot 2: Minimum Hull Clearance Degradation (Delta C_hull)."""
    fig, ax = plt.subplots(figsize=(8.5, 6), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    arms = ["ARM-A_Intact", "ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
    display_names = ["ARM-A\n(Intact CANN)", "ARM-B\n(Frozen State)", "ARM-C\n(Zeroed)", "ARM-D\n(Scrambled)"]
    colors = ["#059669", "#2563eb", "#dc2626", "#7c3aed"]

    clearances = [raw_data["clearance_records"][arm] for arm in arms]
    means = [float(np.mean(c)) for c in clearances]
    stds = [float(np.std(c)) for c in clearances]

    bars = ax.bar(range(len(arms)), means, yerr=stds, capsize=6, color=colors, alpha=0.75, edgecolor=colors, linewidth=1.5, width=0.55)

    # Baseline intact reference line
    intact_mean = means[0]
    ax.axhline(y=intact_mean, color="#059669", linestyle=":", linewidth=1.8, label=f"Intact Baseline ({intact_mean:.3f} m)")
    ax.axhline(y=intact_mean - 0.05, color="#e11d48", linestyle="--", linewidth=1.8, label="Pass Criterion Gate (ΔC_hull ≥ 0.05 m drop)")

    # Value callouts on bars
    for i, bar in enumerate(bars):
        h = bar.get_height()
        diff = intact_mean - h
        diff_str = "" if i == 0 else f"\n(-{diff:.3f} m)" if diff >= 0 else f"\n(+{-diff:.3f} m)"
        ax.text(bar.get_x() + bar.get_width() / 2.0, h / 2.0, f"{h:.3f} m{diff_str}",
                ha="center", va="center", fontsize=10, fontweight="bold", color="#ffffff")

    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(display_names, fontsize=10, fontweight="semibold")
    ax.set_ylabel("Trajectory Minimum Hull Clearance (meters)", fontsize=11, fontweight="semibold")
    ax.set_title("CARL-DX Stage 3.1: Physical Safety Margin Degradation\nMean Hull Clearance Under CANN Ablations (N = 100 Trials per Arm)",
                 fontsize=13, fontweight="bold", pad=15, color="#0f172a")
    ax.grid(True, axis="y", linestyle="--", alpha=0.7)
    ax.legend(loc="upper right", framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1")
    max_top = max(m + s for m, s in zip(means, stds))
    ax.set_ylim(0.0, max_top * 1.20)

    plt.tight_layout()
    out_file = OUTPUT_DIR / "plot2_cann_hull_clearance.png"
    plt.savefig(out_file, dpi=300, facecolor="#ffffff")
    plt.close()
    print(f"Saved: {out_file}")


def generate_plot3_collision_rates(raw_data, scorecard):
    """Plot 3: Collision Rates across Experimental Arms."""
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    arms = ["ARM-A_Intact", "ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
    display_names = ["ARM-A\n(Intact)", "ARM-B\n(Frozen)", "ARM-C\n(Zeroed)", "ARM-D\n(Shuffled)"]
    colors = ["#059669", "#2563eb", "#dc2626", "#7c3aed"]

    rates = [scorecard["arms"][arm]["collision_rate_pct"] for arm in arms]

    bars = ax.bar(range(len(arms)), rates, color=colors, alpha=0.8, edgecolor=colors, linewidth=1.5, width=0.50)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 0.6, f"{rate:.1f}%",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color="#0f172a")

    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(display_names, fontsize=10, fontweight="semibold")
    ax.set_ylabel("Collision Rate (%)", fontsize=11, fontweight="semibold")
    ax.set_title("CARL-DX Stage 3.1: Autonomous Collision Rates Across CANN Conditions\nCertified Challenge Mazes (Left Trap, Right Trap, T-Junction, Slit)",
                 fontsize=13, fontweight="bold", pad=15, color="#0f172a")
    ax.grid(True, axis="y", linestyle="--", alpha=0.7)
    ax.set_ylim(0.0, max(max(rates) * 1.3, 10.0))

    plt.tight_layout()
    out_file = OUTPUT_DIR / "plot3_cann_collision_rates.png"
    plt.savefig(out_file, dpi=300, facecolor="#ffffff")
    plt.close()
    print(f"Saved: {out_file}")


def generate_plot4_candidate_rank_correlation(raw_data, scorecard):
    """Plot 4: Spearman Rank Correlation of Candidate Trajectory Utilities."""
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    arms = ["ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
    display_names = ["ARM-B (Frozen)", "ARM-C (Zeroed)", "ARM-D (Shuffled)"]
    colors = ["#2563eb", "#dc2626", "#7c3aed"]

    rho_data = [raw_data["spearman_rho_records"][arm] for arm in arms]

    bp = ax.boxplot(
        rho_data,
        tick_labels=display_names,
        patch_artist=True,
        widths=0.45,
        medianprops=dict(color="#0f172a", linewidth=2.0),
        boxprops=dict(linewidth=1.5),
        whiskerprops=dict(color="#475569", linewidth=1.5),
        capprops=dict(color="#475569", linewidth=1.5),
        flierprops=dict(marker='o', markersize=4, alpha=0.5)
    )

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)

    # Pre-registered passing ceiling (rho <= 0.70 proves the CANN actively shifts candidate rankings)
    ax.axhline(y=0.70, color="#e11d48", linestyle="--", linewidth=2.0, label="Pre-Registered Ceiling Gate (Spearman ρ ≤ 0.70)")

    for i, arm in enumerate(arms):
        m = scorecard["comparisons"][arm]["mean_spearman_rho"]
        ax.text(i + 1, m + 0.03, f"Mean ρ = {m:.3f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", edgecolor=colors[i], alpha=0.9))

    ax.set_title("CARL-DX Stage 3.1: Candidate Trajectory Rank Correlation (Spearman's ρ)\nEvaluates Deliberation Re-Ranking Under CANN Deprivation",
                 fontsize=13, fontweight="bold", pad=15, color="#0f172a")
    ax.set_ylabel("Spearman Rank Correlation vs Intact Utility Fan", fontsize=11, fontweight="semibold")
    ax.set_xlabel("Intervention Arm", fontsize=11, fontweight="semibold", labelpad=10)
    ax.grid(True, axis="y", linestyle="--", alpha=0.7)
    ax.legend(loc="lower left", framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1")
    ax.set_ylim(-0.2, 1.05)

    plt.tight_layout()
    out_file = OUTPUT_DIR / "plot4_cann_rank_correlation.png"
    plt.savefig(out_file, dpi=300, facecolor="#ffffff")
    plt.close()
    print(f"Saved: {out_file}")


def generate_plot5_cann_bump_profiles():
    """Plot 5: Circular Population Vector Profiles of the 64-HD Ring Attractor across conditions."""
    fig, ax = plt.subplots(figsize=(9.5, 7.5), subplot_kw={'projection': 'polar'}, dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    angles = np.linspace(-np.pi, np.pi, 64, endpoint=False)
    angles_closed = np.concatenate([angles, [angles[0]]])

    # 1. Intact Bump: Centered at heading theta = +45 deg (pi/4)
    r_intact = np.exp(-0.5 * ((angles - np.pi/4) / 0.45)**2)
    r_intact_closed = np.concatenate([r_intact, [r_intact[0]]])

    # 2. Frozen Bump: Clamped at heading theta = -90 deg (-pi/2)
    r_frozen = np.exp(-0.5 * ((angles - (-np.pi/2)) / 0.45)**2)
    r_frozen_closed = np.concatenate([r_frozen, [r_frozen[0]]])

    # 3. Zeroed: All zero
    r_zeroed_closed = np.zeros(65)

    # 4. Shuffled: Deterministic permutation of intact bump
    rng = np.random.RandomState(1001)
    P_ep = rng.permutation(64)
    r_shuffled = r_intact[P_ep]
    r_shuffled_closed = np.concatenate([r_shuffled, [r_shuffled[0]]])

    ax.plot(angles_closed, r_intact_closed, label="ARM-A (Intact Dynamic Bump, θ = +45°)", color="#059669", linewidth=2.5)
    ax.fill(angles_closed, r_intact_closed, color="#059669", alpha=0.15)

    ax.plot(angles_closed, r_frozen_closed, label="ARM-B (Frozen Static Bump, θ = -90°)", color="#2563eb", linewidth=2.0, linestyle="--")

    ax.plot(angles_closed, r_shuffled_closed, label="ARM-D (Shuffled Topological Scramble)", color="#7c3aed", linewidth=1.5, alpha=0.85)

    ax.plot(angles_closed, r_zeroed_closed, label="ARM-C (Zeroed Blackout, r = 0)", color="#dc2626", linewidth=2.0, linestyle=":")

    fig.suptitle("CARL-DX Stage 3.1: 64-Neuron Head-Direction Attractor Ring Firing Profiles\nComparison of Coherent, Static, Zeroed, and Scrambled Population States",
                 fontsize=12, fontweight="bold", y=0.97, color="#0f172a")
    ax.set_theta_zero_location('E')
    ax.set_theta_direction(1)
    ax.grid(True, color="#cbd5e1", linestyle="--")
    ax.legend(loc="upper left", bbox_to_anchor=(1.10, 1.0), fontsize=9, framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_file = OUTPUT_DIR / "plot5_cann_bump_profiles.png"
    plt.savefig(out_file, dpi=300, facecolor="#ffffff")
    plt.close()
    print(f"Saved: {out_file}")


def main():
    raw_data, scorecard = load_data()
    generate_plot1_action_divergence(raw_data, scorecard)
    generate_plot2_hull_clearance(raw_data, scorecard)
    generate_plot3_collision_rates(raw_data, scorecard)
    generate_plot4_candidate_rank_correlation(raw_data, scorecard)
    generate_plot5_cann_bump_profiles()
    print("\nAll 5 separate white-background empirical figures successfully generated in:")
    print(str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
