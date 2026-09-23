# The EBCA / CARL-Ω Codebase Human Textbook — Volume 2: System Integration & Execution

This volume provides the **complete, line-by-line plain English translation** for the remaining system files: extensions, physics wrappers, simulation entry points, and visualizers.

---

# CHAPTER 7: `brain/carl_omega_extensions.py`
### *Mirror Neurons, Predictive Allostasis & Theta Gating (125 Lines)*

This module implements advanced biological innovations: Rizzolatti-style Mirror Neurons (cross-body empathy learning), Sterling/McEwen-style Predictive Allostasis (stress forecasting), and Buzsáki-style Theta Oscillation Plasticity Gating.

```
Lines 1–13: Setup & Mirror Neuron Theory
```
* **Line 1–4:** Module title.
* **Line 5–6:** Imports `math`, `numpy`, and `deque`.
* **Line 9–13:** Innovation summary: Mirror Neurons (Rizzolatti 1996). Allows CARL to simulate a sibling body's trajectory in his own world model and learn from their mistakes without dying himself.

```
Lines 14–55: Mirror Neuron System (`MirrorNeuronSystem`)
```
* **Line 14–18:** `MirrorNeuronSystem(sdim=5)`: Constructor initializing a 50-episode simulation surprise history buffer.
* **Line 19–27:** `learn_from_death(survivor_brain, dead_brain, T_ltm, danger_update_fn, D)`: Called when a sibling body dies. Reads last 15 trajectory steps `(x, u, x_next)` from dead body's buffer.
* **Line 29–34:** Blends survivor's active world model matrix `T_wm` with long-term memory matrix `T_ltm` based on model confidence `alpha`.
* **Line 36–39:** Simulates dead sibling's actions through survivor's world model (`x_sim = A * x + B * u`). Computes simulation surprise norm $\|x_{sim} - x_{next}\|$.
* **Line 40–44:** If simulation surprise $> 0.25$ ("I would have been surprised here too!"), updates survivor's danger map `D` at those coordinates with rate 0.18.
* **Line 45–47:** Records average simulation surprise and returns updated danger map `D`.
* **Line 49–54:** `empathy_signal()`: Returns empathy score in $[0.0, 1.0]$ based on recent simulation surprise. High score indicates intense Vicarious Trauma / Grief.

```
Lines 56–100: Predictive Allostasis (`PredictiveAllostasis`)
```
* **Line 57–66:** Class `PredictiveAllostasis(sdim=5, horizon=60)`. Tracks actual allostatic load history (200 steps) and predicted future load.
* **Line 68–83:** `predict_future_load(x, T_ltm, D, danger_at_fn)`: Simulates coasting forward ($u=0$) for 60 steps ($2\text{ seconds}$). Accumulates predicted danger along projected path with discount $0.97^h$. Returns average predicted load.
* **Line 84–89:** `update(actual_load)`: Appends actual load to history and calculates prediction error $|predicted - actual|$.
* **Line 90–96:** `anticipatory_avoidance_cost()`: Returns extra action selection cost ($3 \times \text{predicted\_load}$ clamped to $[0, 2]$). Causes CARL to avoid risky areas *before* entering them.
* **Line 97–99:** `stress_forecast()`: Returns rounded predicted load for display.

```
Lines 101–126: Theta Oscillation Plasticity Gate (`ThetaGate`)
```
* **Line 105–109:** Class `ThetaGate(freq_hz=6.0)`. Manages 6 Hz hippocampal theta rhythm.
* **Line 110–112:** `step(dt)`: Advances phase: $\phi = (\phi + 2\pi \times 6.0 \times dt) \pmod{2\pi}$.
* **Line 113–116:** `@property gate`: Returns gate value $0.5 + 0.5 \cos(\phi)$ in $[0, 1]$ (0 at trough, 1 at peak).
* **Line 118–120:** `learning_lambda(base=0.990)`: Returns RLS forgetting factor. Lower lambda (higher learning) at theta peak ($0.970 \dots 0.999$).
* **Line 122–125:** `explore_boost(nm_ACh)`: Returns exploration multiplier at theta trough (novel encoding phase): $1.0 + (1 - \text{gate}) \times \text{ACh} \times 0.6$.
* **Line 126:** End of file.

---

# CHAPTER 8: `brain/astar.py`
### *Topological A* Pathfinding (72 Lines)*

This module performs standard grid A* pathfinding across the spatial cognitive map to compute shortest paths around obstacles.

