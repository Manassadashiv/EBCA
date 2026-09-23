# CARL-DX ROOT CAUSE FORENSIC REGISTER

**Contract Standard**: NASA-Inspired Systems Engineering Rigor (Zero-Trust)  
**Deliverable**: Comprehensive Causal Deconstruction of All Historical and Reproduced Failures

---

## 1. Root Cause Analysis Register

### RC-01: Physics Sub-stepping Timestep Mismatch
- **Symptom**: Unresponsive avoidance, aggressive overshooting, inflated prediction errors in live playground.
- **First Causal Divergence Point**: `carl_live_playground.py` executed `for _ in range(8): mujoco.mj_step()` ($0.08\text{s}$ per cognitive tick), whereas `CarlAutonomousOrganismAgent` modeled dynamics with $dt = 0.0333\text{s}$.
- **Root Cause**: Hardcoded loop counter ($8\times$ vs $3\times$) causing a $2.4\times$ temporal mismatch.
- **Resolution**: Changed sub-stepping loop to 3 sub-steps ($0.03\text{s}$), achieving 100% synchrony with the agent's forward kinematics.

### RC-02: Stuck Detector Blind Spot in Zero-Command Obstacle Stalls
- **Symptom**: Robot entered `BRAKE_REST` when facing a wall and remained permanently parked without triggering recovery.
- **First Causal Divergence Point**: `CarlStuckDetector` evaluated `mean_cmd_v * window_dt`. When `BRAKE_REST` was commanded ($\text{cmd\_v} = 0$), `expected_dist` dropped below $0.08\text{m}$, actively decrementing stuck confidence.
- **Root Cause**: Stuck detection assumed zero commanded velocity implied intentional resting rather than an obstacle-induced deadlock.
- **Resolution**: Updated `CarlStuckDetector` to accept `min_obstacle_dist` and increment stuck confidence whenever displacement is $<0.025\text{m}$ over 15 ticks near obstacles.

### RC-03: Hardcoded Perimeter Arena Boundary Ceilings
- **Symptom**: Phantom obstacle detections, premature turning, and boundary vetoes at $x, y = \pm 2.35\text{m}$ in an arena whose outer walls are at $\pm 5.00\text{m}$.
- **First Causal Divergence Point**: Hardcoded $\pm 2.60\text{m}$ raycast truncation in `carl_embodied_organism.py` (lines 215–222) and `abs(pred_x) > 2.35` in `carl_endogenous_agency.py` (line 187).
- **Root Cause**: Legacy boundary constants from an earlier $5\text{m}\times 5\text{m}$ prototype that were not updated when the world XML was expanded to $10\text{m}\times 10\text{m}$.
- **Resolution**: Replaced artificial bounds with true arena perimeter limits ($\pm 4.80\text{m}$).

### RC-04: Left-Right Directional Chatter & Limit Cycles
- **Symptom**: High-frequency steering reversals when approaching symmetrical obstacles.
- **First Causal Divergence Point**: Microscopic sonar measurement fluctuations causing the preferred steering direction to flip sign every tick.
- **Root Cause**: Lack of directional hysteresis in candidate action arbitration.
- **Resolution**: Implemented a 6-tick directional persistence hold filter in `CarlEndogenousAgency`, enforcing continuous curvature arcs.
