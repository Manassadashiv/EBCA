# 🔬 DEEP DIVES #5–#9 — Remaining Files (Every Line, Every Number, Every Why)

---

# 🔬 DEEP DIVE #5 — `carl_grid_cells.py`
> *453 lines. The Nobel Prize GPS system.*

---

## Part 1: `GridCellModule` — Hexagonal Spatial Firing

### Why Hexagonal?

Hexagons are special because three families of evenly-spaced parallel stripes, oriented at 60° to each other, create a hexagonal lattice. This is the densest packing of a 2D plane — mathematically proven to be optimal for encoding 2D position with the minimum number of neurons.

Grid cells were discovered by Moser, Moser, and O'Keefe in 2005. **Nobel Prize in Physiology/Medicine, 2014.** They fire in hexagonal patterns with different scales and orientations — like a multi-scale ruler for 2D space.

---

### Lines 35–60: Constructor

```python
class GridCellModule:
    def __init__(self, scale: float, orientation_deg: float, n_cells: int = 64, ...):
```

**`scale`**: Spacing of the hexagonal pattern in meters. Three modules use scales 0.8m, 1.2m, 1.8m.

**Why three different scales?** Like a vernier caliper: coarse scale narrows down to a room, medium to a corner, fine to a specific location. Three scales with non-integer ratio (0.8:1.2:1.8 = 1:1.5:2.25) give unique combined code for any position in a 10m×10m arena (Chinese Remainder Theorem applied to continuous space).

**`orientation_deg`**: Each module is rotated by a different angle (0°, 30°, 60°). This breaks symmetry — multiple modules at the same orientation would be redundant. Three different orientations provide complementary information.

---

```python
theta = math.radians(orientation_deg)
angles = [theta + i * math.pi / 3.0 for i in range(3)]   # Three angles, 60° apart
freq = 2.0 * math.pi / scale                              # Spatial frequency [rad/m]
self.K = np.array([[math.cos(a), math.sin(a)] for a in angles]) * freq  # Shape: (3, 2)
```

**The interference model (Burgess 2007):**

Three wave vectors `K[0], K[1], K[2]`, each pointing in a different direction (60° apart). Each wave creates sinusoidal stripes across the arena.

**`freq = 2π/scale`**: Spatial frequency. For scale=0.8m: `freq = 2π/0.8 = 7.854 rad/m`. This means the pattern repeats every 0.8m.

**`K` matrix (3, 2):** Each row is a 2D wave vector [kx, ky].
- `K[0] = freq × [cos(θ), sin(θ)]`
- `K[1] = freq × [cos(θ+60°), sin(θ+60°)]`
- `K[2] = freq × [cos(θ+120°), sin(θ+120°)]`

These are the "directions" of the three stripe families.

**`self.phases`**: Shape (n_cells, 3). Each of the 64 cells has its own phase offset in each wave direction. This gives each cell a unique position within the hexagonal pattern — different cells fire at different locations in the hexagon.

---

### `fire()` — Computing Grid Cell Activity

```python
def fire(self, x=None, y=None):
    pos = np.array([x, y]) if x is not None else self.pi_phase
    proj = self.K @ pos   # Shape: (3,) — project position onto 3 wave vectors
    
    for c in range(self.n):
        phi = proj + self.phases[c]   # Add this cell's unique phase offset
        rate = (math.cos(phi[0]) + math.cos(phi[1]) + math.cos(phi[2])) / 3.0
        self.activity[c] = max(0.0, (rate + 1.0) / 2.0 + noise)
```

**`proj = self.K @ pos`**: Matrix-vector multiply (3, 2) × (2,) = (3,).

`proj[0]` = how far position `pos` is along wave vector 0's direction (in radians of the wave cycle).

**`cos(proj[0]) + cos(proj[1]) + cos(proj[2])`**:
Three cosine waves evaluated at the current position projection. At the center of a hexagonal firing field, all three cosines are near their maximum → sum near 3 → rate near 1. Between firing fields, the cosines partially cancel → rate near 0.

