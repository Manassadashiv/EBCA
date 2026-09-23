# The EBCA / CARL-Ω Codebase Human Textbook — Volume 1: Core Cognitive Brain Architecture

This textbook provides a **complete, line-by-line plain English translation of the CARL-Ω codebase**. Every line of code, formula, matrix operation, variable, and conditional logic is translated into human language without python jargon, explaining what it does, why it exists, and how it connects to the physical robot.

---

# CHAPTER 1: `brain/carl_endocrine.py`
### *Neuromodulatory & Hormonal Kinetics (119 Lines)*

This module acts as CARL’s internal endocrine system. It manages four primary brain chemicals (neuromodulators): **Dopamine (DA)**, **Norepinephrine (NE)**, **Serotonin (5-HT)**, and **Acetylcholine (ACh)**. These chemicals dictate CARL's mood, fear, focus, and appetite, and decay naturally over time back to baseline levels.

```
Lines 1–6: Setup & Imports
```
* **Line 1–4:** Module docstring. Identifies this file as managing neuromodulatory endocrine kinetics (diagnostic IDs END-201 through END-204) integrated into unified SoC state slices.
* **Line 5:** Imports `numpy` to handle numerical operations and bounds clamping.
* **Line 6:** Blank line.

```
Lines 7–26: Biological Constants & Baselines
```
* **Line 8:** Defines the `EndocrineSystem` class.
* **Line 9:** `BASELINE_DA = 1.0` — Normal baseline Dopamine. Dopamine represents reward expectation and approach motivation.
* **Line 10:** `BASELINE_NE = 0.1` — Normal baseline Norepinephrine. Norepinephrine represents stress, fear, and panic/alertness.
* **Line 11:** `BASELINE_SHT = 0.8` — Normal baseline Serotonin. Serotonin represents satisfaction, calm, and satiation.
* **Line 12:** `BASELINE_ACH = 0.5` — Normal baseline Acetylcholine. Acetylcholine represents active attention and learning capacity.
* **Line 14:** `DECAY_DA = 2.0` — Dopamine decay rate per second. Extra dopamine drains away quickly.
* **Line 15:** `DECAY_NE = 3.0` — Norepinephrine decay rate per second. Panic/fear drains rapidly once danger passes.
* **Line 16:** `DECAY_SHT = 1.0` — Serotonin decay rate per second. Satisfaction fades slowly.
* **Line 17:** `DECAY_ACH = 2.5` — Acetylcholine decay rate per second. High focus decays steadily back to normal.
* **Line 19:** `PI_0 = 1.0` — Base sensory precision weight (default 1.0).
* **Line 20:** `GAMMA_ACH = 0.6` — Acetylcholine attention multiplier. High focus boosts sensory attention by up to 60%.
* **Line 21:** `GAMMA_NE = 0.4` — Norepinephrine stress multiplier. Stress boosts alertness by up to 40%.
* **Line 22:** `GAMMA_SHT = 0.3` — Serotonin calm multiplier. High calm reduces hyper-vigilance by 30%.
* **Line 24:** `MAX_NM = 3.0` — Maximum upper ceiling for any hormone level.
* **Line 25:** `MIN_NM = 0.0` — Minimum floor for any hormone level (prevents negative concentrations).
* **Line 26:** Blank line.

```
Lines 27–35: Initialization (Birth State)
```
* **Line 27:** `def __init__(self):` — Constructor method initializing a new endocrine system.
* **Line 28:** `self.DA = self.BASELINE_DA` — Initializes current Dopamine to baseline (1.0).
* **Line 29:** `self.NE = self.BASELINE_NE` — Initializes current Norepinephrine to baseline (0.1).
* **Line 30:** `self.SHT = self.BASELINE_SHT` — Initializes current Serotonin to baseline (0.8).
* **Line 31:** `self.ACh = self.BASELINE_ACH` — Initializes current Acetylcholine to baseline (0.5).
* **Line 32:** `self.reward_avg = 0.0` — Sets historical reward average to 0.0.
* **Line 33:** `self.reward_avg_alpha = 0.01` — Sets exponential memory smoothing speed for reward average to 1%.
* **Line 34:** `self.last_surge_event = ""` — Initializes text label for last chemical surge to empty string.
* **Line 35:** Blank line.

```
Lines 36–46: Timestep Chemical Decay (`step`)
```
* **Line 36:** `def step(self, dt: float = 0.033):` — Advances hormone levels by `dt` seconds (30 Hz loop).
* **Line 37:** Updates Dopamine using first-order decay equation: `DA += -2.0 * (DA - 1.0) * dt`. Pulls Dopamine back toward 1.0.
* **Line 38:** Updates Norepinephrine decay: `NE += -3.0 * (NE - 0.1) * dt`. Pulls Norepinephrine back toward 0.1.
* **Line 39:** Updates Serotonin decay: `SHT += -1.0 * (SHT - 0.8) * dt`. Pulls Serotonin back toward 0.8.
* **Line 40:** Updates Acetylcholine decay: `ACh += -2.5 * (ACh - 0.5) * dt`. Pulls Acetylcholine back toward 0.5.
* **Line 42–45:** Clamps all four hormone values to the range [0.0, 3.0].
* **Line 46:** Blank line.

