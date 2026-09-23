# CARL-DX Wall & Obstacle Approach Forensic Report

**Audit Subject**: Forensic Reconstruction of Wall & Obstacle Proximity in `complete_clean_blind_run.mp4`  
**Audit Date**: August 17, 2026  
**Final Forensic Classification**: **`NAVIGATION_AND_AGENCY_REQUIRES_REPAIR`**  
**JSON Evidence**: [`audit/wall_approach_forensic_report.json`](file:///D:/ebca/audit/wall_approach_forensic_report.json)  

---

## 1. Frame-by-Frame Forensic Reconstruction

An independent frame-by-frame and telemetry analysis of `clean_blind_life_run_telemetry.csv` and `decision_trace.jsonl` was conducted:

| Timestamp & Ticks | Spatial State & Pose | Commanded Motors | Sensed Clearance & Safety | Action & Affect | Behavioral Diagnosis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$t = 0.03\text{s} - 1.37\text{s}$**<br>(Ticks 1–41) | Spawn $(0.0, 0.0) \rightarrow (0.63, 0.09)$<br>Heading $\psi = 24.8^\circ$, Speed $0.32\text{ m/s}$ | $(u_L, u_R) = (6.0, 6.0)\text{ rad/s}$ | Sonar clearance: $2.4\text{m} \rightarrow 0.65\text{m}$<br>Safety margin: $0.96 \rightarrow 0.50$ | `STRAIGHT_FORWARD`<br>`SATISFACTION` | Healthy unconstrained forward acceleration. |
| **$t = 1.37\text{s} - 4.00\text{s}$**<br>(Ticks 42–120) | Stall at $(0.74, 0.17)$<br>Speed drops to $0.05\text{ m/s}$ | $(u_L, u_R) = (6.0, 6.0)\text{ rad/s}$ | Sonar clearance: $0.20\text{m}$<br>Safety margin: $0.453$ | `STRAIGHT_FORWARD`<br>`THREAT_AVERSION`<br>Veto: `False` | **FAILURE OF ANTICIPATORY AVOIDANCE.** Robot pushed continuously against obstacle for 78 ticks (2.6s) without steering away. |
| **$t = 4.03\text{s} - 5.00\text{s}$**<br>(Ticks 121–150) | Stationary at $(0.74, 0.25)$<br>Speed $0.003\text{ m/s}$ | $(u_L, u_R) = (0.0, 0.0)\text{ rad/s}$ | Sonar clearance: $0.22\text{m}$<br>Safety margin: $0.450$ | `BRAKE_REST`<br>`THREAT_AVERSION` | **Passive stall.** Robot halted at obstacle rather than executing an active clearance-recovery steering maneuver. |

---

## 2. Technical Root Causes

1. **Dreamer Rollout Horizon Blind to Sensed Obstacles**:
   In `brain/carl_generative_self_model.py` line 153, the counterfactual imagination engine computed boundary risk using a hardcoded arena check (`abs(x) > 4.5m`). It failed to integrate the actual 8-ray sonar rangefinder profile (`sensory.sonar_distances`) into the forward trajectory prediction. As a result, the internal world model predicted zero risk for `STRAIGHT_FORWARD` even when directly facing an obstacle.
2. **Operational Action Veto Disconnect**:
   In `brain/carl_endogenous_agency.py`, the action veto engine was only evaluated against external teleoperation commands, rather than asserting internal autonomous veto when the self-selected candidate violated forward sonar clearance.
3. **Safety Margin Decoupling**:
   In `brain/carl_autonomous_agent.py`, a collapsed safety margin ($S < 0.50$) triggered the expressive posture `THREAT_AVERSION`, but exerted zero mathematical penalty on candidate motor action selection in the Dreamer policy.

---

## 3. Mandatory Engineering Repairs

1. **Anticipatory Obstacle Field Integration in Dreamer**:
   Integrate 8-ray directional sonar clearance into candidate trajectory rollouts. Each candidate action must simulate ray-obstacle clearance along its predicted kinematic arc, penalizing Expected Free Energy $G(a)$ exponentially as forward clearance drops below $1.0\text{m}$.
2. **Autonomous Internal Action Veto**:
   If forward clearance along a candidate vector drops below $0.40\text{m}$ while speed $> 0.1\text{m/s}$, assert autonomous veto, actively forcing steering curvature away from the sensed obstacle normal toward the quadrant with maximum open clearance.
3. **Functional Active Epistemic Gaze**:
   When frontal clearance drops below $0.80\text{m}$, initiate active pan-tilt visual/sonar sweeps ($\pm 45^\circ$) to resolve spatial uncertainty before committing to a steering decision.
