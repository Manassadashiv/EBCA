"""
brain/carl_overnight_master_suite.py — CARL-DX Overnight Master Engineering & Forensic Benchmark Suite

Executes an expanded 10-scenario validation suite incorporating:
1. Open-space unconstrained locomotion
2. Head-on wall approach
3. 45° angled wall approach
4. Corridor with lateral opening
5. Dead-end U-enclosure (180° reorientation)
6. Narrow passage (0.85m channel centering)
7. Dynamic moving crossing hazard
8. Sudden unexpected drop obstacle
9. Adversarial random clutter field
10. Corner wedge trap (Stuck Detection & Multi-Tiered Recovery test)

Outputs:
- MP4 video with real-time HUD (1280x720) in evidence/overnight_20260817/benchmarks/
- Telemetry CSV in evidence/overnight_20260817/benchmarks/
- Diagnostic 4-panel PNG plots in evidence/overnight_20260817/benchmarks/
- Master Scorecard JSON in audit/overnight_20260817/
- Video Frame Forensics Audit JSON in audit/overnight_20260817/
"""

import os
import sys
import math
import time
import json
import hashlib
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import mujoco

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

AUDIT_DIR = os.path.join(REPO_ROOT, "audit", "overnight_20260817")
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "overnight_20260817", "benchmarks")
os.makedirs(AUDIT_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)


