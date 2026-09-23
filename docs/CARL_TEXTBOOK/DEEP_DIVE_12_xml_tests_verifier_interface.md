# 🔬 DEEP DIVE #12 — XML Files, Test Files, Vision Verifier, Genesis Body Interface
> *Every tag, every attribute, every test assertion — explained line by line.*

---

# PART A — `world/carl_mujoco.xml` (188 lines)
> *The physical body specification. Everything CARL IS, in XML.*

---

## Line 1: Root Element

```xml
<mujoco model="carl_elite">
```

**`model="carl_elite"`**: A human-readable name for this model. No functional impact — purely for identification in logs and the viewer title bar.

**MuJoCo XML**: Describes a complete physics simulation in declarative XML. MuJoCo compiles this into an internal binary model at runtime. Think of XML as the "blueprint" and MuJoCo as the "factory."

---

## Line 2: Compiler Options

```xml
<compiler angle="radian" autolimits="true"/>
```

**`angle="radian"`**: All angles in this file are in radians (not degrees). `1.5708 rad = 90°`, `3.1416 rad = 180°`.

**`autolimits="true"`**: Automatically enforce joint limits defined in `range=` attributes. Without this, you'd need to explicitly add `limited="true"` to each joint.

---

## Line 3: Simulation Options

```xml
<option gravity="0 0 -9.81" timestep="0.004166667" iterations="50" solver="Newton" tolerance="1e-10"/>
```

**`gravity="0 0 -9.81"`**: Gravity vector [Gx, Gy, Gz]. Z is up in MuJoCo, so gravity = -9.81 m/s² downward. Standard Earth gravity.

**`timestep="0.004166667"`**: 4.17ms per physics step = `1/240 Hz`. The simulation runs at 240Hz internally. Why 240? Control loop runs at 30Hz. `240/30 = 8` physics steps per control step — gives 8× better contact resolution.

**Why not 1000Hz (1ms)?** Diminishing returns. At 240Hz, contact forces are already stable. 1000Hz would be 4× slower for minimal accuracy gain.

**`iterations="50"`**: The Newton solver runs at most 50 iterations to converge contact forces. For CARL's simple wheel-floor contacts, typically converges in 3-5 iterations. 50 is a generous safety limit.

**`solver="Newton"`**: MuJoCo's most accurate contact solver. Slower than PGS (Projected Gauss-Seidel) but handles the wheel-floor rolling contact more accurately.

**`tolerance="1e-10"`**: Convergence tolerance. Solver stops when contact force residuals are below `10^(-10) N`. Extremely tight — ensures physically accurate forces.

---

## Lines 5–10: Visual Settings

```xml
<visual>
  <headlight ambient="0.28 0.28 0.33" diffuse="0.55 0.55 0.65" specular="0 0 0"/>
  <rgba haze="0.04 0.04 0.07 1"/>
  <map fogstart="7" fogend="18" znear="0.01"/>
  <quality shadowsize="4096"/>
</visual>
```

**`headlight`**: The light that follows the viewer camera. Ambient [R,G,B] = baseline light level everywhere. Diffuse = directional light from the camera direction. Specular=0 = no camera-direction highlights.

**`rgba haze`**: Atmospheric haze color [R,G,B,A] = near-black navy. Creates a slight atmospheric depth effect at distance.

**`fogstart=7 fogend=18`**: Objects start fading at 7m distance, fully invisible at 18m. The arena is ~8m wide — walls at 8m are slightly hazed.

**`znear="0.01"`**: Near clipping plane at 1cm. Objects closer than 1cm to the camera disappear. This prevents "Z-fighting" artifacts (flickering) from overlapping surfaces very close to the camera.

**`shadowsize="4096"`**: Shadow map texture size = 4096×4096 pixels. Higher = sharper shadows. 4K shadows require ~64MB of GPU VRAM. Only use in high-end training visualization.

---

## Lines 12–26: Asset Definitions

