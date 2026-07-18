# EBCA: Embodied Biological Cognitive Architecture

This workspace contains the clean, modular, bottom-up implementation of **CARL** (Cognitive Autonomous Recurrent Lifeform). The codebase is structured sequentially, matching the hierarchical layers of a biological robot from the physics level up to the cognitive processing stack.

---

## Workspace Directory Architecture

```
D:\ebca\
│
├── [LEVEL 0: PHYSICAL EMBODIMENT & SIMULATION ENGINE]
│   ├── world/
│   │   ├── carl_mujoco.xml   <── 3D physics body and actuator definitions (joints, tires, LiDAR)
│   │   └── carl_mj_physics.py <── MuJoCo engine wrapper and physics stepping control
│   └── carl_simulation.py     <── Main simulation runner: coordinates HAL and control loops
│
├── [LEVEL 1: NEUROMODULATORY REFLEXES & INSTINCTUAL PATHWAYS]
│   └── brain/
│       ├── carl_stdp.py       <── Synaptic weight adjustment via Spike-Timing-Dependent Plasticity
│       └── carl_grid_cells.py <── Hexagonal grid wave models mapping spatial coordinates
│
├── [LEVEL 2: RECURRENT COGNITIVE RESERVOIR & PLANNING]
│   └── GENESIS/
│       └── carl_scout/
│           ├── carl_agent.py   <── Nervous system coordinator running the 8-layer stack
│           ├── carl_cortex.py  <── Liquid State Machine (LSM) recurrent neural reservoir (500 neurons)
│           ├── carl_bios.py    <── Dynamic endocrine decay kinetics (DA, 5-HT, NE, ACh)
│           ├── carl_planner.py <── Spatial navigation routing and A* pathfinding
│           └── carl_imagination.py <── Predictive world models (T_wm) simulating trajectory forecasts
│
├── [LEVEL 3: PERSISTENT WEIGHT STATE & CHECKPOINTS]
│   └── memory/
│       └── carl_brain.npz      <── Serialized neural weights and offline learning state configurations
│
├── [SYSTEM VALIDATION & PERFORMANCE PROFILES]
│   └── GENESIS/tests_and_diagnostics/
│       ├── test_speed.py       <── Checks control loop frequency stability against the 30 Hz budget
│       └── test_stability.py   <── Validates signal value bounding (clamps, NaN prevention checks)
│
└── [TECHNICAL DOCUMENTATION & BLUEPRINTS]
    └── docs/
        ├── TECHNICAL_SPECIFICATIONS.md <── Mathematical formulations of matrices and updates
        └── EVOLUTIONARY_ROADMAP.md      <── Rebuild roadmaps and step-by-step progress checklists
```

---

## Core Task Mapping & Directory Reference

For developers and researchers modifying subsystems:

| Task Objective | Target File | Directory Path |
| :--- | :--- | :--- |
| Modify physical geometry or actuator properties | `carl_mujoco.xml` | [D:\ebca\world\](file:///D:/ebca/world/) |
| Edit sensor pre-processing or exteroceptive mapping | `carl_simulation.py` | [D:\ebca\](file:///D:/ebca/) |
| Adjust hormone baseline levels or decay metrics | `carl_bios.py` | [D:\ebca\GENESIS\carl_scout\](file:///D:/ebca/GENESIS/carl_scout/) |
| Inspect or alter spatial grid wave dimensions | `carl_grid_cells.py` | [D:\ebca\brain\](file:///D:/ebca/brain/) |
| Reference core update equations and matrix dimensions | `TECHNICAL_SPECIFICATIONS.md` | [D:\ebca\docs\](file:///D:/ebca/docs/) |

---

## Execution Instructions

To start the simulation environment and initialize the base Hardware Abstraction Layer (HAL) loop:
```powershell
python carl_simulation.py
```
This boots the 30 Hz control cycle and launches the interactive MuJoCo visualization viewer.
