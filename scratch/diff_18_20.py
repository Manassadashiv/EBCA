import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

with open("scratch/test_18_passes.py") as f:
    l18 = f.readlines()
with open("scratch/test_all_20.py") as f:
    l20 = f.readlines()

for i, (line1, line2) in enumerate(zip(l18[30:80], l20[30:80])):
    if line1 != line2:
        print(f"Line {i+31}:")
        print(f"  test_18: {line1.strip()}")
        print(f"  test_20: {line2.strip()}")