```xml
<asset>
  <texture name="grid" type="2d" builtin="checker" width="512" height="512"
           rgb1="0.035 0.042 0.090" rgb2="0.055 0.068 0.145"/>
  <material name="floor_mat" texture="grid" texrepeat="10 10"
            reflectance="0.08" shininess="0.15" rgba="0.05 0.06 0.12 1"/>
  <material name="wall_glow"  rgba="0.15 0.45 1.0 1"  emission="0.6" .../>
```

**`builtin="checker"`**: MuJoCo procedurally generates a checkerboard texture. No image file needed.

**`rgb1/rgb2`**: The two colors of the checkerboard. `0.035 0.042 0.090` = very dark navy (nearly black). `0.055 0.068 0.145` = slightly lighter navy. Creates a subtle dark grid on the floor.

**`texrepeat="10 10"`**: The texture tiles 10 times along X and 10 along Y across the floor plane. With 12m floor and 10 tiles = 1.2m per tile.

**`emission="0.6"`**: A material that EMITS light (not just reflects). The wall_glow material has 60% self-emission — makes wall caps glow blue even in shadows. This creates the sci-fi aesthetic (glowing neon wall tops).

**`contype="0" conaffinity="0"`** (on glow caps): Zero collision type AND affinity → glow cap geoms NEVER participate in any collision. They're purely visual decorations. Without this, the glow caps would physically block the robot.

---

## Lines 29–32: Default Geometry Properties

```xml
<default>
  <geom contype="1" conaffinity="1" condim="3"
        friction="0.85 0.005 0.0001"
        solimp="0.99 0.999 0.001" solref="0.004 1"/>
</default>
```

**`contype="1" conaffinity="1"`**: Standard collision group. Two geoms collide if `(contype1 & conaffinity2) || (contype2 & conaffinity1)` is non-zero. Both 1 → always collide.

**`condim="3"`**: 3D contact (sliding friction in 2D + normal force). `condim=1` = normal force only, `condim=6` = full friction + torsion.

**`friction="0.85 0.005 0.0001"`**: Three friction coefficients:
1. `0.85`: Sliding friction μ — normal direction. Rubber-ish. Allows wheels to grip well.
2. `0.005`: Torsional friction — resistance to spinning in place.
3. `0.0001`: Rolling friction — extremely low (realistic for smooth floor).

**`solimp="0.99 0.999 0.001"`**: Contact softness parameters [dmin, dmax, width]:
- Hard contacts (rigid walls): dmin and dmax near 1 = nearly rigid
- `0.001` width = tiny allowed penetration (1mm) before full force

**`solref="0.004 1"`**: Reference [timeconst, damping]: contact spring time constant = 0.004s (matches timestep). Damping = 1 = critically damped (no oscillation).

---

## Lines 48–82: Maze Geometry

```xml
<geom name="w_s"  type="box" size="3.64 0.04 0.175" pos="3.6  0.0  0.175" material="wall_mat"/>
```

**`type="box"`**: Rectangular prism. MuJoCo box size = HALF-extents in each dimension.

**`size="3.64 0.04 0.175"`**:
- Half-length: 3.64m → full wall length = 7.28m (≈7.2m arena width)
- Half-thickness: 0.04m → 8cm wall thickness (realistic)
- Half-height: 0.175m → wall height = 35cm = 0.35m (tall enough to block the 25cm high robot)

**`pos="3.6 0.0 0.175"`**:
- Center at x=3.6m (middle of arena width)
- y=0 (south edge)
- z=0.175m (center of wall = half its height off the floor)

**Why z at half-height?** MuJoCo geom position = CENTER of the geom. A 35cm tall wall sitting on the floor has its center at 17.5cm = 0.175m.

**Internal wall positions (wi0–wi8)**: Form an L-shaped maze pattern. Grid spacing = 1.2m (explained by `<!-- MAZE WALLS (grid cell=1.2m) -->`). Each wall is placed at multiples of 1.2m from the arena boundary.

---

## Lines 83–118: Robot A Body Hierarchy

