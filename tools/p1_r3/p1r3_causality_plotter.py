"""
tools/p1_r3/p1r3_causality_plotter.py — Publication Figure Generator for P1-R3 Memory Causality

Generates the 9 canonical publication figures in evidence/p1_r3/memory_causality/plots/:
1. 01_decision_state_matching.png
2. 02_FULL_vs_NO_MEMORY_route_choice.png
3. 03_memory_retrieval_vs_route_choice.png
4. 04_prediction_error_episode_progression.png
5. 05_pre_hazard_trajectory_divergence.png
6. 06_EFE_decomposition_at_recurrence.png
7. 07_context_update_extinction.png
8. 08_seed_replication.png
9. 09_physical_clearance_validation.png
"""

import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Dict, Any, List

DARK_BG = "#0E1117"
PANEL_BG = "#161B22"
GRID_COLOR = "#21262D"
TEXT_COLOR = "#E6EDF3"
CYAN = "#00E5FF"
CORAL = "#FF5252"
GREEN = "#00FF66"
GOLD = "#FFD700"
PURPLE = "#BD93F9"


class P1R3CausalityPlotter:
    def __init__(
        self,
        telemetry_dir: str = "evidence/p1_r3/memory_causality/telemetry",
        output_dir: str = "evidence/p1_r3/memory_causality/plots"
    ):
        self.telemetry_dir = telemetry_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        plt.style.use("dark_background")
        self.runs = {}
        for f in glob.glob(os.path.join(self.telemetry_dir, "*.csv")):
            k = os.path.splitext(os.path.basename(f))[0]
            self.runs[k] = pd.read_csv(f)

    def draw_arena_obstacles(self, ax, ep: int = 2):
        """Draws standard arena geometry and obstacles."""
        # Central divider at (0.65, 0.00), size [0.05, 0.25]
        ax.add_patch(plt.Rectangle((0.65 - 0.05, -0.25), 0.10, 0.50, color="#30363D", zorder=2))
        # Outer guide walls
        ax.add_patch(plt.Rectangle((0.65 - 0.45, 0.85 - 0.05), 0.90, 0.10, color="#30363D", zorder=2))
        ax.add_patch(plt.Rectangle((0.65 - 0.45, -0.85 - 0.05), 0.90, 0.10, color="#30363D", zorder=2))
        # Baffles at x=1.15
        ax.add_patch(plt.Rectangle((1.15 - 0.05, 0.55 - 0.25), 0.10, 0.50, color="#30363D", zorder=2))
        ax.add_patch(plt.Rectangle((1.15 - 0.05, -0.55 - 0.25), 0.10, 0.50, color="#30363D", zorder=2))
        # Target Food at (2.20, 0.00)
        ax.plot(2.20, 0.00, marker="*", color=GREEN, markersize=14, zorder=5, label="Target Food (2.20, 0.00)")
        # Latent hazard if Ep 1 or 2
        if ep in (1, 2):
            ax.add_patch(plt.Rectangle((1.45 - 0.05, -0.55 - 0.25), 0.10, 0.50, color="#FF1744", alpha=0.85, zorder=3, label="Latent Hazard Barrier"))

    def plot_01_decision_state_matching(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), facecolor=DARK_BG)
        for ax in (ax1, ax2):
            ax.set_facecolor(PANEL_BG)
            ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
            
        full_ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        nomem_ep2 = self.runs.get("P1R3_NO_MEMORY_S42_EP2")
        
        if full_ep2 is not None and nomem_ep2 is not None:
            sonar_cols = [f"sonar_{i}" for i in range(15)]
            angles = np.linspace(-120, 120, 15)
            
            s_full_t0 = full_ep2[sonar_cols].iloc[0].values
            s_nomem_t0 = nomem_ep2[sonar_cols].iloc[0].values
            
            # Decision tick (x ~ 0.35m)
            idx_f = (full_ep2["x"] > 0.35).idxmax() if (full_ep2["x"] > 0.35).any() else 0
            idx_n = (nomem_ep2["x"] > 0.35).idxmax() if (nomem_ep2["x"] > 0.35).any() else 0
            
            s_full_dec = full_ep2[sonar_cols].iloc[idx_f].values
            s_nomem_dec = nomem_ep2[sonar_cols].iloc[idx_n].values
            
            ax1.plot(angles, s_full_t0, "o-", color=CYAN, lw=2, label="FULL_P1_R3 (t=0)")
            ax1.plot(angles, s_nomem_t0, "s--", color=CORAL, lw=2, label="NO_MEMORY (t=0)")
            ax1.set_title("Initial Sensory State (t = 0.0s)", color=TEXT_COLOR, fontweight="bold")
            ax1.set_xlabel("Sonar Beam Angle (deg)", color=TEXT_COLOR)
            ax1.set_ylabel("Range Measurement (meters)", color=TEXT_COLOR)
            ax1.set_ylim(0, 3.5)
            ax1.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
            diff_dec = np.abs(s_full_dec - s_nomem_dec)
            ax2.bar(angles, diff_dec, width=10, color=GOLD, alpha=0.85, edgecolor=DARK_BG, label="Absolute Sonar Delta (|Δd|)")
            ax2.axhline(0.02, color=CORAL, linestyle="--", lw=1.5, label="Tolerance Gate (0.02 m)")
            ax2.set_title(f"Decision-Point Matching (|Δd| <= 0.02m) at x = 0.35m", color=TEXT_COLOR, fontweight="bold")
            ax2.set_xlabel("Sonar Beam Angle (deg)", color=TEXT_COLOR)
            ax2.set_ylabel("Absolute Difference (meters)", color=TEXT_COLOR)
            ax2.set_ylim(0, 0.05)
            ax2.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "01_decision_state_matching.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_02_full_vs_no_memory_route_choice(self):
        fig, ax = plt.subplots(figsize=(10, 6.5), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        self.draw_arena_obstacles(ax, ep=2)
        
        full_ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        nomem_ep2 = self.runs.get("P1R3_NO_MEMORY_S42_EP2")
        
        if full_ep2 is not None and nomem_ep2 is not None:
            ax.plot(full_ep2["x"], full_ep2["y"], color=CYAN, lw=3, label="FULL_P1_R3 (Episode 2: Route A Divergence)")
            ax.plot(nomem_ep2["x"], nomem_ep2["y"], color=CORAL, lw=3, linestyle="--", label="NO_MEMORY (Episode 2: Route B Persistence)")
            
            ax.axvline(0.35, color=GOLD, linestyle=":", lw=1.5, label="Route Commitment Line (x = 0.35m)")
            ax.axvline(0.45, color=PURPLE, linestyle=":", lw=1.5, label="Hazard Line-of-Sight (x = 0.45m)")
            
            ax.plot(0.0, 0.0, marker="o", color=TEXT_COLOR, markersize=8, label="Start Pose (0,0)")
            ax.set_xlim(-0.2, 2.5)
            ax.set_ylim(-1.1, 1.1)
            ax.set_title("P1-R3 Recurrence: FULL vs NO_MEMORY Route Choice", color=TEXT_COLOR, fontsize=12, fontweight="bold")
            ax.set_xlabel("Arena X (meters)", color=TEXT_COLOR)
            ax.set_ylabel("Arena Y (meters)", color=TEXT_COLOR)
            ax.legend(loc="upper left", facecolor=PANEL_BG, edgecolor=GRID_COLOR, fontsize=9)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "02_FULL_vs_NO_MEMORY_route_choice.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_03_memory_retrieval_vs_route_choice(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, facecolor=DARK_BG)
        for ax in (ax1, ax2):
            ax.set_facecolor(PANEL_BG)
            ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
            
        full_ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        if full_ep2 is not None:
            time_s = full_ep2["tick"] * 0.0333
            ax1.plot(time_s, full_ep2["y"], color=CYAN, lw=2.5, label="Lateral Trajectory y(t)")
            ax1.axhline(0.0, color="#6E7681", linestyle="--", alpha=0.6)
            ax1.set_ylabel("Lateral Position Y (m)", color=TEXT_COLOR)
            ax1.set_title("Memory Retrieval Dynamics Driving Physical Lateral Divergence", color=TEXT_COLOR, fontweight="bold")
            ax1.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
            ax2.plot(time_s, full_ep2["best_memory_similarity"], color=GOLD, lw=2.2, label="Associative Memory Valence Bias")
            ax2.plot(time_s, full_ep2["prediction_error"], color=CORAL, lw=1.8, linestyle=":", label="Prediction Error (m/s)")
            ax2.set_xlabel("Simulation Time (seconds)", color=TEXT_COLOR)
            ax2.set_ylabel("Retrieval Valence & Error", color=TEXT_COLOR)
            ax2.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "03_memory_retrieval_vs_route_choice.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_04_prediction_error_episode_progression(self):
        fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        
        ep1 = self.runs.get("P1R3_FULL_P1_R3_S42_EP1")
        ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        ep3 = self.runs.get("P1R3_FULL_P1_R3_S42_EP3")
        
        if ep1 is not None and ep2 is not None and ep3 is not None:
            ax.plot(ep1["tick"] * 0.0333, ep1["prediction_error"], color=CORAL, lw=2, label="Episode 1 (Experience - Hazard Collision Surge)")
            ax.plot(ep2["tick"] * 0.0333, ep2["prediction_error"], color=CYAN, lw=2, label="Episode 2 (Recurrence - Clean Detour)")
            ax.plot(ep3["tick"] * 0.0333, ep3["prediction_error"], color=GREEN, lw=2, label="Episode 3 (Context Update / Extinction)")
            
            ax.set_title("Prediction Error Dynamics Across Experiential Episodes", color=TEXT_COLOR, fontweight="bold")
            ax.set_xlabel("Simulation Time (seconds)", color=TEXT_COLOR)
            ax.set_ylabel("Prediction Error |v_actual - v_pred| (m/s)", color=TEXT_COLOR)
            ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "04_prediction_error_episode_progression.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_05_pre_hazard_trajectory_divergence(self):
        fig, ax = plt.subplots(figsize=(9, 6), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        
        full_ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        nomem_ep2 = self.runs.get("P1R3_NO_MEMORY_S42_EP2")
        
        if full_ep2 is not None and nomem_ep2 is not None:
            # Zoom-in to pre-hazard decision zone
            ax.plot(full_ep2["x"], full_ep2["y"], color=CYAN, lw=3, label="FULL_P1_R3 (Pre-Hazard Steer to North)")
            ax.plot(nomem_ep2["x"], nomem_ep2["y"], color=CORAL, lw=3, linestyle="--", label="NO_MEMORY (Pre-Hazard Steer to South)")
            
            ax.axvline(0.35, color=GOLD, linestyle="--", lw=2, label="Commitment Line (x = 0.35m)")
            ax.axvline(0.45, color=PURPLE, linestyle=":", lw=2, label="Hazard Line-of-Sight (x = 0.45m)")
            
            # Shaded pre-hazard decision window
            ax.axvspan(0.0, 0.35, color="#1F6FEB", alpha=0.15, label="Causal Pre-Hazard Decision Window")
            
            ax.set_xlim(-0.05, 0.60)
            ax.set_ylim(-0.50, 0.50)
            ax.set_title("Pre-Hazard Causal Divergence (Prior to Obstacle Observability)", color=TEXT_COLOR, fontweight="bold")
            ax.set_xlabel("Arena X (meters)", color=TEXT_COLOR)
            ax.set_ylabel("Arena Y (meters)", color=TEXT_COLOR)
            ax.legend(loc="upper left", facecolor=PANEL_BG, edgecolor=GRID_COLOR, fontsize=9)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "05_pre_hazard_trajectory_divergence.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_06_efe_decomposition_at_recurrence(self):
        fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        
        full_ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        if full_ep2 is not None:
            t = full_ep2["tick"] * 0.0333
            ax.plot(t, full_ep2["EFE_route_A"], color=CYAN, lw=2.2, label="EFE(Route A - North Corridor)")
            ax.plot(t, full_ep2["EFE_route_B"], color=CORAL, lw=2.2, label="EFE(Route B - South Corridor [Memory Biased])")
            
            ax.set_title("Expected Free Energy (EFE) Divergence at Recurrence", color=TEXT_COLOR, fontweight="bold")
            ax.set_xlabel("Simulation Time (seconds)", color=TEXT_COLOR)
            ax.set_ylabel("Expected Free Energy G(S)", color=TEXT_COLOR)
            ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "06_EFE_decomposition_at_recurrence.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_07_context_update_extinction(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        self.draw_arena_obstacles(ax, ep=3)
        
        ep1 = self.runs.get("P1R3_FULL_P1_R3_S42_EP1")
        ep2 = self.runs.get("P1R3_FULL_P1_R3_S42_EP2")
        ep3 = self.runs.get("P1R3_FULL_P1_R3_S42_EP3")
        
        if ep1 is not None and ep2 is not None and ep3 is not None:
            ax.plot(ep1["x"], ep1["y"], color=CORAL, lw=2, label="Ep 1: Experience (Route B)")
            ax.plot(ep2["x"], ep2["y"], color=CYAN, lw=2.5, label="Ep 2: Recurrence (Route A Switch)")
            ax.plot(ep3["x"], ep3["y"], color=GREEN, lw=2.5, linestyle="--", label="Ep 3: Extinction / Context Update")
            
            ax.set_xlim(-0.2, 2.5)
            ax.set_ylim(-1.1, 1.1)
            ax.set_title("3-Episode Progression: Experience -> Recurrence -> Extinction", color=TEXT_COLOR, fontweight="bold")
            ax.set_xlabel("Arena X (meters)", color=TEXT_COLOR)
            ax.set_ylabel("Arena Y (meters)", color=TEXT_COLOR)
            ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "07_context_update_extinction.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_08_seed_replication(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), facecolor=DARK_BG)
        for ax in (ax1, ax2):
            ax.set_facecolor(PANEL_BG)
            ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
            self.draw_arena_obstacles(ax, ep=2)
            
        # Left Panel: FULL_P1_R3 across seeds
        for seed, color in zip([42, 101, 2024], [CYAN, GREEN, PURPLE]):
            k = f"P1R3_FULL_P1_R3_S{seed}_EP2"
            df = self.runs.get(k)
            if df is not None:
                ax1.plot(df["x"], df["y"], color=color, lw=2.2, label=f"Seed {seed}")
        ax1.set_title("FULL_P1_R3 Episode 2 Across Seeds (Route A Switch)", color=TEXT_COLOR, fontweight="bold")
        ax1.set_xlim(-0.2, 2.5)
        ax1.set_ylim(-1.1, 1.1)
        ax1.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
        
        # Right Panel: NO_MEMORY across seeds
        for seed, color in zip([42, 101, 2024], [CORAL, GOLD, "#FF80AB"]):
            k = f"P1R3_NO_MEMORY_S{seed}_EP2"
            df = self.runs.get(k)
            if df is not None:
                ax2.plot(df["x"], df["y"], color=color, lw=2.2, label=f"Seed {seed}")
        ax2.set_title("NO_MEMORY Episode 2 Across Seeds (Route B Persistence)", color=TEXT_COLOR, fontweight="bold")
        ax2.set_xlim(-0.2, 2.5)
        ax2.set_ylim(-1.1, 1.1)
        ax2.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "08_seed_replication.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def plot_09_physical_clearance_validation(self):
        fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=DARK_BG)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linestyle=":", alpha=0.7)
        
        for k, df in self.runs.items():
            if "EP2" in k:
                t = df["tick"] * 0.0333
                col = CYAN if "FULL" in k else CORAL
                alpha = 0.8 if "S42" in k else 0.4
                ax.plot(t, df["minimum_true_robot_wall_distance"], color=col, alpha=alpha, lw=1.5)
                
        ax.axhline(0.0, color="#FF1744", linestyle="--", lw=1.8, label="Physical Solid Boundary (0.0 m)")
        ax.axhline(0.05, color=GOLD, linestyle=":", lw=1.2, label="5 cm Proximity Safety Limit")
        
        ax.set_title("True Geom-to-Geom Physical Clearance Over All Recurrence Episodes", color=TEXT_COLOR, fontweight="bold")
        ax.set_xlabel("Simulation Time (seconds)", color=TEXT_COLOR)
        ax.set_ylabel("True Signed Distance (meters)", color=TEXT_COLOR)
        ax.set_ylim(-0.02, 0.50)
        ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "09_physical_clearance_validation.png"), dpi=300, facecolor=DARK_BG)
        plt.close()

    def generate_all_plots(self):
        print("=" * 80)
        print("GENERATING ALL 9 CANONICAL PUBLICATION FIGURES")
        print("=" * 80)
        self.plot_01_decision_state_matching()
        print("Generated: 01_decision_state_matching.png")
        self.plot_02_full_vs_no_memory_route_choice()
        print("Generated: 02_FULL_vs_NO_MEMORY_route_choice.png")
        self.plot_03_memory_retrieval_vs_route_choice()
        print("Generated: 03_memory_retrieval_vs_route_choice.png")
        self.plot_04_prediction_error_episode_progression()
        print("Generated: 04_prediction_error_episode_progression.png")
        self.plot_05_pre_hazard_trajectory_divergence()
        print("Generated: 05_pre_hazard_trajectory_divergence.png")
        self.plot_06_efe_decomposition_at_recurrence()
        print("Generated: 06_EFE_decomposition_at_recurrence.png")
        self.plot_07_context_update_extinction()
        print("Generated: 07_context_update_extinction.png")
        self.plot_08_seed_replication()
        print("Generated: 08_seed_replication.png")
        self.plot_09_physical_clearance_validation()
        print("Generated: 09_physical_clearance_validation.png")
        print("=" * 80)


if __name__ == "__main__":
    plotter = P1R3CausalityPlotter()
    plotter.generate_all_plots()
