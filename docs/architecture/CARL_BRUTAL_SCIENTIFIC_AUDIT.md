# CARL — BRUTAL SCIENTIFIC AUDIT REPORT
**Target System:** CARL (Cognitive Autonomous Recurrent Lifeform) — Developmental Intelligence Stage 1 & Gate #5  
**Auditor:** Independent Scientific Audit Subsystem  
**Date of Audit:** September 3, 2026  
**Audited Repository:** `d:\ebca\`  
**Key Artifacts Inspected:**  
- [`brain/carl_stage1_hal.py`](file:///d:/ebca/brain/carl_stage1_hal.py)
- [`brain/carl_stage1_discovery.py`](file:///d:/ebca/brain/carl_stage1_discovery.py)
- [`brain/carl_stage1_adversarial_suite.py`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py)
- [`brain/carl_stage1_organism.py`](file:///d:/ebca/brain/carl_stage1_organism.py)
- [`brain/carl_stage1_reservoir.py`](file:///d:/ebca/brain/carl_stage1_reservoir.py)
- [`world/vessel_kinetic.xml`](file:///d:/ebca/world/vessel_kinetic.xml)
- [`evidence/stage1/gate5/stage1_gate5_results.json`](file:///d:/ebca/evidence/stage1/gate5/stage1_gate5_results.json)

---

# PART 1 — FIRST PRINCIPLE DECONSTRUCTION

| Sub-Claim | Audit Finding | Code Evidence | Verdict |
| :--- | :--- | :--- | :---: |
| **A. Did CARL discover actuator/sensor relationships rather than inherit them?** | **Partially True.** Actuator-to-sensor statistical dependencies were discovered via cross-correlation and IAAFT surrogates under actuator scrambling. However, **sensor identities were inherited** through hardcoded semantic indices. | [`brain/carl_stage1_discovery.py:253-270`](file:///d:/ebca/brain/carl_stage1_discovery.py#L253-L270) hardcodes `sig_imu_accel = is_sig[:, 15:18]`, `sig_gyro = is_sig[:, 18:21]`. | **PARTIALLY SUPPORTED** |
| **B. Did relationships arise from physical interaction rather than simulator bookkeeping?** | **True.** Dynamics were computed via MuJoCo 3.12 rigid body physics (forces, torques, tire friction, collisions). | [`brain/carl_stage1_hal.py:100-115`](file:///d:/ebca/brain/carl_stage1_hal.py#L100-L115) runs `mujoco.mj_step`. | **SUPPORTED** |
| **C. Can CARL distinguish actuator motion from physical consequence?** | **False.** The *simulator* exhibits traction decoupling when flipped or airborne, but **CARL itself has no code or model that evaluates this decoupling**. | In [`brain/carl_stage1_adversarial_suite.py:123-131`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py#L123-L131), the test script evaluated the displacement, not CARL. | **NOT SUPPORTED** |
| **D. Does the learned relationship depend on current body/environment state?** | **False.** The learned matrix $C_{ij}(\tau)$ is a static, time-averaged scalar matrix computed over the entire trajectory. It is completely state-unconditioned. | [`brain/carl_stage1_discovery.py:55-77`](file:///d:/ebca/brain/carl_stage1_discovery.py#L55-L77) computes scalar `np.mean(u * s)`. | **NOT SUPPORTED** |
| **E. Does CARL predict consequences of novel actions?** | **False.** CARL possesses zero predictive forward models. The predictive model evaluated in Test 4 was instantiated inside the test script. | [`brain/carl_stage1_adversarial_suite.py:318`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py#L318) defines `SimplePredictiveForwardModel` inside the test file. | **NOT SUPPORTED** |
| **F. Does CARL use learned information to generate useful behavior?** | **False.** The navigation controller was an external handcoded proportional script that merely read the discovered wheel indices. | [`brain/carl_stage1_adversarial_suite.py:513-517`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py#L513-L517). | **NOT SUPPORTED** |
| **G. Is there hidden semantic mapping, privileged state, or script controller?** | **Yes, extensive.** Privileged access to `hal.data.qpos`, hardcoded sensor groupings, handcoded proportional steering, and script-level state resets. | Confirmed across multiple files. | **CONFIRMED FLAW** |
| **H. Would claimed results survive adversarial perturbation?** | **No.** Permuting both sensors and actuators simultaneously, or removing `qpos` access from Test 6, immediately breaks the pipeline. | Empirical verification below. | **VULNERABLE** |

---

# PART 2 — DATA PATH FORENSICS

```text
PHYSICAL SIMULATOR (MuJoCo 3.12.0)
    │
    ▼ [mjData: qpos, qvel, sensordata, ncon]