```
Lines 47–62: Chemical Surges (`surge_da`, `surge_ne`, `surge_sht`, `surge_ach`)
```
* **Line 47–49:** `surge_da(amount=0.35)`: Adds `amount` to Dopamine and sets `last_surge_event` to `"DA+0.35"`. Triggered by food/reward.
* **Line 51–53:** `surge_ne(amount=0.4)`: Adds `amount` to Norepinephrine and sets `last_surge_event` to `"NE+0.40"`. Triggered by collisions/danger.
* **Line 55–57:** `surge_sht(amount=0.15)`: Adds `amount` to Serotonin and sets `last_surge_event` to `"5HT+0.15"`. Triggered post-eating (satiation).
* **Line 59–61:** `surge_ach(amount=0.25)`: Adds `amount` to Acetylcholine and sets `last_surge_event` to `"ACh+0.25"`. Triggered when entering new unvisited cells.
* **Line 62:** Blank line.

```
Lines 63–79: Sensory Trust & RPE
```
* **Line 63–69:** `get_precision_weight()`: Calculates Bayesian precision weight: `1.0 * (1.0 + 0.6*ACh + 0.4*NE - 0.3*SHT)`. Focus and stress increase trust in sensors; calm reduces sensory urgency.
* **Line 70:** Floors precision weight at `0.1` so CARL never ignores sensors completely.
* **Line 72–73:** `get_exploration_noise_scale()`: Returns current Norepinephrine level (minimum floor 0.01) to scale motor noise. High stress creates random escape movements.
* **Line 75–78:** `get_reward_prediction_error()`: Calculates `RPE = DA - reward_avg`. Updates `reward_avg` by blending 1% of current DA. Returns positive RPE for unexpected treats, negative RPE for disappointment.
* **Line 79:** Blank line.

```
Lines 80–114: High-Level Behavioral Governor
```
* **Line 80–86:** Docstring for `get_behavioral_mode()`.
* **Line 87–88:** If food is visible in camera FOV, returns **`"EXPLOIT"`** (approach target).
* **Line 89–90:** Else if battery < 15% OR Norepinephrine > 2.0, returns **`"SURVIVE"`** (desperate food search / emergency escape).
* **Line 91–92:** Else, returns **`"EXPLORE"`** (seek novelty, map arena).
* **Line 94–101:** `get_hunger_drive(battery_level)`: Returns continuous hunger `1.0 - battery_level`, clamped between `0.0` (full) and `1.0` (starving).
* **Line 103–113:** `get_replay_blend_weight(battery_level, max_nav_value)`: Blends memory gradient influence. `hunger = 1.0 - battery`, `signal_strength = nav_value / 2.0`. Returns `signal_strength * (0.3 + 0.7 * hunger)` clamped to [0, 1]. Full robots follow memory weakly; starving robots follow memory urgently.
* **Line 115–118:** `__repr__()`: Returns printable text summary of all hormone concentrations and precision weight.
* **Line 119:** Blank line (End of file).

---

# CHAPTER 2: `brain/carl_reflex.py`
### *Spiking Neural Network LIF Obstacle Avoidance Layer (177 Lines)*

This module implements a Leaky Integrate-and-Fire (LIF) Spiking Neural Network (SNN) that acts as CARL’s instinctive reflex loop (spinal cord). It reads 24 LiDAR sonar rays and fires motor spikes to steer wheels away from obstacles without waiting for higher cognitive brain loops.

```
Lines 1–18: Setup & Parameters
```
* **Line 1–9:** Module docstring describing LIF reflex mechanics, differential steering, and backup-and-spin emergency behaviors.
* **Line 10:** Imports `math` for exponential decay calculations.
* **Line 11:** Imports `numpy` for vector arrays and random numbers.
* **Line 14–18:** Defines the `SpikingReflexLayer` class.

```
Lines 19–34: Network Architecture Initialization
```
* **Line 19:** `def __init__(self, num_sensors=24, num_motor_neurons=2):` — Constructor taking 24 sonar inputs and 2 motor outputs (Motor 0: Turn Left, Motor 1: Turn Right).
* **Line 20–21:** Stores sensor and motor neuron counts.
* **Line 23:** `self.V = np.zeros(2)` — Membrane potentials for Motor 0 and Motor 1 initialized to 0.0 Volts.
* **Line 24:** `self.V_th = 1.0` — Firing voltage threshold set to 1.0 Volt. When potential hits 1.0, neuron fires a spike.
* **Line 25:** `self.tau_m = 0.02` — Membrane leak time constant (20 milliseconds).
* **Line 26:** `self.dt = 0.033` — Control cycle step size (30 Hz).
* **Line 32:** `self.w = np.zeros((2, 24))` — Synaptic weight matrix connecting 24 sonar inputs to 2 motor outputs.
* **Line 33:** `angles = np.linspace(-np.pi, np.pi, 24, endpoint=False)` — Divides 360° around CARL into 24 ray angles from $-\pi$ to $+\pi$.

```
Lines 35–49: Hardwired Reflex Synapse Weighting
```
* **Line 35–36:** Loops through each sonar ray index `j` and gets its angle `a`.
* **Line 38:** Checks if ray `a` is in the front hemisphere ($[-\pi/2, \pi/2]$).
* **Line 40–41:** If obstacle is on front-right ($a < 0$), connects ray to **Motor 0 (Turn Left)** with weight scaling up to 3.0 as angle approaches center.
* **Line 43–44:** If obstacle is on front-left ($a > 0$), connects ray to **Motor 1 (Turn Right)** with weight scaling up to 3.0.
* **Line 46–48:** If obstacle is directly dead ahead ($a == 0$), excites Motor 0 with weight 1.8 and Motor 1 with weight 2.2 to force a left turn/spin.

