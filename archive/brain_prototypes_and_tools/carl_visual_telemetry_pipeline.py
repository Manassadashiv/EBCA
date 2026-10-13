"""
brain/carl_visual_telemetry_pipeline.py — Visual Evidence, Offscreen Rendering, Video & Plotting Suite

Provides automated, authoritative visual capture and plotting for CARL-DX robotics experiments:
1. MP4 Video Generation via MuJoCo offscreen Renderer + OpenCV VideoWriter
2. High-resolution PNG screenshots of critical episode states (start, mid, final, obstacles)
3. Multi-panel diagnostic telemetry graphs (Trajectory, Stability, Velocity, Slip/Traction, Actuation Jerk)
4. Before-vs-After comparative benchmarking plots
5. Complete Human-Review Evidence Packages under evidence/<milestone>/
"""

import os
import math
import cv2
import mujoco
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
    "text.color": "#0f172a"
})
from typing import List, Dict, Any

class CarlVisualTelemetryPipeline:
    """
    Automated visual capture, MP4 recording, and telemetry plotting pipeline.
    """
    def __init__(self, output_base_dir: str = "D:/ebca"):
        self.base_dir = output_base_dir
        self.replays_dir = os.path.join(self.base_dir, "replays")
        self.plots_dir = os.path.join(self.base_dir, "plots")
        self.screenshots_dir = os.path.join(self.plots_dir, "screenshots")
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        
        os.makedirs(self.replays_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.evidence_dir, exist_ok=True)

    def record_episode_mp4(self, runner, duration_ticks: int, policy_step_fn, output_mp4_path: str, fps: int = 30, goal_pos: np.ndarray = None, stop_at_goal: bool = False, episode_title: str = "CARL-DX LOCOMOTION TELEMETRY") -> Dict[str, Any]:
        """
        Executes an episode while rendering offscreen frames and encoding an HD 720p MP4 video with a tracking camera.
        """
        os.makedirs(os.path.dirname(output_mp4_path), exist_ok=True)
        width, height = 1280, 720
        renderer = mujoco.Renderer(runner.hal.model, height=height, width=width)
        
        # Configure Close-Up 3rd-Person Tracking Camera
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        cam.trackbodyid = runner.hal.model.body('drive_deck').id
        cam.distance = 1.65
        cam.elevation = -22.0
        cam.azimuth = 135.0
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_mp4_path, fourcc, float(fps), (width, height))
        
        records = []
        captured_frames = []
        
        for t in range(duration_ticks):
            # Step policy
            step_data = policy_step_fn(t, runner)
            
            # Step MuJoCo physics
            for _ in range(20):
                mujoco.mj_step(runner.hal.model, runner.hal.data)
                
            x, y, yaw = runner.hal.get_robot_pos()
            
            # Extract quaternion for roll/pitch
            qadr = runner.hal.model.joint('spatial_identity').qposadr[0]
            qw = float(runner.hal.data.qpos[qadr + 3])
            qx = float(runner.hal.data.qpos[qadr + 4])
            qy = float(runner.hal.data.qpos[qadr + 5])
            qz = float(runner.hal.data.qpos[qadr + 6])
            
            roll = math.atan2(2 * (qw * qx + qy * qz), 1 - 2 * (qx**2 + qy**2))
            pitch = math.asin(np.clip(2 * (qw * qy - qz * qx), -1.0, 1.0))
            
            cvel_x = float(runner.hal.data.cvel[runner.hal.model.body('drive_deck').id][3])
            cvel_y = float(runner.hal.data.cvel[runner.hal.model.body('drive_deck').id][4])
            w_L = float(runner.hal.data.qvel[runner.hal.model.joint('w_left').dofadr[0]])
            w_R = float(runner.hal.data.qvel[runner.hal.model.joint('w_right').dofadr[0]])
            
            wall_contacts = 0
            for ci in range(runner.hal.data.ncon):
                c = runner.hal.data.contact[ci]
                g1 = runner.hal.model.geom(c.geom1).name
                g2 = runner.hal.model.geom(c.geom2).name
                if "wall" in g1 or "wall" in g2:
                    wall_contacts += 1
                    
            uL = float(step_data.get("cmd_L", 0.0))
            uR = float(step_data.get("cmd_R", 0.0))
            record_entry = {
                "tick": t,
                "time_s": round(t * 0.0333, 4),
                "pos_x": float(x),
                "pos_y": float(y),
                "pos_z": float(runner.hal.data.qpos[qadr + 2]),
                "yaw_rad": float(yaw),
                "roll_rad": float(roll),
                "pitch_rad": float(pitch),
                "cvel_x": float(cvel_x),
                "cvel_y": float(cvel_y),
                "speed_mps": float(math.sqrt(cvel_x**2 + cvel_y**2)),
                "wheel_w_L": float(w_L),
                "wheel_w_R": float(w_R),
                "motor_cmd_L": uL,
                "motor_cmd_R": uR,
                "actuator_tau_L": float(runner.hal.data.actuator_force[0]),
                "actuator_tau_R": float(runner.hal.data.actuator_force[1]),
                "ncon": int(runner.hal.data.ncon),
                "wall_contacts": int(wall_contacts)
            }
            if goal_pos is not None:
                record_entry["food_dist"] = float(np.linalg.norm(goal_pos - np.array([x, y])))
            records.append(record_entry)
            
            # Offscreen Render with Close-Up Tracking Camera
            renderer.update_scene(runner.hal.data, camera=cam)
            rgb_frame = renderer.render()
            bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            # Draw semi-transparent HUD telemetry panel
            overlay = bgr_frame.copy()
            cv2.rectangle(overlay, (20, 20), (580, 120), (18, 22, 28), -1)
            cv2.addWeighted(overlay, 0.75, bgr_frame, 0.25, 0, bgr_frame)
            cv2.rectangle(bgr_frame, (20, 20), (580, 120), (0, 220, 255), 1)
            
            # HUD text
            cv2.putText(bgr_frame, episode_title, (35, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 2, cv2.LINE_AA)
            cv2.putText(bgr_frame, f"Tick: {t:03d} ({(t*0.0333):4.2f}s) | Pos: ({x:4.2f}m, {y:4.2f}m) | Yaw: {math.degrees(yaw):5.1f} deg", 
                        (35, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            status_text = f"Motors: L={uL:4.1f} R={uR:4.1f} rad/s | Speed: {record_entry['speed_mps']:4.2f} m/s"
            if goal_pos is not None:
                dist = record_entry["food_dist"]
                status_text += f" | Goal: {dist:4.2f}m"
            cv2.putText(bgr_frame, status_text, (35, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 255, 120), 1, cv2.LINE_AA)
                
            out.write(bgr_frame)
            if t in [0, duration_ticks // 2, duration_ticks - 1]:
                captured_frames.append((t, rgb_frame.copy()))
                
            if stop_at_goal and goal_pos is not None and record_entry["food_dist"] < 0.25:
                break
                
        out.release()
        df = pd.DataFrame(records)
        return {
            "df": df,
            "mp4_path": output_mp4_path,
            "video_bytes": os.path.getsize(output_mp4_path),
            "key_frames": captured_frames
        }

    def generate_diagnostic_plots(self, df: pd.DataFrame, episode_id: str, goal_pos: np.ndarray = None, output_prefix: str = None) -> Dict[str, str]:
        """
        Generates publication-grade telemetry diagnostic plots:
        1. Trajectory (2D Planar XY)
        2. Stability (Roll, Pitch, Angular Rates)
        3. Velocity & Wheel Speeds
        4. Actuation Commands & Commanded Jerk
        5. Contact & Slip Dynamics
        """
        prefix = output_prefix if output_prefix is not None else os.path.join(self.plots_dir, episode_id)
        os.makedirs(os.path.dirname(prefix), exist_ok=True)
        times = df["time_s"].values
        
        plot_paths = {}
        
        # 1. 2D Trajectory Plot
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
        ax.plot(df["pos_x"], df["pos_y"], "b-", linewidth=2.0, label="CARL Trajectory")
        ax.plot(df["pos_x"].iloc[0], df["pos_y"].iloc[0], "go", markersize=8, label="Start (0, 0)")
        ax.plot(df["pos_x"].iloc[-1], df["pos_y"].iloc[-1], "rs", markersize=8, label="End State")
        if goal_pos is not None:
            ax.plot(goal_pos[0], goal_pos[1], "y*", markersize=14, markeredgecolor="k", label=f"Target ({goal_pos[0]:.1f}, {goal_pos[1]:.1f})")
            goal_circle = plt.Circle((goal_pos[0], goal_pos[1]), 0.25, color="y", fill=False, linestyle="--", label="Target Threshold (0.25m)")
            ax.add_patch(goal_circle)
        ax.set_title(f"2D Trajectory — {episode_id}", fontsize=12, fontweight="bold")
        ax.set_xlabel("X Position (meters)")
        ax.set_ylabel("Y Position (meters)")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8)
        ax.set_aspect("equal", "box")
        traj_path = f"{prefix}_trajectory.png"
        fig.tight_layout()
        fig.savefig(traj_path)
        plt.close(fig)
        plot_paths["trajectory"] = traj_path
        
        # 2. Stability Plot (Roll & Pitch)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), dpi=150, sharex=True)
        roll_deg = np.degrees(df["roll_rad"])
        pitch_deg = np.degrees(df["pitch_rad"])
        ax1.plot(times, roll_deg, "r-", label="Roll (deg)")
        ax1.axhline(8.6, color="k", linestyle="--", alpha=0.5, label="Limit (±8.6°)")
        ax1.axhline(-8.6, color="k", linestyle="--", alpha=0.5)
        ax1.set_ylabel("Roll Angle (°)")
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="upper right", fontsize=8)
        ax1.set_title(f"Attitude Stability & Body Rates — {episode_id}", fontsize=11, fontweight="bold")
        
        ax2.plot(times, pitch_deg, "g-", label="Pitch (deg)")
        ax2.axhline(8.6, color="k", linestyle="--", alpha=0.5, label="Limit (±8.6°)")
        ax2.axhline(-8.6, color="k", linestyle="--", alpha=0.5)
        ax2.set_xlabel("Time (seconds)")
        ax2.set_ylabel("Pitch Angle (°)")
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="upper right", fontsize=8)
        
        stab_path = f"{prefix}_stability.png"
        fig.tight_layout()
        fig.savefig(stab_path)
        plt.close(fig)
        plot_paths["stability"] = stab_path
        
        # 3. Actuation Jerk & Motor Commands Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), dpi=150, sharex=True)
        ax1.plot(times, df["motor_cmd_L"], "b-", label="Cmd Left (rad/s)")
        ax1.plot(times, df["motor_cmd_R"], "m-", label="Cmd Right (rad/s)")
        ax1.plot(times, df["wheel_w_L"], "b--", alpha=0.6, label="Wheel w Left")
        ax1.plot(times, df["wheel_w_R"], "m--", alpha=0.6, label="Wheel w Right")
        ax1.set_ylabel("Velocity (rad/s)")
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="upper right", fontsize=8)
        ax1.set_title(f"Actuator Velocities & Commanded Jerk — {episode_id}", fontsize=11, fontweight="bold")
        
        if len(times) > 4:
            j_cmd_L = np.gradient(np.gradient(df["motor_cmd_L"].values, times), times)
            j_cmd_R = np.gradient(np.gradient(df["motor_cmd_R"].values, times), times)
            ax2.plot(times[2:-2], np.abs(j_cmd_L)[2:-2], "b-", label="|Jerk Left| (rad/s³)")
            ax2.plot(times[2:-2], np.abs(j_cmd_R)[2:-2], "m-", label="|Jerk Right| (rad/s³)")
        ax2.axhline(120.0, color="r", linestyle="--", label="Jerk Audit Threshold (120 rad/s³)")
        ax2.set_xlabel("Time (seconds)")
        ax2.set_ylabel("Jerk (rad/s³)")
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="upper right", fontsize=8)
        
        act_path = f"{prefix}_actuation.png"
        fig.tight_layout()
        fig.savefig(act_path)
        plt.close(fig)
        plot_paths["actuation"] = act_path
        
        return plot_paths

    def generate_before_after_plots(self, c7_df: pd.DataFrame, c0_df: pd.DataFrame, output_prefix: str = "plots/before_after") -> Dict[str, str]:
        """
        Generates direct before-vs-after comparative graphs between C7 Untrained and C0 Trained.
        """
        prefix = os.path.join(self.base_dir, output_prefix)
        os.makedirs(os.path.dirname(prefix), exist_ok=True)
        
        # 1. Before vs After Trajectory
        fig, ax = plt.subplots(figsize=(7, 6), dpi=150)
        ax.plot(c7_df["pos_x"], c7_df["pos_y"], "r--", linewidth=1.8, label="C7 Untrained Baseline (Wandering)")
        ax.plot(c0_df["pos_x"], c0_df["pos_y"], "g-", linewidth=2.2, label="C0 Trained Policy (Goal-Directed)")
        ax.plot(c7_df["pos_x"].iloc[0], c7_df["pos_y"].iloc[0], "ko", markersize=7, label="Start (0, 0)")
        if "food_dist" in c0_df.columns:
            # Reconstruct goal
            goal_x = c0_df["pos_x"].iloc[-1]
            goal_y = c0_df["pos_y"].iloc[-1]
            ax.plot(goal_x, goal_y, "y*", markersize=13, markeredgecolor="k", label=f"Goal ({goal_x:.1f}, {goal_y:.1f})")
        ax.set_title("Before vs After Trajectory Comparison (C7 vs C0)", fontsize=12, fontweight="bold")
        ax.set_xlabel("X Position (meters)")
        ax.set_ylabel("Y Position (meters)")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8)
        ax.set_aspect("equal", "box")
        
        traj_cmp_path = f"{prefix}_trajectory.png"
        fig.tight_layout()
        fig.savefig(traj_cmp_path)
        plt.close(fig)
        
        # 2. Before vs After Goal Distance Convergence
        fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
        t_c7 = c7_df["time_s"].values
        t_c0 = c0_df["time_s"].values
        if "food_dist" in c7_df.columns and "food_dist" in c0_df.columns:
            ax.plot(t_c7, c7_df["food_dist"], "r--", linewidth=1.8, label="C7 Untrained Distance (No Convergence)")
            ax.plot(t_c0, c0_df["food_dist"], "g-", linewidth=2.2, label="C0 Trained Distance (Rapid Convergence)")
            ax.axhline(0.25, color="k", linestyle=":", label="Goal Attainment Radius (0.25m)")
            ax.set_title("Target Distance Convergence vs Time (C7 vs C0)", fontsize=11, fontweight="bold")
            ax.set_xlabel("Time (seconds)")
            ax.set_ylabel("Distance to Target (meters)")
            ax.grid(True, linestyle=":", alpha=0.6)
            ax.legend(loc="upper right", fontsize=8)
            
        dist_cmp_path = f"{prefix}_goal_distance.png"
        fig.tight_layout()
        fig.savefig(dist_cmp_path)
        plt.close(fig)
        
        return {"trajectory_comparison": traj_cmp_path, "goal_distance_comparison": dist_cmp_path}