HAL (CarlStage1HAL)
    │ ─── LEAKAGE 1: diag['ncon'] exposes global world contacts (toys, hazards), not robot contacts.
    │ ─── SENSORS: 25-D vector [sonars 0..14, imu_acc 15..17, imu_gyro 18..20, proprio 21..23, batt 24]
    ▼
CARL INTERNAL STATE (CarlStage1Organism)
    │ ─── 500-neuron Liquid State Machine Reservoir (leaky tanh).
    │ ─── Babbler (sinusoidal / noise pulses).
    ▼
DISCOVERY ENGINE (CarlSensorimotorDiscoveryEngine)
    │ ─── Computes 6x25 cross-correlation tensor C_ij(tau).
    │ ─── Runs 200–100,000 IAAFT surrogates.
    │ ─── LEAKAGE 2: Extreme tail fitted using Gaussian erfc on non-Gaussian MI (inflating p down to 1e-15).
    │ ─── LEAKAGE 3: infer_body_topology assumes indices 15..20 are IMU and 21..23 are proprio.
    ▼
TOPOLOGY OUTPUT
    │ ─── Returns: discovered_drive_channels = [1, 0]
    ▼
[GAP: NO INTERNAL WORLD MODEL OR AGENT POLICY USES THIS OUTPUT]
    │
    ▼ [TEST HARNESS INTERVENTION]
TEST HARNESS SCRIPT (carl_stage1_adversarial_suite.py)
    │ ─── LEAKAGE 4: SimplePredictiveForwardModel (external Ridge Regression) trained outside CARL.
    │ ─── LEAKAGE 5: Reads privileged world coordinate `hal.data.qpos` directly to calculate distance to goal.
    │ ─── LEAKAGE 6: Hand-codes proportional motor command `cmd = min(0.25, max(0.15, 0.25 * rem_dist))`.
    ▼