**`/ 3.0`**: Normalizes the sum to [-1, 1].

**`(rate + 1.0) / 2.0`**: Shifts from [-1, 1] to [0, 1]. Now it's a proper firing RATE (probability of firing), not a raw oscillation value.

**`max(0.0, ...)`**: Ensures non-negative rates. Real neurons can't fire at negative rates.

---

### Path Integration: `integrate()`

```python
def integrate(self, vx: float, vy: float, dt: float):
    dpos = np.array([vx, vy]) * dt   # Distance traveled in this tick
    dphase = self.K @ dpos           # Phase advance in each wave direction
    self.pi_phase += dphase          # Update estimated position (path integration)
```

**Path integration** = estimating current position from velocity without external landmarks. Like navigation by dead reckoning.

`dpos = velocity × dt`: Distance traveled in this timestep.

`dphase = K @ dpos`: How much does each wave's phase advance due to this movement? Moving 0.1m in the wave's direction advances the phase by `freq × 0.1 = 7.854 × 0.1 = 0.785 radians`.

The accumulated `pi_phase` tracks an estimated position WITHOUT needing GPS. Errors accumulate over time (drift), which is why actual GPS position (`x, y`) is used to `fire()` and calibrate the grid cells — the path integration is used when GPS is briefly unavailable.

---

## Part 2: `PlaceCellLayer` — "I Am HERE" Neurons

### Why 400 cells?

The hippocampus has ~1 million place cells in rats. 400 is a manageable number for a 10×10m arena with σ=0.4m firing fields. At 0.4m sigma, each cell covers ~0.5m² effectively, and 400 cells × 0.5m² = 200m² > 100m² arena area. So 400 is sufficient to cover the entire space without gaps.

---

### Firing

```python
def fire_from_position(self, x: float, y: float):
    pos = np.array([x, y])
    d2 = np.sum((self.centres - pos) ** 2, axis=1)   # Shape: (400,) — squared distances
    self.activity = np.exp(-d2 / (2 * self.sigma2))   # Gaussian firing: shape (400,)
```

**`(self.centres - pos)`**: Shape (400, 2) minus (2,) → broadcasts to (400, 2). Each row is the displacement from that cell's center to current position.

**`np.sum(..., axis=1)`**: Sum along axis=1 (sum columns for each row) → shape (400,). Each entry is the squared Euclidean distance from that cell's center.

**`np.exp(-d2 / (2σ²))`**: Gaussian (bell curve). At `d²=0` (at the center): exp(0) = 1.0 (maximum). At `d²=σ²`: exp(-0.5) = 0.61. At `d²=9σ²` (3 sigma away): exp(-4.5) ≈ 0.01 (nearly silent).

**`sigma = 0.4m`**: Each place cell fires within ~0.8m diameter. Two cells 0.5m apart have ~38% overlap — enough for smooth coverage but not too much redundancy.

---

### Topological Graph Building

```python
def update_graph(self, old_cell: int, new_cell: int, tick: int):
    if old_cell != new_cell:
        self.adjacency[old_cell].add(new_cell)
        self.adjacency[new_cell].add(old_cell)
    self.recency[new_cell] = tick
```

**`self.adjacency`**: A list of 400 Python `set` objects. `adjacency[i]` = set of all cells that were visited right after or before cell i.

**Why sets?** Sets automatically deduplicate — if CARL walks from cell 5 to cell 12 100 times, `adjacency[5]` still just contains {12, ...} (not duplicated). Also, `set.add()` is O(1) average.

**Why bidirectional?** `adjacency[old].add(new)` AND `adjacency[new].add(old)`. If you can walk A→B, you can also walk B→A (undirected graph). This allows finding paths in either direction.

**`self.recency[new_cell] = tick`**: Records when each cell was last visited. Used by `get_novelty_target()` to find the LEAST recently visited cells (exploration targets).

---

### Reward Diffusion (Hippocampal Replay)