```
Lines 50–70: STDP Traces & Output State
```
* **Line 51:** `self.trace_pre` — Pre-synaptic spike memory trace for 24 sensors.
* **Line 52:** `self.trace_post` — Post-synaptic spike memory trace for 2 motor neurons.
* **Line 53:** `self.eligibility` — Eligibility trace matrix ($2 \times 24$) storing recent STDP co-firing events.
* **Line 55–57:** Sets STDP decay constants (`tau_stdp = 0.02s`, `tau_e = 0.1s`, `eta_stdp = 0.01`).
* **Line 59–62:** Pre-computes exponential decay factors per step using $e^{-dt / \tau}$.
* **Line 65:** `self.reflex_outputs = np.zeros(2)` — Stores accumulated wheel speed offsets `[left_speed_delta, right_speed_delta]`.
* **Line 66–67:** Sets motor decay time constant (100 ms) and computes `motor_decay` factor.
* **Line 68–69:** Initializes `backup_timer` to 0 and `backup_spin_dir` to 1.0 (forward/spin state).

```
Lines 71–94: Dynamic Distance Thresholding & Collision Check
```
* **Line 71:** `def step(self, sensor_dists, reservoir_bias, da, food_dist=99.0):` — Main reflex update step.
* **Line 75:** Initializes pre-synaptic spike array `spikes_pre` to 24 zeros.
* **Line 76:** `nu_max = 100.0` — Maximum Poisson spike frequency (100 Hz).
* **Line 80–84:** Sets default warning distance threshold `d_trigger = 0.45m` and collision limit `0.28m`. If food is close (`food_dist < 1.0m`), lowers thresholds to `0.32m` and `0.20m` so CARL doesn't back away from food.
* **Line 87–88:** Checks minimum distance among 6 front sonars (indices 9 to 14). Sets `imminent_collision` if distance $< 0.28m$.
* **Line 91–92:** Checks minimum distance among 3 rear sonars (indices 0, 1, 23). Sets `imminent_rear_collision` if distance $< 0.25m$.

```
Lines 95–118: Poisson Spiking & LIF Voltage Integration
```
* **Line 95–100:** If frontal collision is imminent and `backup_timer` is 0, sets `backup_timer = 20` ticks (~0.6s). Compares clearance of front-left sonars vs. front-right sonars; sets `backup_spin_dir = 1.0` toward the side with more space.
* **Line 102–107:** For each sensor `j`, if sonar distance $d < d\_trigger$, calculates spike probability $p = 100 \times (1 - d / d\_trigger) \times 0.033$. If a random float is $< p$, sensor `j` fires a spike (`spikes_pre[j] = 1.0`).
* **Line 110:** Computes input current: `current_inputs = (W @ spikes_pre) + reservoir_bias`.
* **Line 111:** Updates membrane potential: `V = V * mem_decay + current_inputs`. Leaks old voltage and adds new current.
* **Line 113–117:** Checks if Motor 0 or Motor 1 potential $V \ge 1.0V$. If so, sets `spikes_post[i] = 1.0` and resets potential $V[i] = 0.0$.

```
Lines 119–138: Differential Steering Calculation
```
* **Line 120:** Decays previous reflex outputs by `motor_decay`.
* **Line 123–127:** Sets default reflex push strength to `5.0` and clamp limit to `6.0`. If food is near (`< 1.2m`), weakens reflex strength to `1.0` and clamp limit to `1.5` so vision can take control.
* **Line 130–132:** If Motor 0 fires (Turn Left): subtracts `reflex_strength` from left wheel delta and adds `reflex_strength` to right wheel delta.
* **Line 135–137:** If Motor 1 fires (Turn Right): adds `reflex_strength` to left wheel delta and subtracts `reflex_strength` from right wheel delta.

```
Lines 139–160: Emergency Backup & Rear Collision Overrides
```
* **Line 140–153:** If `backup_timer > 0`: decrements timer by 1. If rear is also blocked, spins in place (`left = +3.5 * dir, right = -3.5 * dir`). Else, backs up while swinging front toward open space (`left = -4.5, right = -1.5` or vice versa).
* **Line 154–157:** Else if blocked only from behind, pushes forward (`left = 3.0, right = 3.0`).
* **Line 160:** Clamps reflex outputs to `[-clamp_limit, +clamp_limit]`.

```
Lines 161–177: R-STDP Plasticity Update
```
* **Line 163–164:** Updates pre- and post-synaptic spike memory traces: `trace = trace * decay + spikes`.
* **Line 166–170:** Updates eligibility trace matrix: `eligibility = eligibility * elig_decay + (trace_pre * spikes_post - trace_post * spikes_pre)`. Captures timing correlation between sensor spikes and motor spikes.
* **Line 172–174:** Computes dopamine error `da_error = DA - 1.0`. Updates synaptic weights: `w += 0.01 * eligibility * da_error`. Clamps weights to `[-3.0, +3.0]`. If a reflex move resulted in food/dopamine, that reflex connection is strengthened.
* **Line 176:** Returns `reflex_outputs` vector `[speed_left_delta, speed_right_delta]`.
* **Line 177:** End of file.

---

# CHAPTER 3: `brain/carl_reservoir.py`
### *Liquid State Machine (LSM) Recurrent Neural Cortex (197 Lines)*

This module is CARL's primary cognitive brain. It is a 500-neuron recurrent neural network (Liquid State Machine) with sparse connections scaled to a critical spectral radius of 1.0 (edge of chaos). Inputs drive internal dynamic ripples; an online Recursive Least Squares (RLS) algorithm trains only the readout weights.

