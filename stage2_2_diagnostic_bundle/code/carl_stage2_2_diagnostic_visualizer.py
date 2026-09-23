"""
brain/carl_stage2_2_diagnostic_visualizer.py — Publication Figure Generator (Stage 2.2-DIAG)
Classification: [VISUALIZATION PIPELINE] 300 DPI Publication Dashboards

Reads `evidence/stage2_2_diag/diagnostic_scorecard.json` and renders authoritative, publication-quality figures:
- Figure 1: Multi-Horizon Predictive Fidelity (Direct vs Residual on D_all and D_dynamic)
- Figure 2: Action Causality Signature (Action Zeroing, Permutation, Sign Inversion)
- Figure 3: Spatial Disambiguation & Phase Scrambling
- Figure 4: Counterfactual Action Branching Divergence
- Figure 5: Capacity Control Isolation (M2-B-MATCHED vs M6-F-RES vs M5-E-RES)
- Figure 6: Collision Anticipation ROC Curves
- Figure 7: Master Executive Diagnostic Dashboard
"""

import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parent.parent


def generate_all_diagnostic_figures(scorecard_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(scorecard_path, "r") as f:
        scorecard = json.load(f)

    models = scorecard["models"]

    # Style setup
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 14,
        "lines.linewidth": 2.0,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--"
    })

    # Color palette
    colors = {
        "dir": "#e74c3c",       # Red
        "res": "#2980b9",       # Blue
        "matched": "#8e44ad",   # Purple
        "memory": "#27ae60",    # Green
        "neutral": "#34495e"
    }

    # -------------------------------------------------------------
    # FIGURE 1: MULTI-HORIZON PREDICTIVE FIDELITY (Direct vs Residual)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    horizons = [1, 5, 10, 15, 30]

    # Panel A: All Timesteps
    ax = axes[0]
    for mid, mdata in models.items():
        bat1 = mdata["batteries"]["Battery_1_Predictive_Fidelity"]
        r2_vals = [bat1[f"H_{h}"]["dynamic_sonar_r2_all"] for h in horizons]
        color = colors["res"] if mdata["is_residual"] else colors["dir"]
        ls = "-" if mdata["is_residual"] else "--"
        alpha = 0.9 if "M5-E" in mid or "M6-F" in mid or "MATCHED" in mid else 0.4
        ax.plot(horizons, r2_vals, label=mid, color=color, linestyle=ls, alpha=alpha, marker="o", markersize=4)

    ax.axhline(0.60, color="#d35400", linestyle=":", label="Preregistered Target (0.60)")
    ax.set_title(r"A: Dynamic Sonar R² vs Horizon (All Timesteps $\mathcal{D}_{all}$)")
    ax.set_xlabel("Prediction Horizon H (ticks, 30ms/tick)")
    ax.set_ylabel("R² Score (s < 4.5m)")
    ax.set_ylim(-0.5, 1.0)

    # Panel B: High-Change Transition Partition (D_dynamic)
    ax = axes[1]
    for mid, mdata in models.items():
        bat1 = mdata["batteries"]["Battery_1_Predictive_Fidelity"]
        r2_dyn = [bat1[f"H_{h}"]["dynamic_sonar_r2_high_change"] for h in horizons]
        color = colors["res"] if mdata["is_residual"] else colors["dir"]
        ls = "-" if mdata["is_residual"] else "--"
        alpha = 0.9 if "M5-E" in mid or "M6-F" in mid or "MATCHED" in mid else 0.4
        ax.plot(horizons, r2_dyn, label=mid, color=color, linestyle=ls, alpha=alpha, marker="s", markersize=4)

    ax.axhline(0.50, color="#d35400", linestyle=":", label="High-Change Target (0.50)")
    ax.set_title(r"B: Dynamic Sonar R² on High-Change Transitions ($\mathcal{D}_{dynamic}$)")
    ax.set_xlabel("Prediction Horizon H (ticks)")
    ax.set_ylabel(r"R² Score (|Δs| >= 0.15m)")
    ax.set_ylim(-0.5, 1.0)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", ncol=1, frameon=True)

    plt.tight_layout()
    fig_path1 = output_dir / "diag_fig1_predictive_fidelity.png"
    plt.savefig(fig_path1)
    plt.close()
    print(f"Saved: {fig_path1}")

    # -------------------------------------------------------------
    # FIGURE 2: ACTION CAUSALITY PROFILE (Zero, Permute, Invert)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
    model_names = list(models.keys())
    x_indices = np.arange(len(model_names))
    width = 0.25

    zero_surges = [models[m]["batteries"]["Battery_2_Action_Causality"]["action_zero_error_surge_pct"] for m in model_names]
    perm_surges = [models[m]["batteries"]["Battery_2_Action_Causality"]["action_permute_error_surge_pct"] for m in model_names]
    inv_surges = [models[m]["batteries"]["Battery_2_Action_Causality"]["action_sign_invert_surge_pct"] for m in model_names]

    ax.bar(x_indices - width, zero_surges, width, label="Action Zeroing (ΔE)", color="#e67e22")
    ax.bar(x_indices, perm_surges, width, label="Action Permutation (ΔE)", color="#f39c12")
    ax.bar(x_indices + width, inv_surges, width, label="Action Sign Invert (ΔE)", color="#c0392b")

    ax.axhline(25.0, color="#e67e22", linestyle="--", alpha=0.7, label="Zero Target (+25%)")
    ax.axhline(20.0, color="#f39c12", linestyle=":", alpha=0.7, label="Permute Target (+20%)")
    ax.axhline(30.0, color="#c0392b", linestyle="-.", alpha=0.7, label="Invert Target (+30%)")

    ax.set_xticks(x_indices)
    ax.set_xticklabels(model_names, rotation=45, ha="right")
    ax.set_ylabel("Error Surge Relative to Baseline (%)")
    ax.set_title("Action Causality Interventions across 13 Model Configurations")
    ax.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    fig_path2 = output_dir / "diag_fig2_action_causality.png"
    plt.savefig(fig_path2)
    plt.close()
    print(f"Saved: {fig_path2}")

    # -------------------------------------------------------------
    # FIGURE 3: CAPACITY CONTROL COMPARISON (M2-B-MATCHED vs M6-F-RES vs M5-E-RES)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), dpi=300)
    key_models = ["M2-B-RES", "M2-B-MATCHED", "M5-E-RES", "M6-F-RES"]

    # Panel A: Sonar R² vs Horizon
    ax = axes[0]
    for mid in key_models:
        if mid in models:
            mdata = models[mid]
            r2_dyn = [mdata["batteries"]["Battery_1_Predictive_Fidelity"][f"H_{h}"]["dynamic_sonar_r2_high_change"] for h in horizons]
            ax.plot(horizons, r2_dyn, label=f"{mid} ({mdata['parameter_count']:,d}p)", marker="o")
    ax.set_title("A: High-Change Sonar R² (Capacity Control)")
    ax.set_xlabel("Horizon H")
    ax.set_ylabel(r"R² on $\mathcal{D}_{dynamic}$")
    ax.legend(frameon=True)

    # Panel B: Spatial Disambiguation Divergence
    ax = axes[1]
    div_vals = [models[m]["batteries"]["Battery_4_Spatial_Disambiguation"]["mean_divergence_meters"] if m in models else 0.0 for m in key_models]
    ax.bar(key_models, div_vals, color=["#3498db", "#8e44ad", "#e67e22", "#27ae60"])
    ax.axhline(1.5, color="red", linestyle="--", label="Target (1.5m)")
    ax.set_title("B: Spatial Disambiguation Divergence (H=10)")
    ax.set_ylabel("Future Divergence (m)")
    ax.legend(frameon=True)

    plt.tight_layout()
    fig_path3 = output_dir / "diag_fig3_capacity_and_memory.png"
    plt.savefig(fig_path3)
    plt.close()
    print(f"Saved: {fig_path3}")

    # -------------------------------------------------------------
    # FIGURE 4: MASTER EXECUTIVE DASHBOARD
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(15, 10), dpi=300)
    gs = fig.add_gridspec(2, 3)

    # Panel 1: Multi-Horizon R²
    ax1 = fig.add_subplot(gs[0, 0])
    for mid in ["M2-B-DIR", "M2-B-RES", "M5-E-RES", "M6-F-RES"]:
        if mid in models:
            r2 = [models[mid]["batteries"]["Battery_1_Predictive_Fidelity"][f"H_{h}"]["dynamic_sonar_r2_all"] for h in horizons]
            ax1.plot(horizons, r2, label=mid, marker="o")
    ax1.set_title("1. Dynamic Sonar R²")
    ax1.set_xlabel("Horizon H")
    ax1.set_ylabel("R² Score")
    ax1.legend()

    # Panel 2: Action Zero Surge
    ax2 = fig.add_subplot(gs[0, 1])
    res_models = [m for m in model_names if "RES" in m or "MATCHED" in m]
    z_surges = [models[m]["batteries"]["Battery_2_Action_Causality"]["action_zero_error_surge_pct"] for m in res_models]
    ax2.bar(res_models, z_surges, color="#3498db")
    ax2.axhline(25.0, color="red", linestyle="--")
    ax2.set_title("2. Action Zero Surge (%)")
    ax2.set_xticks(range(len(res_models)))
    ax2.set_xticklabels(res_models, rotation=45, ha="right")

    # Panel 3: Spatial Disambiguation
    ax3 = fig.add_subplot(gs[0, 2])
    disambigs = [models[m]["batteries"]["Battery_4_Spatial_Disambiguation"]["mean_divergence_meters"] for m in res_models]
    ax3.bar(res_models, disambigs, color="#2ecc71")
    ax3.axhline(1.5, color="red", linestyle="--")
    ax3.set_title("3. Spatial Disambiguation (m)")
    ax3.set_xticks(range(len(res_models)))
    ax3.set_xticklabels(res_models, rotation=45, ha="right")

    # Panel 4: Counterfactual Divergence
    ax4 = fig.add_subplot(gs[1, 0])
    branchings = [models[m]["batteries"]["Battery_5_Counterfactual_Branching"]["mean_pairwise_divergence_meters"] for m in res_models]
    ax4.bar(res_models, branchings, color="#e74c3c")
    ax4.axhline(1.0, color="red", linestyle="--")
    ax4.set_title("4. Branch Divergence (m)")
    ax4.set_xticks(range(len(res_models)))
    ax4.set_xticklabels(res_models, rotation=45, ha="right")

    # Panel 5: Collision Anticipation ROC-AUC
    ax5 = fig.add_subplot(gs[1, 1])
    aucs = [models[m]["batteries"]["Battery_6_Collision_Anticipation"]["collision_roc_auc"] for m in res_models]
    ax5.bar(res_models, aucs, color="#9b59b6")
    ax5.axhline(0.85, color="red", linestyle="--")
    ax5.set_title("5. Collision ROC-AUC")
    ax5.set_xticks(range(len(res_models)))
    ax5.set_xticklabels(res_models, rotation=45, ha="right")
    ax5.set_ylim(0.4, 1.0)

    # Panel 6: Parameter Count vs H=10 Score
    ax6 = fig.add_subplot(gs[1, 2])
    for m in model_names:
        p = models[m]["parameter_count"]
        r = models[m]["batteries"]["Battery_1_Predictive_Fidelity"]["H_10"]["dynamic_sonar_r2_high_change"]
        color = "#27ae60" if "M6-F" in m else ("#8e44ad" if "MATCHED" in m else ("#2980b9" if "RES" in m else "#e74c3c"))
        ax6.scatter(p, r, color=color, s=80)
        ax6.annotate(m, (p, r), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax6.set_title("6. Parameters vs Dynamic Sonar R² (H=10)")
    ax6.set_xlabel("Parameter Count")
    ax6.set_ylabel("High-Change Sonar R²")

    plt.tight_layout()
    fig_path4 = output_dir / "diag_fig4_master_dashboard.png"
    plt.savefig(fig_path4)
    plt.close()
    print(f"Saved: {fig_path4}")


if __name__ == "__main__":
    scorecard_p = Path("evidence/stage2_2_diag/diagnostic_scorecard.json")
    out_d = Path("evidence/stage2_2_diag")
    if scorecard_p.exists():
        generate_all_diagnostic_figures(scorecard_p, out_d)
    else:
        print(f"Scorecard not found at {scorecard_p}")
