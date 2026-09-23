# LLM Council Transcript: CARL Stage 2.3 Action Deliberation MVE Certification

**Date:** September 7, 2026 (02:08 IST)  
**Topic:** Formal Scientific Certification of CARL Stage 2.3 MVE & Stage 3 Readiness  
**Governing Skill:** `llm-council` (Karpathy 5-Advisor Multi-Perspective Architecture)  

---

## The Framed Question

> **"Should CARL Stage 2.3 Closed-Loop Action Deliberation MVE be officially accepted as scientifically certified, and is CARL ready to proceed to Stage 3 (Behavioral Discovery / Active Inference)?"**

### Core Context & Audit Findings:
1. **Fresh Empirical Revalidation:** Rerun in physical MuJoCo simulation (`brain/test_stage2_3_mve_runner.py`) across 200 total episodes ($N=50$ trials $\times$ 4 conditions in an asymmetric obstacle trap):
   - **Deliberative (Ours):** 2.0% collision rate (1/50), 59.4/60 ticks survived, p95 latency = 37.73 ms.
   - **Scripted Reflex:** 68.0% collision rate (34/50), 41.8/60 ticks survived.
   - **Amnesic (No Map):** 68.0% collision rate (34/50), 41.8/60 ticks survived.
   - **Random Baseline:** 48.0% collision rate (24/50), 47.7/60 ticks survived.
   - **Statistical Significance:** $p = 6.36 \times 10^{-13}$, Cohen's $d = 1.628$.
   - **Causal Alignment:** 97.9% physical clearance within $\pm 0.25\,\text{m}$ of imagined clearance.
2. **Critical Architectural Constraints:**
   - Evaluated on a known metric grid (`arena_occupancy_grid.pt`), not a drifting open-loop SLAM map.
   - In `test_stage2_3_mve_runner.py:127-131`, current ego-pose $(x, y, \theta)$ is supplied to `select_action` from `hal.data.qpos` at the start of each decision cycle.
   - Evaluates 3 discrete candidate action arcs ($H=10$ ticks / $300\,\text{ms}$).
   - The test domain is an asymmetric corner trap designed to trap naive left-steering reflexes.

---

## Round 1: Independent Advisor Responses

### Advisor 1: The Contrarian
Do not let the "2.0% vs 68.0%" headline blind you. Here is the trap:
Look at lines 127–131 of `test_stage2_3_mve_runner.py`. The test harness feeds ground-truth `qpos` coordinates to the agent at every single decision tick. The robot is not localizing itself in the arena; the simulator is whispering its exact $(x, y, \theta)$ coordinates into its ear before it queries the map.

Furthermore, the test was constructed around a specific asymmetric trap where turning left guarantees hitting a wall. Naive reflex is scripted to turn left, so of course reflex crashes 68% of the time! If the arena had a wall on the right and an opening on the left, that same scripted reflex would have scored 0% collisions. 

Calling this "closed-loop action deliberation certified" without testing noisy localization, dynamic obstacles, or inverted traps is textbook confirmation bias. It is a Minimum Viable Experiment (MVE), yes, but it is fragile. **Do not certify Stage 2.3 as general navigation; certify it ONLY as a proof-of-concept lookahead veto under ideal localization.**

### Advisor 2: The First Principles Thinker
Let us strip away the confusion and ask: *what causal mechanism was Stage 2.3 actually designed to isolate?*

Stage 2.3 was never designed to solve localization or SLAM. That is a perceptual state-estimation problem. Stage 2.3 was designed to answer a single question: **"Can prospective mental unrolls causally alter physical motor selection to avoid hazards before contact?"**

By holding the map (`arena_occupancy_grid.pt`) and pose constant across all four conditions, the experimental design cleanly isolates the exact causal variable under test:
- Strip away lookahead (Reflex) $\to$ 68% crash rate.
- Strip away spatial memory (Amnesic) $\to$ 68% crash rate.
- Add lookahead + spatial memory (Deliberative) $\to$ 2% crash rate.

The fact that the agent receives its current pose does not invalidate the test; in cognitive science and control theory, this is the standard separation between State Estimation (the Kalman filter / CANN) and Policy Deliberation (the forward model). The causal efficacy of prospective imagination is mathematically proven ($p = 6.36 \times 10^{-13}$). **Stage 2.3 achieved its first-principles goal.**

### Advisor 3: The Expansionist
Look at the engineering reality: 37 milliseconds!
A 10-step forward kinematic unroll paired with a 2D bilinear clearance raycaster executing at 27 decisions per second on physical MuJoCo simulation. That is real-time embodied cognition.

Consider what this unlocks for Stage 3 (Behavioral Discovery & Active Inference):
Stage 3 requires an agent that can internally evaluate candidate actions to maximize empowerment and discover affordances. You cannot discover affordances if your forward simulator crashes or takes 20 seconds to think. Stage 2.3 provides the exact real-time forward-simulation engine that Stage 3 needs.

The downstream evidence is conclusive: 97.1% collision reduction, Cohen's $d = 1.628$, and 97.9% causal prediction alignment. Stopping or delaying Stage 3 to build general SLAM right now would be premature optimization. **Certify Stage 2.3 MVE and immediately begin Stage 3.**

### Advisor 4: The Outsider
I have no dog in this fight. Here is what this looks like to an objective external reviewer:

1. You had pre-registered acceptance criteria in `CARL_PROJECT_MASTER_STATE.md`:
   - Collision reduction vs Random $\ge 60\%$ $\to$ **Achieved: 95.8%**
   - Collision reduction vs Reflex $\ge 25\%$ $\to$ **Achieved: 97.1%**
   - Causal alignment $\ge 85\%$ $\to$ **Achieved: 97.9%**
   - Latency $\le 50\,\text{ms}$ $\to$ **Achieved: 37.73 ms**
   - Significance $p < 0.05$ $\to$ **Achieved: $6.36 \times 10^{-13}$**