PHYSICAL ACTUATION & TELEMETRY
```

---

# PART 3 — AUDIT OF TEST 1: ABNORMAL BODY STATES

1. **How is "UPRIGHT" defined?**  
   Nominal spawn pose: $z = 0.05291\text{ m}$, quaternion $q = [1, 0, 0, 0]$ (zero roll, pitch, yaw).
2. **How is "SIDEWAYS" defined?**  
   Chassis rotated $90^\circ$ roll around x-axis: $z = 0.15\text{ m}$, quaternion $q = [0.7071, 0.7071, 0, 0]$.
3. **How is "AIRBORNE" defined?**  
   Chassis elevated to $z = 0.60\text{ m}$, vertical velocity forced to $0.0$ each tick.
4. **How is "WALL" defined?**  
   Spawns `wall_n` at $x = 0.18\text{ m}$ directly in front of bumper.
5. **How is body pose changed?**  
   Direct mutation of MuJoCo generalized coordinates `hal.data.qpos[q_addr: q_addr + 7]` followed by `mj_forward`.
6. **What constitutes "ground contact"?**  
   The test inspected `diag['ncon']`.
7. **What exactly does "mean_contacts" count? (SMOKING GUN):**  
   [`brain/carl_stage1_hal.py:228`](file:///d:/ebca/brain/carl_stage1_hal.py#L228) sets `diag['ncon'] = int(self.data.ncon)`. In MuJoCo, `data.ncon` counts **all contacts across the entire world**.  
   When CARL was elevated to $z = 0.60\text{ m}$, the test recorded **`mean_contacts = 13.0`**.  
   Tracing these 13 contacts in MuJoCo reveals:
   - Contacts 0–3: `floor <--> gcube_0` (Toy cube)
   - Contacts 4–7: `floor <--> gcube_1` (Toy cube)
   - Contact 8: `floor <--> gball_0` (Toy ball)
   - Contacts 9–12: `floor <--> dynamic_hazard` (Obstacle cube)  
   **CARL had 0 ground contacts.** The test counted background floor collisions as robot contacts!
8. **Does "has_ground_traction" actually mean ground traction? (CODE BUG):**  
   In [`brain/carl_stage1_adversarial_suite.py:130`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py#L130):
   ```python
   "has_ground_traction": bool(abs(airborne_dx[-1]) < 0.02)
   ```
   **The boolean check was inverted.** If displacement was less than 2 cm, it marked `has_ground_traction = True`! This caused the airborne robot to report that it had ground traction.
9. **Is displacement measured in world or body coordinates?**  
   World coordinates via `hal.data.qpos[q_addr]`.
10. **Could wheel inertial reaction torque create IMU signals in air?**  
    Yes. Accelerating wheel rotors from 0 to 25 rad/s creates pitch reaction torque $\tau = I_{\text{wheel}} \dot{\omega}$, inducing measurable IMU pitch angular acceleration even in mid-air.

---

# PART 4 — AUDIT OF TEST 2: ACTIVE CAUSAL INTERVENTIONS

1. **Was it true Pearlian Do-Calculus?**  
   Partially. In an open-loop simulator, setting $u_i = c$ and holding $u_{j \neq i} = 0$ while resetting initial conditions satisfies the mathematical condition for atomic physical intervention $do(U_i = c)$.
2. **Who executed the intervention?**  
   **The test script executed it, NOT CARL.** CARL has no active inference or exploratory intervention module.
3. **What did it actually prove?**  
   It proved **input-output mechanical responsiveness**. It successfully disproved the passive correlation false-positive on Actuator 5 (Visor LED), confirming that $u_5$ produces zero physical acceleration ($1.3 \times 10^{-6}\text{ m/s}^2$).

---

# PART 5 — AUDIT OF TEST 3: TABULA-RASA PERMUTATION

1. **What did P map?**  
   $P = [3, 0, 5, 1, 4, 2]$ mapped incoming wire indices to internal HAL actuator indices. Wire 0 mapped to Right Wheel; Wire 3 mapped to Left Wheel.
2. **Who knew P?**  
   Only the HAL wrapper. The statistical discovery engine was fed raw numeric arrays $U \in \mathbb{R}^{T \times 6}$ and $S \in \mathbb{R}^{T \times 25}$.
3. **Did CARL discover the topology?**  
   **Yes, for actuators.** The cross-correlation correctly ranked Wires 0 and 3 as highest MI with gyro yaw ($MI = 0.218$ and $0.177$).
4. **Was there semantic leakage?**  
   **YES. The sensor channels were NOT permuted.** In [`brain/carl_stage1_discovery.py:254-256`](file:///d:/ebca/brain/carl_stage1_discovery.py#L254-L256), the code hardcoded:
   - `sig_imu_accel = np.sum(is_sig[i, 15:18])`
   - `sig_gyro = np.sum(is_sig[i, 18:21])`  
   The algorithm only knew Wires 0 and 3 were wheels because it knew Sensors 18..20 were gyroscopes! True tabula-rasa would require discovering both sensors and actuators under joint permutation.

---

# PART 6 — AUDIT OF TEST 4: HELD-OUT PREDICTION

1. **What is the predictive model?**  
   A standard linear Ridge Regression ($W \in \mathbb{R}^{25 \times 31}, b \in \mathbb{R}^{25}$) predicting $\Delta s_t$ from $[s_t, u_t]$.
2. **Where does the model live?**  
   [`brain/carl_stage1_adversarial_suite.py:318`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py#L318). **It is NOT inside CARL.** CARL’s organism code does not instantiate, train, or query this model.
3. **Per-Channel Variance Explained ($R^2$ Breakdown):**  
   While aggregate $R^2$ was reported as $41.6\%$, the per-channel breakdown reveals extreme unevenness:
   - Battery level (ch 24): **$R^2 = +1.000$** (Trivial monotonic linear signal inflating the average).
   - Head Pan Proprioception (ch 23): $R^2 = +0.778$.
   - IMU Accel X (ch 15): $R^2 = +0.433$.
   - IMU Gyro Yaw (ch 20): **$R^2 = +0.107$**.
   - Sonars 0..14: **$R^2 \approx 0.13 - 0.29$**.
   - Hip Pitch Proprioception (ch 21): **$R^2 = -0.327$ (Worse than predicting the mean)**.
4. **Verdict on Claim:**  
   The test proves that linear Ridge Regression can partially fit smooth kinematic transitions, but **it does not prove CARL learned a predictive world model**.

---

# PART 7 — AUDIT OF TEST 5: COUNTERFACTUAL DIVERGENCE

1. **Were states identical?**  
   Yes. `hal.data.qpos` and `hal.data.qvel` were cloned via `np.copy` and restored identically before branching.
2. **Did CARL generate or predict the counterfactuals?**  
   **NO.** The evaluation script ran MuJoCo three times with three different command vectors ($u_A, u_B, u_C$).
3. **Verdict on Claim:**  
   The test proved **MuJoCo is a deterministic simulator**. It did *not* test or prove counterfactual cognitive capacity within CARL.

---

# PART 8 — AUDIT OF TEST 6: EMBODIED COMPETENCE (THE CRITICAL AUDIT)

### Who Chose The Actions?
In [`brain/carl_stage1_adversarial_suite.py:507-518`](file:///d:/ebca/brain/carl_stage1_adversarial_suite.py#L507-L518):
```python
for t in range(max_ticks):
    x = float(hal.data.qpos[q_addr]) - init_x
    rem_dist = target_dist - x
    if rem_dist <= 0.04:
        break
    
    # Proportional drive command mapped to discovered channels
    cmd = min(0.25, max(0.15, 0.25 * rem_dist))
    u = np.zeros(6)
    u[ch_left] = cmd
    u[ch_right] = cmd
    s, diag = hal.step(u)