```
Lines 1–28: Header & Biological Theory
```
* **Line 1–24:** Docstring explaining LSM architecture (500 neurons, 15% sparsity, spectral radius 1.0, RLS readout learning, FORCE learning principles).
* **Line 25:** Imports `numpy`.
* **Line 26:** Imports `os` for file loading/saving.
* **Line 28:** Blank line.

```
Lines 29–55: Class & Matrix Initialization
```
* **Line 29–30:** Defines `LiquidStateReservoir` class.
* **Line 35–37:** `__init__(self, N=500, M=25, K=3, spectral_radius=1.0, sparsity=0.15, tau=0.1, sigma_in=0.1, seed=42):`
* **Line 49–52:** Stores parameters: `N=500` (reservoir size), `M=25` (sensory input dimension), `K=3` (motor outputs: left wheel, right wheel, neck pan), `tau=0.1s` (leaking time constant), `sigma_noise_base=0.02`.
* **Line 54:** Initializes random number generator with fixed seed `42` for reproducible network topology.
* **Line 58:** Creates input weight matrix `W_in` ($500 \times 25$) with Gaussian random values scaled by `sigma_in` (0.1).

```
Lines 59–78: Sparse Recurrent Weight Matrix & Readout Setup
```
* **Line 61:** Generates raw random weight matrix `W_raw` ($500 \times 500$).
* **Line 63–64:** Creates random boolean mask keeping only 15% of connections (`sparsity=0.15`) and zeros out the other 85%.
* **Line 66–72:** Calculates eigenvalues of `W_raw`. Scales `W_res = W_raw * (target_radius / max_eigenvalue)` so the spectral radius equals exactly **1.0**. This keeps the reservoir at the critical edge of chaos (maximum memory capacity without exploding).
* **Line 77:** Initializes readout weight matrix `W_out` ($3 \times 500$) to all zeros. At birth, CARL has no cognitive motor habits — only reflexes.
* **Line 80:** Initializes reservoir state vector `x` ($500$ neurons) to zero.

```
Lines 82–97: RLS Setup & Telemetry Tracker
```
* **Line 84:** `self.rls_alpha = 1.0` — Initial RLS inverse correlation scale.
* **Line 85:** `self.rls_lambda = 0.999` — RLS forgetting factor (remembers past experiences over thousands of ticks).
* **Line 86:** `self.P = np.eye(500) * 1.0` — RLS inverse correlation matrix ($500 \times 500$) initialized to Identity matrix.
* **Line 89–90:** Initializes RLS update counter to 0 and prediction error array to 3 zeros.
* **Line 92–96:** Prints initialization status to terminal (`[LSM-211] Reservoir initialized...`).
* **Line 97:** Blank line.

```
Lines 98–131: Timestep Dynamics (`step`)
```
* **Line 98–109:** Function `step(self, u, noise_scale=0.02, dt=0.033)`: Advances reservoir state by 1 step at 30 Hz.
* **Line 111:** Generates exploration noise vector $\eta \sim \mathcal{N}(0, 0.02 \times \text{noise\_scale})$ across all 500 neurons.
* **Line 115:** Calculates leak rate factor `leak = dt / tau` ($0.033 / 0.1 = 0.33$).
* **Line 116:** Computes activation drive: `drive = tanh(W_res @ x + W_in @ u + eta)`.
* **Line 117:** Updates leaky integrator state: `x = (1.0 - leak) * x + leak * drive`.
* **Line 119–122:** Checks if `x` contains any NaN or Inf numbers. If detected, prints warning `[LSM-211]` and soft-resets invalid values to 0.0.
* **Line 125:** Computes cognitive motor output: `y = W_out @ x`.
* **Line 128:** Clamps motor output `y` to range `[-2.0, +2.0]`.
* **Line 130:** Returns `y` vector `[left_motor, right_motor, neck_motor]`.

```
Lines 132–174: Online RLS Readout Training (`rls_update`)
```
* **Line 132–143:** Function `rls_update(self, y_target)`: Trains `W_out` using Recursive Least Squares (FORCE learning) at $\le 5\text{ Hz}$.
* **Line 143:** Sets feature vector `phi = self.x` (current 500-neuron state).
* **Line 146–148:** Computes prediction error: `error = y_target - (W_out @ phi)`. Stores copy in `last_prediction_error`.
* **Line 151–155:** Computes RLS gain vector: `gain = (P @ phi) / (lambda + phi^T @ P @ phi)`. Protects against division by zero if denominator is $< 10^{-12}$.
* **Line 158:** Updates inverse correlation matrix: `P = (P - gain @ (phi^T @ P)) / lambda`.
* **Line 161–163:** Clamps matrix `P` if its norm exceeds $10^6$ to prevent numerical explosion.
* **Line 166–167:** Updates readout weights: `W_out[k] += error[k] * gain` for each output dimension `k`.
* **Line 169:** Increments `total_rls_updates` counter by 1.
* **Line 171–174:** `get_state_norm()`: Returns the L2 norm (magnitude) of the 500-neuron state vector `x`.

```
Lines 175–197: Memory Serialization (`save` & `load`)
```
* **Line 175–182:** `save(self, path)`: Saves `x`, `W_out`, `P`, `W_in`, `W_res`, and `total_rls_updates` to a `.npz` binary file on disk. Prints confirmation `[GIS-901]`.
* **Line 183–196:** `load(self, path)`: Restores all weight matrices and state variables from a `.npz` file if it exists. Returns `True` on success, `False` if missing.
* **Line 197:** End of file.

