# 🤖 CARL — Complete Human-Readable Code Guide
> *Every file, every line, explained in plain English. No jargon without explanation.*

---

## 🗺️ What is This Whole Project?

This is **CARL** — a simulated robot that lives inside a virtual maze. CARL has a **brain** made of actual neuroscience — dopamine, serotonin, place cells, grid cells, the same stuff your brain uses. It learns to survive, find food, avoid walls, and remember where it's been — completely on its own, without being told what to do.

The project has two main folders:
- **`d:\ebca\`** — the main project (brain modules + world physics)
- **`d:\carl_simulation\`** — the newer Genesis simulation (robot arm + advanced body)

---

## 📁 PROJECT STRUCTURE AT A GLANCE

```
d:\ebca\
├── brain\               ← All the "thinking" code (neuroscience algorithms)
├── world\               ← The physical arena CARL lives in (XML robot body + physics)
├── GENESIS\             ← Newer, more advanced robot simulation
├── textbook\            ← Human-readable walkthrough documents (PDFs + Markdown)
├── memory\              ← Where CARL saves what it has learned
├── tests\               ← Code to check that everything works correctly
├── carl_simulation.py   ← The MAIN program that runs everything
├── live_plotter.py      ← Real-time dashboard showing what CARL is "thinking"
└── phase18_alife.py     ← A more advanced life-simulation version
```

---

# 🧠 BRAIN MODULE FILES
> These files live in `d:\ebca\brain\` and represent different parts of CARL's brain.

---

## 1. `carl_reflex.py` — The Spinal Cord (Automatic Obstacle Avoidance)

**What it does in one sentence:** When CARL is about to hit a wall, this runs a fast, automatic "dodge" — like how your hand pulls away from a hot stove before you even think about it.

**The Big Idea:** This uses a type of neuron model called **Leaky Integrate-and-Fire (LIF)**. Just like real neurons, these artificial neurons "charge up" when stimulated, and "fire" (send a signal) when the charge crosses a threshold.

---

### Line-by-Line Explanation

```
Lines 1-9: The docstring (description at top)
```
This is just a comment explaining what the file does. The "differential steering" idea means: if something is on your left, speed up your right wheel (so you turn left away from it).

---

```python
import math
import numpy as np
```
- `math` — gives us cosine, pi, etc.
- `numpy (np)` — lets us work with lists of numbers (arrays) very fast. Think of it as a super-powered calculator for lists.

---

```python
class SpikingReflexLayer:
```
A **class** is like a blueprint. This blueprint creates the reflex brain. Every time you make a `SpikingReflexLayer()`, you get a fresh reflex system.

---

```python
def __init__(self, num_sensors=24, num_motor_neurons=2):
```
`__init__` runs when you first create the reflex. It sets everything up.
- `num_sensors=24` — CARL has 24 LiDAR beams (like a rotating laser ruler) pointing in all directions. Each one measures distance to the nearest obstacle.
- `num_motor_neurons=2` — two output neurons: one for "turn left", one for "turn right".

---

```python
self.V = np.zeros(self.num_motors)   # Voltage of each motor neuron (starts at 0)
self.V_th = 1.0                       # Threshold: if voltage reaches 1.0, the neuron FIRES
self.tau_m = 0.02                     # How quickly voltage leaks away (20 milliseconds)
self.dt = 0.033                       # How often we run this (every 33ms = 30 times/sec)
```

Think of `V` as the "charge" in each neuron. It builds up when obstacles are near, and fires when it hits `V_th = 1.0`.

---

```python
self.w = np.zeros((self.num_motors, self.num_sensors))
angles = np.linspace(-np.pi, np.pi, num_sensors, endpoint=False)
```
`self.w` is the **connection strength matrix** (a 2×24 grid of numbers). It decides how strongly each LiDAR beam affects each motor neuron.

`angles` creates 24 evenly-spaced angles around a full circle (like dividing a clock into 24 slices).

---

```python
for j in range(num_sensors):
    a = angles[j]
    if -np.pi/2 <= a <= np.pi/2:   # Front half of the circle
        if a < 0:                   # Front-RIGHT sector
            self.w[0, j] = 3.0 * (1.0 - abs(a) / (np.pi/2))  # excite "turn left"
        elif a > 0:                 # Front-LEFT sector
            self.w[1, j] = 3.0 * (1.0 - a / (np.pi/2))       # excite "turn right"
        else:                       # Directly ahead
            self.w[0, j] = 1.8;  self.w[1, j] = 2.2           # both fire → triggers reverse
```
This sets up **crossed steering**:
- Obstacle on your RIGHT → excite "turn LEFT" neuron (dodge left)
- Obstacle on your LEFT → excite "turn RIGHT" neuron (dodge right)
- Obstacle directly AHEAD → excite BOTH neurons → this triggers a backup sequence

---

```python
# R-STDP variables (learning variables)
self.trace_pre = np.zeros(self.num_sensors)   # Memory of recent LiDAR spikes
self.trace_post = np.zeros(self.num_motors)   # Memory of recent motor spikes
self.eligibility = np.zeros(...)              # "Candidate" for learning update
```
**R-STDP** (Reward-modulated Spike-Timing Dependent Plasticity) — a way for the reflex to LEARN over time. If an action worked well (reward happened), the connections that caused it get stronger.

---

```python
self.backup_timer = 0           # How many more ticks to keep backing up
self.backup_spin_dir = 1.0      # Which direction to spin during a backup
```
When CARL hits a wall head-on, it backs up for ~0.6 seconds, then spins toward the clearer direction.

---

### The `step()` Function — What Happens Every 33ms

```python
def step(self, sensor_dists, reservoir_bias, da, food_dist=99.0):
```
Called 30 times per second. Takes:
- `sensor_dists` — 24 distances from LiDAR beams
- `reservoir_bias` — signal from the reservoir brain (the bigger brain)
- `da` — dopamine level (reward signal for learning)
- `food_dist` — how far the food is (changes sensitivity thresholds)

---

```python
d_trigger = 0.45     # Start reacting when obstacle is within 45cm
collision_limit = 0.28   # Emergency backup if within 28cm
if food_dist < 1.0:
    d_trigger = 0.32   # When food is close, allow closer approach
