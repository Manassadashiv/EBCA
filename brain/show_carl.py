import mujoco
import mujoco.viewer
import numpy as np
import os as _os
_FILE_DIR = _os.path.dirname(_os.path.abspath(__file__))
BASE_DIR = _os.path.dirname(_FILE_DIR)


def show_carl():
    xml_path = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
    print(f"Loading model from {xml_path}...")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)
    
    # Position CARL in the center of the arena
    q_addr = int(model.joint("spatial_identity").qposadr[0])
    data.qpos[q_addr : q_addr+3] = [0.0, 0.0, 0.05]
    
    # Position targets close to CARL so we can see them
    model.geom_pos[model.geom("food").id] = [0.5, 0.5, 0.12]
    model.geom_pos[model.geom("obstacle").id] = [-0.8, 0.6, 0.45]
    model.geom_pos[model.geom("obstacle_glow").id] = [-0.8, 0.6, 0.904]
    model.geom_pos[model.geom("predator").id] = [0.0, -0.6, 0.15]
    model.geom_pos[model.geom("predator_glow").id] = [0.0, -0.6, 0.46]
    
    # Update kinematics
    mujoco.mj_forward(model, data)
    
    print("\n========================================================")
    print("Launching MuJoCo 3D Interactive Viewer!")
    print("--------------------------------------------------------")
    print("Controls:")
    print(" - Left Click + Drag: Rotate Camera")
    print(" - Right Click + Drag: Pan Camera")
    print(" - Scroll Wheel: Zoom In/Out")
    print(" - Double Click on Object: Focus Camera on Object")
    print(" - Spacebar: Pause/Resume Physics")
    print("========================================================\n")
    
    mujoco.viewer.launch(model, data)

if __name__ == '__main__':
    show_carl()
