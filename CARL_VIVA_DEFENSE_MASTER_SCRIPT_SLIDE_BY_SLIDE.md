# CARL-DX Definitive Slide-by-Slide Viva Defense Script
## JNTUH Department of Mechanical Engineering (IDP AMS)
**Candidate:** Manas Sadashiv (Roll: 22011P0310)  
**Title:** DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS  
**Presentation Deck:** `310_stage3.3_scope.pptx` (35 Slides)  
**Target Delivery Duration:** 12 - 14 Minutes (~20-30 seconds per slide, 40-45 seconds on key data slides)

---

## Slide 1: Title & Candidacy
* **Visuals:** Project Title, Institutional Affiliation (JNTUH UCESTH, Department of Mechanical Engineering, IDP AMS), Candidate Details.
* **Key Terms:** IDP AMS (Advanced Manufacturing Systems), 30 Hz Digital Twin.
* **What to Say (Spoken Script - 25s):**
  > "Respected Chairman, external examiner, and members of the faculty: Good morning. I am Manas Sadashiv, Roll Number 22011P0310, pursuing the Integrated Dual Degree in Mechanical Engineering with specialization in Advanced Manufacturing Systems. 
  > Today, I present my mini-project titled: 'Design and Development of a Digital Twin Framework for Biologically Inspired Cognitive Robotic Systems'. 
  > This project bridges contact mechanics, real-time physics simulation, and neuromorphic computational principles to build robust autonomous navigation for mobile robotic systems."
* **Examiner Defense Trap:**
  * *Q: Why is AI/Cognitive robotics being done in a Mechanical Engineering AMS department?*
  * *A:* "Sir, in Industry 4.0 and smart flexible manufacturing, Autonomous Mobile Robots (AMRs) and AGVs must transport payloads across dynamic shop floors with varying floor friction, oil spills, and tight warehouse aisles. Traditional robots fail due to rigid assumptions about wheel traction and kinematics. This project solves autonomous navigation from the ground up—starting with physical contact mechanics and slip estimation before planning."

---

## Slide 2: Abstract
* **Visuals:** Structured abstract covering problem statement, methodology, 3-stage validation, and empirical metrics.
* **Key Numbers & Metrics:** 
  * 30 Hz real-time control loop (33.3 ms cycle budget)
  * Friction regimes mu in [0.05, 1.0]
  * 2,114-unit Continuous Attractor Neural Network (CANN)
  * 0.062 m homing drift
  * Predictive World Model forward velocity R-squared = 0.96
  * MPPI continuous trajectory optimization at 1.36 ms latency (p95 = 2.14 ms)
  * 100% clean AST anti-cheat quarantine
* **What to Say (Spoken Script - 35s):**
  > "This slide summarizes the core problem and our contributions. Traditional autonomous robots isolate perception, mapping, and trajectory control into fragmented software silos, leading to brittle integration and catastrophic failure when wheel traction changes.
  > We develop CARL, an embodied cognitive architecture operating inside a real-time 30 Hz MuJoCo physics digital twin. 
  > Across three stages, we demonstrate: first, unsupervised movement exploration and slip estimation across friction regimes from 0.05 to 1.0; second, a 2,114-unit neural attractor network achieving sensor-only tracking with only 6.2 centimeters of homing drift and an R-squared of 0.96 in forward dynamic prediction; and third, continuous Model Predictive Path Integral control executing in just 1.36 milliseconds under a 100% clean AST anti-cheat quarantine."
* **Examiner Defense Trap:**
  * *Q: What does the 100% clean AST anti-cheat mean?*
  * *A:* "Sir, it proves through automated Abstract Syntax Tree static analysis that our decision loop uses zero simulator cheat variables—no ground-truth simulator positions (qpos) or velocities (qvel). The robot navigates strictly on unprivileged sensors, exactly as it must on physical hardware."

---

