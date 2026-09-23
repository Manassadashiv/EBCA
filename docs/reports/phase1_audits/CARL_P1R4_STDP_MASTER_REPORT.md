# CARL-DX Phase 1-R4: STDP Synaptic Plasticity Reconnection & Causal Validation Master Report

**Date**: August 24, 2026  
**Milestone**: Phase 1-R4 — STDP / Synaptic Plasticity Reconnection  
**Experimental Variant**: Isolated Three-Factor STDP ($M=22 \to K=7$, 154 Plastic Synapses)  
**Primary Seed Evaluated**: Seed 42 (Pilot Causal Gate, 24 Physical Episodes)  
**Official Emergence Classification**: **`LEVEL 1: STDP ACTIVE AND WEIGHTS CHANGE (SUB-THRESHOLD CAUSAL EFFECT)`**

---

## 1. Scientific Objective & The Core Question

> *"Does an experience-driven STDP mechanism modify internal synaptic state in CARL, and does that modification causally change later neural decision-making or behaviour independently of HDC memory?"*

### Official Scientific Verdict:
**PARTIALLY DEMONSTRATED (LEVEL 1 CLASSIFICATION).**
1. **Synaptic Plasticity is Active**: The three-factor STDP mechanism successfully updated synaptic weights online at $30\text{ Hz}$ with asymmetric pre-post eligibility traces ($\text{LTD events} = 298$ across 8 episodes).
2. **Causal Gate Triggered**: The Seed-42 pilot detected that synaptic weight accumulation ($\|\Delta W\| \approx 0.001$) was sub-threshold relative to the strong HDC episodic memory bias ($V_{\text{mem}} \approx 4.5$). Consequently, HDC memory drove the Episode-2 route switch in both `FULL_STDP` and `NO_STDP`, preventing a conclusive attribution of behavioural divergence to STDP alone.
3. **Strict Protocol Compliance**: In accordance with Part J and Part V ("*Do not manufacture positive results. Stop after the first seed if STDP produces no measurable independent behavioural change*"), the runner **halted execution at Seed 42** without wasting compute or making false multi-seed replication claims.

---

## 2. Complete Causal Chain Telemetry Audit

```
[1. Adverse Experience] ────────► VERIFIED (Prediction error PE > 0.18 m/s, speed < 0.05 m/s)
         │
         ▼
[2. Spike / Eligibility Trace] ──► VERIFIED (Asymmetric pre-post correlation E_ij updated at 30Hz)
         │
         ▼
[3. STDP Weight Change ΔW] ────► VERIFIED (LTD events: 298 in FULL_STDP; ||W|| changed from 0 to 0.001)
         │
         ▼
[4. Neural Response Shift] ────► SUB-THRESHOLD (Synaptic gain ||W||=0.001 produced < 0.05 EFE delta)
         │
         ▼
[5. Behavioural Causality] ────► MASKED BY HDC MEMORY (HDC memory alone drove Episode-2 switch)
```

---

## 3. Pre-Flight Architecture & Performance Audit

- **AST Source Audit**: [`P1R4_STDP_AUDIT.json`](file:///d:/ebca/P1R4_STDP_AUDIT.json) — **`100% CLEAN - ZERO HARDCODED RULES`** (0 violations across all modules).
- **System Compute Profile**: [`P1R4_STDP_PERFORMANCE_PROFILE.json`](file:///d:/ebca/P1R4_STDP_PERFORMANCE_PROFILE.json)
  - Median STDP step latency: **$14.5\ \mu\text{s}$** ($0.0145\text{ ms}$).
  - Real-time headroom: **$99.95\%$** of the $33.3\text{ ms}$ ($30\text{ Hz}$) MuJoCo simulation budget.

---

## 4. Master Artifacts & Visualizations

### Pre-Flight & Scientific Publication Figures (in `evidence/p1_r4/plots/`):
1. [`01_current_live_neural_pathway.png`](file:///d:/ebca/evidence/p1_r4/plots/01_current_live_neural_pathway.png) — Active vs disconnected modules in CARL.
2. [`02_stdp_connection_map.png`](file:///d:/ebca/evidence/p1_r4/plots/02_stdp_connection_map.png) — 22-pre to 7-post synaptic topology ($154$ synapses).
3. [`03_stdp_dataflow_diagram.png`](file:///d:/ebca/evidence/p1_r4/plots/03_stdp_dataflow_diagram.png) — Three-factor plasticity dataflow and EFE modulation.
4. [`04_stdp_weight_change_heatmap.png`](file:///d:/ebca/evidence/p1_r4/plots/04_stdp_weight_change_heatmap.png) — Synaptic weight matrix heatmap.
5. [`05_stdp_weight_distribution.png`](file:///d:/ebca/evidence/p1_r4/plots/05_stdp_weight_distribution.png) — Weight distributions (FULL vs Shuffled).
6. [`06_spike_timing_histogram.png`](file:///d:/ebca/evidence/p1_r4/plots/06_spike_timing_histogram.png) — Asymmetric STDP learning window $\Delta W(\Delta t)$.
7. [`07_synaptic_change_over_time.png`](file:///d:/ebca/evidence/p1_r4/plots/07_synaptic_change_over_time.png) — Weight norm dynamics across Acquisition, Persistence, and Reversal.
8. [`08_neural_state_divergence.png`](file:///d:/ebca/evidence/p1_r4/plots/08_neural_state_divergence.png) — Action quality $Q_{\text{stdp}}$ profile across action primitives.
9. [`09_policy_divergence.png`](file:///d:/ebca/evidence/p1_r4/plots/09_policy_divergence.png) — Route choice probability over developmental episodes.
10. [`10_behavioural_learning_curve.png`](file:///d:/ebca/evidence/p1_r4/plots/10_behavioural_learning_curve.png) — Goal acquisition latency across episodes.
11. [`11_STDP_CAUSAL_CHAIN.png`](file:///d:/ebca/evidence/p1_r4/plots/11_STDP_CAUSAL_CHAIN.png) — Summary diagram of the evaluated STDP causal chain.

### Demonstration Videos (24 HD 720p 30 FPS MP4s in `evidence/p1_r4/videos/`):
- `full_stdp_s42_ep1.mp4` through `full_stdp_s42_ep8.mp4`
- `no_stdp_s42_ep1.mp4` through `no_stdp_s42_ep8.mp4`
- `stdp_shuffled_timing_s42_ep1.mp4` through `stdp_shuffled_timing_s42_ep8.mp4`

---

## 5. Next Steps for Phase 1-R4 Completion

To promote STDP from **Level 1** to **Level 3/4 (Causal Behavioral Adaptation)**:
1. **Isolate STDP from HDC (`NO_HDC + STDP` vs `NO_HDC + NO_STDP`)**: Disable episodic memory queries so that behavioral adaptation relies solely on synaptic weight modification.
2. **Calibrate Synaptic Gain**: Increase learning rate $\eta$ and EFE coupling $\lambda_{\text{stdp}}$ so that plastic weight shifts produce noticeable behavioral influence.
3. **Rerun Pilot**: Validate that pure synaptic plasticity causes route switching and reversal in the absence of HDC memory.
