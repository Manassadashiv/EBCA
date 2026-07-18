# CARL-Ω Project Customizations & Rules

## Persistent Project Context

* **Project Progress Summary**:
  * **Overall Project (Phase 1 + Phase 2)**: **34.4% Complete**
  * **Phase 1: Digital Twin (Mini Project)**: **62.5% Complete**
    * Codebase Modules: 100% Written (HDC, LSM, STDP, IK, posturing).
    * Active Integration: 25% Connected (Wheeled simulation is active with LSM and place cells; primate body, limbs, expressions, and RNN imagination are currently standalone).
  * **Phase 2: Physical Hardware (Major Project)**: **0% Complete** (Planned).

## Key Implementation Constraints
* **Sonar Array**: Mapped as a 12-sonar physical ultrasonic array (each with a $30^\circ$ cone) interpolated software-side to 24 virtual sonar rays.
* **Camera Coordinate Frame**: Corrected camera mapping formula:
  $$\text{angle\_cam} = (0.5 - c_x / \text{img\_width}) \times \text{fov\_rad}$$
  Matched to sonar array using:
  $$\text{angle\_body} = \text{angle\_cam} + \text{head\_pan}$$
  with angular wrap-around comparison.