---

# CHAPTER 4: `brain/carl_grid_cells.py`
### *Grid Cells, Place Cells & Hippocampal Replay (453 Lines)*

This module implements the Nobel-Prize winning spatial navigation system (O'Keefe & Moser 2014). It contains 3 multi-scale hexagonal Grid Cell modules (the brain's internal ruler), a 400-node Place Cell layer (location neurons), a topological map graph, and a Sharp-Wave Ripple (SWR) reward diffusion engine that replays memory backwards to create navigation trails toward food.

```
Lines 1–16: Header & Biological References
```
* **Line 1–12:** Module description referencing the 3-wave interference grid model (Burgess 2007) and Hebbian place cell competition.
* **Line 13:** Imports `math`.
* **Line 14:** Imports `numpy`.

```
Lines 17–46: GridCellModule Initialization
```
* **Line 18–26:** Class `GridCellModule`. Uses 3-wave cosine interference: $r(x,y) = \frac{1}{3}[\cos(\vec{k}_1 \cdot \vec{r}) + \cos(\vec{k}_2 \cdot \vec{r}) + \cos(\vec{k}_3 \cdot \vec{r})]$.
* **Line 26:** `__init__(self, scale, orientation_deg, n_cells=64, noise=0.05):`
* **Line 27–29:** Stores spatial scale (wave period in meters), cell count (64), and noise (0.05).
* **Line 32–35:** Converts `orientation_deg` to radians. Generates 3 wave vectors $\vec{k}_1, \vec{k}_2, \vec{k}_3$ spaced $60^\circ$ apart with wave number $2\pi / \text{scale}$.
* **Line 38:** Assigns random phase offsets $[0, 2\pi]$ to each of the 64 cells.
* **Line 41:** Initializes path integration estimate array `pi_phase = [0.0, 0.0]`.
* **Line 44:** Initializes cell activity vector `activity` ($64$) to zero.

```
Lines 46–70: Grid Cell Path Integration & Firing
```
* **Line 46–48:** `reset(self, x, y)`: Anchors path integration position estimate to known coordinates `(x, y)`.
* **Line 50–53:** `integrate(self, vx, vy, dt)`: Updates internal position estimate using velocity: `pi_phase += [vx * dt, vy * dt]`.
* **Line 55–69:** `fire(self, x=None, y=None)`: Computes firing rates for all 64 cells. Projects position onto the 3 wave vectors. Calculates sum of 3 cosines divided by 3. Shifts range from $[-1,1]$ to $[0,1]$, adds Gaussian noise, and clamps to minimum 0.0. Returns copy of 64-element activity array.

```
Lines 72–130: PlaceCellLayer Initialization & Setup
```
* **Line 73–90:** Class `PlaceCellLayer` (400 place cells). Manages spatial locations, topological graph edges, recency timestamps, food reward beacons, and replay diffusion.
* **Line 91–95:** `__init__(self, n_place=400, arena_bounds=(-5.0, 5.0, -5.0, 5.0), sigma=0.4):`
* **Line 97–101:** Generates 400 uniform random place cell center coordinates $(x, y)$ across the $10\text{m} \times 10\text{m}$ arena (`centres` matrix $400 \times 2$).
* **Line 104:** Initializes place cell activity array to 400 zeros.
* **Line 109:** Initializes `adjacency` graph dictionary mapping each place cell index $0..399$ to an empty set of neighbor cell indices.
* **Line 113:** Initializes `recency` array ($400$) to $-1000$ (stores tick timestamp of last visit).
* **Line 117:** Initializes `reward_values` array ($400$) to zeros (stores active food beacon strength).
* **Line 121:** Initializes `nav_values` array ($400$) to zeros (stores diffused replay navigation values).
* **Line 125:** Initializes `persistent_rewards` array ($400$) to zeros (permanent reward floor that never decays).
* **Line 128:** Sets `total_edges = 0`.

```
Lines 131–151: Place Cell Firing & Position Decoding
```
* **Line 130–135:** `fire_from_position(self, x, y)`: Calculates squared distance from $(x, y)$ to all 400 cell centers. Computes Gaussian firing rate: $\text{activity} = \exp(-d^2 / (2\sigma^2))$.
* **Line 137–144:** `decode_position(self)`: Population vector decoding. Estimates $(x_{est}, y_{est})$ by taking the weighted dot product of place cell activities with their center coordinates. Returns `(None, None)` if total activity is $< 10^{-6}$.
* **Line 146–149:** `peak_cell(self)`: Finds the index of the most active place cell and returns `(index, center_coords)`.

```
Lines 152–184: Graph Building & Reward Stamping
```
* **Line 153–164:** `update_graph(self, old_cell, new_cell, tick)`: Records a physical movement transition from `old_cell` to `new_cell`. Adds bidirectional edges into `adjacency` dictionary and increments `total_edges`. Updates `recency[new_cell] = tick`.
* **Line 166–183:** `stamp_reward(self, cell_idx, amount=1.0)`: Triggered when CARL eats food. Stamps `reward_values` and `persistent_rewards` at `cell_idx` with `amount`. Also stamps all neighboring cells within a $1.5\text{m}$ radius with a linear falloff to create a wide reward zone.

