# Walkthrough: `brain/carl_grid_cells.py`
### *Grid Cells, Place Cells & Hippocampal Replay (453 Lines)*

This module implements the Nobel-Prize winning spatial navigation system (O'Keefe & Moser 2014). It contains 3 multi-scale hexagonal Grid Cell modules (the brain's internal ruler), a 400-node Place Cell layer (location neurons), a topological map graph, and a Sharp-Wave Ripple (SWR) reward diffusion engine that replays memory backwards to create navigation trails toward food.

---

## 1. Class: `GridCellModule`

### Setup & Wave Interference Model
* **Lines 18–25:** Defines `GridCellModule`. Uses 3-wave cosine interference model (Burgess 2007) to generate hexagonal firing patterns:
  $$r(x,y) = \frac{1}{3}\left[\cos(\vec{k}_1 \cdot \vec{r}) + \cos(\vec{k}_2 \cdot \vec{r}) + \cos(\vec{k}_3 \cdot \vec{r})\right]$$
* **Lines 26–29:** `__init__(self, scale, orientation_deg, n_cells=64, noise=0.05)`: Initializes module with spatial period `scale` (in meters), 64 neurons, and 5% noise.
* **Lines 31–36:** Generates 3 wave vectors $\vec{k}_1, \vec{k}_2, \vec{k}_3$ separated by $60^\circ$ ($\pi/3$ radians) with spatial frequency $2\pi / \text{scale}$.
* **Line 38:** Assigns a random 3-phase offset vector in $[0, 2\pi]$ to each of the 64 neurons.
* **Line 41:** Initializes dead-reckoning path integration phase state `pi_phase = [0.0, 0.0]`.
* **Line 44:** Allocates activity array of 64 zeros.

### Path Integration & Firing Dynamics
* **Lines 46–48:** `reset(x, y)`: Anchors path integration position estimate to known coordinates $(x, y)$.
* **Lines 50–53:** `integrate(vx, vy, dt)`: Integrates physical velocity: $\text{pi\_phase} \leftarrow \text{pi\_phase} + (v_x \cdot dt, v_y \cdot dt)$.
* **Lines 55–70:** `fire(x=None, y=None)`: Computes firing rates. Uses actual position $(x, y)$ if provided (GPS-grounded), else uses `pi_phase`. Calculates 3-wave projection, shifts values from $[-1, 1]$ to $[0, 1]$, adds Gaussian noise, and returns 64-element firing rate vector.

---

## 2. Class: `PlaceCellLayer`

### Network Setup & Spatial Graph
* **Lines 73–90:** Defines `PlaceCellLayer` (400 place cells). Manages spatial coordinates, topological adjacency graph, recency timestamps, reward beacons, and replay value diffusion.
* **Lines 91–101:** `__init__(n_place=400, arena_bounds=(-5.0, 5.0, -5.0, 5.0), sigma=0.4)`: Generates 400 uniform random center coordinates across the $10\text{m} \times 10\text{m}$ arena (`centres` matrix $400 \times 2$). Sets spatial tuning width $\sigma = 0.4\text{m}$.
* **Lines 104–129:** Initializes:
  * `activity`: 400 firing rates.
  * `adjacency`: Graph dictionary mapping each cell to a set of connected cell indices.
  * `recency`: Array storing tick timestamp of last visit (initialized to -1000).
  * `reward_values`: Active food beacon strengths.
  * `nav_values`: Diffused replay navigation values.
  * `persistent_rewards`: Permanent floor memories that never decay.
  * `total_edges`: Counter tracking graph edges.

### Firing, Decoding & Graph Construction
* **Lines 130–135:** `fire_from_position(x, y)`: Computes Gaussian firing rate based on distance to center: $\text{activity} = \exp(-d^2 / 2\sigma^2)$.
* **Lines 137–144:** `decode_position()`: Population vector decode. Calculates $(x_{est}, y_{est})$ as the activity-weighted dot product of cell centers.
* **Lines 146–149:** `peak_cell()`: Returns `(index, center_coords)` of the most active place cell.
* **Lines 153–164:** `update_graph(old_cell, new_cell, tick)`: Records a physical movement transition between cells. Adds bidirectional edge to `adjacency` and updates `recency[new_cell] = tick`.
* **Lines 166–183:** `stamp_reward(cell_idx, amount=1.0)`: Triggered on food intake. Stamps reward at `cell_idx` and all neighboring cells within $1.5\text{m}$ radius with linear falloff.

### Hippocampal Replay & Value Diffusion
* **Lines 186–224:** `diffuse_rewards(gamma=0.9, decay=0.99995, n_sweeps=5)`: Multi-sweep Sharp-Wave Ripple (SWR) value iteration. Decays standing rewards slowly ($0.99995$). Applies persistent floor (`persistent_rewards * 0.5`). Runs 5 sweeps per tick propagating values:
  $$V(\text{cell}) = \max\left(R(\text{cell}), \gamma \cdot \max_{n \in \text{neighbors}} V(n)\right)$$
* **Lines 227–252:** `get_novelty_target(current_cell, current_tick)`: Returns center coordinates of the graph neighbor with the oldest `recency` timestamp (used in `EXPLORE` mode).
* **Lines 254–278:** `get_replay_target(current_cell)`: Returns coordinates `(x, y, nav_val)` of the neighbor with the highest `nav_values` (used in `SURVIVE` mode).
* **Lines 280–292:** `get_graph_stats()`: Returns diagnostic dictionary of graph statistics.

---

## 3. Class: `HippocampalNavigator`

### Integrated Multi-Module Navigation
* **Lines 296–335:** `__init__()`: Combines 3 grid modules ($scale=0.8\text{m}, 1.2\text{m}, 1.8\text{m}$, total 192 grid cells) with 400 place cells. Allocates Grid-to-Place weight matrix `W_gp` ($400 \times 192$). Sets $6.0\text{ Hz}$ theta oscillation, position estimates, uncertainty, and novelty states.
* **Lines 337–343:** `reset(x, y)`: Anchors all 3 grid modules and position estimates to starting position $(x, y)$.
* **Lines 345–419:** `step(x_actual, y_actual, vx, vy, dt, learn=True)`:
  1. Advances theta phase and calculates gate: $0.5 + 0.5\cos(\theta_{\text{phase}})$.
  2. Updates path integration on all 3 grid modules.
  3. Computes 192-element `grid_vec` and 400-element `place_act`.
  4. Computes path integration error (`pi_error`).
  5. At theta peak (gate $> 0.8$), updates `W_gp` via Oja's Hebbian rule: $\Delta W = 0.002 \cdot \text{gate} \cdot (\text{outer}(place, grid) - place \cdot W_{gp})$.
  6. Blends $90\%$ GPS $+ 10\%$ place cell decode into `x_est, y_est`.
  7. Calculates navigation uncertainty and spatial novelty ($1 / \ln(1 + \text{visits})$).
  8. Returns output dictionary.
* **Lines 421–453:** Helper methods: `theta_learning_rate()`, `curiosity_boost()`, `predict_danger_at()`, and `update_place_danger()`.
