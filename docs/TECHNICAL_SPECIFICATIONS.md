# TECHNICAL SPECIFICATIONS: EBCA MATHEMATICAL & ALGORITHMIC CORE
**Document Reference:** `D:\ebca\docs\TECHNICAL_SPECIFICATIONS.md`  
**Status:** Approved Technical Core Blueprint  

---

## 1. NEUROMORPHIC SUBSTRATE (MATRIX ALGEBRA)

The core brain is simulated as a recurrent **Liquid State Machine (LSM)** reservoir. To ensure compatibility with both PC simulation and real-world microcontrollers, the system operates on dual computational profiles:

### Dual Compute Profiles
1. **Simulation Profile (Digital Twin Baseline):**
   - Reservoir size $N = 500$ neurons (~37,500 sparse recurrent synapses).
   - HDC Dimension $D = 40,000$ (maximizing holographic memory capacity for long-term mapping).
2. **Hardware Profile (Real Robot Deployment):**
   - Reservoir size $N = 250$ neurons (~4,680 sparse recurrent synapses, $7.5\%$ density).
   - HDC Dimension $D = 10,000$ (fits entirely inside L1/L2 cache of a Raspberry Pi / Cortex-A processor).

### Matrix Dimensions (Simulation Profile)
- **Sensory Input Vector ($\mathbf{u}_t$):** $\mathbf{u}_t \in \mathbb{R}^{M \times 1}$, where $M = 25$ (24 LiDAR rays + 1 battery charge metric).
- **Reservoir State Vector ($\mathbf{x}_t$):** $\mathbf{x}_t \in \mathbb{R}^{N \times 1}$, where $N = 500$ (fixed biological sweet spot).
- **Control Output Vector ($\mathbf{y}_t$):** $\mathbf{y}_t \in \mathbb{R}^{K \times 1}$, where $K = 3$ (left wheel torque, right wheel torque, neck pan position).
- **Input Weight Matrix ($W_{\text{in}}$):** $W_{\text{in}} \in \mathbb{R}^{N \times M}$, dense random weights initialized from Gaussian distribution $\mathcal{N}(0, \sigma_{\text{in}}^2)$.
- **Recurrent Weight Matrix ($W_{\text{res}}$):** $W_{\text{res}} \in \mathbb{R}^{N \times N}$, sparse random matrix with $15\%$ non-zero connections, scaled to spectral radius $\rho(W_{\text{res}}) \approx 1.0$ (criticality).
- **Readout Weight Matrix ($W_{\text{out}}$):** $W_{\text{out}} \in \mathbb{R}^{K \times N}$, initialized at zero, trained online.

### State Update Equation
At each control step $\text{d}t = 0.033\text{ seconds}$ ($30\text{ Hz}$):
$$\mathbf{x}(t + \text{d}t) = \left(1 - \frac{\text{d}t}{\tau}\right)\mathbf{x}(t) + \frac{\text{d}t}{\tau} \tanh \left( W_{\text{res}}\mathbf{x}(t) + W_{\text{in}}\mathbf{u}(t) + \mathbf{\eta}(t) \right)$$
- **$\tau$:** Leaking time constant ($0.1\text{ to } 0.5\text{ s}$).
- **$\mathbf{\eta}(t)$:** Thermodynamic action noise vector scaled by Norepinephrine: $\mathbf{\eta}(t) \sim \mathcal{N}(0, \sigma_0^2 \cdot \text{NE}(t))$.

---

## 2. ONLINE LEARNING & SYNAPTIC PLASTICITY ALGORITHMS

### A. Readout Training: Throttled Recursive Least Squares (RLS)
To prevent computational bottlenecks ($O(N^2)$ matrix-vector operations), **RLS weight updates are decoupled from the high-frequency control loop**:
- The forward motor command $W_{\text{out}}\mathbf{x}(t)$ (a cheap $O(N)$ dot product) is executed at **$30\text{ Hz}$**.
- The full RLS parameter update (covariance and weight update) is scheduled and executed via a **strictly tracked counter rule** to prevent update storms:

