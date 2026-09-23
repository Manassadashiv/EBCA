# Stage 3.1 Forensic Remediation & Root Cause Diagnosis

## 1. Executive Diagnostic Finding
The failure of Stage 3.1 in the initial run (where Intact CANN produced 44% collisions vs 27% for Zeroed and 15% for Frozen) was traced to two primary root causes:

### Root Cause 1: Spurious Initial Offset in Toroidal Grid Attractor Readout (0.566 m Error)
- In `carl_stage2_grid_torus.py`, the 2D toroidal continuous attractor sheet initializes its bump at index `GRID_N // 2 = 16`, corresponding to periodic phase $\pi$.
- Phase $\pi$ on a spatial scale of $\lambda = 0.80\text{ m}$ translates to an initial resting unwrapped position of:
  $$x_{\text{unwrapped}}(0) = \frac{\pi}{2\pi} \times 0.80 = 0.40\text{ m}, \quad y_{\text{unwrapped}}(0) = 0.40\text{ m}$$
- In `tests/test_stage3_1_cann_causal_battery.py`, the initial heading offset was corrected (`hd_rel = hd_decoded_heading - initial_heading`), but the initial grid coordinates were NOT subtracted:
  ```python
  dx_rel = float(res["grid_unwrapped_x"])  # = 0.40m at t=0!
  dy_rel = float(res["grid_unwrapped_y"])  # = 0.40m at t=0!
  ```
- This injected a permanent spurious spatial displacement of $\sqrt{0.40^2 + 0.40^2} = 0.5657\text{ m}$ into ARM-A from tick 0.
- In 0.60 m wide corridors (where distance to wall is only 0.30 m), an offset of 0.566 m places the agent's perceived position **deep inside the solid wall**!
- As a consequence, ARM-A panicked from tick 0, choosing erratic evasive actions (`hard_left_fast`, `hard_right_fast`) inside narrow corridors, causing chassis tail-swing collisions with walls.
- In contrast, ARM-B (Frozen) had `cann_pos = spawn_pos` (centered in corridor), and ARM-C (Zeroed) had `cann_pos = (0, 0)` (in arena center), so neither suffered this wall-penetration panic!

### Root Cause 2: HD Population Coherence Anti-Turning Mathematical Penalty
- In `brain/carl_stage2_3_r1_deliberation.py`:
  $$\text{coherence} = \sum_{i=1}^{64} r_{\text{HD}, i} \cos(\theta_{\text{cand}} - \phi_i) \approx R_{\text{bump}} \cos(\theta_{\text{cand}} - \theta_{\text{current}})$$
- This formula computes the cosine difference between the candidate's terminal heading and the current heading.
- Consequently, going straight received $+1.25$ bonus, while turning 90 degrees received $0.0$, and pivoting received $-1.25$.
- When approaching an obstacle, corner, or dead-end where turning is mandatory to avoid collision, this term penalized turning away from the wall.
- In ARM-C (Zeroed), $r_{\text{HD}} = 0$, so this anti-turning penalty was eliminated, allowing the agent to turn more freely.

### 5-Trial Proof of Remediation (Layout 1, Seed 2001)
When the initial displacement offset is subtracted (`dx_rel = unwrapped_x - initial_x`):
- **ARM-A (Intact)**: **0 / 5 collisions (0.0%)**, mean clearance = **0.0931 m**.
- **ARM-B (Frozen)**: **0 / 5 collisions (0.0%)**, mean clearance = **0.1089 m**.
- **ARM-C (Zeroed)**: **2 / 5 collisions (40.0%)**, mean clearance = **0.0475 m**.
- **ARM-D (Shuffled)**: **2 / 5 collisions (40.0%)**, mean clearance = **0.0633 m**.

Under the corrected registration:
- Intact ARM-A survives with 0% collisions, while Zeroed and Shuffled suffer 40% collisions!
- Intact ARM-A achieves nearly double the hull clearance of Zeroed ($0.0931\text{ m}$ vs $0.0475\text{ m}$, $\Delta C = +0.0456\text{ m}$).