## Slide 3: Introduction
* **Visuals:** Conceptual comparison between classical robotics pipelines and biological multi-scale feedback loops.
* **Key Numbers & Terms:** Liquid State Machine (LSM) reservoir, 4-factor endocrine kinetics (Dopamine, Serotonin, Norepinephrine, Acetylcholine), Continuous Attractor Neural Networks (CANN).
* **What to Say (Spoken Script - 25s):**
  > "Autonomous robotics requires adaptive behaviour in unstructured, noisy physical environments. Classical robotics relies on rigid if-else state machines and decoupled ROS stacks, where a 5% sensor error compounds into a crash.
  > In contrast, biological organisms maintain extraordinary robustness through tightly coupled bodily, chemical, and neural feedback loops. 
  > CARL replicates these principles through three developmental stages: physical sensorimotor grounding, continuous attractor spatial memory, and sampling-based predictive trajectory optimization."
* **Examiner Defense Trap:**
  * *Q: Why do you need simulated 'hormones' like Dopamine and Norepinephrine?*
  * *A:* "Sir, instead of brittle if/else thresholds, endocrine kinetics provide continuous global gain control: Dopamine drives goal-seeking speed, while Norepinephrine acts as a physical stress signal, spiking during wheel slip or obstacles to lower velocity and increase caution."

---

## Slides 4, 5, 6: Literature Review (Modules 1, 2, 3)
* **Visuals:** Tables mapping 6 seminal papers to their methodology, findings, and direct role in CARL.
* **Key Papers Cited:**
  * Mazumder et al. (2023) & Makoviychuk et al. (2021) — Digital Twin foundations and GPU physics simulation.
  * Hasani et al. (2021) & Baldini (2022) — Liquid time-constant networks and reservoir computing in robotics.
  * Juarez-Lora et al. (2022) & Liu & Pan (2023) — Spiking neural networks and R-STDP under changing friction.
* **What to Say (Spoken Script - 30s):**
  > "Our literature review spans three foundational modules: 
  > In Embodiment and Physics Simulation, Mazumder and Makoviychuk establish that high-fidelity digital twins with accurate contact dynamics are essential before physical deployment. 
  > In Neural Dynamics, Hasani and Baldini demonstrate that recurrent reservoir and liquid time-constant networks can process temporal dynamics efficiently in real time. 
  > In Adaptive Control, Juarez-Lora proves that spike-timing plasticity can adapt motor control under changing friction. We build directly upon these foundations."
* **Examiner Defense Trap:**
  * *Q: Which physics engine did Makoviychuk develop?*
  * *A:* "Isaac Gym on GPU, sir. We utilized MuJoCo for CARL because MuJoCo provides the world standard for convex contact dynamics, slip friction cones, and constraint-based physical integration."

---

## Slide 7: Literature Summary
* **Visuals:** Bulleted synthesis of simulation, reservoir dynamics, neuromodulation, grid cells, MPPI, and active inference.
* **What to Say (Spoken Script - 20s):**
  > "To summarize the literature: physics-grounded digital twins, continuous attractor networks, and sampling-based trajectory optimization (like MPPI) have all demonstrated strong individual capabilities in literature. 
  > However, past studies investigate these mechanisms independently rather than as one progressively validated, unified embodied organism."

---

## Slide 8: Research Gap
* **Visuals:** 4 explicit research gaps highlighting literature fragmentation.
* **What to Say (Spoken Script - 25s):**
  > "This brings us directly to our Research Gap:
  > First, no existing architecture combines continuous neuromorphic spatial attractors with sampling-based MPPI trajectory optimization inside one real-time embodied control loop.
  > Second, past neural controllers do not couple endocrine-modulated stress kinetics with physical wheel-slip observers.
  > And third, no prior work has subjected a biologically inspired robot to rigorous, fail-closed causal ablation testing within a digital twin."
* **Examiner Defense Trap:**
  * *Q: In one sentence, what is the single biggest gap?*
  * *A:* "The total lack of a unified, real-time 30 Hz architecture that connects neuromorphic spatial memory with forward sampling trajectory optimization under physical contact mechanics."

---

