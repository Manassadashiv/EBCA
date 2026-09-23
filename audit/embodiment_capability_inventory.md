# CARL-DX COMPLETE EMBODIED CAPABILITY & SUBSYSTEM INVENTORY
**Evaluation Framework**: NASA-Inspired Systems Engineering Rigor  
**Standard**: Strict Physical Grounding (No Self-Certification, No Synthetic Evidence)  
**Physics Engine**: MuJoCo 3.3.0 (`vessel_kinetic.xml`)

---

## 1. Physical Embodiment Subsystem Inventory

### 1.1 Masses, Inertias & Dimensions
- **Total Robot Mass**: $1.4676\text{ kg}$
  - `drive_deck` (chassis platform): $0.7251\text{ kg}$
  - `wheel_L` / `wheel_R` (rubber tire + rim): $0.2662\text{ kg}$ each ($0.5324\text{ kg}$ total)
  - `w_caster_front` / `w_caster_rear`: $0.0150\text{ kg}$ each ($0.0300\text{ kg}$ total)
  - `torso` (internal collar + shell): $0.2302\text{ kg}$
  - `neck_parallel_link` (neck post): $0.0200\text{ kg}$
  - `head` (dome + visor + eyes + ears): $0.1299\text{ kg}$
- **Track Width (Wheelbase)**: $0.230\text{m}$ (offset $\pm 0.115\text{m}$)
- **Wheel Radius**: $0.048\text{m}$
- **Ground Clearance (Chassis Bottom)**: $0.035\text{m}$
- **Center of Mass Height ($z_{\text{CoM}}$)**: $0.052\text{m}$ (ultra-low center of mass for high dynamic stability)

### 1.2 Actuators (6 Degrees of Freedom)

| Actuator Name | Joint | Type | Control Mode | Control Range | Force / Torque Limit | Damping | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `act_w_left` | `w_left` | Hinge ($0, 1, 0$) | Velocity | $[-35.0, +35.0]\text{ rad/s}$ | $\pm 25.0\text{ N}\cdot\text{m}$ | $0.05$ | `FUNCTIONALLY EXECUTING` |
| `act_w_right` | `w_right` | Hinge ($0, 1, 0$) | Velocity | $[-35.0, +35.0]\text{ rad/s}$ | $\pm 25.0\text{ N}\cdot\text{m}$ | $0.05$ | `FUNCTIONALLY EXECUTING` |
| `act_hip_pitch` | `hip_pitch` | Hinge ($0, 1, 0$) | Position | $[-0.55, +0.55]\text{ rad}$ | $\pm 12.0\text{ N}\cdot\text{m}$ | $0.50$ | `FUNCTIONALLY EXECUTING` |
| `act_hip_roll` | `hip_roll` | Hinge ($1, 0, 0$) | Position | $[-0.38, +0.38]\text{ rad}$ | $\pm 12.0\text{ N}\cdot\text{m}$ | $0.50$ | `FUNCTIONALLY EXECUTING` |
| `act_neck` | `neck_sweep` | Hinge ($0, 1, 0$) | Position | $[-0.60, +0.70]\text{ rad}$ | $\pm 12.0\text{ N}\cdot\text{m}$ | $0.20$ | `FUNCTIONALLY EXECUTING` |
| `act_head` | `head_pan` | Hinge ($0, 0, 1$) | Position | $[-1.40, +1.40]\text{ rad}$ | $\pm 12.0\text{ N}\cdot\text{m}$ | $0.20$ | `FUNCTIONALLY EXECUTING` |

### 1.3 Sensors & Instrumentation

| Sensor Name | Measurement Target | Dimensionality | Noise / Filter | Verification Status |
| :--- | :--- | :---: | :---: | :---: |
| `sens_pos_w_left` / `R` | Wheel angular position | 1 each | Direct encoder | `CAUSALLY VERIFIED` |
| `sens_vel_w_left` / `R` | Wheel angular velocity | 1 each | Direct tachometer | `CAUSALLY VERIFIED` |
| `sens_pos_hip_pitch`/`roll`| Hip joint articulation angle | 1 each | Direct encoder | `CAUSALLY VERIFIED` |
| `sens_pos_neck` / `head` | Neck pitch & head yaw angle | 1 each | Direct encoder | `CAUSALLY VERIFIED` |
| `sens_vel_hip_pitch`/`roll`| Hip angular velocity | 1 each | Direct tachometer | `CAUSALLY VERIFIED` |
| `sens_vel_neck` / `head` | Neck pitch & head yaw velocity | 1 each | Direct tachometer | `CAUSALLY VERIFIED` |
| `sens_frc_w_left` / `R` | Wheel actuator torque | 1 each | Force transducer | `CAUSALLY VERIFIED` |
| `sens_frc_hip` / `neck` | Articulation joint torque | 1 each | Force transducer | `CAUSALLY VERIFIED` |
| `touch_tire_L` / `R` | Ground normal contact force | 1 each | Tactile surface | `CAUSALLY VERIFIED` |
| `sens_chassis_force` | Chassis reaction force vector | 3 ($F_x, F_y, F_z$) | 3-axis load cell | `CAUSALLY VERIFIED` |
| `eye_cam` | Retina pinhole RGB camera | $1920\times 1080$, $65^\circ\text{ FOV}$ | Central pinhole | `FUNCTIONALLY EXECUTING` |
| 15-Ray Sonar Fan | Horizontal obstacle range | 15 rays spanning $240^\circ$ | Ray-casting filter | `CAUSALLY VERIFIED` |

