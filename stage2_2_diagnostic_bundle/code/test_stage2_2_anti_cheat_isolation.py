"""
tests/test_stage2_2_anti_cheat_isolation.py — Step 3 Anti-Cheat & Full Call-Graph Isolation Harness
Classification: [PRE-EXECUTION VERIFICATION] Non-Negotiable Gate #3

Verifies that the Stage 2.2 Action-Conditioned World Model:
1. Has ZERO static AST reachability to MuJoCo, CarlStage1HAL, or simulator internals.
2. Can instantiate, step, and execute a 30-step autoregressive mental rollout in an air-gapped
   subprocess where MuJoCo is actively poisoned (sys.modules['mujoco'] = None).
"""

import ast
import os
import sys
import subprocess
from pathlib import Path
import pytest


def test_anti_cheat_ast_static_inspection():
    """
    Tier 1: AST static inspection of world model files.
    Asserts zero imports of mujoco and zero references to simulator internals across:
    - brain/carl_stage2_2_world_model.py
    - brain/carl_stage2_2_world_model_suite.py
    - brain/carl_stage2_2_memory_module.py
    """
    target_files = [
        Path("brain/carl_stage2_2_world_model.py"),
        Path("brain/carl_stage2_2_world_model_suite.py"),
        Path("brain/carl_stage2_2_memory_module.py")
    ]
    forbidden_modules = {"mujoco", "CarlStage1HAL", "carl_stage1_hal"}
    forbidden_names = {"mj_ray", "qpos", "qvel", "qacc", "geom_pos"}

    for target_file in target_files:
        assert target_file.exists(), f"Target file {target_file} must exist"

        with open(target_file, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(target_file))

        # Walk all AST nodes
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forb in forbidden_modules:
                        assert forb.lower() not in alias.name.lower(), (
                            f"FORBIDDEN IMPORT VIOLATION: '{alias.name}' in {target_file} line {node.lineno}"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for forb in forbidden_modules:
                        assert forb.lower() not in node.module.lower(), (
                            f"FORBIDDEN FROM-IMPORT VIOLATION: '{node.module}' in {target_file} line {node.lineno}"
                        )

            # Check attribute lookups (e.g. data.qpos, data.contact)
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names, (
                    f"FORBIDDEN ATTRIBUTE VIOLATION: '{node.attr}' in {target_file} line {node.lineno}"
                )

            # Check function calls (e.g. mj_ray)
            elif isinstance(node, ast.Name):
                assert node.id not in forbidden_names, (
                    f"FORBIDDEN NAME VIOLATION: '{node.id}' in {target_file} line {node.lineno}"
                )

        print(f"AST Static Analysis [{target_file}]: CLEAN. Zero MuJoCo reachability detected.")


def test_anti_cheat_subprocess_mujoco_poisoning():
    """
    Tier 2: Subprocess Sandbox Execution.
    Executes a 30-step mental forward rollout in an air-gapped Python subprocess
    where `sys.modules['mujoco'] = None`. If the model touches MuJoCo, it will crash.
    """
    sandbox_code = """
import sys
# Poison MuJoCo completely
sys.modules['mujoco'] = None

# Verify poisoning is active
try:
    import mujoco
    print("POISONING_FAILED")
    sys.exit(1)
except (ImportError, ModuleNotFoundError):
    pass  # Expected

import numpy as np
import torch
from brain.carl_stage2_2_world_model import (
    CarlStage2WorldModel,
    SensoryNormalizer,
    NaivePersistencePredictor,
    LinearActionPredictor
)

# 1. Instantiate World Model
model = CarlStage2WorldModel(hidden_dim=128)
normalizer = SensoryNormalizer(np.zeros(25), np.ones(25))

# 2. Prepare test inputs
h0 = torch.zeros(1, 1, 128)
s0 = torch.zeros(1, 25)
v_hd0 = torch.tensor([[1.0, 0.0]], dtype=torch.float32)
u_seq = torch.zeros(1, 30, 6, dtype=torch.float32)

# 3. Execute 30-step mental forward rollout
s_pred, v_pred, h_final = model.rollout_mental_trajectory(
    h_0=h0,
    s_0=s0,
    v_hd_0=v_hd0,
    u_seq=u_seq,
    normalizer=normalizer
)

assert s_pred.shape == (1, 30, 25), f"Shape mismatch: {s_pred.shape}"
assert v_pred.shape == (1, 30, 2), f"Heading shape mismatch: {v_pred.shape}"
assert h_final.shape == (1, 1, 128), f"Hidden shape mismatch: {h_final.shape}"

# 4. Verify Baselines
persistence = NaivePersistencePredictor()
p_pred = persistence.predict(np.zeros(25), horizon=30)
assert p_pred.shape == (30, 25)

linear = LinearActionPredictor()
linear.fit(np.zeros((10, 25)), np.ones((10, 2)), np.zeros((10, 6)), np.zeros((10, 25)))
l_pred = linear.predict(np.zeros(25), np.array([1.0, 0.0]), np.zeros((30, 6)))
assert l_pred.shape == (30, 25)

print("SUBPROCESS_AIR_GAP_SUCCESS")
"""

    result = subprocess.run(
        [sys.executable, "-c", sandbox_code],
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )

    if result.returncode != 0:
        print("Subprocess STDOUT:\n", result.stdout)
        print("Subprocess STDERR:\n", result.stderr)
        pytest.fail(f"Anti-Cheat Subprocess Sandbox Failed with code {result.returncode}")

    assert "SUBPROCESS_AIR_GAP_SUCCESS" in result.stdout
    print("Subprocess MuJoCo Poisoning Sandbox: PASSED. Mental rollouts are 100% air-gapped.")


if __name__ == "__main__":
    test_anti_cheat_ast_static_inspection()
    test_anti_cheat_subprocess_mujoco_poisoning()
    print("\nALL STEP 3 ANTI-CHEAT ISOLATION GATES VERIFIED!")
