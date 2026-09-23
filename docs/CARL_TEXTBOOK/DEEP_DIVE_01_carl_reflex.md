# 🔬 DEEP DIVE #1 — `carl_reflex.py` (Every Line, Every Number, Every Why)
> *177 lines. Zero skipped. Every operator, matrix, value, algorithm explained.*

---

## FILE PURPOSE

This file is CARL's **spinal cord reflex arc**. In biology, a spinal cord reflex happens without involving the brain — your hand pulls away from fire *before* your brain consciously registers it. That's exactly what this does: it runs an obstacle-avoidance correction **every 33ms**, independently of the reservoir brain.

The algorithm is a **Leaky Integrate-and-Fire (LIF) Spiking Neural Network (SNN)** — the simplest biologically realistic neuron model. It uses **Reward-Modulated Spike-Timing Dependent Plasticity (R-STDP)** to adapt its connection strengths over time based on dopamine reward signals.

---

## LINE-BY-LINE BREAKDOWN

---

### Lines 1–9: Module Docstring

```python
"""
carl_reflex.py — Spiking Neural Network LIF Obstacle Avoidance Layer (END-205)

Implements Leaky Integrate-and-Fire (LIF) reflex mechanics.
Uses a differential steering connectivity profile:
  - Obstacles on the left excite the left-turn reflex (slowing the left wheel, speeding up the right).
  - Obstacles on the right excite the right-turn reflex (slowing the right wheel, speeding up the left).
  - If a front collision is imminent (d < 0.35m), triggers a backup-and-spin sequence.
"""
```

**Why this docstring?** It declares the design contract. The triple-quoted string `"""..."""` in Python is called a **docstring** — it's documentation embedded in the code. `END-205` is a diagnostic tracking code for this subsystem.

**"Differential steering"** = Two-wheeled robot where turning is achieved by spinning wheels at different speeds. No separate steering axle needed. This is how tank tracks work, how Roomba works, how CARL works.

---

### Line 10: `import math`

```python
import math
```

**Why `math` and not `numpy`?** For single scalar operations (like `math.exp`, `math.cos`), Python's built-in `math` library is **faster** than numpy because numpy has overhead for array operations. Here we use `math.exp()` to precompute decay constants — single numbers, not arrays. So `math` is the right choice.

---

### Line 11: `import numpy as np`

```python
import numpy as np
```

**Why `numpy`?** Because we have **arrays** of numbers (24 sensors, 2 motor neurons, 2×24 weight matrix). Numpy performs operations on entire arrays at once using **vectorized C code** — far faster than Python for-loops. The alias `np` is universal convention.

---

### Lines 14–18: Class Declaration

```python
class SpikingReflexLayer:
    """
    Leaky Integrate-and-Fire (LIF) obstacle avoidance reflex layer.
    Outputs differential wheel speeds to steer CARL away from obstacles.
    """
```

**`class`** = A blueprint (template) for creating objects. Each time you call `SpikingReflexLayer()`, you create one **instance** — a unique copy with its own internal state. The class bundles all the reflex data (weights, voltages, timers) together with the functions that operate on them.

---

### Lines 19–21: `__init__` — Constructor

```python
def __init__(self, num_sensors=24, num_motor_neurons=2):
    self.num_sensors = num_sensors
    self.num_motors = num_motor_neurons  # [0]: Turn Left, [1]: Turn Right
```

`__init__` = Python's **constructor** — runs automatically when you create the object.

**`self`** = Reference to the specific instance being created. Anything stored as `self.X` persists across function calls.

**Why `num_sensors=24`?**
CARL has a 24-ray LiDAR. 24 rays means **15° resolution** (360°/24 = 15°). This is fine enough to detect wall openings in a 1.2m-wide corridor and too many rays would slow computation.

**Why `num_motor_neurons=2`?**
Differential drive has exactly TWO independent degrees of freedom: left wheel speed and right wheel speed. Motor neuron 0 governs LEFT. Motor neuron 1 governs RIGHT.

---

### Lines 23–26: Membrane Voltages and Time Constants

```python
self.V = np.zeros(self.num_motors)   # Shape: (2,) — voltage of [motor_0, motor_1]
self.V_th = 1.0                       # Firing threshold
self.tau_m = 0.02                     # Membrane time constant: 20 milliseconds
self.dt = 0.033                       # Control timestep: 33 milliseconds ≈ 30 Hz
```

