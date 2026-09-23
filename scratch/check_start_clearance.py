import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np
import torch

from scratch.fast_eval_branches import grid, px, py, pyaw, mem

# Let's inspect the occupancy grid around (-1.5, -1.8)
ix = int((px + 6.4) / 0.10)
iy = int((py + 6.4) / 0.10)
print(f"Robot start grid index: ix={ix}, iy={iy}")
print("Occupancy grid values in 11x11 window around robot start:")
subgrid = grid[0, 0, iy-5:iy+6, ix-5:ix+6].numpy()
print(np.round(subgrid, 1))

# Also query clearance at starting pose:
p0 = torch.tensor([[px, py, pyaw]], dtype=torch.float32)
clr0 = mem.query_clearance(grid, p0).numpy()[0]
print("\nClearance at starting pose (15 rays):")
print(np.round(clr0, 2))
print("Ray angles relative to heading: [-90°, -77°, ..., +90°]")
print("Min clearance:", np.min(clr0), "m on ray", np.argmin(clr0))
