# CARL Stage 3: Implementation Plan & Engineering Roadmap
## Operational Blueprint for Autonomous Behavioral Discovery (CARL-STAGE3-PLAN-2026-09-08)

---

### Implementation Phases & Milestones

| Phase | Module | Target File | Core Functionality | Deliverable |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 3.1** | **MPPI Controller Core** | `brain/carl_stage3_mppi.py` | Vectorized 128-sample trajectory optimizer over unlabelled 6-D motor space | Real-time optimizer ($p95 \le 35\,\text{ms}$) |
| **Phase 3.2** | **Active Inference Engine** | `brain/carl_stage3_active_inference.py` | Expected Free Energy (EFE) functional, homeostatic & epistemic drive | Intrinsic reward calculator |
| **Phase 3.3** | **Motor Synergy Library** | `brain/carl_motor_synergies.py` | Online clustering and catalog of discovered motor primitives | Compact synergy embeddings |
| **Phase 3.4** | **Experimental Harness** | `brain/test_stage3_battery_runner.py` | Automated battery suite (3A: U-Trap, 3B: Ice Slip, 3C: Impairment) | 150-episode test harness |
| **Phase 3.5** | **Evidence & Visualization** | `brain/plot_stage3_evidence.py` | Multi-panel publication dashboards and trajectory plots | Publication figures & video generator |
| **Phase 3.6** | **Gate Closure & Audit** | `CARL_STAGE3_FINAL_REPORT.md` | Statistical verification, scorecard generation, sign-off | Formal scientific audit |

---

### Step-by-Step Implementation Sequence

#### Step 1: Implement Vectorized MPPI Trajectory Optimizer (`brain/carl_stage3_mppi.py`)
- Define `CARLStage3MPPI` class.
- Vectorize $M=128$ Gaussian perturbations across $H=15$ steps using PyTorch tensor operations.
- Parallel forward unrolling through `GroundedKinematicBodyModel` and `arena_occupancy_grid.pt` grid-sampling.
- Warm-starting control buffer with discount shift.

#### Step 2: Implement Active Inference & Expected Free Energy Module (`brain/carl_stage3_active_inference.py`)
- Define `ActiveInferenceCore`.
- Compute pragmatic cost (collision penalty, battery degradation, forward progress).
- Compute epistemic information gain using spatial occupancy entropy reduction:
  $$\Delta \mathcal{H} = \sum_{x \in \text{FOV}} -p(x) \log_2 p(x)$$
- Balance exploration vs. exploitation via adaptive precision parameter $\gamma$.

#### Step 3: Implement Motor Synergy Genesis (`brain/carl_motor_synergies.py`)
- Monitor trajectory returns; when return exceeds 95th percentile, compress trajectory sequence via PCA.
- Maintain library of named synergies (`synergy_corridor_cruise`, `synergy_flank_escape`, `synergy_hook_reverse`).
- Bi-directional blending: MPPI samples around top-matching synergy rather than zero-mean Gaussian.

#### Step 4: Author Stage 3 Validation Harness (`brain/test_stage3_battery_runner.py`)
- Setup automated test battery:
  - Battery 3A: 50 trials in U-shaped convex trap (`world/vessel_kinetic.xml` trap sub-arena).
  - Battery 3B: 50 trials with mid-run floor friction drop ($\mu = 1.0 \to 0.05$).
  - Battery 3C: 50 trials with left wheel actuator torque degradation ($k_{\text{gain}} = 0.50$).
- Collect full telemetry (cross-track error, collision flag, latency, synergy activation).

#### Step 5: Verification & Gate Certification Suite
- Execute `python brain/test_stage3_battery_runner.py`.
- Verify all 7 pre-registered acceptance criteria:
  1. $p95$ latency $\le 35.0\,\text{ms}$.
  2. Battery 3A escape rate $\ge 90.0\%$.
  3. Battery 3B slip spin-outs $\le 10.0\%$.
  4. Battery 3C cross-track drift $\le 0.20\,\text{m}$.
  5. Epistemic map entropy reduction $\ge 40.0\%$.
  6. Statistical significance $p < 0.001$.
  7. Zero privileged coordinate injection verified.

---

### Pre-Requisites & Verification Commands
```bash
# Verify Stage 2.3-R1 Certification Scorecard
python -c "import json; s=json.load(open('evidence/stage2_3_r1/stage2_3_r1_scorecard.json')); print('Stage 2.3-R1 Status:', s['verdict'])"

# Stage 3 Dependency Check
python -c "import torch, mujoco; print('PyTorch version:', torch.__version__, '| MuJoCo version:', mujoco.__version__)"

# Launch Stage 3 Validation Battery (when implemented)
python brain/test_stage3_battery_runner.py --episodes 150 --seed 20260908
```
