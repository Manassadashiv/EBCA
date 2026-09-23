# 🔬 DEEP DIVE #13 — `phase18_alife_pretrained.py` (Every Line, Every Number, Every Why)
> *1036 lines. The main "Artificial Life" simulation loop. Where ALL modules converge.*

---

## FILE PURPOSE

This is the **top-level brain** of the CARL system — the file you run to start CARL. It pulls together every module (physics, endocrine, reservoir, grid cells, physarum, STDP, omega extensions) and orchestrates the complete biological cognitive loop for **two robots simultaneously**.

Think of it as the "conductor" who leads an orchestra — it doesn't play instruments itself, it tells each musician when to play and at what volume.

---

## LINES 1–21: Encoding + Imports

```python
# -*- coding: utf-8 -*-
```
**UTF-8 declaration**: Tells Python this file uses UTF-8 text encoding. Required when the file contains non-ASCII characters (the box-drawing characters `─`, `│`, `─` in the comment headers). Without this, Python would crash on those characters on Windows.

```python
import sys, time, math, numpy as np, asyncio, websockets, json, threading, random
```

Each library has a specific job:
- `sys`: Modify Python's module search path (`sys.path.extend(["world", "brain"])`)
- `time`: Real-time clock (`time.time()`, `time.sleep(DT)`)
- `math`: `math.atan2()`, `math.cos()`, `math.sin()`, `math.sqrt()`, `math.hypot()`, `math.pi`
- `numpy as np`: All matrix math (array operations, `np.clip`, `np.linalg.norm`)
- `asyncio`, `websockets`: Async WebSocket server for the live dashboard
- `json`: Serialize the `brain{}` dict to JSON for dashboard transmission
- `threading`: Run the WebSocket server on a background thread
- `random`: `random.choice()`, `random.sample()` for stochastic decisions

```python
sys.path.extend(["world", "brain"])
```
Adds `d:\ebca\world` and `d:\ebca\brain` to Python's module search path. This lets you do `from carl_mj_physics import ...` without a relative import — the file behaves as if it's running from inside those directories.

```python
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```
**Windows console encoding fix**: Windows PowerShell often uses cp1252 or cp437 encoding. The `─` and `▶` characters in print statements would either crash or show garbled text. This line forces UTF-8 output. `errors='replace'` means if a character can't be encoded, substitute `?` instead of crashing.

---

## LINES 24–47: Constants

```python
DT        = 1.0 / 240.0       # Physics timestep (matches XML timestep="0.004166667")
ACTIONS   = [-8.,-5.,-2.,-1.,0.,1.,2.,5.,8.]   # 9 forward torques (asymmetric: harder to go very fast)
REDUCED_ACTIONS = [-8.,-3.,0.,3.,8.]            # 5 actions for exploration (faster search)
STEER_ACTIONS   = [-2.,0.,2.]                    # 3 steering torques (left, straight, right)
HORIZON   = 40                 # Planning steps into future
DRES      = 20                 # Danger grid resolution (20×20 cells)
SDIM      = 5                  # State dimension [x, v, pitch, pitch_vel, neck]
P0_WM     = 500.0 * (SDIM+1)  # = 3000. Initial working-memory RLS confidence scale
P0_LTM    = 2000.0 * (SDIM+1) # = 12000. Initial long-term memory confidence scale
N_BODIES  = 2                  # Two robots in the simulation
STEER_GAIN= 6.0                # How much one steer unit rotates heading per timestep
MAP_RES   = 25                 # Cognitive map resolution (25×25 cells)
```

**Why `ACTIONS = [-8,-5,-2,-1,0,1,2,5,8]`?** Non-uniform spacing. Dense near zero (fine control) and coarse at extremes (large moves). This mirrors how we drive — mostly small corrections with occasional large steering inputs. Having 9 distinct values gives reasonable coverage without explosion of combinations: 9 forward × 3 steer = **27 trajectories evaluated per action selection**.

**Why `STEER_GAIN = 6.0`?** When `s = 1.0`, heading changes by `1.0 × 6.0 × DT = 6.0 / 240 = 0.025 rad/step = 1.4°/step`. At 30Hz control: 42°/second turning rate. Fast enough to navigate tight maze corners.

**`P0_WM = 500 × 6 = 3000`**: Initial P matrix = `3000 × I`. RLS confidence = `1 - trace(P)/P0`. At initialization: confidence = 0 (completely uncertain). As P shrinks (learning): confidence rises toward 1.

**Why `P0_LTM` = 4× larger?** LTM learns slower (`λ=0.99995` vs `λ=0.990`). Its P matrix starts larger to reflect that LTM should weight new data less aggressively — it's supposed to be a stable long-term average.

---

