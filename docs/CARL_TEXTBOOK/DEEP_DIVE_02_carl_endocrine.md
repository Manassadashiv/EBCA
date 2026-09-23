# 🔬 DEEP DIVE #2 — `carl_endocrine.py` (Every Line, Every Number, Every Why)
> *188 lines. Zero skipped. Every constant, every formula, every biological reference explained.*

---

## FILE PURPOSE

This is CARL's **neuromodulatory hormone system** — four chemicals (dopamine, norepinephrine, serotonin, acetylcholine) that continuously change how CARL perceives, learns, and decides. These are not just labels — each chemical has exact mathematical kinetics modeled on real biology.

**Why does a robot need hormones?** Because the same inputs (obstacle at 50cm) should cause DIFFERENT responses depending on the robot's internal state (hungry vs. full, calm vs. panicked). Hormones provide this **context-dependent behavioral modulation** without needing a lookup table for every possible situation.

---

## LINE-BY-LINE BREAKDOWN

---

### Lines 1–4: Module Docstring

```python
"""
carl_endocrine.py — Neuromodulatory Endocrine Kinetics (END-201..204)
Integrated into unified SoC state slices.
"""
```

`END-201..204`: Diagnostic tracking codes for the four neuromodulators.
"SoC state slices": System-on-Chip design pattern — the unified memory array `S_unified` has "slices" (views) for each subsystem.

---

### Line 5: `import numpy as np`

```python
import numpy as np
```

Used for `np.clip()` (clamping values), `np.clip()`, and array operations. See DEEP_DIVE_01 for why numpy.

---

### Lines 8–26: Class Constants

```python
class EndocrineSystem:
    BASELINE_DA  = 1.0    # Dopamine resting level
    BASELINE_NE  = 0.1    # Norepinephrine resting level
    BASELINE_SHT = 0.8    # Serotonin resting level
    BASELINE_ACH = 0.5    # Acetylcholine resting level
```

These are **class-level constants** (not instance variables) — defined once for the whole class, not per instance. Used in the `step()` decay formula.

**Why `DA = 1.0`?** Dopamine is the reward/motivation signal. Baseline 1.0 means "normal reward expectation." When reward happens (food eaten), DA spikes above 1.0. The learning algorithms treat DA > 1.0 as "positive reward" and DA < 1.0 as "negative." Having baseline at 1.0 (not 0) means we always have SOME motivation — never completely inert.

**Why `NE = 0.1`?** Norepinephrine (adrenaline equivalent) is the **alertness/threat response** hormone. At rest, 0.1 is very low — CARL is calm. When danger (obstacle) is detected, it surges to 0.4-0.8. This represents a 4-8× increase from baseline, matching the biological "sympathetic nervous system activation" ratio.

**Why `SHT = 0.8`?** Serotonin = calm/satiation. Starting at 0.8 (moderately high) means CARL begins in a calm, satiated state — not desperately hungry. Serotonin acts as a **behavioral inhibitor**: high 5-HT suppresses food-seeking urgency.

**Why `ACH = 0.5`?** Acetylcholine = attention/plasticity. At 0.5 (moderate), CARL is paying moderate attention. In novel environments, ACh surges boost attention and learning rate.

---

```python
    DECAY_DA  = 2.0   # Dopamine decay rate constant
    DECAY_NE  = 3.0   # Norepinephrine decay rate (fastest)
    DECAY_SHT = 1.0   # Serotonin decay rate (slowest)
    DECAY_ACH = 2.5   # Acetylcholine decay rate
```

These are the **first-order decay rate constants** in the ODE:
```
dX/dt = -k × (X - X_baseline)
```

**Higher k = faster decay to baseline.**