```
When food is near, CARL is less shy about obstacles — it's willing to squeeze past to get the food.

---

```python
min_front_dist = np.min(sensor_dists[9:15])   # Check sensors 9 to 14 (front cone)
imminent_collision = min_front_dist < collision_limit
min_rear_dist = min(sensor_dists[0], sensor_dists[1], sensor_dists[23])  # rear sensors
imminent_rear_collision = min_rear_dist < 0.25
```
Looks at just the FRONT sensors for front danger, and REAR sensors for rear danger.

---

```python
if imminent_collision and self.backup_timer == 0:
    self.backup_timer = 20   # Back up for 20 ticks
    left_clear = np.mean(sensor_dists[6:12])    # Average clearance on left
    right_clear = np.mean(sensor_dists[12:18])  # Average clearance on right
    self.backup_spin_dir = 1.0 if left_clear > right_clear else -1.0
```
When CARL first detects a frontal collision: start a 20-tick (~0.6 sec) backup. Figure out which side has more space and remember to spin that way.

---

```python
for j in range(self.num_sensors):
    d = sensor_dists[j]
    if d < d_trigger:
        p = nu_max * (1.0 - d/d_trigger) * self.dt
        if np.random.rand() < min(1.0, p):
            spikes_pre[j] = 1.0   # This sensor "fires" a spike
```
**Probabilistic spiking:** Closer obstacles → higher probability of firing. This is how real sensory neurons work — they fire randomly but more often when the stimulus is stronger.

---

```python
current_inputs = np.dot(self.w, spikes_pre) + reservoir_bias
self.V = self.V * self.mem_decay + current_inputs
```
**LIF integration (the core neuron math):**
- `np.dot(self.w, spikes_pre)` — sum up all the weighted inputs from sensors that fired
- `self.V * self.mem_decay` — let the old voltage "leak" (decay) a little
- Add them together → new voltage

---

```python
for i in range(self.num_motors):
    if self.V[i] >= self.V_th:     # Has voltage crossed the threshold?
        spikes_post[i] = 1.0        # YES → fire!
        self.V[i] = 0.0             # Reset to 0 (like a real neuron after firing)
```
Each motor neuron fires when its voltage crosses 1.0, then resets.

---

```python
if spikes_post[0] > 0:   # "Turn Left" neuron fired
    self.reflex_outputs[0] -= reflex_strength   # Slow down left wheel
    self.reflex_outputs[1] += reflex_strength   # Speed up right wheel
if spikes_post[1] > 0:   # "Turn Right" neuron fired
    self.reflex_outputs[0] += reflex_strength   # Speed up left wheel
    self.reflex_outputs[1] -= reflex_strength   # Slow down right wheel
```
Differential drive: slow one wheel, speed up the other → robot turns.

---

```python
if self.backup_timer > 0:
    self.backup_timer -= 1
    if imminent_rear_collision:   # Blocked front AND back
        self.reflex_outputs[0] = 3.5 * self.backup_spin_dir   # Spin in place
        self.reflex_outputs[1] = -3.5 * self.backup_spin_dir
    else:                         # Only blocked front → back up + swing
        if self.backup_spin_dir > 0:
            self.reflex_outputs[0] = -4.5   # Back-left bias
            self.reflex_outputs[1] = -1.5
```
Emergency maneuvers: if stuck, spin in place. If just front-blocked, curve backwards toward the clearer side.

---

```python
da_error = da - 1.0         # If da > 1.0: reward happened (good). If < 1.0: bad.
self.w += self.eta_stdp * self.eligibility * da_error   # Update connection weights
self.w = np.clip(self.w, -3.0, 3.0)  # Keep weights in a safe range
```
**R-STDP learning:** If reward happened (dopamine > baseline), strengthen connections that contributed. If bad outcome, weaken them. Over time, the reflex gets better at choosing the right direction.

---

## 2. `carl_endocrine.py` — The Hormone System

**What it does in one sentence:** This is CARL's bloodstream — four "hormones" that change how CARL behaves, just like adrenaline, serotonin, and dopamine change how YOU feel and act.

**The Four Chemicals:**
| Code Name | Real Name | Effect |
|---|---|---|
| `DA` | Dopamine | Reward/motivation. Goes up when CARL finds food. |
| `NE` | Norepinephrine (Adrenaline) | Alert/stress. Goes up when CARL hits obstacles or danger. |
| `SHT` | Serotonin (5-HT) | Satiation/calm. Goes up after eating — CARL feels "full" and relaxes. |
| `ACh` | Acetylcholine | Attention. Goes up in novel environments — sharpens focus. |

---

```python
BASELINE_DA  = 1.0   # "Normal" resting dopamine level
BASELINE_NE  = 0.1   # "Normal" alertness (low)
BASELINE_SHT = 0.8   # "Normal" calmness (moderate)
BASELINE_ACH = 0.5   # "Normal" attention
```
These are the resting levels everything decays back to.

---

```python
def step(self, dt=0.033):
    self.DA  += -self.DECAY_DA * (self.DA - self.BASELINE_DA) * dt
    ...
```
**Exponential decay:** Every tick, each chemical moves toward its baseline. The further it is from baseline, the faster it returns. This is exactly how real hormones work in your body.

---

```python
def surge_da(self, amount=0.35):  # "I found food!"
    self.DA += amount

def surge_ne(self, amount=0.4):   # "Danger!"
    self.NE += amount

def surge_sht(self, amount=0.15): # "I ate!"
    self.SHT += amount

def surge_ach(self, amount=0.25): # "Something new!"
    self.ACh += amount
```
**Surge functions** — the main simulation calls these when events happen. Dopamine surges when CARL eats food; norepinephrine surges when hitting walls.

---

```python
def get_precision_weight(self):
    pi = self.PI_0 * (1.0 + GAMMA_ACH * self.ACh + GAMMA_NE * self.NE - GAMMA_SHT * self.SHT)
    return max(0.1, pi)
```
**Precision weight** — how much CARL trusts its sensors vs. its internal model.
- High ACh or NE → trusts sensors MORE (pays attention to the world)
- High Serotonin → trusts sensors LESS (relies on habits/predictions instead)

---

```python
def get_behavioral_mode(self, battery_level, food_visible):
    if food_visible:         return "EXPLOIT"   # Go get the food!
    elif battery_level < 0.15: return "SURVIVE" # Desperate search
    else:                    return "EXPLORE"   # Wander and map
