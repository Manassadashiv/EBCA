#!/usr/bin/env python3
import sys

OUT_FILE = r"D:\ebca\CARL_PRESENTATION_COMPLETE_LAYMAN_GUIDE.md"

phase2_text = """
# Phase 2: Developmental Roadmap & Stage 1 Embodied Grounding (Slides 18–25)

---

## Slide 18: The 5-Stage Master Developmental Roadmap
- **Slide Title**: *CARL DEVELOPMENT & IMPLEMENTATION ROADMAP (Stages 1-5)*
- **What this slide represents**: The master architectural spine of the entire project. It proves that CARL is built like a growing living creature through strict developmental milestones, not a collection of random hackathon scripts.

### Plain-English Core Message & Real-World Analogy
> **Analogy**: How does a human child develop?  
> 1. A newborn baby first kicks its legs in the crib to figure out what legs are (**Stage 1: Learn My Body**).  
> 2. A toddler learns to crawl around the living room, remembering where the sofa and doors are (**Stage 2: Learn My World**).  
> 3. A child learns how to run smoothly, dodge furniture, and explore without bumping into walls (**Stage 3: Learn How to Behave**).  
> 4. As the child grows up, they form lifelong episodic memories of past experiences (**Stage 4: Remember & Develop**).  
> 5. Eventually, an adult develops self-awareness—reflecting on their own mistakes and consciously improving themselves (**Stage 5: Understand Myself & Improve**).

### Breakdown of the 5 Stages
1. **Stage 1 — Sensorimotor Grounding & Body Babbling**: **COMPLETE & CERTIFIED ✅** (Learned body dynamics, wheel slippage, stability envelopes).
2. **Stage 2 — Generative World & Self Modeling**: **COMPLETE & CERTIFIED ✅** (Built 2,114-unit CANN compass, world model with $R^2=0.97$, occupancy memory).
3. **Stage 3 — Continuous Action Synthesis & Behavioral Discovery**: **CURRENT ACTIVE MILESTONE ⏳** (Continuous MPPI trajectory synthesis, Active Inference, dead-end escape).
4. **Stage 4 — Autopoietic / Lifelong Memory & Persistence**: **FUTURE WORK** (Synaptic plasticity via R-STDP, holographic hyperdimensional memory).
5. **Stage 5 — Metacognition & Permission-Gated Self-Modification**: **FINAL MATURITY** ("The Witness" introspective failure analysis).

### Historical Note for Examiners
- Earlier project documents referred to "Phases 0 through 8." These have been cleanly consolidated into this strict 5-Stage biological architecture. (Phase 0 $\to$ Stage 1; Phase 1 $\to$ Stage 1.1; Phase 2 $\to$ Stage 2; Phases 3–4 $\to$ Stage 3).

---

## Slide 19: Stage 1 — Learning My Body (Grounding & Babbling)
- **Slide Title**: *STAGE 1 — SENSORIMOTOR GROUNDING & BODY BABBLING*
- **What this slide represents**: The detailed breakdown of how Stage 1 was constructed and certified.

### Plain-English Core Message
Before you can ask a robot to solve a maze, the robot must first discover what its own body is capable of doing. If a motor receives a command of `0.5`, does the robot roll forward 1 meter, or 0.1 meters, or does it tip over? Stage 1 answers these questions without any pre-programmed assumptions.

### The 4 Pillars Built in Stage 1
1. **Embodied System**: MuJoCo 3D digital twin running at 30 Hz with continuous wheel contacts.
2. **Cognitive System**: 6-channel anonymous motor babbling (sending random pulses to the left and right wheels to observe the resulting physical motion).
3. **Adaptive/Safety System**: An online slip observer and dynamic stability monitor that detects if the chassis is in danger of tipping over.
4. **Validation System**: Pre-registered regression tests evaluated under strict "fail-closed" scoring (if any metric fails, the entire milestone fails).

---

## Slide 20: Stage 1 Live Demonstration
- **Slide Title**: *STAGE 1 LIVE DEMONSTRATION*
- **What this slide represents**: A live simulation recording showing CARL babbling its motors, learning how to roll forward in straight lines and gentle arcs, and safely engaging its reflex override when an obstacle approaches.

### Verbatim Viva Script (What to say out loud)
> *"This video demonstration captures Stage 1 in action inside the MuJoCo twin. Notice that the robot starts with zero prior knowledge of its wheel layout. Through anonymous motor pulses, it correlates wheel RPM with IMU inertial feedback, learning to produce forward velocity while maintaining complete chassis roll/pitch stability."*

---

## Slide 21: Stage 1 Validation Evidence (Trajectory Envelope)
- **Slide Title**: *STAGE 1 VALIDATION EVIDENCE*
- **Visual Element**: **Plot 1 — Physical $(\mu, \theta)$ Trajectory Envelope**

### The "What, Why, When, Where, How" Protocol
- **WHAT is this plot showing?**: It plots the spatial trajectories of CARL across **81 consecutive validation runs** under varying initial headings and friction coefficients. The green paths show clean forward movement without tipping or wall collision.
- **WHY did we make this plot?**: To prove that Stage 1 isn't a fluke that worked once. We had to prove that across 81 distinct random seeds, the body babbling controller is mathematically stable and never crashes.
- **WHEN does this happen?**: At the conclusion of Stage 1 qualification testing, before CARL is allowed to graduate to Stage 1.1.
- **WHERE does the data come from?**: The MuJoCo physics engine recording true chassis odometry at 30 Hz across an 81-trial adversarial parameter grid.
- **HOW do you read it?**: Look at the envelope boundary. The paths remain strictly bounded within the safe corridor. Across all **81 out of 81 runs**, there were **0 collisions** and **0 chassis tip-overs**.

### Verbatim Viva Script
> *"Slide 21 provides the empirical qualification evidence for Stage 1. Across 81 distinct trials varying heading angles and surface conditions, CARL successfully maintained stability and forward progress with an unblemished 100% pass rate and zero collisions, formally certifying Stage 1."*

---

## Slide 22: Stage 1.1 — Individual Emergence & Adaptive Learning
- **Slide Title**: *STAGE 1.1 — INDIVIDUAL EMERGENCE & ADAPTIVE SENSORIMOTOR LEARNING*
- **What this slide represents**: Real robots aren't identical clones fresh off a factory conveyor belt. One robot might have worn-out rubber tires, while another might be driving on slick wet linoleum. Stage 1.1 allows CARL to adapt its internal motor predictions online based on real-time traction feedback.

### The 3 Core Pillars of Stage 1.1
1. **Friction Dynamics**: Continuously measuring the difference between how fast the wheels are spinning and how fast the body is actually moving forward (wheel slip).
2. **Stability Envelopes**: Mapping out the safe operating boundaries of linear speed ($v \in [0.1, 0.5]\text{ m/s}$) and angular turning speed ($\omega \in [0.2, 1.5]\text{ rad/s}$).
3. **Adaptive Outcome**: When the floor becomes icy, CARL automatically scales back its motor aggressive factor to prevent uncontrollable spins.

---

## Slide 23: Stage 1.1 — Dynamical Stability Envelopes
- **Slide Title**: *EMBODIED SENSORIMOTOR GROUNDING: STABILITY ENVELOPES*
- **Visual Element**: **Plot 2 — Figure 2(a): 10,000-Tick Dynamical Stability Phase Portrait**

### The "What, Why, When, Where, How" Protocol
- **WHAT is this plot showing?**: A phase portrait showing linear forward velocity ($v$, on the X-axis) versus rotational yaw velocity ($\omega$, on the Y-axis) over **10,000 continuous simulation ticks** (over 5.5 minutes of continuous high-speed driving).
- **WHY did we make this plot?**: To discover the robot's physical rollover limits. If you turn a sharp corner while driving too fast, centrifugal force flips the rover onto its side. This plot maps the exact safe envelope where tipping never occurs.
- **WHEN does this happen?**: During the 10,000-tick motor babbling stress test in Stage 1.1.
- **WHERE does the data come from?**: The onboard gyroscope and chassis pitch/roll sensors sampled at 30 Hz.
- **HOW do you read it?**: The dense cloud of blue trajectories forms a neat, symmetrical oval centered at $(0, 0)$. As long as the trajectories stay inside the bounding box ($v \le 0.5\text{ m/s}$, $|\omega| \le 1.5\text{ rad/s}$), the chassis pitch and roll angles stay below $3^\circ$ (completely flat and upright). Zero rollovers occurred in 10,000 ticks.

### Verbatim Viva Script
> *"Figure 2(a) on Slide 23 demonstrates CARL's dynamic stability phase portrait over 10,000 execution ticks. By evaluating forward velocity against yaw rate, we establish the safe kinematic operating envelope: linear velocity up to 0.5 m/s and angular rate up to 1.5 rad/s. Throughout this entire battery, the chassis maintained perfect upright equilibrium with zero rollover events."*

---

## Slide 24: Stage 1.1 — Sensorimotor Contingency Matrix
- **Slide Title**: *EMBODIED SENSORIMOTOR GROUNDING: PARAMETER DISCOVERY*
- **Visual Element**: **Plot 3 — Figure 2(b): Empirical Sensorimotor Contingency Matrix**

### The "What, Why, When, Where, How" Protocol
- **WHAT is this plot showing?**: A 2D heatmap showing how much wheel slip occurs across different combinations of motor commands and surface friction coefficients ($\mu$).
- **WHY did we make this plot?**: To identify the **critical friction cliff** where classical robot controllers break down.
- **WHEN does this happen?**: During the systematic friction sweep where floor friction was stepped from dry asphalt down to polished ice.
- **WHERE does the data come from?**: Comparing wheel encoder velocity against actual chassis ground displacement measured by MuJoCo's contact solver.
- **HOW do you read it?**: Look at the color transition. Above $\mu = 0.35$, the surface is green/yellow (traction is good, slip is manageable). But below the critical threshold of **$\mu = 0.35$**, the heatmap turns bright red—longitudinal slip exceeds $40\%$. This proves why a simple robot that assumes wheels never slip will inevitably crash in low-traction environments.

### Verbatim Viva Script
> *"Figure 2(b) maps the empirical sensorimotor contingency matrix across ground friction variations. Notice the sharp phase transition at friction coefficient mu = 0.35. Below this boundary, wheel slip exceeds 40%, proving that dead reckoning alone is fundamentally insufficient and necessitating the continuous attractor spatial representations developed in Stage 2."*

---

## Slide 25: Stage 1.1 — Kinematic Friction & Unprivileged Odometric Drift
- **Slide Title**: *SENSORIMOTOR GROUNDING & ODOMETRY: SLIP MONOTONICITY*
- **Visual Element**: **Plot 4 — Figure 3: Friction Gradient Response and Slip Monotonicity ($\mu \in [0.05, 1.0]$)**

### The "What, Why, When, Where, How" Protocol
- **WHAT is this plot showing?**: A curve showing the exact relationship between floor friction ($\mu$, on the X-axis) and wheel slippage percentage ($\sigma$, on the Y-axis).
- **WHY did we make this plot?**: To prove that CARL's onboard slip observer behaves with strict mathematical monotonicity—meaning as the floor gets slicker, the observer's estimated slip percentage rises smoothly and predictably, rather than fluctuating randomly.
- **WHEN does this happen?**: During the unprivileged odometry validation sweep across 20 distinct friction steps.
- **WHERE does the data come from?**: CARL's internal kinematic observer equations running in real time without external ground-truth feedback.
- **HOW do you read it?**:
  - In high-friction regimes ($\mu \in [0.50, 1.0]$), slip stabilizes around **$24.1\%$** (normal tire deformation).
  - In extreme low-friction ice regimes ($\mu \in [0.05, 0.25]$), slip spikes all the way to **$98.2\%$** (wheels spinning frantically while the chassis barely creeps forward).
  - The curve is completely smooth and monotonic, demonstrating that CARL's sensory grounding can accurately diagnose when it is trapped on ice.

### Verbatim Viva Script
> *"Figure 3 on Slide 25 presents the friction gradient response across the range from mu = 0.05 to 1.0. Under ice conditions, longitudinal slip reaches 98.2%, causing naive wheel odometry to drift rapidly. Because CARL's kinematic observer captures this monotonic slip curve accurately, it knows precisely when its odometry is degraded and dynamically compensates its navigation confidence."*
"""

with open(OUT_FILE, "a", encoding="utf-8") as f:
    f.write(phase2_text)

print("Appended Phase 2 (Slides 18-25)")