#### RLS Scheduling Rule
```
IF (current_tick - last_rls_tick) >= 6:
    Execute RLS Update
    last_rls_tick = current_tick
ELSE IF error_norm > 0.25 AND (current_tick - last_rls_tick) >= 3:
    Execute Dynamic RLS Update
    last_rls_tick = current_tick
```
- *Properties:* This rule guarantees RLS updates run at $\le 5\text{ Hz}$ under baseline conditions, allows dynamic updates for sudden large surprises, and enforces a minimum cool-down interval of $3\text{ ticks}$ ($100\text{ ms}$) to prevent CPU throttling from back-to-back updates.
- *State:* The variable `last_rls_tick` is explicitly stored in the processor state and serialized to disk to prevent stale-weight errors.

1. **State activation:** $\Phi(t) = \mathbf{x}(t)$.
2. **Compute gain vector $\mathbf{k}(t) \in \mathbb{R}^{N \times 1}$:**
   $$\mathbf{k}(t) = \frac{P(t-\text{d}t)\Phi(t)}{\lambda + \Phi(t)^T P(t-\text{d}t)\Phi(t)}$$
3. **Update inverse correlation matrix $P(t)$:**
   $$P(t) = \frac{1}{\lambda} \left[ P(t-\text{d}t) - \mathbf{k}(t)\Phi(t)^T P(t-\text{d}t) \right]$$
4. **Compute prediction error $\mathbf{e}(t) \in \mathbb{R}^{K \times 1}$:**
   $$\mathbf{e}(t) = \mathbf{y}_{\text{target}}(t) - W_{\text{out}}(t-\text{d}t)\Phi(t)$$
5. **Update Readout Weight Matrix:**
   $$W_{\text{out}}(t) = W_{\text{out}}(t-\text{d}t) + \mathbf{e}(t)\mathbf{k}(t)^T$$

### B. Synaptic Learning: Spiking Reflex Layer & R-STDP Interface
To bridge the gap between the reservoir's continuous output ($\mathbf{x}(t) \in [-1, 1]$) and the discrete spike-timing requirement of R-STDP, the reflex layer operates as an independent **Leaky Integrate-and-Fire (LIF) Spiking Neural Network**:

#### 1. Sensory Spike Encoding (Poisson Rate Encoder)
Raw sensor values (LiDAR distances $d_j$) are converted into discrete spike events $s_j(t) \in \{0, 1\}$ at each timestep. The probability of generating a spike is proportional to obstacle proximity:
$$P\left(s_j(t) = 1\right) = \nu_{\text{max}} \cdot \max\left(0, 1 - \frac{d_j}{d_{\text{trigger}}}\right) \text{d}t$$
- **$\nu_{\text{max}}$:** Maximum firing rate ($100\text{ Hz}$).
- **$d_{\text{trigger}}$:** Safety margin distance ($0.5\text{ m}$).

#### 2. Reflex Motor Neuron Integration
The reflex motor neurons (generating left/right wheel escape torques) integrate these sensory spikes, combined with a continuous modulating bias projected from the reservoir:
$$V_i(t + \text{d}t) = V_i(t) - \frac{\text{d}t}{\tau_m} V_i(t) + \sum_{j} w_{ij} s_j(t) + \mathbf{\beta}_i^T \mathbf{x}(t)$$
- **$\tau_m$:** Membrane time constant ($20\text{ ms}$).
- **$\mathbf{\beta}_i \in \mathbb{R}^{N \times 1}$:** Slower, fixed spatial project weights mapping continuous reservoir states into voltage offsets.
- **Spike Trigger:** When $V_i(t) \ge V_{\text{th}}$, the neuron fires a reflex spike at time $t_{\text{post}}$, resets $V_i(t) \leftarrow 0$, and applies a transient torque step to the motor controller:
  $$u_{\text{reflex}}^{(i)}(t) = u_0 \cdot e^{-(t - t_{\text{post}})/\tau_{\text{motor}}}$$

