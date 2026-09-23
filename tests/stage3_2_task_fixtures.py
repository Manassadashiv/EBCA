"""
tests/stage3_2_task_fixtures.py — Stage 3.2 Non-LOS Task Family XML Generator & Fixtures
Classification: [STAGE 3.2 FIXTURE] Authoritative Task Geometries for Non-LOS Equivalence & Evaluation

Defines 5 genuine non-LOS task families satisfying observational equivalence:
- Family 1: Blind-Corner Distal-Connectivity Ambiguity
- Family 2: Irreversible Cul-de-Sac Funnel Trap (Redesigned with mechanical pinch & budget)
- Family 3: Sonically Symmetric Locations (P1 vs P2) with Divergent Optimal Actions
- Family 4: Occluded Dogleg Arterial vs Blind Detour (Redesigned with occluded doglegs)
- Family 5: Multi-Turn Sensory Blackout / Sonic Corridor Symmetry
"""

import os
import math
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np

repo_root = Path(__file__).resolve().parent.parent

BASE_XML_PATH = repo_root / "world" / "clean_arena.xml"
ENV_DIR = repo_root / "world" / "stage3_2_environments"
ENV_DIR.mkdir(parents=True, exist_ok=True)


import re

def get_base_xml_content() -> str:
    with open(BASE_XML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(r'<geom name="food"[\s\S]*?<body name="drive_deck"')
    return pattern.sub('<body name="drive_deck"', content)


def build_family1_xmls() -> Tuple[Path, Path]:
    """
    Family 1: Blind-Corner Distal-Connectivity Ambiguity.
    Symmetrical T-junction corridor: width 1.2m. Approach along +x.
    T-junction at x=0.80: Left runs along +y, Right runs along -y.
    Front wall at x=1.60.
    In A: Left connects to exit (+y to +4.0m); Right dead-ends behind corner at y=-2.2m.
    In B: Right connects to exit (-y to -4.0m); Left dead-ends behind corner at y=+2.2m.
    """
    base_xml = get_base_xml_content()

    common_geoms = """
    <!-- Family 1: Approach Corridor -->
    <geom name="f1_app_n" type="box" size="0.60 0.05 0.25" pos="-0.40  0.65 0.25" material="wall_mat" />
    <geom name="f1_app_s" type="box" size="0.60 0.05 0.25" pos="-0.40 -0.65 0.25" material="wall_mat" />
    <geom name="f1_app_back" type="box" size="0.05 0.70 0.25" pos="-1.00 0.00 0.25" material="wall_mat" />

    <!-- T-junction Front Wall -->
    <geom name="f1_front_wall" type="box" size="0.05 1.50 0.25" pos="1.60 0.00 0.25" material="wall_mat" />

    <!-- T-junction Corner Inner Baffles -->
    <geom name="f1_corner_n" type="box" size="0.05 0.60 0.25" pos="0.30  1.25 0.25" material="wall_mat" />
    <geom name="f1_corner_s" type="box" size="0.05 0.60 0.25" pos="0.30 -1.25 0.25" material="wall_mat" />
    """

    geoms_A = common_geoms + """
    <!-- Condition A: Occluded dead-end wall on Right branch (South) -->
    <geom name="f1_block_south" type="box" size="0.70 0.05 0.25" pos="0.95 -2.00 0.25" material="wall_mat" />
    <geom name="f1_outer_s" type="box" size="0.05 0.75 0.25" pos="1.60 -2.60 0.25" material="wall_mat" />
    <geom name="f1_exit_n" type="box" size="0.05 1.00 0.25" pos="1.60 2.80 0.25" material="wall_mat" />
    """

    geoms_B = common_geoms + """
    <!-- Condition B: Occluded dead-end wall on Left branch (North) -->
    <geom name="f1_block_north" type="box" size="0.70 0.05 0.25" pos="0.95 2.00 0.25" material="wall_mat" />
    <geom name="f1_outer_n" type="box" size="0.05 0.75 0.25" pos="1.60 2.60 0.25" material="wall_mat" />
    <geom name="f1_exit_s" type="box" size="0.05 1.00 0.25" pos="1.60 -2.80 0.25" material="wall_mat" />
    """

    path_A = ENV_DIR / "family1_condA.xml"
    path_B = ENV_DIR / "family1_condB.xml"

    xml_A = base_xml.replace("</worldbody>", f"{geoms_A}\n</worldbody>")
    xml_B = base_xml.replace("</worldbody>", f"{geoms_B}\n</worldbody>")

    with open(path_A, "w", encoding="utf-8") as f:
        f.write(xml_A)
    with open(path_B, "w", encoding="utf-8") as f:
        f.write(xml_B)

    return path_A, path_B


def build_family2_xmls() -> Tuple[Path, Path]:
    """
    Family 2: Irreversible Cul-de-Sac Funnel Trap (Enclosed mechanical funnel corridor).
    Symmetrical Y-fork branching at +/-45 deg:
    Approach corridor width 0.80m (y in [-0.40, 0.40]).
    Center divider wedge starting at x=0.20, branching at +/-45 deg.
    Continuous outer diagonal walls enclosing 0.35m wide channels (robot width 0.28m, length 0.44m).
    In A: North branch occluded dead-end cap at (1.30, 1.55). South branch open to exit.
    In B: South branch occluded dead-end cap at (1.30, -1.55). North branch open to exit.
    """
    base_xml = get_base_xml_content()

    common_geoms = """
    <!-- Family 2: Approach Corridor (x in [-0.80, 0.0], y in [-0.40, 0.40]) -->
    <geom name="f2_app_n" type="box" size="0.40 0.05 0.25" pos="-0.40  0.425 0.25" material="wall_mat" />
    <geom name="f2_app_s" type="box" size="0.40 0.05 0.25" pos="-0.40 -0.425 0.25" material="wall_mat" />
    <geom name="f2_back"  type="box" size="0.05 0.45 0.25" pos="-0.80  0.000 0.25" material="wall_mat" />

    <!-- Center Divider Wedge splitting at +/-45 deg -->
    <geom name="f2_wedge_apex" type="box" size="0.10 0.05 0.25" pos="0.20 0.00 0.25" material="wall_mat" />
    <geom name="f2_wedge_n" type="box" size="0.60 0.05 0.25" pos="0.75  0.40 0.25" euler="0 0 0.7854" material="wall_mat" />
    <geom name="f2_wedge_s" type="box" size="0.60 0.05 0.25" pos="0.75 -0.40 0.25" euler="0 0 -0.7854" material="wall_mat" />

    <!-- Outer Diagonal Corridor Walls (enclosing 0.35m channel) -->
    <geom name="f2_outer_n" type="box" size="0.75 0.05 0.25" pos="0.55  0.80 0.25" euler="0 0 0.7854" material="wall_mat" />
    <geom name="f2_outer_s" type="box" size="0.75 0.05 0.25" pos="0.55 -0.80 0.25" euler="0 0 -0.7854" material="wall_mat" />
    """

    geoms_A = common_geoms + """
    <!-- Condition A: North branch occluded dead-end cap at end of diagonal -->
    <geom name="f2_dead_cap_n" type="box" size="0.25 0.05 0.25" pos="1.30 1.55 0.25" euler="0 0 -0.7854" material="wall_mat" />
    <!-- South branch open to exit -->
    <geom name="f2_exit_s" type="box" size="0.05 0.50 0.25" pos="2.00 -1.80 0.25" material="wall_mat" />
    """

    geoms_B = common_geoms + """
    <!-- Condition B: South branch occluded dead-end cap at end of diagonal -->
    <geom name="f2_dead_cap_s" type="box" size="0.25 0.05 0.25" pos="1.30 -1.55 0.25" euler="0 0 0.7854" material="wall_mat" />
    <!-- North branch open to exit -->
    <geom name="f2_exit_n" type="box" size="0.05 0.50 0.25" pos="2.00 1.80 0.25" material="wall_mat" />
    """

    path_A = ENV_DIR / "family2_condA.xml"
    path_B = ENV_DIR / "family2_condB.xml"

    xml_A = base_xml.replace("</worldbody>", f"{geoms_A}\n</worldbody>")
    xml_B = base_xml.replace("</worldbody>", f"{geoms_B}\n</worldbody>")

    with open(path_A, "w", encoding="utf-8") as f:
        f.write(xml_A)
    with open(path_B, "w", encoding="utf-8") as f:
        f.write(xml_B)

    return path_A, path_B


def build_family3_xmls() -> Tuple[Path, Path]:
    """
    Family 3: Sonically Symmetric Locations (P1 vs P2).
    A symmetrical 4-way intersection maze where:
    Location P1 = (-1.5, 1.2) and Location P2 = (1.5, -1.8) have matched cross-sections.
    At P1: North is open arterial; East is closed occluded dead-end. (Correct action: Left).
    At P2: East is open arterial; North is closed occluded dead-end. (Correct action: Right/Straight).
    """
    base_xml = get_base_xml_content()

    def build_cross(cx, cy, prefix):
        return f"""
        <geom name="{prefix}_back" type="box" size="0.05 0.50 0.25" pos="{cx-0.60:.2f} {cy:.2f} 0.25" material="wall_mat" />
        <geom name="{prefix}_nw" type="box" size="0.30 0.05 0.25" pos="{cx-0.30:.2f} {cy+0.55:.2f} 0.25" material="wall_mat" />
        <geom name="{prefix}_sw" type="box" size="0.30 0.05 0.25" pos="{cx-0.30:.2f} {cy-0.55:.2f} 0.25" material="wall_mat" />
        <geom name="{prefix}_ne" type="box" size="0.30 0.05 0.25" pos="{cx+0.30:.2f} {cy+0.55:.2f} 0.25" material="wall_mat" />
        <geom name="{prefix}_se" type="box" size="0.30 0.05 0.25" pos="{cx+0.30:.2f} {cy-0.55:.2f} 0.25" material="wall_mat" />

        <!-- Symmetrical Corridor End Caps -->
        <geom name="{prefix}_cap_e" type="box" size="0.05 0.80 0.25" pos="{cx+1.20:.2f} {cy:.2f} 0.25" material="wall_mat" />
        <geom name="{prefix}_cap_n" type="box" size="0.80 0.05 0.25" pos="{cx:.2f} {cy+1.20:.2f} 0.25" material="wall_mat" />
        <geom name="{prefix}_cap_s" type="box" size="0.80 0.05 0.25" pos="{cx:.2f} {cy-1.20:.2f} 0.25" material="wall_mat" />

        <!-- Diagonal Corner Caps (catches +/-34.3 deg rays) -->
        <geom name="{prefix}_diag_ne" type="box" size="0.40 0.05 0.25" pos="{cx+1.10:.2f} {cy+1.10:.2f} 0.25" euler="0 0 -0.7854" material="wall_mat" />
        <geom name="{prefix}_diag_se" type="box" size="0.40 0.05 0.25" pos="{cx+1.10:.2f} {cy-1.10:.2f} 0.25" euler="0 0 0.7854" material="wall_mat" />
        """

    g1 = build_cross(-1.50, 1.20, "p1")
    g2 = build_cross( 1.50, -1.80, "p2")

    path = ENV_DIR / "family3_layout.xml"
    xml = base_xml.replace("</worldbody>", f"{g1}\n{g2}\n</worldbody>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)

    return path, path


def build_family4_xmls() -> Tuple[Path, Path]:
    """
    Family 4: Occluded Dogleg Arterial vs Blind Detour (Redesigned).
    Approach corridor along +x.
    Branch A: Straight forward +x extending 1.8m, then dogleg turn North.
    Branch B: Detour at +45 deg extending 1.8m, then dogleg turn South.
    At (0, 0): Both branches are straight and clear for >1.8m (beyond line-of-sight).
    In A: Branch A's dogleg dead-ends 0.6m beyond turn (x=2.3, y=1.2). Branch B's dogleg opens to goal.
    In B: Branch B's dogleg dead-ends 0.6m beyond turn. Branch A's dogleg opens to goal.
    """
    base_xml = get_base_xml_content()

    common_geoms = """
    <!-- Family 4: Approach Corridor (width 0.9m) -->
    <geom name="f4_app_s" type="box" size="0.50 0.05 0.25" pos="-0.30 -0.50 0.25" material="wall_mat" />
    <geom name="f4_app_n" type="box" size="0.50 0.05 0.25" pos="-0.30  0.50 0.25" material="wall_mat" />

    <!-- Branch A: Straight East Corridor Walls (open >1.8m) -->
    <geom name="f4_str_s" type="box" size="0.90 0.05 0.25" pos="1.10 -0.50 0.25" material="wall_mat" />
    <geom name="f4_div_w" type="box" size="0.60 0.05 0.25" pos="0.85  0.35 0.25" euler="0 0 0.7854" material="wall_mat" />

    <!-- Branch B: Detour Corridor Walls (open >1.8m) -->
    <geom name="f4_det_n" type="box" size="0.80 0.05 0.25" pos="0.90  1.35 0.25" euler="0 0 0.7854" material="wall_mat" />
    """

    geoms_A = common_geoms + """
    <!-- Condition A: Straight branch dogleg dead-end wall (occluded at x=2.1, y=0.8) -->
    <geom name="f4_block_straight" type="box" size="0.50 0.05 0.25" pos="2.10 0.80 0.25" material="wall_mat" />
    <geom name="f4_front_cap_A" type="box" size="0.05 0.50 0.25" pos="2.10 0.00 0.25" material="wall_mat" />
    <!-- Detour branch connects to open passage -->
    <geom name="f4_detour_exit_s" type="box" size="0.05 0.80 0.25" pos="1.80 2.20 0.25" material="wall_mat" />
    """

    geoms_B = common_geoms + """
    <!-- Condition B: Detour branch dogleg dead-end wall (occluded at x=1.8, y=2.2) -->
    <geom name="f4_block_detour" type="box" size="0.50 0.05 0.25" pos="1.80 2.20 0.25" material="wall_mat" />
    <!-- Straight branch connects to open passage -->
    <geom name="f4_straight_exit" type="box" size="0.80 0.05 0.25" pos="2.90 -0.50 0.25" material="wall_mat" />
    """

    path_A = ENV_DIR / "family4_condA.xml"
    path_B = ENV_DIR / "family4_condB.xml"

    xml_A = base_xml.replace("</worldbody>", f"{geoms_A}\n</worldbody>")
    xml_B = base_xml.replace("</worldbody>", f"{geoms_B}\n</worldbody>")

    with open(path_A, "w", encoding="utf-8") as f:
        f.write(xml_A)
    with open(path_B, "w", encoding="utf-8") as f:
        f.write(xml_B)

    return path_A, path_B


def build_family5_xmls() -> Tuple[Path, Path]:
    """
    Family 5: Multi-Turn Sensory Blackout / Sonic Corridor Symmetry.
    Symmetrical corridor intersection with alternating baffles where local sonar at decision point
    matches symmetrical perpendicular wall profiles.
    In A: Prior history turned Left; egress is Right.
    In B: Prior history turned Right; egress is Left.
    """
    base_xml = get_base_xml_content()

    geoms = """
    <!-- Family 5: Symmetrical Narrow Baffle Intersection -->
    <!-- Decision point at (0, 0), facing East -->
    <geom name="f5_left_baffle1" type="box" size="0.05 0.40 0.25" pos="-0.40  0.70 0.25" material="wall_mat" />
    <geom name="f5_right_baffle1" type="box" size="0.05 0.40 0.25" pos="-0.40 -0.70 0.25" material="wall_mat" />

    <geom name="f5_left_corridor" type="box" size="0.50 0.05 0.25" pos="0.20  0.60 0.25" material="wall_mat" />
    <geom name="f5_right_corridor" type="box" size="0.50 0.05 0.25" pos="0.20 -0.60 0.25" material="wall_mat" />

    <!-- Symmetrical Perpendicular Baffles at Junction -->
    <geom name="f5_left_baffle2" type="box" size="0.05 0.50 0.25" pos="0.80  1.00 0.25" material="wall_mat" />
    <geom name="f5_right_baffle2" type="box" size="0.05 0.50 0.25" pos="0.80 -1.00 0.25" material="wall_mat" />

    <!-- Front Symmetrical Obstacle Array -->
    <geom name="f5_front_obs" type="box" size="0.10 0.30 0.25" pos="1.50 0.00 0.25" material="wall_mat" />
    """

    path = ENV_DIR / "family5_layout.xml"
    xml = base_xml.replace("</worldbody>", f"{geoms}\n</worldbody>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)

    return path, path


def generate_all_fixtures() -> Dict[str, Tuple[Path, Path]]:
    """Generates all 5 task family environments."""
    fixtures = {
        "family_1": build_family1_xmls(),
        "family_2": build_family2_xmls(),
        "family_3": build_family3_xmls(),
        "family_4": build_family4_xmls(),
        "family_5": build_family5_xmls(),
    }
    return fixtures


if __name__ == "__main__":
    fixtures = generate_all_fixtures()
    print("Successfully generated all 5 task family XML fixtures:")
    for fam, (pA, pB) in fixtures.items():
        print(f"  {fam}: CondA={pA.name}, CondB={pB.name}")
