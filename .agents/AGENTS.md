# CARL-Ω Project Customizations & Rules

## Persistent Project Context

* **Project Progress Summary**:
  * **Overall Project (Phase 1 + Phase 2)**: **36% Complete** *(updated 19 July 2026)*
  * **Phase 1: Digital Twin (Mini Project)**: **63% Complete**
    * Codebase Modules: 100% Written (HDC, LSM, STDP, IK, grid cells, place cells, physarum, omega extensions, SSD-Lite vision).
    * Active Integration: 37% Connected:
      * ✅ Wired: LSM reservoir, EndocrineSystem, SpikingReflexLayer, GridCellModule, PlaceCellLayer, HippocampalNavigator, SSD-Lite vision (inference at 30 Hz)
      * 🟡 Standalone (built, not wired): carl_physarum.py, carl_omega_extensions.py
      * ❌ Not yet built: TheWitness (Layer 4), Imagination Engine T_wm (Layer 6), MPC (Layer 5), SOM/Concept Genesis (Layer 7)
    * Foundation work completed this session:
      * ✅ All hardcoded D:/ebca paths replaced with BASE_DIR resolution (portable on any OS)
      * ✅ phase18_alife_pretrained.py imports fixed (runs from repo root)
      * ✅ requirements.txt complete (torchvision, websockets, opencv-python added)
      * ✅ 80-test suite added (tests/test_endocrine.py, test_reservoir.py, test_grid_cells.py)
      * ✅ GitHub Actions CI workflow (.github/workflows/ci.yml)
      * ✅ Docstrings added to all public functions in brain/carl_endocrine.py
      * ✅ README rewritten (status %, world-split table, 8-layer stack)
      * ✅ codebase_audit_report.md regenerated from git HEAD
      * ✅ integration_roadmap.md written (local, docs/) with acceptance criteria per step
  * **Phase 2: Physical Hardware (Major Project)**: **0% Complete** (Planned).

## Key Implementation Constraints
* **Sonar Array**: Mapped as a 12-sonar physical ultrasonic array (each with a $30^\circ$ cone) interpolated software-side to 24 virtual sonar rays.
* **Camera Coordinate Frame**: Corrected camera mapping formula:
  $$\text{angle\_cam} = (0.5 - c_x / \text{img\_width}) \times \text{fov\_rad}$$
  Matched to sonar array using:
  $$\text{angle\_body} = \text{angle\_cam} + \text{head\_pan}$$
  with angular wrap-around comparison.