## LINES 49–66: `brain{}` — The Global Dashboard State

```python
brain = {"episode": 0, "best_survival": 0.0, "mode": "BOOTING",
         "DA": 0.5, "5HT": 0.6, "NE": 0.2, "ACh": 0.4,
         ...
         "danger_grid": [0.0]*400, "cognitive_map": [0.0]*625, ...}
```

**Why a flat dict?** The WebSocket server sends `json.dumps(brain)` every 33ms to the live dashboard. JSON requires a simple Python dict (not custom objects). Every value must be JSON-serializable: numbers, strings, lists. No numpy arrays, no custom objects.

**`"danger_grid": [0.0]*400`**: Danger grid flattened to a list of 400 values (20×20). Dashboard plots it as a heatmap.

**`"cognitive_map": [0.0]*625`**: Cognitive map danger layer (25×25=625). Dashboard plots it as another heatmap.

---

## LINES 68–81: WebSocket Live Dashboard Server

```python
async def _ws_handler(ws):
    try:
        while True:
            await ws.send(json.dumps(brain))
            await asyncio.sleep(1/30)   # 30 Hz updates
    except: pass
```

**`async def`**: Async function — can be paused/resumed without blocking the thread. `await ws.send(...)` pauses until the send completes, then resumes.

**`await asyncio.sleep(1/30)`**: Sleep for 33ms, yielding control to the event loop. Other async tasks can run during this sleep. If this were `time.sleep(1/30)`, it would block the ENTIRE thread, preventing other connections from being handled.

**`except: pass`**: Catches ALL exceptions (connection drops, JSON errors) and silently ignores them. The dashboard is optional — simulation should keep running even if the browser disconnects.

```python
threading.Thread(target=_run_ws, daemon=True).start()
```

**`daemon=True`**: A daemon thread dies automatically when the main program exits. Without `daemon=True`, the WebSocket thread would keep the process alive forever even after the main loop finishes.

**`threading.Thread` + `asyncio.run`**: The WebSocket server needs an asyncio event loop. `asyncio.run()` creates one. Running this on a background thread means the physics loop (on the main thread) is never blocked by WebSocket I/O.

---

## LINES 84–94: `fresh_wm()` and `fresh_ltm()` — World Model Initialization

```python
def fresh_wm():
    T = np.zeros((SDIM+1, SDIM))   # Shape (6, 5)
    T[:SDIM] = np.eye(SDIM)        # Top 5×5 = Identity
    return T, 500.0 * np.eye(SDIM+1)  # P = 3000 × I
```

**Why start T with an identity?** The world model says `x_next = T.T @ [x, u]`. The top 5×5 block = identity means: "by default, x_next ≈ x" (state stays the same). This is a **conservative prior**: "I don't know the dynamics, so I assume nothing changes." As CARL learns from experience, T adapts away from identity toward the actual robot dynamics.

**`T[SDIM,:] = 0`**: The bottom row (the "u" row — how control input affects state) starts as all zeros: "I don't know how torque affects state." The robot will update this from experience within the first 5-10 steps.

```python
def fresh_ltm():
    if os.path.exists("maze_ltm_T.npy"):
        try: T=np.load("maze_ltm_T.npy"); P=np.load("maze_ltm_P.npy")
        except: pass
    return T, P
```

**Checkpoint loading**: If a previous overnight training run saved `maze_ltm_T.npy`, load it. This is **curriculum learning**: start from prior knowledge rather than from scratch every time.

---

## LINES 96–105: `rls_update()` and Confidence Functions

```python
def rls_update(T, P, xk, uk, xn, lam, p_floor=0.001):
    Phi = np.append(xk, float(uk)).reshape(SDIM+1, 1)   # Shape (6, 1)
    e   = xn - (T.T @ Phi).flatten()                     # Prediction error (5,)
    PPhi = P @ Phi                                        # (6, 1) — covariance × regressor
    denom = lam + float((Phi.T @ PPhi).squeeze())         # Scalar denominator
    gain  = PPhi / denom                                  # Kalman gain (6, 1)
    T     = T + gain @ e.reshape(1, SDIM)                 # Weight update (6, 5)
    P     = (P - gain @ (Phi.T @ P)) / lam               # Covariance update (6, 6)
    P     = np.maximum(P, p_floor * np.eye(SDIM+1))      # Floor P to prevent degeneracy
    return T, P, float(np.linalg.norm(e))
```

This is EXACTLY the same RLS from `carl_reservoir.py` — explained in detail in DD#3. The difference here:
- `Phi = [x, u]`: augmented vector (state + action) as the regressor
- `T.T @ Phi`: predicts next state from current (state, action)
- `e = xn - prediction`: actual vs. predicted next state