## Slide 9: Problem Statement & Objectives
* **Visuals:** Formal problem formulation and project objective.
* **What to Say (Spoken Script - 25s):**
  > "Our Problem Statement addresses the fragile integration of fragmented perception, navigation, and control modules under changing mechanical conditions.
  > Our Objective is to design, develop, and progressively validate CARL—a physics-grounded cognitive robotic architecture that replaces rigid reactive reflexes with continuous forward trajectory planning within a 30 Hz MuJoCo digital twin."

---

## Slide 10: Digital Twin / System Architecture
* **Visuals:** Two-phase execution block diagram: Phase 1 (Boot & Init) and Phase 2 (30 Hz Closed Loop: Steps A through K).
* **Key Terms:** vessel_kinetic.xml, S_unified zero-copy memory array, 30 Hz tick iteration.
* **What to Say (Spoken Script - 30s):**
  > "Slide 10 details our System Architecture. 
  > In Phase 1, we boot the system by loading the MuJoCo robot model, allocating a zero-copy shared memory buffer, and initializing neural weights.
  > In Phase 2, the system runs at 30 Hz through 11 sequential steps: acquiring raw sonar and wheel encoder telemetry, updating endocrine chemical kinetics, executing obstacle reflexes, running the cognitive trajectory optimizer, and outputting motor commands to the differential drive actuators—all strictly within our 33.3 ms cycle budget."

---

## Slide 11: Complete Control Loop & Endocrine Pathways
* **Visuals:** Signal flow diagram highlighting raw sensor inputs, endocrine modulation pathways, SNN reflex overrides, and motor command mixing.
* **What to Say (Spoken Script - 25s):**
  > "Slide 11 illustrates the operational signal flow. Notice the multi-tier safety architecture:
  > In normal conditions, the cognitive path plans optimal paths. 
  > However, if distance drops dangerously low, the fast Spiking Neural Reflex can immediately override cognition to execute an emergency brake or turn. 
  > Simultaneously, the Endocrine system dynamically tunes noise scales and motor gain based on stress and battery level."

---

## Slide 12: CARL Developmental Roadmap (Stages 1 - 3)
* **Visuals:** Chronological milestone roadmap: Stage 1 ('Learn My Body'), Stage 2 ('Learn My World'), Stage 3 ('Learn How to Behave').
* **Key Milestones:**
  * Stage 1: Motor babbling, 1-step momentum, slip estimation across mu in [0.05, 1.0].
  * Stage 2: 2,114-unit CANN (drift 0.062 m), 7-Gate world model (R-squared = 0.96), 40/40 mazes cleared.
  * Stage 3: Anti-cheat quarantine, CANN causal ablation, narrow corridor stress test, MPPI continuous synthesis (1.36 ms, +18.7% clearance).
* **What to Say (Spoken Script - 35s):**
  > "We developed CARL across three strict, sequential developmental stages:
  > Stage 1 ('Learn My Body') grounds physical locomotion, stability, and contact slip.
  > Stage 2 ('Learn My World') builds internal spatial representation using a 2,114-unit continuous attractor network and a 7-gate predictive world model.
  > Stage 3 ('Learn How to Behave') conducts rigorous causal ablation testing and deploys Model Predictive Path Integral continuous control to solve narrow corridor navigation. We will now examine each stage's empirical evidence."

---

## Slide 13: Stage 1 — Sensorimotor Grounding & Movement Exploration
* **Visuals:** Structural summary of Stage 1 embodied components (MuJoCo digital twin, 30 Hz loop, friction observer, fail-closed scoring).
* **What to Say (Spoken Script - 20s):**
  > "Stage 1 establishes the physical foundation: the robot starts with zero prior knowledge of its wheel kinematics and learns how its motors translate into physical motion in contact-rich MuJoCo physics."

---

## Slide 14: Stage 1 Live Demonstration (Video)
* **Visuals:** Embedded video CARL_P0_SEMINAR_DEMO_FINAL.mp4 showing autonomous goal-seeking and obstacle evasion.
* **What to Say (Spoken Script - 30s):**
  > "This video demonstrates the Stage 1 baseline organism in action within the MuJoCo digital twin. 
  > The robot autonomously explores the environment, detects boundary walls using its 12-channel sonar array, smoothly tracks toward goal beacons, and recovers without human intervention or tipping over."