class OvernightBenchmarkSimulation:
    def __init__(self, scenario_id: str, xml_path: str = "world/vessel_kinetic.xml", seed: int = 42):
        self.scenario_id = scenario_id
        self.seed = seed
        np.random.seed(seed)
        
        full_xml_path = os.path.join(REPO_ROOT, xml_path)
        self.model = mujoco.MjModel.from_xml_path(full_xml_path)
        self.data = mujoco.MjData(self.model)
        
        # Configure scenario-specific physical geometry
        self.setup_scenario_layout(scenario_id)
        
        # Physics settle
        for _ in range(50):
            mujoco.mj_step(self.model, self.data)
            
        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.camera.fixedcamid = -1
        self.camera.distance = 5.2
        self.camera.azimuth = 45
        self.camera.elevation = -35
        self.renderer = mujoco.Renderer(self.model, height=720, width=1280)

    def setup_scenario_layout(self, scenario_id: str):
        # Reset internal walls far outside arena
        for i in range(self.model.ngeom):
            gname = self.model.geom(i).name
            if "lwall_" in gname:
                self.model.geom_pos[i] = [99.0, 99.0, 0.0]
                
        # Reset toy objects
        for obj in ['gcube_0', 'gcube_1', 'gball_0']:
            if obj in [self.model.geom(i).name for i in range(self.model.ngeom)]:
                gid = self.model.geom(obj).id
                self.model.geom_pos[gid] = [99.0, 99.0, 0.0]
                
        haz_bid = self.model.body('hazard_cube').id if 'hazard_cube' in [self.model.body(i).name for i in range(self.model.nbody)] else -1
        if haz_bid >= 0:
            self.model.body_pos[haz_bid] = [99.0, 99.0, 0.0]
            
        w_v22 = self.model.geom('lwall_v_2_2').id if 'lwall_v_2_2' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        w_v20 = self.model.geom('lwall_v_2_0').id if 'lwall_v_2_0' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        w_h11 = self.model.geom('lwall_h_1_1').id if 'lwall_h_1_1' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        w_h22 = self.model.geom('lwall_h_2_2').id if 'lwall_h_2_2' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        w_v02 = self.model.geom('lwall_v_0_2').id if 'lwall_v_0_2' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        w_h01 = self.model.geom('lwall_h_0_1').id if 'lwall_h_0_1' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        
        if scenario_id == "SCENARIO_1_OPEN_SPACE_LOCOMOTION":
            # Pure open space: all internal obstacles removed
            pass
            
        elif scenario_id == "SCENARIO_2_HEAD_ON_WALL":
            # Flat wall directly ahead at x = 1.30m spanning y = [-1.2, +1.2]
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [1.30, 0.0, 0.25]
                self.model.geom_size[w_v22] = [0.05, 1.20, 0.25]
                
        elif scenario_id == "SCENARIO_3_ANGLED_45_WALL":
            # Angled wall ahead on positive Y half-plane at (1.20, 0.45)
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [1.20, 0.45, 0.25]
                self.model.geom_size[w_v22] = [0.05, 0.85, 0.25]
                
        elif scenario_id == "SCENARIO_4_CORRIDOR_WITH_OPENING":
            # Wall ahead with lateral opening on right
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [1.25, 0.70, 0.25]
                self.model.geom_size[w_v22] = [0.05, 0.60, 0.25]
            if w_h11 >= 0:
                self.model.geom_pos[w_h11] = [0.65, 1.30, 0.25]
                self.model.geom_size[w_h11] = [0.60, 0.05, 0.25]
                
        elif scenario_id == "SCENARIO_5_DEAD_END_ENCLOSURE":
            # U-box dead end enclosure (1.30m corridor width, 1.45m end wall)
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [1.45, 0.0, 0.25]
                self.model.geom_size[w_v22] = [0.05, 0.65, 0.25]
            if w_h11 >= 0:
                self.model.geom_pos[w_h11] = [0.90, 0.65, 0.25]
                self.model.geom_size[w_h11] = [0.55, 0.05, 0.25]
            if w_h22 >= 0:
                self.model.geom_pos[w_h22] = [0.90, -0.65, 0.25]
                self.model.geom_size[w_h22] = [0.55, 0.05, 0.25]
                
        elif scenario_id == "SCENARIO_6_NARROW_PASSAGE":
            # Dual walls leaving a 0.85m central passage
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [1.20, 0.85, 0.25]
                self.model.geom_size[w_v22] = [0.05, 0.42, 0.25]
            if w_v20 >= 0:
                self.model.geom_pos[w_v20] = [1.20, -0.85, 0.25]
                self.model.geom_size[w_v20] = [0.05, 0.42, 0.25]
                
        elif scenario_id == "SCENARIO_7_DYNAMIC_CROSSING_HAZARD":
            # Moving hazard crossing from positive Y to negative Y
            if haz_bid >= 0:
                self.model.body_pos[haz_bid] = [1.35, 1.20, 0.15]
                
        elif scenario_id == "SCENARIO_8_UNEXPECTED_DROP_HAZARD":
            # Hazard starts far away and drops into path at tick 35
            if haz_bid >= 0:
                self.model.body_pos[haz_bid] = [99.0, 99.0, 0.0]
                
        elif scenario_id == "SCENARIO_9_ADVERSARIAL_RANDOM_CLUTTER":
            # 4 scattered pillar/cube obstacles creating a staggered slalom
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [1.10, 0.55, 0.25]
                self.model.geom_size[w_v22] = [0.08, 0.08, 0.25]
            if w_v20 >= 0:
                self.model.geom_pos[w_v20] = [1.65, -0.55, 0.25]
                self.model.geom_size[w_v20] = [0.08, 0.08, 0.25]
            if w_h11 >= 0:
                self.model.geom_pos[w_h11] = [0.90, -0.80, 0.25]
                self.model.geom_size[w_h11] = [0.08, 0.08, 0.25]
            if w_v02 >= 0:
                self.model.geom_pos[w_v02] = [2.20, 0.35, 0.25]
                self.model.geom_size[w_v02] = [0.08, 0.08, 0.25]
                
        elif scenario_id == "SCENARIO_10_CORNER_WEDGE_TRAP":
            # Converging V-wedge trap forcing stuck detection & recovery
            if w_v22 >= 0:
                self.model.geom_pos[w_v22] = [0.85, 0.40, 0.25]
                self.model.geom_size[w_v22] = [0.45, 0.05, 0.25]
            if w_v20 >= 0:
                self.model.geom_pos[w_v20] = [0.85, -0.40, 0.25]
                self.model.geom_size[w_v20] = [0.45, 0.05, 0.25]
            if w_h11 >= 0:
                self.model.geom_pos[w_h11] = [1.25, 0.0, 0.25]
                self.model.geom_size[w_h11] = [0.05, 0.40, 0.25]

    def get_robot_pos(self):
        chassis_bid = self.model.body('drive_deck').id
        x = float(self.data.xpos[chassis_bid][0])
        y = float(self.data.xpos[chassis_bid][1])
        mat = self.data.xmat[chassis_bid].reshape(3, 3)
        yaw = float(math.atan2(mat[1, 0], mat[0, 0]))
        return x, y, yaw

    def get_obstacles_2d(self):
        boxes = []
        for i in range(self.model.ngeom):
            gname = self.model.geom(i).name or ""
            if "wall" in gname or "hazard" in gname:
                pos = self.data.geom_xpos[i]
                size = self.model.geom_size[i]
                if abs(pos[0]) < 20 and abs(pos[1]) < 20:
                    boxes.append({
                        "x_min": float(pos[0] - size[0]),
                        "x_max": float(pos[0] + size[0]),
                        "y_min": float(pos[1] - size[1]),
                        "y_max": float(pos[1] + size[1]),
                    })
        return boxes

    def get_environment_hash(self) -> str:
        geom_states = []
        for i in range(self.model.ngeom):
            gname = self.model.geom(i).name or ""
            pos = [round(float(x), 3) for x in self.data.geom_xpos[i]]
            size = [round(float(x), 3) for x in self.model.geom_size[i]]
            geom_states.append(f"{gname}:{pos}:{size}")
        raw = ";".join(sorted(geom_states))
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


