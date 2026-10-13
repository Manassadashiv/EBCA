import sys
import math
sys.path.insert(0, ".")
import torch
import numpy as np
from scipy.ndimage import label, binary_dilation

def compute_principled_physarum_sink(grid_np, robot_pos, half_size=6.4, res=0.10):
    """
    Principled biological sink selection:
    Finds the macroscopic unvisited traversable reservoir attracting plasmodial foraging.
    1. Unvisited traversable space: occ < 0.30 and visited < 0.50.
    2. Clusters contiguous unvisited regions.
    3. Selects the dominant reservoir separated from current position.
    4. Selects the cell in that reservoir with maximum clearance from walls.
    """
    c_x, c_y = robot_pos
    grid_size = grid_np.shape[1]
    
    occ = grid_np[0]
    vis = grid_np[1]
    
    traversable = occ < 0.30
    unvisited = vis < 0.50
    
    # Target reservoir: unvisited traversable cells
    reservoir = traversable & unvisited
    
    # Distance from current robot pose (Euclidean or geodesic)
    ys, xs = np.indices((grid_size, grid_size))
    world_x = xs * res - half_size
    world_y = ys * res - half_size
    dists = np.hypot(world_x - c_x, world_y - c_y)
    
    # Filter for macroscopic distance (>= 0.8m) to avoid micro-chatter near chassis
    macro_reservoir = reservoir & (dists >= 0.80)
    if not np.any(macro_reservoir):
        macro_reservoir = reservoir
        
    if not np.any(macro_reservoir):
        # Everything explored; default to furthest free space
        furthest_idx = np.argmax(np.where(traversable, dists, -1.0))
        fy = int(furthest_idx // grid_size)
        fx = int(furthest_idx % grid_size)
        return float(world_x[fy, fx]), float(world_y[fy, fx])
        
    lbl, num_features = label(macro_reservoir, structure=np.ones((3, 3)))
    if num_features == 0:
        return 0.0, 0.0
        
    # Find largest unvisited cluster
    cluster_sizes = np.bincount(lbl.flatten())[1:]
    best_cluster_id = int(np.argmax(cluster_sizes) + 1)
    
    py, px = np.where(lbl == best_cluster_id)
    
    # Within this reservoir cluster, select the point with maximum clearance (furthest from walls)
    # clearance is approximated by distance to nearest obstacle
    wall_dist = np.hypot(world_y[py, px], 0.0) # distance to y=0 centerline
    # Pick the point closest to the natural corridor centerline
    best_idx = int(np.argmin(wall_dist))
    
    snk_x = float(world_x[py[best_idx], px[best_idx]])
    snk_y = float(world_y[py[best_idx], px[best_idx]])
    return snk_x, snk_y

# Test on cul-de-sac grid
g = torch.load("world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt").numpy()[0]
# Simulate robot at spawn (0.58, 0.0) with spawn footprint visited
g_spawn = g.copy()
g_spawn[1, :, :] = 0.0
# visited 0.25m around spawn
rc_x = int((0.58 + 6.4) / 0.10)
rc_y = int((0.0 + 6.4) / 0.10)
for dy in range(-3, 4):
    for dx in range(-3, 4):
        if dx*dx + dy*dy <= 9:
            g_spawn[1, rc_y + dy, rc_x + dx] = 1.0

snk_x, snk_y = compute_principled_physarum_sink(g_spawn, (0.58, 0.0))
print(f"Principled Physarum Sink at spawn: ({snk_x:.2f}, {snk_y:.2f})")

# Test flow field with this sink
from brain.carl_physarum import CarlPhysarumRoutingEngine
p = CarlPhysarumRoutingEngine(grid_dim=32, half_size=6.4)
p.step(src_pos=(0.58, 0.0), snk_pos=(snk_x, snk_y), occ_grid_128=g_spawn[0])
vx, vy, th = p.get_topological_current(0.58, 0.0)
print(f"Topological current at spawn: vx={vx:.3f}, vy={vy:.3f}, th={th:.2f} rad ({math.degrees(th):.1f} deg)")