```python
def diffuse_rewards(self, gamma: float = 0.9, decay: float = 0.99995, n_sweeps: int = 5):
    self.reward_values *= decay   # Slowly forget all rewards
    for persistent in self.persistent_rewards:
        self.reward_values[cell] = max(self.reward_values[cell], self.persistent_rewards[cell])
    
    values = self.reward_values.copy()
    new_values = values.copy()
    
    for sweep in range(n_sweeps):
        for cell_idx in range(self.n_place):
            neighbors = list(self.adjacency[cell_idx])
            if not neighbors:
                continue
            max_neighbor_val = max(values[n] for n in neighbors)
            new_values[cell_idx] = max(values[cell_idx], gamma * max_neighbor_val)
        values = new_values.copy()
    
    self.reward_values = values
    self.nav_values[:] = self.reward_values[:]
```

**`decay = 0.99995`**: Per-tick decay. After T ticks: value = original × 0.99995^T.

Half-life: `T_half = log(0.5) / log(0.99995) ≈ 13,863 ticks × 0.033s = 457 seconds ≈ 7.6 minutes`.

So food locations are remembered for about 7 minutes. After 7 minutes without revisiting, the memory fades.

**`gamma = 0.9`**: Diffusion discount factor. Reward propagates from the food cell to its neighbors at 90% strength, to their neighbors at 81%, to their neighbors at 73%, etc.

This implements **value iteration** from reinforcement learning:
```
V(s) = max(R(s), γ × max_{s'∈N(s)} V(s'))
```
After N sweeps, each cell has a value equal to the discounted reward reachable in N steps through the graph.

**`n_sweeps = 5`**: 5 iterations of value propagation per tick. The reward diffuses up to 5 "hops" through the graph every tick. Since the graph is built incrementally, this progressively "fills in" the gradient field as CARL explores.

**Why `max()` not `sum()`?** This finds the HIGHEST-VALUE neighbor (best path), not an average. Value iteration uses max for optimal policy: always take the best available next step.

After `diffuse_rewards()`, `nav_values[i]` = "estimated reward reachable from cell i." Higher nav_values = closer to food. The gradient (which neighbor has highest value) = which direction to go.

---

## 🔬 DEEP DIVE #6 — `carl_physarum.py`
> *257 lines. The slime mold shortest-path algorithm.*

### The Biology

Physarum polycephalum ("many-headed slime mold") was shown in 2000 to naturally solve maze problems (Nakagaki et al., Nature 2000). In 2010, researchers proved it recreated the Tokyo rail network. The algorithm is:
1. Slime mold fills the maze with tubular connections
2. Food at two locations → fluid flows from one to the other
3. Tubes carrying more fluid grow thicker
4. Tubes carrying less fluid shrink
5. Eventually only the SHORTEST PATH survives

---

### The Mathematics

The slime mold network is modeled as an **electrical circuit**:
- Each node (grid cell) = junction
- Each edge = resistor with conductance D (inverse resistance)
- Food source = high voltage (+1V)
- Food sink = low voltage (0V)
- Pressure at each node = voltage

**Kirchhoff's Current Law**: At every junction, sum of currents flowing in = sum flowing out.

For horizontal edge between cells (i,j) and (i,j+1):
```
current = D_h[i,j] × (pressure[i,j] - pressure[i,j+1])
```

**Applying KCL at every node** creates a system of linear equations:
```
L × p = b
```
Where L is the **graph Laplacian matrix** and b is the right-hand side (pressure sources/sinks).

---

### `_build_laplacian()`

```python
def _build_laplacian(self):
    # For each horizontal edge between (row, col) and (row, col+1):
    d = self.D_h[row, col]   # Conductance
    L[idx, idx]       += d    # Self-connection
    L[idx, idx_right] -= d    # Cross-connection (negative)
    L[idx_right, idx] -= d    # Symmetric
    L[idx_right, idx_right] += d
```

**The graph Laplacian** L is a sparse matrix where:
- `L[i,i]` = sum of all conductances connected to node i (positive)
- `L[i,j]` = -conductance of edge (i,j) (negative)