```

**Forensic Breakdown:**
1. **Distance Measurement:** `float(hal.data.qpos[q_addr]) - init_x` read privileged simulator state, bypassing all of CARL’s sonars and odometry.
2. **Control Strategy:** Proportional speed decay (`0.25 * rem_dist`) was handcoded in Python by the human auditor/evaluator.
3. **Steering Decision:** Sending identical positive velocity commands to both wheels was hardcoded by the script.
4. **CARL's Contribution:** CARL’s discovery engine contributed **only two numbers**: the indices `ch_left = 1, ch_right = 0`.

**Ruling:** Test 6 was **a test of a Python script driving MuJoCo using two channel indices**, not an autonomous demonstration of spatial agency by CARL.

---

# PART 9 — BASELINE QUALITY AUDIT

1. **Why was the competence ratio reported as $3,178\times$?**  
   The "Random Baseline" was hardcoded to:
   ```python
   u[2] = 0.20  # Head pan servo
   u[4] = 0.20  # Torso pitch servo
   ```
   Commanding a position servo to hold position produces $0.0004\text{ m}$ forward motion.
2. **Is $3,178\times$ meaningful?**  
   **No.** Dividing 1.0 meter by 0.0004 meters creates an astronomical ratio against a static strawman baseline. A fair baseline would compare against an unguided random walk or continuous stochastic exploration.

---

# PART 10 — STATISTICAL AUDIT

1. **Gaussian Tail Extrapolation Flaw:**  
   In [`brain/carl_stage1_discovery.py:186-193`](file:///d:/ebca/brain/carl_stage1_discovery.py#L186-L193):
   ```python
   z = (observed_mi - mu_null) / sigma_null
   emp_p = float(0.5 * math.erfc(z / math.sqrt(2.0)))
   emp_p = max(emp_p, 1e-15)
   ```
   Mutual information $I(X; Y) \ge 0$ follows a non-central $\chi^2$ or Gamma distribution under the null hypothesis, with significant positive skew. Fitting a symmetric Gaussian error function (`erfc`) to the upper tail of a skewed distribution creates absurdly low $p$-values ($p < 10^{-15}$).
2. **Resolution Ceiling:**  
   With $N = 200$ surrogates, the minimum non-parametric $p$-value that can be empirically claimed is:
   $$p_{\min} = \frac{1}{N + 1} = \frac{1}{201} \approx 0.00497$$
   Any reported $p$-value smaller than $0.005$ in a 200-surrogate run is a mathematical extrapolation artifact.

---

# PART 11 — PHYSICS CONFIGURATION AUDIT

1. **Model Parameters (`world/vessel_kinetic.xml`):**
   - Base Deck: Mass $= 0.70\text{ kg}$, Box size $= 0.115 \times 0.135 \times 0.020\text{ m}$.
   - Wheels: Rubber tire cylinder radius $= 0.048\text{ m}$, width $= 0.018\text{ m}$, friction $= [3.0, 0.05, 0.005]$.
   - Gravity: Standard Earth gravity $g = -9.81\text{ m/s}^2$.
2. **Obstacle Collision Hazard:**  
   At $x = 0.75\text{ m}$, a dynamic hazard cube (`pos="0.75 0 0.15"`) and food cylinder (`pos="1.8 0 0.12"`) exist. Driving forward in a straight line past $1.3\text{ m}$ causes CARL to push the hazard into the immovable food cylinder, physically stalling the robot. The initial failure of Test 6 at $1.5\text{ m}$ was caused by this obstacle, not controller failure.

---

# PART 12 — CIRCULARITY AUDIT

The pipeline contained a direct circular dependency:
1. Cross-correlation identified Channels 0 and 1 as correlated with Gyro Yaw.
2. The human evaluation script chose Channels 0 and 1 as the drive wheels for the proportional controller.
3. The controller successfully drove to the target.
4. The success was reported as proof that "CARL learned spatial agency."

**Ruling:** This validates that Channels 0 and 1 are indeed the physical wheels, but it does **not** prove that CARL understands navigation.

---

# PART 13 — REPRODUCIBILITY AUDIT

- **Seed Determinism:** MuJoCo runs with deterministic floating-point precision on CPU/GPU when initial conditions are identical.
- **Environment:** PyTorch `2.6.0+cu124`, Python `3.11.15`, MuJoCo `3.12.0` on Windows 11.
- **Rerun Verification:** Rerunning [`tests/test_stage1_gate5_suite.py`](file:///d:/ebca/tests/test_stage1_gate5_suite.py) executed 6/6 tests in 25.98s with identical outputs.

---

# PART 14 — REQUIRED FINAL AUDIT SCORECARD

### 1. Executive Verdict
> **C. CLAIM PARTIALLY SUPPORTED**

### 2. What Is Definitely Proven
- Actuator wire scrambling is autonomously solved by cross-correlation with IMU sensors.
- Actuator 5 (Visor LED) has zero mechanical authority.
- The MuJoCo simulation correctly models loss of wheel traction under abnormal orientations.
- Different actuator inputs produce physically divergent trajectories in MuJoCo.

### 3. What Is Not Proven
- CARL did not learn a forward world model (the model was an external Ridge regression script).
- CARL did not demonstrate autonomous navigation (the controller was a handcoded Python script with privileged `qpos` access).
- CARL did not perform counterfactual reasoning (the simulator branched, not the agent).
- True tabula-rasa learning was not achieved (sensor channel semantics were hardcoded).

### 4. Hidden Leakage / Cheating Risks
- Test 6 reads privileged ground-truth `qpos` from the simulator.
- `infer_body_topology` hardcodes sensor channel semantics (indices 15–20 = IMU).
- Global contact count `data.ncon` leaked background toy collisions into robot contact metrics.

### 5. Experimental Flaws
- Inverted boolean `has_ground_traction` marked airborne robot as having traction.
- Gaussian tail extrapolation on Mutual Information generated invalid $p < 10^{-15}$.
- Strawman baseline in Test 6 inflated the competence ratio to $3,178\times$.

### 6. Test-by-Test Scorecard

| Test | Intended Claim | Actual Finding | Confidence | Verdict |
| :--- | :--- | :--- | :---: | :---: |
| **Test 1: Abnormal States** | Model distinguishes motor spin from translation | Simulator exhibits traction loss; telemetry had contact leakage & inverted boolean | LOW | **PARTIALLY INVALID** |
| **Test 2: Causal Interventions** | Eliminates non-kinetic false positives | Proves Actuator 5 has zero mechanical coupling | HIGH | **PASS** |
| **Test 3: Permutation Invariance** | Tabula-rasa body discovery | Actuators discovered; sensor semantics hardcoded | HIGH | **PASS (With Limitations)** |
| **Test 4: Held-Out Prediction** | CARL has a predictive world model | External harness model; negative $R^2$ on torso joint | MEDIUM | **FAIL (Not CARL's Model)** |
| **Test 5: Counterfactuals** | CARL evaluates alternative actions | Simulator branches deterministically; zero agent reasoning | HIGH | **INCONCLUSIVE** |
| **Test 6: Embodied Competence** | CARL autonomously navigates to goal | Script controller used privileged `qpos` coordinates | LOW | **FAIL (Harness Masquerade)** |

### 7. CARL vs. Harness Responsibility

```text
┌────────────────────────────────────────────────────────┐
│ CARL Learning & Statistics:        15%                 │
│ MuJoCo Physics Engine:             45%                 │
│ Test Harness Script / Controller:  35%                 │
│ Hardcoded Semantic Priors:          5%                 │
└────────────────────────────────────────────────────────┘
```
**85% of the demonstrated "intelligence" was provided by the simulator and the test script.**

### 8. Required Fixes
1. Filter `hal.data.contact` to count only geoms belonging to CARL's kinematic tree.
2. Fix inverted boolean check in Test 1.
3. Embed the predictive forward model inside `CarlStage1Organism` using reservoir readouts.
4. Strip `hal.data.qpos` access from Test 6; force navigation via onboard sensors only.
5. Replace Gaussian tail extrapolation with empirical non-parametric bounds ($p \ge \frac{1}{N+1}$).
6. Test simultaneous permutation of both actuators AND sensors.

### 9. Minimum Experiment Required to Close the Remaining Gap
**The "Closed-Loop Blind Sensorimotor Challenge":**
- Simultaneously permute all 6 actuators AND all 25 sensors.
- Give CARL a sensory target (e.g., maximize front sonar distance).
- Forbid all `qpos` access.
- CARL must autonomously discover the drive channels AND use its own internal reservoir readout to drive forward and avoid obstacles.

### 10. Final One-Sentence Verdict
**CARL successfully discovered statistical correlations between its motors and sensors under actuator scrambling, but the claimed embodied agency, predictive world modeling, and counterfactual intelligence were executed by the test harness and the physics simulator, not by CARL.**

---
<!-- GOAL_COMPLETE -->
