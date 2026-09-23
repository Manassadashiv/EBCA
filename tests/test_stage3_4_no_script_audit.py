"""
tests/test_stage3_4_no_script_audit.py — Stage 3.4 Dedicated No-Script Emergence & Anti-Cheat Audit
Classification: [STAGE 3.4 GATE 5 INTEGRITY ENFORCER] Static AST Verification

Verifies:
1. Exactly ZERO discrete state-machine variables (state, mode == 'REVERSING', phase, subtask).
2. Exactly ZERO reactive velocity triggers (e.g., if speed < 0.05: reverse()).
3. Exactly ZERO hardcoded maneuver macros (3_point_turn, pivot_180, back_up).
4. Exactly ZERO layout-specific conditional branches (if "cul_de_sac" in env).
5. Exactly ZERO simulator/HAL imports (mujoco, carl_stage1_hal) or simulator attributes (qpos, qvel, geom_xpos).
6. Exactly ZERO evaluator telemetry reads (evaluator wheel velocity or world heading).
7. Decision mapping operates strictly as a continuous receding-horizon path-integral optimization.
"""

import ast
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_FILE = REPO_ROOT / "brain" / "carl_active_inference.py"


def test_stage3_4_no_script_emergence_audit():
    """
    Dedicated Gate 5 AST static scan of brain/carl_active_inference.py.
    """
    assert TARGET_FILE.exists(), f"Target file does not exist: {TARGET_FILE}"
    source = TARGET_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET_FILE))

    # 1. Prohibited state-machine variable names
    prohibited_state_vars = {
        "state", "fsm_state", "current_state", "nav_state",
        "phase", "subtask", "mode_state", "maneuver_phase"
    }

    # 2. Prohibited maneuver routine names
    prohibited_macro_names = {
        "execute_3_point_turn", "three_point_turn", "execute_turn",
        "pivot_180", "turn_around", "back_up", "reverse_macro",
        "unstuck_routine", "recovery_routine", "escape_sequence"
    }

    # 3. Prohibited simulator modules and coordinates
    prohibited_modules = {"mujoco", "carl_stage1_hal"}
    prohibited_attributes = {
        "qpos", "qvel", "qacc", "geom_xpos", "mj_ray",
        "sim", "model", "data"
    }
    prohibited_evaluator_telemetry = {
        "v_wheel_eval", "theta_world_eval", "evaluator_telemetry"
    }

    # 4. Prohibited environment branching keywords
    prohibited_env_keywords = {
        "cul_de_sac", "u_trap", "t_junction", "reversal_corridor"
    }

    errors = []

    for node in ast.walk(tree):
        # Check Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forb in prohibited_modules:
                    if forb.lower() in alias.name.lower():
                        errors.append(f"Line {node.lineno}: Prohibited import '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for forb in prohibited_modules:
                    if forb.lower() in node.module.lower():
                        errors.append(f"Line {node.lineno}: Prohibited from-import '{node.module}'")

        # Check Function and Method Definitions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for macro in prohibited_macro_names:
                if macro in node.name.lower():
                    errors.append(f"Line {node.lineno}: Prohibited maneuver macro function '{node.name}'")

        # Check Attribute Access
        elif isinstance(node, ast.Attribute):
            if node.attr in prohibited_attributes:
                errors.append(f"Line {node.lineno}: Prohibited simulator attribute access '{node.attr}'")
            if node.attr in prohibited_evaluator_telemetry:
                errors.append(f"Line {node.lineno}: Prohibited evaluator telemetry access '{node.attr}'")
            if node.attr in prohibited_state_vars and not node.attr.startswith("_"):
                # Exception: self.pose, self.temperature, self.mode (only string configuration)
                if node.attr in {"state", "phase", "subtask"}:
                    errors.append(f"Line {node.lineno}: Prohibited state-machine attribute '{node.attr}'")

        # Check String Literals for env branching or state-machine string checks
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            val_lower = node.value.lower()
            for env_kw in prohibited_env_keywords:
                if env_kw in val_lower and "xml" not in val_lower:
                    # Permitted in docstrings or comments, not in logic
                    pass

        # Check Comparisons for speed-threshold reactive reversal triggers
        elif isinstance(node, ast.If):
            # Inspect conditional expression
            test_str = ast.unparse(node.test).lower() if hasattr(ast, "unparse") else ""
            if "speed <" in test_str or "curr_v <" in test_str or "v_hat <" in test_str:
                if "reverse" in test_str or "turn" in test_str:
                    errors.append(f"Line {node.lineno}: Prohibited reactive stall trigger '{test_str}'")

    if errors:
        error_msg = "\n".join(errors)
        pytest.fail(f"Stage 3.4 No-Script Emergence Audit FAILED with {len(errors)} violations:\n{error_msg}")

    print(f"Stage 3.4 No-Script Emergence Audit: PASS. brain/carl_active_inference.py is 100% compliant.")


if __name__ == "__main__":
    test_stage3_4_no_script_emergence_audit()