2. Every single pre-registered metric passed with enormous margins. If a student or research lab sets quantitative acceptance criteria in advance and then surpasses all of them by a factor of three, you cannot move the goalposts after the fact and say "but you didn't solve full SLAM."

3. The only potential pitfall is dishonest marketing. As long as you label it **Stage 2.3 MVE (Minimum Viable Experiment)** and explicitly state in the report that localization was supplied from simulator ground truth, the paper or project report is completely solid. **Accept and certify.**

### Advisor 5: The Executor
Stop agonizing. Here is the operational reality:

Stage 2.3 is an **MVE (Minimum Viable Experiment)**. The letter "M" stands for *Minimum*. It was specifically scoped as an obstacle-trap avoidance test with 3 discrete branches to demonstrate that mental simulation works closed-loop in under 50 ms. It was never scoped as full Stage 4 lifelong navigation.

Here is the operational checklist:
1. Did the test run without simulator crashes? **Yes.**
2. Did the subprocess air-gap hold? **Yes.**
3. Did it beat all 3 controls with $p < 0.001$? **Yes ($p = 6.36 \times 10^{-13}$).**
4. Does the scorecard reflect genuine physical MuJoCo steps? **Yes (200 episodes).**

Trying to fix odometry drift or build continuous spline trajectory optimization right now is scope creep that will derail the timeline. 
**Verdict: CERTIFY Stage 2.3 MVE immediately. Mark Stage 2 closed. Unblock Stage 3.**

---

## Round 2: Peer Review (Anonymized)

- **Reviewer 1 (The Contrarian):** Response B (First Principles) and D (Outsider) make a fair point: the pre-registered criteria were indeed met, and decoupling state estimation from deliberation is legitimate. However, Response C (Expansionist) is overeager—Stage 3 active inference will fail if the agent's spatial map drifts. The handoff between Stage 2 and Stage 3 must include clear guardrails.
- **Reviewer 2 (The First Principles Thinker):** Response A (Contrarian) correctly caught the `qpos` pose injection in lines 127–131. That must be stated clearly in the documentation so the project retains scientific credibility. But Response E (Executor) is right: moving the goalposts beyond the MVE specification is bad engineering.
- **Reviewer 3 (The Expansionist):** Response D (Outsider) provides the cleanest framing: passing pre-registered criteria is a pass, full stop. The Contrarian's concerns can be addressed simply by honest scoping, not by blocking progress.
- **Reviewer 4 (The Outsider):** All five advisors agree on the empirical facts: the benchmark genuinely passed. The only disagreement is semantic: does "deliberation" imply autonomous localization? No, deliberation implies action selection under a model.
- **Reviewer 5 (The Executor):** Unanimous consensus that the code executed cleanly and the numbers are real. The one blind spot caught by the Contrarian (`qpos` ego-pose injection) is easily resolved by adding an explicit scope note to the milestone report.

---

## Round 3: Chairman Synthesis & Final Verdict

### Council Verdict: Stage 2.3 Action Deliberation MVE Certification

#### Where the Council Agrees:
1. **The empirical benchmark passed decisively:** All 5 pre-registered acceptance criteria in `CARL_PROJECT_MASTER_STATE.md` were exceeded across 200 real physical simulation episodes ($p = 6.36 \times 10^{-13}$, latency $37.7\,\text{ms} \le 50\,\text{ms}$, 97.1% collision reduction).
2. **The causal mechanism is real:** When lookahead is removed (Reflex) or spatial memory is erased (Amnesic), the agent crashes 68% of the time. When lookahead and spatial memory are active (Deliberative), it avoids the trap 98% of the time.
3. **The computational performance is genuine:** 10-step forward unrolls plus bilinear clearance raycasting execute in 37.7 ms, proving that embodied mental simulation is feasible within real-time robotics budgets.

#### Where the Council Clashes:
- **The Contrarian vs. The Expansionist/Executor:** The Contrarian argued that feeding ground-truth `qpos` coordinates to the deliberator at the start of each step and testing on a single corner trap makes the 2.0% score artificially flattering. The First Principles Thinker and Outsider countered that isolating deliberation from state estimation is standard scientific decoupling, and moving goalposts beyond pre-registered criteria undermines scientific process.

#### Blind Spots the Council Caught:
- In `test_stage2_3_mve_runner.py:127-131`, the test harness supplies `curr_x, curr_y, curr_th` from simulator ground truth. If someone reads the report without this context, they might assume CARL has solved full autonomous SLAM and localization. This distinction must be explicitly documented.

#### The Recommendation:
**OFFICIALLY CERTIFY STAGE 2.3 MVE WITH EXPLICIT BOUNDARY DISCLOSURE.**
- Stage 2.3 has achieved full empirical closure against its pre-registered scientific criteria.
- It must be formally classified as:
  > **"A real-time closed-loop prospective action deliberation engine over known spatial memory under ideal localization."**
- It must NOT be claimed as "general autonomous SLAM or unassisted open-world navigation."
- With this classification, **Stage 2 is officially complete and Stage 3 is UNBLOCKED.**

#### The One Thing to Do First:
Document the exact localization boundary in `evidence/stage2_3/CARL_STAGE2_3_MVE_REPORT.md`, update the canonical ledger in `CARL_PROJECT_MASTER_STATE.md`, and transition to Stage 3 planning.