```
**Three behavioral modes** — CARL automatically switches between them based on its hormones and battery level.

---

```python
def get_replay_blend_weight(self, battery_level, max_nav_value):
    hunger = get_hunger_drive(battery_level)
    signal_strength = clip(max_nav_value / 2.0, 0, 1)
    return clip(signal_strength * (0.3 + 0.7 * hunger), 0, 1)
```
How much CARL should follow its memory of where food was. A very hungry CARL follows memory urgently; a full CARL ignores memory and wanders freely.

---

## 3. `carl_reservoir.py` — The Main Brain (Liquid State Machine)

**What it does in one sentence:** This is CARL's cerebral cortex — a network of 500 artificial neurons that learns to translate sensory experience into movement commands.

**The Big Idea (Reservoir Computing):** Think of throwing a stone in a pond. The pond (reservoir) creates complex ripples — different stones create different ripple patterns. The brain just learns to "read" those ripples. The POND itself (W_res) never changes. Only how to READ the ripples (W_out) is learned.

---

```python
class LiquidStateReservoir:
    def __init__(self, N=500, M=25, K=3, ...):
```
- `N=500` — 500 neurons in the reservoir
- `M=25` — 25 sensory inputs (from LiDAR, position, hormones, etc.)
- `K=3` — 3 outputs (left wheel speed, right wheel speed, neck angle)

---

```python
self.W_in = rng.randn(N, M) * sigma_in     # Input connections: sensors → neurons (fixed forever)
W_raw = rng.randn(N, N)                     # Recurrent connections: neurons → neurons
mask = (rng.rand(N, N) < sparsity)         # Only 15% of connections exist (sparse)
W_raw *= mask
eigenvalues = np.linalg.eigvals(W_raw)      # Measure the network's "echo" scale
self.W_res = W_raw * (spectral_radius / current_radius)  # Scale to edge of chaos
```
**Spectral radius ≈ 1.0** means the network is at the "edge of chaos" — this is the sweet spot where it has maximum computational power (can remember the past without exploding into randomness).

---

```python
self.W_out = np.zeros((K, N))    # Output connections: neurons → motors (LEARNED over time)
self.P = np.eye(N) * self.rls_alpha  # Inverse correlation matrix (for RLS learning)
```
`W_out` starts at zero (CARL has no idea what to do). The RLS algorithm will train this over time. `W_in` and `W_res` are FIXED forever — only `W_out` changes.

---

### The `step()` Function — The Core Equation

```python
def step(self, u, noise_scale=0.02, dt=0.033):
    eta = np.random.randn(self.N) * self.sigma_noise_base * noise_scale  # Exploration noise
    leak = dt / self.tau
    drive = np.tanh(self.W_res @ self.x + self.W_in @ u + eta)  # Activation
    self.x = (1.0 - leak) * self.x + leak * drive               # State update
    y = self.W_out @ self.x                                       # Read out motor commands
    return np.clip(y, -2.0, 2.0)
```

**The equation in plain English:**
1. **Add noise** — small random exploration jitter (driven by norepinephrine)
2. **Mix old state + new input** — `W_res @ self.x` is "what are you already thinking?" and `W_in @ u` is "what do you sense right now?"
3. **Squash with tanh** — keeps values between -1 and +1 (prevents explosion)
4. **Leak** — the old state slowly fades, new input takes over
5. **Read out** — `W_out @ self.x` converts the reservoir's activity into motor commands

---

### The `rls_update()` Function — How CARL Learns

```python
def rls_update(self, y_target):
    phi = self.x                      # Current reservoir state
    y_pred = self.W_out @ phi         # What CARL predicted
    error = y_target - y_pred         # How wrong was it?
    P_phi = self.P @ phi
    gain = P_phi / (rls_lambda + phi @ P_phi)  # Learning rate (adaptive)
    self.P = (self.P - np.outer(gain, phi @ self.P)) / rls_lambda
    for k_idx in range(self.K):
        self.W_out[k_idx] += error[k_idx] * gain   # Update output weights
```
**Recursive Least Squares (RLS)** — an efficient way to learn online (one step at a time). Instead of looking at all past data, it keeps a running "memory" matrix `P` that tracks uncertainty. This is called "FORCE learning" — CARL forces itself toward the target output by updating `W_out`.

---

## 4. `carl_grid_cells.py` — The GPS System (Grid + Place Cells)

**What it does in one sentence:** This is CARL's internal map — how it knows WHERE it is in the maze, even with its eyes closed, using the same Nobel Prize-winning neurons found in all mammals.

---

### Part 1: `GridCellModule` — The Brain's GPS Ruler

```python
class GridCellModule:
    def __init__(self, scale, orientation_deg, n_cells=64, ...):
```
Each grid module creates a **hexagonal pattern** that tiles all of space. Like a triangular grid pattern printed on the floor. There are 3 modules with different scales (0.8m, 1.2m, 1.8m), like three overlapping rulers of different lengths. Combined, they uniquely identify any location (like a GPS coordinate).

---

```python
theta = math.radians(orientation_deg)
angles = [theta + i * math.pi / 3.0 for i in range(3)]  # Three directions at 60°
freq = 2.0 * math.pi / scale                              # How often the pattern repeats
self.K = np.array([[cos(a), sin(a)] for a in angles]) * freq  # Wave vectors
```
Three wave vectors at 60° apart create the hexagonal pattern. This is the **interference model** — like ripples from three pebbles creating a hexagonal pattern on water.

---

```python
def fire(self, x=None, y=None):
    pos = np.array([x, y]) if x is not None else self.pi_phase  # Use real or estimated position
    proj = self.K @ pos             # Project position onto wave vectors
    for c in range(self.n):
        phi = proj + self.phases[c] # Add each cell's unique phase offset
        rate = (cos(phi[0]) + cos(phi[1]) + cos(phi[2])) / 3.0  # Average of 3 waves
        self.activity[c] = max(0, (rate + 1.0) / 2.0 + noise)  # Shift to [0,1]