```xml
<body name="base_A" pos="0.40 0.40 0.10">
  <freejoint name="fj_A"/>
  <geom name="chassis_A" type="box" size="0.06 0.08 0.02" material="chassis" mass="0.5"/>
```

**Body hierarchy (kinematic tree):**
```
worldbody
└── base_A (pos=[0.4, 0.4, 0.1])   ← Robot origin
    ├── chassis_A (geom)             ← Body box
    ├── lwheel_A (body)
    │   ├── lw_A (hinge joint)
    │   └── lw_A_tire (geom)
    ├── rwheel_A (body)
    │   └── rw_A_tire (geom)
    └── neck_A (body)
        ├── neck_A (hinge joint)
        ├── neck_A_g (geom)
        └── head_A (body)
            ├── head_A_g (geom)
            ├── eye_A (geom)
            └── eye_cam_A (camera)
```

**`<freejoint>`**: Gives the body 6 degrees of freedom (3 translation + 3 rotation). Without this, the body would be fixed to its parent. A freejoint makes the robot able to move freely in the world.

**`chassis_A size="0.06 0.08 0.02"`**: Half-extents: 6cm long, 8cm wide, 2cm tall → 12cm × 16cm × 4cm box chassis.

**`mass="0.5"`**: 500g chassis. Total robot mass = chassis(500g) + 2 wheels(2×200g) + neck(100g) + head(1500g) = **2.5kg**. Heavier head (neck camera) creates a more realistic inertia distribution.

---

## Wheel Joints

```xml
<joint name="lw_A" type="hinge" axis="0 1 0" damping="0.02" frictionloss="0.005"/>
<geom name="lw_A_tire" type="cylinder" size="0.07 0.0125" euler="1.5708 0 0"
      material="tire" mass="0.2" friction="1.2 0.005 0.0001"/>
```

**`type="hinge" axis="0 1 0"`**: Wheel rotates around the Y-axis (lateral axis). Positive rotation = forward motion (right-hand rule: when looking in +Y direction, positive rotation is from Z toward X = forward).

**`damping="0.02"`**: Joint damping — resistance proportional to angular velocity. 0.02 N·m·s/rad is low — wheel spins easily but not completely frictionlessly.

**`frictionloss="0.005"`**: Constant friction — like a bearing with some stiffness. Prevents the wheel from spinning forever once control is removed.

**`size="0.07 0.0125"`**: For cylinders: `size[0]=radius, size[1]=half-height`.
- Radius = 7cm (14cm diameter wheel)
- Half-height = 1.25cm → wheel width = 2.5cm

**`euler="1.5708 0 0"`**: Rotate the cylinder 90° around X-axis. By default, cylinders in MuJoCo are oriented along the Z-axis (vertical). This rotation makes the wheel horizontal (axle along Y).

**`friction="1.2 0.005 0.0001"`**: Wheels have HIGHER friction (1.2 vs. 0.85 default). High sliding friction ensures the wheels grip the floor and actually drive the robot without slipping.

---

## Actuators (Lines 167–173)

```xml
<actuator>
  <motor    name="lw_A_m"  joint="lw_A"   ctrllimited="true" ctrlrange="-12 12"/>
  <position name="nk_A_p"  joint="neck_A" kp="12" ctrllimited="true" ctrlrange="-0.3 0.3"/>
</actuator>
```

**`<motor>`**: Torque actuator. `ctrl[i]` sets torque in N·m. `ctrlrange="-12 12"` → max ±12 N·m.

**Why ±12?** The robot weighs ~2.5kg. To accelerate at 2g (aggressive): `F = ma = 2.5 × 2 × 9.81 = 49N`. With 7cm radius wheel: `τ = F × r = 49 × 0.07 = 3.4 N·m`. So ±12 is 3.5× the needed torque — provides ample margin for hills and obstacles. Not so large it causes simulation instability.

**`<position>`**: Position-controlled actuator with PD gain. `ctrl[i]` sets TARGET ANGLE (rad). `kp="12"` is the proportional gain — spring stiffness. Neck servo tries to reach the target angle with force proportional to error.

