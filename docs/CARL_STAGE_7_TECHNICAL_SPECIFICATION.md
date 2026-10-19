# CARL-DX Stage 7: Technical Specification & Mathematical Architecture
## Social Embodiment, Non-Verbal Affective Telemetry, Proxemics & Epistemic Companion Robotics

**Document Version:** 1.0.0 (Certified Architectural Design)  
**Author:** CARL-DX Core Engineering Directorate  
**Prerequisites:** Stages 1 through 6 Certified ✅  
**Scientific Foundations:** OpenAlex, Europe PMC, arXiv Multi-Database Corpus (October 2026)  

---

## 1. System Overview & The Companion Paradigm

Stage 7 elevates the CARL-DX 2,114-unit neuromorphic organism from a **solitary autonomous explorer** into a **socially grounded, emotionally expressive companion**.

Rather than utilizing theatrical, scripted animations, Stage 7 grounds all outward expressions (audio chirps, mood LED hue, chassis micro-movements, and personal space deceleration) in **real-time internal latent states**:
1. **The Witness Introspective Telemetry** (7 channels of distress, slip, and prediction error).
2. **Active Inference Expected Free Energy** (Pragmatic goal $G_{\text{pragmatic}}$ vs. Epistemic curiosity $G_{\text{epistemic}}$).
3. **Endocrine Hormonal Modulation** (Cortisol and Adrenaline synthetic levels).
4. **2,048-D HDC Associative Memory** (One-shot filial imprinting of caregiver, friends, and objects).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CANONICAL NEUROMORPHIC CORE (STAGES 1–6)            │
│  [2,114-Unit CANN]  [Active Inference MPPI]  [7-Channel Witness]       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Zero-Copy Agent Bus
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     STAGE 7: SOCIAL EMBODIMENT ORGAN                    │
│                                                                        │
│  1. Somatic Acoustic Prosody Engine (Arousal-Valence PWM Synthesizer)  │
│  2. Photonic Mood Halo (24-bit HSV State Vector Display)               │
│  3. 2-DOF Pan-Tilt Visuomotor Gaze Head (Eye Contact & Ground Scanning)│
│  4. Proxemic Personal Space Field (Ankle Safety Deceleration Bubble)   │
│  5. Social Referencing & Epistemic Inquiry Protocol                    │
│  6. 2,048-D HDC One-Shot Show-and-Tell Filial Imprinting Engine       │
│  7. Bi-Directional Interactive Telemetry & Monologue HUD               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical Formulations & Latent Mappings

### 2.1 Latent Affective Space (Arousal & Valence)
Outward vocal and optical expressions are parameterized over the Russell Circumplex Model of Affect, mapped directly from cognitive organs:

$$\text{Arousal } A(t) = \text{clip}\Big(0.65 \cdot D_{\text{witness}}(t) + 0.35 \cdot C_{\text{endocrine}}(t), \; 0.0, \; 1.0\Big)$$

$$\text{Valence } V(t) = \tanh\Big(1.20 - G_{\text{pragmatic}}(t) - 0.80 \cdot G_{\text{epistemic}}(t) - 2.0 \cdot D_{\text{witness}}(t)\Big)$$