**`self.V = np.zeros(2)`**: A 1D numpy array `[0.0, 0.0]`. This is the **membrane potential** (voltage) of each motor neuron. Think of it like the "charge" building up in a capacitor. Starts at zero = resting state.

**Why `V_th = 1.0`?** Dimensionless threshold. When voltage ≥ 1.0, neuron fires. The actual physical analogy is ~-55mV (relative to resting potential) in real neurons, but we normalize to 1.0 for computation. The WEIGHTS are tuned relative to this threshold — weights of 1.8–3.0 mean a single sensor spike can push voltage over threshold quickly.

**Why `tau_m = 0.02` (20ms)?**
This is the **membrane leak time constant**. In real neurons, the membrane RC time constant is 10–30ms. 20ms is biologically accurate for a fast sensorimotor reflex neuron (like those in the spinal cord). Mathematically:

```
V(t) = V₀ × e^(-t/τ_m)
```

After one time constant (20ms), voltage decays to `V₀ × e^(-1) ≈ 0.37 × V₀`. After 3τ ≈ 60ms, it's essentially gone.

**Why `dt = 0.033`?** The control loop runs at **30 Hz** (30 updates per second), so each tick is `1/30 ≈ 0.033 seconds = 33ms`. This is the physics simulation timestep granularity.

---

### Lines 28–48: Weight Matrix Construction — The Key Algorithm

```python
self.w = np.zeros((self.num_motors, self.num_sensors))  # Shape: (2, 24)
angles = np.linspace(-np.pi, np.pi, num_sensors, endpoint=False)  # (24,)
```

**`self.w`**: A **2×24 matrix**. Each row is one motor neuron. Each column is one sensor. Entry `w[i, j]` = "how much does sensor j excite motor neuron i?"

```
self.w = 
    sensor:  0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  20  21  22  23
Motor 0:    [?, ?, ?, ?, ?, ?, ?, ?, ?, ?,  ?,  ?,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
Motor 1:    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  0,  0,  ?,  ?,  ?,  ?,  ?,  ?,  0,  0,  0,  0,  0,  0]
```
(zeros in back hemisphere, values in front hemisphere)

**`np.linspace(-np.pi, np.pi, 24, endpoint=False)`**:
Creates 24 evenly-spaced angles from -π to +π, NOT including +π (to avoid double-counting). Result: `[-π, -π+2π/24, -π+4π/24, ..., π-2π/24]` which in degrees is `[-180°, -165°, -150°, ..., 165°]`. This maps each of 24 LiDAR beams to a physical angle around the robot.

**`endpoint=False`**: Because the circle wraps — -180° and +180° are the SAME direction (directly behind). Including both would double-count the rear.

---

```python
for j in range(num_sensors):          # j = 0, 1, 2, ..., 23
    a = angles[j]                      # angle in radians for this sensor beam
    if -np.pi/2 <= a <= np.pi/2:      # FRONT HALF only: -90° to +90°
```

**Why only front half?** Back-facing sensors detecting obstacles behind CARL should NOT trigger a front-steering reflex. If CARL is moving forward and detects something behind, turning is irrelevant. The reflex only responds to front-sector threats.

**`-np.pi/2`** = -90° (right side)
**`np.pi/2`** = +90° (left side)

---

```python
        if a < 0:                                                    # Front-RIGHT sector
            self.w[0, j] = 3.0 * (1.0 - abs(a) / (np.pi/2))        # Excite "Turn Left" motor
```

**Why excite "Turn Left" when obstacle is on the RIGHT?**
This is the **Braitenberg Vehicle** wiring rule: wires CROSS. Obstacle on right → turn left to avoid it. Exactly like how your hands steer a bicycle away from a wall.

**Why `3.0 * (1.0 - abs(a) / (np.pi/2))`?**
This is a **linear falloff** from center to edge:
- At `a = 0` (directly ahead): weight = `3.0 × (1 - 0) = 3.0` (maximum)
- At `a = -45°` (-π/4): weight = `3.0 × (1 - 0.5) = 1.5` (half strength)
- At `a = -90°` (-π/2): weight = `3.0 × (1 - 1.0) = 0.0` (no effect)

