# CARL STAGE 1 — REPRODUCIBILITY MANIFEST
**Classification**: [VALIDATION CRITERION] Reproducibility & Provenance Manifest  
**Version**: 1.0.0-canonical  
**Date**: September 3, 2026  

---

## 1. Execution Environment & Dependencies

| Component | Specification |
| :--- | :--- |
| **Operating System** | Microsoft Windows 11 Home / Pro (x86_64) |
| **Host Python Interpreter** | CPython `3.14.2` (`C:\Python314\python.exe`) |
| **Physics Simulation Engine** | MuJoCo `3.3.4` (Headless & Interactive via native bindings) |
| **Numerical Processing** | NumPy `2.2.3` |
| **Scientific Computing** | SciPy `1.15.2` |
| **Plotting & Graphics** | Matplotlib `3.10.1` |
| **Testing Framework** | pytest `9.1.1` |
| **GPU Hardware Detected** | NVIDIA GeForce RTX 3050 Laptop GPU (Driver `581.86`, CUDA `13.0`) |

---

## 2. Experimental Seeds & Parameters

| Experiment | Seed Parameter | Configuration / Regimes | Output Destination |
| :--- | :--- | :--- | :--- |
| **Gate #1 Dynamic Safety Sweep** | `seed = 42` | $10,000$ ticks, step reversal regime ($\pm 0.150$), $\mu \in \{0.3, 0.6, 0.9, 1.2\}$ | `evidence/stage1/stage1_safety_sweep_results.json` |
| **Gate #4 Multi-Seed Discovery** | `seeds = [42, 101, 2024, 777, 999]` | $1,500$ ticks/seed, Coupled Synergy babbling, $N_{\text{surr}} = 200$, $\alpha_{\text{FWER}} = 0.01$ | `evidence/stage1/stage1_discovery_results.json` |
| **Visualization Pipeline** | `seed = 42` | $1,500$ ticks closed-loop babbling | `evidence/stage1/*.png` (7 publication figures) |
| **Unit Regression Suite** | Deterministic (`seed = 42`) | 9 isolated mathematical/architectural tests | `tests/test_stage1_suite.py` |

---

## 3. Cryptographic Checksums (SHA-256)

All production implementation files, tests, and experiment runners are cryptographically locked:

| Relative Path | SHA-256 Cryptographic Checksum |
| :--- | :--- |
| `brain/carl_stage1_babbler.py` | `5EDC633AB68816CE2EC6142D6CAD89405415C5ED39EE6E4144A76134730B64B5` |
| `brain/carl_stage1_discovery.py` | `CE15D1223844264253999004A7020E1B44A0E63AE05E258EBCA7060B0DE710D3` |
| `brain/carl_stage1_hal.py` | `6100A786F26490FA70F844351C155CEA2F5D855417FC1EC4A1560D1CDD7ECDF3` |
| `brain/carl_stage1_organism.py` | `2FB9264B8B3262BEF8840FEB08BE07EE9A82E275ADF00F3B4D846099B7035537` |
| `brain/carl_stage1_reservoir.py` | `1BAA04F656B73BA8D414E0F1D06C5FAFAD681FFEE9C24FD4FC91455A1035F7F8` |
| `tests/test_stage1_suite.py` | `24ABD436D37C391C21061D966C06701BAEBB31FF515E7A4C7C60E85B15261ACA` |
| `experiments/generate_stage1_plots.py` | `62B518C95403ED6DD8F2492B737A9CF37EE4795CC7391E5AA803DEE03CDF8784` |
| `experiments/run_stage1_experiments.py` | `75E61FA772E4100B7001E3E1F914EB2E827C0154C9E1EA1A2E267DD6FA46265C` |

---

## 4. Exact Reproduction Command Sequence

To reproduce all Stage 1 results, figures, and unit test validations from a fresh shell:

```bash
# 1. Run Automated Unit Test Suite (9 tests, ~18 seconds)
python -m pytest tests/test_stage1_suite.py

# 2. Run Formal Stage 1 Validation Experiments (Gates #1 & #4)
python experiments/run_stage1_experiments.py

# 3. Generate All 7 Publication-Grade Visual Scientific Figures
python experiments/generate_stage1_plots.py
```