```
Computes firing rates for all 64 neurons in this module based on position. Each cell fires in a hexagonal pattern — at periodic "fields" across the whole arena.

---

### Part 2: `PlaceCellLayer` — The "I Am HERE" Neurons

```python
class PlaceCellLayer:
    def __init__(self, n_place=400, arena_bounds=(-5.0, 5.0, -5.0, 5.0), sigma=0.4):
        self.centres = np.column_stack([
            np.random.uniform(xmin, xmax, n_place),
            np.random.uniform(ymin, ymax, n_place),
        ])  # 400 cells scattered across the arena
```
400 place cells, each with a "preferred location" (its centre). When CARL is AT that location, that neuron fires strongly. It's like having 400 "I am here!" flags spread across the maze.

---

```python
def fire_from_position(self, x, y):
    pos = np.array([x, y])
    d2 = np.sum((self.centres - pos) ** 2, axis=1)   # Distance² to each cell's centre
    self.activity = np.exp(-d2 / (2 * self.sigma2))   # Gaussian: closer = stronger firing
```
Each place cell fires with a Gaussian curve — strongest at its centre, fading out within ~0.4m.

---

```python
def update_graph(self, old_cell, new_cell, tick):
    if old_cell != new_cell:
        self.adjacency[old_cell].add(new_cell)    # "I walked from A to B"
        self.adjacency[new_cell].add(old_cell)    # Bidirectional connection
    self.recency[new_cell] = tick                  # Remember when we last visited B
```
As CARL walks around, it builds a **topological map** — not a metric grid but a graph of "which places are connected to which." This is how the hippocampus actually works in real brains.

---

```python
def stamp_reward(self, cell_idx, amount=1.0):
    self.reward_values[cell_idx] += amount          # Mark "food was HERE"
    self.persistent_rewards[cell_idx] = max(...)    # Never fully forget this
    # Also stamp nearby cells within 1.5m:
    dists = sqrt(sum((self.centres - centre) ** 2))
    nearby_mask = dists < 1.5
    self.reward_values[nearby_mask] += amount * 0.5 * falloff
```
When CARL eats food, it **stamps** the current place cell with a reward beacon. Nearby cells also get a weaker stamp — creating a "reward zone" in the map.

---

```python
def diffuse_rewards(self, gamma=0.9, decay=0.99995, n_sweeps=5):
    self.reward_values *= decay    # Slowly forget rewards (over ~11 minutes)
    for sweep in range(5):         # 5 passes of value propagation
        for cell_idx in range(self.n):
            neighbors = self.adjacency[cell_idx]
            max_neighbor_val = max(values[n] for n in neighbors)
            new_values[cell_idx] = max(reward_here, gamma * max_neighbor_val)
```
**Hippocampal Replay** — like dreaming about your day but in reverse. Reward values propagate BACKWARDS through the graph (from food location, outward to neighbors, then their neighbors). After this runs, every place cell has a "navigation value" — higher = closer to remembered food.

---

### Part 3: `HippocampalNavigator` — Putting It All Together

```python
class HippocampalNavigator:
    def __init__(self):
        self.modules = [
            GridCellModule(scale=0.8,  orientation_deg=0,  n_cells=64),  # Fine-scale
            GridCellModule(scale=1.2,  orientation_deg=30, n_cells=64),  # Medium-scale
            GridCellModule(scale=1.8,  orientation_deg=60, n_cells=64),  # Coarse-scale
        ]
        self.places = PlaceCellLayer(n_place=400)
        self.W_gp = np.random.randn(400, 192) * 0.01   # Grid-to-place weights (learned)
```
Three grid modules + 400 place cells. The `W_gp` matrix learns to translate the grid cell patterns into place cell activation (how the hippocampus builds its map).

---

```python
def step(self, x_actual, y_actual, vx, vy, dt, learn=True):
    # 1. Theta oscillation (4-8 Hz brain rhythm)
    self.theta_phase = (self.theta_phase + 2*pi * 6.0 * dt) % (2*pi)
    theta_gate = 0.5 + 0.5 * cos(self.theta_phase)   # 0→1 oscillates at 6Hz

    # 2. Path integration (estimate position from velocity)
    for m in self.modules:
        m.integrate(vx, vy, dt)   # "I moved this far in this direction"

    # 3. Fire grid cells using actual GPS position (keeps them calibrated)
    grid_vec = concatenate([m.fire(x_actual, y_actual) for m in self.modules])

    # 4. Fire place cells
    place_act = self.places.fire_from_position(x_actual, y_actual)

    # 5. Hebbian learning (when theta is at peak):
    if learn and theta_gate > 0.8:
        outer = outer(place_act, grid_vec)         # "These place cells fired with these grid cells"
        self.W_gp += 0.002 * theta_gate * (outer - place_act[:, None] * self.W_gp)
```
**Theta oscillations** (4-8 Hz) gate learning — only update the grid-to-place weights during the "peak" of the theta rhythm. This is exactly how real hippocampal plasticity works (Buzsáki 2002).

---

## 5. `carl_stdp.py` — The Synapse Learning System

**What it does in one sentence:** This implements the exact biologically correct learning rule that real synapses use — "neurons that fire together, wire together" — but also the timing matters.

---

### Part 1: `STDPSynapse` — The Core Learning Rule

```python
# Pre before post → STRENGTHEN (LTP)
if np.any(post_spikes > 0):
    ltp = np.outer(self.A_pre, post_spikes) * A_PLUS
    self.E += ltp    # Add to eligibility trace

# Post before pre → WEAKEN (LTD)
if np.any(pre_spikes > 0):
    ltd = np.outer(pre_spikes, self.A_post) * (-A_MINUS)
    self.E += ltd    # Subtract from eligibility trace
```
- **LTP (Long-Term Potentiation):** If the input fires just BEFORE the output fires → the connection gets stronger. "The input CAUSED the output."
- **LTD (Long-Term Depression):** If the input fires AFTER the output already fired → the connection gets weaker. "The input was too late to matter."

---

```python
avg_reward = mean(self.reward_buf)    # Recent reward average
dW = LR * avg_reward * self.E        # Weight change = rate × reward × eligibility
self.W = clip(self.W + dW, W_MIN, W_MAX)
```
**3-factor rule:** Weight change = learning_rate × REWARD × eligibility_trace.

The reward is like a "confirmation signal" that arrives a bit later saying "yes, that was good." The eligibility trace holds a fading memory of what connections were recently active.

---

### Part 2: `STDPActionEvaluator` — Choosing Actions

```python
self.action_map = [-8., -5., -2., -1., 0., 1., 2., 5., 8.]  # 9 possible speeds
```
CARL can choose from 9 different wheel speeds. The STDP network learns which speeds work best in which situations.

---

```python
def update(self, xk, v_pop, uk, surprise, nm_DA):
    raw_reward = nm_DA - surprise * 0.5   # High DA + low surprise = reward
    reward = raw_reward - self.reward_baseline  # Subtract running average (RPE)
    pre_spikes  = pre_spikes * float(surprise > threshold)  # Only learn on surprising events
    post_spikes = post_spikes * float(surprise > threshold)
    self.synapse.step(pre_spikes, post_spikes, reward)
