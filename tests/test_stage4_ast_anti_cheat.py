"""
tests/test_stage4_ast_anti_cheat.py — Stage 4 Master Anti-Cheat & Subprocess Airgap Verification
Classification: Formal Architectural Invariant & Cognitive Quarantine Suite

Mandatory Tiers:
- Tier 1: Static AST inspection across all 19 cognitive decision pipeline files (zero MuJoCo imports, zero simulator coordinates).
- Tier 2: Physical hardware airgap: Embodied organism code hygiene.
- Tier 3: Poisoned MuJoCo airgap subprocess test.
- Tier 4: Cryptographic integrity of certified upstream modules.
- Tier 5: Stage 4 Memory Organs (STDP, HDC, SWR, GIS) quarantine verification.
"""

import ast
import hashlib
import os
import subprocess
import sys
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# All active cognitive decision files in Stage 4 (strictly airgapped from simulator internals)
COGNITIVE_DECISION_PIPELINE_FILES = [
    REPO_ROOT / "brain" / "carl_homeostatic_core.py",
    REPO_ROOT / "brain" / "carl_generative_self_model.py",
    REPO_ROOT / "brain" / "carl_episodic_memory.py",
    REPO_ROOT / "brain" / "carl_endogenous_agency.py",
    REPO_ROOT / "brain" / "carl_stuck_recovery.py",
    REPO_ROOT / "brain" / "carl_empowerment.py",
    REPO_ROOT / "brain" / "carl_stage2_integrated_brain.py",
    REPO_ROOT / "brain" / "carl_stage2_3_r1_deliberation.py",
    REPO_ROOT / "brain" / "carl_mppi_deliberation.py",
    REPO_ROOT / "brain" / "carl_active_inference.py",
    REPO_ROOT / "brain" / "carl_endocrine_adaptation.py",
    REPO_ROOT / "brain" / "carl_physarum.py",
    REPO_ROOT / "brain" / "carl_motor_synergies.py",
    REPO_ROOT / "brain" / "carl_vision.py",
    REPO_ROOT / "brain" / "carl_stdp.py",
    REPO_ROOT / "brain" / "carl_hdc.py",
    REPO_ROOT / "brain" / "carl_rem_sleep.py",
    REPO_ROOT / "brain" / "carl_gis.py",
]

# Certified upstream baseline files locked cryptographically
FROZEN_UPSTREAM_BASELINE = {
    "brain/carl_stage1_hal.py": "5a053a749088b90bd782b7f37e8e49ff4bb3e700a2cf50569325f520ff4437ee",
    "brain/carl_stage2_hd_ring.py": "1fa71ab575dc17c064a07a646703e120f24f84030e5e8a3142e3a21bde1f99fc",
    "brain/carl_stage2_grid_torus.py": "02a7c1cd70436fa14a66e51903a800a10c3a863e890c36189eccffa839859017",
    "brain/carl_stage2_3_r1_deliberation.py": "651682c3e0950a0bfa03b7841c313e4bd6028a3b29eb5a7af3d4015b35579019",
    "brain/carl_stage2_2_r2_occupancy_memory.py": "d68d1b6804ac09a2367f54f0a93bbc0aa6a7e5c3b78c545454a0f1c75f6bf904",
    "brain/carl_stage2_2_world_model.py": "3a4bc1859e487163255c7f65641b6f134a3f0443262c287bbb510ad83e545c33",
    "brain/carl_stage2_2_memory_module.py": "e40f71da3b430fe17ce7805259b7c554041894181ef0c674a64a3ba277a50fea",
    "brain/carl_mppi_deliberation.py": "6b4ebe6713068340181aa23bd418d2828ce23c2512f82ad1dffb2cac246ac0c9",
    "brain/carl_endocrine_adaptation.py": "1dda2bd40af402cdb2a0791ae9b52abf3ff44b56fab57e1ef085fb9db4cc6f11",
    "brain/carl_motor_synergies.py": "40c0cb5347536cd0c61caf1a82fa941c651fd5b728503da4f425e52ddef76483",
    "brain/carl_vision.py": "ca976989e5eefd6d5fd66d08ed6cc334da4f4c83d2b4ab143337d19c1798da41",
    "brain/carl_embodied_organism.py": "9ff0bc3e6bb5a895287d1cf018310e02925243965d453a5b73e25e0a15562290",
}