**`p_floor = 0.001`**: `np.maximum(P, 0.001 × I)` floors the diagonal to 0.001. Prevents P from shrinking to exactly zero (which would give gain=0, freezing learning permanently).

```python
def wm_conf(P): return float(np.clip(1.0 - np.trace(P)/P0_WM, 0., 1.))
```

**Confidence formula**: `conf = 1 - trace(P) / 3000`. Large trace (uncertain) → low confidence. Small trace (confident) → high confidence ≈ 1.0. Used everywhere as a blending weight: `T_use = conf × T_wm + (1 - conf) × T_ltm`.

---

## LINES 108–132: `NeuromodulatorSystem` — Inline Endocrine Module

*Note: This is an earlier, simpler version of `carl_endocrine.EndocrineSystem`. It uses the same biological metaphors but simpler math.*

```python
def update(self, surprise, danger, dist_to_target, target_reached, sibling_died, allostatic_load):
    prog = max(0., 1. - dist_to_target / 8.)   # Progress [0,1]
    if target_reached: self.DA = min(1., self.DA + 0.3)
    else: self.DA = 0.92*self.DA + 0.08*(0.3 + 0.7*prog)
```

**DA (dopamine) update:**
- **Goal reached**: Big +0.3 spike. Immediate reward signal.
- **Otherwise**: `DA = 0.92 × old_DA + 0.08 × (0.3 + 0.7 × progress)`
  - `0.08` = learning rate toward target DA
  - `0.3 + 0.7 × progress`: DA target rises linearly from 0.3 (no progress) to 1.0 (at goal)
  - At 50% of the way to goal: target = `0.3 + 0.7 × 0.5 = 0.65` — encouraging continued approach

```python
    thr = max(danger, surprise*0.5)
    self.NE = (0.80*self.NE + 0.20*thr) if thr > self.NE else (0.92*self.NE + 0.08*thr)
```

**NE (norepinephrine) — asymmetric dynamics:**
- If new threat > current NE: **fast rise** (0.80 old + 0.20 new — 20% weighting)
- If threat subsided: **slow decay** (0.92 old + 0.08 new — 8% weighting)

**Why asymmetric?** Stress responses in biology are asymmetric: adrenaline surges quickly (emergency response) but decays slowly (it takes ~30 min to calm down after a scare). The `if/else` captures this: threat spikes fast, falls slow.

```python
    self.SHT = 0.990*self.SHT + 0.010*max(0., 1.-danger) - self.NE*0.25*0.005
```

**5-HT (serotonin) update:**
- Decays slowly toward `(1 - danger)`: High danger → low serotonin setpoint
- `- NE × 0.25 × 0.005`: NE suppresses serotonin. High stress → lower contentment. Biologically, chronic stress depletes serotonin.

**`effective_learning_rate(base=0.990)`:**
```python
return float(np.clip(base - (self.ACh - 0.4) * 0.008, 0.970, 0.999))
```
ACh above baseline (0.4) → `λ` decreases → faster learning (more attentive).
ACh below baseline → `λ` increases → slower learning (less attentive).
Range [0.970, 0.999] mirrors the theta gate constraint.

---

## LINES 135–156: `HebbianAssociator` — Tabular Association Memory

```python
class HebbianAssociator:
    def __init__(self, capacity=500):
        self.associations = deque(maxlen=capacity)
        self.strength_map = {}
```

**`strength_map`**: A Python dict acting as a sparse table. Keys are `(pitch_bin, vel_bin, action_bin)` tuples. Values are association strengths [0, 1].

```python
def fire(self, pitch, vel, action, surprise, threshold=0.3):
    if surprise < threshold: return          # Only learn from surprising events
    pb = int(np.clip((pitch + .65)/1.30*10, 0, 9))   # Pitch → bin [0,9]
    vb = int(np.clip((vel + 3.)/6.*10, 0, 9))         # Velocity → bin [0,9]
    ab = int(np.clip((action + 8.)/16.*5, 0, 4))      # Action → bin [0,4]
    key = (pb, vb, ab)
    self.strength_map[key] = min(1.0, self.strength_map.get(key, 0.) + surprise*0.1)
```

**Binning:**
- Pitch range [-0.65, 0.65] → 10 bins. Width per bin = `1.30/10 = 0.13 rad = 7.5°`
- Velocity range [-3, 3] m/s → 10 bins. Width = 0.6 m/s
- Action range [-8, 8] → 5 bins: `[-8:-4]→0, [-4:0]→1, [0:4]→2, [4:8]→3, [8]→4`

**`strength_map.get(key, 0.) + surprise*0.1`**: If this key was never seen, start at 0. Add `surprise × 0.1`. Larger surprise → faster strength buildup.