Where:
* $D_{\text{witness}}(t) \in [0, 1]$ is the composite failure distress index from [`carl_metacognitive_witness.py`](file:///d:/ebca/brain/carl_metacognitive_witness.py).
* $C_{\text{endocrine}}(t) \in [0, 1]$ is synthetic cortisol from [`carl_endocrine_system.py`](file:///d:/ebca/brain/carl_endocrine_system.py).
* $G_{\text{pragmatic}}, G_{\text{epistemic}}$ are the twin components of Expected Free Energy from [`carl_active_inference.py`](file:///d:/ebca/brain/carl_active_inference.py).

---

### 2.2 Acoustic Prosody Engine (The R2-D2 Voice)
The acoustic engine synthesizes real-time sound frequencies $F_0(t)$ and harmonic profiles without pre-recorded audio files:

$$F_0(t) = F_{\text{base}} + \Delta F \cdot A(t) + 140 \cdot V(t) \quad (\text{Hz})$$

Where $F_{\text{base}} = 220\text{ Hz}$ (A3) and $\Delta F = 680\text{ Hz}$.

* **Harmonic Consonance ($V > 0.4$, Happy / Purr):**  
  Emits consonant major thirds ($1.25 \cdot F_0$) and fifths ($1.50 \cdot F_0$) with soft, upward pitch glide ($\frac{dF_0}{dt} > 0$).
* **Curiosity Chirp ($G_{\text{epistemic}} > 0.6$, Exploring):**  
  Emits staccato ascending sweeps ($600 \to 1400\text{ Hz}$) with high pulse repetition rate ($8\text{ Hz}$).
* **Alarm / Tantrum ($V < -0.3, A > 0.7$, Trapped / Slipping):**  
  Emits discordant tritone intervals ($1.414 \cdot F_0$) with downward pitch drop and rapid frequency chatter ($25\text{ Hz}$ vibrato).
* **NREM Sleep Breathing (Consolidation):**  
  Slow sinusoidal envelope ($0.25\text{ Hz}$, $160 \to 190\text{ Hz}$) mirroring synaptic downscaling.

---

### 2.3 Photonic Mood Halo (WS2812B RGB Beacon)
A single addressable RGB LED communicates internal state via continuous HSV color space:

$$\text{Hue } H(t) = \begin{cases}
120^\circ \; (\text{Pure Green}) & \text{if } V(t) > 0.5 \quad [\text{Safe / Content}] \\
200^\circ \; (\text{Deep Cyan/Blue}) & \text{if } G_{\text{epistemic}} > 0.5 \text{ and } V \ge 0 \quad [\text{Curious}] \\
45^\circ \; (\text{Warm Amber}) & \text{if } -0.3 \le V(t) \le 0.1 \quad [\text{Caution / Inquiry}] \\
0^\circ \; (\text{Flashing Crimson}) & \text{if } V(t) < -0.3 \quad [\text{Alarm / Stuck}] \\
275^\circ \; (\text{Pulsing Violet}) & \text{if } \text{State} = \text{SLEEP\_REPLAY}
\end{cases}$$

---

### 2.4 Human-Aware Proxemics & Ankle Safety Bubble
To ensure human physical safety and comfort (Edward T. Hall's Proxemics Taxonomy), an asymmetric social repulsive potential $J_{\text{prox}}(\mathbf{x})$ is added to the MPPI continuous trajectory cost:

$$J_{\text{prox}}(\mathbf{x}) = \begin{cases}
+\infty & \|\mathbf{x} - \mathbf{x}_{\text{human}}\| < d_{\text{intimate}} \quad (0.35\text{ m}) \\
\eta_{\text{prox}} \cdot \exp\left(-\frac{\|\mathbf{x} - \mathbf{x}_{\text{human}}\| - d_{\text{intimate}}}{\sigma_{\text{comfort}}}\right) & 0.35\text{ m} \le \|\mathbf{x} - \mathbf{x}_{\text{human}}\| \le 1.20\text{ m} \\
0 & \|\mathbf{x} - \mathbf{x}_{\text{human}}\| > 1.20\text{ m}
\end{cases}$$

Where:
* $d_{\text{intimate}} = 0.35\text{ m}$ is the hard physical non-intrusion safety cushion (preventing any contact with shoes/ankles).
* $\sigma_{\text{comfort}} = 0.25\text{ m}$ governs progressive deceleration.
* When executing the **Puppy Greeting**, CARL drives toward the human at $0.4\text{ m/s}$, decelerates smoothly through the personal zone, and comes to a complete rest at precisely $0.35\text{ m}$, tilting its head $+35^\circ$ to establish visual eye contact.

---

### 2.5 Social Referencing Protocol (Epistemic Caregiver Query)
When encountering an unknown obstacle where visual reconstruction entropy exceeds threshold $H(z) > \theta_{\text{query}}$:
1. **Kinematic Halt:** Rover commands zero wheel velocity ($\mathbf{u} = [0, 0]^\top$).
2. **Gaze Pivot:** Head pan/tilt rotates to caregiver bearing:
   $$\theta_{\text{gaze}}^* = \text{atan2}(y_{\text{caregiver}} - y, \; x_{\text{caregiver}} - x)$$
3. **Inquiry Signal:** Emits interrogative frequency sweep ($440 \to 880\text{ Hz}$) + flashes amber halo.
4. **Telemetry Dispatch:** Transmits to terminal/HUD:  
   *`🤖 CARL: "Unfamiliar obstacle detected. Manas, is it safe to proceed?"`*
5. **Bayesian Prior Update:**
   * **Affirmative Cue (Wave / "Yes"):** Updates obstacle traversability $P(\text{safe}) \leftarrow 0.95$. Bypasses obstacle with normal clearance.
   * **Negative Cue (Palm / "No"):** Updates $P(\text{safe}) \leftarrow 0.00$. Binds obstacle as permanent static hazard; executes PFL2 retreat.

---

### 2.6 One-Shot HDC Filial Imprinting (Show-and-Tell)
Using the Stage 4 2,048-dimensional Fractional Holographic Reduced Representation (FHRR) architecture:
1. The camera extracts normalized visual features $\mathbf{v} \in \mathbb{R}^{64}$ (color, spatial moments, aspect ratio).
2. $\mathbf{v}$ is projected through a static, quasi-orthogonal Gaussian matrix $\mathbf{\Phi} \in \mathbb{R}^{2048 \times 64}$:
   $$\mathbf{h}_{\text{raw}} = \text{sign}\Big(\mathbf{\Phi} \mathbf{v}\Big) \in \{-1, +1\}^{2048}$$
3. Imprinting binds the visual hypervector with semantic identity key $\mathbf{k}_{\text{ID}}$ via circular convolution $\circledast$:
   $$\mathbf{M}_{\text{social}} \leftarrow \mathbf{M}_{\text{social}} + \mathbf{k}_{\text{ID}} \circledast \mathbf{h}_{\text{raw}}$$
4. **Recognition Query:** When searching for an object/person, cosine similarity in HDC space determines match:
   $$\text{Sim}(\mathbf{h}_{\text{current}}, \mathbf{h}_{\text{target}}) = \frac{\mathbf{h}_{\text{current}} \cdot \mathbf{h}_{\text{target}}}{2048} \ge 0.75 \implies \text{MATCH}$$

Execution time: **$< 0.4\text{ ms}$** on CPU / ESP32. Zero pre-training; zero cloud dependencies.

---

## 3. Physical Firmware Integration (ESP32 FreeRTOS Pin Map)

```
Pin 21 (I2C SDA) ──► MPU-6050 IMU + APDS-9960 Gesture Sensor
Pin 22 (I2C SCL) ──► MPU-6050 IMU + APDS-9960 Gesture Sensor
Pin 18, 19, 23, 25 ─► DRV8833 Dual Motor Driver (Left/Right Wheels)
Pin 26 (LEDC 4)  ──► SG90 Pan Servo (Horizontal Head Yaw, ±70°)
Pin 27 (LEDC 5)  ──► SG90 Tilt Servo (Vertical Head Pitch, -35° to +40°)
Pin 13 (RMT/GPIO) ─► WS2812B NeoPixel 8-LED Mood Halo
Pin 14 (LEDC 6)  ──► Passive Piezo Buzzer / PAM8403 Audio Synth
Pin 15, 4, 16    ──► INMP441 I2S Digital Microphone (SCK, WS, SD)
Pin 5, 34, 35, 32 ─► 3x HC-SR04 Sonar Sensors (Left, Center, Right)
```

---

## 4. Verification & Acceptance Criteria

To achieve certified sign-off, Stage 7 must satisfy five pre-registered benchmarks:

1. **Acoustic Latency & Dynamic Range:** Audio frequency responds to Witness distress within $\le 20\text{ ms}$; pitch spans $200\text{ Hz}$ to $2,000\text{ Hz}$ continuously without stutter.
2. **Proxemic Non-Intrusion:** 10/10 human greeting trials must halt at $0.35 \pm 0.05\text{ m}$ distance with **0.0% physical contact** with feet or obstacles.
3. **One-Shot Imprinting Accuracy:** $\ge 90\%$ recognition accuracy on imprinted target vs. 5 unfamiliar distractor items.
4. **Social Referencing Arbitration:** 10/10 unknown obstacle trials must initiate inquiry freeze and correctly branch based on user feedback.
5. **AST Anti-Cheat Invariant:** Zero simulator coordinate leaks (`qpos`, `geom_xpos`) inside the companion decision loop.
