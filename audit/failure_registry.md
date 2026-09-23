# CARL-DX FIRST-CLASS FAILURE REGISTRY & ANOMALY LOG

**Evaluation Standard**: NASA-Inspired Systems Engineering Rigor  
**Target Repository**: `D:\ebca`  
**Purpose**: Rigorous inventory of all 10 first-class forensic failure categories, monitoring rules, detected anomalies, and corrective interventions.

---

## 1. 10 First-Class Failure Categories & Detection Criteria

| Failure Category | Forensic Definition & Detection Threshold | Architectural Root Cause | Active Remediation & Safeguard | Status |
| :--- | :--- | :--- | :--- | :--- |
| **A. STATIONARY_STALL** | Commanded velocity $>0.05\text{ m/s}$ but physical translation $\Delta x_{25} < 0.015\text{m}$ over 25 ticks | Wheel slip, geometric dead-end, or high physical contact load | Rolling 20-tick displacement window triggers 3-tier escalating recovery | **RESOLVED & ZERO FAILURES** |
| **B. BRAKE_LOCK** | `BRAKE_REST` held continuously for $>15$ ticks without emergency condition | Idling penalty insufficient or zero goal gradient | $+100.0$ idling penalty in Dreamer when front clearance $>0.35\text{m}$ | **RESOLVED & ZERO FAILURES** |
| **C. LEFT_RIGHT_LIMIT_CYCLE** | Alternating Left/Right steering commands $\ge 4$ times in 12 ticks | Sonar symmetry or spatial obstacle dead-center bifurcation | Directional steering persistence filter (6–10 tick hold) | **RESOLVED & ZERO FAILURES** |
| **D. FORWARD_REVERSE_LIMIT_CYCLE** | Shifting between Forward and Reverse $\ge 4$ times in 14 ticks | Rapid goal flip or unstable clearance threshold oscillation | Clearance hysteresis window $[0.40\text{m}, 0.65\text{m}]$ | **RESOLVED & ZERO FAILURES** |
| **E. SPIN_LOOP** | Cumulative yaw $>720^\circ$ ($4\pi\text{ rad}$) while net displacement $<0.05\text{m}$ | Symmetrical obstacle trap or absence of translational affordance | Tri-Drive Empowerment vetoes states with collapsing reachable space | **RESOLVED & ZERO FAILURES** |
| **F. HEAD_SCAN_WITHOUT_INFO** | Head pan standard deviation $>0.15\text{ rad}$ with zero uncertainty reduction | Unconnected cosmetic visual sweep routine | Head sweep linked causally to spatial uncertainty reduction | **RESOLVED & ZERO FAILURES** |
| **G. RECOVERY_LOOP** | Recovery manager re-triggered $\ge 3$ times in 30 ticks without breakout | Premature exit from recovery before clearing entrapment zone | Tier 3 forward breakout requires confirmed displacement $\ge 0.35\text{m}$ | **RESOLVED & ZERO FAILURES** |
| **H. GOAL_LOOP** | High-level goal switches $\ge 5$ times in 15 ticks without progress | Homeostatic drives oscillating near boundary thresholds | Goal persistence temporal filter ($>15$ ticks) | **RESOLVED & ZERO FAILURES** |
| **I. ACTION_CHATTER** | Command primitive changing every 1–2 ticks continuously for $>6$ ticks | Unfiltered discrete action switching across closely scored candidates | Expected Free Energy action persistence bonus ($-4.0$) | **RESOLVED & ZERO FAILURES** |
| **J. RESET_SENSITIVE_CONTROL_BIAS** | Non-zero steering bias ($>0.01$) or speed ($>0.05$) persisting post-reset | Stale state variables or integrator windup | Explicit `reset()` lifecycle clearing all filters and state variables | **RESOLVED & ZERO FAILURES** |

---

## 2. Empirical Failure Summary (Adversarial Suite Execution)

```json
{
  "total_failure_events_detected": 0,
  "failure_breakdown": {
    "STATIONARY_STALL": 0,
    "BRAKE_LOCK": 0,
    "LEFT_RIGHT_LIMIT_CYCLE": 0,
    "FORWARD_REVERSE_LIMIT_CYCLE": 0,
    "SPIN_LOOP": 0,
    "HEAD_SCAN_WITHOUT_INFORMATION_GAIN": 0,
    "RECOVERY_LOOP": 0,
    "GOAL_LOOP": 0,
    "ACTION_CHATTER": 0,
    "RESET_SENSITIVE_CONTROL_BIAS": 0
  },
  "verdict": "ZERO_FAILURES"
}
```
