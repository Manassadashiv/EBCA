# CARL-DX BENCHMARK SUITE EXECUTION GRAPH & CODE-PATH AUDIT

**Mission Standard**: NASA-Inspired Systems Engineering Rigor (Zero-Trust)  
**Target Files**: [`brain/carl_reflex_laboratory.py`](file:///D:/ebca/brain/carl_reflex_laboratory.py), [`brain/carl_adversarial_emergence_harness.py`](file:///D:/ebca/brain/carl_adversarial_emergence_harness.py)

---

## 1. Benchmark Suite Initialization & Execution Graph

```mermaid
graph TD
    A["benchmark: run_full_master_qualification() / execute_full_adversarial_validation_directive()"] --> B["MuJoCoHardwareAbstractionLayer.__init__()"]
    B --> C["Load XML: world/vessel_kinetic.xml (dt=0.01s)"]
    C --> D["Default XML Arena Geometries (No setup_fun_playground overrides)"]
    D --> E["Instantiate Agent: CarlAutonomousOrganismAgent(dt=0.0333s)"]
    
    E --> F["Benchmark Headless Evaluation Loop (30Hz Cognitive Steps)"]
    F --> G["1. agent.step_cognitive_cycle(self.hal, [food_coords])"]
    
    G --> H["1a. Proprioception: read_proprioception(self.hal)"]
    G --> I["1b. Stuck Monitor: stuck_detector.update()"]
    G --> J["1c. Empowerment: empowerment_core.evaluate()"]
    G --> K["1d. Self-Model: update_with_observation()"]
    G --> L["1e. Homeostasis: update_interoception()"]
    G --> M["1f. Goal Arbitration: arbitrate_active_goal()"]
    G --> N["1g. Dreamer Rollouts: imagine_counterfactual_rollouts()"]
    G --> O["1h. Action Veto: evaluate_internal_action_veto()"]
    G --> P["1i. Actuator Output: write_actuator_commands(self.hal) -> sets data.ctrl"]
    
    P --> Q["2. Physics Sub-stepping: for _ in range(3): self.hal.step() [0.03s physics]"]
    Q --> R["3. Log Telemetry to CognitiveCycleTelemetry history"]
    R --> S["4. Headless Offscreen Rendering: mujoco.Renderer -> write MP4 frame"]
    S --> F
```

---

## 2. Key Execution Parameters in Benchmark Suite
- **Physics Timestep**: $0.01\text{s}$ (from `vessel_kinetic.xml`)
- **Cognitive Cycle Rate**: $30\text{ Hz}$ ($dt_{\text{agent}} = 0.0333\text{s}$)
- **Physics Sub-steps per Tick**: **3 sub-steps** ($\Delta t_{\text{sim\_per\_tick}} = 3 \times 0.01\text{s} = 0.03\text{s}$)
- **Physics-to-Cognitive Ratio**: $0.03\text{s} / 0.0333\text{s} = \mathbf{0.90\times} \approx \mathbf{1.0\times}$ (Physics is synchronous with the internal forward world model).
- **Arena Wall Configuration**: Default XML maze layout or programmatic adversarial disturbance geoms.