This is a **symmetric positive semi-definite** matrix — it always has a unique solution when boundary conditions (source/sink) are applied.

**Why sparse?** A 25×25 grid has 625 nodes. Full L would be 625×625 = 390,625 entries. But each node connects to at most 4 neighbors → only ~2500 non-zero entries. Using `scipy.sparse.lil_matrix` (list-of-lists sparse format) stores only non-zero values. The linear solve is O(N × nnz) instead of O(N³).

---

### `_solve_pressure()`

```python
def _solve_pressure(self, src_idx: int, snk_idx: int):
    # Build L, then set boundary conditions:
    L_mod = L.copy().tolil()
    rhs = np.zeros(self.N)
    
    # Fix source pressure to 1.0
    L_mod[src_idx, :] = 0;  L_mod[src_idx, src_idx] = 1.0;  rhs[src_idx] = 1.0
    # Fix sink pressure to 0.0
    L_mod[snk_idx, :] = 0;  L_mod[snk_idx, snk_idx] = 1.0;  rhs[snk_idx] = 0.0
    
    p = spsolve(L_mod.tocsr(), rhs)   # Solve L × p = rhs
    self.pressure = p
```

**`spsolve()`**: Direct sparse linear solver (uses LU factorization). For N=625 nodes, this is fast (~milliseconds).

**Boundary conditions**: Setting the source row of L to `[0,...,1,...,0]` and rhs to `1.0` forces `pressure[src] = 1.0`. Same for sink with 0.0. All intermediate pressures are solved to be physically consistent.

**Result**: `self.pressure` contains the "voltage" at every grid node. Gradient points from high to low pressure — from start toward goal.

---

### `_update_conductivities()`

```python
def _update_conductivities(self):
    # Flow through horizontal edges:
    p_left  = self.pressure[left_nodes]    # Pressure on left of each edge
    p_right = self.pressure[right_nodes]   # Pressure on right of each edge
    Q_h = np.abs(self.D_h * (p_left - p_right))  # Flow = conductance × pressure drop
    
    # Physarum adaptation law:
    dD_h = (Q_h**MU - self.D_h) / TAU
    self.D_h = np.clip(self.D_h + dD_h, D_MIN, D_MAX)
```

**Physarum adaptation equation (Tero et al. 2007):**
```
dD/dt = (|Q|^μ - D) / τ
```

- `D`: current conductance (pipe thickness)
- `Q`: flow through this pipe
- `μ = 1.8`: exponentiation power (> 1 → positive feedback: flow causes growth)
- `τ = 10.0`: adaptation timescale

**Why `Q^μ` with μ > 1?** If μ = 1: equilibrium D = Q. Pipes carrying more flow grow to match. If μ > 1: high-flow pipes grow SUPER-linearly → winner-takes-all dynamics → shortest path pipes survive, others die.

**`D_MIN = 0.001, D_MAX = 5.0`**: Clipping prevents pipes from disappearing completely (numerical stability) and from growing infinitely.

---

## 🔬 DEEP DIVE #7 — `train_multi_object_vision.py`
> *172 lines. How CARL's eye is trained.*

### Lines 17–85: `CarlMultiObjectDataset`

```python
def __getitem__(self, idx):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # BGR → RGB
    img_tensor = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1) / 255.0
```

**Why `BGR2RGB`?** OpenCV reads images as BGR (Blue-Green-Red) — a historical quirk. PyTorch and most ML frameworks expect RGB. Swapping is mandatory or colors will be wrong (red tomato appears blue to the network).

**`.permute(2, 0, 1)`**: Reorders dimensions from (H=120, W=160, C=3) to (C=3, H=120, W=160). PyTorch models require channels-first format.

---

```python
    xmin = (xc - w/2.0) * self.W
    ymin = (yc - h/2.0) * self.H
    xmax = (xc + w/2.0) * self.W
    ymax = (yc + h/2.0) * self.H
```

**YOLO format → absolute pixels:**

YOLO labels store: `class_id center_x center_y width height` — all normalized [0, 1].

