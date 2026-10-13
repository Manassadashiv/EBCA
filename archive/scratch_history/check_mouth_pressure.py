import sys
sys.path.insert(0, ".")
import torch
import numpy as np
from brain.carl_physarum import CarlPhysarumRoutingEngine

g = torch.load("world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt").numpy()[0]
p = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4)
p.step(src_pos=(0.0, 0.0), snk_pos=(-2.5, 0.0), occ_grid_128=g[0])

print("Grid x values for columns 11..18:")
# x = -6.4 + (gj + 0.5)*0.4
# gj=11: -1.8, gj=12: -1.4, gj=13: -1.0, gj=14: -0.6, gj=15: -0.2, gj=16: +0.2
for gj in range(11, 18):
    print(f"gj={gj:2d}: x={-6.4 + (gj+0.5)*0.4:+.2f}")

print("\nObstacle mask:")
for gi in range(13, 19):
    row = "".join(["#" if p.obstacle_mask[gi, gj] else "." for gj in range(11, 18)])
    y = -6.4 + (gi + 0.5) * 0.4
    print(f"gi={gi:2d} (y={y:+.2f}): {row}")

print("\nPressure values (scaled 0-99):")
for gi in range(13, 19):
    row = " ".join([f"{int(p.pressure[gi, gj]*100):2d}" for gj in range(11, 18)])
    y = -6.4 + (gi + 0.5) * 0.4
    print(f"gi={gi:2d} (y={y:+.2f}): {row}")