**Why position control for neck but torque for wheels?** Wheels need raw torque for speed control. Neck needs to hold a specific angle (camera direction) regardless of disturbances — position control achieves this automatically.

---

# PART B — `tests/test_endocrine.py` (211 lines)
> *How to verify the endocrine system is correctly implemented.*

---

## Lines 1–13: What is a Test File?

A test file defines **automated checks** that run to verify code works correctly. We run these with `pytest` (Python testing framework). If any check fails, pytest prints the failure with details.

**Why write tests?** The endocrine system has subtle math (ODEs, precision formulas). It's easy to introduce a bug that changes DA decay slightly — and not notice because the simulation "still runs." Tests catch these bugs automatically.

---

## Lines 14–15: Path Setup

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain'))
```

**`os.path.dirname(__file__)`**: Directory of this test file = `d:\ebca\tests`

**`'..', 'brain'`**: Navigate up one level to `d:\ebca`, then into `brain/`. Result: `d:\ebca\brain`.

**`sys.path.insert(0, ...)`**: Add to the FRONT of Python's module search path (index 0). `insert(0, ...)` vs. `append(...)` ensures the local brain/ folder is checked FIRST, before any installed packages. This prevents name collisions with a hypothetical installed package named `carl_endocrine`.

---

## Lines 22–25: `@pytest.fixture`

```python
@pytest.fixture
def endo():
    """Fresh EndocrineSystem at baseline."""
    return EndocrineSystem()
```

**`@pytest.fixture`**: A decorator that marks this function as a "fixture" — shared setup code. Any test function that includes `endo` as a parameter automatically receives a fresh `EndocrineSystem()`.

**Why fixtures instead of creating in each test?** DRY principle (Don't Repeat Yourself). Without fixtures:
```python
def test_da_clamp():
    endo = EndocrineSystem()  # repeated 20 times
    endo.surge_da(100.0)
```

With fixtures, each test function gets a NEW, FRESH object — no state leaks between tests.

---

## Lines 31–41: `TestClamping` Class

```python
class TestClamping:
    def test_no_modulator_exceeds_max_after_large_surge(self, endo):
        """Surging way past MAX_NM and stepping should still clamp to MAX_NM."""
        endo.surge_da(100.0)    # Surge DA by 100 (massively over the 3.0 max)
        endo.step(dt=0.033)     # One physics step
        assert endo.DA <= EndocrineSystem.MAX_NM
```

**What this tests:** The `np.clip()` call in `step()` must keep DA ≤ 3.0 even after a massive 100-unit surge.

**Why test this specifically?** The clip is critical for safety. Without it, a bug that accidentally removes the clip call would cause DA = 101.0 → satiation = 1/101 ≈ 0 → motivation = hunger/0 = infinity → catastrophic behavior.

**`assert endo.DA <= EndocrineSystem.MAX_NM`**: If this assertion is False, pytest raises `AssertionError` with the actual value of `endo.DA`, helping diagnose the bug.

**Using `EndocrineSystem.MAX_NM` (class constant) not `3.0` (literal)**: If someone changes `MAX_NM` to 4.0, the test automatically adapts. Hardcoding `3.0` would mean the test passes even if the implementation uses 4.0 — a subtle bug.

---

## Lines 59–85: `TestDecay`

```python
def test_ne_decays_faster_than_da(self, endo):
    endo2 = EndocrineSystem()
    endo.surge_da(1.0)    # DA += 1.0
    endo2.surge_ne(1.0)   # NE += 1.0 (same surge magnitude)
    da_start, ne_start = endo.DA, endo2.NE
    for _ in range(10):
        endo.step(dt=0.033)
        endo2.step(dt=0.033)
    da_drop = da_start - endo.DA
    ne_drop = ne_start - endo2.NE
    assert ne_drop > da_drop, "NE (DECAY=3.0) should decay faster than DA (DECAY=2.0)"
