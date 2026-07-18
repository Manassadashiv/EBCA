"""
fix_all_hardcoded_paths.py
Replaces every D:/ebca hardcoded path in the EBCA repo with
dynamic os.path resolution relative to each file's own location.
Run from D:/ebca: python fix_all_hardcoded_paths.py
"""
import re, sys, os

BASE = "D:/ebca"

def sub(content, old, new):
    return content.replace(old, new)

# ─────────────────────────────────────────────────────────────────────────────
# carl_simulation.py  (lives at repo root)
# ─────────────────────────────────────────────────────────────────────────────
path = f"{BASE}/carl_simulation.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

src = sub(src,
    'sys.path.append("D:/ebca")',
    'BASE_DIR = os.path.dirname(os.path.abspath(__file__))\nsys.path.append(BASE_DIR)')

src = sub(src,
    '"D:/ebca/memory/carl_multi_object_vision.pt"',
    'os.path.join(BASE_DIR, "memory", "carl_multi_object_vision.pt")')

src = sub(src,
    '"D:/ebca/world/vessel_kinetic.xml"',
    'os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")')

src = sub(src,
    '"D:/ebca/memory/carl_reservoir.npz"',
    'os.path.join(BASE_DIR, "memory", "carl_reservoir.npz")')

src = sub(src,
    '"D:/ebca/memory/telemetry_autonomous.csv"',
    'os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")')

with open(path, "w", encoding="utf-8") as f:
    f.write(src)
print(f"[FIXED] {path}")

# ─────────────────────────────────────────────────────────────────────────────
# live_plotter.py  (lives at repo root)
# ─────────────────────────────────────────────────────────────────────────────
path = f"{BASE}/live_plotter.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

# Insert BASE_DIR after first import block if not already present
if "BASE_DIR" not in src:
    src = 'import os\n' + src if 'import os' not in src else src
    src = src.replace(
        'TELEMETRY_PATH = "D:/ebca/memory/telemetry_autonomous.csv"',
        'BASE_DIR = os.path.dirname(os.path.abspath(__file__))\n'
        'TELEMETRY_PATH = os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")')
else:
    src = sub(src,
        'TELEMETRY_PATH = "D:/ebca/memory/telemetry_autonomous.csv"',
        'TELEMETRY_PATH = os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")')

with open(path, "w", encoding="utf-8") as f:
    f.write(src)
print(f"[FIXED] {path}")

# ─────────────────────────────────────────────────────────────────────────────
# brain scripts — BASE_DIR is one directory up from __file__
# ─────────────────────────────────────────────────────────────────────────────
BRAIN_BASE_DECL = (
    "import os as _os\n"
    "_FILE_DIR = _os.path.dirname(_os.path.abspath(__file__))\n"
    "BASE_DIR = _os.path.dirname(_FILE_DIR)\n"
)

def fix_brain_file(filepath, replacements):
    with open(filepath, encoding="utf-8") as f:
        src = f.read()

    # Inject BASE_DIR declaration after the last import line at top if missing
    if "BASE_DIR" not in src:
        # Insert right after the last sys.path line or after first import block
        insert_after = re.search(r'^(import |from |sys\.path)', src, re.MULTILINE)
        if insert_after:
            # Find end of contiguous import block
            lines = src.split("\n")
            insert_idx = 0
            for i, ln in enumerate(lines):
                if ln.startswith("import ") or ln.startswith("from ") or ln.startswith("sys.path"):
                    insert_idx = i
            lines.insert(insert_idx + 1, BRAIN_BASE_DECL)
            src = "\n".join(lines)

    for old, new in replacements:
        src = src.replace(old, new)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"[FIXED] {filepath}")


# brain/collect_multi_object_dataset.py
fix_brain_file(f"{BASE}/brain/collect_multi_object_dataset.py", [
    ('sys.path.append("D:/ebca/brain")',       'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/world/vessel_kinetic.xml"',     'os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")'),
    ('"D:/ebca/memory/multi_object_dataset"',  'os.path.join(BASE_DIR, "memory", "multi_object_dataset")'),
])

# brain/collect_vision_dataset.py
fix_brain_file(f"{BASE}/brain/collect_vision_dataset.py", [
    ('sys.path.append("D:/ebca/brain")',       'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/world/vessel_kinetic.xml"',     'os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")'),
    ('"D:/ebca/memory/vision_dataset"',        'os.path.join(BASE_DIR, "memory", "vision_dataset")'),
])

# brain/plot_telemetry.py
fix_brain_file(f"{BASE}/brain/plot_telemetry.py", [
    ('"D:/ebca/memory/telemetry_autonomous.csv"', 'os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")'),
    ('"D:/ebca/autonomous_emergence_proof.png"',  'os.path.join(BASE_DIR, "autonomous_emergence_proof.png")'),
])

# brain/show_carl.py
fix_brain_file(f"{BASE}/brain/show_carl.py", [
    ('sys.path.append("D:/ebca/brain")',       'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/world/vessel_kinetic.xml"',     'os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")'),
])

# brain/train_multi_object_vision.py
fix_brain_file(f"{BASE}/brain/train_multi_object_vision.py", [
    ('sys.path.append("D:/ebca/brain")',                'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/memory/multi_object_dataset"',           'os.path.join(BASE_DIR, "memory", "multi_object_dataset")'),
    ('"D:/ebca/memory/carl_multi_object_vision.pt"',    'os.path.join(BASE_DIR, "memory", "carl_multi_object_vision.pt")'),
])

# brain/train_vision.py
fix_brain_file(f"{BASE}/brain/train_vision.py", [
    ('sys.path.append("D:/ebca/brain")',       'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/memory/vision_dataset"',        'os.path.join(BASE_DIR, "memory", "vision_dataset")'),
    ('"D:/ebca/memory/carl_vision.pt"',        'os.path.join(BASE_DIR, "memory", "carl_vision.pt")'),
])

# brain/verify_multi_object_predictions.py
fix_brain_file(f"{BASE}/brain/verify_multi_object_predictions.py", [
    ('sys.path.append("D:/ebca/brain")',                'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/memory/carl_multi_object_vision.pt"',    'os.path.join(BASE_DIR, "memory", "carl_multi_object_vision.pt")'),
    ('"D:/ebca/memory/multi_object_dataset"',           'os.path.join(BASE_DIR, "memory", "multi_object_dataset")'),
    ('"D:/ebca/multi_object_verification_result.png"',  'os.path.join(BASE_DIR, "multi_object_verification_result.png")'),
])

# brain/verify_vision_predictions.py
fix_brain_file(f"{BASE}/brain/verify_vision_predictions.py", [
    ('sys.path.append("D:/ebca/brain")',       'sys.path.append(BASE_DIR)'),
    ('"D:/ebca/memory/carl_vision.pt"',        'os.path.join(BASE_DIR, "memory", "carl_vision.pt")'),
    ('"D:/ebca/memory/vision_dataset"',        'os.path.join(BASE_DIR, "memory", "vision_dataset")'),
    ('"D:/ebca/vision_verification_result.png"', 'os.path.join(BASE_DIR, "vision_verification_result.png")'),
])

print("\n[DONE] All hardcoded D:/ebca paths replaced with dynamic BASE_DIR resolution.")
