# 🔬 DEEP DIVE #11 — `carl_omega_extensions.py`, `astar.py`, `live_plotter.py`, `carl_mj_physics.py`
> *126 + 73 + 133 + 211 lines. Every line, every number, every reason.*

---

# PART A — `carl_omega_extensions.py` (126 lines)
> *Three neuroscience innovations: Mirror neurons, predictive allostasis, theta oscillations.*

---

## Lines 1–5: Imports

```python
import math, numpy as np
from collections import deque
```

**`from collections import deque`**: Doubly-ended queue. All three classes use `deque(maxlen=N)` as circular buffers — old values auto-drop when new ones are added. More memory-efficient than `list.append()` + `list[:-N]`.

---

## Lines 9–53: `MirrorNeuronSystem` — Cross-Body Learning

### The Biology

In 1996, Giacomo Rizzolatti discovered **mirror neurons** in macaque monkeys: neurons that fire BOTH when the monkey performs an action AND when it WATCHES another monkey perform the same action. This led to theories of empathy, imitation, and social learning.

In CARL's multi-robot scenario: when Robot B dies, Robot A (the survivor) uses mirror neurons to simulate "what if that had been ME?" If the simulation predicts the same dangerous outcome, A marks those states as dangerous — learning from B's death without experiencing it.

### `learn_from_death()` — Lines 19–47

```python
def learn_from_death(self, survivor_brain, dead_brain, T_ltm, danger_update_fn, D):
    buf = dead_brain.get('buf', [])
    if not buf:
        return D
```

`buf`: The dead robot's **experience buffer** — its last N (state, action, next_state, outcome) transitions.

`dead_brain.get('buf', [])`: Safely retrieves the buffer. If the key 'buf' doesn't exist (robot died before logging), returns empty list.

`if not buf: return D`: If no experience data available, can't learn anything. Return D (danger map) unchanged.

---

```python
    alpha = max(0.01, 1.0 - float(np.trace(survivor_brain['P_wm'])) / (500*(self.sdim+1)))
    T_use = alpha * survivor_brain['T_wm'] + (1-alpha) * T_ltm
```

**World model blending:**

`survivor_brain['P_wm']`: The covariance matrix P from the survivor's RLS-trained world model. Large trace = high uncertainty.

`np.trace(P_wm)`: Sum of diagonal elements = total variance across all model dimensions.