```
Only learns when something surprising happens (`surprise > 0.15`). Otherwise, it's just noise. This is exactly how dopamine neurons work — they fire on **prediction errors**, not expected events.

---

### Part 3: `QuantumDeliberator` — Making Decisions

```python
class QuantumDeliberator:
```
**What it does:** When multiple strategies are competing (reflex says go left, memory says go right), this resolves the conflict using quantum-inspired math.

```python
phases = costs_norm * math.pi        # Map costs to angles (0 to π)
amplitudes = np.exp(1j * phases)     # Complex number: direction + magnitude
total_amplitude = amplitudes.sum()   # Interference: good strategies amplify each other
coherent_probs = abs(amplitudes * conj(total_amplitude)).real  # Born rule probabilities
chosen_idx = np.random.choice(len(strategies), p=probs)        # Sample from distribution
```
Low-cost strategies get small phase angles (constructive interference → high probability). High-cost strategies get large phases (destructive interference → low probability). The result is a probabilistic choice that naturally explores alternatives.

---

## 6. `carl_physarum.py` — The Slime Mold Pathfinder

**What it does in one sentence:** CARL navigates using the same math as Physarum polycephalum (slime mold), which was proven in 2007 to naturally find the shortest path through any maze.

**The Big Idea:** Imagine a network of pipes connecting every cell in a 25×25 grid. Fluid flows through them. Thick pipes carry more fluid. Thin pipes shrink. Over time, the network finds the shortest path naturally (pipes carrying more flow get thicker, others disappear).

---

```python
self.D_h = np.ones((rows, cols-1))   # Horizontal pipe conductivities (25×24 grid)
self.D_v = np.ones((rows-1, cols))   # Vertical pipe conductivities (24×25 grid)
self.pressure = np.zeros(self.N)     # Pressure at each grid node
```

---

```python
def _build_laplacian(self):
    # Creates a sparse matrix representing all the pipe connections
    # Conductivity D between adjacent cells = how thick the pipe is
```
Builds a **Laplacian matrix** — a mathematical representation of the network. Solving it gives the pressure at every node.

---

```python
def _solve_pressure(self, src_idx, snk_idx):
    # Fix source pressure = 1.0 (like a pump)
    # Fix sink pressure = 0.0 (like a drain)
    # Solve for all intermediate pressures
    p = spsolve(L_mod.tocsr(), rhs)
```
Solves the physics: with a pump at the start (pressure=1) and a drain at the goal (pressure=0), what's the pressure at every intermediate point? The gradient naturally points from high to low pressure — from start toward goal.

---

```python
def _update_conductivities(self):
    Q_h = abs(self.D_h * (p_left - p_right))   # Flow = conductivity × pressure drop
    dD_h = (Q_h**MU - self.D_h) / TAU          # Change: high flow → thicker pipe
    self.D_h = clip(self.D_h + dD_h, D_MIN, D_MAX)
```
**Physarum dynamics:** Pipes carrying more flow (Q) grow thicker. Pipes with no flow shrink to minimum. Over time, only the shortest path remains.

---

```python
def get_heading(self, xw, yw, goal_xw, goal_yw, ...):
    cur = to_grid(xw, yw)   # Convert world position to grid cell
    best = self.best_move(cur, cur, snk)  # Which adjacent cell has lowest pressure?
    bx, by = grid_to_world(best)          # Convert back to world coordinates
    return atan2(by - yw, bx - xw)       # Return heading angle toward that cell
```
The final output: given CARL's current position and the goal, return a heading angle to move toward the goal while avoiding obstacles.

---

## 7. `carl_omega_extensions.py` — Mirror Neurons & Stress Prediction

---

### `MirrorNeuronSystem` — Learning from Others' Mistakes

**Based on:** Rizzolatti 1996 — neurons that fire both when you act AND when you watch others act. Your brain simulates what you observe.

```python
def learn_from_death(self, survivor_brain, dead_brain, T_ltm, danger_update_fn, D):
    buf = dead_brain.get('buf', [])  # Get the dead robot's last 15 actions
    for (xk_m, uk_m, xn_m, _) in buf[-15:]:
        xs_sim = Ad @ xk_m + Bd * uk_m   # Simulate: "if I took that action, what would happen?"
        sim_surprise = norm(xs_sim - xn_m) # How different was the actual outcome?
        if sim_surprise > 0.25:
            D = danger_update_fn(D, ...)   # Mark that location as dangerous
```
When Robot B dies, Robot A "replays" B's last 15 moves through its own model. Places where A's prediction was surprised → A marks those locations as dangerous. **Empathy through simulation.**

---

### `PredictiveAllostasis` — Predicting Future Stress

**Based on:** McEwen 1998 (allostasis = maintaining stability through change), Sterling 2012.

```python
def predict_future_load(self, x, T_ltm, D, danger_at_fn):
    xs = x.copy()
    for h in range(60):           # Simulate 60 steps into the future
        xs = Ad @ xs + Bd * 0.0  # "What if I just coast? Where do I end up?"
        d = danger_at_fn(D, xs[2], xs[3])  # How much danger is at that future position?
        future_load += d * (0.97 ** h)     # Near future counts more than distant future
    self.predicted_load = future_load / 60
```
CARL simulates coasting forward 60 steps and measures how much danger it'll accumulate. This becomes an extra cost added to risky actions — CARL preemptively avoids paths that lead into high-danger zones.

---

### `ThetaGate` — The Learning Rhythm

```python
class ThetaGate:
    def step(self, dt):
        self.phase = (self.phase + 2*pi * self.freq * dt) % (2*pi)  # 6Hz oscillation

    @property
    def gate(self):
        return 0.5 + 0.5 * cos(self.phase)  # 0 at trough, 1 at peak

    def learning_lambda(self, base=0.990):
        return clip(base - self.gate * 0.012, 0.970, 0.999)  # More learning at peak
