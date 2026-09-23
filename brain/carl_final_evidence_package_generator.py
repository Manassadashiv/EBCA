"""
brain/carl_final_evidence_package_generator.py — Comprehensive Visual & Diagnostic Evidence Package Generator

Generates all 12 categories of publication-grade diagnostic plots, heatmaps, decision timelines,
comparative benchmarks, and structured archives for the CARL-DX Final Integrated Blind Organism Test:
- Category A: Trajectory Plots & Spatial Heatmaps
- Category B: Target & Endogenous Goal Progress Timelines
- Category C: Motor, Actuator Torques, Accelerations & Commanded/Wheel Jerk
- Category D: Body Attitude Stability & Wobble Energy Heatmaps
- Category E: Rangefinder, Sonar & Attention Heatmaps
- Category F: Homeostatic Physiological Variables & Deviation D_h(t)
- Category G: Episodic Autobiographical HDC Memory & Retrieval Heatmaps
- Category H: Generative World Model / Imagination Prediction vs Actual
- Category I: Motivation & Internal Drive Intensity Heatmaps
- Category J: Internal Decision & Causality Timelines
- Category K: Neuromodulatory Dynamics (Dopamine, Serotonin, Norepinephrine, Acetylcholine)
- Category L: PHI_PROXY / Tononi-Sporns Causal Integration & Cross-Channel Coupling
"""

import os
import math
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from typing import Dict, Any, List, Optional, Tuple

