# CARL Stage 2.2-R2: Adversarial Pre-Mortem Analysis (v2.1 Hardened)
**Document Classification:** Authoritative Forensic Pre-Mortem Audit  
**Milestone:** Stage 2.2-R2 — Modular Action-Conditioned Predictive World Model  
**Status:** **COMPLETE — PRE-IMPLEMENTATION AUDIT (Frozen Prior to Code Execution)**  
**Governing Principle:** *The Reality Principle: Internal self-consistency is not world modeling; physical reality is the sole judge.*

---

## 1. Executive Summary & Audit Context

Following the failure of monolithic recurrent models in Phase 1 (where models exploited sensory persistence, ignored actions, and collapsed on dynamic transitions), Stage 2.2-R2 established a modular decoupled architecture:
$$\text{Actions } u_t \longrightarrow \text{Body/Ego Model } (\mathcal{M}_{\text{body}}) \longrightarrow \text{Predicted Displacement } \Delta \hat{\mathbf{p}} \longrightarrow \text{Spatial Occupancy Memory } (\mathcal{M}_{\text{env}}) \longrightarrow \text{Predicted Sonar } (\mathcal{M}_{\text{sensor}})$$

In v2.0, the core "Reality Principle" was established: all counterfactual mental predictions must be evaluated against independent physical rollouts in MuJoCo.
In this **v2.1 Hardened Audit**, we resolve the remaining 5 critical vulnerabilities and establish strict process-level computational isolation:
1. **Physical Coasting Semantics:** Correcting the contradiction between $u=0$ and instantaneous halt.
2. **Deterministic Gate 5 Pair Selection:** Pre-registering and freezing an objective $N=50$ pair manifest before evaluation, completely eliminating cherry-picking.
3. **Randomized Action Sequences (Gate 6):** Adding $K=16$ continuously sampled random action sequences to prevent action template memorization.
4. **Alternate Reality Attraction (Gate 5 Swap):** Requiring swapped memory to move closer to the swapped ground truth rather than merely causing non-specific degradation.
5. **Genuinely Novel Unseen Test Environments:** Requiring procedural geometry, obstacle layouts, spawn poses, and friction variations to be generated only after freeze.
6. **Subprocess Air-Gap During Mental Rollout:** Completely isolating the mental world model from MuJoCo, the environment handle, and simulator memory.

---

## 2. Deep Dive: The 5 Hardening Patches & Computational Isolation

### Vulnerability 1: The "u = 0 Means Zero Movement" Contradiction
#### The Flaw Identified
In earlier drafts, Module 1 was described as "zeroing action mathematically stops forward movement," while Gate 3 tested whether the model accurately tracked physical deceleration and coasting. This created an internal contradiction: if a moving robot receives $u=0$, its wheels do not instantly lock to zero velocity; it coasts under momentum and rolling friction until it halts. If we had hardcoded `if u==0: dp=0`, Module 1 would fail physical coasting evaluation!

#### The Structural Defense (True Dynamic Coasting Semantics)
Module 1 receives proprioceptive state $s^{\text{body}}_t = [\text{wheel\_vel}, \text{gyro\_yaw}, \text{joint\_angles}]$ and action $u_t$.
$u_t = 0$ denotes **zero additional motor command / torque**, NOT zero velocity:
```text
u = 0
   ↓
motor torque = 0
   ↓
existing velocity + friction/inertia
   ↓
possible continued motion (coasting)
   ↓
eventual halt
```
Module 1 must learn this dynamic physical deceleration. Under Gate 3, when the physical robot coasts to a halt on $\mathcal{T}_{\text{zero}}$, Module 1 must predict the continuous deceleration curve, achieving $R^2 \ge 0.60$ against physical reality.

---

### Vulnerability 2: Statistical Cherry-Picking in Gate 5 Pair Selection
#### The Flaw Identified
The instruction to "identify episode pairs with similar sensors but different memory" left room for an unscrupulous or biased evaluation:
```text
Generate 1000 candidate pairs
        ↓
Inspect which pairs look best
        ↓
Select the beautiful pairs
        ↓
PASS (p < 0.01)
```
This post-hoc selection would invalidate statistical significance.

#### The Structural Defense (Deterministic Pre-Registered Matching Protocol)
To make cherry-picking mathematically impossible, pair selection is executed via a deterministic, frozen algorithm:
1. **Candidate Pool Generation:** Extract all episode pairs from developmental validation data (`DEV_VAL`).
2. **Fixed Physical Tolerances:** Filter by:
   - $\|s^{(i)}(t_0) - s^{(j)}(t_0)\|_\infty \le 0.35\,\text{m}$ (sonar equivalence).
   - $\|s^{\text{body},(i)}(t_0) - s^{\text{body},(j)}(t_0)\|_\infty \le 0.10$ (proprioceptive equivalence).
   - Mapped obstacle clearance along turn direction differs by $\ge 1.0\,\text{m}$ (spatial memory divergence).
