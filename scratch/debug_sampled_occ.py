import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import torch.nn.functional as F

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL()
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])

mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
grid = torch.zeros(1, 2, 128, 128)
vps = [(-1.5, -1.5), (-1.5, 0), (-1.5, 1.5), (0, -1.5), (0, 0), (0, 1.5), (1.5, -1.5), (1.5, 0), (1.5, 1.5)]
for vx, vy in vps:
    for angle in np.linspace(-np.pi, np.pi, 24, endpoint=False):
        hal.data.qpos[qa:qa+2] = [vx, vy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(angle/2), 0, 0, math.sin(angle/2)]
        import mujoco
        mujoco.mj_forward(hal.model, hal.data)
        s = hal.read_sensors()[:15]
        grid = mem.accumulate_observations(grid, torch.tensor([[vx, vy, angle]]).float(), torch.tensor(s).unsqueeze(0).float())

# Step 5 pose
pose = torch.tensor([[-0.151, 0.960, 17.6 * math.pi / 180.0]]).float()
num_samples_per_ray = 80
radii = torch.linspace(0.05, mem.max_range, num_samples_per_ray)
K = num_samples_per_ray
ray_dirs = pose[:, 2:3] + mem.sonar_angles.unsqueeze(0)
ox = pose[:, 0:1].unsqueeze(1) + mem.r_hull * torch.cos(ray_dirs).unsqueeze(-1)
oy = pose[:, 1:2].unsqueeze(1) + mem.r_hull * torch.sin(ray_dirs).unsqueeze(-1)
sample_x = ox + radii.view(1, 1, K) * torch.cos(ray_dirs).unsqueeze(-1)
sample_y = oy + radii.view(1, 1, K) * torch.sin(ray_dirs).unsqueeze(-1)
u_norm = (sample_x / mem.half_size).clamp(-1.0, 1.0)
v_norm = (sample_y / mem.half_size).clamp(-1.0, 1.0)
query_coords = torch.stack([u_norm, v_norm], dim=-1)

sampled_occ = F.grid_sample(
    grid[:, 0:1, :, :],
    query_coords,
    mode="bilinear",
    padding_mode="zeros",
    align_corners=True
).squeeze(1)

for ray_idx in range(15):
    occ_ray = sampled_occ[0, ray_idx].numpy()
    hits = np.where(occ_ray > 0.05)[0]
    if len(hits) > 0:
        first_k = hits[0]
        r_hit = radii[first_k].item()
        val = occ_ray[first_k]
        print(f"Ray {ray_idx:02d}: first hit at k={first_k:2d}, r={r_hit:.2f}m, val={val:.3f}, all hits k={hits[:5]}")
    else:
        print(f"Ray {ray_idx:02d}: NO HIT (max range 5.0m)")
