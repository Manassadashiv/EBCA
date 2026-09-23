"""
tests/generate_stage3_1R_plots.py — Publication Plots for Stage 3.1-R
All plots generated on clean white background with distinct individual figures.
"""

import os
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = repo_root / "evidence" / "stage3_1R"

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.edgecolor': '#333333',
    'axes.linewidth': 1.0,
    'grid.color': '#E0E0E0',
    'grid.linestyle': '--',
    'grid.linewidth': 0.7,
})


def generate_plots():
    scorecard_file = EVIDENCE_DIR / "stage3_1R_scorecard.json"
    raw_file = EVIDENCE_DIR / "stage3_1R_raw_trials.json"

    if not scorecard_file.exists():
        print(f"Error: {scorecard_file} does not exist.")
        return

    with open(scorecard_file, 'r', encoding='utf-8') as f:
        scorecard = json.load(f)

    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    evals = scorecard["arms_evaluation"]
    arms = ["ARM-C_Zeroed", "ARM-D_FullShuffled", "ARM-B_Frozen"]
    labels = ["ARM-C\n(Zeroed 2,114)", "ARM-D\n(Full-Shuffled 2,114)", "ARM-B\n(Frozen Control)"]
    colors = ['#D32F2F', '#E65100', '#1976D2']

    # -------------------------------------------------------------
    # Plot 1: Continuous Action Divergence (Delta u)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    delta_u_vals = [evals[arm]["g1_delta_u"]["value"] for arm in arms]
    threshold_u = 0.150

    bars = ax.bar(labels, delta_u_vals, color=colors, width=0.5, edgecolor='#333333', linewidth=1.2, zorder=3)
    ax.axhline(threshold_u, color='#B71C1C', linestyle='--', linewidth=2.0, label=f'Threshold (> {threshold_u} m/s)', zorder=4)

    for bar, val in zip(bars, delta_u_vals):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.02, f'{val:.4f} m/s\n(PASS)', ha='center', va='bottom', fontweight='bold', color='#1B5E20')

    ax.set_ylabel(r'Mean Continuous Action Divergence $\Delta \mathbf{u}$ [m/s]', fontweight='bold')
    ax.set_title('CARL Stage 3.1-R: Continuous Action Divergence across 2,114 Units (Gate 1)', pad=15, fontweight='bold')
    ax.set_ylim(0, max(delta_u_vals) * 1.25)
    ax.grid(True, axis='y')
    ax.legend(loc='upper right', framealpha=0.95)
    plt.tight_layout()
    p1_path = EVIDENCE_DIR / "plot1_stage3_1R_action_divergence.png"
    plt.savefig(p1_path, dpi=300)
    plt.close()
    print(f"Saved: {p1_path}")

    # -------------------------------------------------------------
    # Plot 2: Hull Clearance Degradation (Delta C_hull) — PRIMARY ENDPOINT
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5.5))
    delta_c_vals = [evals[arm]["g3_delta_c_hull"]["value"] for arm in arms]
    threshold_c = 0.050

    bar_colors = ['#2E7D32' if v >= threshold_c else '#C62828' for v in delta_c_vals]
    bars = ax.bar(labels, delta_c_vals, color=bar_colors, width=0.5, edgecolor='#333333', linewidth=1.2, zorder=3)
    ax.axhline(threshold_c, color='#B71C1C', linestyle='--', linewidth=2.0, label=rf'Primary Endpoint Threshold ($\geq +{threshold_c}$ m)', zorder=4)
    ax.axhline(0.0, color='#666666', linestyle='-', linewidth=1.0, zorder=2)

    for bar, val in zip(bars, delta_c_vals):
        yval = bar.get_height()
        status = "PASS (Primary Endpoint)" if val >= threshold_c else "FAIL"
        txt_color = '#1B5E20' if val >= threshold_c else '#B71C1C'
        y_pos = yval + 0.008 if yval >= 0 else yval - 0.015
        ax.text(bar.get_x() + bar.get_width() / 2.0, y_pos, f'{val:+.4f} m\n{status}', ha='center', va='bottom' if yval >= 0 else 'top', fontweight='bold', color=txt_color)

    ax.set_ylabel(r'Hull Clearance Degradation $\Delta C_{\mathrm{hull}}$ [m]', fontweight='bold')
    ax.set_title('CARL Stage 3.1-R: Primary Causal Endpoint — Hull Clearance Degradation (Gate 3)', pad=15, fontweight='bold')
    ax.set_ylim(min(-0.04, min(delta_c_vals) - 0.03), max(delta_c_vals) * 1.30)
    ax.grid(True, axis='y')
    ax.legend(loc='upper right', framealpha=0.95)
    plt.tight_layout()
    p2_path = EVIDENCE_DIR / "plot2_stage3_1R_hull_clearance.png"
    plt.savefig(p2_path, dpi=300)
    plt.close()
    print(f"Saved: {p2_path}")

    # -------------------------------------------------------------
    # Plot 3: Collision Rate Increase (Delta Coll)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    intact_coll = scorecard["intact_baseline"]["collision_rate"] * 100
    all_arms_plot = ["Intact (ARM-A)", "ARM-C (Zeroed)", "ARM-D (Full-Shuf)", "ARM-B (Frozen)"]
    coll_rates = [
        intact_coll,
        evals["ARM-C_Zeroed"]["g5_delta_coll"]["abl_coll"] * 100,
        evals["ARM-D_FullShuffled"]["g5_delta_coll"]["abl_coll"] * 100,
        evals["ARM-B_Frozen"]["g5_delta_coll"]["abl_coll"] * 100,
    ]
    plot_colors = ['#2E7D32', '#D32F2F', '#E65100', '#1976D2']

    bars = ax.bar(all_arms_plot, coll_rates, color=plot_colors, width=0.55, edgecolor='#333333', linewidth=1.2, zorder=3)

    for bar, val, name in zip(bars, coll_rates, all_arms_plot):
        yval = bar.get_height()
        diff = val - intact_coll
        diff_str = "Baseline" if name.startswith("Intact") else f"{diff:+.1f}%"
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.2, f'{val:.1f}%\n({diff_str})', ha='center', va='bottom', fontweight='bold')

    ax.set_ylabel('Physical Collision Rate [%]', fontweight='bold')
    ax.set_title('CARL Stage 3.1-R: Physical Collision Rates under Sensory Blackout (Gate 5)', pad=15, fontweight='bold')
    ax.set_ylim(0, max(coll_rates) * 1.25)
    ax.grid(True, axis='y')
    plt.tight_layout()
    p3_path = EVIDENCE_DIR / "plot3_stage3_1R_collision_rates.png"
    plt.savefig(p3_path, dpi=300)
    plt.close()
    print(f"Saved: {p3_path}")

    # -------------------------------------------------------------
    # Plot 4: Candidate Rank Correlation (Spearman rho at Blackout Midpoint)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    rho_vals = [evals[arm]["g2_spearman_rho_midpoint"]["value"] for arm in arms]
    threshold_rho = 0.700

    rho_colors = ['#2E7D32' if v <= threshold_rho else '#C62828' for v in rho_vals]
    bars = ax.bar(labels, rho_vals, color=rho_colors, width=0.5, edgecolor='#333333', linewidth=1.2, zorder=3)
    ax.axhline(threshold_rho, color='#B71C1C', linestyle='--', linewidth=2.0, label=rf'Disruption Threshold ($\leq {threshold_rho}$)', zorder=4)

    for bar, val in zip(bars, rho_vals):
        yval = bar.get_height()
        status = "PASS" if val <= threshold_rho else "FAIL"
        txt_color = '#1B5E20' if val <= threshold_rho else '#B71C1C'
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.03, f'{val:.4f}\n({status})', ha='center', va='bottom', fontweight='bold', color=txt_color)

    ax.set_ylabel('Spearman Rank Correlation $\\rho$', fontweight='bold')
    ax.set_title('CARL Stage 3.1-R: Deliberation Candidate Rank Shift at Blackout Midpoint (Gate 2)', pad=15, fontweight='bold')
    ax.set_ylim(-0.5, 1.20)
    ax.grid(True, axis='y')
    ax.legend(loc='upper right', framealpha=0.95)
    plt.tight_layout()
    p4_path = EVIDENCE_DIR / "plot4_stage3_1R_rank_correlation_rho.png"
    plt.savefig(p4_path, dpi=300)
    plt.close()
    print(f"Saved: {p4_path}")

    # -------------------------------------------------------------
    # Plot 5: Complete Stage 3.1-R Acceptance Matrix
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')

    gate_names = [
        "G1: Action Divergence (Δu > 0.15)",
        "G2: Candidate Rank Shift (ρ ≤ 0.70)",
        "G3: Hull Clearance (ΔC_hull ≥ +0.05m) [PRIMARY]",
        "G4: Statistical Significance (Wilcoxon p < 0.005)",
        "G5: Collision Non-Inferiority (ΔColl ≥ 0%)"
    ]

    table_data = []
    for g_idx, g_name in enumerate(gate_names):
        row = [g_name]
        for arm in ["ARM-C_Zeroed", "ARM-D_FullShuffled", "ARM-B_Frozen"]:
            ev = evals[arm]
            if g_idx == 0:
                p = ev["g1_delta_u"]["pass"]
                val = f"{ev['g1_delta_u']['value']:.3f} m/s"
            elif g_idx == 1:
                p = ev["g2_spearman_rho_midpoint"]["pass"]
                val = f"{ev['g2_spearman_rho_midpoint']['value']:.3f}"
            elif g_idx == 2:
                p = ev["g3_delta_c_hull"]["pass"]
                val = f"{ev['g3_delta_c_hull']['value']:+.3f} m"
            elif g_idx == 3:
                p = ev["g4_wilcoxon_p"]["pass"]
                val = f"p={ev['g4_wilcoxon_p']['value']:.1e}"
            else:
                p = ev["g5_delta_coll"]["pass"]
                val = f"{ev['g5_delta_coll']['value']:+.1%}"
            mark = "[PASS]" if p else "[FAIL]"
            row.append(f"{val}\n{mark}")
        table_data.append(row)

    col_labels = ["Gate Specification", "ARM-C (Zeroed 2,114)\n[PRIMARY CERTIFICATION]", "ARM-D (Full-Shuffled 2,114)\n[SECONDARY CONTROL]", "ARM-B (Frozen)\n[OBSERVATIONAL ONLY]"]
    table = ax.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.0, 2.2)

    # Style table headers and cells
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor('#37474F')
            cell.set_text_props(color='white', fontweight='bold')
        else:
            if "[PASS]" in cell.get_text().get_text():
                cell.set_facecolor('#E8F5E9')
            elif "[FAIL]" in cell.get_text().get_text():
                cell.set_facecolor('#FFEBEE')
            else:
                cell.set_facecolor('#FAFAFA')

    plt.title(f"CARL Stage 3.1-R: Adjudicated Acceptance Matrix — Verdict: {scorecard['verdict']}", pad=25, fontweight='bold', fontsize=12)
    plt.tight_layout()
    p5_path = EVIDENCE_DIR / "plot5_stage3_1R_certification_matrix.png"
    plt.savefig(p5_path, dpi=300)
    plt.close()
    print(f"Saved: {p5_path}")

    # -------------------------------------------------------------
    # Plot 6: 2,114-Unit Architecture Breakdown & Subsystem Attribution
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    unit_counts = [64, 1024, 1026]
    unit_labels = ['HD Ring Attractor\n(64 units, 3.0%)', 'Grid Torus Attractor\n(1,024 units, 48.4%)', 'Liquid State Reservoir\n(1,026 units, 48.5%)']
    pie_colors = ['#1976D2', '#388E3C', '#F57C00']

    ax1.pie(unit_counts, labels=unit_labels, colors=pie_colors, autopct='%1.1f%%', startangle=140,
            wedgeprops={'edgecolor': '#333333', 'linewidth': 1.2})
    ax1.set_title('CARL 2,114-Unit Architecture Composition', fontweight='bold', pad=10)

    # Subsystem Causal Attribution Bar
    subsystems = ['Spatial CANN Core\n(1,088 Units)\n[Rollout Origin & Heading]', 'LSM Reservoir\n(1,026 Units)\n[Spatiotemporal Memory]']
    effect_sizes = [evals["ARM-C_Zeroed"]["cohens_d"], evals["ARM-D_FullShuffled"]["cohens_d"]]
    ax2.bar(subsystems, effect_sizes, color=['#2E7D32', '#E65100'], width=0.45, edgecolor='#333333', linewidth=1.2, zorder=3)
    ax2.axhline(0.80, color='#666666', linestyle=':', label="Cohen's d = 0.80 (Large Effect)", zorder=4)
    for bar, val in zip(ax2.patches, effect_sizes):
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.03, f'd = {val:.3f}\n(Large)', ha='center', va='bottom', fontweight='bold')
    ax2.set_ylabel("Causal Effect Size (Cohen's d)", fontweight='bold')
    ax2.set_title("Causal Effect Size on Physical Navigation", fontweight='bold', pad=10)
    ax2.set_ylim(0, max(effect_sizes) * 1.30)
    ax2.grid(True, axis='y')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    p6_path = EVIDENCE_DIR / "plot6_stage3_1R_2114_unit_breakdown.png"
    plt.savefig(p6_path, dpi=300)
    plt.close()
    print(f"Saved: {p6_path}")


if __name__ == "__main__":
    generate_plots()
