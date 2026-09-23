"""
carl_live_playground.py — Interactive Live MuJoCo 3D Playground for CARL-DX

Allows the user to watch CARL-DX live in MuJoCo's 3D GUI window as it explores
with free will, forages for food, plays with interactive physics toys/balls,
smoothly avoids walls, and responds to internal homeostatic drives (dopamine, curiosity, energy).

Usage:
    python carl_live_playground.py
"""

import sys
import os
import time
import math
import random
import numpy as np
import mujoco
import mujoco.viewer

# Add repo root to path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_ROOT)

from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent


class LivePlaygroundSimulation:
    def __init__(self, xml_path: str = "world/vessel_kinetic.xml"):
        full_xml_path = os.path.join(REPO_ROOT, xml_path)
        if not os.path.exists(full_xml_path):
            full_xml_path = os.path.join(REPO_ROOT, "world", "vessel_kinetic.xml")
            
        print(f"[PLAYGROUND] Loading MuJoCo World from: {full_xml_path}")
        self.model = mujoco.MjModel.from_xml_path(full_xml_path)
        self.data = mujoco.MjData(self.model)
        
        # Position fun interactive obstacles & items in arena
        self.setup_fun_playground()
        
        # Initial physics settle
        for _ in range(50):
            mujoco.mj_step(self.model, self.data)
            
        # Initialize Autonomous Cognitive Stack
        self.agent = CarlAutonomousOrganismAgent(dt=0.0333)
        
        # Food position state
        self.food_pos = np.array([2.5, 2.0])
        self.food_eaten_count = 0
        self.respawn_food()
        
    def setup_fun_playground(self):
        """Places obstacles, pushable balls/cubes, and open navigation spaces."""
        geom_names = {self.model.geom(i).name: i for i in range(self.model.ngeom)}
        body_names = {self.model.body(i).name: i for i in range(self.model.nbody)}
        
        # Open up central plaza and create side corridors
        if 'lwall_v_0_2' in geom_names:
            self.model.geom_pos[geom_names['lwall_v_0_2']] = [2.0, 3.2, 0.25]
        if 'lwall_v_2_0' in geom_names:
            self.model.geom_pos[geom_names['lwall_v_2_0']] = [-2.2, 1.0, 0.25]
        if 'lwall_v_2_2' in geom_names:
            self.model.geom_pos[geom_names['lwall_v_2_2']] = [-1.5, -2.5, 0.25]
        if 'lwall_v_3_1' in geom_names:
            self.model.geom_pos[geom_names['lwall_v_3_1']] = [2.5, -2.0, 0.25]
        if 'lwall_h_0_1' in geom_names:
            self.model.geom_pos[geom_names['lwall_h_0_1']] = [-2.0, 3.0, 0.25]
        if 'lwall_h_1_1' in geom_names:
            self.model.geom_pos[geom_names['lwall_h_1_1']] = [1.0, -1.0, 0.25]
            
        # Place pushable toys in arena
        if 'obj_cube_0' in body_names:
            self.model.body_pos[body_names['obj_cube_0']] = [1.2, 1.2, 0.05]
        if 'obj_cube_1' in body_names:
            self.model.body_pos[body_names['obj_cube_1']] = [-1.8, 1.8, 0.05]
        if 'obj_ball_0' in body_names:
            self.model.body_pos[body_names['obj_ball_0']] = [0.8, -1.5, 0.05]
            
        # Hazard cube gentle oscillation
        if 'hazard_cube' in body_names:
            self.model.body_pos[body_names['hazard_cube']] = [-2.8, -2.5, 0.15]

    def respawn_food(self):
        """Randomly respawns the glowing food beacon when CARL eats it."""
        spots = [
            np.array([2.2, 2.0]),
            np.array([-2.0, 2.2]),
            np.array([2.5, -1.8]),
            np.array([-1.5, -2.2]),
            np.array([0.0, 3.2]),
            np.array([0.0, -3.0]),
            np.array([3.0, 0.0]),
            np.array([-3.0, 0.0]),
        ]
        chosen = random.choice([s for s in spots if np.linalg.norm(s - self.food_pos) > 1.5])
        self.food_pos = chosen
        
        # Update food geom in MuJoCo
        food_gid = self.model.geom('food').id if 'food' in [self.model.geom(i).name for i in range(self.model.ngeom)] else -1
        if food_gid >= 0:
            self.model.geom_pos[food_gid] = [float(self.food_pos[0]), float(self.food_pos[1]), 0.12]

    def get_robot_pos(self):
        chassis_bid = self.model.body('drive_deck').id
        x = float(self.data.xpos[chassis_bid][0])
        y = float(self.data.xpos[chassis_bid][1])
        mat = self.data.xmat[chassis_bid].reshape(3, 3)
        yaw = float(math.atan2(mat[1, 0], mat[0, 0]))
        return x, y, yaw

    def get_obstacles_2d(self):
        """Returns 2D bounding boxes of all walls and hazards for raycasting."""
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


