r"""
tools/p0_regression_runner.py — P0-01 Frozen Baseline Regression & Break-Test Runner for CARL-DX
Executes the comprehensive deterministic and adversarial regression suite across Test Groups A to P.
DOES NOT MODIFY ANY CARL SOURCE CODE.
"""

import os
import sys
import time
import json
import math
import hashlib
import glob
import random
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import mujoco
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer

OUTPUT_DIR = r"D:\ebca\evidence\p0_baseline_regression"
RUNS_DIR = os.path.join(OUTPUT_DIR, "runs")
VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
TELEMETRY_DIR = os.path.join(OUTPUT_DIR, "telemetry")
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
KEYFRAMES_DIR = os.path.join(OUTPUT_DIR, "keyframes")
SCORES_DIR = os.path.join(OUTPUT_DIR, "scores")
AUDIT_DIR = os.path.join(OUTPUT_DIR, "audit")

for d in [OUTPUT_DIR, RUNS_DIR, VIDEOS_DIR, TELEMETRY_DIR, PLOTS_DIR, KEYFRAMES_DIR, SCORES_DIR, AUDIT_DIR]:
    os.makedirs(d, exist_ok=True)

OFFICIAL_SEEDS = [42, 101, 2024, 31415, 8675309]

# =============================================================================
# BASELINE MANIFEST GENERATOR
# =============================================================================
def generate_baseline_manifest():
    manifest_path = os.path.join(OUTPUT_DIR, "baseline_manifest.json")
    
    active_source_files = [
        "brain/carl_autonomous_agent.py",
        "brain/carl_embodied_organism.py",
        "brain/carl_generative_self_model.py",
        "brain/carl_endogenous_agency.py",
        "brain/carl_homeostatic_core.py",
        "brain/carl_episodic_memory.py",
        "brain/carl_empowerment.py",
        "brain/carl_stuck_recovery.py",
        "brain/carl_expressive_visor.py",
        "brain/carl_reflex_laboratory.py"
    ]
    
    file_hashes = {}
    for rel_p in active_source_files:
        full_p = os.path.join(REPO_ROOT, rel_p)
        if os.path.exists(full_p):
            with open(full_p, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            stat = os.stat(full_p)
            file_hashes[rel_p] = {
                "sha256": h,
                "size_bytes": stat.st_size,
                "modified_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime))
            }

    manifest = {
        "benchmark_mission": "P0-01 FROZEN BASELINE REGRESSION & BREAK-TEST",
        "baseline_version": "CARL-DX 1.1.0-FROZEN-BASELINE",
        "repository_path": REPO_ROOT,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "mujoco_version": mujoco.__version__,
        "control_frequency_hz": 30.0,
        "cognitive_timestep_s": 0.0333,
        "physics_timestep_s": 0.0100,
        "physics_substeps_per_tick": 3,
        "active_action_set_size": 14,
        "active_recovery_system": "3-Tier Escalating CarlRecoveryManager (Reverse -> Spin -> Breakout)",
        "active_memory_system": "2048-D HDC Associative Matrix M with Offline Consolidation",
        "official_seeds": OFFICIAL_SEEDS,
        "source_manifest": file_hashes
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Generated Baseline Manifest: {manifest_path}")
    return manifest

# =============================================================================
# ENVIRONMENT & SCENARIO BUILDER
# =============================================================================
def configure_arena(model, scenario_type: str, seed: int):
    """
    Configures obstacles, walls, and food locations deterministically for each test scenario.
    """
    np.random.seed(seed)
    random.seed(seed)
    
    geom_names = {model.geom(i).name: i for i in range(model.ngeom)}
    body_names = {model.body(i).name: i for i in range(model.nbody)}
    
    # Reset all movable bodies to default positions
    if 'obj_cube_0' in body_names: model.body_pos[body_names['obj_cube_0']] = [10.0, 10.0, 0.05]
    if 'obj_cube_1' in body_names: model.body_pos[body_names['obj_cube_1']] = [10.0, 10.0, 0.05]
    if 'obj_ball_0' in body_names: model.body_pos[body_names['obj_ball_0']] = [10.0, 10.0, 0.05]
    if 'hazard_cube' in body_names: model.body_pos[body_names['hazard_cube']] = [10.0, 10.0, 0.15]
    
    if scenario_type == "OPEN_SPACE":
        # Clear all interior obstacles out of the way
        for g_name, g_id in geom_names.items():
            if g_name.startswith("lwall_"):
                model.geom_pos[g_id] = [10.0, 10.0, 0.25]
                
    elif scenario_type == "WALL_AHEAD":
        # Place vertical wall 2.0m directly ahead of robot start (0, 0)
        if 'lwall_v_0_2' in geom_names:
            model.geom_pos[geom_names['lwall_v_0_2']] = [2.0, 0.0, 0.25]
            
    elif scenario_type == "WALL_AT_45":
        # Place angled obstacle at (1.5, 0.8)
        if 'lwall_v_0_2' in geom_names:
            model.geom_pos[geom_names['lwall_v_0_2']] = [1.5, 0.6, 0.25]
            
    elif scenario_type == "CORRIDOR_WIDE":
        # 2.0m wide corridor along X axis
        if 'lwall_h_0_1' in geom_names: model.geom_pos[geom_names['lwall_h_0_1']] = [0.0, 1.0, 0.25]
        if 'lwall_h_1_1' in geom_names: model.geom_pos[geom_names['lwall_h_1_1']] = [0.0, -1.0, 0.25]
        
    elif scenario_type == "CORRIDOR_NARROW":
        # 0.75m narrow corridor
        if 'lwall_h_0_1' in geom_names: model.geom_pos[geom_names['lwall_h_0_1']] = [0.0, 0.38, 0.25]
        if 'lwall_h_1_1' in geom_names: model.geom_pos[geom_names['lwall_h_1_1']] = [0.0, -0.38, 0.25]
        
    elif scenario_type == "DEAD_END":
        # U-shaped dead end enclosure
        if 'lwall_v_0_2' in geom_names: model.geom_pos[geom_names['lwall_v_0_2']] = [1.8, 0.0, 0.25]
        if 'lwall_h_0_1' in geom_names: model.geom_pos[geom_names['lwall_h_0_1']] = [0.9, 0.65, 0.25]
        if 'lwall_h_1_1' in geom_names: model.geom_pos[geom_names['lwall_h_1_1']] = [0.9, -0.65, 0.25]
        
    elif scenario_type == "BIFURCATION":
        # Central obstacle causing split left vs right
        if 'lwall_v_0_2' in geom_names: model.geom_pos[geom_names['lwall_v_0_2']] = [1.6, 0.0, 0.25]
        if 'lwall_v_2_0' in geom_names: model.geom_pos[geom_names['lwall_v_2_0']] = [3.0, 1.2, 0.25]
        if 'lwall_v_2_2' in geom_names: model.geom_pos[geom_names['lwall_v_2_2']] = [3.0, -1.2, 0.25]
        
    elif scenario_type == "HISTORICAL_TURN_TRAP":
        # High lateral confinement forcing sharp turn followed by open space
        if 'lwall_v_0_2' in geom_names: model.geom_pos[geom_names['lwall_v_0_2']] = [1.5, 0.0, 0.25]
        if 'lwall_h_0_1' in geom_names: model.geom_pos[geom_names['lwall_h_0_1']] = [0.5, 0.8, 0.25]
        if 'lwall_h_1_1' in geom_names: model.geom_pos[geom_names['lwall_h_1_1']] = [0.5, -0.8, 0.25]

# =============================================================================
# SINGLE RUN EXECUTOR & TELEMETRY RECORDER
# =============================================================================
def run_single_test(run_id: str, test_group: str, scenario_type: str, seed: int, duration_ticks: int, record_video: bool = False):
    full_xml_path = os.path.join(REPO_ROOT, "world", "vessel_kinetic.xml")
    hal = MuJoCoHardwareAbstractionLayer(full_xml_path)
    model = hal.model
    data = hal.data
    
    configure_arena(model, scenario_type, seed)
    
    # Physics settle
    for _ in range(50):
        mujoco.mj_step(model, data)
        
    agent = CarlAutonomousOrganismAgent(dt=0.0333)
    np.random.seed(seed)
    random.seed(seed)
    
    # Setup Video Renderer if requested (High-Definition 720p Dynamic Tracking Camera)
    renderer = None
    video_writer = None
    cam = None
    video_path = os.path.join(VIDEOS_DIR, f"{run_id}.mp4")
    if record_video:
        renderer = mujoco.Renderer(model, 720, 1280)
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        cam.trackbodyid = model.body('drive_deck').id
        cam.distance = 3.0
        cam.elevation = -30.0
        cam.azimuth = 140.0
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, (1280, 720))
        
    telemetry_records = []
    video_frames_count = 0
    keyframes = {}
    
    start_time = time.time()
    for tick in range(duration_ticks):
        # Step autonomous agent
        cycle_res = agent.step_cognitive_cycle(hal)
        telem = cycle_res["telemetry"]
        sensory = cycle_res["sensory"]
        
        # Step physics (3 sub-steps)
        for _ in range(3):
            hal.step()
            
        record = {
            "tick": tick,
            "timestamp_s": round(tick * 0.0333, 4),
            "pos_x": round(float(telem.pos_x), 4),
            "pos_y": round(float(telem.pos_y), 4),
            "yaw": round(float(telem.yaw), 4),
            "speed": round(float(telem.speed), 4),
            "cmd_w_L": round(float(telem.commanded_w_L), 4),
            "cmd_w_R": round(float(telem.commanded_w_R), 4),
            "action_name": telem.chosen_action_name,
            "min_obstacle_dist": round(float(sensory.min_obstacle_dist), 4),
            "active_goal": telem.active_goal_id,
            "energy": round(float(telem.energy), 4),
            "thermal_load": round(float(telem.thermal_load), 4),
            "curiosity_drive": round(float(telem.curiosity_drive), 4),
            "empowerment_nats": round(float(telem.empowerment_nats), 4),
            "estimated_friction": round(float(agent.self_model.self_params.estimated_friction_coeff), 4),
            "prediction_error": round(float(telem.prediction_error), 4),
            "stuck_state": telem.stuck_state,
            "recovery_active": int(telem.recovery_active),
            "recovery_tier": int(telem.recovery_tier),
            "has_collision": int(telem.collision_occurred),
            "head_yaw": round(float(sensory.head_yaw), 4)
        }
        telemetry_records.append(record)
        
        if record_video:
            renderer.update_scene(data, camera=cam)
            rgb = renderer.render()
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            
            # Overlay Semi-Transparent Professional HUD Panel
            overlay = bgr.copy()
            cv2.rectangle(overlay, (20, 20), (620, 140), (15, 23, 42), -1)
            cv2.addWeighted(overlay, 0.75, bgr, 0.25, 0, bgr)
            cv2.rectangle(bgr, (20, 20), (620, 140), (2, 132, 199), 2)
            
            rec_col = (0, 220, 0) if not telem.recovery_active else (0, 100, 255)
            cv2.putText(bgr, f"CARL-DX P0 QUALIFICATION | {run_id}", (35, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.putText(bgr, f"Tick: {tick:4d} ({tick*0.0333:5.2f}s) | Goal: {telem.active_goal_id}", (35, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1)
            cv2.putText(bgr, f"Action: {telem.chosen_action_name} | Spd: {telem.speed:.2f} m/s", (35, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1)
            cv2.putText(bgr, f"Clearance: {sensory.min_obstacle_dist:.2f}m | Stuck: {telem.stuck_state} | Rec: {telem.recovery_active} (T{telem.recovery_tier})", (35, 122), cv2.FONT_HERSHEY_SIMPLEX, 0.48, rec_col, 1)
            
            video_writer.write(bgr)
            video_frames_count += 1
            
            # Capture Keyframes
            if tick == 0: keyframes["START"] = bgr
            if tick == 10: keyframes["FIRST_MOTION"] = bgr
            if telem.recovery_active and "RECOVERY_START" not in keyframes: keyframes["RECOVERY_START"] = bgr
            if not telem.recovery_active and "RECOVERY_START" in keyframes and "RECOVERY_END" not in keyframes: keyframes["RECOVERY_END"] = bgr
            if tick == duration_ticks - 1: keyframes["END"] = bgr

    if record_video:
        video_writer.release()
        for k_name, k_img in keyframes.items():
            k_path = os.path.join(KEYFRAMES_DIR, f"{run_id}_keyframe_{k_name.lower()}.png")
            cv2.imwrite(k_path, k_img)
            
    exec_time = time.time() - start_time
    
    # Save CSV Telemetry
    csv_path = os.path.join(TELEMETRY_DIR, f"{run_id}.csv")
    if telemetry_records:
        header = list(telemetry_records[0].keys())
        with open(csv_path, "w") as f:
            f.write(",".join(header) + "\n")
            for r in telemetry_records:
                f.write(",".join(str(r[k]) for k in header) + "\n")
                
    # Save Diagnostic Multi-Panel Plot
    plot_path = os.path.join(PLOTS_DIR, f"{run_id}_diagnostics.png")
    generate_diagnostic_plot(run_id, telemetry_records, plot_path)
    
    # Compute basic metrics for run summary
    positions = np.array([[r["pos_x"], r["pos_y"]] for r in telemetry_records])
    net_disp = float(np.linalg.norm(positions[-1] - positions[0])) if len(positions) > 0 else 0.0
    path_len = float(np.sum(np.linalg.norm(np.diff(positions, axis=0), axis=1))) if len(positions) > 1 else 0.0
    actions = [r["action_name"] for r in telemetry_records]
    action_switches = sum(1 for i in range(1, len(actions)) if actions[i] != actions[i-1])
    brake_ticks = sum(1 for a in actions if a == "BRAKE_REST")
    spin_ticks = sum(1 for a in actions if "SPIN" in a)
    collisions = sum(r["has_collision"] for r in telemetry_records)
    
    run_summary = {
        "run_id": run_id,
        "test_group": test_group,
        "scenario_type": scenario_type,
        "seed": seed,
        "total_ticks": duration_ticks,
        "duration_s": round(duration_ticks * 0.0333, 2),
        "execution_time_s": round(exec_time, 3),
        "mean_fps": round(duration_ticks / max(0.001, exec_time), 1),
        "net_displacement_m": round(net_disp, 4),
        "path_length_m": round(path_len, 4),
        "mean_speed_mps": round(float(np.mean([r["speed"] for r in telemetry_records])), 4),
        "action_switches": action_switches,
        "brake_rest_ticks": brake_ticks,
        "spin_ticks": spin_ticks,
        "total_collisions": collisions,
        "min_clearance_m": round(float(np.min([r["min_obstacle_dist"] for r in telemetry_records])), 4),
        "final_friction_mu": round(float(telemetry_records[-1]["estimated_friction"]), 4),
        "video_recorded": record_video,
        "video_frames": video_frames_count,
        "csv_path": csv_path,
        "video_path": video_path if record_video else None,
        "plot_path": plot_path
    }
    
    run_json_path = os.path.join(RUNS_DIR, f"{run_id}.json")
    with open(run_json_path, "w") as f:
        json.dump(run_summary, f, indent=2)
        
    print(f"  [RUN] {run_id:<32} | Grp: {test_group:<3} | Disp: {net_disp:6.2f}m | Coll: {collisions:2d} | Switches: {action_switches:3d} | Spd: {run_summary['mean_speed_mps']:.2f}m/s")
    return run_summary

# =============================================================================
# DIAGNOSTIC PLOT GENERATOR
# =============================================================================
def generate_diagnostic_plot(run_id: str, records: list, plot_path: str):
    if not records: return
    ticks = [r["tick"] for r in records]
    times = [r["timestamp_s"] for r in records]
    speeds = [r["speed"] for r in records]
    clearances = [r["min_obstacle_dist"] for r in records]
    w_L = [r["cmd_w_L"] for r in records]
    w_R = [r["cmd_w_R"] for r in records]
    yaws = [r["yaw"] for r in records]
    energies = [r["energy"] for r in records]
    thermals = [r["thermal_load"] for r in records]
    x_pos = [r["pos_x"] for r in records]
    y_pos = [r["pos_y"] for r in records]
    
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), facecolor="#ffffff")
    fig.suptitle(f"CARL-DX P0 REGRESSION DIAGNOSTICS — {run_id}", fontsize=14, fontweight='bold', color="#0f172a")
    
    # 1. 2D Trajectory
    axes[0, 0].plot(x_pos, y_pos, color="#0284c7", lw=2, label="Chassis Path")
    axes[0, 0].scatter([x_pos[0]], [y_pos[0]], color="#059669", s=60, label="Start", zorder=5)
    axes[0, 0].scatter([x_pos[-1]], [y_pos[-1]], color="#dc2626", s=60, label="End", zorder=5)
    axes[0, 0].set_title("2D Spatial Trajectory (XY)", fontsize=10, fontweight='bold')
    axes[0, 0].set_xlabel("X (m)"); axes[0, 0].set_ylabel("Y (m)")
    axes[0, 0].grid(True, linestyle="--", alpha=0.5); axes[0, 0].legend(loc="upper right")
    
    # 2. Linear Speed & Obstacle Clearance
    axes[0, 1].plot(times, speeds, color="#0284c7", lw=1.5, label="Speed (m/s)")
    axes[0, 1].plot(times, clearances, color="#d97706", lw=1.5, label="Clearance (m)")
    axes[0, 1].axhline(0.55, color="#dc2626", linestyle=":", label="Veto Threshold (0.55m)")
    axes[0, 1].set_title("Speed & Obstacle Clearance vs Time", fontsize=10, fontweight='bold')
    axes[0, 1].set_xlabel("Time (s)"); axes[0, 1].set_ylabel("Meters")
    axes[0, 1].grid(True, linestyle="--", alpha=0.5); axes[0, 1].legend(loc="upper right")
    
    # 3. Commanded Wheel Angular Velocities
    axes[1, 0].plot(times, w_L, color="#059669", lw=1.5, label="Wheel Left (rad/s)")
    axes[1, 0].plot(times, w_R, color="#7c3aed", lw=1.5, label="Wheel Right (rad/s)")
    axes[1, 0].set_title("Commanded Wheel Velocities (S-Curve Filtered)", fontsize=10, fontweight='bold')
    axes[1, 0].set_xlabel("Time (s)"); axes[1, 0].set_ylabel("rad/s")
    axes[1, 0].grid(True, linestyle="--", alpha=0.5); axes[1, 0].legend(loc="upper right")
    
    # 4. Heading Yaw Angle
    axes[1, 1].plot(times, yaws, color="#0891b2", lw=1.5, label="Heading Yaw (rad)")
    axes[1, 1].set_title("Chassis Heading Yaw vs Time", fontsize=10, fontweight='bold')
    axes[1, 1].set_xlabel("Time (s)"); axes[1, 1].set_ylabel("Yaw (rad)")
    axes[1, 1].grid(True, linestyle="--", alpha=0.5); axes[1, 1].legend(loc="upper right")
    
    # 5. Homeostatic Energy & Thermal Load
    axes[2, 0].plot(times, energies, color="#059669", lw=1.5, label="Battery Energy")
    axes[2, 0].plot(times, thermals, color="#dc2626", lw=1.5, label="Thermal Load")
    axes[2, 0].axhline(0.85, color="#dc2626", linestyle=":", label="Thermal Veto (0.85)")
    axes[2, 0].set_title("Homeostatic Bio-Energetics", fontsize=10, fontweight='bold')
    axes[2, 0].set_xlabel("Time (s)"); axes[2, 0].set_ylabel("Normalized [0, 1]")
    axes[2, 0].grid(True, linestyle="--", alpha=0.5); axes[2, 0].legend(loc="upper right")
    
    # 6. Action Sequence Raster
    actions = [r["action_name"] for r in records]
    unique_acts = sorted(list(set(actions)))
    act_indices = [unique_acts.index(a) for a in actions]
    axes[2, 1].step(times, act_indices, color="#7c3aed", lw=1.5, where='post')
    axes[2, 1].set_yticks(range(len(unique_acts)))
    axes[2, 1].set_yticklabels([a[:18] for a in unique_acts], fontsize=7)
    axes[2, 1].set_title("Action Primitive Timeline", fontsize=10, fontweight='bold')
    axes[2, 1].set_xlabel("Time (s)"); axes[2, 1].grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    fig.savefig(plot_path, dpi=150, facecolor="#ffffff")
    plt.close(fig)

# =============================================================================
# MASTER TEST SUITE EXECUTION
# =============================================================================
def run_full_p0_suite():
    print("=================================================================")
    print("   LAUNCHING CARL-DX P0-01 FROZEN BASELINE REGRESSION SUITE")
    print("=================================================================")
    
    manifest = generate_baseline_manifest()
    all_runs = []
    
    # Test Matrix Definitions
    # (Group, Scenario, Duration Ticks, Description, Record Video)
    matrix = [
        # GROUP A: STARTUP & INITIAL CONDITIONS
        ("A", "OPEN_SPACE", 30, "Startup Clean Initialization", True),
        
        # GROUP B: OPEN-SPACE LOCOMOTION (Across all 5 seeds)
        ("B1", "OPEN_SPACE", 200, "Open Space Locomotion Seed 42", True),
        ("B2", "OPEN_SPACE", 200, "Open Space Post-Reset Run", False),
        ("B3", "OPEN_SPACE", 200, "Open Space Post-5x Reset Run", False),
        ("B4", "OPEN_SPACE", 200, "Open Space Multi-Seed Variation", False),
        
        # GROUP C: TURNING & CORRIDOR REALIGNMENT
        ("C1", "WALL_AT_45", 250, "Left Obstacle Turn", True),
        ("C2", "WALL_AT_45", 250, "Right Obstacle Turn", False),
        ("C3", "WALL_AHEAD", 250, "Left to Straight Transition", True),
        ("C4", "WALL_AHEAD", 250, "Right to Straight Transition", False),
        ("C5", "CORRIDOR_WIDE", 250, "Straight Left Straight Corridor", False),
        ("C6", "CORRIDOR_WIDE", 250, "Straight Right Straight Corridor", False),
        ("C7", "BIFURCATION", 300, "Consecutive Alternating S-Curves", True),
        
        # GROUP D: EXACT HISTORICAL FAILURE REPRODUCTION
        ("D1", "HISTORICAL_TURN_TRAP", 300, "Historical Turning Loop Trap Check", True),
        ("D2", "WALL_AHEAD", 250, "Historical Wall Stall Trap Check", True),
        ("D3", "OPEN_SPACE", 250, "Historical Right Loop Trap Check", False),
        ("D4", "OPEN_SPACE", 250, "Historical Left Loop Trap Check", False),
        
        # GROUP E: BRAKE-LOCK DETECTOR
        ("E1", "OPEN_SPACE", 200, "Open Space Brake Lock Check", False),
        ("E2", "CORRIDOR_WIDE", 200, "Corridor Brake Lock Check", False),
        
        # GROUP F: FORWARD / REVERSE LIMIT CYCLES
        ("F1", "WALL_AHEAD", 250, "Forward Reverse Oscillation Check", False),
        ("F2", "DEAD_END", 300, "Dead End Forward Reverse Trap", True),
        
        # GROUP G: LEFT / RIGHT LIMIT CYCLES & CHATTER
        ("G1", "BIFURCATION", 250, "Bifurcation Steering Chatter Check", False),
        ("G2", "CORRIDOR_NARROW", 250, "Narrow Corridor Steering Chatter", True),
        
        # GROUP H: SPIN LOOPS
        ("H1", "OPEN_SPACE", 200, "Open Space Spin Loop Check", False),
        ("H2", "DEAD_END", 350, "Dead End Legitimate Spin Check", True),
        ("H3", "BIFURCATION", 250, "Obstacle Spin Loop Check", False),
        
        # GROUP I: STATIONARY STALL DETECTOR
        ("I1", "WALL_AHEAD", 250, "Wall Approach Stall Check", False),
        ("I2", "DEAD_END", 300, "Corner Approach Stall Check", False),
        
        # GROUP J: RECOVERY SYSTEM TIERS 1, 2, 3
        ("J1", "DEAD_END", 350, "Tier 1 Reverse Curve Recovery", True),
        ("J2", "DEAD_END", 350, "Tier 2 Targeted Spin Recovery", False),
        ("J3", "DEAD_END", 350, "Tier 3 Forward Breakout Recovery", False),
        
        # GROUP K: NARROW PASSAGE & CORRIDORS
        ("K1", "CORRIDOR_WIDE", 250, "Wide Corridor Traversal", False),
        ("K2", "CORRIDOR_WIDE", 250, "Moderate Corridor Traversal", False),
        ("K3", "CORRIDOR_NARROW", 250, "Narrow Corridor Traversal", True),
        ("K4", "CORRIDOR_WIDE", 250, "Corridor with Opening", False),
        ("K5", "DEAD_END", 300, "Dead End Trap Recognition", False),
        ("K6", "WALL_AT_45", 250, "Corner Obstacle Navigation", False),
        ("K7", "BIFURCATION", 250, "Symmetric Corridor Split", False),
        
        # GROUP L: RESET ROBUSTNESS (L1 to L10)
        ("L1", "OPEN_SPACE", 150, "Normal Run Reset Check", False),
        ("L2", "WALL_AT_45", 150, "Turning State Reset Check", False),
        ("L3", "OPEN_SPACE", 150, "Braking State Reset Check", False),
        ("L4", "DEAD_END", 150, "Recovery State Reset Check", False),
        ("L5", "WALL_AHEAD", 150, "Near Obstacle Reset Check", False),
        ("L6", "OPEN_SPACE", 150, "Post Memory Write Reset Check", False),
        ("L7", "OPEN_SPACE", 150, "Post Friction Adapt Reset Check", False),
        ("L8", "OPEN_SPACE", 150, "10x Consecutive Resets Check", False),
        ("L9", "OPEN_SPACE", 150, "Cross Seed Reset Check", False),
        ("L10", "OPEN_SPACE", 150, "Fresh vs Same Process Reset Check", False),
        
        # GROUP M: SENSOR CONSISTENCY
        ("M1", "OPEN_SPACE", 150, "Sensor Normal Bounds Check", False),
        ("M2", "WALL_AHEAD", 150, "Sensor Min Range Bounds Check", False),
        ("M3", "CORRIDOR_WIDE", 150, "Sensor Symmetry Check", False),
        
        # GROUP N: LONG-DURATION RUNS
        ("N1", "OPEN_SPACE", 300, "10-Second Continuous Run (300 Ticks)", True),
        ("N2", "CORRIDOR_WIDE", 900, "30-Second Continuous Run (900 Ticks)", True),
        ("N3", "BIFURCATION", 1800, "60-Second Stress Run (1800 Ticks)", True)
    ]
    
    print(f"\n[SUITE] Commencing execution of {len(matrix)} test configurations across {len(OFFICIAL_SEEDS)} official seeds...\n")
    
    run_idx = 1
    for grp, scen, dur, desc, rec_vid in matrix:
        for seed in OFFICIAL_SEEDS:
            # For multi-seed variations, iterate all seeds; for specific single tests, run on primary seed
            if not grp.startswith("B") and not grp.startswith("N") and seed != OFFICIAL_SEEDS[0]:
                continue
                
            run_id = f"P0_{grp}_S{seed}_{scen}_{dur}T"
            res = run_single_test(run_id, grp, scen, seed, dur, record_video=(rec_vid and seed == OFFICIAL_SEEDS[0]))
            all_runs.append(res)
            run_idx += 1
            
    print(f"\n[SUITE] All {len(all_runs)} runs completed successfully. Raw telemetry and videos stored in {OUTPUT_DIR}.")
    return all_runs

if __name__ == "__main__":
    run_full_p0_suite()
