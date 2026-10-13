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

print("=== TESTING DOWNSTREAM TOPOLOGICAL CURRENT (0.25m AHEAD) ===")
for px, py in positions:
    # Sink is at egress in arena (-2.5, 0.0)
    p.step(src_pos=(px, py), snk_pos=(-2.5, 0.0), occ_grid_128=g[0])
    
    # Sample 0.25m downstream towards sink
    dx_sink = -2.5 - px
    dy_sink = 0.0 - py
    norm_sink = math.hypot(dx_sink, dy_sink)
    downstream_x = px + 0.25 * (dx_sink / norm_sink)
    downstream_y = py + 0.25 * (dy_sink / norm_sink)
    
    vx, vy, th = p.get_topological_current(downstream_x, downstream_y)
    print(f"pos=({px:+.2f}, {py:+.2f}) -> downstream=({downstream_x:+.2f}, {downstream_y:+.2f}) | flow=(vx={vx:+.3f}, vy={vy:+.3f}, th={math.degrees(th):+.1f} deg)")