```

**Why two separate objects (`endo` and `endo2`)?** Both are tested in parallel. `endo2 = EndocrineSystem()` creates a SEPARATE instance with its own state. Without this, surging DA and NE in the SAME object would make their interactions confound the test.

**What this verifies:** The mathematical relationship `DECAY_NE = 3.0 > DECAY_DA = 2.0` results in OBSERVABLE faster NE decay. This is an integration test — checks that the constants correctly propagate into the actual numerical behavior.

**`da_drop` and `ne_drop`**: How much each modulator dropped from its post-surge level after 10 steps (~330ms). The assertion confirms the biological property: "NE (adrenaline) decays faster than dopamine."

---

```python
def test_baseline_is_stable_equilibrium(self, endo):
    da_before = endo.DA   # = BASELINE_DA = 1.0 (fresh object)
    endo.step(dt=0.033)
    assert abs(endo.DA - da_before) < 0.001
```

**Fixed-point stability test:** At baseline, `dX/dt = -k × (X - X) = 0`. So stepping should produce zero change. The `< 0.001` tolerance allows for floating-point rounding (not exactly zero due to IEEE 754 arithmetic).

**Why 0.001?** `DECAY_DA × BASELINE_DA × dt = 2.0 × 1.0 × 0.033 × (1.0 - 1.0) = 0`. Exactly zero, no error. Using `< 1e-10` would also pass. `0.001` is a generous tolerance showing we ONLY care that it doesn't drift, not about numerical precision.

---

## Lines 154–169: `TestBehavioralMode`

```python
def test_exploit_overrides_low_battery(self, endo):
    """Food visible should always return EXPLOIT, even at critical battery."""
    assert endo.get_behavioral_mode(battery_level=0.01, food_visible=True) == "EXPLOIT"
```

**Edge case test:** Tests the PRIORITY of the behavioral mode switch. At 1% battery, you'd expect "SURVIVE" — but food visible should OVERRIDE even critical battery.

This verifies the specific IF-ELIF order in `get_behavioral_mode()`:
```python
if food_visible:      # Checked FIRST
    return "EXPLOIT"
elif battery < 0.15:  # Only if food NOT visible
    return "SURVIVE"
```

**Why test edge cases?** Bugs often hide in priority logic. If someone accidentally changed to `elif food_visible:` (with elif instead of if), this test would catch it — because at battery=0.01, the battery check would trigger first.

---

## Lines 194–210: `TestReplayBlendWeight`

```python
def test_zero_nav_value_gives_zero_blend(self, endo):
    """No nav signal = no replay guidance, regardless of hunger."""
    assert endo.get_replay_blend_weight(battery_level=0.0, max_nav_value=0.0) == 0.0
```

**Boundary condition:** Even at maximum hunger (battery=0), if there's no nav signal (no food ever remembered), replay blend should be zero. The formula:
```
signal_strength = clip(0.0 / 2.0, 0, 1) = 0
blend = 0 × (0.3 + 0.7 × 1.0) = 0
```

Checking `== 0.0` (exact equality) because this involves only integer-safe operations (no floating-point rounding).

---

# PART C — `tests/test_grid_cells.py` (300 lines)
> *Every test assertion for the hippocampal GPS system.*

---

## Lines 85–95: `GridCellModuleNoiseZero` — Test Helper Class

```python
class GridCellModuleNoiseZero(GridCellModule):
    """Helper: zero-noise module for deterministic tests."""
    def fire(self, x=None, y=None, noise=None):
        pos = np.array([x, y], dtype=float) if x is not None else self.pi_phase
        proj = self.K @ pos
        act = np.zeros(self.n)
        for c in range(self.n):
            phi = proj + self.phases[c]
            rate = (math.cos(phi[0]) + math.cos(phi[1]) + math.cos(phi[2])) / 3.0
            act[c] = max(0.0, (rate + 1.0) / 2.0)
        return act