Why these specific rates?
- **NE = 3.0 (fastest)**: Adrenaline/panic is a SHORT-LIVED response. Your adrenaline spike from a fright lasts ~10-30 seconds. Biologically, NE has a half-life of ~2-3 minutes in the synapse. In CARL's 33ms timescale, 3.0 means NE returns to baseline within ~5 ticks (165ms) after a small surge.
- **SHT = 1.0 (slowest)**: Serotonin changes slowly. Post-meal satiation lasts for HOURS in biology. In CARL, 1.0 means serotonin is the most persistent modulator.
- **DA = 2.0**: Dopamine reward signals are transient but longer-lasting than adrenaline. Medium decay.
- **ACH = 2.5**: Acetylcholine fluctuates fairly quickly with attentional state.

**Discrete-time decay formula per timestep (dt=0.033s):**
```
X_new = X_old + (-DECAY × (X_old - BASELINE)) × dt
       = X_old × (1 - DECAY × dt) + BASELINE × DECAY × dt
```
At `dt=0.033` and `DECAY_NE=3.0`:
```
NE_new = NE_old + (-3.0 × (NE_old - 0.1)) × 0.033
       = NE_old × (1 - 0.099) + 0.1 × 0.099
       = NE_old × 0.901 + 0.0099
```
So each tick NE loses ~10% of its deviation from baseline. A surge to NE=0.5 returns to baseline NE=0.1 in approximately `log(0.4/0.01) / 0.099 / 30 ≈ 12 seconds`.

---

```python
    PI_0      = 1.0    # Base precision weight
    GAMMA_ACH = 0.6    # ACh influence on precision
    GAMMA_NE  = 0.4    # NE influence on precision
    GAMMA_SHT = 0.3    # 5-HT influence on precision (inhibitory)

    MAX_NM = 3.0       # Maximum neuromodulator level
    MIN_NM = 0.0       # Minimum (can't be negative)
```

**Precision parameters:** These shape the `get_precision_weight()` formula (explained below).

**`GAMMA_ACH = 0.6` (highest)**: ACh has the strongest boosting effect on precision. Biologically, acetylcholine is the PRIMARY attention neuromodulator — high ACh = sharp focus. So it gets the largest coefficient.

**`GAMMA_NE = 0.4`**: Norepinephrine also boosts attention (fight-or-flight sharpens perception). Smaller coefficient than ACh because NE's main role is behavioral activation, not sensory precision per se.

**`GAMMA_SHT = 0.3` (inhibitory)**: Serotonin REDUCES precision weight. High serotonin = satiated calm state = rely more on internal models (habits/priors) and less on sensors. The negative sign in the formula (`- GAMMA_SHT × SHT`) reduces the overall precision.

**`MAX_NM = 3.0`**: Maximum 3× baseline. Prevents runaway accumulation from multiple rapid surges.

**`MIN_NM = 0.0`**: Neuromodulators can't go negative (no "negative dopamine"). Zero = complete absence of the chemical.

---

### Lines 27–34: Constructor

```python
def __init__(self):
    self.DA  = self.BASELINE_DA   # 1.0
    self.NE  = self.BASELINE_NE   # 0.1
    self.SHT = self.BASELINE_SHT  # 0.8
    self.ACh = self.BASELINE_ACH  # 0.5
    self.reward_avg = 0.0          # Running average of dopamine (for RPE)
    self.reward_avg_alpha = 0.01   # Smoothing factor for running average
    self.last_surge_event = ""     # String log of most recent surge (for telemetry)
```

**`self.reward_avg = 0.0`**: The running average of dopamine, used to compute **Reward Prediction Error (RPE)**. Starts at 0 so the first few ticks might show large RPE — this is fine, CARL needs to "calibrate" what normal feels like.

**`self.reward_avg_alpha = 0.01`**: Exponential moving average decay. 1% update per tick means the average smooths over ~100 ticks (~3 seconds). This is the "recent past" window for what counts as "expected" reward.

**`self.last_surge_event = ""`**: A human-readable string like `"DA+0.35"` or `"NE+0.40"` that gets logged in the telemetry CSV. Useful for debugging — lets you see exactly when and why hormones were triggered.

