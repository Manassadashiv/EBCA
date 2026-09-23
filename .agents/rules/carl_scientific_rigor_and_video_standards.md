# CARL Scientific Rigor & Video Standards (Permanent Rule)

> [!IMPORTANT]
> **PERMANENT EXECUTION & EVIDENCE STANDARDS**:
> All experimental verification, benchmarking, and video rendering must adhere strictly to these physical and methodological standards.

---

## 1. Simulation Timestep Invariant (No Assumed Constants)

* **Exact Executable Timestep Rule:**
  The recording and control loop must use the **exact executable simulation/control timestep**. Documentation and code must derive `dt` directly from the actual model configuration (`model.opt.timestep * substeps`), and **never assume a hardcoded `0.0333 s`**.
* **Strict 1:1 Step Synchronization:**
  In any video or demonstration recording, **1 simulation step = 1 neural update = 1 video frame**. Artificially sub-stepping physics (e.g. running multiple physics steps per control loop iteration to stretch video length) is strictly forbidden because it alters the effective temporal dynamics of continuous attractor ODEs.

---

## 2. Benchmark-Specific Evidence & Anti-Optimization Policy

* **Benchmark-Specific Evidence:**
  The findings of Stage 2.1B (CANN drifting $18.27\,\text{cm}$ vs classical math $4.63\,\text{cm}$, and short-horizon recurrence ablation $W_{\text{rec}} = 0$ drifting $15.83\,\text{cm}$) are **specific to the tested Stage 2.1B open-space benchmark**. They are empirical observations from that test harness, not universal properties of continuous attractor networks.
* **No Benchmark Hacking:**
  Do not tune neural parameters, adjust gains, or introduce special-case logic simply to make the CANN beat classical calculus on an easy, frictionless benchmark.
* **Attractor Justification Mandate:**
  Continuous attractor architectures must be tested under conditions where attractors structurally earn their keep (e.g. Stage 2.1B-R: sensor dropout working memory, state disturbance recovery, long-horizon drift bounds).

---

## 3. Physical Environment & Arena Isolation

* **Complete Obstacle Purging in Open-Space Mode:**
  When `open_space=True` is invoked, the environment must move **all** external bodies and geoms (`hazard_cube`, `food`, `obj_cube_0`, `obj_cube_1`, `obj_ball_0`, `laser_target`, and `lwall_*`) completely out of the active arena to $(99.0, 99.0, -99.0)$. The robot must never collide with or bulldoze unintended obstacles during open-space navigation tests.

---

## 4. Video Demonstration & Visual Evidence Standards

* **Camera Framing:** Use a dynamic, close-up follow-tracking camera (`cam.type = mjCAMERA_FREE`, `cam.lookat = [pos_x, pos_y, 0.18]`, `cam.distance \approx 1.50 - 1.60`, `cam.elevation \approx -26.0^\circ \text{ to } -28.0^\circ`). The robot must be large, centered, and clearly visible.
* **Pacing & Action Duration:** Title cards must be minimal ($\le 2.0\,\text{s}$). The vast majority ($> 85\%$) of the video duration must show active, continuous robot movement.
* **HUD Readability:** All text and HUD overlays (HD polar ring, grid torus heatmap, mini-map) must have semi-transparent dark backing plates to guarantee high contrast regardless of floor lighting. Mini-maps must auto-scale to fill the display cleanly.

---

## 5. Architectural Unification Rule

* CARL is **ONE organism, ONE physical body, ONE canonical cognitive architecture**.
* Every developmental capability (Stage 1 body babbling, Stage 1.6 traction gating, Stage 2.1B continuous attractor navigation, Stage 2.2 place cells, Stage 3 continuous actions) is an organ being grown to integrate into [`carl_embodied_organism.py`](file:///d:/ebca/brain/carl_embodied_organism.py) on the flat zero-copy memory bus (`S_unified`).
* Creating disposable, fragmented standalone script islands is strictly forbidden.
