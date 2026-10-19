import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

STL_PATH = r"d:\ebca\experiments\morphological_coevolution\novel_biomimetic_cad\carl_morpho_diode_assembly.stl"
OUT_IMG = r"d:\ebca\experiments\morphological_coevolution\novel_biomimetic_cad\novel_mechanism_mesh_preview.png"

mesh = trimesh.load(STL_PATH)
vertices = mesh.vertices
faces = mesh.faces

fig = plt.figure(figsize=(18, 6), dpi=300)

# View 1: Isometric View
ax1 = fig.add_subplot(1, 3, 1, projection='3d')
tri1 = Poly3DCollection(vertices[faces], alpha=0.90, edgecolor='darkslategray', linewidths=0.15)
tri1.set_facecolor('#00e5ff')
ax1.add_collection3d(tri1)
ax1.set_xlim(-130, 90)
ax1.set_ylim(-110, 110)
ax1.set_zlim(-40, 50)
ax1.view_init(elev=28, azim=-55)
ax1.set_title("Novel Monolithic Organism (Isometric FEA Mesh)", fontweight="bold", fontsize=11)
ax1.set_xlabel("X (mm)", fontweight="bold")
ax1.set_ylabel("Y (mm)", fontweight="bold")
ax1.set_zlabel("Z (mm)", fontweight="bold")

# View 2: Side View (Showing Tesla Spiral Vanes & Caster S-Curve)
ax2 = fig.add_subplot(1, 3, 2, projection='3d')
tri2 = Poly3DCollection(vertices[faces], alpha=0.90, edgecolor='black', linewidths=0.15)
tri2.set_facecolor('#76ff03')
ax2.add_collection3d(tri2)
ax2.set_xlim(-130, 90)
ax2.set_ylim(-110, 110)
ax2.set_zlim(-40, 50)
ax2.view_init(elev=0, azim=-90)
ax2.set_title("Side Profile: Tesla Spiral Vanes & S-Flexure", fontweight="bold", fontsize=11)
ax2.set_xlabel("X (mm)", fontweight="bold")
ax2.set_zlabel("Z (mm)", fontweight="bold")

# View 3: Top View (Showing Cheetah-Vertebra Morphing Ribcage)
ax3 = fig.add_subplot(1, 3, 3, projection='3d')
tri3 = Poly3DCollection(vertices[faces], alpha=0.90, edgecolor='darkblue', linewidths=0.15)
tri3.set_facecolor('#ff3d00')
ax3.add_collection3d(tri3)
ax3.set_xlim(-130, 90)
ax3.set_ylim(-110, 110)
ax3.set_zlim(-40, 50)
ax3.view_init(elev=90, azim=-90)
ax3.set_title("Top Profile: Morphing Squeeze Ribcage (184mm)", fontweight="bold", fontsize=11)
ax3.set_xlabel("X (mm)", fontweight="bold")
ax3.set_ylabel("Y (mm)", fontweight="bold")

plt.tight_layout()
plt.savefig(OUT_IMG, bbox_inches="tight")
plt.close()
print("Saved novel mechanism preview:", OUT_IMG)
