# CARL-DX Phase 1-R4: STDP Synaptic Plasticity Reconnection & Causal Protocol

## 1. Scientific Objective
Investigates whether biological Three-Factor Spike-Timing-Dependent Plasticity (STDP) can operate as an active, causally relevant developmental mechanism in CARL:
$$\text{Experience} \longrightarrow \text{Spike / Eligibility Correlation} \longrightarrow \Delta W \longrightarrow \Delta \text{Neural Response } (Q_{\text{stdp}}) \longrightarrow \Delta \text{Action Preference} \longrightarrow \text{Adaptive Behaviour}$$

---

## 2. Condition Matrix (Ablations)
1. **`FULL_STDP`**: Active three-factor STDP ($M=22 \to K=7$, 154 plastic synapses) + HDC memory.
2. **`NO_STDP`**: STDP disabled ($\Delta W = 0, W = 0$) + HDC memory.
3. **`STDP_SHUFFLED_TIMING`**: Timing correlation randomized (causal timing control) + HDC memory.

---

## 3. Multi-Episode Developmental Structure (8 Episodes per Seed)
- **Episodes 1–3 (Acquisition)**:
  - Route B (South) contains obstacle; Route A (North) is clear.
  - Test rapid synaptic depression of adverse sensorimotor connections and potentiation of safe detours.
- **Episodes 4–5 (Persistence Test)**:
  - Test whether learned synaptic weights $W$ persist across developmental resets and maintain adaptive action bias.
- **Episodes 6–8 (Reversal / Extinction Test)**:
  - Hazard inverted to Route A (North); Route B (South) cleared.
  - Test plastic unlearning and reversal of synaptic weights $\Delta W$.

---

## 4. Primary Causal Gate (Seed 42)
- Step 1: Execute Seed 42 across all 8 developmental episodes.
- Step 2: Verify $\Delta W \ne 0$, $\Delta Q_{\text{stdp}} \ne 0$, and policy divergence before launching multi-seed replication.
