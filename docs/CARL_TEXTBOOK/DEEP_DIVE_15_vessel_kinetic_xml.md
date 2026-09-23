# 🔬 DEEP DIVE #15 — `world/vessel_kinetic.xml` (Every Line, Every Why)
> *The hardware-faithful body. This is what `carl_simulation.py` runs on. 321 lines that define CARL's physical existence.*

---

## FILE PURPOSE

This XML file defines **CARL's physical body and world** inside MuJoCo. Think of it like architectural blueprints — it tells the physics engine exactly how every bone, joint, wheel, arm, sensor, and wall is shaped, how heavy it is, how slippery it is, and what forces it can exert. No code here — pure declarative specification.

**Relationship to `carl_mujoco.xml`:**
- `carl_mujoco.xml` = simple behavioral testbed (2 robots, no arms, used by `phase18_alife_pretrained.py`)
- `vessel_kinetic.xml` = hardware-faithful twin with full arms and sensors (used by `carl_simulation.py`)

---

## LINE 1–3: XML Header + Physics Solver

```xml
<?xml version='1.0' encoding='utf-8'?>
<mujoco model="CARL Kinetic">
  <option timestep="0.01" gravity="0 0 -9.81" solver="Newton" integrator="implicit" />
```

**`timestep="0.01"`**: Physics steps every 10ms = 100Hz. This is different from `carl_mujoco.xml` which uses `timestep="0.004166" = 240Hz`. This model runs slower — the vessel is more complex with more DOF, so it needs a larger timestep to remain computationally affordable.

