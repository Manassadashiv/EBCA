# CARL-DX P0-02 Recovery Repair Changelog

**Target Subsystem**: CARL Active Stuck Recovery & Stuck Detection Subsystem  
**Source Files Modified**:
1. [`D:\ebca\brain\carl_stuck_recovery.py`](file:///D:/ebca/brain/carl_stuck_recovery.py)
2. [`D:\ebca\brain\carl_autonomous_agent.py`](file:///D:/ebca/brain/carl_autonomous_agent.py)

---

## Precise Architectural Changes

### 1. `CarlStuckDetector` (in `brain/carl_stuck_recovery.py`)
- **Dynamic Proximity Evaluation Window**:
  - Replaced static 20-tick window with a dynamic 10-tick window when `min_obstacle_dist < 0.50m`, reducing detection latency from 32 ticks (1.07s) to 8–10 ticks (0.26–0.33s).
- **Speed-Gated Stall Discrimination**:
  - Added `speed < 0.05m/s` gate for stuck candidate accumulation so active turning maneuvers ($\ge 0.07\text{m/s}$) cannot falsely accumulate stuck ticks.
- **Passing Proprioceptive Speed**:
  - Updated `CarlAutonomousOrganismAgent.step_cognitive_cycle` to pass `speed=sensory.speed` directly into `stuck_detector.update()`.

### 2. `CarlRecoveryManager` (in `brain/carl_stuck_recovery.py`)
- **Direct Forward Clearance Ray Lock**:
  - Replaced `front_cone_clear = float(max(sonar[7], np.mean(sonar[6:9])))` with `front_direct_clear = float(sonar[7])` to eliminate false corner averaging.
- **Direct Open-Avenue Breakout Bypass**:
  - In `trigger_recovery()`, if `front_direct_clear > 1.20m`, the organism immediately bypasses reverse/spin and enters `TIER_3_FORWARD_BREAKOUT` directly.
- **Brisk Angular Velocity for Turnarounds**:
  - Increased Tier 2 spin command from $4.5\text{ rad/s}$ to $7.0\text{ rad/s}$ ($[-7.0, 7.0]$ / $[7.0, -7.0]$), allowing full $180^\circ$ turns in narrow corridors to complete in $\le 16\text{ ticks}$ ($0.53\text{s}$).
- **True Open Avenue Spin Alignment**:
  - In enclosed spaces (`max_sonar < 1.0m`), spin continues until an open avenue ($>1.0\text{m}$) rotates into the central cone (`best_ray_idx in [6, 7, 8]`).
- **Breakout Phase Origin Tracking**:
  - Added `self.breakout_origin` tracked at the moment Breakout begins, evaluating forward displacement from the start of the breakout stroke rather than the pre-reverse origin.
- **Kinematic Match for Breakout Completion**:
  - Breakout successfully releases control as soon as:
    1. Forward escape path is open (`front_direct_clear > 0.45m`, `min_dist > 0.15m`, `effective_disp >= 0.020m` after 5 ticks), OR
    2. Net displacement reaches $\ge 0.06\text{m}$ under motor S-curve acceleration.
