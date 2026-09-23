# Walkthrough: `phase18_alife_pretrained.py`
### *Emergent Brain Simulation (1,035 Lines)*

This is the standalone ALife "Emergent Brain" demonstration script documented in `SESSION_STATE.md`. It runs against `carl_mujoco.xml` (the 2-body predator/prey environment) and integrates mirror neurons, predictive allostasis, and long-term memory replay.

---

## 1. System Setup & WebSocket Broadcasting
* **Lines 1–25:** UTF-8 header, imports `asyncio`, `websockets`, `json`, `mujoco`, `torch`, `numpy`. Configures `sys.path` to include `world/` and `brain/`.
* **Lines 26–100:** Sets up WebSocket server broadcasting real-time JSON telemetry frames to web dashboards.
* **Lines 101–150:** Loads `world/carl_mujoco.xml` (dual-body setup: Body A = CARL, Body B = Sibling/Predator).

---

## 2. Integrated Brain Engine & Mirror Learning
* **Lines 151–300:** Instantiates dual brain modules for Body A and Body B (LSM reservoirs, endocrine systems, place cells, mirror neuron systems, predictive allostasis engines).
* **Lines 301–450:** Implements cross-body mirror neuron learning (`learn_from_death`): when Body B fails/dies, Body A simulates Body B's trajectory in its own world model and stamps high-danger coordinates into its map.
* **Lines 451–500:** Implements predictive allostasis stress forecasting across a 60-step horizon ($2\text{s}$).

---

## 3. Simulation Loop & Sharp-Wave Replay
* **Lines 501–700:** 30 Hz control loop executing dual body movement, sonar processing, dopamine/norepinephrine surges, and sharp-wave ripple reward diffusion across 400 place cells.
* **Lines 701–850:** Evaluates emergent survival behaviors (flocking, danger avoidance, cooperative foraging). Broadcasts JSON telemetry frames to WebSocket clients.

---

## 4. Checkpoint Management & Terminal Runner
* **Lines 851–1000:** Handles checkpoint loading/saving (`memory/mj_ltm_T.npy`, `memory/mj_danger_A.npy`). Saves weight states on exit.
* **Lines 1001–1035:** Entry point execution block `if __name__ == '__main__': asyncio.run(main())`.