#### 3. R-STDP Weight Updates
The fast synaptic connections $w_{ij}$ between sensory inputs and motor neurons are adjusted based on spike times $t_{\text{pre}}$ (when sensor spike occurred) and $t_{\text{post}}$ (when reflex neuron fired):
$$\frac{\text{d}E_{ij}}{\text{d}t} = -\frac{E_{ij}}{\tau_e} + \delta(t - t_{\text{post}}) \int_0^{\infty} W(s) e^{-s/\tau_{\text{stdp}}} \text{d}s$$
$$\Delta w_{ij}(t) = \eta_{\text{stdp}} \cdot E_{ij}(t) \cdot \left( \text{DA}(t) - \text{DA}_{\text{baseline}} \right)$$

---

## 3. SPATIAL REPRESENTATION & NAVIGATIONAL GEOMETRY

CARL maps and navigates using hippocampal-inspired geometries:

### A. Place Cells (Radial Basis Functions)
Each place cell $i$ represents a specific $2\text{D}$ coordinate $(x_i, y_i)$ in the maze. Its activation $p_i(x,y)$ is calculated as:
$$p_i(x, y) = \exp \left( -\frac{(x - x_i)^2 + (y - y_i)^2}{2\sigma_{\text{place}}^2} \right)$$
- **$(x, y)$:** Current robot pose from odometry.
- **$\sigma_{\text{place}}$:** Activation radius ($0.15\text{ m}$).

### B. Grid Cells (Hexagonal Tiling)
Grid cell activity is simulated by sum-of-three-sinusoids plane waves at $60^\circ$ angles, creating hexagonal firing patterns:
$$g(\mathbf{r}) = \psi \left( \sum_{j=1}^3 \cos(\mathbf{k}_j \cdot \mathbf{r}) \right)$$

---

## 4. COGNITIVE MEMORY & HOLOGRAPHIC REDISTRIBUTION (HDC)

Sensory states and place activations are bound into high-dimensional bipolar hypervectors in a **$40,000$-dimensional space** ($\{-1, +1\}^D$) for the digital twin, and **$10,000$ dimensions** for hardware.

### Event-Driven Bundling Safeguard
To prevent memory copy overhead, **Holographic Memory Updates are strictly event-driven**:
- Instead of re-bundling the spatial memory vector $\mathbf{M}_{\text{spatial}}$ at every $30\text{ Hz}$ control tick, updates are triggered only on **place-cell transitions** (e.g. when the active place cell changes index) or when a major drive threshold is crossed (e.g., target harvest or collision).
- This reduces the execution cost by **$99\%$** ($30$ times a second down to once every $2$-$5$ seconds), mimicking biological episodic memory consolidation.

### Bipolar Algebra
1. **Binding ($\otimes$):** Element-wise multiplication (XOR in binary).
   $$\mathbf{C} = \mathbf{A} \otimes \mathbf{B} \quad \implies \quad C_i = A_i \cdot B_i$$
2. **Bundling ($\oplus$):** Element-wise addition followed by sign operation.
   $$\mathbf{S} = \text{sign}(\mathbf{A} + \mathbf{B} + \mathbf{C})$$

---

## 5. INFORMATION THEORY & CONSTRAINT ECOLOGS

We apply information theory to exteroceptive inputs to model them as partitions of uncertainty.

### A. Sensory Information Partitioning
Each physical constraint $g_i(x) \le 0$ divides the design space into allowed and forbidden sectors. The information content $I_i$ of constraint $i$ is calculated as:
$$I_i = \log_2 \left( \frac{|X|}{|X_{\text{allowed}}^{(i)}|} \right) \text{ bits}$$

