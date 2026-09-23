# CARL-DX Phase 1-R4: Forensic Telemetry Audit Report

**Date**: August 24, 2026  
**Subject**: Forensic Investigation of Episode 1 Route Selection & STDP Causal Attribution in P1-R4 Isolation  
**Official Forensic Verdict**: **`NOT CAUSAL (FOR DOWNSTREAM HAZARD DETOUR) — LEVEL 1 CLASSIFICATION`**

---

## 1. Executive Summary: What the Telemetry Actually Proves

A rigorous, tick-by-tick forensic trace of [`evidence/p1_r4_isolation/telemetry/P1R4_ISOLATION_NO_HDC_STDP_S42_EP1.csv`](file:///d:/ebca/evidence/p1_r4_isolation/telemetry/P1R4_ISOLATION_NO_HDC_STDP_S42_EP1.csv) demonstrates that:

1. **Episode-1 North Choice Did NOT Originate from Downstream Obstacle Avoidance**:
   - The robot selected **`ROUTE_A (North)`** in Episode 1 long before it ever approached the downstream barrier at $(1.45, -0.55\text{ m})$.
2. **The Exact Cause was Startup Physical Inertia (Tick 1)**:
   - When launching from rest $(v = 0.0\text{ m/s})$ at Tick 0, the motor commanded a target velocity $v_{\text{est}} \approx 0.225\text{ m/s}$.
   - At **Tick 1** ($x = 0.0001\text{ m}$), the chassis was still accelerating ($v \approx 0.01\text{ m/s}$), producing a motor prediction error surge:
     $$\text{PE} = |0.01 - 0.225| = \mathbf{0.2141\text{ m/s}} > 0.180\text{ m/s}$$
   - This startup acceleration lag triggered the STDP surprise gate ($\text{valence} = -1.0$), updating and depressing the synaptic weights connected to `SWERVE_RIGHT` (the action taken at Tick 1).
3. **Early Action Divergence at Tick 2 ($x = 0.0003\text{ m}$)**:
   - At **Tick 2**, because `SWERVE_RIGHT` had its synaptic weights depressed ($Q_{\text{stdp}}(\text{SWERVE\_RIGHT}) < 0$), Active Inference evaluated `SWERVE_LEFT` as having lower Expected Free Energy ($545.57 < 545.58$).
   - This small early steering bias caused the robot to curve Northward at the entrance, never entering the South corridor in Episode 1.
4. **Episodes 2–8 Merely Persisted This Startup Artifact**:
   - Because CARL went North in Episode 1, it never experienced the South barrier. In subsequent episodes, it simply retained the startup-induced Northward bias.

---

## 2. Answers to the Eight Specific Audit Requirements

### (1) Exact Episode-1 Route Choice Tick and Cause
- **Commitment Tick**: **Tick 84** ($x = 0.3529\text{ m}, y = +0.1560\text{ m}$, Route: `ROUTE_A (North)`).
- **Physical Root Cause**: Startup acceleration lag at **Tick 1** produced $\text{PE} = 0.2141\text{ m/s}$, depressing `SWERVE_RIGHT` synapses at $x = 0.0001\text{ m}$ and causing an immediate switch to `SWERVE_LEFT` at **Tick 2** ($x = 0.0003\text{ m}$).

### (2) Initial $W$ Matrix Statistics Before Learning (Tick 0)
- $W \equiv 0.0$ ($22 \times 7$ zeros).
- $\|W\|_F = \mathbf{0.000000}$, $\text{mean}(W) = \mathbf{0.000000}$, $\text{var}(W) = \mathbf{0.000000}$.
- Synaptic weights were un-biased at initialization.

### (3) $Q_{\text{stdp}}$ for all 7 Actions Before Any Learning (Tick 0)
- $Q_{\text{stdp}}(S) = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]$ across all 7 action primitives.

### (4) First Tick Where STDP Changes $W$
- **Simulation Tick 1** ($x = 0.0001\text{ m}, y = 0.0000\text{ m}$).
- $\|\Delta W\| = \mathbf{0.000090}$, $\|W\| = \mathbf{0.000100}$.

### (5) First Tick Where STDP Changes Action Ranking / Policy
- **Simulation Tick 2** ($x = 0.0003\text{ m}, y = 0.0000\text{ m}$).
- `NO_HDC_NO_STDP` chose: `SWERVE_RIGHT` ($\text{EFE} = 545.58$).
- `NO_HDC_STDP` chose: `SWERVE_LEFT` ($\text{EFE} = 545.57$).

### (6) Did the Episode-1 North Behavior Exist Before Learning?
- **NO at Tick 0** ($W=0$, perfect symmetry).
- **YES at Tick 2** ($x = 0.0003\text{ m}$), caused by startup acceleration prediction error rather than downstream barrier interaction.

### (7) Does a Genuine Later STDP-Caused Behavioral Transition Exist?
- **NO.** The robot did not encounter the downstream obstacle at $(1.45, -0.55\text{ m})$ in Episode 1 because it had already diverged North at $x = 0.0003\text{ m}$. Subsequent episodes merely persisted this startup-induced bias.

### (8) Final Forensic Verdict
- **`NOT CAUSAL (FOR DOWNSTREAM HAZARD DETOUR)`**
- **Correct Emergence Classification**: **`LEVEL 1: STDP ACTIVE AND WEIGHTS CHANGE (STARTUP INERTIA ARTIFACT)`**.

---

## 3. Forensic Telemetry Comparison (Ticks 0–5)

| Tick | Longitudinal $x$ | Metric | `NO_HDC_STDP` (STDP Active) | `NO_HDC_NO_STDP` (Control Baseline) |
| :---: | :---: | :---: | :---: | :---: |
| **0** | $0.0000\text{ m}$ | Action / EFE | `SWERVE_LEFT` ($545.35$) | `SWERVE_LEFT` ($545.35$) |
| **1** | $0.0001\text{ m}$ | Action / PE / $\Delta W$ | `SWERVE_RIGHT` ($\text{PE}=0.214$, $\Delta W=9\cdot 10^{-5}$) | `SWERVE_RIGHT` ($\text{PE}=0.214$, $\Delta W=0.0$) |
| **2** | $0.0003\text{ m}$ | Action / EFE | **`SWERVE_LEFT` ($545.57$) [Diverged North]** | **`SWERVE_RIGHT` ($545.58$) [Remained South]** |
| **3** | $0.0006\text{ m}$ | Action / EFE | `SWERVE_LEFT` ($545.87$) | `SWERVE_RIGHT` ($545.88$) |
| **4** | $0.0011\text{ m}$ | Action / EFE | `SWERVE_LEFT` ($546.33$) | `SWERVE_RIGHT` ($546.33$) |

---

## 4. Forensic Visualizations (in `evidence/p1_r4_forensic/`)

1. [`01_forensic_initial_q_and_actions.png`](file:///d:/ebca/evidence/p1_r4_forensic/01_forensic_initial_q_and_actions.png) — Proof of $Q_{\text{stdp}} \equiv 0$ at Tick 0 and the broken EFE symmetry at Tick 2.
2. [`02_forensic_w_norm_vs_time_divergence.png`](file:///d:/ebca/evidence/p1_r4_forensic/02_forensic_w_norm_vs_time_divergence.png) — Startup acceleration prediction error surge (Ticks 0–15) marking the exact divergence point.
3. [`03_forensic_trajectory_overlay_first_update.png`](file:///d:/ebca/evidence/p1_r4_forensic/03_forensic_trajectory_overlay_first_update.png) — Trajectory overlaid with the exact first update point ($x = 0.0001\text{ m}$).
