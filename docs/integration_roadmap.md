# CARL-Ω Integration Roadmap
**Written:** 18 July 2026 | **Status:** Planning — not yet implemented
**Goal:** Close the gap from 25% → 100% active module integration in `carl_simulation.py`

---

## Context

All cognitive modules are fully written. The gap is wiring, not code. The current loop
actively uses: `LiquidStateReservoir`, `EndocrineSystem`, `SpikingReflexLayer`,
`GridCellModule`, `PlaceCellLayer`, `HippocampalNavigator`, and the SSD-Lite vision
model (genuine inference at line 192 every tick). Everything else is standalone.

**The two worlds are intentional and permanent:**
- `vessel_kinetic.xml` + `carl_simulation.py` = **hardware-faithful twin** (28-DOF, real
  actuator layout, will port to GPIO/PWM in Phase 2)
- `carl_mujoco.xml` + `phase18_alife_pretrained.py` = **behavioral testbed** (simpler
  2-body, faster iteration, where emergent behaviors are prototyped before being ported
  into the twin)

New cognitive behaviors should be prototyped in `phase18` first, then ported into
`carl_simulation.py` once stable. Neither replaces the other.

---

## Step 1 — Wire the Arm Actuators (Layer 0 completion)

**Priority: Highest | Cost: Low | Unlock: First visible limb behavior in the hardware twin**

### What's broken

`vessel_kinetic.xml` defines 16 arm actuators (all confirmed present in the XML):

| Actuator | Joint | ctrlrange |
|---|---|---|
| `act_shoulder_yaw_L/R` | `shoulder_yaw_L/R` | −0.1 → 1.57 / −1.57 → 0.1 |
| `act_shoulder_L/R` | `shoulder_L/R` | −2.0 → 2.0 |
| `act_elbow_L/R` | `elbow_L/R` | −2.44 → 0 |
| `act_wrist_L/R` | `wrist_L/R` | −1.57 → 1.57 |
| `act_grip_L/R` | `grip_L/R` | 0 → 0.52 |

Zero references to any of them exist in `carl_simulation.py`. The arms are fully
simulated but receive zero control input — they hang limp every tick.

### Signals already live in the loop to drive the reflex

| Signal | Where it lives | Meaning |
|---|---|---|
| `food_dist` | Computed each tick in motor block | Distance to nearest food, 0–10 m |
| `food_angle` | Motor mixing block | Bearing to nearest food |
| `self.endocrine.DA` | Every tick | Hunger / approach drive |
| `active_place_idx` | Line ~589 | Current place cell (spatial context) |
| `data.contact` | MuJoCo | Contact array — grip trigger |

### Wiring plan (reflex, not IK)

Insert after the motor mixing block (~line 700):

```python
# ── Reach Reflex (Step 1 integration) ──────────────────────────────────────
REACH_DIST   = 1.2          # metres — within physical reach envelope
HUNGER_THRESH = 0.8         # DA level that triggers reach
food_close = (food_dist < REACH_DIST)
hungry     = (self.endocrine.DA > HUNGER_THRESH)

if food_close and hungry:
    shoulder_target  = float(np.clip(food_angle * 0.5, -2.0, 2.0))
    elbow_target     = -1.2
    wrist_target     = 0.0
    grip_target      = 0.45   # close
else:
    shoulder_target  = 0.0
    elbow_target     = -0.3
    wrist_target     = 0.0
    grip_target      = 0.0    # open / rest

# Resolve actuator IDs once at init, not every tick
# self._arm_ids = {n: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in [...]}
for side, sign in [("L", 1.0), ("R", -1.0)]:
    data.ctrl[self._arm_ids[f"act_shoulder_{side}"]]     = shoulder_target * sign
    data.ctrl[self._arm_ids[f"act_elbow_{side}"]]        = elbow_target
    data.ctrl[self._arm_ids[f"act_wrist_{side}"]]        = wrist_target
    data.ctrl[self._arm_ids[f"act_grip_{side}"]]         = grip_target
# ───────────────────────────────────────────────────────────────────────────
```

### Acceptance criteria

- [ ] Arms visibly extend toward food when `food_dist < 1.2` and `DA > 0.8`
- [ ] Grip closes at contact; opens when food eaten or CARL moves away
- [ ] Arms return to rest posture when no food nearby
- [ ] No NaN in `data.ctrl` — all targets clamped to `ctrlrange`
- [ ] Wheel / nav behaviour unchanged (arm indices verified non-overlapping via `mj_name2id`)

---

## Step 2 — Wire `carl_physarum.py` and `carl_omega_extensions.py`

**Priority: High | Cost: Low (reference impl in `phase18`) | Unlock: Smarter pathfinding, theta gating, predictive allostasis**

### Reference implementation

`phase18_alife_pretrained.py` already wires both modules to the grid cell / endocrine
system. That file is the porting guide — not new engineering.

### `carl_physarum.py` — Slime-mould pathfinder

Physarum adapts edge weights dynamically based on traversal success — more biologically
plausible than static A* and degrades gracefully in unmapped areas.

**Wiring steps:**
1. Import `PhysarumPathfinder` at top of `carl_simulation.py`
2. Instantiate alongside `HippocampalNavigator` in `__init__`
3. Feed `hippocampus.places` graph edges as the Physarum substrate
4. Call `physarum.step(current_node, target_node)` → returns next waypoint
5. Replace current A* target in motor mixing with Physarum waypoint

### `carl_omega_extensions.py` — Three sub-components