### B. Constraint Interaction Graph (CIG)
The CIG is represented as an adjacency matrix $A_{\text{CIG}} \in \mathbb{R}^{M_c \times M_c}$, where $M_c$ is the number of constraints (torque, collision, battery, tilt):
- If constraints $i$ and $j$ fail simultaneously:
  $$A_{\text{CIG}}[i, j] \leftarrow A_{\text{CIG}}[i, j] + \eta_c$$

### C. Meta-Control Loop (MCL)
The MCL monitors the derivative of the mapping learning rate $\Delta L_r$ and switches behavioral modes:
- If $\Delta L_r > 0.05 \implies$ High ACh $\implies$ Trigger `GLOBAL_EXPLORE` (broad search).
- If $\Delta L_r \le 0.05 \implies$ High 5-HT $\implies$ Trigger `REFINE_BOUNDARY` (conservative sampling).

---

## 6. ENDOCRINE KINETICS & PRECISION WEIGHTING

### Neuromodulator Baselines
We model four neuromodulator concentrations updating dynamically:
$$\frac{\text{dNM}}{\text{d}t} = -\delta_{\text{decay}} \left( \text{NM} - \text{NM}_{\text{baseline}} \right) + \text{Spike}_{\text{event}}$$

### Dynamic Precision Weighting
Neuromodulators scale the precision $\pi_{\text{sensory}}$ (inverse variance weight) of exteroceptive prediction errors:
$$\pi_{\text{sensory}} = \pi_0 \left( 1.0 + \gamma_{\text{ACh}} \cdot \text{ACh}(t) + \gamma_{\text{NE}} \cdot \text{NE}(t) - \gamma_{\text{5HT}} \cdot \text{5HT}(t) \right)$$
Incoming prediction errors are scaled before weight updates:
$$\mathbf{e}_{\text{weighted}}(t) = \pi_{\text{sensory}} \cdot \mathbf{e}(t)$$

---

## 7. COGNITIVE COMPLEXITY: INTEGRATION INDEX PROXY

To measure CARL's complexity scale, we define an offline diagnostic score known as the **Integration Index ($\phi_{\text{proxy}}$)**.

### Mathematical Definition of $\phi_{\text{proxy}}$
We partition the 500-neuron reservoir state into two systems, $A$ and $B$, along a fixed structural cut. $\phi_{\text{proxy}}$ measures the information loss when the connection between $A$ and $B$ is cut:
$$\phi_{\text{proxy}}(t) = H \left( X(t) | X(t-\text{d}t) \right) - H \left( A(t) | A(t-\text{d}t) \right) - H \left( B(t) | B(t-\text{d}t) \right)$$
- Under a linear Gaussian approximation:
  $$\phi_{\text{proxy}} = \frac{1}{2} \ln \left( \frac{\det(\Sigma_{A|A}) \det(\Sigma_{B|B})}{\det(\Sigma_{X|X})} \right)$$
- **Why this is a Proxy:** To avoid the combinatorial explosion ($O(2^N)$ splits) of finding the mathematical Minimum Information Partition (MIP) in real-time, this calculation is fixed to a single partition and calculated offline as a diagnostic tool.

---

## 8. THE 8-LAYER INTEGRATED COGNITIVE STACK

