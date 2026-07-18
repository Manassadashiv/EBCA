# ARCHITECTURAL PATCH: NEUROMODULATORY PRECISION WEIGHTING
### Integrating Active Inference Theory and Reservoir Computing Dynamics into CARL
**Document Reference:** `D:\carl_simulation\ebca\docs\PRECISION_WEIGHTING_PATCH.md`  
**Status:** Approved Technical Patch  

---

## 1. THE ACADEMIC DISCOVERY

Recent research in computational neuroscience and synthetic biology establishes a direct mathematical link between **Active Inference (AIF)**, **Reservoir Computing (RC)**, and **Neuromodulation**:

> In the Free Energy Principle, **neuromodulation is formally modeled as Precision Weighting** ($\pi$). Precision represents the inverse variance (confidence) of sensory prediction errors. By adjusting neuromodulatory gains, the brain dynamically decides whether to trust incoming exteroceptive data (exploring/learning) or rely on internal prior beliefs (exploiting/conserving).

---

## 2. THE CARL EMULATION FORMULA

We will patch CARL’s Liquid State Machine (LSM) readout and endocrine loop (`carl_endocrine.py` & `carl_reservoir.py`) to implement **Dynamic Precision Weighting**. 

Instead of treating sensory inputs with fixed gains, the prediction error $\mathbf{e}(t)$ of his sensors is scaled by a dynamic precision coefficient $\pi_{sensory}$ computed from neurotransmitter levels:

$$\mathbf{e}(t) = \mathbf{y}_{\text{sensor}}(t) - \mathbf{y}_{\text{predicted}}(t)$$

$$\mathbf{e}_{\text{weighted}}(t) = \pi_{\text{sensory}} \cdot \mathbf{e}(t)$$

### A. The Precision Weights ($\pi$)
The precision of exteroceptive exteroception (LiDAR prediction errors) and interoceptive drives (energy limits) is governed by active neuromodulatory levels:

$$\pi_{\text{sensory}} = \pi_{\text{baseline}} \cdot \left( 1.0 + \gamma_{\text{ACh}} \cdot \text{ACh}(t) + \gamma_{\text{NE}} \cdot \text{NE}(t) - \gamma_{\text{5HT}} \cdot \text{5HT}(t) \right)$$

1. **High Acetylcholine (ACh) & Norepinephrine (NE):** 
   - Boosts sensory precision $\pi_{sensory}$. 
   - CARL becomes highly sensitive to tiny prediction errors. He pays close attention to new corridors, immediately updating his reservoir readout weights (active learning).
2. **High Serotonin (5-HT) & Dopamine (DA):**
   - Suppresses sensory precision $\pi_{sensory}$.
   - CARL ignores small exteroceptive sensory fluctuations (sensor noise) and relies heavily on his established spatial priors (the compiled Cognitive Map), entering a high-speed, low-energy traversal state.

---

## 3. BENEFIT FOR THE MINI & MAJOR PROJECT

- **Mini Project (Simulation):** When CARL enters a new maze sector, the sudden spatial surprise spikes Norepinephrine (NE). This instantly elevates sensory precision, causing the reservoir readout to adapt rapidly to the new walls. Once the area is mapped, NE decays, Serotonin stabilizes the weights, and control transitions from exploration to high-speed exploitation.
- **Major Project (Physical Robot):** Physical sensors have high noise (e.g., LiDAR reflecting off dusty surfaces). By scaling precision weighting with Dopamine and Serotonin, we can filter out real-world physical noise when CARL is navigating known corridors, preventing erratic wheel corrections.

---

## 4. INTEGRATION CHECKPOINT

We will integrate this mathematical formulation into:
1. `D:\carl_simulation\ebca\carl_endocrine.py` — calculating the dynamic $\pi_{sensory}$ from active modulator states.
2. `D:\carl_simulation\ebca\carl_reservoir.py` — multiplying prediction error buffers by $\pi_{sensory}$ before triggering online Recursive Least Squares (RLS) parameter updates.
