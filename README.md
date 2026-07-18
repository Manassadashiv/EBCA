# EBCA — Embodied Biological Cognitive Architecture

**CARL** (Cognitive Autonomous Recurrent Lifeform) is a MuJoCo-simulated digital organism combining a Liquid State Machine reservoir, endocrine neuromodulator dynamics (DA / 5-HT / NE / ACh), STDP plasticity, hippocampal grid & place cells, and a planned imagination / free-energy engine — built toward an eventual sub-₹7,000 physical hardware deployment.

---

## Current Status

| Scope | Completion |
|---|---|
| Phase 1 — Digital Twin | **62.5%** |
| — Codebase modules written | 100% |
| — Modules actively wired into control loop | 25% |
| Phase 2 — Physical Hardware | 0% (planned) |
| **Overall** | **34.4%** |

Full per-module breakdown: [`.agents/AGENTS.md`](.agents/AGENTS.md)

---

## Simulation Worlds

This repo contains **two separate experiments** — they are not interchangeable:

| World file | Body | Entry point | Stage |
|---|---|---|---|
| `world/vessel_kinetic.xml` | 28-DOF arm + wheels (100 geoms, 18 joints) | `carl_simulation.py` | Primary development loop |
| `world/carl_mujoco.xml` | 2-body wheeled predator/prey (48 sensors) | `phase18_alife_pretrained.py` | Standalone emergent-behaviour demo |

---

## Repository Structure

```
EBCA/
├── carl_simulation.py          — Main entry point (30 Hz HAL loop)
├── phase18_alife_pretrained.py — Standalone ALife demo (emergent brain)
├── live_plotter.py             — Real-time telemetry dashboard
├── requirements.txt
│
├── world/                      — Physics bodies & MuJoCo wrapper
│   ├── carl_mujoco.xml
│   ├── vessel_kinetic.xml
│   ├── carl.urdf
│   └── carl_mj_physics.py
│
├── brain/                      — Cognitive modules
│   ├── carl_reservoir.py       — LSM reservoir (RLS-trained readout)
│   ├── carl_endocrine.py       — DA/NE/5-HT/ACh kinetics
│   ├── carl_reflex.py          — Spiking reflex layer
│   ├── carl_grid_cells.py      — Hexagonal grid + place cells
│   ├── carl_stdp.py            — STDP action evaluator
│   ├── carl_physarum.py        — Slime-mould-inspired pathfinding
│   ├── carl_omega_extensions.py— Mirror neurons, predictive allostasis, theta gate
│   ├── astar.py
│   └── (8 vision dataset / train / verify scripts — SSD-Lite)
│
├── memory/                     — Checkpoints (gitignored; created at runtime)
│
├── docs/                       — Architecture docs & roadmaps
│
└── external/                   — Adjacent research documents (not CARL-specific)
    └── cocl.md                 — COCL 2.0 aeroelastic capstone treatise
```

---

## 8-Layer Cognitive Stack

| Layer | Concept | Status |
|---|---|---|
| 0 | Physical embodiment (chassis, LiDAR, IMU) | ✅ Two world XMLs |
| 1 | Two-speed memory (working + holographic LTM, HDC) | 🟡 Reservoir built; HDC not wired |
| 2 | Endocrine + R-STDP plasticity | ✅ Built, partially wired |
| 3 | Grid/place cells, danger mapping | ✅ Built & wired |
| 4 | The Witness (metacognition, failure-pattern detection) | ❌ Planned |
| 5 | Causal reasoning / Optimal MPC | ❌ Planned |
| 6 | Imagination engine (predictive world model) | 🟡 Referenced; not integrated |
| 7 | Concept Genesis (unsupervised SOM) | ❌ Planned |

Full target architecture: [`docs/EBCA_MASTER_ROADMAP.md`](docs/EBCA_MASTER_ROADMAP.md)

---

## Quick Start

```bash
git clone https://github.com/Manassadashiv/EBCA.git
cd EBCA
pip install -r requirements.txt

# Primary simulation loop
python carl_simulation.py

# Standalone emergent-brain demo
python phase18_alife_pretrained.py
```

> Both entry points resolve all paths relative to `__file__` — no drive-letter assumptions.
> MuJoCo and a CUDA-capable PyTorch install are required for full functionality.

---

## Key Docs

| Doc | Purpose |
|---|---|
| [`docs/EBCA_MASTER_ROADMAP.md`](docs/EBCA_MASTER_ROADMAP.md) | Target 8-layer architecture & Pillar definitions |
| [`docs/GENESIS_MANIFEST.md`](docs/GENESIS_MANIFEST.md) | Phase-by-phase build plan |
| [`docs/TECHNICAL_SPECIFICATIONS.md`](docs/TECHNICAL_SPECIFICATIONS.md) | Matrix dimensions, update equations |
| [`docs/SESSION_STATE.md`](docs/SESSION_STATE.md) | Living session notes & current focus |
| [`.agents/AGENTS.md`](.agents/AGENTS.md) | Per-module integration checklist (honest % complete) |
| [`docs/codebase_audit_report.md`](docs/codebase_audit_report.md) | Repo health report (regenerated `cee9225`) |