`alpha = 1 - trace / (500 × 6)`: When trace is small (confident model), `alpha` is near 1 (use survivor's own model). When trace is large (uncertain model), `alpha` is near 0 (fallback to long-term memory `T_ltm`).

`T_use = alpha × T_wm + (1-alpha) × T_ltm`: Weighted interpolation between:
- `T_wm`: Survivor's recent world model (accurate but possibly overfitted)
- `T_ltm`: Long-term stable world model (general but possibly stale)

**Why blend?** If the survivor is in a novel environment (high uncertainty), its recent model is unreliable. Blending toward the long-term model makes the simulation more conservative and stable.

---

```python
    Ad = T_use[:self.sdim, :].T   # Transition matrix A (state × state)
    Bd = T_use[self.sdim, :]      # Input vector B (state per unit control)
```

**World model structure:** The combined model matrix `T_use` has shape `(sdim+1, sdim) = (6, 5)`.

The world model says: `x_next = A × x_current + B × u_current`

- `A = T_use[:5, :].T` — shape (5, 5): How the state evolves on its own
- `B = T_use[5, :]` — shape (5,): How control input u affects each state dimension

`.T` (transpose): Because `T_use` stores coefficients row-by-row in a format different from the standard matrix equation. Transposing aligns dimensions correctly.

---

```python
    for (xk_m, uk_m, xn_m, _) in buf[-15:]:
        xs_sim = Ad @ xk_m + Bd * uk_m
        sim_surprise = float(np.linalg.norm(xs_sim - xn_m))
```

**Simulate dead robot's last 15 transitions through survivor's world model:**

`buf[-15:]`: Python slice — last 15 elements of the buffer.

`xs_sim = A @ x + B × u`: Predicted next state according to survivor's model.

`sim_surprise = ||xs_sim - xn_m||`: Euclidean distance between:
- What CARL's model PREDICTED would happen (`xs_sim`)
- What ACTUALLY happened to the dead robot (`xn_m`)

Large `sim_surprise` → "I would have been surprised here too" → this state was genuinely unexpected and dangerous.

---

```python
        if sim_surprise > 0.25:
            D = danger_update_fn(D, xn_m[2], xn_m[3],
                                 sim_surprise * 0.55, rate=0.18)
```

**Why threshold 0.25?** `sim_surprise` is a Euclidean norm over 5 state dimensions. Typical "normal" model error for a well-trained system ≈ 0.1-0.2. Above 0.25 = genuinely unexpected = worth marking as dangerous.

**`danger_update_fn(D, x, y, amount, rate)`**: A callback function that marks the 2D danger map at position `(xn_m[2], xn_m[3])` (position components of state). The mark strength = `sim_surprise × 0.55`.

**Why `× 0.55`?** Scale factor < 1 because we're making an INDIRECT inference ("B was surprised there, so I might be too") — not a direct experience. We're 55% as confident as if we had experienced it ourselves.

**`rate=0.18`**: How fast this danger mark decays over time. Lower rate = mark persists longer.

---

```python
    avg = total_sim_surprise / max(1, len(buf[-15:]))
    self.sim_surprise_history.append(avg)
    return D
```

`max(1, len(buf[-15:]))`: Prevents division by zero if buf has < 15 elements.

Returns the updated danger map D (not a copy — caller receives the modified map).

---

### `empathy_signal()` — Lines 49–53

```python
def empathy_signal(self):
    return float(np.clip(np.mean(self.sim_surprise_history) * 2.0, 0., 1.))
```

**What it measures:** "How much did the survivor's simulation surprise it?" = "How much did the survivor 'feel' its sibling's death?"

`× 2.0`: Scales the average surprise (typically 0.1-0.5) to a [0, 1] range. Average surprise of 0.5 → empathy = 1.0 (maximum).

**How it's used:** When empathy is high, survivor CARL:
- Boosts NE (stress response to witnessing a death)
- Updates its goal-setting with the new danger map
- May temporarily avoid the area where the sibling died

---

## Lines 60–98: `PredictiveAllostasis` — Forward-Simulated Stress

### The Biology

Classic **homeostasis** (Cannon 1929): React to current stress — "I'm cold, shiver now."  
**Allostasis** (Sterling & Eyer 1988): Predict future stress — "It's going to get cold tonight, start gathering firewood NOW."

`PredictiveAllostasis` simulates CARL "coasting" forward (no control input) for 60 steps and accumulating predicted danger. If the predicted path runs through dangerous territory, CARL adjusts its current trajectory — before hitting the danger.

### `predict_future_load()` — Lines 68–82

```python
def predict_future_load(self, x, T_ltm, D, danger_at_fn):
    xs = x.copy()
    future_load = 0.0
    for h in range(self.horizon):   # horizon = 60 steps
        xs = Ad @ xs + Bd * 0.0    # coast: u=0
        d  = danger_at_fn(D, xs[2], xs[3])
        future_load += d * (0.97 ** h)
    self.predicted_load = float(future_load / self.horizon)
    return self.predicted_load
```

**`Bd * 0.0`**: Zero control input = "coasting." Simulates what happens if CARL does NOTHING for the next 60 steps. This is the "default future."

**`d × (0.97^h)`**: Discounted future danger. Each future step is worth 3% less than the previous:
- h=0 (now): discount = 1.0 (full weight)
- h=10: discount = 0.97^10 = 0.74
- h=30: discount = 0.97^30 = 0.40
- h=60: discount = 0.97^60 = 0.16

Far future danger matters less than near future.

**`/ self.horizon`**: Average over all 60 simulated steps.

---

### `anticipatory_avoidance_cost()` — Lines 90–95

```python
def anticipatory_avoidance_cost(self):
    return float(np.clip(self.predicted_load * 3.0, 0., 2.0))
```

Returns an extra cost (0 to 2.0) added to actions heading toward high-load futures. In `carl_simulation.py`'s action cost computation:
```
total_cost = base_cost + anticipatory_avoidance_cost()
```
When `predicted_load = 0.4`, anticipatory cost = `0.4 × 3 = 1.2` — a significant penalty that biases CARL away from the forecasted dangerous area even before reaching it.

**`× 3.0`**: Amplification factor — makes the allostatic signal 3× stronger than the raw danger prediction. Without this, the weak prediction signal (typical 0-0.3) would be overwhelmed by direct sensor readings.

**`clip(0, 2.0)`**: Caps at 2.0 — prevents the allostatic system from completely dominating all other behavioral drives.

---

## Lines 105–125: `ThetaGate` — Hippocampal Learning Oscillation

### The Biology

György Buzsáki (2002) showed that the **theta rhythm** (4-8 Hz oscillation) in the hippocampus gates when learning occurs:
- **Theta peak** (high gate): Encoding phase — new memories are consolidated
- **Theta trough** (low gate): Retrieval phase — stored memories are replayed

`ThetaGate` models this as a cosine oscillator that controls the **forgetting factor λ** of RLS learning and the **exploration boost** in navigation.

### `step()` — Lines 110–111

```python
def step(self, dt):
    self.phase = (self.phase + 2*math.pi * self.freq * dt) % (2*math.pi)
```

**Phase advance:** Increments the oscillator phase by `2π × freq × dt` each tick.

For `freq = 6.0 Hz` and `dt = 0.033s`:  
Phase advance per tick = `2π × 6 × 0.033 = 1.244 rad/tick`  
Period = `2π / 1.244 = 5.05 ticks = 167 ms` ≈ 6 Hz. ✓

**`% (2π)`**: Wraps phase to [0, 2π]. After one complete cycle, phase resets to 0.

### `gate` property — Lines 113–116

```python
@property
def gate(self):
    return 0.5 + 0.5 * math.cos(self.phase)
```

**Cosine gate:** Maps phase [0, 2π] → gate [0, 1].

- Phase = 0 (cycle start): `0.5 + 0.5×cos(0) = 0.5 + 0.5 = 1.0` (PEAK — maximum learning)
- Phase = π/2: `0.5 + 0.5×cos(π/2) = 0.5 + 0 = 0.5` (mid-phase)
- Phase = π: `0.5 + 0.5×cos(π) = 0.5 - 0.5 = 0.0` (TROUGH — no learning, replay)

### `learning_lambda()` — Lines 118–120

```python
def learning_lambda(self, base=0.990):
    return float(np.clip(base - self.gate * 0.012, 0.970, 0.999))
```

**RLS forgetting factor modulated by theta:**

- At peak (gate=1.0): `λ = 0.990 - 1.0 × 0.012 = 0.978` — FAST learning (lower λ = more responsive)
- At trough (gate=0.0): `λ = 0.990 - 0 × 0.012 = 0.990` — SLOW learning (higher λ = more stable)

**Why modulate learning rate with theta?** At theta peak (encoding phase), the reservoir should learn QUICKLY from new experiences. At theta trough (replay phase), it should stabilize — preserve what was just learned rather than overwriting it.

The range [0.978, 0.990] is narrow but meaningful for RLS — a 1.2% change in λ changes the effective memory window from 1/(1-0.978)=45 ticks to 1/(1-0.990)=100 ticks.

---

# PART B — `astar.py` (73 lines)

---

## The A* Algorithm (What, Why, How)

**What is A*?** A graph search algorithm that finds the SHORTEST PATH from a start to a goal on a weighted grid. It's guaranteed to find the optimal path when costs are non-negative.

**Why A* over Dijkstra?** Dijkstra's algorithm explores in all directions equally — wastes time going away from goal. A* uses a **heuristic** (estimated remaining distance) to preferentially explore toward the goal. Much faster for point-to-point pathfinding.

**Why A* over direct gradient following?** The place cell nav_values are a diffusion gradient — not a proper path. They might route CARL into corners or dead ends in tight mazes. A* uses the EXPLICIT OBSTACLE MAP (danger map) to find a guaranteed collision-free path.

---

## Lines 5–10: Map Constants

```python
MAP_RES = 25
MAP_XMIN = -0.5
MAP_XMAX = 7.7
MAP_YMIN = -0.5
MAP_YMAX = 6.5
```

**Why 25×25?** Resolution of 25 cells over 8.2m wide × 7.0m tall = one cell per 0.33m.

Wall thickness ≈ 8cm. Cells are 33cm — a wall occupies ~0.25 cells. With 25×25, walls are still detectable (a wall cell has danger > 0.85).

**Why -0.5 to 7.7 (not 0 to 7.2)?** The maze spans 7.2m wide, starting at 0. The -0.5 and +0.5 margins prevent boundary artifacts — a robot at x=0.01 would otherwise map to cell 0, but cells at the very edge of the array might have stability issues. The margin gives a buffer.

---

## Lines 12–15: `_map_cell()` — World → Grid Coordinates

```python
def _map_cell(xw, yw):
    ix = int(np.clip((xw - MAP_XMIN)/(MAP_XMAX - MAP_XMIN)*MAP_RES, 0, MAP_RES-1))
    iy = int(np.clip((yw - MAP_YMIN)/(MAP_YMAX - MAP_YMIN)*MAP_RES, 0, MAP_RES-1))
    return ix, iy
```

**Formula:** `grid_index = (world_pos - min) / (max - min) × resolution`

Example: `xw = 3.6m`
```
ix = (3.6 - (-0.5)) / (7.7 - (-0.5)) × 25 = 4.1 / 8.2 × 25 = 12.5 → int = 12
```

**`np.clip(..., 0, MAP_RES-1)`**: Ensures index stays in [0, 24]. Without clipping, a world position outside the map bounds would give a negative index or out-of-range index.

**`int()`**: Truncates float to int. Combined with clip, gives a valid array index.

---

## Lines 21–21: Obstacle Grid

```python
grid = (CM[:, :, 0] > 0.85).astype(int)
```

`CM[:,:,0]`: The danger map slice — shape (25, 25). Values 0 (safe) to 1 (deadly).

`> 0.85`: Threshold. Only cells with danger > 0.85 are treated as ABSOLUTE obstacles. Pre-seeded walls have danger = 0.9-1.0; experienced near-wall positions have danger = 0.3-0.7.

**Why 0.85 threshold (not 0.5)?** Using 0.5 would make many "risky" cells impassable, overly restricting navigation. 0.85 only blocks cells that are EXTREMELY dangerous (very likely to be walls or death locations). Lower-danger cells are still passable — their cost is just higher (see danger_cost below).

**`.astype(int)`**: Converts bool (True/False) to int (1/0) for the grid collision check.

**`grid[gx, gy] == 1` check**: If the GOAL is inside a wall, the code currently does `pass` (does nothing). This is an acknowledged limitation — in practice, the goal is always a valid place cell center, never a wall.

---

## Lines 27–35: Priority Queue Initialization

```python
open_set = []
heapq.heappush(open_set, (0, sx, sy))
came_from = {}
g_score = {(x,y): float('inf') for x in range(MAP_RES) for y in range(MAP_RES)}
g_score[(sx, sy)] = 0
f_score = {(sx, sy): abs(sx - gx) + abs(sy - gy)}
```

**`heapq.heappush(open_set, (0, sx, sy))`**: Pushes a tuple onto a min-heap. The heap is sorted by the FIRST element (cost 0 for the start node). `heapq` in Python is always a MIN-heap — lowest cost is always at index 0.

**`came_from = {}`**: Dictionary mapping each cell to its parent in the path. Used to reconstruct the path from goal back to start.

**`g_score[(x,y)]: float('inf')`**: Initialize all cells with infinite cost. Only the start node has cost 0. Every other cell's cost is unknown until explored.

**Dictionary comprehension**: `{(x,y): float('inf') for x in range(25) for y in range(25)}` creates a 625-entry dict in one line. More concise than nested loops.

**`abs(sx-gx) + abs(sy-gy)`**: Manhattan distance heuristic for start→goal. In A*, `f = g + h` where h is the heuristic.

---

## Lines 37–70: Main A* Loop

```python
while open_set:
    _, cx, cy = heapq.heappop(open_set)

    if cx == gx and cy == gy:
        # Reconstruct path
        ...
```

`heapq.heappop()`: Removes and returns the LOWEST-COST element. `_` = the cost (we don't need it here since we access g_score). `cx, cy` = current cell coordinates.

**Goal check first**: If the popped cell IS the goal, we've found the shortest path. Reconstruct and return.

**Path reconstruction:**
```python
path = []
curr = (cx, cy)
while curr in came_from:
    path.append(curr)
    curr = came_from[curr]
path.reverse()
```
Traces backward from goal to start via `came_from`, then reverses to get start→goal order.

---

```python
for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,1), (1,-1), (-1,-1)]:
    nx, ny = cx + dx, cy + dy
```

**8-directional movement**: 4 cardinal directions + 4 diagonals. This allows CARL to navigate diagonally — more direct paths in open areas.

**Why not just 4 directions?** With only 4 directions, diagonal navigation requires going E then N (2 steps = distance 2). With 8 directions, going NE directly = 1 step = distance 1.414. 8-directional paths are ~30% shorter on average.

---

```python
    danger_cost = CM[nx, ny, 0] * 50.0
    step_cost = (1.414 if dx != 0 and dy != 0 else 1.0)
    tentative_g = g_score[(cx, cy)] + step_cost + danger_cost
```

**Cost calculation:**

`step_cost`: Diagonal steps cost 1.414 (= √2 ≈ Euclidean distance for diagonal). Cardinal steps cost 1.0.

**Why √2 for diagonals?** If diagonal and cardinal steps both cost 1.0, A* would prefer diagonals even when the direct path is shorter. Using √2 makes costs proportional to actual Euclidean distance — the heuristic remains admissible (never overestimates).

`danger_cost = CM[nx,ny,0] × 50.0`: A danger value of 0.9 (near wall) adds `0.9 × 50 = 45` to the path cost. This is 45× the cost of a safe step — making near-wall paths EXTREMELY expensive. The algorithm will strongly prefer going through open spaces.

**Why 50?** High enough penalty that walls (danger ≈ 0.9) effectively block routing, while lower-danger cells (0.1-0.3) add only a modest 5-15 unit penalty. This creates a "soft" obstacle model — walls aren't absolutely impassable (in degenerate cases, A* might route through a "wall" gap), but they're very expensive.

**`tentative_g < g_score[(nx, ny)]`**: Only update if we found a CHEAPER path to (nx, ny). This is the key A* optimization — prune paths that can't be optimal.

---

## Lines 52–54: Grid → World Coordinates

```python
c_x = MAP_XMIN + (px + 0.5) / MAP_RES * (MAP_XMAX - MAP_XMIN)
c_y = MAP_YMIN + (py + 0.5) / MAP_RES * (MAP_YMAX - MAP_YMIN)
```

**Why `px + 0.5`?** We convert the CENTER of each grid cell (not its corner) to world coordinates. Cell (12, 12) spans x=[MAP_XMIN + 12/25 × range, MAP_XMIN + 13/25 × range]. The center is at +0.5/25 into that range. `(12 + 0.5)/25 × range` gives the cell's center x-coordinate.

**Inverse of `_map_cell()`**: This reverses the world→grid mapping.

---

# PART C — `live_plotter.py` (133 lines)

---

## Line 13: TELEMETRY_PATH

```python
TELEMETRY_PATH = os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")
```

`os.path.join()`: Platform-safe path construction. On Windows this gives `D:\ebca\memory\telemetry_autonomous.csv`, on Linux `D:/ebca/memory/...`. Always use `os.path.join` rather than hardcoding `\\` or `/`.

---

## Lines 15–41: `read_telemetry()` — Live CSV Parsing

```python
headers = next(reader)       # Read first row as column names
for h in headers:
    data[h] = []             # Create empty list for each column
for row in reader:
    if not row or len(row) != len(headers):
        continue             # Skip malformed rows
    for h, val in zip(headers, row):
        if h == 'surge_event':
            data[h].append(val)    # Keep as string
        else:
            data[h].append(float(val))  # Parse as number
```

**Why `zip(headers, row)`?** Pairs column names with values in the same position. Safer than indexing — if a row has fewer values than headers, zip stops at the shorter one.

**Why `len(row) != len(headers): continue`?** CSV files being written WHILE being read can have partial rows (if the writer is mid-write when the reader reads). Skipping partial rows prevents `ValueError` on float conversion.

**`try: float(val)` with fallback**: Non-numeric values (strings) would crash `float()`. The outer try-except catches this and appends the raw string value.

**`data[h] = np.array(data[h])`**: After reading all rows, convert lists to numpy arrays for vectorized operations. Can't do this during reading because numpy arrays have fixed size.

---

## Lines 43–129: Dashboard Layout

```python
fig = plt.figure(figsize=(15, 9))
ax1 = fig.add_subplot(221)    # Top-left
ax2 = fig.add_subplot(222)    # Top-right
ax3 = fig.add_subplot(223)    # Bottom-left
ax4 = fig.add_subplot(224)    # Bottom-right
```

`figsize=(15, 9)`: 15 inches wide, 9 inches tall. Standard widescreen (16:9-ish) proportion. At typical screen resolution (96 DPI), this is 1440×864 pixels.

`add_subplot(221)`: subplot syntax = `N_rows N_cols Index`. `221` = 2 rows, 2 cols, subplot 1 (top-left). `224` = subplot 4 (bottom-right).

**Why 4 subplots?** They're designed to answer 4 questions simultaneously:
1. **Trajectory** (ax1): WHERE has CARL been? (spatial map)
2. **Hormones** (ax2): WHAT is CARL feeling? (internal state)
3. **Brain vs Reflex** (ax3): WHO is driving? (cognitive vs reactive)
4. **Motivation** (ax4): HOW hungry and motivated is CARL? (energetics)

---

## Lines 58–58: Time Normalization

```python
time_s = data['wall_time_s'] - data['wall_time_s'][0]
```

**Start time subtraction**: Raw timestamps are Unix timestamps (seconds since 1970). Subtracting the first timestamp makes time start at 0. `time_s = 0` = simulation start. `time_s = 60` = 1 minute into simulation.

---

## Lines 96–101: Motivation Calculation

```python
battery = data['battery']
da = data['DA']
hunger = 1.0 + 2.0 * (1.0 - battery)
satiation = 1.0 / np.maximum(0.5, da)
motivation = hunger * satiation
```

This REPRODUCES the same motivation formula from `carl_simulation.py` using the CSV data. This lets us PLOT the motivation level retroactively.

**Why `np.maximum(0.5, da)` instead of `max()`?** `da` is a numpy array. Python's `max()` returns a scalar. `np.maximum(0.5, array)` applies element-wise maximum — returns an array where each element is at least 0.5.

**Why `0.5` floor for DA?** `1/DA` would explode if DA approaches 0 (satiation = infinity). The 0.5 floor caps satiation at `1/0.5 = 2.0` maximum.

---

## Lines 112–118: Dual Y-Axis

```python
ax4_twin = ax4.twinx()
ax4_twin.clear()
line3 = ax4_twin.plot(time_s, motivation, color='#ef4444', ...)
ax4_twin.set_ylabel("Motivation Drive (x1)", color='#ef4444')
ax4_twin.grid(False)  # avoid overlapping gridlines
```

**`twinx()`**: Creates a second Y-axis sharing the same X-axis. This lets us plot two metrics with DIFFERENT Y-scales on the same subplot.

Battery is in [0, 100]% (left axis). Motivation is in [0.33, 6.0] (right axis). If plotted on the same scale, one would be unreadable. `twinx()` solves this by giving each its own scale.

**`ax4_twin.grid(False)`**: Without this, BOTH sets of gridlines would appear, creating a confusing double-grid pattern. Turning off the twin's grid leaves only the primary gridlines.

---

## Line 127: `FuncAnimation`

```python
ani = FuncAnimation(fig, update, interval=2000, cache_frame_data=False)
```

**`FuncAnimation`**: Calls `update(frame)` every `interval=2000` milliseconds (2 seconds). This is what makes it "live" — the plots refresh with new CSV data every 2 seconds.

**`cache_frame_data=False`**: Each frame reads the CSV fresh. If this were True, matplotlib would cache the first frame's data and never update — making it NOT live.

**Why 2 seconds?** Fast enough to see real-time behavior. Slow enough not to overwhelm CPU with CSV reads + plot redraws.

---

# PART D — `carl_mj_physics.py` (211 lines)

---

## Lines 4–18: `BCFG` — Two-Robot Configuration Table

```python
# qpos / qvel layout:
# fj_A  : qpos[0:7]   qvel[0:6]
# lw_A  : qpos[7]     qvel[6]
# rw_A  : qpos[8]     qvel[7]
# neck_A: qpos[9]     qvel[8]
# fj_B  : qpos[10:17] qvel[9:15]
# ...

BCFG = [
    dict(name='A', q0=0,  v0=0,  nq=9,  nv=8,  cl=0, cr=1, cn=2),
    dict(name='B', q0=10, v0=9,  nq=19, nv=17, cl=3, cr=4, cn=5),
]
```

**Why this layout?** MuJoCo packs ALL robot state into one `qpos` array. Robot A's state starts at index 0, Robot B's starts at index 10.

`q0`: Starting qpos index for this robot's free joint (7 values: x, y, z, qw, qx, qy, qz).  
`v0`: Starting qvel index (6 values: vx, vy, vz, ωx, ωy, ωz).  
`nq`: Index of the neck joint's qpos. Robot A: `qpos[9]`, Robot B: `qpos[19]`.  
`cl/cr/cn`: Control indices (which `data.ctrl` element to write) for left-wheel, right-wheel, neck.

**Why a config table instead of hardcoded values?** Makes the code GENERIC — `get_state(BCFG[0])` and `get_state(BCFG[1])` work identically for both robots. Adding a third robot would just need a new dict entry.

---

## Lines 31–46: `init_physics()`

```python
wall_names = ['w_s','w_n','w_w','w_e'] + [f'wi{i}' for i in range(9)]
_wall_gids = {_model.geom(n).id for n in wall_names}
```

**Set comprehension**: `{expression for n in list}` creates a Python `set` — no duplicates, O(1) lookup.

`_model.geom(n).id`: Looks up a geometry by name and returns its integer ID (0-indexed). The IDs are used in contact checking (`check_wall_contact()`).

**`'w_s','w_n','w_w','w_e'`**: South, North, West, East outer walls.  
`[f'wi{i}' for i in range(9)]`: Internal walls wi0 through wi8. `f'wi{i}'` is an f-string — `i=3` gives `'wi3'`.

---

## Lines 114–120: `quat_to_euler()`

```python
def quat_to_euler(q):
    w, x, y, z = q
    roll  = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
    sinp  = float(np.clip(2*(w*y - z*x), -1.0, 1.0))
    pitch = math.asin(sinp)
    yaw   = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
    return roll, pitch, yaw
```

**Quaternion to Euler Angles (ZYX convention):**

A quaternion `q = [w, x, y, z]` encodes a 3D rotation. Converting to Euler angles (roll, pitch, yaw):

**Roll (rotation around X):**
```
roll = atan2(2(wx + yz), 1 - 2(x² + y²))
```

**Pitch (rotation around Y):**
```
sinp = 2(wy - zx)
pitch = asin(sinp)
```
`np.clip(sinp, -1, 1)`: Prevents numerical error from producing `asin()` argument slightly outside [-1, 1], which would return NaN.

**Yaw (rotation around Z):**
```
yaw = atan2(2(wz + xy), 1 - 2(y² + z²))
```

**Why `atan2()` not `atan()`?** `atan(y/x)` has range (-π/2, π/2) and breaks at x=0. `atan2(y, x)` returns the FULL (-π, π] range and handles x=0 correctly. Essential for tracking yaw across all 360°.

**Why extract yaw specifically?** The 2D LiDAR and motor control only need yaw (rotation in the horizontal plane). Roll and pitch are incidental (would require 3D path planning). Only yaw is used: `get_lidar()` uses yaw to orient the ray directions.

---

## Lines 148–153: `apply_torque()`

```python
def apply_torque(cfg, u_fwd, u_steer=0.0):
    fwd   = float(np.clip(u_fwd,   -8., 8.))
    steer = float(np.clip(u_steer, -3., 3.))
    _data.ctrl[cfg['cl']] = fwd + steer
    _data.ctrl[cfg['cr']] = fwd - steer
```

**Differential drive mixing:**
```
left  = forward + steer
right = forward - steer
```

When `steer > 0` (right turn): left wheel gets more power, right wheel gets less → robot turns right.

**Why clip `fwd` to ±8 and `steer` to ±3?** The XML actuator limits are `ctrlrange="-12 12"`. The maximum combined command = `fwd + steer = 8 + 3 = 11` — just within the 12N·m physical limit. Clipping prevents singlesided overload: if `steer=3` and `fwd=8`, right wheel = `8-3=5` (reasonable), left = `8+3=11` (just under limit).

---

## Lines 174–179: `park_robot()` — Underground Disposal

```python
def park_robot(cfg):
    """Move dead robot underground so it doesn't interfere."""
    q0 = cfg['q0']
    _data.qpos[q0]   = -5.0   # x: far left
    _data.qpos[q0+1] = -5.0   # y: far bottom
    _data.qpos[q0+2] = -5.0   # z: 5 meters underground
```

**Why -5m underground?** The arena floor is at z=0. Placing the dead robot at z=-5m puts it far below the physics world. The freejoint has no limit on z, so this is physically valid. The robot is invisible in the viewer (below the floor), doesn't collide with anything (no objects underground), and its actuators are zeroed so it doesn't drift.

**Alternative approaches and why they weren't used:**
- `delete object`: MuJoCo doesn't support runtime object deletion
- `disable contacts`: Would require rebuilding the contact model
- `move far away on surface`: z=0 at (−5, −5) → might still appear in LiDAR rays

---

## Lines 185–192: `check_wall_contact()`

```python
def check_wall_contact(cfg):
    rg = _robot_gids[cfg['name']]
    for i in range(_data.ncon):
        c = _data.contact[i]
        g1, g2 = int(c.geom1), int(c.geom2)
        if (g1 in rg and g2 in _wall_gids) or (g2 in rg and g1 in _wall_gids):
            return True
    return False
```

**MuJoCo contact array:** `_data.contact` is an array of all ACTIVE contacts this timestep. `_data.ncon` = number of active contacts. Each contact has `geom1` and `geom2` (the two geometry IDs in contact).

**`if (g1 in rg and g2 in _wall_gids) or (g2 in rg and g1 in _wall_gids)`**: Two cases because contact order is arbitrary — robot-wall and wall-robot are both valid orderings.

**`rg` is a set**: `in rg` is O(1) for sets vs. O(n) for lists. With potentially thousands of contacts per step (in dense environments), this matters.

**Why not use MuJoCo's collision filter?** Collision filtering (`contype`/`conaffinity`) prevents contacts from occurring at all. But we WANT the contact to happen physically (walls stop the robot). We just want to DETECT when it happens.

---

## Lines 195–202: `apply_wind()` / `clear_wind()`

```python
def apply_wind(cfg, fx):
    bid = _model.body(f'base_{cfg["name"]}').id
    _data.xfrc_applied[bid, 0] = fx   # force X in world frame
```

**`_data.xfrc_applied`**: MuJoCo's "externally applied forces" array. Shape `(nbody, 6)` — 3 force components + 3 torque components per body.

`[bid, 0]`: Force in world X direction. Index 0=Fx, 1=Fy, 2=Fz, 3=τx, 4=τy, 5=τz.

**Why apply force to `base_*` body?** Applying to the root body (base) affects the whole robot. Applying to a wheel would only push the wheel, not the chassis.

**Use case:** In the multi-body competition scenario, "wind" is used as a training perturbation — adding random lateral forces forces the robot to learn robust control under disturbance.