---

### Lines 36–54: `step()` — Per-Tick Decay

```python
def step(self, dt: float = 0.033):
    self.DA  += -self.DECAY_DA  * (self.DA  - self.BASELINE_DA)  * dt
    self.NE  += -self.DECAY_NE  * (self.NE  - self.BASELINE_NE)  * dt
    self.SHT += -self.DECAY_SHT * (self.SHT - self.BASELINE_SHT) * dt
    self.ACh += -self.DECAY_ACH * (self.ACh - self.BASELINE_ACH) * dt
```

**This is Euler integration of a first-order linear ODE:**

The ODE (continuous):
```
dX/dt = -k × (X - X_baseline)
```

The exact solution is: `X(t) = X_baseline + (X_0 - X_baseline) × e^(-k × t)`

But we use **Forward Euler** (simplest numerical integration):
```
X(t+dt) = X(t) + f(X(t)) × dt
         = X(t) + (-k × (X(t) - X_baseline)) × dt
```

**Why Forward Euler instead of exact exponential?** With very small `dt=0.033` and moderate `k` (1-3), Euler is stable and accurate enough. The error per step is `O(dt²)` = `(0.033)² ≈ 0.001` = 0.1%. Acceptable. More accurate methods (Runge-Kutta) would be overkill for this smoothness requirement.

**Numerical check (NE example):**
- `DECAY_NE = 3.0`, `BASELINE_NE = 0.1`, `dt = 0.033`
- If `NE = 0.5` (after a surge):
  ```
  NE += -3.0 × (0.5 - 0.1) × 0.033 = -3.0 × 0.4 × 0.033 = -0.0396
  NE_new = 0.5 - 0.0396 = 0.4604
  ```
- Each tick, deviation from baseline (0.4) shrinks by `3.0 × 0.033 = 9.9%`.
- Half-life: `0.693 / 3.0 = 0.231 seconds` = 7 ticks.

---

```python
    self.DA  = np.clip(self.DA,  self.MIN_NM, self.MAX_NM)
    self.NE  = np.clip(self.NE,  self.MIN_NM, self.MAX_NM)
    self.SHT = np.clip(self.SHT, self.MIN_NM, self.MAX_NM)
    self.ACh = np.clip(self.ACh, self.MIN_NM, self.MAX_NM)
```

**`np.clip(value, min, max)`** on scalars: Clamps to [0.0, 3.0]. After any operation, neuromodulators stay within physical bounds. Without clipping, multiple rapid surges could push DA to 5, 10, causing mathematically valid but biologically absurd behavior.

**Why `np.clip` on scalars?** It works on single floats too. It's equivalent to `max(MIN_NM, min(MAX_NM, value))` but cleaner.

---

### Lines 56–98: Surge Functions

```python
def surge_da(self, amount: float = 0.35):
    self.DA += amount
    self.last_surge_event = f"DA+{amount:.2f}"
```

**Why `+= amount`?** Hormones **add to current level**, not set it. Multiple rapid surges accumulate (until clipped at 3.0). This models biological receptor saturation — if you eat two pieces of food quickly, dopamine is higher than after one piece.

**`f"DA+{amount:.2f}"`**: Python f-string formatting. `{amount:.2f}` formats `amount` as 2 decimal places. Creates strings like `"DA+0.35"` for the telemetry log.

**Why `amount=0.35` default?** 0.35 above baseline of 1.0 brings DA to 1.35 — a 35% increase. This is a **moderate reward signal**, appropriate for finding food at a distance. For actual eating, `surge_da(0.7)` is called — a stronger 70% spike.

---

```python
def surge_ne(self, amount: float = 0.4):
    self.NE += amount
    self.last_surge_event = f"NE+{amount:.2f}"
```

