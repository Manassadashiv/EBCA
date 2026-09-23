# CARL STAGE 1 — PARAMETER PROVENANCE TAXONOMY
**Classification**: Architectural Governance & Parameter Provenance  
**Date**: September 3, 2026  
**Status**: APPROVED & LOCKED  

---

## Parameter Taxonomy Table

All parameters active in CARL Stage 1 are rigorously classified into exactly one of the four foundational categories:

| Parameter Name | Value | Component | Category | Theoretical & Empirical Provenance |
| :--- | :--- | :--- | :--- | :--- |
| `MAX_BABBLE_AMPLITUDE` | $0.150$ | `carl_stage1_babbler.py` | `[VALIDATION CRITERION]` | Safe exploratory ceiling preventing tipping under maximal opposing step reversals |
| `S_UNIFIED_DIM` | $1061$ | `carl_stage1_organism.py` | `[MATHEMATICAL INVARIANT]` | Exact dimensional sum of sensors ($25$), reservoir ($1026$), endocrine ($4$), and actions ($6$) |
| `N_RESERVOIR` | $1026$ | `carl_stage1_reservoir.py` | `[PHYSIOLOGICAL / PHYSICAL]` | Cortical-scale liquid state machine neuron population with high dimensional expansion ratio ($41\times$) |
| `SPECTRAL_RADIUS` ($\rho$) | $0.98$ | `carl_stage1_reservoir.py` | `[MATHEMATICAL INVARIANT]` | Guarantees Echo State Property (ESP) and edge-of-chaos critical dynamics without divergence |
| `RESERVOIR_SPARSITY` | $0.10$ | `carl_stage1_reservoir.py` | `[PHYSIOLOGICAL / PHYSICAL]` | Biological sparse recurrent connectivity matching mammalian cortical microcircuitry |
| `INTRINSIC_TARGET_ACT` ($\bar{a}$) | $0.15$ | `carl_stage1_reservoir.py` | `[PHYSIOLOGICAL / PHYSICAL]` | Homeostatic intrinsic plasticity set-point regulating mean population firing rate |
| `INTRINSIC_ETA` ($\eta_g$) | $0.001$ | `carl_stage1_reservoir.py` | `[LEARNED / EMERGENCE]` | Continuous online adaptation rate for intrinsic excitability gain $g_t$ |
| `SENSOR_DIM` | $25$ | `carl_stage1_hal.py` | `[PHYSIOLOGICAL / PHYSICAL]` | Hardware physical layout: 15 sonars, 3 accel, 3 gyro, 3 proprio, 1 battery |
| `ACTUATOR_DIM` | $6$ | `carl_stage1_hal.py` | `[PHYSIOLOGICAL / PHYSICAL]` | Physical MuJoCo joints: 2 drive wheels, 2 gaze servos, 1 torso pitch, 1 visor |
| `DISCOVERY_MAX_LAG` ($\tau_{\max}$) | $20\text{ ticks}$ ($0.66\text{s}$) | `carl_stage1_discovery.py` | `[VALIDATION CRITERION]` | Maximum causal physical transmission horizon for motor-to-sensor propagation |
| `SURROGATE_COUNT` ($N_{\text{surr}}$) | $200$ | `carl_stage1_discovery.py` | `[VALIDATION CRITERION]` | Minimum IAAFT trace count providing accurate empirical null mean and variance estimation |
| `FWER_ALPHA` ($\alpha_{\text{FWER}}$) | $0.01$ | `carl_stage1_discovery.py` | `[VALIDATION CRITERION]` | Family-Wise Error Rate statistical threshold controlling false discoveries across 150 channel pairs |
| `CONTROL_TIMESTEP` ($\Delta t$) | $0.03333\text{s}$ ($30\text{ Hz}$) | `carl_stage1_hal.py` | `[PHYSIOLOGICAL / PHYSICAL]` | Embodied sensorimotor loop frequency matching physical robot real-time loop |
| `ROLL_SAFETY_THRESHOLD` | $0.20\text{ rad}$ ($11.46^\circ$) | `run_stage1_experiments.py` | `[VALIDATION CRITERION]` | Maximum allowable dynamic roll before chassis instability/tipping hazard |
| `PITCH_SAFETY_THRESHOLD` | $0.25\text{ rad}$ ($14.32^\circ$) | `run_stage1_experiments.py` | `[VALIDATION CRITERION]` | Maximum allowable dynamic pitch before chassis instability/tipping hazard |
| `DRIVE_PAIR_COUPLING` | $[1, 0]$ | `carl_stage1_discovery.py` | `[LEARNED / EMERGENCE]` | Autonomously discovered bilateral locomotion wheel channels from tabula-rasa mutual information |
| `GAZE_PAIR_COUPLING` | $[2, 3]$ | `carl_stage1_discovery.py` | `[LEARNED / EMERGENCE]` | Autonomously discovered head pan/tilt joint servos from proprioceptive mutual information |
| `TORSO_COUPLING` | $[4]$ | `carl_stage1_discovery.py` | `[LEARNED / EMERGENCE]` | Autonomously discovered torso pitch hinge channel from pitch encoder mutual information |
