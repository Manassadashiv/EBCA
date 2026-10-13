import sys
sys.path.insert(0, ".")
import torch
import numpy as np
from brain.carl_physarum import CarlPhysarumRoutingEngine

p = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4)
g = torch.load("world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt")
p.update_occupancy(g[0, 0].numpy())

print("Obstacle mask along corridor:")
# gi is y index, gj is x index
# y = -6.4 + (gi + 0.5)*0.4. For gi=14, y = -6.4 + 14.5*0.4 = -0.6. gi=15: y=-0.2. gi=16: y=+0.2. gi=17: y=+0.6.
for gi in range(13, 19):
    y = -6.4 + (gi + 0.5) * 0.4
    row = "".join(["#" if p.obstacle_mask[gi, gj] else "." for gj in range(12, 21)])
    print(f"gi={gi:02d} (y={y:+.2f}): {row}")

# Check x values for gj in 12..20
x_vals = [-6.4 + (gj + 0.5) * 0.4 for gj in range(12, 21)]
print("gj: " + "".join([f"{gj:2d}" for gj in range(12, 21)]))
print("x:  " + " ".join([f"{x:+.1f}" for x in x_vals]))