```
Lines 185–225: Hippocampal Replay: Value Diffusion (`diffuse_rewards`)
```
* **Line 186–206:** Docstring explaining multi-sweep value iteration modeling Sharp-Wave Ripples (SWRs).
* **Line 208:** Decays standing reward values very slowly: `reward_values *= decay` (decay = 0.99995).
* **Line 211:** Applies persistent floor: `reward_values = max(reward_values, persistent_rewards * 0.5)`.
* **Line 214–223:** Runs 5 value iteration sweeps per tick. For each cell, checks all connected graph neighbors and updates value: $V(\text{cell}) = \max(R(\text{cell}), \gamma \times \max(V(\text{neighbors})))$ where $\gamma = 0.9$. Propagates reward backwards 5 graph hops per frame.
* **Line 224:** Stores result in `self.nav_values`.

```
Lines 226–294: Navigation Waypoint Decoders & Stats
```
* **Line 227–252:** `get_novelty_target(current_cell, current_tick)`: Used in `EXPLORE` mode. Scans graph neighbors of `current_cell` and returns the coordinates of the neighbor with the oldest `recency` timestamp (least recently visited).
* **Line 254–278:** `get_replay_target(current_cell)`: Used in `SURVIVE` mode. Scans graph neighbors of `current_cell` and returns coordinates `(x, y, nav_val)` of the neighbor with the highest `nav_values`. Guides CARL along the steepest reward gradient.
* **Line 280–292:** `get_graph_stats()`: Returns diagnostic dictionary containing total edges, connected cell count, maximum degree, max nav value, mean nav value, and beacon counts.

```
Lines 295–344: Full Hippocampal Navigator System
```
* **Line 296–305:** Class `HippocampalNavigator`. Combines 3 grid cell modules with 400 place cells into a complete navigation system.
* **Line 306–313:** Initializes 3 grid cell modules at scales $0.8\text{m}$, $1.2\text{m}$, $1.8\text{m}$ and orientations $0^\circ, 30^\circ, 60^\circ$ ($192$ grid cells total).
* **Line 315:** Initializes 400-node `PlaceCellLayer`.
* **Line 318:** Initializes Grid-to-Place weight matrix `W_gp` ($400 \times 192$) with random values scaled by 0.01.
* **Line 321–322:** Sets running position estimates `x_est = 0.4`, `y_est = 0.4`.
* **Line 325–326:** Sets theta phase oscillation ($6.0\text{ Hz}$).
* **Line 328–335:** Initializes uncertainty to 1.0, novelty to 1.0, and `visit_map` dictionary to empty.
* **Line 337–343:** `reset(x, y)`: Anchors all 3 grid modules and position estimates to starting coordinates `(x, y)`.

```
Lines 345–420: Timestep Step & Learning (`step`)
```
* **Line 346–358:** `step(self, x_actual, y_actual, vx, vy, dt, learn=True)`: Main hippocampal update.
* **Line 360–361:** Advances theta oscillation phase and calculates theta gate: $0.5 + 0.5 \cos(\theta_{\text{phase}})$. Oscillates between 0.0 and 1.0 at 6 Hz.
* **Line 364–365:** Updates path integration across all 3 grid modules using velocity `vx, vy`.
* **Line 368–373:** Computes grid cell firing across all 3 modules and concatenates into a 192-element vector `grid_vec`.
* **Line 376:** Computes place cell firing from position (`place_act` 400-element vector).
* **Line 379–383:** Computes path integration error (`pi_error`) between dead-reckoned grid phase mean and actual GPS coordinates.
* **Line 386–390:** If `learn=True` and theta gate $> 0.8$ (at theta peak), updates grid-to-place weight matrix `W_gp` using Oja's Hebbian learning rule: $\Delta W = 0.002 \times \text{gate} \times (\text{outer}(place, grid) - place \times W_{gp})$. Clamps weights to $[-2.0, +2.0]$.
* **Line 393–397:** Decodes position from place cells and blends $90\%$ GPS $+ 10\%$ decoded place position into `x_est`, `y_est`.
* **Line 401–403:** Calculates navigation uncertainty: $(1.0 - \text{peak\_place\_rate}) \times 0.7 + \min(\text{pi\_error}/2, 1.0) \times 0.3$.
* **Line 406–408:** Bins position into $0.5\text{m}$ grid, increments visit count in `visit_map`, and calculates spatial novelty: $1.0 / \ln(1 + \text{visits})$.
* **Line 410–419:** Returns diagnostic output dictionary containing grid vector, place vector, estimated position, uncertainty, novelty, theta gate, and PI error.

```
Lines 421–453: Theta Gating, Curiosity Boost & Danger Memory
```
* **Line 422–428:** `theta_learning_rate(base_lam=0.990)`: Modulates weight decay rate by theta phase. High plasticity at theta peak, consolidation at theta trough.
* **Line 431–436:** `curiosity_boost(base_curiosity)`: Amplifies curiosity using spatial novelty: $\text{curiosity} \times (1 + \text{novelty} \times 0.8)$.
* **Line 439–446:** `predict_danger_at(x, y, danger_memory)`: Computes dot product of place cell firing at $(x, y)$ with danger memory vector to predict spatial danger.
* **Line 448–452:** `update_place_danger(danger_memory, x, y, danger_val)`: Blends current danger value into `danger_memory` vector at location $(x, y)$ using Hebbian learning.
* **Line 453:** End of file.

---

# CHAPTER 5: `brain/carl_stdp.py`
### *Reward-Modulated Spike-Timing Dependent Plasticity (278 Lines)*

This module implements three-factor Reward-Modulated Spike-Timing Dependent Plasticity (R-STDP) based on Markram (1997) and Izhikevich (2007). It adjusts synaptic weights based on the exact millisecond timing between pre-synaptic and post-synaptic spikes, modulated by dopamine.