**Why tabular (not neural)?** O(1) lookup for action cost. No training required. Interpretable: "I know (pitch=0.3, vel=1.0, action=5) has association strength=0.7." Direct cost function with no neural overhead.

```python
def wire_together_decay(self):
    for k in list(self.strength_map):
        self.strength_map[k] *= 0.9999
        if self.strength_map[k] < 0.01: del self.strength_map[k]
```

**Decay + pruning**: `× 0.9999` per call (called every 240 steps = 1 second of simulation). After `log(0.01)/log(0.9999) ≈ 46000 steps` of no re-activation, an entry decays to 0.01 and gets deleted. Prevents unbounded memory growth.

---

## LINES 159–175: `PredictiveCoder` — Prediction Error Tracking

```python
def predict(self, x, u, T_wm, T_ltm, P_wm):
    alpha = wm_conf(P_wm)
    T_use = alpha*T_wm + (1.-alpha)*T_ltm    # Confidence-weighted blend
    Phi = np.append(x, float(u)).reshape(SDIM+1, 1)
    self.prediction = (T_use.T @ Phi).flatten()
    return self.prediction
```

Makes a one-step prediction BEFORE the physics step. Then `compute_error()` is called AFTER the step to find how wrong it was.

```python
def precision_weight(self):
    if len(self.error_history) < 10: return 0.5
    return float(np.clip(1./(1. + np.var(list(self.error_history))*10.), 0.1, 0.9))
```

**Precision from variance:**
- High variance in errors → model is inconsistent → low precision weight
- Low variance → model is consistent (even if biased) → high precision

`1/(1 + var × 10)`: When `var = 0.1`, precision = `1/(1+1) = 0.5`. When `var = 0.01`, precision = `0.91`. When `var = 0`, precision = 1.0.

**Why `×10`?** Scales variance to the usable range. Typical prediction errors are ~0.1-0.5 m/s², so variance ≈ 0.01-0.25. Without ×10, even bad models would get precision ≈ 0.8.

---

## LINES 178–204: `HomeostaticRegulator`

```python
HOMEOSTATIC_SETPOINTS = {"pitch": 0.0, "velocity": 0.0, "arousal": 0.3,
                         "fatigue": 0.0, "curiosity_drive": 0.4, "social_comfort": 0.7}
```

**Setpoints are DESIRED states** (biological "healthy" values):
- `pitch = 0.0`: CARL should stay vertical (0 lean)
- `velocity = 0.0`: At rest unless purposely moving (but modified to 0.3 when navigating)
- `arousal = 0.3`: Moderate alertness (not panicked, not asleep)
- `fatigue = 0.0`: No fatigue is the goal (fatigue accumulates with effort)
- `curiosity_drive = 0.4`: Moderately curious
- `social_comfort = 0.7`: Comfortable with sibling nearby

```python
total_error += abs(self.variables[key] - sp)
self.allostatic_load = min(1., self.allostatic_load + total_error*0.0001)
```

**Allostatic load**: Cumulative sum of all setpoint deviations over time. `×0.0001` keeps it from growing too fast — only matters after hundreds of steps of sustained deviation.

**Used in:**
- Cost function: High load → robot tries to reduce movement/stress
- Sleep trigger: High load → deeper/longer sleep needed for recovery

---

## LINES 215–234: Cognitive Map Functions

### `diffuse_scent()` — Chemical Trail to Goal

```python
def diffuse_scent(CM, goal_pos):
    s = CM[:,:,3]            # Channel 3 = scent map
    ns = np.zeros_like(s)
    ns[1:-1,1:-1] = (s[:-2,1:-1] + s[2:,1:-1] + s[1:-1,:-2] + s[1:-1,2:])
    ns2 = s.copy()
    ns2[1:-1,1:-1] += 0.25*(ns[1:-1,1:-1] - 4*s[1:-1,1:-1])
    ns2[d > 0.5] = 0.0       # Walls block diffusion
    ns2 *= 0.999             # Decay
    ns2[gi, gj] = 1.0        # Goal always emits maximum scent
    CM[:,:,3] = ns2
```

**Discrete Laplacian diffusion:**
```
Δs = s[i-1,j] + s[i+1,j] + s[i,j-1] + s[i,j+1] - 4×s[i,j]
s_new = s + 0.25 × Δs
```

This is the **heat equation discretized on a grid** — identical to how odors/chemicals diffuse in air. The goal emits "scent" at `s=1.0`. Each step, scent diffuses outward to neighbors. After 200 steps of pre-diffusion (line 583), the entire arena has a gradient pointing toward the goal.

**`ns2[d > 0.5] = 0.0`**: Walls are sinks. Scent cannot pass through walls (danger > 0.5 = wall cells). This creates a realistic chemical gradient that routes AROUND walls, not through them.

