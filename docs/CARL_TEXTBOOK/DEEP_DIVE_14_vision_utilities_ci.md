# 🔬 DEEP DIVE #14 — Vision Files, Utilities, CI Pipeline, Git Config
> *Every remaining file. Every line. Zero skipped.*

---

# PART A — `brain/train_vision.py` (163 lines)
> *Single-object CNN: builds, trains, saves the old food/obstacle/predator detector.*

---

## Lines 14–50: `CarlVisionDataset` — PyTorch Data Loader

```python
class CarlVisionDataset(Dataset):
    def __init__(self, dataset_dir, W=160, H=120):
        self.filenames = [f[:-4] for f in os.listdir(self.images_dir) if f.endswith(".jpg")]
```

**`Dataset`**: PyTorch abstract base class. Any class inheriting from it must implement `__len__()` and `__getitem__()`. PyTorch's `DataLoader` automatically calls these to build batches.

**`f[:-4]`**: Removes the last 4 characters (`.jpg`) to get the filename stem. `"img_0042.jpg"[:-4] = "img_0042"`. Used to find the matching label file `img_0042.txt`.

```python
def __getitem__(self, idx):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_tensor = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1) / 255.0
```

**`cv2.COLOR_BGR2RGB`**: OpenCV reads images as BGR (Blue-Green-Red). PyTorch/torchvision expects RGB. Converts the channel order.

**`.permute(2, 0, 1)`**: Changes shape from `(H, W, C) = (120, 160, 3)` to `(C, H, W) = (3, 120, 160)`. PyTorch expects channels FIRST. `permute(2,0,1)` = take dimension 2 first, then 0, then 1.