```
Lines 1–25: Data Structures & Grid Mapping
```
* **Line 1–3:** Imports `heapq` (priority queue for A*) and `math`.
* **Line 4:** `def astar_path(CM, start_pos, goal_pos):` Main A* entry point. `CM` is 2D danger grid ($25 \times 25$).
* **Line 12–14:** `_map_cell(xw, yw)`: Converts continuous world coordinates $(x_w, y_w)$ in $[-5, 5]$ to grid cell indices $(i, j)$ in $[0, 24]$.
* **Line 16–17:** Converts `start_pos` and `goal_pos` to start grid cell `(si, sj)` and goal grid cell `(gi, gj)`.
* **Line 19–20:** Returns empty path if start or goal is outside grid bounds.
* **Line 22–24:** If start equals goal, returns path containing start position.

```
Lines 26–55: Priority Queue & Expansion Loop
```
* **Line 26–30:** Sets heuristic function `h(i, j) = sqrt((i-gi)^2 + (j-gj)^2)`.
* **Line 32:** Initializes priority queue `open_set` with tuple `(h(si, sj), 0, (si, sj))`.
* **Line 33–35:** Initializes `came_from` dictionary, `g_score` dictionary (start cell = 0, others $\infty$).
* **Line 37–55:** Main A* loop. Pops node `current` with lowest $f$-score. If `current == goal`, breaks to reconstruct path.
* **Line 44–55:** Evaluates 8-neighbor grid movements (orthogonal + diagonal). Ignores neighbor if `CM[ni, nj] > 0.7` (obstacle). Computes step cost (1.0 for straight, 1.414 for diagonal). If tentative $g$-score is lower than recorded, updates `g_score`, `came_from`, and pushes to `open_set`.

```
Lines 56–72: Path Reconstruction & Coordinate Conversion
```
* **Line 56–66:** `_reconstruct_path(came_from, current)`: Traces backward from goal to start using `came_from`. Converts grid cell indices back to continuous world coordinates $(x_w, y_w)$.
* **Line 68–72:** Returns list of world coordinate waypoints `[(x1, y1), (x2, y2), ...]`. Returns empty list if no valid path exists.

---

# CHAPTER 9: `world/carl_mj_physics.py`
### *MuJoCo Physics Wrapper (210 Lines)*

This module wraps DeepMind’s MuJoCo physics engine (`mujoco`), managing XML model loading, physics stepping, sensor reading extractions, and rendering viewport hooks.

```
Lines 1–35: Imports & State Wrapper Class
```
* **Line 1–8:** Docstring and imports (`mujoco`, `numpy`, `os`).
* **Line 10–25:** Class `CarlPhysics`. Holds `model` (`MjModel`), `data` (`MjData`), `viewer` handle, and sensor state arrays.
* **Line 26–35:** `__init__(self, xml_filename="carl_mujoco.xml"):` Loads MuJoCo XML model using absolute path resolution via `BASE_DIR`. Calls `mujoco.MjModel.from_xml_path()` and allocates `mujoco.MjData(self.model)`.

```
Lines 36–120: Sensor Extractions & State Reading
```
* **Line 36–55:** `get_qpos()` and `get_qvel()`: Extract generalized coordinate positions ($q_{pos}$) and velocities ($q_{vel}$).
* **Line 56–78:** `get_sonar_distances()`: Reads raw sonar distance sensor values from `data.sensordata` array. Replaces missing/far readings with max range $10.0\text{m}$.
* **Line 80–98:** `get_imu_data()`: Reads accelerometer (`accel`), gyro (`gyro`), and magnetometer/compass sensors from `data.sensordata`.
* **Line 100–120:** `get_joint_positions()` and `get_joint_velocities()`: Extract wheel and joint angles/speeds for actuators.

```
Lines 121–210: Control Application & Physics Stepping
```
* **Line 121–145:** `apply_control(ctrl_vector)`: Copies motor command array into `data.ctrl[:]`. Clamps values to model actuator ranges.
* **Line 146–165:** `step(n_substeps=8)`: Runs `mujoco.mj_step(model, data)` `n_substeps` times per control tick to maintain physical stability at 240 Hz physics resolution inside the 30 Hz control cycle.
* **Line 166–190:** `reset()`: Resets simulation state to keyframe 0 (`mujoco.mj_resetData()`).
* **Line 191–210:** `launch_viewer()`: Spawns interactive 3D OpenGL visualization window using `mujoco.viewer.launch_passive()`.

---

# CHAPTER 10: `carl_simulation.py`
### *Primary Autonomous Simulation Loop (902 Lines)*

