import sys
import math
from pathlib import Path
import numpy as np
import mujoco

repo_root = Path(".").resolve()
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL

# Let's test a clean, enclosed Y-fork geometry for Family 2:
# Symmetrical branch angle = 45 deg (0.7854 rad)
# Width of approach = 0.80 m (y in [-0.40, 0.40])
# Width of each diagonal branch = 0.35 m

common_geoms = """
    <!-- Approach corridor (x in [-0.80, 0.0], y in [-0.40, 0.40]) -->
    <geom name="f2_app_n" type="box" size="0.40 0.05 0.25" pos="-0.40  0.425 0.25" material="wall_mat" />
    <geom name="f2_app_s" type="box" size="0.40 0.05 0.25" pos="-0.40 -0.425 0.25" material="wall_mat" />
    <geom name="f2_back"  type="box" size="0.05 0.45 0.25" pos="-0.80  0.000 0.25" material="wall_mat" />

    <!-- Center Divider Wedge splitting at +/-45 deg -->
    <!-- Apex at x=0.20, y=0.0 -->
    <geom name="f2_wedge_apex" type="box" size="0.10 0.05 0.25" pos="0.20 0.00 0.25" material="wall_mat" />
    <!-- North inner diagonal wall (euler: +45 deg) -->
    <geom name="f2_wedge_n" type="box" size="0.60 0.05 0.25" pos="0.75  0.40 0.25" euler="0 0 0.7854" material="wall_mat" />
    <!-- South inner diagonal wall (euler: -45 deg) -->
    <geom name="f2_wedge_s" type="box" size="0.60 0.05 0.25" pos="0.75 -0.40 0.25" euler="0 0 -0.7854" material="wall_mat" />

    <!-- Outer Diagonal Corridor Walls (enclosing 0.35m channel) -->
    <!-- North outer wall (euler: +45 deg) -->
    <geom name="f2_outer_n" type="box" size="0.75 0.05 0.25" pos="0.55  0.80 0.25" euler="0 0 0.7854" material="wall_mat" />
    <!-- South outer wall (euler: -45 deg) -->
    <geom name="f2_outer_s" type="box" size="0.75 0.05 0.25" pos="0.55 -0.80 0.25" euler="0 0 -0.7854" material="wall_mat" />
"""

geoms_A = common_geoms + """
    <!-- Condition A: North branch occluded dead-end cap at end of diagonal (x=1.35, y=1.60) -->
    <geom name="f2_dead_cap_n" type="box" size="0.25 0.05 0.25" pos="1.30 1.55 0.25" euler="0 0 -0.7854" material="wall_mat" />
    <!-- South branch open to exit -->
    <geom name="f2_exit_s" type="box" size="0.05 0.50 0.25" pos="2.00 -1.80 0.25" material="wall_mat" />
"""

geoms_B = common_geoms + """
    <!-- Condition B: South branch occluded dead-end cap at end of diagonal (x=1.35, y=-1.60) -->
    <geom name="f2_dead_cap_s" type="box" size="0.25 0.05 0.25" pos="1.30 -1.55 0.25" euler="0 0 0.7854" material="wall_mat" />
    <!-- North branch open to exit -->
    <geom name="f2_exit_n" type="box" size="0.05 0.50 0.25" pos="2.00 1.80 0.25" material="wall_mat" />
"""

base_xml = Path("world/clean_arena.xml").read_text()
import re
base_clean = re.sub(r'<geom name="food"[\s\S]*?<body name="drive_deck"', '<body name="drive_deck"', base_xml)

xml_A = base_clean.replace("</worldbody>", f"{geoms_A}\n</worldbody>")
xml_B = base_clean.replace("</worldbody>", f"{geoms_B}\n</worldbody>")

Path("world/stage3_2_environments/family2_condA.xml").write_text(xml_A)
Path("world/stage3_2_environments/family2_condB.xml").write_text(xml_B)

print("Wrote test XMLs. Testing observational equivalence at [0, 0]...")

hal_A = CarlStage1HAL(xml_path="world/stage3_2_environments/family2_condA.xml")
hal_B = CarlStage1HAL(xml_path="world/stage3_2_environments/family2_condB.xml")

s_A = hal_A.read_sensors()[:15]
s_B = hal_B.read_sensors()[:15]

d_sens = np.linalg.norm(s_A - s_B)
max_ray = np.max(np.abs(s_A - s_B))

print(f"D_sensory: {d_sens:.6f} m, Max Single Ray Diff: {max_ray:.6f} m")
print(f"Sonar A: {np.round(s_A, 3)}")
print(f"Sonar B: {np.round(s_B, 3)}")