```
┌──────────────────────────────┬──────────────────────────────────────────────┐
│ Layer                        │ Operational Algorithm & Mathematical Module │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ 7. Concept Genesis           │ Unsupervised SOM topological clustering     │
│ 6. The Imagination           │ Predictive World Model simulation (T_wm)     │
│ 5. Causal Reasoning / MPC    │ 50-step quadratic cost horizon optimizer     │
│ 4. The Witness               │ Circular episode state-monitoring buffer     │
│ 3. Spatial & Danger Mapping  │ Hippocampal Grid/Place cells + CIG limits    │
│ 2. Biological Endocrine      │ DA/NE/5-HT/ACh decay kinetics + R-STDP       │
│ 1. Two-Speed Memory & GIS    │ Working Memory ⊗ Holographic LTM (HDC)       │
│ 0. Physical Embodiment       │ MuJoCo Physics runner & interface sensor API │
└──────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 9. ZERO-COPY UNIFIED STATE MEMORY LAYOUT

To optimize data flow and minimize memory copy latency, the entire system state is stored in a single, pre-allocated flat NumPy array:
$$\mathbf{S}_{\text{unified}} \in \mathbb{R}^{532 \times 1}$$

### Memory Mapping & Slicing Coordinates:
- **Sensory Inputs:** `S_unified[0:25]` (24 LiDAR rays + 1 battery charge level).
- **Reservoir Brain States:** `S_unified[25:525]` (500 recurrent reservoir neurons).
- **Neuromodulatory Concentrates:** `S_unified[525:529]` (Dopamine, Norepinephrine, Serotonin, Acetylcholine values).
- **Actuator Torques:** `S_unified[529:532]` (left motor torque, right motor torque, neck position target).

---

## 10. HARDWARE ABSTRATION LAYER (HAL) SYSTEM STRUCTURE

To make the cognitive core independent of the physical platform, the brain communicates strictly with an abstract `HardwareInterface` class:

```python
class HardwareInterface:
    def read_sensors(self) -> np.ndarray:
        """Returns 25-D vector mapping [LiDAR (24), Battery (1)]"""
        raise NotImplementedError

    def write_motors(self, torque_left: float, torque_right: float, neck_target: float):
        """Applies torque control signals directly to physical/virtual servos"""
        raise NotImplementedError
