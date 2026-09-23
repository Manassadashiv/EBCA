"""
tools/p1/p1_visual_pipeline.py — Phase 1 Visual Telemetry, Plotting & Video Rendering Pipeline

1. HD 720p 30 FPS MuJoCo Video Renderer with Semi-Transparent Professional HUD Overlay.
2. 10 Canonical Scientific Verification Plots.
"""

import os
import sys
import json
import math
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

PLOTS_DIR = os.path.join(REPO_ROOT, "evidence", "p1", "plots")
VIDEOS_DIR = os.path.join(REPO_ROOT, "evidence", "p1", "videos")
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)


def draw_hud_overlay(frame_bgr: np.ndarray, telem: Any, run_title: str) -> np.ndarray:
    """
    Draws a semi-transparent dark slate HUD panel with live telemetry metrics.
    """
    overlay = frame_bgr.copy()
    cv2.rectangle(overlay, (20, 20), (740, 160), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.78, frame_bgr, 0.22, 0, frame_bgr)
    cv2.rectangle(frame_bgr, (20, 20), (740, 160), (2, 132, 199), 2)
    
    rec_col = (0, 220, 0) if not getattr(telem, "recovery_active", False) else (0, 100, 255)
    mem_col = (255, 200, 0) if getattr(telem, "memory_retrieval_event", False) else (200, 200, 200)
    
    cv2.putText(frame_bgr, f"CARL-DX P1 DEVELOPMENTAL LAB | {run_title}", (35, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    cv2.putText(frame_bgr, f"Tick: {telem.tick:4d} ({telem.time_s:5.2f}s) | Goal: {telem.active_goal} ({telem.goal_type})", (35, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    cv2.putText(frame_bgr, f"Action: {telem.action} | Spd: {telem.speed:.2f} m/s | EFE: {telem.efe_chosen:.1f}", (35, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    cv2.putText(frame_bgr, f"Clearance: {telem.obstacle_clearance:.2f}m | Energy: {telem.energy:.2f} | PredErr: {telem.prediction_error:.3f}", (35, 122), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
    cv2.putText(frame_bgr, f"Memory: {telem.episodes_in_memory} eps (Val: {telem.memory_valence:.2f}) | Stuck: {telem.recovery_state} | Rec: {telem.recovery_active} (T{telem.recovery_tier})", (35, 146), cv2.FONT_HERSHEY_SIMPLEX, 0.46, mem_col, 1)
    return frame_bgr


def generate_all_10_canonical_plots(
    all_runs_data: Dict[str, Any],
    full_p1_sample_telemetry: List[Any],
    output_dir: str = PLOTS_DIR
):
    """
    Generates all 10 project-mandated scientific verification plots.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 01_episode_trajectory.png
    plt.figure(figsize=(10, 8), dpi=150)
    plt.title("01. Trajectory Progression Across Developmental Episodes (P1 Full)", fontsize=14, fontweight='bold')
    colors = plt.cm.viridis(np.linspace(0, 1, 15))
    
    # Extract trajectories for episodes 1 to 15 from P1 full runs
    p1_episodes = all_runs_data.get("FULL_P1", {}).get("episodes_by_seed", {}).get("42", [])
    for ep_idx, ep in enumerate(p1_episodes):
        traj = ep.get("trajectory", [])
        if traj:
            xs = [p[0] for p in traj]
            ys = [p[1] for p in traj]
            label = f"Ep {ep_idx+1}" if ep_idx in [0, 4, 9, 14] else None
            plt.plot(xs, ys, color=colors[ep_idx], alpha=0.8, linewidth=2.0 if ep_idx in [0, 5, 10] else 1.2, label=label)
            
    # Draw resource beacon and obstacles
    plt.scatter([3.2], [0.0], color='lime', s=200, marker='*', zorder=10, label='Food Resource (3.2, 0.0)')
    plt.axvline(x=1.8, ymin=0.45, ymax=0.55, color='red', linestyle='--', linewidth=2.5, label='Perturbation Barrier (Ep 6-10)')
    plt.xlim(-0.5, 4.0)
    plt.ylim(-2.5, 2.5)
    plt.xlabel("X Position (m)", fontsize=12)
    plt.ylabel("Y Position (m)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "01_episode_trajectory.png"))
    plt.close()

    # 02_action_distribution.png
    plt.figure(figsize=(12, 6), dpi=150)
    plt.title("02. Action Primitive Selection Distribution Across Conditions", fontsize=14, fontweight='bold')
    actions = ["STRAIGHT_FORWARD", "CURVE_LEFT_SLIGHT", "CURVE_LEFT_MODERATE", "CURVE_LEFT_STRONG",
               "CURVE_RIGHT_SLIGHT", "CURVE_RIGHT_MODERATE", "CURVE_RIGHT_STRONG", "SLOW_CREEP_FORWARD", "BRAKE_REST"]
    
    cond_counts = {}
    for cond_name in ["FULL_P1", "P0_CONTROL", "NO_MEMORY", "NO_ADAPTATION"]:
        cond_data = all_runs_data.get(cond_name, {})
        counts = {a: 0 for a in actions}
        for ep in cond_data.get("all_episodes", []):
            for a_name, cnt in ep.get("action_counts", {}).items():
                if a_name in counts:
                    counts[a_name] += cnt
        tot = max(1, sum(counts.values()))
        cond_counts[cond_name] = [counts[a] / tot for a in actions]
        
    x = np.arange(len(actions))
    width = 0.2
    for i, (c_name, freqs) in enumerate(cond_counts.items()):
        plt.bar(x + (i - 1.5) * width, freqs, width, label=c_name)
    plt.xticks(x, [a.replace("CURVE_", "").replace("_FORWARD", "") for a in actions], rotation=30, ha='right')
    plt.ylabel("Selection Frequency", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "02_action_distribution.png"))
    plt.close()

    # 03_prediction_error_over_time.png
    plt.figure(figsize=(10, 5), dpi=150)
    plt.title("03. Forward Self-Model Kinematic Prediction Error Evolution", fontsize=14, fontweight='bold')
    if full_p1_sample_telemetry:
        ticks = [t.tick for t in full_p1_sample_telemetry]
        errs = [t.prediction_error for t in full_p1_sample_telemetry]
        plt.plot(ticks, errs, color='crimson', linewidth=1.5, label='Live Step Prediction Error $\\epsilon_t$')
        # Moving average
        if len(errs) > 10:
            ma = np.convolve(errs, np.ones(10)/10, mode='valid')
            plt.plot(ticks[:len(ma)], ma, color='navy', linewidth=2.5, label='10-Tick Smoothed MA')
    plt.xlabel("Cognitive Loop Tick", fontsize=12)
    plt.ylabel("Prediction Error $\\epsilon_t$", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "03_prediction_error_over_time.png"))
    plt.close()

    # 04_internal_state_over_time.png
    plt.figure(figsize=(10, 6), dpi=150)
    plt.title("04. Homeostatic Physiological State Vector Kinetics $h(t)$", fontsize=14, fontweight='bold')
    if full_p1_sample_telemetry:
        times = [t.time_s for t in full_p1_sample_telemetry]
        plt.plot(times, [t.energy for t in full_p1_sample_telemetry], label='Metabolic Energy $E(t)$', color='forestgreen', linewidth=2)
        plt.plot(times, [t.thermal_load for t in full_p1_sample_telemetry], label='Thermal Load $T(t)$', color='darkorange', linewidth=1.5)
        plt.plot(times, [t.motor_fatigue for t in full_p1_sample_telemetry], label='Motor Fatigue $F(t)$', color='purple', linewidth=1.5)
        plt.plot(times, [t.curiosity_drive for t in full_p1_sample_telemetry], label='Curiosity Drive $C(t)$', color='deepskyblue', linewidth=1.5)
    plt.xlabel("Elapsed Simulation Time (s)", fontsize=12)
    plt.ylabel("Normalized Physiological State [0.0, 1.0]", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "04_internal_state_over_time.png"))
    plt.close()

    # 05_memory_usage.png
    plt.figure(figsize=(10, 5), dpi=150)
    plt.title("05. Hyperdimensional Episodic Memory Accumulation & Query Valence", fontsize=14, fontweight='bold')
    if full_p1_sample_telemetry:
        times = [t.time_s for t in full_p1_sample_telemetry]
        plt.plot(times, [t.episodes_in_memory for t in full_p1_sample_telemetry], label='Episodes Stored in HDC Memory', color='navy', linewidth=2)
        plt.plot(times, [t.memory_valence * 50.0 for t in full_p1_sample_telemetry], label='Query Similarity Valence (Scaled x50)', color='darkorange', linestyle='--', linewidth=1.5)
    plt.xlabel("Simulation Time (s)", fontsize=12)
    plt.ylabel("Memory Metrics", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "05_memory_usage.png"))
    plt.close()

    # 06_target_distance.png
    plt.figure(figsize=(10, 5), dpi=150)
    plt.title("06. Euclidean Distance to Resource Beacon Over Time", fontsize=14, fontweight='bold')
    if full_p1_sample_telemetry:
        times = [t.time_s for t in full_p1_sample_telemetry]
        plt.plot(times, [t.target_distance for t in full_p1_sample_telemetry], color='dodgerblue', linewidth=2.0, label='Distance to Resource (m)')
        plt.axhline(y=0.30, color='lime', linestyle=':', linewidth=2.0, label='Acquisition Threshold (0.30m)')
    plt.xlabel("Simulation Time (s)", fontsize=12)
    plt.ylabel("Distance (m)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "06_target_distance.png"))
    plt.close()

    # 07_EFE_candidate_ranking.png
    plt.figure(figsize=(10, 6), dpi=150)
    plt.title("07. Candidate Action Expected Free Energy $G(a)$ Ranking Profile", fontsize=14, fontweight='bold')
    if full_p1_sample_telemetry and len(full_p1_sample_telemetry) > 20:
        sample_point = full_p1_sample_telemetry[20]
        c_scores = sample_point.candidate_action_scores
        sorted_acts = sorted(c_scores.items(), key=lambda kv: kv[1])
        act_names = [k.replace("CURVE_", "").replace("_FORWARD", "") for k, v in sorted_acts]
        scores = [v for k, v in sorted_acts]
        bars = plt.barh(act_names, scores, color='teal')
        bars[0].set_color('goldenrod') # Highlight chosen minimum
    plt.xlabel("Expected Free Energy $G(a)$ (Lower = Preferred)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "07_EFE_candidate_ranking.png"))
    plt.close()

    # 08_learning_or_adaptation_progress.png
    plt.figure(figsize=(10, 5), dpi=150)
    plt.title("08. Developmental Trajectory Efficiency & Time-to-Resource across Episodes", fontsize=14, fontweight='bold')
    ep_nums = list(range(1, 16))
    
    # Calculate average time to food across seeds for FULL P1 vs P0 Control
    for cond_name, col in [("FULL_P1", "blue"), ("P0_CONTROL", "gray"), ("NO_MEMORY", "red")]:
        cond_data = all_runs_data.get(cond_name, {})
        mean_times = []
        for ep_i in range(1, 16):
            times_ep = [ep["time_to_food_s"] for ep in cond_data.get("all_episodes", []) if ep["episode"] == ep_i and ep["target_acquired"]]
            mean_times.append(np.mean(times_ep) if times_ep else 15.0)
        plt.plot(ep_nums, mean_times, marker='o', linewidth=2.0, color=col, label=f"{cond_name} Mean Acquisition Time")
        
    plt.axvspan(5.5, 10.5, color='orange', alpha=0.15, label='Perturbation Phase (Ep 6-10)')
    plt.xlabel("Developmental Episode Number", fontsize=12)
    plt.ylabel("Time to Resource (s)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "08_learning_or_adaptation_progress.png"))
    plt.close()

    # 09_ablation_comparison.png
    plt.figure(figsize=(10, 6), dpi=150)
    plt.title("09. Causal Mechanism Ablation Comparison (Perturbed Phase 6–10)", fontsize=14, fontweight='bold')
    ablation_names = ["FULL_P1", "P0_CONTROL", "NO_MEMORY", "NO_ADAPTATION", "NO_NEED"]
    success_rates = []
    mean_tortuosities = []
    
    for c_name in ablation_names:
        c_data = all_runs_data.get(c_name, {})
        pert_eps = [ep for ep in c_data.get("all_episodes", []) if 6 <= ep["episode"] <= 10]
        succ = sum(1 for ep in pert_eps if ep.get("target_acquired", False)) / max(1, len(pert_eps))
        tort = np.mean([ep.get("tortuosity", 1.0) for ep in pert_eps]) if pert_eps else 1.0
        success_rates.append(succ * 100.0)
        mean_tortuosities.append(tort)
        
    x = np.arange(len(ablation_names))
    width = 0.35
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=150)
    ax2 = ax1.twinx()
    
    ax1.bar(x - width/2, success_rates, width, color='mediumseagreen', label='Resource Acquisition Rate (%)')
    ax2.bar(x + width/2, mean_tortuosities, width, color='royalblue', label='Mean Trajectory Tortuosity')
    
    ax1.set_ylabel("Acquisition Rate (%)", color='mediumseagreen', fontsize=12)
    ax2.set_ylabel("Trajectory Tortuosity", color='royalblue', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(ablation_names, rotation=20, ha='right')
    ax1.set_ylim(0, 110)
    plt.title("09. Causal Mechanism Ablation Comparison (Perturbed Phase 6–10)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "09_ablation_comparison.png"))
    plt.close()

    # 10_generalization_comparison.png
    plt.figure(figsize=(10, 6), dpi=150)
    plt.title("10. Cross-Environment Generalization Performance", fontsize=14, fontweight='bold')
    env_names = ["ENV_1_BIFURCATION", "ENV_2_ASYMMETRIC", "ENV_3_FRICTIONAL"]
    env_keys = ["FULL_P1", "GEN_ENV_2", "GEN_ENV_3"]
    
    env_succ = []
    env_time = []
    for k in env_keys:
        e_data = all_runs_data.get(k, {})
        eps = e_data.get("all_episodes", [])
        succ = sum(1 for ep in eps if ep.get("target_acquired", False)) / max(1, len(eps))
        times = [ep["time_to_food_s"] for ep in eps if ep.get("target_acquired", False)]
        env_succ.append(succ * 100.0)
        env_time.append(np.mean(times) if times else 15.0)
        
    x = np.arange(len(env_names))
    plt.bar(x - 0.18, env_succ, 0.35, label='Acquisition Success Rate (%)', color='teal')
    plt.bar(x + 0.18, env_time, 0.35, label='Mean Time to Food (s)', color='goldenrod')
    plt.xticks(x, env_names)
    plt.ylabel("Performance Metrics", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "10_generalization_comparison.png"))
    plt.close()
    
    print(f"[OK] Generated all 10 canonical scientific plots in {output_dir}")