```

**Why define a subclass just for tests?** The real `fire()` method adds random noise. For deterministic tests (where we check exact values), noise would make the test flaky — sometimes pass, sometimes fail. This subclass overrides `fire()` to remove noise.

**`@pytest.fixture`** with `GridCellModule(noise=0.0)`: In the main tests, the fixture uses `noise=0.0` parameter if the class supports it. This helper class manually reimplements `fire()` without the noise step.

---

## Lines 52–57: Path Integration Test

```python
def test_path_integration_accumulates(self, gcm):
    gcm.reset(0.0, 0.0)
    gcm.integrate(vx=1.0, vy=0.5, dt=1.0)
    assert abs(gcm.pi_phase[0] - 1.0) < 1e-9
    assert abs(gcm.pi_phase[1] - 0.5) < 1e-9
```

**What it verifies:** After `integrate(vx=1.0, vy=0.5, dt=1.0)`:
```
dpos = [1.0, 0.5] × 1.0 = [1.0, 0.5]
dphase = K @ dpos
pi_phase += dphase
```

Wait — the test checks `pi_phase[0] == 1.0`, not `(K @ dpos)[0]`. This means this test checks the DIRECT path integration update `pi_phase += [vx, vy] × dt` — not the phase transformation. This tests whether the position estimate itself (in meters) updates correctly, not the wave phase.

**`< 1e-9`**: Tight tolerance (1 nanometer). Floating-point operations on small numbers should be VERY accurate. `1.0 + 0.5 × 1.0 = 1.0` is exact in IEEE 754.

---

## Lines 136–155: Graph Invariants

```python
def test_update_graph_creates_bidirectional_edge(self, pcl):
    pcl.update_graph(old_cell=0, new_cell=1, tick=10)
    assert 1 in pcl.adjacency[0]
    assert 0 in pcl.adjacency[1]
```

**Tests bidirectionality**: A single `update_graph()` call must create edges in BOTH directions. If someone accidentally removed the `adjacency[new].add(old)` line, this test catches it.

```python
def test_duplicate_edge_not_double_counted(self, pcl):
    pcl.update_graph(0, 1, 1)
    before = pcl.total_edges
    pcl.update_graph(0, 1, 2)  # same edge again
    assert pcl.total_edges == before
```

**Why test this?** `adjacency` uses Python `set` — adding the same element twice doesn't increase the set size. But `total_edges` is a separate integer counter. If it's incremented using `len(adjacency[0])` each time, it would double-count. This test verifies `total_edges` only increments when a TRULY NEW edge is formed.

---

## Lines 167–173: Persistent Beacon Test

```python
def test_persistent_beacon_survives_heavy_decay(self, pcl):
    pcl.stamp_reward(cell_idx=10, amount=5.0)
    for _ in range(500):
        pcl.diffuse_rewards(gamma=0.9, decay=0.99995, n_sweeps=1)
    assert pcl.reward_values[10] > 0.0
```

**Why 500 iterations?** `decay=0.99995` per step. After 500 steps: `0.99995^500 = 0.975`. The raw value decays to 97.5% — still positive. But the PERSISTENT beacon keeps getting re-stamped each step (to its original value), preventing full decay.

This is a stress test verifying the `persistent_rewards` floor mechanism works correctly over a long time horizon.

---

## Lines 288–299: Theta Learning Rate Test

```python
def test_theta_learning_rate_in_valid_range(self, nav):
    for _ in range(20):
        nav.step(0.5, 0.5, 0.0, 0.0, 0.033)
        lam = nav.theta_learning_rate()
        assert 0.970 <= lam <= 0.999