3. **Deterministic Similarity Ranking:** Compute $d_{ij} = \|s^{(i)}(t_0) - s^{(j)}(t_0)\|_2 + \|s^{\text{body},(i)}(t_0) - s^{\text{body},(j)}(t_0)\|_2$.
4. **Frozen Selection:** Select the top $N = 50$ pairs ranked by minimum $d_{ij}$.
5. **Frozen Manifest Lock:** Write the exact pair indices to `frozen_tripartite_evaluation_pairs.json` **before** computing any model predictions.
6. **No Post-Hoc Inspection:** Zero outcome metrics can be inspected prior to manifest lock. The Wilcoxon signed-rank test ($p < 0.01$) uses these pre-registered $N=50$ pairs.

---

### Vulnerability 3: Action Template Memorization (Gate 6)
#### The Flaw Identified
Evaluating only four canonical actions (Forward, Left, Right, Reverse) allows a sufficiently high-capacity model to memorize discrete input-output mappings:
- `[0.8, 0.8]` $\to$ Forward template
- `[-0.7, 0.7]` $\to$ Left template
- `[0.7, -0.7]` $\to$ Right template
- `[-0.6, -0.6]` $\to$ Reverse template
This would pass the gate without learning a general, continuous action-conditioned world model.

#### The Structural Defense (Randomized Continuous Sequences & Execution Isolation)
Gate 6 requires passing:
1. **The 4 Canonical Branches (Mandatory):** Forward, Hard Left, Hard Right, Hard Reverse.
2. **$K = 16$ Randomized Continuous Action Sequences:**
   - Generated from a frozen evaluator PRNG (`seed=20260905`) instantiated strictly **after** model freeze.
   - Continuously sampled steering commands $u_L, u_R \in [-1.0, 1.0]$.
   - Random horizons $H \in [5, 15]$ steps.
   - Mixed acceleration and turning profiles.
3. **Execution-Isolation & Non-Selectivity Invariant:**
   The evaluator freezes starting state $\mathbf{S}_0$ and all $4 + 16 = 20$ action sequences into a locked manifest (`frozen_branch_sequences.json`) **before** any model predictions or outcome inspection. Physical rollouts are generated independently in MuJoCo. The mental model runs without seeing those trajectories. **No action sequence may be selected, removed, substituted, or rerun based on its outcome.**
4. **Mandatory Per-Branch Pass (Zero Aggregate Cloaking):**
   Every single branch $k \in \{1, \dots, 20\}$ must INDIVIDUALLY achieve $R^2 \ge 0.50$ and diagonal dominance ($\text{margin} \ge 0.30\,\text{m}$). An aggregate average is strictly insufficient; 19 passing branches cannot hide 1 failing branch. Granular per-branch metrics are published in the scorecard.

---

### Vulnerability 4: Non-Specific Memory Degradation (Gate 5 Directional Swap)
#### The Flaw Identified
If memory is scrambled or swapped, any model that relies on memory as a generic capacity expansion will suffer increased error. Merely showing that error increases on the original trajectory does not prove the memory contains *veridical geometric boundaries*.

#### The Structural Defense (Causal Alternate Reality Attraction)
When memory maps are swapped ($\mathbf{M}_1 \leftrightarrow \mathbf{M}_2$), the prediction must be **directionally attracted to the ground truth of the alternate reality**:
```text
Error(swapped M1 → episode 2 reality) < Error(swapped M1 → episode 1 reality)
and
Error(swapped M2 → episode 1 reality) < Error(swapped M2 → episode 2 reality)
```
- **Mandatory Threshold:** This condition must hold for $\ge 85\%$ of the $N=50$ pre-registered pairs.
- **Statistical Significance:** Paired Wilcoxon signed-rank test proves that the swapped prediction is significantly closer to the alternate physical reality ($p < 0.01$).
*This mathematically proves that $\mathbf{M}_2$ contains the specific geometric obstacle layout of Episode 2.*

---

### Vulnerability 5: Superficial Seed Novelty in Unseen Evaluation
#### The Flaw Identified
If the primary unseen test set uses "new seeds" but the procedural generator produces the identical square room topology and obstacle distribution, the test evaluates seed interpolation rather than genuine environmental generalization.

#### The Structural Defense (Procedurally Novel Arena Topologies)
For `PRIMARY_UNSEEN_TEST`, the following parameters are compiled and frozen strictly **after** architecture and weights are locked:
1. **Arena Geometry:** Novel multi-compartment layouts (L-shaped corridors, T-junctions, variable corridor widths $\in [1.2\,\text{m}, 3.5\,\text{m}]$).
2. **Obstacle Layouts:** Unseen pillar counts, asymmetric placements, and distinct obstacle cross-sections.
3. **Spawn Pose Distribution:** Unvisited coordinates and orientations.
4. **Friction Variations:** Surface friction patches $\mu \in [0.05, 1.2]$ (glaze ice, smooth tile, high traction).
5. **Action Sequences:** Independent trajectory PRNG.

