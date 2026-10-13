import sys
import math
sys.path.insert(0, ".")
import torch
import numpy as np
from brain.carl_physarum import CarlPhysarumRoutingEngine

g = torch.load("world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt").numpy()[0]
p = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4)

positions = [
    (0.58, 0.0),
    (0.40, 0.05),
    (0.20, -0.05),
    (0.00, 0.02),
    (-0.25, -0.02),
    (-0.45, 0.01),
    (-0.55, 0.0),
    (-0.80, 0.0)
]

print("=== TESTING SINK AT (-2.5, 0.0) INSIDE ARENA ===")
for px, py in positions:
    p.step(src_pos=(px, py), snk_pos=(-2.5, 0.0), occ_grid_128=g[0])
    vx, vy, th = p.get_topological_current(px, py)
    print(f"pos=({px:+.2f}, {py:+.2f}) -> flow=(vx={vx:+.3f}, vy={vy:+.3f}, th={math.degrees(th):+.1f} deg)")