---

## Slide 15: Stage 1 Validation Evidence (Figure 1)
* **Visuals:** Figure 1: Goal-Directed Navigation Trajectories Under Environmental Constraint.
* **What to Say (Spoken Script - 20s):**
  > "Figure 1 shows the recorded trajectory paths across multiple environmental configurations. Even under obstacle clutter and boundary constraints, the robot consistently navigates from start coordinates to target beacons with smooth, repeatable trajectories."

---

## Slide 16: Stage 1.1 Stability Envelopes (Figure 2a)
* **Visuals:** Figure 2(a): 10,000-Tick Dynamical Stability Phase Layout.
* **Key Numbers & Metrics:** 
  * Linear velocity swept from 0.1 to 0.5 m/s
  * Angular velocity swept from 0.2 to 1.5 rad/s
  * 150 trials conducted
  * Exactly ZERO chassis tip-overs or simulation divergences observed
* **What to Say (Spoken Script - 30s):**
  > "In Figure 2(a), we rigorously mapped the dynamical stability envelope. 
  > We systematically swept forward speeds from 0.1 to 0.5 meters per second and turning rates up to 1.5 radians per second across 150 experimental trials. 
  > Across all 150 trials, exactly zero chassis tip-overs and zero simulation divergences occurred, proving the robot's physical center of gravity and suspension geometry are stable."

---

## Slide 17: Stage 1.1 Steering-to-Motion Response Map (Figure 2b)
* **Visuals:** Figure 2(b): Empirical Steering-to-Motion Response Map.
* **Key Numbers & Metrics:** Critical friction boundary identified at mu = 0.35, where longitudinal slip exceeds 40%.
* **What to Say (Spoken Script - 25s):**
  > "Figure 2(b) shows the empirical response mapping from wheel steering input to physical chassis displacement. 
  > Crucially, our unsupervised parameter sweep identified a critical friction boundary at mu = 0.35. Above 0.35, steering is linear; below 0.35, wheel slip exceeds 40%, demanding adaptive spatial tracking."

---

## Slide 18: Stage 1.1 Friction Gradient Sweep (Figure 3)
* **Visuals:** Figure 3: Friction Gradient Response and Slip Monotonicity.
* **Key Numbers & Metrics:** 
  * Low friction (mu = 0.05): longitudinal slip reaches 98.2% (wheels spin, chassis halts)
  * High friction (mu = 0.50 to 1.0): slip stabilizes at 24.1%
* **What to Say (Spoken Script - 30s):**
  > "Figure 3 illustrates longitudinal slip across a continuous friction gradient from 0.05 to 1.0. 
  > On wet ice at mu = 0.05, wheel slip reaches 98.2%—the wheels spin but forward progress stops. 
  > On dry surfaces above mu = 0.5, slip stabilizes at 24.1%. 
  > This experiment physically proves why simple dead reckoning fails in robotics: wheel encoders alone drift catastrophically when traction is lost, proving that neural head-direction tracking is mandatory."

---

## Slide 19: Stage 2 — Generative World & Self Modeling Overview
* **Visuals:** Overview of Stage 2 capabilities (Continuous Attractor spatial tracking, 7-Gate predictive world model, deliberation vs reflex).
* **What to Say (Spoken Script - 20s):**
  > "Having grounded physical locomotion in Stage 1, Stage 2 transitions CARL from reactive movement to forward-predictive planning by constructing an internal self-model and continuous attractor spatial memory."

---

## Slide 20: Stage 2.1 Continuous Attractor Dynamics (Position Tracking)
* **Visuals:** Multi-seed tracking comparison: Physical Reality vs Internal CANN Self Model.
* **Key Numbers & Metrics:** 
  * Development Seed 101: final homing drift = 0.0650 m
  * Unseen Seed 505: final homing drift = 0.0570 m (target gate < 0.22 m)
