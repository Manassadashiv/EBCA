import torch
from pathlib import Path
g_r2 = torch.load('evidence/stage2_2_r2/arena_occupancy_grid.pt')
g_gr = torch.load('evidence/stage2_2_grounded/grounded_occupancy_grid.pt')

print("arena_occupancy_grid shape:", g_r2.shape, "min:", g_r2.min().item(), "max:", g_r2.max().item())
print("grounded_occupancy_grid shape:", g_gr.shape, "min:", g_gr.min().item(), "max:", g_gr.max().item())

# Check diff around (-1.5, -1.8)
ix = int((-1.5 + 6.4) / 0.10)
iy = int((-1.8 + 6.4) / 0.10)
print(f"Around start pose ({ix}, {iy}):")
print("arena_occupancy_grid:")
print(torch.round(g_r2[0, 0, iy-3:iy+4, ix-3:ix+4], decimals=1))
print("grounded_occupancy_grid:")
print(torch.round(g_gr[0, 0, iy-3:iy+4, ix-3:ix+4], decimals=1))

diff = torch.abs(g_r2 - g_gr)
print(f"Max abs difference: {diff.max().item():.4f}, Mean abs diff: {diff.mean().item():.4f}")
