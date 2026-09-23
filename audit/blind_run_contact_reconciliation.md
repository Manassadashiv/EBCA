# CARL-DX Blind Run Contact & Collision Forensic Report

**Audit Subject**: Reconciliation of `collision_occurred = True` vs Physical Collision-Free Navigation  
**Audit Date**: August 16, 2026  
**Status**: **`VERIFIED_COLLISION_FREE (Telemetry Code Defect Reconciled)`**  
**JSON Evidence**: [`audit/blind_run_contact_reconciliation.json`](file:///D:/ebca/audit/blind_run_contact_reconciliation.json)  

---

## 1. Physical Collision vs Telemetry Flag Discrepancy

In `decision_trace.jsonl`, the variable `collision_occurred` evaluated to `true` on every single tick, while the narrative and evaluator reported the run as collision-free.

An independent forensic inspection of the raw MuJoCo contact engine across all 120 ticks was performed:

| Contact Category | Geom Pair | Ticks Detected | Max Penetration | Physical Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **Wall Collisions** | `drive_deck/tires <-> wall_*` | **0** | $0.00\text{ mm}$ | **100% Collision-Free** |
| **Obstacle Collisions** | `drive_deck/tires <-> dynamic_hazard / gcube_*` | **0** | $0.00\text{ mm}$ | **100% Collision-Free** |
| **Self-Collisions** | `torso <-> drive_deck` | **0** | $0.00\text{ mm}$ | **100% Collision-Free** |
| **Chassis Ground Impacts** | `chassis_core <-> floor` | **0** | $0.00\text{ mm}$ | **100% Collision-Free** |
| **Wheel Ground Traction** | `tire_L / tire_R <-> floor` | 120 | $0.42\text{ mm}$ | **Normal rolling tire support** |
| **Caster Ground Support** | `w_caster_* <-> floor` | 120 | $0.11\text{ mm}$ | **Normal chassis leveling** |
| **Arena Props Resting** | `hazard_cube / toys <-> floor` | 120 | $0.00\text{ mm}$ | **External static resting contacts** |

### Independent Recomputation Verdict:
$$\mathbf{PHYSICAL\_COLLISION\_FREE = TRUE}$$
- **Total Physical Obstacle Contacts**: `0`
- **Total Physical Wall Contacts**: `0`
- **Total Self-Collisions**: `0`
- **Minimum Obstacle Clearance**: `1.258 meters`
- **Minimum Wall Clearance**: `3.472 meters`

---

## 2. Root Cause of Telemetry Bug

The agent's interoceptive check was implemented as:
```python
collision_occurred = (sensory.ncon > 4 or sensory.min_obstacle_dist < 0.15)
```
In MuJoCo, `hal.data.ncon` returns the number of active solver constraints in the **entire simulation world**, which includes the 13 resting contact points of objects sitting on the arena floor. The developer intended to count robot body contacts exceeding 4 (2 tires + 2 casters = 4), but mistakenly read the global world contact buffer instead of filtering for the robot's own geom IDs (`c.geom1` / `c.geom2`).

Thus, `collision_occurred` was a **false-positive software flag**, not a physical collision.