* **What to Say (Spoken Script - 25s):**
  > "Slide 20 compares physical ground-truth position against CARL's internal CANN estimate. 
  > Across both seen development seeds and completely unseen validation seeds, the final homing drift remained between 5.7 and 6.5 centimeters—well below our pre-registered acceptance gate of 22 centimeters—operating strictly on sensor data without simulator cheats."

---

## Slide 21: Stage 2.1 Continuous Attractor Heading Dynamics
* **Visuals:** 1D CANN Ring Attractor architecture, 5-seed homing error scorecard, Blackout Resilience dynamics.
* **Key Numbers & Metrics:** 
  * 1D CANN with periodic boundary, 64 head-direction neurons
  * Mean homing error across 5 seeds: 0.065 m, 0.071 m, 0.062 m, 0.059 m, 0.057 m (Overall Mean = 0.062 m)
  * Blackout Resilience: directional drift < 0.02 rad/s during complete sensor dropouts
* **What to Say (Spoken Script - 35s):**
  > "Slide 21 details our 1D Continuous Attractor Neural Network. 
  > Using recurrent local excitation and global inhibition (a Mexican-hat connectivity pattern), 64 neurons maintain a sharp, stable activity bump representing heading across 360 degrees. 
  > Across 5 randomized seeds, mean homing error averaged just 6.2 centimeters. 
  > Furthermore, during simulated sensor dropouts, the recurrent connections sustain the bump in place, keeping angular drift below 0.02 radians per second."
* **Examiner Defense Trap:**
  * *Q: Why did you use CANN instead of an Extended Kalman Filter (EKF)?*
  * *A:* "Sir, an EKF relies on linearized Gaussian noise assumptions that break down during severe wheel slip or abrupt sensor outages. CANN provides a biologically grounded, non-linear attractor manifold whose recurrent dynamics hold the orientation state even during complete sensory blackouts."

---

## Slide 22: Stage 2.2 Predictive World Model (Table 1: 7-Gate Validation)
* **Visuals:** Table 1: Complete 7-Gate Validation Results.
* **Key Numbers & Metrics:**
  * Gate 1 (Forward Velocity v): R-squared >= 0.90 -> Achieved R-squared = 0.9613 (PASS)
  * Gate 2 (Angular Rate omega): R-squared >= 0.80 -> Achieved R-squared = 0.8466 (PASS)
  * Gate 3 (Virtual Sonar Rays): R-squared >= 0.50 -> Achieved R-squared = 0.5377 (PASS)
  * Gate 4 (Collision Prediction): ROC AUC >= 0.90 -> Achieved ROC AUC = 0.995 (PASS)
  * Gate 5 (Multi-Step Stability): 5-Step Drift < 15.0% -> Achieved 8.18% (PASS)
  * Gate 6 (Causal Sensitivity): Delta >= 0.35 -> Achieved Delta = 0.442 (PASS)
  * Gate 7 (Compute Latency): Inference <= 10.0 ms -> Achieved 2.12 ms (PASS)
* **What to Say (Spoken Script - 40s):**
  > "Table 1 represents our most rigorous evaluation in Stage 2: a pre-registered Seven-Gate validation of our decoupled predictive world model. 
  > All seven gates passed with zero exceptions:
  > Forward velocity prediction achieved an R-squared of 0.9613 against a 0.90 threshold;
  > Imminent collision prediction achieved an extraordinary ROC AUC of 0.995;
  > Five-step forward rollout drift was held to 8.18%, well below the 15% limit;
  > And total inference cycle latency was just 2.12 milliseconds against our 10-millisecond gate. 
  > This proves the world model accurately predicts physical consequences in real time."

---

## Slide 23: Stage 2.2 Predictive World Model Evidence (Figure 4)
* **Visuals:** Figure 4: Individual Counterfactual Branch Fidelity (20/20 Pass Bar Chart).
* **Key Numbers & Metrics:** 
  * 20 distinct counterfactual action branches evaluated
  * 20/20 branches exceed R-squared >= 0.50 threshold
  * Mean R-squared across all 20 branches = 0.781
  * Causal discrimination margin > +0.30 m
