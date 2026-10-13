"""
brain/p1_integrate/carl_p1_integrate_visualizer.py
===================================================
Generates publication-quality visualizations for P1-Integrate:
1. Synaptic Weight Matrix Delta Heatmap (W_hazard before vs after crash).
2. Multi-Panel Neural & Neuromodulatory Dynamics Causal Trace.
3. 2D Spatial Trajectory Comparison (Training Crash vs Post-Learning Avoidance vs Relocated Transfer).
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

RESULTS_JSON = "scratch/p1_integrate_results.json"
OUTPUT_DIR = "C:/Users/MANAS/.gemini/antigravity-ide/brain/a3c6a2a8-e5db-41ca-891e-577421bbd5ca"


def generate_all_visualizations():
    if not os.path.exists(RESULTS_JSON):
        print(f"Error: {RESULTS_JSON} not found. Run carl_p1_integrate_harness.py first.")
        return

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    traces = data.get("detailed_traces", {}).get("seed_101_group_4", {})
    if not traces:
        print("Warning: Detailed trace data for seed 101 not found.")
        return

    w_init = np.array(traces["w_initial"])       # (1024, 7)
    w_post = np.array(traces["w_post_train"])    # (1024, 7)
    delta_w = w_post - w_init

    train_tel = traces["train_telemetry"]
    test_a_tel = traces["test_a_telemetry"]
    test_b_tel = traces["test_b_telemetry"]

    action_labels = [
        "STRAIGHT", "CURVE_L_GENTLE", "CURVE_L_SHARP", "SWERVE_L",
        "CURVE_R_GENTLE", "CURVE_R_SHARP", "SWERVE_R"
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # PLOT 1: SYNAPTIC WEIGHT HEATMAP (REAL NEURAL PLASTICITY DEPICTION)
    # ══════════════════════════════════════════════════════════════════════════
    fig1, axes = plt.subplots(1, 3, figsize=(18, 8), facecolor='#0f111a')
    for ax in axes:
        ax.set_facecolor('#1a1c29')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#444a66')

    # Zoom in on first 64 neurons for visible biological synaptic detail
    n_display = 64
    im0 = axes[0].imshow(w_init[:n_display, :], aspect='auto', cmap='magma', vmin=0, vmax=2.5)
    axes[0].set_title("Initial Synaptic Weights (W_initial)\nBefore Experience (Uniform / Zero)", color='white', fontsize=12, pad=12)
    axes[0].set_xlabel("Candidate Actions", color='white', fontsize=10)
    axes[0].set_ylabel("Reservoir Neurons (1..64)", color='white', fontsize=10)
    axes[0].set_xticks(range(7))
    axes[0].set_xticklabels(action_labels, rotation=45, ha='right', color='white', fontsize=8)

    im1 = axes[1].imshow(w_post[:n_display, :], aspect='auto', cmap='magma', vmin=0, vmax=2.5)
    axes[1].set_title("Post-Collision Weights (W_hazard)\nAfter Physical Collision Experience", color='white', fontsize=12, pad=12)
    axes[1].set_xlabel("Candidate Actions", color='white', fontsize=10)
    axes[1].set_xticks(range(7))
    axes[1].set_xticklabels(action_labels, rotation=45, ha='right', color='white', fontsize=8)

    im2 = axes[2].imshow(delta_w[:n_display, :], aspect='auto', cmap='viridis', vmin=0, vmax=2.5)
    axes[2].set_title("Synaptic Plasticity Delta (ΔW = η·Surprise·Valence·E)\nSelective Straight-Action Hazard Potentiation", color='#4deeea', fontsize=12, pad=12)
    axes[2].set_xlabel("Candidate Actions", color='white', fontsize=10)
    axes[2].set_xticks(range(7))
    axes[2].set_xticklabels(action_labels, rotation=45, ha='right', color='white', fontsize=8)

    cbar = fig1.colorbar(im2, ax=axes.ravel().tolist(), shrink=0.8, pad=0.02)
    cbar.ax.tick_params(colors='white')
    cbar.set_label("Synaptic Weight Potentiation (Hazard Readout)", color='white', fontsize=11)

    fig1.suptitle("CARL-DX P1-Integrate: Live Synaptic Plasticity in 1024-Neuron Reservoir Readout", color='white', fontsize=16, weight='bold', y=0.98)
    plot1_path = os.path.join(OUTPUT_DIR, "p1_integrate_synaptic_heatmap.png")
    fig1.savefig(plot1_path, dpi=200, bbox_inches='tight', facecolor=fig1.get_facecolor())
    plt.close(fig1)
    print(f"Saved Plot 1: {plot1_path}")

    # ══════════════════════════════════════════════════════════════════════════
    # PLOT 2: CAUSAL NEURAL & NEUROMODULATORY TIMELINE TRACE
    # ══════════════════════════════════════════════════════════════════════════
    fig2 = plt.figure(figsize=(16, 12), facecolor='#0f111a')
    gs = gridspec.GridSpec(5, 1, hspace=0.35)

    ticks = [t["tick"] * 0.033 for t in train_tel]
    collisions = [1.0 if t["collision"] else 0.0 for t in train_tel]
    surprises = [t["surprise"] for t in train_tel]
    valences = [t["valence"] for t in train_tel]
    dw_mags = [t["dw_mag"] for t in train_tel]
    q_hazards = [t["q_hazard"] for t in train_tel]
    efes = [t["efe"] for t in train_tel]

    ax0 = fig2.add_subplot(gs[0, 0], facecolor='#1a1c29')
    ax0.plot(ticks, collisions, color='#ff3366', linewidth=2.5, label="Physical Collision Event")
    ax0.fill_between(ticks, 0, collisions, color='#ff3366', alpha=0.3)
    ax0.set_ylabel("Collision", color='white')
    ax0.set_title("1. Physical Collision & Contact Impulse", color='white', fontsize=11, loc='left')
    ax0.grid(True, color='#2d3148', linestyle='--')
    ax0.tick_params(colors='white')

    ax1 = fig2.add_subplot(gs[1, 0], facecolor='#1a1c29')
    ax1.plot(ticks, surprises, color='#ffcc00', linewidth=2.0, label="Noradrenaline / Surprise Gate")
    ax1.plot(ticks, valences, color='#00ffcc', linewidth=1.5, linestyle=':', label="Dopaminergic Outcome Valence")
    ax1.set_ylabel("Modulation", color='white')
    ax1.set_title("2. Neuromodulatory Arousal & Reinforcement Signals", color='white', fontsize=11, loc='left')
    ax1.legend(loc='upper right', facecolor='#1a1c29', edgecolor='#444a66', labelcolor='white')
    ax1.grid(True, color='#2d3148', linestyle='--')
    ax1.tick_params(colors='white')

    ax2 = fig2.add_subplot(gs[2, 0], facecolor='#1a1c29')
    ax2.plot(ticks, dw_mags, color='#bf55ec', linewidth=2.0, label="Synaptic Weight Delta (||ΔW||_1)")
    ax2.fill_between(ticks, 0, dw_mags, color='#bf55ec', alpha=0.25)
    ax2.set_ylabel("||ΔW||", color='white')
    ax2.set_title("3. Experience-Dependent Three-Factor STDP Synaptic Update", color='white', fontsize=11, loc='left')
    ax2.grid(True, color='#2d3148', linestyle='--')
    ax2.tick_params(colors='white')

    ax3 = fig2.add_subplot(gs[3, 0], facecolor='#1a1c29')
    ax3.plot(ticks, q_hazards, color='#ff793f', linewidth=2.2, label="Learned Hazard Prediction P(Hazard | x_t)")
    ax3.set_ylabel("P(Hazard)", color='white')
    ax3.set_title("4. Grounded Hazard Likelihood Spiking in Active Direction", color='white', fontsize=11, loc='left')
    ax3.grid(True, color='#2d3148', linestyle='--')
    ax3.tick_params(colors='white')

    ax4 = fig2.add_subplot(gs[4, 0], facecolor='#1a1c29')
    ax4.plot(ticks, efes, color='#4deeea', linewidth=2.0, label="Selected Expected Free Energy G(a*)")
    ax4.set_xlabel("Time (seconds)", color='white', fontsize=11)
    ax4.set_ylabel("Min EFE", color='white')
    ax4.set_title("5. Free Energy Decision Landscape & Argmin Policy Flip", color='white', fontsize=11, loc='left')
    ax4.grid(True, color='#2d3148', linestyle='--')
    ax4.tick_params(colors='white')

    for ax in [ax0, ax1, ax2, ax3, ax4]:
        for spine in ax.spines.values():
            spine.set_color('#444a66')

    fig2.suptitle("CARL-DX Causal Timeline: Crash -> Noradrenaline Surge -> Plasticity -> Hazard Prediction -> Action Flip", color='white', fontsize=14, weight='bold', y=0.99)
    plot2_path = os.path.join(OUTPUT_DIR, "p1_integrate_causal_timeline.png")
    fig2.savefig(plot2_path, dpi=200, bbox_inches='tight', facecolor=fig2.get_facecolor())
    plt.close(fig2)
    print(f"Saved Plot 2: {plot2_path}")

    # ══════════════════════════════════════════════════════════════════════════
    # PLOT 3: 2D SPATIAL TRAJECTORY & GENERALIZATION TRANSFER
    # ══════════════════════════════════════════════════════════════════════════
    fig3, (tax1, tax2) = plt.subplots(1, 2, figsize=(16, 7), facecolor='#0f111a')
    for ax in (tax1, tax2):
        ax.set_facecolor('#1a1c29')
        ax.tick_params(colors='white')
        ax.grid(True, color='#2d3148', linestyle='--')
        for spine in ax.spines.values():
            spine.set_color('#444a66')

    # Arena A: Training Crash vs Post-Learning Avoidance
    # Obstacle at (1.0, 0.0)
    obs_patch_a = plt.Rectangle((0.85, -0.15), 0.30, 0.30, color='#ff3366', alpha=0.8, label="Physical Obstacle (x=1.0, y=0.0)")
    tax1.add_patch(obs_patch_a)
    tax1.scatter([2.2], [0.0], color='#00ffcc', s=120, zorder=5, label="Target Food (2.2, 0.0)")

    train_x = [t["x"] for t in train_tel]
    train_y = [t["y"] for t in train_tel]
    test_a_x = [t["x"] for t in test_a_tel]
    test_a_y = [t["y"] for t in test_a_tel]

    tax1.plot(train_x, train_y, color='#ff9f43', linestyle='--', linewidth=2.2, label="Run 1: Training (Crash & Learn)")
    tax1.plot(test_a_x, test_a_y, color='#4deeea', linewidth=2.8, label="Run 2: Test A (Learned Synaptic Avoidance)")
    tax1.set_title("Arena A: Training Crash vs. Learned Avoidance", color='white', fontsize=13, weight='bold')
    tax1.set_xlabel("X Position (meters)", color='white')
    tax1.set_ylabel("Y Position (meters)", color='white')
    tax1.set_xlim(-0.2, 2.5)
    tax1.set_ylim(-0.8, 0.8)
    tax1.legend(loc='lower left', facecolor='#1a1c29', edgecolor='#444a66', labelcolor='white')

    # Arena B: Generalization Transfer (Relocated Obstacle at x=1.0, y=1.5)
    obs_patch_b = plt.Rectangle((0.85, 1.35), 0.30, 0.30, color='#ff3366', alpha=0.8, label="Relocated Obstacle (x=1.0, y=1.5)")
    tax2.add_patch(obs_patch_b)
    tax2.scatter([2.2], [1.5], color='#00ffcc', s=120, zorder=5, label="Relocated Target (2.2, 1.5)")

    test_b_x = [t["x"] for t in test_b_tel]
    test_b_y = [t["y"] for t in test_b_tel]

    tax2.plot(test_b_x, test_b_y, color='#bf55ec', linewidth=2.8, label="Test B: Spatial Generalization Transfer")
    tax2.set_title("Arena B: Relocated Obstacle Generalization", color='white', fontsize=13, weight='bold')
    tax2.set_xlabel("X Position (meters)", color='white')
    tax2.set_ylabel("Y Position (meters)", color='white')
    tax2.set_xlim(-0.2, 2.5)
    tax2.set_ylim(0.7, 2.3)
    tax2.legend(loc='lower left', facecolor='#1a1c29', edgecolor='#444a66', labelcolor='white')

    fig3.suptitle("CARL-DX P1-Integrate: Spatial Trajectory & Generalization Transfer Proofs", color='white', fontsize=16, weight='bold', y=0.98)
    plot3_path = os.path.join(OUTPUT_DIR, "p1_integrate_spatial_trajectories.png")
    fig3.savefig(plot3_path, dpi=200, bbox_inches='tight', facecolor=fig3.get_facecolor())
    plt.close(fig3)
    print(f"Saved Plot 3: {plot3_path}")


if __name__ == "__main__":
    generate_all_visualizations()
