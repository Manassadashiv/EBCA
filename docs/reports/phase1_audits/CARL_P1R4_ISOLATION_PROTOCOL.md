# CARL-DX Phase 1-R4: Isolated STDP Causal Validation Protocol (HDC Ablated)

## 1. Scientific Objective
Determine whether biological Three-Factor Spike-Timing-Dependent Plasticity (STDP) alone, without HDC episodic memory assistance, can produce a reproducible, experience-dependent change in CARL's later behaviour:
$$\text{Experience} \longrightarrow \text{Spike / Eligibility Correlation} \longrightarrow \Delta W \longrightarrow \Delta Q_{\text{stdp}}(S, a) \longrightarrow \Delta \text{Action} \longrightarrow \Delta \text{Behaviour}$$

---

## 2. Experimental Conditions (All with HDC Completely Disabled)
1. **`NO_HDC_STDP`**:
   - HDC memory completely disabled ($V_{\text{mem}} = 0.0$).
   - Three-Factor STDP active ($M=22 \to K=7$, 154 plastic synapses).
2. **`NO_HDC_NO_STDP`**:
   - HDC memory disabled.
   - STDP disabled ($W = 0, \Delta W = 0$).
   - Static non-plastic baseline control.
3. **`NO_HDC_SHUFFLED_STDP`**:
   - HDC memory disabled.
   - STDP active, but pre-post spike timing correlation randomized.
   - Timing causal control.

---

## 3. Multi-Episode Developmental Structure (8 Episodes per Seed)
- **Episodes 1–3 (Acquisition)**:
  - Route B (South) contains occluded obstacle at $(1.45, -0.55\text{m})$; Route A (North) is clear.
  - Tests whether adverse experience in Route B depresses South-turning synapses and promotes Northward detour.
- **Episodes 4–5 (Persistence)**:
  - Tests whether learned synaptic weights $W$ persist across developmental resets and maintain adaptive action bias without forgetting.
- **Episodes 6–8 (Reversal / Extinction)**:
  - Hazard inverted to Route A (North, $1.45, +0.55\text{m}$); Route B (South) cleared.
  - Tests plastic unlearning and reversal of synaptic weights $\Delta W$.

---

## 4. Parameter Calibration Protocol
- Step 1: Run baseline parameters ($\eta = 0.015, \lambda_{\text{stdp}} = 45.0$) on Seed 42.
- Step 2: If weight accumulation $\|\Delta W\|$ is demonstrably sub-threshold to produce behavioral divergence, execute a bounded biological gain sweep ($\eta \in [0.015, 0.05, 0.10, 0.15]$, $\lambda_{\text{stdp}} \in [45, 90, 150]$) and select the minimal stable parameters.
- Step 3: Run full 3-seed replication (Seeds 42, 101, 2024).