* **What to Say (Spoken Script - 30s):**
  > "Figure 4 verifies the predictive fidelity across 20 distinct counterfactual motor rollouts. 
  > Every single branch exceeds our strict R-squared threshold of 0.50, achieving an overall mean R-squared of 0.781. 
  > Furthermore, the causal discrimination margin exceeded 0.30 meters, confirming that different motor commands produce distinct mental rollouts and the model does not suffer from mode collapse."

---

## Slide 24: Stage 2.3 Action Deliberation vs Reflex Showdown (Figures 5a & 5b)
* **Visuals:** 
  * Figure 5(a): Causal Prediction Alignment (97.9% within 0.25 m acceptance band).
  * Figure 5(b): Asymmetric Evasion: Reactive Reflex vs Prospective Deliberation.
* **What to Say (Spoken Script - 35s):**
  > "Slide 24 demonstrates why forward deliberation is superior to reactive control:
  > Figure 5(a) shows calibration: 97.9% of predicted sonar distances match physical observations within 0.25 meters, proving predictions do not suffer hallucinatory drift.
  > Figure 5(b) illustrates our asymmetric showdown: a reactive reflex only looks 1 step ahead; seeing clear space immediately in front, it charges into a dead-end corridor and gets trapped. 
  > CARL's deliberative engine simulates 5 steps into the future, anticipates the dead-end wall, and turns away before ever entering!"

---

## Slide 25: Stage 3 — Causal Verification & Continuous Action Synthesis Overview
* **Visuals:** Summary of Stage 3 capabilities (CANN causal ablation, trajectory fidelity, corridor stress testing, continuous MPPI, zero-leak governance).
* **What to Say (Spoken Script - 25s):**
  > "Stage 3 represents our final developmental phase: 'Learn How to Behave'. 
  > Here, we conduct formal causal ablation experiments to prove our neural network actually controls actions, evaluate discrete steering limitations in narrow corridors, and synthesize continuous trajectories using Model Predictive Path Integral control."

---

## Slide 26: Stage 3.1 CANN Causal Ablation (Figures 6a & 6b)
* **Visuals:** 
  * Figure 6(a): Action Divergence across Ablation Arms.
  * Figure 6(b): Collision Rates across Intact vs Ablated Conditions.
* **Key Numbers & Metrics:** 
  * Action divergence: Zeroed CANN delta u = 0.563, Shuffled CANN delta u = 0.582 (p < 10^-16)
  * Collision rate: Intact Baseline = 4.0%
  * Zeroed CANN = 31.0% (7.75x worse)
  * Shuffled CANN = 25.0% (6.25x worse)
* **What to Say (Spoken Script - 35s):**
  > "A common criticism of neural robotics is: 'How do you know the neural network is actually driving the robot rather than acting as decorative code?'
  > Slide 26 answers this definitively through a 4-arm causal ablation battery:
  > When we Zeroed the 2,114-unit network, motor actions diverged significantly by 0.563 m/s, and collision rates exploded from 4% up to 31%—over 7.7 times worse!
  > When we Shuffled the neurons, collisions reached 25%—over 6.2 times worse. 
  > With a Wilcoxon p-value below 10^-16, this proves the CANN network is causally necessary for collision avoidance."

---

## Slide 27: Stage 3.2 Non-Line-of-Sight Corridor Evaluation (Figure 8)
* **Visuals:** Figure 8: Task Family Success Rate Across Experimental Arms.
* **Key Numbers & Metrics:** 
  * Evaluated across 100 matched pairs in narrow 0.65 m corridors
  * Success rates: Intact = 11%, Amnesic = 16%, Scrambled = 11%, Potential Field = 4%, Reflex = 14%
  * Both arms failed in 84 out of 100 pairs
  * Exact McNemar test p = 1.000 (difference between 11% and 16% is pure statistical noise)
  * Discrete steering bottleneck in 0.65 m corridors directly motivated Stage 3.3 MPPI