**Why use linear, not Gaussian or cosine?** Linear is simplest, fastest to compute, and sufficient for this application. A Gaussian would be smoother but more expensive. Linear gives a clean "gradual handoff" from directly-ahead threats to side threats.

**Why weight `3.0`?** With `V_th = 1.0` and typical input currents, a single spike from a directly-ahead sensor creates a current of `3.0 × 1 = 3.0` in the motor neuron — triple the threshold. This ensures **immediate firing** for frontal threats. If weight were 0.5, it would take 2 consecutive ticks of sensor spikes to fire — too slow for collision avoidance.

---

```python
        elif a > 0:                                                  # Front-LEFT sector
            self.w[1, j] = 3.0 * (1.0 - a / (np.pi/2))             # Excite "Turn Right" motor
```

Symmetric logic: obstacle on LEFT → excite "Turn Right" motor.

---

```python
        else:                    # a == 0: directly ahead
            self.w[0, j] = 1.8  # Excite both motors
            self.w[1, j] = 2.2
```

**Why both motors for directly-ahead obstacle?** When something is exactly in front, NEITHER a pure left-turn NOR a pure right-turn is obviously correct. Exciting both means they compete. The slight asymmetry (1.8 vs 2.2) means Motor 1 (Turn Right) fires slightly more often — making CARL have a **natural bias to turn right** when stuck head-on. This breaks the symmetry and prevents CARL from oscillating in-place forever.

**Why 1.8 and 2.2 specifically?** The sum `1.8 + 2.2 = 4.0` is similar to the maximum single-side weight (3.0), meaning the total excitation into both motors is comparable. The asymmetry ratio 1.8:2.2 = 0.818 is arbitrary — just needs to be different enough to break symmetry but close enough to not hard-code a specific turn direction in all situations.

---

### Lines 50–62: R-STDP Variables

```python
self.trace_pre = np.zeros(self.num_sensors)              # Shape: (24,) — pre-synaptic traces
self.trace_post = np.zeros(self.num_motors)              # Shape: (2,) — post-synaptic traces
self.eligibility = np.zeros((self.num_motors, self.num_sensors))  # Shape: (2, 24) — eligibility traces
```

**What are traces?** In R-STDP, learning doesn't happen instantly. Instead:
1. Every time a pre-synaptic neuron (sensor) fires, `trace_pre[j]` jumps up, then decays
2. Every time a post-synaptic neuron (motor) fires, `trace_post[i]` jumps up, then decays
3. The **eligibility trace** `eligibility[i,j]` captures the CORRELATION between pre and post firing

**Why (2, 24) eligibility matrix?** One eligibility value per synapse (connection). 2 motors × 24 sensors = 48 synapses total.

---

```python
self.tau_stdp = 0.02   # STDP trace decay: 20ms
self.tau_e = 0.1       # Eligibility trace decay: 100ms
self.eta_stdp = 0.01   # Learning rate
```

**Why `tau_stdp = 0.02` (20ms)?** Matches biology — real STDP traces decay with τ ≈ 10-30ms. This means the trace from a spike "remembers" that spike for ~60ms (3 time constants).

**Why `tau_e = 0.1` (100ms)?** The eligibility trace must decay SLOWER than the spike traces — it needs to "bridge" the gap between when an action is taken and when the reward (dopamine) arrives. Dopamine is released hundreds of milliseconds after the action, so eligibility must persist longer (100-500ms range). 100ms is on the shorter end but keeps things simple.

**Why `eta_stdp = 0.01`?** Learning rate — 1% of the eligibility signal is added to the weight each update. Too large → weights blow up. Too small → never learns. 0.01 is a standard starting point for neural plasticity simulations.

---

### Lines 59–62: Pre-computing Decay Constants

```python
self.pre_decay  = math.exp(-self.dt / self.tau_stdp)   # ≈ e^(-0.033/0.02) ≈ e^(-1.65) ≈ 0.192
self.post_decay = math.exp(-self.dt / self.tau_stdp)   # same ≈ 0.192
self.elig_decay = math.exp(-self.dt / self.tau_e)      # ≈ e^(-0.033/0.1)  ≈ e^(-0.33) ≈ 0.719
self.mem_decay  = math.exp(-self.dt / self.tau_m)      # ≈ e^(-0.033/0.02) ≈ 0.192
```

