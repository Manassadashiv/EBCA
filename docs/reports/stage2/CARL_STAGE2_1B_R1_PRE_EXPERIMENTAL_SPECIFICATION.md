# CARL STAGE 2.1B-R.1: RIGOROUS PRE-EXPERIMENTAL SPECIFICATION (LOCKED vFINAL)
**Document Identifier:** `CARL-SPEC-STAGE2.1B-R1-LOCKED-vFINAL`  
**Classification:** Embodied Neuromorphic Cognitive Architecture  
**Evaluation Standard:** Zero-Leakage Held-Out Falsification & Tripartite Benchmark Protocol  
**Date:** September 4, 2026  
**Status:** **PERMANENTLY LOCKED — READY FOR EXECUTION 🔒**  

---

### Task Alignment Declaration (Current-Stage Gate)

```text
CARL North Star:          The 5-Stage Evolutionary Organism
Current Stage:            Stage 2 — Generative World & Self Modeling
Current Subproblem:       Stage 2.1B-R.1 — Self-Model Grounding, Measurement Rectification & Entorhinal Aliasing
Lock Status:              ABSOLUTE PROTOCOL LOCK. The 3 final scientific corrections are incorporated.
                          No further modifications to this protocol may occur before execution.
```

---

## 1. The Three Final Protocol Corrections

1. **Task 3 Decision Logic De-Coupling:**
   * If Candidate A (Multi-Scale Coprime Grid) succeeds $\implies$ Entorhinal neural geometry is sufficient to resolve spatial aliasing over the tested range; remain within Stage 2.1.
   * If Candidate A fails $\implies$ Entorhinal multi-scale geometry is insufficient; **DO NOT automatically declare Place Cells mandatory**. The Independent Council will review the failure profile to determine whether Stage 2.2 is justified or if another representation is warranted.
2. **Strict Generalization Gate Partition:**
   * Development Seeds (`[42, 101, 202]`): Used strictly for model discovery, parameter estimation, and sanity checks.
   * **Primary Generalization Gate (`[303, 404, 505, 606, 707]`):** Evaluated strictly with the frozen model. The pass/fail determination is based exclusively on these 5 unseen seeds. Development scores are reported separately.
3. **One-Way Held-Out Validation Guarantee:**
   * The 200-step novel motor babbling trajectory is **strictly read-only**. It calculates prediction $R^2 \ge 0.85$ and is mathematically forbidden from updating weights or regression gains.

---

## 2. What CARL Actually Knows vs What It Does NOT Know

### What CARL Actually Knows (Verified):
1. **Vestibular Turn Discovery:** Discovers the gyroscope turn channel unsupervised from 25 anonymous sensor streams via babbling cross-covariance ($\mathbf{w}_{\text{rot}}$), achieving $\le 1.0^\circ$ heading error under active sensing.
2. **Stationary Working Memory:** Mexican-hat recurrence sustains a stable bump with $100\%$ amplitude retention and $0.000000^\circ$ drift over 10s of sensory silence.
3. **Attractor Basin Relaxation:** Recovers $100\%$ bump amplitude within 3–5 control ticks after violent shock ($\eta \sim \mathcal{N}(0, 2.0)$), preserving heading within $0.54^\circ - 5.23^\circ$.
4. **Local Path Integration:** Achieves $7.7\,\text{cm}$ ATE vs $11.5\,\text{cm}$ for classical Euler over a 350-tick exploration by filtering high-frequency noise.
5. **Slip Gating:** Detects glaze-ice wheel slip via acceleration chatter variance ($\sigma(a_x) < 0.35$).

### What CARL Does NOT Know (The Exact Failure Modes):
1. **Rotating in the Dark (Stationary Latch):** In blackout, the CANN has no motor efference copy, so its bump stays pinned at $-45.2^\circ$ while the body turns $120^\circ$, causing **$120.6^\circ$ error** (failing the $< 30^\circ$ gate).
2. **Which Copy of the World It Is In (Repeating Wallpaper):** The single 2D grid torus repeats every $\lambda = 0.80\,\text{m}$. Position $\mathbf{x}$ and periodic aliases $\mathbf{x} + \mathbf{k}\lambda$ have identical firing rates.
3. **Global Metric Distance:** Homing steering computes wrapped phase differences, steering toward the nearest periodic replica of the origin and causing **$1.45\,\text{m}$ homing drift** (homing to ghost origins).

---

## 3. The Three Tasks of Stage 2.1B-R.1