* **What to Say (Spoken Script - 40s):**
  > "Slide 27 presents our corridor stress-test across five non-line-of-sight task families in narrow 0.65-meter corridors. 
  > Here, all arms scored low—between 4% and 16%. In 84 out of 100 matched pairs, both Intact and Amnesic arms failed due to corridor wall trapping. With a McNemar p-value of 1.000, the difference between 11% and 16% is statistical noise.
  > This experiment revealed a critical engineering finding: the robot was restricted to a discrete 7-action turning palette. In tight 0.65 m corridors, jerky discrete turns caused wall-clipping and timeouts. 
  > Rather than papering over this, our system Failed Closed. This empirical limit was our direct motivation for Stage 3.3: replacing discrete turns with smooth, continuous MPPI trajectory optimization."
* **Examiner Defense Trap:**
  * *Q: Why did Amnesic get 16% while Intact got 11%? Did memory hurt?*
  * *A:* "Sir, the McNemar test explicitly showed p = 1.000, with 84 out of 100 pairs failing in both arms. The 5-run difference is pure statistical noise. The benchmark suffered from a floor effect because neither arm could steer smoothly with discrete actions. That failure directly motivated our continuous MPPI controller."

---

## Slide 28: Stage 3.3 MPPI Continuous Trajectory Certification (Table 2)
* **Visuals:** Table 2: Stage 3.3 MPPI Trajectory Synthesis 5-Gate Acceptance Battery.
* **Key Numbers & Metrics:**
  * Gate 1 (Action Smoothness): Mean delta u <= 0.35 -> Achieved 0.060 (PASS)
  * Gate 2 (Cycle Latency): Mean <= 20 ms, p95 <= 45 ms -> Achieved Mean 1.36 ms, p95 2.14 ms (PASS)
  * Gate 3 (Collision Reduction): >= 50% vs Discrete Stage 2 -> Achieved 50.0% reduction (15.0% down to 7.5%) (PASS)
  * Gate 4 (CANN Multi-Objective): Spearman rho >= 0.30 -> Achieved rho = 0.34 (PASS)
  * Gate 5 (AST Anti-Cheat Scan): 100% clean isolation scan -> Achieved 100% Clean / 0 Leaks (PASS)
* **What to Say (Spoken Script - 40s):**
  > "Table 2 presents the certified 5-Gate acceptance battery for Stage 3.3 MPPI control:
  > Gate 1 verifies Action Smoothness: consecutive delta-u was held to 0.060, eliminating actuator chatter;
  > Gate 2 confirms Real-Time Latency: mean cycle latency was just 1.36 milliseconds (p95 = 2.14 ms), consuming only 6.4% of our 33.3 ms budget;
  > Gate 3 demonstrates Collision Reduction: collisions were cut in half—dropping from 15.0% down to 7.5%;
  > Gate 4 confirms CANN multi-objective correlation at rho = 0.34;
  > And Gate 5 confirms a 100% clean AST anti-cheat scan with zero ground-truth leaks. All 5 gates passed certification."

---

## Slide 29: Stage 3.3 MPPI Trajectory Proof & Corridor Escape (Figures 9a & 9b)
* **Visuals:** 
  * Figure 9(a): Continuous MPPI Trajectory Rollout & Heading Reversal.
  * Figure 9(b): Autonomous Corridor Escape & Target Acquisition.
  * Empirical Performance Scorecard box.
* **Key Numbers & Metrics:** 
  * M = 128 rollouts over 15-step horizon (0.45 s) at 30 Hz
  * Mean latency 1.36 ms (p95 = 2.14 ms)
  * Action smoothness delta u = 0.060
  * +18.7% physical clearance margin gain over discrete baseline
  * 0.00% collisions during complex corridor reversal demo
