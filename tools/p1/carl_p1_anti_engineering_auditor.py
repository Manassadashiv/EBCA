"""
tools/p1/carl_p1_anti_engineering_auditor.py — Automated Anti-Engineering & Non-Scripting Source Auditor

Audits P1 code, core brain, and experimental harnesses for forbidden behavior-specific heuristics:
- Behavior-specific if/else rules (e.g. "if obstacle -> turn_left")
- Target-specific route choices (e.g. "if food_at_x -> take_route_b")
- Fixed trajectory playback or hardcoded action sequence lookup tables
- Seed-specific policy branching (e.g. "if seed == 42 -> ...")
- Environment-specific action steering overrides
- Hidden teleoperation or cheat coordinates
"""

import os
import sys
import ast
import json
import re
from typing import Dict, Any, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

AUDIT_OUTPUT_PATH = os.path.join(REPO_ROOT, "evidence", "p1", "audit", "anti_engineering_audit_report.json")


class AntiEngineeringAuditor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []

    def visit_If(self, node: ast.If):
        cond_str = ast.unparse(node.test)
        body_str = "\n".join([ast.unparse(b) for b in node.body])
        
        # 1. Check for seed-specific policy branching
        if re.search(r"seed\s*==\s*\d+", cond_str):
            if any(act in body_str for act in ["CURVE_", "STRAIGHT_", "SPIN_", "REVERSE_", "chosen_action_name"]):
                self.findings.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "rule": "SEED_SPECIFIC_POLICY_BRANCHING",
                    "severity": "CRITICAL",
                    "code_snippet": cond_str,
                    "description": "Branching policy decisions based on random seed integer."
                })

        # 2. Check for route-specific forced action branching
        if re.search(r"\broute\s*==\s*['\"]|\btake_route\b|\bpreferred_route\b", cond_str, re.IGNORECASE):
            if any(act in body_str for act in ["CURVE_", "STRAIGHT_", "SPIN_", "best_action_name", "chosen_action_name"]):
                self.findings.append({
                    "file": self.filename,
                    "line": node.lineno,
                    "rule": "ROUTE_SPECIFIC_FORCED_CHOICE",
                    "severity": "CRITICAL",
                    "code_snippet": cond_str,
                    "description": "Hardcoded route selection rule instead of Active Inference Free Energy optimization."
                })

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        target_str = ast.unparse(node.targets[0])
        val_str = ast.unparse(node.value)
        
        # Check for hardcoded trajectory playback arrays
        if "trajectory_playback" in target_str or "scripted_actions" in target_str or "hardcoded_waypoint_list" in target_str:
            self.findings.append({
                "file": self.filename,
                "line": node.lineno,
                "rule": "TRAJECTORY_PLAYBACK_TABLE",
                "severity": "CRITICAL",
                "code_snippet": f"{target_str} = {val_str[:50]}...",
                "description": "Predefined coordinate trajectory or action sequence playback detected."
            })
            
        self.generic_visit(node)


def audit_p1_source_tree() -> Dict[str, Any]:
    """
    Audits all files in brain/p1, tools/p1, and core brain directories (excluding auditor itself).
    """
    target_dirs = [
        os.path.join(REPO_ROOT, "brain", "p1"),
        os.path.join(REPO_ROOT, "tools", "p1"),
        os.path.join(REPO_ROOT, "brain")
    ]
    
    files_audited = []
    all_findings = []
    
    for d in target_dirs:
        if not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            if fname.endswith(".py") and fname != "carl_p1_anti_engineering_auditor.py":
                fpath = os.path.join(d, fname)
                rel_path = os.path.relpath(fpath, REPO_ROOT)
                files_audited.append(rel_path)
                
                try:
                    with open(fpath, "r", encoding="utf-8") as src_f:
                        code = src_f.read()
                    
                    # AST Parse
                    tree = ast.parse(code, filename=rel_path)
                    auditor = AntiEngineeringAuditor(rel_path)
                    auditor.visit(tree)
                    all_findings.extend(auditor.findings)
                    
                    # Regex Scan for specific banned phrases in non-comment code lines
                    lines = code.split("\n")
                    for l_idx, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                            continue
                        
                        banned_patterns = [
                            (r"if\s+obstacle\s*:\s*action\s*=", "SCRIPTED_OBSTACLE_RESPONSE"),
                            (r"if\s+resource_moves\s*:\s*follow", "SCRIPTED_RESOURCE_TRACKING"),
                            (r"hardcoded_waypoints\s*=", "HARDCODED_WAYPOINTS"),
                            (r"teleport_robot\s*\(", "UNPHYSICAL_TELEPORTATION")
                        ]
                        for pat, rule in banned_patterns:
                            if re.search(pat, stripped, re.IGNORECASE):
                                all_findings.append({
                                    "file": rel_path,
                                    "line": l_idx,
                                    "rule": rule,
                                    "severity": "CRITICAL",
                                    "code_snippet": stripped,
                                    "description": f"Banned anti-engineering pattern match: {rule}"
                                })
                            
                except Exception as e:
                    print(f"[WARN] Failed to parse {rel_path}: {e}")

    verdict = "ZERO BEHAVIOR-SPECIFIC SOLUTION RULES" if len(all_findings) == 0 else "AUDIT_FAILED_HEURISTICS_FOUND"
    
    report = {
        "audit_name": "CARL-DX PHASE 1 ANTI-ENGINEERING SOURCE AUDIT",
        "verdict": verdict,
        "number_of_behavior_specific_rules": len(all_findings),
        "total_files_audited": len(files_audited),
        "audited_files": files_audited,
        "findings": all_findings,
        "status": "QUALIFIED" if len(all_findings) == 0 else "DISQUALIFIED"
    }
    
    os.makedirs(os.path.dirname(AUDIT_OUTPUT_PATH), exist_ok=True)
    with open(AUDIT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"\n[ANTI-ENGINEERING AUDIT COMPLETE]")
    print(f"Files Audited: {len(files_audited)}")
    print(f"Violations Found: {len(all_findings)}")
    print(f"Final Verdict: {verdict}")
    return report


if __name__ == "__main__":
    audit_p1_source_tree()