```text
========================================================================================
                          STAGE 2.1B-R.1 THREE-TASK PROTOCOL
========================================================================================

TASK 1: Measurement Rectification (Preserving Artifacts & Correcting Formula)
  • Preserve original evidence/stage2_1b_r/stage2_1b_r_telemetry.json intact.
  • Re-run Battery 2 shock recovery using population vector length:
        R(t) = || sum_i r_i(t) * e^{j theta_i} ||
  • Log both original formula (0.657 / 4.770 = 13.8%) and corrected ratio
    (4.770 / 4.770 = 100.0%) side-by-side in evidence/stage2_1b_r1/stage2_1b_r1_ledger.json.
  • Zero changes to CANN brain code.

TASK 2: Learned Motor Efference Blackout Test (Freeze & Causal Controls)
  • Phase A (Development on Seeds [42, 101, 202]):
      - Babbling dataset 1 (400 steps): learn w_rot and k_eff via least-squares:
            k_eff = sum_t (u_R - u_L) * (s_t . w_rot) / sum_t (u_R - u_L)^2
      - Held-Out Babbling dataset 2 (200 novel steps): validate prediction (READ-ONLY, NO UPDATES):
            R^2 = 1 - sum(omega_sensory - k_eff * Delta u)^2 / sum(omega_sensory - mean)^2
      - Gate: R^2 >= 0.85 required before freezing.
      - FREEZE w_rot and k_eff PERMANENTLY.
  • Phase B (Primary Generalization Test on Unseen Seeds [303, 404, 505, 606, 707]):
      - Evaluate frozen k_eff across 90 ticks (2.7s) sensory blackout under active turning.
      - 4-Way Causal Controls evaluated in parallel:
          Substrate A: Sensory-Only CANN (I_shift = 0 in blackout)
          Substrate B: CANN + Correct Frozen Efference (hat{omega} = k_eff * Delta u)
          Substrate C: CANN + Inverted Efference (hat{omega} = -k_eff * Delta u)
          Substrate D: Calibrated Classical Baseline
      - Primary Generalization Gate: Substrate B post-dropout error < 30.0 deg across ALL 5 unseen seeds.
      - Causal Gate: Substrate B (< 30 deg) must beat Substrate C (> 150 deg).

TASK 3: Entorhinal Spatial Aliasing Showdown (Multi-Scale vs Wrap Counter)
  • Wander trajectory of 350 ticks (> 1.25m from origin, crossing 0.80m torus boundary).
  • Two Candidate Representations Evaluated:
      Candidate A: Multi-Scale Coprime Grid Modules (Recurrent Neural Spatial Representation)
                   Module 1: 32x32 torus, lambda_1 = 0.80m
                   Module 2: 32x32 torus, lambda_2 = 1.15m
                   Exact common period: 18.40m. Joint vector homing law.
      Candidate B: Integer Phase-Winding Register (Explicit Engineered Coordinate Control)
                   Single 32x32 torus (lambda = 0.80m) + winding registers (k_x, k_y) in Z.
  • Measure: Homing return drift (m), computational latency (ms), parameter count.
  • Dual Verdict Structure:
      - Engineering Verdict: Which representation achieves homing drift <= 0.22m?
      - Scientific Verdict: Does multi-scale entorhinal geometry solve global homing
        without requiring Hippocampal Place Cells? If Candidate A fails, Council reviews
        whether Stage 2.2 is justified (no automatic jump).
========================================================================================
```

---

## 4. Pre-Registered Hypotheses & Acceptance Criteria

| Task / Battery | Hypothesized Phenomenon | Primary Acceptance Gate | Failure Threshold |
| :--- | :--- | :--- | :--- |
| **Task 1: Measurement Rectification** | Attractor basin recovers solitary bump | Corrected $R_{\text{post}} / R_{\text{pre}} \ge 90.0\%$ in $\le 6$ ticks across all seeds | $R_{\text{post}} / R_{\text{pre}} < 80.0\%$ |
| **Task 2: Efference Validation** | Linear self-model predicts turning on held-out data | Read-only held-out validation $R^2 \ge 0.85$ on Dev seeds | $R^2 < 0.80$ |
| **Task 2: Generalization Gate** | Frozen efference guides bump during 2.7s blackout | **Substrate B Mean error $< 30.0^\circ$ across the 5 unseen seeds** (`[303, 404, 505, 606, 707]`) | Substrate B Mean error $\ge 30.0^\circ$ |
| **Task 2: Causal Isolation** | Correct vs Inverted efference proves model specificity | Substrate B error $< 30^\circ$ AND Substrate C error $> 150^\circ$ on unseen seeds | Substrate C $\le 60^\circ$ (model non-specific) |
| **Task 3: Global Homing (Eng)** | Homing return from $> 1.25\,\text{m}$ | Candidate achieving final distance $d \le 0.22\,\text{m}$ | All candidates drift $> 0.50\,\text{m}$ |
| **Task 3: Entorhinal Geometry (Sci)** | Multi-scale coprime grid solves aliasing | Candidate A achieves $d \le 0.22\,\text{m}$ $\implies$ Entorhinal sufficient | Candidate A fails ($d > 0.50\,\text{m}$) $\implies$ **Council reviews Stage 2.2 justification** |

---

## 5. Stop/Go Roadmap Rule

```text
                               STAGE 2.1B-R.1 EVALUATION
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [Task 2 Blackout FAILS]                       [Task 2 Blackout PASSES]
         (Error >= 30 deg on Unseen seeds)             (Error < 30 deg on Unseen, Inverted C > 150 deg)
                  │                                               │
                  ▼                                               ▼
         STAY IN STAGE 2.1                               EVALUATE TASK 3
         (Investigate unmodeled slip &                            │
          non-linear tire dynamics)              ┌────────────────┴────────────────┐
                                                 ▼                                 ▼
                                       [Candidate A PASSES]              [Candidate A FAILS]
                                       (Multi-scale grid homes)          (Multi-scale grid aliases)
                                                 │                                 │
                                                 ▼                                 ▼
                                        STAGE 2.1 CERTIFIED               COUNCIL REVIEWS EVIDENCE:
                                        (Entorhinal space sufficient;     Does Task 3 justify Stage 2.2
                                         advance to Stage 2.3 World Model) Place Cells, or another path?
```

**Permanently Ratified & Locked:** September 4, 2026.