**Why precompute?** `math.exp()` is expensive. Since `dt`, `tau_stdp`, `tau_e`, and `tau_m` never change during runtime, computing the decay factor ONCE in `__init__` and reusing it in `step()` (which runs 30×/sec) saves significant CPU time.

**The math:** Exponential decay formula: `V(t) = V₀ × e^(-t/τ)`. After one timestep `dt`:
```
V(t+dt) = V(t) × e^(-dt/τ)
```
So the "one-step decay factor" is `e^(-dt/τ)`.

- `pre_decay ≈ 0.192` means traces decay FAST (lose 80% every tick at 30Hz = essentially gone in 100ms)
- `elig_decay ≈ 0.719` means eligibility decays SLOW (loses 28% per tick = lasts ~300ms)
- `mem_decay ≈ 0.192` means membrane voltage decays fast (responsive to recent spikes)

---

### Lines 64–69: Output Motor Variables

```python
self.reflex_outputs = np.zeros(2)       # [speed_left_delta, speed_right_delta]
self.tau_motor = 0.1                    # Motor output smoothing: 100ms
self.motor_decay = math.exp(-self.dt / self.tau_motor)  # ≈ e^(-0.33) ≈ 0.719
self.backup_timer = 0                   # Countdown for backup maneuver (in ticks)
self.backup_spin_dir = 1.0              # +1 = spin left, -1 = spin right
```

**`self.reflex_outputs = np.zeros(2)`**: The actual motor speed adjustments this reflex sends. Shape `(2,)` = `[left_delta, right_delta]`.

**Why smooth the motor output (`tau_motor = 0.1`)?** Without smoothing, a single sensor spike → single motor spike → motor command jumps instantly → wheel jerks. Smoothing with `motor_decay` creates a **low-pass filter** on the motor output: spikes contribute a temporary boost that fades over ~300ms. This prevents wheel-banging oscillations and makes movement more realistic and stable.

**Why `backup_timer = 0`?** Starts at 0 = "not backing up". When a collision is imminent, this is set to 20 (ticks). Each tick it decrements by 1. When it reaches 0, backup is over.

**Why `backup_spin_dir = 1.0`?** +1.0 = spin counterclockwise (left). Set when the backup begins based on which side has more clearance.

---

### Lines 71–81: `step()` — The Main Function Signature

```python
def step(self, sensor_dists: np.ndarray, reservoir_bias: np.ndarray, da: float, food_dist: float = 99.0) -> np.ndarray:
    """
    Step SNN reflex. Returns [left_speed_delta, right_speed_delta].
    """
    spikes_pre = np.zeros(self.num_sensors)   # Shape: (24,) — which sensors fired this tick
    nu_max = 100.0                             # Maximum spike rate in Hz
```

**Arguments:**
- `sensor_dists`: numpy array of 24 LiDAR distances (shape (24,))
- `reservoir_bias`: numpy array of shape (2,) — additional input from the reservoir brain
- `da`: float — current dopamine level (from EndocrineSystem)
- `food_dist`: float — distance to nearest food (changes thresholds near food)

**Return value:** numpy array shape (2,) = [left_wheel_adjustment, right_wheel_adjustment]

**`nu_max = 100.0`**: Maximum firing rate = 100 spikes per second. This is used in the Poisson spike generation math below.

---

### Lines 78–84: Dynamic Threshold Adjustment

```python
d_trigger = 0.45      # Start warning at 45cm
collision_limit = 0.28  # Emergency backup at 28cm
if food_dist < 1.0:
    d_trigger = 0.32      # Near food: allow closer approach
    collision_limit = 0.20
```

**Why `d_trigger = 0.45`?** 45cm is chosen based on CARL's speed (max ~8 motor units) and reaction time (33ms latency). At full speed, CARL might travel ~5-8cm per tick. Starting evasion at 45cm gives ~9 ticks (300ms) to stop.

**Why reduce to `0.32` near food?** The food sphere is 24cm diameter. If CARL starts dodging at 45cm, it might never get close enough to eat. Near food, CARL needs to squeeze closer — 32cm clearance is enough because it's moving more slowly and cautiously.

**`collision_limit = 0.28`**: 28cm is approximately CARL's chassis half-width (12cm chassis + 8cm tire + 8cm safety margin ≈ 28cm). Below this, actual physical contact is imminent.

---