Converting: `xmin = (cx - w/2) × W_pixels`. This recovers the pixel bounding box corners.

---

```python
    labels_list.append(class_id + 1)
```

**Why `+1`?** Torchvision detection models RESERVE class 0 for BACKGROUND. So:
- File label 0 (Food) → model label 1
- File label 1 (Obstacle) → model label 2
- File label 2 (Predator) → model label 3

---

### Lines 87–88: `collate_fn`

```python
def collate_fn(batch):
    return tuple(zip(*batch))
```

**Why custom collate?** Default DataLoader stacking requires all tensors in a batch to have the same shape. But images with 0 objects vs. 3 objects have different `boxes` tensor sizes. `zip(*batch)` transposes the list-of-tuples into a tuple-of-lists (each list contains tensors of varying shapes), which SSD can handle as a variable-length batch.

---

### Lines 90–110: SSDLite Model Configuration

```python
norm_layer = functools.partial(nn.BatchNorm2d, eps=0.001, momentum=0.03)
```

**`functools.partial()`**: Creates a "frozen" function with some arguments pre-filled. `nn.BatchNorm2d(eps=0.001, momentum=0.03)` becomes a callable that acts like `nn.BatchNorm2d` but always uses those specific hyperparameters.

**`eps=0.001`**: Added to variance in denominator of BatchNorm to prevent division by zero. Standard value.

**`momentum=0.03`**: Running statistics update rate. Smaller than default (0.1) → smoother running mean/variance estimates. Appropriate for small batches.

---

### Lines 124–127: Optimizer and Scheduler

```python
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
```

**Adam optimizer (Kingma & Ba, 2015):**
- Combines momentum (smooth gradient direction) with adaptive learning rates (per-parameter)
- `lr=0.001`: Starting learning rate. Adam is relatively insensitive to this choice (hence its popularity for fine-tuning).

**StepLR scheduler:**
- Every `step_size=10` epochs, multiply `lr` by `gamma=0.5`
- After 10 epochs: lr = 0.001 × 0.5 = 0.0005
- After 20 epochs: lr = 0.0005 × 0.5 = 0.00025
- After 30 epochs: lr = 0.000125

**Why halve LR every 10 epochs?** "Learning rate decay" ensures the network makes big updates early (fast learning) and small refinements late (fine-tuning). Without decay, the optimizer would keep making large steps even near convergence, causing oscillation.

**Why 30 epochs total?** With 1200 images and batch_size=16, each epoch = 75 batches. 30 epochs = 2250 gradient steps. SSD fine-tuning typically converges in 20-40 epochs.

---

### Lines 147–152: Loss Computation

```python
loss_dict = model(images, targets)   # SSD returns a dict of losses
total_loss = sum(loss for loss in loss_dict.values())
total_loss.backward()
optimizer.step()
```

**SSD loss dict contains:**
1. `classification`: Cross-entropy loss. "Which class is each anchor box?"
2. `bbox_regression`: Smooth L1 loss. "How much to adjust each anchor box to match the ground truth box?"

**`sum()`**: Just add them together. Both losses use the same units (nats/bits for classification, meters-ish for regression). Unweighted sum worked empirically for this scale.

**`.backward()`**: Backpropagation — computes gradients of `total_loss` with respect to ALL trainable parameters in the model.

**`optimizer.step()`**: Updates parameters: `param -= lr × gradient × (Adam scaling)`.

---

## 🔬 DEEP DIVE #8 — `collect_multi_object_dataset.py`
> *260 lines. How training images are generated.*

### `project_to_camera()` — 3D World → 2D Pixel

```python
def project_to_camera(model, data, cam_id, world_pos, W, H):
    cam_pos = data.cam_xpos[cam_id]           # Camera position in world
    cam_mat = data.cam_xmat[cam_id].reshape(3, 3)  # Camera rotation matrix (3×3)
    
    rel_pos = world_pos - cam_pos             # Vector from camera to point
    
    x_c = np.dot(rel_pos, cam_mat[:, 0])     # Component along camera RIGHT axis
    y_c = np.dot(rel_pos, cam_mat[:, 1])     # Component along camera UP axis
    z_c = -np.dot(rel_pos, cam_mat[:, 2])    # Component along camera FORWARD (-Z in OpenGL)
```