**Why `amount=0.4` default?** Starting at NE=0.1 baseline, +0.4 brings NE to 0.5 — a 5× spike. In biology, threatening stimuli cause 3-10× NE increase. 0.4 (5×) is a strong alerting signal appropriate for obstacle collision.

Calling `surge_ne(0.2)` for distant obstacles (farther threat = smaller signal), `surge_ne(0.5)` for wall contacts (immediate threat = larger signal).

---

```python
def surge_sht(self, amount: float = 0.15):
    self.SHT += amount
    self.last_surge_event = f"5HT+{amount:.2f}"
```

**Why `amount=0.15` and smaller than others?** Serotonin changes slowly and has a low baseline `DECAY_SHT=1.0`. Even small additions accumulate over slow decay. A 0.15 surge + 0.8 baseline = 0.95, nearly at the 1.0 comfortable satiation level.

---

```python
def surge_ach(self, amount: float = 0.25):
    self.ACh += amount
    self.last_surge_event = f"ACh+{amount:.2f}"
```

**Why ACh is called:** In novel environments or when vision detects something new. ACh boosts sensory precision (makes sensors "louder") and accelerates Hebbian learning in the grid cell system.

---

### Lines 100–117: `get_precision_weight()` — Bayesian Sensory Weighting

```python
def get_precision_weight(self) -> float:
    pi = self.PI_0 * (
        1.0
        + self.GAMMA_ACH * self.ACh
        + self.GAMMA_NE  * self.NE
        - self.GAMMA_SHT * self.SHT
    )
    return max(0.1, pi)
```

**The formula:**
```
π = π₀ × (1 + γ_ACh × ACh + γ_NE × NE - γ_5HT × 5HT)
```

