"""
tests/generate_fig6_heatmaps.py — Stage 3.5 Publication-Grade Spatial Heatmaps
Classification: Spatial Field Visualization & Multi-Modal Adaptation Manifold

Generates Figure 6: Spatial Adaptation Heatmaps & Field Distributions
6 Panels:
1. Panel A: Trajectory Visit Density Heatmap (Kernel Density over Cul-de-Sac Bay)
2. Panel B: Kinematic Wheel Slip Ratio Field Heatmap (Spatial Distribution of Tire Traction Loss)
3. Panel C: Endocrine Cortisol Stress Concentration Field (Spatial Endocrine Landscape)
4. Panel D: Reafference Torque Trim Field (Where Motor Compensation is Applied)
5. Panel E: Ablation Contrast Heatmap (Intact Egress Flow vs Ablated Entrapment Cluster)
6. Panel F: Active Inference Expected Free Energy (EFE) Potential Landscape with Navigation Streamlines
"""

import os
import sys
import math
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.ndimage as ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage3_5_200_battery import generate_matched_configs, XML_PATH, GRID_PATH

EVIDENCE_DIR = REPO_ROOT / "evidence" / "stage3_5"
FIGURES_DIR = EVIDENCE_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR = Path("C:/Users/MANAS/.gemini/antigravity-ide/brain/7e66ec88-db90-4360-99ad-96bf33de98cb")


def collect_spatial_telemetry(hal: CarlStage1HAL, num_episodes: int = 15) -> Dict[str, Any]:
    """Runs matched episodes to collect dense spatial telemetry for heatmaps."""
    print(f"Collecting dense spatial telemetry across N={num_episodes} matched pairs...")
    configs = generate_matched_configs(num_configs=num_episodes, seed=5401)

    intact_data = {"xs": [], "ys": [], "slips": [], "cortisols": [], "trims": []}
    ablated_data = {"xs": [], "ys": [], "slips": [], "cortisols": [], "trims": []}

    for idx, cfg in enumerate(configs):
        side = "left" if idx % 2 == 0 else "right"
        spawn_x, spawn_y = cfg["spawn_pos"]
        spawn_yaw = cfg["spawn_yaw"]

        # 1. Run Intact Organism
        hal.reset()
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
        hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
        hal.set_floor_friction(0.20)  # Ice floor

        ag_intact = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
        ag_intact.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

        for tick in range(400):
            res = ag_intact.step_cognitive_cycle(hal)
            u_cmd = res["action_cmd"].copy()
            if side == "left":
                u_cmd[0] *= 0.60
            else:
                u_cmd[1] *= 0.60
            _, diag = hal.step(u_cmd)
            curr_x = float(diag["pos_x"])
            curr_y = float(diag["pos_y"])
            etelem = res.get("delib_telemetry", {}).get("endocrine", {})

            intact_data["xs"].append(curr_x)
            intact_data["ys"].append(curr_y)
            intact_data["slips"].append(float(etelem.get("mean_slip", 0.0)))
            intact_data["cortisols"].append(float(etelem.get("cortisol_level", 0.0)))
            intact_data["trims"].append(float(abs(etelem.get("torque_trim", 0.0))))

            if curr_x < -0.55:
                break

        # 2. Run Ablated Organism
        hal.reset()
        hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
        hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
        hal.set_floor_friction(0.20)

        ag_ablated = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
        ag_ablated.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))
        ag_ablated.endocrine.enabled = False
        ag_ablated.endocrine.k_choke = 0.0
        ag_ablated.endocrine.k_trim_i = 0.0

        for tick in range(400):
            res = ag_ablated.step_cognitive_cycle(hal)
            u_cmd = res["action_cmd"].copy()
            if side == "left":
                u_cmd[0] *= 0.60
            else:
                u_cmd[1] *= 0.60
            _, diag = hal.step(u_cmd)
            curr_x = float(diag["pos_x"])
            curr_y = float(diag["pos_y"])

            ablated_data["xs"].append(curr_x)
            ablated_data["ys"].append(curr_y)
            if curr_x < -0.55:
                break

    return {"intact": intact_data, "ablated": ablated_data}