* **What to Say (Spoken Script - 35s):**
  > "Slide 29 demonstrates the physical power of MPPI continuous control:
  > In Figure 9(a), the optimizer evaluates 128 continuous candidate curves across a 15-step horizon (0.45 seconds) in just 1.36 ms.
  > Instead of getting wedged against the wall, Figure 9(b) shows the robot executing a smooth, continuous heading reversal, maintaining an 18.7% wider hull clearance margin, and escaping the cul-de-sac with 0.00% collisions. 
  > This solves the exact narrow corridor failure seen in Stage 3.2!"

---

## Slide 30: Conclusion
* **Visuals:** Structured summary bullets for Stage 1, Stage 2, and Stage 3.
* **Key Numbers Summary:** 
  * Stage 1: 150 trials, 0 tip-overs, mu in [0.05, 1.0].
  * Stage 2: 2,114-unit CANN, 0.062 m homing drift, R-squared = 0.9613, 40/40 mazes cleared.
  * Stage 3: Causal ablation p < 10^-16, MPPI 1.36 ms latency, +18.7% clearance, 100% clean AST quarantine.
* **What to Say (Spoken Script - 35s):**
  > "To conclude: this work developed and validated CARL inside a real-time 30 Hz MuJoCo digital twin:
  > Stage 1 grounded sensorimotor stability across 150 trials without tip-overs and mapped friction regimes;
  > Stage 2 built a 2,114-unit neural attractor achieving 6.2 cm homing drift and a 7-gate predictive world model with an R-squared of 0.96;
  > Stage 3 proved neural causal necessity (p < 10^-16) and deployed continuous MPPI optimization, reducing collisions by 50% and expanding clearance by 18.7% under complete AST anti-cheat quarantine. 
  > CARL successfully bridges contact mechanics with cognitive predictive planning."

---

## Slide 31: Limitations
* **Visuals:** 4 explicit engineering limitations.
* **Key Limitations:** 
  * Simulation-to-reality gap (sensor noise, floor irregularities)
  * Flat 2D ground navigation (planar assumption, no chassis roll/pitch or stairs)
  * Residual collisions under MPPI (7.5% residual collisions in dense clutter)
  * Sensor modality boundary (RGB camera stream not yet coupled directly to steering)
* **What to Say (Spoken Script - 30s):**
  > "In the interest of scientific rigor, we acknowledge four limitations:
  > First, validation was performed in MuJoCo; physical hardware introduces acoustic transducer noise and surface irregularities.
  > Second, kinematics are currently planar 2D, without modeling 3D pitch, roll, or multi-elevation steps.
  > Third, while MPPI halved collisions, a 7.5% residual collision rate remains in tight clutter.
  > Fourth, steering currently relies on ultrasonic sonars and odometry; the onboard RGB camera feed is not yet closed into the steering loop."

---

## Slide 32: Scope for Future Work
* **Visuals:** 4 actionable future research avenues.
* **Key Items:** Embedded edge hardware (Jetson Orin Nano / Orange Pi 5, 15W budget), VL53L1X ToF sensors + MPU-6050 IMU, CNN vision navigation, lifelong associative memory.
* **What to Say (Spoken Script - 30s):**
  > "Our scope for future work includes:
  > Deploying the architecture onto embedded edge hardware—specifically an NVIDIA Jetson Orin Nano or Orange Pi 5 within a 15-Watt power budget;
  > Integrating physical Time-of-Flight sensors and a 6-axis MEMS IMU over SPI/I2C buses;
  > Ingesting the RGB camera stream through a lightweight CNN for visual landmark recognition;
  > And integrating continuous learning with associative memory so navigation layouts persist across recharge cycles."

---

## Slides 33 & 34: References
* **Visuals:** 16 peer-reviewed academic references (IEEE, Science Robotics, Nature, Neural Networks).
* **What to Say (Spoken Script - 10s):**
  > "Slides 33 and 34 list our 16 primary academic references spanning digital twins, reservoir computing, continuous attractor dynamics, and MPPI trajectory control."

---

## Slide 35: Thank You & Q&A
* **Visuals:** Closing slide, Candidate Details.
* **What to Say (Spoken Script - 10s):**
  > "Thank you for your time and consideration. I am now open to your questions and feedback."
