#!/usr/bin/env python3
import sys

OUT_FILE = r"D:\ebca\CARL_PRESENTATION_COMPLETE_LAYMAN_GUIDE.md"

phase3_text = r"""
# Phase 3: Stage 2 — Generative World & Self Modeling (Slides 26–31)

---

## Slide 26: Stage 2 Overview — Learning My World
- **Slide Title**: *STAGE 2 — GENERATIVE WORLD & SELF MODELING*
- **What this slide represents**: Moving from a purely reactive organism (that only responds when it bumps into something) to a **prospective organism** (that can look ahead into the future and imagine what will happen before taking a single step).

### Plain-English Core Message & Real-World Analogy
> **Analogy**: Imagine walking into your living room in total darkness.  
> You don't crash into the dining table every night because your brain holds an **internal spatial model** of where the table, the TV, and the doorway are located. Even with your eyes shut, your internal compass tracks which way you are facing.  
> Stage 2 gives CARL that exact internal imagination and spatial memory.

### The 4 Major Systems Built in Stage 2
1. **Spatial Cognition System**: A **2,114-unit Continuous Attractor Neural Network (CANN)** acting as an unprivileged biological compass and grid map.
2. **Predictive World Model**: A neural forward dynamics model that predicts future sensor readings conditioned on motor actions ($R^2 = 0.9613$).
3. **Deliberation System**: Simulating possible future action branches to avoid dead ends before entering them.
4. **Validation System**: Pre-registered 7-gate acceptance battery ensuring mental simulations match physical reality.

---

## Slide 27: Continuous Attractor Dynamics — Homing Belief vs. Reality
- **Slide Title**: *CONTINUOUS ATTRACTOR DYNAMICS: PHYSICAL REALITY VS INTERNAL CANN SELF MODEL*
- **Visual Element**: **Plots 5 & 6 — Closed-Loop Homing Trajectories (Dev Seed 101 vs. Unseen Seed 505)**

### The "What, Why, When, Where, How" Protocol
- **WHAT are these plots showing?**: Two comparative trajectory graphs showing CARL driving out into a room and then attempting to return to its exact starting dock ("homing") relying purely on its internal CANN attractor network without GPS.
  - Left Plot: Development Seed 101.
  - Right Plot: Unseen Evaluation Seed 505 (a completely novel environment layout).
- **WHY did we make these plots?**: To prove that CARL's internal compass and path integrator do not suffer from catastrophic drift. In classical robotics, wheel odometry errors compound exponentially until the robot is completely lost.
- **WHEN does this happen?**: During the closed-loop homing return test at the end of Stage 2.1.
- **WHERE does the data come from?**: Comparing the internal CANN belief coordinates against ground-truth MuJoCo coordinates.
- **HOW do you read it?**:
  - The blue path is where the robot actually drove in physical reality.
  - The dotted red path is where CARL's internal neural attractor believed it drove.
  - Look at where it ends up: On Seed 101, the final return drift error is just **0.0650 meters** (6.5 cm). On the unseen Seed 505, the error is **0.0570 meters** (5.7 cm). Both are well inside the strict **0.22-meter target gate**.
  - This proves that CARL can successfully navigate out and return to its home dock across both familiar and completely unseen environments.

### Verbatim Viva Script
> *"Slide 27 presents the physical trajectory versus internal CANN belief state across closed-loop homing trials. On development Seed 101, the return drift is just 0.0650 m. On the completely unseen evaluation Seed 505, the drift is 0.0570 m. Both comfortably clear our pre-registered 0.22 m target gate, verifying that the 2,114-unit attractor architecture provides robust, unprivileged spatial localization without GPS."*

---

## Slide 28: Continuous Attractor Head Direction (Ring Attractor Bump)
- **Slide Title**: *CONTINUOUS ATTRACTOR DYNAMICS: 64-HD RING ATTRACTOR BUMP*
- **Visual Element**: **Plot 7 — CANN Ring Attractor Firing Bump Dynamics**

### The "What, Why, When, Where, How" Protocol
- **WHAT is this plot showing?**: A neural activity plot showing 64 Head-Direction (HD) neurons arranged in a continuous circle ($0^\circ$ to $360^\circ$). The Y-axis shows neuronal firing rate, forming a smooth, bell-shaped "activity bump."
- **WHY did we make this plot?**: To verify the biological mechanism of CARL's internal compass. A true continuous attractor network must maintain a single, sharp bump of activity that shifts smoothly when the robot turns, but never disperses into noise or splits into two bumps.
- **WHEN does this happen?**: Throughout all driving movements in Stage 2.
- **WHERE does the data come from?**: The membrane potentials of the 64 HD spiking neurons in the CANN ring.
- **HOW do you read it?**:
  - As the robot rotates, angular velocity signals from the gyroscope push the activity packet around the ring.
  - When the robot stops, the Mexican-hat connectivity (local excitation, global inhibition) holds the bump perfectly stationary.
  - During complete sensory blackouts (simulated blindness), directional drift remained below **0.02 rad/s**, meaning CARL remembers which way it is facing even in pitch darkness.

### Verbatim Viva Script
> *"Figure on Slide 28 illustrates the 1D Continuous Attractor Neural Network bump dynamics. Arranged over a 360-degree periodic manifold, the 64 neurons maintain a sharp, unimodal Gaussian activity packet. Gyroscopic inputs smoothly translate this bump without phase dispersion. Across all 5 multi-seed validation runs, mean homing error was bounded below 0.071 m, and drift during complete sensory blackouts remained under 0.02 rad/s."*

---

## Slide 29: Stage 2.2 — Predictive World Model 7-Gate Validation Table
- **Slide Title**: *STAGE 2.2 — PREDICTIVE WORLD MODEL 7 GATE VALIDATION*
- **Visual Element**: **Table 2 — The Seven-Gate Validation Results**

### Plain-English Breakdown of the 7 Gates
This table represents the rigorous "entrance exam" that the predictive world model had to pass before being allowed to guide real motor decisions:

| Gate # | What It Tests | Acceptance Threshold | Achieved Score | Verdict | Plain-English Meaning |
|:---:|:---|:---:|:---:|:---:|:---|
| **Gate 1** | Forward Velocity ($v$) | $R^2 \ge 0.90$ | **$R^2 = 0.9613$** | **PASS ✅** | The world model predicts forward speed with 96% accuracy. |
| **Gate 2** | Yaw Rate ($\omega$) | $R^2 \ge 0.80$ | **$R^2 = 0.8466$** | **PASS ✅** | The world model predicts turning speed with 85% accuracy. |
| **Gate 3** | Sonar Distances | $R^2 \ge 0.50$ | **$R^2 = 0.5377$** | **PASS ✅** | Correctly predicts how distance to walls will change. |
| **Gate 4** | Collision Prediction | $\text{ROC-AUC} \ge 0.90$ | **$\text{ROC-AUC} = 0.995$** | **PASS ✅** | Near-perfect (99.5%) accuracy in predicting imminent crashes. |
| **Gate 5** | 5-Step Rollout Drift | $< 15.0\%$ | **$8.18\%$** | **PASS ✅** | Mental simulations don't hallucinate over 5 steps. |
| **Gate 6** | Causal Intervention | $\Delta > 0.35$ | **$\Delta = 0.442$** | **PASS ✅** | Changing steering commands genuinely changes future predictions. |
| **Gate 7** | Compute Latency | $\le 10.0\text{ ms}$ | **$2.12\text{ ms}$** | **PASS ✅** | Mental simulation runs in just 2.12 ms (well under the 33.3 ms tick budget). |

### Verbatim Viva Script
> *"Table 2 summarizes the Stage 2.2 predictive world model seven-gate certification. The model achieved an R-squared of 0.9613 on forward velocity, an ROC-AUC of 0.995 on collision detection, and multi-step rollout drift bounded at 8.18%. Most importantly, Gate 7 confirmed an inference latency of just 2.12 ms against a 10.0 ms budget, comfortably satisfying all pre-registered criteria with 7 out of 7 passes."*

---

## Slide 30: Predictive World Model Evidence — Counterfactual Branching
- **Slide Title**: *PREDICTIVE WORLD MODEL EVIDENCE: ACTION BRANCHING & FUTURE PREDICTION*
- **Visual Element**: **Plot 8 — Figure 4: Individual Counterfactual Branch Fidelity (20/20 Pass)**

### The "What, Why, When, Where, How" Protocol
- **WHAT is this plot showing?**: A breakdown of **20 distinct counterfactual action rollouts** (imagined paths for different left/right wheel speed combinations). The bars show the $R^2$ accuracy score for each individual action branch compared to what actually happened in the physics engine.
- **WHY did we make this plot?**: To prove the model doesn't suffer from "mode collapse" (where a model always predicts the same average path regardless of what the wheels do).
- **WHEN does this happen?**: During prospective deliberation testing in Stage 2.2.
- **WHERE does the data come from?**: Comparing predicted 5-step state trajectories against unrolled MuJoCo physics states.
- **HOW do you read it?**:
  - The dashed horizontal line marks the strict acceptance threshold ($R^2 \ge 0.50$).
  - Every single one of the 20 branches exceeds this line, achieving a mean $R^2$ of **0.772**.
  - The causal action discrimination margin is **$\Delta \ge +0.30\text{ m}$**, proving that steering left versus steering right produces distinctly separated mental predictions.

### Verbatim Viva Script
> *"Figure 4 on Slide 30 demonstrates individual counterfactual branch fidelity across 20 distinct steering actions. All 20 branches surpass the R-squared 0.50 threshold, with a mean score of 0.772. Furthermore, the causal action discrimination margin exceeds 0.30 meters, confirming that the world model is highly sensitive to control interventions and does not suffer from mode collapse."*

---

## Slide 31: Stage 2.3 Action Deliberation — Reflex vs. Deliberation
- **Slide Title**: *ACTION DELIBERATION MVE BENCHMARK: REFLEX VS DELIBERATION*
- **Visual Element**: **Plots 9 & 10 — Causal Sonar Calibration & Asymmetric Evasion Showdown**

### The "What, Why, When, Where, How" Protocol
- **WHAT are these plots showing?**:
  - Left Plot (Figure 5a): Comparison between prospective sonar predictions and actual observed physical sonar readings.
  - Right Plot (Figure 5b): A head-to-head showdown in a tricky dead-end corner between a **purely reactive reflex agent** (red trace) and the **prospective deliberative CARL** (blue trace).
- **WHY did we make these plots?**: To prove that "thinking ahead" produces fundamentally superior survival behavior compared to simple reactive bumper reflexes.
- **WHEN does this happen?**: During the Stage 2.3 Model-based Value Expansion (MVE) benchmark.
- **WHERE does the data come from?**: Synchronized MuJoCo telemetry in asymmetric dead-end maze environments.
- **HOW do you read it?**:
  - In Figure 5(a), **$97.9\%$** of all prospective sonar predictions fall strictly within the tight $\pm 0.25\text{ m}$ acceptance band, proving minimal simulation drift.
  - In Figure 5(b), watch the paths: The reactive reflex robot drives straight into the dead-end pocket, hits a wall, bounces back, and gets hopelessly trapped. In contrast, the deliberative CARL (blue path) mentally anticipates the wall 0.45 seconds in advance, slows down before entering the pocket, executes a wide arc, and smoothly navigates past the hazard.

### Verbatim Viva Script
> *"Slide 31 provides the definitive proof of deliberation over pure reflex. Figure 5(a) shows that 97.9% of prospective sensory predictions fall within our 0.25 m acceptance band. Figure 5(b) illustrates the real-world consequence: while a reactive reflex agent blindly enters the dead-end corner and gets trapped, deliberative CARL evaluates the future rollout in imagination, rejects the blocked trajectory, and steers smoothly into open space."*
"""

with open(OUT_FILE, "a", encoding="utf-8") as f:
    f.write(phase3_text)

print("Appended Phase 3 (Slides 26-31)")