**`/ 255.0`**: Normalize pixel values from [0, 255] to [0.0, 1.0]. Neural networks work better with small input values (gradients don't explode).

```python
class_id = 3   # Default: Background
bbox = torch.tensor([0.5, 0.5, 0.0, 0.0], dtype=torch.float32)
```

**Default label**: Class 3 = background (no object in image). Default bbox = centered with zero size. If no label file exists (background sample), these defaults are returned.

```python
parts = line.split()
class_id = int(parts[0])
bbox = torch.tensor([float(x) for x in parts[1:]], dtype=torch.float32)
```

**YOLO label format**: `class_id x_center y_center width height` — all on one line, space-separated. `parts[1:]` gives the 4 bbox values.

---

## Lines 52–96: `CarlVisionNet` — CNN Architecture

```python
class CarlVisionNet(nn.Module):
    def __init__(self):
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),   # (3,120,160) → (16,120,160)
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                            # → (16, 60, 80)
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),  # → (32, 60, 80)
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                            # → (32, 30, 40)
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # → (64, 30, 40)
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                            # → (64, 15, 20)
        )
        self.flat_dim = 64 * 15 * 20   # = 19200
```

**`Conv2d(3, 16, kernel_size=3, padding=1)`:**
- Input: 3 channels (RGB)
- Output: 16 channels (feature maps)
- `kernel_size=3`: 3×3 filter. Each output pixel is computed from a 3×3 neighborhood of input.
- `padding=1`: Adds 1 pixel of zeros around the border. Keeps spatial size the same (120→120, 160→160).

**Why 16→32→64 filters?** Standard "doubling" progression. Early layers detect simple patterns (edges, corners — need few filters). Later layers detect complex patterns (shapes, textures — need more filters). Starting small keeps parameter count low.

**`BatchNorm2d(16)`**: Normalizes each channel's activations across the batch. Stabilizes training dramatically — gradients don't vanish or explode. Each channel gets its own learnable scale (γ) and shift (β).

**Why BatchNorm BEFORE ReLU?** Normalization centers the pre-activation distribution at 0. ReLU then clips negatives. If done after ReLU, the distribution would always be positive — harder to normalize properly.

**`MaxPool2d(2, 2)`**: 2×2 max pooling with stride 2. Takes the maximum of each 2×2 block → halves both height and width. `(60, 80) → (30, 40)`. Creates **spatial invariance**: a feature at pixel (10,10) and (11,11) looks the same after pooling. Also reduces computation by 4×.

```python
self.classifier = nn.Sequential(
    nn.Linear(self.flat_dim, 128),   # 19200 → 128
    nn.ReLU(),
    nn.Dropout(0.2),                 # Randomly zero 20% of neurons during training
    nn.Linear(128, 4)                # 128 → 4 classes
)

self.bbox_regressor = nn.Sequential(
    nn.Linear(self.flat_dim, 128),
    nn.ReLU(),
    nn.Linear(128, 4),
    nn.Sigmoid()                     # Output in (0, 1)
)
```

**Dual-head architecture**: One input (flattened features) → two separate outputs:
- **Classifier**: 4 logits (Food/Obstacle/Predator/Background). Takes CrossEntropyLoss.
- **BBox regressor**: 4 values in [0,1] (xc, yc, w, h). Takes MSELoss.

**`Dropout(0.2)`**: During training, randomly zeroes 20% of the 128 neurons per batch. Prevents overfitting — the network can't rely on any one neuron always being available. During inference (`model.eval()`), dropout is disabled (all 128 active).

**`Sigmoid()` on bbox**: Forces output to (0, 1). YOLO coordinates are normalized — boxes can't be at -0.5 or 1.5. Without sigmoid, the regressor could output arbitrary numbers.

```python
def forward(self, x):
    x = self.features(x)          # Shape: (B, 64, 15, 20)
    x = x.view(x.size(0), -1)     # Flatten: (B, 19200)
    cls_out = self.classifier(x)   # Shape: (B, 4)
    bbox_out = self.bbox_regressor(x) # Shape: (B, 4)
    return cls_out, bbox_out
```

**`x.view(x.size(0), -1)`**: Reshapes from `(B, 64, 15, 20)` to `(B, 19200)`. `x.size(0)` = batch size. `-1` = "infer this dimension" = `64 × 15 × 20 = 19200`. This is the "flatten" operation connecting the convolutional backbone to the fully-connected heads.

---

## Lines 109–143: Training Loop

```python
cls_criterion = nn.CrossEntropyLoss()
bbox_criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
```

**`CrossEntropyLoss`**: Combines softmax + negative log-likelihood. For a 4-class problem: `loss = -log(p_correct_class)`. If model predicts the correct class with probability 0.9: `loss = -log(0.9) = 0.105`. If it predicts 0.1: `loss = -log(0.1) = 2.3`. Punishes uncertainty.

**`MSELoss`**: Mean Squared Error = `mean((prediction - target)²)`. For bbox: averages over all 4 coordinates and all batch items.

**`Adam(lr=0.001)`**: Adaptive Moment Estimation optimizer. Adjusts learning rate per-parameter based on gradient history. Generally much better than vanilla SGD for image tasks.

```python
active_mask = (classes != 3).float().unsqueeze(1)   # Shape: (B, 1)
loss_bbox = bbox_criterion(bbox_out * active_mask, bboxes * active_mask)
```

**Active mask**: `classes != 3` → True/False per sample. `.float()` → 1.0/0.0. `.unsqueeze(1)` → shape (B, 1) for broadcasting with (B, 4) bbox tensors.

**Why mask background samples?** For background images (class=3), the label bbox = `[0.5, 0.5, 0.0, 0.0]` (arbitrary default). Training the bbox head on these would confuse it — it would learn to predict zero-size boxes whenever it's uncertain. The mask zeroes out background bbox loss entirely.

```python
total_loss = loss_cls + 2.0 * loss_bbox
```

**Why `2.0 × bbox`?** Bbox loss is typically smaller in magnitude than classification loss (MSE on 4 values in [0,1] vs. cross-entropy). Multiplying by 2.0 rebalances the gradient contributions so the bbox head gets trained as aggressively as the classifier.

---

# PART B — `brain/collect_vision_dataset.py` (217 lines)
> *How CARL generates its own training data — a self-supervised camera calibration.*

---

## Lines 12–31: `project_to_camera()` — Pinhole Camera Projection

```python
def project_to_camera(model, data, cam_id, world_pos, W, H):
    cam_pos = data.cam_xpos[cam_id]           # Camera position in world [x,y,z]
    cam_mat = data.cam_xmat[cam_id].reshape(3,3)  # Camera rotation matrix
    rel_pos = world_pos - cam_pos             # Vector from camera to object
    
    x_c = np.dot(rel_pos, cam_mat[:, 0])     # Right direction component
    y_c = np.dot(rel_pos, cam_mat[:, 1])     # Up direction component
    z_c = -np.dot(rel_pos, cam_mat[:, 2])    # Forward depth (negated: camera looks -Z)
    
    if z_c <= 0.02: return None              # Object behind camera
    
    fovy_rad = np.deg2rad(model.cam_fovy[cam_id])   # 65° field of view
    f = H / (2.0 * np.tan(fovy_rad / 2.0))          # Focal length in pixels
    
    u = W/2.0 + (x_c / z_c) * f             # Pixel column
    v = H/2.0 - (y_c / z_c) * f             # Pixel row (inverted: +Y up = -row)
    return int(u), int(v)
```

**Pinhole camera model (computer vision standard):**
```
u = (x_c / z_c) × f + W/2
v = -(y_c / z_c) × f + H/2
```

1. `rel_pos = world - cam`: Vector FROM camera TO object in world space.
2. `cam_mat[:, 0/1/2]`: Camera's right, up, and forward axes in world space.
3. `np.dot(rel_pos, axis)`: Projects the world vector onto each camera axis → camera-space coordinates.
4. `f = H / (2 × tan(fovy/2))`: Focal length. For `fovy=65°`, `f = 120 / (2×tan(32.5°)) = 120/1.273 = 94.3 pixels`.
5. `(x_c / z_c) × f`: Perspective projection — objects farther away (large z_c) appear smaller (smaller x_c/z_c).
6. `W/2.0 + ...`: Shifts origin from image center to top-left corner.
7. `-y_c/z_c`: Negative because image rows increase downward, but 3D Y increases upward.

**`z_c <= 0.02`**: Object within 2cm of camera or behind it → can't project meaningfully → return None.

---

## Lines 33–92: `get_geom_bbox()` — 3D Corner Computation

**Sphere (lines 51–53):**
```python
r = size[0]
for offset in [np.array([r,0,0]), np.array([-r,0,0]), ...]:
    points.append(pos + offset)
```
Projects 6 extreme points (±X, ±Y, ±Z by radius) onto the camera. The 2D bounding box of these 6 points = the sphere's projected bbox.

**Box (lines 54–59):**
```python
sx, sy, sz = size   # Half-extents
for dx in [-sx, sx]:
    for dy in [-sy, sy]:
        for dz in [-sz, sz]:
            points.append(pos + np.dot(mat, np.array([dx, dy, dz])))
```
All 8 corners of the box (2×2×2 combinations of ±half-extents), rotated by the object's orientation matrix. Projects all 8 corners and takes the 2D min/max bounding rectangle.

**Why include rotation `np.dot(mat, ...)`?** If the obstacle is rotated 45°, its corners are at diagonal positions. Without rotation, we'd compute the corners of an axis-aligned box — wrong for rotated objects.

**`if (u_max - u_min) < 2 or (v_max - v_min) < 2: return None`**: If the projected bbox is < 2 pixels wide or tall, it's too small to be useful as a training sample. Skip it.

---

## Lines 130–211: `generate_dataset()` — Sample Generation Loop

```python
for cat_name, geom_name, class_id in categories:
    for _ in range(samples_per_cat):   # 300 per category = 1200 total
        x_off = np.random.uniform(-3.5, 3.5)
        y_off = np.random.uniform(-3.5, 3.5)
        yaw   = np.random.uniform(-np.pi, np.pi)
```

**Random camera pose**: Places CARL at random positions and orientations. This creates **pose diversity** — the model learns to recognize objects from all angles and distances.

```python
data.qpos[q_addr : q_addr+3] = [x_off, y_off, 0.05]   # Position
hp = yaw / 2.0
data.qpos[q_addr+3 : q_addr+7] = [math.cos(hp), 0.0, 0.0, math.sin(hp)]  # Quaternion
```

**`hp = yaw / 2.0`**: Quaternion for a pure yaw rotation around Z: `q = [cos(θ/2), 0, 0, sin(θ/2)]`. We set yaw by half-angle in the quaternion's W and Z components.

```python
model.geom_pos[model.geom("food").id] = [99.0, 99.0, 0.12]   # Park at 99m
```

**"Park" distant objects**: Geoms not being sampled are moved to (99, 99) — far outside the 10m arena. They won't appear in the camera frame. This prevents "accidentally visible" objects from creating ambiguous training samples.

```python
dist = np.random.uniform(0.5, 2.2)
rel_angle = np.random.uniform(-0.4, 0.4)   # Within ±23° (camera FOV = ±32.5°)
t_x = x_off + dist * math.cos(yaw + rel_angle)
t_y = y_off + dist * math.sin(yaw + rel_angle)
```

**Guaranteed visibility**: Place the target object at `dist` meters in front of the camera, within `±0.4 rad = ±23°` of center. The camera's half-FOV is `32.5°` — so the target is always in frame, preventing wasted samples where the object is off-screen.

```python
lf.write(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}\n")
```

**YOLO format output**: Standard label file. 6 decimal places = sub-pixel precision — more than needed for 160×120 resolution but follows best practice.

---

# PART C — `brain/verify_multi_object_predictions.py` (96 lines)

```python
pred_boxes = pred["boxes"].numpy()    # Shape: (N, 4) in pixel coords [xmin, ymin, xmax, ymax]
pred_labels = pred["labels"].numpy()  # Shape: (N,) class indices
pred_scores = pred["scores"].numpy()  # Shape: (N,) confidence [0, 1]
```

**SSD output format** (different from single-object model!): Instead of one bbox per image, SSD produces **N boxes** with scores. `N` can be 0 to hundreds depending on the image. The model internally runs NMS (Non-Maximum Suppression) to remove overlapping detections.

```python
for i in range(len(pred_boxes)):
    score = pred_scores[i]
    if score >= 0.50:    # Only show predictions with ≥50% confidence
```

**Threshold 0.5**: Predictions below 50% confidence are too uncertain to display. SSD produces many low-confidence proposals — filtering at 0.5 shows only meaningful detections.

**Why 0.5 and not 0.9?** For verification purposes, 0.5 shows more detections (including marginal ones), helping debug the model. In production use (carl_simulation.py), the threshold might be higher to reduce false positives.

```python
xmin, ymin, xmax, ymax = [int(x) for x in pred_boxes[i]]
```

SSD outputs boxes in **pixel coordinates** (absolute, not normalized). This is different from the single-object model which outputs normalized [0,1] YOLO coordinates. SSD's output already accounts for image size.

---

# PART D — `brain/show_carl.py` (44 lines)

```python
q_addr = int(model.joint("spatial_identity").qposadr[0])
data.qpos[q_addr : q_addr+3] = [0.0, 0.0, 0.05]
```

**`joint("spatial_identity").qposadr`**: Looks up the array index in `qpos` where this joint's degrees of freedom start. `spatial_identity` is likely a freejoint (7 DOF: x, y, z, qw, qx, qy, qz). Index `[0]` = first DOF = x position.

**Why not hardcode index 0?** The joint's index in `qpos` depends on the order joints appear in the XML. If someone adds a new joint before `spatial_identity`, the index shifts. Name-based lookup always finds the right index regardless of ordering.

```python
model.geom_pos[model.geom("food").id] = [0.5, 0.5, 0.12]
```

**Direct model modification**: `model.geom_pos` is a writable numpy array. Setting it directly moves the geometry in the model definition (not the simulation state). This is a "model-level" edit — persists for the entire simulation session.

**Why `geom_pos` instead of `data.geom_xpos`?** `data.geom_xpos` is READ-ONLY (computed by MuJoCo physics). `model.geom_pos` is the DEFINITION that MuJoCo uses to compute `data.geom_xpos`.

```python
mujoco.mj_forward(model, data)
```

**`mj_forward`**: Runs MuJoCo's forward kinematics — computes all derived quantities (positions, velocities, contact forces) from `qpos` and `qvel`. Required after manually setting `qpos` to make everything consistent before the viewer opens.

**Without `mj_forward`**: The model loads with objects at their XML default positions, not at the positions we just set. The viewer would show food in the wrong location.

```python
mujoco.viewer.launch(model, data)
```

**`viewer.launch` vs `viewer.launch_passive`**: `launch` is BLOCKING — the script pauses here until the viewer window is closed. `launch_passive` (used in the physics loop) is non-blocking — returns immediately and you control sync timing manually.

---

# PART E — `brain/plot_telemetry.py` (147 lines)

```python
box = np.ones(window_size) / window_size   # box = [1/150, 1/150, ..., 1/150]
cog_smoothed = np.convolve(cog_total, box, mode='same')
```

**Box filter (moving average) via convolution:**

`np.convolve(signal, kernel, mode)`: Slides the kernel over the signal, multiplying and summing at each position.

For a box kernel of size 150: at each point `i`, the output = `mean(signal[i-75 : i+75])` — a 150-sample moving average.

**Why convolution instead of a loop?** `np.convolve` is implemented in C/FORTRAN. For a 10000-sample signal with a 150-sample window, convolution is ~100× faster than a Python `for` loop.

**`mode='same'`**: Output has the same length as `cog_total`. Without `mode='same'`, convolution would output `len(signal) + len(kernel) - 1` samples — longer than the input, misaligned with the time axis.

**Why 150 samples?** At 30Hz telemetry logging, 150 samples = 5 seconds. Smoothing over 5 seconds removes high-frequency noise while preserving the slow trend of brain vs. reflex dominance.

```python
plt.savefig(output_path, dpi=150, bbox_inches='tight')
```

**`dpi=150`**: 150 dots-per-inch resolution. At 16 inches wide × 10 inches tall: `16×150 × 10×150 = 2400×1500 pixels`. High enough for presentation-quality charts.

**`bbox_inches='tight'`**: Crops the saved figure to the minimum bounding box — removes excess white margins. Without this, matplotlib adds ~0.5 inch margins on all sides.

---

# PART F — `.github/workflows/ci.yml` (53 lines)
> *The automatic guardian — runs every time code is pushed.*

---

## Lines 1–7: Trigger Conditions

```yaml
name: CARL-Ω CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

**`on: push: branches: [main]`**: Run this workflow whenever anyone pushes code to the `main` branch.

**`on: pull_request:`**: Also run when someone opens a Pull Request targeting `main`. This means PRs must PASS CI before merging — broken code can't enter the main branch.

**Why only `main`?** Experimental branches can have broken code. The guard only protects the stable production branch.

---

## Lines 11–14: Matrix Strategy

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11"]
```

**Matrix builds**: GitHub Actions runs the ENTIRE workflow TWICE — once with Python 3.10 and once with Python 3.11. If a bug only appears on Python 3.11 (e.g., a deprecated API), it's caught here.

**Why 3.10 and 3.11?** The project targets modern Python (≥3.10). 3.12+ not included because MuJoCo wheel support may lag. 3.9 and below excluded because f-strings with `=` (debugging syntax) require 3.8+ and `match` statements require 3.10+.

---

## Lines 26–31: Dependency Installation

```yaml
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install numpy scipy websockets opencv-python-headless pytest pandas matplotlib
```

**`--index-url .../cpu`**: Installs the CPU-only version of PyTorch. The GPU version (CUDA) is 3GB. CI servers have no GPU, so CUDA is useless and slow to install. CPU version = 200MB.

**`opencv-python-headless`** instead of `opencv-python`: The regular OpenCV opens display windows. CI servers have no display (no monitor, no X11 server). The headless version removes all GUI functionality — no `cv2.imshow()`, but `cv2.imread()` and `cv2.imwrite()` still work.

**Note: `mujoco` is NOT installed**: MuJoCo requires a real display and GPU context for rendering. CI runs headless → MuJoCo would fail during import. The tests are designed to work WITHOUT MuJoCo by only importing the brain modules.

---

## Lines 33–35: Syntax Check

```yaml
python -m compileall -q carl_simulation.py phase18_alife_pretrained.py live_plotter.py brain/ world/
```

**`python -m compileall`**: Compiles all listed Python files to bytecode (`.pyc`). If any file has a SYNTAX ERROR (missing colon, mismatched brackets), `compileall` reports it immediately — before running a single line.

**`-q`**: Quiet mode. Only print errors, not progress. Keeps CI logs clean.

**Why this before unit tests?** Compileall is instant (< 1 second). Unit tests take 5-30 seconds. Catching syntax errors first saves time.

---

## Lines 37–48: Import Smoke Test

```yaml
python -c "
import sys; sys.path.insert(0, 'brain')
from carl_endocrine import EndocrineSystem
from carl_reservoir import LiquidStateReservoir
from carl_grid_cells import GridCellModule, PlaceCellLayer, HippocampalNavigator
from carl_reflex import SpikingReflexLayer
from carl_stdp import STDPActionEvaluator
print('All brain module imports: OK')
"
```

**"Smoke test"**: Minimal test to verify there's no FIRE (critical failure). Just importing each class exercises:
- All top-level module imports succeed
- Class definitions are valid
- No `__init__` crashes on module load

**Why separate from unit tests?** If an import fails, ALL unit tests fail with `ImportError` — which is confusing. A dedicated import test pinpoints WHICH module is broken.

---

## Line 51–52: Unit Tests

```yaml
python -m pytest tests/ -v --tb=short
```

**`-v`**: Verbose mode. Shows each test name and PASSED/FAILED status.

**`--tb=short`**: "Short" traceback on failures. Shows the failing assertion and 3 lines of context. Full tracebacks (`--tb=long`) can be hundreds of lines for complex errors.

---

# PART G — `.gitignore` (68 lines)
> *What Git deliberately ignores.*

---

## Key Patterns

```gitignore
*.npy
*.npz
*.pt
*.pth
```

**Why exclude all model weights?** Binary files (numpy arrays, PyTorch weights) don't diff well — Git can't show what changed between two `.npy` files meaningfully. They're also large (MB-GB). Instead, the code re-learns them from scratch (or downloads pre-trained checkpoints separately).

```gitignore
memory/vision_dataset/
memory/multi_object_dataset/
```

**Why exclude datasets?** Generated datasets are 300+ MB and reproducible — `collect_vision_dataset.py` can regenerate them. Storing them in Git would make `git clone` take minutes instead of seconds.

```gitignore
*.png
*.jpg
```

**Why exclude images?** Telemetry plots and verification images are OUTPUTS (generated by running the code). They change every run. Tracking them in Git creates noise — every simulation run would show "modified files."

```gitignore
GENESIS/
final_build_checkpoint/
```

**Why exclude `GENESIS/`?** The GENESIS folder contains experimental multi-body work still in development. It's not part of the stable codebase yet. Keeping it out of Git prevents unstable experimental code from appearing in the main repository.

```gitignore
textbook/*.pdf
```

**Why exclude PDFs?** PDF walkthroughs are generated from the markdown files (the `.md` files ARE tracked). The PDFs are derivative outputs — large binary files that don't benefit from version control.

```gitignore
ebca_project_gantt.csv
```

**Project management file**: The Gantt chart is a planning tool, not code. It changes frequently during development but is not relevant to code review or deployment.

---

# PART H — `requirements.txt` (11 lines)
> *Every dependency and why it exists.*

```
numpy       # Array math — used in EVERY module. Foundation of all numerical computation.
torch       # PyTorch — neural networks (CarlVisionNet, SSD, STDP synapse).
mujoco      # Physics engine — simulates robot body, contacts, dynamics.
scipy       # Scientific computing — used for sparse matrix ops, signal processing.
matplotlib  # Plotting — live_plotter.py, plot_telemetry.py, training curves.
torchvision # Pre-trained SSD backbone, image transforms for multi-object detection.
websockets  # WebSocket server in phase18 — streams brain state to live dashboard.
opencv-python  # Image loading/saving, camera geometry, bbox drawing.
pandas      # CSV loading in some analysis scripts (alternative to csv module).
pytest      # Test framework — runs test_endocrine.py and test_grid_cells.py.
```

**No version pinning** (e.g., `numpy==1.24.0`): This is a known trade-off. Pinning gives reproducibility but requires manual updates. Not pinning gives flexibility (install what's available) but risks breaking if a dependency changes its API. For a research/development codebase, not pinning is common.

---

# PART I — `tests/__init__.py` (2 lines)

```python
# tests/__init__.py
```

**Empty init file**: Makes `tests/` a Python package (importable). Without this file, `pytest tests/` would work on newer pytest versions (which auto-discover tests) but `python -m pytest tests/` would fail to find the package. The comment is the entire content — this file exists purely to mark the directory as a package.

**Why needed?** When test files use `from carl_endocrine import EndocrineSystem` with `sys.path.insert(0, '../brain')`, Python needs to know `tests/` is a package to resolve relative imports correctly.