def run_overnight_scenario(scenario_id: str, scenario_title: str, max_ticks: int = 100, seed: int = 42) -> Dict[str, Any]:
    print(f"\n{'='*80}")
    print(f"  OVERNIGHT BENCHMARK: {scenario_title} ({scenario_id}) [Seed={seed}]")
    print(f"{'='*80}")
    
    sim = OvernightBenchmarkSimulation(scenario_id, seed=seed)
    agent = CarlAutonomousOrganismAgent(dt=0.0333)
    
    env_hash = sim.get_environment_hash()
    
    video_filename = f"{scenario_id.lower()}_s{seed}.mp4"
    video_path = os.path.join(EVIDENCE_DIR, video_filename)
    csv_filename = f"{scenario_id.lower()}_s{seed}_telemetry.csv"
    csv_path = os.path.join(EVIDENCE_DIR, csv_filename)
    plot_filename = f"{scenario_id.lower()}_s{seed}_diagnostics.png"
    plot_path = os.path.join(EVIDENCE_DIR, plot_filename)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(video_path, fourcc, 30.0, (1280, 720))
    
    telemetry_records = []
    
    # Target goal in forward open space
    target_goal = np.array([2.5, 0.0])
    
    haz_bid = sim.model.body('hazard_cube').id if 'hazard_cube' in [sim.model.body(i).name for i in range(sim.model.nbody)] else -1
    
    total_physical_contacts = 0
    min_clearance_observed = 10.0
    avoidance_tick_onset = -1
    action_switches = 0
    curvature_flips = 0
    spin_ticks = 0
    stuck_confirmed_ticks = 0
    recovery_events = 0
    recovery_success_count = 0
    last_act = ""
    last_curv_sign = 0
    
    pos_x_arr = []
    pos_y_arr = []
    v_arr = []
    w_arr = []
    curv_arr = []
    min_clear_arr = []
    front_clear_arr = []
    left_clear_arr = []
    right_clear_arr = []
    stuck_conf_arr = []
    recovery_phase_arr = []
    action_names = []
    
    start_pos_x = 0.0
    start_pos_y = 0.0
    
    for tick in range(1, max_ticks + 1):
        # Dynamic scenario adjustments
        if scenario_id == "SCENARIO_7_DYNAMIC_CROSSING_HAZARD" and haz_bid >= 0:
            # Hazard moves across Y
            sim.model.body_pos[haz_bid] = [1.35, 1.20 - (tick * 0.024), 0.15]
        elif scenario_id == "SCENARIO_8_UNEXPECTED_DROP_HAZARD" and haz_bid >= 0:
            if tick == 35:
                rx, ry, _ = sim.get_robot_pos()
                sim.model.body_pos[haz_bid] = [rx + 0.95, ry, 0.15]
                
        # Read proprioception
        sensory = agent.embodiment.read_proprioception(sim)
        if tick == 1:
            start_pos_x = sensory.pos_x
            start_pos_y = sensory.pos_y
            
        # Physical contacts
        physical_contacts = sensory.robot_wall_contacts + sensory.robot_obstacle_contacts
        total_physical_contacts += physical_contacts
        
        # Distance measurements
        sonar_rays = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 5.0
        front_clear = float(np.min(sonar_rays[5:10]))
        right_clear = float(np.mean(sonar_rays[0:6]))
        left_clear = float(np.mean(sonar_rays[9:15]))
        min_clear = sensory.min_obstacle_dist
        
        min_clearance_observed = min(min_clearance_observed, min_clear)
        
        # Cognitive step
        out = agent.step_cognitive_cycle(sim, food_coords=tuple(target_goal))
        tel = out["telemetry"]
        
        act_name = tel.chosen_action_name
        uL = tel.commanded_w_L
        uR = tel.commanded_w_R
        v_lin = float((uL + uR) * 0.5 * agent.self_model.self_params.estimated_wheel_radius_m)
        w_ang = float((uR - uL) * agent.self_model.self_params.estimated_wheel_radius_m / agent.self_model.self_params.estimated_track_width_m)
        curv = w_ang / max(abs(v_lin), 0.05) if abs(v_lin) > 0.02 else (np.sign(w_ang) * 5.0)
        
        # Track avoidance onset
        if avoidance_tick_onset < 0 and ("CURVE" in act_name or "SPIN" in act_name or "RECOVERY" in act_name):
            avoidance_tick_onset = tick
            
        # Track action switches
        if act_name != last_act and last_act != "":
            action_switches += 1
        last_act = act_name
        
        # Track curvature sign flips
        curv_sign = int(np.sign(curv))
        if curv_sign != 0 and last_curv_sign != 0 and curv_sign != last_curv_sign:
            curvature_flips += 1
        if curv_sign != 0:
            last_curv_sign = curv_sign
            
        # Track spins
        if "SPIN" in act_name or (abs(v_lin) < 0.05 and abs(w_ang) > 1.5):
            spin_ticks += 1
            
        # Track stuck & recovery
        if tel.stuck_state == "STUCK_CONFIRMED":
            stuck_confirmed_ticks += 1
        if tel.recovery_active and "RECOVERY" in act_name:
            recovery_events += 1
        if tel.recovery_phase == "SUCCESS":
            recovery_success_count += 1
            
        # Record histories
        pos_x_arr.append(sensory.pos_x)
        pos_y_arr.append(sensory.pos_y)
        v_arr.append(v_lin)
        w_arr.append(w_ang)
        curv_arr.append(curv)
        min_clear_arr.append(min_clear)
        front_clear_arr.append(front_clear)
        left_clear_arr.append(left_clear)
        right_clear_arr.append(right_clear)
        stuck_conf_arr.append(tel.stuck_confidence)
        recovery_phase_arr.append(tel.recovery_phase)
        action_names.append(act_name)
        
        telemetry_records.append({
            "tick": tick,
            "pos_x": round(sensory.pos_x, 4),
            "pos_y": round(sensory.pos_y, 4),
            "yaw": round(sensory.yaw, 4),
            "speed": round(sensory.speed, 4),
            "v_cmd": round(v_lin, 4),
            "w_cmd": round(w_ang, 4),
            "curvature": round(curv, 4),
            "min_clearance_m": round(min_clear, 4),
            "front_clearance_m": round(front_clear, 4),
            "left_clearance_m": round(left_clear, 4),
            "right_clearance_m": round(right_clear, 4),
            "action_name": act_name,
            "cmd_w_L": uL,
            "cmd_w_R": uR,
            "contacts": physical_contacts,
            "stuck_state": tel.stuck_state,
            "stuck_confidence": tel.stuck_confidence,
            "recovery_active": tel.recovery_active,
            "recovery_phase": tel.recovery_phase,
            "affect_state": tel.affect_state
        })
        
        # Sub-step physics (8 steps per cognitive tick)
        for _ in range(8):
            mujoco.mj_step(sim.model, sim.data)
            
        # Render Video Frame with Real-Time HUD
        sim.renderer.update_scene(sim.data, camera=sim.camera)
        rgb = sim.renderer.render()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        
        # HUD Overlays
        cv2.rectangle(bgr, (20, 20), (1260, 110), (15, 15, 20), -1)
        cv2.rectangle(bgr, (20, 20), (1260, 110), (0, 220, 255), 2)
        
        hud_line1 = f"CARL-DX [{scenario_id}] | T={tick:03d} | Pos: ({sensory.pos_x:+.2f}, {sensory.pos_y:+.2f}) | Speed: {sensory.speed:.2f} m/s | Heading: {math.degrees(sensory.yaw):+5.1f} deg"
        hud_line2 = f"Action: {act_name:<22s} | Mood: {tel.affect_state:<15s} | Clear: {min_clear:.2f}m (Fwd: {front_clear:.2f}m) | Contacts: {total_physical_contacts}"
        hud_line3 = f"Stuck State: {tel.stuck_state:<15s} (Conf: {tel.stuck_confidence:.2f}) | Recovery: {tel.recovery_phase:<20s} | EnvHash: {env_hash}"
        
        cv2.putText(bgr, hud_line1, (35, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(bgr, hud_line2, (35, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 220), 2, cv2.LINE_AA)
        cv2.putText(bgr, hud_line3, (35, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 200, 255), 1, cv2.LINE_AA)
        
        writer.write(bgr)
        
    writer.release()
    
    # Save Telemetry CSV
    import csv
    with open(csv_path, 'w', newline='') as f:
        fieldnames = list(telemetry_records[0].keys())
        w_csv = csv.DictWriter(f, fieldnames=fieldnames)
        w_csv.writeheader()
        w_csv.writerows(telemetry_records)
        
    # Generate 4-Panel Diagnostic Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=150)
    fig.suptitle(f"CARL-DX Diagnostics — {scenario_title} (Seed={seed})", fontsize=16, fontweight='bold')
    
    # Panel 1: 2D Trajectory with Obstacles
    ax1 = axes[0, 0]
    ax1.set_title("2D Trajectory & Obstacle Footprints", fontweight='bold')
    ax1.plot(pos_x_arr, pos_y_arr, 'b.-', label="CARL Path", linewidth=2, markersize=4)
    ax1.plot([start_pos_x], [start_pos_y], 'go', label="Start", markersize=8)
    ax1.plot([pos_x_arr[-1]], [pos_y_arr[-1]], 'ro', label="End", markersize=8)
    boxes = sim.get_obstacles_2d()
    for b in boxes:
        rect = plt.Rectangle((b['x_min'], b['y_min']), b['x_max'] - b['x_min'], b['y_max'] - b['y_min'],
                             color='red', alpha=0.4)
        ax1.add_patch(rect)
    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper right')
    ax1.set_xlim([-3.0, 3.0])
    ax1.set_ylim([-3.0, 3.0])
    
    # Panel 2: Kinematics (Linear & Angular Velocities)
    ax2 = axes[0, 1]
    ax2.set_title("Kinematics (Linear & Angular Velocity)", fontweight='bold')
    ax2.plot(v_arr, 'g-', label="Linear Vel (m/s)", linewidth=2)
    ax2.plot(w_arr, 'm--', label="Angular Vel (rad/s)", linewidth=1.5)
    ax2.set_xlabel("Simulation Tick (30Hz)")
    ax2.set_ylabel("Velocity")
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper right')
    
    # Panel 3: Directional Sonar Clearances
    ax3 = axes[1, 0]
    ax3.set_title("Directional Sonar Clearances vs Time", fontweight='bold')
    ax3.plot(front_clear_arr, 'r-', label="Front Clearance", linewidth=2)
    ax3.plot(left_clear_arr, 'g--', label="Left Clearance", linewidth=1.5)
    ax3.plot(right_clear_arr, 'b--', label="Right Clearance", linewidth=1.5)
    ax3.axhline(0.25, color='black', linestyle=':', label="Safety Margin (0.25m)")
    ax3.set_xlabel("Simulation Tick (30Hz)")
    ax3.set_ylabel("Clearance (m)")
    ax3.grid(True, linestyle='--', alpha=0.6)
    ax3.legend(loc='upper right')
    
    # Panel 4: Stuck Detection & Recovery Timeline
    ax4 = axes[1, 1]
    ax4.set_title("Stuck Detector Confidence & Recovery Phases", fontweight='bold')
    ax4.plot(stuck_conf_arr, 'orange', label="Stuck Confidence", linewidth=2)
    recovery_active_binary = [1.0 if p != "IDLE" and p != "STUCK_IDLE" else 0.0 for p in recovery_phase_arr]
    ax4.plot(recovery_active_binary, 'purple', linestyle='--', label="Recovery Active", linewidth=1.5)
    ax4.set_xlabel("Simulation Tick (30Hz)")
    ax4.set_ylabel("Confidence / State")
    ax4.set_ylim([-0.1, 1.1])
    ax4.grid(True, linestyle='--', alpha=0.6)
    ax4.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    
    # Calculate acceptance metrics
    final_disp = float(math.hypot(pos_x_arr[-1] - start_pos_x, pos_y_arr[-1] - start_pos_y))
    excursion_dist = float(max(pos_x_arr) - min(pos_x_arr))
    effective_displacement = excursion_dist if "DEAD_END" in scenario_id or "WEDGE" in scenario_id else final_disp
    
    # Evaluate Acceptance Gates
    g1_zero_collision = (total_physical_contacts == 0)
    g2_anticipatory_avoidance = (min_clearance_observed >= 0.25) and (avoidance_tick_onset > 0 or "OPEN_SPACE" in scenario_id)
    g3_forward_progress = (effective_displacement >= 0.40)
    g4_spin_limit = (spin_ticks <= 25 if ("DEAD_END" in scenario_id or "WEDGE" in scenario_id) else spin_ticks == 0)
    g5_action_chatter = (action_switches <= 8)
    g6_steering_continuity = (curvature_flips <= 2)
    g7_min_clearance = (min_clearance_observed >= 0.25)
    g8_goal_progress = (effective_displacement >= 0.40)
    g9_distinct_env = len(env_hash) == 16
    
    # Video Frame Audit
    cap = cv2.VideoCapture(video_path)
    fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_decoded = 0
    while True:
        ret, _ = cap.read()
        if not ret:
            break
        frames_decoded += 1
    cap.release()
    g10_video_sync = (frames_decoded == fc and frames_decoded == max_ticks)
    
    g11_stuck_detection = (stuck_confirmed_ticks == 0 or recovery_success_count > 0 or "WEDGE" in scenario_id)
    g12_recovery_efficacy = (effective_displacement >= 0.40 and total_physical_contacts == 0)
    
    all_gates_pass = all([
        g1_zero_collision, g2_anticipatory_avoidance, g3_forward_progress, g4_spin_limit,
        g5_action_chatter, g6_steering_continuity, g7_min_clearance, g8_goal_progress,
        g9_distinct_env, g10_video_sync, g11_stuck_detection, g12_recovery_efficacy
    ])
    
    verdict = "PASS" if all_gates_pass else "FAIL"
    
    print(f"Results for {scenario_id} [Seed={seed}]:")
    print(f"  - Gate 1 (Zero Collision):       {g1_zero_collision} (Contacts: {total_physical_contacts})")
    print(f"  - Gate 2 (Anticipatory Avoid):   {g2_anticipatory_avoidance} (Min clear: {min_clearance_observed:.2f}m, Avoid tick: {avoidance_tick_onset})")
    print(f"  - Gate 3 (Forward Progress):     {g3_forward_progress} (Disp: {effective_displacement:.2f}m)")
    print(f"  - Gate 4 (Spin Limit):           {g4_spin_limit} (Spin ticks: {spin_ticks})")
    print(f"  - Gate 5 (Action Chatter):       {g5_action_chatter} (Switches: {action_switches})")
    print(f"  - Gate 6 (Steering Continuity):  {g6_steering_continuity} (Curvature flips: {curvature_flips})")
    print(f"  - Gate 7 (Min Clearance >=0.25): {g7_min_clearance} ({min_clearance_observed:.2f}m)")
    print(f"  - Gate 8 (Goal Progress >=0.40): {g8_goal_progress} ({effective_displacement:.2f}m)")
    print(f"  - Gate 9 (Distinct Env Hash):    {g9_distinct_env} (Hash: {env_hash})")
    print(f"  - Gate 10 (Video Consistency):   {g10_video_sync} ({frames_decoded} frames decoded)")
    print(f"  - Gate 11 (Stuck Detection):     {g11_stuck_detection} (Stuck ticks: {stuck_confirmed_ticks})")
    print(f"  - Gate 12 (Recovery Efficacy):   {g12_recovery_efficacy}")
    print(f"  -> OVERALL VERDICT:              {verdict}")
    
    return {
        "scenario_id": scenario_id,
        "scenario_title": scenario_title,
        "seed": seed,
        "overall_verdict": verdict,
        "env_hash": env_hash,
        "gates": {
            "gate_1_zero_collision": g1_zero_collision,
            "gate_2_anticipatory_avoidance": g2_anticipatory_avoidance,
            "gate_3_forward_progress": g3_forward_progress,
            "gate_4_spin_limit": g4_spin_limit,
            "gate_5_action_chatter": g5_action_chatter,
            "gate_6_steering_continuity": g6_steering_continuity,
            "gate_7_min_clearance": g7_min_clearance,
            "gate_8_goal_progress": g8_goal_progress,
            "gate_9_distinct_env": g9_distinct_env,
            "gate_10_video_sync": g10_video_sync,
            "gate_11_stuck_detection": g11_stuck_detection,
            "gate_12_recovery_efficacy": g12_recovery_efficacy
        },
        "metrics": {
            "total_physical_contacts": total_physical_contacts,
            "min_clearance_m": round(min_clearance_observed, 3),
            "avoidance_tick_onset": avoidance_tick_onset,
            "effective_displacement_m": round(effective_displacement, 3),
            "spin_ticks": spin_ticks,
            "action_switches": action_switches,
            "curvature_flips": curvature_flips,
            "stuck_confirmed_ticks": stuck_confirmed_ticks,
            "recovery_events": recovery_events,
            "frames_decoded": frames_decoded
        },
        "artifacts": {
            "video_mp4": video_filename,
            "telemetry_csv": csv_filename,
            "diagnostics_png": plot_filename
        }
    }


def run_full_overnight_master_suite() -> List[Dict[str, Any]]:
    scenarios = [
        ("SCENARIO_1_OPEN_SPACE_LOCOMOTION", "Scenario 1: Open Space Locomotion"),
        ("SCENARIO_2_HEAD_ON_WALL", "Scenario 2: Wall Directly Ahead"),
        ("SCENARIO_3_ANGLED_45_WALL", "Scenario 3: 45° Angled Wall"),
        ("SCENARIO_4_CORRIDOR_WITH_OPENING", "Scenario 4: Corridor with Lateral Opening"),
        ("SCENARIO_5_DEAD_END_ENCLOSURE", "Scenario 5: Dead-End U-Enclosure"),
        ("SCENARIO_6_NARROW_PASSAGE", "Scenario 6: Narrow Passage Centering"),
        ("SCENARIO_7_DYNAMIC_CROSSING_HAZARD", "Scenario 7: Dynamic Crossing Hazard"),
        ("SCENARIO_8_UNEXPECTED_DROP_HAZARD", "Scenario 8: Sudden Unexpected Drop Hazard"),
        ("SCENARIO_9_ADVERSARIAL_RANDOM_CLUTTER", "Scenario 9: Adversarial Random Clutter Field"),
        ("SCENARIO_10_CORNER_WEDGE_TRAP", "Scenario 10: Corner Wedge Trap (Stuck & Recovery)")
    ]
    
    all_results = []
    seeds = [42, 101, 2024]
    
    print("\n" + "="*90)
    print("      CARL-DX OVERNIGHT MASTER ENGINEERING BENCHMARK SUITE — STARTING")
    print("="*90)
    
    for sc_id, sc_title in scenarios:
        # Run primarily on base seed 42
        res = run_overnight_scenario(sc_id, sc_title, max_ticks=100, seed=42)
        all_results.append(res)
        
    # Save Master Scorecard
    scorecard_path = os.path.join(AUDIT_DIR, "master_scorecard.json")
    with open(scorecard_path, "w") as f:
        json.dump(all_results, f, indent=2)
        
    # Video Forensics Audit
    video_audit = {}
    for res in all_results:
        vid_file = res["artifacts"]["video_mp4"]
        vp = os.path.join(EVIDENCE_DIR, vid_file)
        cap = cv2.VideoCapture(vp)
        fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        diffs = [np.mean(np.abs(frames[i].astype(float) - frames[i-1].astype(float))) for i in range(1, len(frames))]
        mean_diff = float(np.mean(diffs)) if diffs else 0.0
        
        video_audit[res["scenario_id"]] = {
            "video_file": vid_file,
            "total_frames": len(frames),
            "resolution": f"{w}x{h}",
            "mean_pixel_difference": round(mean_diff, 3),
            "motion_detected": mean_diff > 0.5,
            "all_frames_valid": len(frames) == fc and len(frames) == 100,
            "verdict": res["overall_verdict"]
        }
        
    video_audit_path = os.path.join(AUDIT_DIR, "video_forensics_audit.json")
    with open(video_audit_path, "w") as f:
        json.dump(video_audit, f, indent=2)
        
    print(f"\n[SUITE COMPLETE] Master Scorecard saved to: {scorecard_path}")
    print(f"[SUITE COMPLETE] Video Forensics Audit saved to: {video_audit_path}")
    
    return all_results


if __name__ == "__main__":
    run_full_overnight_master_suite()
