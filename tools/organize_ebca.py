"""
Script to systematically organize the EBCA workspace:
1. Moves all legacy arm/hand scripts & weights to 99_legacy_arm_experiments/
2. Moves old presentation scripts and dumps to 98_legacy_dump_and_scripts/
"""
import os
import shutil

BASE_DIR = r"D:\ebca"
ARM_DIR = os.path.join(BASE_DIR, "99_legacy_arm_experiments")
DUMP_DIR = os.path.join(BASE_DIR, "98_legacy_dump_and_scripts")

os.makedirs(ARM_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)

ARM_FILES = [
    "train_carl_arm_fingers.py",
    "train_carl_curiosity_curriculum.py",
    "train_carl_v2_dapg.py",
    "train_carl_overnight.py",
    "brute_force_100g.py",
    "brute_force_3f.py",
    "diagnose_carl_fingertips.py",
    "diagnose_f2_gap.py",
    "diagnose_grasp.py",
    "sweep_ik_height.py",
    "sweep_wrist_height.py",
    "verify_f2_contact.py",
    "vsu_verify.py",
    "showcase_carl_manipulation.py",
    "generate_carl_v2.py",
    "generate_carl_v2_demos.py",
    "carl_v2_core.py",
    "test_carl_v2_core.py"
]

DUMP_FILES = [
    "generate_carl_lit_review_13_papers.py",
    "generate_jntuh_lit_review.py",
    "carl_1_pptx_data.json",
    "MUJOCO_LOG.TXT"
]

def organize():
    print("=" * 80)
    print("  ORGANIZING EBCA WORKSPACE STRUCTURE")
    print("=" * 80)

    # 1. Move Arm Legacy Files
    arm_count = 0
    for fname in ARM_FILES:
        src = os.path.join(BASE_DIR, fname)
        dst = os.path.join(ARM_DIR, fname)
        if os.path.exists(src):
            shutil.move(src, dst)
            arm_count += 1
            print(f"  [ARM RETIRED] Moved {fname} -> 99_legacy_arm_experiments/")

    # 2. Move Dump Files
    dump_count = 0
    for fname in DUMP_FILES:
        src = os.path.join(BASE_DIR, fname)
        dst = os.path.join(DUMP_DIR, fname)
        if os.path.exists(src):
            shutil.move(src, dst)
            dump_count += 1
            print(f"  [DUMP ARCHIVED] Moved {fname} -> 98_legacy_dump_and_scripts/")

    print("=" * 80)
    print(f"[SUCCESS] Moved {arm_count} arm files and {dump_count} dump files.")
    print("=" * 80)

if __name__ == "__main__":
    organize()
