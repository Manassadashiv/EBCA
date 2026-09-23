"""
world/stage3_4_environments/generate_stage3_4_fixtures.py — Stage 3.4 Environment Fixture Generator
Classification: [STAGE 3.4 FIXTURES] Authoritative Physical Tasks for Active Inference Emergence

Generates the 3 pre-registered physical environments:
1. cul_de_sac_trap.xml: 1.8m x 0.70m non-convex U-trap where forward controllers wedge permanently.
2. asymmetric_t_junction.xml: Information-ambiguity decision fixture (one branch open, one dead-end).
3. narrow_reversal_corridor.xml: Narrow corridor (W=0.55m) requiring authentic reverse-pivot maneuvers.

Also generates the corresponding certified raster occupancy memory grids (.pt).
"""

import re
import math
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent.parent
BASE_XML_PATH = repo_root / "world" / "clean_arena.xml"
OUT_DIR = repo_root / "world" / "stage3_4_environments"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_base_xml_content() -> str:
    with open(BASE_XML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # Remove default food and test objects
    pattern = re.compile(r'<geom name="food"[\s\S]*?<body name="drive_deck"')
    return pattern.sub('<body name="drive_deck"', content)


def build_cul_de_sac_trap_xml() -> Path:
    """
    1.8m x 0.70m non-convex U-trap.
    End wall at x=1.20, y in [-0.35, 0.35].
    North wall at y=0.35 from x=-0.60 to x=1.20 (length 1.80m).
    South wall at y=-0.35 from x=-0.60 to x=1.20 (length 1.80m).
    Mouth opening at x=-0.60.
    """
    base_xml = get_base_xml_content()
    geoms = """
    <!-- Stage 3.4: 1.8m x 0.70m Non-Convex Cul-de-Sac U-Trap -->
    <!-- North Wall: center x=0.30, y=0.40, size=(0.90, 0.05, 0.25) -> x in [-0.60, 1.20] -->
    <geom name="cds_wall_n" type="box" size="0.90 0.05 0.25" pos="0.30  0.40 0.25" material="wall_mat" />
    <!-- South Wall: center x=0.30, y=-0.40, size=(0.90, 0.05, 0.25) -> x in [-0.60, 1.20] -->
    <geom name="cds_wall_s" type="box" size="0.90 0.05 0.25" pos="0.30 -0.40 0.25" material="wall_mat" />
    <!-- Dead-End Cap: center x=1.25, y=0.0, size=(0.05, 0.45, 0.25) -> blocks x=1.20 to 1.30 -->
    <geom name="cds_cap_e"  type="box" size="0.05 0.45 0.25" pos="1.25  0.00 0.25" material="wall_mat" />

    <!-- External Funnel Guide Walls outside mouth (x in [-1.50, -0.60]) -->
    <geom name="cds_guide_n" type="box" size="0.55 0.05 0.25" pos="-1.10  0.95 0.25" euler="0 0 -0.7854" material="wall_mat" />
    <geom name="cds_guide_s" type="box" size="0.55 0.05 0.25" pos="-1.10 -0.95 0.25" euler="0 0  0.7854" material="wall_mat" />
    """
    path = OUT_DIR / "cul_de_sac_trap.xml"
    xml_content = base_xml.replace("</worldbody>", f"{geoms}\n</worldbody>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return path


def build_cul_de_sac_turning_bay_xml() -> Path:
    """
    Stage 3.4-R: Cul-de-Sac with Rotational Turning Bay (W_bay = 1.30m for x in [0.35, 0.85]).
    Total corridor length = 1.80m (x in [-0.60, 1.20]).
    Egress channel: x in [-0.60, 0.35], width = 0.70m (y in [-0.35, 0.35]).
    Turning bay: x in [0.35, 0.85], width = 1.30m (y in [-0.65, 0.65]).
    Inner pocket: x in [0.85, 1.20], width = 0.70m (y in [-0.35, 0.35]).
    Dead-end cap: blocks x in [1.20, 1.30], y in [-0.35, 0.35].
    """
    base_xml = get_base_xml_content()
    geoms = """
    <!-- Stage 3.4-R: Cul-de-Sac with 1.30m Turning Bay (L=1.80m, W=0.70m, W_bay=1.30m) -->
    <!-- 1. Approach / Egress Corridor (x in [-0.60, 0.35], width 0.70m) -->
    <!-- North Wall: center x=-0.125, y=0.40, size=(0.475, 0.05, 0.25) -> x in [-0.60, 0.35], y_inner=0.35 -->
    <geom name="tb_app_n" type="box" size="0.475 0.05 0.25" pos="-0.125  0.40 0.25" material="wall_mat" />
    <!-- South Wall: center x=-0.125, y=-0.40, size=(0.475, 0.05, 0.25) -> x in [-0.60, 0.35], y_inner=-0.35 -->
    <geom name="tb_app_s" type="box" size="0.475 0.05 0.25" pos="-0.125 -0.40 0.25" material="wall_mat" />

    <!-- 2. Turning Bay Expansion (x in [0.35, 0.85], width 1.30m -> y_inner in [-0.65, 0.65]) -->
    <!-- North Entrance Shoulder (at x=0.35): spans y from 0.35 to 0.70 -->
    <geom name="tb_shld_n_in"  type="box" size="0.025 0.175 0.25" pos="0.325  0.525 0.25" material="wall_mat" />
    <!-- South Entrance Shoulder (at x=0.35): spans y from -0.70 to -0.35 -->
    <geom name="tb_shld_s_in"  type="box" size="0.025 0.175 0.25" pos="0.325 -0.525 0.25" material="wall_mat" />

    <!-- North Bay Wall: center x=0.60, y=0.70, size=(0.25, 0.05, 0.25) -> x in [0.35, 0.85], y_inner=0.65 -->
    <geom name="tb_bay_n" type="box" size="0.25 0.05 0.25" pos="0.60  0.70 0.25" material="wall_mat" />
    <!-- South Bay Wall: center x=0.60, y=-0.70, size=(0.25, 0.05, 0.25) -> x in [0.35, 0.85], y_inner=-0.65 -->
    <geom name="tb_bay_s" type="box" size="0.25 0.05 0.25" pos="0.60 -0.70 0.25" material="wall_mat" />

    <!-- North Exit Shoulder (at x=0.85): spans y from 0.35 to 0.70 -->
    <geom name="tb_shld_n_out" type="box" size="0.025 0.175 0.25" pos="0.875  0.525 0.25" material="wall_mat" />
    <!-- South Exit Shoulder (at x=0.85): spans y from -0.70 to -0.35 -->
    <geom name="tb_shld_s_out" type="box" size="0.025 0.175 0.25" pos="0.875 -0.525 0.25" material="wall_mat" />

    <!-- 3. Inner Pocket & Dead End Cap (x in [0.85, 1.20], width 0.70m) -->
    <!-- North Pocket Wall: center x=1.05, y=0.40, size=(0.15, 0.05, 0.25) -> x in [0.90, 1.20], y_inner=0.35 -->
    <geom name="tb_pock_n" type="box" size="0.15 0.05 0.25" pos="1.05  0.40 0.25" material="wall_mat" />
    <!-- South Pocket Wall: center x=1.05, y=-0.40, size=(0.15, 0.05, 0.25) -> x in [0.90, 1.20], y_inner=-0.35 -->
    <geom name="tb_pock_s" type="box" size="0.15 0.05 0.25" pos="1.05 -0.40 0.25" material="wall_mat" />
    <!-- Dead-End Cap: center x=1.25, y=0.0, size=(0.05, 0.45, 0.25) -> blocks x=1.20 to 1.30 -->
    <geom name="tb_cap_e"  type="box" size="0.05 0.45 0.25" pos="1.25  0.00 0.25" material="wall_mat" />

    <!-- External Funnel Guide Walls outside mouth (x in [-1.50, -0.60]) -->
    <geom name="tb_guide_n" type="box" size="0.55 0.05 0.25" pos="-1.10  0.95 0.25" euler="0 0 -0.7854" material="wall_mat" />
    <geom name="tb_guide_s" type="box" size="0.55 0.05 0.25" pos="-1.10 -0.95 0.25" euler="0 0  0.7854" material="wall_mat" />
    """
    path = OUT_DIR / "cul_de_sac_turning_bay.xml"
    xml_content = base_xml.replace("</worldbody>", f"{geoms}\n</worldbody>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return path


def build_asymmetric_t_junction_xml() -> Path:
    """
    Asymmetric T-Junction: Approach corridor leads to bifurcation at x=0.50.
    North branch (+y) is occluded dead-end at y=1.60.
    South branch (-y) opens into traversable corridor.
    """
    base_xml = get_base_xml_content()
    geoms = """
    <!-- Stage 3.4: Asymmetric T-Junction Decision Fixture -->
    <!-- Approach corridor (x in [-1.0, 0.50], width 0.80m) -->
    <geom name="atj_app_n" type="box" size="0.75 0.05 0.25" pos="-0.25  0.45 0.25" material="wall_mat" />
    <geom name="atj_app_s" type="box" size="0.75 0.05 0.25" pos="-0.25 -0.45 0.25" material="wall_mat" />
    <geom name="atj_back"  type="box" size="0.05 0.50 0.25" pos="-1.05  0.00 0.25" material="wall_mat" />

    <!-- Front Dividing Wall at T-Junction -->
    <geom name="atj_front" type="box" size="0.05 1.50 0.25" pos="1.20  0.00 0.25" material="wall_mat" />

    <!-- North Branch Dead-End Cap -->
    <geom name="atj_cap_n" type="box" size="0.40 0.05 0.25" pos="0.80  1.60 0.25" material="wall_mat" />
    <!-- Outer North Corridor Wall -->
    <geom name="atj_out_n" type="box" size="0.05 0.60 0.25" pos="0.45  1.05 0.25" material="wall_mat" />

    <!-- South Branch Open Exit Walls -->
    <geom name="atj_out_s" type="box" size="0.05 1.00 0.25" pos="0.45 -1.45 0.25" material="wall_mat" />
    """
    path = OUT_DIR / "asymmetric_t_junction.xml"
    xml_content = base_xml.replace("</worldbody>", f"{geoms}\n</worldbody>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return path


def build_narrow_reversal_corridor_xml() -> Path:
    """
    Narrow Reversal Corridor (W=0.55m, L=1.6m).
    Width: 0.55m. Requires authentic multi-phase reverse-pivot (3-point turn).
    """
    base_xml = get_base_xml_content()
    geoms = """
    <!-- Stage 3.4: Narrow Reversal Corridor (W=0.55m) -->
    <!-- North Wall: y=+0.325, x in [-0.40, 1.20] -->
    <geom name="nrc_wall_n" type="box" size="0.80 0.05 0.25" pos="0.40  0.325 0.25" material="wall_mat" />
    <!-- South Wall: y=-0.325, x in [-0.40, 1.20] -->
    <geom name="nrc_wall_s" type="box" size="0.80 0.05 0.25" pos="0.40 -0.325 0.25" material="wall_mat" />
    <!-- End Cap at x=1.20 -->
    <geom name="nrc_cap_e"  type="box" size="0.05 0.375 0.25" pos="1.25  0.000 0.25" material="wall_mat" />

    <!-- Guide funnels outside mouth at x=-0.40 -->
    <geom name="nrc_guide_n" type="box" size="0.50 0.05 0.25" pos="-0.85  0.75 0.25" euler="0 0 -0.7854" material="wall_mat" />
    <geom name="nrc_guide_s" type="box" size="0.50 0.05 0.25" pos="-0.85 -0.75 0.25" euler="0 0  0.7854" material="wall_mat" />
    """
    path = OUT_DIR / "narrow_reversal_corridor.xml"
    xml_content = base_xml.replace("</worldbody>", f"{geoms}\n</worldbody>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return path


def rasterize_environment_grid(xml_path: Path, out_grid_path: Path):
    """
    Samples rays via MuJoCo physics to produce a high-fidelity certified 2D occupancy grid (.pt).
    Channel 0: Obstacle occupancy (0 = free, >0.85 = obstacle)
    Channel 1: Explored visibility mask (1.0 = observed)
    """
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)

    # Move robot chassis out of the arena to rasterize only static arena obstacles
    if model.nq >= 3:
        data.qpos[0] = 50.0
        data.qpos[1] = 50.0
        data.qpos[2] = 10.0
    mujoco.mj_forward(model, data)

    grid_size = 128
    resolution = 0.10
    half_size = 6.4

    grid_occ = np.zeros((grid_size, grid_size), dtype=np.float32)
    grid_vis = np.zeros((grid_size, grid_size), dtype=np.float32)

    # Raycast outward from a grid of scan vantage points
    vantage_x = np.linspace(-3.0, 3.0, 31)
    vantage_y = np.linspace(-3.0, 3.0, 31)
    sonar_angles = np.linspace(-np.pi, np.pi, 36, endpoint=False)

    for vx in vantage_x:
        for vy in vantage_y:
            p_start = np.array([vx, vy, 0.08], dtype=np.float64)
            for angle in sonar_angles:
                p_dir = np.array([math.cos(angle), math.sin(angle), 0.0], dtype=np.float64)
                geom_id = np.zeros(1, dtype=np.int32)
                dist = mujoco.mj_ray(model, data, p_start, p_dir, None, 1, -1, geom_id)
                if dist < 0 or dist > 4.5:
                    d_ray = 4.5
                else:
                    d_ray = dist

                # Mark ray path visibility and endpoint hits
                r_samples = np.linspace(0.10, d_ray - 0.05, 10)
                px = vx + r_samples * math.cos(angle)
                py = vy + r_samples * math.sin(angle)
                ix = np.clip(((px + half_size) / resolution).astype(int), 0, grid_size - 1)
                iy = np.clip(((py + half_size) / resolution).astype(int), 0, grid_size - 1)
                grid_vis[iy, ix] = 1.0

                if dist >= 0 and dist <= 4.5:
                    hx = vx + dist * math.cos(angle)
                    hy = vy + dist * math.sin(angle)
                    h_ix = np.clip(((hx + half_size) / resolution).astype(int), 0, grid_size - 1)
                    h_iy = np.clip(((hy + half_size) / resolution).astype(int), 0, grid_size - 1)
                    grid_occ[h_iy, h_ix] = 1.0
                    grid_vis[h_iy, h_ix] = 1.0

    # Tensor format: (1, 2, G, G)
    grid_tensor = torch.zeros(1, 2, grid_size, grid_size, dtype=torch.float32)
    grid_tensor[0, 0] = torch.from_numpy(grid_occ)
    grid_tensor[0, 1] = torch.from_numpy(grid_vis)

    torch.save(grid_tensor, out_grid_path)
    print(f"Rasterized {out_grid_path.name}: shape {grid_tensor.shape}, hits = {int((grid_occ > 0).sum())}")


def generate_all_fixtures():
    print("Generating Stage 3.4 & Stage 3.4-R Environment Fixtures...")
    p1 = build_cul_de_sac_trap_xml()
    rasterize_environment_grid(p1, OUT_DIR / "cul_de_sac_trap_grid.pt")

    p1_tb = build_cul_de_sac_turning_bay_xml()
    rasterize_environment_grid(p1_tb, OUT_DIR / "cul_de_sac_turning_bay_grid.pt")

    p2 = build_asymmetric_t_junction_xml()
    rasterize_environment_grid(p2, OUT_DIR / "asymmetric_t_junction_grid.pt")

    p3 = build_narrow_reversal_corridor_xml()
    rasterize_environment_grid(p3, OUT_DIR / "narrow_reversal_corridor_grid.pt")

    print(f"All environments and grids successfully generated in {OUT_DIR}")


if __name__ == "__main__":
    generate_all_fixtures()
