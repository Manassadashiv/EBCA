"""
tools/p1_r2/p1r2_plot_generator.py — Forensic Plot Generator for P1-R2 Pilot Campaign

Generates canonical 4-panel publication-grade figures:
1. evidence/p1_r2/plots/p1r2_trajectory_comparison.png
2. evidence/p1_r2/plots/p1r2_time_to_target_comparison.png
3. evidence/p1_r2/plots/p1r2_memory_growth_trace.png
4. evidence/p1_r2/plots/p1r2_efe_candidate_distribution.png
"""

import os
import glob
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_p1r2_plots(base_dir: str = "d:/ebca"):
    plots_dir = os.path.join(base_dir, "evidence", "p1_r2", "plots")
    telemetry_dir = os.path.join(base_dir, "evidence", "p1_r2", "telemetry")
    os.makedirs(plots_dir, exist_ok=True)
    
    plt.style.use('dark_background')
    
    # 1. Trajectory Comparison Plot (Ep 1 vs Ep 3 vs Ep 5)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
    fig.suptitle("CARL-DX Phase 1-R2: 2D Trajectory Emergence Across Perturbation Episodes", fontsize=14, color="#00e5ff")
    
    episodes = [1, 3, 5]
    ep_titles = ["Episode 1: Initial Baseline", "Episode 3: North Corridor Perturbation", "Episode 5: Recurrent Perturbation"]
    
    colors = {"FULL_P1_R2": "#00ffcc", "P0_CONTROL": "#ff7043", "NO_MEMORY": "#ab47bc"}
    
    for ax_idx, ep in enumerate(episodes):
        ax = axes[ax_idx]
        ax.set_title(ep_titles[ax_idx], fontsize=11, color="#e0e0e0")
        ax.set_xlim(-0.5, 2.2)
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlabel("X Position (m)", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Y Position (m)", fontsize=10)
        ax.grid(True, alpha=0.25, linestyle="--")
        
        # Draw central divider & food beacon
        ax.plot([0.20, 0.85], [0.0, 0.0], color="#ff5252", linewidth=3, label="Central Divider" if ax_idx==0 else "")
        ax.scatter([1.60], [0.0], color="#ffd700", s=150, marker="*", label="Food Beacon (Goal)" if ax_idx==0 else "")
        
        if ep in (3, 5):
            ax.scatter([0.55], [0.45], color="#ff1744", s=120, marker="X", label="Perturbation Barrier" if ax_idx==1 else "")
            
        for cond in ["FULL_P1_R2", "P0_CONTROL", "NO_MEMORY"]:
            for seed in [42, 101, 2024]:
                csv_path = os.path.join(telemetry_dir, f"telemetry_{cond}_s{seed}_ep{ep}.csv")
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    lbl = cond if (seed == 42) else ""
                    ax.plot(df["pos_x"], df["pos_y"], color=colors[cond], alpha=0.75, linewidth=1.8, label=lbl)
                    
        if ax_idx == 0:
            ax.legend(loc="upper left", fontsize=8)
            
    plt.tight_layout()
    traj_path = os.path.join(plots_dir, "p1r2_trajectory_comparison.png")
    plt.savefig(traj_path, dpi=300)
    plt.close()
    print(f"[PLOT] Generated {traj_path}")
    
    # 2. Time-To-Target Comparison Bar Chart
    with open(os.path.join(base_dir, "CARL_P1R2_PILOT_REPORT.json"), "r") as fp:
        rep = json.load(fp)
        
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle("CARL-DX P1-R2: Time-to-Target Across Experimental Conditions", fontsize=14, color="#00e5ff")
    
    cond_names = list(rep["condition_summaries"].keys())
    means = [rep["condition_summaries"][c]["mean_time_to_target"] for c in cond_names]
    stds = [rep["condition_summaries"][c]["std_time_to_target"] for c in cond_names]
    
    bar_colors = ["#00ffcc", "#ff7043", "#ab47bc"]
    bars = ax.bar(cond_names, means, yerr=stds, capsize=6, color=bar_colors, alpha=0.85, edgecolor="#ffffff")
    
    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2.0, m + 0.3, f"{m:.2f}s", ha="center", va="bottom", color="#ffffff", fontweight="bold")
        
    ax.set_ylabel("Mean Time to Target (s)", fontsize=11)
    ax.set_ylim(0, 12)
    ax.grid(True, alpha=0.25, linestyle="--", axis="y")
    
    plt.tight_layout()
    time_path = os.path.join(plots_dir, "p1r2_time_to_target_comparison.png")
    plt.savefig(time_path, dpi=300)
    plt.close()
    print(f"[PLOT] Generated {time_path}")
    
    # 3. Memory Accumulation Trace
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle("CARL-DX P1-R2: HDC Episodic Memory Accumulation Across Sequential Episodes", fontsize=14, color="#00e5ff")
    
    episodes_x = [1, 2, 3, 4, 5]
    for seed in [42, 101, 2024]:
        mem_counts = []
        for ep in episodes_x:
            rpath = os.path.join(base_dir, "evidence", "p1_r2", "runs", f"run_FULL_P1_R2_s{seed}_ep{ep}.json")
            if os.path.exists(rpath):
                with open(rpath, "r") as fp:
                    rdata = json.load(fp)
                    mem_counts.append(rdata["episodes_in_memory"])
            else:
                mem_counts.append(0)
        ax.plot(episodes_x, mem_counts, marker="o", linewidth=2.2, label=f"FULL_P1_R2 (Seed {seed})")
        
    ax.set_xlabel("Episode Number", fontsize=11)
    ax.set_ylabel("Total Episodes in Autobiographical Memory", fontsize=11)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.legend(loc="upper left")
    
    plt.tight_layout()
    mem_path = os.path.join(plots_dir, "p1r2_memory_growth_trace.png")
    plt.savefig(mem_path, dpi=300)
    plt.close()
    print(f"[PLOT] Generated {mem_path}")
    
    # 4. EFE Candidate Sequence Landscape
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle("CARL-DX P1-R2: Expected Free Energy (EFE) Distribution of Candidate Sequences", fontsize=14, color="#00e5ff")
    
    sample_csv = os.path.join(telemetry_dir, "telemetry_FULL_P1_R2_s42_ep3.csv")
    if os.path.exists(sample_csv):
        df = pd.read_csv(sample_csv)
        ax.plot(df["tick"], df["best_efe"], color="#00ffcc", linewidth=2, label="Selected Sequence EFE")
        ax.plot(df["tick"], df["pred_error"] * 100.0, color="#ff5252", linewidth=1.5, linestyle="--", label="Prediction Error (x100)")
        ax.set_xlabel("Simulation Tick (30 Hz)", fontsize=11)
        ax.set_ylabel("Expected Free Energy (EFE)", fontsize=11)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.legend(loc="upper right")
        
    plt.tight_layout()
    efe_path = os.path.join(plots_dir, "p1r2_efe_candidate_distribution.png")
    plt.savefig(efe_path, dpi=300)
    plt.close()
    print(f"[PLOT] Generated {efe_path}")


if __name__ == "__main__":
    generate_p1r2_plots()
