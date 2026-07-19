# Walkthrough: `live_plotter.py`
### *Real-Time Telemetry Dashboard (132 Lines)*

This module is a standalone Matplotlib live visualization dashboard that reads `memory/telemetry_autonomous.csv` and renders real-time telemetry plots during simulation runs.

---

## 1. Setup & CSV Anchor
* **Lines 1–10:** Imports `matplotlib.pyplot`, `matplotlib.animation`, `pandas`, `numpy`, and `os`.
* **Lines 11–15:** Sets `TELEMETRY_PATH` using portable `BASE_DIR` absolute resolution pointing to `memory/telemetry_autonomous.csv`.
* **Lines 16–30:** Sets up Matplotlib figure with a $2 \times 2$ subplot grid layout.

---

## 2. Live Subplot Renderers (`animate`)
* **Lines 31–45:** `animate(i)`: Reads latest telemetry rows from `telemetry_autonomous.csv` using `pandas.read_csv()`.
* **Lines 46–60:** **Subplot 1 (Top-Left):** Plots $(x, y)$ trajectory trace of CARL in the arena. Draws start position, current position, and food locations.
* **Lines 61–75:** **Subplot 2 (Top-Right):** Plots four hormone level curves over time (DA = green, NE = red, 5-HT = blue, ACh = yellow).
* **Lines 76–90:** **Subplot 3 (Bottom-Left):** Plots place cell graph edge growth (edges vs. ticks) and active navigation value ($V_{nav}$).
* **Lines 91–100:** **Subplot 4 (Bottom-Right):** Plots motor speed outputs (left wheel vs. right wheel) and RLS update counts.

---

## 3. Animation Loop Launcher
* **Lines 101–125:** Configures `FuncAnimation(fig, animate, interval=200)` to refresh subplots every 200 ms ($5\text{ Hz}$).
* **Lines 126–132:** Displays window using `plt.show()`. End of file.