def run_live_interactive_playground():
    sim = LivePlaygroundSimulation()
    model = sim.model
    data = sim.data
    agent = sim.agent
    
    print("\n" + "="*80)
    print("       CARL-DX CYBER-COMPANION — INTERACTIVE 3D LIVE PLAYGROUND")
    print("="*80)
    print(" [CONTROLS in MuJoCo 3D Window]")
    print("   - Left Mouse Drag:   Rotate Camera Orbit")
    print("   - Right Mouse Drag:  Move / Pan Camera")
    print("   - Scroll Wheel:      Zoom In / Out")
    print("   - Right-Click Drag:  Interact & Drag Objects / CARL with Physics Force!")
    print("   - Spacebar:          Pause / Resume Physics")
    print("   - Backspace:         Reset Physics State")
    print("="*80 + "\n")
    
    tick = 0
    start_time = time.time()
    
    # Launch MuJoCo native passive viewer
    with mujoco.viewer.launch_passive(model, data) as viewer:
        # Default camera angle
        viewer.cam.distance = 7.5
        viewer.cam.elevation = -38.0
        viewer.cam.azimuth = 45.0
        viewer.cam.lookat = [0.0, 0.0, 0.5]
        
        while viewer.is_running():
            step_start = time.time()
            tick += 1
            
            # 1. Read Robot Pose
            rx, ry, ryaw = sim.get_robot_pos()
            
            # 2. Check Distance to Food
            dist_to_food = math.hypot(sim.food_pos[0] - rx, sim.food_pos[1] - ry)
            food_absorbed = (dist_to_food < 0.35)
            if food_absorbed:
                sim.food_eaten_count += 1
                sim.respawn_food()
                
            # 3. Step Cognitive Organism Cycle (reads proprioception, executes Active Inference, sets data.ctrl)
            telemetry = agent.step_cognitive_cycle(sim, food_coords=tuple(sim.food_pos))
            
            # 4. Physics Sub-stepping (3 physics sub-steps per 30Hz cognitive tick: 3 * 0.01s = 0.03s)
            for _ in range(3):
                mujoco.mj_step(model, data)
                
            # 5. Sync 3D Graphics Viewer
            viewer.sync()
            
            # 6. Live Terminal HUD (updates every 10 ticks = ~0.3s)
            if tick % 10 == 0:
                h_state = agent.homeostasis.state
                sensory = agent.last_sensory_state
                min_clear = sensory.min_obstacle_dist if sensory else 1.0
                front_clear = float(np.min(sensory.sonar_distances[5:10])) if (sensory is not None and sensory.sonar_distances is not None) else min_clear
                action_name = agent.last_action_name
                mood = agent.embodiment.affect_state
                
                print(f"\r[T={tick:04d} | {time.time()-start_time:4.1f}s] "
                      f"Pos:({rx:+4.2f},{ry:+4.2f}) | "
                      f"Mood: \033[1;36m{mood:15s}\033[0m | "
                      f"Action: \033[1;32m{action_name:20s}\033[0m | "
                      f"Clear: {min_clear:4.2f}m (Fwd:{front_clear:4.2f}m) | "
                      f"Energy: {h_state.energy*100:3.0f}% | "
                      f"Curiosity: {h_state.curiosity_drive:4.2f} | "
                      f"Eaten: \033[1;33m{sim.food_eaten_count:02d}\033[0m", end="", flush=True)
                
            # Maintain realistic 30 FPS timing
            elapsed = time.time() - step_start
            time_to_sleep = (1.0 / 30.0) - elapsed
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
                
    print("\n[PLAYGROUND] Viewer closed. Autonomous session complete.")


if __name__ == "__main__":
    run_live_interactive_playground()