```

### Concrete Deployments:
1. **`SimulationHAL` (Digital Twin):** Maps to MuJoCo ray-casting and `mjData.ctrl` motor buffers.
2. **`PhysicalHAL` (Real Robot):** Maps to serial readings from physical LiDAR and general-purpose GPIO PWM signals.

---

## 11. DIAGNOSTIC ID REGISTRY (ERROR & EXCEPTION TRACING)

To ensure real-time troubleshooting, every subsystem and cognitive operation is assigned a unique **Diagnostic ID**. Any logging output or exception thrown must reference this ID to identify the root cause immediately.

| ID Code | Category | Component Name | Description |
| :--- | :--- | :--- | :--- |
| **`PHY-001`** | Physical | Wheel Actuators | Left/Right wheel differential motor torque execution. |
| **`PHY-002`** | Physical | Neck Actuators | Hinge/Prismatic expressive neck positioning. |
| **`PHY-003`** | Physical | LiDAR Sensor | 24-ray ray-casting (simulation) or serial packet reads (real). |
| **`PHY-004`** | Physical | Battery / Fuel | Metabolic energy drainage calculations and sensors. |
| **`MEM-101`** | Memory | Working Memory | High-frequency active state buffer (`T_wm`). |
| **`MEM-102`** | Memory | Long-Term Memory | Holographic bipolar hypervector arrays (`HDC` storage). |
| **`MEM-103`** | Memory | Place Cells | Gaussian radial basis function activations. |
| **`MEM-104`** | Memory | Grid Cells | Hexagonal path integration grids. |
| **`LSM-211`** | LSM | Recurrent Reservoir | 500-node recurrent state updates. |
| **`LSM-212`** | LSM | RLS Optimizer | Readout parameter fitting via Recursive Least Squares. |
| **`END-201`** | Endocrine | Dopamine (DA) | Gating R-STDP learning rate. |
| **`END-202`** | Endocrine | Norepinephrine (NE) | Calculating surprise and injecting exploration noise. |
| **`END-203`** | Endocrine | Serotonin (5-HT) | Managing safety margins and velocity constraints. |
| **`END-204`** | Endocrine | Acetylcholine (ACh) | Modulating exteroceptive attention and exploration pressure. |
| **`END-205`** | Endocrine | Plasticity (R-STDP) | Local Hebbian eligibility trace tracking. |
| **`WIT-401`** | Witness | Metacognition | Circular episode fail-state logger. |
| **`CAU-501`** | Causal | Causal Scaffold | Counterfactual question generator and adjacency matrix. |
| **`MPC-511`** | Planning | Model Predictive Control| 50-step horizon quadratic cost trajectory optimizer. |
| **`IMA-601`** | Imagination | Predictive Simulation | Internal world prediction runner (`T_wm` primary reality). |
| **`CON-701`** | Concept | Concept Genesis | Unsupervised SOM topological clustering. |
| **`GIS-901`** | Persistence | Global State Manager | Disk serialization/loading (`state.npz` operations). |
| **`HAL-911`** | Abstraction | Hardware Interface | Simulation/Physical HAL redirection. |

---

## 12. AUTOMATED SAFEGUARDS & RECOVERY ACTIONS (CRASH-PROOFING)

To make the codebase 100% fool-proof and crash-proof during long runs, the simulation loop implements two automated runtime safeguards:

### A. Physics Glitch Recovery (Auto-Teleport Safeguard)
- **Trigger Condition:** The robot's coordinates exceed the maze bounding box ($x < 0$ or $x > 7.2$ or $y < 0$ or $y > 6.0$), or tilt pitch angle exceeds $|\theta| > 1.2\text{ radians}$ for $> 50$ consecutive steps.
- **Recovery Action:** Teleports the robot back to the spawning coordinate ($x=0.4, y=0.4, z=0.10$), and resets velocities to zero.
- **Preservation:** The internal brain state, place cells, R-STDP weights, and spatial maps are **not reset**.

### B. Mathematical Overflow Protection (NaN/Inf Clamping)
- **Trigger Condition:** Any value in the reservoir state vector $\mathbf{x}(t)$ becomes `NaN` or `Inf`.
- **Recovery Action:** Clamped via `np.nan_to_num`. If a total crash occurs, a **Soft Brain Reset** is executed, clearing the active state vector to zero ($\mathbf{x} = \mathbf{0}$) and slightly decaying input weights.

---

## 13. COMPUTATIONAL BUDGET & HARDWARE PROFILING

To ensure that the digital twin runs reliably on a standard PC and the physical robot runs on consumer microcontrollers (e.g. Raspberry Pi 4/5), we profile the computation:

### Memory & Compute Cost Projections (Theoretical Benchmarks)

| Subsystem | Operation | Time Cost (Sim Profile - Projected) | Time Cost (Hardware Profile - Projected) | Cache Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **LSM Reservoir** | $W_{\text{res}} \mathbf{x}(t) + W_{\text{in}} \mathbf{u}(t)$ | $\approx 0.12\text{ ms}$ (at $N=500$) | $\approx 0.03\text{ ms}$ (at $N=250$) | $500 \times 500$ floats $\approx 1\text{ MB}$ (Fits in L2) |
| **RLS Readout** | $P(t)\Phi(t) \text{ and } \mathbf{k}(t)$ | $\approx 1.8\text{ ms}$ (at $5\text{ Hz}$ throttle) | $\approx 0.45\text{ ms}$ (at $5\text{ Hz}$ throttle) | $500 \times 500$ matrix $\approx 1\text{ MB}$ |
| **HDC Bundling** | $\mathbf{A} \otimes \mathbf{B} \oplus \mathbf{C}$ | $\approx 3.2\text{ ms}$ (Event-driven only) | $\approx 0.8\text{ ms}$ (Event-driven only) | $40,000 \times 1\text{ byte} = 40\text{ KB}$ (Fits in L1) |
| **Active Loop Total**| Main step cycle | **$\approx 0.95\text{ ms}$ per tick** | **$\approx 0.23\text{ ms}$ per tick** | **Fully Optimized for L1/L2 Cache** |

> [!NOTE]
> These values represent theoretical calculations of operations/seconds based on single-thread FLOP processing power. Actual runtime latency will be measured and profiled directly in code during execution to capture Python/NumPy interpreter and memory registry overhead.
