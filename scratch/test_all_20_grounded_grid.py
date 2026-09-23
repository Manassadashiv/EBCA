import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import torch

from scratch.test_all_20 import eval_all_20
import scratch.test_all_20 as t20

# Replace grid with grounded_occupancy_grid.pt
g_gr = torch.load('evidence/stage2_2_grounded/grounded_occupancy_grid.pt')
if g_gr.dim() == 3:
    g_gr = g_gr.unsqueeze(0)
t20.grid = g_gr

passes, r2s, mars = t20.eval_all_20()
print(f"Under grounded_occupancy_grid.pt: Passes = {passes}/20")