```
Lines 1–31: Mathematical Constants & Parameters
```
* **Line 1–16:** Docstring explaining 3-factor learning rule: $\Delta W = \text{learning\_rate} \times \text{Reward} \times \text{Eligibility\_Trace}$.
* **Line 17–18:** Imports `numpy` and `deque`.
* **Line 22:** `TAU_PRE = 20.0` — Pre-synaptic spike memory decay time constant (20 ms).
* **Line 23:** `TAU_POST = 20.0` — Post-synaptic spike memory decay time constant (20 ms).
* **Line 24:** `TAU_E = 50.0` — Eligibility trace decay time constant (50 ms).
* **Line 25:** `A_PLUS = 0.01` — Long-Term Potentiation (LTP) amplitude (strengthening).
* **Line 26:** `A_MINUS = 0.012` — Long-Term Depression (LTD) amplitude (weakening; slightly larger to favor depression).
* **Line 27:** `W_MAX = 2.0` — Maximum synaptic weight ceiling.
* **Line 28:** `W_MIN = -0.5` — Minimum synaptic weight floor (allows mild inhibition).
* **Line 29:** `LR = 0.008` — Reward modulation learning rate.

```
Lines 32–75: STDPSynapse Class Initialization & Core Dynamics
```
* **Line 32–40:** Class `STDPSynapse`. Manages a 2D weight matrix between `pre_size` input neurons and `post_size` output neurons.
* **Line 41–43:** Stores dimensions and initializes weight matrix `W` ($post \times pre$) with random values scaled by `init_scale` (0.1).
* **Line 46–48:** Initializes pre-spike memory trace `trace_pre` ($pre$), post-spike memory trace `trace_post` ($post$), and eligibility trace matrix `E` ($post \times pre$) to zeros.
* **Line 50–74:** `step(self, pre_spikes, post_spikes, reward, dt=1.0)`: Main STDP update step.
* **Line 57–59:** Decays pre-trace, post-trace, and eligibility traces using $e^{-dt / \tau}$.
* **Line 62–63:** Adds new pre-spikes to `trace_pre` and new post-spikes to `trace_post`.
* **Line 66:** Computes STDP correlation: pre-before-post causes positive LTP (`A_PLUS * outer(post_spikes, trace_pre)`), post-before-pre causes negative LTD (`A_MINUS * outer(trace_post, pre_spikes)`). Updates eligibility trace matrix `E`.
* **Line 69:** Updates synaptic weight matrix: `W += 0.008 * reward * E`.
* **Line 72:** Clamps weights `W` to range `[-0.5, +2.0]`.

```
Lines 76–123: Readout Predictions & Reset Mechanics
```
* **Line 76–83:** `predict(self, pre_spikes)`: Computes forward matrix multiplication `W @ pre_spikes` to predict action values from pre-synaptic state input.
* **Line 85–92:** `reset_traces(self)`: Resets `trace_pre`, `trace_post`, and `E` matrix back to zeros (used at episode boundaries).
* **Line 94–122:** `get_synapse_stats()`: Returns diagnostic statistics dictionary containing weight norm, mean weight, max weight, min weight, mean eligibility, max eligibility, pre-trace norm, and post-trace norm.

```
Lines 124–163: STDPActionEvaluator Class Setup
```
* **Line 124–135:** Class `STDPActionEvaluator`. Uses R-STDP to evaluate action qualities from state inputs.
* **Line 136–143:** `__init__(self, state_dim=5, visual_dim=15, n_actions=9):` Sets up total input state dimension `full_dim = 20` ($5$ proprioception $+ 15$ visual features) and 9 candidate actions. Instantiates `STDPSynapse(20, 9)`.
* **Line 146–147:** Initializes reward baseline to 0.0 and baseline decay time constant to 200 steps.
* **Line 150:** Defines discrete action candidate map `[-8.0, -5.0, -2.0, -1.0, 0.0, 1.0, 2.0, 5.0, 8.0]` (wheel steer angles).
* **Line 152–155:** `encode_state(x, v_pop)`: Normalizes 5 proprioceptive state variables and concatenates with 15 visual features into a 20-element vector bounded in $[0, 1]$.
* **Line 157–162:** `encode_action(u)`: Finds the nearest discrete action index for input value `u` and returns a 9-element one-hot spike vector (1.0 at chosen action index, 0.0 elsewhere).

```
Lines 164–200: STDP Action Learning & Evaluation
```
* **Line 164–172:** `update(self, xk, v_pop, uk, surprise, nm_DA)`: Called every step with state `xk`, vision `v_pop`, action `uk`, RLS surprise error, and Dopamine `nm_DA`.
* **Line 171–172:** Encodes pre-synaptic state spikes and post-synaptic action spikes.
* **Line 175–178:** Calculates raw reward: `nm_DA - surprise * 0.5`. Subtracts `reward_baseline` to compute dopamine prediction error. Blends current reward into baseline.
* **Line 181–183:** Gates spikes by surprise threshold (0.15): spikes only pass if `surprise > 0.15` (learning occurs only on notable unexpected events).
* **Line 185:** Executes `synapse.step(pre_spikes, post_spikes, reward)`.
* **Line 187–195:** `action_quality(x, v_pop, u)`: Predicts STDP action quality for action `u` in state `x`. Returns negated quality as an action selection cost.
* **Line 197–200:** `best_action_bias(x, v_pop)`: Returns 9-element action quality vector across all candidate actions.

