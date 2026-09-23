# Deterministic Embodiment Low-Level Control Qualification Report

**Audit Date**: August 16, 2026  
**Qualification Gate Status**: **`EMBODIMENT_QUALIFICATION = PASS`**  
**JSON Output**: [`audit/embodiment_control_qualification.json`](file:///D:/ebca/audit/embodiment_control_qualification.json)  
**Telemetry Location**: [`telemetry_raw/embodiment_qualification/`](file:///D:/ebca/telemetry_raw/embodiment_qualification/)  

---

## 1. Executive Summary

To qualify the low-level physics, actuator interfaces, and differential drive kinematics independently of CARL's learned neural policies, four deterministic open-loop control primitives were executed directly in MuJoCo physics.

All 4 primitives passed with verified physical displacement, angular rotation, active deceleration, and stable normal wheel-ground traction.

$$\mathbf{EMBODIMENT\_QUALIFICATION = PASS}$$

---

## 2. Primitive Execution & Telemetry Verification Matrix

| Primitive Name | Commanded Velocity $(u_L, u_R)$ | Duration | Measured Displacement | Measured Delta Yaw | Final Speed | Final Wheel Speeds $(\omega_L, \omega_R)$ | Peak Torque | Audit Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`FORWARD`** | $(+6.0, +6.0)\text{ rad/s}$ | $2.0\text{s}$ | **$+1.983\text{ m}$** | $-1.90^\circ$ | $1.024\text{ m/s}$ | $(+5.82, +5.82)\text{ rad/s}$ | $1.84\text{ N}\cdot\text{m}$ | **`PASS`** |
| **`STOP`** | $(0.0, 0.0)\text{ rad/s}$ | $2.0\text{s}$ | $+0.004\text{ m}$ | $0.00^\circ$ | **$0.0020\text{ m/s}$** | $(+0.04, +0.04)\text{ rad/s}$ | $0.12\text{ N}\cdot\text{m}$ | **`PASS`** |
| **`TURN_LEFT`** | $(-4.0, +4.0)\text{ rad/s}$ | $2.0\text{s}$ | $0.003\text{ m}$ | **$+133.00^\circ$ (CCW)**| $0.0015\text{ m/s}$ | $(-3.74, +3.76)\text{ rad/s}$ | $1.22\text{ N}\cdot\text{m}$ | **`PASS`** |
| **`TURN_RIGHT`**| $(+4.0, -4.0)\text{ rad/s}$ | $2.0\text{s}$ | $0.011\text{ m}$ | **$-127.50^\circ$ (CW)** | $0.0021\text{ m/s}$ | $(+3.81, -3.77)\text{ rad/s}$ | $1.22\text{ N}\cdot\text{m}$ | **`PASS`** |

---

## 3. Physical Findings by Primitive

### A. FORWARD Primitive
- **Command**: Both wheels $+6.0\text{ rad/s}$.
- **Response**: Straight-line translation along $+X$ reaching $+1.983\text{m}$ with negligible angular drift ($-1.90^\circ$).
- **Wheel Synchronization**: Left wheel $\omega_L = 5.82\text{ rad/s}$, Right wheel $\omega_R = 5.82\text{ rad/s}$.
- **Result**: **`PASS`**.

### B. STOP Primitive
- **Command**: Pre-rolled at $+6.0\text{ rad/s}$, then commanded $0.0\text{ rad/s}$.
- **Response**: The robot actively decelerated, velocity dropped monotonically from $1.02\text{ m/s} \rightarrow 0.0020\text{ m/s}$, and wheel velocities dropped to $< 0.05\text{ rad/s}$ with zero unwanted post-stop drift.
- **Result**: **`PASS`**.

### C. TURN_LEFT Primitive
- **Command**: Left wheel $-4.0\text{ rad/s}$, Right wheel $+4.0\text{ rad/s}$ (in-place counter-clockwise spin).
- **Response**: Robot spun CCW by $+133.00^\circ$ with center-of-mass planar drift of only $0.003\text{m}$.
- **Result**: **`PASS`**.

### D. TURN_RIGHT Primitive
- **Command**: Left wheel $+4.0\text{ rad/s}$, Right wheel $-4.0\text{ rad/s}$ (in-place clockwise spin).
- **Response**: Robot spun CW by $-127.50^\circ$ with center-of-mass planar drift of only $0.011\text{m}$.
- **Result**: **`PASS`**.

---

## 4. Frozen Asset Integrity Confirmation

During this qualification, the frozen assets were inspected and confirmed 100% untouched:
- `brain/carl_experiment_auditor.py`: `a0d6b0115a40e48b10685d0156289eaf8b1ead384a888008f952e5d894092004` (**MATCH**)
- `checkpoints/initial_untrained_C7.npz`: `73d3cbe17a50e1f65c8eaaa95ad413a1b67f9be7af24f4722e0bee99e483c78a` (**MATCH**)
- `evaluation_sets/manifest_eval_sets.json`: `df935592c4c655d4abfbbdc3d4627f8a25bc0d4421ac0a0ce37afeb8d8cc781d` (**MATCH**)

---

## 5. Final Gate Verdict

$$\mathbf{PRE\_TRAINING\_QUALIFICATION = PASS}$$
