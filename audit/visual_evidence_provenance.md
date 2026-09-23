# CARL-DX Visual Evidence Provenance Forensic Report

**Audit Subject**: Lineage, Simulation Duration, RNG Seeds, and Data Source Classification for all PNGs and MP4s  
**Audit Date**: August 16, 2026  
**Status**: **`VERIFIED_AND_CATALOGED`**  
**JSON Evidence**: [`audit/visual_evidence_provenance.json`](file:///D:/ebca/audit/visual_evidence_provenance.json)  

---

## 1. Visual Evidence in `evidence/final_blind_organism_test/`

All 12 visual evidence plots and the primary video originate directly from the 120-tick unbroken unscripted blind life run:

| Artifact File | Artifact Type | Exact Source Data | Simulation Ticks | Seed | Final Run Provenance |
| :--- | :---: | :--- | :---: | :---: | :---: |
| [`complete_blind_run.mp4`](file:///D:/ebca/evidence/final_blind_organism_test/complete_blind_run.mp4) | MP4 Video | Real MuJoCo Offscreen Rendering | 120 ($4.0\text{s}$) | `20260816` | **100% Final Blind Run** |
| [`trajectory/trajectory_2d.png`](file:///D:/ebca/evidence/final_blind_organism_test/trajectory/trajectory_2d.png) | PNG Plot | `blind_life_run_telemetry.csv` ($x, y, \psi$) | 120 | `20260816` | **100% Final Blind Run** |
| [`stability/attitude_stability.png`](file:///D:/ebca/evidence/final_blind_organism_test/stability/attitude_stability.png) | PNG Plot | `blind_life_run_telemetry.csv` (Roll, Pitch) | 120 | `20260816` | **100% Final Blind Run** |
| [`motors/commanded_and_wheel_jerk.png`](file:///D:/ebca/evidence/final_blind_organism_test/motors/commanded_and_wheel_jerk.png) | PNG Plot | `blind_life_run_telemetry.csv` ($u_L, u_R, \omega_L, \omega_R$) | 120 | `20260816` | **100% Final Blind Run** |
| [`sensors/range_sensor_heatmap.png`](file:///D:/ebca/evidence/final_blind_organism_test/sensors/range_sensor_heatmap.png) | PNG Plot | `blind_life_run_telemetry.csv` (Sonar clearance) | 120 | `20260816` | **100% Final Blind Run** |
| [`homeostasis/physiological_variables.png`](file:///D:/ebca/evidence/final_blind_organism_test/homeostasis/physiological_variables.png) | PNG Plot | `decision_trace.jsonl` ($E, T, F, S, D_h$) | 120 | `20260816` | **100% Final Blind Run** |
| [`memory/episodic_memory_map.png`](file:///D:/ebca/evidence/final_blind_organism_test/memory/episodic_memory_map.png) | PNG Plot | `agent.memory.episodes` | 120 | `20260816` | **100% Final Blind Run** |
| [`prediction/prediction_vs_actual.png`](file:///D:/ebca/evidence/final_blind_organism_test/prediction/prediction_vs_actual.png) | PNG Plot | `decision_trace.jsonl` ($\epsilon_t$ RMSE) | 120 | `20260816` | **100% Final Blind Run** |
| [`motivation/motivation_heatmap.png`](file:///D:/ebca/evidence/final_blind_organism_test/motivation/motivation_heatmap.png) | PNG Plot | `decision_trace.jsonl` (Drive matrix) | 120 | `20260816` | **100% Final Blind Run** |
| [`agency/internal_decision_timeline.png`](file:///D:/ebca/evidence/final_blind_organism_test/agency/internal_decision_timeline.png) | PNG Plot | `decision_trace.jsonl` (Chosen actions) | 120 | `20260816` | **100% Final Blind Run** |
| [`agency/endogenous_goals_vs_time.png`](file:///D:/ebca/evidence/final_blind_organism_test/agency/endogenous_goals_vs_time.png) | PNG Plot | `decision_trace.jsonl` (Active goals) | 120 | `20260816` | **100% Final Blind Run** |
| [`neuromodulation/neuromodulator_dynamics.png`](file:///D:/ebca/evidence/final_blind_organism_test/neuromodulation/neuromodulator_dynamics.png) | PNG Plot | Derived from $\epsilon_t, E, S$ | 120 | `20260816` | **Derived Metric Proxy** |
| [`integration/phi_proxy_timeline.png`](file:///D:/ebca/evidence/final_blind_organism_test/integration/phi_proxy_timeline.png) | PNG Plot | Tononi-Sporns cross-channel evaluation | 120 | `20260816` | **Derived Metric Proxy** |

---

## 2. Benchmark Video Lineage in `D:\ebca\replays/`

| Video File | Exact Origin | Relationship to Final Blind Run |
| :--- | :--- | :--- |
| `complete_blind_run.mp4` | 120-tick unscripted life run | **Master Final Blind Run Video** |
| `best_autonomous_episode.mp4` | 120-tick unscripted life run | Mirror of master blind run |
| `first_internally_generated_goal.mp4` | 120-tick unscripted life run | Mirror of master blind run |
| `strongest_organism_like_sequence.mp4` | 120-tick unscripted life run | Mirror of master blind run |
| `worst_autonomous_episode.mp4` | Separate 50-tick perturbation control trial (pitch push at tick 15) | **Targeted Control Experiment** |
| `recovery_episode.mp4` | Separate 50-tick perturbation control trial | Mirror of perturbation control trial |
| `memory_dependent_behavior.mp4` | Separate 50-tick memory causality control trial | **Targeted Control Experiment** |
| `self_model_adaptation.mp4` | Separate 50-tick ground friction adaptation trial | **Targeted Control Experiment** |
| `active_sensing_behavior.mp4` | Separate 50-tick curiosity gaze scanning trial | **Targeted Control Experiment** |
| `action_veto_behavior.mp4` | Separate 50-tick 30 rad/s ramming command rejection trial | **Targeted Control Experiment** |