```
The theta rhythm (4-8 Hz) gates plasticity. At peak: more learning happens. At trough: consolidation. This oscillation is found in every mammalian hippocampus.

---

## 8. `astar.py` — A* Pathfinding

**What it does in one sentence:** Given CARL's danger map of the maze, find the safest route from current position to goal.

**A* algorithm:** A well-known graph search algorithm. It explores paths in order of (cost so far + estimated cost to goal), so it finds the cheapest path efficiently.

```python
def astar_path(CM, start_pos, goal_pos):
    grid = (CM[:, :, 0] > 0.85).astype(int)  # Cells with danger > 85% = wall
    open_set = []
    heapq.heappush(open_set, (0, sx, sy))      # Start with the start cell
    g_score[(sx, sy)] = 0                      # Cost to reach start = 0
    f_score[(sx, sy)] = abs(sx-gx) + abs(sy-gy)  # Estimated total cost (Manhattan distance)
```

```python
    while open_set:
        _, cx, cy = heapq.heappop(open_set)    # Always expand the cell with lowest f_score
        if cx == gx and cy == gy:              # Reached goal → reconstruct and return path
            ...
        for dx, dy in 8_directions:            # Check all 8 neighbors
            danger_cost = CM[nx, ny, 0] * 50.0 # High-danger cells cost a lot to pass through
            step_cost = 1.414 if diagonal else 1.0  # Diagonal steps cost more (Pythagorean)
            tentative_g = g_score[(cx,cy)] + step_cost + danger_cost
            if tentative_g < g_score[(nx,ny)]:  # Better path found → update
                g_score[(nx,ny)] = tentative_g
                heapq.heappush(open_set, (f, nx, ny))
```
The danger cost (up to 50×) makes dangerous cells very expensive to traverse — CARL will walk farther to avoid them. Walls (>0.85 danger) are impassable.

---

## 9. `show_carl.py` — 3D Viewer Launcher

**What it does:** Opens a 3D interactive window showing CARL and the arena.

```python
def show_carl():
    xml_path = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")  # Find the arena XML file
    model = mujoco.MjModel.from_xml_path(xml_path)  # Load the physics model
    data = mujoco.MjData(model)                     # Create simulation data

    q_addr = int(model.joint("spatial_identity").qposadr[0])  # Find CARL's position joint
    data.qpos[q_addr : q_addr+3] = [0.0, 0.0, 0.05]          # Place CARL at center

    # Place visible objects near CARL so you can see them:
    model.geom_pos[model.geom("food").id] = [0.5, 0.5, 0.12]
    model.geom_pos[model.geom("obstacle").id] = [-0.8, 0.6, 0.45]

    mujoco.mj_forward(model, data)    # Compute initial physics state
    mujoco.viewer.launch(model, data) # Open the 3D viewer window
```

---

## 10. `plot_telemetry.py` — Proof Generator

**What it does:** Reads the recorded data from a simulation run and creates a 4-panel scientific proof chart.

```python
fig = plt.figure(figsize=(16, 10))

# Panel 1: 2D Trajectory — where did CARL actually go?
ax1.plot(data['x'], data['y'], ...)   # Draw CARL's path through the maze

# Panel 2: Hormone Levels — how did dopamine/serotonin change?
ax2.plot(time_s, data['DA'], label='Dopamine (DA)')
ax2.plot(time_s, data['NE'], label='Norepinephrine (NE)')

# Panel 3: Brain vs Reflex — who was in charge?
cog_total = abs(data['cognitive_L']) + abs(data['cognitive_R'])  # Reservoir brain output
rfx_total = abs(data['reflex_L']) + abs(data['reflex_R'])        # Reflex output
# Shows: as CARL learns, the brain gradually takes over from the reflex

# Panel 4: Metabolic motivation — battery + food + hunger drive
battery = data['battery']
hunger = 1.0 + 2.0 * (1.0 - battery)   # Hungrier = lower battery
satiation = 1.0 / maximum(0.5, da)     # Full = high dopamine
motivation = hunger * satiation         # Overall drive to find food
```

---

## 11. `live_plotter.py` — Real-Time Dashboard

**What it does:** The same 4 charts as `plot_telemetry.py` but LIVE — refreshes every 2 seconds while CARL is running.

```python
ani = FuncAnimation(fig, update, interval=2000, cache_frame_data=False)
```
`FuncAnimation` calls the `update()` function every 2000ms (2 seconds). Each call re-reads the CSV file and redraws all charts.

```python
def read_telemetry():
    with open(TELEMETRY_PATH, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)    # First row = column names
        for row in reader:        # All other rows = data
            for h, val in zip(headers, row):
                data[h].append(float(val))  # Parse each value as a number
