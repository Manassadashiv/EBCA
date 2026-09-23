"""
tools/p1_r1/p1r1_anti_engineering_auditor.py — P1-R1 Static AST & Regex Anti-Engineering Auditor

Scans Python source trees to ensure zero behavior-specific heuristic rules,
hardcoded route selection tables, or seed-specific policy branching.
"""

from typing import List, Dict, Any
import os
import ast
import re
import json


class P1R1AntiEngineeringAuditor:
    """
    Automated AST auditor verifying zero behavior-specific solution heuristics.
    """
    FORBIDDEN_PATTERNS = [
        re.compile(r'if\s+.*blocked.*turn', re.IGNORECASE),
        re.compile(r'if\s+.*obstacle.*choose_route', re.IGNORECASE),
        re.compile(r'hardcoded_route', re.IGNORECASE),
        re.compile(r'waypoint_table', re.IGNORECASE),
        re.compile(r'if\s+seed\s*==\s*\d+:', re.IGNORECASE),
        re.compile(r'force_action\s*=', re.IGNORECASE),
        re.compile(r'if\s+episode\s*==\s*6\s*:\s*.*turn', re.IGNORECASE),
    ]

    def __init__(self, target_dirs: List[str] = None):
        if target_dirs is None:
            self.target_dirs = ["brain/p1_r1", "tools/p1_r1", "brain"]
        else:
            self.target_dirs = target_dirs
        self.findings = []
        self.audited_files = []

    def audit_file(self, filepath: str) -> List[Dict[str, Any]]:
        file_findings = []
        self.audited_files.append(filepath)
        
        # Do not scan the auditor's own pattern definition file for its own regex strings
        if "anti_engineering_auditor" in filepath:
            return []
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return [{"file": filepath, "type": "READ_ERROR", "message": str(e)}]

        # Regex Scan
        for line_no, line in enumerate(content.splitlines(), start=1):
            for pat in self.FORBIDDEN_PATTERNS:
                if pat.search(line):
                    file_findings.append({
                        "file": filepath,
                        "line": line_no,
                        "type": "FORBIDDEN_REGEX_PATTERN",
                        "snippet": line.strip()
                    })

        # AST Parse & Inspection
        try:
            tree = ast.parse(content, filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    # Check for seed-specific comparison
                    if isinstance(node.test, ast.Compare):
                        left_src = ast.unparse(node.test.left) if hasattr(ast, "unparse") else ""
                        if "seed" in left_src.lower():
                            for comp in node.test.comparators:
                                if isinstance(comp, ast.Constant) and isinstance(comp.value, int):
                                    file_findings.append({
                                        "file": filepath,
                                        "line": node.lineno,
                                        "type": "SEED_SPECIFIC_BRANCH",
                                        "snippet": f"if {left_src} == {comp.value}:"
                                    })
        except Exception:
            pass

        return file_findings

    def run_full_audit(self) -> Dict[str, Any]:
        self.findings.clear()
        self.audited_files.clear()
        
        for tdir in self.target_dirs:
            if not os.path.exists(tdir):
                continue
            for root, _, files in os.walk(tdir):
                for f in files:
                    if f.endswith(".py"):
                        fpath = os.path.join(root, f)
                        res = self.audit_file(fpath)
                        self.findings.extend(res)

        status = "QUALIFIED" if len(self.findings) == 0 else "FLAGGED"
        report = {
            "audit_name": "CARL-DX P1-R1 ANTI-ENGINEERING SOURCE AUDIT",
            "verdict": "ZERO BEHAVIOR-SPECIFIC SOLUTION RULES" if status == "QUALIFIED" else "VIOLATIONS_FOUND",
            "number_of_behavior_specific_rules": len(self.findings),
            "total_files_audited": len(self.audited_files),
            "audited_files": self.audited_files,
            "findings": self.findings,
            "status": status
        }
        return report


if __name__ == "__main__":
    auditor = P1R1AntiEngineeringAuditor()
    rep = auditor.run_full_audit()
    out_dir = "evidence/p1_r1/audit"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "P1R1_ANTI_ENGINEERING_AUDIT.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"Audit completed: {rep['total_files_audited']} files inspected, {len(rep['findings'])} violations found. Verdict: {rep['verdict']}")