This is derived from **Bayesian Active Inference** (Karl Friston's framework). In this framework, the brain computes:
```
Perception = precision_weight × likelihood + (1 - precision) × prior
```
When precision is HIGH (π > 1): trust sensors more than internal predictions.
When precision is LOW (π < 1): trust internal models (habits/memory) more than sensors.

**Numerical example (normal state):**
```
π = 1.0 × (1 + 0.6×0.5 + 0.4×0.1 - 0.3×0.8)
  = 1.0 × (1 + 0.30 + 0.04 - 0.24)
  = 1.0 × 1.10
  = 1.10
```
Slightly above 1 — pays moderate attention to sensors.

**Numerical example (danger state: NE=0.8, ACh=0.7):**
```
π = 1.0 × (1 + 0.6×0.7 + 0.4×0.8 - 0.3×0.8)
  = 1.0 × (1 + 0.42 + 0.32 - 0.24)
  = 1.0 × 1.50
```
50% higher sensory weight — CARL pays sharp attention to every sensor reading during danger.

**Numerical example (satiated calm: SHT=2.5, NE=0.1):**
```
π = 1.0 × (1 + 0.6×0.5 + 0.4×0.1 - 0.3×2.5)
  = 1.0 × (1 + 0.30 + 0.04 - 0.75)
  = 1.0 × 0.59
```
Only 59% sensory weight — after a big meal, trusts habits/memory more.

**`return max(0.1, pi)`**: Floor at 0.1. Even in the most satiated, calm state, CARL still gives 10% weight to sensors. Never completely ignores the physical world.

---

### Lines 119–129: `get_exploration_noise_scale()`

```python
def get_exploration_noise_scale(self) -> float:
    return max(0.01, self.NE)
```

**Returns NE level directly as noise scale.**

In the Reservoir brain (`carl_reservoir.py`), exploration noise η is scaled by this value:
```
η ~ N(0, σ₀² × noise_scale)
```

**Why NE = noise scale?** The **locus coeruleus** is the brain region that produces norepinephrine. It's been shown (Aston-Jones & Cohen 2005) that NE gates between:
- **Low NE (exploitation):** Focused on current task, low noise, predictable behavior
- **High NE (exploration):** Broad stochastic search, high noise, tries new things

So high adrenaline (danger/novelty) = more random movement = explores escape routes. Low adrenaline (calm, food found) = precise, repeatable movements.

**`max(0.01, self.NE)`**: Floor at 0.01 so there's always a tiny bit of noise (motor jitter) even in the calmest state. Zero noise = completely deterministic = can get stuck in loops.

---

### Lines 131–147: `get_reward_prediction_error()`

```python
def get_reward_prediction_error(self) -> float:
    rpe = self.DA - self.reward_avg
    self.reward_avg += self.reward_avg_alpha * (self.DA - self.reward_avg)
    return rpe
```

**Reward Prediction Error (RPE)** — this is THE fundamental concept of dopamine neuroscience, confirmed by Wolfram Schultz in 1997 (Nobel-adjacent work).

**What RPE means:**
- `RPE > 0`: Actual reward (DA) > Expected reward (avg). **Better than expected.** → Learn: this situation is better than I thought.
- `RPE < 0`: DA < avg. **Worse than expected.** → Unlearn: this situation is not as good as I thought.
- `RPE = 0`: Exactly as expected. **No new information.** → Don't change weights.

**The exponential moving average update:**
```
reward_avg(t+1) = reward_avg(t) + α × (DA(t) - reward_avg(t))
```
- `α = 0.01`: Updates 1% toward current DA each tick. This makes `reward_avg` a smooth ~100-tick average.
- This is an **online algorithm** — no need to store all past DA values, just the running average.

**Why doesn't it just return `DA - BASELINE_DA`?** Because "baseline" is static. The RPE is relative to the RECENT history of rewards. If CARL has been eating food every 10 seconds, the running average will be elevated, and the RPE from another food will be smaller (less surprising). This matches real dopamine neuron behavior: reward learning adjusts expectations.

---

### Lines 149–161: `get_behavioral_mode()`

```python
def get_behavioral_mode(self, battery_level: float, food_visible: bool) -> str:
    if food_visible:
        return "EXPLOIT"           # Food in camera FOV → lock on and approach
    elif battery_level < 0.15 or self.NE > 2.0:
        return "SURVIVE"           # Critical hunger or extreme stress
    else:
        return "EXPLORE"           # Normal state → wander and map
```

**Three modes, priority-ordered:**

1. **EXPLOIT** (highest priority): If food is visible RIGHT NOW, ignore everything else and approach it. No internal state matters — food visibility overrides all.

2. **SURVIVE**: Two triggers:
   - `battery_level < 0.15`: Less than 15% battery = desperate. CARL must find food NOW. Initiates urgent replay-guided navigation to remembered food locations.
   - `self.NE > 2.0`: Extreme danger (NE at 20× baseline). Flee reflex dominates.
   
   **Why 15% battery threshold?** If battery drains at 0.0001/tick and capacity is 1.0, at 15% battery there are 1500 ticks remaining = 50 seconds. Enough time to navigate to remembered food IF action starts now.

3. **EXPLORE** (default): Battery OK, no food visible → wander the maze, build the map, seek novelty. This is the default state where the hippocampal system builds its cognitive map.

**Why this priority order?** Biological survival hierarchy: immediate reward > critical need > curiosity. Any other order would be suboptimal — you wouldn't prioritize wandering over eating when food is right in front of you.

---

### Lines 163–170: `get_hunger_drive()`

```python
def get_hunger_drive(self, battery_level: float) -> float:
    return float(np.clip(1.0 - battery_level, 0.0, 1.0))
```

**A simple linear mapping:** `hunger = 1 - battery`

| Battery | Hunger |
|---|---|
| 1.0 (full) | 0.0 (not hungry) |
| 0.5 (half) | 0.5 (moderately hungry) |
| 0.0 (dead) | 1.0 (starving) |

**Why linear?** Simple, interpretable, and spans the full range. Animals don't feel nothing until some threshold — hunger builds continuously as energy depletes.

**`np.clip(...)` to [0, 1]**: Battery could theoretically go slightly negative due to timing; clipping prevents nonsensical hunger values.

**`float()`**: Ensures a Python float is returned (not a numpy scalar), which plays nicely with Python arithmetic downstream.

---

### Lines 172–182: `get_replay_blend_weight()`

```python
def get_replay_blend_weight(self, battery_level: float, max_nav_value: float) -> float:
    hunger = self.get_hunger_drive(battery_level)
    signal_strength = float(np.clip(max_nav_value / 2.0, 0.0, 1.0))
    return float(np.clip(signal_strength * (0.3 + 0.7 * hunger), 0.0, 1.0))
```

**How much should CARL follow its memory map (hippocampal replay)?**

**`signal_strength = max_nav_value / 2.0`**:
- `max_nav_value` = the strongest reward gradient in the hippocampal place cell map
- Divided by 2.0 to normalize: nav values > 2.0 give full signal strength
- If `max_nav_value = 0` (no food ever found, no gradient): signal_strength = 0 → don't follow map

**`signal_strength × (0.3 + 0.7 × hunger)`**: The formula:
- **Base follow rate: 0.3**: Even at full battery (hunger=0), if a strong gradient exists, follow it mildly (30%). CARL is never completely ignoring its memory.
- **Hunger amplification: 0.7 × hunger**: As battery drops, increasingly follow the map urgently. At full hunger (hunger=1.0): coefficient = 0.3 + 0.7 = 1.0 = fully follow the memory map.

**Why 0.3 and 0.7?** They sum to 1.0 — when fully hungry, blend weight = signal_strength × 1.0 = pure replay navigation. At full battery, blend weight = signal_strength × 0.3 = light memory influence. The 30/70 split was chosen as a reasonable balance between curiosity-led exploration and memory-led exploitation.

---

### Lines 184–187: `__repr__()` — Debug Display

```python
def __repr__(self):
    return (f"DA={self.DA:.2f}, NE={self.NE:.2f}, "
            f"5HT={self.SHT:.2f}, ACh={self.ACh:.2f}, "
            f"pi={self.get_precision_weight():.2f}")
```

**`__repr__`**: Python's "official string representation" — shown when you `print(endocrine_object)`.

Used in the main simulation's console output:
```
[TICK   150] MODE:EXPLORE pos:(1.23,2.45) | DA=1.05, NE=0.12, 5HT=0.78, ACh=0.52, pi=1.10
```

**`:.2f`**: Format float to 2 decimal places. Sufficient precision for monitoring without cluttering the console.

---

## COMPLETE FORMULA REFERENCE

| Formula | Code | Meaning |
|---|---|---|
| `dX/dt = -k(X-X_b)` | `X += -DECAY*(X-BASELINE)*dt` | First-order decay to baseline |
| `π = π₀(1 + γ_ACh·ACh + γ_NE·NE - γ_5HT·5HT)` | `get_precision_weight()` | Bayesian sensory precision |
| `noise = NE` | `get_exploration_noise_scale()` | Noise ∝ norepinephrine |
| `RPE = DA - avg(DA)` | `get_reward_prediction_error()` | Temporal difference signal |
| `hunger = 1 - battery` | `get_hunger_drive()` | Linear depletion mapping |
| `blend = strength × (0.3 + 0.7 × hunger)` | `get_replay_blend_weight()` | Memory navigation urgency |

## BIOLOGICAL REFERENCES

| Concept | Source |
|---|---|
| Dopamine = reward prediction error | Schultz 1997, Science |
| NE = explore/exploit trade-off | Aston-Jones & Cohen 2005 |
| ACh = sensory precision | Yu & Dayan 2005 |
| 5-HT = behavioral inhibition | Crockett 2009 |
| Precision weighting | Friston (Active Inference) 2009 |
