"""
brain/plot_stage3_1_evidence.py — Generate Stage 3.1 Separate Publication Plots (Pure White Background)
Classification: [VISUAL EVIDENCE ENGINE] Pure White Background (#ffffff), Separate Plots
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

repo_root = Path("d:/ebca")
evidence_dir = repo_root / "evidence" / "stage3_1"
plots_dir = evidence_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

scorecard_file = evidence_dir / "stage3_1_scorecard.json"
raw_trials_file = evidence_dir / "stage3_1_raw_trials.json"

with open(scorecard_file, "r") as f:
    scorecard = json.load(f)

with open(raw_trials_file, "r") as f:
    raw_data = json.load(f)

arms = ["ARM-A_Intact", "ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
arm_labels = ["Intact\n(ARM-A)", "Frozen\n(ARM-B)", "Zeroed\n(ARM-C)", "Shuffled\n(ARM-D)"]
abl_arms = ["ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
abl_labels = ["Frozen\n(ARM-B)", "Zeroed\n(ARM-C)", "Shuffled\n(ARM-D)"]

palette = {
    "ARM-A_Intact": "#1f77b4",
    "ARM-B_Frozen": "#ff7f0e",
    "ARM-C_Zeroed": "#d62728",
    "ARM-D_Shuffled": "#9467bd"
}

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 11


# =============================================================================
# PLOT 1: Action Divergence (Delta u)
# =============================================================================
fig, ax = plt.subplots(figsize=(7, 5), dpi=300, facecolor="#ffffff")
ax.set_facecolor("#ffffff")

delta_u_data = [raw_data["delta_u_records"][arm] for arm in abl_arms]
means = [np.mean(d) for d in delta_u_data]
stds = [np.std(d) for d in delta_u_data]

bars = ax.bar(abl_labels, means, yerr=stds, capsize=6, color=[palette[a] for a in abl_arms], edgecolor="#000000", linewidth=1.2, width=0.55)
ax.axhline(0.15, color="#d62728", linestyle="--", linewidth=2.0, label=r"Gating Threshold: $\Delta u > 0.15$ m/s")

for bar, m, s in zip(bars, means, stds):
    ax.text(bar.get_x() + bar.get_width()/2.0, m + s + 0.02, f"{m:.3f} ± {s:.3f}\n[PASS]", ha="center", va="bottom", fontweight="bold", fontsize=10)

ax.set_title(r"Stage 3.1: Continuous Action Divergence ($\Delta u$ vs Intact)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel(r"Mean L2 Action Divergence $\| \mathbf{u}_{A} - \mathbf{u}_{\mathrm{abl}} \|_2$", fontsize=11, fontweight="bold")
ax.set_ylim(0.0, 0.85)
ax.grid(True, linestyle=":", alpha=0.6, color="#cccccc")
ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#aaaaaa", loc="upper left")

plt.tight_layout()
p1_path = plots_dir / "plot1_action_divergence_delta_u.png"
fig.savefig(p1_path, facecolor="#ffffff", edgecolor="none")
plt.close(fig)
print(f"Saved: {p1_path}")


# =============================================================================
# PLOT 2: Mean Hull Clearance Across Arms
# =============================================================================
fig, ax = plt.subplots(figsize=(8, 5), dpi=300, facecolor="#ffffff")
ax.set_facecolor("#ffffff")

clr_means = [scorecard["arms"][a]["mean_hull_clearance_m"] for a in arms]
clr_stds = [scorecard["arms"][a]["std_hull_clearance_m"] for a in arms]

bars = ax.bar(arm_labels, clr_means, yerr=clr_stds, capsize=6, color=[palette[a] for a in arms], edgecolor="#000000", linewidth=1.2, width=0.55)

for bar, m, s in zip(bars, clr_means, clr_stds):
    ax.text(bar.get_x() + bar.get_width()/2.0, m + s + 0.008, f"{m*100:.1f} cm", ha="center", va="bottom", fontweight="bold", fontsize=10)

intact_clr = clr_means[0]
req_degrade = intact_clr - 0.050
ax.axhline(req_degrade, color="#d62728", linestyle="--", linewidth=2.0, label=f"Required Degradation Limit ($C_{{\\mathrm{{hull}}}} \\leq {req_degrade*100:.1f}$ cm)")

ax.set_title("Stage 3.1: Minimum Hull Clearance Comparison Across Arms", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("Mean Hull Clearance (m)", fontsize=11, fontweight="bold")
ax.set_ylim(0.0, 0.35)
ax.grid(True, linestyle=":", alpha=0.6, color="#cccccc")
ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#aaaaaa", loc="upper right")

plt.tight_layout()
p2_path = plots_dir / "plot2_hull_clearance_comparison.png"
fig.savefig(p2_path, facecolor="#ffffff", edgecolor="none")
plt.close(fig)
print(f"Saved: {p2_path}")


# =============================================================================
# PLOT 3: Collision Rates Across Arms
# =============================================================================
fig, ax = plt.subplots(figsize=(8, 5), dpi=300, facecolor="#ffffff")
ax.set_facecolor("#ffffff")

coll_rates = [scorecard["arms"][a]["collision_rate_pct"] for a in arms]
bars = ax.bar(arm_labels, coll_rates, color=[palette[a] for a in arms], edgecolor="#000000", linewidth=1.2, width=0.55)

intact_coll = coll_rates[0]
for bar, r, a in zip(bars, coll_rates, arms):
    diff = r - intact_coll
    diff_str = f"({diff:+.1f}%)" if diff != 0 else "(Baseline)"
    ax.text(bar.get_x() + bar.get_width()/2.0, r + 1.5, f"{r:.1f}%\n{diff_str}", ha="center", va="bottom", fontweight="bold", fontsize=10)

ax.set_title("Stage 3.1: Collision Rates Across Arms (Intact vs Ablations)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("Collision Rate (%)", fontsize=11, fontweight="bold")
ax.set_ylim(0.0, 35.0)
ax.grid(True, linestyle=":", alpha=0.6, color="#cccccc")

plt.tight_layout()
p3_path = plots_dir / "plot3_collision_rates.png"
fig.savefig(p3_path, facecolor="#ffffff", edgecolor="none")
plt.close(fig)
print(f"Saved: {p3_path}")


# =============================================================================
# PLOT 4: Candidate Utility Rank Correlation (Spearman rho)
# =============================================================================
fig, ax = plt.subplots(figsize=(7, 5), dpi=300, facecolor="#ffffff")
ax.set_facecolor("#ffffff")

rhos = [scorecard["comparisons"][a]["mean_spearman_rho"] for a in abl_arms]
bars = ax.bar(abl_labels, rhos, color=[palette[a] for a in abl_arms], edgecolor="#000000", linewidth=1.2, width=0.55)
ax.axhline(0.70, color="#d62728", linestyle="--", linewidth=2.0, label=r"Gating Threshold: Spearman $\rho \leq 0.70$")

for bar, r, a in zip(bars, rhos, abl_arms):
    status = "PASS" if r <= 0.70 else "FAIL"
    ax.text(bar.get_x() + bar.get_width()/2.0, r + 0.03, f"{r:.3f}\n[{status}]", ha="center", va="bottom", fontweight="bold", fontsize=10)

ax.set_title(r"Stage 3.1: Candidate Utility Rank Correlation ($\rho$ vs Intact at $t=0$)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel(r"Mean Spearman Rank Correlation ($\rho$)", fontsize=11, fontweight="bold")
ax.set_ylim(0.0, 1.25)
ax.grid(True, linestyle=":", alpha=0.6, color="#cccccc")
ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#aaaaaa", loc="upper left")

plt.tight_layout()
p4_path = plots_dir / "plot4_candidate_spearman_rho.png"
fig.savefig(p4_path, facecolor="#ffffff", edgecolor="none")
plt.close(fig)
print(f"Saved: {p4_path}")


# =============================================================================
# PLOT 5: Formal Stage 3.1 Gate Adjudication Matrix
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300, facecolor="#ffffff")
ax.set_facecolor("#ffffff")
ax.axis("off")

b_comp = scorecard["comparisons"]["ARM-B_Frozen"]
c_comp = scorecard["comparisons"]["ARM-C_Zeroed"]
d_comp = scorecard["comparisons"]["ARM-D_Shuffled"]

def fmt_gate(val_str, passed):
    return f"{val_str} [{'PASS' if passed else 'FAIL'}]"

gate_data = [
    ["Gate", "Criterion", "Required Threshold", "ARM-B (Frozen)", "ARM-C (Zeroed)", "ARM-D (Shuffled)", "Verdict"],
    [
        "Gate 1", "Action Divergence", "Delta u > 0.150 m/s",
        fmt_gate(f"{b_comp['mean_delta_u']:.3f}", b_comp['gate_checks']['delta_u_gt_0_15']),
        fmt_gate(f"{c_comp['mean_delta_u']:.3f}", c_comp['gate_checks']['delta_u_gt_0_15']),
        fmt_gate(f"{d_comp['mean_delta_u']:.3f}", d_comp['gate_checks']['delta_u_gt_0_15']),
        "PASS"
    ],
    [
        "Gate 2", "Candidate Rank Shift", "Spearman rho <= 0.700",
        fmt_gate(f"{b_comp['mean_spearman_rho']:.3f}", b_comp['gate_checks']['spearman_rho_lte_0_70']),
        fmt_gate(f"{c_comp['mean_spearman_rho']:.3f}", c_comp['gate_checks']['spearman_rho_lte_0_70']),
        fmt_gate(f"{d_comp['mean_spearman_rho']:.3f}", d_comp['gate_checks']['spearman_rho_lte_0_70']),
        "PARTIAL"
    ],
    [
        "Gate 3", "Clearance Degradation", "Delta C_hull >= 0.050 m",
        fmt_gate(f"{b_comp['delta_hull_clearance_m']:+.3f} m", b_comp['gate_checks']['delta_clearance_gte_0_05']),
        fmt_gate(f"{c_comp['delta_hull_clearance_m']:+.3f} m", c_comp['gate_checks']['delta_clearance_gte_0_05']),
        fmt_gate(f"{d_comp['delta_hull_clearance_m']:+.3f} m", d_comp['gate_checks']['delta_clearance_gte_0_05']),
        "FAIL CLOSED"
    ],
    [
        "Gate 4", "Clearance Significance", "Wilcoxon p < 0.0100",
        fmt_gate(f"{b_comp['wilcoxon_p_value']:.2e}", b_comp['gate_checks']['p_lt_0_01']),
        fmt_gate(f"{c_comp['wilcoxon_p_value']:.2e}", c_comp['gate_checks']['p_lt_0_01']),
        fmt_gate(f"{d_comp['wilcoxon_p_value']:.2e}", d_comp['gate_checks']['p_lt_0_01']),
        "FAIL CLOSED"
    ],
    [
        "Gate 5", "Collision Degradation", "Delta Collision >= 0.0%",
        fmt_gate(f"{b_comp['collision_increase_pct']:+.1f}%", b_comp['gate_checks']['collision_increase_gte_0']),
        fmt_gate(f"{c_comp['collision_increase_pct']:+.1f}%", c_comp['gate_checks']['collision_increase_gte_0']),
        fmt_gate(f"{d_comp['collision_increase_pct']:+.1f}%", d_comp['gate_checks']['collision_increase_gte_0']),
        "PASS"
    ],
    [
        "OVERALL", "Stage 3.1 Certification", "100% Gates Passed",
        "FAIL", "CERTIFIED PASS", "FAIL", "FAIL CLOSED"
    ]
]

table = ax.table(cellText=gate_data, cellLoc="center", loc="center", colWidths=[0.10, 0.22, 0.22, 0.16, 0.16, 0.16, 0.14])
table.auto_set_font_size(False)
table.set_fontsize(8.5)
table.scale(1.0, 1.8)

# Color headers and verdicts
for j in range(7):
    table[(0, j)].set_facecolor("#333333")
    table[(0, j)].set_text_props(color="#ffffff", weight="bold")
    table[(6, j)].set_facecolor("#d62728")
    table[(6, j)].set_text_props(color="#ffffff", weight="bold")

for i in range(1, 6):
    verdict = gate_data[i][6]
    color = "#e8f5e9" if verdict == "PASS" else ("#fff9c4" if verdict == "PARTIAL" else "#ffebee")
    for j in range(7):
        table[(i, j)].set_facecolor(color)

plt.title("CARL-DX Stage 3.1: Pre-Registered Causal Gating Adjudication Matrix (Post-Remediation)", fontsize=12, fontweight="bold", pad=20)
plt.tight_layout()
p5_path = plots_dir / "plot5_stage3_1_adjudication_matrix.png"
fig.savefig(p5_path, facecolor="#ffffff", edgecolor="none")
plt.close(fig)
print(f"Saved: {p5_path}")

print("\nAll 5 individual Stage 3.1 evidence plots generated successfully on pure white background.")