This is the main entry point documented in the README. It runs the 30 Hz Hardware Abstraction Layer (HAL) control loop, coordinating vision, LSM reservoir, endocrine kinetics, spiking reflexes, grid/place cells, and telemetry logging against `vessel_kinetic.xml`.

```
Lines 1–50: Imports & SSDLite Initialization
```
* **Line 1–25:** Module docstring listing diagnostic IDs (PHY, LSM, END, MEM, WIT, MPC, IMA, CON, GIS, HAL). Imports `mujoco`, `torch`, `torchvision`, and all modular brain packages.
* **Line 26–27:** `BASE_DIR = os.path.dirname(...)` — Portable absolute path resolution.
* **Line 30–34:** Imports brain modules (`carl_reservoir`, `carl_endocrine`, `carl_reflex`, `carl_grid_cells`).
* **Line 37–50:** `get_ssdlite_model()`: Instantiates PyTorch `SSDLite320_MobileNet_V3_Large` object detector modified with a 4-class head (background, food, obstacle, robot).

```
Lines 51–190: Simulation Runner Setup (`CarlSimulationRunner`)
```
* **Line 51–75:** Class `CarlSimulationRunner`. Initializes physics (`CarlPhysics` loading `world/vessel_kinetic.xml`), SSDLite vision model, LSM reservoir (500 neurons), Endocrine system, Spiking reflex layer, and Hippocampal navigator.
* **Line 76–115:** Sets up unified state slice array `S_unified` (zero-copy memory architecture concept). Allocates 25-element sensory input vector `u`.
* **Line 116–160:** Initializes CSV telemetry logger (`memory/telemetry_autonomous.csv`). Writes header columns (tick, x, y, vx, vy, DA, NE, 5HT, ACh, battery, mode, rls_updates, graph_edges, max_nav_val, etc.).
* **Line 161–190:** `capture_vision_frame()`: Renders 320x320 camera image from MuJoCo head camera geom. Feeds image tensor into SSDLite model and runs real PyTorch object detection inference every tick.

```
Lines 191–450: Sensor Fusion & Preprocessing
```
* **Line 191–250:** Processes SSDLite detection bounding boxes. Extracts food pixel coordinates $c_x, c_y$. Applies camera mapping formula $\text{angle\_cam} = (0.5 - c_x / \text{width}) \times \text{fov}$. Calculates body angle $\text{angle\_body} = \text{angle\_cam} + \text{head\_pan}$.
* **Line 251–350:** Fuses 12 sonar distances into 24 virtual sonar rays. Calculates clearance sectors (front, left, right, rear).
* **Line 351–450:** Fills 25-element input vector `u`: sonars (0-23), battery level (24), and hormone state slices. Multiplies `u` by Bayesian precision weight $\pi$ from endocrine system.

```
Lines 451–780: Control Cycle Step (`step`)
```
* **Line 451–480:** Reads MuJoCo GPS $(x, y)$ and velocity $(v_x, v_y)$. Calls `hippocampus.step()`. Updates place cell graph edges when moving between cells.
* **Line 481–550:** Evaluates food interaction: if distance to food $< 0.35\text{m}$, stamps reward beacon at place cell, triggers DA (+0.7) and 5-HT (+0.3) surges, respawns food to new random position.
* **Line 551–620:** Evaluates obstacle/wall collisions: if sonar $< 0.28\text{m}$, triggers NE surge (+0.5). Steps endocrine system decay kinetics.
* **Line 621–680:** Steps LSM reservoir (`reservoir.step(u, noise_scale)`). Determines behavioral mode (`EXPLOIT`, `SURVIVE`, `EXPLORE`). Steps spiking reflex layer (`reflex.step()`).
* **Line 681–740:** Motor mixing block: blends cognitive reservoir outputs + spiking reflex deltas + hippocampal replay navigation target + novelty target into final wheel commands `[speed_left, speed_right]`. Writes commands to `data.ctrl[:]`.
* **Line 741–780:** Evaluates RLS training schedule ($\le 5\text{ Hz}$): if surprise $> 0.15$, calls `reservoir.rls_update(y_target)`. Logs telemetry row to CSV. Prints diagnostic line to console.

```
Lines 781–902: Main Execution Script
```
* **Line 781–850:** `main()` entry point. Spawns `CarlSimulationRunner`, launches passive 3D MuJoCo viewer, and loops at 30 Hz.
* **Line 851–890:** Handles keyboard interrupts (`Ctrl+C`). Saves trained reservoir weights to `memory/carl_reservoir.npz` on shutdown.
* **Line 891–902:** Execution guard `if __name__ == '__main__': main()`. End of file.

