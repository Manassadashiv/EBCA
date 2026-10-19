import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
import numpy as np

STL_PATH = r"d:\ebca\experiments\morphological_coevolution\cad_models\carl_evolved_assembly.stl"
OUT_IMG = r"d:\ebca\experiments\morphological_coevolution\cad_models\carl_cad_mesh_preview.png"

mesh = trimesh.load(STL_PATH)
vertices = mesh.vertices
faces = mesh.faces

fig = plt.figure(figsize=(16, 6), dpi=300)

# View 1: Isometric View
ax1 = fig.add_subplot(1, 3, 1, projection='3d')
tri1 = Poly3DCollection(vertices[faces], alpha=0.85, edgecolor='black', linewidths=0.2)
tri1.set_facecolor('#00bcd4')
ax1.add_collection3d(tri1)
ax1.set_xlim(-130, 100)
ax1.set_ylim(-110, 110)
ax1.set_zlim(-40, 70)
ax1.view_init(elev=25, azim=-60)
ax1.set_title("Isometric 3D CAD Mesh (PrePoMax / ANSYS)", fontweight="bold", fontsize=11)
ax1.set_xlabel("X (mm)", fontweight="bold")
ax1.set_ylabel("Y (mm)", fontweight="bold")
ax1.set_zlabel("Z (mm)", fontweight="bold")

# View 2: Top View (XY Plane - Showing 184mm Track Width)
ax2 = fig.add_subplot(1, 3, 2, projection='3d')
tri2 = Poly3DCollection(vertices[faces], alpha=0.85, edgecolor='black', linewidths=0.2)
tri2.set_facecolor('#4caf50')
ax2.add_collection3d(tri2)
ax2.set_xlim(-130, 100)
ax2.set_ylim(-110, 110)
ax2.set_zlim(-40, 70)
ax2.view_init(elev=90, azim=-90)
ax2.set_title("Top View (Track Width = 184mm)", fontweight="bold", fontsize=11)
ax2.set_xlabel("X (mm)", fontweight="bold")
ax2.set_ylabel("Y (mm)", fontweight="bold")

# View 3: Front View (YZ Plane - Showing 74mm Wheel Diameter)
ax3 = fig.add_subplot(1, 3, 3, projection='3d')
tri3 = Poly3DCollection(vertices[faces], alpha=0.85, edgecolor='black', linewidths=0.2)
tri3.set_facecolor('#ff9800')
ax3.add_collection3d(tri3)
ax3.set_xlim(-130, 100)
ax3.set_ylim(-110, 110)
ax3.set_zlim(-40, 70)
ax3.view_init(elev=0, azim=0)
ax3.set_title("Front View (Wheel Diam = 74mm)", fontweight="bold", fontsize=11)
ax3.set_ylabel("Y (mm)", fontweight="bold")
ax3.set_zlabel("Z (mm)", fontweight="bold")

plt.tight_layout()
plt.savefig(OUT_IMG, bbox_inches="tight")
plt.close()
print("Saved mesh preview:", OUT_IMG)
