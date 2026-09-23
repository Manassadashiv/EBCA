"""
tests/test_stage3_ast_anti_cheat.py — Stage 3.0 Pre-Flight Anti-Cheat & Pipeline Isolation Suite
Classification: [STAGE 3.0 INTEGRITY GATEWAY] Fail-Closed Pre-Flight Verification

Verifies:
1. Zero static AST reachability to privileged simulator state in cognitive/decision pipeline.
2. Complete purge of dormant geom_xpos and qpos z-height leaks in carl_embodied_organism.py.
3. Air-gapped subprocess sandbox execution with poisoned MuJoCo (sys.modules['mujoco'] = None).
4. Baseline cryptographic SHA-256 integrity verification.
5. CANN & Spatial Memory data path verification.
"""

import ast
import hashlib
import os
import sys
import subprocess
from pathlib import Path
import numpy as np
import torch
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# 1. Cognitive Decision Pipeline modules that MUST NOT access simulator state
COGNITIVE_DECISION_PIPELINE_FILES = [
    REPO_ROOT / "brain" / "carl_autonomous_agent.py",
    REPO_ROOT / "brain" / "carl_stage2_3_r1_deliberation.py",
    REPO_ROOT / "brain" / "carl_stage2_2_r2_occupancy_memory.py",
    REPO_ROOT / "brain" / "carl_stage2_2_world_model.py",
    REPO_ROOT / "brain" / "carl_stage2_2_memory_module.py",
    REPO_ROOT / "brain" / "carl_stage2_integrated_brain.py",
    REPO_ROOT / "brain" / "carl_stage2_hd_ring.py",
    REPO_ROOT / "brain" / "carl_stage2_grid_torus.py",
    REPO_ROOT / "brain" / "carl_mppi_deliberation.py",
    REPO_ROOT / "brain" / "carl_active_inference.py",
]

# 2. Frozen Stage 3.1 Cognitive Baseline Hashes
STAGE2_FROZEN_BASELINE = {
    # Certified Stage 3.3 baseline with continuous MPPI deliberation integrated
    "brain/carl_autonomous_agent.py": "721678532c6444ac19ae70294a20a18674bfc9c248f0c4ca9f03ebe2b2a295fc",
    "brain/carl_stage1_hal.py": "3a37fd1569980880310f96b21b006ada74cfdf20f1e13a84ff9671c3fdf8f89f",
    "brain/carl_stage2_integrated_brain.py": "7ca0d38794de86088eb6b0a678b4b119b934b181573911d4bca8d970c5e1f78c",
    "brain/carl_stage2_hd_ring.py": "1fa71ab575dc17c064a07a646703e120f24f84030e5e8a3142e3a21bde1f99fc",
    "brain/carl_stage2_grid_torus.py": "02a7c1cd70436fa14a66e51903a800a10c3a863e890c36189eccffa839859017",
    "brain/carl_stage2_3_r1_deliberation.py": "651682c3e0950a0bfa03b7841c313e4bd6028a3b29eb5a7af3d4015b35579019",
    "brain/carl_stage2_2_r2_occupancy_memory.py": "d68d1b6804ac09a2367f54f0a93bbc0aa6a7e5c3b78c545454a0f1c75f6bf904",
    "checkpoints/stage2_2_grounded/grounded_body_model.pt": "b23b2dac6b7c4d8830999cd57645cde867da2f76481ee02791ea892c8cf29b16",
    "evidence/stage2_2_r2/arena_occupancy_grid.pt": "9b79f52d82582b8299625a69e6439bb47774e60f25d7a92e0c13c048f7f05424",
    "evidence/stage2_final/stage2_final_scorecard.json": "39d211fcd376783b32e527ed9970bc5adff7612fe3ab51f8607626536662d908",
    "evidence/stage2_3_r1/stage2_3_r1_scorecard.json": "cd5e51f11185fece59986c783166f4a3b3b8e645b5499bf0640292f20c650be6",
    # Post-purge hash for carl_embodied_organism.py
    "brain/carl_embodied_organism.py": "d08b5cf379ff8ca5796415477113114c57bbb31e2ca57e3898e57236ae955bce",
}


