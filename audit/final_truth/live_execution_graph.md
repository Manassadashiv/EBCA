# CARL-DX LIVE PLAYGROUND EXECUTION GRAPH & CODE-PATH AUDIT

**Mission Standard**: NASA-Inspired Systems Engineering Rigor (Zero-Trust)  
**Target File**: [`carl_live_playground.py`](file:///D:/ebca/carl_live_playground.py)

---

## 1. Live Playground Initialization & Execution Graph

```mermaid
graph TD
    A["carl_live_playground.py: run_live_interactive_playground()"] --> B["LivePlaygroundSimulation.__init__()"]
    B --> C["Load XML: world/vessel_kinetic.xml (dt=0.01s)"]
    C --> D["setup_fun_playground(): Reposition 6 wall geoms & 3 pushable objects"]
    D --> E["50 physics settle steps: mujoco.mj_step()"]
    E --> F["Instantiate Agent: CarlAutonomousOrganismAgent(dt=0.0333s)"]
    F --> G["Launch Passive 3D Viewer: mujoco.viewer.launch_passive()"]
    
    G --> H["While viewer.is_running(): Main 30Hz Loop"]
    H --> I["1. Read Robot Position (get_robot_pos)"]
    I --> J["2. Food Absorption Check (dist < 0.35m -> respawn_food)"]
    J --> K["3. agent.step_cognitive_cycle(sim, food_coords)"]
    
    K --> L["3a. Proprioception: read_proprioception(sim)"]
    K --> M["3b. Stuck Monitor: stuck_detector.update()"]
    K --> N["3c. Empowerment: empowerment_core.evaluate()"]
    K --> O["3d. Self-Model: update_with_observation()"]
    K --> P["3e. Homeostasis: update_interoception()"]
    K --> Q["3f. Goal Arbitration: arbitrate_active_goal()"]
    K --> R["3g. Dreamer Rollouts: imagine_counterfactual_rollouts()"]
    K --> S["3h. Action Veto: evaluate_internal_action_veto()"]
    K --> T["3i. Actuator Output: write_actuator_commands(sim) -> sets data.ctrl"]
    
    T --> U["4. Physics Sub-stepping: for _ in range(8): mujoco.mj_step() [0.08s physics]"]
    U --> V["5. Viewer Sync: viewer.sync()"]
    V --> W["6. Terminal HUD Print (every 10 ticks)"]
    W --> X["7. Wall-Clock Sleep: time.sleep(1/30 - elapsed)"]
    X --> H
```

---

## 2. Key Execution Parameters in Live Playground
- **Physics Timestep**: $0.01\text{s}$ (from `vessel_kinetic.xml`)
- **Cognitive Cycle Rate**: $30\text{ Hz}$ ($dt_{\text{agent}} = 0.0333\text{s}$)
- **Physics Sub-steps per Tick**: **8 sub-steps** ($\Delta t_{\text{sim\_per\_tick}} = 8 \times 0.01\text{s} = 0.08\text{s}$)
- **Physics-to-Cognitive Ratio**: $0.08\text{s} / 0.0333\text{s} = \mathbf{2.4\times}$ (Physics runs 2.4x faster than the internal forward world model expects).
- **Arena Wall Configuration**: Repositioned by `setup_fun_playground()`.