### Lines 86–92: Front/Rear Collision Detection

```python
min_front_dist = np.min(sensor_dists[9:15])   # Sensors 9-14: front cone (±45°)
imminent_collision = min_front_dist < collision_limit

min_rear_dist = min(sensor_dists[0], sensor_dists[1], sensor_dists[23])  # Rear sensors
imminent_rear_collision = min_rear_dist < 0.25
```

**Why sensors 9-14 for front?** 
With 24 rays from -180° to +165° (15° apart), sensor index:
- Index 0 = -180° (directly behind)
- Index 6 = -90° (directly right)
- Index 12 = 0° (directly ahead)
- Index 18 = 90° (directly left)

So sensors 9-14 span from -45° to +30° — roughly the front cone. Using `np.min()` takes the CLOSEST obstacle in that cone — worst-case distance.

**Why sensors 0, 1, 23 for rear?** Index 0 = -180°, index 1 = -165°, index 23 = 165°. These are the three sensors closest to directly behind. Checking all three catches a rear wall even if CARL is slightly angled.

**`min()` vs `np.min()`:** Using Python's built-in `min()` for 3 specific values is faster than NumPy (avoids array creation overhead). NumPy's `np.min(sensor_dists[9:15])` is used for 6-element slice where numpy's vectorization helps.

---

### Lines 94–100: Backup State Machine

```python
if imminent_collision and self.backup_timer == 0:
    self.backup_timer = 20   # Back up for 20 ticks
    left_clear  = np.mean(sensor_dists[6:12])   # Average distance: left sector (sensors 6-11)
    right_clear = np.mean(sensor_dists[12:18])  # Average distance: right sector (sensors 12-17)
    self.backup_spin_dir = 1.0 if left_clear > right_clear else -1.0
```

**State Machine logic:** `backup_timer == 0` means "not currently backing up." The collision condition only STARTS a backup if not already in one (prevents resetting the timer mid-backup).

**Why 20 ticks?** `20 ticks × 0.033 sec/tick = 0.66 seconds`. Analysis: at a backing-up speed of ~4.5 motor units and wheel radius 7cm, CARL moves roughly 10cm/second backward. In 0.66 seconds, it moves ~6-7cm backward — enough to clear a typical wall contact.

**`np.mean(sensor_dists[6:12])`**: Sensors 6-11 = left hemisphere (-90° to +15°). Average distance to obstacles on that side. Higher = more clearance.

**`np.mean(sensor_dists[12:18])`**: Sensors 12-17 = right hemisphere (-15° to +90°). Same logic for right side.

**Selection logic:** `1.0 if left_clear > right_clear else -1.0`: If left has more space → spin left (+1). If right has more space → spin right (-1). This chooses the spin direction that moves CARL away from the tighter space.

---

### Lines 102–107: Probabilistic Spike Generation (Poisson Process)

```python
for j in range(self.num_sensors):
    d = sensor_dists[j]
    if d < d_trigger:
        p = nu_max * (1.0 - d / d_trigger) * self.dt
        if np.random.rand() < min(1.0, p):
            spikes_pre[j] = 1.0
```

**This is the core Poisson spike model.** In real neuroscience, sensory neurons generate spikes according to a Poisson process — the probability of firing in any short time window is proportional to the neuron's firing rate.

**Step 1:** Calculate firing rate `ν` (spikes per second):
```
ν = nu_max × (1.0 - d/d_trigger)
```
- When `d = 0` (obstacle touching): `ν = 100 Hz` (fires as fast as possible)
- When `d = d_trigger/2`: `ν = 50 Hz` (fires half the time)
- When `d = d_trigger`: `ν = 0 Hz` (never fires)

Linear interpolation from 0 to nu_max as distance decreases from d_trigger to 0.

**Step 2:** Convert firing rate to per-tick spike probability:
```
p = ν × dt = 100 × (1 - d/d_trigger) × 0.033
```
At d=0: `p = 100 × 1 × 0.033 = 3.3` → clamped to `min(1.0, 3.3) = 1.0` = fires every tick
At d=d_trigger/2: `p = 100 × 0.5 × 0.033 = 1.65` → clamped to 1.0 = fires every tick (still very close)
At d=d_trigger×0.9: `p = 100 × 0.1 × 0.033 = 0.33` = fires 33% of ticks

