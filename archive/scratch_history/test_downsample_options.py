import sys
sys.path.insert(0, ".")
import torch
import numpy as np
import time
from brain.carl_physarum import CarlPhysarumRoutingEngine

g = torch.load("world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt")[0, 0].numpy()

# Option A: 32x32 with mean downsampling
p32 = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4)
factor = 4
down_mean = g.reshape(32, factor, 32, factor).mean(axis=(1, 3))
down_center = g.reshape(32, factor, 32, factor)[:, 1:3, :, 1:3].mean(axis=(1, 3))
print("32x32 mean > 0.40:")
for gi in range(13, 19):
    y = -6.4 + (gi + 0.5) * 0.4
    row = "".join(["#" if down_mean[gi, gj] > 0.40 else "." for gj in range(12, 21)])
    print(f"y={y:+.2f}: {row}")

print("\n32x32 center > 0.45:")
for gi in range(13, 19):
    y = -6.4 + (gi + 0.5) * 0.4
    row = "".join(["#" if down_center[gi, gj] > 0.45 else "." for gj in range(12, 21)])
    print(f"y={y:+.2f}: {row}")

# Option B: 64x64 grid (res = 0.20m)
p64 = CarlPhysarumRoutingEngine(grid_dim=64, half_size=6.4)
p64.update_occupancy(g)
t0 = time.perf_counter()
p64.step(src_pos=(0.58, 0.0), snk_pos=(-1.5, 0.0))
t_solve = (time.perf_counter() - t0) * 1000.0
print(f"\n64x64 solve time: {t_solve:.2f} ms")
print(f"p64 flow at (0.58, 0.0): {p64.get_topological_current(0.58, 0.0)}")

# Test 32x32 flow when corridor is open:
p32.obstacle_mask = down_mean > 0.40
t0 = time.perf_counter()
p32.step(src_pos=(0.58, 0.0), snk_pos=(-1.5, 0.0))
t32_solve = (time.perf_counter() - t0) * 1000.0
print(f"\n32x32 (mean) solve time: {t32_solve:.2f} ms")
print(f"p32 flow at (0.58, 0.0): {p32.get_topological_current(0.58, 0.0)}")
