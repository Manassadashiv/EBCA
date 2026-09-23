"""
tests/render_stage3_4R_videos.py — High-Definition Video Demonstration for Stage 3.4-R
Classification: [STAGE 3.4-R VIDEO EVIDENCE GENERATOR]

Produces 2 Authoritative 720p (1280x720, 30 FPS) Demonstration Videos:
1. video_turning_bay_escape.mp4:
   Side-by-side composite: 3D Tracking / POV View + Occupancy Entropy / Deliberation Dashboard.
   Demonstrates ARM-A discovery of complete reversal -> turning bay pivot -> corridor egress.
2. video_tjunction_epistemic_showdown.mp4:
   Synchronized side-by-side comparison at Asymmetric T-Junction:
   Left: ARM-B (Pragmatic-Only Baseline) -> Entrapment in dead-end pocket
   Right: ARM-A (Frontier Active Inference) -> Selection of open arena
"""

import sys
import math
from pathlib import Path
import numpy as np
import cv2
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

VIDEOS_DIR = repo_root / "evidence" / "stage3_4R" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR = Path("C:/Users/MANAS/.gemini/antigravity-ide/brain/70ce1824-88d3-4886-8215-ae84fa5df454")

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"


def render_telemetry_panel(
    width: int,
    height: int,
    tick: int,
    arm: str,
    action: np.ndarray,
    v_wheel: float,
    heading_deg: float,
    phi_frontier: float,
    outcome_str: str,
    occ_grid: np.ndarray = None,
    robot_pose: np.ndarray = None
) -> np.ndarray:
    """
    Renders a high-contrast scientific telemetry dashboard (640x720).
    """
    panel = np.zeros((height, width, 3), dtype=np.uint8)
    panel[:] = (24, 24, 24)

    # Header Box
    cv2.rectangle(panel, (15, 15), (width - 15, 80), (38, 38, 38), -1)
    cv2.rectangle(panel, (15, 15), (width - 15, 80), (70, 70, 70), 1)
    cv2.putText(panel, "CARL-DX COGNITIVE TELEMETRY", (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    cv2.putText(panel, f"Arm: {arm} | Step: {tick:03d} (dt=0.030s)", (25, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 180, 180), 1)

    # Mini Map
    map_size = 280
    map_top = 95
    map_left = (width - map_size) // 2
    cv2.rectangle(panel, (map_left - 2, map_top - 2), (map_left + map_size + 2, map_top + map_size + 2), (60, 60, 60), 1)

    if occ_grid is not None:
        occ_norm = np.clip(occ_grid * 255.0, 0, 255).astype(np.uint8)
        occ_color = cv2.applyColorMap(occ_norm, cv2.COLORMAP_VIRIDIS)
        occ_resized = cv2.resize(occ_color, (map_size, map_size), interpolation=cv2.INTER_NEAREST)
        panel[map_top:map_top + map_size, map_left:map_left + map_size] = occ_resized

        if robot_pose is not None:
            rx = int(np.clip((robot_pose[0] + 1.5) / 3.0 * map_size, 0, map_size - 1)) + map_left
            ry = int(np.clip((1.5 - robot_pose[1]) / 3.0 * map_size, 0, map_size - 1)) + map_top
            cv2.circle(panel, (rx, ry), 5, (0, 0, 255), -1)
            cv2.circle(panel, (rx, ry), 6, (255, 255, 255), 1)

    # Telemetry Bars
    bar_top = 400
    row_h = 36

    # Action Left
    cv2.putText(panel, f"u_L: {action[0]:+5.2f}", (30, bar_top), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
    bx = int(np.clip((action[0] + 1.0) / 2.0 * 200, 0, 200))
    cv2.rectangle(panel, (150, bar_top - 14), (350, bar_top + 2), (45, 45, 45), -1)
    cv2.rectangle(panel, (250, bar_top - 14), (150 + bx, bar_top + 2), (0, 165, 255), -1)

    # Action Right
    cv2.putText(panel, f"u_R: {action[1]:+5.2f}", (30, bar_top + row_h), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
    bx_r = int(np.clip((action[1] + 1.0) / 2.0 * 200, 0, 200))
    cv2.rectangle(panel, (150, bar_top + row_h - 14), (350, bar_top + row_h + 2), (45, 45, 45), -1)
    cv2.rectangle(panel, (250, bar_top + row_h - 14), (150 + bx_r, bar_top + row_h + 2), (0, 165, 255), -1)

    # Wheel Speed
    cv2.putText(panel, f"v_wheel: {v_wheel:+5.2f} m/s", (30, bar_top + 2 * row_h), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

    # Heading
    cv2.putText(panel, f"Heading: {heading_deg:5.1f} deg", (30, bar_top + 3 * row_h), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

    # Frontier Progress
    cv2.putText(panel, f"Frontier Pot: {phi_frontier:+5.2f}", (30, bar_top + 4 * row_h), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 255, 100), 1)

    # Status Box
    status_bg = (40, 70, 40) if "ESCAPED" in outcome_str else ((40, 40, 80) if "COLLISION" in outcome_str else (50, 50, 50))
    cv2.rectangle(panel, (20, height - 70), (width - 20, height - 20), status_bg, -1)
    cv2.rectangle(panel, (20, height - 70), (width - 20, height - 20), (100, 100, 100), 1)
    cv2.putText(panel, f"STATE: {outcome_str}", (35, height - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    return panel


def render_video_turning_bay():
    """
    Renders 720p demonstration of complete turning bay escape (ARM-A).
    """
    out_path = VIDEOS_DIR / "video_turning_bay_escape.mp4"
    print(f"Rendering {out_path.name}...")

    hal = CarlStage1HAL(xml_path=str(ENV1_XML))
    controller = CARLActiveInferenceEngine(grid_path=str(ENV1_GRID), w_info=1.0, lambda_frontier=8.0)

    # Spawn configuration 0: x=0.50, y=0.0, th=0.0
    spawn_x, spawn_y, spawn_yaw = 0.50, 0.00, 0.00
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [spawn_x, spawn_y]
    hal.data.qpos[qa+3:qa+7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    controller.initialize_pose(spawn_x, spawn_y, spawn_yaw)

    # Setup offscreen camera renderer
    renderer = mujoco.Renderer(hal.model, height=720, width=640)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(out_path), fourcc, 30.0, (1280, 720))

    v_est = 0.0
    outcome_str = "ACTIVE INFERENCE ENGAGED"

    for tick in range(160):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])

        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)

        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])
        hal.step(cmd_6d)

        # Get robot position and camera view
        q_curr = hal.data.qpos[qa:qa+7]
        curr_pos = np.array([float(q_curr[0]), float(q_curr[1])])
        curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        heading_deg = math.degrees(curr_yaw)

        # Render 3D view
        renderer.update_scene(hal.data, camera="eye_cam")
        frame_cam = renderer.render()
        frame_bgr = cv2.cvtColor(frame_cam, cv2.COLOR_RGB2BGR)

        w_l_id = hal.model.sensor("sens_vel_w_left").id
        w_r_id = hal.model.sensor("sens_vel_w_right").id
        w_left_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
        w_right_vel = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
        wheel_spd = 0.5 * (w_left_vel + w_right_vel) * 0.048

        # Check outcome
        if curr_pos[0] <= -0.55:
            outcome_str = "SUCCESSFUL COMPLETE ESCAPE"
        elif wheel_spd < -0.05:
            outcome_str = "REVERSING TOWARD TURNING BAY"
        elif abs(heading_deg) > 90.0:
            outcome_str = "PIVOTING & EGRESSING"

        telem_panel = render_telemetry_panel(
            width=640, height=720, tick=tick, arm="ARM-A", action=action,
            v_wheel=wheel_spd, heading_deg=heading_deg, phi_frontier=float(telem.get("mean_epistemic", 0.0)),
            outcome_str=outcome_str, occ_grid=controller.grid_np[1], robot_pose=curr_pos
        )

        composite = np.hstack([frame_bgr, telem_panel])
        out_writer.write(composite)

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        if curr_pos[0] <= -0.55:
            # Hold final frame for 1 second
            for _ in range(30):
                out_writer.write(composite)
            break

    out_writer.release()
    print(f"Rendered {out_path} ({out_path.stat().st_size} bytes)")
    if BRAIN_DIR.exists():
        import shutil
        shutil.copy2(out_path, BRAIN_DIR / out_path.name)


def render_video_tjunction_showdown():
    """
    Renders synchronized 720p comparison video at Asymmetric T-Junction:
    ARM-B (Pragmatic-Only) on Left vs ARM-A (Frontier Active Inference) on Right.
    """
    out_path = VIDEOS_DIR / "video_tjunction_epistemic_showdown.mp4"
    print(f"Rendering {out_path.name}...")

    # Load T-junction models for both arms
    hal_b = CarlStage1HAL(xml_path=str(ENV2_XML))
    ctrl_b = CARLActiveInferenceEngine(grid_path=str(ENV2_GRID), w_info=0.0, lambda_frontier=8.0)

    hal_a = CarlStage1HAL(xml_path=str(ENV2_XML))
    ctrl_a = CARLActiveInferenceEngine(grid_path=str(ENV2_GRID), w_info=1.0, lambda_frontier=8.0)

    sx, sy, syaw = -0.45, 0.00, 0.00

    for hal, ctrl in [(hal_b, ctrl_b), (hal_a, ctrl_a)]:
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
        mujoco.mj_forward(hal.model, hal.data)
        ctrl.initialize_pose(sx, sy, syaw)

    renderer_b = mujoco.Renderer(hal_b.model, height=720, width=640)
    renderer_a = mujoco.Renderer(hal_a.model, height=720, width=640)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(out_path), fourcc, 30.0, (1280, 720))

    v_est_b = 0.0
    v_est_a = 0.0

    qa = int(hal_b.model.joint("spatial_identity").qposadr[0])

    for tick in range(150):
        # Step B
        s_b = hal_b.read_sensors()
        ctrl_b.update_odometry(v_wheel=v_est_b, w_gyro=float(s_b[20]), dt=0.030)
        act_b, _ = ctrl_b.select_action(s_b[:15], curr_v=v_est_b, curr_w=float(s_b[20]))
        cmd_b = np.zeros(6, dtype=np.float64); cmd_b[0] = float(act_b[0]); cmd_b[1] = float(act_b[1])
        hal_b.step(cmd_b)
        v_est_b = 0.70 * v_est_b + 0.30 * (0.5 * (cmd_b[0] + cmd_b[1]) * 0.30)

        # Step A
        s_a = hal_a.read_sensors()
        ctrl_a.update_odometry(v_wheel=v_est_a, w_gyro=float(s_a[20]), dt=0.030)
        act_a, _ = ctrl_a.select_action(s_a[:15], curr_v=v_est_a, curr_w=float(s_a[20]))
        cmd_a = np.zeros(6, dtype=np.float64); cmd_a[0] = float(act_a[0]); cmd_a[1] = float(act_a[1])
        hal_a.step(cmd_a)
        v_est_a = 0.70 * v_est_a + 0.30 * (0.5 * (cmd_a[0] + cmd_a[1]) * 0.30)

        # Render Left: ARM-B
        renderer_b.update_scene(hal_b.data, camera="eye_cam")
        frame_b = cv2.cvtColor(renderer_b.render(), cv2.COLOR_RGB2BGR)
        cv2.rectangle(frame_b, (20, 20), (620, 70), (0, 0, 0), -1)
        cv2.putText(frame_b, "ARM-B: Pragmatic-Only (w_info=0.0)", (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 100, 255), 2)

        # Render Right: ARM-A
        renderer_a.update_scene(hal_a.data, camera="eye_cam")
        frame_a = cv2.cvtColor(renderer_a.render(), cv2.COLOR_RGB2BGR)
        cv2.rectangle(frame_a, (20, 20), (620, 70), (0, 0, 0), -1)
        cv2.putText(frame_a, "ARM-A: Frontier Active Inf (w_info=1.0)", (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 255, 100), 2)

        composite = np.hstack([frame_b, frame_a])
        out_writer.write(composite)

    out_writer.release()
    print(f"Rendered {out_path} ({out_path.stat().st_size} bytes)")
    if BRAIN_DIR.exists():
        import shutil
        shutil.copy2(out_path, BRAIN_DIR / out_path.name)


def render_all_videos():
    print("Rendering Stage 3.4-R Demonstration Videos...")
    render_video_turning_bay()
    render_video_tjunction_showdown()
    print("All Stage 3.4-R demonstration videos rendered.")


if __name__ == "__main__":
    render_all_videos()