**Why `min(1.0, p)`?** Probability can't exceed 1.0. When the obstacle is very close, `ν × dt > 1.0`, so we clamp.

**`np.random.rand()`**: Generates a uniform random number in [0, 1). If it's less than `p`, the sensor fires. This is the classic **Bernoulli trial** for Poisson spike simulation.

**Why stochastic?** In real biological neurons, spike timing has inherent variability (jitter). This stochasticity also provides **exploration** — sometimes CARL reacts to a close obstacle, sometimes it just barely doesn't, giving natural variation in behavior.

---

### Lines 109–117: LIF Membrane Integration — The Core Neuron Equation

```python
current_inputs = np.dot(self.w, spikes_pre) + reservoir_bias
self.V = self.V * self.mem_decay + current_inputs
```

**The LIF equation (one discrete timestep):**
```
V[t+dt] = V[t] × e^(-dt/τ_m) + I[t]
```
where `I[t] = W @ spikes + bias`

**`np.dot(self.w, spikes_pre)`**: Matrix-vector multiplication.
- `self.w` shape: (2, 24)
- `spikes_pre` shape: (24,)
- Result shape: (2,) — one current value per motor neuron

This computes: for each motor neuron `i`, sum up `w[i,j] × spikes_pre[j]` for all 24 sensors. Only sensors that fired (`spikes_pre[j] = 1.0`) contribute. Sensors that didn't fire contribute 0.

**`+ reservoir_bias`**: Adds the reservoir brain's "hint" to each motor neuron. This allows the higher brain to modulate the reflex — if the reservoir thinks CARL should turn right, it can bias Motor 1 (Turn Right) upward.

**`self.V * self.mem_decay`**: The leaky part. Old voltage decays by factor `≈ 0.192` per tick. This means voltage from 5 ticks ago contributes `0.192^5 ≈ 0.00026` — effectively zero. The neuron only "remembers" the last ~3 ticks.

---

```python
spikes_post = np.zeros(self.num_motors)
for i in range(self.num_motors):
    if self.V[i] >= self.V_th:     # Threshold crossing check
        spikes_post[i] = 1.0        # Fire!
        self.V[i] = 0.0             # RESET (action potential)
```

**Threshold crossing:** If membrane voltage ≥ 1.0, the neuron fires ("action potential"). **After firing, voltage RESETS to 0**. This is the defining feature of LIF neurons — they're "all-or-nothing" with a hard reset, unlike rate-coded neurons that output a graded signal.

**Why reset to 0 instead of a negative "hyperpolarization" value?** Real neurons have afterhyperpolarization (dip below resting), but for simplicity here we reset to 0. Including hyperpolarization would require another parameter and doesn't significantly change behavior for this application.

---

### Lines 119–120: Motor Output Smoothing

```python
self.reflex_outputs *= self.motor_decay   # Decay old outputs: ≈ × 0.719
```

**Why decay BEFORE adding new spikes?** This creates a **first-order low-pass filter** (exponential moving average) on the motor output:
- Old output loses 28% each tick
- New spike contributions are added on top
- Net result: motor responds quickly to new spikes but smoothly, not jerkily

This is equivalent to a **leaky integrator** for the motor output, with τ=100ms.

---

### Lines 122–137: Dynamic Reflex Strength and Motor Application

```python
reflex_strength = 5.0
clamp_limit = 6.0
if food_dist < 1.2:
    reflex_strength = 1.0
    clamp_limit = 1.5
```