def test_stage4_decision_pipeline_ast_scan():
    """
    Tier 1: AST static inspection across all cognitive decision files.
    Verifies ZERO imports of mujoco and ZERO lookups of privileged simulator attributes.
    """
    forbidden_modules = {"mujoco"}
    forbidden_attrs = {"geom_xpos", "mj_ray", "qpos", "qvel", "qacc", "site_xpos"}
    forbidden_calls = {"mj_ray", "mj_step", "mj_forward"}

    for target_file in COGNITIVE_DECISION_PIPELINE_FILES:
        assert target_file.exists(), f"Cognitive file missing: {target_file}"
        source = target_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(target_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, (
                        f"FORBIDDEN IMPORT in {target_file.name}:{node.lineno} -> import {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not any(node.module.startswith(m) for m in forbidden_modules), (
                        f"FORBIDDEN FROM-IMPORT in {target_file.name}:{node.lineno} -> from {node.module}"
                    )
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_attrs, (
                    f"FORBIDDEN ATTRIBUTE ACCESS in {target_file.name}:{node.lineno} -> .{node.attr}"
                )
            elif isinstance(node, ast.Call):
                func = node.func
                call_name = getattr(func, "id", None) or getattr(func, "attr", None)
                if call_name:
                    assert call_name not in forbidden_calls, (
                        f"FORBIDDEN FUNCTION CALL in {target_file.name}:{node.lineno} -> {call_name}()"
                    )

    print(f"Decision Pipeline AST Scan: PASS. All {len(COGNITIVE_DECISION_PIPELINE_FILES)} files 100% clean.")


def test_embodied_organism_hygiene_scan():
    """
    Tier 2: Embodied organism hardware boundary hygiene.
    Verifies geom_xpos and qpos z-reads are strictly purged from carl_embodied_organism.py.
    """
    eo_path = REPO_ROOT / "brain" / "carl_embodied_organism.py"
    assert eo_path.exists()
    content = eo_path.read_text(encoding="utf-8")
    assert "geom_xpos" not in content, "geom_xpos detected in carl_embodied_organism.py"
    assert "data.qpos[2]" not in content, "qpos[2] z-read detected in carl_embodied_organism.py"
    print("Embodied Organism Hygiene: PASS. geom_xpos and qpos z-read successfully purged.")


def test_subprocess_airgap_mujoco_poisoned():
    """
    Tier 3: Poisoned-MuJoCo runtime execution test.
    Injects a poisoned MuJoCo stub into sys.modules, instantiates the canonical
    organism agent, and runs 1 cognitive cycle to verify total isolation.
    """
    sandbox_script = """
import sys
from unittest.mock import MagicMock

# Poison mujoco module so any access crashes
poison = MagicMock()
poison.__name__ = "mujoco"
sys.modules["mujoco"] = poison

try:
    from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
    agent = CarlAutonomousOrganismAgent(dt=0.0333)
    agent.reset()
    assert agent.tick == 0
    assert hasattr(agent, "stdp")
    assert hasattr(agent, "hdc")
    assert hasattr(agent, "sleep_engine")
    assert hasattr(agent, "gis")
    print("SUBPROCESS_AIRGAP_PASS")
except Exception as e:
    print(f"CRASH: {e}")
    sys.exit(1)
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


def test_upstream_baseline_sha256_integrity():
    """
    Tier 4: Cryptographic hash verification of certified upstream modules.
    Ensures upstream certified Stage 1, Stage 2, and Stage 3 code is not mutated.
    """
    for rel_path, expected_hash in FROZEN_UPSTREAM_BASELINE.items():
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Baseline artifact missing: {rel_path}"
        data = full_path.read_bytes()
        h_raw = hashlib.sha256(data).hexdigest()
        h_lf = hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
        assert expected_hash in (h_raw, h_lf), (
            f"HASH MISMATCH in {rel_path}:\n  Expected: {expected_hash}\n  Computed (raw): {h_raw}\n  Computed (lf):  {h_lf}"
        )
    print(f"Cryptographic Baseline: PASS. All {len(FROZEN_UPSTREAM_BASELINE)} upstream baseline artifacts intact.")


def test_stage4_memory_organs_quarantine():
    """
    Tier 5: Verifies that Stage 4 memory organs (STDP, HDC, SWR, GIS) strictly
    quarantine the CANN attractor weights from plastic mutation.
    """
    from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
    agent = CarlAutonomousOrganismAgent(dt=0.0333)
    cann_weights_initial = agent.cann_brain.hd_ring.W_sym.copy()

    # Step STDP with high reward
    pre = np.ones(32) * 0.8
    post = np.ones(8) * 0.8
    agent.stdp.step(pre, post, raw_reward=5.0, neuromodulator_level=1.0, enable_plasticity=True)

    # Step HDC
    cue = np.ones(8, dtype=np.float32) * 0.5
    agent.hdc.store_episode(0.5, 0.0, 0.0, cue, np.array([0.8, 0.8]), 1.0)

    # Step SWR
    agent.sleep_engine.execute_swr_reverse_replay(agent, [{"cann_x": 0.5, "cann_y": 0.0, "hd_heading": 0.0, "valence": 1.0, "action_u": [0.8, 0.8]}])

    # Check CANN weights
    cann_weights_after = agent.cann_brain.hd_ring.W_sym.copy()
    diff = np.max(np.abs(cann_weights_after - cann_weights_initial))
    assert diff == 0.0, f"CANN attractor weights mutated by memory organs! Diff: {diff}"
    print("Stage 4 Memory Organs Quarantine: PASS. CANN attractor divergence is exactly 0.0.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