```

This verifies that the theta gate modulation stays within physically valid RLS lambda bounds. Lambda outside [0.970, 0.999] could cause RLS instability (< 0.970 = forgetting too fast; > 0.999 = effective memory over 1000 ticks).

The test runs for 20 steps covering almost 4 theta cycles (20 × 0.033s = 0.66s, theta period = 0.167s → 4 full oscillations). This ensures the boundary holds across ALL theta phases.

---

# PART D — `brain/verify_vision_predictions.py` (101 lines)
> *Visual sanity check for the old single-object vision model.*

---

## Lines 48–53: Inference

```python
cls_out, bbox_out = model(img_tensor.unsqueeze(0))
probs = torch.softmax(cls_out, dim=1).numpy()[0]
pred_class = np.argmax(probs)
pred_conf = probs[pred_class]
pred_bbox = bbox_out.squeeze(0).numpy()
```

**`img_tensor.unsqueeze(0)`**: Adds a batch dimension. `img_tensor` shape: (3, 120, 160). After `unsqueeze(0)`: (1, 3, 120, 160). Models expect batch input.

**`torch.softmax(cls_out, dim=1)`**: Converts raw logits to probabilities. `dim=1` = softmax over the class dimension (4 classes). Result: each batch item has 4 probabilities summing to 1.

**`.numpy()[0]`**: Convert to numpy array, take first (only) batch item. Result: shape (4,) = probabilities for [Food, Obstacle, Predator, Background].

**`np.argmax(probs)`**: Index of highest probability = predicted class.

**`bbox_out.squeeze(0).numpy()`**: Remove batch dimension, convert to numpy. Result: [xc, yc, w, h] in normalized [0,1] coordinates (YOLO format).

---

## Lines 63–72: Drawing Ground Truth Box

```python
if class_id != 3:                          # Skip if background
    gt_xc, gt_yc, gt_w, gt_h = bbox.numpy()
    gt_u1 = int((gt_xc - gt_w/2) * W)     # Left edge (pixels)
    gt_v1 = int((gt_yc - gt_h/2) * H)     # Top edge
    gt_u2 = int((gt_xc + gt_w/2) * W)     # Right edge
    gt_v2 = int((gt_yc + gt_h/2) * H)     # Bottom edge
    cv2.rectangle(img_bgr, (gt_u1, gt_v1), (gt_u2, gt_v2), (0, 255, 0), 1)
```

**YOLO → pixel coordinates:**
```
xmin_pixel = (xc - w/2) × image_width
ymin_pixel = (yc - h/2) × image_height
```

**`cv2.rectangle(img, pt1, pt2, color, thickness)`**:
- `(gt_u1, gt_v1)` = top-left corner
- `(gt_u2, gt_v2)` = bottom-right corner
- `(0, 255, 0)` = green (BGR format — note: NOT RGB! OpenCV uses BGR)
- `1` = 1-pixel thick border

**Why `(0, 255, 0)` = green in BGR?** OpenCV stores color as Blue-Green-Red (not Red-Green-Blue). So `(B=0, G=255, R=0)` = full green, no blue or red.

**`class_id != 3`**: Class 3 = Background → no bounding box to draw (background has no location).

---

## Lines 91–96: 2×2 Grid Layout

```python
top_row = np.hstack((grid_imgs[0], grid_imgs[1]))   # Horizontal stack
bot_row = np.hstack((grid_imgs[2], grid_imgs[3]))
grid_all = np.vstack((top_row, bot_row))             # Vertical stack
cv2.imwrite(output_path, grid_all)
```

**`np.hstack`**: Horizontal concatenation. `(120, 160, 3)` + `(120, 160, 3)` → `(120, 320, 3)`.

**`np.vstack`**: Vertical concatenation. `(120, 320, 3)` + `(120, 320, 3)` → `(240, 320, 3)`.

Result: 4 images arranged in a 2×2 grid = one PNG with all 4 side-by-side comparisons.

**Why save to PNG not show?** `cv2.imshow()` requires a GUI window — doesn't work on headless servers or over SSH. `cv2.imwrite()` saves the file, which can then be viewed in any image viewer or embedded in documentation.

---

# PART E — `genesis_body_interface.py` (211 lines)
> *The hardware abstraction layer for the primate-form Genesis CARL.*

---

## Lines 111–115: Actuator Name → Index Map

```python
self.act = {}
for i in range(model.nu):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
    if name:
        self.act[name] = i