**`ns2 *= 0.999`**: 0.1% decay per diffusion step. Prevents scent from saturating everywhere at 1.0. Creates a proper gradient (lower far from goal, higher near goal).

### `get_olfactory_reward()` — Bilinear Interpolation

```python
def get_olfactory_reward(CM, xw, yw):
    xp = (xw - MAP_XMIN)/(MAP_XMAX - MAP_XMIN)*MAP_RES  # Float grid coordinate
    x0 = int(math.floor(xp)); x1 = int(math.ceil(xp))
    dx = xp - x0  # Fractional position within cell
    def bi(c):
        return (CM[x0,y0,c]*(1-dx)*(1-dy) + CM[x1,y0,c]*dx*(1-dy) +
                CM[x0,y1,c]*(1-dx)*dy     + CM[x1,y1,c]*dx*dy)
    return bi(3)*2.0 + bi(4)*0.5
```

**Bilinear interpolation**: Rather than snapping to the nearest grid cell (coarse), this smoothly interpolates between 4 neighboring cells using the fractional position `(dx, dy)`. The result is a smooth reward signal even when moving within a cell.

**`bi(3)*2.0 + bi(4)*0.5`**: Channel 3 (scent) weighted 2× + channel 4 (pheromone from past visits) weighted 0.5×. The trail to the goal is twice as attractive as memory of previous foraging.

---

## LINES 275–290: `biological_sleep()` — Three-Phase Memory Consolidation

```python
def biological_sleep(T_ltm, P_ltm, D, buf, near_miss_buf, hebbian, allostatic_load):
    print("  [NREM-1]")
    # Replay MOST SURPRISING experiences (top 20 by surprise)
    for (xk_m, uk_m, xn_m, surp) in sorted(buf, key=lambda m: m[3], reverse=True)[:20]:
        T_ltm, P_ltm, _ = rls_update(T_ltm, P_ltm, xk_m, uk_m, xn_m, lam=0.9999, p_floor=0.005)
    
    print("  [NREM-3]")
    # Replay most dangerous experiences — burn danger INTO memory
    for (xk_m, uk_m, xn_m, surp) in sorted(buf, ...)[:30]:
        for _ in range(3): D = danger_update(D, xn_m[2], xn_m[3], surp, rate=0.25)
    
    hebbian.wire_together_decay()
    
    print("  [REM]")
    # Replay near-misses (close to goal) — gentle "what if" exploration
    for (xk_m, uk_m, xn_m, surp) in sorted(near_miss_buf, ...)[:15]:
        D = danger_update(D, ..., max(0., surp*0.2), rate=0.05)  # Soft danger update
        T_ltm, P_ltm, _ = rls_update(T_ltm, P_ltm, ...)
    return T_ltm, P_ltm, D
```

**Three-phase sleep biology:**