| Component | What it does | Wiring point | Priority |
|---|---|---|---|
| **Theta gate** | Suppresses plasticity during high-NE states | Around RLS update block (~line 767) — gate `reservoir.rls_update()` on `theta_gate.open` | Wire first |
| **Predictive allostasis** | Anticipates homeostatic needs before they become acute | Replace reactive `surge_*` calls with predicted ones from allostasis model | Wire second |
| **Mirror neurons** | Fire when observed agent mimics own action | Requires second body in sim — **defer to social mechanics step** | Defer |

### Acceptance criteria

- [ ] `PhysarumPathfinder` in active loop; nav benchmark times ≥ current (no regression)
- [ ] Theta gate measurably suppresses RLS updates when `NE > 0.4` — log suppression events
- [ ] Predictive allostasis fires ≥ 1 anticipatory DA surge per 1,000-tick run
- [ ] No regression in Open Space / Maze eat times vs. pre-Step-2 baseline

---

## Step 3 — The Witness (Layer 4 — Metacognition)

**Priority: Medium | Cost: Low | Unlock: CARL stops repeating the same failure modes**

### What it is

A circular episode buffer + repeated-failure-pattern counter. `TelemetryLogger` is
already wired and writing every tick — this is a *reader* of existing data, not a new
sensing problem. Diagnostic ID `WIT-401` is already reserved in the module docstring.

### Core class

```python
from collections import deque, defaultdict

class TheWitness:
    def __init__(self, buffer_len=200):
        self.episodes      = deque(maxlen=buffer_len)
        self.failure_counts = defaultdict(int)   # (place_cell_idx, action) → count

    def observe(self, pos_cell, ne_level, action, outcome):
        key = (pos_cell, action)
        if outcome == "failure":
            self.failure_counts[key] += 1
        self.episodes.append((pos_cell, ne_level, action, outcome))

    def get_penalty(self, pos_cell, action):
        """Torque penalty multiplier in [0, 0.9] for repeated failures at this cell+action."""
        count = self.failure_counts.get((pos_cell, action), 0)
        return min(count * 0.15, 0.9)
```

**Wiring point:** After boundary-breach and obstacle-avoidance events (~lines 575–603).
Call `witness.observe(active_place_idx, self.endocrine.NE, action, outcome)`.
Apply `get_penalty()` as a scaling factor on motor output before writing `data.ctrl`.

### Acceptance criteria

- [ ] Witness buffer fills correctly with no memory leak on 10,000-tick runs
- [ ] Repeated boundary breach → measurable reduction in subsequent breach rate
- [ ] `witness_penalty` column present in telemetry CSV
- [ ] `WIT-401` diagnostic fires in console when penalty exceeds 0.3

---

## Step 4a — Imagination Engine (Layer 6, build before Layer 5)

**Priority: Medium-low | Cost: High | Unlock: Forward world model for MPC**

### Why Layer 6 before Layer 5

`remaining_tasks.md` lists Layer 5 (MPC) before Layer 6 (Imagination). **This order
is wrong for implementation.** MPC's 50-step trajectory optimizer needs a forward model
`T_wm` to evaluate candidate trajectories against. Without it you would build a throwaway
placeholder predictor anyway. Build the real predictor once (Layer 6), then hand it to
MPC (Layer 5).

### What to build

A spatiotemporal RNN that predicts `(next_pos, next_endocrine_state)` from
`(current_state, proposed_action)`. Once trained online, CARL's internal prediction
becomes the primary reality signal — physical sensors become error-correction only
(predictive coding loop, diagnostic ID `IMA-601`).

**Prototype workflow:** Build and train `T_wm` in `phase18` first (smaller state space,
faster iteration). Port to `carl_simulation.py` once RMSE target is hit.

### Acceptance criteria (Layer 6)

- [ ] `T_wm` predicts next position within 0.15 m RMSE after 5,000 training steps
- [ ] Prediction error logged every tick (`prediction_error` column in telemetry)
- [ ] Runs at ≥ 25 Hz within the 30 Hz control budget (profile before shipping)

---

## Step 4b — MPC / Causal Reasoning (Layer 5, after T_wm is stable)

**Priority: Medium-low | Cost: High | Depends on: Step 4a**

Post-failure: run 3 alternative 50-step forward simulations using `T_wm`. Choose the
trajectory with the best expected outcome. Scale RLS weights on that trajectory.
Diagnostic ID `MPC-511` already reserved.

### Acceptance criteria

- [ ] ≥ 1 verifiable post-failure trajectory correction per 10 failure events
- [ ] Counterfactual simulations complete in < 5 ms (batch eval via `T_wm`)
- [ ] `MPC-511` fires in console when a corrective trajectory is applied

---

## Explicitly deferred (do not prioritise yet)

| Item | Reason |
|---|---|
| **VSA / HDC wiring (Layer 1)** | 40K-dim vectors — high memory cost, low immediate behavioral payoff. Revisit after Steps 1–3 stable. |
| **Concept Genesis / SOM (Layer 7)** | Legitimately last — depends on stable sensors and memory from all layers above. |
| **Mirror neurons** | Requires a second body in the sim. Defer until single-body loop is complete. |
| **Sleep consolidation / NREM/REM** | Requires stable LTM first. Defer until HDC wiring is done. |
| **Phase 2 — Physical hardware** | Depends on Phase 1 100% stable. Already last in `remaining_tasks.md` — stays last. |

---

## Ordered summary

```
Step 1  →  Arm reach reflex                (vessel_kinetic.xml — hardware twin)
Step 2  →  Physarum + Omega extensions     (port wiring pattern from phase18)
Step 3  →  The Witness (metacognition)     (reader of existing telemetry — low cost)
Step 4a →  Imagination Engine (T_wm)       (prototype in phase18 first)
Step 4b →  MPC / Causal Reasoning          (consumes T_wm from Step 4a)
```

Each step is independent — no hard dependency on the next. This order maximises
visible behavioral change per unit of engineering effort.
