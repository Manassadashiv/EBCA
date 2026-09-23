"""
run_carl_showcase.py — Interactive 3D Showcase Launcher for CARL-DX Cyber-Companion

Features:
1. Live 3D MuJoCo Viewer with smooth third-person camera auto-tracking.
2. Real-time on-screen HUD telemetry overlay (Endocrine status, Battery, Behavior Mode, HDC thoughts).
3. Expressive procedural audio synthesis (Wall-E / R2-D2 chattering, food trills, alarm chirps).
4. Interactive Mouse Laser Pointer (point anywhere in arena for CARL to visually lock-on and follow).
5. Background CLI command prompt: type directives ("food", "dance", "laser", "guard", "sleep", "hop") live!
"""

import os
import sys
import math
import time
import threading
import numpy as np
import mujoco
import mujoco.viewer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from carl_simulation import CarlSimulationRunner


def interactive_command_listener(runner: CarlSimulationRunner):
    """Background console prompt enabling live typed directives without interrupting 3D rendering."""
    print("\n" + "═"*60)
    print("  [CARL-DX INTERACTIVE COMMAND TERMINAL]")
    print("  Type any command and press ENTER:")
    print("    • 'food'   -> Order CARL to forage green food beacon")
    print("    • 'laser'  -> Activate interactive laser tracking mode")
    print("    • 'dance'  -> Trigger happy celebration wiggle & trills")
    print("    • 'jump'   -> Trigger energetic torque-pop lunge")
    print("    • 'guard'  -> Trigger defensive alert posture")
    print("    • 'sleep'  -> Trigger low-power rest & consolidation")
    print("    • 'exit'   -> Terminate showcase")
    print("═"*60 + "\n")

    while True:
        try:
            line = input("CARL-COMMAND >> ").strip()
            if not line:
                continue
            if line.lower() in ["exit", "quit"]:
                print("[SHOWCASE] Exiting simulation...")
                break
            runner.command_interface.send_command(line)
        except (EOFError, KeyboardInterrupt):
            break


def main():
    print("\n" + "="*64)
    print("  CARL-DX: EMBODIED CYBER-COMPANION SHOWCASE LAUNCHER")
    print("="*64)

    runner = CarlSimulationRunner(open_space=False, headless=False)
    
    # Start non-blocking console command listener thread
    cmd_thread = threading.Thread(target=interactive_command_listener, args=(runner,), daemon=True)
    cmd_thread.start()

    # Configure MuJoCo 3D Viewer Camera tracking
    camera = runner.hal.viewer.cam
    camera.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    deck_id = mujoco.mj_name2id(runner.hal.model, mujoco.mjtObj.mjOBJ_BODY, "drive_deck")
    if deck_id >= 0:
        camera.trackbodyid = deck_id
    camera.distance = 2.2
    camera.elevation = -22.0
    camera.azimuth = 135.0

    print("[SHOWCASE] 3D Simulation active at 30 Hz. Enjoy interacting with CARL!")

    control_period = 1.0 / 30.0
    next_control_time = time.time()

    def sync_viewer_overlays():
        if runner.hal.viewer and runner.hal.viewer.is_running():
            runner.hal.viewer.user_scn.ngeom = 0
            for p1, p2, hit in runner.hal.lidar_rays:
                if runner.hal.viewer.user_scn.ngeom >= runner.hal.viewer.user_scn.maxgeom:
                    break
                color = np.array([1, 0, 0, 1]) if hit else np.array([0, 1, 0.5, 0.4])
                mujoco.mjv_initGeom(
                    runner.hal.viewer.user_scn.geoms[runner.hal.viewer.user_scn.ngeom],
                    mujoco.mjtGeom.mjGEOM_LINE, np.zeros(3),
                    np.zeros(3), np.zeros(9), color
                )
                mujoco.mjv_connector(
                    runner.hal.viewer.user_scn.geoms[runner.hal.viewer.user_scn.ngeom],
                    mujoco.mjtGeom.mjGEOM_LINE, 2,
                    np.array(p1), np.array(p2)
                )
                runner.hal.viewer.user_scn.ngeom += 1
            runner.hal.viewer.sync()

    try:
        while runner.hal.viewer.is_running():
            loop_start = time.time()
            if loop_start >= next_control_time:
                runner.step(step_physics=True)
                sync_viewer_overlays()
                next_control_time += control_period
            else:
                time.sleep(0.001)
    except KeyboardInterrupt:
        print("\n[SHOWCASE] Closing...")
    finally:
        runner.gis.save_state(
            reservoir=runner.reservoir,
            hippocampus=runner.hippocampus,
            physarum=runner.physarum,
            cig=runner.cig,
            hdc=runner.hdc,
            stats={"current_tick": runner.current_tick, "food_eaten": runner.food_eaten_total}
        )
        print("[SHOWCASE] Cognitive memory state saved atomically.")


if __name__ == '__main__':
    main()