**NREM-1 (Light Sleep — Learning):** Replay the 20 most surprising experiences from the episode into LTM. `lam=0.9999` = very slow, careful update (doesn't overwrite old knowledge). This is like "reviewing today's highlights."

**NREM-3 (Deep Sleep — Fear Consolidation):** Replay most dangerous events 3× each into the danger map. The 3× repetition simulates "sleep spindles" — deep sleep re-activates traumatic memories to reinforce avoidance. `rate=0.25` = strong update.

**REM (Dream Sleep — Creative):** Replay near-miss experiences at 1/5th strength (`surp*0.2`). Near-misses are close-to-goal transitions — REM "imagines" reaching the goal from near-goal states, gently guiding LTM toward success without overwriting danger.

`hebbian.wire_together_decay()`: During sleep, Hebbian associations decay slightly — forgetting weaker associations.

---

## LINES 293–327: `pick_action_maze()` — Standard Planning

```python
for u in ACTIONS:         # 9 forward actions
    for s in STEER_ACTIONS:  # 3 steering actions = 27 combinations
        xs, F = x.copy(), 0.
        xw, yw = pos_2d; heading = yaw
        for h in range(horizon):              # Simulate HORIZON=40 steps
            xs_n = Ad @ xs + Bd * u          # World model step
            heading -= s * STEER_GAIN * DT   # Update heading
            spd = xs_n[1] * DT * 25.         # Speed → displacement
            xw += spd * math.cos(heading)    # Update 2D position
            yw += spd * math.sin(heading)
            
            kin_d = danger_at(D, xs_n[2], xs_n[3]) * ne_amp * grief_w
            sp_d  = cognitive_map_danger(CM, xw, yw) * ne_amp * 0.5
            olf   = get_olfactory_reward(CM, xw, yw) * dop_w
            
            F += (... + kin_d + sp_d - olf + ...) * conf   # Accumulate cost
        if F < best_F: best_F, best_u, best_s, best_traj = F, u, s, traj
```

**This is Model Predictive Control (MPC):**
- For each of 27 action combos, simulate 40 steps into the future
- Accumulate cost (danger - reward) with discount `conf = max(alpha, 0.1) × 0.95^h`
- Pick the combo with lowest total cost

**`0.95^h`**: Discount factor — future costs matter 5% less per step. At h=40: `0.95^40 = 0.129`. Near future ~8× more important than far future.

**`ne_amp = 1.0 + NE × 1.5`**: NE amplifies danger sensitivity. Stressed CARL perceives danger as 2.5× larger. Biologically, norepinephrine heightens vigilance and risk aversion.

**`grief_w = 1.0 + grief × 0.5`**: Grieving CARL (after sibling death) becomes extra-cautious.

**`hom = abs(homeostatic.correction_signal(xs_n[2])) × 0.1`**: Homeostatic cost. Penalizes actions that increase pitch away from vertical.

---

## LINES 330–415: `daughter_minds_maze()` — Multi-Strategy MPC

This is a **2-level tree search**: 3 strategies each plan 20 steps, then each does a **second pass** of 10 additional steps (evaluating all 9 forward actions). Result: 3 × (9 × 20 + 9 × 10) = 810 trajectory evaluations.

**3 Strategies:**
```python
strategies = [
    {'d_w': 2.0 + NE*1.5, 'dop_w': 0.0, 'name': 'SAFE'},     # Avoid everything
    {'d_w': max(0.2, 0.5-DA*0.5), 'dop_w': dopamine_w, 'name': 'BOLD'},  # Chase food
    {'d_w': 1.0, 'dop_w': dopamine_w, 'name': 'BALANCED'},    # Normal
]
```

- **SAFE**: When NE=1.0, danger weight = `2.0 + 1.5 = 3.5`. No food attraction (`dop_w=0`). Pure avoidance.
- **BOLD**: When DA=1.0, danger weight = `max(0.2, 0.5-0.5) = 0.2`. Strong food attraction. Risk-seeking.
- **BALANCED**: Standard tradeoff.

**Why three strategies?** Real animals don't optimize one utility function — they have competing behavioral systems. At junctions, the competing strategies "vote" via the QuantumDeliberator.

---

## LINES 440–479: `spawn_brain()` — Robot Birth

```python
def spawn_brain(T_ltm, P_ltm, idx):
    if os.path.exists('mj_ltm_T.npy'):
        T_inst = np.load('mj_ltm_T.npy')   # Use overnight LTM as starting WM
    elif os.path.exists('school_T_wm.npy'):
        T_inst = np.load('school_T_wm.npy') # Use pre-trained physics model
    
    stdp_module = STDPActionEvaluator()
    if os.path.exists('school_W_stdp.npy'):
        stdp_module.synapse.W = np.load('school_W_stdp.npy')
    
    return {'T_wm': T_inst.copy(), 'P_wm': P_inst.copy(), ...,
            'hippo':    HippocampalNavigator(),
            'stdp':     stdp_module,
            'quantum':  QuantumDeliberator(),
            'mirror':   MirrorNeuronSystem(),
            'pred_allo': PredictiveAllostasis(),
            'theta':    ThetaGate(freq_hz=6.0),
            'energy':   100.0,    # Full battery
            'sleeping': False,    # Awake
            ...}
```

**"Robot School" (Curriculum Learning):** If pre-trained weights exist (from overnight runs), load them as the starting working model. New robots begin with physics knowledge already internalized — like a student who studied before the first day of class.

**Why `T_inst.copy()`?** Both robots share the same LTM, but have SEPARATE working memories. `.copy()` creates an independent array. If Robot A modifies its WM, Robot B's WM is unaffected.

**`'energy': 100.0`**: Full metabolic energy at birth. Energy depletes with effort and running quantum deliberation (5× more expensive).

---

## LINES 488–511: `pfc_worker()` — Prefrontal Cortex Thread

```python
def pfc_worker(b_idx):
    while pfc_active:
        path = astar_path(CM_global, b['pos_2d'], goal_pos)
        b['astar_path'] = path
        if path and len(path) > 1:
            dx = path[1][0] - b['pos_2d'][0]
            dy = path[1][1] - b['pos_2d'][1]
            ideal_yaw = math.atan2(dy, dx)
            yaw_err = (ideal_yaw - b['yaw'] + math.pi) % (2*math.pi) - math.pi
            b['target_s'] = float(np.clip(-yaw_err * 2.5, -1.5, 1.5))
            b['target_u'] = 3.0
        time.sleep(0.05)   # 20Hz planning rate
```

**Why a separate thread?** A* takes 5-30ms to compute depending on map complexity. If run in the main physics loop (240Hz = 4.17ms per step), A* would slow the physics by 2-7×. On a separate thread, A* computes in the background while physics runs at full speed.

**`time.sleep(0.05)` = 20Hz planning**: Path replanning at 20Hz is fast enough to react to map changes (walls discovered by LiDAR) without overloading the CPU.

**Yaw error wrapping:**
```python
yaw_err = (ideal_yaw - b['yaw'] + math.pi) % (2*math.pi) - math.pi
```
This wraps the angle to [-π, π]. Without this, a yaw difference of 3.5 rad (≈200°) would give a huge steer command, when the correct action is turning -2.78 rad (-160°) the other way. The modulo wrapping always picks the shorter turn direction.

---

## LINES 604–1033: `main()` — The Master Control Loop

### Wall Pre-seeding (Lines 539–547)

```python
for (gx1,gy1,gx2,gy2) in MAZE_WALLS_GRID:
    x1, y1 = gx1*MAZE_CELL, gy1*MAZE_CELL
    n_pts = max(2, int(math.sqrt((x2-x1)**2+(y2-y1)**2)/0.15))
    for k in range(n_pts+1):
        t = k/max(1,n_pts)
        xw = x1+t*(x2-x1); yw = y1+t*(y2-y1)
        for ddx in [-0.1, 0., 0.1]:
            for ddy in [-0.1, 0., 0.1]:
                cognitive_map_update(CM_global, xw+ddx, yw+ddy, danger=0.9, trust_delta=0.)
```

**Why pre-seed walls?** A* needs to know where walls are from episode 1. Without pre-seeding, CARL would crash into every wall before learning they exist. Pre-seeding gives the robot "blueprint knowledge" — like seeing a map before entering a building.

**`n_pts = ... / 0.15`**: Place danger markers every 15cm along each wall segment. Grid cells are 33cm wide, so 15cm spacing ensures no cell between two wall points is missed.

**`for ddx, ddy in [-0.1, 0., 0.1]²`**: Mark a 3×3 neighborhood (30cm radius) around each wall point. Creates a "thick" danger boundary so A* routes clearly AWAY from walls, not just through the 1-cell gap.

### Visual SLAM (Lines 671–680)

```python
for (hx, hy) in hit_points:   # LiDAR hit points
    CM_global[gi, gj, 0] = 1.0   # Max danger (wall confirmed by sensor)
    CM_global[gi, gj, 1] = 1.0   # Max trust (we saw it)
    D_global[di, dj] = 50.0       # High danger in kinematic grid
```

**"Simultaneous Localization and Mapping" (SLAM) in 4 lines**: When a LiDAR ray hits something, mark that grid cell as `danger=1.0, trust=1.0` in the cognitive map. This is the real-time obstacle discovery system — no pre-loading needed; the map is built from live sensor data.

**`D_global[di, dj] = 50.0`**: 50 = very large danger value in the kinematic danger grid (Dres=20). Much higher than the typical 0.3-0.8 values from model surprise. This ensures A* and MPC treat LiDAR-confirmed walls as absolutely impassable.

### Visual Population Code (Lines 682–688)

```python
v_prox = [np.clip(1.0 - d/2.0, 0.0, 1.0) for d in lidar_dists]  # 5 neurons
v_void = [1.0 if d > 4.5 else 0.0 for d in lidar_dists]          # 5 neurons
v_loom = [np.clip((prev_lidar[j] - lidar_dists[j])*10.0, 0.0, 1.0) for j in range(5)]  # 5 neurons
v_pop = np.array(v_prox + v_void + v_loom, dtype=float)   # 15 neurons total
```

**Three types of distance coding (15 neurons from 5 rays):**
- **Proximity** (`v_prox`): Fires strongly when object < 2m. "Something nearby."
- **Void** (`v_void`): Fires when ray > 4.5m (open corridor). "Clear path ahead."
- **Looming** (`v_loom`): Fires when distance is DECREASING (`prev - current`). "Approaching obstacle."

`× 10.0` for loom: Typical approach rate ≈ 0.05-0.1 m/step. `0.1 × 10 = 1.0` (saturates at 1). Without ×10, loom values would be tiny (0.001-0.01) — too small for STDP to learn from.

### The Biomimetic Cascade Controller (Lines 829–865)

```python
# 1. Compute safe target velocity from LiDAR
target_vel = 0.6 * np.clip((min_lidar - 0.5) / 1.5, 0.0, 1.0)

# 2. Ramp up based on awake time
awake_time = (step - rb.get('wake_step', 0)) * DT
ramp = np.clip(awake_time / 2.0, 0.0, 1.0)

# 3. Turn brake
turn_brake = np.clip(1.0 - abs(yaw_err)/1.0, 0.2, 1.0)
target_vel *= turn_brake * ramp

# 4. LiDAR hard brake
if min_lidar < 1.5:
    brake_factor = np.clip((min_lidar - 0.5)/1.0, 0.0, 1.0)
    target_vel *= brake_factor

# 5. Cerebellar PID torque
target_pitch = np.clip((target_vel - current_vel)*0.25, -0.25, 0.25)
best_u = np.clip(25.0*(current_pitch - target_pitch) + 4.0*pitch_vel, -8., 8.)
```

**This is a bio-inspired cascade controller — 5 layers:**

1. **LiDAR velocity cap**: Max 0.6 m/s. If closest obstacle is at 0.5m → target_vel=0. Effectively freezes when about to hit a wall.

2. **Wake-up ramp**: After sleeping, start slowly for 2 seconds (ramp 0→1). Prevents violent lurching that would cause a fall on revival.

3. **Turn brake**: Slow down proportional to steering angle. `yaw_err = 0.5 rad (28°)` → `turn_brake = 0.5` → half speed. Prevents tipping during sharp turns.

4. **Hard LiDAR brake**: Additional braking if obstacle < 1.5m.

5. **Cerebellar PID**: `torque = 25×(pitch_error) + 4×(pitch_rate)`. This is a PD controller (Proportional + Derivative) for balance.
   - `25.0`: Proportional gain. Each radian of lean → 25 N·m restoring torque
   - `4.0`: Derivative gain. Damps oscillation (prevents wobbling)

**Why called "cerebellar"?** The cerebellum in animals handles balance and fine motor coordination — exactly what this PID does.

### Action Mode Selection (Lines 869–910)

```python
if pfc_path:                   # A* path exists → AUTOPILOT
    mode = 'AUTOPILOT'
elif dl > 0.5:                 # High danger → QUANTUM deliberation
    mode = f'QUANTUM-{q_name}'
elif curio > np.random.random() and dl < 0.4:   # Curious + safe → EXPLORE
    mode = 'CURIOUS'
else:                          # Default → standard MPC
    mode = ('FEARFUL' if dl>0.4 else 'GRIEVING' if grief>0.3 else 'EXPLORING')
```

**Priority cascade (highest to lowest):**
1. **A* AUTOPILOT**: If there's a planned path → follow it. Most efficient.
2. **QUANTUM**: When danger is high (>0.5), deploy three competing strategies voted by Born rule.
3. **CURIOUS**: When curiosity is triggered (`curio > rand`), do exploratory information-seeking.
4. **FEARFUL/GRIEVING/EXPLORING**: Standard MPC with different emotional weightings.

### Metabolism (Lines 917–924)

```python
effort = abs(un) + abs(sn) + (5.0 if 'QUANTUM' in mode else 1.0)
rb['energy'] -= effort * 0.001
if rb['energy'] <= 0.0:
    rb['sleeping'] = True
```

**Why QUANTUM costs 5× more?** Quantum deliberation runs ~810 trajectory evaluations. This represents the high metabolic cost of complex deliberation — real brains consume 20-25% of body energy while doing intensive planning. Making it 5× more expensive creates evolutionary pressure: CARL shouldn't always deliberate (too costly) — only when danger warrants it.

**`energy -= effort × 0.001`**: For typical effort=10, energy decreases by 0.01 per step. At 240Hz: 2.4 per second. Starting energy=100 → would run for 41 seconds. In practice, lower-effort navigation extends this significantly.

### Memory Checkpoint (Lines 1029–1032)

```python
if step % 2000 == 0:
    np.save('memory/mj_ltm_T.npy', T_ltm_ep)
    np.save('memory/mj_danger.npy', D_global)
    print(f'  [MEMORY] Saved checkpoint ALife Step {step}')
```

**Every 2000 steps = 8.3 seconds of simulation**: Save LTM, danger map, and cognitive map. If the program crashes, these checkpoints are loaded on the next run (see `fresh_ltm()`). No learning progress is lost.

---

## COMPLETE BEHAVIORAL STATE MACHINE

```
BOOTING
    ↓ init
AUTOPILOT  ←── A* path exists (most efficient path-following)
    ↓ A* path lost
QUANTUM    ←── danger > 0.5 (multi-strategy deliberation)
    ↓ danger < 0.4
CURIOUS    ←── curio > random (exploration drive)
    ↓ curio not triggered
FEARFUL / GRIEVING / EXPLORING  (standard MPC)
    ↓ energy = 0
SLEEPING   ←── metabolic collapse
    ↑ energy = 100 (recovery complete)
```
