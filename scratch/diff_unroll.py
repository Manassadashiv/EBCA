import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

# Let's inspect the exact lines of unroll in both files
with open("scratch/fast_eval_branches.py") as f:
    f1 = f.readlines()
with open("scratch/test_k_fwd_margin.py") as f:
    f2 = f.readlines()

print("fast_eval_branches.py lines 60-85:")
print("".join(f1[60:85]))

print("test_k_fwd_margin.py lines 42-67:")
print("".join(f2[42:67]))