**Camera coordinate system:**
- Column 0 of cam_mat = camera's RIGHT axis (in world frame)
- Column 1 = camera's UP axis
- Column 2 = camera's FORWARD axis (but convention: -Z = forward in OpenGL/MuJoCo)

`rel_pos` is the vector from camera to the world point. Projecting onto each axis gives the camera-frame coordinates.

**Why negative for z_c?** In MuJoCo's camera convention (OpenGL), -Z points forward. So `z_c = -dot(rel_pos, cam_mat[:,2])` gives positive depth when the point is in front of the camera.

---

```python
    fovy_rad = np.deg2rad(model.cam_fovy[cam_id])   # Field of view in radians (60°)
    f = H / (2.0 * np.tan(fovy_rad / 2.0))          # Focal length in pixels
```

**Pinhole camera focal length:**
The full image height covers angle `fovy_rad`. The image center is at y=H/2. 

Half the image height covers `fovy_rad/2` angle. The focal length `f` relates pixel coordinates to angles:
```
f = (H/2) / tan(fovy/2) = 120/2 / tan(30°) = 60 / 0.577 = 103.9 pixels
```

---

```python
    u = W / 2.0 + (x_c / z_c) * f   # Horizontal pixel coordinate
    v = H / 2.0 - (y_c / z_c) * f   # Vertical pixel coordinate (flipped: image Y grows down)
```

**Perspective projection (pinhole model):**
```
u = W/2 + (X_cam / Z_cam) × f
v = H/2 - (Y_cam / Z_cam) × f
```

The `-` for v: In image coordinates, Y increases DOWNWARD (top-left is [0,0]). Camera space Y increases UPWARD. The flip converts between conventions.

---

### `is_geom_visible()` — Occlusion Check

```python
    ray_start = cam_pos + 0.15 * cam_forward   # Start 15cm ahead (avoid self-hit)
    geom_pos = data.geom_xpos[geom_id]
    dir_vec = geom_pos - ray_start
    dist = np.linalg.norm(dir_vec)
    dir_vec = dir_vec / dist                    # Normalize to unit vector
    
    hit_dist = mujoco.mj_ray(model, data, ray_start, dir_vec, ...)
    
    if hit_dist >= 0 and hit_dist < (dist - 0.05):
        # Ray hit something CLOSER than the target → target is occluded
        hit_name = mujoco.mj_id2name(...)
        if 'wall' in hit_name or 'obstacle' in hit_name:
            return False   # Hidden behind a wall
    return True
```

**Raycasting visibility test:** Cast a ray from the camera to the target geom. If the ray hits SOMETHING (wall/obstacle) CLOSER than the target (by 5cm tolerance), the target is hidden — don't label it.

**Why 5cm tolerance?** Floating point precision issues mean the target geom itself might be hit at distance = dist - ε. The 5cm buffer (`dist - 0.05`) ensures we only discard if a truly separate object is in between.

---

### `get_geom_bbox()` — 3D Object → 2D Bounding Box

```python
if g_type == mujoco.mjtGeom.mjGEOM_SPHERE:
    r = size[0]
    for offset in [+x, -x, +y, -y, +z, -z]:   # 6 "pole" points
        points.append(pos + r * offset)
        
elif g_type == mujoco.mjtGeom.mjGEOM_BOX:
    sx, sy, sz = size
    for dx in [-sx, sx]:
        for dy in [-sy, sy]:
            for dz in [-sz, sz]:
                points.append(pos + mat @ [dx, dy, dz])   # 8 corners, rotated
                
elif g_type == mujoco.mjtGeom.mjGEOM_CYLINDER:
    r, h = size[0], size[1]
    for theta in linspace(0, 2π, 8):
        for dz in [-h, h]:
            points.append(pos + mat @ [r×cos(θ), r×sin(θ), dz])  # 16 rim points
```