```
Reads the CSV file from scratch every 2 seconds. This ensures the latest data is always displayed.

---

# 🌍 WORLD FILES
> These files describe the physical body and environment.

---

## 12. `world/carl_mujoco.xml` — The Arena Blueprint

**What it does:** This is the "house plan" of CARL's world — written in XML (a structured text format). MuJoCo (the physics simulator) reads this to build the 3D world.

### Key Sections:

**Physics Settings:**
```xml
<option gravity="0 0 -9.81" timestep="0.004166667" iterations="50" solver="Newton"/>
```
- `gravity="0 0 -9.81"` — Standard Earth gravity (9.81 m/s² downward)
- `timestep="0.004166667"` — Physics updates 240 times per second (ultra-precise)
- `solver="Newton"` — Uses Newton's method to solve contact forces

**Materials (Visual Appearance):**
```xml
<material name="floor_mat" texture="grid" rgba="0.05 0.06 0.12 1"/>  <!-- Dark blue floor -->
<material name="wall_glow"  rgba="0.15 0.45 1.0 1" emission="0.6"/>  <!-- Glowing blue walls -->
<material name="eye_mat"    rgba="0.0 0.9 1.0 1" emission="0.5"/>    <!-- Cyan glowing eyes -->
```

**Maze Walls:**
```xml
<geom name="w_s" type="box" size="3.64 0.04 0.175" pos="3.6 0.0 0.175" material="wall_mat"/>
```
South wall: a box 7.28m wide, 8cm thick, 35cm tall.

**Robot Body — Robot A:**
```xml
<body name="base_A" pos="0.40 0.40 0.10">    <!-- Start at position (0.4, 0.4) -->
  <freejoint name="fj_A"/>                     <!-- Can move freely in 3D -->
  <geom name="chassis_A" type="box" size="0.06 0.08 0.02"/>  <!-- 12×16cm chassis -->
  
  <body name="lwheel_A" pos="0 0.095 0">      <!-- Left wheel, 9.5cm from centre -->
    <joint name="lw_A" type="hinge" axis="0 1 0"/>  <!-- Spins around Y-axis -->
    <geom name="lw_A_tire" type="cylinder" size="0.07 0.0125"/>  <!-- 7cm radius wheel -->
  </body>
  
  <body name="neck_A">
    <joint name="neck_A" type="hinge" range="-0.3 0.3"/>  <!-- Can tilt ±17 degrees -->
    <body name="head_A">
      <camera name="eye_cam_A" fovy="65"/>    <!-- Camera with 65° field of view -->
    </body>
  </body>
</body>
```

**Actuators (What CARL Can Control):**
```xml
<motor name="lw_A_m" joint="lw_A" ctrlrange="-12 12"/>   <!-- Left wheel: -12 to +12 Nm -->
<motor name="rw_A_m" joint="rw_A" ctrlrange="-12 12"/>   <!-- Right wheel: -12 to +12 Nm -->
<position name="nk_A_p" joint="neck_A" kp="12" ctrlrange="-0.3 0.3"/>  <!-- Neck angle -->
```

---

## 13. `world/carl.urdf` — Alternative Robot Description

**What it does:** URDF (Unified Robot Description Format) is another way to describe robot bodies, used by ROS (Robot Operating System). This is the same CARL robot as the XML but in URDF format, used for different tools.

Key parts:
- `base_link` — the main chassis (12×16cm box, dark graphite)
- `left_wheel` / `right_wheel` — 7cm radius cylinders, continuous rotation joints
- `neck_link` — 40cm tall thin cylinder (8mm radius), revolute joint ±17°
- `head_link` — the heavy "brain box" (1.5kg!) on top of the neck — makes CARL top-heavy and unstable (realistic!)

---

## 14. `world/carl_mj_physics.py` — The Physics Interface Layer

**What it does in one sentence:** All the low-level functions for communicating with MuJoCo — moving robots, reading sensors, firing LiDAR beams.

```python
BCFG = [
    dict(name='A', q0=0, v0=0, nq=9, nv=8, cl=0, cr=1, cn=2),   # Robot A config
    dict(name='B', q0=10, v0=9, nq=19, nv=17, cl=3, cr=4, cn=5), # Robot B config
]
```
`q0` = where in the position array this robot's data starts. `cl/cr/cn` = which control inputs to use for left wheel/right wheel/neck.

---

```python
def get_lidar(cfg):
    """Cast 5 laser rays forward, return distances"""
    angles = [-0.785, -0.392, 0.0, 0.392, 0.785]  # -45°, -22.5°, 0°, +22.5°, +45°
    for a in angles:
        vec = [cos(yaw+a), sin(yaw+a), 0]            # Ray direction
        dist = mujoco.mj_ray(model, data, pnt, vec, None, 1, -1, geomid)  # Raycast!
```
Fires 5 rays in a fan. `mj_ray` is MuJoCo's built-in raycast function — it returns the distance to the first object hit.

---

```python
def apply_torque(cfg, u_fwd, u_steer=0.0):
    fwd = clip(u_fwd, -8, 8)
    steer = clip(u_steer, -3, 3)
    data.ctrl[cfg['cl']] = fwd + steer   # Left wheel = forward + steer (differential drive)
    data.ctrl[cfg['cr']] = fwd - steer   # Right wheel = forward - steer
```
**Differential drive steering:** Add steer to one wheel, subtract from the other. This makes the robot turn without a dedicated steering mechanism.

---

# 🧪 VISION PIPELINE FILES

---

## 15. `brain/collect_vision_dataset.py` — Building Training Data

**What it does:** Automatically generates thousands of training images for CARL's eye by running the simulator, placing objects in random positions, and capturing what CARL's camera sees.

```python
categories = [
    ("FOOD", "food", 0),      # Class 0 = Food
    ("OBSTACLE", "obstacle", 1),  # Class 1 = Obstacle
    ("PREDATOR", "predator", 2),  # Class 2 = Predator
    ("BACKGROUND", None, 3)       # Class 3 = Nothing
]
samples_per_cat = 300   # 300 images per category = 1200 total
```

For each image:
1. Place CARL at a random position and angle
2. Place the target object somewhere in front of CARL
3. Render the camera view (160×120 pixels)
4. Calculate the bounding box of the object in the image
5. Save image + label file

```python
x_center = ((u_min + u_max) / 2.0) / W    # Bounding box center X (normalized 0-1)
y_center = ((v_min + v_max) / 2.0) / H    # Bounding box center Y (normalized 0-1)
bbox_width = (u_max - u_min) / W           # Width (normalized 0-1)
lf.write(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")
```
Label format: `class_id center_x center_y width height` — this is the YOLO format, standard for object detection.

---

## 16. `brain/train_vision.py` — Teaching CARL to See

**What it does:** Trains a convolutional neural network to look at CARL's camera and say "that's food" or "that's a predator."

```python
class CarlVisionNet(nn.Module):
    def __init__(self):
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),  # 16 filters, detect edges/colors
            nn.BatchNorm2d(16),                            # Normalize (stable training)
            nn.ReLU(),                                     # Non-linearity
            nn.MaxPool2d(2, 2),                            # Shrink image 2× (60×80)

            nn.Conv2d(16, 32, kernel_size=3, padding=1),  # 32 filters, detect shapes
            nn.MaxPool2d(2, 2),                            # Shrink again (30×40)

            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # 64 filters, detect objects
            nn.MaxPool2d(2, 2),                            # Shrink again (15×20)
        )
        self.classifier = nn.Sequential(
            nn.Linear(19200, 128),  # Flatten 64×15×20=19200 → 128 features
            nn.ReLU(),
            nn.Dropout(0.2),        # Randomly drop 20% to prevent overfitting
            nn.Linear(128, 4)       # 4 outputs: Food / Obstacle / Predator / Background
        )
        self.bbox_regressor = nn.Sequential(
            nn.Linear(19200, 128),
            nn.ReLU(),
            nn.Linear(128, 4),      # 4 outputs: x_center, y_center, width, height
            nn.Sigmoid()            # Keep outputs in [0, 1] range
        )