**Why weaker near food?** When food is within 1.2m, CARL should approach despite obstacles. If reflex_strength stays at 5.0, the reflex would override the food-seeking behavior entirely and CARL would bounce away. Reducing to 1.0 means the reflex is still active (won't crash) but doesn't dominate.

---

```python
if spikes_post[0] > 0:                       # "Turn Left" motor fired
    self.reflex_outputs[0] -= reflex_strength   # Slow down LEFT wheel (Δ=-5)
    self.reflex_outputs[1] += reflex_strength   # Speed up RIGHT wheel (Δ=+5)
```

**Differential drive turning math:** 
- Left wheel slows: reduces left side speed
- Right wheel accelerates: increases right side speed
- Net effect: robot turns LEFT (counterclockwise)

This is the fundamental **skid-steer** (tank-steer) control: differential speed between the two wheels creates rotation.

```python
if spikes_post[1] > 0:                       # "Turn Right" motor fired
    self.reflex_outputs[0] += reflex_strength   # Speed up LEFT wheel
    self.reflex_outputs[1] -= reflex_strength   # Slow down RIGHT wheel
```

Symmetric: speeds up left, slows right → turns RIGHT.

**Note:** Both motors CAN fire in the same tick (if both voltage thresholds are crossed). If that happens, effects partially cancel — producing a reduced, mixed response.

---

### Lines 139–157: Emergency Override — Backup and Spin FSM

```python
if self.backup_timer > 0:
    self.backup_timer -= 1
    if imminent_rear_collision:
        # BLOCKED FRONT + BACK: Spin in place
        self.reflex_outputs[0] = 3.5 * self.backup_spin_dir
        self.reflex_outputs[1] = -3.5 * self.backup_spin_dir
    else:
        # BLOCKED FRONT, CLEAR REAR: Curve backwards
        if self.backup_spin_dir > 0:
            self.reflex_outputs[0] = -4.5   # Fast reverse left wheel
            self.reflex_outputs[1] = -1.5   # Slower reverse right wheel
        else:
            self.reflex_outputs[0] = -1.5
            self.reflex_outputs[1] = -4.5
```

**Two sub-states in the backup FSM:**

**Case 1: Blocked front AND rear (corner/alcove)**
```
reflex_outputs[0] =  3.5 × spin_dir
reflex_outputs[1] = -3.5 × spin_dir
```
Equal but opposite wheel speeds = **pure rotation in place** (zero forward motion). Rotation direction is `spin_dir` (chosen at backup start based on clearer side).

**Why ±3.5?** Enough torque for meaningful rotation while not being so aggressive as to destabilize the robot.

**Case 2: Blocked front, clear rear (standard backup)**
```
Left  = -4.5
Right = -1.5  (or swapped depending on spin_dir)
```
Both negative = both wheels go in reverse. But asymmetrically: one side goes faster backward (-4.5) than the other (-1.5). This creates **curved reverse** — CARL doesn't just back straight into the same wall, it backs AND swings the front around toward the clearer direction.

**Why the specific values -4.5 and -1.5?**
The difference (-4.5) - (-1.5) = -3.0 creates the steering component. The average (-4.5 + -1.5)/2 = -3.0 is the reverse speed. Chosen empirically to clear a 1.2m-wide corridor in ~20 ticks.

---

```python
elif imminent_rear_collision:
    # Rear blocked, front clear: PUSH FORWARD
    self.reflex_outputs[0] = 3.0
    self.reflex_outputs[1] = 3.0
```

**Why push forward when rear is blocked?** If only the rear is blocked (CARL backed into a wall), the right response is to go forward — away from the rear obstacle. Both wheels = +3.0 = equal forward velocity = straight ahead.

---

### Line 160: Clamping

```python
self.reflex_outputs = np.clip(self.reflex_outputs, -clamp_limit, clamp_limit)
```

**`np.clip(array, min, max)`**: Clamps every element to [min, max]. Prevents runaway values from accumulating over many ticks if multiple spikes keep adding up.

**Why `clamp_limit = 6.0`?** The main simulation allows motor speeds up to ±20. The reflex contributes a maximum ±6 delta, which is 30% of max speed. This ensures reflex corrections are influential but don't completely override forward locomotion commanded by the higher brain.

---

### Lines 162–174: R-STDP Eligibility Trace Update

```python
self.trace_pre  = self.trace_pre  * self.pre_decay  + spikes_pre    # Update pre trace
self.trace_post = self.trace_post * self.post_decay + spikes_post   # Update post trace

for i in range(self.num_motors):
    for j in range(self.num_sensors):
        self.eligibility[i, j] = (
            self.eligibility[i, j] * self.elig_decay
            + (self.trace_pre[j] * spikes_post[i]   # LTP term: pre trace × post spike
             - self.trace_post[i] * spikes_pre[j])  # LTD term: post trace × pre spike
        )
```

**STDP rule (Spike-Timing Dependent Plasticity):**

`trace_pre[j]`: Running average of recent spikes from sensor j. High if sensor j fired recently.

`trace_post[i]`: Running average of recent spikes from motor i. High if motor i fired recently.

**LTP (Long-Term Potentiation) — strengthen:**
`trace_pre[j] × spikes_post[i]`
= "sensor j fired recently AND motor i fires NOW"
= sensor j was CAUSAL for motor i firing
→ **strengthen** the connection (make w[i,j] bigger)

**LTD (Long-Term Depression) — weaken:**
`trace_post[i] × spikes_pre[j]`
= "motor i fired recently AND sensor j fires NOW"
= sensor j fires AFTER motor i (non-causal correlation)
→ **weaken** the connection

The eligibility trace `eligibility[i,j]` builds up (+) when sensor j reliably precedes motor i, and decays (-) when the timing is reversed. Over many exposures, high eligibility = genuinely predictive synapse.

**`self.elig_decay ≈ 0.719`**: Eligibility fades with τ=100ms, so it "remembers" about 300ms of recent STDP events. The reward (dopamine) must arrive within ~300ms after the action to cause learning.

---

### Lines 172–174: Dopamine-Gated Weight Update

```python
da_error = da - 1.0          # Dopamine baseline is 1.0. Positive = reward, negative = punishment.
self.w += self.eta_stdp * self.eligibility * da_error
self.w = np.clip(self.w, -3.0, 3.0)
```

**3-factor learning rule (R-STDP):**
```
ΔW[i,j] = η × eligibility[i,j] × (DA - DA_baseline)
```

- `η = 0.01` = learning rate (1% of eligibility)
- `eligibility[i,j]` = how strongly this synapse is "candidate for change" (STDP correlation)
- `DA - 1.0` = **Reward Prediction Error (RPE)**: positive = better than expected, negative = worse

**Why DA_baseline = 1.0?** The EndocrineSystem sets `BASELINE_DA = 1.0`. When nothing special happens, DA = 1.0. When reward happens, DA > 1.0. So `DA - 1.0 > 0` means reward, strengthening recently-active synapses.

**`self.w = np.clip(self.w, -3.0, 3.0)`**: Weights can't grow indefinitely. Clamped to [-3.0, 3.0]. Why ±3.0? That's the initialization maximum weight. Allowing weights to grow beyond 3.0 could cause runaway excitation (positive feedback loop where strong weights cause strong firing causing weight growth).

**Why allow negative weights (-3.0)?** In neural networks, negative weights = inhibitory connections. A sensor that was reliably active when things went BADLY could have its weight driven negative — the reflex then DOES NOTHING when it sees that sensor pattern (because the inhibitory weight cancels excitation). This is adaptive inhibition.

---

### Line 176: Return

```python
return self.reflex_outputs.copy()
```

**Why `.copy()`?** Returns a **copy** of the array, not the original. If the caller modifies the returned array, it won't corrupt `self.reflex_outputs` which is used internally next tick. Always return `.copy()` from internal state arrays.

---

## SUMMARY TABLE

| Variable | Shape | Type | Why |
|---|---|---|---|
| `self.V` | (2,) | float32 | Membrane voltage per motor neuron |
| `self.w` | (2,24) | float64 | Synaptic weight matrix (learned) |
| `self.trace_pre` | (24,) | float64 | STDP pre-synaptic trace |
| `self.trace_post` | (2,) | float64 | STDP post-synaptic trace |
| `self.eligibility` | (2,24) | float64 | Synapse eligibility for learning |
| `self.reflex_outputs` | (2,) | float64 | Motor speed adjustments |
| `spikes_pre` | (24,) | float64 | Which sensors fired this tick |
| `spikes_post` | (2,) | float64 | Which motor neurons fired this tick |

## ALGORITHM FLOW (every tick)
```
1. Poisson spike generation:  sensor_dist → probability → Bernoulli trial → spikes_pre
2. LIF current injection:     spikes_pre × w + reservoir_bias → current
3. LIF membrane update:       V = V × mem_decay + current
4. Threshold check:           if V[i] ≥ 1.0 → fire, reset V[i]=0
5. Motor output accumulation: reflex_outputs += ±reflex_strength (per firing motor)
6. Backup FSM override:       if backup_timer > 0 → override with backup commands
7. Clip output:               np.clip(reflex_outputs, -6, 6)
8. R-STDP trace update:       trace_pre, trace_post, eligibility update
9. Weight update:             w += 0.01 × eligibility × (DA - 1.0)
10. Return motor delta:       [left_delta, right_delta]
```