**Approach:** For each geometry type, compute a set of "key points" that bound the shape, project all of them to 2D pixels, then take the min/max pixel coordinates as the bounding box.

**Sphere**: 6 points at the surface poles (+/-x, +/-y, +/-z). Their projected pixels encompass the sphere in the image.

**Box**: 8 corners of the box. Rotated by `mat` (the geometry's rotation matrix) to account for orientation. The projected bounding box of all 8 corners tightly fits the rotated box.

**Cylinder**: 16 points on the top and bottom circular rims (8 angles × 2 heights). Correctly handles tilted cylinders.

---

### Random Scene Generation (Lines 159–212)

```python
x_off = np.random.uniform(-3.5, 3.5)
y_off = np.random.uniform(-3.5, 3.5)
yaw = np.random.uniform(-np.pi, np.pi)
hp = yaw / 2.0
data.qpos[q_addr+3 : q_addr+7] = [math.cos(hp), 0.0, 0.0, math.sin(hp)]
```

**Quaternion encoding of yaw rotation:**  
A rotation of angle `yaw` around the Z axis is encoded as quaternion:
```
q = [cos(yaw/2), 0, 0, sin(yaw/2)] = [qw, qx, qy, qz]
```

`hp = yaw/2.0`: "Half angle" for quaternion.

**Why quaternion?** MuJoCo stores joint rotations as unit quaternions (4 values) rather than Euler angles (3 values). Quaternions avoid gimbal lock, handle composition of rotations efficiently, and MuJoCo's internal representation.

---

```python
num_objects = random.choices([0, 1, 2, 3], weights=[0.1, 0.4, 0.4, 0.1], k=1)[0]
```

**`random.choices()`** with weights: Weighted random selection.
- 10% chance: 0 objects (background-only images)
- 40% chance: 1 object
- 40% chance: 2 objects
- 10% chance: 3 objects

Why this distribution? Most real scenes have 1-2 objects. Giving 40% to 1 and 40% to 2 ensures plenty of multi-object training. 10% background teaches the model to output "nothing" when there's nothing there.

---

## 🔬 DEEP DIVE #9 — `genesis_run.py`
> *269 lines. The Scout robot — pick-and-place with LiDAR.*

### State Machine Architecture

```python
self.state = "SEARCH"   # Initial state
```

The controller is a **Finite State Machine (FSM)** with 6 states:

```
SEARCH → APPROACH → REACH → GRASP → LIFT → CELEBRATE → (SEARCH again)
```

Each state checks conditions and transitions when met. The robot can only be in ONE state at a time.

---

### LiDAR Bearing Estimation (Lines 79–94)

```python
for idx in forward_rays:   # [0, 1, 2, 22, 23] — front ±30° rays
    r = ranges[idx]
    if 0.02 < r < 0.50:   # Valid detection: 2cm to 50cm
        deg = idx * 15.0  # Each ray is 15° apart
        if deg > 180: deg -= 360   # Wrap to [-180, 180]
        w = 1.0 / (r * r)           # Weight = inverse square of distance
        sum_w += w
        sum_ang += w * math.radians(deg)
        best_r = min(best_r, r)

bearing = sum_ang / sum_w   # Weighted average angle
```

**Inverse-square weighting:** Closer detections get more weight. If the cube is at 0.1m and 30°, and there's noise at 0.4m and -10°:
- Weights: `1/0.1² = 100` and `1/0.4² = 6.25`
- Weighted bearing: `(100×30° + 6.25×(-10°)) / 106.25 ≈ 27.7°`

The close, true detection dominates the noisy distant one. This is more robust than simple averaging.

**Why `deg > 180: deg -= 360`?** Ray 22 = 22×15° = 330° → subtract 360 → -30°. This puts all angles in [-180°, +180°] range for consistent signed arithmetic.

---

### Dynamic yaw tracking (Line 98)

```python
rel_cube_y = (self.detected_range + 0.135) * self.detected_bearing
self.sy_target = np.clip(4.0 * rel_cube_y - 0.160, -0.3, 0.1)
```

`rel_cube_y`: Estimated lateral offset of cube relative to CARL's center. `range × bearing` gives the arc offset. Adding 0.135 (robot base-to-shoulder distance) converts from sensor frame to shoulder frame.

`4.0 × rel_cube_y`: Proportional gain — 4 radians of shoulder yaw per meter of lateral offset.

`- 0.160`: Baseline neutral position of the left shoulder yaw joint.

`np.clip(..., -0.3, 0.1)`: Joint limits — shoulder can swing right to -0.3 rad or left to +0.1 rad.

---

### REACH State — Two-Stage Trajectory (Lines 165–185)

```python
if dt < 0.8:
    body.set_joint("act_sp_L", 0.650)   # Shoulder pitch: reach forward
    body.set_joint("act_el_L", -1.300)  # Elbow: bend downward
    body.set_joint("act_wp_L", 0.50)    # Wrist pitch: angle down
else:
    body.set_joint("act_sp_L", 0.980)   # Reach FURTHER forward
    body.set_joint("act_el_L", -1.300)  # Same elbow
    body.set_joint("act_wp_L", 0.50)    # Same wrist
```

**Two-stage approach prevents collision:**
- Stage 1 (0-0.8s): Bring arm to pre-grasp position ABOVE the cube
- Stage 2 (0.8-1.8s): Extend shoulder further to descend to grasp height

Without the two-stage, a direct reach might clip the cube with the forearm before the hand is properly positioned.

---

### GRASP State — Finger Trajectory (Lines 187–196)

```python
p = min(1.0, dt / 1.0)   # Progress: 0→1 over 1 second
body.set_joint("act_th_L",   -0.80 + p * 2.0)   # Thumb: opens to -0.8, closes to +1.2
body.set_joint("act_idx1_L",  0.25 + p * -1.65)  # Index proximal: opens +0.25, closes -1.4
body.set_joint("act_idx2_L",  0.05 + p * -1.45)  # Index distal: opens +0.05, closes -1.4
```

**Linear interpolation from OPEN to CLOSED position:**
```
joint_angle(t) = start + progress × (end - start)
```

This creates smooth finger closing over 1 second. `p = dt/1.0` maps 0→1 second to 0→1 progress. `min(1.0, ...)` caps at 1.0 (fully closed) even if state stays longer.

**Why linear?** Simple, smooth, and fast enough. A real robot would use a spring-damper impedance controller (grasping with controlled force), but linear position interpolation achieves reliable grasps in simulation.

---

## SUMMARY TABLE — All Files

| File | Lines | Algorithm | Key Math |
|---|---|---|---|
| `carl_reflex.py` | 177 | LIF SNN + R-STDP | Poisson spikes, W@spikes, V×decay |
| `carl_endocrine.py` | 188 | First-order ODEs | dX/dt = -k(X-X_b) |
| `carl_reservoir.py` | 197 | LSM + RLS | W_res eigenvalues, P-matrix, gain=P·φ/(λ+φᵀPφ) |
| `carl_grid_cells.py` | 453 | Grid+Place cells | Hexagonal interference, Gaussian firing, value iteration |
| `carl_physarum.py` | 257 | Network flow | Kirchhoff laws, Laplacian, Physarum dynamics |
| `carl_stdp.py` | 278 | STDP + Quantum deliberation | 3-factor learning, Born rule probabilities |
| `carl_omega_extensions.py` | 126 | Mirror neurons, Allostasis | Forward simulation, prediction horizon |
| `carl_simulation.py` | 903 | System integration | S_unified, precision weighting, motor mixing |
| `train_multi_object_vision.py` | 172 | Transfer learning | SSDLite, Adam, StepLR, cross-modal loss |
| `collect_multi_object_dataset.py` | 260 | 3D→2D projection | Pinhole model, raycasting, bounding box extraction |
| `genesis_run.py` | 269 | Pick-and-place FSM | Weighted bearing, 2-stage reach, linear grasp interp |