```

**Two heads (dual output):**
- **Classifier** — "What is it?" (one of 4 categories)
- **Bbox regressor** — "Where is it in the image?" (bounding box coordinates)

```python
loss_cls = cls_criterion(cls_out, classes)   # Cross-entropy: classify correctly
active_mask = (classes != 3).float()         # Only compute bbox loss when object exists
loss_bbox = bbox_criterion(bbox_out * active_mask, bboxes * active_mask)
total_loss = loss_cls + 2.0 * loss_bbox     # Bbox loss counts double (harder task)
```
Background images (class 3) don't get bounding box loss — there's no object to localize.

---

# 🤖 GENESIS / CARL SCOUT FILES

---

## 17. `GENESIS/carl_scout/genesis_run.py` — Next-Gen Robot Simulation

**What it does:** Runs CARL inside the Genesis physics engine (newer, faster alternative to MuJoCo) with a full bimanual arm robot body.

```python
import genesis as gs
gs.init(backend=gs.cuda)    # Use GPU physics (much faster)
scene = gs.Scene(show_viewer=True)
plane = scene.add_entity(gs.morphs.Plane())  # Floor
robot = scene.add_entity(gs.morphs.MJCF(file="genesis_carl_body.xml"))  # Load robot
```

---

## 18. `GENESIS/carl_scout/test_yolo.py` — Vision System Test

**What it does:** Tests YOLO (You Only Look Once — a real-time object detection AI) on CARL's camera feed.

```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")   # Load a pretrained YOLOv8 nano model (fast + small)
results = model(frame)       # Run detection on camera frame
for box in results[0].boxes:
    cls_id = int(box.cls[0])
    conf = float(box.conf[0])   # Confidence: how sure is the model?
    x1, y1, x2, y2 = box.xyxy[0].tolist()  # Bounding box pixel coordinates
```

---

# 🏗️ XML ROBOT BODY FILES

---

## 19. `world/vessel_kinetic.xml` — The Full Simulation Arena

Similar to `carl_mujoco.xml` but larger and more complex — includes the food sphere, obstacle cube, predator, and CARL's full articulated body with 24-ray LiDAR.

Key additions over the simple XML:
- `food` geom: a glowing sphere (the reward target)
- `obstacle` geom: a cube CARL avoids
- `predator` geom: a threat that causes CARL to flee
- `spatial_identity` joint: CARL's position/orientation in the world

---

## 20. `GENESIS/carl_scout/genesis_carl_body.xml` / `carl_body.xml` — Advanced Robot Body

The Genesis scout robot is more complex — a **primate-like robot** with:
- A differential-drive base (wheels)
- A torso
- Two arms with shoulders, elbows, and wrists
- A head with camera
- Used for manipulation tasks (reaching, grasping)

---

# 🧪 TEST FILES

---

## 21. `tests/test_endocrine.py` — Testing the Hormone System

Automated tests that verify the endocrine system behaves correctly:
- Does dopamine decay back to baseline after a surge?
- Does serotonin suppress precision weight correctly?
- Do behavioral modes switch at the right thresholds?

---

## 22. `tests/test_grid_cells.py` — Testing Navigation

Verifies that grid cells and place cells work correctly:
- Do grid cells fire in hexagonal patterns?
- Does path integration accumulate position correctly from velocity?
- Does reward diffusion propagate through the graph?

---

## 23. `tests/test_reservoir.py` — Testing the Reservoir Brain

Tests that the liquid state machine:
- Initializes with correct spectral radius
- State stays bounded (no explosion)
- RLS updates actually reduce prediction error over time

---

# 📊 HOW IT ALL FITS TOGETHER

Here's the flow every 33ms when CARL is running:

```
1. MuJoCo Physics → position, velocity, LiDAR distances
         ↓
2. EndocrineSystem.step() → DA, NE, SHT, ACh levels update
         ↓
3. HippocampalNavigator.step() → grid cells fire, place cells fire, graph updated
         ↓
4. LiquidStateReservoir.step() → 500 neurons compute motor commands
         ↓
5. SpikingReflexLayer.step() → emergency obstacle avoidance
         ↓
6. Commands blended: reservoir_brain + reflex + physarum_navigation
         ↓
7. apply_torque() → wheels spin
         ↓
8. Data logged to CSV → live_plotter shows the dashboard
```

---

## 🎓 Key Scientific Concepts Used

| Concept | What It Models | File |
|---|---|---|
| Leaky Integrate-and-Fire (LIF) | Real neuron firing | `carl_reflex.py` |
| Reservoir Computing / LSM | Cerebral cortex | `carl_reservoir.py` |
| Recursive Least Squares (RLS) | Synaptic plasticity | `carl_reservoir.py` |
| Grid Cells (Nobel Prize 2014) | Spatial GPS | `carl_grid_cells.py` |
| Place Cells (Nobel Prize 2014) | "I am here" neurons | `carl_grid_cells.py` |
| Hippocampal Replay | Memory consolidation | `carl_grid_cells.py` |
| R-STDP | 3-factor learning rule | `carl_stdp.py`, `carl_reflex.py` |
| Dopamine / Reward Prediction Error | Motivation | `carl_endocrine.py` |
| Theta Oscillations (4-8 Hz) | Plasticity gating | `carl_omega_extensions.py` |
| Mirror Neurons | Learning from observation | `carl_omega_extensions.py` |
| Allostasis | Stress prediction | `carl_omega_extensions.py` |
| Physarum Polycephalum | Path optimization | `carl_physarum.py` |
| A* Pathfinding | Shortest safe route | `astar.py` |
| Convolutional Neural Networks | Computer vision | `train_vision.py` |
| YOLO Object Detection | Real-time vision | `test_yolo.py` |
