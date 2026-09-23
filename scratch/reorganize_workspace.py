"""
scratch/reorganize_workspace.py — Master Workspace Cleanup & Reorganization for D:\ebca

Systematically organizes D:\ebca into a clean, modern, professional structure:
- Root: Only master reports, master videos, simulation entrypoints, README, requirements, and main subsystem directories.
- training/: All training curricula and developmental suites.
- tools/: All utility scripts, visualizers, and diagnostics.
- docs/: Textbooks, research papers, hardware specs, and presentations.
- evidence/: Telemetry, replay logs, evaluation sets, and diagnostic plots.
- legacy/: Archived legacy arm, quadruped, and old dump experiments.
"""

import os
import shutil

BASE_DIR = r"D:\ebca"

def move_item(src_rel, dst_rel):
    src = os.path.join(BASE_DIR, src_rel)
    dst = os.path.join(BASE_DIR, dst_rel)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                # Merge directory
                for item in os.listdir(src):
                    s_item = os.path.join(src, item)
                    d_item = os.path.join(dst, item)
                    if not os.path.exists(d_item):
                        shutil.move(s_item, d_item)
                shutil.rmtree(src, ignore_errors=True)
            else:
                os.remove(dst)
                shutil.move(src, dst)
        else:
            shutil.move(src, dst)
        print(f"  [MOVED] {src_rel} -> {dst_rel}")

def reorganize_workspace():
    print("=" * 80)
    print("  EXECUTING COMPREHENSIVE EBCA WORKSPACE CLEANUP & REORGANIZATION")
    print("=" * 80)

    # 1. Create Target Directories
    for d in ["training", "tools", "docs", "evidence", "legacy"]:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

    # 2. Organize Training & Curriculum Suites
    training_files = [
        "train_carl_continuous_pinnacle.py",
        "train_carl_developmental_mastery.py",
        "train_carl_grand_mastery_suite.py",
        "train_carl_mastery_curriculum.py",
        "train_carl_parental_curriculum.py",
        "train_carl_perfection_suite.py",
        "train_carl_waterflow_locomotion.py",
        "phase18_alife_pretrained.py",
        "run_carl_showcase.py"
    ]
    for tf in training_files:
        move_item(tf, os.path.join("training", tf))

    # 3. Organize Tools & Diagnostics
    tool_files = [
        "live_plotter.py",
        "verify_locomotion.py",
        "test_collision_auditor.py",
        "organize_ebca.py"
    ]
    for t in tool_files:
        move_item(t, os.path.join("tools", t))

    # 4. Organize Documentation & Textbooks
    move_item("hardware_prototyping.md", os.path.join("docs", "hardware_prototyping.md"))
    move_item("carl_physical_prototype.png", os.path.join("docs", "hardware", "carl_physical_prototype.png"))
    move_item("carl_physical_prototype_labeled.png", os.path.join("docs", "hardware", "carl_physical_prototype_labeled.png"))
    move_item("presentation", os.path.join("docs", "presentation"))
    move_item("papers", os.path.join("docs", "papers"))
    move_item("textbook", os.path.join("docs", "textbook"))
    move_item("CARL_TEXTBOOK", os.path.join("docs", "CARL_TEXTBOOK"))

    # 5. Organize Evidence, Telemetry & Plots
    move_item("carl_dx_master_telemetry_dashboard.png", os.path.join("evidence", "master_dashboard", "carl_dx_master_telemetry_dashboard.png"))
    move_item("plots", os.path.join("evidence", "plots"))
    move_item("pngs", os.path.join("evidence", "pngs"))
    move_item("replays", os.path.join("evidence", "replays"))
    move_item("telemetry_raw", os.path.join("evidence", "telemetry_raw"))
    move_item("evaluation_sets", os.path.join("evidence", "evaluation_sets"))

    # 6. Organize Audit Artifacts
    move_item("phase0_integrity_reconciliation.json", os.path.join("audit", "phase0_integrity_reconciliation.json"))
    move_item("recovery_change_log.json", os.path.join("audit", "recovery_change_log.json"))
    move_item("manifest.json", os.path.join("audit", "manifest.json"))
    move_item("MUJOCO_LOG.TXT", os.path.join("audit", "MUJOCO_LOG.TXT"))

    # 7. Move Legacy Experiments & Old Dumps
    move_item("99_legacy_arm_experiments", os.path.join("legacy", "arm_experiments"))
    move_item("98_legacy_dump_and_scripts", os.path.join("legacy", "old_dump"))
    move_item("oldnot needed", os.path.join("legacy", "old_not_needed"))
    move_item("GENESIS", os.path.join("legacy", "GENESIS"))
    move_item("carl_quadruped_robot_files", os.path.join("legacy", "quadruped_robot_files"))

    print("=" * 80)
    print("  WORKSPACE REORGANIZATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    reorganize_workspace()
