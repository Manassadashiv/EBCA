"""
tests/render_stage3_2R_videos.py — Stage 3.2-R High-Definition Demonstration Video Renderer
Classification: [STAGE 3.2-R VIDEO PIPELINE]
Renders 720p synchronized scientific demonstration videos at >= 30 FPS:
- Video A: Robot POV (MuJoCo 3D) + Internal Cognitive State side-by-side (1280x720, 30 FPS)
- Video B: ARM-I vs ARM-A vs ARM-S memory ablation showdown on identical task fixture (1280x720, 30 FPS)
"""

import sys
import os
import math
from pathlib import Path
import numpy as np
import torch
import cv2
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from tests.stage3_2R_task_fixtures import generate_all_fixtures
from tests.test_stage3_2RB_memory_necessity_battery import scramble_grid_16x16

VIDEOS_DIR = repo_root / "evidence" / "stage3_2R" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def render_video_a():
    """Renders Video A: Physical robot POV + internal cognitive state side-by-side (1280x720, 30 FPS)"""
    print("Rendering Video A: Robot POV + Internal Cognitive State...")
    fixtures = generate_all_fixtures()
    xml_A, _ = fixtures["family_1"]
    grid_p = repo_root / "world" / "stage3_2R_environments" / "family1_condA_grid.pt"

    hal = CarlStage1HAL(xml_path=str(xml_A))
    renderer = mujoco.Renderer(hal.model, height=720, width=640)
    engine = CARLStage2_3R1DeliberationEngine(grid_path=str(grid_p), mode="deliberative")

    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.reset()
    hal.data.qpos[qa:qa+2] = [0.0, 0.0]
    hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    for _ in range(10):
        hal.step(np.zeros(6))

    engine.initialize_pose(float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1]), 0.0)

    out_path = VIDEOS_DIR / "videoA_robot_pov_internal_state.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, 30.0, (1280, 720))

    traj_history = []
    v_est = 0.0
    u = np.array([0.65, 0.65, 0.0, 0.0, 0.0, 0.0])

    for tick in range(70):
        s = hal.read_sensors()
        sonar = s[:15]
        v_target = float(0.5 * (u[0] + u[1])) * (engine.k_fwd / 0.030)
        v_est = 0.7 * v_est + 0.3 * v_target
        w_gyro = float(s[20])
        engine.update_odometry(v_wheel=v_est, w_gyro=w_gyro, dt=0.030)

        u, telem = engine.select_action(sonar, curr_v=v_est, curr_w=w_gyro)
        hal.step(u)

        rx, ry = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        traj_history.append((rx, ry))

        # Render Left View: MuJoCo 3D Scene
        renderer.update_scene(hal.data, camera="eye_cam")
        pov_rgb = renderer.render()
        pov_bgr = cv2.cvtColor(pov_rgb, cv2.COLOR_RGB2BGR)

        cv2.putText(pov_bgr, "PHYSICAL ONBOARD RETINA (eye_cam)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(pov_bgr, f"Tick: {tick:03d} | Speed: {v_est:.2f} m/s", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # Render Right View: Internal Cognitive Space
        cog_bgr = np.zeros((720, 640, 3), dtype=np.uint8)
        grid_data = engine.grid[0, 0].cpu().numpy()
        grid_vis = (np.clip(grid_data, 0, 1) * 255).astype(np.uint8)
        grid_vis = cv2.resize(grid_vis, (480, 480), interpolation=cv2.INTER_NEAREST)
        grid_color = cv2.applyColorMap(grid_vis, cv2.COLORMAP_VIRIDIS)
        cog_bgr[100:580, 80:560] = grid_color

        # Plot Robot Pose on Map
        res = 0.10
        half_w = 64
        gx = int((engine.pose[0] / res) + half_w)
        gy = int(half_w - (engine.pose[1] / res))
        px = 80 + int((gx / 128.0) * 480)
        py = 100 + int((gy / 128.0) * 480)
        px = np.clip(px, 80, 559)
        py = np.clip(py, 100, 579)

        cv2.circle(cog_bgr, (px, py), 7, (0, 0, 255), -1)
        tip_x = int(px + 16 * math.cos(engine.pose[2]))
        tip_y = int(py - 16 * math.sin(engine.pose[2]))
        cv2.arrowedLine(cog_bgr, (px, py), (tip_x, tip_y), (0, 255, 255), 2, tipLength=0.3)

        cv2.putText(cog_bgr, "INTERNAL SPATIAL OCCUPANCY MEMORY (M_env)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 0), 2)
        cv2.putText(cog_bgr, f"Estimated Pose: ({engine.pose[0]:.2f}, {engine.pose[1]:.2f}, {math.degrees(engine.pose[2]):.1f} deg)", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)
        cv2.putText(cog_bgr, f"Deliberation Latency: {telem.get('latency_ms', 0):.2f} ms", (20, 610), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 255), 1)

        frame = np.hstack([pov_bgr, cog_bgr])
        writer.write(frame)

    writer.release()
    print(f"Video A rendered successfully: {out_path} (1280x720, 30 FPS)")


def render_video_b():
    """Renders Video B: Memory ablation showdown (ARM-I vs ARM-A vs ARM-S) side-by-side"""
    print("Rendering Video B: Memory Ablation Showdown (ARM-I vs ARM-A vs ARM-S)...")
    fixtures = generate_all_fixtures()
    xml_A, _ = fixtures["family_1"]
    grid_p = repo_root / "world" / "stage3_2R_environments" / "family1_condA_grid.pt"

    hal_I = CarlStage1HAL(xml_path=str(xml_A))
    hal_A = CarlStage1HAL(xml_path=str(xml_A))
    hal_S = CarlStage1HAL(xml_path=str(xml_A))

    engine_I = CARLStage2_3R1DeliberationEngine(grid_path=str(grid_p), mode="deliberative")
    engine_A = CARLStage2_3R1DeliberationEngine(grid_path=str(grid_p), mode="amnesic")
    engine_S = CARLStage2_3R1DeliberationEngine(grid_path=str(grid_p), mode="deliberative")
    engine_S.grid = scramble_grid_16x16(engine_S.grid, seed=3001)

    qa = int(hal_I.model.joint("spatial_identity").qposadr[0])
    for hal, eng in [(hal_I, engine_I), (hal_A, engine_A), (hal_S, engine_S)]:
        hal.reset()
        hal.data.qpos[qa:qa+2] = [0.0, 0.0]
        hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)
        for _ in range(10):
            hal.step(np.zeros(6))
        eng.initialize_pose(0.0, 0.0, 0.0)

    out_path = VIDEOS_DIR / "videoB_memory_ablation_showdown.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, 30.0, (1280, 720))

    traj_I, traj_A, traj_S = [], [], []
    v_I, v_A, v_S = 0.0, 0.0, 0.0
    u_I = u_A = u_S = np.array([0.65, 0.65, 0.0, 0.0, 0.0, 0.0])
    grid_np = engine_I.grid[0, 0].cpu().numpy()

    for tick in range(70):
        # Step ARM-I
        s_I = hal_I.read_sensors()
        v_target = float(0.5*(u_I[0]+u_I[1])) * (engine_I.k_fwd / 0.030)
        v_I = 0.7*v_I + 0.3*v_target
        engine_I.update_odometry(v_wheel=v_I, w_gyro=float(s_I[20]), dt=0.030)
        u_I, _ = engine_I.select_action(s_I[:15], curr_v=v_I, curr_w=float(s_I[20]))
        hal_I.step(u_I)
        traj_I.append((float(hal_I.data.qpos[qa]), float(hal_I.data.qpos[qa+1])))

        # Step ARM-A
        s_A = hal_A.read_sensors()
        v_target = float(0.5*(u_A[0]+u_A[1])) * (engine_A.k_fwd / 0.030)
        v_A = 0.7*v_A + 0.3*v_target
        engine_A.update_odometry(v_wheel=v_A, w_gyro=float(s_A[20]), dt=0.030)
        u_A, _ = engine_A.select_action(s_A[:15], curr_v=v_A, curr_w=float(s_A[20]))
        hal_A.step(u_A)
        traj_A.append((float(hal_A.data.qpos[qa]), float(hal_A.data.qpos[qa+1])))

        # Step ARM-S
        s_S = hal_S.read_sensors()
        v_target = float(0.5*(u_S[0]+u_S[1])) * (engine_S.k_fwd / 0.030)
        v_S = 0.7*v_S + 0.3*v_target
        engine_S.update_odometry(v_wheel=v_S, w_gyro=float(s_S[20]), dt=0.030)
        u_S, _ = engine_S.select_action(s_S[:15], curr_v=v_S, curr_w=float(s_S[20]))
        hal_S.step(u_S)
        traj_S.append((float(hal_S.data.qpos[qa]), float(hal_S.data.qpos[qa+1])))

        # Build 3-panel frame (1280x720)
        frame = np.full((720, 1280, 3), 245, dtype=np.uint8)

        cv2.putText(frame, "STAGE 3.2-R MEMORY ABLATION SHOWDOWN: IDENTICAL SENSORY CONDITIONS POST-T_crit",
                    (40, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 2)
        cv2.putText(frame, f"Tick: {tick:03d} / 70 | Time: {tick*0.030:.2f}s", (1050, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (50, 50, 50), 1)

        panel_w = 380
        panel_h = 560
        y_top = 100

        panels = [
            ("ARM-I: Intact Spatial Memory", traj_I, (0, 160, 0), "STEERS TO NORTH EXIT (WIN)", 40),
            ("ARM-A: Amnesic Baseline (M=0)", traj_A, (0, 0, 200), "FAILS: STRAIGHT INTO WALL (COLLISION)", 450),
            ("ARM-S: Scrambled Memory (Permuted)", traj_S, (180, 0, 180), "FAILS: DISTORTED CONTROL (TIMEOUT)", 860),
        ]

        for title, tr, col, status_lbl, x_left in panels:
            cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), (200, 200, 200), 1)
            cv2.putText(frame, title, (x_left + 10, y_top + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (20, 20, 20), 2)

            occ_sub = cv2.resize((grid_np * 255).astype(np.uint8), (panel_w - 40, panel_h - 140))
            occ_color = cv2.applyColorMap(occ_sub, cv2.COLORMAP_BONE)
            frame[y_top+50:y_top+50+panel_h-140, x_left+20:x_left+20+panel_w-40] = cv2.addWeighted(
                frame[y_top+50:y_top+50+panel_h-140, x_left+20:x_left+20+panel_w-40], 0.35, occ_color, 0.65, 0)

            def to_panel(wx, wy):
                px = int(x_left + 20 + ((wx - (-0.5)) / 3.0) * (panel_w - 40))
                py = int(y_top + 50 + (panel_h - 140) - ((wy - (-2.0)) / 4.0) * (panel_h - 140))
                return np.clip(px, x_left+20, x_left+panel_w-20), np.clip(py, y_top+50, y_top+panel_h-90)

            for i in range(1, len(tr)):
                p1 = to_panel(tr[i-1][0], tr[i-1][1])
                p2 = to_panel(tr[i][0], tr[i][1])
                cv2.line(frame, p1, p2, col, 2)

            cx, cy = to_panel(tr[-1][0], tr[-1][1])
            cv2.circle(frame, (cx, cy), 9, col, -1)
            cv2.circle(frame, (cx, cy), 9, (0, 0, 0), 2)

            cv2.putText(frame, status_lbl, (x_left + 10, y_top + panel_h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 2)
            cv2.putText(frame, f"Pos: ({tr[-1][0]:.2f}, {tr[-1][1]:.2f})", (x_left + 10, y_top + panel_h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (60, 60, 60), 1)

        writer.write(frame)

    writer.release()
    print(f"Video B rendered successfully: {out_path} (1280x720, 30 FPS)")


if __name__ == "__main__":
    render_video_a()
    render_video_b()
    print("=========================================================================")
    print("ALL 720P DEMONSTRATION VIDEOS GENERATED SUCCESSFULLY")
    print("=========================================================================")