```
Lines 201–278: Network Diagnostics & Verification Helpers
```
* **Line 201–277:** Diagnostic functions and diagnostic script execution helpers verifying STDP weight evolution.
* **Line 278:** End of file.

---

# CHAPTER 6: `brain/carl_physarum.py`
### *Slime-Mold Flow Network Path Optimizer (256 Lines)*

This module implements the *Physarum polycephalum* slime-mold pathfinding algorithm based on Tero, Kobayashi & Nakagaki (2007, *Science*). It models the maze as a network of fluid tubes where high-flow tubes thicken and unused tubes shrink, provably converging to the shortest path around obstacles.

```
Lines 1–17: Constants & Setup
```
* **Line 1–7:** Module docstring describing Physarum shortest-path tube adaptation mechanics.
* **Line 8:** Imports `numpy`.
* **Line 9–10:** Imports `scipy.sparse` and `spsolve` for sparse matrix linear equations.
* **Line 13:** `MU = 1.8` — Tube reinforcement exponent ($1 < \mu < 2$ guarantees mathematical convergence).
* **Line 14:** `TAU = 80.0` — Conductivity adaptation time constant (80 steps).
* **Line 15:** `D_MIN = 1e-5` — Minimum tube conductivity floor (prevents network disconnection).
* **Line 16:** `D_MAX = 50.0` — Maximum tube conductivity ceiling.

```
Lines 18–46: PhysarumMaze Class Setup
```
* **Line 19–25:** Class `PhysarumMaze`. Represents a $25 \times 25$ grid (625 total nodes) as a network of fluid tubes.
* **Line 26–29:** `__init__(self, rows=25, cols=25):` Stores grid dimensions $R=25, C=25, N=625$.
* **Line 32:** `D_h = np.ones((25, 24))` — Horizontal tube conductivities initialized to 1.0.
* **Line 34:** `D_v = np.ones((24, 25))` — Vertical tube conductivities initialized to 1.0.
* **Line 37:** `obstacle = np.zeros((25, 25), dtype=bool)` — Boolean grid map marking impassable obstacle cells.
* **Line 40:** `pressure = np.zeros(625)` — Fluid pressure field vector across all 625 nodes.
* **Line 43:** `nav_signal = np.zeros((25, 25))` — 2D navigation gradient map.
* **Line 45:** Initializes `_step_count = 0`.

```
Lines 47–98: Index Mapping & Sparse Kirchhoff Laplacian (`_build_laplacian`)
```
* **Line 48–52:** `_idx(i, j)` and `_pos(idx)`: Helper functions converting 2D grid coordinates $(i, j)$ to 1D flat index $N$ and vice versa.
* **Line 55–57:** `update_obstacles(CM_danger, danger_thresh=0.7)`: Marks grid cells with danger values $> 0.7$ as obstacles.
* **Line 60–97:** `_build_laplacian()`: Constructs sparse Kirchhoff/Laplacian matrix $L$ representing fluid flow conservation ($\sum Q_{in} = \sum Q_{out}$). Sets off-diagonal entries to $-D_{ij}$ and diagonal entries to sum of adjacent tube conductivities. Places $10^{-6}$ on isolated obstacle nodes to prevent matrix singularity.

```
Lines 99–144: Fluid Pressure Solver & Tube Adaptation
```
* **Line 99–116:** `_solve_pressure(src_idx, snk_idx)`: Sets boundary conditions (source pressure = 1.0 at start, sink pressure = 0.0 at destination). Solves linear system $L \cdot p = b$ using `scipy.sparse.linalg.spsolve`. Clamps pressure field `p` to $[0.0, 1.0]$.
* **Line 117–144:** `_update_conductivities()`: Updates tube conductivities based on fluid flux $Q = D \cdot |\Delta p|$. Applies adaptation equation: $\Delta D = (Q^\mu - D) / \tau$. Thicken tubes with high flow; shrinks tubes with zero flow. Zeroes out conductivities for obstacle edges.

```
Lines 145–203: Navigation Signal & Main Update Step (`step`)
```
* **Line 145–165:** `_compute_nav_signal()`: Computes navigation signal at each cell by summing edge flux pointing toward lower pressure (toward destination). Normalizes signal matrix to $[0, 1]$.
* **Line 167–203:** `step(src_cell, snk_cell, CM_danger=None, every=1)`: Executes one Physarum cycle. Updates obstacle mask, solves pressure field between `src_cell` and `snk_cell`, resets active conductivities to 1.0 to prevent dead-tube lock-in, zeroes out obstacle edges, and recomputes navigation signal map.

```
Lines 204–256: Gradient Navigation & World Coordinate Heading
```
* **Line 205–227:** `best_move(cur_cell, src_cell, snk_cell)`: Finds the best adjacent cell by following the steepest pressure drop ($\min p_{neighbor}$). Guarantees zero local minima and obstacle avoidance.
* **Line 229–252:** `get_heading(xw, yw, goal_xw, goal_yw, MAP_XMIN, MAP_XMAX, MAP_YMIN, MAP_YMAX)`: Converts world coordinates $(x_w, y_w)$ into grid coordinates, computes `best_move`, converts target grid cell back to world coordinates, and returns target heading angle $\arctan2(\Delta y, \Delta x)$ in radians.
* **Line 254–256:** `path_strength()`: Returns the 90th percentile of tube conductivities as a metric of path connectivity.
* **Line 257:** End of file.

---

### End of Volume 1
Volume 1 covers the core **Cognitive & Pathfinding Subsystems** (Chapters 1–6).