def test_decision_pipeline_ast_static_scan():
    """
    Tier 1: AST static inspection of all active cognitive decision files.
    Verifies ZERO imports of mujoco and ZERO lookups of privileged simulator attributes.
    """
    forbidden_modules = {"mujoco"}
    forbidden_attrs = {"geom_xpos", "mj_ray", "qpos", "qvel", "qacc"}
    forbidden_calls = {"mj_ray", "mj_step", "mj_forward"}

    for target_file in COGNITIVE_DECISION_PIPELINE_FILES:
        assert target_file.exists(), f"Missing decision file: {target_file}"
        source = target_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(target_file))

        for node in ast.walk(tree):
            # 1. Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forb in forbidden_modules:
                        assert forb.lower() not in alias.name.lower(), (
                            f"FORBIDDEN IMPORT: '{alias.name}' in {target_file.name} line {node.lineno}"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for forb in forbidden_modules:
                        assert forb.lower() not in node.module.lower(), (
                            f"FORBIDDEN FROM-IMPORT: '{node.module}' in {target_file.name} line {node.lineno}"
                        )

            # 2. Attributes
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_attrs, (
                    f"FORBIDDEN SIMULATOR ATTRIBUTE: '{node.attr}' in {target_file.name} line {node.lineno}"
                )

            # 3. Calls / Identifiers
            elif isinstance(node, ast.Name):
                assert node.id not in forbidden_calls, (
                    f"FORBIDDEN SIMULATOR CALL: '{node.id}' in {target_file.name} line {node.lineno}"
                )

    print(f"Decision Pipeline AST Scan: PASS. All {len(COGNITIVE_DECISION_PIPELINE_FILES)} files 100% clean.")


def test_embodied_organism_hygiene_scan():
    """
    Verifies that carl_embodied_organism.py has purged geom_xpos and qpos z-height reads.
    """
    target = REPO_ROOT / "brain" / "carl_embodied_organism.py"
    source = target.read_text(encoding="utf-8")

    # 1. geom_xpos must be completely purged from code and comments
    assert "geom_xpos" not in source, "LEAK DETECTED: geom_xpos still present in carl_embodied_organism.py"

    # 2. AST inspection: assert no geom_xpos attribute access
    tree = ast.parse(source, filename=str(target))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "geom_xpos":
            pytest.fail(f"geom_xpos attribute access at line {node.lineno}")

    # Check that z is assigned a constant rest height
    assert "z = 0.05" in source, "Chassis rest height 0.05m must be used instead of qpos z"
    print("Embodied Organism Hygiene: PASS. geom_xpos and qpos z-read successfully purged.")


def test_subprocess_airgap_mujoco_poisoned():
    """
    Tier 2: Subprocess Sandbox Execution with poisoned MuJoCo.
    Executes deliberation and CANN updates where sys.modules['mujoco'] = None.
    """
    sandbox_script = """
import sys
# Poison MuJoCo completely
sys.modules['mujoco'] = None

# Verify poisoning is active
try:
    import mujoco
    print("POISON_FAILED")
    sys.exit(1)
except (ImportError, ModuleNotFoundError):
    pass

import numpy as np
import torch
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain

# 1. Instantiate CANN
cann = CarlStage2BIntegratedBrain(seed=42)
cann.w_rot[20] = 1.0
cann.w_fwd[15] = 1.0
cann.is_developmentally_trained = True

raw_s = np.zeros(25, dtype=np.float64)
raw_s[:15] = 2.5
u_act = np.zeros(6, dtype=np.float64)
res_cann = cann.update_brain(u_executed=u_act, s_current=raw_s)
assert res_cann["total_neurons_active"] == 2114, "CANN neuron count mismatch"

# 2. Instantiate Deliberation Engine
delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
sonars = np.full(15, 2.5, dtype=np.float32)
act, tel = delib.select_action(curr_sensors=sonars, curr_v=0.1, curr_w=0.0)
assert act.shape == (6,), f"Action shape mismatch: {act.shape}"
assert "selected_branch" in tel, "Missing selected_branch in telemetry"

print("SUBPROCESS_AIRGAP_PASS")
sys.exit(0)
"""
    proc = subprocess.run(
        [sys.executable, "-c", sandbox_script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60
    )
    assert proc.returncode == 0, f"Air-gapped subprocess crashed:\n{proc.stderr}\n{proc.stdout}"
    assert "SUBPROCESS_AIRGAP_PASS" in proc.stdout, f"Expected pass message, got: {proc.stdout}"
    print("Subprocess Airgap: PASS. Cognitive pipeline executes with poisoned MuJoCo.")


def test_baseline_sha256_integrity():
    """
    Tier 3: Cryptographic baseline hash verification.
    Ensures no baseline Stage 2 artifacts are silently mutated.
    """
    for rel_path, expected_hash in STAGE2_FROZEN_BASELINE.items():
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Baseline artifact missing: {rel_path}"
        computed_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert computed_hash == expected_hash, (
            f"HASH MISMATCH in {rel_path}:\n  Expected: {expected_hash}\n  Computed: {computed_hash}"
        )
    print(f"Cryptographic Baseline: PASS. All {len(STAGE2_FROZEN_BASELINE)} baseline artifacts intact.")


def test_cann_data_path_verification():
    """
    Tier 4A: CANN Data Path Verification.
    Verifies that the 2,114-unit neuromorphic computational architecture:
    - Steps deterministically given motor and sensor inputs.
    - Decodes continuous head-direction attractor bump angle.
    - Decodes continuous 2D toroidal grid displacement.
    """
    from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain

    brain = CarlStage2BIntegratedBrain(seed=42, dt=0.030)
    assert brain.TOTAL_NEURONS == 2114

    # Babble to train projections unprivileged
    rng = np.random.RandomState(42)
    U_babble = rng.uniform(-0.15, 0.15, size=(50, 6))
    S_babble = np.zeros((50, 25), dtype=np.float64)
    S_babble[:, 20] = (U_babble[:, 1] - U_babble[:, 0]) * 1.5  # Gyro response
    S_babble[:, 15] = 0.5 * (U_babble[:, 0] + U_babble[:, 1]) * 2.0  # Accel response
    brain.develop_from_babbling(U_babble, S_babble)
    brain.learn_motor_efference(U_babble, S_babble)

    # Step brain with sample action and sensor vector
    u_test = np.array([0.10, 0.05, 0.0, 0.0, 0.0, 0.0])
    s_test = np.zeros(25, dtype=np.float64)
    s_test[:15] = 3.0
    s_test[20] = 0.25  # Gyro yaw
    s_test[15] = 1.0   # Accel x

    res = brain.update_brain(u_executed=u_test, s_current=s_test)
    assert "hd_decoded_heading" in res
    assert "grid_unwrapped_x" in res
    assert "grid_unwrapped_y" in res
    assert res["total_neurons_active"] == 2114
    assert isinstance(res["hd_decoded_heading"], (float, np.floating))
    print(f"CANN Data Path: PASS. Heading={res['hd_decoded_heading']:.4f} rad, Grid=({res['grid_unwrapped_x']:.3f}, {res['grid_unwrapped_y']:.3f})")


def test_spatial_memory_data_path_verification():
    """
    Tier 4B: Spatial Memory Data Path Verification.
    Verifies that spatial occupancy memory actively enters candidate trajectory evaluation.
    Compares deliberative mode (active map) vs amnesic mode (erased map):
    An obstacle placed along a candidate branch must reduce that branch's utility in deliberative
    mode while leaving amnesic mode unaffected.
    """
    from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

    # 1. Create deliberative engine
    delib_active = CARLStage2_3R1DeliberationEngine(mode="deliberative")
    delib_amnesic = CARLStage2_3R1DeliberationEngine(mode="amnesic")

    delib_active.initialize_pose(0.0, 0.0, 0.0)
    delib_amnesic.initialize_pose(0.0, 0.0, 0.0)

    # Place obstacle 0.4m ahead in delib_active's occupancy grid
    gx = int((0.40 - (-6.4)) / 0.10)
    gy = int((0.00 - (-6.4)) / 0.10)
    delib_active.grid_ch0[0, 0, gy, gx] = 10.0  # High occupancy hit

    sonars_open = np.full(15, 4.0, dtype=np.float32)

    _, tel_active = delib_active.select_action(curr_sensors=sonars_open, curr_v=0.1, curr_w=0.0)
    _, tel_amnesic = delib_amnesic.select_action(curr_sensors=sonars_open, curr_v=0.1, curr_w=0.0)

    # In amnesic mode, straight branch should have higher utility than in active mode where obstacle is remembered
    u_straight_active = tel_active.get("all_utilities", {}).get("straight_full", None)
    u_straight_amnesic = tel_amnesic.get("all_utilities", {}).get("straight_full", None)

    assert u_straight_active is not None, "all_utilities missing straight_full in active mode"
    assert u_straight_amnesic is not None, "all_utilities missing straight_full in amnesic mode"

    assert u_straight_active < u_straight_amnesic, (
        f"Spatial memory failed to penalize branch utility: active={u_straight_active}, amnesic={u_straight_amnesic}"
    )
    print(f"Spatial Memory Data Path: PASS. Active utility ({u_straight_active:.2f}) < Amnesic utility ({u_straight_amnesic:.2f}) due to remembered obstacle.")


def test_cann_causal_wiring_verification():
    """
    Tier 4C: CANN Causal Wiring Verification.
    Verifies that passing CANN continuous attractor state to deliberation.select_action():
    - Modulates candidate branch utilities via population directional coherence.
    - Demonstrates that Intact CANN vs Zeroed CANN yields measurable utility differences.
    """
    from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

    delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
    delib.initialize_pose(0.0, 0.0, 0.0)
    sonars_open = np.full(15, 3.0, dtype=np.float32)

    # 1. Intact CANN state (bump at 0 rad - pointing straight)
    r_hd_intact = np.zeros(64, dtype=np.float64)
    # Peak at neuron 32 (center of [-pi, pi] = 0 rad)
    angles_hd = np.linspace(-np.pi, np.pi, 64, endpoint=False)
    r_hd_intact = np.exp(-0.5 * (angles_hd / 0.4)**2)

    cann_intact = {
        "hd_decoded_heading": 0.0,
        "grid_unwrapped_x": 0.0,
        "grid_unwrapped_y": 0.0,
        "hd_rates": r_hd_intact,
    }

    # 2. Zeroed CANN state
    cann_zeroed = {
        "hd_decoded_heading": 0.0,
        "grid_unwrapped_x": 0.0,
        "grid_unwrapped_y": 0.0,
        "hd_rates": np.zeros(64, dtype=np.float64),
    }

    _, tel_intact = delib.select_action(curr_sensors=sonars_open, curr_v=0.1, curr_w=0.0, cann_state=cann_intact)
    _, tel_zeroed = delib.select_action(curr_sensors=sonars_open, curr_v=0.1, curr_w=0.0, cann_state=cann_zeroed)

    u_intact_straight = tel_intact["all_utilities"]["straight_full"]
    u_zeroed_straight = tel_zeroed["all_utilities"]["straight_full"]

    # The intact CANN bump at 0 rad must add positive directional coherence to straight_full
    delta_util = u_intact_straight - u_zeroed_straight
    assert delta_util > 0.50, f"CANN directional coherence failed to modulate utility: delta={delta_util:.3f}"
    assert tel_intact["cann_wired"] is True
    assert tel_zeroed["cann_wired"] is True
    print(f"CANN Causal Wiring: PASS. Intact straight utility ({u_intact_straight:.2f}) > Zeroed ({u_zeroed_straight:.2f}), delta={delta_util:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
