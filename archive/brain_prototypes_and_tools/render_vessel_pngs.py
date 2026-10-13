"""
render_vessel_pngs.py — High-Resolution Offscreen Rendering for CARL-DX Cyber-Companion

Generates:
1. pngs/carl_cyber_companion_vessel.png (Close-up 3D perspective hero shot of CARL-DX)
2. pngs/arena_environment_setup.png (Top-down / isometric view of the arena and maze)
"""

import os
import sys
import numpy as np
import mujoco
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

PNG_DIR = os.path.join(BASE_DIR, "pngs")
os.makedirs(PNG_DIR, exist_ok=True)

xml_path = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
model = mujoco.MjModel.from_xml_path(xml_path)
for i in range(model.ngeom):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i)
    if name and name.startswith("lwall_"):
        model.geom_pos[i] = [99.0, 99.0, -99.0]
data = mujoco.MjData(model)

# Forward kinematics to settle onto caster
mujoco.mj_step(model, data)

# 1. Close-up 3D Hero Perspective of CARL-DX
renderer = mujoco.Renderer(model, height=720, width=960)

q_addr = int(model.joint("spatial_identity").qposadr[0])
data.qpos[q_addr : q_addr+3] = [0.0, 0.0, 0.055]
data.qpos[q_addr+3 : q_addr+7] = [1.0, 0.0, 0.0, 0.0]
mujoco.mj_forward(model, data)

deck_pos = data.xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "drive_deck")]

camera = mujoco.MjvCamera()
camera.type = mujoco.mjtCamera.mjCAMERA_FREE
camera.fixedcamid = -1
camera.lookat[:] = [0.0, 0.0, 0.15]
camera.distance = 1.20
camera.azimuth = 135
camera.elevation = -25

renderer.update_scene(data, camera=camera)
hero_rgb = renderer.render()
hero_img = Image.fromarray(hero_rgb)
hero_path = os.path.join(PNG_DIR, "carl_cyber_companion_vessel.png")
hero_img.save(hero_path)
print(f"[RENDER] Saved close-up hero shot to {hero_path}")

# 2. Arena & Environment Overview Shot
camera_arena = mujoco.MjvCamera()
camera_arena.type = mujoco.mjtCamera.mjCAMERA_FREE
camera_arena.fixedcamid = -1
camera_arena.lookat[:] = [0.0, 0.0, 0.2]
camera_arena.distance = 8.5
camera_arena.azimuth = 45
camera_arena.elevation = -42

renderer.update_scene(data, camera=camera_arena)
arena_rgb = renderer.render()
arena_img = Image.fromarray(arena_rgb)
arena_path = os.path.join(PNG_DIR, "arena_environment_setup.png")
arena_img.save(arena_path)
print(f"[RENDER] Saved arena environment setup shot to {arena_path}")