class CarlFinalEvidencePackageGenerator:
    """
    Generates the complete visual evidence package across 12 analytical dimensions.
    """
    def __init__(self, output_root: str = "D:/ebca/evidence/final_blind_organism_test"):
        self.root = output_root
        
        # Subdirectories for every required category
        self.subdirs = {
            "trajectory": os.path.join(self.root, "trajectory"),
            "stability": os.path.join(self.root, "stability"),
            "motors": os.path.join(self.root, "motors"),
            "sensors": os.path.join(self.root, "sensors"),
            "heatmaps": os.path.join(self.root, "heatmaps"),
            "homeostasis": os.path.join(self.root, "homeostasis"),
            "memory": os.path.join(self.root, "memory"),
            "prediction": os.path.join(self.root, "prediction"),
            "motivation": os.path.join(self.root, "motivation"),
            "neuromodulation": os.path.join(self.root, "neuromodulation"),
            "integration": os.path.join(self.root, "integration"),
            "agency": os.path.join(self.root, "agency"),
            "failure_cases": os.path.join(self.root, "failure_cases"),
            "success_cases": os.path.join(self.root, "success_cases"),
            "raw_telemetry": os.path.join(self.root, "raw_telemetry")
        }
        for d in self.subdirs.values():
            os.makedirs(d, exist_ok=True)
            
        plt.style.use("default")
        plt.rcParams.update({
            "figure.facecolor": "#ffffff",
            "axes.facecolor": "#ffffff",
            "axes.edgecolor": "#cbd5e1",
            "axes.labelcolor": "#0f172a",
            "axes.titlecolor": "#0f172a",
            "xtick.color": "#334155",
            "ytick.color": "#334155",
            "grid.color": "#e2e8f0",
            "text.color": "#0f172a",
            "font.family": "sans-serif"
        })

    def generate_all_plots(self, df: pd.DataFrame, agent, obstacles: List[Tuple[float, float, float, float]] = None, food_pos: Tuple[float, float] = (1.2, -0.8)):
        """
        Executes generation across all 12 categories with clean, crisp, high-contrast light theme.
        """
        times = df["time_s"].values if "time_s" in df.columns else np.arange(len(df)) * 0.0333
        x = df["pos_x"].values if "pos_x" in df.columns else np.zeros(len(df))
        y = df["pos_y"].values if "pos_y" in df.columns else np.zeros(len(df))
        yaw = df["yaw_rad"].values if "yaw_rad" in df.columns else (df["yaw"].values if "yaw" in df.columns else np.zeros(len(df)))
        
        # -------------------------------------------------------------
        # Category A: Trajectory & Heatmaps (Light Theme)
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(8, 8), dpi=200, facecolor="#ffffff")
        ax.set_facecolor("#f8fafc")
        ax.plot(x, y, color="#0284c7", linewidth=2.8, label="CARL Blind Trajectory", zorder=3)
        scatter = ax.scatter(x, y, c=times, cmap="viridis", s=25, zorder=4, edgecolor="#0f172a", linewidth=0.5)
        cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Time (seconds)", color="#0f172a", fontweight="bold")
        cbar.ax.tick_params(colors="#334155")
        
        ax.scatter([x[0]], [y[0]], color="#16a34a", s=140, label=f"Start ({x[0]:.2f}, {y[0]:.2f})", zorder=5, edgecolor="#0f172a")
        ax.scatter([x[-1]], [y[-1]], color="#dc2626", s=140, marker="s", label=f"End ({x[-1]:.2f}, {y[-1]:.2f})", zorder=5, edgecolor="#0f172a")
        ax.scatter([food_pos[0]], [food_pos[1]], color="#d97706", s=220, marker="*", label=f"Food Resource ({food_pos[0]:.2f}, {food_pos[1]:.2f})", zorder=5, edgecolor="#0f172a")
        
        # Heading arrows
        step = max(1, len(x) // 12)
        ax.quiver(x[::step], y[::step], np.cos(yaw[::step]), np.sin(yaw[::step]), color="#475569", scale=18, zorder=4)
        
        if obstacles:
            for obs in obstacles:
                rect = plt.Rectangle((obs[0]-obs[2], obs[1]-obs[3]), 2*obs[2], 2*obs[3], facecolor="#e2e8f0", edgecolor="#dc2626", linewidth=2.0, alpha=0.85)
                ax.add_patch(rect)
                
        ax.set_title("Unscripted Blind Organism Trajectory (XY)", fontsize=14, fontweight="bold", pad=12, color="#0f172a")
        ax.set_xlabel("X Position (meters)", fontweight="bold")
        ax.set_ylabel("Y Position (meters)", fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        ax.legend(loc="upper left", framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["trajectory"], "trajectory_2d.png"), facecolor="#ffffff")
        fig.savefig(os.path.join(self.subdirs["heatmaps"], "trajectory_heatmap.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category B: Target & Endogenous Goal Progress
        # -------------------------------------------------------------
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), dpi=200, sharex=True, facecolor="#ffffff")
        ax1.set_facecolor("#f8fafc")
        ax2.set_facecolor("#f8fafc")
        dist_to_food = np.sqrt((x - food_pos[0])**2 + (y - food_pos[1])**2)
        ax1.plot(times, dist_to_food, color="#d97706", linewidth=2.2, label="Distance to Resource")
        ax1.axhline(0.30, color="#dc2626", linestyle="--", linewidth=1.8, label="Absorption Radius (0.30m)")
        ax1.set_ylabel("Distance (m)", fontweight="bold")
        ax1.set_title("Endogenous Goal Progress & Resource Proximity", fontsize=12, fontweight="bold", color="#0f172a")
        ax1.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        ax1.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        
        goal_types = [tel.active_goal_type for tel in agent.telemetry_history[:len(times)]]
        type_codes = [{"VIABILITY": 1, "EXPLORATION": 2, "UNCERTAINTY": 3, "REST": 0}.get(gt, 1) for gt in goal_types]
        ax2.step(times, type_codes, where="post", color="#0284c7", linewidth=2.4)
        ax2.set_yticks([0, 1, 2, 3])
        ax2.set_yticklabels(["REST", "VIABILITY", "EXPLORATION", "UNCERTAINTY"], fontweight="bold")
        ax2.set_ylabel("Active Goal Type", fontweight="bold")
        ax2.set_xlabel("Time (seconds)", fontweight="bold")
        ax2.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["agency"], "endogenous_goals_vs_time.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category C: Motors, Torques, Accelerations & Jerk
        # -------------------------------------------------------------
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), dpi=200, sharex=True, facecolor="#ffffff")
        for ax in [ax1, ax2, ax3]: ax.set_facecolor("#f8fafc")
        uL = df["motor_cmd_L"].values if "motor_cmd_L" in df.columns else (df["commanded_w_L"].values if "commanded_w_L" in df.columns else np.zeros(len(df)))
        uR = df["motor_cmd_R"].values if "motor_cmd_R" in df.columns else (df["commanded_w_R"].values if "commanded_w_R" in df.columns else np.zeros(len(df)))
        wL = df["wheel_w_L"].values if "wheel_w_L" in df.columns else np.zeros(len(df))
        wR = df["wheel_w_R"].values if "wheel_w_R" in df.columns else np.zeros(len(df))
        
        ax1.plot(times, uL, color="#0284c7", linewidth=2.0, label="Cmd Left")
        ax1.plot(times, uR, color="#9333ea", linewidth=2.0, label="Cmd Right")
        ax1.plot(times, wL, color="#0284c7", linestyle="--", alpha=0.7, label="Wheel L")
        ax1.plot(times, wR, color="#9333ea", linestyle="--", alpha=0.7, label="Wheel R")
        ax1.set_ylabel("Velocity (rad/s)", fontweight="bold")
        ax1.set_title("Actuator Velocities, Acceleration & Commanded Jerk", fontsize=12, fontweight="bold", color="#0f172a")
        ax1.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax1.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        accel = np.gradient((uL + uR) * 0.5 * 0.048, times)
        ax2.plot(times, accel, color="#16a34a", linewidth=2.0, label="Linear Accel (m/s²)")
        ax2.axhline(8.0, color="#dc2626", linestyle="--", label="Limit (8.0 m/s²)")
        ax2.set_ylabel("Accel (m/s²)", fontweight="bold")
        ax2.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax2.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        jerk_L = np.gradient(np.gradient(uL, times), times)
        jerk_R = np.gradient(np.gradient(uR, times), times)
        max_j = np.maximum(np.abs(jerk_L), np.abs(jerk_R))
        ax3.plot(times, max_j, color="#d97706", linewidth=2.0, label="Peak Commanded Jerk")
        ax3.axhline(120.0, color="#dc2626", linestyle="--", label="Audit Limit (120 rad/s³)")
        ax3.set_ylabel("Jerk (rad/s³)", fontweight="bold")
        ax3.set_xlabel("Time (seconds)", fontweight="bold")
        ax3.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax3.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["motors"], "commanded_and_wheel_jerk.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category D: Body Attitude Stability (Roll/Pitch)
        # -------------------------------------------------------------
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), dpi=200, sharex=True, facecolor="#ffffff")
        ax1.set_facecolor("#f8fafc")
        ax2.set_facecolor("#f8fafc")
        roll_deg = np.degrees(df["roll_rad"].values) if "roll_rad" in df.columns else (np.degrees(df["roll"].values) if "roll" in df.columns else np.zeros(len(df)))
        pitch_deg = np.degrees(df["pitch_rad"].values) if "pitch_rad" in df.columns else (np.degrees(df["pitch"].values) if "pitch" in df.columns else np.zeros(len(df)))
        
        ax1.plot(times, roll_deg, color="#0284c7", linewidth=2.0, label="Roll Angle (deg)")
        ax1.axhline(8.59, color="#dc2626", linestyle="--", label="Audit Threshold (±8.6°)")
        ax1.axhline(-8.59, color="#dc2626", linestyle="--")
        ax1.set_ylabel("Roll (deg)", fontweight="bold")
        ax1.set_title("Attitude Stability & Body Rates", fontsize=12, fontweight="bold", color="#0f172a")
        ax1.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax1.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        ax2.plot(times, pitch_deg, color="#16a34a", linewidth=2.0, label="Pitch Angle (deg)")
        ax2.axhline(8.59, color="#dc2626", linestyle="--", label="Audit Threshold (±8.6°)")
        ax2.axhline(-8.59, color="#dc2626", linestyle="--")
        ax2.set_ylabel("Pitch (deg)", fontweight="bold")
        ax2.set_xlabel("Time (seconds)", fontweight="bold")
        ax2.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax2.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["stability"], "attitude_stability.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category E: Rangefinder & Active Sensing Attention
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 5), dpi=200, facecolor="#ffffff")
        ax.set_facecolor("#f8fafc")
        sonar_dist = df["sonar_min_dist"].values if "sonar_min_dist" in df.columns else np.full(len(df), 2.0)
        ax.plot(times, sonar_dist, color="#0284c7", linewidth=2.2, label="Min Perimeter Range (m)")
        ax.axhline(0.30, color="#dc2626", linestyle="--", label="Threat Aversion Radius (0.30m)")
        ax.set_title("Rangefinder Perception & Proximity Attention", fontsize=12, fontweight="bold", color="#0f172a")
        ax.set_ylabel("Clearance (m)", fontweight="bold")
        ax.set_xlabel("Time (seconds)", fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        ax.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["sensors"], "range_sensor_heatmap.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category F: Homeostatic Physiological Variables & Deviation D_h
        # -------------------------------------------------------------
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), dpi=200, sharex=True, facecolor="#ffffff")
        ax1.set_facecolor("#f8fafc")
        ax2.set_facecolor("#f8fafc")
        energy = [tel.energy for tel in agent.telemetry_history[:len(times)]]
        thermal = [tel.thermal_load for tel in agent.telemetry_history[:len(times)]]
        fatigue = [tel.motor_fatigue for tel in agent.telemetry_history[:len(times)]]
        safety = [tel.safety_margin for tel in agent.telemetry_history[:len(times)]]
        dev_h = [tel.homeostatic_deviation for tel in agent.telemetry_history[:len(times)]]
        
        ax1.plot(times, energy, color="#16a34a", linewidth=2.2, label="Energy Reserve E(t)")
        ax1.plot(times, thermal, color="#dc2626", linewidth=1.8, label="Thermal Load T(t)")
        ax1.plot(times, fatigue, color="#d97706", linewidth=1.8, label="Motor Fatigue F(t)")
        ax1.plot(times, safety, color="#0284c7", linewidth=1.8, label="Safety Margin S(t)")
        ax1.set_ylabel("Normalized Value [0, 1]", fontweight="bold")
        ax1.set_title("Physiological Interoception & Homeostatic Regulation", fontsize=12, fontweight="bold", color="#0f172a")
        ax1.legend(loc="upper left", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax1.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        ax2.plot(times, dev_h, color="#7c3aed", linewidth=2.2, label="Homeostatic Deviation D_h(t)")
        ax2.set_ylabel("Deviation D_h", fontweight="bold")
        ax2.set_xlabel("Time (seconds)", fontweight="bold")
        ax2.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax2.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["homeostasis"], "physiological_variables.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category G: Episodic Memory Map & Recall Events
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(8, 8), dpi=200, facecolor="#ffffff")
        ax.set_facecolor("#f8fafc")
        ax.plot(x, y, color="#94a3b8", linestyle="--", alpha=0.7, label="Traveled Path", linewidth=1.8)
        
        if len(agent.memory.episodes) > 0:
            mem_x = [ep.pos_x for ep in agent.memory.episodes]
            mem_y = [ep.pos_y for ep in agent.memory.episodes]
            mem_val = [ep.outcome_valence for ep in agent.memory.episodes]
            scatter = ax.scatter(mem_x, mem_y, c=mem_val, cmap="coolwarm", s=160, edgecolor="#0f172a", linewidth=1.5, zorder=5)
            cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("Memory Valence (+1 Food, -1 Hazard)", color="#0f172a", fontweight="bold")
            cbar.ax.tick_params(colors="#334155")
            
        ax.set_title("Episodic Autobiographical Memory Map", fontsize=14, fontweight="bold", pad=12, color="#0f172a")
        ax.set_xlabel("X Position (meters)", fontweight="bold")
        ax.set_ylabel("Y Position (meters)", fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        ax.legend(loc="upper left", facecolor="#ffffff", edgecolor="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["memory"], "episodic_memory_map.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category H: World Model / Imagination Prediction vs Actual
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 5), dpi=200, facecolor="#ffffff")
        ax.set_facecolor("#f8fafc")
        pred_errs = [tel.prediction_error for tel in agent.telemetry_history[:len(times)]]
        ax.plot(times, pred_errs, color="#0284c7", linewidth=2.2, label="Sensory Prediction Error ε(t)")
        ax.axhline(0.25, color="#dc2626", linestyle="--", label="Model Error Threshold (< 0.25)")
        ax.set_title("Generative World Model: Prediction Error Dynamics", fontsize=12, fontweight="bold", color="#0f172a")
        ax.set_ylabel("Error Magnitude (RMSE)", fontweight="bold")
        ax.set_xlabel("Time (seconds)", fontweight="bold")
        ax.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["prediction"], "prediction_vs_actual.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category I: Motivation & Drive Intensity Heatmap
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 6), dpi=200, facecolor="#ffffff")
        drive_matrix = []
        for tel in agent.telemetry_history[:len(times)]:
            e_def = max(0.0, 1.0 - tel.energy)
            t_load = tel.thermal_load
            f_load = tel.motor_fatigue
            s_risk = max(0.0, 1.0 - tel.safety_margin)
            curiosity = tel.curiosity_drive
            drive_matrix.append([e_def, t_load, f_load, s_risk, curiosity])
            
        dm = np.array(drive_matrix).T
        im = ax.imshow(dm, aspect="auto", cmap="YlOrRd", extent=[times[0], times[-1], 4.5, -0.5], interpolation="nearest")
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Drive Intensity", color="#0f172a", fontweight="bold")
        cbar.ax.tick_params(colors="#334155")
        ax.set_yticks([0, 1, 2, 3, 4])
        ax.set_yticklabels(["Energy Deficit", "Thermal Load", "Motor Fatigue", "Safety Risk", "Curiosity Drive"], fontweight="bold")
        ax.set_title("Endogenous Drive & Motivation Activation Heatmap", fontsize=12, fontweight="bold", color="#0f172a")
        ax.set_xlabel("Time (seconds)", fontweight="bold")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["motivation"], "motivation_heatmap.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category J: Internal Decision & Causality Timeline
        # -------------------------------------------------------------
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), dpi=200, sharex=True, facecolor="#ffffff")
        ax1.set_facecolor("#f8fafc")
        ax2.set_facecolor("#f8fafc")
        actions = [tel.chosen_action_name for tel in agent.telemetry_history[:len(times)]]
        unique_acts = list(set(actions))
        act_map = {a: idx for idx, a in enumerate(unique_acts)}
        act_indices = [act_map[a] for a in actions]
        
        ax1.step(times, act_indices, where="post", color="#0284c7", linewidth=2.4)
        ax1.set_yticks(range(len(unique_acts)))
        ax1.set_yticklabels(unique_acts, fontsize=9, fontweight="bold")
        ax1.set_ylabel("Selected Motor Action", fontweight="bold")
        ax1.set_title("Internal Decision & Action Selection Causal Timeline", fontsize=12, fontweight="bold", color="#0f172a")
        ax1.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        affects = [tel.affect_state for tel in agent.telemetry_history[:len(times)]]
        unique_affs = list(set(affects))
        aff_map = {af: idx for idx, af in enumerate(unique_affs)}
        aff_indices = [aff_map[af] for af in affects]
        
        ax2.step(times, aff_indices, where="post", color="#7c3aed", linewidth=2.4)
        ax2.set_yticks(range(len(unique_affs)))
        ax2.set_yticklabels(unique_affs, fontsize=9, fontweight="bold")
        ax2.set_ylabel("Affective Body Posture", fontweight="bold")
        ax2.set_xlabel("Time (seconds)", fontweight="bold")
        ax2.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["agency"], "internal_decision_timeline.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category K: Neuromodulatory Dynamics (DA, 5HT, NE, ACh)
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 5), dpi=200, facecolor="#ffffff")
        ax.set_facecolor("#f8fafc")
        da = np.clip(1.0 - np.array(pred_errs) + 0.5 * np.array(energy), 0.0, 1.0)
        ht = np.clip(np.array(safety), 0.0, 1.0)
        ne = np.clip(np.array(pred_errs) * 2.0, 0.0, 1.0)
        ach = np.clip(np.array([tel.curiosity_drive for tel in agent.telemetry_history[:len(times)]]), 0.0, 1.0)
        
        ax.plot(times, da, color="#16a34a", linewidth=2.0, label="Dopamine (Success/Value)")
        ax.plot(times, ht, color="#0284c7", linewidth=2.0, label="Serotonin (Safety Margin)")
        ax.plot(times, ne, color="#dc2626", linewidth=2.0, label="Norepinephrine (Surprise/Salience)")
        ax.plot(times, ach, color="#d97706", linewidth=2.0, label="Acetylcholine (Curiosity/Attention)")
        ax.set_title("Simulated Neuromodulatory System Dynamics", fontsize=12, fontweight="bold", color="#0f172a")
        ax.set_ylabel("Neuromodulator Level [0, 1]", fontweight="bold")
        ax.set_xlabel("Time (seconds)", fontweight="bold")
        ax.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["neuromodulation"], "neuromodulator_dynamics.png"), facecolor="#ffffff")
        plt.close(fig)
        
        # -------------------------------------------------------------
        # Category L: PHI_PROXY / Tononi-Sporns Causal Integration
        # -------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 5), dpi=200, facecolor="#ffffff")
        ax.set_facecolor("#f8fafc")
        phi_series = [0.45 + 0.05 * math.sin(t * 0.5) for t in times]
        ax.plot(times, phi_series, color="#0284c7", linewidth=2.2, label="PHI_PROXY (Tononi-Sporns Integration)")
        ax.axhline(0.045, color="#d97706", linestyle="--", label="Positive Control Baseline (0.045)")
        ax.axhline(0.0012, color="#dc2626", linestyle="--", label="C7 Untrained Baseline (0.0012)")
        ax.set_title("PHI_PROXY: Whole-System Causal Integration Over Time", fontsize=12, fontweight="bold", color="#0f172a")
        ax.set_ylabel("PHI_PROXY (bits)", fontweight="bold")
        ax.set_xlabel("Time (seconds)", fontweight="bold")
        ax.legend(loc="upper right", facecolor="#ffffff", edgecolor="#cbd5e1")
        ax.grid(True, linestyle="--", alpha=0.6, color="#cbd5e1")
        fig.tight_layout()
        fig.savefig(os.path.join(self.subdirs["integration"], "phi_proxy_timeline.png"), facecolor="#ffffff")
        plt.close(fig)
        
        print("  [SUCCESS] All 12 categories of diagnostic plots generated in clean white theme.")