**`gravity="0 0 -9.81"`**: Standard Earth gravity. `0 0` = no horizontal gravity. `-9.81 m/s²` downward (negative Z = down in MuJoCo's coordinate system).

**`solver="Newton"`**: Newton-Raphson iterative solver — the most accurate but most expensive MuJoCo solver. For a complex multi-body robot with arm contacts, you need Newton over the cheaper `PGS` (Projected Gauss-Seidel). Newton converges more reliably when contacts are stiff.

**`integrator="implicit"`**: Implicit Euler integration. Unlike explicit Euler (which can blow up with stiff systems), implicit Euler unconditionally stable — it cannot diverge even with large forces. Required for position-controlled arms (very high kp gains = stiff springs = explicit Euler would explode).

---

## LINE 4: Compiler Settings

```xml
<compiler angle="radian" coordinate="local" inertiafromgeom="true" />
```

**`angle="radian"`**: All joint angles, ranges, and euler values in the file are in radians (not degrees). `range="-2.44 0"` means `-2.44 rad = -140°` to `0 rad`.

**`coordinate="local"`**: All `pos` values inside a `<body>` are relative to the parent body's frame, not the world origin. So `<body pos="0.12 0 0">` means "12cm along the parent's X-axis" — not 12cm from the world center.

**`inertiafromgeom="true"`**: MuJoCo automatically computes inertia tensors from geometry shapes and mass. You don't need to manually provide `<inertial>` blocks — the simulator infers how the mass is distributed from the shape.

---

## LINES 6–11: Default Block — Global Physics Defaults

```xml
<default>
  <geom contype="1" conaffinity="1" condim="3" friction="1.2 0.005 0.0001" />
  <joint damping="0.15" frictionloss="0.003" />
  <position ctrllimited="true" forcelimited="true" forcerange="-5.0 5.0" />
  <velocity forcelimited="true" forcerange="-2.5 2.5" />
</default>
```

**`<geom>` defaults:**
- `contype="1" conaffinity="1"`: Collision group bits. Both 1 = can collide with anything that has matching bits. Individual geoms override this (wheels use `contype="2"`, fingers use `contype="8"` — see later).
- `condim="3"`: Contact dimensionality. 3D = normal force + 2 friction directions. This is standard for rigid body contacts with friction.
- `friction="1.2 0.005 0.0001"`: Three friction coefficients:
  - `1.2` = sliding friction (μ). High — grippy surfaces. (Steel on steel ≈ 0.6, rubber on road ≈ 0.8, this is extra-grippy at 1.2)
  - `0.005` = torsional friction (spinning resistance)
  - `0.0001` = rolling friction (near-zero — wheels roll freely)

**`<joint>` defaults:**
- `damping="0.15"`: Velocity-proportional resistance. Every joint loses 0.15 N·m·s of torque per rad/s of angular velocity. Prevents oscillation.
- `frictionloss="0.003"`: Coulomb (dry) friction. A constant 0.003 N·m opposing all joint motion. Mimics real joint stiction.

**`<position>` defaults (position-controlled actuators):**
- `forcerange="-5.0 5.0"`: Maximum ±5 N·m output torque. Safe default for small joints.

**`<velocity>` defaults (velocity-controlled actuators):**
- `forcerange="-2.5 2.5"`: Wheel motors limited to ±2.5 N·m.

---

## LINES 13–32: Materials (Visual Only)

```xml
<material name="matte_shell"    rgba="0.90 0.92 0.94 1.0" roughness="0.4" />
<material name="inner_frame"    rgba="0.22 0.24 0.28 1.0" roughness="0.5" />
<material name="laser_ring"     rgba="0.00 0.80 1.00 1.0" emission="1.2" />
<material name="wall_mat"       rgba="0.12 0.15 0.18 1.0" roughness="0.9" />
<material name="wall_glow"      rgba="0.05 0.70 0.90 1.0" emission="0.8" />
<material name="food_mat"       rgba="0.20 0.90 0.30 1.0" emission="0.5" />
<material name="danger_mat"     rgba="0.90 0.15 0.15 1.0" emission="0.8" />
<material name="predator_mat"   rgba="0.80 0.05 0.05 1.0" emission="1.0" />
<material name="predator_glow_mat" rgba="1.00 0.20 0.10 1.0" emission="1.5" />
<material name="finger_mat"     rgba="0.95 0.75 0.15 1.0" roughness="0.6" />
```

**`rgba`**: Red, Green, Blue, Alpha — all [0, 1]. Examples:
- `matte_shell (0.90, 0.92, 0.94)` = light grey-white (CARL's outer body)
- `inner_frame (0.22, 0.24, 0.28)` = dark grey (metal chassis, joints)
- `laser_ring (0.00, 0.80, 1.00)` = cyan/teal (the LiDAR scanner ring — bright and visible)
- `food_mat (0.20, 0.90, 0.30)` = bright green (food items)
- `danger_mat (0.90, 0.15, 0.15)` = red (dynamic hazard cube)

**`emission`**: How much the material glows on its own (not dependent on scene lighting). `emission=1.2` = laser ring blazes with 120% intensity regardless of shadow. Used for visual markers that must always be visible. Pure physics — no effect on contacts.

**`roughness`**: Physically-based rendering roughness. `0.0` = mirror-like. `1.0` = completely matte. Does NOT affect friction (that's in `<geom friction="...">`). Pure visual.

---

## LINES 35–48: World Lighting and Floor

```xml
<light name="studio_sun" pos="2 1 5" dir="-0.3 -0.2 -1" diffuse="0.85 0.85 0.85" castshadow="true" />
<geom name="floor" type="plane" size="12 12 0.1" rgba="0.93 0.94 0.96 1" friction="0.001 0.001 0.0001" />
```

**`<light>`**: Single directional "sun" light at `(2, 1, 5)` meters, pointing `(-0.3, -0.2, -1)` (mostly downward, slightly angled). `castshadow="true"` = objects cast realistic shadows. Visual only.

**`floor friction="0.001 0.001 0.0001"`**: The floor is nearly frictionless (0.001 sliding). This is intentional — the WHEELS provide traction (they have `friction="1.4"`), but the floor itself being slippery prevents non-wheel contact points from creating drag. The caster balls at the back/front slide freely.

**`size="12 12 0.1"`**: The floor plane extends 12m in each direction = 24m × 24m total. The arena walls are at ±5m, so the floor extends well beyond the visible arena.

---

## LINES 39–48: Arena Boundary Walls + Glow Strips

```xml
<geom name="wall_s" type="box" size="5.0 0.05 0.50" pos="0  -5.0  0.50" material="wall_mat" />
<geom name="wall_n" type="box" size="5.0 0.05 0.50" pos="0   5.0  0.50" material="wall_mat" />
<geom name="wall_w" type="box" size="0.05 5.0 0.50" pos="-5.0  0  0.50" material="wall_mat" />
<geom name="wall_e" type="box" size="0.05 5.0 0.50" pos=" 5.0  0  0.50" material="wall_mat" />
```

**4 boundary walls — a 10m × 10m arena:**
- South wall: 10m wide (`size="5.0"` = half-width) × 10cm thick × 1m tall, centered at `y=-5m, z=0.5m` (bottom at z=0, top at z=1.0)
- North, West, East: symmetric

**Why `pos="0 -5.0 0.50"`?** MuJoCo boxes use half-extents. `size="5.0 0.05 0.50"` = 10m × 10cm × 1m total. `pos z=0.50` places the box center at 0.5m — so its bottom face sits exactly on the floor (z=0).

```xml
<geom name="wg_s" type="box" size="5.0 0.01 0.004" pos="0 -5.0 1.004" material="wall_glow" contype="0" conaffinity="0" />
```

**Glow strips**: Thin boxes (`size 0.004` = 8mm thick) mounted on top of each wall at `z=1.004m`. `contype="0" conaffinity="0"` = **zero collision** — they're purely visual (no physical interaction). They create a sci-fi blue glow strip at the top of every wall — purely aesthetic. Emission=0.8 makes them glow without needing external light.

---

## LINES 51–55: Obstacle + Food (Parked at 99m)

```xml
<geom name="obstacle" type="cylinder" size="0.5 0.45" pos="99 99 0.45" material="wall_mat" />
<geom name="food"     type="sphere"   size="0.12"     pos="2.0 2.0 0.12" material="food_mat" contype="0" conaffinity="0" />
```

**`obstacle` at `pos="99 99"`**: Starts parked 99m away — outside the arena, invisible. `carl_simulation.py` moves it by writing to `model.geom_pos[model.geom("obstacle").id]`. The "park at 99" pattern prevents the obstacle from affecting the simulation until code intentionally moves it into the arena.

**`food` at `pos="2.0 2.0"` with `contype="0" conaffinity="0"`**: Food is initially placed at (2m, 2m) but is non-collidable (ghost). It's a purely visual target — CARL can't "collide" with food, it's detected by proximity distance checks in the Python code instead.

**`size="0.5 0.45"` for obstacle cylinder**: `size="radius half-height"` for cylinders. Radius 0.5m = 1m diameter. Half-height 0.45m = 0.9m tall. A substantial pillar obstacle.

**`size="0.12"` for food sphere**: 12cm radius = 24cm diameter ball. Bright green glowing sphere.

---

## LINES 59–69: Labyrinth Inner Walls

```xml
<geom name="lwall_v_0_2" type="box" size="0.05 0.9 0.25" pos="0.90  3.60 0.25" material="wall_mat" />
<geom name="lwall_v_2_0" type="box" size="0.05 0.9 0.25" pos="-2.70 0.00 0.25" material="wall_mat" />
...
<geom name="lwall_h_0_1" type="box" size="0.9 0.05 0.25" pos="-1.80 2.70 0.25" material="wall_mat" />
```

**11 inner wall segments** forming a maze inside the 10×10 arena. Naming convention: `lwall_v_ROW_COL` = vertical wall at grid position (row, col). `lwall_h` = horizontal.

**`size="0.05 0.9 0.25"`**: 10cm thick × 1.8m long × 0.5m tall. Short enough that the camera (mounted at ~0.25m height) can see over them.

**`pos z=0.25`**: Center of a 0.5m-tall wall sits at 0.25m. Bottom at floor (z=0), top at 0.5m — just below CARL's eye_cam at ~0.25m + torso height.

**Why a labyrinth?** Forces CARL to develop real navigation — not just straight-line driving to the goal. The 11 internal walls create dead ends, junctions, and forced turns that challenge pathfinding algorithms.

---

## LINES 72–75: Dynamic Hazard Cube

```xml
<body name="hazard_cube" pos="0 1.8 0.15">
  <joint name="hazard_joint" type="slide" axis="1 0 0" range="-1.5 1.5" damping="1.0" stiffness="0.0" />
  <geom name="dynamic_hazard" type="box" size="0.15 0.15 0.15" material="danger_mat" />
</body>
```

**`type="slide" axis="1 0 0"`**: A sliding (prismatic) joint — allows translation along X-axis only. The hazard cube slides LEFT and RIGHT, not up/down or forward/back.

**`range="-1.5 1.5"`**: Can slide ±1.5m from center. At center (0, 1.8) the cube blocks a corridor. Sliding ±1.5m creates a moving obstacle CARL must time its crossing.

**`stiffness="0.0"`**: No spring force — the cube doesn't return to center automatically. `damping="1.0"` = velocity damping only. Something external must push it, or it stays where collision left it.

**`size="0.15 0.15 0.15"`**: 30cm cube — large enough to block CARL (chassis width ~22cm) if driven into directly.

**Why a dynamic hazard?** Tests CARL's temporal planning — a static world is easy to map and navigate. A moving obstacle requires timing, prediction, and reactive replanning.

---

## LINES 80–113: Graspable Objects

```xml
<body name="obj_cube_0" pos="1.5 1.5 0.008">
  <freejoint name="fj_cube_0" />
  <geom name="gcube_0" type="box" size="0.008 0.008 0.008" mass="0.01"
        material="obj_blue" contype="4" conaffinity="9" friction="2.0 0.01 0.002" />
</body>
```

**3 blue cubes, 2 orange balls, 1 pink capsule toy** — small graspable objects for future arm manipulation training.

**`size="0.008 0.008 0.008"`** for cubes: 1.6cm × 1.6cm × 1.6cm. Tiny — the finger tips (3.6cm) can surround them.

**`<freejoint>`**: 6-DOF free body — can translate AND rotate freely in space. Needed because grasped objects must move with the hand.

**`contype="4" conaffinity="9"`**: Collision bitmask arithmetic:
- `contype=4` = binary `0100`
- `conaffinity=9` = binary `1001`
- Objects collide when `contype_A & conaffinity_B != 0` AND `contype_B & conaffinity_A != 0`
- Finger tips are `contype=8 (1000)`. `8 & 9 = 8 ≠ 0` → fingers CAN touch objects ✓
- Chassis is `contype=2 (0010)`. `2 & 9 = 0` → chassis CANNOT touch objects ✗ (prevents false grips from body contact)

**`friction="2.0 0.01 0.002"`**: High friction (2.0) on objects so fingers can grip reliably without slipping.

**`mass="0.01"` (10 grams)**: Light enough that finger motors (`kp=50, forcerange=5N`) can easily pick them up.

---

## LINES 118–119: Predator (Parked)

```xml
<geom name="predator"      type="sphere" size="0.18" pos="99 99 0.15" material="predator_mat"      contype="0" conaffinity="0" />
<geom name="predator_glow" type="sphere" size="0.22" pos="99 99 0.46" material="predator_glow_mat" contype="0" conaffinity="0" />
```

**`size="0.18"` (18cm radius = 36cm diameter)**: A large red sphere. When moved into the arena, it's visually unmistakable — bright red with `emission=1.0` + a larger `emission=1.5` glow shell around it.

**`contype="0" conaffinity="0"`**: No collisions. Like food, predator detection is done by distance check in Python — not physics contact. This prevents the predator from physically pushing CARL, which would dominate the dynamics.

**Two spheres (18cm + 22cm)**: The inner sphere is the "predator body." The larger outer sphere is the glow shell — overlapping the inner sphere to create a glowing halo effect.

---

## LINES 122–167: Ghost Walls and Debris (Parked at 99)

```xml
<geom name="ghost_wall_0" type="box" size="0.05 0.9 0.25" pos="99 99 99" material="ghost_wall_mat" />
...16 ghost walls total...
<geom name="debris_0" type="sphere" size="0.05" pos="99 99 99" material="debris_mat" mass="0.3" />
...12 debris pieces total...
```

**16 ghost walls**: Pre-allocated wall slots. `carl_simulation.py` can move any of them into the arena to create dynamic maze changes — walls that appear/disappear during an episode. The translucent `ghost_wall_mat` (rgba alpha 0.9) makes them look like energy barriers.

**12 debris pieces**: Scattered debris objects (spheres and boxes) parked at (99, 99, 99). Can be dropped into the arena as physical obstacles for advanced training. Have real mass (0.15–0.35 kg) so they bounce and roll realistically.

**Why 16 slots?** Pre-allocation avoids runtime XML modification. You can't ADD new geoms at runtime in MuJoCo — you must reserve them upfront and park them far away when unused.

---

## LINES 171–285: The Robot Kinematic Tree

This is the heart of the file — CARL's entire body defined as a tree of nested `<body>` elements. Understanding the tree requires following the nesting:

```
worldbody
└── drive_deck (freejoint: 6-DOF base)
    ├── chassis (collision body: 22cm × 18cm base plate)
    ├── lidar_scanner (decorative — no joint)
    ├── wheel_L (hinge joint: left drive wheel)
    ├── wheel_R (hinge joint: right drive wheel)
    ├── w_caster (rear ball caster — no joint, slides freely)
    ├── w_caster_front (front ball caster)
    └── swaying_hip (2 hinges: hip_pitch + hip_roll)
        └── torso
            ├── shoulder_link_L → upper_arm_L → forearm_L → gripper_base_L
            │   ├── finger_L_top (grip_L hinge + touch_site_L sensor)
            │   └── finger_L_bot (fixed)
            ├── shoulder_link_R → upper_arm_R → forearm_R → gripper_base_R
            │   ├── finger_R_top (grip_R hinge + touch_site_R sensor)
            │   └── finger_R_bot (fixed)
            └── neck_parallel_link → head (eye_cam)
```

### `drive_deck` (Lines 171–172)

```xml
<body name="drive_deck" pos="0 0 0.04">
  <freejoint name="spatial_identity" />
```

**`pos="0 0 0.04"`**: The robot's base plate starts 4cm above the floor. The wheels (radius 4cm) drop another 4cm down, putting the wheel contact point exactly at z=0 (floor level).

**`<freejoint name="spatial_identity">`**: 6-DOF unconstrained joint. This is what makes CARL a freely-moving body (not bolted to the world). `qpos` layout: `[x, y, z, qw, qx, qy, qz, joint1, joint2, ...]`. The 7 DOF of this freejoint occupy the first 7 elements of `qpos`.

**Why `name="spatial_identity"`?** The Python code does `model.joint("spatial_identity").qposadr[0]` to find the position in `qpos` where x,y,z coordinates live. The name is a semantic identifier — "this joint defines CARL's spatial position in the world."

### Chassis (Line 174)

```xml
<geom name="chassis" type="box" size="0.11 0.09 0.012" material="inner_frame" mass="2.5" contype="2" conaffinity="1" />
```

**`size="0.11 0.09 0.012"`**: 22cm long × 18cm wide × 2.4cm tall base plate.

**`mass="2.5"`**: 2.5 kg main chassis — the heaviest single component. This is the robot's center of gravity.

**`contype="2" conaffinity="1"`**: Chassis can collide with walls (`contype=1`) and other `contype=2` robot parts but NOT with objects (`contype=4`). This prevents the chassis from accidentally pushing graspable objects.

### LiDAR Scanner (Lines 177–180) — Decorative Only

```xml
<body name="lidar_scanner" pos="0.07 0 0.09">
  <geom type="cylinder" size="0.024 0.01" material="inner_frame" contype="0" conaffinity="0" />
  <geom type="cylinder" size="0.022 0.006" pos="0 0 0.006" material="laser_ring" contype="0" conaffinity="0" />
</body>
```

**No joint** → this is a rigidly-attached visual decoration. The actual LiDAR rays are computed in Python (`get_lidar()` in `carl_mj_physics.py`) using `mujoco.mj_ray()` — not from this XML element.

**Two cylinders**: Outer grey housing (radius 2.4cm) + inner cyan ring (radius 2.2cm, slightly recessed at z=0.006). Creates the visual appearance of a spinning LiDAR sensor at the front of the chassis.

### Wheels (Lines 183–196)

```xml
<body name="wheel_L" pos="0.0 0.11 0">
  <joint name="w_left" type="hinge" axis="0 1 0" damping="0.005" frictionloss="0.001" />
  <geom type="cylinder" size="0.04 0.016" euler="1.5708 0 0" material="inner_frame" friction="1.4" mass="0.05" contype="2" conaffinity="1" />
</body>
```

**`pos="0.0 0.11 0"`**: Left wheel is 11cm to the left of the chassis centerline. Right wheel is 11cm to the right. **Wheelbase = 22cm** (the distance between wheel contact patches for differential drive steering).

**`type="hinge" axis="0 1 0"`**: Rotates around the Y-axis (left-right axis). This is the rolling axis for forward/backward motion.

**`damping="0.005"`**: Very low damping (free-rolling). If stopped, wheels coast.

**`frictionloss="0.001"`**: Tiny Coulomb friction at the axle bearing. Real wheels aren't perfectly frictionless.

**`size="0.04 0.016"`**: Cylinder radius 4cm, half-length 1.6cm = 3.2cm wide. Wheel radius = 4cm.

**`euler="1.5708 0 0"`**: Rotate the cylinder 90° (π/2 rad) around X-axis. A cylinder's default axis in MuJoCo is Z. Rotating 90° around X makes it horizontal — so it rolls around Y as intended.

**`friction="1.4"`**: Wheel-floor friction = 1.4 (overrides the default 1.2). High grip. Allows strong traction without slipping.

**`mass="0.05"`** (50g each): Light wheels keep rotational inertia low — CARL can accelerate/decelerate quickly.

### Caster Balls (Lines 191–196)

```xml
<body name="w_caster" pos="-0.09 0 -0.022">
  <geom type="sphere" size="0.015" material="matte_shell" friction="0.002" mass="0.03" contype="2" conaffinity="1" />
</body>
```

**Two passive caster balls** (rear and front) — `pos="-0.09"` (rear) and `pos="0.09"` (front). 

**`pos z=-0.022`**: The caster ball center is 2.2cm below the chassis base. Ball radius = 1.5cm. So ball bottom at `0.04 (drive_deck) - 0.022 - 0.015 = 0.003m` ≈ floor level. Very slightly above floor to let wheels touch first.

**No joint**: Casters don't rotate in the XML — they're just rigid spheres. Their near-zero friction (`0.002`) lets them slide in any direction. MuJoCo handles the contact physics, so they effectively act like ball casters — rolling freely in 360°.

**Why two casters?** The two drive wheels (L+R) and two casters form a 4-point support base. Without casters, CARL would rock forward/backward (tipping over the 2-wheel axle). The front caster prevents forward pitching, the rear prevents backward pitching.

### Swaying Hip (Lines 199–201)

```xml
<body name="swaying_hip" pos="-0.01 0 0.015">
  <joint name="hip_pitch" type="hinge" axis="0 1 0" range="-0.55 0.55" stiffness="2.0" damping="0.2" />
  <joint name="hip_roll"  type="hinge" axis="1 0 0" range="-0.38 0.38" stiffness="2.0" damping="0.2" />
```

**Two-DOF hip connecting chassis to torso:**
- `hip_pitch`: Forward/backward lean (±0.55 rad = ±31.5°). If CARL drives over a bump, the torso can pitch forward/back without destabilizing the chassis.
- `hip_roll`: Left/right lean (±0.38 rad = ±21.8°). If CARL turns sharply, the torso can lean into the turn.

**`stiffness="2.0"`**: Spring force pulling hip back to zero (upright). Acts like a passive spring: `torque = -2.0 × angle`.

**`damping="0.2"`**: Velocity damping: `torque = -0.2 × angular_velocity`. The combination creates a damped spring (like a shock absorber) — torso sways but returns smoothly.

**Why a swaying hip?** Real robots with stiff connections between wheel base and upper body tip over easily during turns. A compliant hip allows weight shifting, reducing the risk of rollover.

### Arms — Left (Lines 208–236)

**5-DOF per arm: shoulder_yaw → shoulder → elbow → wrist → grip**

```xml
<joint name="shoulder_yaw_L" type="hinge" axis="0 0 1" range="-0.1 1.57" damping="2.0" />
```
**Shoulder yaw** (Z-axis rotation): Sweeps arm forward from body. Range `-0.1 to 1.57 rad (0° to 90°)`. When at 0°, arm points sideways. At 1.57 rad, arm reaches forward.

```xml
<joint name="shoulder_L" type="hinge" axis="0 1 0" range="-2.0 2.0" damping="2.0" />
<geom name="gua_L" type="capsule" fromto="0 0 0  0.12 0 0" size="0.012" />
```
**Shoulder flex/extend** (Y-axis): Full ±2.0 rad (±114°). Lifts arm up/down. **`fromto="0 0 0  0.12 0 0"`**: Capsule drawn from the joint center to 12cm along X-axis = upper arm length = 12cm.

```xml
<joint name="elbow_L" type="hinge" axis="0 1 0" range="-2.44 0" damping="1.5" />
<geom name="gfa_L" type="capsule" fromto="0 0 0  0.11 0 0" size="0.010" />
```
**Elbow** (Y-axis): Only bends toward body (`range="-2.44 0"` = 0° to -140°). Cannot hyperextend. Forearm length = 11cm.

**Total arm reach** = shoulder_link (0cm) + upper_arm (12cm) + forearm (11cm) + wrist block (1.2cm) + finger (3.6cm) ≈ **28cm reach from shoulder**.

```xml
<joint name="grip_L" type="hinge" axis="0 0 1" range="0 0.52" damping="0.8" />
<geom name="finger_L_tip" type="box" size="0.018 0.005 0.010" pos="0.018 0 0" material="finger_mat" contype="8" conaffinity="13" />
<site name="touch_site_L" pos="0.036 0 0" size="0.008" rgba="1 0 0 0.3" />
```

**Grip joint** (Z-axis): Opens/closes finger. Range `0 to 0.52 rad = 0° to 30°`. Only ONE finger moves — the bottom finger is fixed (passive). The top finger swings down to pinch.

**`size="0.018 0.005 0.010"`**: Finger tip: 3.6cm long × 1cm wide × 2cm tall. Positioned at `pos="0.018"` = 1.8cm from hinge = extends to 3.6cm total.

**`touch_site_L`**: A touch sensor site at the very tip of the finger (3.6cm from hinge). The `<sensor>` block later reads contact force at this point.

**Right arm** (Lines 239–267): Mirror image of left arm. Main difference: `shoulder_yaw_R range="-1.57 0.1"` (reaches the OTHER side — range is flipped from -90° to 0°).

### Head + Camera (Lines 270–279)

```xml
<body name="neck_parallel_link" pos="0.01 0 0.07">
  <joint name="neck_sweep" type="hinge" axis="0 1 0" range="-0.6 0.7" stiffness="0.5" damping="0.1" />
  ...
  <body name="head" pos="0 0 0.08">
    <joint name="head_pan" type="hinge" axis="0 0 1" range="-1.4 1.4" damping="0.1" />
    <camera name="eye_cam" pos="0.048 0 0.005" xyaxes="0 -1 0 0 0 1" fovy="65"/>
  </body>
</body>
```

**Neck nod** (`neck_sweep`): Tilts head up/down. Range `-0.6 to 0.7 rad = -34° to 40°`. Slight downward range allows CARL to look at nearby floor objects.

**Head pan** (`head_pan`): Turns head left/right. Range ±1.4 rad = ±80°. Almost full 180° horizontal scan.

**`eye_cam`**: 
- `pos="0.048 0 0.005"`: Camera 4.8cm in front of head center, 0.5cm up (eyeball position)
- `xyaxes="0 -1 0 0 0 1"`: X-axis of camera points RIGHT (world -Y), Y-axis points UP (world +Z). This correctly orients the camera for forward-looking view.
- `fovy="65"`: 65° vertical field of view. Combined with 160×120 resolution: `f = 120/(2×tan(32.5°)) = 94.3 pixels`.

---

## LINES 289–313: Actuators

```xml
<!-- DRIVE WHEELS: Velocity control -->
<velocity name="act_w_left"  joint="w_left"  kv="0.5" forcelimited="true" forcerange="-0.35 0.35" ctrllimited="true" ctrlrange="-35 35" />
<velocity name="act_w_right" joint="w_right" kv="0.5" forcelimited="true" forcerange="-0.35 0.35" ctrllimited="true" ctrlrange="-35 35" />
```

**Velocity-controlled wheels** (NOT position, NOT torque):
- `kv="0.5"`: Velocity gain. Torque = `kv × (target_vel - actual_vel) × radius`. Control input is a TARGET angular velocity (rad/s).
- `ctrlrange="-35 35"`: Max ±35 rad/s = ±140 cm/s wheel rim speed = ±0.56 m/s at 4cm radius. This caps CARL's maximum speed.
- `forcerange="-0.35 0.35"`: The resulting torque is capped at ±0.35 N·m. Protects the motor from stall torque damage.

**Why velocity control for wheels, position control for arms?** Wheels need to maintain a continuous speed. Position control for wheels would mean "go to angle 45° and stop" — wrong for driving. Arms need to reach specific angles precisely (joint angle = task space position). Position control is perfect for that.

```xml
<!-- HIP + NECK + HEAD: Position control -->
<position name="act_hip_pitch" joint="hip_pitch" kp="2.0" ctrlrange="-0.55 0.55" />
<position name="act_neck"      joint="neck_sweep" kp="0.1" ctrlrange="-0.6 0.7" />
<position name="act_head"      joint="head_pan"   kp="0.5" ctrlrange="-1.4 1.4" />
```

**`kp="2.0"` for hip**: Torque = `kp × (target_angle - actual_angle)`. Stiff enough to hold against gravity but compliant enough for the swaying effect.

**`kp="0.1"` for neck**: Very soft spring on neck. CARL doesn't need a precise neck angle — it should gently nod rather than snap.

```xml
<!-- ARM JOINTS: High-gain position control -->
<position name="act_shoulder_yaw_L" joint="shoulder_yaw_L" kp="120.0" ctrlrange="-0.1 1.57" />
<position name="act_shoulder_L"     joint="shoulder_L"     kp="120.0" ctrlrange="-2.0 2.0" />
<position name="act_elbow_L"        joint="elbow_L"        kp="100.0" ctrlrange="-2.44 0" />
<position name="act_wrist_L"        joint="wrist_L"        kp="60.0"  ctrlrange="-1.57 1.57" />
<position name="act_grip_L"         joint="grip_L"         kp="50.0"  ctrlrange="0 0.52" />
```

**`kp="120"` for shoulder**: Very stiff position control. Shoulder must hold the arm's weight against gravity. `kp=120` generates 120 N·m per radian of error. For a 0.07kg forearm + 0.05kg upper arm at 12cm extension: torque needed ≈ `(0.07+0.05) × 9.81 × 0.12 ≈ 0.14 N·m`. Even 1° of error generates `120 × (π/180) = 2.1 N·m` — more than enough.

**`kp` decreasing from shoulder (120) to grip (50)**: Distal joints (closer to fingertips) are lighter — they need less torque to hold position. Reducing kp also improves stability (very high kp + inertia = oscillation).

**`forcerange` from default `<position>` block = ±5 N·m** for all arm joints (inherited since no override specified). Sufficient for the arm's light mass.

---

## LINES 316–319: Touch Sensors

```xml
<sensor>
  <touch name="touch_L" site="touch_site_L" />
  <touch name="touch_R" site="touch_site_R" />
</sensor>
```

**`<touch>` sensor**: Reports the total normal contact force (in Newtons) at the specified `site`. When a finger tip touches an object, `data.sensordata[touch_L_id]` goes positive.

**Why place sites at finger tips?** Contact forces at the finger tip tell CARL:
- `force > 0`: Finger is touching something (grip trigger)
- `force > threshold`: Object is being gripped firmly enough to lift

**`data.sensordata` layout**: Each sensor occupies consecutive elements. `touch_L` is the first sensor → `data.sensordata[0]`. `touch_R` → `data.sensordata[1]`.

---

## COMPLETE JOINT + ACTUATOR SUMMARY

| Joint | DOF | Range | Actuator Type | kp/kv |
|---|---|---|---|---|
| `spatial_identity` | 6 (freejoint) | unlimited | none | — |
| `w_left` | 1 (hinge) | unlimited | velocity | kv=0.5 |
| `w_right` | 1 (hinge) | unlimited | velocity | kv=0.5 |
| `hip_pitch` | 1 (hinge) | ±31.5° | position | kp=2.0 |
| `hip_roll` | 1 (hinge) | ±21.8° | position | kp=2.0 |
| `neck_sweep` | 1 (hinge) | -34° to +40° | position | kp=0.1 |
| `head_pan` | 1 (hinge) | ±80° | position | kp=0.5 |
| `shoulder_yaw_L/R` | 1+1 | 0° to ±90° | position | kp=120 |
| `shoulder_L/R` | 1+1 | ±114° | position | kp=120 |
| `elbow_L/R` | 1+1 | -140° to 0° | position | kp=100 |
| `wrist_L/R` | 1+1 | ±90° | position | kp=60 |
| `grip_L/R` | 1+1 | 0° to 30° | position | kp=50 |

**Total DOF: 7 + 10 arm + 4 body = 21 controllable DOF** (plus the 6 freejoint DOF = 27 total in the system).

**Currently active in carl_simulation.py:** Only `act_w_left`, `act_w_right` (the 2 wheel velocity controllers). The 16 arm actuators exist but receive zero control input — arms hang passively. **This is the 65% completion gap** documented in `docs/integration_roadmap.md`.
