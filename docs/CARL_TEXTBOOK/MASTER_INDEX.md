# 📚 THE CARL CODEBASE TEXTBOOK
## Complete Line-by-Line Guide — Differential Drive Robot (Current Build)
### All 15 Deep Dives · Logical Reading Order

---

> *Every Python file. Every XML file. Every line. Every reason.*
> *If you read this textbook cover to cover, you can explain every decision in this codebase to anyone.*

---

## 📖 READING ORDER (Bottom-Up — Body → Brain → Behavior)

Read in this order. Each chapter builds on the one before it.

---

### CHAPTER 1 — The Physical Body

**What it answers:** *What does CARL's body look like? What joints does it have? What forces can it exert? What sensors does it have?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 01 | [vessel_kinetic.xml Deep Dive](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_15_vessel_kinetic_xml.md) | `world/vessel_kinetic.xml` | MuJoCo Newton solver, implicit Euler, contype bitmasks, differential drive wheels, 5-DOF arms (parked), eye_cam pinhole, touch sensors, velocity vs position actuators |
| 02 | [carl_mujoco.xml Deep Dive (part of DD#12)](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_12_xml_tests_verifier_interface.md) | `world/carl_mujoco.xml` | Behavioral testbed body (simpler 2-robot version for phase18) |

---

### CHAPTER 2 — The Physics Interface

**What it answers:** *How does Python talk to MuJoCo? How are LiDAR rays computed? How is yaw extracted from a quaternion?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 03 | [DD#11 — Omega, A\*, Plotter, Physics](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_11_omega_astar_plotter_physics.md) | `world/carl_mj_physics.py` | `mj_ray()` LiDAR, quaternion→Euler yaw, `apply_torque()`, `get_state()`, robot cfg dict |

---

### CHAPTER 3 — Hardwired Reflexes (No Learning)

**What it answers:** *How does CARL avoid walls without thinking? What is the "fast lane" of the nervous system?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 04 | [DD#01 — carl_reflex](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_01_carl_reflex.md) | `brain/carl_reflex.py` | LIF neuron model, Poisson spike generation, membrane potential decay, R-STDP eligibility traces, dopamine-gated weight update, backup FSM |

---

### CHAPTER 4 — The Endocrine System (Internal Chemistry)

**What it answers:** *How does CARL feel hunger, stress, and curiosity? How do hormones change behavior?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 05 | [DD#02 — carl_endocrine](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_02_carl_endocrine.md) | `brain/carl_endocrine.py` | First-order ODE decay, Euler integration, Bayesian precision weighting, reward prediction error (RPE), hunger formula, DA/NE/5HT/ACh interactions |

---

### CHAPTER 5 — The Learning Engine (Reservoir Computing)

**What it answers:** *How does CARL learn from experience? What is the math behind RLS? What is an echo state network?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 06 | [DD#03 — carl_reservoir](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_03_carl_reservoir.md) | `brain/carl_reservoir.py` | Echo state network, spectral radius scaling, W_in/W_res construction, RLS P-matrix update, Kalman gain, `tanh()` activation, forgetting factor λ |

---

### CHAPTER 6 — Spatial Navigation (Where Am I? Where Am I Going?)

**What it answers:** *How does CARL know its position? How does it plan a path through a maze? How does it follow the scent trail to food?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 07 | [DD#05-09 — Grid Cells + Physarum + Astar](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_05_09_remaining_files.md) | `brain/carl_grid_cells.py`, `brain/carl_physarum.py` | Hexagonal interference patterns, Nobel GPS model, value iteration, Laplacian pipe dynamics, slime mold path optimization |
| 08 | [DD#11 — A\* Pathfinding](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_11_omega_astar_plotter_physics.md) | `brain/astar.py` | A* search, f=g+h cost model, Manhattan heuristic, √2 diagonal cost, danger-weighted traversal |

---

### CHAPTER 7 — Vision (What Does CARL See?)

**What it answers:** *How does CARL's eye work? How was it trained? How are objects detected and located?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 09 | [DD#14 — Vision Data Collection](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `brain/collect_vision_dataset.py` | Pinhole camera projection math, 3D corner generation, bilinear bbox, guaranteed visibility sampling |
| 10 | [DD#14 — CNN Training](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `brain/train_vision.py` | Conv2d math, MaxPool2d halving, BatchNorm2d, Dropout, dual-head loss, active_mask background exclusion |
| 11 | [DD#05-09 — Multi-Object Vision](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_05_09_remaining_files.md) | `brain/train_multi_object_vision.py`, `brain/collect_multi_object_dataset.py` | SSD-Lite architecture, transfer learning, NMS, COCO API format |
| 12 | [DD#12 — Vision Verification](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_12_xml_tests_verifier_interface.md) | `brain/verify_vision_predictions.py` | Softmax inference, argmax class selection, pixel overlay |
| 13 | [DD#14 — Multi-Object Verification](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `brain/verify_multi_object_predictions.py` | SSD output format (boxes/labels/scores dict), score threshold 0.5, 2×2 grid visualization |

---

### CHAPTER 8 — Advanced Learning (STDP + Quantum Deliberation)

**What it answers:** *How does CARL learn which actions are good or bad from rewards? How does it choose between competing strategies?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 14 | [DD#10 — STDP](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_10_carl_stdp.md) | `brain/carl_stdp.py` | Three-factor rule, LTP/LTD outer products, causal spike ordering, Born rule probability mapping, Shannon entropy |

---

### CHAPTER 9 — Neuroscience Extensions (Mirror Neurons, Allostasis, Theta)

**What it answers:** *How does CARL respond to a sibling's death? How does it predict future stress? What is the theta oscillation gate?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 15 | [DD#11 — Omega Extensions](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_11_omega_astar_plotter_physics.md) | `brain/carl_omega_extensions.py` | MirrorNeuronSystem empathy signal, PredictiveAllostasis forward sim, ThetaGate oscillation gating of RLS λ |

---

### CHAPTER 10 — The Main Brain Loop (carl_simulation.py)

**What it answers:** *How does all of this come together? What happens every 30Hz tick? How is the state vector built? How is motor output generated?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 16 | [DD#04 — carl_simulation](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_04_carl_simulation.md) | `carl_simulation.py` (903 lines) | S_unified memory vector, HAL-pattern class, sonar interpolation, cross-modal gate, motor mixing formula, WebSocket telemetry, vision inference at 30Hz |

---

### CHAPTER 11 — The Artificial Life Loop (phase18_alife_pretrained.py)

**What it answers:** *How does CARL live, sleep, and die? How does it deliberate? What is the metabolism system? What are the three sleep phases?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 17 | [DD#13 — phase18_alife_pretrained](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_13_phase18_alife_pretrained.md) | `phase18_alife_pretrained.py` (1036 lines) | WebSocket async, NeuromodulatorSystem, HebbianAssociator, PredictiveCoder, HomeostaticRegulator, SocialCognition, scent diffusion, NREM/REM sleep, MPC planning, daughter minds, biomimetic cascade PID, metabolism, Visual SLAM, 15-neuron population code, quantum deliberation cascade |

---

### CHAPTER 12 — Observation & Visualization Tools

**What it answers:** *How do you watch CARL think in real-time? How do you plot telemetry data after a run?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 18 | [DD#11 — Live Plotter](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_11_omega_astar_plotter_physics.md) | `live_plotter.py` | `FuncAnimation`, WebSocket client, circular buffer, real-time matplotlib |
| 19 | [DD#14 — Plot Telemetry](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `brain/plot_telemetry.py` | Box filter convolution, rolling average, dual-axis chart, dpi=150 |
| 20 | [DD#14 — Show Carl](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `brain/show_carl.py` | qposadr lookup, model.geom_pos direct edit, mj_forward kinematics, viewer.launch blocking |

---

### CHAPTER 13 — Testing & Quality Assurance

**What it answers:** *How do you know the math is right? How does the automated test suite work?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 21 | [DD#12 — Tests](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_12_xml_tests_verifier_interface.md) | `tests/test_endocrine.py`, `tests/test_grid_cells.py` | pytest fixtures, invariant testing, monotonicity assertions, boundary conditions |
| 22 | [DD#14 — CI Pipeline](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `.github/workflows/ci.yml` | Matrix strategy (Python 3.10/3.11), `compileall`, import smoke test, why MuJoCo excluded from CI |

---

### CHAPTER 14 — Project Configuration

**What it answers:** *What libraries are needed? What files are intentionally excluded from Git and why?*

| # | Document | Files Covered | Key Concepts |
|---|---|---|---|
| 23 | [DD#14 — Config Files](file:///C:/Users/MANAS/.gemini/antigravity-ide/brain/02c6ac9a-09f0-4629-aaa8-b51f5e1796d7/DEEP_DIVE_14_vision_utilities_ci.md) | `.gitignore`, `requirements.txt`, `tests/__init__.py` | Why weights excluded, why datasets excluded, why PNG excluded, package purpose |

---

## 🗺️ ARCHITECTURE MAP — How Chapters Connect

```
┌─────────────────────────────────────────────────────────────────┐
│                    Chapter 10/11: Main Brain Loops              │
│         carl_simulation.py ←──→ phase18_alife_pretrained.py    │
└────────┬────────────────────────────────────────────────────────┘
         │ calls
         ▼
┌────────────────────────────────────────────────────────────────┐
│  Ch.2: Physics Interface (carl_mj_physics.py)                  │
│    ↕ reads/writes MuJoCo data arrays                           │
│  Ch.1: Physical Body (vessel_kinetic.xml / carl_mujoco.xml)    │
└────────────────────────────────────────────────────────────────┘

┌────── Ch.3 ────┐  ┌──── Ch.4 ────┐  ┌──── Ch.5 ────┐
│ carl_reflex.py │  │carl_endocrine│  │carl_reservoir│
│ LIF spikes     │  │ ODE hormones │  │ RLS learning │
└────────────────┘  └──────────────┘  └──────────────┘

┌──── Ch.6 ──────────────┐  ┌──── Ch.7 ─────────────┐
│ Grid Cells / Physarum  │  │ Vision CNN / SSD-Lite  │
│ A* Pathfinding         │  │ Dataset / Verify       │
└────────────────────────┘  └───────────────────────┘

┌──── Ch.8 ──────┐  ┌──── Ch.9 ─────────────────────┐
│ carl_stdp.py   │  │ carl_omega_extensions.py       │
│ LTP/LTD/Born   │  │ Mirror neurons / Allostasis    │
└────────────────┘  └───────────────────────────────┘

┌──── Ch.12 ─────────────┐  ┌──── Ch.13/14 ──────────┐
│ Visualization tools    │  │ Tests / CI / Config     │
│ live_plotter, telemetry│  │ pytest, ci.yml, .gitignore│
└────────────────────────┘  └────────────────────────┘
```

---

## 📐 ALL KEY FORMULAS (Master Reference)

### Body Physics (Chapter 1)
```
Wheel angular velocity → linear speed: v = ω × r_wheel = ω × 0.04 m
Differential drive turning: ω_robot = (v_R - v_L) / wheelbase = (v_R - v_L) / 0.22
Position actuator torque: τ = kp × (θ_target - θ_actual)
```

### LiDAR (Chapter 2)
```
ray_dir[i] = [cos(θ_i), sin(θ_i), 0]   where θ_i = i × (2π/5) for 5 rays
ray_hit, dist = mujoco.mj_ray(model, data, pos, dir, geomgroup, flg_static, bodyexclude, geomid)
yaw = atan2(2(wz + xy), 1 - 2(y² + z²))   [quaternion to yaw]
```

### LIF Neuron (Chapter 3)
```
V[t+1] = V[t] × decay + W × spikes_in
spike_prob[i] = max(0, V[i] - V_threshold) / V_threshold
```

### Endocrine ODE (Chapter 4)
```
X[t+dt] = X[t] + (-k × (X[t] - X_baseline)) × dt
π = π₀ × (1 + γ_ACh·ACh + γ_NE·NE - γ_5HT·5HT)   [Bayesian precision]
```

### Reservoir Computing (Chapter 5)
```
x[t+dt] = (1-dt/τ)·x[t] + (dt/τ)·tanh(W_res·x[t] + W_in·u[t])
y[t] = W_out · x[t]
gain = P·Φ / (λ + Φᵀ·P·Φ)           [Kalman gain]
P = (P - gain × Φᵀ·P) / λ            [covariance update]
W_out += error × gain                  [weight update]
W_res_scaled = W_res × (ρ_target / max|eigenvalues(W_res)|)
```

### Grid Cell Navigation (Chapter 6)
```
rate_c = max(0, cos(K[0]·pos) + cos(K[1]·pos) + cos(K[2]·pos)) / 3
K = [[cos(0°), sin(0°)], [cos(60°), sin(60°)], [cos(120°), sin(120°)]] × (2π/λ)
V(s) = max(R(s), γ × max_{s'∈N(s)} V(s'))   [value iteration]
```

### Physarum Pipes (Chapter 6)
```
Q = D × (p_source - p_sink)             [flow through pipe]
dD/dt = (|Q|^μ - D) / τ               [pipe diameter evolution]
```

### A* Pathfinding (Chapter 6 / 8)
```
f = g + h
g = cumulative_cost,   step_cost = 1.0 (cardinal) or √2 (diagonal)
h = |Δrow| + |Δcol|   (Manhattan heuristic)
danger_cost = danger_value × 50
```

### Vision CNN (Chapter 7)
```
Conv2d: output_size = (input + 2×padding - kernel) / stride + 1
MaxPool2d(2,2): output = input / 2 (both H and W)
flat_dim = 64 × 15 × 20 = 19200
total_loss = CrossEntropy(cls) + 2.0 × MSE(bbox × active_mask)
```

### Pinhole Camera (Chapter 7)
```
f = H / (2 × tan(fovy/2))
u = W/2 + (x_c / z_c) × f
v = H/2 - (y_c / z_c) × f
```

### Three-Factor STDP (Chapter 8)
```
E_LTP += A_pre ⊗ post_spikes × A_PLUS
E_LTD -= pre_spikes ⊗ A_post × A_MINUS
ΔW = LR × reward_signal × eligibility_trace
amplitude_i = e^(i × cost_normalized_i × π)      [Born rule]
P_i ∝ |amplitude_i × conj(Σ amplitudes)|²
```

### Motor Mixing (Chapter 10)
```
u_left  = CPG + cognitive[0] + reflex[0] + nav_taxis[0]
u_right = CPG + cognitive[1] + reflex[1] + nav_taxis[1]
```

### MPC Planning (Chapter 11)
```
F = Σ_h (danger + cognitive_map_danger - olfactory_reward + homeostatic) × 0.95^h
xs_n = Ad @ xs + Bd × u                [one-step world model prediction]
conf = max(wm_conf, 0.1) × 0.95^h     [confidence decay]
```

### Biomimetic Cascade Controller (Chapter 11)
```
target_vel = 0.6 × clip((min_lidar - 0.5) / 1.5, 0, 1)
target_pitch = clip((target_vel - current_vel) × 0.25, -0.25, 0.25)
best_u = clip(25.0 × (pitch - target_pitch) + 4.0 × pitch_vel, -8, 8)
```

---

## ✅ COMPLETE FILE CHECKLIST — Current Differential Drive Build

### Physical Body & World
- [x] `world/vessel_kinetic.xml` — Chapter 1 (DD#15) ← **hardware-faithful twin**
- [x] `world/carl_mujoco.xml` — Chapter 1 (DD#12) ← behavioral testbed

### Physics Interface
- [x] `world/carl_mj_physics.py` — Chapter 2 (DD#11)

### Brain Modules
- [x] `brain/carl_reflex.py` — Chapter 3 (DD#01)
- [x] `brain/carl_endocrine.py` — Chapter 4 (DD#02)
- [x] `brain/carl_reservoir.py` — Chapter 5 (DD#03)
- [x] `brain/carl_grid_cells.py` — Chapter 6 (DD#05-09)
- [x] `brain/carl_physarum.py` — Chapter 6 (DD#05-09)
- [x] `brain/astar.py` — Chapter 6 (DD#11)
- [x] `brain/collect_vision_dataset.py` — Chapter 7 (DD#14)
- [x] `brain/train_vision.py` — Chapter 7 (DD#14)
- [x] `brain/collect_multi_object_dataset.py` — Chapter 7 (DD#05-09)
- [x] `brain/train_multi_object_vision.py` — Chapter 7 (DD#05-09)
- [x] `brain/verify_vision_predictions.py` — Chapter 7 (DD#12)
- [x] `brain/verify_multi_object_predictions.py` — Chapter 7 (DD#14)
- [x] `brain/carl_stdp.py` — Chapter 8 (DD#10)
- [x] `brain/carl_omega_extensions.py` — Chapter 9 (DD#11)

### Main Loops
- [x] `carl_simulation.py` — Chapter 10 (DD#04)
- [x] `phase18_alife_pretrained.py` — Chapter 11 (DD#13)

### Visualization
- [x] `live_plotter.py` — Chapter 12 (DD#11)
- [x] `brain/plot_telemetry.py` — Chapter 12 (DD#14)
- [x] `brain/show_carl.py` — Chapter 12 (DD#14)

### Tests & Config
- [x] `tests/test_endocrine.py` — Chapter 13 (DD#12)
- [x] `tests/test_grid_cells.py` — Chapter 13 (DD#12)
- [x] `tests/__init__.py` — Chapter 14 (DD#14)
- [x] `.github/workflows/ci.yml` — Chapter 13 (DD#14)
- [x] `.gitignore` — Chapter 14 (DD#14)
- [x] `requirements.txt` — Chapter 14 (DD#14)

---

**🎓 Total: 26 files. 15 deep dive documents. ~6,000+ lines explained.**
**Every file of the current differential drive build is covered.**