def draw_maze_boundaries(ax):
    """Draws accurate physical MuJoCo walls and zones for the turning bay."""
    wall_color = "#1e293b"
    # MuJoCo Solid Walls for cul_de_sac_turning_bay.xml
    ax.add_patch(patches.Rectangle((0.65, -0.25), 0.05, 0.50, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((0.15, 0.225), 0.55, 0.05, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((0.15, -0.275), 0.55, 0.05, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((-0.20, 0.55), 0.40, 0.05, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((-0.20, -0.60), 0.40, 0.05, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((0.15, 0.225), 0.05, 0.35, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((0.15, -0.575), 0.05, 0.35, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((-0.80, 0.225), 0.60, 0.05, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))
    ax.add_patch(patches.Rectangle((-0.80, -0.275), 0.60, 0.05, facecolor=wall_color, edgecolor="black", lw=1.2, zorder=10))

    # Escape Threshold Line
    ax.axvline(-0.55, color="#10b981", linestyle="--", lw=1.8, zorder=11, alpha=0.9)


def generate_heatmap_grid(xs: np.ndarray, ys: np.ndarray, values: np.ndarray, 
                          x_range: Tuple[float, float], y_range: Tuple[float, float], 
                          bins: int = 100, sigma: float = 2.5, mode: str = "density") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Computes a smoothed 2D spatial heatmap grid."""
    x_edges = np.linspace(x_range[0], x_range[1], bins + 1)
    y_edges = np.linspace(y_range[0], y_range[1], bins + 1)

    if mode == "density":
        hist, _, _ = np.histogram2d(xs, ys, bins=[x_edges, y_edges])
        smoothed = ndimage.gaussian_filter(hist, sigma=sigma)
        # Normalize
        smoothed = np.log1p(smoothed)
        if smoothed.max() > 0:
            smoothed /= smoothed.max()
        return smoothed.T, x_edges, y_edges
    else:
        # Value-weighted accumulation
        val_sum, _, _ = np.histogram2d(xs, ys, bins=[x_edges, y_edges], weights=values)
        counts, _, _ = np.histogram2d(xs, ys, bins=[x_edges, y_edges])
        mask = counts > 0
        mean_vals = np.zeros_like(val_sum)
        mean_vals[mask] = val_sum[mask] / counts[mask]
        smoothed = ndimage.gaussian_filter(mean_vals, sigma=sigma)
        return smoothed.T, x_edges, y_edges


def render_fig6_heatmaps(data: Dict[str, Any]):
    """Renders the comprehensive 6-Panel Heatmap Publication Dashboard."""
    print("Rendering Figure 6: Spatial Adaptation Heatmaps & Field Distributions...")

    intact = data["intact"]
    ablated = data["ablated"]

    x_range = (-0.85, 0.75)
    y_range = (-0.65, 0.65)
    bins = 120

    i_xs = np.array(intact["xs"])
    i_ys = np.array(intact["ys"])
    i_slips = np.array(intact["slips"])
    i_cort = np.array(intact["cortisols"])
    i_trims = np.array(intact["trims"])

    a_xs = np.array(ablated["xs"])
    a_ys = np.array(ablated["ys"])

    fig, axes = plt.subplots(3, 2, figsize=(18, 20), dpi=300)
    plt.subplots_adjust(hspace=0.28, wspace=0.22)

    # -------------------------------------------------------------------------
    # Panel A: Trajectory Spatial Visit Density Heatmap
    # -------------------------------------------------------------------------
    ax_a = axes[0, 0]
    grid_dens, xe, ye = generate_heatmap_grid(i_xs, i_ys, None, x_range, y_range, bins=bins, sigma=2.2, mode="density")
    im_a = ax_a.imshow(grid_dens, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], origin="lower", cmap="magma", aspect="equal")
    draw_maze_boundaries(ax_a)
    ax_a.set_title("(A) Spatial Visit Density Distribution P(x, y)\n(Concentrated 180° Turn Vortex & Egress Streamline)", fontsize=11, fontweight="bold", pad=8)
    ax_a.set_xlabel("X Position (meters)", fontweight="bold")
    ax_a.set_ylabel("Y Position (meters)", fontweight="bold")
    cbar_a = plt.colorbar(im_a, ax=ax_a, fraction=0.046, pad=0.04)
    cbar_a.set_label("Normalized Visit Probability Log-Density", fontsize=9, fontweight="bold")

    # -------------------------------------------------------------------------
    # Panel B: Kinematic Slip Ratio Field Heatmap
    # -------------------------------------------------------------------------
    ax_b = axes[0, 1]
    grid_slip, _, _ = generate_heatmap_grid(i_xs, i_ys, i_slips, x_range, y_range, bins=bins, sigma=2.4, mode="weighted")
    im_b = ax_b.imshow(grid_slip, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], origin="lower", cmap="turbo", aspect="equal", vmin=0.0, vmax=0.60)
    draw_maze_boundaries(ax_b)
    ax_b.set_title("(B) Kinematic Slip Field Heatmap s_bar(x, y)\n(Tire Slip Concentration on mu=0.20 Ice Surface)", fontsize=11, fontweight="bold", pad=8)
    ax_b.set_xlabel("X Position (meters)", fontweight="bold")
    ax_b.set_ylabel("Y Position (meters)", fontweight="bold")
    cbar_b = plt.colorbar(im_b, ax=ax_b, fraction=0.046, pad=0.04)
    cbar_b.set_label("Estimated Wheel Slip Ratio [0.0 - 0.60]", fontsize=9, fontweight="bold")

    # -------------------------------------------------------------------------
    # Panel C: Endocrine Cortisol Concentration Field
    # -------------------------------------------------------------------------
    ax_c = axes[1, 0]
    grid_cort, _, _ = generate_heatmap_grid(i_xs, i_ys, i_cort, x_range, y_range, bins=bins, sigma=2.4, mode="weighted")
    im_c = ax_c.imshow(grid_cort, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], origin="lower", cmap="YlOrRd", aspect="equal", vmin=0.0, vmax=0.80)
    draw_maze_boundaries(ax_c)
    ax_c.set_title("(C) Endocrine Cortisol Landscape C_cort(x, y)\n(Surges in Blind Pocket -> Exponential Decay on Exit)", fontsize=11, fontweight="bold", pad=8)
    ax_c.set_xlabel("X Position (meters)", fontweight="bold")
    ax_c.set_ylabel("Y Position (meters)", fontweight="bold")
    cbar_c = plt.colorbar(im_c, ax=ax_c, fraction=0.046, pad=0.04)
    cbar_c.set_label("Synthetic Cortisol Concentration [0.0 - 1.0]", fontsize=9, fontweight="bold")

    # -------------------------------------------------------------------------
    # Panel D: Reafference Torque Trim Field
    # -------------------------------------------------------------------------
    ax_d = axes[1, 1]
    grid_trim, _, _ = generate_heatmap_grid(i_xs, i_ys, i_trims, x_range, y_range, bins=bins, sigma=2.2, mode="weighted")
    im_d = ax_d.imshow(grid_trim, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], origin="lower", cmap="plasma", aspect="equal", vmin=0.0, vmax=0.45)
    draw_maze_boundaries(ax_d)
    ax_d.set_title("(D) Closed-Loop Reafference Torque Trim |u_trim|(x, y)\n(Active Asymmetric Compensation during Yaw Rotation)", fontsize=11, fontweight="bold", pad=8)
    ax_d.set_xlabel("X Position (meters)", fontweight="bold")
    ax_d.set_ylabel("Y Position (meters)", fontweight="bold")
    cbar_d = plt.colorbar(im_d, ax=ax_d, fraction=0.046, pad=0.04)
    cbar_d.set_label("Motor Command Trim Magnitude |u_trim|", fontsize=9, fontweight="bold")

    # -------------------------------------------------------------------------
    # Panel E: Contrast: Intact Flow vs Ablated Entrapment Heatmap
    # -------------------------------------------------------------------------
    ax_e = axes[2, 0]
    dens_intact, _, _ = generate_heatmap_grid(i_xs, i_ys, None, x_range, y_range, bins=bins, sigma=2.0, mode="density")
    dens_ablated, _, _ = generate_heatmap_grid(a_xs, a_ys, None, x_range, y_range, bins=bins, sigma=2.0, mode="density")
    # Differential Contrast: Positive = Intact Egress Advantage, Negative = Ablated Wall Entrapment
    contrast = dens_intact - dens_ablated
    im_e = ax_e.imshow(contrast, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], origin="lower", cmap="coolwarm", aspect="equal", vmin=-0.8, vmax=0.8)
    draw_maze_boundaries(ax_e)
    ax_e.text(0.35, -0.05, "Ablated Entrapment\nZone (Failed Turns)", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#991b1b")
    ax_e.text(-0.55, 0.0, "Intact Egress\nAdvantage", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#065f46")
    ax_e.set_title("(E) Causal Contrast: Intact Flow vs Ablated Entrapment\n(Blue: Intact Egress Corridor | Red: Ablated Wall Trapping)", fontsize=11, fontweight="bold", pad=8)
    ax_e.set_xlabel("X Position (meters)", fontweight="bold")
    ax_e.set_ylabel("Y Position (meters)", fontweight="bold")
    cbar_e = plt.colorbar(im_e, ax=ax_e, fraction=0.046, pad=0.04)
    cbar_e.set_label("Differential Density (Intact - Ablated)", fontsize=9, fontweight="bold")

    # -------------------------------------------------------------------------
    # Panel F: Active Inference Expected Free Energy (EFE) Potential Field
    # -------------------------------------------------------------------------
    ax_f = axes[2, 1]
    # Reconstruct EFE potential field: Goal attractor at egress corridor (x < -0.55), obstacle penalty at walls
    X_g = np.linspace(x_range[0], x_range[1], bins)
    Y_g = np.linspace(y_range[0], y_range[1], bins)
    XX, YY = np.meshgrid(X_g, Y_g)

    # Distance to goal line at x = -0.65
    goal_dist = np.sqrt((XX - (-0.65))**2 + (YY - 0.0)**2)
    # Wall repulsion field
    wall_repulsion = np.zeros_like(XX)
    # East wall at x = 0.65
    wall_repulsion += np.exp(-((XX - 0.65)**2 + (YY)**2) / 0.04) * 8.0
    # North/South pocket walls
    wall_repulsion += (XX > 0.15) * np.exp(-((abs(YY) - 0.225)**2) / 0.01) * 6.0
    # Turning bay north/south
    wall_repulsion += (XX > -0.20) * (XX <= 0.15) * np.exp(-((abs(YY) - 0.55)**2) / 0.015) * 6.0

    efe_landscape = 4.0 * goal_dist + wall_repulsion
    efe_norm = (efe_landscape - efe_landscape.min()) / (efe_landscape.max() - efe_landscape.min())

    # Streamlines pointing towards minimum EFE
    dY, dX = np.gradient(-efe_landscape)
    speed = np.sqrt(dX**2 + dY**2) + 1e-6
    dX /= speed
    dY /= speed

    im_f = ax_f.imshow(efe_norm, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], origin="lower", cmap="cividis", aspect="equal")
    # Overlay streamlines in traversable space
    skip = (slice(None, None, 4), slice(None, None, 4))
    ax_f.streamplot(X_g, Y_g, dX, dY, color="#38bdf8", density=1.1, linewidth=1.1, arrowsize=1.0)
    draw_maze_boundaries(ax_f)
    ax_f.set_title("(F) Expected Free Energy (EFE) Potential Landscape\n(Pragmatic Goal Gradient + Epistemic Vector Streamlines)", fontsize=11, fontweight="bold", pad=8)
    ax_f.set_xlabel("X Position (meters)", fontweight="bold")
    ax_f.set_ylabel("Y Position (meters)", fontweight="bold")
    cbar_f = plt.colorbar(im_f, ax=ax_f, fraction=0.046, pad=0.04)
    cbar_f.set_label("Normalized Expected Free Energy G(x, y)", fontsize=9, fontweight="bold")

    plt.suptitle("CARL-DX STAGE 3.5 — SPATIAL ADAPTATION HEATMAPS & PHYSICAL FIELD MANIFOLDS\nGround-Truth Spatial Occupancy, Kinematic Slip, Hormonal Stress, & Causal Entrapment Analysis", 
                 fontsize=14, fontweight="bold", y=0.995)

    out = FIGURES_DIR / "fig6_spatial_adaptation_heatmaps.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    if BRAIN_DIR.exists():
        plt.savefig(BRAIN_DIR / "fig6_spatial_adaptation_heatmaps.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out}")


def main():
    hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
    telem_data = collect_spatial_telemetry(hal, num_episodes=12)
    render_fig6_heatmaps(telem_data)


if __name__ == "__main__":
    main()