```

**`model.nu`**: Number of actuators (Nu). For the full primate body, this is ~50 (wheels, spine, arms, hands, head, fingers).

**`mj_id2name()`**: Given an actuator index `i`, returns its name string (e.g., `"act_sp_L"`) or `None` if unnamed.

**`self.act[name] = i`**: Build a reverse map: name → index. Then `self.data.ctrl[self.act["act_sp_L"]] = 0.5` becomes readable and safe.

**Why build at init (not hardcode indices)?** If someone adds or rearranges actuators in the XML, hardcoded indices break. Name-based lookup auto-adapts to any XML change.

---

## Lines 117–124: Sensor Offset Map

```python
self.sens_idx = {}
idx = 0
for i in range(model.nsensor):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i)
    if name:
        self.sens_idx[name] = idx
    idx += model.sensor_dim[i]
```

**`model.sensor_dim[i]`**: Each sensor outputs a DIFFERENT number of values. An IMU gyro sensor outputs 3 values (ωx, ωy, ωz). A LiDAR rangefinder outputs 1 value. A touch sensor outputs 1 value.

**Running `idx` pointer**: The sensor data is packed into one flat `sensordata` array. To find where sensor i starts, you must sum up the dimensions of all sensors before it.

Example: If sensors = [LiDAR(1), IMU_accel(3), IMU_gyro(3), Touch(1)]:
- LiDAR starts at idx=0
- IMU_accel starts at idx=1
- IMU_gyro starts at idx=4
- Touch starts at idx=7

**Why not just use the sensor index `i`?** Because sensor i with 3 outputs occupies indices i, i+1, i+2 in sensordata — NOT just index i.

---

## Line 128: Lazy Renderer

```python
self._renderer = None  # lazy init to avoid OpenGL conflicts with viewer
```

**"Lazy initialization"**: Don't create the OpenGL renderer in `__init__` — only create it the FIRST TIME `get_camera_bgr()` is called.

**Why?** Creating a `mujoco.Renderer` initializes an OpenGL context. If a MuJoCo viewer window is already open, creating a second OpenGL context can cause `Segmentation fault` or `GLX errors` on some systems. Lazy init means the renderer is only created if the camera is actually used.

---

## Lines 149–155: `set_joint()` with Automatic Clamping

```python
def set_joint(self, name: str, value: float):
    if name in self.act:
        self.data.ctrl[self.act[name]] = np.clip(
            value,
            self.model.actuator_ctrlrange[self.act[name], 0],
            self.model.actuator_ctrlrange[self.act[name], 1],
        )
```

**`actuator_ctrlrange[idx, 0]`**: Minimum allowed control value for actuator `idx`.

**`actuator_ctrlrange[idx, 1]`**: Maximum allowed control value.

**Why clip here?** MuJoCo already clips control values internally — but it does so SILENTLY. This explicit clip:
1. Makes the code explicit about what's happening
2. Prevents the caller from thinking a value outside range was accepted
3. The clamp values come directly from the model — no hardcoding needed

**`if name in self.act:`**: Silently ignores unknown joint names. `genesis_run.py` calls `set_joint()` with names that might not exist in some model variants. Rather than crashing with `KeyError`, it's a no-op for unknown joints.

---

## Lines 187–200: LiDAR Sector Helpers

```python
def lidar_front(self) -> float:
    """Min range of the forward-facing rays (±37.5°, sensors 0-2 and 22-23)."""
    r = self.get_lidar()
    vals = [r[i] for i in [0, 1, 2, 22, 23] if r[i] > 0]
    return min(vals) if vals else 5.0
```

**Why rays [0, 1, 2, 22, 23]?** The 24 LiDAR rays are indexed 0-23, covering 360°. Each ray covers 360/24 = 15°. Forward (0°) = ray 0. The forward sector (±37.5° = ±2.5 rays) covers rays -2 to +2. Since indices wrap: ray -2 = ray 22, ray -1 = ray 23. So rays [0, 1, 2, 22, 23] cover ±37.5° forward.

**`if r[i] > 0`**: In the XML, LiDAR sensors return -1 when no hit within range. Filtering > 0 excludes "no-hit" readings.

**`min(vals) if vals else 5.0`**: If ALL forward rays show no hit (open space), return 5.0 (maximum range). Using 5.0 rather than -1 makes downstream code simpler — "anything > 4m is effectively open."
