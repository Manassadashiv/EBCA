# CARL-DX Blind Run Memory Provenance Forensic Report

**Audit Subject**: Forensic Reconciliation of the 120 Memories in `decision_trace.jsonl`  
**Audit Date**: August 16, 2026  
**Status**: **`VERIFIED_WITH_LIMITATIONS`**  
**JSON Evidence**: [`audit/blind_run_memory_provenance.json`](file:///D:/ebca/audit/blind_run_memory_provenance.json)  

---

## 1. Executive Summary & Required Answers

| Question | Forensic Answer | Evidence |
| :--- | :--- | :--- |
| **1. Which file/checkpoint created the 120 memories?** | Created dynamically at runtime in RAM by `brain/carl_autonomous_agent.py` line 163 during the execution of `scratch/run_final_integrated_blind_test.py`. No checkpoint file loaded them. | `brain/carl_autonomous_agent.py:L160-172` |
| **2. Were they loaded before the blind run?** | **NO.** At tick 0 (`agent = CarlAutonomousOrganismAgent()`), `agent.memory.episodes` was strictly initialized to empty `[]` and `agent.memory.hdc_memory_matrix = np.zeros(2048)`. | `brain/carl_episodic_memory.py:L59-60` |
| **3. Were they created during the blind run?** | **YES.** Exactly 1 memory was appended per simulation tick from tick 1 through tick 120. | `brain/carl_autonomous_agent.py:L83,163` |
| **4. Were any of them relevant to the test environment?** | **NO.** They were false-positive collision episodes generated because normal ground floor contacts were misclassified as hazardous body collisions. | `vessel_kinetic.xml` contact analysis |
| **5. Was the blind run genuinely memory-clean at start?** | **YES.** The organism started with zero autobiographical experiences and zero pre-seeded knowledge of the arena or food beacon coordinates. | Code audit |
| **6. Zero-memory blind emergence claim standard?** | The run was memory-clean at startup, but during runtime, memory accumulated 120 false-positive hazard warnings. It should be classified as **`VERIFIED_WITH_LIMITATIONS (Runtime Memory Contamination)`**, not pure zero-memory emergence. | Technical Root Cause |

---

## 2. Technical Root Cause Analysis

### A. The Global `ncon` False-Positive Trigger
In `brain/carl_autonomous_agent.py` line 83:
```python
collision_occurred = (sensory.ncon > 4 or sensory.min_obstacle_dist < 0.15)
```
In MuJoCo, `d.ncon` measures all contact constraints across the entire world model. In `world/vessel_kinetic.xml`, multiple static and dynamic props rest on the floor:
- 4 floor contacts from `hazard_cube`
- 4 floor contacts from `gcube_0`
- 4 floor contacts from `gcube_1`
- 1 floor contact from `gball_0`
- 2 floor contacts from robot casters
- 4 floor contacts from robot drive wheels

Total world contacts on step 1 equaled **19 contacts**. Because $19 > 4$, `sensory.ncon > 4` evaluated to `True` on every single tick, falsely signaling a "collision" even while the robot was smoothly rolling across empty open floor.

### B. The Post-Run Trace Serialization Artifact
In `scratch/run_final_integrated_blind_test.py`:
```python
for tel in agent.telemetry_history:
    trace_entry = {
        ...,
        "memory_retrieval": {
            "episodes_in_memory": len(agent.memory.episodes)
        }
    }
```
Because the decision trace was serialized to disk **after** the 120-tick simulation finished, `len(agent.memory.episodes)` evaluated to 120 at the time of file writing, writing `episodes_in_memory = 120` on every single row (including tick 1) instead of recording the cumulative runtime count at that exact tick.