---

### Vulnerability 6: Sensor Peeking & Process Reachability
#### The Flaw Identified
Even if `mj_ray()` is not called directly, if the mental model process shares memory space with the simulator or environment object, indirect pointer dereferencing or hidden cache access could leak ground-truth spatial geometry.

#### The Structural Defense (Subprocess Air-Gap Architecture)
```text
                  PHYSICAL WORLD
                       │
               ┌───────┴────────┐
               │                │
          Mental model      Evaluator
         (Air-gapped)       (MuJoCo)
               │                │
               ▼                ▼
          prediction       real rollout
               │                │
               └───────┬────────┘
                       ▼
                    COMPARE
```
During mental rollout execution:
- The mental world model runs in an isolated subprocess.
- MuJoCo is actively poisoned (`sys.modules['mujoco'] = None`).
- Zero handles to `CarlStage1HAL`, `env`, or simulator objects exist.
- Evaluator executes physics rollouts in a separate step *after* mental rollouts are serialized.

---

## 3. Pre-Mortem Attack & Defense Matrix (v2.1)

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       ADVERSARIAL PRE-MORTEM MATRIX v2.1                                        │
├────────────────────┬─────────────────────────────┬───────────────────────────────┬──────────────────────────────┤
│ ATTACK VECTOR      │ HOW THE CHEAT WOULD OPERATE │ WHY PHASE 1 FELL FOR IT       │ HOW R2 STRUCTURALLY BLOCKS IT│
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 1. Manufactured    │ Outputs distinct constant   │ Gate 6 only tested pairwise   │ Requires R² >= 0.50 against  │
│    Branching       │ vectors for each branch to  │ divergence:                   │ true physical branch AND     │
│    Divergence      │ manufacture divergence.     │ ||s_A - s_B|| >= 0.80 m.      │ diagonal dominance (>=0.30m).│
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 2. Action Template │ Memorizes 4 fixed action    │ Only 4 discrete actions       │ Adds K=16 randomized         │
│    Memorization    │ vectors ([0.8,0.8], etc.)   │ were tested.                  │ continuous action sequences  │
│                    │ as lookup keys.             │                               │ with random durations.       │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 3. Action Zeroing  │ Defaults to global arena    │ Only evaluated u=0 on active  │ Requires u=0 prediction to   │
│    Spurious Shift  │ mean clearance, shifting    │ physical trajectory; did not  │ match physical coasting run  │
│                    │ error without understanding.│ test physical coasting run.   │ (R² >= 0.60) and fail active.│
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 4. Hidden-State    │ Uses memory vector as a     │ Scramble test was diagnostic; │ Tripartite test with swap:   │
│    Cache Cheat     │ high-capacity recurrent     │ did not control for identical │ must attract to alternate    │
│                    │ shortcut without geometry.  │ current sensor + body state.  │ physical reality (p < 0.01). │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 5. Statistical     │ Generates 1000 candidate    │ Pair selection protocol was   │ Deterministic algorithm      │
│    Cherry-Picking  │ pairs and selects best-     │ unspecified.                  │ pre-registers top N=50 pairs │
│                    │ looking pairs post-hoc.     │                               │ before outcome inspection.   │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 6. Inert           │ Coordinates treated as      │ No mandatory falsification    │ Gate 4 is a mandatory pass   │
│    Coordinates     │ generic regressors; ignores │ gate on memory destruction;   │ gate: Erased memory MUST     │
│    Bypass          │ actual obstacle grid cells. │ no swap intervention.         │ surge error >= +25%.         │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 7. Proprioceptive  │ Body model gets R² = 0.95,  │ Metrics were averaged into    │ Strict lexical hierarchy:    │
│    Masquerade      │ world gets R² = 0.10; claims│ a composite score, hiding     │ Body has 0% compensatory     │
│                    │ "0.80 average fidelity".    │ environmental failure.        │ weight for world gates.      │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 8. Persistence     │ Copies current sonar:       │ Evaluated on flat arena floor │ Module 3 has no sonar input; │
│    Free-Rider      │ s_{t+H} ≈ s_t or Δs ≈ 0.    │ where 80% of steps are static │ evaluated strictly on        │
│                    │                             │ (|Δs| < 0.15 m).              │ D_dynamic (|Δs| >= 0.15 m).  │
├────────────────────┼─────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 9. Test Set        │ Architectural choices tuned │ Test seeds were accessible    │ Seeds [303,404,505,606,707]  │
│    Overfitting     │ on held-out test seeds.     │ during development.           │ STRICTLY FORBIDDEN from      │
│                    │                             │                               │ existing until Phase D lock. │
└────────────────────┴─────────────────────────────┴───────────────────────────────┴──────────────────────────────┘
```

---

## 4. Certification

All identified failure modes have been formally analyzed and structurally blocked. The specification represents an airtight, ungameable benchmark for Stage 2.2-R2. **Implementation remains frozen awaiting final user authorization.**