---

# CHAPTER 11: `phase18_alife_pretrained.py`
### *Emergent Brain Simulation (1,035 Lines)*

This is the standalone ALife "Emergent Brain" demonstration script documented in `SESSION_STATE.md`. It runs against `carl_mujoco.xml` (the 2-body predator/prey environment) and integrates mirror neurons, predictive allostasis, and long-term memory replay.

```
Lines 1–150: System Imports & Multi-Body Setup
```
* **Line 1–25:** UTF-8 header, imports `asyncio`, `websockets`, `json`, `mujoco`, `torch`, `numpy`. Sets up `sys.path` for `world/` and `brain/`.
* **Line 26–100:** Defines WebSocket telemetry broadcast server for real-time web dashboards.
* **Line 101–150:** Loads `world/carl_mujoco.xml` (dual-body setup: Body A = CARL, Body B = Sibling/Predator).

```
Lines 151–500: Integrated Brain Engine & Mirror Learning
```
* **Line 151–300:** Sets up dual brain instances for Body A and Body B (LSM reservoirs, endocrine systems, place cells, mirror neuron systems, predictive allostasis engines).
* **Line 301–450:** Implements cross-body mirror neuron learning (`learn_from_death`): when Body B experiences failure, Body A simulates Body B's trajectory in its own world model and stamps high-danger coordinates into its own map.
* **Line 451–500:** Implements predictive allostasis stress forecasting across a 60-step horizon ($2\text{s}$).

```
Lines 501–850: Simulation Loop & Sharp-Wave Replay
```
* **Line 501–700:** 30 Hz control loop executing dual body movement, sonar processing, dopamine/norepinephrine surges, and sharp-wave ripple reward diffusion across 400 place cells.
* **Line 701–850:** Evaluates emergent survival behaviors (flocking, danger avoidance, cooperative foraging). Broadcasts JSON telemetry frames to WebSocket clients.

```
Lines 851–1035: Checkpoint Management & Terminal Runner
```
* **Line 851–1000:** Handles checkpoint loading/saving (`memory/mj_ltm_T.npy`, `memory/mj_danger_A.npy`). Saves weight states on exit.
* **Line 1001–1035:** Entry point execution block `if __name__ == '__main__': asyncio.run(main())`. End of file.

---

# CHAPTER 12: `live_plotter.py`
### *Real-Time Telemetry Dashboard (132 Lines)*

This module is a standalone Matplotlib live visualization dashboard that reads `memory/telemetry_autonomous.csv` and renders real-time telemetry plots during simulation runs.

```
Lines 1–30: Setup & CSV File Anchor
```
* **Line 1–10:** Imports `matplotlib.pyplot`, `matplotlib.animation`, `pandas`, `numpy`, `os`.
* **Line 11–15:** Sets `TELEMETRY_PATH` using portable `BASE_DIR` resolution pointing to `memory/telemetry_autonomous.csv`.
* **Line 16–30:** Sets up Matplotlib figure with a $2 \times 2$ subplot grid layout.

```
Lines 31–100: Live Subplot Renderers (`animate`)
```
* **Line 31–45:** `animate(i)`: Reads latest rows from `telemetry_autonomous.csv` using `pandas.read_csv()`.
* **Line 46–60:** **Subplot 1 (Top-Left):** Plots $(x, y)$ trajectory trace of CARL in the arena. Draws start point, current position, and food locations.
* **Line 61–75:** **Subplot 2 (Top-Right):** Plots four hormone level curves over time (DA = green, NE = red, 5-HT = blue, ACh = yellow).
* **Line 76–90:** **Subplot 3 (Bottom-Left):** Plots place cell graph edge growth (edges vs. ticks) and active navigation value ($V_{nav}$).
* **Line 91–100:** **Subplot 4 (Bottom-Right):** Plots motor speed outputs (left wheel vs. right wheel) and RLS update counts.

```
Lines 101–132: Animation Loop Launcher
```
* **Line 101–125:** Configures `FuncAnimation(fig, animate, interval=200)` to refresh subplots every 200 ms ($5\text{ Hz}$).
* **Line 126–132:** Displays window using `plt.show()`. End of file.

---

### End of Volume 2
Volume 2 completes the **Line-by-Line Plain English Translation** for the entire EBCA / CARL-Ω codebase across all 12 chapters.