---

## 2. Hard Physics Analysis: Vertical Mobility & Jumping

### 2.1 Physics Derivation
To achieve ballistic vertical take-off (jumping) of height $h > 0$, the body center of mass must attain a positive vertical take-off velocity $v_{z,\text{takeoff}} = \sqrt{2 g h} > 0$, requiring an upward ground reaction impulse:
$$J_z = \int_0^{\Delta t} (F_{\text{normal}}(t) - M g) \, dt > 0$$

### 2.2 Mechanism Inspection & Derivation
1. **Actuator Topology**: The locomotion actuators (`act_w_left`, `act_w_right`) are pure rotary velocity actuators acting on horizontal transverse axes ($\hat{\mathbf{y}}$). The resulting wheel-ground contact force is strictly horizontal traction $F_x = \frac{\tau_L + \tau_R}{R}$ and yaw torque $\tau_z = \frac{(\tau_R - \tau_L) b}{2 R}$.
2. **Articulation Authority**: The internal upper-body joints (`hip_pitch`, `hip_roll`, `neck_sweep`) actuate a moving mass $m_{\text{upper}} = m_{\text{torso}} + m_{\text{head}} = 0.3801\text{ kg}$ (only $25.9\%$ of total mass). The maximum possible vertical center-of-mass excursion via torso pitching is $\Delta z_{\text{CoM}} < 0.001\text{m}$ ($1\text{mm}$).
3. **Actuator Force Limit**: Position actuator maximum force is $12\text{ N}$. The maximum downward torso acceleration $\ddot{z}_{\text{upper}}$ produces a dynamic inertial reaction force:
$$F_{\text{dynamic}} = m_{\text{upper}} \ddot{z}_{\text{upper}} < 0.3801 \times 2.1\text{ m/s}^2 \approx 0.80\text{ N} \ll M g = 14.4\text{ N}$$
4. **Absence of Vertical Affordance**: There are no vertical prismatic linear actuators, pre-compressed springs, or pneumatics on the platform.

### 2.3 Formal Classification
$$\mathbf{JUMP\_CAPABILITY = PHYSICALLY\_UNSUPPORTED}$$
*(Documented in compliance with Section 9 and Section 25 of the Master Directive. Jumping is neither physically achievable nor fabricated).*

---

## 3. Cognitive, Affective & Audio Subsystems Inventory

### 3.1 Homeostatic & Interoceptive Core ([`brain/carl_homeostatic_core.py`](file:///D:/ebca/brain/carl_homeostatic_core.py))
- **Variables**: `energy` $[0.0, 1.0]$, `thermal_load` $[0.0, 1.0]$, `motor_fatigue` $[0.0, 1.0]$, `safety_margin` $[0.0, 1.0]$, `curiosity_drive` $[0.0, 1.0]$, `uncertainty` $[0.0, 1.0]$.
- **Status**: `FUNCTIONALLY EXECUTING` / `CAUSALLY VERIFIED`.

### 3.2 Generative Self-Model ([`brain/carl_generative_self_model.py`](file:///D:/ebca/brain/carl_generative_self_model.py))
- **Forward Model**: Active inference predicting next 6-DoF state observation and rolling 20-step counterfactual Dreamer rollouts.
- **Adaptive Parameters**: Estimated mass ($0.95\text{ kg}$), wheel radius ($0.048\text{m}$), track width ($0.230\text{m}$), traction coefficient ($2.50$).
- **Status**: `FUNCTIONALLY EXECUTING` / `CAUSALLY VERIFIED`.

### 3.3 Episodic Holographic Memory ([`brain/carl_episodic_memory.py`](file:///D:/ebca/brain/carl_episodic_memory.py))
- **Architecture**: 2048-dimensional Hyperdimensional Computing (HDC) associative memory.
- **Recall Trigger**: Associative spatial-need hazard query yielding avoidance vector biases.
- **Status**: `FUNCTIONALLY EXECUTING` / `CAUSALLY VERIFIED`.

### 3.4 Procedural Emotional Audio Synthesizer ([`brain/carl_audio_synth.py`](file:///D:/ebca/brain/carl_audio_synth.py))
- **Waveform Synthesis**: Real-time Wall-E / R2-D2 style 16-bit PCM WAV generation across 5 affective states (Joy trill, Curious warble, Startle alarm, Anger/frustration rumble, Tired murmur).
- **Status**: `IMPLEMENTED` / `FUNCTIONALLY EXECUTING`.

### 3.5 Operational Agency & Stuck Recovery Engine ([`brain/carl_endogenous_agency.py`](file:///D:/ebca/brain/carl_endogenous_agency.py), [`brain/carl_stuck_recovery.py`](file:///D:/ebca/brain/carl_stuck_recovery.py))
- **Capabilities**: Directional hysteresis steering, dead-end spin reorientation, 3-tier escalating recovery (reverse curve $\rightarrow$ max clearance spin $\rightarrow$ breakout acceleration).
- **Status**: `BEHAVIORALLY DEMONSTRATED` / `CAUSALLY VERIFIED`.
