# Codebase Audit Report

> **Last regenerated:** 18 July 2026 against commit `cee9225`
> **Scope:** Files actually pushed to the repository — local-only workspace directories
> (`GENESIS/`, `GENESIS_BIPED/`, `GENESIS_HAND/`) are **excluded** by `.gitignore`
> and do **not** appear in a fresh clone.

---

## Summary

| Category | Count |
|---|---|
| Python source files | 22 |
| XML / URDF world files | 3 |
| Syntax errors | **0** |
| Stub / TODO markers in code | **0** |
| Hardcoded absolute paths | **0** (fixed `cee9225`) |
| Missing `requirements.txt` entries | **0** (fixed `cee9225`) |

---

## 1. Python Modules (brain/)

All files compile clean (`py_compile` verified):

| File | Lines | Status |
|---|---|---|
| `carl_reservoir.py` | ~320 | ✅ Active — wired into `carl_simulation.py` |
| `carl_endocrine.py` | ~280 | ✅ Active — DA/5-HT/NE/ACh wired |
| `carl_reflex.py` | ~180 | ✅ Active — spiking reflex layer |
| `carl_grid_cells.py` | ~452 | ✅ Active — place/grid cells wired |
| `carl_stdp.py` | ~200 | ✅ Active — STDP evaluator |
| `carl_physarum.py` | ~150 | 🟡 Built, not yet wired into main loop |
| `carl_omega_extensions.py` | ~280 | 🟡 Built (mirror neurons, theta gate), not yet wired |
| `astar.py` | ~60 | ✅ Active — used by grid cells |
| `collect_multi_object_dataset.py` | ~160 | 🔧 Data pipeline — run manually |
| `collect_vision_dataset.py` | ~120 | 🔧 Data pipeline — run manually |
| `train_multi_object_vision.py` | ~200 | 🔧 Training script — run manually |
| `train_vision.py` | ~170 | 🔧 Training script — run manually |
| `verify_multi_object_predictions.py` | ~100 | 🔧 Eval script — run manually |
| `verify_vision_predictions.py` | ~100 | 🔧 Eval script — run manually |
| `plot_telemetry.py` | ~145 | 🔧 Analysis script — run manually |
| `show_carl.py` | ~60 | 🔧 Visualizer — run manually |

---

## 2. Root-Level Entry Points

| File | Lines | Status |
|---|---|---|
| `carl_simulation.py` | 901 | ✅ Primary entry point (README-documented) |
| `phase18_alife_pretrained.py` | 1,033 | ✅ Standalone ALife demo (emergent brain) |
| `live_plotter.py` | 131 | 🔧 Real-time telemetry dashboard |

---

## 3. World Files

| File | Body | Used by |
|---|---|---|
| `world/vessel_kinetic.xml` | 28-DOF arm + wheels (100 geoms, 18 joints) | `carl_simulation.py` |
| `world/carl_mujoco.xml` | 2-body wheeled predator/prey (48 sensors) | `phase18_alife_pretrained.py` |
| `world/carl.urdf` | URDF mirror of kinetic body | Import reference |
| `world/carl_mj_physics.py` | MuJoCo wrapper | Both simulation runners |

> **Note:** `vessel_kinetic.xml` and `carl_mujoco.xml` define **different robots** for two different experiment stages.
> They are not interchangeable entry points — see README §"Simulation Worlds" for the distinction.

---

## 4. Previously Reported Issues (All Resolved)

These were real bugs in earlier commits; they are listed here for historical accuracy and are **already fixed**:

| Issue | Fixed in |
|---|---|
| `phase18_alife_pretrained.py` — `ModuleNotFoundError` (flat imports vs. `world/`/`brain/` layout) | `034d21c` |
| All scripts — hardcoded `D:/ebca/...` paths break on any other machine | `cee9225` |
| `requirements.txt` — missing `torchvision`, `websockets`, `opencv-python` | `034d21c` + `cee9225` |

---

## 5. Known Minor Issues (Non-Blocking)

| Issue | Severity | Location |
|---|---|---|
| UTF-8/cp1252 mojibake (`â€"` for `—`) in comments | Cosmetic | `phase18_alife_pretrained.py` line 2; `SESSION_STATE.md` title |
| `phase18` checkpoint saves resolve relative to CWD, not `__file__` | Low — safe if launched from repo root | `phase18_alife_pretrained.py` checkpoint block |
| `carl_physarum.py` and `carl_omega_extensions.py` not yet wired into main loop | Integration gap, tracked in `AGENTS.md` | `carl_simulation.py` |

---

## 6. Integration Completion (From `.agents/AGENTS.md`)

| Scope | Status |
|---|---|
| Overall project (Phase 1 + Phase 2) | **34.4%** |
| Phase 1 — Digital Twin | **62.5%** (modules 100% written; 25% actively wired) |
| Phase 2 — Physical Hardware | **0%** (planned) |

> The gap between "written" and "wired" is the primary engineering priority.
> Tracked module-by-module in `.agents/AGENTS.md`.
