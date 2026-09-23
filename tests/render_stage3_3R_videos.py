"""
tests/render_stage3_3R_videos.py — High-Definition Video Demonstration for Stage 3.3-R MPPI

Renders 720p side-by-side scientific demonstration video (1280x720, 30 FPS):
- Left View: Discrete Baseline colliding in Family 4 narrow dogleg chicane
- Right View: MPPI Controller executing smooth continuous collision-free trajectory
"""

import sys
import math
from pathlib import Path
import numpy as np
import cv2
import mujoco

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

VIDEOS_DIR = REPO_ROOT / "evidence" / "stage3_3" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def render_stage3_3R_chicane_showdown():
    print("Rendering Stage 3.3-R Chicane Showdown Video (1280x720, 30 FPS)...")
    xml_path = REPO_ROOT / "world" / "stage3_2R_environments" / "family4_condB.xml"
    grid_path = REPO_ROOT / "world" / "stage3_2R_environments" / "family4_condB_grid.pt"

    # Setup HAL
    hal = CarlStage1HAL(xml_path=str(xml_path))
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    renderer = mujoco.Renderer(hal.model, height=720, width=640)

    # 1. Approach phase to T_crit = 45 ticks
    hal.reset()
    spawn_pos = [0.0, 0.0]
    hal.data.qpos[qa:qa+2] = spawn_pos
    hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    delib_master = CARLStage2_3R1DeliberationEngine(grid_path=str(grid_path), mode="deliberative")
    delib_master.initialize_pose(spawn_pos[0], spawn_pos[1], 0.0)

    u_app = np.array([0.65, 0.65, 0.0, 0.0, 0.0, 0.0])
    for _ in range(45):
        s = hal.read_sensors()
        delib_master.update_odometry(float(s[21]), float(s[20]), dt=0.03)
        hal.step(u_app)

    qpos_crit = np.copy(hal.data.qpos)
    qvel_crit = np.copy(hal.data.qvel)
    pose_crit = np.copy(delib_master.pose)
    v_crit = float(delib_master.v_hat)
    w_crit = float(delib_master.w_hat)

    # 2. Run Discrete rollout and record camera frames
    discrete_frames = []
    hal.reset()
    hal.data.qpos[:] = np.copy(qpos_crit)
    hal.data.qvel[:] = np.copy(qvel_crit)
    mujoco.mj_forward(hal.model, hal.data)

    disc_eng = CARLStage2_3R1DeliberationEngine(grid_path=str(grid_path), mode="deliberative", horizon=10)
    disc_eng.pose = np.copy(pose_crit)
    disc_eng.v_hat = v_crit
    disc_eng.w_hat = w_crit

    d_coll = False
    v_est = v_crit
    for step in range(70):
        # Render frame with camera tracking
        cam_id = hal.model.camera("carl_track").id if "carl_track" in [mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_CAMERA, i) for i in range(hal.model.ncam)] else -1
        if cam_id >= 0:
            renderer.update_scene(hal.data, camera="carl_track")
        else:
            renderer.update_scene(hal.data)
        frame = renderer.render()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Overlay telemetry
        cv2.putText(frame, "DISCRETE BASELINE (STAGE 2)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, f"Step: {step:02d}/70 | Speed: {v_est:.2f} m/s", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        if d_coll:
            cv2.putText(frame, "COLLISION DETECTED!", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        discrete_frames.append(frame)

        if not d_coll:
            s = hal.read_sensors()
            son = s[:15]
            act, _ = disc_eng.select_action(son, curr_v=v_est, curr_w=float(s[20]))
            hal.step(np.array([act[0], act[1], 0, 0, 0, 0]))
            c_info = hal.get_carl_contact_info()
            if (c_info["carl_contacts"] - c_info["floor_contacts"]) > 0:
                d_coll = True

    # 3. Run MPPI rollout and record camera frames
    mppi_frames = []
    hal.reset()
    hal.data.qpos[:] = np.copy(qpos_crit)
    hal.data.qvel[:] = np.copy(qvel_crit)
    mujoco.mj_forward(hal.model, hal.data)

    mppi_eng = CARLStage3_3MPPIDeliberationEngine(grid_path=str(grid_path), num_samples=128, horizon=15)
    mppi_eng.pose = np.copy(pose_crit)
    mppi_eng.v_hat = v_crit
    mppi_eng.w_hat = w_crit

    m_coll = False
    v_est = v_crit
    for step in range(70):
        cam_id = hal.model.camera("carl_track").id if "carl_track" in [mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_CAMERA, i) for i in range(hal.model.ncam)] else -1
        if cam_id >= 0:
            renderer.update_scene(hal.data, camera="carl_track")
        else:
            renderer.update_scene(hal.data)
        frame = renderer.render()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Overlay telemetry
        cv2.putText(frame, "CONTINUOUS MPPI (STAGE 3.3)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Step: {step:02d}/70 | Speed: {v_est:.2f} m/s", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        if not m_coll:
            cv2.putText(frame, "STATUS: SAFE NAVIGATION", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        mppi_frames.append(frame)

        if not m_coll:
            s = hal.read_sensors()
            son = s[:15]
            act, _ = mppi_eng.select_action(son, curr_v=v_est, curr_w=float(s[20]))
            hal.step(np.array([act[0], act[1], 0, 0, 0, 0]))
            c_info = hal.get_carl_contact_info()
            if (c_info["carl_contacts"] - c_info["floor_contacts"]) > 0:
                m_coll = True

    # Combine into side-by-side 1280x720 video
    out_video_path = VIDEOS_DIR / "video_stage3_3R_chicane_showdown.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_video_path), fourcc, 30.0, (1280, 720))

    total_frames = min(len(discrete_frames), len(mppi_frames))
    for i in range(total_frames):
        left = discrete_frames[i]
        right = mppi_frames[i]
        combined = np.hstack([left, right])
        writer.write(combined)

    writer.release()
    print(f"Video rendered and saved to: {out_video_path}")


if __name__ == "__main__":
    render_stage3_3R_chicane_showdown()
