# CARL-DX LIVE VS BENCHMARK EXECUTION DIVERGENCE & PRE-REPAIR FORENSIC ANALYSIS

**Mission Standard**: NASA-Inspired Systems Engineering Rigor (Zero-Trust)  
**Deliverable**: Root Cause Reconciliation of Live Playground vs Benchmark Behavioral Divergence

---

## 1. Executive First-Difference Analysis Table

| Domain / Parameter | Live Playground (`carl_live_playground.py`) | Benchmark Suite (`carl_adversarial_emergence_harness.py`) | Divergence Magnitude / Impact | Root Cause & Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Physics Sub-Stepping Rate** | `for _ in range(8): mujoco.mj_step()` ($\Delta t_{\text{phys}} = 0.080\text{s}$) | `for _ in range(3): hal.step()` ($\Delta t_{\text{phys}} = 0.030\text{s}$) | **$2.67\times$ Over-stepping Mismatch** | Agent's internal forward model assumes $dt = 0.0333\text{s}$. Live playground moves robot $2.4\times$ farther per cognitive cycle than the planner predicts. |
| **Arena Wall Positions** | `setup_fun_playground()` relocates 6 inner walls | Default XML positions / programmatic scenario layouts | **Spatial Geometry Divergence** | Relocated walls create different corridor widths not present in the benchmark suite. |
| **Perimeter Boundary Hardcoding** | Rays check boundary at $\pm 2.60\text{m}$, veto at $\pm 2.35\text{m}$ | Same hardcoded $\pm 2.60\text{m}$ | **Model-vs-World Mismatch** | `vessel_kinetic.xml` defines actual outer walls at $\pm 5.00\text{m}$. The agent perceives a phantom perimeter wall at $x, y = \pm 2.60\text{m}$. |
| **BRAKE_REST Deadlock Loop Trigger** | Idling in `BRAKE_REST` (cmd_v = 0.0) bypasses stuck detector | Same | **Stuck Detector Blind Spot** | `CarlStuckDetector` only flags stalls when commanded velocity $>0.05\text{ m/s}$. If Dreamer selects `BRAKE_REST`, the stuck detector treats it as intended rest rather than a stall. |

---

## 2. Reproduction of the User-Observed BRAKE_REST / Loop Failure

### Failure Trace Log (Live Playground Execution with 8x Sub-stepping):
- **Tick 110 to 125**: Robot approaches wall at $x = 1.80\text{m}$, speed $v = 0.21\text{ m/s}$.
- **Tick 130**: Sonar detects front obstacle at $0.75\text{m}$. Dreamer attempts deceleration by selecting `BRAKE_REST`.
- **Tick 135 to 140**: Robot comes to complete stop ($v = 0.026\text{ m/s}$) at $(x=1.909, y=0.232)$.
- **Tick 140+**: Because front clearance is low, candidate forward actions have collision risk. Because the robot is stationary with `cmd_v = 0.0`, `CarlStuckDetector` does not increment stuck confidence because it assumes the agent chose to remain parked.
- **Result**: **`BRAKE_REST` Stall Deadlock** until manual user interaction (mouse drag or reset).

---

## 3. Pre-Repair Forensic Status Summary
- **First Causal Divergence Point**: Physics sub-stepping mismatch ($8\times$ vs $3\times$) coupled with stuck detector ignoring zero-command stalls when obstacles block forward motion.
- **Pre-Repair Verification Status**: **`PRE_REPAIR_DIAGNOSIS_COMPLETE`**.
- **Next Required Step**: Synchronize live playground sub-stepping to 3 sub-steps ($0.03\text{s}$), update stuck detector to detect stationary deadlock under low clearance regardless of command velocity, and align perimeter raycast limits with actual XML wall coordinates ($\pm 5.0\text{m}$).
