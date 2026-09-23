# Stage 2.1A-R — Task Tracker

- [x] Forensic Seed Plumbing & Sensor Tap Audit (Council Report issued: `CARL-COUNCIL-FORENSIC-AUDIT-STAGE2.1A-PLUMBING`)
- [x] Formally reclassify Stage 2.1A as `Stage 2.1A-Baseline (Deterministic Scaffold)`
- [x] Create `carl_stage2_spatial_controller.py`:
  - [x] Unsupervised vestibular discovery ($\rho(u_R - u_L, s_j)$ — zero hardcoded indices)
  - [x] Closed-loop autonomous homing P-controller (*Cataglyphis* path integration)
- [x] Create `test_stage2_1a_r_spatial.py`:
  - [x] Stochastic initial pose perturbations ($x_0, y_0, \theta_0$) + sensor & actuator noise
  - [x] Exp 1: Autonomous wander & closed-loop homing to origin
  - [x] Exp 2: Glaze ice patch crossing with slip gating
  - [x] Exp 3: Dual-blind sensor permutation gyro recovery
- [x] Evaluate Development Seeds `[42, 101, 202]` — 3/3 passed (100%)
- [x] STRICTLY FREEZE ALGORITHM (Zero code or threshold modifications)
- [x] Evaluate Unseen Test Seeds `[303, 404, 505, 606, 707]` — 4/5 passed (80.0%, honest reporting of Seed 404 $+2.1\,\text{mm}$ boundary failure)
- [x] Total Multi-Seed Compliance: 7/8 Passed (87.5%), Exp 1 Homing: 8/8 (100%), Exp 3 Permutation: 8/8 (100%)
- [x] Render Visual Telemetry Package (`figure1_autonomous_homing_trajectories.png`, `figure2_unsupervised_vestibular_discovery.png`, `figure3_ice_gating_drift_rejection.png`, `figure4_stochastic_multiseed_scorecard.png`)
- [x] Render Master 720p 30 FPS Demonstration Video (`carl_stage2_1a_r_spatial_demonstration.mp4`, 5.95 MB)
- [x] Independent Karpathy LLM Council Audit (`CARL_STAGE2_1A_R_INDEPENDENT_COUNCIL_AUDIT.md`)
- [x] Update Master Walkthrough (`walkthrough.md`)
